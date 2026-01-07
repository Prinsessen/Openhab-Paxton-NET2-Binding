# openHAB Paxton Net2 SignalR Binding

A real-time door access control binding for openHAB that integrates with [Paxton Net2 access control systems](https://www.paxton.co.uk) via their WebAPI and classic ASP.NET SignalR 2 protocol.

## Features

- **Real-time door events** via WebSocket (SignalR 2)
- **4 channels per door**: Status (activity pulse), Action (unlock command), Last Access User, Last Access Time
- **Automatic status pulse** - 5-second ON/OFF indication for door activity
- **OAuth token management** - Automatic renewal every ~30 minutes
- **Multi-door support** - Single server bridge with unlimited doors
- **Fallback polling** - API-based door status refresh if WebSocket unavailable
- **Discovery service** - Auto-discovery of connected doors from Net2 server

## Compatibility

- **openHAB Version**: 5.1.0 or later
- **Net2 Server**: Classic ASP.NET access control system with WebAPI enabled
- **Java**: 11+

## Installation

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

### Quick Start

1. Copy `org.openhab.binding.net2-5.1.0.jar` to `/usr/share/openhab/addons/`
2. Restart openHAB
3. Create a bridge in Things with:
    - **Host**: Your Net2 server hostname (e.g., `milestone.agesen.dk` or `prinsessen.agesen.dk`)
   - **Port**: API port (default: 8443)
   - **Username**: Admin credentials
   - **Password**: Admin credentials
   - **Client ID** & **Client Secret**: OAuth application credentials
4. Add Door Things under the bridge
5. Link items to door channels

## Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for detailed channel and item setup.

### Example Items

```openhab
// Door Status (ON when activity detected, OFF after 5 seconds)
Switch Net2_Door1_Status "Front Door [%s]" <door> { channel="net2:door:server:door1:status" }

// Door Unlock Action
Switch Net2_Door1_Unlock "Unlock Front Door" { channel="net2:door:server:door1:action" }

// Last Access Information
String Net2_Door1_User "Last User [%s]" { channel="net2:door:server:door1:lastAccessUser" }
DateTime Net2_Door1_Time "Last Access [%1$td.%1$tm.%1$tY %1$tH:%1$tM]" { channel="net2:door:server:door1:lastAccessTime" }
```

## Architecture

### SignalR Protocol

The binding uses **classic ASP.NET SignalR 2** (not Core) to establish persistent WebSocket connections:

1. **Negotiate** → Obtain transport information and token
2. **Connect** → Establish WebSocket connection
3. **Start** → Begin receiving real-time events
4. **Events** → Server pushes door access events (swipes, key codes, mobile unlock)

### Event Types

- **20**: Door unlock (generic)
- **28**: Door unlock (PIN/key code)
- **47**: Door unlock (mobile app)
- **Other LiveEvent codes**: Door activity indication

### OAuth Flow

1. Client uses Basic Auth with credentials to obtain Bearer token
2. Token included in Authorization header for all API calls
3. Token auto-refreshes every ~25 minutes (before expiry)
4. Failed token refresh triggers connection restart

## Channels

### Door Thing

| Channel | Type | Description | R/W |
|---------|------|-------------|-----|
| `status` | Switch | Door activity indicator (ON/OFF pulse) | R |
| `action` | Switch | Unlock command | W |
| `lastAccessUser` | String | Name of last person who accessed | R |
| `lastAccessTime` | DateTime | Timestamp of last access | R |

## Discovery

The binding includes an auto-discovery service:

1. Go to **Things → Discover** 
2. Select **Net2 Door Discovery**
3. Binding queries server API for all doors
4. Available doors appear in Inbox
5. Accept to auto-create Door Things

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Connection issues
- Missing events
- Token refresh failures
- WebSocket timeouts
- Debug logging setup

## Build from Source

```bash
# Clone repository
git clone https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding.git
cd Openhab-Paxton-NET2-Binding

# Build with Maven
mvn clean install

# JAR file will be in: target/org.openhab.binding.net2-5.1.0.jar
```

## Project Structure

```
├── pom.xml                                  # Maven configuration
├── src/main/java/org/openhab/binding/net2/
│   ├── Net2BindingConstants.java           # Constants (channel IDs, config keys)
│   ├── handler/
│   │   ├── Net2ServerHandler.java          # Bridge handler (token, SignalR)
│   │   ├── Net2DoorHandler.java            # Door handler (status, events)
│   │   ├── Net2SignalRClient.java          # Classic SignalR 2 client
│   │   ├── Net2ApiClient.java              # REST API client
│   │   └── Net2HandlerFactory.java         # Thing handler factory
│   └── discovery/
│       └── Net2DoorDiscoveryService.java   # Auto-discovery service
└── src/main/resources/OH-INF/
    ├── binding/binding.xml                 # Binding metadata
    └── thing/thing-types.xml              # Channel definitions
```

## Key Files

### `Net2SignalRClient.java`
Classic ASP.NET SignalR 2 WebSocket client with:
- Dual-mode support (classic + Core)
- Token-based Bearer auth
- Automatic token refresh
- Event dispatch via callbacks
- Connection state management
- Proper URI encoding for query parameters

### `Net2DoorHandler.java`
Per-door event processor:
- Maps SignalR events to item states
- Manages 5-second status pulse timer
- Preserves lastAccessUser/Time across API refreshes
- Handles unlock commands

### `Net2ServerHandler.java`
Bridge handler managing:
- OAuth authentication
- Token lifecycle
- SignalR client lifecycle
- Periodic API polling
- Door discovery

## Development Notes

- **Token Expiry**: ~30 minutes. Binding refreshes at ~25 minutes to avoid expiration.
- **Status Pulse**: All LiveEvent codes (20, 28, 47, etc.) trigger 5-second ON pulse.
- **URI Encoding**: Uses `URI.create()` with pre-formatted strings to avoid double-encoding.
- **Message Dispatch**: Unwraps nested SignalR JSON arrays for classic protocol.
- **Thread Safety**: Scheduled executors used for timers; state updates thread-safe.

## Security

- Credentials stored in openHAB's secure config (encrypted in items storage)
- OAuth tokens used for API calls (not basic auth)
- HTTPS recommended for Net2 server communication
- WebSocket uses SSL/TLS when server uses HTTPS

## License

This project is licensed under the **Eclipse Public License 2.0** (EPL-2.0) - see the [LICENSE](LICENSE) file for details.

This is the same license used by the openHAB project, ensuring compatibility and adherence to community standards.

**What this means:**
- ✅ Free to use, modify, and distribute
- ✅ Commercial use allowed
- ✅ Must include copyright notice and license
- ✅ Changes must be documented
- ✅ Patent grant included

## Support

- **Issues/Questions**: Submit via GitHub Issues
- **Net2 API Docs**: Contact Paxton support
- **openHAB Community**: https://community.openhab.org

## Changelog

### v5.1.0 (Initial Release)
- Classic ASP.NET SignalR 2 protocol support
- Real-time door event streaming
- Auto-off status indication
- OAuth token management
- Multi-door support
- Discovery service
- API polling fallback
