#!/usr/bin/env python3

"""
Deep dive into Net2 door and area commands
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

def main():
    config = load_config()
    token = get_token(config)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Get door status (full details)
    print("=== DOOR STATUS (Detailed) ===")
    resp = requests.get(f"{config['base_url']}/doors/status", headers=headers, verify=False)
    if resp.status_code == 200:
        doors = resp.json()
        print(f"Found {len(doors)} door statuses\n")
        if doors:
            print("First door full structure:")
            print(json.dumps(doors[0], indent=2))
            
            # Look for lockdown/secure fields
            print("\n=== Looking for lock/secure/mode fields ===")
            for key in doors[0].keys():
                print(f"  {key}: {doors[0][key]}")
    
    # Get access levels details
    print("\n\n=== ACCESS LEVELS (Full) ===")
    resp = requests.get(f"{config['base_url']}/accesslevels", headers=headers, verify=False)
    if resp.status_code == 200:
        levels = resp.json()
        print(f"Found {len(levels)} access levels")
        if levels:
            print("\nAccess levels:")
            for level in levels:
                print(f"  ID: {level['id']}, Name: {level['name']}")
    
    # Try sending lockdown commands to specific doors
    print("\n\n=== TESTING DOOR COMMANDS ===")
    
    # Get first door ID
    resp = requests.get(f"{config['base_url']}/doors", headers=headers, verify=False)
    if resp.status_code == 200:
        doors = resp.json()
        if doors:
            test_door_id = doors[0]['id']
            print(f"Using door ID: {test_door_id} ({doors[0]['name']})\n")
            
            # Try different command patterns
            commands = [
                ("lockdown", {"DoorId": test_door_id}),
                ("secure", {"DoorId": test_door_id}),
                ("lock", {"DoorId": test_door_id}),
                ("holdclosed", {"DoorId": test_door_id}),
                ("mode", {"DoorId": test_door_id, "Mode": "lockdown"}),
                ("mode", {"DoorId": test_door_id, "Mode": "secure"}),
            ]
            
            for cmd, payload in commands:
                url = f"{config['base_url']}/commands/door/{cmd}"
                try:
                    resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=5)
                    if resp.status_code in [200, 201, 204]:
                        print(f"✓ SUCCESS: /commands/door/{cmd}")
                        print(f"  Response: {resp.text}")
                    elif resp.status_code != 404:
                        print(f"? /commands/door/{cmd} - Status: {resp.status_code}")
                        print(f"  Response: {resp.text[:100]}")
                except Exception as e:
                    pass
    
    # Try OPTIONS request to see available methods
    print("\n\n=== API OPTIONS (What methods are supported?) ===")
    test_endpoints = [
        "/doors",
        "/commands/door/control",
        "/areas",
    ]
    
    for endpoint in test_endpoints:
        url = f"{config['base_url']}{endpoint}"
        try:
            resp = requests.options(url, headers=headers, verify=False, timeout=5)
            if 'allow' in resp.headers:
                print(f"{endpoint}:")
                print(f"  Allowed: {resp.headers['allow']}")
        except:
            pass

if __name__ == '__main__':
    main()
