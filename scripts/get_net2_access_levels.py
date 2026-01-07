#!/usr/bin/env python3
"""Fetch Net2 access levels to find valid IDs"""
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://milestone.agesen.dk:8443/api/v1"
USERNAME = "Nanna Agesen"
PASSWORD = "Jekboapj110"
CLIENT_ID = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

def authenticate():
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "scope": "offline_access"
    }
    resp = requests.post(f"{BASE_URL}/authorization/tokens", data=data, verify=False)
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_access_levels(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/accesslevels", headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    print("Authenticating...")
    token = authenticate()
    print("✓ Authenticated\n")
    
    print("Available access levels:")
    print("-" * 60)
    levels = get_access_levels(token)
    for level in levels:
        print(f"ID: {level.get('id'):4}  Name: {level.get('name', 'N/A')}")
    print("-" * 60)
    print(f"\nTotal: {len(levels)} access levels")
    
    if levels:
        print(f"\n✓ Use access level ID {levels[0]['id']} for test")
