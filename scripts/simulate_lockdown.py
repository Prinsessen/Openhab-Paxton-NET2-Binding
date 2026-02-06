#!/usr/bin/env python3

"""
Net2 Lockdown Simulation Script

Since the Net2 API doesn't have a dedicated lockdown endpoint, this script
simulates a lockdown by controlling all doors simultaneously.

Lockdown modes:
  - ENABLE:  Hold all doors closed (set all doors to hold closed state)
  - DISABLE: Return all doors to normal operation
  - STATUS:  Check status of all doors

Usage:
  python3 simulate_lockdown.py status
  python3 simulate_lockdown.py enable
  python3 simulate_lockdown.py disable
  python3 simulate_lockdown.py test     # Full test cycle
"""

import json
import requests
import sys
import os
import urllib3
from datetime import datetime
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message, color=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        if 'milestone' in config['base_url']:
            config['base_url'] = config['base_url'].replace('milestone', 'net2')
            log("Updated base_url: milestone → net2", Colors.WARNING)
        return config

def get_token(config):
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    
    log(f"Authenticating...", Colors.OKBLUE)
    resp = requests.post(url, data=payload, verify=False, timeout=10)
    
    if resp.status_code != 200:
        log(f"Authentication failed: {resp.status_code}", Colors.FAIL)
        sys.exit(1)
    
    log("Authentication successful", Colors.OKGREEN)
    return resp.json()['access_token']

def get_all_doors(config, token):
    """Get list of all doors"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    resp = requests.get(f"{config['base_url']}/doors", headers=headers, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

def get_door_status(config, token):
    """Get detailed status of all doors"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    resp = requests.get(f"{config['base_url']}/doors/status", headers=headers, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

def close_door(config, token, door_id, door_name):
    """Close/secure a specific door"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Try the close endpoint first (if available)
    close_url = f"{config['base_url']}/commands/door/close"
    payload = {"DoorId": door_id}
    
    try:
        resp = requests.post(close_url, headers=headers, json=payload, verify=False, timeout=5)
        if resp.status_code in [200, 201, 204]:
            return True, "close"
    except:
        pass
    
    # Fallback to control endpoint with relay command
    # RelayAction=2 typically means "Lock" or "Secure"
    control_url = f"{config['base_url']}/commands/door/control"
    control_payload = {
        "DoorId": door_id,
        "RelayFunction": {
            "RelayId": 1,
            "RelayAction": 2,  # Lock/Secure action
            "RelayOpenTime": 0
        },
        "LedFlash": "0"
    }
    
    try:
        resp = requests.post(control_url, headers=headers, json=control_payload, verify=False, timeout=5)
        if resp.status_code in [200, 201, 204]:
            return True, "control"
        else:
            return False, f"error:{resp.status_code}"
    except Exception as e:
        return False, f"error:{str(e)}"

def open_door(config, token, door_id, door_name):
    """Return door to normal operation (momentary unlock)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    #Try momentary door open
    control_url = f"{config['base_url']}/commands/door/control"
    control_payload = {
        "DoorId": door_id,
        "RelayFunction": {
            "RelayId": 1,
            "RelayAction": 1,  # Momentary unlock
            "RelayOpenTime": 1000  # 1 second
        },
        "LedFlash": "0"
    }
    
    try:
        resp = requests.post(control_url, headers=headers, json=control_payload, verify=False, timeout=5)
        if resp.status_code in [200, 201, 204]:
            return True, "unlocked"
        else:
            return False, f"error:{resp.status_code}"
    except Exception as e:
        return False, f"error:{str(e)}"

def show_status(config, token):
    """Display current status of all doors"""
    log("Fetching door status...", Colors.OKBLUE)
    
    doors_status = get_door_status(config, token)
    
    if not doors_status:
        log("No door status available", Colors.FAIL)
        return
    
    print(f"\n{'Door Name':<45} {'Relay':<10} {'Contact':<10} {'Alarm':<10}")
    print("=" * 80)
    
    for door in doors_status:
        name = door['name'][:44]
        relay_open = "OPEN" if door['status']['doorRelayOpen'] else "CLOSED"
        contact_closed = "CLOSED" if door['status']['doorContactClosed'] else "OPEN"
        alarm = "ARMED" if door['status']['intruderAlarmArmed'] else "DISARMED"
        
        # Color code the relay status
        relay_color = Colors.WARNING if door['status']['doorRelayOpen'] else Colors.OKGREEN
        
        print(f"{name:<45} {relay_color}{relay_open:<10}{Colors.ENDC} {contact_closed:<10} {alarm:<10}")
    
    print()

def enable_lockdown(config, token):
    """Simulate lockdown by closing/securing all doors"""
    log("=" * 60, Colors.HEADER)
    log("ENABLING LOCKDOWN MODE", Colors.HEADER)
    log("=" * 60, Colors.HEADER)
    
    doors = get_all_doors(config, token)
    
    if not doors:
        log("No doors found", Colors.FAIL)
        return False
    
    log(f"Found {len(doors)} doors to secure", Colors.OKBLUE)
    
    success_count = 0
    fail_count = 0
    
    for door in doors:
        door_id = door['id']
        door_name = door['name']
        
        log(f"Securing: {door_name}", Colors.OKCYAN)
        success, method = close_door(config, token, door_id, door_name)
        
        if success:
            log(f"  ✓ Secured via {method}", Colors.OKGREEN)
            success_count += 1
        else:
            log(f"  ✗ Failed: {method}", Colors.FAIL)
            fail_count += 1
        
        time.sleep(0.2)  # Small delay between commands
    
    print()
    log(f"Lockdown complete: {success_count} secured, {fail_count} failed", 
        Colors.OKGREEN if fail_count == 0 else Colors.WARNING)
    
    return fail_count == 0

def disable_lockdown(config, token):
    """Disable lockdown by returning doors to normal"""
    log("=" * 60, Colors.HEADER)
    log("DISABLING LOCKDOWN MODE", Colors.HEADER)
    log("=" * 60, Colors.HEADER)
    
    doors = get_all_doors(config, token)
    
    if not doors:
        log("No doors found", Colors.FAIL)
        return False
    
    log(f"Found {len(doors)} doors - sending unlock pulse to return to normal", Colors.OKBLUE)
    
    success_count = 0
    fail_count = 0
    
    for door in doors:
        door_id = door['id']
        door_name = door['name']
        
        log(f"Resetting: {door_name}", Colors.OKCYAN)
        success, method = open_door(config, token, door_id, door_name)
        
        if success:
            log(f"  ✓ Reset to normal", Colors.OKGREEN)
            success_count += 1
        else:
            log(f"  ✗ Failed: {method}", Colors.FAIL)
            fail_count += 1
        
        time.sleep(0.2)  # Small delay between commands
    
    print()
    log(f"Lockdown disabled: {success_count} reset, {fail_count} failed", 
        Colors.OKGREEN if fail_count == 0 else Colors.WARNING)
    
    return fail_count == 0

def test_cycle(config, token):
    """Run a complete test cycle"""
    log("=" * 60, Colors.BOLD)
    log("STARTING LOCKDOWN TEST CYCLE", Colors.BOLD)
    log("=" * 60, Colors.BOLD)
    
    print("\n1. INITIAL STATUS")
    show_status(config, token)
    
    input("\nPress ENTER to enable lockdown...")
    
    print("\n2. ENABLING LOCKDOWN")
    enable_lockdown(config, token)
    time.sleep(2)
    
    print("\n3. STATUS DURING LOCKDOWN")
    show_status(config, token)
    
    input("\nPress ENTER to disable lockdown...")
    
    print("\n4. DISABLING LOCKDOWN")
    disable_lockdown(config, token)
    time.sleep(2)
    
    print("\n5. FINAL STATUS")
    show_status(config, token)
    
    log("=" * 60, Colors.BOLD)
    log("TEST CYCLE COMPLETE", Colors.BOLD)
    log("=" * 60, Colors.BOLD)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    config = load_config()
    token = get_token(config)
    
    if command == 'status':
        show_status(config, token)
    elif command == 'enable':
        enable_lockdown(config, token)
    elif command == 'disable':
        disable_lockdown(config, token)
    elif command == 'test':
        test_cycle(config, token)
    else:
        log(f"Unknown command: {command}", Colors.FAIL)
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
