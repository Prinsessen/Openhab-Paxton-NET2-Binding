#!/usr/bin/env python3
"""
Hikvision NAS Folder Monitor for Body/Face Detection
Monitors Hikvision .pic files (ATTACHIF format) for size changes
Each size increase = new body/face detection event added to container
Extracts and displays detection snapshots

Author: Nanna Agesen (@Prinsessen)
Email: Nanna@agesen.dk
GitHub: https://github.com/Prinsessen/openhab-hikvision-analytics
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
    # Try to get script directory intelligently
    if '__file__' in globals():
        script_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        # Fallback for testing or when __file__ is not available
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if not script_dir or script_dir == '.':
            script_dir = os.getcwd()
    
    config_file = os.path.join(script_dir, 'config.json')
    
    if not os.path.exists(config_file):
        print(f"ERROR: Configuration file not found: {config_file}")
        print(f"Please create it from the example: config.example.json")
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
        
        # FIX OCR MISTAKES: Common character misreads and formatting issues
        text_fixed = text_normalized
        
        # Fix em-dash and other dash variants used in dates
        text_fixed = text_fixed.replace('—', '-').replace('–', '-')  # em-dash and en-dash to hyphen
        
        # Fix Unicode smart quotes to regular quotes (OCR outputs U+2018, U+2019, U+201C, U+201D)
        text_fixed = text_fixed.replace('\u2018', "'").replace('\u2019', "'")  # U+2018, U+2019 → U+0027 (ASCII apostrophe)
        text_fixed = text_fixed.replace('\u201c', '"').replace('\u201d', '"')  # U+201C, U+201D → U+0022 (ASCII quote)
        
        print(f"    [DEBUG] OCR text normalized: {text_normalized[:200]}...")  # DEBUG - first 200 chars
        
        # OCR often reads '0' (zero) as 'O' (letter O) or '7' as '?'
        # Fix "O" at start of date components: "O7-02-2026" → "07-02-2026" (for DD-MM-YYYY capture time)
        text_fixed = re.sub(r'\bO(\d)(?=[-/])', r'0\1', text_fixed)  # Leading O before dash
        # Fix "O" followed by 2 digits in any position: "02-O07-2026" or "2026-02-O07" → "02-07-2026" or "2026-02-07"
        text_fixed = re.sub(r'[-/]O(\d{2})', r'-\1', text_fixed)  # Dash+O+2digits → Dash+2digits
        # Fix "O" followed by 2 digits after year-month: "2026-02-O07" → "2026-02-07" (fallback)
        text_fixed = re.sub(r'(\d{4}[-/]\d{2}[-/])O(\d{2})', r'\g<1>\g<2>', text_fixed)
        # Fix dash followed by O and single digit: "-O7 " → "-07 "
        text_fixed = re.sub(r'[-/]O(\d)(?!\d)', r'-0\1', text_fixed)  # Only single digit after O
        # Fix "O?" patterns (with optional space after dash)
        text_fixed = re.sub(r'[-/]\s*O\?', r'-07', text_fixed)  # "- O?" or "-O?" → "-07"
        text_fixed = re.sub(r'O\?\s', '07 ', text_fixed)
        
        # ========================================
        # NEW STRUCTURED EXTRACTION APPROACH
        # ========================================
        # Extract full analysis block from earliest of "Capture"/"Enter" to "Entrance"
        # OCR can output fields in different orders due to line wrapping
        
        # Find earliest starting point (whichever comes first)
        capture_idx = text_fixed.find('Capture')
        if capture_idx == -1:
            capture_idx = text_fixed.find('apture')  # OCR sometimes drops first letter
        
        enter_idx = text_fixed.find('Enter')
        
        # Start from whichever comes first (or only one if other not found)
        if capture_idx >= 0 and enter_idx >= 0:
            capture_start = min(capture_idx, enter_idx)
        elif capture_idx >= 0:
            capture_start = capture_idx
        elif enter_idx >= 0:
            capture_start = enter_idx
        else:
            print(f"    [WARNING] Could not find analysis block start (neither Capture nor Enter)", file=sys.stderr)
            return None
        
        camera_end = text_fixed.find('Entrance')
        if camera_end == -1:
            camera_end = len(text_fixed)  # Use full text if "Entrance" not found
        else:
            camera_end += len('Entrance')  # Include "Entrance" in the block
        
        # Extract the analysis block
        analysis_block = text_fixed[capture_start:camera_end]
        print(f"    [DEBUG] Analysis block ({len(analysis_block)} chars): {analysis_block[:150]}...", file=sys.stderr)
        
        # Initialize data dictionary
        data = {
            'capture_time': None,
            'enter_direction': None,
            'leave_direction': None,
            'top_color': None,
            'bottom_color': None,
            'top_type': None,
            'bottom_type': None,
            'has_backpack': False,
            'carrying_things': False,
            'has_hat': False,
            'entry_time': None,
            'exit_time': None,
            'camera': None
        }
        
        # ========================================
        # SYSTEMATIC FIELD EXTRACTION
        # Extract values by searching for field names and getting the value after ":"
        # ========================================
        
        def extract_field_value(text, field_name, pattern=r'([^:]+)', fallback_pattern=None):
            """Extract value after a field name. Returns cleaned string or None."""
            # Try main field name with flexible spacing
            match = re.search(rf'{field_name}[:\s]+{pattern}', text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Stop at next field delimiter (colon before capital letter or "or Not")
                value = re.split(r'(?=[A-Z][a-z]+\s*:|or Not)', value)[0].strip()
                # Clean quotes and extra whitespace
                value = value.strip('\'"').strip()
                return value if value and value not in ['-', 'N/A', 'None'] else None
            
            # Try fallback pattern if provided
            if fallback_pattern:
                match = re.search(fallback_pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return None
        
        # Capture Time - sometimes appears as "Capture T" or different format
        capture_raw = extract_field_value(analysis_block, r'Captur[^\s:]*\s+T[^\s:]*', r'[0-9\-:\s]+')
        if capture_raw:
            # Format is often DD-MM-YYYY HH:MM:SS, convert to YYYY-MM-DD HH:MM:SS
            parts = capture_raw.split()
            if len(parts) >= 2:
                date_part, time_part = parts[0], parts[1]
                date_components = date_part.split('-')
                if len(date_components) == 3 and len(date_components[2]) == 4:
                    # DD-MM-YYYY format
                    dd, mm, yyyy = date_components
                    data['capture_time'] = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)} {time_part}"
                elif len(date_components) == 3 and len(date_components[0]) == 4:
                    # Already YYYY-MM-DD format
                    data['capture_time'] = f"{date_part} {time_part}"
        
        # Entry Time - YYYY-MM-DD HH:MM:SS format
        entry_raw = extract_field_value(analysis_block, 'Entry Time', r'([0-9\-:\s]+)')
        if entry_raw:
            # Clean and validate
            match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{1,2}:[0-9]{2}:[0-9]{2})', entry_raw)
            if match:
                data['entry_time'] = match.group(1)
        
        # Exit Time - YYYY-MM-DD HH:MM:SS format (may have year as "202" instead of "2026" or OCR garbage like "NP?")
        # Use lenient pattern to capture garbage, then extract digits
        exit_raw = extract_field_value(analysis_block, 'Exit Time', r'([0-9\-:\s\w?]+)')
        if exit_raw:
            # Extract all digits for reconstruction (handles OCR garbage like "2026-02- NP? 20:36:41")
            digits = re.findall(r'[0-9]+', exit_raw)
            if len(digits) >= 6:  # Year, month, day, hour, min, sec
                year_str = digits[0]
                # Fix incomplete year: "202" → "2026"
                if len(year_str) == 3 and year_str.startswith('20'):
                    year_str = '2026' if year_str == '202' else f'20{year_str[2]}6'
                
                month_str = digits[1].zfill(2)
                day_str = digits[2].zfill(2)
                hour_str = digits[3].zfill(2)
                min_str = digits[4].zfill(2)
                sec_str = digits[5].zfill(2)
                
                data['exit_time'] = f"{year_str}-{month_str}-{day_str} {hour_str}:{min_str}:{sec_str}"
        
        # Directions
        enter_dir = extract_field_value(analysis_block, 'Enter', r'(\w+)')
        if enter_dir:
            data['enter_direction'] = enter_dir
        
        leave_dir = extract_field_value(analysis_block, 'Leave', r'(\w+)')
        if leave_dir:
            data['leave_direction'] = leave_dir
        
        # Colors - ROBUST extraction handling line-break splits
        # Normalize analysis block to handle "Botto\n\n'White" → "Botto 'White"
        analysis_normalized = re.sub(r'\s+', ' ', analysis_block)
        
        # Primary pattern: Look for color values after "Color", "Colo", "Col", "Co", "lor" (OCR variations)
        # Handles: "Top Color :White", "Bottom Colo 'White", "Bottom Co ... lor:White"
        # NOTE: Now includes "Co" and "lor" patterns for severe line-break splits like "Bottom Co\nlor:White"
        colors = re.findall(r'(?:Colo?r?|Co|lor)\s*:?\s*[\'\"]?\s*([A-Za-z]{3,})', analysis_normalized, re.IGNORECASE)
        
        # Filter out field names BEFORE checking if we need fallback
        # IMPORTANT: Also filter "Color" and "Colo" which are field names, not color values
        # Filter "Time" and "Entry" which can appear in OCR scrambled text like "Colo = Time" or "Co lor:Entry"
        # Filter "lor" which is a fragment of "Color" when split by line breaks: "Co lor:White"
        colors_clean = [c for c in colors if c and c not in ['Type', 'Top', 'Bottom', 'Not', 'Yes', 'No', 'Hat', 'Long', 'Short', 'Sleeve', 'Color', 'Colo', 'Col', 'apture', 'Tine', 'Time', 'Entry', 'Exit', 'lor']]
        
        # Only use fallback if primary pattern found less than 2 colors
        if len(colors_clean) < 2:
            # Fallback: Look for "Top" or "Bottom" followed eventually by color word (even if "Color" is missing)
            # Handles: "Bottom Co\n\n'apture... lor:White" by searching for color words after Top/Bottom
            section_colors = re.findall(r'(?:Top|Bottom)[^:]{0,30}:?\s*[\'\"]?\s*([A-Z][a-z]{2,})', analysis_normalized)
            colors_clean.extend([c for c in section_colors if c not in colors_clean and c not in ['Type', 'Top', 'Bottom', 'Not', 'Yes', 'No', 'Long', 'Short', 'Sleeve', 'Color', 'Colo', 'Col', 'apture', 'Tine', 'Time', 'Entry', 'Exit', 'lor']])
        
        if len(colors_clean) >= 1:
            data['top_color'] = colors_clean[0]
        if len(colors_clean) >= 2:
            data['bottom_color'] = colors_clean[1]
        print(f"    [DEBUG] Extracted colors: {colors_clean}", file=sys.stderr)
        
        # Clothing Types
        top_type = extract_field_value(analysis_block, 'Top Type', r'([\w\s]+)')
        if top_type:
            # Clean up - stop at next field
            top_type = re.split(r'Bottom|Backpack', top_type, flags=re.IGNORECASE)[0].strip()
            data['top_type'] = top_type
        
        bottom_type = extract_field_value(analysis_block, 'Bottom Type', r'([\w\s]+)')
        if bottom_type:
            # Clean up - stop at next field
            bottom_type = re.split(r'Backpack|Carrying', bottom_type, flags=re.IGNORECASE)[0].strip()
            data['bottom_type'] = bottom_type
        
        # Accessories - Yes/No fields
        backpack_match = re.search(r'Backpack[:\s]+or[\s]+Not[:\s]+(\w+)', analysis_block, re.IGNORECASE)
        if backpack_match:
            data['has_backpack'] = backpack_match.group(1).lower() == 'yes'
        
        carrying_match = re.search(r'Carrying[:\s]+[^:]*or[\s]+Not[:\s]+(\w+)', analysis_block, re.IGNORECASE)
        if carrying_match:
            data['carrying_things'] = carrying_match.group(1).lower() == 'yes'
        
        hat_match = re.search(r'Hat[:\s]+or[\s]+Not[:\s]+(\w+)', analysis_block, re.IGNORECASE)
        if hat_match:
            data['has_hat'] = hat_match.group(1).lower() == 'yes'
        
        # Camera - usually "Device No. :Entrance" or "Device No. 'Entrance" (OCR apostrophe)
        # Don't use extract_field_value since it requires colon/space before value
        camera_match = re.search(r'Device\s+No\.?\s*[:\'\"]?\s*([A-Za-z][\w\s]*)', analysis_block, re.IGNORECASE)
        if camera_match:
            camera = camera_match.group(1).strip()
            if camera and camera not in ['-', 'N/A', 'None']:
                data['camera'] = camera
        
        # ========================================
        # POST-PROCESSING & VALIDATION
        # ========================================
        
        # Fallback: Use entry_time as capture_time if capture_time is missing
        if (not data.get('capture_time') or data['capture_time'] is None) and data.get('entry_time'):
            data['capture_time'] = data['entry_time']
            print(f"    ℹ Using Entry Time as Capture Time (OCR couldn't read Capture Time field)", file=sys.stderr)
        
        # Clean up invalid timestamps
        for time_field in ['capture_time', 'entry_time', 'exit_time']:
            if data.get(time_field) and '0000-00-00' in data[time_field]:
                data[time_field] = None
        
        print(f"    [DEBUG] Extracted {sum(1 for v in data.values() if v)} / 13 fields", file=sys.stderr)
        
        return data if any(data.values()) else None
        
    except Exception as e:
        print(f"    {Colors.WARNING}⚠ OCR extraction failed: {e}{Colors.ENDC}")
        return None

def update_openhab_items(analysis):
    """Update OpenHAB items with detection analysis data"""
    if not analysis:
        return
    
    # Mapping from analysis keys to OpenHAB item names
    item_mapping = {
        'capture_time': 'Camera_Detection_Capture_Time',
        'enter_direction': 'Camera_Detection_Enter_Direction',
        'leave_direction': 'Camera_Detection_Leave_Direction',
        'top_color': 'Camera_Detection_Top_Color',
        'bottom_color': 'Camera_Detection_Bottom_Color',
        'top_type': 'Camera_Detection_Top_Type',
        'bottom_type': 'Camera_Detection_Bottom_Type',
        'has_backpack': 'Camera_Detection_Has_Backpack',
        'carrying_things': 'Camera_Detection_Carrying_Things',
        'has_hat': 'Camera_Detection_Has_Hat',
        'entry_time': 'Camera_Detection_Entry_Time',
        'exit_time': 'Camera_Detection_Exit_Time',
        'camera': 'Camera_Detection_Camera_Name'
    }
    
    headers = {'Content-Type': 'text/plain'}
    updated_count = 0
    
    for key, item_name in item_mapping.items():
        # Check if key exists in analysis, if not send "NA"
        if key not in analysis:
            value = 'UNDEF'  # OpenHAB undefined state
        else:
            value = analysis[key]
        
        # Check for invalid/missing data patterns
        if value is None or value == '' or value == '0000-00-00 00:00:00':
            # For DateTime items, use UNDEF; for String items, use "NA"
            if key in ['capture_time', 'entry_time', 'exit_time']:
                value = 'UNDEF'
            else:
                value = 'NA'
        # Convert boolean to ON/OFF for Switch items
        elif isinstance(value, bool):
            value = 'ON' if value else 'OFF'
        # Convert datetime strings to ISO format for DateTime items
        elif key in ['capture_time', 'entry_time', 'exit_time'] and value:
            try:
                # Parse the datetime string and convert to ISO format
                # All times should now be in YYYY-MM-DD HH:MM:SS format
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                value = dt.isoformat()
            except Exception as e:
                # If parsing fails, mark as undefined
                value = 'UNDEF'
        
        # Update item via REST API
        try:
            url = f"{OPENHAB_REST_URL}/{item_name}/state"
            response = requests.put(url, data=str(value), headers=headers, timeout=2)
            if response.status_code in [200, 202]:
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
                # Fallback: Use entry_time as capture_time if capture_time is missing
                if (not analysis.get('capture_time') or analysis['capture_time'] is None) and analysis.get('entry_time'):
                    analysis['capture_time'] = analysis['entry_time']
                    print(f"    {Colors.WARNING}ℹ Using Entry Time as Capture Time (OCR couldn't read Capture Time field){Colors.ENDC}")
                
                # Save as JSON
                json_path = os.path.join(OPENHAB_HTML_PATH, JSON_FILENAME)
                with open(json_path, 'w') as f:
                    json.dump(analysis, f, indent=2)
                
                print(f"    {Colors.OKGREEN}✓ Extracted analysis metadata{Colors.ENDC}")
                
                # Update timestamp file with ACTUAL capture time from camera overlay
                # HTML expects just HH:MM:SS format
                if 'capture_time' in analysis and analysis['capture_time']:
                    # Extract time portion from "YYYY-MM-DD HH:MM:SS"
                    time_parts = analysis['capture_time'].split()
                    if len(time_parts) >= 2:
                        time_only = time_parts[1]  # HH:MM:SS
                        with open(timestamp_path, 'w') as f:
                            f.write(time_only + '\n')
                
                # Update OpenHAB items
                update_openhab_items(analysis)
                
                # Print key info
                if 'top_type' in analysis and 'bottom_type' in analysis:
                    print(f"      Clothing: {analysis.get('top_type', 'Unknown')} / {analysis.get('bottom_type', 'Unknown')}")
                if 'top_color' in analysis and 'bottom_color' in analysis:
                    print(f"      Colors: {analysis.get('top_color', 'Unknown')} / {analysis.get('bottom_color', 'Unknown')}")
                    print(f"      [DEBUG] Full color data: top={repr(analysis.get('top_color'))}, bottom={repr(analysis.get('bottom_color'))}")  # DEBUG
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
    if analysis and 'capture_time' in analysis and analysis['capture_time']:
        # Parse capture_time format: "YYYY-MM-DD HH:MM:SS" → extract "HH:MM:SS"
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
