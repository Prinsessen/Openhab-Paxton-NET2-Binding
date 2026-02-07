#!/usr/bin/env python3
"""
Hikvision NAS Folder Monitor for Body/Face Detection
Monitors Hikvision .pic files (ATTACHIF format) for size changes
Each size increase = new body/face detection event added to container
Extracts and displays detection snapshots
"""

import os
import sys
import time
import subprocess
import re
import json
import requests
from datetime import datetime
from collections import defaultdict
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Load configuration from external file
def load_config():
    """Load configuration from JSON file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, 'hikvision_monitor_config.json')
    
    if not os.path.exists(config_file):
        print(f"ERROR: Configuration file not found: {config_file}")
        print(f"Please create it from the example: hikvision_monitor_config.example.json")
        sys.exit(1)
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not load config file: {e}")
        sys.exit(1)

# Load configuration
CONFIG = load_config()

# Extract configuration values
NAS_PATH = CONFIG['nas']['mount_path']
CHECK_INTERVAL = CONFIG['nas']['check_interval']
OPENHAB_REST_URL = CONFIG['openhab']['rest_url']
OPENHAB_HTML_PATH = CONFIG['openhab']['html_path']
OCR_TIMEOUT = CONFIG['ocr']['tesseract_timeout']
OCR_PANEL_HEIGHT = CONFIG['ocr']['panel_crop_height']
TEMP_PATH = CONFIG['output']['temp_path']
IMAGE_FILENAME = CONFIG['output']['image_filename']
JSON_FILENAME = CONFIG['output']['json_filename']
TIMESTAMP_FILENAME = CONFIG['output']['timestamp_filename']

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

def extract_analysis_text(image_path):
    """Extract person analysis text from detection image using OCR"""
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Load image and crop bottom section (analysis panel)
        img = Image.open(image_path)
        width, height = img.size
        
        # Analysis panel is typically in bottom pixels (configurable)
        panel_height = OCR_PANEL_HEIGHT
        crop_box = (0, height - panel_height, width, height)
        panel = img.crop(crop_box)
        
        # Save cropped panel temporarily
        panel_path = os.path.join(TEMP_PATH, 'ocr_panel.jpg')
        panel.save(panel_path)
        
        # Run tesseract OCR
        result = subprocess.run(
            ['tesseract', panel_path, 'stdout'],
            capture_output=True,
            text=True,
            timeout=OCR_TIMEOUT
        )
        
        text = result.stdout
        
        # CRITICAL: Normalize text by collapsing all whitespace (including newlines) to single spaces
        # This handles OCR line-wrapping where "Bottom Color" becomes "Bott\nom C    olor"
        text_normalized = re.sub(r'\s+', ' ', text)
        
        # FIX OCR MISTAKES: Common character misreads in datetime patterns
        # OCR often reads '0' (zero) as 'O' (letter O) or '7' as '?'
        text_fixed = text_normalized
        # Fix "O" followed by 2 digits: "2026-02-O07" → "2026-02-07" (not "007"!)
        text_fixed = re.sub(r'(\d{4}[-/]\d{2}[-/])O(\d{2})', r'\g<1>\g<2>', text_fixed)
        # Fix dash followed by O and digit: "-O7" → "-07"
        text_fixed = re.sub(r'[-/]O(\d)(?!\d)', r'-0\1', text_fixed)  # Only single digit after O
        # Fix "O?" patterns (with optional space after dash)
        text_fixed = re.sub(r'[-/]\s*O\?', r'-07', text_fixed)  # "- O?" or "-O?" → "-07"
        text_fixed = re.sub(r'O\?\s', '07 ', text_fixed)
        
        # Parse structured data
        data = {}
        
        # Capture Time
        match = re.search(r'Capture [Tt]ime[:\s]+([0-9\-: ]+)', text_normalized)
        if match:
            data['capture_time'] = match.group(1).strip()
        
        # Movement direction
        match = re.search(r'Enter[:\s]+(\w+)', text_normalized)
        if match:
            data['enter_direction'] = match.group(1)
        
        match = re.search(r'Leave[:\s]+(\w+)', text_normalized)
        if match:
            data['leave_direction'] = match.group(1)
        
        # Clothing colors - IMPROVED: Handle split word "Bottom Color" → "Bottom Co lor:"
        # Strategy 1: Try to find complete "Color:" patterns
        all_colors = re.findall(r'[Cc]olor\s*:\s*(\w+)', text_normalized, re.IGNORECASE)
        
        if len(all_colors) >= 1:
            if all_colors[0] not in ['-', 'N/A', 'None']:
                data['top_color'] = all_colors[0]
        
        if len(all_colors) >= 2:
            if all_colors[1] not in ['-', 'N/A', 'None']:
                data['bottom_color'] = all_colors[1]
        
        # Strategy 2: If bottom_color not found, look for partial matches "lor:" or "olor:"
        if 'bottom_color' not in data:
            # Search for "Bottom" followed by any text, then "lor:" (broken "Color:")
            bottom_match = re.search(r'Bottom[^:]*?(?:Co\s+)?(?:o)?lor\s*:\s*(\w+)', text_normalized, re.IGNORECASE)
            if bottom_match:
                color_value = bottom_match.group(1)
                if color_value not in ['-', 'N/A', 'None']:
                    data['bottom_color'] = color_value
        
        # Strategy 3: Fallback - extract from section between "Top Color:" and "Top Type:"
        if 'bottom_color' not in data:
            section = re.search(r'Top Color.*?Top Type', text_normalized, re.IGNORECASE)
            if section:
                # Look for second color value in this section (first is top, second is bottom)
                colors_in_section = re.findall(r':(\w+)', section.group(0))
                colors_in_section = [c for c in colors_in_section if c not in ['-', 'N/A', 'None', 'No', 'Long', 'Short', 'Sleeve', 'Co', 'lor']]
                if len(colors_in_section) >= 2:
                    data['bottom_color'] = colors_in_section[1]
        
        # Clothing types
        match = re.search(r'Top\s+Type[:\s]+([\w ]+?)(?:Bottom|Backpack|\n)', text_normalized)
        if match:
            data['top_type'] = match.group(1).strip()
        
        match = re.search(r'Bottom\s+Type[:\s]+([\w ]+?)(?:Backpack|Carrying|\n)', text_normalized)
        if match:
            data['bottom_type'] = match.group(1).strip()
        
        # Accessories
        match = re.search(r'Backpack\s+or\s+Not[:\s]+(\w+)', text_normalized)
        if match:
            data['has_backpack'] = match.group(1).lower() == 'yes'
        
        match = re.search(r'Carrying\s+Things\s+or\s+Not[:\s]+(\w+)', text_normalized)
        if match:
            data['carrying_things'] = match.group(1).lower() == 'yes'
        
        match = re.search(r'Hat\s+or\s+Not[:\s]+(\w+)', text_normalized)
        if match:
            data['has_hat'] = match.group(1).lower() == 'yes'
        
        # Entry time - Use OCR-fixed text
        match = re.search(r'Entry\s+Time[:\s]+([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}[\s]+[0-9]{2}:[0-9]{2}:[0-9]{2})', text_fixed)
        if match:
            data['entry_time'] = match.group(1).strip().replace('/', '-')
        
        # Exit time - Use digit extraction from OCR-fixed text
        exit_section = re.search(r'Exit\s+Time[:\s]+(.+?)(?:Camera|Device|$)', text_fixed, re.IGNORECASE)
        if exit_section:
            # Extract all digit sequences from the exit time section
            digits = re.findall(r'[0-9]+', exit_section.group(1))
            # Need at least 6 groups: year, month, day (or parts), hour, min, sec
            if len(digits) >= 5:  # At minimum: year, month, day, HH, MM, SS
                year_str = digits[0]
                remaining = digits[1:]
                
                # Last 3 are always HH:MM:SS
                if len(remaining) >= 3:
                    time_parts = remaining[-3:]
                    date_parts = remaining[:-3]
                    
                    # Reconstruct date from remaining parts
                    if len(date_parts) == 2:
                        month_str, day_str = date_parts
                    elif len(date_parts) == 3:
                        # Combine first two for month: "0" + "2" = "02"
                        month_str = date_parts[0] + date_parts[1] if int(date_parts[0]) == 0 else date_parts[0]
                        day_str = date_parts[2]
                    elif len(date_parts) == 4:
                        # Combine pairs: "0"+"2" and "0"+"7"
                        month_str = date_parts[0] + date_parts[1]
                        day_str = date_parts[2] + date_parts[3]
                    else:
                        # Fallback: use what we have
                        month_str = date_parts[0] if len(date_parts) > 0 else "01"
                        day_str = date_parts[1] if len(date_parts) > 1 else "01"
                    
                    # Format the exit time
                    data['exit_time'] = f"{year_str}-{month_str.zfill(2)}-{day_str.zfill(2)} {time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:{time_parts[2].zfill(2)}"
        
        # Camera info
        match = re.search(r'Device\s+No\.[:\s]+([\w ]+)', text_normalized)
        if match:
            data['camera'] = match.group(1).strip()
        
        return data if data else None
        
    except Exception as e:
        print(f"    {Colors.WARNING}⚠ OCR extraction failed: {e}{Colors.ENDC}")
        return None

def update_openhab_items(analysis):
    """Update OpenHAB items with detection analysis data"""
    if not analysis:
        return
    
    # Mapping from analysis keys to OpenHAB item names
    item_mapping = {
        'enter_direction': 'Camera_Detection_Enter_Direction',
        'leave_direction': 'Camera_Detection_Leave_Direction',
        'top_color': 'Camera_Detection_Top_Color',
        'bottom_color': 'Camera_Detection_Bottom_Color',
        'top_type': 'Camera_Detection_Top_Type',
        'bottom_type': 'Camera_Detection_Bottom_Type',
        'has_backpack': 'Camera_Detection_Has_Backpack',
        'has_hat': 'Camera_Detection_Has_Hat',
        'entry_time': 'Camera_Detection_Entry_Time',
        'exit_time': 'Camera_Detection_Exit_Time',
        'camera': 'Camera_Detection_Camera_Name'
    }
    
    headers = {'Content-Type': 'text/plain'}
    updated_count = 0
    
    for key, item_name in item_mapping.items():
        if key not in analysis:
            continue
        
        value = analysis[key]
        
        # Convert boolean to ON/OFF for Switch items
        if isinstance(value, bool):
            value = 'ON' if value else 'OFF'
        # Convert datetime strings to ISO format for DateTime items
        elif key in ['entry_time', 'exit_time'] and value:
            try:
                # Parse the datetime string and convert to ISO format
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                value = dt.isoformat()
            except:
                pass  # Keep original if parsing fails
        
        # Update item via REST API
        try:
            url = f"{OPENHAB_REST_URL}/{item_name}/state"
            response = requests.put(url, data=str(value), headers=headers, timeout=2)
            if response.status_code == 202:
                updated_count += 1
        except Exception as e:
            pass  # Silently fail for individual items
    
    if updated_count > 0:
        print(f"    {Colors.OKGREEN}✓ Updated {updated_count} OpenHAB items{Colors.ENDC}")

def display_image(jpeg_data, timestamp):
    """Save JPEG and display using system viewer"""
    if not jpeg_data:
        return None
    
    try:
        # Save to temp file
        temp_path = os.path.join(TEMP_PATH, f"hikvision_detection_{timestamp.replace(':', '-')}.jpg")
        with open(temp_path, 'wb') as f:
            f.write(jpeg_data)
        
        # Also save to OpenHAB html directory for web serving
        openhab_path = os.path.join(OPENHAB_HTML_PATH, IMAGE_FILENAME)
        try:
            with open(openhab_path, 'wb') as f:
                f.write(jpeg_data)
            
            # Save timestamp in separate file for instant web display
            timestamp_path = os.path.join(OPENHAB_HTML_PATH, TIMESTAMP_FILENAME)
            with open(timestamp_path, 'w') as f:
                f.write(timestamp + '\n')
            
            print(f"    {Colors.OKGREEN}✓ Updated web image: {openhab_path}{Colors.ENDC}")
            
            # Extract and save analysis text
            analysis = extract_analysis_text(openhab_path)
            if analysis:
                # Save as JSON
                json_path = os.path.join(OPENHAB_HTML_PATH, JSON_FILENAME)
                with open(json_path, 'w') as f:
                    json.dump(analysis, f, indent=2)
                
                print(f"    {Colors.OKGREEN}✓ Extracted analysis metadata{Colors.ENDC}")
                
                # Update timestamp file with ACTUAL capture time from camera overlay
                if 'capture_time' in analysis:
                    with open(timestamp_path, 'w') as f:
                        f.write(analysis['capture_time'] + '\n')
                
                # Update OpenHAB items
                update_openhab_items(analysis)
                
                # Print key info
                if 'top_type' in analysis and 'bottom_type' in analysis:
                    print(f"      Clothing: {analysis.get('top_type', 'Unknown')} / {analysis.get('bottom_type', 'Unknown')}")
                if 'top_color' in analysis and 'bottom_color' in analysis:
                    print(f"      Colors: {analysis.get('top_color', 'Unknown')} / {analysis.get('bottom_color', 'Unknown')}")
                if 'enter_direction' in analysis or 'leave_direction' in analysis:
                    print(f"      Movement: Enter {analysis.get('enter_direction', 'Unknown')}, Leave {analysis.get('leave_direction', 'Unknown')}")
            
        except Exception as e:
            print(f"    {Colors.WARNING}⚠ Could not save to OpenHAB html: {e}{Colors.ENDC}")
        
        # Try to display using feh (lightweight image viewer) in background
        try:
            subprocess.Popen(['feh', '--geometry', '800x600', '--title', 'Body Detection', temp_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # feh not available, just save the file
            pass
        
        return (temp_path, analysis if 'analysis' in locals() else None)
    except Exception as e:
        print(f"Error saving image: {e}")
        return (None, None)

def check_nas_folder():
    """Check .pic files for size changes (new detections added)"""
    if not os.path.exists(NAS_PATH):
        print(f"{Colors.FAIL}NAS path not mounted: {NAS_PATH}{Colors.ENDC}")
        print(f"Please mount the NAS share first. See README_hikvision_monitor.md for instructions.")
        print(f"Example: sudo mount -t cifs //YOUR_NAS_IP/YOUR_SHARE {os.path.dirname(NAS_PATH)} -o credentials=/etc/camera_nas_credentials,vers=3.0")
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
    analysis = None
    if jpeg_data:
        image_path, analysis = display_image(jpeg_data, timestamp)
        if image_path:
            print(f"{Colors.OKGREEN}✓ Snapshot saved: {image_path}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Failed to save snapshot{Colors.ENDC}")
    
    # Use actual capture time from camera overlay if available
    display_time = timestamp
    if analysis and 'capture_time' in analysis:
        # Parse capture_time format: "02-07-2026 09:43:23" → "09:43:23"
        capture_time_parts = analysis['capture_time'].split()
        if len(capture_time_parts) >= 2:
            display_time = capture_time_parts[1]
            last_detection_time = display_time
    
    clear_screen()
    print("\n" + "="*80)
    print(f"{Colors.BG_GREEN}{Colors.BLACK}  🔔 {detection_type} DETECTED! 🔔  {Colors.ENDC}")
    print("="*80)
    print(f"\n⏰ Detection Time: {display_time}")
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
