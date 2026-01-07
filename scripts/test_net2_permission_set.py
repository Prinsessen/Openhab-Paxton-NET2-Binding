#!/usr/bin/env python3
"""Test script to fetch Net2 door permission set structure"""
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://milestone.agesen.dk:8443/api/v1"
USERNAME = "Nanna Agesen"
PASSWORD = "Jekboapj110"
CLIENT_ID = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

def authenticate():
    """Get access token"""
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
    """List available access levels"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/accesslevels", headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()

def get_user_permission_set(token, user_id):
    """Get door permission set for a user"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/users/{user_id}/doorpermissionset", headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    print("Authenticating...")
    token = authenticate()
    print("✓ Authenticated\n")
    
    print("Fetching access levels...")
    levels = get_access_levels(token)
    print(f"✓ Found {len(levels)} access levels:")
    for level in levels[:5]:  # Show first 5
        print(f"  - ID {level.get('id')}: {level.get('name', 'N/A')}")
    print()
    
    print("Fetching user 3 door permission set...")
    perm_set = get_user_permission_set(token, 3)
    print("✓ Door permission set structure:")
    print(json.dumps(perm_set, indent=2))
