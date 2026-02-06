#!/usr/bin/env python3
"""
Test script for investigating wireless door (Værksted Dør) API behavior
Door ID: 03962494 (wireless unit)
Compare with working door: 6203980 (wired Net2 Plus - Kirkegade)
"""

import json
import requests
import urllib3
from datetime import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration
with open('/etc/openhab/scripts/net2_config.json', 'r') as f:
    config = json.load(f)

BASE_URL = config['base_url']
USERNAME = config['username']
PASSWORD = config['password']
CLIENT_ID = config['client_id']
GRANT_TYPE = config.get('grant_type', 'password')

# Door IDs to test
WIRED_DOOR_ID = 6203980      # Working door (Kirkegade - Net2 Plus)
WIRELESS_DOOR_ID = 3962494   # Wireless door (Værksted)

def get_token():
    """Get authentication token"""
    url = f"{BASE_URL}/authorization/tokens"
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": GRANT_TYPE,
        "client_id": CLIENT_ID
    }
    
    response = requests.post(url, data=data, verify=False, timeout=10)
    response.raise_for_status()
    return response.json()['access_token']

def get_door_info(token, door_id):
    """Get detailed door information"""
    url = f"{BASE_URL}/doors/{door_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": getattr(response, 'status_code', None)}

def get_door_state(token, door_id):
    """Get door state/status"""
    url = f"{BASE_URL}/doors/{door_id}/state"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": getattr(response, 'status_code', None)}

def control_door_standard(token, door_id):
    """Standard door control method (used by binding for wired doors)"""
    url = f"{BASE_URL}/commands/door/control"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "DoorId": door_id,
        "RelayFunction": {
            "RelayId": "Relay1",
            "RelayAction": "TimedOpen",
            "RelayOpenTime": 5000  # 5 seconds in milliseconds
        },
        "LedFlash": 3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        return {
            "method": "POST /commands/door/control",
            "status_code": response.status_code,
            "response": response.text,
            "success": response.status_code in [200, 202, 204]
        }
    except Exception as e:
        return {"method": "POST /commands/door/control", "error": str(e)}

def control_door_unlock(token, door_id):
    """Alternative method: /unlock endpoint"""
    url = f"{BASE_URL}/doors/{door_id}/unlock"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(url, headers=headers, verify=False, timeout=10)
        return {
            "method": "POST /doors/{id}/unlock",
            "status_code": response.status_code,
            "response": response.text,
            "success": response.status_code in [200, 202, 204]
        }
    except Exception as e:
        return {"method": "POST /doors/{id}/unlock", "error": str(e)}

def control_door_commands(token, door_id, command_type):
    """Alternative method: /commands endpoint"""
    url = f"{BASE_URL}/doors/{door_id}/commands"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"command": command_type}  # Try different command types
    
    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        return {
            "method": f"POST /doors/{{id}}/commands (command={command_type})",
            "status_code": response.status_code,
            "response": response.text,
            "success": response.status_code in [200, 202, 204]
        }
    except Exception as e:
        return {"method": f"POST /doors/{{id}}/commands (command={command_type})", "error": str(e)}

def list_all_doors(token):
    """List all doors in the system"""
    url = f"{BASE_URL}/doors"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("Net2 Wireless Door Investigation")
    print(f"Testing at: {datetime.now()}")
    print("=" * 80)
    
    # Get authentication token
    print("\n[1] Getting authentication token...")
    try:
        token = get_token()
        print(f"✓ Token obtained: {token[:20]}...")
    except Exception as e:
        print(f"✗ Failed to get token: {e}")
        return
    
    # List all doors
    print("\n[2] Listing all doors in system...")
    doors = list_all_doors(token)
    if "error" in doors:
        print(f"✗ Error: {doors['error']}")
    else:
        print(f"✓ Found {len(doors)} doors")
        for door in doors:
            door_type = "WIRELESS" if door.get('id') == WIRELESS_DOOR_ID else "WIRED" if door.get('id') == WIRED_DOOR_ID else "OTHER"
            print(f"  - ID: {door.get('id')} | Name: {door.get('name')} | Type: {door_type}")
    
    # Test both doors
    for door_id, door_name in [(WIRED_DOOR_ID, "Wired Door (Kirkegade)"), 
                                (WIRELESS_DOOR_ID, "Wireless Door (Værksted)")]:
        print(f"\n{'=' * 80}")
        print(f"Testing: {door_name} (ID: {door_id})")
        print('=' * 80)
        
        # Get door information
        print(f"\n[3] Getting door info for {door_id}...")
        info = get_door_info(token, door_id)
        if "error" in info:
            print(f"✗ Error: {info['error']} (Status: {info.get('status_code')})")
        else:
            print(f"✓ Door info retrieved:")
            print(json.dumps(info, indent=2))
        
        # Get door state
        print(f"\n[4] Getting door state for {door_id}...")
        state = get_door_state(token, door_id)
        if "error" in state:
            print(f"✗ Error: {state['error']} (Status: {state.get('status_code')})")
        else:
            print(f"✓ Door state retrieved:")
            print(json.dumps(state, indent=2))
        
        # Test control methods
        print(f"\n[5] Testing control methods for {door_id}...")
        
        # Method 1: Standard control (used by binding)
        print("\n  Method 1: POST /commands/door/control")
        result = control_door_standard(token, door_id)
        print(f"  Result: {json.dumps(result, indent=4)}")
        
        # Method 2: Unlock endpoint
        print("\n  Method 2: POST /doors/{id}/unlock")
        result = control_door_unlock(token, door_id)
        print(f"  Result: {json.dumps(result, indent=4)}")
        
        # Method 3: Commands endpoint with different command types
        for cmd in ["open", "unlock", "1", "momentary"]:
            print(f"\n  Method 3: POST /doors/{{id}}/commands (command='{cmd}')")
            result = control_door_commands(token, door_id, cmd)
            print(f"  Result: {json.dumps(result, indent=4)}")
        
        print("\n" + "-" * 80)
    
    print("\n" + "=" * 80)
    print("Investigation complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
