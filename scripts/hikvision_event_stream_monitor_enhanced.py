#!/usr/bin/env python3
"""
Hikvision Enhanced Event Monitor with Smart Detection Polling
Monitors alertStream + polls ContentMgmt API for body/face detections (firmware workaround)
"""

import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import sys
import os
from collections import defaultdict
import threading
import time

# Color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BLACK = '\033[30m'

# Camera configuration
CAMERA_IP = "10.0.11.101"
USERNAME = "admin"
PASSWORD = "Jekboapj110"
STREAM_URL = f"http://{CAMERA_IP}/ISAPI/Event/notification/alertStream"
SEARCH_URL = f"http://{CAMERA_IP}/ISAPI/ContentMgmt/search"

# Event tracking
event_stats = defaultdict(int)
last_events = []
max_history = 10
last_search_time = None
smart_event_cache = set()
search_enabled = True

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def format_event_type(event_type):
    """Format event type with emoji icon"""
    event_icons = {
        'VMD': '🏃 Motion Detection',
        'videoloss': '📹 Video Loss',
        'mixedTargetDetection': '👤 Smart Body Detection',
        'faceDetection': '😊 Face Detection',
        'linedetection': '🚷 Line Crossing',
        'fielddetection': '🔍 Field Detection',
        'regionEntrance': '➡️  Region Entrance',
        'regionExiting': '⬅️  Region Exit',
        'tamperdetection': '⚠️  Tamper Detection',
    }
    return event_icons.get(event_type, f'📡 {event_type}')

def print_dashboard(current_event=None, polling_status=None):
    """Print live dashboard"""
    clear_screen()
    
    print("\n╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║     🎥  HIKVISION ENHANCED EVENT MONITOR - LIVE DASHBOARD  🎥                ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝\n")
    
    print(f"\n📹 Camera: {CAMERA_IP} | 📺 Channel: IPdome (Ch1) | 🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
    
    if polling_status:
        print(f"🔍 Smart Detection Polling: {Colors.OKGREEN}ACTIVE{Colors.ENDC} | Last check: {polling_status}")
    
    print("\n════════════════════════════════════════════════════════════════════════════════════\n")
    
    # Current event display
    if current_event:
        event_type = current_event.get('eventType', 'Unknown')
        state = current_event.get('activePostCount', 'unknown')
        
        if state == '0':
            print(f"  🔵 🔵 🔵  {format_event_type(event_type)}  🔵 🔵 🔵  ")
            print(f"  ℹ️   EVENT CLEARED  ℹ️  \n")
        else:
            print(f"  🔴 🔴 🔴  {format_event_type(event_type)}  🔴 🔴 🔴  ")
            print(f"  ⚠️  ACTIVE EVENT  ⚠️  \n")
        
        print("Event Details:")
        print(f"  ├─ State: {'ACTIVE' if state != '0' else 'CLEARED'}")
        print(f"  ├─ Time: {current_event.get('dateTime', 'N/A')}")
        print(f"  └─ Description: {current_event.get('eventDescription', 'N/A')}")
    
    print("\n════════════════════════════════════════════════════════════════════════════════════")
    
    # Event statistics
    print("\n📊 EVENT STATISTICS:\n")
    if event_stats:
        max_count = max(event_stats.values()) if event_stats else 1
        for event_type, count in sorted(event_stats.items(), key=lambda x: x[1], reverse=True):
            bar_length = int((count / max_count) * 30)
            bar = '█' * bar_length
            color = Colors.BG_MAGENTA if event_type == 'mixedTargetDetection' else ''
            print(f"  {color}{format_event_type(event_type):<30}{Colors.ENDC} │ {bar} {count}")
    else:
        print("  No events received yet...")
    
    print("\n════════════════════════════════════════════════════════════════════════════════════")
    
    # Recent history
    print("\n📜 RECENT EVENT HISTORY (Last 10 events):\n")
    if last_events:
        for i, event in enumerate(last_events[:max_history], 1):
            event_type = event.get('eventType', 'Unknown')
            state = event.get('state', 'unknown')
            timestamp = event.get('time', 'N/A')
            
            if state == 'active':
                indicator = '🟢'
            else:
                indicator = '⚪'
            
            print(f"   {i:2d}. {indicator} {timestamp} │ {format_event_type(event_type):<30} │ {state}")
    else:
        print("  No events yet...")
    
    print("\n────────────────────────────────────────────────────────────────────────────────────")
    print("💡 Press Ctrl+C to stop monitoring\n")

def process_event(event_type, active_post_count, date_time, description):
    """Process and log an event"""
    event_stats[event_type] += 1
    
    state = 'active' if active_post_count != '0' else 'inactive'
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    last_events.insert(0, {
        'eventType': event_type,
        'state': state,
        'time': timestamp
    })
    
    # Log to file
    with open('/tmp/hikvision_all_events.log', 'a') as f:
        f.write(f"{datetime.now()} - Event: {event_type} - State: {state} - Desc: {description}\n")
    
    return {
        'eventType': event_type,
        'activePostCount': active_post_count,
        'dateTime': date_time,
        'eventDescription': description
    }

def poll_smart_detections():
    """Poll camera's ContentMgmt search API for mixedTargetDetection events"""
    global last_search_time, smart_event_cache, search_enabled
    
    if not search_enabled:
        return
    
    try:
        # Search from last check to now
        now = datetime.now(timezone.utc)
        start_time = (last_search_time or (now - timedelta(minutes=1))).strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        search_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<CMSearchDescription>
    <searchID>S{int(time.time())}</searchID>
    <trackIDList>
        <trackID>1</trackID>
    </trackIDList>
    <timeSpanList>
        <timeSpan>
            <startTime>{start_time}</startTime>
            <endTime>{end_time}</endTime>
        </timeSpan>
    </timeSpanList>
    <maxResults>100</maxResults>
    <searchResultPostion>0</searchResultPostion>
    <metadataList>
        <metadataDescriptor>
            <metadataType>mixedTargetDetection</metadataType>
        </metadataDescriptor>
    </metadataList>
</CMSearchDescription>'''
        
        response = requests.post(
            SEARCH_URL,
            auth=HTTPDigestAuth(USERNAME, PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=search_xml,
            timeout=5
        )
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            matches = root.findall('.//{http://www.hikvision.com/ver20/XMLSchema}searchMatchItem')
            
            for match in matches:
                timespan = match.find('.//{http://www.hikvision.com/ver20/XMLSchema}timeSpan')
                if timespan is not None:
                    start = timespan.find('.//{http://www.hikvision.com/ver20/XMLSchema}startTime')
                    if start is not None and start.text:
                        event_key = f"{start.text}"
                        
                        # Only process new events
                        if event_key not in smart_event_cache:
                            smart_event_cache.add(event_key)
                            
                            # Limit cache size
                            if len(smart_event_cache) > 1000:
                                smart_event_cache.clear()
                            
                            # Process as event
                            process_event(
                                'mixedTargetDetection',
                                '1',  # active
                                start.text,
                                'Smart body/face detection'
                            )
        
        last_search_time = now
        
    except Exception as e:
        print(f"Smart detection poll error: {e}", file=sys.stderr)

def smart_detection_poller():
    """Background thread to poll for smart detections"""
    global last_search_time
    last_search_time = datetime.now(timezone.utc) - timedelta(seconds=30)
    
    while search_enabled:
        try:
            poll_smart_detections()
            time.sleep(5)  # Poll every 5 seconds
        except Exception as e:
            print(f"Poller thread error: {e}", file=sys.stderr)
            time.sleep(5)

def main():
    """Main event stream monitoring"""
    global search_enabled
    
    print(f"{Colors.BOLD}Hikvision Enhanced Event Monitor{Colors.ENDC}")
    print(f"Camera: {CAMERA_IP}")
    print(f"Stream URL: {STREAM_URL}")
    print(f"Smart Detection Polling: ENABLED (every 5s)")
    print(f"Press Ctrl+C to stop\n")
    
    # Start smart detection poller thread
    poller_thread = threading.Thread(target=smart_detection_poller, daemon=True)
    poller_thread.start()
    
    try:
        response = requests.get(
            STREAM_URL,
            auth=HTTPDigestAuth(USERNAME, PASSWORD),
            stream=True,
            timeout=None
        )
        
        if response.status_code != 200:
            print(f"{Colors.FAIL}Failed to connect to alert stream: {response.status_code}{Colors.ENDC}")
            return
        
        buffer = b""
        boundary = None
        current_event = None
        POLL_STATUS = ""
        
        for chunk in response.iter_content(chunk_size=1024):
            if not chunk:
                continue
                
            buffer += chunk
            
            # Find boundary
            if boundary is None and b'boundary=' in buffer:
                boundary_start = buffer.find(b'boundary=') + 9
                boundary_end = buffer.find(b'\r\n', boundary_start)
                if boundary_end > boundary_start:
                    boundary = buffer[boundary_start:boundary_end].strip()
            
            # Process complete events
            if boundary and boundary in buffer:
                parts = buffer.split(b'--' + boundary)
                
                for part in parts[:-1]:
                    if b'<EventNotificationAlert' in part:
                        try:
                            xml_start = part.find(b'<EventNotificationAlert')
                            xml_end = part.find(b'</EventNotificationAlert>') + len(b'</EventNotificationAlert>')
                            
                            if xml_start >= 0 and xml_end > xml_start:
                                xml_data = part[xml_start:xml_end]
                                root = ET.fromstring(xml_data)
                                
                                event_type = root.find('.//{http://www.hikvision.com/ver20/XMLSchema}eventType')
                                active_post_count = root.find('.//{http://www.hikvision.com/ver20/XMLSchema}activePostCount')
                                date_time = root.find('.//{http://www.hikvision.com/ver20/XMLSchema}dateTime')
                                event_desc = root.find('.//{http://www.hikvision.com/ver20/XMLSchema}eventDescription')
                                
                                if event_type is not None:
                                    current_event = process_event(
                                        event_type.text,
                                        active_post_count.text if active_post_count is not None else '0',
                                        date_time.text if date_time is not None else 'N/A',
                                        event_desc.text if event_desc is not None else 'N/A'
                                    )
                                    
                                    # Update poll status
                                    if last_search_time:
                                        POLL_STATUS = last_search_time.strftime('%H:%M:%S')
                                    
                                    print_dashboard(current_event, POLL_STATUS)
                        
                        except ET.ParseError as e:
                            pass
                
                buffer = b'--' + boundary + parts[-1]
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BOLD}=== Final Statistics ==={Colors.ENDC}")
        for event_type, count in sorted(event_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"{format_event_type(event_type)}: {count}")
        print("\nMonitoring stopped.\n")
        search_enabled = False
    
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}\n")
        search_enabled = False

if __name__ == "__main__":
    main()
