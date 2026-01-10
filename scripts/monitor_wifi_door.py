#!/usr/bin/env python3
"""
Net2 SignalR Event Monitor

Monitors all door events from Paxton Net2 system via SignalR including:
- LiveEvents: All access control events (badge swipes, access granted/denied)
- DoorEvents: Door open/closed status changes
- DoorStatusEvents: Door relay and sensor status updates
- RollCallEvents: Emergency roll call events

Usage:
    cd /etc/openhab/scripts
    source /etc/openhab/.venv/bin/activate
    python3 monitor_wifi_door.py

Configuration:
    Scripts location: /etc/openhab/scripts/
    Edit /etc/openhab/scripts/net2_config.json to set Net2 server credentials
    Edit ALL_DOOR_IDS list in this script to monitor specific doors

Output:
    Displays real-time events with timestamps and full JSON payloads
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

# Known door IDs from Net2 system
ALL_DOOR_IDS = [
    6612642,   # Front Door
    6203980,   # Terndrupvej 81
    7242929,   # Garage Port - Kirkegade
    6626578,   # Udv.Basement - Kirkegade
    5598430    # WiFi Door
]

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
            print(f"MONITORING ALL DOORS")
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
        
        # 2. Subscribe to DoorEvents for each known door
        msg_id = 2
        for door_id in ALL_DOOR_IDS:
            subscribe_door = {
                "H": "eventHubLocal",
                "M": "subscribeToDoorEvents",
                "A": [door_id],
                "I": msg_id
            }
            await ws.send_str(json.dumps(subscribe_door))
            msg_id += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → Subscribed to DoorEvents for {len(ALL_DOOR_IDS)} doors")
        
        # 3. Subscribe to DoorStatusEvents for each known door
        for door_id in ALL_DOOR_IDS:
            subscribe_status = {
                "H": "eventHubLocal",
                "M": "subscribeToDoorStatusEvents",
                "A": [door_id],
                "I": msg_id
            }
            await ws.send_str(json.dumps(subscribe_status))
            msg_id += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → Subscribed to DoorStatusEvents for {len(ALL_DOOR_IDS)} doors")
    
    async def handle_message(self, data):
        """Handle incoming SignalR messages"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        try:
            msg = json.loads(data)
            
            # Skip subscription confirmations
            if "R" in msg or "I" in msg:
                return
            
            # Process event messages
            if isinstance(msg, dict) and "M" in msg:
                for message in msg["M"]:
                    hub = message.get("H", "")
                    target = message.get("M", "")
                    args = message.get("A", [])
                    
                    if hub == "EventHubLocal" and target in ["DoorStatusEvents", "DoorEvents", "LiveEvents", "RollCallEvents"]:
                        for arg_array in args:
                            if isinstance(arg_array, list):
                                for arg in arg_array:
                                    if isinstance(arg, dict):
                                        door_id = arg.get("doorId") or arg.get("deviceId")
                                        
                                        if target == "LiveEvents":
                                            event_type = arg.get("eventType", "?")
                                            event_subtype = arg.get("eventSubType", "?")
                                            user = arg.get("userName", "?")
                                            device = arg.get("deviceId", "?")
                                            area = arg.get("areaName", "?")
                                            
                                            if device == WIFI_DOOR_ID:
                                                print(f"\n{'🚪'*40}")
                                                print(f"[{timestamp}] ⭐ WiFi DOOR {WIFI_DOOR_ID} LIVE EVENT!")
                                                print(json.dumps(arg, indent=2))
                                                print(f"{'🚪'*40}\n")
                                            else:
                                                print(f"\n[{timestamp}] 📡 LiveEvent - Device:{device}, Type:{event_type}/{event_subtype}, User:{user}")
                                                print(f"  Area: {area}")
                                        
                                        elif door_id == WIFI_DOOR_ID:
                                            print(f"\n{'🚪'*40}")
                                            print(f"[{timestamp}] ⭐ WiFi DOOR {WIFI_DOOR_ID} {target}!")
                                            print(json.dumps(arg, indent=2))
                                            print(f"{'🚪'*40}\n")
                                        elif door_id is not None:
                                            print(f"\n[{timestamp}] 🚪 Door {door_id} - {target}")
                                            print(json.dumps(arg, indent=2))
                                        elif target == "RollCallEvents":
                                            print(f"\n[{timestamp}] 📋 RollCallEvent:")
                                            print(json.dumps(arg, indent=2))
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"[{timestamp}] Error: {e}")
    
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
