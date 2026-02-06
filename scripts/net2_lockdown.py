#!/usr/bin/env python3

"""
Net2 Lockdown Control via Trigger/Action Rules

The Net2 lockdown feature works by:
1. Creating a Trigger/Action rule that defines which doors to lock
2. Firing the trigger to execute the lockdown
3. Optionally creating a separate rule to unlock doors

Usage:
  python3 net2_lockdown.py list-triggers           # List all trigger/action rules
  python3 net2_lockdown.py list-doors              # List all doors in system
  python3 net2_lockdown.py create-lockdown-rule    # Create lockdown trigger rule
  python3 net2_lockdown.py enable                  # Fire lockdown trigger (locks doors)
  python3 net2_lockdown.py disable                 # Fire unlock trigger (unlocks doors)
  python3 net2_lockdown.py status                  # Check current door status
"""

import json
import requests
import sys
import os
import urllib3
from datetime import datetime

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
    """Print log message with timestamp and optional color"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")

def load_config():
    """Load API configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Fix URL if needed
        if 'milestone' in config['base_url']:
            config['base_url'] = config['base_url'].replace('milestone', 'net2')
        if ':8443' not in config['base_url']:
            config['base_url'] = config['base_url'].replace('/api', ':8443/api')
        
        return config
    except Exception as e:
        log(f"ERROR: Failed to load config: {e}", Colors.FAIL)
        sys.exit(1)

def get_token(config):
    """Get authentication token"""
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    
    try:
        resp = requests.post(url, data=payload, verify=False, timeout=10)
        if resp.status_code != 200:
            log(f"Authentication failed: {resp.status_code}", Colors.FAIL)
            log(f"Response: {resp.text}", Colors.FAIL)
            sys.exit(1)
        
        return resp.json()['access_token']
    except Exception as e:
        log(f"ERROR: Authentication failed: {e}", Colors.FAIL)
        sys.exit(1)

def list_triggers(config, token):
    """List all trigger/action rules"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Try different possible endpoints
    endpoints = [
        f"{config['base_url']}/triggers",
        f"{config['base_url']}/actions",
        f"{config['base_url']}/rules",
        f"{config['base_url']}/triggerandactions",
        f"{config['base_url']}/automation/triggers"
    ]
    
    log("Searching for trigger/action rules...", Colors.OKBLUE)
    
    for endpoint in endpoints:
        try:
            log(f"Trying: {endpoint}")
            resp = requests.get(endpoint, headers=headers, verify=False, timeout=10)
            
            if resp.status_code == 200:
                log(f"✓ Found endpoint: {endpoint}", Colors.OKGREEN)
                data = resp.json()
                print(json.dumps(data, indent=2))
                return data
            elif resp.status_code == 404:
                log(f"  Not found (404)", Colors.WARNING)
            else:
                log(f"  Status: {resp.status_code}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not find triggers endpoint", Colors.FAIL)
    return None

def list_doors(config, token):
    """List all doors in the system"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        log("Fetching doors list...", Colors.OKBLUE)
        resp = requests.get(f"{config['base_url']}/doors", headers=headers, verify=False, timeout=10)
        
        if resp.status_code == 200:
            doors = resp.json()
            log(f"✓ Found {len(doors)} doors", Colors.OKGREEN)
            
            print("\nAvailable Doors:")
            print("-" * 80)
            for door in doors:
                door_id = door.get('id', 'N/A')
                door_name = door.get('name', 'Unnamed')
                print(f"  ID: {door_id:10} | Name: {door_name}")
            
            return doors
        else:
            log(f"Failed to fetch doors: {resp.status_code}", Colors.FAIL)
            return None
    except Exception as e:
        log(f"ERROR: {e}", Colors.FAIL)
        return None

def create_lockdown_rule(config, token, door_ids=None):
    """
    Create a trigger/action rule for lockdown
    
    Args:
        door_ids: List of door IDs to lock. If None, will fetch all doors.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # If no door IDs provided, get all doors
    if door_ids is None:
        doors = list_doors(config, token)
        if doors:
            door_ids = [d.get('id') for d in doors if d.get('id')]
            log(f"Using all {len(door_ids)} doors for lockdown rule", Colors.OKCYAN)
        else:
            log("ERROR: Could not fetch doors", Colors.FAIL)
            return False
    
    # Try to create trigger/action rule
    endpoints = [
        f"{config['base_url']}/triggers",
        f"{config['base_url']}/actions",
        f"{config['base_url']}/triggerandactions"
    ]
    
    lockdown_rule = {
        "name": "Emergency Lockdown",
        "description": "Lock all doors in emergency",
        "enabled": True,
        "actions": [
            {
                "type": "DoorLock",
                "doorIds": door_ids
            }
        ]
    }
    
    log("Creating lockdown trigger/action rule...", Colors.WARNING)
    
    for endpoint in endpoints:
        try:
            log(f"Trying: {endpoint}")
            resp = requests.post(endpoint, headers=headers, json=lockdown_rule, verify=False, timeout=10)
            
            if resp.status_code in [200, 201]:
                log(f"✓ Lockdown rule created!", Colors.OKGREEN)
                result = resp.json()
                print(json.dumps(result, indent=2))
                return result
            elif resp.status_code == 404:
                log(f"  Endpoint not found", Colors.WARNING)
            else:
                log(f"  Status: {resp.status_code}", Colors.WARNING)
                log(f"  Response: {resp.text}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not create lockdown rule", Colors.FAIL)
    return None

def fire_trigger(config, token, trigger_id=None, trigger_name=None):
    """
    Fire a trigger/action rule (the actual lockdown command)
    
    Args:
        trigger_id: ID of trigger to fire
        trigger_name: Name of trigger to fire (if ID not known)
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Command variations to try
    commands = [
        {
            "CommandName": "FireTrigger",
            "Input": {"TriggerId": trigger_id} if trigger_id else {"TriggerName": trigger_name}
        },
        {
            "CommandName": "ExecuteTrigger",
            "Input": {"TriggerId": trigger_id} if trigger_id else {"TriggerName": trigger_name}
        },
        {
            "CommandName": "TriggerAction",
            "Input": {"Id": trigger_id} if trigger_id else {"Name": trigger_name}
        }
    ]
    
    log(f"Firing trigger: {trigger_id or trigger_name}", Colors.WARNING)
    
    for cmd in commands:
        try:
            log(f"Trying command: {cmd['CommandName']}")
            resp = requests.post(
                f"{config['base_url']}/commands",
                headers=headers,
                json=cmd,
                verify=False,
                timeout=10
            )
            
            if resp.status_code in [200, 201]:
                log(f"✓ Trigger fired successfully!", Colors.OKGREEN)
                result = resp.json()
                print(json.dumps(result, indent=2))
                return True
            elif resp.status_code == 404:
                log(f"  Command not found", Colors.WARNING)
            else:
                log(f"  Status: {resp.status_code}", Colors.WARNING)
                log(f"  Response: {resp.text}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    return False

def enable_lockdown(config, token):
    """
    Enable lockdown by firing the lockdown trigger
    This is the "fire and forget" command
    """
    log("=== ENABLING LOCKDOWN ===", Colors.HEADER)
    
    # First, let's try to find existing lockdown trigger
    triggers = list_triggers(config, token)
    
    if triggers:
        # Look for lockdown trigger
        for trigger in triggers if isinstance(triggers, list) else []:
            trigger_name = trigger.get('name', '').lower()
            trigger_id = trigger.get('id')
            
            if 'lockdown' in trigger_name or 'emergency' in trigger_name:
                log(f"Found lockdown trigger: {trigger.get('name')}", Colors.OKGREEN)
                return fire_trigger(config, token, trigger_id=trigger_id)
    
    # If no trigger found, try firing by name
    log("Attempting to fire lockdown trigger by name...", Colors.WARNING)
    return fire_trigger(config, token, trigger_name="Emergency Lockdown")

def disable_lockdown(config, token):
    """
    Disable lockdown by firing the unlock trigger
    """
    log("=== DISABLING LOCKDOWN ===", Colors.HEADER)
    
    # First, let's try to find existing unlock trigger
    triggers = list_triggers(config, token)
    
    if triggers:
        # Look for unlock trigger
        for trigger in triggers if isinstance(triggers, list) else []:
            trigger_name = trigger.get('name', '').lower()
            trigger_id = trigger.get('id')
            
            if 'unlock' in trigger_name or 'release' in trigger_name:
                log(f"Found unlock trigger: {trigger.get('name')}", Colors.OKGREEN)
                return fire_trigger(config, token, trigger_id=trigger_id)
    
    # If no trigger found, try firing by name
    log("Attempting to fire unlock trigger by name...", Colors.WARNING)
    return fire_trigger(config, token, trigger_name="Release Lockdown")

def check_door_status(config, token):
    """Check current status of all doors"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        log("Checking door status...", Colors.OKBLUE)
        resp = requests.get(f"{config['base_url']}/doors/status", headers=headers, verify=False, timeout=10)
        
        if resp.status_code == 200:
            doors = resp.json()
            
            print("\nDoor Status:")
            print("-" * 80)
            for door in doors:
                door_id = door.get('id', 'N/A')
                door_name = door.get('name', 'Unnamed')
                locked = door.get('locked', door.get('isLocked', 'Unknown'))
                print(f"  {door_name:30} | ID: {door_id:10} | Locked: {locked}")
            
            return doors
        else:
            log(f"Failed to fetch door status: {resp.status_code}", Colors.FAIL)
            return None
    except Exception as e:
        log(f"ERROR: {e}", Colors.FAIL)
        return None

def print_usage():
    """Print usage instructions"""
    print(__doc__)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Load configuration
    config = load_config()
    
    # Get authentication token
    log("Authenticating...", Colors.OKBLUE)
    token = get_token(config)
    log("✓ Authenticated", Colors.OKGREEN)
    
    # Execute command
    if command == 'list-triggers':
        list_triggers(config, token)
    
    elif command == 'list-doors':
        list_doors(config, token)
    
    elif command == 'create-lockdown-rule':
        create_lockdown_rule(config, token)
    
    elif command == 'enable':
        if enable_lockdown(config, token):
            log("✓ LOCKDOWN ENABLED", Colors.OKGREEN)
            sys.exit(0)
        else:
            log("✗ Failed to enable lockdown", Colors.FAIL)
            sys.exit(1)
    
    elif command == 'disable':
        if disable_lockdown(config, token):
            log("✓ LOCKDOWN DISABLED", Colors.OKGREEN)
            sys.exit(0)
        else:
            log("✗ Failed to disable lockdown", Colors.FAIL)
            sys.exit(1)
    
    elif command == 'status':
        check_door_status(config, token)
    
    else:
        log(f"Unknown command: {command}", Colors.FAIL)
        print_usage()
        sys.exit(1)

if __name__ == '__main__':
    main()
