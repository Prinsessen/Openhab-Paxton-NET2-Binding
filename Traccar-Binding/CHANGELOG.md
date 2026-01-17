# Changelog

All notable changes to the Traccar binding will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-17

### Added
- Initial release of Traccar binding for openHAB
- Traccar server bridge thing for connecting to Traccar GPS tracking servers
- Device thing for individual GPS tracked vehicles/devices
- Real-time position tracking with GPS coordinates, speed, and direction
- Comprehensive position channels:
  - `position` - GPS coordinates (latitude, longitude, altitude)
  - `speed` - Configurable speed units (km/h, mph, knots)
  - `course` - Direction/heading in degrees
  - `accuracy` - GPS accuracy in meters
  - `address` - Street address from reverse geocoding
  - `lastUpdate` - Timestamp of last update
- Device status monitoring:
  - `status` - Online/offline/unknown status
  - `batteryLevel` - Battery percentage
  - `motion` - Movement detection
  - `odometer` - Total distance traveled
- Geofencing support with webhooks:
  - `geofenceEvent` - Entry/exit events
  - `geofenceId` - Numeric geofence identifier
  - `geofenceName` - Human-readable geofence name
- Automatic device discovery from Traccar server
- Dual update mechanism:
  - Configurable polling interval (minimum 10 seconds)
  - Webhook support for instant geofence notifications
- Speed unit conversion from Traccar's native knots to km/h, mph, or knots
- Comprehensive documentation with examples
- Support for multiple Traccar servers simultaneously

### Features
- HTTP/HTTPS support for Traccar server connections
- Secure credential handling
- Configurable webhook port (1024-65535)
- Efficient API usage with hybrid polling/webhook approach
- Full support for Traccar 5.x and 6.x
- Compatible with 200+ GPS protocols and 2000+ device models

### Technical Details
- Built for openHAB 5.x
- Uses Jetty for webhook server
- OSGi bundle architecture
- Implements AbstractThingHandlerDiscoveryService for automatic discovery
- RESTful API integration with Traccar

### Author
- Nanna Agesen (Nanna@agesen.dk / @Prinsessen)

## [Unreleased]

### Planned Features
- Support for Traccar commands (send commands to devices)
- Driver behavior analysis channels
- Maintenance tracking and alerts
- Fuel level monitoring (for supported devices)
- Enhanced filtering options for position updates
- Configurable geofence event retention
