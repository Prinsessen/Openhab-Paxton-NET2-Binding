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

### Daily Odometer Reset

```openhab
Number:Length MyCar_Odometer "Total Distance [%.1f km]" 
    {channel="traccar:device:demo:mycar:odometer"}

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
    Item MyCar_Odometer changed
then
    val currentOdo = MyCar_Odometer.state as QuantityType<Length>
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

## Contact

Questions about these examples? Contact:
- **Nanna Agesen**
- Email: Nanna@agesen.dk
- GitHub: @Prinsessen
