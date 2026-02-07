#!/usr/bin/env python3
"""
Hikvision NAS Folder Monitor for Body/Face Detection
Monitors Hikvision .pic files (ATTACHIF format) for size changes
Each size increase = new body/face detection event added to container
Extracts and displays detection snapshots
"""

import os
import time
import subprocess
from datetime import datetime
from collections import defaultdict

# NAS Configuration
NAS_PATH = "/mnt/camera_nas/Camera"  # Mounted at: \\10.0.5.25\Agesen_Storange4\Camera
CHECK_INTERVAL = 2  # Check every 2 seconds

# Track file sizes (not just existence)
file_sizes = {}
event_stats = defaultdict(int)
last_detection_time = None

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

def extract_last_jpeg(pic_filepath):
    """Extract the highest quality (largest) JPEG from the most recent detection in the file"""
    try:
        with open(pic_filepath, 'rb') as f:
            # Only read last 3MB where newest detections are (avoid reading entire 136MB)
            file_size = os.path.getsize(pic_filepath)
            read_size = min(3 * 1024 * 1024, file_size)  # 3MB or file size
            f.seek(-read_size, 2)  # Seek from end
            data = f.read()
        
        # Find all JPEG markers (SOI: 0xFFD8, EOI: 0xFFD9)
        jpeg_start_marker = b'\xff\xd8\xff'
        jpeg_end_marker = b'\xff\xd9'
        
        # Find all JPEG images in the tail
        jpegs = []
        pos = 0
        while True:
            start = data.find(jpeg_start_marker, pos)
            if start == -1:
                break
            end = data.find(jpeg_end_marker, start)
            if end == -1:
                break
            # Extract JPEG including end marker
            jpeg_data = data[start:end+2]
            jpegs.append(jpeg_data)
            pos = end + 2
        
        if jpegs:
            # Each detection has 2-3 images. Take the largest from LAST 3 images only
            # This ensures we get the high-res from the absolute most recent detection
            recent_jpegs = jpegs[-3:]
            return max(recent_jpegs, key=len)
        return None
    except Exception as e:
        print(f"Error extracting JPEG: {e}")
        return None

def display_image(jpeg_data, timestamp):
    """Save JPEG and display using system viewer"""
    if not jpeg_data:
        return None
    
    try:
        # Save to temp file
        temp_path = f"/tmp/hikvision_detection_{timestamp.replace(':', '-')}.jpg"
        with open(temp_path, 'wb') as f:
            f.write(jpeg_data)
        
        # Also save to OpenHAB html directory for web serving
        openhab_path = "/etc/openhab/html/hikvision_latest.jpg"
        try:
            with open(openhab_path, 'wb') as f:
                f.write(jpeg_data)
            
            # Save timestamp in separate file for instant web display
            timestamp_path = "/etc/openhab/html/hikvision_latest_time.txt"
            with open(timestamp_path, 'w') as f:
                f.write(timestamp + '\n')
            
            print(f"    {Colors.OKGREEN}✓ Updated web image: {openhab_path}{Colors.ENDC}")
        except Exception as e:
            print(f"    {Colors.WARNING}⚠ Could not save to OpenHAB html: {e}{Colors.ENDC}")
        
        # Try to display using feh (lightweight image viewer) in background
        try:
            subprocess.Popen(['feh', '--geometry', '800x600', '--title', 'Body Detection', temp_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # feh not available, just save the file
            pass
        
        return temp_path
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def check_nas_folder():
    """Check .pic files for size changes (new detections added)"""
    if not os.path.exists(NAS_PATH):
        print(f"{Colors.FAIL}NAS path not mounted: {NAS_PATH}{Colors.ENDC}")
        print(f"Mount with: sudo mount -t cifs //10.0.5.25/Agesen_Storange4 /mnt/camera_nas -o username=Nanna,password=<pass>,vers=3.0")
        return []
    
    size_changes = []
    try:
        for root, dirs, files in os.walk(NAS_PATH):
            for filename in files:
                if filename.endswith('.pic'):
                    filepath = os.path.join(root, filename)
                    try:
                        current_size = os.path.getsize(filepath)
                        mtime = os.path.getmtime(filepath)
                        
                        # Check if file grew (new detection added)
                        if filepath in file_sizes:
                            if current_size > file_sizes[filepath]:
                                size_diff = current_size - file_sizes[filepath]
                                file_sizes[filepath] = current_size
                                size_changes.append((filepath, filename, mtime, size_diff, current_size))
                        else:
                            # First time seeing this file - initialize but don't alert
                            file_sizes[filepath] = current_size
                    except OSError:
                        pass  # File might be locked during write
    except Exception as e:
        print(f"{Colors.FAIL}Error reading NAS: {e}{Colors.ENDC}")
    
    return size_changes

def print_detection(filename, filepath, mtime, size_diff, current_size):
    """Print detection event when .pic file grows and show snapshot"""
    global last_detection_time
    timestamp = datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
    last_detection_time = timestamp
    
    detection_type = "👤 Smart Body/Face Detection"
    event_stats['detections'] += 1
    
    # Extract and display the detection snapshot
    print(f"\n{Colors.WARNING}Extracting detection snapshot...{Colors.ENDC}")
    jpeg_data = extract_last_jpeg(filepath)
    image_path = None
    if jpeg_data:
        image_path = display_image(jpeg_data, timestamp)
        if image_path:
            print(f"{Colors.OKGREEN}✓ Snapshot saved: {image_path}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Failed to save snapshot{Colors.ENDC}")
    
    clear_screen()
    print("\n" + "="*80)
    print(f"{Colors.BG_GREEN}{Colors.BLACK}  🔔 {detection_type} DETECTED! 🔔  {Colors.ENDC}")
    print("="*80)
    print(f"\n⏰ Detection Time: {timestamp}")
    print(f"📁 Container File: {filename}")
    print(f"📂 Path: {filepath}")
    print(f"📊 File grew by: {size_diff / 1024:.1f} KB (new snapshot added)")
    print(f"💾 Current size: {current_size / (1024*1024):.1f} MB")
    if image_path:
        print(f"📸 Snapshot: {image_path}")
        print(f"   {Colors.OKGREEN}→ Image viewer opened (if available){Colors.ENDC}")
    print(f"\n📈 Total Detections Today: {event_stats['detections']}")
    print(f"⏱️  Last Detection: {last_detection_time}")
    print("\n" + "="*80 + "\n")

def main():
    print(f"{Colors.BOLD}Hikvision NAS Body/Face Detection Monitor{Colors.ENDC}")
    print(f"Monitoring: {NAS_PATH}")
    print(f"Checking .pic files every {CHECK_INTERVAL} seconds...")
    print(f"Detection method: File size changes (ATTACHIF format)")
    print(f"Press Ctrl+C to stop\n")
    
    # Initial scan to populate file sizes
    print("Performing initial scan of .pic files...")
    check_nas_folder()
    print(f"Tracking {len(file_sizes)} .pic container files\n")
    print("Monitoring for new detections...\n")
    
    try:
        while True:
            size_changes = check_nas_folder()
            for filepath, filename, mtime, size_diff, current_size in size_changes:
                print_detection(filename, filepath, mtime, size_diff, current_size)
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BOLD}=== Final Statistics ==={Colors.ENDC}")
        print(f"Total Detections: {event_stats['detections']}")
        print(f"Last Detection: {last_detection_time if last_detection_time else 'None'}")
        print(f"Files Monitored: {len(file_sizes)}")
        print("\nMonitoring stopped.\n")

if __name__ == "__main__":
    main()
