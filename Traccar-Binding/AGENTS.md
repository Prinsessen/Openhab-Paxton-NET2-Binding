# AGENTS.md - Traccar Binding Development Guide

## Overview

This is a comprehensive GPS tracking binding that integrates Traccar server with openHAB. The binding supports real-time position updates via webhooks, extensive channel support, and handles multiple GPS protocols with their specific attribute differences.

**Key Achievement**: Full dual-mode operation (polling + webhooks) with 22 channels per device, protocol-agnostic attribute handling, and automatic unit conversions.

## Architecture

### Core Components

```
TraccarBindingConstants.java
├── Channel constants (CHANNEL_POSITION, CHANNEL_ALTITUDE, etc.)
└── Thing type UIDs (THING_TYPE_SERVER, THING_TYPE_DEVICE)

TraccarServerHandler.java (Bridge)
├── Traccar API client (authentication, device discovery)
├── Webhook server (TraccarWebhookServer on configurable port)
├── Polling mechanism (position refresh every N seconds)
└── Device registry (maps deviceId to TraccarDeviceHandler)

TraccarDeviceHandler.java (Thing)
├── Position channel updates (dual source: polling + webhooks)
├── Geofence event handling
├── Protocol-agnostic attribute extraction
└── Unit conversions (speed, distance, time)

TraccarWebhookServer.java
├── Jetty HTTP server (default port 8090)
├── POST/GET webhook receiver
├── JSON parsing (position + event data)
└── Handler dispatch to TraccarServerHandler
```

### Data Flow

**Polling Flow**:
1. `TraccarServerHandler.startPolling()` → scheduleWithFixedDelay every `refreshInterval`
2. HTTP GET `/api/positions?deviceId=X` to Traccar API
3. Parse JSON → `TraccarDeviceHandler.updatePositionChannels(position)`
4. Extract attributes → `updateState()` for each channel

**Webhook Flow**:
1. Traccar sends POST to `http://openhab:8090/webhook` with JSON body
2. `TraccarWebhookServer.handle()` receives request
3. Parse JSON → `TraccarServerHandler.handleWebhookEvent(data)`
4. Look up device by deviceId → `TraccarDeviceHandler.handleWebhookEvent(position)`
5. `updatePositionChannels()` extracts all attributes → channel updates

### Channel Implementation Pattern

All channels follow this pattern in `TraccarDeviceHandler.updatePositionChannels()`:

```java
// 1. Extract from position object or attributes
Object valueObj = position.get("fieldName");  // Main position fields
// OR
Object valueObj = attributes.get("attributeName");  // Protocol-specific attributes

// 2. Type check and conversion
if (valueObj instanceof Number) {
    double value = ((Number) valueObj).doubleValue();
    
    // 3. Apply unit conversion if needed
    updateState(CHANNEL_NAME, new QuantityType<>(value, Units.UNIT));
}
// OR for boolean
if (valueObj instanceof Boolean boolValue) {
    updateState(CHANNEL_NAME, OnOffType.from(boolValue));
}
// OR for string
if (valueObj != null) {
    updateState(CHANNEL_NAME, new StringType(valueObj.toString()));
}
```

## Channel Implementation Details

### Position & Navigation Channels

**Source**: Main `position` object from Traccar API/webhook

| Channel | Type | Source Field | Unit | Notes |
|---------|------|--------------|------|-------|
| `position` | Location | `latitude`, `longitude`, `altitude` | - | PointType with 3 coordinates |
| `altitude` | Number:Length | `altitude` | SIUnits.METRE | Direct from position |
| `speed` | Number:Speed | `speed` | Configurable | Traccar sends knots, converted to kmh/mph |
| `course` | Number:Angle | `course` | Units.DEGREE_ANGLE | 0-359° compass bearing |
| `accuracy` | Number:Length | `accuracy` | SIUnits.METRE | GPS accuracy radius |
| `valid` | Switch | `valid` | - | Boolean: GPS fix validity |
| `address` | String | `address` | - | Reverse geocoded street address |

**Speed Conversion**:
```java
// Traccar sends speed in knots
double speedKnots = ((Number) speedObj).doubleValue();
double convertedSpeed;
Unit<?> speedUnit;

switch(speedUnitConfig) {
    case "mph": 
        convertedSpeed = speedKnots * 1.15078; 
        speedUnit = ImperialUnits.MILES_PER_HOUR;
        break;
    case "knots":
        convertedSpeed = speedKnots;
        speedUnit = Units.KNOT;
        break;
    case "kmh":
    default:
        convertedSpeed = speedKnots * 1.852;
        speedUnit = SIUnits.KILOMETRE_PER_HOUR;
}
updateState(CHANNEL_SPEED, new QuantityType<>(convertedSpeed, speedUnit));
```

### Distance Channels (Protocol-Agnostic)

**Critical Implementation**: Handles both Teltonika (`totalDistance`) and OSMand (`odometer`)

```java
// Odometer - support both OSMand (odometer) and Teltonika (totalDistance)
Object odometerObj = attributes.get("odometer");
if (odometerObj == null) {
    odometerObj = attributes.get("totalDistance");
    logger.debug("Using totalDistance for odometer: {}", odometerObj);
} else {
    logger.debug("Using odometer attribute: {}", odometerObj);
}
if (odometerObj instanceof Number) {
    double odometerMeters = ((Number) odometerObj).doubleValue();
    logger.debug("Odometer: {} meters", odometerMeters);
    // Send in meters - OpenHAB will convert based on item metadata
    updateState(CHANNEL_ODOMETER, new QuantityType<>(odometerMeters, SIUnits.METRE));
}

// Distance - incremental distance since last update
Object distanceObj = attributes.get("distance");
if (distanceObj instanceof Number) {
    double distanceMeters = ((Number) distanceObj).doubleValue();
    updateState(CHANNEL_DISTANCE, new QuantityType<>(distanceMeters, SIUnits.METRE));
}
```

**Unit Conversion Philosophy**:
- Binding sends values in **base units** (meters, not kilometers)
- OpenHAB framework handles conversion based on item `unit="km"` metadata
- This allows users to choose any unit (km, mi, ft, etc.) without binding changes
- REST API shows converted state: `"state": "33279.52 km"` with `"unitSymbol": "km"`

### Vehicle Information Channels

**Engine Hours** (Teltonika-specific):
```java
// Engine hours (in milliseconds from Traccar)
Object hoursObj = attributes.get("hours");
if (hoursObj instanceof Number) {
    double hoursMs = ((Number) hoursObj).doubleValue();
    double hoursValue = hoursMs / 3600000.0; // Convert milliseconds to hours
    logger.debug("Engine hours: {} ms = {} hours", hoursMs, hoursValue);
    updateState(CHANNEL_HOURS, new QuantityType<>(hoursValue, Units.HOUR));
}
```

**Event Codes** (Teltonika-specific):
```java
// Event code (device-specific)
Object eventObj = attributes.get("event");
if (eventObj instanceof Number) {
    int eventCode = ((Number) eventObj).intValue();
    updateState(CHANNEL_EVENT, new DecimalType(eventCode));
}
```

### Activity Recognition (OSMand-specific)

```java
// Activity (OSMand-specific activity detection)
Object activityObj = attributes.get("activity");
if (activityObj != null) {
    updateState(CHANNEL_ACTIVITY, new StringType(activityObj.toString()));
}
```

Values: `walking`, `in_vehicle`, `still`, `on_bicycle`, `on_foot`, `running`

### Protocol Identification

```java
// Protocol from main position object (not attributes)
Object protocolObj = position.get("protocol");
if (protocolObj != null) {
    updateState(CHANNEL_PROTOCOL, new StringType(protocolObj.toString()));
}
```

## Protocol-Specific Attributes

### Teltonika (Industrial GPS Trackers)

**Webhook attributes example**:
```json
{
  "attributes": {
    "priority": 0,
    "sat": 0,
    "event": 10831,
    "distance": 0.0,
    "totalDistance": 33279520.98,
    "motion": false,
    "hours": 861239290
  }
}
```

**Key points**:
- Uses `totalDistance` instead of `odometer`
- Provides `hours` in milliseconds (engine hours)
- Provides device-specific `event` codes (10828=ignition off, 10829=ignition on, 10831=movement)
- `sat` attribute for GPS satellite count
- No battery (wired devices) or activity recognition

### OSMand / Traccar Client (Mobile Apps)

**Webhook attributes example**:
```json
{
  "attributes": {
    "batteryLevel": 85.0,
    "distance": 15.3,
    "odometer": 179924.0,
    "motion": true,
    "activity": "walking"
  }
}
```

**Key points**:
- Uses `odometer` attribute (not `totalDistance`)
- Provides `activity` recognition (Android/iOS motion APIs)
- Provides `batteryLevel` (percentage)
- No GPS satellite count, no engine hours, no event codes

### Implementation Strategy for Protocol Differences

1. **Always check both attribute names** (fallback pattern):
   ```java
   Object value = attributes.get("preferredName");
   if (value == null) {
       value = attributes.get("alternativeName");
   }
   ```

2. **Null-safe extraction** - channels show NULL if attribute missing (this is expected):
   ```java
   if (valueObj instanceof Type) {
       // Only update if present
       updateState(CHANNEL_NAME, ...);
   }
   // No else needed - channel stays NULL if not supported by protocol
   ```

3. **Debug logging** helps identify protocol differences:
   ```java
   logger.debug("Using totalDistance for odometer: {}", odometerObj);
   logger.debug("Using odometer attribute: {}", odometerObj);
   ```

## Webhook Server Implementation

### Server Lifecycle

**Startup** (in `TraccarServerHandler.initialize()`):
```java
webhookServer = new TraccarWebhookServer(webhookPort, this);
webhookServer.start();
```

**Shutdown** (in `TraccarServerHandler.dispose()`):
```java
if (webhookServer != null) {
    webhookServer.stop();
}
```

### Request Handling

`TraccarWebhookServer.java` extends Jetty `AbstractHandler`:

```java
@Override
public void handle(String target, Request baseRequest, HttpServletRequest request,
        HttpServletResponse response) throws IOException {
    
    if ("/webhook".equals(target) && "POST".equals(request.getMethod())) {
        // Read JSON body
        StringBuilder jsonBuilder = new StringBuilder();
        try (BufferedReader reader = request.getReader()) {
            String line;
            while ((line = reader.readLine()) != null) {
                jsonBuilder.append(line);
            }
        }
        
        // Parse JSON
        Gson gson = new Gson();
        Type type = new TypeToken<Map<String, Object>>() {}.getType();
        Map<String, Object> eventData = gson.fromJson(jsonBuilder.toString(), type);
        
        // Log webhook type
        Object eventObj = eventData.get("event");
        if (eventObj instanceof Map<?, ?>) {
            // Geofence/device event webhook
            logger.info("Processing webhook event type: {}", event.get("type"));
        } else {
            // Position-only webhook
            logger.info("Processing webhook position update");
        }
        
        // Dispatch to handler
        serverHandler.handleWebhookEvent(eventData);
        
        // Send response
        response.setStatus(HttpServletResponse.SC_OK);
        baseRequest.setHandled(true);
    }
}
```

### Webhook vs Polling Coordination

Both mechanisms call the same `updatePositionChannels()` method:

- **Polling**: `TraccarServerHandler` queries API → `TraccarDeviceHandler.updatePositionChannels()`
- **Webhooks**: Server receives POST → `TraccarServerHandler.handleWebhookEvent()` → `TraccarDeviceHandler.handleWebhookEvent()` → `updatePositionChannels()`

This ensures consistent channel updates regardless of source.

## Unit Conversion Best Practices

### DO: Send Base Units, Let OpenHAB Convert

✅ **Correct approach**:
```java
// Send in meters (base unit)
updateState(CHANNEL_ODOMETER, new QuantityType<>(33279520.98, SIUnits.METRE));

// Item definition with unit metadata
Number:Length Vehicle_Odometer "Odometer [%.1f km]" 
    {channel="traccar:device:myserver:car1:odometer", unit="km"}
```

Result: OpenHAB displays `33,279.5 km`, REST API returns `"state": "33279.52 km"`

### DON'T: Convert in Binding Code

❌ **Wrong approach**:
```java
// Don't do this - breaks flexibility
double odometerKm = odometerMeters / 1000.0;
updateState(CHANNEL_ODOMETER, new QuantityType<>(odometerKm, Units.KILOMETRE));
```

Problem: User can't change units without binding modification.

### Why This Matters

1. **Flexibility**: Users can choose any unit (km, mi, ft) via item metadata
2. **Consistency**: OpenHAB framework handles all conversions uniformly
3. **API Correctness**: REST API returns proper unitSymbol
4. **Persistence**: State stored in normalized base units

### Exception: Speed Conversion

Speed requires conversion because Traccar uses **knots** (not SI base unit m/s):

```java
// This is necessary because knots is not the openHAB base unit
double speedKnots = ((Number) speedObj).doubleValue();
double convertedSpeed = speedKnots * 1.852; // to km/h
updateState(CHANNEL_SPEED, new QuantityType<>(convertedSpeed, SIUnits.KILOMETRE_PER_HOUR));
```

User can still override with `unit="mph"` in item - OpenHAB will convert km/h → mph.

## Debugging and Troubleshooting

### Enable Debug Logging

```
openhab> log:set DEBUG org.openhab.binding.traccar
openhab> log:set TRACE org.openhab.binding.traccar  # For full detail
```

### Key Log Messages

**Webhook server**:
```
[INFO] Webhook server started on port 8090
[INFO] Received webhook (POST): {"position":...}
[INFO] Processing webhook position update
[INFO] Processing webhook event type: geofenceEnter
```

**Odometer protocol detection**:
```
[DEBUG] Using totalDistance for odometer: 3.3279520E7
[DEBUG] Using odometer attribute: 179924.0
[DEBUG] Odometer: 33279520.98 meters
```

**Engine hours conversion**:
```
[DEBUG] Engine hours: 861239290.0 ms = 239.23 hours
```

### Webhook Testing Script

Create `webhook_monitor.py` to capture raw webhook traffic:

```python
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys

class WebhookMonitor(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = self.headers.get('Content-Length')
        if content_length:
            body = self.rfile.read(int(content_length)).decode('utf-8')
            try:
                data = json.loads(body)
                print(json.dumps(data, indent=2))
            except:
                print(body)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8091
    server = HTTPServer(('0.0.0.0', port), WebhookMonitor)
    print(f"Listening on port {port}...")
    server.serve_forever()
```

Usage:
```bash
python3 webhook_monitor.py 8091
# Update Traccar to forward to port 8091 temporarily
```

### Common Issues

**Odometer showing meters instead of km**:
- Check item has `unit="km"` metadata
- Verify binding sends `SIUnits.METRE` not manual division by 1000

**Engine hours showing milliseconds**:
- Check conversion: `hoursMs / 3600000.0`
- Verify `Units.HOUR` is used, not milliseconds

**Channels always NULL**:
- Check protocol supports that attribute (see Protocol-Specific Attributes section)
- Verify attribute exists in Traccar API: `curl -u "user:pass" "https://traccar/api/positions?deviceId=1"`

**Webhooks not received**:
- Check firewall allows port 8090
- Verify Traccar `forward.url` points to correct OpenHAB IP
- Test with: `curl -X POST http://localhost:8090/webhook -d '{"test":true}'`

## Build and Deployment

### Build binding:
```bash
cd /etc/openhab-addons/bundles/org.openhab.binding.traccar
mvn clean install -DskipTests
```

### Deploy:
```bash
sudo cp target/org.openhab.binding.traccar-5.2.0-SNAPSHOT.jar /usr/share/openhab/addons/
```

OpenHAB hot-reloads automatically (check karaf logs).

### Code Style

**Import ordering**: Spotless enforces alphabetical imports:
```java
import javax.measure.Unit;
import org.openhab.core.library.unit.ImperialUnits;
import org.openhab.core.library.unit.SIUnits;
import org.openhab.core.library.unit.Units;
```

Fix with: `mvn spotless:apply`

## Files to Synchronize

Keep these directories in sync:
- `/etc/openhab-addons/bundles/org.openhab.binding.traccar/` (Maven build source)
- `/etc/openhab/Traccar-Binding/` (Development copy)

Sync command:
```bash
cp -r /etc/openhab-addons/bundles/org.openhab.binding.traccar/src/main/java/org/openhab/binding/traccar/internal/* \
      /etc/openhab/Traccar-Binding/src/main/java/org/openhab/binding/traccar/internal/

cp /etc/openhab-addons/bundles/org.openhab.binding.traccar/src/main/resources/OH-INF/thing/thing-types.xml \
   /etc/openhab/Traccar-Binding/src/main/resources/OH-INF/thing/thing-types.xml
```

## Adding New Channels

### 1. Add constant to `TraccarBindingConstants.java`:
```java
public static final String CHANNEL_NEW = "newChannel";
```

### 2. Add channel definition to `thing-types.xml`:
```xml
<channel id="newChannel" typeId="new-channel"/>

<!-- Later in file -->
<channel-type id="new-channel">
    <item-type>Number:Length</item-type>
    <label>New Channel</label>
    <description>Description of new channel</description>
    <state readOnly="true" pattern="%.1f m"/>
</channel-type>
```

### 3. Add extraction logic to `TraccarDeviceHandler.java`:

```java
// In updatePositionChannels() method
Object newObj = attributes.get("newAttribute");
if (newObj instanceof Number) {
    double value = ((Number) newObj).doubleValue();
    updateState(CHANNEL_NEW, new QuantityType<>(value, SIUnits.METRE));
}
```

### 4. Add items to configuration:
```openhab
Number:Length Vehicle_New "New Channel [%.1f m]" 
    {channel="traccar:device:myserver:car1:newChannel"}
```

### 5. Rebuild and deploy (see Build and Deployment section)

## Future Enhancement Ideas

1. **Historic position tracking**: Store position history in persistence, display tracks on map
2. **Geofence creation via UI**: Allow defining geofences from openHAB instead of Traccar
3. **Multi-tracker routing**: Display routes for multiple vehicles simultaneously
4. **Fuel consumption**: Calculate based on odometer + engine hours for compatible devices
5. **Driver behavior scoring**: Aggregate harsh acceleration/braking/cornering events
6. **Bluetooth beacon support**: For Teltonika devices with BLE sensors
7. **CAN bus data**: Extract vehicle data for Teltonika with CAN adapter
8. **Temperature sensors**: Many industrial trackers support external temperature probes

## Resources

- **Traccar API Documentation**: https://www.traccar.org/api-reference/
- **Traccar Protocol List**: https://www.traccar.org/protocols/
- **OpenHAB Units**: https://www.openhab.org/docs/concepts/units-of-measurement.html
- **Jetty Documentation**: https://eclipse.dev/jetty/documentation/

## Contact

- **Author**: Nanna Agesen
- **Email**: Nanna@agesen.dk
- **GitHub**: [@Prinsessen](https://github.com/Prinsessen)
