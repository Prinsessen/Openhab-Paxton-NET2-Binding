#!/usr/bin/env python3

import json
import requests
import argparse

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

# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# API Endpoints & Auth Data
# Getting an Ca-Certificate validation error: Get the recent CA-cert from eg. Digicert copy and paste it in the beginning of /etc/ssl/certs/ca-certificates.crt
# -------------------------------------------------------------------------------------------------------------------------------------------------------------

Paxton_auth = "https://milestone.agesen.dk:8443/api/v1/authorization/tokens"
Paxton_open_door = "https://milestone.agesen.dk:8443/api/v1/commands/door/control"

username = "Nanna Agesen"
password = "Jekboapj110"
grant_type = "password"
client_id = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

# -----------------------------
# Authentication Request
# -----------------------------
payload_auth = {
    'username': username,
    'password': password,
    'grant_type': grant_type,
    'client_id': client_id
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
