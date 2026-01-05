#!/usr/bin/env python3

"""
Paxton Net2 User Activity Daemon
Continuously polls for user access events and generates HTML reports
"""

import json
import requests
import time
import signal
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import os
import re

# -----------------------------
# Configuration
# -----------------------------
POLL_INTERVAL = 1800  # 30 minutes in seconds
OUTPUT_HTML = "/etc/openhab/html/net2_activity.html"
DOOR_DIR = "/etc/openhab/html/doors"
REFRESH_INTERVAL = 1800  # 30 minutes in seconds
LOG_FILE = "/var/log/openhab/net2-daemon.log"
HOURS_TO_RETRIEVE = 24

# API Configuration
BASE_URL = "https://milestone.agesen.dk:8443/api/v1"
AUTH_ENDPOINT = f"{BASE_URL}/authorization/tokens"
EVENTS_ENDPOINT = f"{BASE_URL}/events"
USERS_ENDPOINT = f"{BASE_URL}/users"

username = "Nanna Agesen"
password = "Jekboapj110"
grant_type = "password"
client_id = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

# Global flag for graceful shutdown
shutdown_requested = False

# -----------------------------
# Signal Handlers
# -----------------------------
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    log(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# -----------------------------
# Helper Functions
# -----------------------------
def log(message):
    """Log message to file and stdout"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
    except Exception as e:
        print(f"Failed to write to log file: {e}")

def authenticate():
    """Authenticate with Paxton Net2 API and return access token"""
    log("Authenticating with Paxton Net2 API...")
    
    payload = {
        'username': username,
        'password': password,
        'grant_type': grant_type,
        'client_id': client_id
    }

    try:
        response = requests.post(AUTH_ENDPOINT, data=payload, timeout=10)
        
        if response.status_code != 200:
            log(f"ERROR: Authentication failed with status {response.status_code}")
            return None
        
        token = response.json().get("access_token")
        log("Authentication successful")
        return token
    
    except requests.exceptions.RequestException as e:
        log(f"ERROR: Connection failed - {e}")
        return None

def get_user_events(token, hours=24):
    """Retrieve user access events from the API"""
    log(f"Retrieving events from last {hours} hours...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    params = {
        'startDate': start_time.isoformat(),
        'endDate': end_time.isoformat(),
        'pageSize': 1000
    }
    
    try:
        response = requests.get(EVENTS_ENDPOINT, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            events = response.json()
            log(f"Retrieved {len(events) if isinstance(events, list) else 'N/A'} events")
            return events
        else:
            log(f"WARNING: Failed to retrieve events (status {response.status_code})")
            return []
    
    except requests.exceptions.RequestException as e:
        log(f"ERROR: Failed to retrieve events - {e}")
        return []

def process_events(events):
    """Process events and organize by user"""
    log("Processing events...")
    
    user_activity = defaultdict(lambda: {'events': [], 'last_seen': None, 'access_count': 0})
    
    if isinstance(events, dict):
        events_list = events.get('events', events.get('data', events.get('results', [])))
    else:
        events_list = events if isinstance(events, list) else []
    
    DOOR_EVENT_TYPES = [20, 23, 24, 25, 26, 27, 28, 29, 46, 47, 93]
    ACCESS_GRANTED_TYPES = [20, 26]
    ACCESS_DENIED_TYPES = [23, 24, 25, 27]
    
    total_events = 0
    door_events = 0
    access_granted = 0
    access_denied = 0
    unique_users = set()
    
    for event in events_list:
        total_events += 1
        event_type_code = event.get('eventType', 0)
        
        if event_type_code not in DOOR_EVENT_TYPES:
            continue
        
        door_events += 1
        
        first_name = event.get('firstName', '')
        middle_name = event.get('middleName', '')
        surname = event.get('surname', '')
        name_parts = [first_name, middle_name, surname]
        user_name = ' '.join([p for p in name_parts if p]).strip()
        
        if not user_name:
            user_name = 'Unknown User'
        
        unique_users.add(user_name)
        
        event_description = event.get('eventDescription', 'Unknown')
        event_details = event.get('eventDetails', '')
        timestamp = event.get('eventTime', '')
        device_name = event.get('deviceName', 'Unknown Location')
        
        if event_type_code in ACCESS_GRANTED_TYPES:
            result = 'Access Granted'
            access_granted += 1
        elif event_type_code in ACCESS_DENIED_TYPES:
            result = 'Access Denied'
            access_denied += 1
        elif event_type_code in [28, 46]:
            result = 'Door Opened'
        elif event_type_code in [29, 47]:
            result = 'Door Closed'
        elif event_type_code == 93:
            result = 'Door Held Open'
        else:
            result = event_description
        
        user_activity[user_name]['events'].append({
            'timestamp': timestamp,
            'location': device_name,
            'event_type': event_description,
            'result': result,
            'details': event_details
        })
        
        if user_activity[user_name]['last_seen'] is None or timestamp > user_activity[user_name]['last_seen']:
            user_activity[user_name]['last_seen'] = timestamp
        
        if result == 'Access Granted':
            user_activity[user_name]['access_count'] += 1
    
    log(f"Processed {door_events} door events (out of {total_events} total) for {len(unique_users)} users")
    
    event_summary = {
        'total_events': door_events,
        'access_granted': access_granted,
        'access_denied': access_denied,
        'unique_users': unique_users
    }
    
    return user_activity, event_summary

def process_events_by_door(events):
    """Process events and organize by door"""
    log("Processing events by door...")
    
    door_activity = defaultdict(list)
    
    if isinstance(events, dict):
        events_list = events.get('events', events.get('data', events.get('results', [])))
    else:
        events_list = events if isinstance(events, list) else []
    
    DOOR_EVENT_TYPES = [20, 23, 24, 25, 26, 27, 28, 29, 46, 47, 93]
    ACCESS_GRANTED_TYPES = [20, 26]
    ACCESS_DENIED_TYPES = [23, 24, 25, 27]
    
    for event in events_list:
        event_type_code = event.get('eventType', 0)
        
        if event_type_code not in DOOR_EVENT_TYPES:
            continue
        
        device_name = event.get('deviceName', 'Unknown Location')
        if not device_name or device_name == 'Unknown Location':
            continue
        
        first_name = event.get('firstName', '')
        middle_name = event.get('middleName', '')
        surname = event.get('surname', '')
        name_parts = [first_name, middle_name, surname]
        user_name = ' '.join([p for p in name_parts if p]).strip()
        
        if not user_name:
            user_name = 'Unknown User'
        
        event_description = event.get('eventDescription', 'Unknown')
        event_details = event.get('eventDetails', '')
        timestamp = event.get('eventTime', '')
        
        if event_type_code in ACCESS_GRANTED_TYPES:
            result = 'Access Granted'
        elif event_type_code in ACCESS_DENIED_TYPES:
            result = 'Access Denied'
        elif event_type_code in [28, 46]:
            result = 'Door Opened'
        elif event_type_code in [29, 47]:
            result = 'Door Closed'
        elif event_type_code == 93:
            result = 'Door Held Open'
        else:
            result = event_description
        
        door_activity[device_name].append({
            'user_name': user_name,
            'timestamp': timestamp,
            'event_type': event_description,
            'result': result,
            'details': event_details
        })
    
    log(f"Processed events for {len(door_activity)} doors")
    return door_activity

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    if not timestamp_str:
        return "Unknown"
    
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def sanitize_filename(name):
    """Convert door name to safe filename"""
    name = name.lower()
    name = re.sub(r'[^a-z0-9_\-]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def generate_html(user_activity, event_summary, hours, refresh_interval):
    """Generate main HTML report"""
    log("Generating HTML report...")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{refresh_interval}">
    <title>Paxton Net2 User Activity</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; transition: transform 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); box-shadow: 0 5px 20px rgba(0,0,0,0.2); }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .stat-label {{ color: #666; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }}
        .content {{ padding: 30px; }}
        .user-section {{ margin-bottom: 30px; background: #f8f9fa; border-radius: 10px; overflow: hidden; }}
        .user-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .user-header:hover {{ background: linear-gradient(135deg, #7686f0 0%, #8656b0 100%); }}
        .user-name {{ font-size: 1.3em; font-weight: bold; }}
        .user-stats {{ font-size: 0.9em; opacity: 0.9; }}
        .events-table {{ width: 100%; border-collapse: collapse; }}
        .events-table th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        .events-table td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; }}
        .events-table tr:hover {{ background: #f5f5f5; }}
        .event-result {{ padding: 5px 10px; border-radius: 5px; font-weight: bold; display: inline-block; }}
        .result-granted {{ background: #d4edda; color: #155724; }}
        .result-denied {{ background: #f8d7da; color: #721c24; }}
        .result-unknown {{ background: #e2e3e5; color: #383d41; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; border-top: 1px solid #e0e0e0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Paxton Net2 User Activity</h1>
            <p>Last {hours} hours of access activity</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Events</div>
                <div class="stat-value">{event_summary['total_events']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Access Granted</div>
                <div class="stat-value">{event_summary['access_granted']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Access Denied</div>
                <div class="stat-value">{event_summary['access_denied']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Users</div>
                <div class="stat-value">{len(event_summary['unique_users'])}</div>
            </div>
        </div>
        
        <div class="content">
"""
    
    for user_name in sorted(user_activity.keys()):
        user_data = user_activity[user_name]
        sorted_events = sorted(user_data['events'], key=lambda x: x.get('timestamp', ''), reverse=True)
        
        html_content += f"""
            <div class="user-section">
                <div class="user-header">
                    <div class="user-name">👤 {user_name}</div>
                    <div class="user-stats">
                        {user_data['access_count']} accesses | Last seen: {format_timestamp(user_data['last_seen'])}
                    </div>
                </div>
                <table class="events-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Location</th>
                            <th>Event Type</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for event in sorted_events[:50]:
            timestamp = format_timestamp(event.get('timestamp', ''))
            location = event.get('location', 'Unknown')
            event_type = event.get('event_type', 'Unknown')
            result = str(event.get('result', 'Unknown'))
            details = event.get('details', '')
            
            if details:
                event_type = f"{event_type} - {details}"
            
            if 'grant' in result.lower() or 'success' in result.lower():
                result_class = 'result-granted'
            elif 'deni' in result.lower() or 'deny' in result.lower() or 'fail' in result.lower():
                result_class = 'result-denied'
            else:
                result_class = 'result-unknown'
            
            html_content += f"""
                        <tr>
                            <td>{timestamp}</td>
                            <td>{location}</td>
                            <td>{event_type}</td>
                            <td><span class="event-result {result_class}">{result}</span></td>
                        </tr>
"""
        
        html_content += """
                    </tbody>
                </table>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="footer">
            Auto-refresh every {refresh_interval // 60} minutes | OpenHAB Paxton Net2 Integration<br>
            Generated by: {username}
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def generate_door_html(door_name, door_events, refresh_interval):
    """Generate per-door HTML report"""
    log(f"Generating HTML for door: {door_name}")
    
    sorted_events = sorted(door_events, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{refresh_interval}">
    <title>{door_name} - Activity Log</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ font-size: 0.9em; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .events-table {{ width: 100%; border-collapse: collapse; }}
        .events-table th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
        .events-table td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; }}
        .events-table tr:hover {{ background: #f5f5f5; }}
        .event-result {{ padding: 5px 10px; border-radius: 5px; font-weight: bold; }}
        .result-granted {{ background: #d4edda; color: #155724; }}
        .result-denied {{ background: #f8d7da; color: #721c24; }}
        .result-unknown {{ background: #e2e3e5; color: #383d41; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚪 {door_name}</h1>
            <p>Activity Log - {len(sorted_events)} events</p>
            <p style="margin-top: 10px;">Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <table class="events-table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Timestamp</th>
                        <th>Event Type</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for event in sorted_events:
        user_name = event.get('user_name', 'Unknown')
        timestamp = format_timestamp(event.get('timestamp', ''))
        event_type = event.get('event_type', 'Unknown')
        result = str(event.get('result', 'Unknown'))
        details = event.get('details', '')
        
        if details:
            event_type = f"{event_type} - {details}"
        
        if 'grant' in result.lower() or 'success' in result.lower():
            result_class = 'result-granted'
        elif 'deni' in result.lower() or 'deny' in result.lower() or 'fail' in result.lower():
            result_class = 'result-denied'
        else:
            result_class = 'result-unknown'
        
        html_content += f"""
                    <tr>
                        <td><strong>{user_name}</strong></td>
                        <td>{timestamp}</td>
                        <td>{event_type}</td>
                        <td><span class="event-result {result_class}">{result}</span></td>
                    </tr>
"""
    
    html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            Auto-refresh every {refresh_interval // 60} minutes | OpenHAB Paxton Net2 Integration<br>
            Generated by: {username}
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def save_html(html_content, output_path):
    """Save HTML content to file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        log(f"HTML report saved to {output_path}")
    except Exception as e:
        log(f"ERROR: Failed to save HTML file - {e}")

def poll_and_update():
    """Single poll cycle - retrieve and update reports"""
    try:
        # Authenticate
        token = authenticate()
        if not token:
            log("Failed to authenticate, skipping this poll cycle")
            return
        
        # Retrieve events
        events = get_user_events(token, HOURS_TO_RETRIEVE)
        if not events:
            log("No events retrieved, skipping update")
            return
        
        # Process events
        user_activity, event_summary = process_events(events)
        
        # Generate and save main HTML report
        html_content = generate_html(user_activity, event_summary, HOURS_TO_RETRIEVE, REFRESH_INTERVAL)
        save_html(html_content, OUTPUT_HTML)
        
        # Process events by door
        door_activity = process_events_by_door(events)
        
        # Create door directory if needed
        if not os.path.exists(DOOR_DIR):
            os.makedirs(DOOR_DIR, exist_ok=True)
            log(f"Created directory: {DOOR_DIR}")
        
        # Track valid door files
        valid_door_files = set()
        
        # Generate HTML for each door
        for door_name, door_events in door_activity.items():
            if len(door_events) > 0:
                safe_name = sanitize_filename(door_name)
                door_html_path = os.path.join(DOOR_DIR, f"{safe_name}.html")
                valid_door_files.add(os.path.basename(door_html_path))
                door_html = generate_door_html(door_name, door_events, REFRESH_INTERVAL)
                save_html(door_html, door_html_path)
        
        # Clean up old door HTML files (only those created by this script)
        # Only remove files that match our naming pattern (sanitized door names)
        if os.path.exists(DOOR_DIR):
            for filename in os.listdir(DOOR_DIR):
                # Only process files that end with .html and match our pattern
                if filename.endswith('.html') and filename not in valid_door_files:
                    # Only remove if it looks like a door file (contains door identifiers)
                    # Skip net2_activity.html and other non-door files
                    if filename == 'net2_activity.html':
                        continue
                    # Only remove files with our specific naming pattern (door names with ACU, etc.)
                    if any(pattern in filename.lower() for pattern in ['acu', 'central', 'hikvision', 'ford_r', 'garage']):
                        old_file_path = os.path.join(DOOR_DIR, filename)
                        try:
                            os.remove(old_file_path)
                            log(f"Removed old door file: {old_file_path}")
                        except Exception as e:
                            log(f"Warning: Could not remove {old_file_path}: {e}")
        
        log(f"Poll cycle completed: {event_summary['total_events']} events, {len(event_summary['unique_users'])} users, {len(door_activity)} doors")
        
    except Exception as e:
        log(f"ERROR in poll cycle: {e}")

# -----------------------------
# Main Daemon Loop
# -----------------------------
def main():
    """Main daemon loop"""
    log("=" * 60)
    log("Paxton Net2 User Activity Daemon Starting")
    log(f"Poll interval: {POLL_INTERVAL} seconds ({POLL_INTERVAL/60} minutes)")
    log(f"Output: {OUTPUT_HTML}")
    log(f"Door reports: {DOOR_DIR}")
    log("=" * 60)
    
    # Initial poll
    poll_and_update()
    
    # Main loop
    while not shutdown_requested:
        try:
            # Sleep in small increments to allow quick shutdown
            for _ in range(POLL_INTERVAL):
                if shutdown_requested:
                    break
                time.sleep(1)
            
            if not shutdown_requested:
                poll_and_update()
        
        except KeyboardInterrupt:
            log("Received keyboard interrupt")
            break
        except Exception as e:
            log(f"ERROR in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying on error
    
    log("Daemon shutting down")
    log("=" * 60)

if __name__ == "__main__":
    main()
