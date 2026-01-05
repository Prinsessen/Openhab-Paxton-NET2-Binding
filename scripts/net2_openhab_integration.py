#!/usr/bin/env python3

"""
Paxton Net2 - OpenHAB Integration Script
Syncs Net2 access control data with OpenHAB items for automation and monitoring
"""

import json
import requests
import argparse
from datetime import datetime, timedelta, timezone
import sys
import time
import os

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://milestone.agesen.dk:8443/api/v1"
AUTH_ENDPOINT = f"{BASE_URL}/authorization/tokens"
EVENTS_ENDPOINT = f"{BASE_URL}/events"
DOORS_ENDPOINT = f"{BASE_URL}/doors"
USERS_ENDPOINT = f"{BASE_URL}/users"

# Net2 Authentication
NET2_USERNAME = "Nanna Agesen"
NET2_PASSWORD = "Jekboapj110"
NET2_GRANT_TYPE = "password"
NET2_CLIENT_ID = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

# Net2 TLS verification (path to CA bundle or 'false' to disable)
NET2_VERIFY_ENV = os.getenv("NET2_VERIFY")
NET2_VERIFY_DEFAULT = "/etc/ssl/certs/ca-certificates.crt"
if NET2_VERIFY_ENV is None:
    NET2_VERIFY = NET2_VERIFY_DEFAULT
elif NET2_VERIFY_ENV.lower() in ["0", "false", "no"]:
    NET2_VERIFY = False
else:
    NET2_VERIFY = NET2_VERIFY_ENV

# OpenHAB Configuration
OPENHAB_URL = "https://openhab5.agesen.dk"
OPENHAB_REST_API = f"{OPENHAB_URL}/rest/items"
# Optional bearer token for secured OpenHAB REST API
OPENHAB_TOKEN = os.getenv("OPENHAB_TOKEN")
# Optional TLS verification override for OpenHAB (path to CA bundle or 'false')
OPENHAB_VERIFY_ENV = os.getenv("OPENHAB_VERIFY")
OPENHAB_VERIFY_DEFAULT = "/etc/ssl/certs/ca-certificates.crt"
if OPENHAB_VERIFY_ENV is None:
    OPENHAB_VERIFY = OPENHAB_VERIFY_DEFAULT
elif OPENHAB_VERIFY_ENV.lower() in ["0", "false", "no"]:
    OPENHAB_VERIFY = False
else:
    OPENHAB_VERIFY = OPENHAB_VERIFY_ENV

# Event type mappings
ACCESS_GRANTED_TYPES = [20, 26]  # 20=card, 26=PIN
ACCESS_DENIED_TYPES = [23, 24, 25, 27]
DOOR_OPENED_TYPES = [28, 46]
# Add common "door secured/locked" event codes (45/49) used by some Net2 controllers
DOOR_CLOSED_TYPES = [29, 47, 45, 49]
DOOR_HELD_OPEN_TYPES = [93]

# Auto-close fallback (seconds) to handle pulse-only doors without explicit close events
AUTO_CLOSE_SECONDS = int(os.getenv("NET2_DOOR_AUTOCLOSE_SECONDS", "7"))

# -----------------------------
# Argument Parser
# -----------------------------
parser = argparse.ArgumentParser(
    description='Paxton Net2 - OpenHAB Integration'
)
parser.add_argument("--mode", choices=['sync', 'monitor', 'init'], default='sync',
                    help="Mode: init (create items), sync (one-time sync), monitor (continuous)")
parser.add_argument("--interval", type=int, default=30,
                    help="Poll interval in seconds for monitor mode (default: 30)")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
parser.add_argument("--test", action="store_true", help="Test mode - don't update OpenHAB")

args = parser.parse_args()

# -----------------------------
# Helper Functions
# -----------------------------
def log(message, level="INFO"):
    """Print log message"""
    if args.verbose or level in ["ERROR", "WARNING"]:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

def authenticate_net2():
    """Authenticate with Paxton Net2 API"""
    log("Authenticating with Net2 API...")
    
    payload = {
        'username': NET2_USERNAME,
        'password': NET2_PASSWORD,
        'grant_type': NET2_GRANT_TYPE,
        'client_id': NET2_CLIENT_ID
    }
    
    try:
        response = requests.post(AUTH_ENDPOINT, data=payload, timeout=10, verify=NET2_VERIFY)
        if response.status_code != 200:
            log(f"Authentication failed: {response.status_code}", "ERROR")
            return None
        
        token = response.json().get("access_token")
        log("Authentication successful")
        return token
    
    except Exception as e:
        log(f"Authentication error: {e}", "ERROR")
        return None

def update_openhab_item(item_name, state, state_type="String"):
    """Update an OpenHAB item state"""
    if args.test:
        log(f"TEST MODE: Would update {item_name} = {state}")
        return True
    
    try:
        url = f"{OPENHAB_REST_API}/{item_name}/state"
        headers = {"Content-Type": "text/plain", "Accept": "application/json"}
        if OPENHAB_TOKEN:
            headers["Authorization"] = f"Bearer {OPENHAB_TOKEN}"
        
        # Convert state to appropriate format
        if state_type == "Switch":
            state = "ON" if state else "OFF"
        elif state_type == "Number":
            state = str(state)
        elif state_type == "DateTime":
            # OpenHAB expects ISO format with timezone
            if isinstance(state, str):
                state = state
            else:
                state = state.isoformat()
        
        response = requests.put(url, data=str(state), headers=headers, timeout=5, verify=OPENHAB_VERIFY)
        
        if response.status_code in [200, 202]:
            log(f"Updated {item_name} = {state}")
            return True
        else:
            log(f"Failed to update {item_name}: {response.status_code}", "WARNING")
            return False
    
    except Exception as e:
        log(f"Error updating {item_name}: {e}", "ERROR")
        return False

def get_net2_doors(token):
    """Get list of doors from Net2"""
    log("Fetching doors from Net2...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(DOORS_ENDPOINT, headers=headers, timeout=10, verify=NET2_VERIFY)
        if response.status_code == 200:
            doors = response.json()
            log(f"Retrieved {len(doors)} doors")
            return doors
        else:
            log(f"Failed to get doors: {response.status_code}", "ERROR")
            return []
    except Exception as e:
        log(f"Error getting doors: {e}", "ERROR")
        return []

def get_net2_users(token):
    """Get list of users from Net2"""
    log("Fetching users from Net2...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(USERS_ENDPOINT, headers=headers, timeout=10, verify=NET2_VERIFY)
        if response.status_code == 200:
            users = response.json()
            log(f"Retrieved {len(users)} users")
            return users
        else:
            log(f"Failed to get users: {response.status_code}", "ERROR")
            return []
    except Exception as e:
        log(f"Error getting users: {e}", "ERROR")
        return []

def get_recent_events(token, minutes=5):
    """Get recent events from Net2"""
    log(f"Fetching events from last {minutes} minutes...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=minutes)
    
    params = {
        'startDate': start_time.isoformat(),
        'endDate': end_time.isoformat(),
        'pageSize': 100
    }
    
    try:
        response = requests.get(EVENTS_ENDPOINT, headers=headers, params=params, timeout=30, verify=NET2_VERIFY)
        if response.status_code == 200:
            events = response.json()
            log(f"Retrieved {len(events)} events")
            return events
        else:
            log(f"Failed to get events: {response.status_code}", "ERROR")
            return []
    except Exception as e:
        log(f"Error getting events: {e}", "ERROR")
        return []

def sanitize_item_name(name):
    """Convert door/user name to valid OpenHAB item name"""
    import re
    # Convert Danish characters to ASCII equivalents
    replacements = {
        'æ': 'ae', 'ø': 'oe', 'å': 'aa',
        'Æ': 'Ae', 'Ø': 'Oe', 'Å': 'Aa'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    # Remove special characters except word chars, spaces, and hyphens
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces and hyphens with underscores
    name = re.sub(r'[-\s]+', '_', name)
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    return name.strip('_')

def parse_iso_datetime(value):
    """Parse ISO8601 timestamps, handling trailing Z."""
    if not value:
        return None
    try:
        # Handle Zulu suffix
        if isinstance(value, str):
            value = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(value)
        # If timezone-naive, assume UTC to keep comparisons consistent
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def normalize_event_time(value):
    """Return ISO string with timezone; assume local tz if missing."""
    if not value:
        return None
    try:
        if isinstance(value, str):
            value = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return dt.isoformat()
    except Exception:
        return value

def process_events_for_openhab(events):
    """Process events and extract OpenHAB-relevant information"""
    door_states = {}  # device_name: last_event
    user_presence = {}  # user_name: last_seen
    security_events = []
    
    # Door-related event types
    DOOR_EVENT_TYPES = [20, 23, 24, 25, 26, 27, 28, 29, 46, 47, 93]
    
    for event in events:
        event_type = event.get('eventType', 0)
        
        if event_type not in DOOR_EVENT_TYPES:
            continue
        
        # Extract user info
        first_name = event.get('firstName', '')
        middle_name = event.get('middleName', '')
        surname = event.get('surname', '')
        user_name = ' '.join([p for p in [first_name, middle_name, surname] if p]).strip()
        
        if not user_name:
            user_name = 'Unknown'
        
        # Extract event details
        device_name = event.get('deviceName', '')
        event_time = event.get('eventTime', '')
        event_desc = event.get('eventDescription', '')
        
        # Track door entry using ACCESS_GRANTED (contains the actual entry time/user). Treat as OPEN for state.
        if device_name and event_type in ACCESS_GRANTED_TYPES and user_name and user_name != 'Unknown':
            current = door_states.get(device_name)
            incoming_ts = parse_iso_datetime(event_time)
            current_ts = parse_iso_datetime(current['time']) if current else None
            if current is None or (incoming_ts and current_ts and incoming_ts > current_ts) or (incoming_ts and current_ts is None):
                door_states[device_name] = {
                    'state': 'OPEN',
                    'time': event_time,
                    'user': user_name,
                    'event_type': event_type
                }

        # Track explicit door opened events
        if device_name and event_type in DOOR_OPENED_TYPES:
            current = door_states.get(device_name)
            incoming_ts = parse_iso_datetime(event_time)
            current_ts = parse_iso_datetime(current['time']) if current else None
            if current is None or (incoming_ts and current_ts and incoming_ts > current_ts) or (incoming_ts and current_ts is None):
                door_states[device_name] = {
                    'state': 'OPEN',
                    'time': event_time,
                    'user': user_name,
                    'event_type': event_type
                }

        # Track explicit door closed events
        if device_name and event_type in DOOR_CLOSED_TYPES:
            current = door_states.get(device_name)
            incoming_ts = parse_iso_datetime(event_time)
            current_ts = parse_iso_datetime(current['time']) if current else None
            if current is None or (incoming_ts and current_ts and incoming_ts > current_ts) or (incoming_ts and current_ts is None):
                door_states[device_name] = {
                    'state': 'CLOSED',
                    'time': event_time,
                    'user': user_name,
                    'event_type': event_type
                }
        
        # Track user presence (access granted means user entered)
        if event_type in ACCESS_GRANTED_TYPES:
            user_presence[user_name] = {
                'location': device_name,
                'time': event_time,
                'method': 'PIN' if event_type == 26 else 'Card'
            }
        
        # Track security events (access denied)
        if event_type in ACCESS_DENIED_TYPES:
            security_events.append({
                'user': user_name,
                'door': device_name,
                'time': event_time,
                'description': event_desc,
                'severity': 'WARNING'
            })
        
        # Track door held open
        if event_type in DOOR_HELD_OPEN_TYPES:
            security_events.append({
                'user': user_name,
                'door': device_name,
                'time': event_time,
                'description': 'Door held open',
                'severity': 'ALERT'
            })
    
    return door_states, user_presence, security_events

def extract_door_key(device_name):
    """Extract the key part of device name (remove location prefix and direction suffix)"""
    # Remove location prefix (e.g., "Kirkegade50 - ", "Porsevej19 - ", "Terndrupvej 81 - ")
    if ' - ' in device_name:
        parts = device_name.split(' - ', 1)
        if len(parts) > 1:
            device_name = parts[1]
    
    # Remove direction suffix like " (Ind)", " (Ud)"
    if ' (' in device_name:
        device_name = device_name.split(' (')[0]
    
    return device_name.strip()

def sync_to_openhab(token):
    """Sync Net2 data to OpenHAB items"""
    log("Starting sync to OpenHAB...")
    
    # Get recent events
    events = get_recent_events(token, minutes=5)
    door_states, user_presence, security_events = process_events_for_openhab(events)

    # Auto-close doors that only emit an open pulse and no close event
    if AUTO_CLOSE_SECONDS > 0:
        now_ts = datetime.now(timezone.utc)
        for door_name, state_info in list(door_states.items()):
            if state_info.get('state') != 'OPEN':
                continue
            event_ts = parse_iso_datetime(state_info.get('time'))
            if event_ts is None:
                continue
            elapsed = (now_ts - event_ts).total_seconds()
            if elapsed >= AUTO_CLOSE_SECONDS:
                door_states[door_name] = {
                    'state': 'CLOSED',
                    # keep original event time so LastUpdate reflects entry time, not auto-close
                    'time': state_info.get('time'),
                    'user': state_info.get('user', 'auto-close'),
                    'event_type': 'auto_close'
                }
    
    # Merge door states by canonical item to avoid older sister-reader events overwriting newer ones
    merged_door_states = {}
    for door_name, state_info in door_states.items():
        door_key = extract_door_key(door_name)
        if "6612642" in door_key:
            door_key = "Fordør ACU 6612642"
        item_name = f"Net2_Door_{sanitize_item_name(door_key)}"

        incoming_ts = parse_iso_datetime(state_info.get('time'))
        existing = merged_door_states.get(item_name)
        existing_ts = parse_iso_datetime(existing['time']) if existing else None

        # Keep the newest event per item_name
        if existing is None or (incoming_ts and existing_ts and incoming_ts > existing_ts) or (incoming_ts and existing_ts is None):
            merged_door_states[item_name] = {**state_info, 'door_key': door_key}

    # Update door states
    for item_name, state_info in merged_door_states.items():
        # Write door state if present
        if state_info.get('state') in ['OPEN', 'CLOSED']:
            update_openhab_item(f"{item_name}_State", state_info['state'], "String")
        # Only write last user when known to avoid overwriting with "Unknown"
        if state_info.get('user') and state_info.get('user') != 'Unknown':
            update_openhab_item(f"{item_name}_LastUser", state_info['user'], "String")
        # Only write timestamp when it's from a real event (skip auto_close)
        if state_info.get('event_type') != 'auto_close':
            normalized_time = normalize_event_time(state_info.get('time'))
            if normalized_time:
                update_openhab_item(f"{item_name}_LastUpdate", normalized_time, "DateTime")
    
    # Update user presence
    for user_name, presence_info in user_presence.items():
        item_name = f"Net2_User_{sanitize_item_name(user_name)}"
        update_openhab_item(f"{item_name}_Present", True, "Switch")
        update_openhab_item(f"{item_name}_Location", presence_info['location'], "String")
        update_openhab_item(f"{item_name}_LastSeen", presence_info['time'], "DateTime")
    
    # Update security events
    if security_events:
        latest_security_event = security_events[-1]
        update_openhab_item("Net2_Security_LastEvent", latest_security_event['description'], "String")
        update_openhab_item("Net2_Security_LastUser", latest_security_event['user'], "String")
        update_openhab_item("Net2_Security_LastTime", latest_security_event['time'], "DateTime")
        update_openhab_item("Net2_Security_AlertCount", len(security_events), "Number")
    
    # Update overall statistics
    update_openhab_item("Net2_Stats_EventCount", len(events), "Number")
    update_openhab_item("Net2_Stats_ActiveUsers", len(user_presence), "Number")
    update_openhab_item("Net2_Stats_LastSync", datetime.now().isoformat(), "DateTime")
    
    log(f"Sync complete: {len(door_states)} doors, {len(user_presence)} users, {len(security_events)} security events")

def generate_openhab_items(token):
    """Generate OpenHAB items file for Net2 integration"""
    log("Generating OpenHAB items...")
    
    doors = get_net2_doors(token)
    users = get_net2_users(token)
    
    items_content = """// Paxton Net2 Integration Items
// Auto-generated by net2_openhab_integration.py

Group gNet2 "Paxton Net2" <lock>
Group Net2_Doors "Net2 Doors" <door> (gNet2)
Group Net2_Users "Net2 Users" <user> (gNet2)
Group Net2_Security "Net2 Security" <alarm> (gNet2)
Group Net2_Stats "Net2 Statistics" <chart> (gNet2)

// ==============================================
// Global Statistics
// ==============================================
Number Net2_Stats_EventCount "Event Count [%d]" <chart> (Net2_Stats)
Number Net2_Stats_ActiveUsers "Active Users [%d]" <user> (Net2_Stats)
DateTime Net2_Stats_LastSync "Last Sync [%1$tY-%1$tm-%1$td %1$tH:%1$tM]" <time> (Net2_Stats)

// ==============================================
// Security Events
// ==============================================
String Net2_Security_LastEvent "Last Security Event" <alarm> (Net2_Security)
String Net2_Security_LastUser "Last Alert User" <user> (Net2_Security)
DateTime Net2_Security_LastTime "Last Alert Time [%1$tY-%1$tm-%1$td %1$tH:%1$tM]" <time> (Net2_Security)
Number Net2_Security_AlertCount "Alert Count [%d]" <alarm> (Net2_Security)

// ==============================================
// Doors
// ==============================================
"""
    
    for door in doors:
        door_name = door.get('name', '')
        door_id = door.get('id', '')
        safe_name = sanitize_item_name(door_name)
        
        items_content += f"""
// {door_name} (ID: {door_id})
String Net2_Door_{safe_name}_LastUser "Last User" <user> (Net2_Doors)
DateTime Net2_Door_{safe_name}_LastUpdate "Last Update [%1$tY-%1$tm-%1$td %1$tH:%1$tM]" <time> (Net2_Doors)
"""
    
    items_content += """
// ==============================================
// Users
// ==============================================
"""
    
    for user in users:
        first_name = user.get('firstName', '')
        middle_name = user.get('middleName', '')
        last_name = user.get('lastName', '')
        user_id = user.get('id', '')
        
        full_name = ' '.join([p for p in [first_name, middle_name, last_name] if p])
        safe_name = sanitize_item_name(full_name)
        
        items_content += f"""
// {full_name} (ID: {user_id})
Switch Net2_User_{safe_name}_Present "Present" <presence> (Net2_Users)
String Net2_User_{safe_name}_Location "Location" <location> (Net2_Users)
DateTime Net2_User_{safe_name}_LastSeen "Last Seen [%1$tY-%1$tm-%1$td %1$tH:%1$tM]" <time> (Net2_Users)
"""
    
    # Save to file
    output_path = "/etc/openhab/items/net2.items"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(items_content)
        log(f"Items file generated: {output_path}")
        print(f"\n✅ Items file created: {output_path}")
        print(f"   - {len(doors)} doors")
        print(f"   - {len(users)} users")
        print("\nNext steps:")
        print("1. Restart OpenHAB or reload items")
        print("2. Run sync mode: ./net2_openhab_integration.py --mode sync")
        print("3. Or run monitor mode: ./net2_openhab_integration.py --mode monitor")
    except Exception as e:
        log(f"Error writing items file: {e}", "ERROR")

def monitor_mode(token):
    """Continuous monitoring mode"""
    log(f"Starting monitor mode (interval: {args.interval}s)")
    print(f"Monitoring Net2 events and syncing to OpenHAB every {args.interval} seconds...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            sync_to_openhab(token)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        log("Monitor mode terminated")

# -----------------------------
# Main Execution
# -----------------------------
def main():
    print("=" * 60)
    print("Paxton Net2 - OpenHAB Integration")
    print("=" * 60)
    
    # Authenticate
    token = authenticate_net2()
    if not token:
        print("❌ Authentication failed")
        sys.exit(1)
    
    # Execute based on mode
    if args.mode == 'init':
        generate_openhab_items(token)
    
    elif args.mode == 'sync':
        sync_to_openhab(token)
        print("✅ Sync complete")
    
    elif args.mode == 'monitor':
        monitor_mode(token)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
