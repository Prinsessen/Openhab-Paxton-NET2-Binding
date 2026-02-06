#!/usr/bin/env python3
"""
Test script for wireless door handle control
Door Handle ID: 02850160
"""

import json
import requests
import urllib3

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

DOOR_HANDLE_ID = 2850160  # Note: Leading zero removed for integer

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

def test_door_control(token, door_id, duration_ms=5000):
    """Test door control with TimedOpen"""
    url = f"{BASE_URL}/commands/door/control"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "DoorId": door_id,
        "RelayFunction": {
            "RelayId": "Relay1",
            "RelayAction": "TimedOpen",
            "RelayOpenTime": duration_ms
        },
        "LedFlash": 3
    }
    
    print(f"Testing door handle ID: {door_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_door_holdopen(token, door_id):
    """Test door hold open (toggle unlock)"""
    url = f"{BASE_URL}/commands/door/holdopen"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"DoorId": door_id}
    
    print(f"Testing UNLOCK (holdopen) for handle ID: {door_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_door_close(token, door_id):
    """Test door close (toggle lock)"""
    url = f"{BASE_URL}/commands/door/close"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"DoorId": door_id}
    
    print(f"Testing LOCK (close) for handle ID: {door_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_door_info(token, door_id):
    """Get door information"""
    url = f"{BASE_URL}/doors/{door_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Door info status: {response.status_code}")
        if response.status_code == 200:
            print(f"Door info: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error getting door info: {e}")

def main():
    print("=" * 80)
    print("Testing Wireless Door Handle (Toggle Lock)")
    print("=" * 80)
    
    # Get token
    print("\n1. Getting authentication token...")
    try:
        token = get_token()
        print("✓ Token obtained")
    except Exception as e:
        print(f"✗ Failed to get token: {e}")
        return
    
    # Get door info
    print(f"\n2. Getting door handle info (ID: {DOOR_HANDLE_ID})...")
    get_door_info(token, DOOR_HANDLE_ID)
    
    # Test UNLOCK
    print(f"\n3. Testing UNLOCK (holdopen)...")
    input("Press Enter to send UNLOCK command...")
    test_door_holdopen(token, DOOR_HANDLE_ID)
    
    print("\nWait and check if handle unlocked...")
    input("Press Enter when ready to test LOCK...")
    
    # Test LOCK
    print(f"\n4. Testing LOCK (close)...")
    test_door_close(token, DOOR_HANDLE_ID)
    
    print("\nWait and check if handle locked...")
    input("Press Enter to continue...")
    
    # Test with control endpoint
    print(f"\n5. Testing with /control endpoint (TimedOpen 5 seconds)...")
    test_door_control(token, DOOR_HANDLE_ID, 5000)
    
    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
