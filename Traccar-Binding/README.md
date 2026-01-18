# Traccar Binding

The Traccar binding integrates [Traccar](https://www.traccar.org/) GPS tracking server with openHAB, enabling real-time vehicle/device tracking, geofencing automation, and comprehensive location monitoring.

Traccar is an open-source GPS tracking system that supports over 200 GPS protocols and 2000+ GPS tracking devices.

## Author

- **Name**: Nanna Agesen
- **Email**: Nanna@agesen.dk  
- **GitHub**: [@Prinsessen](https://github.com/Prinsessen)

## Supported Things

This binding supports the following thing types:

- **`server`** (Bridge) - Connection to a Traccar server instance (cloud or self-hosted)
- **`device`** - Individual GPS tracked device/vehicle managed by the Traccar server

## Features

### Real-Time Position Tracking
- GPS coordinates (latitude, longitude)
- Altitude/elevation above sea level
- Speed with configurable units (km/h, mph, knots)
- Direction/course (compass bearing)
- Location accuracy
- GPS fix validity indicator
- Street address (reverse geocoding)
- Last update timestamp
- Device protocol identification

### Distance Tracking
- **Odometer**: Total distance traveled with automatic km conversion
- **Incremental Distance**: Distance since last position update (trip tracking)
- Protocol-agnostic support (Teltonika `totalDistance`, OSMand `odometer`)

### Device Information
- Battery level monitoring
- Motion detection
- Device activity recognition (walking, in_vehicle, still)
- Online/offline status
- Engine hours tracking (for vehicle trackers)
- Device-specific event codes
- GPS satellite count
- GSM/cellular signal strength

### Geofencing Automation
- Real-time geofence entry/exit events via webhooks
- Geofence ID and name tracking
- Instant notifications (no polling delay)
- Perfect for automating garage doors, lights, security systems

### Dual Update Mechanism
- **Polling**: Configurable interval (minimum 10 seconds) for position updates
- **Webhooks**: Real-time position updates + instant event notifications
- Efficient hybrid approach minimizes API calls while maintaining responsiveness
- Webhook support for position forwarding (every 1-2 seconds during movement)

## Discovery

The binding automatically discovers devices configured in your Traccar server:

1. Add and configure the Traccar Server bridge
2. Devices will appear in the Inbox automatically
3. Accept discovered devices or manually configure them with device ID

## Thing Configuration

### Server Bridge

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | text | Yes | - | Traccar server URL (e.g., `https://demo.traccar.org`) |
| `username` | text | Yes | - | Traccar account username/email |
| `password` | text | Yes | - | Traccar account password |
| `refreshInterval` | integer | No | 60 | Position polling interval in seconds (minimum: 10) |
| `webhookPort` | integer | No | 8090 | Port for receiving webhooks (1024-65535) |
| `speedUnit` | text | No | kmh | Speed unit: `kmh`, `mph`, or `knots` |

### Device

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deviceId` | integer | Yes | Traccar device ID |

## Channels

### Position & Navigation

| Channel | Type | Description | Example State |
|---------|------|-------------|---------------|
| `position` | Location | GPS coordinates (lat, lon, altitude) | 57.0921333,9.5253683 |
| `altitude` | Number:Length | Altitude/elevation above sea level | 45.2 m |
| `speed` | Number:Speed | Current speed (converted to configured unit) | 65.5 km/h |
| `course` | Number:Angle | Direction/heading (0-359°) | 135° |
| `accuracy` | Number:Length | GPS accuracy in meters | 3.5 m |
| `valid` | Switch | GPS fix validity (ON=valid, OFF=no fix) | ON |
| `address` | String | Street address from reverse geocoding | "123 Main St" |

### Distance Tracking

| Channel | Type | Description | Example State |
|---------|------|-------------|---------------|
| `odometer` | Number:Length | Total distance traveled (auto-converts to km) | 33,279.5 km |
| `distance` | Number:Length | Incremental distance since last update | 15.3 m |

### Device Status

| Channel | Type | Description | Example State |
|---------|------|-------------|---------------|
| `status` | String | Device status | online/offline/unknown |
| `lastUpdate` | DateTime | Timestamp of last update | 2026-01-18T09:23:10 |
| `batteryLevel` | Number:Dimensionless | Battery level (0-100%) | 85% |
| `motion` | Switch | Movement detection (ON=moving) | ON |
| `activity` | String | Activity recognition (OSMand only) | walking/in_vehicle/still |
| `protocol` | String | Device protocol/connection type | teltonika/osmand |

### Vehicle Information

| Channel | Type | Description | Example State |
|---------|------|-------------|---------------|
| `ignition` | Switch | Ignition status (ON=ignition on, OFF=off) | ON |
| `hours` | Number:Time | Total engine running hours | 239.2 h |
| `event` | Number | Device-specific event code | 10831 |

### Connectivity

| Channel | Type | Description | Example State |
|---------|------|-------------|---------------|
| `gpsSatellites` | Number | Number of GPS satellites | 8 |
| `gsmSignal` | Number:Dimensionless | GSM/cellular signal strength | 75% |

### Geofencing

| Channel | Type | Description | Example State |
|---------|------|-------------|---------------|
| `geofenceEvent` | String | Event type | geofenceEnter/geofenceExit |
| `geofenceId` | Number | Numeric ID of triggered geofence | 1 |
| `geofenceName` | String | Name of triggered geofence | "Home" |

## Full Example

### traccar.things

```openhab
Bridge traccar:server:myserver "Traccar Server" [
    url="https://demo.traccar.org",
    username="user@example.com",
    password="password123",
    refreshInterval=30,
    webhookPort=8090,
    speedUnit="kmh"
] {
    Thing device car1 "Family Car" [ deviceId=1 ]
    Thing device phone1 "My Phone" [ deviceId=2 ]
}
```

### traccar.items

```openhab
Group gFamilyCar "Family Car" <car>

// Position & Navigation
Location FamilyCar_Position "Position" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:position"}

Number:Length FamilyCar_Altitude "Altitude [%.1f m]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:altitude"}

Number:Speed FamilyCar_Speed "Speed [%.1f %unit%]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:speed"}

Number:Angle FamilyCar_Course "Direction [%.0f °]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:course"}

Number:Length FamilyCar_Accuracy "GPS Accuracy [%.1f m]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:accuracy"}

Switch FamilyCar_GpsValid "GPS Valid" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:valid"}

String FamilyCar_Address "Address [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:address"}

// Distance Tracking (automatic km conversion with unit="km")
Number:Length FamilyCar_Odometer "Odometer [%.1f km]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:odometer", unit="km"}

Number:Length FamilyCar_Distance "Distance [%.1f m]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:distance"}

// Device Status
String FamilyCar_Status "Status [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:status"}

DateTime FamilyCar_LastUpdate "Last Update [%1$tF %1$tR]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:lastUpdate"}

Number:Dimensionless FamilyCar_Battery "Battery [%.0f %%]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:batteryLevel"}

Switch FamilyCar_Motion "Motion" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:motion"}

String FamilyCar_Activity "Activity [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:activity"}

String FamilyCar_Protocol "Protocol [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:protocol"}

// Vehicle Information
Switch FamilyCar_Ignition "Ignition [MAP(ignition.map):%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:ignition"}

Number:Time FamilyCar_Hours "Engine Hours [%.1f h]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:hours", unit="h"}

Number FamilyCar_Event "Event [MAP(teltonika_event.map):%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:event"}

// Connectivity
Number FamilyCar_GpsSatellites "GPS Satellites [%d]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:gpsSatellites"}

Number:Dimensionless FamilyCar_GsmSignal "GSM Signal [%.0f %%]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:gsmSignal"}

// Geofencing
String FamilyCar_GeofenceEvent "Event [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:geofenceEvent"}

Number FamilyCar_GeofenceId "Geofence ID" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:geofenceId"}

String FamilyCar_GeofenceName "Geofence [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:geofenceName"}
```

### traccar.sitemap

```openhab
sitemap tracking label="Vehicle Tracking" {
    Frame label="Family Car" {
        Mapview item=FamilyCar_Position height=10
        
        Text item=FamilyCar_Status label="Status [%s]" icon="status"
        Text item=FamilyCar_LastUpdate label="Last Update" icon="time"
        
        Text item=FamilyCar_Speed label="Speed [%.1f %unit%]" icon="speed"
        Text item=FamilyCar_Course label="Course [%.0f°]" icon="wind"
        Text item=FamilyCar_Altitude label="Altitude [%.1f m]" icon="altitude"
        Switch item=FamilyCar_GpsValid label="GPS Valid" icon="network"
        Text item=FamilyCar_Accuracy label="Accuracy [%.1f m]" icon="zoom"
        
        Text item=FamilyCar_Odometer label="Odometer [%.1f km]" icon="line"
        Text item=FamilyCar_Distance label="Distance [%.1f m]" icon="line"
        Text item=FamilyCar_Hours label="Engine Hours [%.1f h]" icon="time"
        
        Text item=FamilyCar_Battery label="Battery [%.0f %%]" icon="battery"
        Switch item=FamilyCar_Motion label="Motion" icon="motion"
        Text item=FamilyCar_Activity label="Activity [%s]" icon="motion"
        
        Text item=FamilyCar_GpsSatellites label="GPS Satellites [%d]" icon="network"
        Text item=FamilyCar_GsmSignal label="GSM Signal [%.0f %%]" icon="qualityofservice"
        
        Text item=FamilyCar_GeofenceName label="Location [%s]" icon="location"
        Text item=FamilyCar_Address label="Address [%s]" icon="location"
        Text item=FamilyCar_Protocol label="Protocol [%s]" icon="text"
        Text item=FamilyCar_Event label="Event Code [%d]" icon="text"
    }
}
```

### Geofencing Rule Example

```openhab
rule "Open Garage on Arrival"
when
    Item FamilyCar_GeofenceEvent changed to "geofenceEnter"
then
    val geofenceId = (FamilyCar_GeofenceId.state as Number).intValue()
    
    if (geofenceId == 1) { // Home geofence
        logInfo("Garage", "Car arriving, opening garage door")
        GarageDoor.sendCommand(ON)
        GarageLight.sendCommand(ON)
    }
end

rule "Trip Tracking"
when
    Item FamilyCar_Distance received update
then
    val distance = (FamilyCar_Distance.state as QuantityType<Length>).toUnit("m").doubleValue()
    
    if (distance > 0) {
        logInfo("Trip", "Distance since last update: {} m", distance)
        // Accumulate trip distance
        TripDistance.postUpdate((TripDistance.state as Number).doubleValue() + distance)
    }
end

rule "Activity Detection"
when
    Item FamilyCar_Activity changed
then
    val activity = FamilyCar_Activity.state.toString()
    
    switch(activity) {
        case "walking": {
            logInfo("Activity", "Driver is walking")
        }
        case "in_vehicle": {
            logInfo("Activity", "Driver is in vehicle")
        }
        case "still": {
            logInfo("Activity", "Driver is stationary")
        }
    }
end

rule "Low GPS Accuracy Alert"
when
    Item FamilyCar_Accuracy changed
then
    val accuracy = (FamilyCar_Accuracy.state as QuantityType<Length>).toUnit("m").doubleValue()
    
    if (accuracy > 50) {
        logWarn("GPS", "Poor GPS accuracy: {} m", accuracy)
        sendNotification("admin@example.com", "Poor GPS signal on Family Car")
    }
end

rule "GPS Fix Lost"
when
    Item FamilyCar_GpsValid changed to OFF
then
    logWarn("GPS", "GPS fix lost - position may be unreliable")
    // Could trigger indoor parking automation
end
```

## Webhook Configuration

Webhooks enable real-time position updates and instant geofence notifications. The binding supports two types of webhook data:

### 1. Position Updates (Real-Time Tracking)
Receive position updates every 1-2 seconds during movement without polling.

### 2. Event Notifications (Geofencing)
Instant notifications for geofence entry/exit, device online/offline events.

### Traccar Server Configuration

#### Modern Configuration (Traccar 5.0+)

Edit `/opt/traccar/conf/traccar.xml` (or equivalent):

```xml
<!-- Enable position forwarding -->
<entry key='forward.enable'>true</entry>
<entry key='forward.url'>http://YOUR_OPENHAB_IP:8090/webhook</entry>
<entry key='forward.type'>json</entry>
<entry key='forward.retry'>true</entry>

<!-- Enable event forwarding -->
<entry key="event.forward.enable">true</entry>
<entry key='event.forward.url'>http://YOUR_OPENHAB_IP:8090/webhook</entry>
```

**Replace `YOUR_OPENHAB_IP`** with your openHAB server's IP address (e.g., `192.168.1.50`).

Restart Traccar:
```bash
sudo systemctl restart traccar
```

#### Web Interface Configuration (Alternative)

1. Go to **Traccar web interface** → **Settings** → **Notifications**
2. Add notification for events you want:
   - `geofenceEnter` - Device enters geofence
   - `geofenceExit` - Device exits geofence
   - `deviceOnline` - Device comes online
   - `deviceOffline` - Device goes offline
3. Select **Web Request (POST)**
4. Set URL: `http://YOUR_OPENHAB_IP:8090/webhook`
5. Content Type: `application/json`

### Webhook Port Configuration

The default webhook port is **8090**. You can change it in the bridge configuration:

```openhab
Bridge traccar:server:myserver [ webhookPort=8090 ]
```

**Important**: 
- Port must be between 1024-65535
- Ensure firewall allows incoming connections on this port
- Traccar server must be able to reach openHAB IP address

### Testing Webhooks

#### 1. Test with curl

```bash
curl -X POST http://localhost:8090/webhook \
  -H "Content-Type: application/json" \
  -d '{"position":{"id":1,"deviceId":1,"latitude":57.092,"longitude":9.525}}'
```

#### 2. Monitor Webhook Traffic

Create a monitoring script to see all incoming webhooks:

```python
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys

class WebhookMonitor(BaseHTTPRequestHandler):
    def log_request_details(self):
        content_length = self.headers.get('Content-Length')
        
        # GET request
        if self.command == 'GET':
            query = self.path.split('?', 1)
            if len(query) > 1:
                params = dict(p.split('=') for p in query[1].split('&') if '=' in p)
                print(f"\n{'='*60}")
                print(f"GET Request - Query Parameters:")
                print(json.dumps(params, indent=2))
                
        # POST request
        elif self.command == 'POST' and content_length:
            body = self.rfile.read(int(content_length)).decode('utf-8')
            try:
                data = json.loads(body)
                print(f"\n{'='*60}")
                print(f"POST Request - JSON Body:")
                print(json.dumps(data, indent=2))
            except:
                print(f"\n{'='*60}")
                print(f"POST Request - Raw Body:")
                print(body)
    
    def do_GET(self):
        self.log_request_details()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    
    def do_POST(self):
        self.log_request_details()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8091
    server = HTTPServer(('0.0.0.0', port), WebhookMonitor)
    print(f"Webhook monitor listening on port {port}...")
    server.serve_forever()
```

Save as `webhook_monitor.py` and run:
```bash
python3 webhook_monitor.py 8091
```

Then temporarily update Traccar to forward to port 8091 to see raw webhook data.

#### 3. Check OpenHAB Logs

Enable debug logging:
```
openhab> log:set DEBUG org.openhab.binding.traccar
```

Watch for webhook messages:
```bash
tail -f /var/log/openhab/openhab.log | grep "webhook"
```

You should see:
```
[INFO] Received webhook (POST): {"position":{"latitude":57.092,...}}
[INFO] Processing webhook position update
```

### Webhook Data Format

#### Position Update Example
```json
{
  "position": {
    "id": 0,
    "deviceId": 10,
    "protocol": "teltonika",
    "serverTime": "2026-01-18T08:23:16.836+00:00",
    "deviceTime": "2026-01-18T08:23:10.011+00:00",
    "fixTime": "2026-01-18T08:23:10.011+00:00",
    "valid": false,
    "latitude": 57.0921333,
    "longitude": 9.5253683,
    "altitude": 0.0,
    "speed": 0.0,
    "course": 0.0,
    "accuracy": 0.0,
    "attributes": {
      "priority": 0,
      "sat": 0,
      "event": 10828,
      "distance": 0.0,
      "totalDistance": 33279520.98,
      "motion": false,
      "hours": 861239290
    }
  },
  "device": {
    "id": 10,
    "name": "Dream Catcher - FMM920",
    "uniqueId": "866088075183606",
    "status": "online"
  }
}
```

#### Geofence Event Example
```json
{
  "event": {
    "id": 1234,
    "type": "geofenceEnter",
    "eventTime": "2026-01-18T08:23:16.836+00:00",
    "deviceId": 10,
    "geofenceId": 1
  },
  "position": {
    "latitude": 57.092,
    "longitude": 9.525
  },
  "device": {
    "id": 10,
    "name": "Family Car"
  },
  "geofence": {
    "id": 1,
    "name": "Home"
  }
}
```

## Speed Unit Conversion

Traccar reports speed in **knots**. The binding converts to:
- **kmh**: × 1.852 (default)
- **mph**: × 1.15078
- **knots**: no conversion

Configure in bridge:
```openhab
Bridge traccar:server:myserver [ speedUnit="kmh" ]
```

## Distance Unit Conversion

### Automatic Kilometer Conversion

The binding sends odometer values in **meters** (Traccar's base unit). To display in kilometers, use item metadata:

```openhab
Number:Length Vehicle_Odometer "Odometer [%.1f km]" 
    {channel="traccar:device:myserver:car1:odometer", unit="km"}
```

OpenHAB automatically converts:
- Traccar sends: `33,279,520.98` meters
- OpenHAB stores: `33279520.98 m` (base unit)
- Display with `unit="km"`: `33,279.5 km`
- REST API returns: `"state": "33279.52 km"` with `"unitSymbol": "km"`

### Other Distance Units

You can use any unit supported by OpenHAB:
```openhab
Number:Length Vehicle_Odometer_Miles "Odometer [%.1f mi]" 
    {channel="traccar:device:myserver:car1:odometer", unit="mi"}

Number:Length Vehicle_Distance_Feet "Distance [%.1f ft]" 
    {channel="traccar:device:myserver:car1:distance", unit="ft"}
```

### Protocol Differences

Different GPS protocols report odometer differently:

| Protocol | Attribute Name | Notes |
|----------|----------------|-------|
| Teltonika | `totalDistance` | Industrial trackers, cumulative distance |
| OSMand | `odometer` | Mobile apps, trip odometer |
| H02/GT06 | `odometer` | Hardware trackers |

The binding **automatically handles both**:
1. First checks for `odometer` attribute
2. Falls back to `totalDistance` if not present
3. Logs which attribute was used (visible in DEBUG mode)

## Advanced Features

### Ignition Monitoring & Notifications

The `ignition` channel provides real-time ignition status from compatible vehicle trackers (e.g., Teltonika FMM920). Use this for automatic notifications when your vehicle starts or is parked:

```openhab
// Items
Switch Vehicle_Ignition "Ignition [MAP(ignition.map):%s]" <fire>
    {channel="traccar:device:myserver:car1:ignition"}

// MAP transformation: transform/ignition.map
ON=On
OFF=Off
NULL=Unknown
-=Unknown

// Rule
rule "Vehicle Ignition ON Notification"
when
    Item Vehicle_Ignition changed from OFF to ON
then
    val position = Vehicle_Position.state.toString
    val address = Vehicle_Address.state.toString
    val speed = Vehicle_Speed.state
    val odometer = Vehicle_Odometer.state
    
    // Extract coordinates
    val coords = position.split(",")
    val latitude = coords.get(0)
    val longitude = coords.get(1)
    val mapLink = "https://www.google.com/maps?q=" + latitude + "," + longitude
    
    // Format timestamp
    val dateFormat = new java.text.SimpleDateFormat("dd/MM HH:mm")
    val timestamp = dateFormat.format(new java.util.Date())
    
    // Send HTML email
    val mailActions = getActions("mail","mail:smtp:samplesmtp")
    
    val emailBody = "<html><body style='font-family: Arial, sans-serif;'>" +
        "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); " +
        "color: white; padding: 20px; border-radius: 10px;'>" +
        "<h2 style='margin: 0;'>🏍️ VEHICLE STARTED</h2>" +
        "<p style='margin: 5px 0; opacity: 0.9;'>" + timestamp + "</p>" +
        "</div>" +
        "<div style='background: #f8f9fa; padding: 15px; margin-top: 10px; border-radius: 8px;'>" +
        "<h3 style='color: #667eea; margin-top: 0;'>📍 Location</h3>" +
        "<p style='margin: 5px 0;'>" + address + "</p>" +
        "<p style='margin-top: 10px;'><a href='" + mapLink + "' " +
        "style='color: #667eea; text-decoration: none;'>📍 View on Map</a></p>" +
        "</div>" +
        "<table style='width: 100%; margin-top: 10px;'>" +
        "<tr><td style='padding: 10px; background: #e8f5e9; border-radius: 5px;'>" +
        "<strong>🔥 Ignition:</strong> ON</td></tr>" +
        "<tr><td style='padding: 10px; background: #e3f2fd; border-radius: 5px;'>" +
        "<strong>📏 Odometer:</strong> " + odometer + "</td></tr>" +
        "</table>" +
        "</body></html>"
    
    mailActions.sendHtmlMail("user@example.com", "🏍️ Vehicle Started", emailBody)
    logInfo("vehicle", "Ignition ON notification sent")
end

rule "Vehicle Ignition OFF Notification"
when
    Item Vehicle_Ignition changed from ON to OFF
then
    val position = Vehicle_Position.state.toString
    val address = Vehicle_Address.state.toString
    val odometer = Vehicle_Odometer.state
    val coords = position.split(",")
    val mapLink = "https://www.google.com/maps?q=" + coords.get(0) + "," + coords.get(1)
    
    val dateFormat = new java.text.SimpleDateFormat("dd/MM HH:mm")
    val timestamp = dateFormat.format(new java.util.Date())
    
    val mailActions = getActions("mail","mail:smtp:samplesmtp")
    
    val emailBody = "<html><body style='font-family: Arial, sans-serif;'>" +
        "<div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); " +
        "color: white; padding: 20px; border-radius: 10px;'>" +
        "<h2 style='margin: 0;'>🏍️ VEHICLE PARKED</h2>" +
        "<p style='margin: 5px 0; opacity: 0.9;'>" + timestamp + "</p>" +
        "</div>" +
        "<div style='background: #f8f9fa; padding: 15px; margin-top: 10px; border-radius: 8px;'>" +
        "<h3 style='color: #f5576c; margin-top: 0;'>📍 Parked Location</h3>" +
        "<p style='margin: 5px 0;'>" + address + "</p>" +
        "<p style='margin-top: 10px;'><a href='" + mapLink + "' " +
        "style='color: #f5576c; text-decoration: none;'>📍 View on Map</a></p>" +
        "</div>" +
        "</body></html>"
    
    mailActions.sendHtmlMail("user@example.com", "🏍️ Vehicle Parked", emailBody)
    logInfo("vehicle", "Ignition OFF notification sent")
end
```

### Trip Distance Tracking

Use the `distance` channel to track trip segments:

```openhab
// Items
Number:Length Trip_Distance "Trip Distance [%.1f km]" {unit="km"}
Number:Length Vehicle_Distance "Distance" {channel="traccar:device:myserver:car1:distance"}

// Rule
rule "Accumulate Trip Distance"
when
    Item Vehicle_Distance received update
then
    val increment = (Vehicle_Distance.state as QuantityType<Length>).toUnit("m").doubleValue()
    
    if (increment > 0) {
        val current = (Trip_Distance.state as QuantityType<Length>).toUnit("m").doubleValue()
        Trip_Distance.postUpdate(new QuantityType((current + increment), "m"))
        
        logInfo("Trip", "Added {} m to trip (total: {} km)", 
            increment, (current + increment) / 1000.0)
    }
end

rule "Reset Trip on Arrival"
when
    Item Vehicle_GeofenceEvent changed to "geofenceEnter"
then
    if ((Vehicle_GeofenceId.state as Number).intValue() == 1) {
        val finalDistance = (Trip_Distance.state as QuantityType<Length>).toUnit("km").doubleValue()
        logInfo("Trip", "Trip completed: {} km", finalDistance)
        
        Trip_Distance.postUpdate(new QuantityType(0, "m"))
    }
end
```

### Real-Time Movement Monitoring

Webhooks deliver position updates every 1-2 seconds during movement:

```openhab
rule "Real-Time Speed Monitoring"
when
    Item Vehicle_Speed received update
then
    val speed = (Vehicle_Speed.state as QuantityType<Speed>).toUnit("km/h").doubleValue()
    
    if (speed > 120) {
        sendNotification("admin@example.com", 
            String::format("Vehicle speeding: %.0f km/h!", speed))
        logWarn("Speed", "Excessive speed detected: {} km/h", speed)
    }
end

rule "Track GPS Quality During Movement"
when
    Item Vehicle_Motion changed to ON
then
    createTimer(now.plusSeconds(5), [ |
        val accuracy = (Vehicle_Accuracy.state as QuantityType<Length>).toUnit("m").doubleValue()
        val satellites = Vehicle_GpsSatellites.state as Number
        val gpsValid = Vehicle_GpsValid.state == ON
        
        logInfo("GPS", "Movement started - GPS quality check:")
        logInfo("GPS", "  Valid: {}", gpsValid)
        logInfo("GPS", "  Accuracy: {} m", accuracy)
        logInfo("GPS", "  Satellites: {}", satellites)
        
        if (!gpsValid || accuracy > 50) {
            sendNotification("admin@example.com", "Poor GPS quality during movement")
        }
    ])
end
```

### Activity-Based Automation

For OSMand/Traccar Client apps:

```openhab
rule "Detect Driver Left Vehicle"
when
    Item Phone_Activity changed from "in_vehicle" to "walking"
then
    logInfo("Activity", "Driver exited vehicle and is walking")
    
    // Wait 2 minutes to confirm
    createTimer(now.plusMinutes(2), [ |
        if (Phone_Activity.state.toString() == "walking") {
            // Driver has been walking for 2 minutes
            logInfo("Activity", "Driver confirmed away from vehicle")
            Vehicle_Status_Text.postUpdate("Driver away")
            
            // Lock vehicle if supported
            Vehicle_Lock.sendCommand(ON)
        }
    ])
end

rule "Detect Arrival Home on Foot"
when
    Item Phone_GeofenceEvent changed to "geofenceEnter"
then
    val activity = Phone_Activity.state.toString()
    val geofenceId = (Phone_GeofenceId.state as Number).intValue()
    
    if (geofenceId == 1 && activity == "walking") {
        logInfo("Arrival", "Arrived home on foot - enable walking mode")
        // Turn on pathway lights instead of garage
        Pathway_Lights.sendCommand(ON)
        Front_Door.sendCommand(UNLOCK)
    } else if (geofenceId == 1 && activity == "in_vehicle") {
        logInfo("Arrival", "Arrived home by vehicle - open garage")
        Garage_Door.sendCommand(ON)
    }
end
```

### Multi-Device Proximity Detection

Track multiple vehicles/phones:

```openhab
rule "Family Members Home"
when
    Item Person1_GeofenceEvent received update or
    Item Person2_GeofenceEvent received update or
    Item Car_GeofenceEvent received update
then
    val person1Home = Person1_GeofenceName.state.toString() == "Home"
    val person2Home = Person2_GeofenceName.state.toString() == "Home"
    val carHome = Car_GeofenceName.state.toString() == "Home"
    
    val countHome = (person1Home ? 1 : 0) + (person2Home ? 1 : 0) + (carHome ? 1 : 0)
    
    logInfo("Presence", "Devices at home: {}", countHome)
    
    if (countHome == 0) {
        logInfo("Presence", "Nobody home - enable away mode")
        House_Mode.postUpdate("away")
        Climate_Away.sendCommand(ON)
        Security_Armed.sendCommand(ON)
    } else if (countHome >= 1) {
        logInfo("Presence", "Someone home - disable away mode")
        House_Mode.postUpdate("home")
        Climate_Away.sendCommand(OFF)
    }
end
```

### Engine Hours Maintenance Tracking

Track maintenance intervals:

```openhab
// Items
Number:Time Vehicle_Hours "Engine Hours [%.1f h]" 
    {channel="traccar:device:myserver:car1:hours", unit="h"}
Number:Time Last_Service_Hours "Last Service At [%.1f h]"
Number:Time Next_Service_Hours "Next Service At [%.1f h]"

// Rule
rule "Check Maintenance Due"
when
    Item Vehicle_Hours received update
then
    val currentHours = (Vehicle_Hours.state as QuantityType<Time>).toUnit("h").doubleValue()
    val lastService = (Last_Service_Hours.state as QuantityType<Time>).toUnit("h").doubleValue()
    val hoursSinceService = currentHours - lastService
    
    if (hoursSinceService >= 50) {  // Service every 50 hours
        logWarn("Maintenance", "Service due! Hours since last: {}", hoursSinceService)
        sendNotification("admin@example.com", 
            String::format("Vehicle maintenance due: %.1f hours since service", hoursSinceService))
        
        Maintenance_Due.postUpdate(ON)
        
        // Calculate next service
        Next_Service_Hours.postUpdate(new QuantityType(currentHours + 50, "h"))
    }
end

rule "Record Service Completed"
when
    Item Service_Completed_Button received command ON
then
    val currentHours = Vehicle_Hours.state as QuantityType<Time>
    Last_Service_Hours.postUpdate(currentHours)
    Next_Service_Hours.postUpdate(currentHours.add(new QuantityType(50, "h")))
    Maintenance_Due.postUpdate(OFF)
    
    logInfo("Maintenance", "Service recorded at {} hours", currentHours)
    sendNotification("admin@example.com", "Vehicle service logged")
end
```

### Event Code Monitoring

Track device-specific events (Teltonika example):

```openhab
rule "Monitor Vehicle Events"
when
    Item Vehicle_Event received update
then
    val eventCode = (Vehicle_Event.state as DecimalType).intValue()
    
    // Teltonika FMM920 event codes
    switch(eventCode) {
        case 10828: logInfo("Vehicle", "Ignition OFF")
        case 10829: logInfo("Vehicle", "Ignition ON")
        case 10831: logInfo("Vehicle", "Movement detected")
        case 10832: logInfo("Vehicle", "Harsh acceleration")
        case 10833: logInfo("Vehicle", "Harsh braking")
        case 10834: logInfo("Vehicle", "Harsh cornering")
        default: logInfo("Vehicle", "Event code: {}", eventCode)
    }
    
    // Alert on harsh driving
    if (eventCode >= 10832 && eventCode <= 10834) {
        sendNotification("admin@example.com", 
            String::format("Harsh driving detected! Event: %d", eventCode))
    }
end
```

### GPS Quality Alerting

Monitor GPS reliability:

```openhab
rule "GPS Quality Alert"
when
    Item Vehicle_Accuracy received update or
    Item Vehicle_GpsSatellites received update or
    Item Vehicle_GpsValid received update
then
    val accuracy = (Vehicle_Accuracy.state as QuantityType<Length>).toUnit("m").doubleValue()
    val satellites = (Vehicle_GpsSatellites.state as DecimalType).intValue()
    val gpsValid = Vehicle_GpsValid.state == ON
    
    var String quality = "Unknown"
    var Boolean alert = false
    
    if (!gpsValid) {
        quality = "No GPS Fix"
        alert = true
    } else if (accuracy <= 5) {
        quality = "Excellent"
    } else if (accuracy <= 15) {
        quality = "Good"
    } else if (accuracy <= 50) {
        quality = "Fair"
    } else {
        quality = "Poor"
        alert = true
    }
    
    GPS_Quality_Text.postUpdate(quality)
    
    if (alert && Vehicle_Motion.state == ON) {
        logWarn("GPS", "Poor GPS quality during movement: {} m accuracy, {} satellites", 
            accuracy, satellites)
        sendNotification("admin@example.com", 
            String::format("Poor GPS: %s (%.0f m, %d sats)", quality, accuracy, satellites))
    }
end
```

## Protocol-Specific Channel Availability

Not all channels are supported by every device protocol. Availability depends on what data your GPS tracker sends to Traccar.

### Common Protocol Capabilities

| Protocol | Position | Altitude | Valid | Distance | Odometer | Hours | Event | Activity | Satellites | GSM | Battery |
|----------|----------|----------|-------|----------|----------|-------|-------|----------|------------|-----|---------|
| **Teltonika** | ✅ | ✅ | ✅ | ✅ | ✅ (`totalDistance`) | ✅ | ✅ | ❌ | ✅ (`sat`) | ❌ | ❌ |
| **OSMand** | ✅ | ✅ | ✅ | ✅ | ✅ (`odometer`) | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **H02** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **GT06** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Traccar Client** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |

### Channel Details by Protocol

#### Teltonika (Industrial GPS Trackers)
**Example devices**: FMM920, FMB920, FMT100

**Supported channels**:
- All position/navigation channels (position, altitude, speed, course, accuracy, valid)
- Distance tracking (odometer via `totalDistance`, distance)
- Engine hours (hours in milliseconds)
- GPS satellites (sat attribute)
- Device events (event codes like 10828, 10829, 10831)
- Protocol identification

**Not supported**:
- Activity recognition (hardware limitation)
- Battery level (wired devices)
- GSM signal (not reported by most models)

**Odometer notes**: 
- Uses `totalDistance` attribute
- Binding automatically falls back to this if `odometer` is not present
- Reported in meters, auto-converted to km with `unit="km"` in item definition

**Example webhook attributes**:
```json
{
  "sat": 8,
  "event": 10831,
  "distance": 0.0,
  "totalDistance": 33279520.98,
  "motion": false,
  "hours": 861239290,
  "priority": 0
}
```

#### OSMand / Traccar Client (Mobile Apps)
**Example apps**: Traccar Client (Android/iOS), OSMand with Traccar plugin

**Supported channels**:
- All position/navigation channels
- Distance tracking (odometer attribute)
- Activity recognition (walking, in_vehicle, still, on_bicycle, on_foot)
- Battery level
- Protocol identification

**Not supported**:
- Engine hours (not applicable to phones)
- GPS satellites (not exposed by apps)
- GSM signal (not exposed by apps)
- Device events (app limitation)

**Activity recognition**: Powered by Android/iOS motion APIs, updates automatically:
- `walking` - Pedestrian movement
- `in_vehicle` - Driving/passenger in car
- `still` - Not moving
- `on_bicycle` - Cycling
- `on_foot` - Walking/running (variant of walking)
- `running` - Fast pedestrian movement

**Example webhook attributes**:
```json
{
  "batteryLevel": 85.0,
  "distance": 15.3,
  "odometer": 179924.0,
  "motion": true,
  "activity": "walking"
}
```

#### H02 / GT06 (Chinese Hardware Trackers)
**Example devices**: TK103, GT06N, Concox GT06

**Supported channels**:
- All position/navigation channels
- Distance tracking
- GPS satellites
- GSM signal strength
- Battery level
- Protocol identification

**Not supported**:
- Engine hours (not measured)
- Activity recognition (hardware limitation)
- Device events (protocol limitation)

### Protocol Attribute Mapping

The binding handles protocol differences automatically:

| Channel | Teltonika | OSMand | H02/GT06 | Fallback Behavior |
|---------|-----------|--------|----------|-------------------|
| `odometer` | `totalDistance` | `odometer` | `odometer` | Checks `odometer` first, then `totalDistance` |
| `hours` | `hours` (ms) | `hours` (ms) | ❌ | NULL if not present |
| `gpsSatellites` | `sat` | ❌ | `sat` | NULL if not present |
| `activity` | ❌ | `activity` | ❌ | NULL if not present |
| `event` | `event` | ❌ | ❌ | NULL if not present |

### Checking Your Device's Attributes

To see what data your specific device sends:

#### Via Traccar API:
```bash
curl -u "username:password" \
  "https://your-traccar-server/api/positions?deviceId=1" | python3 -m json.tool
```

Look for the `attributes` object:
```json
{
  "attributes": {
    "sat": 8,
    "motion": true,
    "distance": 0.0,
    "totalDistance": 33279520.98,
    "hours": 861239290,
    "event": 10831
  }
}
```

#### Via OpenHAB Webhook Monitor:
Run the webhook monitor script (see Webhook Configuration section) and observe what attributes appear in incoming webhooks during device movement.

#### Via OpenHAB Logs:
```bash
tail -f /var/log/openhab/openhab.log | grep "attributes"
```

### Understanding NULL States

If a channel shows `NULL`, it means your device protocol doesn't provide that data. **This is normal and expected.**

Common NULL channels by protocol:
- **Teltonika devices**: `activity`, `batteryLevel`, `gsmSignal` will be NULL
- **OSMand apps**: `gpsSatellites`, `gsmSignal`, `hours`, `event` will be NULL  
- **H02/GT06**: `hours`, `activity`, `event` will be NULL

The binding gracefully handles missing attributes - channels simply remain NULL without errors.

## Troubleshooting

### Things show OFFLINE

**Symptoms**: Bridge or device things show OFFLINE status

**Solutions**:
1. Verify Traccar URL is accessible from openHAB server:
   ```bash
   curl -u "user:pass" "https://your-traccar-server/api/devices"
   ```
2. Check username/password are correct
3. Verify firewall allows outbound HTTPS connections
4. Enable debug logging to see connection errors:
   ```
   openhab> log:set DEBUG org.openhab.binding.traccar
   ```

### No position updates

**Symptoms**: Position channels don't update, last update timestamp frozen

**Solutions**:
1. Ensure `refreshInterval` ≥ 10 seconds in bridge configuration
2. Check device is online in Traccar web interface
3. Verify device has reported position recently in Traccar
4. Check OpenHAB logs for errors:
   ```bash
   tail -f /var/log/openhab/openhab.log | grep traccar
   ```
5. Test Traccar API manually:
   ```bash
   curl -u "user:pass" "https://your-traccar-server/api/positions?deviceId=1"
   ```

### Webhooks not working

**Symptoms**: Geofence events delayed, no real-time position updates

**Solutions**:

1. **Test webhook endpoint locally**:
   ```bash
   curl -X POST http://localhost:8090/webhook \
     -H "Content-Type: application/json" \
     -d '{"position":{"deviceId":1}}'
   ```
   Should return `200 OK`

2. **Check OpenHAB webhook server**:
   ```bash
   tail -f /var/log/openhab/openhab.log | grep webhook
   ```
   Should see: `Webhook server started on port 8090`

3. **Verify firewall allows incoming connections**:
   ```bash
   sudo ufw status
   sudo ufw allow 8090/tcp  # If blocked
   ```

4. **Test from Traccar server** (if self-hosted):
   ```bash
   curl -X POST http://OPENHAB_IP:8090/webhook \
     -H "Content-Type: application/json" \
     -d '{"position":{"deviceId":1}}'
   ```

5. **Check Traccar configuration** (`traccar.xml`):
   ```xml
   <entry key='forward.enable'>true</entry>
   <entry key='forward.url'>http://OPENHAB_IP:8090/webhook</entry>
   <entry key='forward.type'>json</entry>
   ```

6. **Restart Traccar** after configuration changes:
   ```bash
   sudo systemctl restart traccar
   ```

7. **Use webhook monitor** to debug (see Webhook Configuration section)

### Odometer shows huge numbers or wrong units

**Symptoms**: Odometer displays `33279520 m` instead of `33,279.5 km`

**Solution**: Add `unit="km"` metadata to item definition:
```openhab
Number:Length Vehicle_Odometer "Odometer [%.1f km]" 
    {channel="traccar:device:myserver:car1:odometer", unit="km"}
```

OpenHAB will automatically convert meters (from Traccar) to kilometers for display.

**How it works**:
1. Traccar sends: `33279520.98` meters
2. Binding stores in base unit (meters): `QuantityType(33279520.98, SIUnits.METRE)`
3. Item metadata `unit="km"` tells OpenHAB to convert for display
4. UI shows: `33,279.5 km`

### Some channels always show NULL

**Symptoms**: Channels like `activity`, `hours`, `event` never have values

**This is normal!** Not all channels are supported by every protocol.

**Common NULL channels**:
- **Teltonika devices**: `activity`, `batteryLevel` (wired devices don't have battery)
- **OSMand apps**: `gpsSatellites`, `hours`, `event` (apps don't expose this data)
- **All protocols**: `activity` only works with OSMand/Traccar Client apps

**Solutions**:
1. Check "Protocol-Specific Channel Availability" section above
2. Verify your device sends this data:
   ```bash
   curl -u "user:pass" "https://your-traccar/api/positions?deviceId=1" | grep attributes
   ```
3. Only use channels that your device protocol supports

### GPS Valid shows OFF but position updates

**This is normal for some situations:**
- Device is indoors (parking garage, covered area)
- Device uses cell tower triangulation instead of GPS
- Device has lost GPS lock but still reports last-known position

**The `valid` channel indicates**:
- `ON` - GPS has current satellite fix, position is accurate
- `OFF` - Position is estimated/cached, may be inaccurate

**Solution**: Use GPS Valid status to determine position reliability:
```openhab
rule "Check GPS Quality"
when
    Item Vehicle_GpsValid changed to OFF
then
    logWarn("GPS", "Vehicle position is estimated - GPS fix lost")
    // Don't trigger automations based on position
end
```

### Activity recognition not working

**Symptoms**: `activity` channel always NULL

**Requirements**:
- Only works with **OSMand** or **Traccar Client** mobile apps
- Does NOT work with hardware GPS trackers (Teltonika, H02, GT06, etc.)
- Requires device motion sensors (accelerometer, gyroscope)

**Solutions**:
1. Verify you're using OSMand or Traccar Client app
2. Check app permissions allow motion sensor access
3. Enable activity recognition in app settings
4. Hardware trackers will never support this - use `motion` channel instead

### Engine hours showing wrong values

**Symptoms**: Hours displays `861239290` instead of `239.2 h`

**Cause**: Traccar sends engine hours in **milliseconds**, binding must convert to hours.

**Solution**: This should be automatic. If not working:
1. Verify channel is defined correctly in items:
   ```openhab
   Number:Time Vehicle_Hours "Engine Hours [%.1f h]" 
       {channel="traccar:device:myserver:car1:hours", unit="h"}
   ```
2. Check binding logs for conversion:
   ```bash
   tail -f /var/log/openhab/openhab.log | grep "Engine hours"
   ```
   Should see: `Engine hours: 861239290.0 ms = 239.23 hours`

### Webhook monitor shows data but openHAB doesn't update

**Symptoms**: Webhook monitor receives data, but channels don't update

**Solutions**:
1. **Check device ID matches** between Traccar and openHAB thing configuration
2. **Verify thing is ONLINE**:
   ```bash
   curl http://localhost:8080/rest/things/traccar:device:myserver:car1
   ```
3. **Enable debug logging**:
   ```
   openhab> log:set DEBUG org.openhab.binding.traccar
   ```
   Should see: `Processing webhook position update` or `Processing webhook event type: geofenceEnter`
4. **Check JSON structure** - webhook must contain `position` and `device` objects

### Getting more help

**Enable full debug logging**:
```
openhab> log:set TRACE org.openhab.binding.traccar
```

**Collect diagnostic information**:
```bash
# Check bridge status
curl http://localhost:8080/rest/things/traccar:server:myserver

# Check device status  
curl http://localhost:8080/rest/things/traccar:device:myserver:car1

# Check item states
curl http://localhost:8080/rest/items/Vehicle_Position
curl http://localhost:8080/rest/items/Vehicle_Odometer

# Test Traccar API
curl -u "user:pass" "https://your-traccar/api/devices"
curl -u "user:pass" "https://your-traccar/api/positions?deviceId=1"

# Check webhook endpoint
curl -X POST http://localhost:8090/webhook -d '{"test":true}'

# View recent logs
tail -n 100 /var/log/openhab/openhab.log | grep -i traccar
```

## Support

- **Author**: Nanna Agesen
- **Email**: Nanna@agesen.dk
- **GitHub**: [@Prinsessen](https://github.com/Prinsessen)
- **More Examples**: See [EXAMPLES.md](EXAMPLES.md)

## License

Eclipse Public License 2.0 (EPL-2.0)
