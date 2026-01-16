
# Net2 Binding Configuration Examples

This document provides complete working examples for configuring the Net2 binding with items, sitemaps, rules, and user management.

## Complete Working Example

### Items Configuration

**File: items/net2.items**

```openhab
// Door 1 - Front Door
Switch Net2_Door1_Action "Door 1 Action" { channel="net2:door:server:door1:action" }
Switch Net2_Door1_Status "Door 1 Status" { channel="net2:door:server:door1:status" }
Number Net2_Door1_ControlTimed "Door 1 Timed Control" { channel="net2:door:server:door1:controlTimed" }
String Net2_Door1_LastUser "Door 1 Last User" { channel="net2:door:server:door1:lastAccessUser" }
DateTime Net2_Door1_LastTime "Door 1 Last Time" { channel="net2:door:server:door1:lastAccessTime" }
String Net2_Door1_EntryLog "Door 1 Entry Log" { channel="net2:door:server:door1:entryLog" }
String Net2_Door1_AccessDenied "Door 1 Access Denied" { channel="net2:door:server:door1:accessDenied" }

// Door 2 - Side Door
String Net2_Door2_AccessDenied "Door 2 Access Denied" { channel="net2:door:server:door2:accessDenied" }

// Door 3 - Garage Door
String Net2_Door3_AccessDenied "Door 3 Access Denied" { channel="net2:door:server:door3:accessDenied" }

// Bridge User Management Channels
String Net2_CreateUser "Create User" { channel="net2:net2server:server:createUser" }
String Net2_DeleteUser "Delete User" { channel="net2:net2server:server:deleteUser" }
String Net2_ListAccessLevels "List Access Levels" { channel="net2:net2server:server:listAccessLevels" }
String Net2_ListUsers "List Users" { channel="net2:net2server:server:listUsers" }
```

### Sitemap Configuration

**File: sitemaps/myhouse.sitemap**

```openhab
Frame label="Door 1 Controls" {
    Text item=Net2_Door1_Status label="Fordør Status" icon="door"
    Switch item=Net2_Door1_Action label="Fordør Action" icon="lock-key"
    Switch item=Net2_Door1_ControlTimed label="Fordør Timed Door" mappings=[1="Open"] icon="lock-key"
    Text item=Net2_Door1_EntryLog label="Last Entry [JS(entrylog.js):%s]" icon="log"
}
```

**Key Points:**
- `Status` item shows **physical door relay state** (read-only, updates via SignalR instantly)
- `Action` item is for **manual control** (ON=Hold Open, OFF=Close)
- `ControlTimed` with mapping `[1="Open"]` sends value `1` = 1 second open time

### Synchronization Rules

**File: rules/net2_sync.rules**

These rules keep the Action buttons synchronized with the physical door status:

```openhab
rule "Net2 Door 1 Status to Action Sync"
when
    Item Net2_Door1_Status changed
then
    logInfo("Net2Sync", "Door 1 Status changed to: " + Net2_Door1_Status.state)
    Net2_Door1_Action.postUpdate(Net2_Door1_Status.state)
end

rule "Net2 Door 2 Status to Action Sync"
when
    Item Net2_Door2_Status changed
then
    logInfo("Net2Sync", "Door 2 Status changed to: " + Net2_Door2_Status.state)
    Net2_Door2_Action.postUpdate(Net2_Door2_Status.state)
end

rule "Net2 Door 3 Status to Action Sync"
when
    Item Net2_Door3_Status changed
then
    logInfo("Net2Sync", "Door 3 Status changed to: " + Net2_Door3_Status.state)
    Net2_Door3_Action.postUpdate(Net2_Door3_Status.state)
end

rule "Net2 Door 4 Status to Action Sync"
when
    Item Net2_Door4_Status changed
then
    logInfo("Net2Sync", "Door 4 Status changed to: " + Net2_Door4_Status.state)
    Net2_Door4_Action.postUpdate(Net2_Door4_Status.state)
end
```

**Why These Rules Are Needed:**
- The `Status` channel receives instant updates from SignalR (doorRelayOpen field)
- The `Action` channel is used for sending commands
- These rules sync the Action button display to match the physical door state
- Without these rules, the Action button won't reflect remote/card-based door operations

## User Management Examples

### List All Users

Query the Net2 system for all users and log the complete JSON payload:

**From Rules:**
```openhab
rule "Query All Users"
when
    // Trigger condition (e.g., time-based, button press, etc.)
then
    sendCommand(Net2_ListUsers, ON)
    // Results logged to /var/log/openhab/openhab.log
    // Look for: "Users JSON payload: [...]"
end
```

**From REST API:**
```bash
curl -X POST "http://localhost:8080/rest/items/Net2_ListUsers" \
  -H "Content-Type: text/plain" \
  -d "REFRESH"
```

**View Results:**
```bash
grep "Users JSON" /var/log/openhab/openhab.log | tail -1
```

**JSON Output Example:**
```json
[
  {
    "Id": 1,
    "FirstName": "John",
    "LastName": "Doe",
    "ExpiryDate": "2027-01-10T12:46:20.723523+01:00",
    "ActivateDate": "2026-01-11T12:46:20.723523+01:00",
    "PIN": "1234",
    "Telephone": "01273 100200",
    "Extension": "200",
    "AccessLevelId": 3,
    "AccessLevelName": "Staff",
    "CustomFields": {...},
    "IsAlarmUser": false,
    "HasImage": true
  },
  ...
]
```

### List Access Levels

Query available access levels in the system:

**From Rules:**
```openhab
rule "Query Access Levels"
when
    // Trigger condition
then
    sendCommand(Net2_ListAccessLevels, ON)
    // Results logged as: "Access levels: [1:Public] [2:Staff] [3:Admin]"
end
```

**View Results:**
```bash
grep "Access levels" /var/log/openhab/openhab.log | tail -1
```

### Create User

Create a new user with specified access level and PIN:

**From Rules:**
```openhab
rule "Create New User"
when
    // Trigger condition
then
    // Format: firstName,lastName,accessLevel,pin
    sendCommand(Net2_CreateUser, "Michael,Smith,3,5678")
    logInfo("Net2", "User creation command sent")
end
```

**Access Level Options:**
- Can be numeric ID (e.g., `3`) or name (e.g., `Staff`)
- Query available levels first using `listAccessLevels`

### Delete User

Remove a user by their ID:

**From Rules:**
```openhab
rule "Delete User"
when
    // Trigger condition
then
    sendCommand(Net2_DeleteUser, "79")  // User ID
    logInfo("Net2", "User deletion command sent for ID 79")
end
```

**Get User IDs:**
Use `listUsers` channel to see all user IDs, then delete by ID number.

## Channel Details

## Default Door Control (Hold Open/Close)

The standard `action` channel allows you to hold a door open or close it immediately. Example item and sitemap usage:

**Items:**
```openhab
Switch Net2_Door1_Action "Door 1 Action" { channel="net2:door:server:door1:action" }
```

**Sitemap:**
```openhab
Switch item=Net2_Door1_Action label="Door 1 (Hold Open/Close)"
```

- Sending `ON` will hold the door open (until manually closed or timeout in Net2 config).
- Sending `OFF` will close/lock the door.

## Advanced Timed Door Control (controlTimed Channel)

The new `controlTimed` channel allows you to trigger a door open for a specific time (server-side timing) and optionally customize the payload (e.g., LED flash).

**Items:**
```openhab
Number Net2_Door1_ControlTimed "Door 1 Timed Open" { channel="net2:door:server:door1:controlTimed" }
```

**Sitemap:**
```openhab
Switch item=Net2_Door1_ControlTimed label="Door 1 Timed Open (1s)" mappings=[1="Open"]
```

- Sending `1` will trigger a timed open for **1 second** (1000ms).
- Sending `5` will open for 5 seconds, `10` for 10 seconds, etc.
- You can use rules to send custom values for different open times:

```openhab
rule "Open Door 1 for 10 seconds"
when
    Item Some_Trigger received command ON
then
    Net2_Door1_ControlTimed.sendCommand(10) // Opens for 10 seconds
end
```

### Custom Payload (Advanced)

The handler automatically converts your command (in seconds) to the correct JSON payload for the API:

```json
{
  "DoorId": 6612642,
  "RelayFunction": {
    "RelayId": "Relay1",
    "RelayAction": "TimedOpen",
    "RelayOpenTime": 1000 // milliseconds (command value × 1000)
  },
  "LedFlash": 3
}
```

- The value you send (e.g., `1`) is interpreted as **seconds** and automatically converted to milliseconds in the payload.
- Default: 1 second if no value specified or invalid value provided.
- LED flash count is fixed at 3 (can be customized in handler code if needed).

## Summary Table

| Channel         | Item Type | Usage Example                | Description                                 |
|----------------|-----------|------------------------------|---------------------------------------------|
| action         | Switch    | ON/OFF                       | Hold open/close door                        |
| controlTimed   | Number    | 1, 5, 10 (seconds)           | Timed open with server-side timing          |

## Author

- Nanna Agesen (@Prinsessen)
- Email: nanna@agesen.dk
- GitHub: https://github.com/Prinsessen

### Rule 1: Automatic Door Lock on Schedule

**File: rules/net2_schedule_lock.rules**

```java
rule "Auto-lock front door at night"
when
    Time cron "0 22 * * *"  // 10 PM daily
then
    Front_Door_Lock.sendCommand(OFF)
    logInfo("Door", "Front door locked automatically at night")
end
```

### Rule 2: Log Access Events

**File: rules/net2_access_log.rules**

```java
rule "Log door access"
when
    Item Front_Door_LastUser changed
then
    logInfo("Access", "Door accessed by: " + Front_Door_LastUser.state)
    logInfo("Time", "Access time: " + Front_Door_LastTime.state)
end
```

### Rule 3: Alert on Unauthorized Access Attempts

**File: rules/net2_security_alert.rules**

```java
rule "Alert on access attempt"
when
    Item Front_Door_Status changed
then
    if (Front_Door_Status.state == ON) {
        logWarn("Security", "Front door opened/unlocked at " + now)
        // Send notification
        sendNotification("security@example.com", "Door accessed: " + Front_Door_LastUser.state)
    }
end
```

### Rule 4: Integration with Alarm System

**File: rules/net2_alarm_integration.rules**

```java
rule "Disarm alarm when authorized door access"
when
    Item Front_Door_LastUser changed
then
    val user = Front_Door_LastUser.state.toString()
    if (user == "John Doe" || user == "Jane Smith") {
        Alarm_System.sendCommand(DISARM)
        logInfo("Alarm", "Alarm disarmed after authorized access by " + user)
    }
end
```

### Rule 5: Track Door Activity

**File: rules/net2_activity_tracker.rules**

```java
rule "Track door activity"
when
    Item Front_Door_LastTime changed
then
    // Update door activity log
    DoorActivity_LastAccess.postUpdate(Front_Door_LastTime.state)
    DoorActivity_LastUser.postUpdate(Front_Door_LastUser.state)
    
    logInfo("Activity", "Door activity updated at " + now)
end
```

### Rule 6: Emergency Door Unlock

**File: rules/net2_emergency.rules**

```java
rule "Emergency unlock all doors"
when
    Item Emergency_Button received command ON
then
    Front_Door_Lock.sendCommand(ON)
    Back_Door_Lock.sendCommand(ON)
    Garage_Door_Lock.sendCommand(ON)
    
    logWarn("Emergency", "All doors unlocked at " + now)
    sendNotification("admin@example.com", "Emergency unlock triggered")
end
```

## Example sitemap Integration

**File: sitemaps/net2_doors.sitemap**

```
sitemap net2_doors label="Net2 Door Control" {
    Frame label="Front Door" {
        Switch item=Front_Door label="Front Door" icon="lock" mappings=[OFF="Lock", ON="Unlock"]
        Text item=Front_Door_Status label="Status [%s]" icon="door"
        Text item=Front_Door_LastUser label="Last Access: [%s]"
        Text item=Front_Door_LastTime label="Last Time: [%1$td.%1$tm.%1$tY %1$tH:%1$tM:%1$tS]"
        Text item=Front_Door_EntryLog label="Entry [JS(entrylog.js):%s]" icon="log"
    }

    Frame label="Back Door" {
        Switch item=Back_Door label="Back Door" icon="lock"
        Text item=Back_Door_Status label="Status [%s]"
        Text item=Back_Door_LastUser label="Last Access: [%s]"
    }

    Frame label="Garage Door" {
        Switch item=Garage_Door label="Garage" icon="lock"
        Text item=Garage_Door_Status label="Status [%s]"
    }
}

## REST Quick Test

```bash
# Create user
curl -X POST "http://localhost:8080/rest/items/Net2_CreateUser" \
    -H "Content-Type: text/plain" \
    --data "Michael,Agesen,3,7654"

# List access levels
curl -X POST "http://localhost:8080/rest/items/Net2_ListAccessLevels" \
    -H "Content-Type: text/plain" \
    --data "REFRESH"

# Delete user (replace 79 with the created ID)
curl -X POST "http://localhost:8080/rest/items/Net2_DeleteUser" \
    -H "Content-Type: text/plain" \
    --data "79"
```
```

## Items Configuration with Persistence

**File: items/net2_doors.items**

```
Group gNet2Doors "Net2 Doors" <lock>

Group gFrontDoor "Front Door" <lock> (gNet2Doors)
Switch Front_Door "Front Door" <lock> (gFrontDoor) { channel="net2:door:myserver:fordoor:action" }
Switch Front_Door_Status "Status" <door> (gFrontDoor) { channel="net2:door:myserver:fordoor:status" }
String Front_Door_LastUser "Last User" (gFrontDoor) { channel="net2:door:myserver:fordoor:lastAccessUser" }
DateTime Front_Door_LastTime "Last Access" (gFrontDoor) { channel="net2:door:myserver:fordoor:lastAccessTime" }

Group gBackDoor "Back Door" <lock> (gNet2Doors)
Switch Back_Door "Back Door" <lock> (gBackDoor) { channel="net2:door:myserver:backdoor:action" }
Switch Back_Door_Status "Status" <door> (gBackDoor) { channel="net2:door:myserver:backdoor:status" }

Group gGarageDoor "Garage" <lock> (gNet2Doors)
Switch Garage_Door "Garage Door" <lock> (gGarageDoor) { channel="net2:door:myserver:garage:action" }
Switch Garage_Door_Status "Status" <door> (gGarageDoor) { channel="net2:door:myserver:garage:status" }

// Additional items for tracking
Group gDoorActivity "Door Activity"
DateTime DoorActivity_LastAccess "Last Access Time" (gDoorActivity)
String DoorActivity_LastUser "Last User" (gDoorActivity)

// Emergency control
Switch Emergency_Button "🚨 Emergency Unlock" <alarm> (gNet2Doors)
```

## Persistence Configuration

**File: persistence/net2_doors.persist**

```
Strategies {
    everyMinute : "0 * * * * ?"
    everyHour   : "0 0 * * * ?"
    everyDay    : "0 0 0 * * ?"
    default     = everyDay
}

Items {
    // Track all door access
    gDoorActivity* : strategy=everyMinute, everyDay
    
    // Store door status changes
    Front_Door_Status,
    Back_Door_Status,
    Garage_Door_Status
    : strategy=everyChange, everyDay
    
    // Track unlock events
    Front_Door,
    Back_Door,
    Garage_Door
    : strategy=everyChange
}
```

## Grafana Dashboard Configuration

Example queries for Grafana using RRD4j persistence:

```json
{
  "panels": [
    {
      "title": "Door Access Count (Daily)",
      "targets": [
        {
          "query": "SELECT COUNT(*) FROM items WHERE itemname LIKE '%LastUser%' GROUP BY day"
        }
      ]
    },
    {
      "title": "Door Status Timeline",
      "targets": [
        {
          "query": "SELECT time, state FROM Front_Door_Status ORDER BY time DESC LIMIT 1000"
        }
      ]
    }
  ]
}
```

## API Integration Example (Python)

```python
#!/usr/bin/env python3
import requests

# Control door via OpenHAB
OPENHAB_API = "https://openhab.example.com/rest/items"

def unlock_door(door_name):
    """Unlock a door via OpenHAB binding"""
    response = requests.post(
        f"{OPENHAB_API}/{door_name}/command",
        data="ON",
        headers={"Content-Type": "text/plain"}
    )
    return response.status_code == 200

def lock_door(door_name):
    """Lock a door via OpenHAB binding"""
    response = requests.post(
        f"{OPENHAB_API}/{door_name}/command",
        data="OFF",
        headers={"Content-Type": "text/plain"}
    )
    return response.status_code == 200

# Usage
if __name__ == "__main__":
    unlock_door("Front_Door")
    lock_door("Front_Door")
```

## Build & Deploy Instructions

```bash
# Build the binding
cd /etc/openhab/net2-binding
mvn clean install

# Copy JAR to OpenHAB addons
cp target/org.openhab.binding.net2-*.jar /opt/openhab/addons/

# Restart OpenHAB
systemctl restart openhab

# Check binding is loaded
tail -f /var/log/openhab/openhab.log | grep net2
```

## Entry Logging Examples

### Complete Entry Logging Setup

**Items Configuration:**

```openhab
// Entry Log Items (JSON format for Grafana)
String Net2_Door1_EntryLog "Entry Log [%s]" { channel="net2:door:server:door1:entryLog" }
String Net2_Door2_EntryLog "Entry Log [%s]" { channel="net2:door:server:door2:entryLog" }
String Net2_Door3_EntryLog "Entry Log [%s]" { channel="net2:door:server:door3:entryLog" }
String Net2_Door4_EntryLog "Entry Log [%s]" { channel="net2:door:server:door4:entryLog" }
String Net2_Door5_EntryLog "Entry Log [%s]" { channel="net2:door:server:door5:entryLog" }
```

**Transform for UI Display:**

File: `/etc/openhab/transform/entrylog.js`

```javascript
(function(data) {
    if (!data || data === "NULL") {
        return "No entries yet";
    }
    try {
        var entry = JSON.parse(data);
        var time = entry.timestamp.substring(11, 19);
        return entry.firstName + " " + entry.lastName + " entered " + entry.doorName + " at " + time;
    } catch (e) {
        return "Error parsing entry log";
    }
})(input)
```

**Sitemap Display:**

```openhab
Frame label="Fordør Kirkegade" {
    Text item=Net2_Door1_EntryLog label="Last Entry [JS(entrylog.js):%s]" icon="log"
}
```

**Persistence Configuration:**

```openhab
Items {
    Net2_Door1_EntryLog : strategy = everyChange
}
```

### Entry Log Output Format

**JSON Format (stored in item):**
```json
{
  "firstName": "Nanna",
  "lastName": "Agesen",
  "doorName": "Front Door",
  "timestamp": "2026-01-10T18:48:34",
  "doorId": 6612642
}
```

**UI Display (via transform):**
```
Last Entry: Nanna Agesen entered Front Door at 18:48:34
```

### Testing Entry Logging

**Monitor entry logs:**
```bash
tail -f /var/log/openhab/openhab.log | grep "Entry log"
```

**Check item value:**
```bash
curl -s http://localhost:8080/rest/items/Net2_Door1_EntryLog | python3 -m json.tool
```

### Grafana Integration

See complete Grafana setup guide below in the **Entry Log Dashboard** section.

---

## Entry Log Dashboard with InfluxDB and Grafana

This example shows how to create a comprehensive entry log dashboard displaying door access events from all doors in a clean, sorted table.

### Overview

The Net2 binding provides real-time entry logs via the `entryLog` channel. Each entry contains JSON data with:
- `firstName` - User's first name
- `lastName` - User's last name  
- `doorName` - Name of the door accessed
- `timestamp` - Time of entry (ISO 8601 format)
- `doorId` - Unique door identifier

This guide shows how to persist these logs to InfluxDB and visualize them in Grafana.

### Step 1: Items Configuration

**File: items/net2.items**

```openhab
// Door 1 - Entry logging items
String Net2_Door1_EntryLog "Entry Log [%s]" { channel="net2:door:server:door1:entryLog" }
Number Net2_Door1_EntryCount "Entry Count [%d]"

// Door 2 - Entry logging items
String Net2_Door2_EntryLog "Entry Log [%s]" { channel="net2:door:server:door2:entryLog" }
Number Net2_Door2_EntryCount "Entry Count [%d]"

// Door 3 - Entry logging items
String Net2_Door3_EntryLog "Entry Log [%s]" { channel="net2:door:server:door3:entryLog" }
Number Net2_Door3_EntryCount "Entry Count [%d]"

// Door 4 - Entry logging items
String Net2_Door4_EntryLog "Entry Log [%s]" { channel="net2:door:server:door4:entryLog" }
Number Net2_Door4_EntryCount "Entry Count [%d]"

// Door 5 - Entry logging items
String Net2_Door5_EntryLog "Entry Log [%s]" { channel="net2:door:server:door5:entryLog" }
Number Net2_Door5_EntryCount "Entry Count [%d]"
```

**What these items do:**
- `EntryLog` - Receives JSON entry data from the binding (persisted to InfluxDB)
- `EntryCount` - Auto-incrementing counter providing unique ID for each entry (optional but useful)

### Step 2: Rules Configuration

**File: rules/net2_entry_counter.rules**

```openhab
// ==============================================
// Net2 Entry Log Counter
// Provides unique ID for each entry
// ==============================================

rule "Net2 Door1 Entry Counter"
when
    Item Net2_Door1_EntryLog changed
then
    var count = 0
    if (Net2_Door1_EntryCount.state instanceof Number) {
        count = (Net2_Door1_EntryCount.state as Number).intValue()
    }
    count = count + 1
    
    // Update counter only - provides unique ID for each entry
    Net2_Door1_EntryCount.postUpdate(count)
end

rule "Net2 Door2 Entry Counter"
when
    Item Net2_Door2_EntryLog changed
then
    var count = 0
    if (Net2_Door2_EntryCount.state instanceof Number) {
        count = (Net2_Door2_EntryCount.state as Number).intValue()
    }
    count = count + 1
    
    // Update counter only - provides unique ID for each entry
    Net2_Door2_EntryCount.postUpdate(count)
end

rule "Net2 Door3 Entry Counter"
when
    Item Net2_Door3_EntryLog changed
then
    var count = 0
    if (Net2_Door3_EntryCount.state instanceof Number) {
        count = (Net2_Door3_EntryCount.state as Number).intValue()
    }
    count = count + 1
    
    // Update counter only - provides unique ID for each entry
    Net2_Door3_EntryCount.postUpdate(count)
end

rule "Net2 Door4 Entry Counter"
when
    Item Net2_Door4_EntryLog changed
then
    var count = 0
    if (Net2_Door4_EntryCount.state instanceof Number) {
        count = (Net2_Door4_EntryCount.state as Number).intValue()
    }
    count = count + 1
    
    // Update counter only - provides unique ID for each entry
    Net2_Door4_EntryCount.postUpdate(count)
end

rule "Net2 Door5 Entry Counter"
when
    Item Net2_Door5_EntryLog changed
then
    var count = 0
    if (Net2_Door5_EntryCount.state instanceof Number) {
        count = (Net2_Door5_EntryCount.state as Number).intValue()
    }
    count = count + 1
    
    // Update counter only - provides unique ID for each entry
    Net2_Door5_EntryCount.postUpdate(count)
end
```

**What these rules do:**
- Automatically increment a counter each time a door entry occurs
- Provides unique ID for each entry (useful for tracking and debugging)
- Counter persists to InfluxDB alongside the JSON data

### Step 3: Persistence Configuration

**File: persistence/influxdb.persist**

```openhab
Strategies {
    everyChange : "everyChange"
}

Items {
    // Entry log JSON - contains all entry data
    Net2_Door1_EntryLog : strategy = everyChange
    Net2_Door2_EntryLog : strategy = everyChange
    Net2_Door3_EntryLog : strategy = everyChange
    Net2_Door4_EntryLog : strategy = everyChange
    Net2_Door5_EntryLog : strategy = everyChange
    
    // Entry counters - unique ID for each entry
    Net2_Door1_EntryCount : strategy = everyChange, restoreOnStartup
    Net2_Door2_EntryCount : strategy = everyChange, restoreOnStartup
    Net2_Door3_EntryCount : strategy = everyChange, restoreOnStartup
    Net2_Door4_EntryCount : strategy = everyChange, restoreOnStartup
    Net2_Door5_EntryCount : strategy = everyChange, restoreOnStartup
}
```

**Configuration notes:**
- `everyChange` strategy persists data whenever the item changes
- `restoreOnStartup` restores counter values after OpenHAB restart
- Only the `EntryLog` JSON items are needed for Grafana - counters are optional

**InfluxDB Configuration:**
- Configure InfluxDB persistence in OpenHAB Main UI
- Settings → Persistence → InfluxDB
- Ensure connection is working (check openhab.log for "InfluxDB persistence service started")

### Step 4: Grafana Dashboard Setup

#### 4.1 Create New Panel

1. Open Grafana
2. Create new dashboard or open existing one
3. Click "Add panel" → "Add a new panel"
4. Select **Table** visualization type (top right dropdown)

#### 4.2 Configure Query

In the **Query** tab, enter this Flux query:

```flux
union(tables: [
  from(bucket: "openhab_db/autogen")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "Net2_Door1_EntryLog"),
  from(bucket: "openhab_db/autogen")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "Net2_Door2_EntryLog"),
  from(bucket: "openhab_db/autogen")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "Net2_Door3_EntryLog"),
  from(bucket: "openhab_db/autogen")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "Net2_Door4_EntryLog"),
  from(bucket: "openhab_db/autogen")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "Net2_Door5_EntryLog")
])
|> sort(columns: ["_time"], desc: true)
```

**Query explanation:**
- `union()` combines all 5 doors into a single data stream
- `range(start: -24h)` shows last 24 hours (adjust as needed: `-7d`, `-1h`, etc.)
- `filter()` selects the EntryLog measurements for each door
- `sort()` orders by time (newest first)

**For single door dashboard:**
```flux
from(bucket: "openhab_db/autogen")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "Net2_Door1_EntryLog")
  |> sort(columns: ["_time"], desc: true)
```

#### 4.3 Configure Transformations

Click the **Transform** tab and add these transformations **in order**:

**Transformation 1: Extract fields**
- Click "Add transformation"
- Select "Extract fields"
- Source: `_value`
- Format: `JSON`

This extracts firstName, lastName, doorName, timestamp, doorId from the JSON.

**Transformation 2: Merge**
- Click "Add transformation"
- Select "Merge"

This combines all door data frames into a single table.

**Transformation 3: Sort by**
- Click "Add transformation"
- Select "Sort by"
- Field: `timestamp`
- Enable "Reverse" toggle (for descending order - newest first)

This ensures entries are sorted by actual door entry time.

**Transformation 4: Organize fields**
- Click "Add transformation"
- Select "Organize fields"
- **Hide these columns** (click eye icon):
  - `_value` (raw JSON)
  - `_measurement` (duplicate measurement name)
  - `doorId` (if you don't need it)
- **Keep visible:**
  - `_time` (or `Time`)
  - `firstName`
  - `lastName`
  - `doorName`
  - `timestamp`
- **Rename columns** (click column name to edit):
  - `firstName` → `First Name`
  - `lastName` → `Last Name`
  - `doorName` → `Door Name`
  - `timestamp` → `Entry Time`
  - `_time` → `Logged At`

#### 4.4 Optional: Format Timestamp

To display timestamp in readable format instead of ISO format:

1. Scroll to **"Overrides"** section in right sidebar
2. Click **"Add field override"**
3. Select: **"Fields with name"** → `timestamp`
4. Click **"Add override property"** → **"Standard options"** → **"Unit"**
5. Select a date format:
   - `YYYY-MM-DD HH:mm:ss` → displays as `2026-01-11 11:22:50`
   - `MM/DD/YYYY h:mm:ss a` → displays as `01/11/2026 11:22:50 AM`
   - Or choose your preferred format from the list

**Result:** Timestamp displays as `2026-01-11 11:22:50` instead of `2026-01-11T11:22:50`

#### 4.5 Panel Options

In the right sidebar:

**Panel options:**
- Title: "Door Entry Logs" (or your preferred name)
- Description: "Real-time door access events from all doors"

**Table options:**
- Show table header: **ON**
- Cell display mode: **Auto** (or **Color text**)

**Standard options:**
- Unit: Leave as default for string fields
- Decimals: Not applicable for text data

#### 4.6 Save Dashboard

1. Click "Apply" (top right)
2. Click "Save dashboard" (top right)
3. Name it: "Door Entry Logs"
4. Click "Save"

### Result

Your dashboard will display a clean table like this:

| Time | First Name | Last Name | Door Name | Entry Time |
|------|------------|-----------|-----------|------------|
| 2026-01-11 10:17:35 | Nanna | Agesen | Front Door | 2026-01-11 10:17:35 |
| 2026-01-11 08:25:02 | Nanna | Agesen | Front Door | 2026-01-11 08:25:01 |
| 2026-01-10 21:27:24 | Nanna | Agesen | Front Door | 2026-01-10 21:27:23 |
| 2026-01-10 19:36:41 | Nanna | Agesen | Garage Port | 2026-01-10 19:36:40 |

### Troubleshooting

**No data showing in Grafana:**
1. Check InfluxDB persistence is running:
   ```bash
   grep -i "influx.*started" /var/log/openhab/openhab.log
   ```
2. Verify items are persisting:
   ```bash
   grep "Net2.*EntryLog" /var/log/openhab/events.log | tail -5
   ```
3. Test InfluxDB query in Data Explorer (Grafana)

**"Data is missing a number field" error:**
- Ensure panel type is **Table**, not "Time series" or "Graph"
- String data only works in Table visualizations

**"Organize fields only works with a single frame" error:**
- Add **Merge** transformation before **Organize fields**
- Ensure **Extract fields** runs first

**Entries not sorted by time:**
- Add **Sort by** transformation with `timestamp` field
- Enable "Reverse" for descending order (newest first)

**String items not persisting to InfluxDB:**
- This is a known limitation of OpenHAB's InfluxDB binding
- Use the JSON `EntryLog` items directly (works perfectly)
- Avoid creating separate String items for firstName, lastName, etc.

### Advanced: Time Range Variables

Add a time range variable to your dashboard for flexible date filtering:

1. Dashboard settings → Variables → Add variable
2. Type: **Custom**
3. Name: `timeRange`
4. Values: `-1h,-6h,-12h,-24h,-7d,-30d`
5. Display name: `Time Range`

Update query to use variable:
```flux
union(tables: [
  from(bucket: "openhab_db/autogen")
    |> range(start: $timeRange)
    |> filter(fn: (r) => r._measurement == "Net2_Door1_EntryLog"),
  // ... other doors
])
```

### Advanced: Door Filter Variable

Add a door filter dropdown:

1. Dashboard settings → Variables → Add variable
2. Type: **Custom**
3. Name: `door`
4. Values: `All,Door1,Door2,Door3,Door4,Door5`
5. Multi-value: **ON**
6. Include All: **ON**

Update filter in query:
```flux
|> filter(fn: (r) => 
  r._measurement =~ /Net2_${door}_EntryLog/
)
```

### Performance Considerations

**For high-traffic installations:**
- Limit query range to recent data: `range(start: -7d)` instead of `-30d`
- Use Grafana's auto-refresh sparingly (30s or 1m minimum)
- Consider archiving old data (InfluxDB retention policies)

**InfluxDB retention policy example:**
```sql
CREATE RETENTION POLICY "90_days" ON "openhab_db" DURATION 90d REPLICATION 1 DEFAULT
```

This automatically removes entry logs older than 90 days.

### Integration with Alerts

**Grafana Alert example - Unauthorized door access:**

1. Create separate query for unauthorized users
2. Use transformation to filter by specific names
3. Set alert condition: "when count above 0"
4. Configure notification channel (email, Slack, etc.)

This setup provides complete visibility into door access patterns with minimal OpenHAB configuration.

