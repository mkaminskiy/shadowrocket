---
name: update-routing
description: Add, remove or modify VPN client routing rules in proxy.list. Use when user asks to route a domain/IP/port through VPN or change routing configuration.
argument-hint: [description of routing change]
---

# Update Routing Rules

## Source of truth

Only edit `proxy.list`. The JSON config is generated automatically by `generate_routing.py` — NEVER edit it manually.

## proxy.list format

- Groups start with `#GroupName` (no space after `#`)
- `DOMAIN-SUFFIX,example.com` — domain and all subdomains
- `DOMAIN,api.example.com` — exact domain match
- `DOMAIN-KEYWORD,foo` — domains containing the keyword
- `IP-CIDR,x.x.x.x/y,no-resolve` — IP block
- `DST-PORT,3478,PROXY` — destination port

## AND-logic in V2Ray/xray-core

If a group contains BOTH domain AND IP-CIDR entries, they end up in a single rule in the generated JSON. In xray-core, `domain` + `ip` in one rule means AND (must match both). If you need OR semantics (match domain OR IP), put them in **separate groups**.

## Workflow after editing proxy.list

1. **Generate JSON:** `python3 generate_routing.py` — review the output
2. **Run tests:** `python3 -m pytest test_generate_routing.py`
3. **Commit and push** — GitHub Actions will also regenerate the JSON
4. **Update servers:**
   ```bash
   ssh vpn.kaminskiy.me '/opt/vpn/update-routing.sh -v'
   ssh vpn-de.kaminskiy.me '/opt/vpn/update-routing.sh -v'
   ```
5. **Verify:** after push, wait ~5 min (cron pulls updates) or manually run update-routing.sh on servers
