
# Net2 Timed Door Control Channel Examples

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
Switch item=Net2_Door1_ControlTimed label="Door 1 Timed Open (5s)" mappings=[1="Open 5s"]
```

- Sending `1` will trigger a timed open (default 5 seconds, as set in the handler or thing config).
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

If you want to send a custom payload (e.g., different LED flash count), you can extend the handler or use a rule to send a specific value. The handler will map the number to the correct JSON payload for the API:

```json
{
  "DoorId": "6612642",
  "RelayFunction": {
    "RelayId": "Relay1",
    "RelayAction": "TimedOpen",
    "RelayOpenTime": 1000 // milliseconds
  },
  "LedFlash": 3
}
```

- The value you send (e.g., `10`) is interpreted as seconds and converted to milliseconds in the payload.
- LED flash and other advanced options can be set in the handler or by extending the rule logic.

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
OPENHAB_API = "https://openhab5.agesen.dk/rest/items"

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
