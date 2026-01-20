#!/usr/bin/env python3
"""
Traccar Webhook Monitor - Beacon Data Analysis
Monitors Traccar webhooks and analyzes Teltonika EYE beacon data
"""

import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import signal
import sys

# Configuration
WEBHOOK_PORT = 8090
BEACON_AVL_IDS = {
    385: "Simple Mode (Auto-parsed beacon data)",
    548: "Advanced Mode (Manual config beacon data)",
    10828: "Periodic full EYE Beacon list",
    10829: "EYE Beacon found event",
    10831: "EYE Beacon lost event"
}

# Store captured data
captured_data = []
beacon_data = []
running = True

class TraccarWebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhook requests from Traccar"""
    
    def log_message(self, format, *args):
        """Override to provide custom logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] {format % args}")
    
    def do_POST(self):
        """Handle POST requests from Traccar"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Parse JSON data
            try:
                data = json.loads(post_data.decode('utf-8'))
                self.analyze_webhook_data(data, timestamp)
            except json.JSONDecodeError:
                # Try to parse as form data
                try:
                    data = parse_qs(post_data.decode('utf-8'))
                    self.analyze_form_data(data, timestamp)
                except:
                    print(f"[{timestamp}] ❌ Failed to parse webhook data")
                    print(f"Raw data: {post_data.decode('utf-8', errors='replace')}")
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            print(f"Error handling POST: {e}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests from Traccar"""
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            self.analyze_form_data(query_params, timestamp)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            print(f"Error handling GET: {e}")
            self.send_response(500)
            self.end_headers()
    
    def analyze_webhook_data(self, data, timestamp):
        """Analyze JSON webhook data for beacon information"""
        print(f"\n{'='*80}")
        print(f"[{timestamp}] 📡 WEBHOOK RECEIVED (JSON)")
        print(f"{'='*80}")
        
        # Store data
        captured_data.append({
            'timestamp': timestamp,
            'type': 'json',
            'data': data
        })
        
        # Pretty print the data
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Check for event type
        event_type = data.get('event', {}).get('type', 'unknown')
        print(f"\n🔔 Event Type: {event_type}")
        
        # Check for position data
        if 'position' in data:
            position = data['position']
            print(f"\n📍 Position Data:")
            print(f"  Device ID: {position.get('deviceId', 'N/A')}")
            print(f"  Protocol: {position.get('protocol', 'N/A')}")
            print(f"  Speed: {position.get('speed', 'N/A')} km/h")
            print(f"  Latitude: {position.get('latitude', 'N/A')}")
            print(f"  Longitude: {position.get('longitude', 'N/A')}")
            
            # Check for attributes (this is where beacon data usually appears)
            if 'attributes' in position:
                attrs = position['attributes']
                print(f"\n🏷️  Position Attributes ({len(attrs)} items):")
                
                # Look for beacon-related AVL IDs
                beacon_found = False
                for key, value in attrs.items():
                    # Check if key matches known beacon AVL IDs
                    if key.startswith('io') or key.startswith('avl'):
                        avl_id = key.replace('io', '').replace('avl', '')
                        try:
                            avl_id_num = int(avl_id)
                            if avl_id_num in BEACON_AVL_IDS:
                                beacon_found = True
                                print(f"  🎯 BEACON DATA FOUND!")
                                print(f"     AVL ID {avl_id_num}: {BEACON_AVL_IDS[avl_id_num]}")
                                print(f"     Value: {value}")
                                
                                # Store beacon data
                                beacon_data.append({
                                    'timestamp': timestamp,
                                    'avl_id': avl_id_num,
                                    'description': BEACON_AVL_IDS[avl_id_num],
                                    'value': value,
                                    'device_id': position.get('deviceId'),
                                    'protocol': position.get('protocol')
                                })
                        except ValueError:
                            pass
                    
                    # Print all attributes
                    print(f"     {key}: {value}")
                
                if not beacon_found:
                    print(f"  ℹ️  No beacon data found in this position update")
        
        # Check for device data
        if 'device' in data:
            device = data['device']
            print(f"\n📱 Device Info:")
            print(f"  Name: {device.get('name', 'N/A')}")
            print(f"  Unique ID: {device.get('uniqueId', 'N/A')}")
            print(f"  Status: {device.get('status', 'N/A')}")
    
    def analyze_form_data(self, data, timestamp):
        """Analyze form-encoded webhook data"""
        print(f"\n{'='*80}")
        print(f"[{timestamp}] 📡 WEBHOOK RECEIVED (FORM DATA)")
        print(f"{'='*80}")
        
        # Store data
        captured_data.append({
            'timestamp': timestamp,
            'type': 'form',
            'data': data
        })
        
        # Print all parameters
        for key, values in data.items():
            value = values[0] if isinstance(values, list) else values
            print(f"  {key}: {value}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\n🛑 Stopping webhook monitor...")
    running = False
    print_summary()
    sys.exit(0)

def print_summary():
    """Print summary of captured data"""
    print(f"\n\n{'='*80}")
    print(f"📊 MONITORING SUMMARY")
    print(f"{'='*80}")
    print(f"Total webhooks received: {len(captured_data)}")
    print(f"Beacon data entries found: {len(beacon_data)}")
    
    if beacon_data:
        print(f"\n🎯 BEACON DATA SUMMARY:")
        print(f"{'='*80}")
        
        # Group by AVL ID
        avl_groups = {}
        for entry in beacon_data:
            avl_id = entry['avl_id']
            if avl_id not in avl_groups:
                avl_groups[avl_id] = []
            avl_groups[avl_id].append(entry)
        
        for avl_id, entries in avl_groups.items():
            print(f"\nAVL ID {avl_id}: {BEACON_AVL_IDS.get(avl_id, 'Unknown')}")
            print(f"  Count: {len(entries)}")
            print(f"  First seen: {entries[0]['timestamp']}")
            print(f"  Last seen: {entries[-1]['timestamp']}")
            print(f"  Sample values:")
            for entry in entries[:3]:  # Show first 3 samples
                print(f"    [{entry['timestamp']}] {entry['value']}")
    else:
        print("\n⚠️  No beacon data detected yet.")
        print("\nTroubleshooting steps:")
        print("1. Verify FMM920 Bluetooth® settings are enabled")
        print("2. Confirm Codec 8 Extended is activated")
        print("3. Check that Beacon Detection is set to 'All' or 'Configured'")
        print("4. Ensure beacons are within range of the tracker")
        print("5. Verify Traccar is forwarding all position updates via webhook")

def run_server():
    """Run the webhook server"""
    server = HTTPServer(('0.0.0.0', WEBHOOK_PORT), TraccarWebhookHandler)
    print(f"\n{'='*80}")
    print(f"🚀 Traccar Webhook Monitor Started")
    print(f"{'='*80}")
    print(f"Listening on port: {WEBHOOK_PORT}")
    print(f"Monitoring for Teltonika EYE Beacon data...")
    print(f"Looking for AVL IDs: {', '.join(map(str, BEACON_AVL_IDS.keys()))}")
    print(f"\nPress Ctrl+C to stop and view summary\n")
    print(f"{'='*80}\n")
    
    # Run server in a loop
    while running:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in server loop: {e}")

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        run_server()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
