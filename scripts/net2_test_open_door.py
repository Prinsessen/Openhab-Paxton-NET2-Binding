#!/usr/bin/env python3

"""
Test script to open a door using the Net2 API, based on net2.py logic.
This script does NOT modify net2.py and is self-contained.
"""

import json
import requests
import sys
import os

# Load config from net2_config.json (same as net2.py)
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception as e:
    print(f"ERROR: Failed to load config: {e}")
    sys.exit(1)

# Set your test door parameters here
DOOR_ID = config.get('test_door_id') or input('Enter Door ID: ')
RELAY_ID = "Relay1"
RELAY_ACTION = "TimedOpen"
RELAY_OPEN_TIME = 8000  # ms (8 seconds)
LED_FLASH = 3

# Authenticate
Paxton_auth = f"{config['base_url']}/authorization/tokens"
payload_auth = {
    'username': config['username'],
    'password': config['password'],
    'grant_type': config['grant_type'],
    'client_id': config['client_id']
}

resp_auth = requests.post(Paxton_auth, data=payload_auth)
if resp_auth.status_code != 200:
    print("Authentication failed:", resp_auth.text)
    sys.exit(1)
token = resp_auth.json().get("access_token")

# Open door
Paxton_open_door = f"{config['base_url']}/commands/door/control"
data = {
    "DoorId": DOOR_ID,
    "RelayFunction": {
        "RelayId": RELAY_ID,
        "RelayAction": RELAY_ACTION,
        "RelayOpenTime": RELAY_OPEN_TIME
    },
    "LedFlash": LED_FLASH
}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {token}"
}

resp_door = requests.post(Paxton_open_door, headers=headers, data=json.dumps(data))
print("\n--- RAW RESPONSE CONTENT ---")
print(resp_door.content)
print("\n--- RESPONSE OBJECT ---")
print(resp_door)
print("\n--- RESPONSE TEXT ---")
print(resp_door.text)
