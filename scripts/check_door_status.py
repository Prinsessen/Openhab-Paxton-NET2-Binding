#!/usr/bin/env python3
"""
Check door lock status via Net2 REST API

Usage:
    cd /etc/openhab/scripts
    source /etc/openhab/.venv/bin/activate
    python3 check_door_status.py --door 5598430
"""

import json
import requests
import argparse
import sys

# Load configuration
with open('net2_config.json') as f:
    config = json.load(f)

parser = argparse.ArgumentParser(description='Check Net2 door status')
parser.add_argument("--door", required=True, help="Door ID to check")
args = parser.parse_args()

# Authenticate
auth_url = f"{config['base_url']}/authorization/tokens"
payload_auth = {
    'username': config['username'],
    'password': config['password'],
    'grant_type': config['grant_type'],
    'client_id': config['client_id']
}

response_auth = requests.post(auth_url, data=payload_auth, verify=False)
if response_auth.status_code != 200:
    print("Authentication failed:", response_auth.text)
    sys.exit(1)

token = response_auth.json().get("access_token")
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

# Get door details
door_url = f"{config['base_url']}/doors/{args.door}"
response = requests.get(door_url, headers=headers, verify=False)

if response.status_code == 200:
    door_data = response.json()
    print(json.dumps(door_data, indent=2))
else:
    print(f"Error {response.status_code}: {response.text}")
