#!/usr/bin/env python3
"""
net2_door_control.py

Control Paxton Net2 doors via API: keep a door open or close it.
Usage:
  python3 net2_door_control.py --door "DOOR_NAME" --action open
  python3 net2_door_control.py --door "DOOR_NAME" --action close
  python3 net2_door_control.py            # lists all available doors

Requires net2_config.json in the same directory (same as your daemon).
"""
import sys
import os
import json
import requests
import argparse
from datetime import datetime

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def authenticate(config):
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    auth_endpoint = f"{config['base_url']}/authorization/tokens"
    response = requests.post(auth_endpoint, data=payload, timeout=30)
    if response.status_code != 200:
        print(f"ERROR: Authentication failed with status {response.status_code}")
        sys.exit(1)
    return response.json().get("access_token")

def get_doors(config, token):
    headers = {"Authorization": f"Bearer {token}"}
    doors_endpoint = f"{config['base_url']}/doors"
    response = requests.get(doors_endpoint, headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"ERROR: Failed to retrieve doors (status {response.status_code})")
        sys.exit(1)
    doors = response.json()
    # Try to support both list and dict API responses
    if isinstance(doors, dict):
        return doors.get('doors', doors.get('data', doors.get('results', [])))
    return doors

def find_door(doors, name):
    # Match by name (case-insensitive, partial allowed)
    name = name.lower()
    for door in doors:
        if name in door.get('name', '').lower():
            return door
    return None

def set_door_state(config, token, door_id, keep_open):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # The actual API endpoint and payload may differ; adjust as needed for your Net2 API
    endpoint = f"{config['base_url']}/doors/{door_id}/commands"
    payload = {"command": "keepOpen" if keep_open else "close"}
    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        print(f"Success: Door command sent.")
    else:
        print(f"ERROR: Failed to send command (status {response.status_code}): {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Control Paxton Net2 doors via API.")
    parser.add_argument('--door', type=str, help='Door name (partial match allowed)')
    parser.add_argument('--action', type=str, choices=['open', 'close'], help='Action: open (keep open) or close')
    args = parser.parse_args()

    config = load_config()
    token = authenticate(config)
    doors = get_doors(config, token)

    if not args.door:
        print("Available doors:")
        for door in doors:
            print(f"- {door.get('name', 'Unknown')} (ID: {door.get('id', 'N/A')})")
        print("\nTo control a door: python3 net2_door_control.py --door \"DOOR_NAME\" --action open|close")
        sys.exit(0)

    door = find_door(doors, args.door)
    if not door:
        print(f"ERROR: Door '{args.door}' not found. Run without arguments to list doors.")
        sys.exit(1)

    if not args.action:
        print("ERROR: --action open|close is required when specifying a door.")
        sys.exit(1)

    print(f"Selected door: {door.get('name')} (ID: {door.get('id')})")
    set_door_state(config, token, door.get('id'), keep_open=(args.action == 'open'))

if __name__ == "__main__":
    main()
