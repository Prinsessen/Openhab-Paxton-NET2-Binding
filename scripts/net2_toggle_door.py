#!/usr/bin/env python3

"""
Net2 door control script with status checking and explicit open/close commands.
Usage:
  python3 net2_toggle_door.py <door_id> [open|close|status|toggle]
  
Examples:
  python3 net2_toggle_door.py 6203980 open    # Hold door open
  python3 net2_toggle_door.py 6203980 close   # Close door
  python3 net2_toggle_door.py 6203980 status  # Check door status
  python3 net2_toggle_door.py 6203980 toggle  # Toggle based on state (default)
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

def hold_door_open(config, token, door_id):
    """Hold door open until closed"""
    url = f"{config['base_url']}/commands/door/holdopen"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {"DoorId": int(door_id)}
    resp = requests.post(url, headers=headers, json=data, verify=False)
    print(f"DEBUG holdopen: {resp.status_code} - {resp.text}")
    return resp.status_code == 200

def close_door(config, token, door_id):
    """Close door - use close endpoint"""
    url = f"{config['base_url']}/commands/door/close"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {"DoorId": int(door_id)}
    resp = requests.post(url, headers=headers, json=data, verify=False)
    print(f"DEBUG close: {resp.status_code} - {resp.text}")
    return resp.status_code == 200

def get_door_status(config, token, door_id):
    """Get current door status from API"""
    url = f"{config['base_url']}/doors/status"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        try:
            doors = resp.json()
            for door in doors:
                if door.get('id') == int(door_id):
                    return door
            return None
        except:
            return None
    return None

def list_all_doors(config, token):
    """List all available doors from API"""
    url = f"{config['base_url']}/doors"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        try:
            return resp.json()
        except:
            return None
    return None

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
    config = load_config()
    token = get_token(config)
    
    # Determine door_id and action
    if len(sys.argv) >= 3:
        # Full command line: door_id and action provided
        door_id = sys.argv[1]
        action = sys.argv[2].lower()
    elif len(sys.argv) == 2:
        # Only door_id provided, prompt for action
        door_id = sys.argv[1]
        action = None
    else:
        # No arguments, list doors and prompt for everything
        print("Fetching available doors...")
        doors = list_all_doors(config, token)
        
        if not doors or len(doors) == 0:
            print("No doors found or unable to retrieve door list")
            sys.exit(1)
        
        # Debug: print first door structure
        if len(doors) > 0:
            print(f"\nDEBUG - First door structure: {json.dumps(doors[0], indent=2)}")
        
        print("\nAvailable doors:")
        for idx, door in enumerate(doors, 1):
            # Try both uppercase and lowercase field names
            door_name = door.get('name') or door.get('Name') or 'Unknown'
            door_id_val = door.get('id') or door.get('Id') or 'N/A'
            print(f"{idx}. {door_name} (ID: {door_id_val})")
        
        choice = input("\nSelect door number (or press Enter to cancel): ").strip()
        if not choice or not choice.isdigit():
            print("Cancelled")
            sys.exit(0)
        
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(doors):
            print("Invalid selection")
            sys.exit(1)
        
        selected_door = doors[choice_idx]
        door_id = str(selected_door.get('id') or selected_door.get('Id'))
        action = None
    
    # If action not provided, check status and prompt
    if action is None:
        print(f"\nChecking current status for door {door_id}...")
        status = get_door_status(config, token, door_id)
        
        if status:
            door_state = status.get('doorStatus', {})
            is_held_open = door_state.get('isHeldOpen', False)
            print(f"Current state: {'HELD OPEN' if is_held_open else 'CLOSED'}")
        else:
            print("Current state: Unknown")
        
        print("\nWhat would you like to do?")
        print("1. Open (hold door open)")
        print("2. Close")
        print("3. Status")
        print("4. Cancel")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            action = "open"
        elif choice == "2":
            action = "close"
        elif choice == "3":
            action = "status"
        else:
            print("Cancelled")
            sys.exit(0)
    
    # Handle status command
    if action == "status":
        print(f"Checking status for door {door_id}...")
        status = get_door_status(config, token, door_id)
        if status:
            print(f"Door Status: {json.dumps(status, indent=2)}")
        else:
            print("Could not retrieve door status")
        sys.exit(0)
    
    # Handle open command
    if action == "open":
        print(f"Holding door {door_id} open...")
        success = hold_door_open(config, token, door_id)
        if success:
            set_door_state(door_id, True)
            print("✓ Door held open (until closed)")
        else:
            print("✗ Failed to open door")
        sys.exit(0)
    
    # Handle close command
    if action == "close":
        print(f"Closing door {door_id}...")
        success = close_door(config, token, door_id)
        if success:
            set_door_state(door_id, False)
            print("✓ Door closed")
        else:
            print("✗ Failed to close door")
        sys.exit(0)
    
    print(f"Unknown action: {action}")
    print("Valid actions: open, close, status")
    sys.exit(1)

if __name__ == "__main__":
    main()
