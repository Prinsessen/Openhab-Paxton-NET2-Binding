#!/usr/bin/env python3
"""
Monitor Traccar webhook data for Teltonika EYE Beacon information
Watches openHAB logs for beacon-related AVL IDs: 385, 548, 10828, 10829, 10831
"""

import subprocess
import re
import json
from datetime import datetime
import sys

# Beacon AVL IDs we're looking for
BEACON_AVL_IDS = {
    385: "Simple Mode - Standard Eddystone/iBeacon",
    548: "Advanced Mode - Custom beacon data",
    10828: "Periodic EYE Beacon list",
    10829: "EYE Beacon found event",
    10831: "EYE Beacon lost event"
}

def colorize(text, color_code):
    """Add color to terminal output"""
    return f"\033[{color_code}m{text}\033[0m"

def format_timestamp():
    """Get formatted timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def parse_json_data(text):
    """Try to extract and parse JSON from log line"""
    try:
        # Look for JSON-like structures
        json_match = re.search(r'\{.*\}', text)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    return None

def analyze_beacon_data(data):
    """Analyze data for beacon information"""
    findings = []
    
    if isinstance(data, dict):
        # Look for AVL IDs
        for avl_id, description in BEACON_AVL_IDS.items():
            if str(avl_id) in str(data):
                findings.append(f"  🔵 Found AVL ID {avl_id}: {description}")
        
        # Look for beacon-related keys
        beacon_keys = ['beacon', 'ble', 'bluetooth', 'eye', 'eddystone', 'ibeacon', 'mac', 'uuid']
        for key in data.keys():
            if any(beacon_word in key.lower() for beacon_word in beacon_keys):
                findings.append(f"  📡 Beacon key: {key} = {data[key]}")
        
        # Look for attributes
        if 'attributes' in data:
            attrs = data['attributes']
            if isinstance(attrs, dict):
                for key, value in attrs.items():
                    if any(beacon_word in key.lower() for beacon_word in beacon_keys):
                        findings.append(f"  📊 Attribute: {key} = {value}")
                    # Check for AVL IDs in attributes
                    for avl_id in BEACON_AVL_IDS.keys():
                        if str(avl_id) in key or str(avl_id) in str(value):
                            findings.append(f"  ⚡ AVL {avl_id} in attribute: {key} = {value}")
    
    return findings

def monitor_logs():
    """Monitor openHAB logs for Traccar webhook data"""
    print(colorize("=" * 80, "1;36"))
    print(colorize("🔍 Traccar EYE Beacon Monitor", "1;33"))
    print(colorize("=" * 80, "1;36"))
    print(f"\n{colorize('Monitoring for AVL IDs:', '1;32')}")
    for avl_id, desc in BEACON_AVL_IDS.items():
        print(f"  • {colorize(str(avl_id), '1;35')}: {desc}")
    print(f"\n{colorize('Watching openHAB logs... (Press Ctrl+C to stop)', '1;32')}\n")
    
    # Monitor both openhab.log and events.log
    cmd = "tail -F /var/log/openhab/openhab.log /var/log/openhab/events.log 2>/dev/null"
    
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains Traccar-related content
            if 'traccar' in line.lower() or 'webhook' in line.lower():
                timestamp = format_timestamp()
                print(f"\n{colorize(f'[{timestamp}]', '1;34')} {colorize('Traccar event:', '1;32')}")
                print(f"  {line}")
                
                # Try to parse JSON and analyze
                json_data = parse_json_data(line)
                if json_data:
                    print(colorize("  📄 JSON Data:", "1;33"))
                    print(json.dumps(json_data, indent=4))
                    
                    findings = analyze_beacon_data(json_data)
                    if findings:
                        print(colorize("\n  🎯 BEACON DATA DETECTED:", "1;31"))
                        for finding in findings:
                            print(finding)
                    
                print(colorize("-" * 80, "0;36"))
            
            # Also check for any beacon-related keywords
            elif any(word in line.lower() for word in ['beacon', 'ble', 'bluetooth', 'eye', 'avl']):
                timestamp = format_timestamp()
                print(f"\n{colorize(f'[{timestamp}]', '1;34')} {colorize('Potential beacon data:', '1;35')}")
                print(f"  {line}")
                print(colorize("-" * 80, "0;36"))
                
    except KeyboardInterrupt:
        print(f"\n\n{colorize('👋 Monitoring stopped by user', '1;33')}")
        process.terminate()
    except Exception as e:
        print(f"\n{colorize(f'❌ Error: {e}', '1;31')}")
        sys.exit(1)

if __name__ == "__main__":
    monitor_logs()
