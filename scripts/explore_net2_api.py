#!/usr/bin/env python3

"""
Explore Net2 API structure to find lockdown or area-level controls
"""

import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = '/etc/openhab/scripts/net2_config.json'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        if 'milestone' in config['base_url']:
            config['base_url'] = config['base_url'].replace('milestone', 'net2')
        return config

def get_token(config):
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    resp = requests.post(url, data=payload, verify=False)
    return resp.json()['access_token']

def explore_api(config, token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Get doors list
    print("=== DOORS ===")
    resp = requests.get(f"{config['base_url']}/doors", headers=headers, verify=False)
    if resp.status_code == 200:
        doors = resp.json()
        print(f"Found {len(doors)} doors")
        if doors:
            print("\nFirst door structure:")
            print(json.dumps(doors[0], indent=2))
            
            # Check if doors have lockdown properties
            print("\n=== Checking for lockdown-related properties ===")
            for key in doors[0].keys():
                if any(word in key.lower() for word in ['lock', 'secure', 'area', 'mode', 'status', 'state']):
                    print(f"  {key}: {doors[0][key]}")
    
    # Try area-related endpoints
    print("\n\n=== AREAS / ZONES ===")
    area_endpoints = [
        "/areas",
        "/zones",
        "/accesslevels",
        "/departments",
        "/sites",
    ]
    
    for endpoint in area_endpoints:
        url = f"{config['base_url']}{endpoint}"
        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                print(f"\n✓ {endpoint}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"  Count: {len(data)}")
                    print(f"  Sample keys: {list(data[0].keys())}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
        except:
            pass
    
    # Try command endpoints with different verbs
    print("\n\n=== COMMAND ENDPOINTS ===")
    command_patterns = [
        "/commands/area/secure",
        "/commands/area/lockdown",
        "/commands/system/lockdown",
        "/commands/site/lockdown",
        "/commands/building/secure",
        "/commands/secure/enable",
        "/commands/emergency/lockdown",
    ]
    
    for endpoint in command_patterns:
        url = f"{config['base_url']}{endpoint}"
        try:
            # Try POST with empty body
            resp = requests.post(url, headers=headers, json={}, verify=False, timeout=5)
            if resp.status_code != 404:
                print(f"  {endpoint} - Status: {resp.status_code}")
                if resp.text:
                    print(f"    Response: {resp.text[:100]}")
        except:
            pass
    
    # Try GET on commands to see available commands
    print("\n\n=== AVAILABLE COMMANDS ===")
    commands_list = [
        "/commands",
        "/commands/door",
        "/commands/area",
        "/commands/system",
    ]
    
    for endpoint in commands_list:
        url = f"{config['base_url']}{endpoint}"
        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=5)
            if resp.status_code == 200:
                print(f"\n✓ {endpoint}")
                print(f"  Response: {resp.text[:200]}")
        except:
            pass

def main():
    config = load_config()
    token = get_token(config)
    print(f"✓ Authenticated\n")
    explore_api(config, token)

if __name__ == '__main__':
    main()
