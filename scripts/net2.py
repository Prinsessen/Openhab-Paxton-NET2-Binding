#!/usr/bin/env python3

import json
import requests
import argparse
import os
import sys

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

# -----------------------------
# Configuration Loading
# -----------------------------
def load_config():
    """Load configuration from net2_config.json file"""
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"ERROR: Configuration file not found: {CONFIG_FILE}")
            print(f"Please create the config file with API credentials.")
            sys.exit(1)
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_fields = ['base_url', 'username', 'password', 'grant_type', 'client_id']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"ERROR: Missing required fields in config: {', '.join(missing_fields)}")
            sys.exit(1)
        
        return config
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        sys.exit(1)

# -----------------------------
# Argument Parser
# -----------------------------
parser = argparse.ArgumentParser(
    description='Net2 Door Control '
                '--did <Door-ID> '
                '--rid <Relay ID> '
                '--rea <Relay Action> '
                '--ret <Relay Open Time> '
                '--fla <LED Flash Time>'
)

parser.add_argument("--did", required=True, help="Door ID")
parser.add_argument("--rid", required=True, help="Relay ID")
parser.add_argument("--rea", required=True, help="Relay Action")
parser.add_argument("--ret", required=True, help="Relay Open Time (ms)")
parser.add_argument("--fla", required=True, help="LED Flash Mode")

args = parser.parse_args()

# Load configuration
config = load_config()

# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# API Endpoints & Auth Data
# Getting an Ca-Certificate validation error: Get the recent CA-cert from eg. Digicert copy and paste it in the beginning of /etc/ssl/certs/ca-certificates.crt
# -------------------------------------------------------------------------------------------------------------------------------------------------------------

Paxton_auth = f"{config['base_url']}/authorization/tokens"
Paxton_open_door = f"{config['base_url']}/commands/door/control"

# -----------------------------
# Authentication Request
# -----------------------------
payload_auth = {
    'username': config['username'],
    'password': config['password'],
    'grant_type': config['grant_type'],
    'client_id': config['client_id']
}

response_auth = requests.post(Paxton_auth, data=payload_auth)

if response_auth.status_code != 200:
    print("Authentication failed:", response_auth.text)
    exit(1)

token = response_auth.json().get("access_token")

# -----------------------------
# Door Control Request
# -----------------------------
data = {
    "DoorId": args.did,
    "RelayFunction": {
        "RelayId": args.rid,
        "RelayAction": args.rea,
        "RelayOpenTime": int(args.ret)
    },
    "LedFlash": args.fla
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {token}"
}

response_door = requests.post(
    url=Paxton_open_door,
    headers=headers,
    data=json.dumps(data)
)

print("\n--- RAW RESPONSE CONTENT ---")
print(response_door.content)

print("\n--- RESPONSE OBJECT ---")
print(response_door)

print("\n--- RESPONSE TEXT ---")
print(response_door.text)
