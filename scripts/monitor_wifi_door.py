#!/usr/bin/env python3
"""
Monitor SignalR events for WiFi door (ID: 5598430)
Tests if WiFi doors send status updates even if not controllable via Net2 UI
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Load configuration
with open('net2_config.json') as f:
    config = json.load(f)

NET2_HOST = config['host']
NET2_PORT = config['port']
USERNAME = config['username']
PASSWORD = config['password']
CLIENT_ID = config['client_id']

WIFI_DOOR_ID = 5598430

class Net2SignalRMonitor:
    def __init__(self):
        self.base_url = f"https://{NET2_HOST}:{NET2_PORT}"
        self.token = None
        self.connection_token = None
        self.session = None
        
    async def authenticate(self):
        """Get OAuth token"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Authenticating...")
        
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        auth_url = f"{self.base_url}/api/v1/authorization/tokens"
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "clientId": CLIENT_ID
        }
        
        async with self.session.post(auth_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data.get("token")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Authenticated")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Authentication failed: {response.status}")
                return False
    
    async def connect_signalr(self):
        """Connect to SignalR"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Connecting to SignalR...")
        
        # Negotiate connection
        negotiate_url = f"{self.base_url}/signalr/negotiate?clientProtocol=1.5"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with self.session.get(negotiate_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.connection_token = data.get("ConnectionToken")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Connection token obtained")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Negotiate failed: {response.status}")
                return
        
        # Connect to WebSocket
        ws_url = f"wss://{NET2_HOST}:{NET2_PORT}/signalr/connect?transport=webSockets&clientProtocol=1.5&connectionToken={self.connection_token}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Opening WebSocket...")
        async with self.session.ws_connect(ws_url, headers=headers, ssl=False) as ws:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WebSocket connected")
            
            # Subscribe to events
            await self.subscribe_to_events(ws)
            
            # Listen for messages
            print(f"\n{'='*80}")
            print(f"MONITORING WiFi DOOR ID: {WIFI_DOOR_ID}")
            print(f"Watching for: DoorStatusEvents, DoorEvents, LiveEvents")
            print(f"Press Ctrl+C to stop")
            print(f"{'='*80}\n")
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"❌ WebSocket error")
                    break
    
    async def subscribe_to_events(self, ws):
        """Subscribe to SignalR hubs"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Subscribing to events...")
        
        # Subscribe to DoorStatusEvents (for doorRelayOpen)
        subscribe_msg = {
            "H": "eventHubLocal",
            "M": "SubscribeToDoorStatusEvents",
            "A": [WIFI_DOOR_ID],
            "I": 1
        }
        await ws.send_json(subscribe_msg)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → Subscribed to DoorStatusEvents for door {WIFI_DOOR_ID}")
        
        # Also subscribe to general door events
        subscribe_msg2 = {
            "H": "eventHubLocal",
            "M": "SubscribeToDoorEvents",
            "A": [WIFI_DOOR_ID],
            "I": 2
        }
        await ws.send_json(subscribe_msg2)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → Subscribed to DoorEvents for door {WIFI_DOOR_ID}")
    
    async def handle_message(self, data):
        """Handle incoming SignalR messages"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        try:
            msg = json.loads(data)
            
            # Check for door-related events
            if isinstance(msg, dict):
                # Check M field (Messages array)
                if "M" in msg:
                    for message in msg["M"]:
                        target = message.get("M", "")  # Method name
                        args = message.get("A", [])     # Arguments
                        
                        if target in ["DoorStatusEvents", "DoorEvents", "LiveEvents"]:
                            for arg in args:
                                if isinstance(arg, dict):
                                    door_id = arg.get("doorId") or arg.get("deviceId")
                                    
                                    if door_id == WIFI_DOOR_ID:
                                        print(f"\n{'🚪'*40}")
                                        print(f"[{timestamp}] ⭐ WiFi DOOR EVENT DETECTED!")
                                        print(f"Event Type: {target}")
                                        print(f"Full payload:")
                                        print(json.dumps(arg, indent=2))
                                        print(f"{'🚪'*40}\n")
                                    else:
                                        # Show other door events in gray for context
                                        print(f"[{timestamp}] Other door: {door_id} - {target}")
        except json.JSONDecodeError:
            pass  # Ignore non-JSON messages (keepalives, etc.)
        except Exception as e:
            print(f"[{timestamp}] Error processing message: {e}")
    
    async def run(self):
        """Main run loop"""
        try:
            if await self.authenticate():
                await self.connect_signalr()
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopped by user")
        finally:
            if self.session:
                await self.session.close()

async def main():
    monitor = Net2SignalRMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())
