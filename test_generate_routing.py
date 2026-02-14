#!/usr/bin/env python3
"""Tests for generate_routing.py"""
import json
import os
import re
import tempfile

from generate_routing import parse_proxy_list, generate_routing_json


def test_port_range_with_en_dash():
    """Port ranges with en-dash (–) or other Unicode dashes must be converted to hyphen (-)"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.list', delete=False, encoding='utf-8') as f:
        # U+2013 EN DASH and U+200B ZERO-WIDTH SPACE — exactly what proxy.list has
        f.write('#Test\nDOMAIN-SUFFIX,example.com\n')
        f.write('DST-PORT,19302\u200b\u201319309,PROXY\n')
        f.name
    try:
        _, dst_ports = parse_proxy_list(f.name)
        port_string = ','.join(dst_ports)
        assert '19302-19309' in port_string, \
            f"Expected '19302-19309' but got '{port_string}' — en-dash was not converted to hyphen"
    finally:
        os.unlink(f.name)


def test_port_range_with_regular_hyphen():
    """Normal port ranges with ASCII hyphen must work correctly"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.list', delete=False, encoding='utf-8') as f:
        f.write('#Test\nDOMAIN-SUFFIX,example.com\n')
        f.write('DST-PORT,596-599,PROXY\n')
        f.name
    try:
        _, dst_ports = parse_proxy_list(f.name)
        assert '596-599' in dst_ports, f"Expected '596-599' in {dst_ports}"
    finally:
        os.unlink(f.name)


def test_port_string_format_valid():
    """All ports in generated JSON must match pattern: digits, commas, hyphens only"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.list', delete=False, encoding='utf-8') as f:
        f.write('#Test\nDOMAIN-SUFFIX,example.com\n')
        f.write('DST-PORT,3478,PROXY\n')
        f.write('DST-PORT,19302\u200b\u201319309,PROXY\n')  # en-dash + zero-width space
        f.write('DST-PORT,596-599,PROXY\n')
        f.name
    try:
        _, dst_ports = parse_proxy_list(f.name)
        port_string = ','.join(dst_ports)
        assert re.fullmatch(r'[\d,\-]+', port_string), \
            f"Port string contains invalid characters: '{port_string}'"
    finally:
        os.unlink(f.name)


def test_no_concatenated_port_numbers():
    """Port ranges must not produce concatenated numbers like '1930219309' instead of '19302-19309'"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.list', delete=False, encoding='utf-8') as f:
        f.write('#Test\nDOMAIN-SUFFIX,example.com\n')
        f.write('DST-PORT,19302\u200b\u201319309,PROXY\n')
        f.name
    try:
        _, dst_ports = parse_proxy_list(f.name)
        port_string = ','.join(dst_ports)
        assert '1930219309' not in port_string, \
            f"Port numbers were concatenated: '{port_string}' — dash character was stripped instead of normalized"
    finally:
        os.unlink(f.name)


def test_generated_json_port_ranges():
    """End-to-end: generated JSON must have correct port ranges"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.list', delete=False, encoding='utf-8') as f:
        f.write('# NAME: Test\n')
        f.write('#Test\nDOMAIN-SUFFIX,example.com\n')
        f.write('DST-PORT,3478,PROXY\n')
        f.write('DST-PORT,19302\u200b\u201319309,PROXY\n')
        tmp_list = f.name

    tmp_json = tmp_list + '.json'
    try:
        generate_routing_json(tmp_list, tmp_json)
        with open(tmp_json, 'r') as f:
            data = json.load(f)

        # Find the voice calls rule
        port_rules = [r for r in data['rules'] if 'port' in r]
        assert len(port_rules) == 1, f"Expected 1 port rule, got {len(port_rules)}"

        port_str = port_rules[0]['port']
        assert '19302-19309' in port_str, \
            f"Expected '19302-19309' in port string, got '{port_str}'"
        assert '1930219309' not in port_str, \
            f"Concatenated port number found in JSON: '{port_str}'"
    finally:
        os.unlink(tmp_list)
        if os.path.exists(tmp_json):
            os.unlink(tmp_json)


if __name__ == '__main__':
    test_port_range_with_en_dash()
    test_port_range_with_regular_hyphen()
    test_port_string_format_valid()
    test_no_concatenated_port_numbers()
    test_generated_json_port_ranges()
    print("All tests passed!")
