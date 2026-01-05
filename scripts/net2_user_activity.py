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

# -----------------------------
# Argument Parser
# -----------------------------
parser = argparse.ArgumentParser(
    description='Net2 User Activity Retrieval - Generates HTML report of user access events'
)

parser.add_argument("--hours", type=int, default=24, help="Number of hours to retrieve (default: 24)")
parser.add_argument("--output", default="/etc/openhab/html/net2_activity.html", help="Output HTML file path")
parser.add_argument("--refresh", type=int, default=60, help="HTML auto-refresh interval in seconds (default: 60)")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

args = parser.parse_args()

# -----------------------------
# API Configuration
# -----------------------------
BASE_URL = "https://milestone.agesen.dk:8443/api/v1"
AUTH_ENDPOINT = f"{BASE_URL}/authorization/tokens"
EVENTS_ENDPOINT = f"{BASE_URL}/events"
USERS_ENDPOINT = f"{BASE_URL}/users"

username = "Nanna Agesen"
password = "Jekboapj110"
grant_type = "password"
client_id = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

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
        'username': username,
        'password': password,
        'grant_type': grant_type,
        'client_id': client_id
    }

    try:
        response = requests.post(AUTH_ENDPOINT, data=payload, timeout=10)
        
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
    
    # API parameters for event retrieval
    params = {
        'startDate': start_time.isoformat(),
        'endDate': end_time.isoformat(),
        'pageSize': 1000  # Adjust based on expected volume
    }
    
    try:
        response = requests.get(EVENTS_ENDPOINT, headers=headers, params=params, timeout=30)
        
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
        'unique_users': set()
    }
    
    # Handle different response structures
    if isinstance(events, dict):
        # If response is paginated or wrapped
        events_list = events.get('events', events.get('data', events.get('results', [])))
    else:
        events_list = events if isinstance(events, list) else []
    
    for event in events_list:
        event_summary['total_events'] += 1
        
        # Extract user information (field names may vary)
        user_name = event.get('userName', event.get('UserName', event.get('user', 'Unknown')))
        event_type = event.get('eventType', event.get('EventType', event.get('type', 'Unknown')))
        timestamp = event.get('timestamp', event.get('Timestamp', event.get('dateTime', '')))
        door_name = event.get('doorName', event.get('DoorName', event.get('door', 'Unknown')))
        result = event.get('result', event.get('Result', event.get('status', 'Unknown')))
        
        # Track statistics
        if 'grant' in str(result).lower() or 'success' in str(result).lower():
            event_summary['access_granted'] += 1
        elif 'deni' in str(result).lower() or 'fail' in str(result).lower():
            event_summary['access_denied'] += 1
        
        event_summary['unique_users'].add(user_name)
        
        user_activity[user_name].append({
            'timestamp': timestamp,
            'event_type': event_type,
            'door': door_name,
            'result': result,
            'raw': event  # Keep raw data for debugging
        })
    
    log(f"Processed {event_summary['total_events']} events for {len(event_summary['unique_users'])} users")
    
    return user_activity, event_summary

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    if not timestamp_str:
        return "Unknown"
    
    try:
        # Try different timestamp formats
        for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
            try:
                dt = datetime.strptime(timestamp_str.split('.')[0].split('+')[0], fmt)
                return dt.strftime('%d-%m-%Y %H:%M:%S')
            except ValueError:
                continue
        return timestamp_str
    except:
        return str(timestamp_str)

def generate_html(user_activity, event_summary, hours):
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
                
                # Determine result CSS class
                if 'grant' in result.lower() or 'success' in result.lower():
                    result_class = 'result-granted'
                elif 'deni' in result.lower() or 'fail' in result.lower():
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
            Auto-refresh every {args.refresh} seconds | OpenHAB Paxton Net2 Integration
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
    
    # Generate HTML
    html_content = generate_html(user_activity, event_summary, args.hours)
    
    # Save HTML
    save_html(html_content, args.output)
    
    print("=" * 60)
    print(f"Total Events: {event_summary['total_events']}")
    print(f"Unique Users: {len(event_summary['unique_users'])}")
    print(f"Access Granted: {event_summary['access_granted']}")
    print(f"Access Denied: {event_summary['access_denied']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
