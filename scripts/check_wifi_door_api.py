#!/usr/bin/env python3
"""
Check if WiFi door 5598430 is accessible via Net2 REST API
"""

import requests
import json
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Load config
with open('net2_config.json') as f:
    config = json.load(f)

BASE_URL = config['base_url']
USERNAME = config['username']
PASSWORD = config['password']
CLIENT_ID = config['client_id']

WIFI_DOOR_ID = 5598430

# Authenticate
print("Authenticating...")
auth_response = requests.post(
    f"{BASE_URL}/authorization/tokens",
    data={
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password",
        "client_id": CLIENT_ID
    },
    verify=False
)

if auth_response.status_code != 200:
    print(f"❌ Authentication failed: {auth_response.status_code}")
    print(auth_response.text)
    exit(1)

token = auth_response.json()['access_token']
print(f"✅ Authenticated\n")

headers = {"Authorization": f"Bearer {token}"}

# Get all doors
print("Fetching all doors from API...")
doors_response = requests.get(f"{BASE_URL}/doors", headers=headers, verify=False)

if doors_response.status_code == 200:
    doors = doors_response.json()
    print(f"Total doors in system: {len(doors)}\n")
    
    # Look for WiFi door
    wifi_door = None
    for door in doors:
        door_id = door.get('id') or door.get('doorId') or door.get('address')
        if door_id == WIFI_DOOR_ID:
            wifi_door = door
            break
    
    if wifi_door:
        print(f"⭐ FOUND WiFi Door {WIFI_DOOR_ID}:")
        print(json.dumps(wifi_door, indent=2))
    else:
        print(f"❌ WiFi Door {WIFI_DOOR_ID} NOT FOUND in API door list\n")
        print("Available door IDs:")
        for door in doors[:10]:  # Show first 10
            door_id = door.get('id') or door.get('doorId') or door.get('address')
            name = door.get('name', 'Unknown')
            print(f"  - {door_id}: {name}")
else:
    print(f"❌ Failed to get doors: {doors_response.status_code}")
    print(doors_response.text)

# Try to get WiFi door status directly
print(f"\n\nTrying direct status fetch for door {WIFI_DOOR_ID}...")
status_response = requests.get(
    f"{BASE_URL}/doors/{WIFI_DOOR_ID}",
    headers=headers,
    verify=False
)

if status_response.status_code == 200:
    print(f"✅ WiFi Door {WIFI_DOOR_ID} status:")
    print(json.dumps(status_response.json(), indent=2))
else:
    print(f"❌ Failed to get WiFi door status: {status_response.status_code}")
    print(status_response.text)
