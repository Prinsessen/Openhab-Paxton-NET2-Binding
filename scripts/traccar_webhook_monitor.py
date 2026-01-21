#!/usr/bin/env python3
"""
Enhanced Traccar Webhook Monitor
Displays webhook data from Traccar in a clean, easy-to-monitor format
Shows changes for every IO, AVL ID, and events from raw webhook data
"""

import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import signal
import sys
from collections import defaultdict
import os

# Configuration
WEBHOOK_PORT = 8091  # Different port to avoid conflicts
LOG_FILE = "/tmp/traccar_webhook_monitor.log"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DIM = '\033[2m'

# Track previous values to detect changes
previous_values = {}
event_counter = 0
running = True

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def format_timestamp(ts=None):
    """Format timestamp in readable format"""
    if ts is None:
        ts = datetime.now()
    return ts.strftime('%H:%M:%S.%f')[:-3]

def print_separator(char='=', length=100):
    """Print a separator line"""
    print(f"{Colors.DIM}{char * length}{Colors.END}")

def print_header(text):
    """Print a colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")

def print_subheader(text):
    """Print a colored subheader"""
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")

def print_change(key, old_value, new_value):
    """Print a value change with highlighting"""
    print(f"  {Colors.YELLOW}▶{Colors.END} {Colors.BOLD}{key}{Colors.END}: "
          f"{Colors.DIM}{old_value}{Colors.END} → {Colors.GREEN}{new_value}{Colors.END}")

def print_unchanged(key, value):
    """Print an unchanged value"""
    print(f"  {Colors.DIM}•{Colors.END} {key}: {value}")

def print_new(key, value):
    """Print a new value"""
    print(f"  {Colors.GREEN}✓{Colors.END} {Colors.BOLD}{key}{Colors.END}: {Colors.GREEN}{value}{Colors.END}")

class EnhancedTraccarWebhookHandler(BaseHTTPRequestHandler):
    """Handle and display incoming webhook requests from Traccar"""
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass
    
    def do_POST(self):
        """Handle POST requests from Traccar"""
        global event_counter, previous_values
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            timestamp = datetime.now()
            event_counter += 1
            
            # Parse JSON data
            try:
                data = json.loads(post_data.decode('utf-8'))
                self.display_webhook_data(data, timestamp)
            except json.JSONDecodeError:
                try:
                    data = parse_qs(post_data.decode('utf-8'))
                    self.display_form_data(data, timestamp)
                except Exception as e:
                    print(f"{Colors.RED}❌ Failed to parse webhook data: {e}{Colors.END}")
            
            # Log to file
            self.log_to_file(timestamp, data)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            print(f"{Colors.RED}Error handling POST: {e}{Colors.END}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests from Traccar"""
        global event_counter
        
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            timestamp = datetime.now()
            event_counter += 1
            
            self.display_form_data(query_params, timestamp)
            self.log_to_file(timestamp, query_params)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            print(f"{Colors.RED}Error handling GET: {e}{Colors.END}")
            self.send_response(500)
            self.end_headers()
    
    def display_webhook_data(self, data, timestamp):
        """Display JSON webhook data in organized format"""
        global previous_values
        
        print_separator('━')
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══ WEBHOOK EVENT #{event_counter} ═══ "
              f"{format_timestamp(timestamp)} ═══{Colors.END}")
        print_separator('━')
        
        # Event information
        if 'event' in data:
            event = data['event']
            event_type = event.get('type', 'unknown')
            print_header(f"📢 EVENT: {event_type.upper()}")
            
            for key, value in event.items():
                if key != 'type':
                    prev_key = f"event.{key}"
                    if prev_key in previous_values and previous_values[prev_key] != value:
                        print_change(key, previous_values[prev_key], value)
                    elif prev_key not in previous_values:
                        print_new(key, value)
                    else:
                        print_unchanged(key, value)
                    previous_values[prev_key] = value
        
        # Device information
        if 'device' in data:
            device = data['device']
            print_header(f"📱 DEVICE: {device.get('name', 'Unknown')}")
            print(f"  ID: {device.get('id', 'N/A')} | "
                  f"Unique ID: {device.get('uniqueId', 'N/A')} | "
                  f"Status: {device.get('status', 'N/A')}")
        
        # Position data with IO values
        if 'position' in data:
            position = data['position']
            print_header(f"📍 POSITION DATA")
            
            # Basic position info
            print_subheader("Basic Info:")
            basic_fields = {
                'protocol': position.get('protocol'),
                'deviceId': position.get('deviceId'),
                'deviceTime': position.get('deviceTime'),
                'fixTime': position.get('fixTime'),
                'serverTime': position.get('serverTime'),
                'latitude': position.get('latitude'),
                'longitude': position.get('longitude'),
                'altitude': position.get('altitude'),
                'speed': position.get('speed'),
                'course': position.get('course'),
                'accuracy': position.get('accuracy'),
                'valid': position.get('valid'),
            }
            
            for key, value in basic_fields.items():
                if value is not None:
                    prev_key = f"position.{key}"
                    if prev_key in previous_values and previous_values[prev_key] != value:
                        print_change(key, previous_values[prev_key], value)
                    else:
                        print_unchanged(key, value)
                    previous_values[prev_key] = value
            
            # Attributes (IO values)
            if 'attributes' in position:
                attrs = position['attributes']
                print_subheader(f"\n🔧 ATTRIBUTES / IO VALUES ({len(attrs)} items):")
                
                # Separate IO values from other attributes
                io_values = {}
                other_attrs = {}
                
                for key, value in sorted(attrs.items()):
                    if key.startswith('io') or key.startswith('avl'):
                        io_values[key] = value
                    else:
                        other_attrs[key] = value
                
                # Display IO values first (these are the most important)
                if io_values:
                    print(f"\n  {Colors.BOLD}IO/AVL Values:{Colors.END}")
                    for key, value in sorted(io_values.items()):
                        prev_key = f"attr.{key}"
                        if prev_key in previous_values and previous_values[prev_key] != value:
                            print_change(key, previous_values[prev_key], value)
                        elif prev_key not in previous_values:
                            print_new(key, value)
                        else:
                            print_unchanged(key, value)
                        previous_values[prev_key] = value
                
                # Display other attributes
                if other_attrs:
                    print(f"\n  {Colors.BOLD}Other Attributes:{Colors.END}")
                    for key, value in sorted(other_attrs.items()):
                        prev_key = f"attr.{key}"
                        if prev_key in previous_values and previous_values[prev_key] != value:
                            print_change(key, previous_values[prev_key], value)
                        elif prev_key not in previous_values:
                            print_new(key, value)
                        else:
                            print_unchanged(key, value)
                        previous_values[prev_key] = value
        
        print_separator('─')
        print()
    
    def display_form_data(self, data, timestamp):
        """Display form-encoded webhook data"""
        global previous_values
        
        print_separator('━')
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══ WEBHOOK EVENT #{event_counter} (FORM) ═══ "
              f"{format_timestamp(timestamp)} ═══{Colors.END}")
        print_separator('━')
        
        print_header("📦 FORM DATA:")
        for key, values in sorted(data.items()):
            value = values[0] if isinstance(values, list) else values
            prev_key = f"form.{key}"
            
            if prev_key in previous_values and previous_values[prev_key] != value:
                print_change(key, previous_values[prev_key], value)
            elif prev_key not in previous_values:
                print_new(key, value)
            else:
                print_unchanged(key, value)
            previous_values[prev_key] = value
        
        print_separator('─')
        print()
    
    def log_to_file(self, timestamp, data):
        """Log webhook data to file for later analysis"""
        try:
            with open(LOG_FILE, 'a') as f:
                log_entry = {
                    'timestamp': timestamp.isoformat(),
                    'event_number': event_counter,
                    'data': data
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Silently fail if logging fails - don't interrupt monitoring
            pass

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    running = False
    print(f"\n\n{Colors.YELLOW}{'='*100}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}🛑 Stopping webhook monitor...{Colors.END}")
    print(f"{Colors.YELLOW}{'='*100}{Colors.END}")
    print(f"\n{Colors.GREEN}Total events received: {event_counter}{Colors.END}")
    print(f"{Colors.GREEN}Log file: {LOG_FILE}{Colors.END}\n")
    sys.exit(0)

def run_server():
    """Run the webhook server"""
    server = HTTPServer(('0.0.0.0', WEBHOOK_PORT), EnhancedTraccarWebhookHandler)
    
    clear_screen()
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                         TRACCAR WEBHOOK MONITOR - ENHANCED EDITION                            ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    print(f"{Colors.GREEN}✓{Colors.END} Listening on port: {Colors.BOLD}{WEBHOOK_PORT}{Colors.END}")
    print(f"{Colors.GREEN}✓{Colors.END} Monitoring all IO values, AVL IDs, and events")
    print(f"{Colors.GREEN}✓{Colors.END} Logging to: {LOG_FILE}")
    print(f"{Colors.GREEN}✓{Colors.END} Press {Colors.BOLD}Ctrl+C{Colors.END} to stop\n")
    print(f"{Colors.DIM}Legend:")
    print(f"  {Colors.GREEN}✓{Colors.END} New value  |  {Colors.YELLOW}▶{Colors.END} Changed value  |  {Colors.DIM}•{Colors.END} Unchanged value")
    print(f"{Colors.END}")
    print_separator('═')
    print(f"{Colors.YELLOW}Waiting for webhook data...{Colors.END}\n")
    
    # Run server in a loop
    while running:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Colors.RED}Error in server loop: {e}{Colors.END}")

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Clear old log file
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except:
        pass
    
    try:
        run_server()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"{Colors.RED}❌ Error: Port {WEBHOOK_PORT} is already in use!{Colors.END}")
            print(f"\n{Colors.YELLOW}Options:{Colors.END}")
            print(f"1. Stop the process using port {WEBHOOK_PORT}")
            print(f"2. Edit the script and change WEBHOOK_PORT to a different value")
            print(f"3. Find the process: {Colors.BOLD}lsof -i :{WEBHOOK_PORT}{Colors.END}")
        else:
            print(f"{Colors.RED}Fatal error: {e}{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.END}")
        sys.exit(1)
