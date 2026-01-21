# Traccar Binding - Beacon Name Update Fix
**Date:** January 21, 2026, 16:30 - 17:15
**Session:** Beacon name dynamic update issue

## Problem Identified
- Beacon names weren't updating dynamically in OpenHAB
- Beacon 3 renamed from "OXFORD_Bag" to "Stinger 22" on the physical device 10 hours ago
- Name stuck at old value in OpenHAB

## Root Cause
In `TraccarDeviceHandler.java` line 706-710:
```java
Object name = attributes.get(beaconPrefix + "Name");
if (name instanceof String nameValue) {
    String cleanName = nameValue.replaceAll("\\u0000", "").trim();
    updateState(channelPrefix + "-name", new StringType(cleanName));
}
```

**Issue:** Only updates when `tagXName` attribute present in webhook. No persistence or storage of last known name.

## Fix Applied
**File:** `/etc/openhab-addons/bundles/org.openhab.binding.traccar/src/main/java/org/openhab/binding/traccar/internal/TraccarDeviceHandler.java`

**Changes:**
1. Added `beaconNames` Map to store last known names (line ~62)
2. Added `initializeBeaconNamesFromProperties()` method to restore names on startup
3. Modified `updateBeaconData()` to:
   - Store new names in Thing properties when detected
   - Always update channel with last known name
   - Log when names change
   - Persist across restarts

**Build & Deploy:**
```bash
cd /etc/openhab-addons/bundles/org.openhab.binding.traccar
mvn clean install
sudo cp target/org.openhab.binding.traccar-5.2.0-SNAPSHOT.jar /usr/share/openhab/addons/
```

**Status:** ✅ Deployed at 16:42, auto-reloaded by OpenHAB (bundle 250)

## Backups Created
- `/etc/openhab/Traccar-Binding-backup-20260121-163526/`
- `/etc/openhab-addons/bundles/org.openhab.binding.traccar-backup-20260121-163603/`

## Current Beacon Status
**Device:** FMM920 (deviceId 10) "Springfield"

| Beacon | MAC | Name | Status |
|--------|-----|------|--------|
| beacon1 | 7cd9f413830b | MOSKO_Bag | ✅ Detected |
| beacon2 | 7cd9f414d0d7 | PANNIERS | ✅ Detected |
| beacon3 | 7cd9f4128704 | Stinger 22 | ❌ Not detected by tracker |

## Issue: Beacon 3 Not Detected
- Beacon 3 is powered on and advertising (verified via Eye app)
- FMM920 only detecting beacons 1 & 2
- **Likely cause:** FMM920 configuration issue
  - Check beacon whitelist in FMM920
  - Verify max beacon limit
  - Confirm beacon detection mode (All vs Configured)
  - Ensure MAC `7cd9f4128704` is in tracker config

## Testing Plan
**Test with Beacon 2:** Change name on beacon 2 to verify fix works before troubleshooting beacon 3 detection.

## Logs to Monitor
```bash
# OpenHAB logs
sudo tail -f /var/log/openhab/openhab.log | grep -i beacon

# Webhook monitor
tail -f /tmp/traccar_webhook_monitor.log | jq -r 'select(.data.position.attributes | keys[] | startswith("tag"))'

# Look for name changes
sudo grep "Beacon name changed" /var/log/openhab/openhab.log
```

## Next Steps
1. ✅ Reboot to check FMM920 configuration
2. Verify beacon 3 MAC in FMM920 whitelist/config
3. Test beacon 2 name change to verify fix
4. Once beacon 3 detected, name will update automatically

## Key Files
- Binding source: `/etc/openhab-addons/bundles/org.openhab.binding.traccar/`
- Thing config: `/etc/openhab/things/traccar.things`
- Installed JAR: `/usr/share/openhab/addons/org.openhab.binding.traccar-5.2.0-SNAPSHOT.jar`

---
**Status:** Fix deployed and active. Waiting for beacon 3 detection by FMM920.
