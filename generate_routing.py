#!/usr/bin/env python3
"""
Generate V2RayTun routing JSON from proxy.list
"""
import json
import uuid
import re
from typing import List, Dict, Any


def generate_uuid() -> str:
    """Generate a UUID in uppercase format"""
    return str(uuid.uuid4()).upper()


def parse_proxy_list(filename: str) -> Dict[str, Dict[str, List[str]]]:
    """Parse proxy.list and group rules by comment headers"""
    groups = {}
    current_group = None
    pending_group = None  # Group name waiting for first rule
    dst_ports = []

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and file header comments
            if not line or line.startswith('# NAME:') or line.startswith('# AUTHOR:') or \
               line.startswith('# REPO:') or line.startswith('# UPDATED:'):
                continue

            # DST-PORT rules go into separate collection (don't create groups)
            if line.startswith('DST-PORT,'):
                parts = line.split(',')
                if len(parts) >= 2:
                    port = parts[1]
                    # Normalize Unicode dashes (en-dash U+2013, em-dash U+2014, etc.) to ASCII hyphen
                    port = re.sub(r'[\u2010-\u2015\u2212\uFE58\uFE63\uFF0D]', '-', port)
                    # Remove remaining non-port characters (zero-width spaces, etc.)
                    port = re.sub(r'[^\d\-,]', '', port)
                    if port:
                        dst_ports.append(port)
                # DST-PORT doesn't activate pending group
                pending_group = None
                continue

            # Group header comment
            if line.startswith('#'):
                # Extract group name (remove leading # and strip)
                group_name = line[1:].strip()

                # Skip inline comments that are not group headers:
                # - URLs (https://, http://)
                # - Commented-out rules (# DST-PORT, # TCP)
                # - Empty comments
                if not group_name or \
                   any(group_name.startswith(x) for x in ['https://', 'http://']) or \
                   any(group_name.startswith(x) for x in ['DST-PORT', 'TCP ', 'RTP']):
                    continue

                # Mark this as a pending group (will be activated only if followed by DOMAIN/IP rules)
                pending_group = group_name
                continue

            # Domain rules
            if line.startswith('DOMAIN'):
                # Activate pending group if any
                if pending_group:
                    current_group = pending_group
                    if current_group not in groups:
                        groups[current_group] = {
                            'domains': [],
                            'ips': [],
                        }
                    pending_group = None

                if current_group:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        rule_type = parts[0]
                        domain = parts[1].strip()

                        if rule_type == 'DOMAIN-SUFFIX':
                            groups[current_group]['domains'].append(f'domain:{domain}')
                        elif rule_type == 'DOMAIN':
                            groups[current_group]['domains'].append(f'full:{domain}')
                        elif rule_type == 'DOMAIN-KEYWORD':
                            groups[current_group]['domains'].append(f'keyword:{domain}')

            # IP-CIDR rules
            elif line.startswith('IP-CIDR,'):
                # Activate pending group if any
                if pending_group:
                    current_group = pending_group
                    if current_group not in groups:
                        groups[current_group] = {
                            'domains': [],
                            'ips': [],
                        }
                    pending_group = None

                if current_group:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        cidr = parts[1].strip()
                        groups[current_group]['ips'].append(cidr)

    return groups, dst_ports


def create_fixed_rules() -> List[Dict[str, Any]]:
    """Create fixed rules that are not generated from proxy.list"""
    return [
        {
            "__name__": "Прямые домены",
            "id": generate_uuid(),
            "type": "field",
            "domain": [
                "full:captive.apple.com",
                "domain:kaspersky.com",
                "domain:avp.ru",
                "regexp:^.*\\.local$",
                "full:localhost"
            ],
            "ip": [
                "geoip:private",
                "62.128.100.0/23",
                "82.202.184.0/23",
                "88.217.237.0/24",
                "91.103.64.0/21",
                "119.254.74.0/24",
                "212.5.89.0/24",
                "212.5.110.0/24",
                "200.61.184.40/32",
                "35.243.206.127/32",
                "51.250.52.72/29",
                "51.250.52.136/29",
                "51.250.92.73/32",
                "84.201.174.229/32",
                "158.160.10.133/32",
                "217.28.236.8/29",
                "217.28.224.24/29",
                "158.160.63.96/29",
                "151.192.48.0/24",
                "202.163.6.0/24",
                "72.163.1.80/32",
                "82.202.191.166/32",
                "185.54.220.72/32",
                "34.38.164.204/32",
                "51.250.32.16/32",
                "51.250.33.143/32",
                "188.227.72.4/32",
                "46.8.206.35/32",
                "195.122.169.56/32",
                "195.128.246.0/23",
                "94.158.243.0/25",
                "185.85.12.0/24",
                "185.85.14.0/24",
                "77.74.176.0/23",
                "77.74.179.128/25",
                "77.74.180.0/24",
                "77.74.181.0/24",
                "77.74.182.128/25",
                "93.159.227.0/24",
                "93.159.229.128/25",
                "93.159.230.0/23",
                "104.26.0.63/32",
                "104.26.1.63/32",
                "172.67.74.254/32",
                "79.133.168.0/22",
                "82.202.190.177/32"
            ],
            "outboundTag": "direct"
        },
        {
            "__name__": "Прямые RU",
            "id": generate_uuid(),
            "type": "field",
            "ip": [
                "geoip:ru"
            ],
            "outboundTag": "direct"
        }
    ]


def create_default_rule() -> Dict[str, Any]:
    """Create default catch-all rule"""
    return {
        "__name__": "Default",
        "id": generate_uuid(),
        "type": "field",
        "network": ["tcp"],
        "outboundTag": "direct"
    }


def create_voice_calls_rule(dst_ports: List[str]) -> Dict[str, Any]:
    """Create voice/video calls rule from DST-PORT entries"""
    # Join all ports into single string
    port_string = ','.join(dst_ports)

    return {
        "__name__": "Голосовые и видеозвонки",
        "id": generate_uuid(),
        "type": "field",
        "port": port_string,
        "outboundTag": "proxy"
    }


def generate_routing_json(proxy_list_path: str, output_path: str):
    """Generate V2RayTun routing JSON from proxy.list"""

    # Parse proxy.list
    groups, dst_ports = parse_proxy_list(proxy_list_path)

    # Start with fixed rules
    rules = create_fixed_rules()

    # Add rules for each group from proxy.list
    for group_name, group_data in groups.items():
        rule = {
            "__name__": group_name,
            "id": generate_uuid(),
            "type": "field",
            "outboundTag": "proxy"
        }

        # Add domain array if present
        if group_data['domains']:
            rule['domain'] = group_data['domains']

        # Add ip array if present
        if group_data['ips']:
            rule['ip'] = group_data['ips']

        rules.append(rule)

    # Add voice/video calls rule if there are DST-PORT entries
    if dst_ports:
        rules.append(create_voice_calls_rule(dst_ports))

    # Add default rule at the end
    rules.append(create_default_rule())

    # Create final JSON structure
    routing = {
        "domainStrategy": "AsIs",
        "id": generate_uuid(),
        "balancers": [],
        "domainMatcher": "hybrid",
        "name": "Ruleset",
        "rules": rules
    }

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(routing, f, indent=2, ensure_ascii=False)

    print(f"✓ Generated {output_path}")
    print(f"  Total rules: {len(rules)}")
    print(f"  Groups from proxy.list: {len(groups)}")
    print(f"  DST-PORT entries: {len(dst_ports)}")


if __name__ == '__main__':
    generate_routing_json('proxy.list', 'KaminskiyVPN.v2raytun.routing.json')
