# Paxton Net2 Access Control Binding

This binding provides integration with the Paxton Net2 Access Control system via its REST API.

## Features

- **Door Control**: Open/close doors remotely, timed open (advanced)
- **Real-time Synchronization**: Hybrid sync with SignalR real-time events + API polling fallback
- **Status Monitoring**: Live door lock/unlock status synchronized with Net2 server
- **Access Logging**: Track last user and access time per door
- **Multi-Door Support**: Control multiple doors from a single Net2 server
- **Token Management**: Automatic JWT token refresh (30-min tokens)
- **User Management**: Create/delete users and assign access levels from the bridge

## Requirements

- OpenHAB 5.0+
- Paxton Net2 6.6 SR5 or newer
- Net2 Local API enabled and licensed
- Valid API client credentials

## Installation

1. Copy the binding JAR to `addons/`
2. Restart OpenHAB
3. The binding will appear in Add-ons → Bindings

## Configuration

### Bridge: Net2 Server

Create a bridge thing to represent your Net2 server:

**Configuration Parameters:**
- `hostname` - Net2 server hostname/IP
- `port` - HTTPS port (default: 8443)
- `username` - Net2 operator username (First Name Last Name)
- `password` - Net2 operator password
- `clientId` - Net2 API license Client ID
- `tlsVerification` - Enable/disable SSL certificate verification (default: true)
- `refreshInterval` - Door status polling interval in seconds (default: 600 = 10 minutes, now that SignalR provides instant updates)

### Thing: Net2 Door

Add door things as children of the Net2 Server bridge:

**Configuration Parameters:**
- `doorId` - Net2 Door ID (serial number) - Required
- `name` - User-friendly door name (optional)

## Channels

### Door Channels

Each door exposes the following channels:

| Channel         | Type     | Access | Description                                 |
|-----------------|----------|--------|---------------------------------------------|
| `status`        | Switch   | RO     | Door relay physical status (ON=Open, OFF=Closed) - Real-time via SignalR doorRelayOpen |
| `action`        | Switch   | RW     | Control door (ON=Hold Open, OFF=Close) - For manual control |
| `controlTimed`  | Number   | RW     | Timed open in seconds (1=1sec, 5=5sec, etc.) - Server-side timing |
| `lastAccessUser`| String   | RO     | Last user who accessed the door             |
| `lastAccessTime`| DateTime | RO     | Timestamp of last door access               |

**Synchronization Behavior:**
- `status` channel: Shows **physical door relay state** - receives instant updates via SignalR DoorStatusEvents with `doorRelayOpen` field
  - Updates in real-time when door opens (doorRelayOpen: true → ON)
  - Updates in real-time when door closes (doorRelayOpen: false → OFF)
  - Works for ALL door operations: OpenHAB commands, Net2 UI, physical cards, timed opens
- `action` channel: Used for **manual control** - can be synced to status via rules
- Both channels backed by:
  - **SignalR DoorStatusEvents** - Instant updates with doorRelayOpen field
  - **API polling** - Fallback synchronization every 10 minutes (configurable via `refreshInterval`)
- SignalR provides <500ms latency; API polling serves as backup for network issues

See [EXAMPLES.md](EXAMPLES.md) for advanced timed control usage and custom payloads.

### Bridge Channels
## Author

- Nanna Agesen (@Prinsessen)
- Email: nanna@agesen.dk
- GitHub: https://github.com/Prinsessen

The Net2 Server bridge exposes the following user-management channels:

| Channel | Type | Access | Description |
|---------|------|--------|-------------|
| `createUser` | String | WO | Create a user: `firstName,lastName,accessLevel,pin` (e.g., `Michael,Agesen,3,7654`). Access level may be ID or name; it is assigned after creation. |
| `deleteUser` | String | WO | Delete a user by ID (e.g., `79`). |
| `listAccessLevels` | String | WO | Query available access levels. Send any command (e.g., `REFRESH` or `ON`) to trigger. Results logged to `/var/log/openhab/openhab.log` as: `Access levels: [1:Public] [2:Staff] ...` |

## Example Configuration

### Text Files (.things)

```
Bridge net2:net2server:myserver [hostname="net2.example.com", port=8443, username="your_username", password="your_secure_password", clientId="your_oauth_client_id"] {
    Thing door fordoor [doorId=6203980, name="Front Door"]
    Thing door backdoor [doorId=6203981, name="Back Door"]
}
```

### Items (.items)

```
Switch Front_Door_Lock "Front Door" <lock> { channel="net2:door:myserver:fordoor:action" }
Switch Front_Door_Status "Front Door Status" <door> { channel="net2:door:myserver:fordoor:status" }
String Front_Door_LastUser "Last Access: [%s]" { channel="net2:door:myserver:fordoor:lastAccessUser" }
DateTime Front_Door_LastTime "Last Access Time [%1$td.%1$tm.%1$tY %1$tH:%1$tM:%1$tS]" { channel="net2:door:myserver:fordoor:lastAccessTime" }

// Bridge channels (user management)
String Net2_CreateUser        "Create User"        { channel="net2:net2server:myserver:createUser" }
String Net2_DeleteUser        "Delete User"        { channel="net2:net2server:myserver:deleteUser" }
String Net2_ListAccessLevels  "List Access Levels" { channel="net2:net2server:myserver:listAccessLevels" }
```

### Usage Examples

Create a user and assign access level 3 with PIN 7654:

```
sendCommand(Net2_CreateUser, "Michael,Agesen,3,7654")
```

List access levels (query Net2 system and log results):

**From Rules:**
```java
sendCommand(Net2_ListAccessLevels, ON)
// or
sendCommand(Net2_ListAccessLevels, "REFRESH")
```

**From OpenHAB UI:**
- Navigate to the item `Net2_ListAccessLevels`
- Click and send any command (ON, OFF, REFRESH, etc.)

**From REST API:**
```bash
curl -X POST "http://localhost:8080/rest/items/Net2_ListAccessLevels" \
  -H "Content-Type: text/plain" \
  -d "ON"
```

**From Karaf Console:**
```bash
openhab-cli console -p habopen
openhab> openhab:send Net2_ListAccessLevels ON
```

View the results in log:
```bash
grep "Access levels" /var/log/openhab/openhab.log | tail -1
# Output example: Access levels: [1:Public] [2:Staff] [3:Admin] [5:Maintenance]
```

Delete a user by ID:

```
sendCommand(Net2_DeleteUser, "79")
```

## Rules Example

```
rule "Door Opened"
when
    Item Front_Door_Status changed to ON
then
    logInfo("Door", "Front door has been opened")
end

rule "Unlock Front Door"
when
    Item Security_Command received command ON
then
    Front_Door_Lock.sendCommand(ON)
    logInfo("Door", "Unlocking front door")
end
```

## API Details

### Authentication
- Uses OAuth2 JWT tokens
- Tokens valid for 30 minutes
- Automatic refresh token handling
- Credentials stored securely in OpenHAB configuration

### Real-time Synchronization

The binding uses a hybrid synchronization approach for reliable door state tracking:

**SignalR Real-time Events:**
- WebSocket connection to Net2 server using SignalR 2 Classic protocol
- Subscribes to **DoorStatusEvents** with `doorRelayOpen` field:
  - `doorRelayOpen: true` → Door relay is OPEN (status channel = ON)
  - `doorRelayOpen: false` → Door relay is CLOSED (status channel = OFF)
- Also subscribes to LiveEvents for access logging (eventType 20, 28, 46)
- **Sub-500ms latency** for door state changes
- Tracks physical door relay state regardless of trigger method (OpenHAB, Net2 UI, card readers, timed opens)
- Event format: `{"target": "DoorStatusEvents", "payload": {"deviceId": 6612642, "status": {"doorRelayOpen": true}}}`

**API Polling Fallback:**
- Periodic status checks via REST API (`GET /api/v1/doors/status`)
- Default: every 10 minutes (configurable via `refreshInterval`)
- Provides backup synchronization if SignalR connection drops
- Parses `doorRelayOpen` field from status object
- Default interval: 30 seconds (configurable via `refreshInterval`)
- Reads actual door relay status (`doorRelayOpen` field)
- Updates both `action` and `status` channels with current state
- Ensures synchronization even if SignalR events are missed

**Why Hybrid Approach?**
- SignalR `doorEvents` and `doorStatusEvents` documented but not implemented by Net2 API
- Only `LiveEvents` hub available, providing eventType-based notifications
- EventType 47 (door closed) is inconsistently sent by the server
- API polling guarantees state accuracy within the refresh interval
- Combination provides both immediate response and guaranteed correctness

**Event Types:**
- `20` - Access granted (door opened via card reader)
- `28` - Door relay opened (timed control)
- `46` - Door forced/held open
- `47` - Door closed/secured (unreliable, hence API polling backup)

### REST API Endpoints
- **Authentication**: `POST /api/v1/authorization/tokens`
- **Door Control**: `POST /api/v1/commands/door/holdopen`, `POST /api/v1/commands/door/close`
- **Door Status**: `GET /api/v1/doors/status` (used for polling)
- **List Doors**: `GET /api/v1/doors`
- **SignalR Hub**: `wss://host:port/signalr` (LiveEvents hub)

## Security Considerations

1. **TLS Verification**: Always use TLS verification in production (tlsVerification=true)
2. **Credentials**: Use strong, unique passwords for API operators
3. **API Access**: Restrict Net2 server API access to trusted networks
4. **Token Handling**: Tokens are stored in memory and never persisted to disk

## Troubleshooting

### Bridge won't connect
- Verify hostname and port are correct
- Check username format (First Name Last Name)
- Ensure API is enabled in Net2 Configuration Utility
- Verify API license is installed
- Test connectivity: `curl -k https://host:8443/api/v1/doors`

### Door commands not working
- Verify door ID is correct (check Net2 Configuration)
- Ensure operator has permission to control doors
- Check OpenHAB logs for error messages

### Status not updating
- Verify refreshInterval is set appropriately (default: 30 seconds)
- Check bridge status is ONLINE
- Review OpenHAB logs for API errors
- For real-time debugging, filter logs: `grep -E "refreshDoorStatus|updateFromApiResponse|SignalR event" openhab.log`
- Verify SignalR connection: Look for "Subscribed to door events for door ID" in logs
- Check door relay status in API response: `doorRelayOpen` field should match UI state

## Building from Source

Prerequisites:
- Java 21 JDK
- Maven 3.6+
- Git

```bash
cd net2-binding
mvn clean install
```

## Support

For issues related to:
- **OpenHAB binding**: Check OpenHAB logs and community forum
- **Net2 API**: Contact Paxton Access support
- **Door hardware**: Contact your door system installer

## Maintainer

- Nanna Agesen (@Prinsessen) — Nanna@agesen.dk
