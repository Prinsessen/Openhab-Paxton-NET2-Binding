# Paxton Net2 Access Control Binding

This binding provides integration with the Paxton Net2 Access Control system via its REST API, enabling door control, real-time status monitoring, access logging, user management, and building lockdown -- all from openHAB.

## Features

- **Door Control** -- Open/close doors remotely, timed open with server-side timing
- **Real-time Synchronization** -- Hybrid sync with SignalR real-time events (<500ms latency) + API polling fallback
- **SignalR Auto-Reconnect** -- Automatic reconnection with exponential backoff after Net2 server restart or network outage *(new in v5.2.1)*
- **Status Monitoring** -- Live door lock/unlock status via SignalR doorRelayOpen events
- **Access Logging** -- Track last user and access time per door, JSON-formatted entry events
- **Access Denied Detection** -- Real-time alerts for unauthorized access attempts (invalid cards/tokens)
- **User Management** -- Create/delete users and assign access levels from the bridge
- **Building Lockdown** -- Enable/disable lockdown across all configured doors
- **Activity Report** -- Auto-generated HTML report showing last 24h of access events, embeddable in sitemaps
- **Entry Log Dashboard** -- JSON entry events ready for InfluxDB persistence and Grafana visualization
- **Multi-Door Support** -- Control multiple doors from a single Net2 server
- **Token Management** -- Automatic JWT token refresh (30-min tokens)
- **Self-signed SSL** -- Works with Net2 self-signed certificates

## Requirements

- Paxton Net2 6.6 SR5 or newer
- Net2 Local API enabled and licensed
- Valid API client credentials (OAuth2)
- Paxton Net2 Plus ACU or Net2 Classic ACU (Nano/Paxlock not supported)

## Supported Things

| Thing Type | Description |
|-----------|-------------|
| net2server (Bridge) | Connection to Net2 server via REST API + SignalR |
| door | Individual door with relay control and status |

## Channels

### Door Channels

| Channel | Type | R/W | Description |
|---------|------|-----|-------------|
| status | Switch | RO | Door relay physical status (ON=Open, OFF=Closed) -- real-time via SignalR |
| action | Switch | RW | Control door (ON=Hold Open, OFF=Close) |
| controlTimed | Number | RW | Timed open in seconds (server-side timing) |
| lastAccessUser | String | RO | Last user who accessed the door |
| lastAccessTime | DateTime | RO | Timestamp of last door access |
| entryLog | String | RO | JSON entry event (physical badge access only) |
| accessDenied | String | RO | JSON access denied event (invalid card/token) |

### Bridge Channels

| Channel | Type | R/W | Description |
|---------|------|-----|-------------|
| createUser | String | WO | Create user: firstName,lastName,accessLevel,pin |
| deleteUser | String | WO | Delete user by ID |
| listAccessLevels | String | WO | Query and log all access levels |
| listUsers | String | WO | Query and log all users as JSON |
| lockdown | Switch | RW | Building lockdown (ON=enable, OFF=disable) |
| activityReport | String | RO | Last report update timestamp |

## Quick Start

### net2.things

```java
Bridge net2:net2server:myserver [
    hostname="net2.example.com",
    port=8443,
    username="John Doe",
    password="your_secure_password",
    clientId="your_oauth_client_id",
    tlsVerification=false,
    refreshInterval=600
] {
    Thing door frontdoor  [doorId=6203980, name="Front Door"]
    Thing door backdoor   [doorId=6203981, name="Back Door"]
    Thing door garage     [doorId=6203982, name="Garage"]
}
```

### net2.items

```java
Group gNet2 "Access Control" <lock>

// Front Door
Switch Front_Door_Lock     "Front Door"           <lock>     (gNet2) { channel="net2:door:myserver:frontdoor:action" }
Switch Front_Door_Status   "Front Door Status"     <door>     (gNet2) { channel="net2:door:myserver:frontdoor:status" }
String Front_Door_LastUser "Last Access [%s]"                 (gNet2) { channel="net2:door:myserver:frontdoor:lastAccessUser" }
DateTime Front_Door_LastTime "Last Time [%1$td.%1$tm.%1$tY %1$tH:%1$tM]" (gNet2) { channel="net2:door:myserver:frontdoor:lastAccessTime" }
String Front_Door_EntryLog "Entry Log [%s]"                   (gNet2) { channel="net2:door:myserver:frontdoor:entryLog" }
String Front_Door_Denied   "Access Denied [%s]"               (gNet2) { channel="net2:door:myserver:frontdoor:accessDenied" }

// Bridge - User Management
String Net2_CreateUser       "Create User"       { channel="net2:net2server:myserver:createUser" }
String Net2_DeleteUser       "Delete User"       { channel="net2:net2server:myserver:deleteUser" }
Switch Net2_Lockdown         "Building Lockdown"  { channel="net2:net2server:myserver:lockdown" }
```

## Rules Example

```java
rule "Door Opened"
when
    Item Front_Door_Status changed to ON
then
    logInfo("Door", "Front door has been opened")
end

rule "Access Denied Alert"
when
    Item Front_Door_Denied received update
then
    logWarn("Security", "Unauthorized access attempt: {}", Front_Door_Denied.state)
    sendNotification("admin@example.com", "Access denied at Front Door!")
end

rule "Create User"
when
    Item CreateUser_Button received command ON
then
    Net2_CreateUser.sendCommand("Michael,Agesen,3,7654")
end
```

## Activity Report

The binding auto-generates an HTML report at `/static/net2_activity.html`:

```
Webview url="/static/net2_activity.html" height=100
```

## Real-time Synchronization

The binding uses a hybrid approach:

| Method | Latency | Purpose |
|--------|---------|---------|
| SignalR WebSocket | <500ms | Instant door state changes via DoorStatusEvents |
| API Polling | 10 min (configurable) | Backup synchronization fallback |

SignalR subscribes to **DoorStatusEvents** (door relay open/close) and **LiveEvents** (access granted/denied events).

**Auto-Reconnect (v5.2.1):** If the Net2 server restarts or a network outage occurs, the binding automatically reconnects SignalR with exponential backoff (30s, 60s, 120s, 240s, 300s cap). All door subscriptions are re-established after reconnect. The API polling cycle also acts as a safety-net: if it detects SignalR is down with no reconnect scheduled, it triggers one immediately.

## Resources

- **Download JAR (v5.2.1):** [org.openhab.binding.net2-5.2.0-SNAPSHOT.jar](https://github.com/Prinsessen/openhab-net2-binding/releases/download/v5.2.1/org.openhab.binding.net2-5.2.0-SNAPSHOT.jar) (59 KB)
- **Source Code:** [github.com/Prinsessen/openhab-net2-binding](https://github.com/Prinsessen/openhab-net2-binding)
- **Full Documentation:** [README.md](https://github.com/Prinsessen/openhab-net2-binding/blob/main/README.md)
- **Quick Start Guide:** [QUICKSTART.md](https://github.com/Prinsessen/openhab-net2-binding/blob/main/QUICKSTART.md)
- **Examples:** [EXAMPLES.md](https://github.com/Prinsessen/openhab-net2-binding/blob/main/EXAMPLES.md)
- **Entry Log Dashboard (Grafana):** [ENTRY_LOGGING.md](https://github.com/Prinsessen/openhab-net2-binding/blob/main/ENTRY_LOGGING.md)
- **Changelog:** [CHANGELOG.md](https://github.com/Prinsessen/openhab-net2-binding/blob/main/CHANGELOG.md)
- **License:** EPL-2.0
