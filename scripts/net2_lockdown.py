#!/usr/bin/env python3
"""
Net2 Lockdown Control

Simple script to enable/disable building lockdown via Net2 API.

Usage:
  python3 net2_lockdown.py enable   # Lock all doors
  python3 net2_lockdown.py disable  # Return to normal
  python3 net2_lockdown.py on       # Alias for enable
  python3 net2_lockdown.py off      # Alias for disable

API: POST /api/v1/commands/controlLockdown
"""

import json
import requests
import sys
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

def load_config():
    """Load API configuration"""
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    # Update to new API endpoint
    config['base_url'] = config['base_url'].replace('milestone.agesen.dk', 'net2.agesen.dk')
    if ':8443' not in config['base_url']:
        config['base_url'] = config['base_url'].replace('/api/v1', ':8443/api/v1')
    return config

def get_token(config):
    """Get authentication token"""
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    resp = requests.post(url, data=payload, verify=False, timeout=10)
    if resp.status_code != 200:
        print(f"ERROR: Authentication failed ({resp.status_code})")
        sys.exit(1)
    return resp.json()['access_token']

def control_lockdown(config, token, enable):
    """
    Enable or disable lockdown
    
    Args:
        enable: True to lock doors, False to unlock
    
    Returns:
        bool: Success status
    """
    url = f"{config['base_url']}/commands/controlLockdown"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {"lockdown": enable}
    
    try:
        resp = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        
        if resp.status_code in [200, 201, 204]:
            result = resp.json()
            action = "enabled" if enable else "disabled"
            print(f"✓ Lockdown {action}")
            
            # Check for errors in response
            if result.get('output', {}).get('errors'):
                print(f"  Errors: {result['output']['errors']}")
                return False
            
            return True
        else:
            print(f"ERROR: Request failed ({resp.status_code})")
            print(f"  Response: {resp.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Map commands
    if command in ['enable', 'on', 'lock']:
        enable = True
    elif command in ['disable', 'off', 'unlock']:
        enable = False
    else:
        print(f"ERROR: Unknown command '{command}'")
        print(__doc__)
        sys.exit(1)
    
    # Execute
    config = load_config()
    token = get_token(config)
    
    if control_lockdown(config, token, enable):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
