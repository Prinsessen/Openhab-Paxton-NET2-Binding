# Paxton Net2 Access Control Binding

This binding provides integration with the Paxton Net2 Access Control system via its REST API.

## Features

- **Door Control**: Open/close doors remotely
- **Status Monitoring**: Real-time door lock/unlock status
- **Access Logging**: Track last user and access time per door
- **Multi-Door Support**: Control multiple doors from a single Net2 server
- **Token Management**: Automatic JWT token refresh (30-min tokens)

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

Each door exposes the following channels:

| Channel | Type | Access | Description |
|---------|------|--------|-------------|
| `status` | Switch | RO | Door lock/unlock status (ON=Open, OFF=Closed) |
| `action` | Switch | RW | Control door (ON=Hold Open, OFF=Close) |
| `lastAccessUser` | String | RO | Last user who accessed the door |
| `lastAccessTime` | DateTime | RO | Timestamp of last door access |

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

### Endpoints
- **Authentication**: `POST /api/v1/authorization/tokens`
- **Door Control**: `POST /api/v1/commands/door/holdopen`, `POST /api/v1/commands/door/close`
- **Status**: `GET /api/v1/doors/status`
- **List Doors**: `GET /api/v1/doors`

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
- Verify refreshInterval is set appropriately
- Check bridge status is ONLINE
- Review OpenHAB logs for API errors

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
