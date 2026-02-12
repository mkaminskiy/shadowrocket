# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a configuration repository for VPN client routing rules. Supported clients:
- **Shadowrocket** (iOS) — primary client
- **V2RayTun** (Android)

Configuration files are served via GitHub raw URLs for auto-update by the clients.

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

**`proxy.list` is the source of truth.** All routing changes go into this file. After modifying `proxy.list`, regenerate `KaminskiyVPN.v2raytun.routing.json` by converting the rules to V2Ray JSON format.

### Rule syntax mapping (proxy.list → V2Ray JSON)

| Shadowrocket (`proxy.list`)  | V2Ray JSON (`routing.json`)       |
|------------------------------|-----------------------------------|
| `DOMAIN-SUFFIX,example.com`  | `"domain:example.com"`            |
| `DOMAIN,api.example.com`     | `"full:api.example.com"`          |
| `DOMAIN-KEYWORD,foo`         | `"keyword:foo"`                   |
| `IP-CIDR,x.x.x.x/y,no-resolve` | IP added to `"ip"` array      |
| `DST-PORT,3478,PROXY`        | Added to `"port"` array           |

### V2Ray JSON structure

The JSON file has ordered rules:
1. `"direct"` — domains/IPs that bypass proxy (local, Kaspersky, etc.) + `geoip:private`
2. `"direct"` — `geoip:ru`
3. `"proxy"` — domains from `proxy.list`
4. `"proxy"` — IPs and ports from `proxy.list`
5. `"direct"` — catch-all for everything else

## Key Conventions

- Entries in `proxy.list` are grouped by service with `#` comment headers (AI, Meta, Twitter/X, YouTube, Telegram, WhatsApp, etc.)
- The `.conf` files have `update-url` pointing to their own raw GitHub URL on `main` branch — changes take effect on clients after push
