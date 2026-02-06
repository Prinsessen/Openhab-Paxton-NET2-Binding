#!/usr/bin/env python3
"""
Hikvision ISAPI Event Stream Monitor
Connects to camera's alertStream and displays events in real-time
Enhanced Visual Display
"""

import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os
from collections import defaultdict

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
    UNDERLINE = '\033[4m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BLACK = '\033[30m'

# Camera configuration
CAMERA_IP = "10.0.11.101"
USERNAME = "admin"
PASSWORD = "Jekboapj110"
STREAM_URL = f"http://{CAMERA_IP}/ISAPI/Event/notification/alertStream"

# Event statistics
event_stats = defaultdict(int)
last_events = []
max_history = 10

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_dashboard(current_event=None):
    """Print live dashboard with statistics"""
    clear_screen()
    
    print(f"\n{Colors.BG_BLUE}{Colors.BLACK}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║          🎥  HIKVISION CAMERA EVENT MONITOR - LIVE DASHBOARD  🎥              ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Camera info
    print(f"{Colors.BOLD}📹 Camera:{Colors.ENDC} {Colors.OKCYAN}{CAMERA_IP}{Colors.ENDC} | "
          f"{Colors.BOLD}📺 Channel:{Colors.ENDC} {Colors.OKCYAN}IPdome (Ch1){Colors.ENDC} | "
          f"{Colors.BOLD}🕐 Time:{Colors.ENDC} {Colors.OKCYAN}{datetime.now().strftime('%H:%M:%S')}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}{'═'*84}{Colors.ENDC}\n")
    
    # Current event display (BIG)
    if current_event:
        event_type = current_event['eventType']
        event_state = current_event['eventState']
        
        if event_state == 'active':
            bg_color = Colors.BG_GREEN
            icon = "🔴 🔴 🔴"
            status = "⚠️  ACTIVE EVENT  ⚠️"
        else:
            bg_color = Colors.BG_BLUE
            icon = "🟢 🟢 🟢"
            status = "✅  EVENT CLEARED  ✅"
        
        print(f"{bg_color}{Colors.BLACK}{Colors.BOLD}")
        print(f"  {icon}  {format_event_type(event_type).upper()}  {icon}  ")
        print(f"  {status}  ")
        print(f"{Colors.ENDC}\n")
        
        print(f"{Colors.BOLD}Event Details:{Colors.ENDC}")
        print(f"  ├─ State: {Colors.OKGREEN if event_state == 'active' else Colors.WARNING}{event_state.upper()}{Colors.ENDC}")
        print(f"  ├─ Time: {Colors.OKCYAN}{current_event['dateTime']}{Colors.ENDC}")
        print(f"  └─ Description: {Colors.OKCYAN}{current_event['eventDescription']}{Colors.ENDC}")
        print()
    else:
        print(f"{Colors.BG_BLUE}{Colors.BLACK}{Colors.BOLD}  🟢 🟢 🟢  MONITORING - NO ACTIVE EVENTS  🟢 🟢 🟢  {Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}{'═'*84}{Colors.ENDC}\n")
    
    # Statistics
    print(f"{Colors.BOLD}📊 EVENT STATISTICS:{Colors.ENDC}\n")
    if event_stats:
        for event_type, count in sorted(event_stats.items(), key=lambda x: x[1], reverse=True):
            bar_length = min(30, count)
            bar = "█" * bar_length
            print(f"  {format_event_type(event_type):30} │ {Colors.OKGREEN}{bar}{Colors.ENDC} {count}")
    else:
        print(f"  {Colors.WARNING}No events recorded yet...{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{'═'*84}{Colors.ENDC}\n")
    
    # Recent event history
    print(f"{Colors.BOLD}📜 RECENT EVENT HISTORY (Last {len(last_events)} events):{Colors.ENDC}\n")
    if last_events:
        for i, event in enumerate(reversed(last_events[-10:]), 1):
            state_icon = "🟢" if event['eventState'] == 'active' else "⚪"
            time_str = event['dateTime'].split('T')[1][:8] if 'T' in event['dateTime'] else event['dateTime']
            print(f"  {i:2}. {state_icon} {time_str} │ {format_event_type(event['eventType']):30} │ {event['eventState']}")
    else:
        print(f"  {Colors.WARNING}No events yet...{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{'─'*84}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}💡 Press Ctrl+C to stop monitoring{Colors.ENDC}\n")

def parse_event(xml_data):
    """Parse XML event data"""
    try:
        root = ET.fromstring(xml_data)
        ns = {'ns': 'http://www.hikvision.com/ver20/XMLSchema'}
        
        event = {
            'ip': root.find('.//ns:ipAddress', ns).text if root.find('.//ns:ipAddress', ns) is not None else 'N/A',
            'channel': root.find('.//ns:channelID', ns).text if root.find('.//ns:channelID', ns) is not None else 'N/A',
            'channelName': root.find('.//ns:channelName', ns).text if root.find('.//ns:channelName', ns) is not None else 'N/A',
            'dateTime': root.find('.//ns:dateTime', ns).text if root.find('.//ns:dateTime', ns) is not None else 'N/A',
            'eventType': root.find('.//ns:eventType', ns).text if root.find('.//ns:eventType', ns) is not None else 'N/A',
            'eventState': root.find('.//ns:eventState', ns).text if root.find('.//ns:eventState', ns) is not None else 'N/A',
            'eventDescription': root.find('.//ns:eventDescription', ns).text if root.find('.//ns:eventDescription', ns) is not None else 'N/A',
        }
        return event
    except Exception as e:
        print(f"{Colors.FAIL}Error parsing XML: {e}{Colors.ENDC}")
        return None

def format_event_type(event_type):
    """Format event type with emoji"""
    event_icons = {
        'VMD': '🏃 Motion Detection',
        'videoloss': '📹 Video Loss',
        'tamperdetection': '🔒 Tampering',
        'linedetection': '🚶 Line Crossing',
        'fielddetection': '⚠️  Intrusion',
        'facedetection': '👤 Face Detection',
        'PIR': '🔥 PIR Sensor',
        'unattendedBaggage': '👜 Unattended Bag',
        'attendedBaggage': '🎒 Object Removal',
        'defocus': '🌫️  Defocus',
        'humanBody': '🚶 Human Body',
        'shelterDetection': '🚶 Shelter Detection',
        'peopleDetection': '👥 People Detection',
        'bodyDetection': '🚶 Body Detection',
        'regionEntrance': '➡️  Region Entrance',
        'regionExiting': '⬅️  Region Exit',
    }
    return event_icons.get(event_type, f'📡 {event_type}')

def process_event(event):
    """Process and display event"""
    if not event:
        return
    
    # Update statistics
    event_stats[event['eventType']] += 1
    
    # Log unknown event types to a file for debugging
    known_events = ['VMD', 'videoloss', 'tamperdetection', 'linedetection', 'fielddetection', 
                   'facedetection', 'PIR', 'unattendedBaggage', 'attendedBaggage', 'defocus']
    if event['eventType'] not in known_events:
        with open('/tmp/hikvision_unknown_events.log', 'a') as f:
            f.write(f"{datetime.now()} - Unknown event: {event['eventType']} - State: {event['eventState']}\n")
    
    # Add to history
    last_events.append(event)
    if len(last_events) > max_history:
        last_events.pop(0)
    
    # Show dashboard with current event
    if event['eventState'] == 'active':
        print_dashboard(event)
    else:
        print_dashboard()

def monitor_stream():
    """Monitor the event stream"""
    print_dashboard()
    
    try:
        auth = HTTPDigestAuth(USERNAME, PASSWORD)
        
        print(f"{Colors.OKGREEN}🔌 Connecting to camera...{Colors.ENDC}")
        
        with requests.get(STREAM_URL, auth=auth, stream=True, timeout=None) as response:
            if response.status_code != 200:
                print(f"{Colors.FAIL}❌ Failed to connect. Status: {response.status_code}{Colors.ENDC}")
                return
            
            print(f"{Colors.OKGREEN}✅ Connected! Monitoring events...{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Waiting for events...{Colors.ENDC}\n")
            
            buffer = b""
            boundary = b"--boundary"
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    buffer += chunk
                    
                    # Split by boundary
                    while boundary in buffer:
                        # Find the next boundary
                        idx = buffer.find(boundary)
                        part = buffer[:idx]
                        buffer = buffer[idx + len(boundary):]
                        
                        # Extract XML from the part
                        if b'<EventNotificationAlert' in part:
                            # Find the XML content
                            xml_start = part.find(b'<?xml')
                            if xml_start == -1:
                                xml_start = part.find(b'<EventNotificationAlert')
                            
                            if xml_start != -1:
                                xml_data = part[xml_start:].decode('utf-8', errors='ignore')
                                
                                # Parse and display
                                event = parse_event(xml_data)
                                if event:
                                    process_event(event)
    
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n{Colors.BOLD}{'═'*84}{Colors.ENDC}\n")
        print(f"{Colors.WARNING}🛑 Monitoring stopped by user{Colors.ENDC}\n")
        print(f"{Colors.BOLD}Final Statistics:{Colors.ENDC}\n")
        if event_stats:
            total = sum(event_stats.values())
            for event_type, count in sorted(event_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                print(f"  {format_event_type(event_type):30} │ {count:4} events ({percentage:.1f}%)")
        print(f"\n{Colors.BOLD}{'═'*84}{Colors.ENDC}\n")
        print(f"{Colors.OKGREEN}✅ Total events captured: {sum(event_stats.values())}{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}\n")

if __name__ == "__main__":
    monitor_stream()
