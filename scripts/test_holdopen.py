#!/usr/bin/env python3
"""
Test different door control methods to hold door open
"""

import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('/etc/openhab/scripts/net2_config.json', 'r') as f:
    config = json.load(f)

BASE_URL = config['base_url']
USERNAME = config['username']
PASSWORD = config['password']
CLIENT_ID = config['client_id']
GRANT_TYPE = config.get('grant_type', 'password')

WIRELESS_DOOR_ID = 3962494

def get_token():
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

def test_control(token, door_id, relay_action, open_time=None, test_name=""):
    """Test door control with different parameters"""
    url = f"{BASE_URL}/commands/door/control"
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "DoorId": door_id,
        "RelayFunction": {
            "RelayId": "Relay1",
            "RelayAction": relay_action
        },
        "LedFlash": 3
    }
    
    if open_time is not None:
        data["RelayFunction"]["RelayOpenTime"] = open_time
    
    try:
        print(f"\n{test_name}")
        print(f"Payload: {json.dumps(data, indent=2)}")
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code in [200, 202, 204]
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 80)
    print("Testing Hold-Open Methods for Wireless Door")
    print("=" * 80)
    
    token = get_token()
    print(f"✓ Token obtained\n")
    
    # Test 1: Very long timeout (1 hour)
    test_control(token, WIRELESS_DOOR_ID, "TimedOpen", 3600000, 
                 "Test 1: TimedOpen with 1 hour (3600000 ms)")
    
    input("\nPress Enter to continue to Test 2...")
    
    # Test 2: Latch action (if supported)
    test_control(token, WIRELESS_DOOR_ID, "Latch", None,
                 "Test 2: Latch action (no timeout)")
    
    input("\nPress Enter to continue to Test 3...")
    
    # Test 3: Hold action (if supported)
    test_control(token, WIRELESS_DOOR_ID, "Hold", None,
                 "Test 3: Hold action (no timeout)")
    
    input("\nPress Enter to continue to Test 4...")
    
    # Test 4: Close/Lock to test closing
    test_control(token, WIRELESS_DOOR_ID, "Close", None,
                 "Test 4: Close action")
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
