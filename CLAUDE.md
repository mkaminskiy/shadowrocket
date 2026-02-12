# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a configuration repository for proxy/VPN routing rules, used by **Shadowrocket** (iOS proxy client) and **V2RayTun**. There is no build system, no tests, and no application code — only configuration files served via GitHub raw URLs for auto-update by the clients.

## Files

- **`proxy.list`** — The shared proxy ruleset. Both Shadowrocket configs reference this file via its raw GitHub URL. Contains domain rules (`DOMAIN-SUFFIX`, `DOMAIN-KEYWORD`, `DOMAIN`), port rules (`DST-PORT`), and IP CIDR rules (`IP-CIDR`). This is the primary file that gets edited when adding/removing proxied services.
- **`default.conf`** — Minimal Shadowrocket configuration with standard settings.
- **`KaminskiyVPN.conf`** — Extended Shadowrocket configuration with additional `skip-proxy` and `tun-excluded-routes` entries (Kaspersky, Yandex Cloud, and other Russian service IPs that should always be direct).
- **`KaminskiyVPN.v2raytun.routing.json`** — V2RayTun routing config. Contains equivalent rules to `proxy.list` but in V2Ray JSON format. Must be kept in sync with `proxy.list` when domains/IPs change.

## Routing Logic

The routing priority is:
1. Specific domains/IPs listed in `proxy.list` → routed through **PROXY**
2. Russian GeoIP (`GEOIP,RU`) → **DIRECT**
3. Everything else → **DIRECT**

## Key Conventions

- `proxy.list` uses Shadowrocket rule syntax: `DOMAIN-SUFFIX`, `DOMAIN-KEYWORD`, `DOMAIN`, `DST-PORT`, `IP-CIDR` (with `no-resolve` for IP rules)
- `KaminskiyVPN.v2raytun.routing.json` uses V2Ray syntax: `domain:`, `full:`, `keyword:`, and IP arrays
- Entries in `proxy.list` are grouped by service (AI, Meta, Twitter/X, Media, YouTube, Video, TikTok, Telegram, WhatsApp, etc.) with comment headers using `#`
- When adding a new proxied service, add entries to both `proxy.list` and `KaminskiyVPN.v2raytun.routing.json`
- The `.conf` files have `update-url` pointing to their own raw GitHub URL on `main` branch — changes take effect on clients after push
