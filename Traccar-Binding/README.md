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
- GPS coordinates (latitude, longitude, altitude)
- Speed with configurable units (km/h, mph, knots)
- Direction/course (compass bearing)
- Location accuracy
- Street address (reverse geocoding)
- Last update timestamp

### Device Information
- Battery level monitoring
- Motion detection
- Odometer/total distance traveled
- Online/offline status

### Geofencing Automation
- Real-time geofence entry/exit events via webhooks
- Geofence ID and name tracking
- Instant notifications (no polling delay)
- Perfect for automating garage doors, lights, security systems

### Dual Update Mechanism
- **Polling**: Configurable interval (minimum 10 seconds) for position updates
- **Webhooks**: Instant event notifications (geofence, device status changes)
- Efficient hybrid approach minimizes API calls while maintaining responsiveness

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

| Channel | Type | Description |
|---------|------|-------------|
| `position` | Location | GPS coordinates (lat, lon, altitude) |
| `speed` | Number:Speed | Current speed (converted to configured unit) |
| `course` | Number:Angle | Direction/heading (0-359°) |
| `accuracy` | Number:Length | GPS accuracy in meters |
| `address` | String | Street address from reverse geocoding |
| `status` | String | Device status: online/offline/unknown |
| `batteryLevel` | Number:Dimensionless | Battery level (0.0-1.0) |
| `motion` | Switch | Movement detection (ON=moving) |
| `odometer` | Number:Length | Total distance traveled |
| `lastUpdate` | DateTime | Timestamp of last update |
| `geofenceEvent` | String | geofenceEnter/geofenceExit/deviceOnline/etc |
| `geofenceId` | Number | Numeric ID of triggered geofence |
| `geofenceName` | String | Name of triggered geofence |
| `gpsSatellites` | Number | Number of GPS satellites used for positioning |
| `gsmSignal` | Number:Dimensionless | GSM/cellular signal strength (0-100%) |

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

Location FamilyCar_Position "Position" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:position"}

Number:Speed FamilyCar_Speed "Speed [%.1f %unit%]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:speed"}

Number:Angle FamilyCar_Course "Direction [%.0f °]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:course"}

String FamilyCar_Address "Address [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:address"}

Number:Dimensionless FamilyCar_Battery "Battery [%.0f %%]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:batteryLevel"}

String FamilyCar_Status "Status [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:status"}

String FamilyCar_GeofenceEvent "Event [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:geofenceEvent"}

Number FamilyCar_GeofenceId "Geofence ID" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:geofenceId"}

String FamilyCar_GeofenceName "Geofence [%s]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:geofenceName"}

Number FamilyCar_GpsSatellites "GPS Satellites [%d]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:gpsSatellites"}

Number:Dimensionless FamilyCar_GsmSignal "GSM Signal [%.0f %%]" (gFamilyCar) 
    {channel="traccar:device:myserver:car1:gsmSignal"}
```

### traccar.sitemap

```openhab
sitemap tracking label="Vehicle Tracking" {
    Frame label="Family Car" {
        Mapview item=FamilyCar_Position height=10
        Text item=FamilyCar_Speed
        Text item=FamilyCar_Course
        Text item=FamilyCar_Address
        Text item=FamilyCar_Battery
        Text item=FamilyCar_Status
        Text item=FamilyCar_GeofenceName
        Text item=FamilyCar_GpsSatellites
        Text item=FamilyCar_GsmSignal
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
```

## Webhook Configuration

For instant geofence notifications, configure webhooks in Traccar:

1. Go to **Traccar web interface** → **Settings** → **Notifications**
2. Add notification for `geofenceEnter` and `geofenceExit`
3. Select **Web Request (GET or POST)**
4. Set URL: `http://YOUR_OPENHAB_IP:8090/webhook`
5. Traccar will send events instantly to openHAB

## Speed Unit Conversion

Traccar reports speed in **knots**. The binding converts to:
- **kmh**: × 1.852
- **mph**: × 1.15078
- **knots**: no conversion

## Protocol-Specific Channel Availability

Not all channels are supported by every device protocol. Availability depends on what data your GPS tracker sends to Traccar:

### Common Protocol Limitations

| Protocol | GPS Satellites | GSM Signal | Battery | Odometer | Notes |
|----------|----------------|------------|---------|----------|-------|
| **Teltonika** | ✅ Yes | ❌ No | ❌ No | ✅ Yes | Industrial trackers, excellent GPS data |
| **OSMand** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | Phone apps (Traccar Client, GPSLogger) |
| **H02** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Chinese trackers, full feature set |
| **GT06** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Common low-cost trackers |
| **OsmAnd** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | Mobile apps (limited data) |

### Checking Available Attributes

To see what data your device sends, check the Traccar API:

```bash
curl -u "user:password" "https://your-traccar-server/api/positions?deviceId=1"
```

Look in the `attributes` object for available data:
- `sat` - GPS satellites count
- `rssi` - GSM signal strength (dBm, converted to %)
- `gsm` - GSM signal (already as percentage)
- `batteryLevel` - Battery percentage
- `motion` - Motion detection
- `odometer` - Distance traveled

**Note**: Channels will show `NULL` if your device doesn't provide that data. This is normal and protocol-dependent.

## Troubleshooting

### Things show OFFLINE

- Verify Traccar URL is accessible
- Check username/password are correct
- Test: `curl -u "user:pass" "https://your-traccar/api/devices"`

### No position updates

- Ensure `refreshInterval` ≥ 10 seconds
- Check device is online in Traccar web interface
- Enable debug logging: `log:set DEBUG org.openhab.binding.traccar`

### Webhooks not working

- Test endpoint: `curl http://localhost:8090/webhook`
- Verify firewall allows incoming connections on webhook port
- Check Traccar can reach openHAB IP address

## Support

- **Author**: Nanna Agesen
- **Email**: Nanna@agesen.dk
- **GitHub**: [@Prinsessen](https://github.com/Prinsessen)
- **More Examples**: See [EXAMPLES.md](EXAMPLES.md)

## License

Eclipse Public License 2.0 (EPL-2.0)
