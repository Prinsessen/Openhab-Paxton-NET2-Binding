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
- `refreshInterval` - Door status polling interval in seconds (default: 30)

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
| `status`        | Switch   | RO     | Door lock/unlock status (ON=Open, OFF=Closed) - Synchronized in real-time |
| `action`        | Switch   | RW     | Control door (ON=Hold Open, OFF=Close) - Synchronized with server state |
| `controlTimed`  | Number   | RW     | Timed open with server-side timing (seconds) |
| `lastAccessUser`| String   | RO     | Last user who accessed the door             |
| `lastAccessTime`| DateTime | RO     | Timestamp of last door access               |

**Synchronization Behavior:**
- `action` channel: Persistent state that stays ON until door is closed (manually, via Net2 UI, or by timeout)
- `status` channel: Momentary state showing current door relay status
- Both channels automatically sync with Net2 server state via:
  - **SignalR real-time events** - Instant updates when doors open (eventType 20, 28, 46)
  - **API polling** - Fallback synchronization every 30 seconds (configurable via `refreshInterval`)
- Door state synchronized regardless of control method (OpenHAB, Net2 UI, physical card reader, etc.)

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
| `listAccessLevels` | String | WO | Send any command (e.g., `REFRESH`) to log all available access levels. |

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

List access levels in the log:

```
sendCommand(Net2_ListAccessLevels, "REFRESH")
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
- Subscribes to LiveEvents hub for all doors on the server
- Door-specific subscriptions for each configured door
- Instant notifications for door access events (eventType 20, 28, 46)
- Event-driven state updates without polling delays

**API Polling Fallback:**
- Periodic status checks via REST API (`GET /api/v1/doors/status`)
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
