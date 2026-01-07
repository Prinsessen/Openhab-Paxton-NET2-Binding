# Paxton Net2 Access Control Binding

This binding integrates the Paxton Net2 Access Control system with openHAB. It communicates with the Net2 Local API over HTTPS and receives live events via the classic SignalR 2 transport.

## Features
- Door control (hold open / close)
- Real-time door status events via SignalR
- Last access user and timestamp per door
- Multi-door support under a single bridge
- OAuth2/JWT token handling with automatic refresh

## Configuration Overview
- Create a bridge (`net2server`) with hostname/IP, port (default 8443), username, password, clientId, TLS verification flag, and refresh interval.
- Add child door things with `doorId` and optional `name`.
- Channels per door: `status` (RO), `action` (RW), `lastAccessUser` (RO), `lastAccessTime` (RO).

## Maintainer
- Nanna Agesen (@Prinsessen) — Nanna@agesen.dk

## Build
```bash
mvn clean install -pl :org.openhab.binding.net2
```

## Notes
- This binding is not yet part of upstream openHAB add-ons. Use the standalone repo or this fork until upstreamed.
