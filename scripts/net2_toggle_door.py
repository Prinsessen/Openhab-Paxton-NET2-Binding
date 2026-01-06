#!/usr/bin/env python3

"""
Simple Net2 door control script - keeps door open until run again.
First run: Opens and keeps door open (1 hour)
Second run: Closes door (resets to normal operation)
"""

import json
import requests
import sys
import os
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.door_state.json')

def load_config():
    """Load API configuration"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_token(config):
    """Get authentication token"""
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    resp = requests.post(url, data=payload, verify=False)
    if resp.status_code != 200:
        print(f"Auth failed: {resp.status_code}")
        sys.exit(1)
    return resp.json()['access_token']

def control_door(config, token, door_id, open_time_ms):
    """Send door control command"""
    url = f"{config['base_url']}/commands/door/control"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "DoorId": int(door_id),
        "RelayFunction": {
            "RelayId": "Relay1",
            "RelayAction": "TimedOpen",
            "RelayOpenTime": open_time_ms
        },
        "LedFlash": 3
    }
    resp = requests.post(url, headers=headers, json=data, verify=False)
    return resp.status_code == 200

def get_door_state(door_id):
    """Check if door is currently kept open"""
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        return state.get(str(door_id), False)
    except:
        return False

def set_door_state(door_id, is_open):
    """Save door state"""
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        except:
            pass
    state[str(door_id)] = is_open
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 net2_toggle_door.py <door_id>")
        print("Example: python3 net2_toggle_door.py 6612642")
        sys.exit(1)
    
    door_id = sys.argv[1]
    config = load_config()
    token = get_token(config)
    
    is_currently_open = get_door_state(door_id)
    
    if is_currently_open:
        # Close door (use 0ms to close/lock)
        print(f"Closing door {door_id}...")
        success = control_door(config, token, door_id, 0)  # 0ms = close/lock
        if success:
            set_door_state(door_id, False)
            print("✓ Door closed")
        else:
            print("✗ Failed to close door")
    else:
        # Open door for 10 seconds
        print(f"Opening door {door_id} for 10 seconds...")
        success = control_door(config, token, door_id, 10000)  # 10 seconds
        if success:
            set_door_state(door_id, True)
            print("✓ Door opened (10 seconds)")
        else:
            print("✗ Failed to open door")

if __name__ == "__main__":
    main()
