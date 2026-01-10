#!/usr/bin/env python3
"""
Poll Net2 door lock status via REST API

Monitors door lock state changes by polling the API every few seconds.
This detects remote lock/unlock commands sent via the Paxton UI.

Usage:
    cd /etc/openhab/scripts
    source /etc/openhab/.venv/bin/activate
    python3 poll_door_lock.py
"""

import json
import requests
import time
from datetime import datetime
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration
with open('net2_config.json') as f:
    config = json.load(f)

WORKSHOP_DOOR_ID = 3962494  # Værksted Dør - UI Controllable

def authenticate():
    """Get OAuth token"""
    auth_url = f"{config['base_url']}/authorization/tokens"
    payload_auth = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    
    response = requests.post(auth_url, data=payload_auth, verify=False)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def get_door_lock_status(token, door_id):
    """Get current lock status of a door"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    # Try getting door details
    door_url = f"{config['base_url']}/doors/{door_id}"
    response = requests.get(door_url, headers=headers, verify=False)
    
    if response.status_code == 200:
        door_data = response.json()
        # Look for locked/unlocked state in the response
        return door_data
    else:
        return None

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting door lock monitor...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring door: {WORKSHOP_DOOR_ID} 🔧 Værksted Dør")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Polling every 3 seconds for lock state changes...\n")
    
    token = authenticate()
    if not token:
        print("Failed to authenticate. Exiting.")
        return
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Authenticated\n")
    
    last_state = None
    token_refresh_time = time.time()
    
    try:
        while True:
            # Refresh token every 15 minutes
            if time.time() - token_refresh_time > 900:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Refreshing token...")
                token = authenticate()
                if not token:
                    print("Token refresh failed. Exiting.")
                    break
                token_refresh_time = time.time()
            
            # Get current door status
            status = get_door_lock_status(token, WORKSHOP_DOOR_ID)
            
            if status:
                # Print full status on first run
                if last_state is None:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Initial door data:")
                    print(json.dumps(status, indent=2))
                    last_state = status
                # Check for changes
                elif status != last_state:
                    print(f"\n{'🔧'*40}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ VÆRKSTED DØR STATE CHANGED!")
                    print(f"{'🔧'*40}")
                    print("\nPrevious state:")
                    print(json.dumps(last_state, indent=2))
                    print("\nNew state:")
                    print(json.dumps(status, indent=2))
                    print(f"{'🔧'*40}\n")
                    last_state = status
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Failed to get door status")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopping monitor...")

if __name__ == "__main__":
    main()
