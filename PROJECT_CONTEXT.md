# Net2 Binding Project Context

**Last Updated:** January 9, 2026  
**Developer:** Nanna Agesen (@Prinsessen)  
**Status:** Active Development - v5.2.0 Production Ready

## Quick Start Info

### Project Overview
Custom OpenHAB binding for **Paxton Net2 Access Control System** integration.
- Controls door locks/relays via Net2 Local API
- Real-time door status via SignalR WebSocket
- User management and access control
- Hybrid synchronization system (SignalR + API polling)

### Environment

**OpenHAB:**
- Version: **5.1.0** (running in production)
- Install: `/usr/share/openhab/`
- Logs: `/var/log/openhab/openhab.log`
- Addons: `/usr/share/openhab/addons/`

**Binding:**
- Version: **5.2.0-SNAPSHOT** (built for 5.2.0, runs on 5.1.0)
- Deployed JAR: `/usr/share/openhab/addons/org.openhab.binding.net2-5.2.0-SNAPSHOT.jar`

**Development:**
- Java: 21
- Maven: 3.9.9
- Build Tool: Maven (skip tests, skip spotless)

### File Locations

**Primary Development:**
```
/etc/openhab-addons/bundles/org.openhab.binding.net2/
├── pom.xml                          # Maven config (parent: 5.2.0-SNAPSHOT)
├── src/main/java/                   # Java source code
│   └── org/openhab/binding/net2/
│       ├── handler/
│       │   ├── Net2DoorHandler.java      # Door control & sync
│       │   ├── Net2ServerHandler.java    # Bridge, API polling
│       │   └── Net2SignalRClient.java    # WebSocket events
│       └── Net2BindingConstants.java
└── target/                          # Build output (not in git)
    └── org.openhab.binding.net2-5.2.0-SNAPSHOT.jar
```

**Git Repository (sync destination):**
```
/etc/openhab/net2-binding/
├── src/                             # Synced from openhab-addons
├── *.md                             # Documentation
├── pom.xml                          # Simplified POM
└── .git/                            # Git repo
```

**GitHub:**
- URL: https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding
- Branch: main
- Latest commits: Timer removal (28dbd60, a88861c)

**OpenHAB Config:**
```
/etc/openhab/
├── things/                          # Net2 thing definitions
├── items/                           # Net2 items (paxton.items)
├── rules/                           # Automation rules
└── sitemaps/                        # UI definitions (myhouse.sitemap)
```

## Current Implementation Status

### ✅ Completed Features

**Hybrid Synchronization (v5.2.0):**
- SignalR WebSocket for instant door open detection
- API polling (30s default) for reliable door close detection
- Door-specific event subscriptions
- Both `action` and `status` channels synchronized
- No auto-off timer (removed Jan 9, 2026)

**Channels:**
- `action` (Switch, RW) - Control & monitor door relay state
- `status` (Switch, RO) - Real-time status mirror
- `lastAccessUser` (String) - Last person who accessed door
- `lastAccessTime` (DateTime) - Timestamp of last access

**Bridge Channels:**
- `createUser` - Create Net2 users
- `deleteUser` - Remove users
- `listAccessLevels` - Query available access levels

**Authentication:**
- OAuth2 JWT with auto-refresh
- Configurable TLS verification
- Secure token management

### 🔧 Recent Changes (Jan 9, 2026)

**Timer Removal:**
- Removed 5-second auto-off timer
- Door status now reflects actual Net2 state
- Opens: Instant via SignalR (eventType 20/28/46)
- Closes: API polling detection (within refresh interval)
- Commit: 28dbd60, a88861c

**Why Timer Was Removed:**
- Old behavior: Door opens → ON, then timer forces OFF after 5s (even if still open!)
- New behavior: Door opens → ON (SignalR), stays ON until API confirms closed
- Reason: EventType 47 (door closed) is unreliable in Net2 API

## Technical Details

### Build & Deploy

**Build command:**
```bash
cd /etc/openhab-addons
mvn package -pl bundles/org.openhab.binding.net2 -am -DskipTests -Dspotless.check.skip=true
```

**Deploy:**
```bash
sudo cp bundles/org.openhab.binding.net2/target/org.openhab.binding.net2-5.2.0-SNAPSHOT.jar \
  /usr/share/openhab/addons/
```

**Auto-reload:** OpenHAB detects new JAR and reloads binding automatically

### Sync Git Repository

**After code changes:**
```bash
# Copy source code
cp -r /etc/openhab-addons/bundles/org.openhab.binding.net2/src /etc/openhab/net2-binding/

# Copy updated docs
cd /etc/openhab/net2-binding
cp CHANGELOG.md SYNCHRONIZATION.md VERSION_5.2.0_NOTES.md \
  /etc/openhab-addons/bundles/org.openhab.binding.net2/

# Commit and push
git add -A
git commit -m "Description"
git push origin main
```

### Key APIs & Protocols

**Net2 Local API:**
- Base URL: `https://<host>:8443/api/v1/`
- Authentication: OAuth2 JWT (Bearer token)
- Endpoints:
  - `/doors/status` - Get all door states (API polling)
  - `/doors/{id}/control` - Open/close door
  - `/users` - User management

**SignalR Classic (v2):**
- WebSocket endpoint: `/signalr`
- Hub: `LiveEvents` (only one implemented)
- Connection: SignalR Classic negotiation protocol
- Events: JSON with `Target` and `Arguments` fields

**EventTypes:**
| Code | Description | Reliability |
|------|-------------|-------------|
| 20 | Access granted (card reader) | ✅ Reliable |
| 28 | Door relay opened (timed) | ✅ Reliable |
| 46 | Door forced/held open | ✅ Reliable |
| 47 | Door closed/secured | ⚠️ Unreliable (why we need API polling) |

### Synchronization Flow

**Door Opens:**
1. User opens door (any method: card, OpenHAB, Net2 UI)
2. Net2 server sends SignalR event (eventType 20/28/46)
3. `Net2DoorHandler.applyEvent()` called
4. Both channels → ON immediately
5. OpenHAB UI updates instantly (< 1 second)

**Door Closes:**
1. Door closes (timeout, manual, or physical)
2. Net2 *might* send eventType 47 (unreliable)
3. **API polling** (every 30s) reads `doorRelayOpen` status
4. `Net2DoorHandler.updateFromApiResponse()` called
5. Detects `doorRelayOpen=false`
6. Both channels → OFF
7. OpenHAB UI syncs (within refresh interval)

### Important Classes

**Net2DoorHandler.java:**
- Handles individual door Thing
- `applyEvent()` - Process SignalR events
- `updateFromApiResponse()` - Process API polling results
- `subscribeToSignalREvents()` - Subscribe to door-specific events
- `handleCommand()` - Process OpenHAB commands (open/close door)

**Net2ServerHandler.java:**
- Handles Bridge Thing (Net2 server connection)
- `refreshDoorStatus()` - API polling job (scheduled every 30s)
- `onSignalRConnected()` - Callback when SignalR ready, subscribes all doors
- Manages SignalR client lifecycle

**Net2SignalRClient.java:**
- SignalR Classic WebSocket client
- `connect()` - Establish WebSocket connection
- `subscribeToDoorEvents(doorId)` - Subscribe to door-specific events
- `setOnConnectedCallback()` - Notify when connection ready

## Debugging

### Enable Debug Logging
```bash
# In OpenHAB console (openhab-cli console)
log:set DEBUG org.openhab.binding.net2
```

### Monitor Logs
```bash
# Watch all Net2 activity
tail -f /var/log/openhab/openhab.log | grep -i net2

# Watch synchronization
tail -f /var/log/openhab/openhab.log | grep -E "refreshDoorStatus|updateFromApiResponse|Door.*opened|Door.*closed"

# Check SignalR connection
grep "Connected to SignalR" /var/log/openhab/openhab.log
grep "Subscribed to door events" /var/log/openhab/openhab.log
```

### Key Log Messages

**SignalR:**
```
[INFO] Net2SignalRClient - Connected to SignalR
[INFO] Net2DoorHandler - Subscribed to door events for door ID 6612642
[INFO] Net2SignalRClient - SignalR message received: {...}
```

**Door Events:**
```
[INFO] Net2DoorHandler - Door 6612642 opened (eventType 20)
[INFO] Net2DoorHandler - Door 6612642 closed (eventType 47)
```

**API Polling:**
```
[DEBUG] Net2ServerHandler - refreshDoorStatus: Starting API poll
[DEBUG] Net2ServerHandler - refreshDoorStatus: Got API response: [...]
[DEBUG] Net2ServerHandler - refreshDoorStatus: Parsed array with 7 doors
[INFO] Net2DoorHandler - updateFromApiResponse: Door 6612642 doorRelayOpen=false -> OFF
```

## Configuration Example

**things/net2.things:**
```java
Bridge net2:net2server:myserver [
    hostname="192.168.1.100",
    port=8443,
    username="admin",
    password="password",
    refreshInterval=30,
    verifyCertificate=false
] {
    Thing door frontdoor "Front Door" [doorId=6612642]
    Thing door backdoor "Back Door" [doorId=6626578]
}
```

**items/paxton.items:**
```java
Switch FrontDoor_Action "Front Door" <door> {channel="net2:door:myserver:frontdoor:action"}
Switch FrontDoor_Status "Front Door Status" {channel="net2:door:myserver:frontdoor:status"}
String FrontDoor_LastUser {channel="net2:door:myserver:frontdoor:lastAccessUser"}
DateTime FrontDoor_LastTime {channel="net2:door:myserver:frontdoor:lastAccessTime"}
```

## Known Issues & Limitations

1. **EventType 47 Unreliable**
   - Net2 API inconsistently sends door close events
   - Solution: API polling provides fallback (30s max delay)

2. **SignalR Hubs**
   - Documentation mentions `doorEvents` and `doorStatusEvents`
   - Reality: Only `LiveEvents` hub is implemented by Net2

3. **Refresh Interval Trade-off**
   - Lower = faster close detection, more API load
   - 30s provides good balance
   - Minimum recommended: 5s

4. **Version Mismatch**
   - Built for 5.2.0-SNAPSHOT
   - Running on 5.1.0
   - Works fine (backward compatible), future-proof for 5.2.0 release

## System Info

**Server:**
- OS: Linux (Debian-based)
- CPU: Intel Xeon E5-2620 v4 @ 2.10GHz (1 core)
- RAM: 7.5 GB (OpenHAB uses ~1.5 GB at steady state)
- Disk: 119 GB (27 GB used)
- Uptime: Stable, production environment

**Network:**
- 7 doors monitored
- SignalR: 1 WebSocket per bridge
- API polling: 1 HTTP call per 30s
- Network impact: Minimal

## Documentation Files

All in `/etc/openhab/net2-binding/`:
- **README.md** - Overview, features, installation
- **CHANGELOG.md** - Version history
- **SYNCHRONIZATION.md** - Deep dive into sync architecture (14KB)
- **VERSION_5.2.0_NOTES.md** - Release notes for v5.2.0
- **EXAMPLES.md** - Usage examples
- **DEVELOPMENT.md** - Developer guide
- **QUICKSTART.md** - Quick setup guide
- **PROJECT_CONTEXT.md** - This file!

## Contact

**Developer:**
- Name: Nanna Agesen
- Email: nanna@agesen.dk
- GitHub: @Prinsessen
- Location: Denmark

**Repository:**
- https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding

## Quick Reference Commands

**Check OpenHAB version:**
```bash
openhab-cli info | grep Version
```

**Rebuild binding:**
```bash
cd /etc/openhab-addons
mvn package -pl bundles/org.openhab.binding.net2 -am -DskipTests -Dspotless.check.skip=true
sudo cp bundles/org.openhab.binding.net2/target/org.openhab.binding.net2-5.2.0-SNAPSHOT.jar /usr/share/openhab/addons/
```

**Check binding status:**
```bash
openhab-cli console -p habopen "bundle:list | grep net2"
```

**View recent logs:**
```bash
tail -100 /var/log/openhab/openhab.log | grep -i net2
```

**Check system resources:**
```bash
uptime
free -h
ps aux | grep openhab
```

**Sync to git:**
```bash
cd /etc/openhab/net2-binding
git status
git add -A
git commit -m "Your message"
git push origin main
```

---

## Summary for AI Assistant

If you're reading this after a disconnection:

1. **We're building:** Custom OpenHAB binding for Paxton Net2 access control
2. **Version:** 5.2.0-SNAPSHOT, running on OpenHAB 5.1.0
3. **Recent work:** Removed 5-second auto-off timer, implemented hybrid sync
4. **Build location:** `/etc/openhab-addons/bundles/org.openhab.binding.net2/`
5. **Git repo:** `/etc/openhab/net2-binding/` (sync after changes)
6. **Status:** Production-ready, 7 doors in active use
7. **Key feature:** SignalR (instant open) + API polling (reliable close detection)
8. **Build command:** `mvn package -pl bundles/org.openhab.binding.net2 -am -DskipTests -Dspotless.check.skip=true`
9. **Deploy:** Copy JAR to `/usr/share/openhab/addons/`
10. **Everything works:** Synchronization perfect, logs showing proper operation

**Last activity:** Removed 5-second timer, updated docs, pushed to GitHub (commits 28dbd60, a88861c)
