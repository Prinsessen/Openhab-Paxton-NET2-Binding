#!/usr/bin/env python3
"""
Hikvision Webhook Monitor
Captures and displays all webhook notifications from Hikvision cameras
"""

from flask import Flask, request, Response
from datetime import datetime
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)

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

def pretty_print_xml(xml_string):
    """Pretty print XML data"""
    try:
        root = ET.fromstring(xml_string)
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    except:
        return xml_string

def print_separator():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_webhook_data(method, path, headers, params, body, content_type):
    """Print webhook data in a nice formatted way"""
    print_separator()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Header
    print(f"{Colors.HEADER}{Colors.BOLD}🎬 HIKVISION WEBHOOK EVENT 🎬{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Timestamp: {timestamp}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Method: {method} | Path: {path}{Colors.ENDC}")
    
    # Headers
    if headers:
        print(f"\n{Colors.WARNING}{Colors.BOLD}📋 Headers:{Colors.ENDC}")
        for key, value in headers.items():
            if key.lower() not in ['host', 'connection']:  # Skip boring headers
                print(f"  {Colors.OKGREEN}{key}:{Colors.ENDC} {value}")
    
    # Query Parameters
    if params:
        print(f"\n{Colors.WARNING}{Colors.BOLD}🔍 Query Parameters:{Colors.ENDC}")
        for key, value in params.items():
            print(f"  {Colors.OKGREEN}{key}:{Colors.ENDC} {value}")
    
    # Body Content
    if body:
        print(f"\n{Colors.WARNING}{Colors.BOLD}📦 Body Content:{Colors.ENDC}")
        print(f"  Content-Type: {content_type}")
        print(f"  Length: {len(body)} bytes\n")
        
        # Try to format based on content type
        if 'json' in content_type.lower():
            try:
                json_data = json.loads(body)
                print(json.dumps(json_data, indent=2))
            except:
                print(body)
        elif 'xml' in content_type.lower():
            print(pretty_print_xml(body))
        else:
            # Try XML anyway (Hikvision often sends XML)
            if body.strip().startswith('<'):
                print(pretty_print_xml(body))
            else:
                print(body)
    else:
        print(f"\n{Colors.FAIL}(No body content){Colors.ENDC}")
    
    print_separator()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all(path):
    """Catch all webhook requests"""
    
    # Get request data
    method = request.method
    headers = dict(request.headers)
    params = dict(request.args)
    body = request.get_data(as_text=True)
    content_type = request.content_type or 'unknown'
    
    # Print the webhook data
    print_webhook_data(method, f"/{path}", headers, params, body, content_type)
    
    # Return success response (important for Hikvision to not retry)
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><ResponseStatus><requestURL>/</requestURL><statusCode>2</statusCode><statusString>OK</statusString></ResponseStatus>',
        status=200,
        mimetype='application/xml'
    )

if __name__ == '__main__':
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        Hikvision Webhook Monitor - Starting...               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print(f"{Colors.OKGREEN}📡 Listening on: http://0.0.0.0:5001{Colors.ENDC}")
    print(f"{Colors.OKGREEN}🎯 Camera should send webhooks to: http://<your-openhab-ip>:5001/webhook{Colors.ENDC}")
    print(f"{Colors.WARNING}⚠️  Port 5001 - Won't conflict with Traccar (8090){Colors.ENDC}")
    print(f"{Colors.OKCYAN}💡 Press Ctrl+C to stop{Colors.ENDC}\n")
    
    try:
        # Run on port 5001 (Traccar uses 8090)
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}🛑 Stopping webhook monitor...{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}\n")
