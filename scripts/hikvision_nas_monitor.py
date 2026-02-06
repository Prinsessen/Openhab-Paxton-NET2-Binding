#!/usr/bin/env python3
"""
Hikvision NAS Folder Monitor
Monitors NAS folder for new picture uploads from body/face detection
Treats new files as body detection events since camera sends pictures on detection
"""

import os
import time
from datetime import datetime
from collections import defaultdict

# NAS Configuration
NAS_PATH = "/mnt/camera_nas"  # Mount point for \\10.0.5.25\Agesen_Storange4\Camera
CHECK_INTERVAL = 2  # Check every 2 seconds

# Track files we've seen
known_files = set()
event_stats = defaultdict(int)

class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    BG_GREEN = '\033[42m'
    BLACK = '\033[30m'

def clear_screen():
    os.system('clear')

def check_nas_folder():
    """Check NAS folder for new files"""
    if not os.path.exists(NAS_PATH):
        print(f"{Colors.FAIL}NAS path not mounted: {NAS_PATH}{Colors.ENDC}")
        print(f"Mount it with: sudo mount -t cifs //10.0.5.25/Agesen_Storange4/Camera {NAS_PATH} -o username=Hikvision,password=XXX")
        return []
    
    new_files = []
    try:
        for root, dirs, files in os.walk(NAS_PATH):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(root, filename)
                    if filepath not in known_files:
                        known_files.add(filepath)
                        new_files.append((filepath, filename, os.path.getmtime(filepath)))
    except Exception as e:
        print(f"{Colors.FAIL}Error reading NAS: {e}{Colors.ENDC}")
    
    return new_files

def print_detection(filename, filepath, mtime):
    """Print detection event"""
    timestamp = datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
    
    # Try to determine if it's face or body from filename
    detection_type = "👤 Body/Face Detection"
    if 'face' in filename.lower():
        detection_type = "👤 Face Detection"
        event_stats['face'] += 1
    elif 'body' in filename.lower() or 'human' in filename.lower():
        detection_type = "🚶 Body Detection"
        event_stats['body'] += 1
    else:
        detection_type = "👤 Smart Detection"
        event_stats['smart'] += 1
    
    clear_screen()
    print("\n" + "="*80)
    print(f"{Colors.BG_GREEN}{Colors.BLACK}  🔔 {detection_type} DETECTED! 🔔  {Colors.ENDC}")
    print("="*80)
    print(f"\n⏰ Time: {timestamp}")
    print(f"📁 File: {filename}")
    print(f"📂 Path: {filepath}")
    print(f"\n📊 Total Detections:")
    print(f"   Face: {event_stats['face']}")
    print(f"   Body: {event_stats['body']}")
    print(f"   Smart: {event_stats['smart']}")
    print(f"   Total: {sum(event_stats.values())}")
    print("\n" + "="*80 + "\n")

def main():
    print(f"{Colors.BOLD}Hikvision NAS Folder Monitor{Colors.ENDC}")
    print(f"Monitoring: {NAS_PATH}")
    print(f"Checking every {CHECK_INTERVAL} seconds...")
    print(f"Press Ctrl+C to stop\n")
    
    # Initial scan to populate known files
    print("Performing initial scan...")
    check_nas_folder()
    print(f"Found {len(known_files)} existing files\n")
    print("Monitoring for new detections...\n")
    
    try:
        while True:
            new_files = check_nas_folder()
            for filepath, filename, mtime in new_files:
                print_detection(filename, filepath, mtime)
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BOLD}=== Final Statistics ==={Colors.ENDC}")
        print(f"Face Detections: {event_stats['face']}")
        print(f"Body Detections: {event_stats['body']}")
        print(f"Smart Detections: {event_stats['smart']}")
        print(f"Total: {sum(event_stats.values())}")
        print("\nMonitoring stopped.\n")

if __name__ == "__main__":
    main()
