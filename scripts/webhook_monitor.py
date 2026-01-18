#!/usr/bin/env python3
"""
Traccar Webhook Monitor
Monitors all incoming webhook requests from Traccar to understand the data structure.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class WebhookMonitor(BaseHTTPRequestHandler):
    
    def log_request_details(self):
        """Log all details about the incoming request"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        print("\n" + "="*80)
        print(f"[{timestamp}] {self.command} {self.path}")
        print("="*80)
        
        # Parse URL and query parameters
        parsed_url = urlparse(self.path)
        print(f"\nPath: {parsed_url.path}")
        
        if parsed_url.query:
            print("\nQuery Parameters:")
            params = parse_qs(parsed_url.query)
            for key, values in params.items():
                for value in values:
                    print(f"  {key}: {value}")
                    # If it's a json parameter, try to pretty print it
                    if key == 'json':
                        try:
                            json_data = json.loads(value)
                            print(f"\n  Parsed JSON:")
                            print(json.dumps(json_data, indent=4))
                        except:
                            pass
        
        # Log headers
        print("\nHeaders:")
        for header, value in self.headers.items():
            print(f"  {header}: {value}")
        
        # Read and log body for POST requests
        if self.command == 'POST':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
                print("\nBody:")
                print(body)
                try:
                    json_data = json.loads(body)
                    print("\nParsed JSON:")
                    print(json.dumps(json_data, indent=4))
                except:
                    pass
        
        print("\n" + "="*80 + "\n")
    
    def do_GET(self):
        """Handle GET requests"""
        self.log_request_details()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def do_POST(self):
        """Handle POST requests"""
        self.log_request_details()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=8090):
    """Start the webhook monitoring server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookMonitor)
    
    print(f"Traccar Webhook Monitor")
    print(f"Listening on port {port}")
    print(f"Waiting for webhooks from Traccar...")
    print(f"Press Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down webhook monitor...")
        httpd.shutdown()

if __name__ == '__main__':
    import sys
    
    # Allow custom port via command line argument
    port = 8090
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            print("Usage: python3 webhook_monitor.py [port]")
            sys.exit(1)
    
    run_server(port)
