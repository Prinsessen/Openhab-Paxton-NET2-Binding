# Traccar Binding - Release Package

Version 1.0.0 - January 17, 2026

## Author

**Nanna Agesen**  
Email: Nanna@agesen.dk  
GitHub: [@Prinsessen](https://github.com/Prinsessen)

## Package Contents

This release-ready package includes:

### Documentation
- **README.md** - Complete user documentation with setup instructions
- **CHANGELOG.md** - Version history and release notes
- **CONTRIBUTING.md** - Developer contribution guidelines
- **EXAMPLES.md** - Comprehensive configuration examples
- **RELEASE_NOTES.md** - This file

### Source Code
- **src/main/java/** - Java source files
  - TraccarBindingConstants.java - Channel and constant definitions
  - TraccarHandlerFactory.java - Thing handler factory
  - TraccarServerHandler.java - Bridge handler (API client, polling, webhooks)
  - TraccarDeviceHandler.java - Device handler (channel updates)
  - TraccarDiscoveryService.java - Auto-discovery service
  - TraccarApiClient.java - Traccar REST API wrapper
  - TraccarWebhookServer.java - Jetty webhook server
  - Configuration classes

- **src/main/resources/OH-INF/** - Thing definitions and internationalization
  - thing/thing-types.xml - Thing and channel type definitions

### Build Files
- **pom.xml** - Maven build configuration
- **NOTICE** - Copyright notices
- **target/** - Compiled JAR files (if built)

## Features Summary

### Position Tracking
- GPS coordinates with altitude
- Speed (km/h, mph, or knots)
- Direction/course
- Accuracy
- Address (reverse geocoding)
- Last update timestamp

### Device Monitoring
- Battery level
- Motion detection
- Odometer
- Online/offline status

### Geofencing
- Entry/exit events via webhooks
- Geofence ID and name tracking
- Instant notifications
- Automation support (garage doors, lights, etc.)

### Update Mechanisms
- Configurable polling (minimum 10 seconds)
- Webhook support for instant events
- Hybrid approach for efficiency

## Installation

### From JAR File

1. Copy the binding JAR to openHAB addons folder:
   ```bash
   cp target/org.openhab.binding.traccar-*.jar /usr/share/openhab/addons/
   ```

2. Wait for openHAB to load the binding (check logs)

3. Configure via UI or text files (see README.md)

### From Source

Build from source:
```bash
cd org.openhab.binding.traccar
mvn clean package -DskipTests
```

Install:
```bash
cp target/org.openhab.binding.traccar-5.2.0-SNAPSHOT.jar /usr/share/openhab/addons/
```

## Quick Start

1. **Add Traccar Server Bridge**
   ```openhab
   Bridge traccar:server:myserver [
       url="https://demo.traccar.org",
       username="your@email.com",
       password="yourpassword"
   ]
   ```

2. **Auto-discover devices** from Inbox

3. **Configure webhooks** in Traccar for instant geofence events:
   - URL: `http://YOUR_OPENHAB_IP:8090/webhook`
   - Events: geofenceEnter, geofenceExit

4. **Create automation rules** (see EXAMPLES.md)

## Requirements

- openHAB 5.x or later
- Java 21
- Traccar 5.x or 6.x server (self-hosted or cloud)
- Network connectivity between openHAB and Traccar server
- For webhooks: Traccar must be able to reach openHAB

## Support

For issues, questions, or contributions:

- **Email**: Nanna@agesen.dk
- **GitHub**: [@Prinsessen](https://github.com/Prinsessen)

Please include:
- openHAB version
- Traccar version
- Device/tracker model
- Relevant log output
- Configuration details (with sensitive data removed)

## License

This binding is licensed under the Eclipse Public License 2.0 (EPL-2.0).

See: https://www.eclipse.org/legal/epl-2.0/

## Credits

- Built for the openHAB community
- Integrates with Traccar GPS tracking system
- Developed by Nanna Agesen

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

**Release Date**: January 17, 2026  
**Version**: 1.0.0  
**Status**: Production Ready
