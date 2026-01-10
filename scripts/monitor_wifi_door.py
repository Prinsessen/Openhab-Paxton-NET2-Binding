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

# Extract host from base_url (remove https:// and /api/v1)
base_url = config['base_url']
NET2_HOST = base_url.replace('https://', '').replace('/api/v1', '').split(':')[0]
NET2_PORT = base_url.replace('https://', '').replace('/api/v1', '').split(':')[1] if ':' in base_url.replace('https://', '') else '8443'
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
            "grant_type": "password",
            "client_id": CLIENT_ID
        }
        
        async with self.session.post(auth_url, data=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data.get("access_token")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Authenticated")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Authentication failed: {response.status}")
                return False
    
    async def connect_signalr(self):
        """Connect to SignalR"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Connecting to SignalR...")
        
        # Negotiate connection
        negotiate_url = f"{self.base_url}/signalr/negotiate"
        params = {
            "clientProtocol": "1.5",
            "connectionData": json.dumps([{"name": "eventHubLocal"}]),
            "_": str(int(datetime.now().timestamp() * 1000))
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with self.session.get(negotiate_url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.connection_token = data.get("ConnectionToken")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Connection token obtained")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Negotiate failed: {response.status}")
                return
        
        # Call start endpoint for classic SignalR
        start_url = f"{self.base_url}/signalr/start"
        start_params = {
            "transport": "webSockets",
            "clientProtocol": "1.5",
            "connectionToken": self.connection_token,
            "connectionData": json.dumps([{"name": "eventHubLocal"}])
        }
        async with self.session.get(start_url, params=start_params, headers=headers) as response:
            if response.status == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Classic start completed")
        
        # Connect to WebSocket
        from urllib.parse import urlencode
        ws_url = f"{self.base_url.replace('https://', 'wss://')}/signalr/connect"
        ws_params = {
            "transport": "webSockets",
            "clientProtocol": "1.5",
            "connectionToken": self.connection_token,
            "connectionData": json.dumps([{"name": "eventHubLocal"}])
        }
        full_ws_url = f"{ws_url}?{urlencode(ws_params)}"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Opening WebSocket...")
        async with self.session.ws_connect(full_ws_url, headers=headers, ssl=False) as ws:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WebSocket connected")
            
            # Subscribe to events
            await self.subscribe_to_events(ws)
            
            # Listen for messages
            print(f"\n{'='*80}")
            print(f"MONITORING ALL DOORS (WiFi door {WIFI_DOOR_ID} highlighted)")
            print(f"Watching ALL 4 event types:")
            print(f"  1. LiveEvents (all monitorable events)")
            print(f"  2. DoorEvents (open/closed for all doors)")
            print(f"  3. DoorStatusEvents (status updates for all doors)")
            print(f"  4. RollCallEvents (safe/unsafe events)")
            print(f"Press Ctrl+C to stop")
            print(f"{'='*80}\n")
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"❌ WebSocket error")
                    break
    
    async def subscribe_to_events(self, ws):
        """Subscribe to all 4 SignalR event types"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Subscribing to all event types...")
        
        # 1. Subscribe to LiveEvents (all monitorable events)
        subscribe_live = {
            "H": "eventHubLocal",
            "M": "SubscribeToLiveEvents",
            "A": [],
            "I": 1
        }
        await ws.send_json(subscribe_live)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → Subscribed to LiveEvents (all events)")
        
        # Note: Not subscribing to specific door IDs anymore - LiveEvents should cover all doors
        # If we still want specific door subscriptions, we'd need to subscribe to each door individually
    
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
                        
                        if target in ["DoorStatusEvents", "DoorEvents", "LiveEvents", "RollCallEvents"]:
                            for arg in args:
                                if isinstance(arg, dict):
                                    door_id = arg.get("doorId") or arg.get("deviceId")
                                    
                                    if door_id == WIFI_DOOR_ID:
                                        # Highlight WiFi door
                                        print(f"\n{'🚪'*40}")
                                        print(f"[{timestamp}] ⭐ WiFi DOOR {WIFI_DOOR_ID} EVENT!")
                                        print(f"Event Type: {target}")
                                        print(f"Full payload:")
                                        print(json.dumps(arg, indent=2))
                                        print(f"{'🚪'*40}\n")
                                    elif door_id is not None:
                                        # Show all other door events with full details
                                        print(f"\n[{timestamp}] 🚪 Door {door_id} - {target}")
                                        print(json.dumps(arg, indent=2))
                                    elif target == "RollCallEvents":
                                        # Show roll call events
                                        print(f"\n[{timestamp}] 📋 RollCallEvent:")
                                        print(json.dumps(arg, indent=2))
                                    elif target == "LiveEvents":
                                        # Show live events that aren't door-specific
                                        event_type = arg.get("eventType", "unknown")
                                        user = arg.get("userName", "unknown")
                                        device = arg.get("deviceId", "unknown")
                                        print(f"[{timestamp}] 📡 LiveEvent: Type={event_type}, User={user}, Device={device}")
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
