#!/usr/bin/env python3

"""
Paxton Net2 User Activity Retrieval Script
Retrieves user access events and generates an HTML report
"""

import json
import requests
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import os
import re

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

# -----------------------------
# Configuration Loading
# -----------------------------
def load_config():
    """Load configuration from net2_config.json file"""
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"❌ Configuration file not found: {CONFIG_FILE}")
            sys.exit(1)
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_fields = ['base_url', 'username', 'password', 'grant_type', 'client_id']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"❌ Missing required fields in config: {', '.join(missing_fields)}")
            sys.exit(1)
        
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

# -----------------------------
# Argument Parser
# -----------------------------
parser = argparse.ArgumentParser(
    description='Net2 User Activity Retrieval - Generates HTML report of user access events'
)

parser.add_argument("--hours", type=int, default=24, help="Number of hours to retrieve (default: 24)")
parser.add_argument("--output", default="/etc/openhab/html/net2_activity.html", help="Output HTML file path")
parser.add_argument("--door-dir", default="/etc/openhab/html/doors", help="Directory for per-door HTML files")
parser.add_argument("--refresh", type=int, default=1800, help="HTML auto-refresh interval in seconds (default: 1800 / 30 minutes)")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

args = parser.parse_args()

# Load configuration
config = load_config()

# -----------------------------
# Helper Functions
# -----------------------------
def log(message):
    """Print log message if verbose mode is enabled"""
    if args.verbose:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def authenticate():
    """Authenticate with Paxton Net2 API and return access token"""
    log("Authenticating with Paxton Net2 API...")
    
    payload = {
        'username': config['username'],
        'password': config['password'],
        'grant_type': config['grant_type'],
        'client_id': config['client_id']
    }
    
    auth_endpoint = f"{config['base_url']}/authorization/tokens"

    try:
        response = requests.post(auth_endpoint, data=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"ERROR: Authentication failed with status {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        token = response.json().get("access_token")
        log("Authentication successful")
        return token
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Connection failed - {e}")
        sys.exit(1)

def get_user_events(token, hours=24):
    """Retrieve user access events from the API"""
    log(f"Retrieving events from last {hours} hours...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    events_endpoint = f"{config['base_url']}/events"
    
    # API parameters for event retrieval
    params = {
        'startDate': start_time.isoformat(),
        'endDate': end_time.isoformat(),
        'pageSize': 1000  # Adjust based on expected volume
    }
    
    try:
        response = requests.get(events_endpoint, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            events = response.json()
            log(f"Retrieved {len(events) if isinstance(events, list) else 'N/A'} events")
            return events
        elif response.status_code == 404:
            # Try alternative endpoint structure
            log("Primary endpoint failed, trying alternative...")
            alt_endpoint = f"{BASE_URL}/monitoring/events"
            response = requests.get(alt_endpoint, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                events = response.json()
                log(f"Retrieved {len(events) if isinstance(events, list) else 'N/A'} events from alternative endpoint")
                return events
        
        print(f"WARNING: Failed to retrieve events (status {response.status_code})")
        print(f"Response: {response.text}")
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to retrieve events - {e}")
        return []

def process_events(events):
    """Process events and organize by user"""
    log("Processing events...")
    
    user_activity = defaultdict(list)
    event_summary = {
        'total_events': 0,
        'access_granted': 0,
        'access_denied': 0,
        'door_events': 0,
        'unique_users': set()
    }
    
    # Handle different response structures
    if isinstance(events, dict):
        # If response is paginated or wrapped
        events_list = events.get('events', events.get('data', events.get('results', [])))
    else:
        events_list = events if isinstance(events, list) else []
    
    # Event types for door access (based on Paxton Net2 API)
    ACCESS_GRANTED_TYPES = [20, 26]  # 20=card, 26=PIN
    ACCESS_DENIED_TYPES = [23, 24, 25, 27]  # Various denial reasons
    DOOR_EVENT_TYPES = [20, 23, 24, 25, 26, 27, 28, 29, 46, 47, 93]  # All door-related events
    
    for event in events_list:
        event_type_code = event.get('eventType', 0)
        
        # Only process door-related events
        if event_type_code not in DOOR_EVENT_TYPES:
            continue
        
        event_summary['total_events'] += 1
        event_summary['door_events'] += 1
        
        # Build full user name from components
        first_name = event.get('firstName', '')
        middle_name = event.get('middleName', '')
        surname = event.get('surname', '')
        
        name_parts = [first_name, middle_name, surname]
        user_name = ' '.join([p for p in name_parts if p]).strip()
        
        if not user_name:
            user_name = 'Unknown User'
        
        # Get event details
        event_description = event.get('eventDescription', 'Unknown')
        event_details = event.get('eventDetails', '')
        timestamp = event.get('eventTime', '')
        device_name = event.get('deviceName', 'Unknown Location')
        card_no = event.get('cardNo', '')
        
        # Determine result based on event type
        if event_type_code in ACCESS_GRANTED_TYPES:
            result = 'Access Granted'
            event_summary['access_granted'] += 1
        elif event_type_code in ACCESS_DENIED_TYPES:
            result = 'Access Denied'
            event_summary['access_denied'] += 1
        elif event_type_code in [28, 46]:
            result = 'Door Opened'
        elif event_type_code in [29, 47]:
            result = 'Door Closed'
        elif event_type_code == 93:
            result = 'Door Held Open'
        else:
            result = event_description
        
        event_summary['unique_users'].add(user_name)
        
        user_activity[user_name].append({
            'timestamp': timestamp,
            'event_type': event_description,
            'event_type_code': event_type_code,
            'door': device_name,
            'result': result,
            'details': event_details,
            'card_no': card_no,
            'raw': event  # Keep raw data for debugging
        })
    
    log(f"Processed {event_summary['door_events']} door events (out of {len(events_list)} total) for {len(event_summary['unique_users'])} users")
    
    return user_activity, event_summary

def process_events_by_door(events):
    """Process events and organize by door"""
    log("Processing events by door...")
    
    door_activity = defaultdict(list)
    
    # Handle different response structures
    if isinstance(events, dict):
        events_list = events.get('events', events.get('data', events.get('results', [])))
    else:
        events_list = events if isinstance(events, list) else []
    
    # Event types for door access
    DOOR_EVENT_TYPES = [20, 23, 24, 25, 26, 27, 28, 29, 46, 47, 93]
    ACCESS_GRANTED_TYPES = [20, 26]
    ACCESS_DENIED_TYPES = [23, 24, 25, 27]
    
    for event in events_list:
        event_type_code = event.get('eventType', 0)
        
        # Only process door-related events
        if event_type_code not in DOOR_EVENT_TYPES:
            continue
        
        # Get door/device name
        device_name = event.get('deviceName', 'Unknown Location')
        if not device_name or device_name == 'Unknown Location':
            continue
        
        # Build full user name
        first_name = event.get('firstName', '')
        middle_name = event.get('middleName', '')
        surname = event.get('surname', '')
        name_parts = [first_name, middle_name, surname]
        user_name = ' '.join([p for p in name_parts if p]).strip()
        
        if not user_name:
            user_name = 'Unknown User'
        
        # Get event details
        event_description = event.get('eventDescription', 'Unknown')
        event_details = event.get('eventDetails', '')
        timestamp = event.get('eventTime', '')
        card_no = event.get('cardNo', '')
        
        # Determine result
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
            'details': event_details,
            'card_no': card_no
        })
    
    log(f"Processed events for {len(door_activity)} doors")
    return door_activity

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    if not timestamp_str:
        return "Unknown"
    
    try:
        # Paxton Net2 format: 2026-01-05T06:00:01.017+01:00
        # Remove timezone and milliseconds for parsing
        clean_timestamp = timestamp_str.split('+')[0].split('.')[0]
        dt = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except:
        try:
            # Fallback: try other formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    dt = datetime.strptime(timestamp_str.split('.')[0].split('+')[0], fmt)
                    return dt.strftime('%d-%m-%Y %H:%M:%S')
                except ValueError:
                    continue
            return timestamp_str
        except:
            return str(timestamp_str)

def generate_html(user_activity, event_summary, hours, username):
    """Generate HTML report"""
    log("Generating HTML report...")
    
    now = datetime.now()
    
    # Sort users by most recent activity
    sorted_users = sorted(
        user_activity.items(),
        key=lambda x: max([e.get('timestamp', '') for e in x[1]], default=''),
        reverse=True
    )
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Refresh" content="{args.refresh}">
    <title>Paxton Net2 - User Activity Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2d2e30 0%, #434449 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .user-section {{
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            overflow: hidden;
            background: white;
        }}
        
        .user-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }}
        
        .user-header:hover {{
            background: linear-gradient(135deg, #5568d3 0%, #653a8b 100%);
        }}
        
        .user-name {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        .user-badge {{
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        
        .events-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .events-table th {{
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .events-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .events-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .event-result {{
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .result-granted {{
            background: #d4edda;
            color: #155724;
        }}
        
        .result-denied {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .result-unknown {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .no-events {{
            padding: 40px;
            text-align: center;
            color: #6c757d;
            font-style: italic;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }}
        
        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: 1fr;
            }}
            
            .events-table {{
                font-size: 0.9em;
            }}
            
            .events-table th,
            .events-table td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Paxton Net2 Activity Report</h1>
            <div class="subtitle">User Access Events - Last {hours} Hours</div>
            <div class="subtitle">Generated: {now.strftime('%d-%m-%Y %H:%M:%S')}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{event_summary['total_events']}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(event_summary['unique_users'])}</div>
                <div class="stat-label">Active Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{event_summary['access_granted']}</div>
                <div class="stat-label">Access Granted</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{event_summary['access_denied']}</div>
                <div class="stat-label">Access Denied</div>
            </div>
        </div>
        
        <div class="content">
"""
    
    if not sorted_users:
        html_content += """
            <div class="no-events">
                <h2>No Events Found</h2>
                <p>No user activity recorded in the specified time period.</p>
            </div>
"""
    else:
        for user_name, events in sorted_users:
            event_count = len(events)
            html_content += f"""
            <div class="user-section">
                <div class="user-header">
                    <div class="user-name">{user_name}</div>
                    <div class="user-badge">{event_count} event{'s' if event_count != 1 else ''}</div>
                </div>
                <table class="events-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Event Type</th>
                            <th>Door/Location</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            # Sort events by timestamp (most recent first)
            sorted_events = sorted(events, key=lambda x: x.get('timestamp', ''), reverse=True)
            
            for event in sorted_events:
                timestamp = format_timestamp(event.get('timestamp', ''))
                event_type = event.get('event_type', 'Unknown')
                door = event.get('door', 'Unknown')
                result = str(event.get('result', 'Unknown'))
                details = event.get('details', '')
                
                # Add details if present
                if details:
                    event_type = f"{event_type} - {details}"
                
                # Determine result CSS class
                if 'grant' in result.lower() or 'success' in result.lower():
                    result_class = 'result-granted'
                elif 'deni' in result.lower() or 'deny' in result.lower() or 'fail' in result.lower():
                    result_class = 'result-denied'
                else:
                    result_class = 'result-unknown'
                
                html_content += f"""
                        <tr>
                            <td>{timestamp}</td>
                            <td>{event_type}</td>
                            <td>{door}</td>
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
            Auto-refresh every {args.refresh // 60} minutes | OpenHAB Paxton Net2 Integration<br>
            Generated by: {username}
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def sanitize_filename(name):
    """Convert door name to safe filename"""
    # Remove special characters and replace spaces with underscores
    safe_name = re.sub(r'[^\w\s-]', '', name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return safe_name.lower()

def generate_door_html(door_name, events, refresh_interval, username):
    """Generate HTML report for a specific door"""
    log(f"Generating HTML for door: {door_name}")
    
    now = datetime.now()
    
    # Sort events by timestamp (most recent first) and take top 25
    sorted_events = sorted(events, key=lambda x: x.get('timestamp', ''), reverse=True)[:25]
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Refresh" content="{refresh_interval}">
    <title>{door_name} - Recent Activity</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2d2e30 0%, #434449 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .events-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .events-table th {{
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .events-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .events-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .event-result {{
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .result-granted {{
            background: #d4edda;
            color: #155724;
        }}
        
        .result-denied {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .result-unknown {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }}
        
        .badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin: 20px 0;
            font-weight: 600;
        }}
        
        @media (max-width: 768px) {{
            .events-table {{
                font-size: 0.9em;
            }}
            
            .events-table th,
            .events-table td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚪 {door_name}</h1>
            <div class="subtitle">Last 25 Access Events</div>
            <div class="subtitle">Updated: {now.strftime('%d-%m-%Y %H:%M:%S')}</div>
        </div>
        
        <div class="content">
            <div class="badge">Latest Activity</div>
            
            <table class="events-table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Timestamp</th>
                        <th>Event</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Limit to last 25 events
    for event in sorted_events[:25]:
        user_name = event.get('user_name', 'Unknown')
        timestamp = format_timestamp(event.get('timestamp', ''))
        event_type = event.get('event_type', 'Unknown')
        result = str(event.get('result', 'Unknown'))
        details = event.get('details', '')
        
        # Add details if present
        if details:
            event_type = f"{event_type} - {details}"
        
        # Determine result CSS class
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
        print(f"SUCCESS: Report generated at {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to save HTML file - {e}")
        sys.exit(1)

# -----------------------------
# Main Execution
# -----------------------------
def main():
    print("=" * 60)
    print("Paxton Net2 User Activity Report Generator")
    print("=" * 60)
    
    # Authenticate
    token = authenticate()
    
    # Retrieve events
    events = get_user_events(token, args.hours)
    
    # Process events
    user_activity, event_summary = process_events(events)
    
    # Generate and save main HTML report
    html_content = generate_html(user_activity, event_summary, args.hours, config['username'])
    save_html(html_content, args.output)
    
    # Process events by door
    door_activity = process_events_by_door(events)
    
    # Create door directory if it doesn't exist
    door_dir = args.door_dir
    if not os.path.exists(door_dir):
        os.makedirs(door_dir, exist_ok=True)
        log(f"Created directory: {door_dir}")
    
    # Track which door files should exist
    valid_door_files = set()
    
    # Generate HTML for each door
    door_files = []
    for door_name, door_events in door_activity.items():
        if len(door_events) > 0:
            safe_name = sanitize_filename(door_name)
            door_html_path = os.path.join(door_dir, f"{safe_name}.html")
            valid_door_files.add(os.path.basename(door_html_path))
            door_html = generate_door_html(door_name, door_events, args.refresh, config['username'])
            save_html(door_html, door_html_path)
            door_files.append((door_name, door_html_path, len(door_events)))
    
    # Clean up old HTML files for doors with no activity
    if os.path.exists(door_dir):
        for filename in os.listdir(door_dir):
            if filename.endswith('.html') and filename not in valid_door_files:
                old_file_path = os.path.join(door_dir, filename)
                try:
                    os.remove(old_file_path)
                    log(f"Removed old door file with no activity: {old_file_path}")
                except Exception as e:
                    log(f"Warning: Could not remove old file {old_file_path}: {e}")
    
    print("=" * 60)
    print(f"Total Events: {event_summary['total_events']}")
    print(f"Unique Users: {len(event_summary['unique_users'])}")
    print(f"Access Granted: {event_summary['access_granted']}")
    print(f"Access Denied: {event_summary['access_denied']}")
    print("=" * 60)
    print(f"\nPer-Door Reports Generated: {len(door_files)}")
    for door_name, file_path, event_count in sorted(door_files, key=lambda x: x[2], reverse=True)[:10]:
        print(f"  - {door_name}: {event_count} events -> {file_path}")
    if len(door_files) > 10:
        print(f"  ... and {len(door_files) - 10} more doors")
    print("=" * 60)

if __name__ == "__main__":
    main()
