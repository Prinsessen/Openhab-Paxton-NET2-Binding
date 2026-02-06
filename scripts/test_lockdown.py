#!/usr/bin/env python3

"""
Net2 Lockdown Test Script

Tests the Net2 building lockdown feature. Lockdown is a security feature
that can lock all doors simultaneously in an emergency.

Usage:
  python3 test_lockdown.py status                          # Check current lockdown status
  python3 test_lockdown.py rules                           # Discover trigger/action rules
  python3 test_lockdown.py enable [trigger_id] [action_id] # Enable lockdown
  python3 test_lockdown.py disable [trigger_id] [action_id]# Disable lockdown
  python3 test_lockdown.py test                            # Test with status check before/after

Examples:
  python3 test_lockdown.py rules
  python3 test_lockdown.py enable 123 456
  python3 test_lockdown.py disable

API Endpoint:
  POST /api/v1/commands/controlLockdown
  
  Requires trigger and action rules to be configured in Net2 system.
  These rules define which doors are affected by lockdown.

Requirements:
  - net2_config.json in same directory with API credentials
  - requests library: pip install requests
"""

import json
import requests
import sys
import os
import urllib3
from datetime import datetime

# Disable SSL warnings (self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

# Color codes for terminal output
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
    """Load API configuration from net2_config.json"""
    try:
        if not os.path.exists(CONFIG_FILE):
            log(f"ERROR: Configuration file not found: {CONFIG_FILE}", Colors.FAIL)
            log("Please create net2_config.json with the following structure:", Colors.WARNING)
            print(json.dumps({
                "base_url": "https://net2.agesen.dk:8443/api/v1",
                "username": "your_username",
                "password": "your_password",
                "grant_type": "password",
                "client_id": "your_client_id"
            }, indent=2))
            sys.exit(1)
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Update base URL if needed - handle both old hostnames
        if 'milestone.agesen.dk' in config['base_url']:
            log("Updating base_url: milestone → net2", Colors.WARNING)
            config['base_url'] = config['base_url'].replace('milestone.agesen.dk', 'net2.agesen.dk')
        elif 'net2.agesen.dk:8443' not in config['base_url']:
            log("Adding port 8443 to net2.agesen.dk", Colors.WARNING)
            config['base_url'] = config['base_url'].replace('https://net2.agesen.dk', 'https://net2.agesen.dk:8443')
        
        return config
    except Exception as e:
        log(f"ERROR: Failed to load config: {e}", Colors.FAIL)
        sys.exit(1)

def get_token(config):
    """Get authentication token from Net2 API"""
    url = f"{config['base_url']}/authorization/tokens"
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    
    try:
        log(f"Authenticating with {url}...", Colors.OKBLUE)
        resp = requests.post(url, data=payload, verify=False, timeout=10)
        
        if resp.status_code != 200:
            log(f"Authentication failed: {resp.status_code}", Colors.FAIL)
            log(f"Response: {resp.text}", Colors.FAIL)
            sys.exit(1)
        
        token = resp.json()['access_token']
        log("Authentication successful", Colors.OKGREEN)
        return token
    except Exception as e:
        log(f"ERROR: Authentication failed: {e}", Colors.FAIL)
        sys.exit(1)

def get_lockdown_status(config, token):
    """
    Get current lockdown status from Net2 API
    
    Returns:
        dict: Lockdown status information
    """
    # Try different possible endpoints
    endpoints = [
        f"{config['base_url']}/lockdown/status",
        f"{config['base_url']}/system/lockdown",
        f"{config['base_url']}/building/lockdown/status",
        f"{config['base_url']}/commands/lockdown/status"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    log("Checking lockdown status...", Colors.OKBLUE)
    
    for endpoint in endpoints:
        try:
            log(f"Trying endpoint: {endpoint}")
            resp = requests.get(endpoint, headers=headers, verify=False, timeout=10)
            
            if resp.status_code == 200:
                log(f"✓ Found working endpoint: {endpoint}", Colors.OKGREEN)
                return {
                    'success': True,
                    'endpoint': endpoint,
                    'data': resp.json()
                }
            elif resp.status_code == 404:
                log(f"  Endpoint not found (404)", Colors.WARNING)
            else:
                log(f"  Status code: {resp.status_code}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not find lockdown status endpoint", Colors.FAIL)
    return {'success': False, 'endpoint': None, 'data': None}

def get_lockdown_rules(config, token):
    """
    Get available trigger and action rules for lockdown
    
    Returns:
        dict: Available rules
    """
    # Try to find rules endpoints
    endpoints = [
        (f"{config['base_url']}/rules", "All Rules"),
        (f"{config['base_url']}/lockdown/rules", "Lockdown Rules"),
        (f"{config['base_url']}/triggers", "Trigger Rules"),
        (f"{config['base_url']}/actions", "Action Rules"),
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    log("Discovering lockdown rules...", Colors.OKBLUE)
    
    results = {}
    for endpoint, name in endpoints:
        try:
            log(f"Checking {name}: {endpoint}")
            resp = requests.get(endpoint, headers=headers, verify=False, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                log(f"✓ Found {name}", Colors.OKGREEN)
                results[name] = data
                # Print preview
                if isinstance(data, list) and len(data) > 0:
                    log(f"  Found {len(data)} items", Colors.OKCYAN)
                    log(f"  Sample: {json.dumps(data[0] if len(data) > 0 else {}, indent=2)[:200]}...", Colors.OKCYAN)
            elif resp.status_code == 404:
                log(f"  Not found (404)", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    return results

def enable_lockdown(config, token, trigger_rule_id=None, action_rule_id=None):
    """
    Enable lockdown mode (locks all doors)
    Uses /api/v1/commands/controlLockdown endpoint
    
    Args:
        trigger_rule_id: Optional trigger rule ID (discovery mode if None)
        action_rule_id: Optional action rule ID (discovery mode if None)
    
    Returns:
        bool: True if successful
    """
    url = f"{config['base_url']}/commands/controlLockdown"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    log("Attempting to enable lockdown...", Colors.WARNING)
    
    # Try different payload structures
    payloads = []
    
    # If specific IDs provided, use them
    if trigger_rule_id and action_rule_id:
        payloads.append({
            "TriggerRuleId": trigger_rule_id,
            "ActionRuleId": action_rule_id,
            "lockdown": True
        })
    
    # Discovery mode - try common structures (based on API response showing "lockdown" field)
    payloads.extend([
        {"lockdown": True},  # Try this first - API response shows this field name
        {"Lockdown": True},
        {"Enabled": True},
        {"Enable": True},
        {"State": "Enabled"},
        {"Action": "Enable"},
        {"LockdownState": True},
        {},  # Empty body
    ])
    
    for i, data in enumerate(payloads):
        try:
            log(f"Trying payload #{i+1}: {json.dumps(data)}")
            resp = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
            
            if resp.status_code in [200, 201, 204]:
                log(f"✓ Lockdown enabled successfully!", Colors.OKGREEN)
                if resp.text:
                    try:
                        result = resp.json()
                        log(f"  Response: {json.dumps(result, indent=2)}", Colors.OKCYAN)
                    except:
                        log(f"  Response: {resp.text}", Colors.OKCYAN)
                return True
            elif resp.status_code == 400:
                log(f"  Bad request (400): {resp.text}", Colors.WARNING)
            elif resp.status_code == 404:
                log(f"  Command not found (404)", Colors.FAIL)
                return False
            else:
                log(f"  Status code: {resp.status_code}, Response: {resp.text}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not enable lockdown - check API documentation for required parameters", Colors.FAIL)
    return False

def disable_lockdown(config, token, trigger_rule_id=None, action_rule_id=None):
    """
    Disable lockdown mode (returns to normal operation)
    Uses /api/v1/commands/controlLockdown endpoint
    
    Args:
        trigger_rule_id: Optional trigger rule ID
        action_rule_id: Optional action rule ID
    
    Returns:
        bool: True if successful
    """
    url = f"{config['base_url']}/commands/controlLockdown"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    log("Attempting to disable lockdown...", Colors.OKBLUE)
    
    # Try different payload structures
    payloads = []
    
    # If specific IDs provided, use them
    if trigger_rule_id and action_rule_id:
        payloads.append({
            "TriggerRuleId": trigger_rule_id,
            "ActionRuleId": action_rule_id,
            "lockdown": False
        })
    
    # Discovery mode - try common structures (based on API response showing "lockdown" field)
    payloads.extend([
        {"lockdown": False},  # Try this first - API response shows this field name
        {"Lockdown": False},
        {"Enabled": False},
        {"Enable": False},
        {"State": "Disabled"},
        {"Action": "Disable"},
        {"LockdownState": False},
    ])
    
    for i, data in enumerate(payloads):
        try:
            log(f"Trying payload #{i+1}: {json.dumps(data)}")
            resp = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
            
            if resp.status_code in [200, 201, 204]:
                log(f"✓ Lockdown disabled successfully!", Colors.OKGREEN)
                if resp.text:
                    try:
                        result = resp.json()
                        log(f"  Response: {json.dumps(result, indent=2)}", Colors.OKCYAN)
                    except:
                        log(f"  Response: {resp.text}", Colors.OKCYAN)
                return True
            elif resp.status_code == 400:
                log(f"  Bad request (400): {resp.text}", Colors.WARNING)
            elif resp.status_code == 404:
                log(f"  Command not found (404)", Colors.FAIL)
                return False
            else:
                log(f"  Status code: {resp.status_code}, Response: {resp.text}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not disable lockdown - check API documentation for required parameters", Colors.FAIL)
    return False

def test_lockdown_cycle(config, token):
    """
    Complete test cycle: check status, enable, check, disable, check
    """
    log("=== Starting Lockdown Test Cycle ===", Colors.HEADER)
    
    # Initial status check
    log("\n1. Initial Status Check", Colors.BOLD)
    initial_status = get_lockdown_status(config, token)
    if initial_status['success']:
        print(json.dumps(initial_status['data'], indent=2))
    
    # Enable lockdown
    log("\n2. Enabling Lockdown", Colors.BOLD)
    if enable_lockdown(config, token):
        log("Waiting 2 seconds...", Colors.OKCYAN)
        import time
        time.sleep(2)
        
        # Check status after enable
        log("\n3. Status After Enable", Colors.BOLD)
        enabled_status = get_lockdown_status(config, token)
        if enabled_status['success']:
            print(json.dumps(enabled_status['data'], indent=2))
        
        # Disable lockdown
        log("\n4. Disabling Lockdown", Colors.BOLD)
        if disable_lockdown(config, token):
            log("Waiting 2 seconds...", Colors.OKCYAN)
            time.sleep(2)
            
            # Final status check
            log("\n5. Final Status Check", Colors.BOLD)
            final_status = get_lockdown_status(config, token)
            if final_status['success']:
                print(json.dumps(final_status['data'], indent=2))
    
    log("\n=== Test Cycle Complete ===", Colors.HEADER)

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
    token = get_token(config)
    
    # Optional trigger/action rule IDs from command line
    trigger_rule_id = sys.argv[2] if len(sys.argv) > 2 else None
    action_rule_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Execute command
    if command == 'status':
        status = get_lockdown_status(config, token)
        if status['success']:
            print("\nLockdown Status:")
            print(json.dumps(status['data'], indent=2))
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'rules':
        rules = get_lockdown_rules(config, token)
        if rules:
            print("\n=== Available Lockdown Rules ===")
            print(json.dumps(rules, indent=2))
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'enable':
        if enable_lockdown(config, token, trigger_rule_id, action_rule_id):
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'disable':
        if disable_lockdown(config, token, trigger_rule_id, action_rule_id):
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'test':
        test_lockdown_cycle(config, token)
        sys.exit(0)
    
    else:
        log(f"Unknown command: {command}", Colors.FAIL)
        print_usage()
        sys.exit(1)

if __name__ == '__main__':
    main()
