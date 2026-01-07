#!/usr/bin/env python3
import json
import ssl
import time
import threading
import urllib.parse
import urllib.request
import traceback
from datetime import datetime

try:
    import websocket  # websocket-client
except ImportError:
    websocket = None

CFG_PATH = "/etc/openhab/scripts/net2_signalr_config.json"

class Net2SignalRBridge:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ctx = ssl.create_default_context()
        if not cfg.get("tlsVerify", True):
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE
        self.token = None
        self.conn_token = None
        self.ws = None
        self.invoke_id = 1
        self.running = False
        self.conn_data = urllib.parse.quote('[{"name":"eventHubLocal"}]')
        self.headers = {}
        self.last_event_ts = 0
        self.door_map = {d["doorId"]: d for d in cfg.get("doors", [])}

    def auth(self):
        body = urllib.parse.urlencode({
            'username': self.cfg['username'],
            'password': self.cfg['password'],
            'grant_type': 'password',
            'client_id': self.cfg['clientId'],
            'scope': 'offline_access',
        }).encode()
        req = urllib.request.Request(
            f"https://{self.cfg['host']}:{self.cfg['port']}/api/v1/authorization/tokens",
            data=body,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, context=self.ctx) as r:
            tok = json.loads(r.read().decode())
            self.token = tok.get('access_token')
        self.headers = { 'Authorization': f'Bearer {self.token}' }
        print("[net2-bridge] Auth OK; token length:", len(self.token))

    def negotiate(self):
        url = (
            f"https://{self.cfg['host']}:{self.cfg['port']}/signalr/negotiate"
            f"?clientProtocol=1.5&connectionData={self.conn_data}&_={int(time.time()*1000)}"
        )
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self.ctx) as r:
            data = json.loads(r.read().decode())
        self.conn_token = data.get('ConnectionToken')
        if not self.conn_token:
            raise RuntimeError("No ConnectionToken from negotiate")
        print("[net2-bridge] Negotiate OK; ConnectionId:", data.get('ConnectionId'))

    def start(self):
        url = (
            f"https://{self.cfg['host']}:{self.cfg['port']}/signalr/start"
            f"?transport=webSockets&clientProtocol=1.5&connectionToken={urllib.parse.quote(self.conn_token)}"
            f"&connectionData={self.conn_data}"
        )
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self.ctx) as r:
            body = r.read().decode()
        if 'Started' not in body and '1' not in body:
            print("[net2-bridge] start response:", body)
        print("[net2-bridge] Start OK")

    def connect_ws(self):
        if websocket is None:
            raise RuntimeError("websocket-client not installed")
        ws_url = (
            f"wss://{self.cfg['host']}:{self.cfg['port']}/signalr/connect"
            f"?transport=webSockets&clientProtocol=1.5&connectionToken={urllib.parse.quote(self.conn_token)}"
            f"&connectionData={self.conn_data}"
        )
        header = [f"Authorization: Bearer {self.token}"]
        sslopt = {}
        if not self.cfg.get("tlsVerify", True):
            sslopt = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
        self.ws = websocket.WebSocketApp(
            ws_url,
            header=header,
            on_message=self.on_message,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error,
        )
        t = threading.Thread(target=self.ws.run_forever, kwargs={"sslopt": sslopt, "ping_interval": 20})
        t.daemon = True
        t.start()
        # Wait a moment for open
        time.sleep(1.0)

    def on_open(self, ws):
        print("[net2-bridge] WS open")

    def on_close(self, ws, code, msg):
        print("[net2-bridge] WS closed", code, msg)

    def on_error(self, ws, err):
        print("[net2-bridge] WS error:", err)

    def send_invoke(self, method, args=None):
        if args is None:
            args = []
        payload = {
            "H": "eventHubLocal",
            "M": method,
            "A": args,
            "I": self.invoke_id,
        }
        self.invoke_id += 1
        data = json.dumps(payload)
        try:
            self.ws.send(data)
            print(f"[net2-bridge] invoke {method} sent")
        except Exception:
            print("[net2-bridge] invoke send failed:")
            traceback.print_exc()

    def subscribe(self):
        # Subscribe live events first
        self.send_invoke("subscribeToLiveEvents")
        # Optional: subscribe to door status for configured doors
        for d in self.cfg.get('doors', []):
            self.send_invoke("subscribeToDoorStatusEvents", [d['doorId']])
            self.send_invoke("subscribeToDoorEvents", [d['doorId']])

    def on_message(self, ws, message):
        # Classic SignalR can deliver batches: {"C":"...","M":[{...}]}
        try:
            data = json.loads(message)
        except Exception:
            print("[net2-bridge] Non-JSON message:", message[:200])
            return
        # Batch of invocations
        if isinstance(data, dict) and 'M' in data and isinstance(data['M'], list):
            for entry in data['M']:
                hub = entry.get('H')
                method = entry.get('M')
                args = entry.get('A') or []
                if hub != 'eventHubLocal':
                    continue
                self.handle_event(method, args)
        else:
            # Heartbeats or acks can be ignored
            pass

    def handle_event(self, method, args):
        # We don't have exact schema; print once and try to parse common fields
        if args:
            evt = args[0]
        else:
            evt = {}
        # Debug sample occasionally
        now = time.time()
        if now - self.last_event_ts > 5:
            print(f"[net2-bridge] Event {method}: {json.dumps(evt)[:400]}")
            self.last_event_ts = now
        # Try to extract door id, user and timestamp
        door_id = evt.get('doorId') or evt.get('door') or evt.get('DoorId')
        if isinstance(door_id, dict) and 'id' in door_id:
            door_id = door_id.get('id')
        user = evt.get('userName') or evt.get('user') or evt.get('cardholder') or evt.get('UserName')
        ts = evt.get('timestamp') or evt.get('time') or evt.get('occurredAt')
        # Normalize time to ISO if possible
        if isinstance(ts, (int, float)):
            try:
                ts = datetime.fromtimestamp(ts/1000.0).isoformat()
            except Exception:
                ts = str(ts)
        if door_id in self.door_map:
            door_cfg = self.door_map[door_id]
            if user:
                self.update_item(door_cfg['itemLastUser'], user)
            if ts:
                self.update_item(door_cfg['itemLastTime'], ts)

    def update_item(self, item, state):
        # Write to openHAB REST
        oh = self.cfg.get('openhabUrl', 'http://localhost:8080').rstrip('/')
        url = f"{oh}/rest/items/{urllib.parse.quote(item)}/state"
        headers = {'Content-Type': 'text/plain'}
        if self.cfg.get('openhabToken'):
            headers['Authorization'] = f"Bearer {self.cfg['openhabToken']}"
        data = state if isinstance(state, (str, bytes)) else str(state)
        if isinstance(data, str):
            data = data.encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as r:
                if r.status not in (200,202):
                    print(f"[net2-bridge] Item {item} update status {r.status}")
        except Exception as e:
            print(f"[net2-bridge] Item {item} update failed: {e}")

    def run(self):
        self.running = True
        while self.running:
            try:
                self.auth()
                self.negotiate()
                self.connect_ws()
                self.start()
                self.subscribe()
                # Keep forever while WS thread runs; sleep and let ping keepalive work
                while self.running and self.ws and self.ws.keep_running:
                    time.sleep(5)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("[net2-bridge] Loop error:", e)
                traceback.print_exc()
                time.sleep(5)

if __name__ == '__main__':
    with open(CFG_PATH, 'r') as f:
        cfg = json.load(f)
    bridge = Net2SignalRBridge(cfg)
    bridge.run()
