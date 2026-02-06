#!/usr/bin/env python3

"""
Net2 Lockdown Test Script

Tests the Net2 building lockdown feature. Lockdown is a security feature
that can lock all doors simultaneously in an emergency.

Usage:
  python3 test_lockdown.py status              # Check current lockdown status
  python3 test_lockdown.py enable              # Enable lockdown (locks all doors)
  python3 test_lockdown.py disable             # Disable lockdown (returns to normal)
  python3 test_lockdown.py test                # Test with status check before/after

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

def enable_lockdown(config, token):
    """
    Enable lockdown mode (locks all doors)
    
    Returns:
        bool: True if successful
    """
    # Try command-based approach (standard Net2 API pattern)
    command_names = [
        "LockdownEnable",
        "EnableLockdown", 
        "Lockdown",
        "BuildingLockdown",
        "LockdownOn"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    log("Attempting to enable lockdown via command API...", Colors.WARNING)
    
    for command_name in command_names:
        try:
            # Standard Net2 command structure
            data = {
                "CommandName": command_name,
                "Input": {
                    "Enabled": True
                }
            }
            
            log(f"Trying command: {command_name}")
            resp = requests.post(
                f"{config['base_url']}/commands",
                headers=headers,
                json=data,
                verify=False,
                timeout=10
            )
            
            if resp.status_code in [200, 201]:
                result = resp.json()
                log(f"✓ Command accepted: {command_name}", Colors.OKGREEN)
                log(f"  Command ID: {result.get('Id', 'N/A')}")
                log(f"  Output: {json.dumps(result.get('Output', {}))}")
                return True
            elif resp.status_code == 404:
                log(f"  Command not found", Colors.WARNING)
            elif resp.status_code == 400:
                log(f"  Bad request: {resp.text}", Colors.WARNING)
            else:
                log(f"  Status code: {resp.status_code}, Response: {resp.text}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not enable lockdown", Colors.FAIL)
    return False

def disable_lockdown(config, token):
    """
    Disable lockdown mode (returns to normal operation)
    
    Returns:
        bool: True if successful
    """
    # Try command-based approach
    command_names = [
        "LockdownDisable",
        "DisableLockdown",
        "LockdownOff",
        "BuildingLockdownDisable"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    log("Attempting to disable lockdown via command API...", Colors.OKBLUE)
    
    for command_name in command_names:
        try:
            # Standard Net2 command structure
            data = {
                "CommandName": command_name,
                "Input": {
                    "Enabled": False
                }
            }
            
            log(f"Trying command: {command_name}")
            resp = requests.post(
                f"{config['base_url']}/commands",
                headers=headers,
                json=data,
                verify=False,
                timeout=10
            )
            
            if resp.status_code in [200, 201]:
                result = resp.json()
                log(f"✓ Command accepted: {command_name}", Colors.OKGREEN)
                log(f"  Command ID: {result.get('Id', 'N/A')}")
                log(f"  Output: {json.dumps(result.get('Output', {}))}")
                return True
            elif resp.status_code == 404:
                log(f"  Command not found", Colors.WARNING)
            elif resp.status_code == 400:
                log(f"  Bad request: {resp.text}", Colors.WARNING)
            else:
                log(f"  Status code: {resp.status_code}, Response: {resp.text}", Colors.WARNING)
        except Exception as e:
            log(f"  Error: {e}", Colors.WARNING)
    
    log("Could not disable lockdown", Colors.FAIL)
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
    
    # Execute command
    if command == 'status':
        status = get_lockdown_status(config, token)
        if status['success']:
            print("\nLockdown Status:")
            print(json.dumps(status['data'], indent=2))
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'enable':
        if enable_lockdown(config, token):
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'disable':
        if disable_lockdown(config, token):
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
