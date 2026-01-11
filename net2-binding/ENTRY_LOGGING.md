# Net2 Entry Logging Feature

## Overview
The Net2 binding includes an entry logging feature that captures door access events with user information, providing JSON-formatted data suitable for both OpenHAB UI display and Grafana integration.

## Implementation Date
- **Added**: January 10, 2026
- **Version**: 5.2.0-SNAPSHOT
- **Build Location**: `/etc/openhab-addons/bundles/org.openhab.binding.net2/`

## Architecture

### Channel: `entryLog`
- **Type**: String (Read-only)
- **Description**: JSON-formatted entry event data
- **Trigger**: LiveEvents with non-null userName (physical badge/card access)
- **Does NOT trigger**: Remote UI door openings (userName is null)

### JSON Format
```json
{
  "firstName": "Nanna",
  "lastName": "Agesen",
  "doorName": "Front Door",
  "timestamp": "2026-01-10T18:48:34",
  "doorId": 6612642
}
```

### Field Specifications
| Field | Type | Source | Description |
|-------|------|--------|-------------|
| firstName | String | userName (after space) | User's first name from Net2 |
| lastName | String | userName (before space) | User's last name from Net2 |
| doorName | String | Thing label or "Door {doorId}" | Human-readable door name |
| timestamp | String | eventTime | ISO 8601 format from LiveEvents |
| doorId | Number | deviceId | Net2 door device ID |

**Name Parsing Logic:**
- Net2 provides `userName` as: "Agesen Nanna" (LastName FirstName)
- Code splits on first space and swaps: `lastName = parts[0]`, `firstName = parts[1]`
- Result: firstName="Nanna", lastName="Agesen"

## Source Code Locations

### Constants
**File**: `src/main/java/org/openhab/binding/net2/Net2BindingConstants.java`
```java
public static final String CHANNEL_ENTRY_LOG = "entryLog";
```

### Channel Definition
**File**: `src/main/resources/OH-INF/thing/thing-types.xml`
```xml
<channel id="entryLog" typeId="entryLog"/>

<channel-type id="entryLog">
    <item-type>String</item-type>
    <label>Entry Log</label>
    <description>JSON-formatted entry event: {"firstName":"John","lastName":"Doe","doorName":"Front Door","timestamp":"2026-01-10T18:04:01"}</description>
    <state readOnly="true"></state>
</channel-type>
```

### Event Handler Logic
**File**: `src/main/java/org/openhab/binding/net2/handler/Net2DoorHandler.java`

**Method**: `applyEvent(String target, JsonObject payload)`

**Logic Flow**:
1. Check if event is LiveEvents with non-null userName
2. Parse userName string and split on space
3. Swap firstName/lastName (Net2 format is "Last First")
4. Get doorName from thing label
5. Extract timestamp from eventTime
6. Build JsonObject with all fields
7. Update CHANNEL_ENTRY_LOG state
8. Log entry event

**Code Snippet**:
```java
if (("LiveEvents".equalsIgnoreCase(target) || "liveEvents".equalsIgnoreCase(target))
        && payload.has("userName") && !payload.get("userName").isJsonNull()) {

    String fullName = payload.get("userName").getAsString();
    String[] nameParts = fullName.split(" ", 2);
    String lastName = nameParts.length > 0 ? nameParts[0] : "";
    String firstName = nameParts.length > 1 ? nameParts[1] : "";

    String doorName = getThing().getLabel() != null ? getThing().getLabel() : "Door " + doorId;
    String timestamp = payload.has("eventTime") ? payload.get("eventTime").getAsString() : "";

    JsonObject entryLog = new JsonObject();
    entryLog.addProperty("firstName", firstName);
    entryLog.addProperty("lastName", lastName);
    entryLog.addProperty("doorName", doorName);
    entryLog.addProperty("timestamp", timestamp);
    entryLog.addProperty("doorId", doorId);

    updateState(Net2BindingConstants.CHANNEL_ENTRY_LOG, new StringType(entryLog.toString()));
    logger.info("Entry log: {}", entryLog.toString());
}
```

## OpenHAB Configuration

### Items Definition
**File**: `/etc/openhab/items/net2.items`

```openhab
// Entry Log Items (JSON format for Grafana)
String Net2_Door1_EntryLog "Entry Log [%s]" { channel="net2:door:server:door1:entryLog" }
String Net2_Door2_EntryLog "Entry Log [%s]" { channel="net2:door:server:door2:entryLog" }
String Net2_Door3_EntryLog "Entry Log [%s]" { channel="net2:door:server:door3:entryLog" }
String Net2_Door4_EntryLog "Entry Log [%s]" { channel="net2:door:server:door4:entryLog" }
String Net2_Door5_EntryLog "Entry Log [%s]" { channel="net2:door:server:door5:entryLog" }
```

### UI Transform
**File**: `/etc/openhab/transform/entrylog.js`

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

**Output Example**: "Nanna Agesen entered Front Door at 18:48:34"

### Sitemap Display
**File**: `/etc/openhab/sitemaps/myhouse.sitemap`

```openhab
Frame label="Fordør Kirkegade" {
    Switch item=Net2_Door1_Action mappings=[ON="Open", OFF="Closed"] label="Control Door" icon="lock-key" 
    Switch item=Net2_Door1_Status label="Door Physical Status" icon="activity" 
    Switch item=Net2_Door1_ControlTimed label="Fordør Timed Door" mappings=[1="Open"] icon="lock-key"
    Text item=Net2_Door1_Status label="Frontdoor Activity [MAP(net2doorstatus.map):%s]" icon="activity"
    Default item=Net2_Door1_LastTime label="Frontdoor Last Time Access" icon="activity-time"	
    Default item=Net2_Door1_LastUser label="Frontdoor Last User Access" icon="color-user"
    Text item=Net2_Door1_EntryLog label="Last Entry [JS(entrylog.js):%s]" icon="log"
}
```

### Persistence Configuration
**File**: `/etc/openhab/persistence/influxdb.persist`

```openhab
Items {
    Net2_Door1_EntryLog : strategy = everyChange
    Net2_Door2_EntryLog : strategy = everyChange
    Net2_Door3_EntryLog : strategy = everyChange
    Net2_Door4_EntryLog : strategy = everyChange
    Net2_Door5_EntryLog : strategy = everyChange
}
```

**Strategy**: `everyChange` - Captures every entry event immediately

## Grafana Integration

### Complete Dashboard Setup Guide

For a **step-by-step guide to creating an entry log dashboard** with InfluxDB persistence and Grafana visualizations, see:

**[EXAMPLES.md - Entry Log Dashboard Section](EXAMPLES.md#entry-log-dashboard-with-influxdb-and-grafana)**

This comprehensive guide includes:
- Complete items, rules, and persistence configuration
- Working Flux queries for single and combined door dashboards
- All transformation steps with exact settings
- Troubleshooting common issues
- Advanced features (time range variables, filters, alerts)

### Quick Reference

**Data Source:**
- **Type**: InfluxDB 2.x
- **Database**: `openhab_db/autogen`
- **Query Target**: `Net2_Door*_EntryLog` measurements

**Basic Flux Query (All Doors):**
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

**Grafana Transformations (in order):**
1. **Extract fields** - Source: `_value`, Format: `JSON`
2. **Merge** - Combines all door frames
3. **Sort by** - Field: `timestamp`, Reverse: ON
4. **Organize fields** - Hide raw JSON, rename columns

**Result:**
Clean table showing First Name, Last Name, Door Name, Entry Time from all doors, sorted by time.

### JSON Format Reference

The `entryLog` channel provides JSON data:
```json
{
  "firstName": "Nanna",
  "lastName": "Agesen",
  "doorName": "Front Door",
  "timestamp": "2026-01-10T18:48:34",
  "doorId": 6612642
}
```

### Visualization Examples

#### Table Panel (Recommended)
Display all entry events in a sortable table:
- **Columns**: First Name, Last Name, Door Name, Entry Time
- **Sort**: Timestamp descending (newest first)
- **Filter**: By door, by user, by time range
- **See**: Complete setup in [EXAMPLES.md](EXAMPLES.md#entry-log-dashboard-with-influxdb-and-grafana)

#### Stat Panel
Show latest entry:
- **Query**: Last value of EntryLog
- **Display**: Use Extract fields transformation, show firstName + lastName + doorName

#### Bar Chart
Entry frequency by door:
- **Query**: Count of entries grouped by measurement
- **Time range**: Last 7 days
- **Visualization**: Bar chart showing which doors are most used

#### Time Series

Access patterns:
- **X-axis**: Time of day (0-23 hours)
- **Y-axis**: Day of week
- **Color**: Number of entries

### Dashboard Layout Example
```
+----------------------------------+----------------------------------+
|  Latest Entry                    |  Entry Count Today               |
|  Nanna Agesen @ Front Door       |  45 entries                      |
+----------------------------------+----------------------------------+
|  Recent Entries Table                                               |
|  +---------------+---------------+-----------------+--------------+ |
|  | First Name    | Last Name     | Door Name       | Time         | |
|  +---------------+---------------+-----------------+--------------+ |
|  | Nanna         | Agesen        | Front Door      | 18:48:34     | |
|  | Kenneth       | Larsen        | Garage          | 17:23:15     | |
|  | Anna          | Hansen        | Basement Door   | 16:45:02     | |
|  +---------------+---------------+-----------------+--------------+ |
+---------------------------------------------------------------------+
|  Entry Frequency by Hour (Last 7 Days)                             |
|  [Bar chart showing access patterns throughout the day]            |
+---------------------------------------------------------------------+
```

## Testing

### Test Physical Access
1. Use physical badge/RFID card on any door
2. Check OpenHAB log: `tail -f /var/log/openhab/openhab.log | grep "Entry log"`
3. Verify JSON format in log output
4. Check item state: `curl http://localhost:8080/rest/items/Net2_Door1_EntryLog`
5. View in OpenHAB UI sitemap - should show formatted text

### Test Remote Access (Should NOT log)
1. Open door via OpenHAB UI or Net2 web interface
2. Confirm NO entry log generated (userName is null in remote openings)
3. This is by design - only physical badge access is logged

### Verify Persistence
```bash
# Check InfluxDB for stored entries
influx -database openhab -execute "SELECT * FROM Net2_Door1_EntryLog ORDER BY time DESC LIMIT 10"
```

## Troubleshooting

### No Entry Logs Generated
1. **Check SignalR connection**: Look for heartbeat messages in logs
2. **Verify badge access**: Use physical card, not remote UI
3. **Check userName field**: `grep userName /var/log/openhab/openhab.log`
4. **Bundle status**: `ssh -p 8101 openhab@localhost` → `bundle:list | grep net2`

### Wrong Name Order
- Verify code has: `lastName = nameParts[0]`, `firstName = nameParts[1]`
- Check Net2 system userName format (should be "Last First")

### Transform Not Working
1. **File exists**: `ls -l /etc/openhab/transform/entrylog.js`
2. **Syntax valid**: Test JavaScript in browser console
3. **Check logs**: `grep -i javascript /var/log/openhab/openhab.log`

### Persistence Not Storing
1. **InfluxDB running**: `systemctl status influxdb`
2. **Configuration valid**: Check `/etc/openhab/persistence/influxdb.persist`
3. **Item names match**: Must be exact, wildcards limited

## Future Enhancements

### Potential Additions
- [ ] Add `accessLevel` field (from Net2 user data)
- [ ] Add `tokenNumber` field (badge ID)
- [ ] Add `eventType` and `eventSubType` fields
- [ ] Create aggregated hourly/daily entry statistics
- [ ] Add entry/exit tracking (if Net2 supports exit events)
- [ ] Implement entry duration tracking (entry + door close time)

### Grafana Dashboards
- [ ] Create pre-built dashboard JSON export
- [ ] Add alerting rules (e.g., unauthorized access times)
- [ ] Implement anomaly detection (unusual access patterns)
- [ ] Add user access reports (who accessed which doors when)

## Related Documentation
- [README.md](README.md) - Main binding documentation
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Project context and history

## Version History
- **5.2.0-SNAPSHOT** (2026-01-10): Initial implementation of entry logging feature
  - Added entryLog channel
  - Implemented JSON formatting
  - Created UI transform
  - Configured persistence
  - Documented Grafana integration
