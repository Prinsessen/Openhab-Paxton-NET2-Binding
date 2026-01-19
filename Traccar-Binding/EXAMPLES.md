# Traccar Binding Examples

Complete working examples for the Traccar binding.

## Author
**Nanna Agesen** (Nanna@agesen.dk / @Prinsessen)

---

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Geofencing Examples](#geofencing-examples)
3. [Presence Detection](#presence-detection)
4. [Speed Monitoring](#speed-monitoring)
5. [Battery Alerts](#battery-alerts)
6. [Distance Tracking](#distance-tracking)
7. [Multi-Vehicle Tracking](#multi-vehicle-tracking)
8. [GPS Signal and Connectivity Monitoring](#gps-signal-and-connectivity-monitoring)

---

## Basic Setup

### Minimal Configuration

**traccar.things:**
```openhab
Bridge traccar:server:demo "Traccar Demo Server" [
    url="https://demo.traccar.org",
    username="demo@example.com",
    password="demo123"
] {
    Thing device mycar "My Car" [ deviceId=1 ]
}
```

**traccar.items:**
```openhab
Group gMyCar "My Car" <car>

Location MyCar_Position "Position" (gMyCar) 
    {channel="traccar:device:demo:mycar:position"}

Number:Speed MyCar_Speed "Speed [%.1f km/h]" (gMyCar) 
    {channel="traccar:device:demo:mycar:speed"}

String MyCar_Status "Status [%s]" (gMyCar) 
    {channel="traccar:device:demo:mycar:status"}
```

**traccar.sitemap:**
```openhab
sitemap traccar label="My Car" {
    Frame {
        Mapview item=MyCar_Position height=8
        Text item=MyCar_Speed
        Text item=MyCar_Status
    }
}
```

---

## Geofencing Examples

### Automatic Garage Door

**Requirements:**
- Geofence ID 1 = "Home Garage"
- Garage door item: `GarageDoor_Control`
- Garage door sensors: `GarageDoor_TopStop`, `GarageDoor_BottomStop`

**traccar.items:**
```openhab
String MyCar_GeofenceEvent "Event [%s]" 
    {channel="traccar:device:demo:mycar:geofenceEvent"}

Number MyCar_GeofenceId "Geofence ID" 
    {channel="traccar:device:demo:mycar:geofenceId"}

String MyCar_GeofenceName "Geofence [%s]" 
    {channel="traccar:device:demo:mycar:geofenceName"}

Switch GarageDoor_Control "Garage Door"
Contact GarageDoor_TopStop "Top Sensor [%s]" <door>
Contact GarageDoor_BottomStop "Bottom Sensor [%s]" <door>
```

**garage.rules:**
```openhab
rule "Open Garage on Arrival"
when
    Item MyCar_GeofenceEvent changed to "geofenceEnter"
then
    val geofenceId = (MyCar_GeofenceId.state as Number).intValue()
    
    // Check if entering home garage (ID=1) and door is closed
    if (geofenceId == 1 && 
        GarageDoor_TopStop.state == CLOSED && 
        GarageDoor_BottomStop.state == OPEN) {
        
        logInfo("Garage", "Car arriving, opening garage door")
        GarageDoor_Control.sendCommand(ON)
    }
end

rule "Close Garage on Departure"
when
    Item MyCar_GeofenceEvent changed to "geofenceExit"
then
    val geofenceId = (MyCar_GeofenceId.state as Number).intValue()
    
    // Check if leaving home garage (ID=1) and door is open
    if (geofenceId == 1 && 
        GarageDoor_TopStop.state == OPEN && 
        GarageDoor_BottomStop.state == CLOSED) {
        
        logInfo("Garage", "Car leaving, closing garage door")
        GarageDoor_Control.sendCommand(OFF)
    }
end
```

### Welcome Home Automation

```openhab
rule "Welcome Home"
when
    Item MyCar_GeofenceEvent changed to "geofenceEnter"
then
    val geofenceId = (MyCar_GeofenceId.state as Number).intValue()
    
    if (geofenceId == 1) { // Home geofence
        logInfo("HomeAutomation", "Welcome home!")
        
        // Turn on entry lights
        EntryLight.sendCommand(ON)
        LivingRoomLight.sendCommand(50) // 50% brightness
        
        // Disable security system
        AlarmSystem.sendCommand("DISARM")
        
        // Adjust climate
        Thermostat_SetPoint.sendCommand(21.5)
        
        // Turn off lights after 10 minutes
        createTimer(now.plusMinutes(10), [ |
            EntryLight.sendCommand(OFF)
        ])
    }
end
```

---

## Presence Detection

### Family Presence Tracking

**traccar.items:**
```openhab
Group gPresence "Family Presence"

// Dad's Car
Number DadCar_GeofenceId {channel="traccar:device:server:dadcar:geofenceId"}
String DadCar_Status {channel="traccar:device:server:dadcar:status"}

// Mom's Car  
Number MomCar_GeofenceId {channel="traccar:device:server:momcar:geofenceId"}
String MomCar_Status {channel="traccar:device:server:momcar:status"}

// Calculated presence
String Dad_Presence "Dad [%s]" (gPresence)
String Mom_Presence "Mom [%s]" (gPresence)
String Home_Occupancy "Home Status [%s]"
```

**presence.rules:**
```openhab
rule "Update Dad Presence"
when
    Item DadCar_GeofenceId changed or
    Item DadCar_Status changed
then
    val geofenceId = (DadCar_GeofenceId.state as Number)?.intValue() ?: -1
    val status = DadCar_Status.state?.toString() ?: "unknown"
    
    if (geofenceId == 1 && status == "online") {
        Dad_Presence.postUpdate("HOME")
    } else if (geofenceId == 2) { // Office geofence
        Dad_Presence.postUpdate("WORK")
    } else if (status == "online") {
        Dad_Presence.postUpdate("AWAY")
    } else {
        Dad_Presence.postUpdate("OFFLINE")
    }
end

rule "Update Mom Presence"
when
    Item MomCar_GeofenceId changed or
    Item MomCar_Status changed
then
    val geofenceId = (MomCar_GeofenceId.state as Number)?.intValue() ?: -1
    val status = MomCar_Status.state?.toString() ?: "unknown"
    
    if (geofenceId == 1 && status == "online") {
        Mom_Presence.postUpdate("HOME")
    } else if (geofenceId == 2) {
        Mom_Presence.postUpdate("WORK")
    } else if (status == "online") {
        Mom_Presence.postUpdate("AWAY")
    } else {
        Mom_Presence.postUpdate("OFFLINE")
    }
end

rule "Calculate Home Occupancy"
when
    Item Dad_Presence changed or
    Item Mom_Presence changed
then
    val dadHome = Dad_Presence.state?.toString() == "HOME"
    val momHome = Mom_Presence.state?.toString() == "HOME"
    
    if (dadHome && momHome) {
        Home_Occupancy.postUpdate("EVERYONE_HOME")
    } else if (dadHome || momHome) {
        Home_Occupancy.postUpdate("SOMEONE_HOME")
    } else {
        Home_Occupancy.postUpdate("EMPTY")
    }
end

rule "Home Security Mode"
when
    Item Home_Occupancy changed
then
    switch (Home_Occupancy.state?.toString()) {
        case "EMPTY": {
            logInfo("Security", "House empty - enabling away mode")
            Thermostat_Mode.sendCommand("ECO")
            AlarmSystem.sendCommand("ARM_AWAY")
            AllLights.sendCommand(OFF)
        }
        case "SOMEONE_HOME": {
            logInfo("Security", "Someone home - partial arm")
            Thermostat_Mode.sendCommand("COMFORT")
            AlarmSystem.sendCommand("ARM_STAY")
        }
        case "EVERYONE_HOME": {
            logInfo("Security", "Everyone home - disarmed")
            AlarmSystem.sendCommand("DISARM")
        }
    }
end
```

---

## Speed Monitoring

### Speed Alert System

```openhab
rule "Speed Alert - Excessive Speed"
when
    Item MyCar_Speed changed
then
    val speedKmh = (MyCar_Speed.state as QuantityType<Speed>).toUnit("km/h")?.doubleValue() ?: 0
    
    if (speedKmh > 130) {
        logWarn("SpeedMonitor", "ALERT: Vehicle exceeding 130 km/h - Current: {} km/h", speedKmh)
        
        // Send notification
        val message = String::format("Speed Alert: %.0f km/h at %s", 
            speedKmh, 
            MyCar_Address.state?.toString() ?: "unknown location")
        
        sendNotification("parent@example.com", message)
        
        // Flash warning light
        SpeedWarningLight.sendCommand(ON)
        createTimer(now.plusSeconds(30), [ |
            SpeedWarningLight.sendCommand(OFF)
        ])
    }
end

rule "Teen Driver Monitoring"
when
    Item TeenCar_Speed changed
then
    val speedKmh = (TeenCar_Speed.state as QuantityType<Speed>).toUnit("km/h")?.doubleValue() ?: 0
    val speedLimit = 90 // km/h
    
    if (speedKmh > speedLimit) {
        logInfo("TeenDriver", "Speed limit exceeded: {} km/h (limit: {})", speedKmh, speedLimit)
        
        // Log violation
        TeenDriver_Violations.sendCommand(INCREASE)
        
        // Notify parents
        sendNotification("parents@example.com", 
            String::format("Teen driver speeding: %.0f km/h", speedKmh))
    }
end
```

---

## Battery Alerts

### Low Battery Monitoring

```openhab
Number:Dimensionless MyCar_Battery "Battery [%.0f %%]" 
    {channel="traccar:device:demo:mycar:batteryLevel"}

rule "Low Battery Alert"
when
    Item MyCar_Battery changed
then
    val batteryPercent = (MyCar_Battery.state as DecimalType).intValue()
    
    if (batteryPercent < 20) {
        logWarn("Battery", "GPS tracker battery low: {}%", batteryPercent)
        
        // Send push notification
        sendNotification("owner@example.com", 
            String::format("GPS tracker battery low: %d%%", batteryPercent))
        
        // Visual indicator
        BatteryWarningLight.sendCommand(ON)
    } else if (batteryPercent >= 20) {
        BatteryWarningLight.sendCommand(OFF)
    }
end
```

---

## Distance Tracking

### Understanding Distance Channels

The Traccar binding provides three separate distance channels to accommodate different tracking protocols and use cases:

**1. `odometer` - Device Odometer (OSMand Protocol)**
- Available only for OSMand protocol (phone tracking apps)
- Contains the distance value reported by the tracking app
- Example: 347.8 km (distance tracked by phone app)

**2. `totalDistance` - Server Cumulative Distance (All Protocols)**
- Available for all protocols (Teltonika, OSMand, etc.)
- Cumulative distance calculated by Traccar server
- For Teltonika devices: Contains actual vehicle odometer value
- For OSMand devices: Contains server-calculated total (may be very high)

**3. `distance` - Trip Distance (All Protocols)**
- Distance since last position update
- Used for real-time trip tracking
- Example: 15.3 m (distance moved in last update)

### Protocol-Specific Examples

#### Teltonika Vehicle Tracker (Motorcycle/Car)

```openhab
// Use totalDistance for actual vehicle odometer
Number:Length Springfield_TotalDistance "Odometer [%.1f km]" 
    {channel="traccar:device:gpsserver:motorcycle:totalDistance", unit="km"}

Number:Length Springfield_Trip "Trip Distance [%.1f m]" 
    {channel="traccar:device:gpsserver:motorcycle:distance"}
```

**Why totalDistance?** Teltonika devices send the actual vehicle odometer value in the `totalDistance` field. This gives you the real motorcycle/car odometer reading (e.g., 33,280 km).

#### OSMand Phone Tracker

```openhab
// Use odometer for device-reported distance
Number:Length Phone_Odometer "Distance (Device) [%.1f km]" 
    {channel="traccar:device:gpsserver:phone:odometer", unit="km"}

// Optionally also track server cumulative (usually very high)
Number:Length Phone_TotalDistance "Total (Server) [%.1f km]" 
    {channel="traccar:device:gpsserver:phone:totalDistance", unit="km"}

Number:Length Phone_Trip "Trip Distance [%.1f m]" 
    {channel="traccar:device:gpsserver:phone:distance"}
```

**Why odometer?** OSMand apps report their own distance tracking in the `odometer` field. This is the actual distance tracked by the phone (e.g., 347.8 km). The `totalDistance` field contains Traccar's cumulative calculation which can be unrealistically high (e.g., 190,021 km).

### Daily Odometer Reset

```openhab
// Choose appropriate channel based on your device protocol
Number:Length MyCar_TotalDistance "Total Distance [%.1f km]" 
    {channel="traccar:device:demo:mycar:totalDistance", unit="km"}

Number:Length MyCar_DailyDistance "Today [%.1f km]"
Number:Length MyCar_MonthlyDistance "This Month [%.1f km]"

rule "Reset Daily Distance at Midnight"
when
    Time cron "0 0 0 * * ?" // Every day at midnight
then
    MyCar_DailyDistance.postUpdate(0|km)
    logInfo("Odometer", "Daily distance reset")
end

rule "Reset Monthly Distance"
when
    Time cron "0 0 0 1 * ?" // First day of month at midnight
then
    MyCar_MonthlyDistance.postUpdate(0|km)
    logInfo("Odometer", "Monthly distance reset")
end

rule "Update Daily Distance"
when
    Item MyCar_TotalDistance changed
then
    val currentOdo = MyCar_TotalDistance.state as QuantityType<Length>
    val dailyStart = MyCar_DailyDistance.state as QuantityType<Length>
    
    // Calculate distance driven today
    val dailyDist = currentOdo.subtract(dailyStart)
    MyCar_DailyDistance.postUpdate(dailyDist)
    
    // Maintenance reminder
    if (dailyDist.toUnit("km").doubleValue() > 500) {
        logInfo("Maintenance", "Daily distance exceeds 500 km - check vehicle")
    }
end
```

---

## Multi-Vehicle Tracking

### Fleet Management

**fleet.things:**
```openhab
Bridge traccar:server:fleet "Fleet Tracker" [
    url="https://fleet.traccar.org",
    username="fleet@company.com",
    password="fleetpass123",
    refreshInterval=30
] {
    Thing device truck1 "Truck #1" [ deviceId=101 ]
    Thing device truck2 "Truck #2" [ deviceId=102 ]
    Thing device truck3 "Truck #3" [ deviceId=103 ]
    Thing device van1 "Van #1" [ deviceId=201 ]
}
```

**fleet.items:**
```openhab
Group gFleet "Fleet Vehicles" <car>
Group gTrucks "Trucks" (gFleet)
Group gVans "Vans" (gFleet)

// Truck 1
Location Truck1_Position (gTrucks) {channel="traccar:device:fleet:truck1:position"}
String Truck1_Status (gTrucks) {channel="traccar:device:fleet:truck1:status"}
Switch Truck1_Motion (gTrucks) {channel="traccar:device:fleet:truck1:motion"}

// Truck 2
Location Truck2_Position (gTrucks) {channel="traccar:device:fleet:truck2:position"}
String Truck2_Status (gTrucks) {channel="traccar:device:fleet:truck2:status"}
Switch Truck2_Motion (gTrucks) {channel="traccar:device:fleet:truck2:motion"}

// Fleet statistics
Number Fleet_VehiclesOnline "Online [%d vehicles]"
Number Fleet_VehiclesMoving "Moving [%d vehicles]"
```

**fleet.rules:**
```openhab
rule "Update Fleet Statistics"
when
    Item Truck1_Status changed or
    Item Truck2_Status changed or
    Item Truck3_Status changed or
    Item Van1_Status changed
then
    var onlineCount = 0
    
    if (Truck1_Status.state?.toString() == "online") onlineCount = onlineCount + 1
    if (Truck2_Status.state?.toString() == "online") onlineCount = onlineCount + 1
    if (Truck3_Status.state?.toString() == "online") onlineCount = onlineCount + 1
    if (Van1_Status.state?.toString() == "online") onlineCount = onlineCount + 1
    
    Fleet_VehiclesOnline.postUpdate(onlineCount)
    
    // Alert if vehicles offline
    if (onlineCount < 4) {
        logWarn("Fleet", "Some vehicles offline: {} of 4", onlineCount)
    }
end

rule "Track Active Vehicles"
when
    Item Truck1_Motion changed or
    Item Truck2_Motion changed or
    Item Truck3_Motion changed or
    Item Van1_Motion changed
then
    var movingCount = 0
    
    if (Truck1_Motion.state == ON) movingCount = movingCount + 1
    if (Truck2_Motion.state == ON) movingCount = movingCount + 1
    if (Truck3_Motion.state == ON) movingCount = movingCount + 1
    if (Van1_Motion.state == ON) movingCount = movingCount + 1
    
    Fleet_VehiclesMoving.postUpdate(movingCount)
    
    logInfo("Fleet", "{} vehicles currently moving", movingCount)
end
```

---

## Advanced: Custom Map Dashboard

**HTML file** (`/etc/openhab/html/fleet_map.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <title>Fleet Tracker</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 600px; }
    </style>
</head>
<body>
    <h1>Fleet Vehicles</h1>
    <div id="map"></div>
    
    <script>
        // Initialize map
        const map = L.map('map').setView([56.0, 10.0], 8);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        // Fetch vehicle positions from openHAB REST API
        async function updateVehicles() {
            const response = await fetch('/rest/items/gFleet?recursive=true');
            const data = await response.json();
            
            // Parse and display on map
            // Add markers for each vehicle
        }
        
        updateVehicles();
        setInterval(updateVehicles, 10000); // Update every 10 seconds
    </script>
</body>
</html>
```

**Sitemap integration:**
```openhab
sitemap fleet label="Fleet Management" {
    Frame label="Fleet Map" {
        Webview url="/static/fleet_map.html" height=15
    }
    Frame label="Vehicle Status" {
        Text item=Fleet_VehiclesOnline
        Text item=Fleet_VehiclesMoving
    }
}
```

---

## GPS Signal and Connectivity Monitoring

### Poor GPS Signal Alert

Monitor GPS satellite count and alert when signal is weak.

**traccar.items:**
```openhab
Number Vehicle_GpsSatellites "GPS Satellites [%d]" <network>
    {channel="traccar:device:server:car:gpsSatellites"}

Number:Dimensionless Vehicle_GsmSignal "GSM Signal [%.0f %%]" <qualityofservice>
    {channel="traccar:device:server:car:gsmSignal"}

Switch Vehicle_Motion "Motion" 
    {channel="traccar:device:server:car:motion"}

String GPS_SignalQuality "GPS Quality [%s]"
String Vehicle_Alert "Alert [%s]"
```

**signal_monitor.rules:**
```openhab
rule "Monitor GPS Signal Quality"
when
    Item Vehicle_GpsSatellites changed
then
    val satellites = (Vehicle_GpsSatellites.state as Number)?.intValue() ?: 0
    
    if (satellites >= 8) {
        GPS_SignalQuality.postUpdate("EXCELLENT")
    } else if (satellites >= 5) {
        GPS_SignalQuality.postUpdate("GOOD")
    } else if (satellites >= 3) {
        GPS_SignalQuality.postUpdate("POOR")
    } else if (satellites > 0) {
        GPS_SignalQuality.postUpdate("WEAK")
    } else {
        GPS_SignalQuality.postUpdate("NO_SIGNAL")
    }
end

rule "Alert on Poor GPS While Moving"
when
    Item GPS_SignalQuality changed to "POOR" or
    Item GPS_SignalQuality changed to "WEAK"
then
    if (Vehicle_Motion.state == ON) {
        logWarn("GPSMonitor", "Poor GPS signal while vehicle is moving!")
        Vehicle_Alert.postUpdate("WEAK_GPS_SIGNAL")
        
        // Send notification (requires notification binding)
        // sendNotification("user@example.com", "Vehicle has weak GPS signal")
    }
end

rule "Alert on Low GSM Signal"
when
    Item Vehicle_GsmSignal changed
then
    val signal = (Vehicle_GsmSignal.state as QuantityType<?>)?.doubleValue() ?: 0.0
    
    if (signal < 25.0 && signal > 0.0) {
        logWarn("GSMMonitor", "Low GSM signal: " + signal + "%")
        Vehicle_Alert.postUpdate("WEAK_GSM_SIGNAL")
    }
end
```

### Device Health Dashboard

**traccar.items:**
```openhab
// Vehicle 1
Number Vehicle1_GpsSatellites "GPS Sats [%d]" 
    {channel="traccar:device:server:vehicle1:gpsSatellites"}
Number:Dimensionless Vehicle1_GsmSignal "GSM [%.0f %%]" 
    {channel="traccar:device:server:vehicle1:gsmSignal"}
Number:Dimensionless Vehicle1_BatteryLevel "Battery [%.0f %%]" 
    {channel="traccar:device:server:vehicle1:batteryLevel"}
Number:Length Vehicle1_Accuracy "Accuracy [%.1f m]" 
    {channel="traccar:device:server:vehicle1:accuracy"}

// Vehicle 2
Number Vehicle2_GpsSatellites "GPS Sats [%d]" 
    {channel="traccar:device:server:vehicle2:gpsSatellites"}
Number:Dimensionless Vehicle2_GsmSignal "GSM [%.0f %%]" 
    {channel="traccar:device:server:vehicle2:gsmSignal"}
Number:Dimensionless Vehicle2_BatteryLevel "Battery [%.0f %%]" 
    {channel="traccar:device:server:vehicle2:batteryLevel"}
```

**health.sitemap:**
```openhab
sitemap health label="Device Health" {
    Frame label="Vehicle 1 Health" {
        Text item=Vehicle1_GpsSatellites 
            valuecolor=[<3="red", <5="orange", >=5="green"]
        Text item=Vehicle1_GsmSignal 
            valuecolor=[<25="red", <50="orange", >=50="green"]
        Text item=Vehicle1_BatteryLevel 
            valuecolor=[<20="red", <50="orange", >=50="green"]
        Text item=Vehicle1_Accuracy
            valuecolor=[>50="red", >20="orange", <=20="green"]
    }
    Frame label="Vehicle 2 Health" {
        Text item=Vehicle2_GpsSatellites 
            valuecolor=[<3="red", <5="orange", >=5="green"]
        Text item=Vehicle2_GsmSignal 
            valuecolor=[<25="red", <50="orange", >=50="green"]
        Text item=Vehicle2_BatteryLevel 
            valuecolor=[<20="red", <50="orange", >=50="green"]
    }
}
```

### Protocol-Specific Considerations

**Note**: GPS satellites and GSM signal availability depends on your device protocol:

- **Teltonika trackers**: Report GPS satellites (`sat`) but typically not GSM signal
- **OSMand/phone apps**: Usually don't report satellites or signal strength
- **H02/GT06 trackers**: Often report both satellites and signal strength
- **Check your data**: Use Traccar API to see what attributes your device sends

```bash
# Check available attributes for your device
curl -u "user:password" "https://your-traccar/api/positions?deviceId=YOUR_DEVICE_ID" | jq '.[0].attributes'
```

---

## Nominatim Reverse Geocoding

### International Travel with English Addresses

Get clean, transliterated addresses worldwide without special characters:

**traccar.things:**
```openhab
Bridge traccar:server:global "Traccar Global" [
    url="https://gps.example.com",
    username="user@example.com",
    password="password",
    useNominatim=true,
    nominatimLanguage="en",
    geocodingCacheDistance=50
] {
    Thing device motorcycle "Springfield" [ deviceId=10 ]
    Thing device phone "Dream Catcher" [ deviceId=1 ]
}
```

**Example address output:**
- **Denmark**: `Kirkegade 50, 9460 Brovst, North Denmark Region, Denmark`
- **Greece**: `Leof. Vasilissis Sofias 2, 106 74 Athens, Attica, Greece` (not Λεωφ. Βασιλίσσης Σοφίας)
- **Russia**: `Krasnaya ploshchad 1, 109012 Moscow, Moscow, Russia` (not Красная площадь)
- **China**: `Dong Chang'an Jie, 100006 Beijing, Beijing, China` (not 东长安街)

**Benefits:**
- Consistent format: `Street number, Postcode City, Province, Country`
- No Greek, Cyrillic, Arabic, Chinese, Japanese characters
- Postal codes included
- Province/region names for better location context

### Custom Nominatim Server

Use your own Nominatim instance for higher request limits:

**traccar.things:**
```openhab
Bridge traccar:server:private "Traccar Private" [
    url="https://gps.example.com",
    username="user@example.com",
    password="password",
    useNominatim=true,
    nominatimUrl="https://nominatim.example.com",
    nominatimLanguage="en",
    geocodingCacheDistance=100
] {
    Thing device fleet1 "Fleet Vehicle 1" [ deviceId=1 ]
}
```

### Language-Specific Addresses

Get addresses in local language:

**traccar.things (Danish addresses):**
```openhab
Bridge traccar:server:denmark "Traccar Denmark" [
    url="https://gps.example.com",
    username="user@example.com",
    password="password",
    useNominatim=true,
    nominatimLanguage="da",
    geocodingCacheDistance=50
] {
    Thing device car "Family Car" [ deviceId=1 ]
}
```

**Address output**: `Kirkegade 50, 9460 Brovst, Region Nordjylland, Danmark`

**Supported languages**: `en` (English), `da` (Danish), `de` (German), `fr` (French), `es` (Spanish)

### Caching Configuration

**Aggressive caching (reduce API calls):**
```openhab
geocodingCacheDistance=200  // Reuse address within 200m radius
```

**Precise updates (frequent geocoding):**
```openhab
geocodingCacheDistance=10  // Request new address every 10m
```

**Typical scenarios:**
- **Highway driving**: 100-200m cache (addresses change slowly)
- **City driving**: 30-50m cache (frequent street changes)
- **Walking/cycling**: 10-20m cache (detailed location tracking)

---

## Speed Threshold (GPS Noise Filtering)

### Eliminate False Motion

Filter GPS signal drift and small movements (walking around house with phone):

**traccar.things:**
```openhab
Bridge traccar:server:home "Traccar Home" [
    url="https://gps.example.com",
    username="user@example.com",
    password="password",
    speedThreshold=2.0  // Default: filters walking/small movements
] {
    Thing device phone "Phone Tracker" [ deviceId=1 ]
    Thing device car "Family Car" [ deviceId=2 ]
}
```

**Result**: Speeds below 2 km/h display as 0 km/h

### Activity-Based Thresholds

**Walking/Indoor movement** (2 km/h):
```openhab
speedThreshold=2.0  // Show 0 when walking around house
```

**Cycling/Scooter** (5 km/h):
```openhab
speedThreshold=5.0  // Only show actual cycling movement
```

**Vehicle only** (10 km/h):
```openhab
speedThreshold=10.0  // Ignore parking lot creeping
```

**No filtering** (0 km/h):
```openhab
speedThreshold=0.0  // Show all speeds, including GPS drift
```

### Use Cases

- **Phone trackers**: 2 km/h (filter indoor walking)
- **Bicycle GPS**: 5 km/h (ignore pushing bike)
- **Vehicle trackers**: 2-5 km/h (standard)
- **High-precision apps**: 0 km/h (no filtering)

---

## Contact

Questions about these examples? Contact:
- **Nanna Agesen**
- Email: Nanna@agesen.dk
- GitHub: @Prinsessen
