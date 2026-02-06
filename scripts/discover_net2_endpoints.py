#!/usr/bin/env python3

"""
Net2 API Endpoint Discovery Script

Tries to discover available API endpoints by checking common patterns
and examining the API documentation/swagger if available.
"""

import json
import requests
import sys
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        # Update to new endpoint
        if 'milestone' in config['base_url']:
            config['base_url'] = config['base_url'].replace('milestone', 'net2')
        return config

def get_token(config):
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    resp = requests.post(url, data=payload, verify=False)
    if resp.status_code != 200:
        print(f"Auth failed: {resp.status_code}")
        sys.exit(1)
    return resp.json()['access_token']

def discover_endpoints(config, token):
    """Try to discover available endpoints"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Common API discovery endpoints
    discovery_endpoints = [
        "",  # Root
        "/swagger/v1/swagger.json",
        "/swagger.json",
        "/api-docs",
        "/v1/api-docs",
        "/../swagger/v1/swagger.json",  # Sometimes swagger is outside /api/v1
    ]
    
    print("=== Searching for API Documentation ===\n")
    
    for endpoint in discovery_endpoints:
        url = config['base_url'] + endpoint
        print(f"Trying: {url}")
        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=5)
            if resp.status_code == 200:
                print(f"✓ FOUND: {url}")
                try:
                    data = resp.json()
                    print("\nAPI Documentation found!")
                    
                    # Look for lockdown-related paths
                    if 'paths' in data:
                        print("\n=== Lockdown-related endpoints ===")
                        for path, methods in data['paths'].items():
                            if 'lockdown' in path.lower():
                                print(f"  {path}")
                                for method in methods.keys():
                                    print(f"    - {method.upper()}")
                        
                        print("\n=== All available command endpoints ===")
                        for path in sorted(data['paths'].keys()):
                            if 'command' in path.lower():
                                print(f"  {path}")
                    
                    # Save full docs
                    with open('/tmp/net2_api_docs.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print("\n✓ Full API docs saved to: /tmp/net2_api_docs.json")
                    return data
                except:
                    print(f"Response is not JSON: {resp.text[:200]}")
            elif resp.status_code == 401:
                print(f"  Unauthorized (might need different auth)")
            elif resp.status_code != 404:
                print(f"  Status: {resp.status_code}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n=== No API documentation found, trying common patterns ===\n")
    
    # Try common command endpoints
    test_endpoints = [
        "/commands",
        "/doors",
        "/areas",
        "/building",
        "/system",
        "/status",
    ]
    
    print("Testing base endpoints (GET):")
    for endpoint in test_endpoints:
        url = config['base_url'] + endpoint
        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=5)
            if resp.status_code == 200:
                print(f"  ✓ {endpoint} - {resp.status_code}")
                try:
                    data = resp.json()
                    if isinstance(data, list):
                        print(f"    Returns array with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"    Returns object with keys: {list(data.keys())[:5]}")
                except:
                    pass
            elif resp.status_code != 404:
                print(f"  ? {endpoint} - {resp.status_code}")
        except Exception as e:
            pass
    
    return None

def check_known_endpoints(config, token):
    """Check endpoints we know work from other scripts"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    known = [
        ("/doors/status", "GET"),
        ("/commands/door/holdopen", "POST"),
        ("/commands/door/close", "POST"),
        ("/commands/door/control", "POST"),
    ]
    
    print("\n=== Known Working Endpoints (from other scripts) ===\n")
    for endpoint, method in known:
        url = config['base_url'] + endpoint
        print(f"{method:4s} {endpoint}")

def main():
    config = load_config()
    token = get_token(config)
    print(f"✓ Authenticated successfully\n")
    print(f"Base URL: {config['base_url']}\n")
    
    discover_endpoints(config, token)
    check_known_endpoints(config, token)
    
    print("\n=== Suggestion ===")
    print("If no lockdown endpoints were found, check:")
    print("1. Net2 API version - lockdown might be in different version")
    print("2. User permissions - your account might not have lockdown access")
    print("3. Net2 documentation - lockdown might use different terminology")
    print("   (e.g., 'secure', 'emergency', 'area/control', etc.)")

if __name__ == '__main__':
    main()
