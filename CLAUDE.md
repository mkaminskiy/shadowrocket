# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a configuration repository for VPN client routing rules. Supported clients:
- **Shadowrocket** (iOS) — primary client
- **V2RayTun** (Android)

Configuration files are served via GitHub raw URLs.

## Files

- **`proxy.list`** — The shared proxy ruleset. Both Shadowrocket configs reference this file via its raw GitHub URL. Contains domain rules (`DOMAIN-SUFFIX`, `DOMAIN-KEYWORD`, `DOMAIN`), port rules (`DST-PORT`), and IP CIDR rules (`IP-CIDR`). This is the primary file that gets edited when adding/removing proxied services.
- **`default.conf`** — Minimal Shadowrocket configuration with standard settings.
- **`KaminskiyVPN.conf`** — Extended Shadowrocket configuration with additional `skip-proxy` and `tun-excluded-routes` entries (Kaspersky, Yandex Cloud, and other Russian service IPs that should always be direct).
- **`KaminskiyVPN.v2raytun.routing.json`** — V2RayTun routing config (generated from `proxy.list`).

## Routing Logic

The routing priority is:
1. Specific domains/IPs listed in `proxy.list` → routed through **PROXY**
2. Russian GeoIP (`GEOIP,RU`) → **DIRECT**
3. Everything else → **DIRECT**

## Workflow

**`proxy.list` is the source of truth.** All routing changes go into this file.

### Automatic JSON Generation (Recommended)

When you push changes to `proxy.list` to the `main` branch, GitHub Actions automatically:
1. Runs `generate_routing.py` to regenerate `KaminskiyVPN.v2raytun.routing.json`
2. Creates a commit with the updated JSON (by `github-actions[bot]`)
3. Pushes the commit back to the repository

See `.github/workflows/update-routing.yml` for the workflow configuration.

### Manual JSON Generation (Optional)

If you need to generate JSON locally:

```bash
python3 generate_routing.py
```

This will update `KaminskiyVPN.v2raytun.routing.json` in place. You can then commit both files together.

### Rule syntax mapping (proxy.list → V2Ray JSON)

| Shadowrocket (`proxy.list`)        | V2Ray JSON                   |
|------------------------------------|------------------------------|
| `DOMAIN-SUFFIX,example.com`        | `"domain:example.com"`       |
| `DOMAIN,api.example.com`           | `"full:api.example.com"`     |
| `DOMAIN-KEYWORD,foo`               | `"keyword:foo"`              |
| `IP-CIDR,x.x.x.x/y,no-resolve`   | added to `"ip"` array        |
| `DST-PORT,3478,PROXY`              | added to `"port"` string     |

### V2RayTun JSON format

Root object fields: `domainStrategy`, `id` (UUID), `balancers`, `domainMatcher`, `name`, `rules`.

Each rule object has: `__name__` (group label), `id` (UUID), `type` ("field"), `outboundTag`, and traffic matching fields (`domain`, `ip`, `port`, `network`).

Note: `port` is a **string** (e.g. `"3478,3480,5222,596-599"`), not an array.

### V2Ray JSON rule structure

Each `#`-group from `proxy.list` maps to a **separate rule block** with its own `__name__`, `id`, `domain`/`ip` arrays, and `outboundTag`. The full rule order:

1. **"Прямые домены"** (`direct`) — local domains/IPs, Kaspersky, etc. + `geoip:private`. Not generated from proxy.list.
2. **"Прямые RU"** (`direct`) — `geoip:ru`. Not generated from proxy.list.
3. **One rule per group from proxy.list** (`proxy`) — e.g. "Google Gemini", "Anthropic", "OpenAI", "Meta", "Twitter/X", "Media", "Youtube", "Video", "TikTok", "Разное", "WhatsApp", "Telegram". Groups with `IP-CIDR` entries (WhatsApp, Telegram) include both `domain` and `ip` arrays in the same rule.
4. **"Голосовые и видеозвонки"** (`proxy`) — all `DST-PORT` entries combined into a single `port` string.
5. **"Default"** (`direct`) — catch-all, `network: ["tcp"]`.

## Delivery pipeline

```
proxy.list изменён → git push → GitHub Actions
                                       ↓
                            generate_routing.py (автоматически)
                                       ↓
                       JSON обновлён → auto commit → GitHub raw
                                                          ↓
                                            cron (каждые 5 мин) на VPN-сервере
                                                          ↓
                                                /opt/vpn/update-routing.sh
                                                → curl JSON из GitHub
                                                → base64 → nginx snippet
                                                → nginx reload
                                                          ↓
                                        V2RayTun обновляет подписку (каждый час)
                                        → получает заголовок routing с base64 JSON
                                        → применяет маршрутизацию
```

### Shadowrocket (iOS)
Shadowrocket читает `proxy.list` напрямую из GitHub raw URL (указан в `update-url` внутри `.conf` файлов, интервал 60 сек).

### V2RayTun (Android)
V2RayTun получает маршрутизацию через HTTP-заголовок `routing` (base64-encoded JSON) при обновлении подписки 3x-ui. Nginx на VPN-сервере проксирует подписки по HTTPS (Let's Encrypt) и инжектит этот заголовок. V2RayTun требует HTTPS для подписок с публичных хостов (HTTP допускается только с localhost/private IP).

## Server infrastructure

- **3x-ui** — панель управления Xray, запущена в Docker (`/home/max/3x-ui/`, `network_mode: host`)
- **Nginx** — HTTPS reverse proxy для подписок (Let's Encrypt), добавляет заголовок `routing` с base64 JSON маршрутизации
- **Xray** — VPN-сервер (порт 443)
- **Certbot** — автообновление Let's Encrypt сертификата; renewal hooks открывают/закрывают порт 80 в UFW

### Порты
- **443** — Xray (VPN трафик)
- **2096** — Nginx HTTPS (проксирует подписки, добавляет routing header). V2RayTun требует HTTPS для подписок с публичных хостов.
- **12096** (localhost) — 3x-ui subscription handler (внутренний, проксируется через nginx)
- **65512** — 3x-ui web panel

### Настройки подписки в 3x-ui (SQLite: `/home/max/3x-ui/db/x-ui.db`, таблица `settings`)
- `subPort=12096`, `subListen=127.0.0.1` — подписки слушают только на localhost
- `subURI` — внешний URL подписки (включая путь), используется для генерации QR-кодов и ссылок в панели. Должен быть `https://` и указывать на nginx (порт 2096), а не на внутренний порт.
- `subPath` — путь подписки (например `/sub/.../`), входит в `subURI`

### Ключевые файлы на сервере
- `/opt/vpn/routing.json` — текущий JSON маршрутизации (скачан из GitHub)
- `/opt/vpn/nginx-routing-header.conf` — сгенерированный nginx snippet с base64 routing в переменных (разбит на чанки по 3500 символов из-за лимита строки nginx)
- `/opt/vpn/update-routing.sh` — скрипт обновления: скачивает JSON, кодирует в base64, генерирует nginx snippet, делает reload
- `/etc/cron.d/update-routing` — cron задача (`*/5 * * * *`)
- `/etc/nginx/sites-available/v2raytun-sub.conf` — конфиг nginx
- `/etc/letsencrypt/live/vpn.kaminskiy.me/` — Let's Encrypt сертификат
- `/etc/letsencrypt/renewal-hooks/pre/open-port80.sh` — открывает порт 80 перед обновлением сертификата
- `/etc/letsencrypt/renewal-hooks/post/close-port80.sh` — закрывает порт 80 и делает nginx reload после обновления

### HTTP-заголовки подписки (V2RayTun)
- `routing` — base64-encoded JSON маршрутизации, добавляется nginx, применяется клиентом автоматически при подключении VPN
- `profile-update-interval` — интервал обновления подписки в часах, проходит от 3x-ui (настраивается в панели)

## Key Conventions

- Entries in `proxy.list` are grouped by service with `#` comment headers (AI, Meta, Twitter/X, YouTube, Telegram, WhatsApp, etc.)
- Group names in `proxy.list` comments must match the desired rule names in V2Ray JSON (e.g., `#Anthropic`, not `#Antropic`)
- The `.conf` files have `update-url` pointing to their own raw GitHub URL on `main` branch — changes take effect on clients after push
- **DO NOT manually edit `KaminskiyVPN.v2raytun.routing.json`** — it's auto-generated by GitHub Actions
- After editing `proxy.list`: commit and push — GitHub Actions will regenerate JSON automatically, then VPN server picks up changes within 5 minutes

## Automation Files

- **`generate_routing.py`** — Python script that converts `proxy.list` to V2Ray JSON format
- **`.github/workflows/update-routing.yml`** — GitHub Actions workflow for automatic JSON regeneration
- **`AUTOMATION.md`** — Detailed documentation about the automation system
