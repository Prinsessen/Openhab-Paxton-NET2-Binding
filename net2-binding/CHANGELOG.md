# Changelog

All notable changes to the Paxton Net2 Binding are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.2.0] - 2026-01-09

### Added
- **Hybrid Synchronization System**
  - SignalR real-time event subscription for each door
  - Door-specific LiveEvents subscriptions for instant notifications
  - API polling fallback for guaranteed state accuracy (every 30s by default)
  - Both `action` and `status` channels now sync with Net2 server state
  - Synchronization works regardless of control method (OpenHAB, Net2 UI, physical access)
- **Enhanced Event Handling**
  - EventType-based state tracking (20, 28, 46 for door open; 47 for door close)
  - Proper handling of `doorRelayOpen` field from API status endpoint
  - Door state updates from both SignalR events and API polling
- **Improved SignalR Integration**
  - Connection callback mechanism to notify door handlers when SignalR ready
  - Automatic door-specific subscriptions after SignalR connection established
  - Fixed race condition in SignalR client initialization
  - Subscriptions logged for debugging: "Subscribed to door events for door ID"
- **Debug Logging**
  - Comprehensive logging for synchronization events
  - `refreshDoorStatus` logs show API polling activity
  - `updateFromApiResponse` logs show door state updates from API
  - SignalR event logs show real-time door events with eventType

### Changed
- `action` channel now maintains persistent state until door physically closes (via API polling detection)
- `status` channel now mirrors actual door relay state from Net2 server
- Both channels update from API polling to ensure accurate synchronization
- Door handlers notified via callback when SignalR connection ready (not during connect)
- **Removed 5-second auto-off timer** - API polling now provides authoritative door close detection

### Fixed
- Door state not synchronizing when closed physically or via Net2 UI
- SignalR client race condition where callback fired before client was assigned
- Incorrect API field parsing (`state` → `status.doorRelayOpen`)
- EventType 47 (door closed) unreliability addressed by API polling fallback
- Missing state updates for `action` channel during API refresh
- False door status OFF after 5 seconds while door remained open (timer removed)

### Technical Details
- API response structure: `{"id": doorId, "status": {"doorRelayOpen": boolean}}`
- SignalR Classic mode protocol with LiveEvents hub
- Net2 API does not implement documented `doorEvents` or `doorStatusEvents` hubs
- EventType 47 inconsistently sent, requiring API polling backup
- Default refresh interval: 30 seconds (configurable)
- **Door closes detected by API polling only** (within refresh interval, no timer)

## [5.1.0] - 2026-01-07

### Added
- Initial release for openHAB 5.1
- Timed door control channel (`controlTimed`) for advanced server-side timed open
- **Bridge Channels (User Management)**
  - `createUser` channel: Create users with access level assignment
  - `deleteUser` channel: Remove users by ID
  - `listAccessLevels` channel: Enumerate available access levels
- **Door Control**
  - `status` channel: Monitor door lock/unlock status
  - `action` channel: Control door (hold open/close)
  - `lastAccessUser` channel: Track last user who accessed door
  - `lastAccessTime` channel: Timestamp of last access
- **Authentication & Security**
  - OAuth2 JWT token handling with automatic refresh
  - Configurable TLS certificate verification
  - Secure credential storage in openHAB
- **Real-time Updates**
  - SignalR 2 event support for live door status
  - Configurable polling interval (default 30s)
  - Automatic door discovery
- **API Integration**
  - Full support for Net2 Local API v1
  - User management (create, delete)
  - Access level assignment to doors
  - Door permission set management
- **Documentation**
  - Comprehensive README with examples
  - EXAMPLES.md with detailed usage for timed and default door control
  - Contributing guidelines
  - Troubleshooting section
  - Configuration examples for text and UI
## Author

**Nanna Agesen** (@Prinsessen)
- Email: nanna@agesen.dk
- GitHub: https://github.com/Prinsessen

### Fixed
- Token refresh handling to prevent authentication timeouts
- Proper resource cleanup on binding shutdown
- Concurrent access token management

### Changed
- Bridge configuration requires explicit API credentials
- Improved error logging for API failures
- Enhanced SignalR connection resilience

### Security
- Token expiry checking with 5-minute buffer
- TLS verification enabled by default
- Credentials never persisted to disk
- Secure memory handling for tokens

## [Unreleased]

### Planned Features
- Event-driven door status updates without polling
- Integration with openHAB's native permissions system
- Mobile app support
- SMS/email notifications for access events
- Advanced scheduling for temporary access

### Under Investigation
- Integration with Home Assistant
- Support for additional access control systems
- Native openHAB UI dashboard templates

---

## Versioning

This binding follows semantic versioning:
- **MAJOR** (5.x.0): Compatibility with openHAB major versions
- **MINOR** (5.1.x): New features, backward compatible
- **PATCH** (5.1.0): Bug fixes, backward compatible

## Release Support

| Version | openHAB | Java | Status | Support Until |
|---------|---------|------|--------|----------------|
| 5.1.0   | 5.1+    | 21+  | Active | 2027-01-07   |

## Contributors

- **Nanna Agesen** (@Prinsessen) - Lead Developer, Maintainer
  - Email: Nanna@agesen.dk
  - GitHub: https://github.com/Prinsessen

## License

All changes are licensed under the Eclipse Public License 2.0 (EPL-2.0).

## Notes

### Breaking Changes
None in current version.

### Migration Guide
First-time users: See README.md for complete setup instructions.

### Known Limitations
- SignalR events may be delayed on high-latency networks
- User creation requires valid access level in Net2 system
- Maximum 100 doors per Net2 instance (API limitation)

### Compatibility Matrix

| Feature | Net2 Version | openHAB Version |
|---------|--------------|-----------------|
| Basic Door Control | 6.6 SR5+ | 5.0+ |
| User Management | 6.6 SR5+ | 5.0+ |
| SignalR Events | 6.6 SR5+ | 5.0+ |
| Auto-Discovery | 6.6 SR5+ | 5.0+ |

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Requesting features
- Submitting code changes
- Code style requirements
- Testing procedures

## Contact & Support

- **Issues**: https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding/issues
- **Email**: Nanna@agesen.dk
- **Community**: https://community.openhab.org/
