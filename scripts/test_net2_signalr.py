#!/usr/bin/env python3
"""
Test script to investigate Net2 SignalR door events.
Tests both doorEvents and doorStatusEvents to see what information is available.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from pathlib import Path

# Load configuration
CONFIG_FILE = Path(__file__).parent / "net2_config.json"
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

# Configuration
BASE_URL = config['base_url'].replace('/api/v1', '')
USERNAME = config['username']
PASSWORD = config['password']
DOOR_ADDRESS = "6612642"  # Test door

class Net2SignalRTester:
    def __init__(self):
        self.token = None
        self.session = None
        self.connection_token = None
        self.message_id = 0
        
    async def authenticate(self):
        """Get authentication token"""
        print(f"[{self.timestamp()}] Authenticating...")
        
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        auth_url = f"{BASE_URL}/api/v1/authorization/tokens"
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "grant_type": "password",
            "client_id": config.get('client_id', '00aab996-6439-4f16-89b4-6c0cc851e8f3')
        }
        
        async with self.session.post(auth_url, data=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data.get('access_token')
                print(f"[{self.timestamp()}] ✓ Authentication successful")
                return True
            else:
                text = await response.text()
                print(f"[{self.timestamp()}] ✗ Authentication failed: {response.status} - {text}")
                return False
    
    async def negotiate_signalr(self):
        """Negotiate SignalR connection"""
        print(f"[{self.timestamp()}] Negotiating SignalR connection...")
        
        negotiate_url = f"{BASE_URL}/signalr/negotiate"
        params = {
            "clientProtocol": "1.5",
            "connectionData": json.dumps([{"name": "eventHubLocal"}]),
            "_": str(int(datetime.now().timestamp() * 1000))
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        async with self.session.get(negotiate_url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.connection_token = data.get('ConnectionToken')
                print(f"[{self.timestamp()}] ✓ SignalR negotiation successful")
                return True
            else:
                print(f"[{self.timestamp()}] ✗ SignalR negotiation failed: {response.status}")
                return False
    
    async def classic_start(self, connection_token):
        """Call start endpoint for classic SignalR"""
        start_url = f"{BASE_URL}/signalr/start"
        params = {
            "transport": "webSockets",
            "clientProtocol": "1.5",
            "connectionToken": connection_token,
            "connectionData": json.dumps([{"name": "eventHubLocal"}])
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        async with self.session.get(start_url, params=params, headers=headers) as response:
            if response.status == 200:
                print(f"[{self.timestamp()}] ✓ Classic SignalR start completed")
                return True
            else:
                text = await response.text()
                print(f"[{self.timestamp()}] ⚠ Classic start warning: {response.status} - {text}")
                return False
    
    async def connect_signalr(self):
        """Connect to SignalR WebSocket"""
        print(f"[{self.timestamp()}] Connecting to SignalR WebSocket...")
        
        # First call start for classic SignalR
        await self.classic_start(self.connection_token)
        
        ws_url = f"{BASE_URL.replace('https://', 'wss://')}/signalr/connect"
        params = {
            "transport": "webSockets",
            "clientProtocol": "1.5",
            "connectionToken": self.connection_token,
            "connectionData": json.dumps([{"name": "eventHubLocal"}])
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        # Build full URL with params  
        from urllib.parse import urlencode
        param_str = urlencode(params)
        full_ws_url = f"{ws_url}?{param_str}"
        
        async with self.session.ws_connect(full_ws_url, headers=headers, ssl=False) as ws:
            print(f"[{self.timestamp()}] ✓ Connected to SignalR WebSocket")
            
            # Subscribe to both door event streams
            await self.subscribe_to_door_events(ws)
            await self.subscribe_to_door_status_events(ws)
            
            print(f"\n{'='*80}")
            print(f"LISTENING FOR EVENTS - Open/close door {DOOR_ADDRESS} to test")
            print(f"{'='*80}\n")
            
            # Listen for events
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"[{self.timestamp()}] ✗ WebSocket error: {ws.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print(f"[{self.timestamp()}] WebSocket connection closed")
                    break
    
    async def subscribe_to_door_events(self, ws):
        """Subscribe to doorEvents stream"""
        self.message_id += 1
        subscribe_msg = {
            "H": "eventHubLocal",
            "M": "subscribeToDoorEvents",
            "A": [DOOR_ADDRESS],
            "I": self.message_id
        }
        await ws.send_str(json.dumps(subscribe_msg))
        print(f"[{self.timestamp()}] → Subscribed to doorEvents for door {DOOR_ADDRESS}")
    
    async def subscribe_to_door_status_events(self, ws):
        """Subscribe to doorStatusEvents stream"""
        self.message_id += 1
        subscribe_msg = {
            "H": "eventHubLocal",
            "M": "subscribeToDoorStatusEvents",
            "A": [DOOR_ADDRESS],
            "I": self.message_id
        }
        await ws.send_str(json.dumps(subscribe_msg))
        print(f"[{self.timestamp()}] → Subscribed to doorStatusEvents for door {DOOR_ADDRESS}")
    
    async def handle_message(self, data):
        """Handle incoming SignalR messages"""
        if not data or data == "{}":
            return
        
        try:
            msg = json.loads(data)
            
            # Subscription confirmation
            if "R" in msg:
                print(f"[{self.timestamp()}] ✓ Subscription confirmed: {msg}")
                return
            
            # Event messages
            if "M" in msg:
                for message in msg["M"]:
                    method = message.get("M")
                    args = message.get("A", [])
                    
                    if method == "doorEvents":
                        print(f"\n{'='*80}")
                        print(f"[{self.timestamp()}] 📨 DOOR EVENT RECEIVED")
                        print(f"{'='*80}")
                        print(json.dumps(args, indent=2))
                        print(f"{'='*80}\n")
                    
                    elif method == "doorStatusEvents":
                        print(f"\n{'='*80}")
                        print(f"[{self.timestamp()}] 📊 DOOR STATUS EVENT RECEIVED")
                        print(f"{'='*80}")
                        if args:
                            status = args[0]
                            print(f"Door ID: {status.get('doorId')}")
                            print(f"Notification Type: {status.get('notificationType')}")
                            print(f"\nStatus Details:")
                            status_obj = status.get('status', {})
                            print(f"  • Door Contact Closed: {status_obj.get('doorContactClosed')}")
                            print(f"  • Door Relay Open: {status_obj.get('doorRelayOpen')}")
                            print(f"  • PSU Contact Closed: {status_obj.get('psuContactClosed')}")
                            print(f"  • Tamper Contact Closed: {status_obj.get('tamperContactClosed')}")
                            print(f"  • Intruder Alarm Armed: {status_obj.get('intruderAlarmArmed')}")
                            print(f"  • Alarm Tripped: {status_obj.get('alarmTripped')}")
                        print(f"{'='*80}\n")
                    
                    else:
                        print(f"[{self.timestamp()}] 📬 Other event: {method}")
                        print(json.dumps(args, indent=2))
            
        except json.JSONDecodeError:
            print(f"[{self.timestamp()}] Invalid JSON: {data}")
    
    def timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def main():
    tester = Net2SignalRTester()
    
    try:
        # Authenticate
        if not await tester.authenticate():
            return
        
        # Negotiate SignalR
        if not await tester.negotiate_signalr():
            return
        
        # Connect and listen
        await tester.connect_signalr()
        
    except KeyboardInterrupt:
        print(f"\n[{tester.timestamp()}] Test interrupted by user")
    except Exception as e:
        print(f"\n[{tester.timestamp()}] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    print("="*80)
    print("Net2 SignalR Door Events Test")
    print("="*80)
    print(f"Testing door: {DOOR_ADDRESS}")
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    print("\nPress Ctrl+C to stop\n")
    
    asyncio.run(main())
