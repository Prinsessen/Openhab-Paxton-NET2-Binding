# OBD-II Integration Implementation Guide

## Overview

This document details the implementation of OBD-II (On-Board Diagnostics) channels from a Bluetooth OBD-II dongle paired with a Teltonika FMM920 GPS tracker. The dongle connects to the motorcycle's diagnostic port and transmits data via the tracker to OpenHAB.

## Hardware Setup

- **Vehicle**: Motorcycle (Springfield)
- **GPS Tracker**: Teltonika FMM920 (IMEI: 866088075183606)
- **OBD-II Dongle**: Bluetooth ELM327/STN1110 compatible
- **Connection**: Dongle paired with FMM920 via Bluetooth, transmits as AVL IO parameters

## Implemented Channels

### Standard OBD-II Channels

| Channel ID | AVL ID | Description | Unit | Notes |
|------------|--------|-------------|------|-------|
| obdDtcCount | io30 | Diagnostic Trouble Codes Count | count | Number of active DTCs |
| obdEngineLoad | io31 | Calculated Engine Load | % | 0-100% |
| obdCoolantTemp | io32 | Engine Coolant Temperature | °C | Engine temperature |
| obdShortFuelTrim | io33 | Short Term Fuel Trim | % | ±10% normal range |
| obdFuelPressure | io35 | Fuel Rail Pressure | kPa | Converted to Pa internally |
| obdRpm | io36 | Engine RPM | RPM | Direct value, not Hz |
| obdSpeed | io40 | Vehicle Speed | km/h | From OBD-II |
| obdFuelLevel | io48 | Fuel Tank Level | % | **Inverted** (100 - value) |
| obdOemOdometer | - | Vehicle Odometer | km | Real odometer from CAN bus |

### Trip Meter Channels (Require FMM920 Configuration)

| Channel ID | AVL ID | Description | Unit | Configuration Required |
|------------|--------|-------------|------|----------------------|
| io199 | io199 | Trip Odometer 1 | km | Enable in FMM920 I/O settings |
| io205 | io205 | Trip Odometer 2 | km | Enable in FMM920 I/O settings |
| io389 | io389 | Total ECU Mileage | km | Enable in FMM920 I/O settings |

## Implementation Details

### 1. Channel Constants

Located in `TraccarBindingConstants.java`:

```java
// OBD-II Channels
public static final String CHANNEL_OBD_DTC_COUNT = "obdDtcCount";
public static final String CHANNEL_OBD_ENGINE_LOAD = "obdEngineLoad";
public static final String CHANNEL_OBD_COOLANT_TEMP = "obdCoolantTemp";
public static final String CHANNEL_OBD_SHORT_FUEL_TRIM = "obdShortFuelTrim";
public static final String CHANNEL_OBD_FUEL_PRESSURE = "obdFuelPressure";
public static final String CHANNEL_OBD_RPM = "obdRpm";
public static final String CHANNEL_OBD_SPEED = "obdSpeed";
public static final String CHANNEL_OBD_FUEL_LEVEL = "obdFuelLevel";
public static final String CHANNEL_OBD_OEM_ODOMETER = "obdOemOdometer";

// Trip Meters
public static final String CHANNEL_IO199 = "io199";
public static final String CHANNEL_IO205 = "io205";
public static final String CHANNEL_IO389 = "io389";
```

### 2. Channel Handlers

Located in `TraccarDeviceHandler.java`:

#### RPM Handler (Critical Fix)
```java
// io36: RPM [revolutions/min]
// IMPORTANT: Use DecimalType, NOT QuantityType with Units.RPM
// Units.RPM converts to Hz (1/60), showing 13.5 instead of 810
Object io36Obj = attributes.get("io36");
if (io36Obj instanceof Number) {
    int rpm = ((Number) io36Obj).intValue();
    updateState(CHANNEL_OBD_RPM, new DecimalType(rpm));
}
```

**Why DecimalType?** OpenHAB's `Units.RPM` represents revolutions per minute as 1/60 Hz, causing incorrect display. Using `DecimalType` preserves the raw RPM value.

#### Fuel Level Handler (Inverted)
```java
// io48: Fuel Level [%] - Inverted because bike reports fuel used, not remaining
Object io48Obj = attributes.get("io48");
if (io48Obj instanceof Number) {
    double fuelUsed = ((Number) io48Obj).doubleValue();
    double fuelRemaining = 100.0 - fuelUsed;
    updateState(CHANNEL_OBD_FUEL_LEVEL, new QuantityType<>(fuelRemaining, Units.PERCENT));
}
```

**Why Inverted?** The motorcycle ECU reports fuel consumed (14%) rather than fuel remaining. With a nearly full tank, 14% consumed = 86% remaining.

#### Fuel Pressure Handler (Unit Conversion)
```java
// io35: Fuel Pressure [kPa]
Object io35Obj = attributes.get("io35");
if (io35Obj instanceof Number) {
    double fuelPressureKpa = ((Number) io35Obj).doubleValue();
    // Convert kPa to Pa for OpenHAB (1 kPa = 1000 Pa)
    double fuelPressurePa = fuelPressureKpa * 1000;
    updateState(CHANNEL_OBD_FUEL_PRESSURE, new QuantityType<>(fuelPressurePa, SIUnits.PASCAL));
}
```

#### Trip Meters Handler (Meters to Kilometers)
```java
// io199: Trip 1 [meters]
Object io199Obj = attributes.get("io199");
if (io199Obj instanceof Number) {
    double trip1Meters = ((Number) io199Obj).doubleValue();
    updateState(CHANNEL_IO199,
        new QuantityType<>(trip1Meters / 1000.0, MetricPrefix.KILO(SIUnits.METRE)));
}
```

### 3. Channel Definitions

Located in `thing-types.xml`:

```xml
<!-- OBD-II Channels -->
<channel id="obdRpm" typeId="obd-rpm"/>
<channel id="obdFuelLevel" typeId="obd-fuel-level"/>
<channel id="obdShortFuelTrim" typeId="obd-short-fuel-trim"/>

<!-- Channel Types -->
<channel-type id="obd-rpm">
    <item-type>Number</item-type>
    <label>OBD RPM</label>
    <description>Engine RPM from OBD-II</description>
    <state readOnly="true" pattern="%d RPM"/>
</channel-type>

<channel-type id="obd-fuel-level">
    <item-type>Number:Dimensionless</item-type>
    <label>Fuel Level</label>
    <description>Fuel tank level percentage from OBD-II</description>
    <state readOnly="true" pattern="%.1f %%"/>
</channel-type>

<channel-type id="obd-short-fuel-trim">
    <item-type>Number:Dimensionless</item-type>
    <label>Short Term Fuel Trim</label>
    <description>Short term fuel trim adjustment percentage</description>
    <state readOnly="true" pattern="%.2f %%"/>
</channel-type>
```

### 4. Item Definitions

Located in `traccar.items`:

```openhab
// OBD-II Items
Number Vehicle10_ObdDtcCount "DTC Count [%d]" <error> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdDtcCount"}
Number:Dimensionless Vehicle10_ObdEngineLoad "Engine Load [%.1f %%]" <pressure> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdEngineLoad"}
Number:Temperature Vehicle10_ObdCoolantTemp "Coolant Temp [%.1f %unit%]" <temperature> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdCoolantTemp"}
Number:Dimensionless Vehicle10_ObdShortFuelTrim "Fuel Trim [JS(fuelTrim.js):%s] (%.1f %%)" <line> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdShortFuelTrim"}
Number:Pressure Vehicle10_ObdFuelPressure "Fuel Pressure [%.0f kPa]" <pressure> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdFuelPressure", unit="kPa"}
Number Vehicle10_ObdRpm "RPM" <qualityofservice> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdRpm"}
Number:Speed Vehicle10_ObdSpeed "Speed [%.0f km/h]" <speed> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdSpeed"}
Number:Dimensionless Vehicle10_ObdFuelLevel "Fuel Level [%.1f %%]" <oil> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:obdFuelLevel"}

// Trip Meters
Number:Length Vehicle10_Io199 "Trip 1 [%.1f km]" <line> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:io199", unit="km"}
Number:Length Vehicle10_Io205 "Trip 2 [%.1f km]" <line> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:io205", unit="km"}
Number:Length Vehicle10_Io389 "Total ECU Mileage [%.1f km]" <line> (gVehicle10) {channel="traccar:device:gpsserver:866088075183606:io389", unit="km"}
```

### 5. Sitemap Configuration

Located in `myhouse.sitemap`:

```openhab
Frame label="Springfield (Tracker)" {
    // ... GPS data ...
    
    Text label="OBD-II Data" {
        Frame label="Engine" {
            Text item=Vehicle10_ObdRpm label="RPM [%d]" icon="qualityofservice"
            Text item=Vehicle10_ObdEngineLoad label="Engine Load [%.1f %%]" icon="pressure"
            Text item=Vehicle10_ObdCoolantTemp label="Coolant Temp [%.1f °C]" icon="temperature"
        }
        Frame label="Fuel System" {
            Text item=Vehicle10_ObdFuelLevel label="Fuel Level [%.1f %%]" icon="oil"
            Text item=Vehicle10_ObdFuelPressure label="Fuel Pressure [%.0f kPa]" icon="pressure"
            Text item=Vehicle10_ObdShortFuelTrim icon="line"
        }
        Frame label="Diagnostics" {
            Text item=Vehicle10_ObdDtcCount label="Trouble Codes [%d]" icon="error"
            Text item=Vehicle10_ObdSpeed label="Speed [%.0f km/h]" icon="speed"
        }
        Frame label="Experimental Channels" {
            Text item=Vehicle10_Io199 label="Trip 1 [%.1f km]" icon="line"
            Text item=Vehicle10_Io205 label="Trip 2 [%.1f km]" icon="line"
            Text item=Vehicle10_Io389 label="Total ECU Mileage [%.1f km]" icon="line"
        }
    }
}
```

## Transformations

### Fuel Trim Quality Indicator

File: `transform/fuelTrim.js`

```javascript
(function(i) {
    var val = parseFloat(i);
    if (isNaN(val)) return "Unknown";
    
    var abs = Math.abs(val);
    
    if (abs <= 2) return "Perfect";
    if (abs <= 5) return "Excellent";
    if (abs <= 10) return "Good";
    if (abs <= 15) return "Monitor";
    return "Check Engine";
})(input)
```

**Usage**: Displays "Perfect (2.5 %)" instead of just "2.5 %" for better user understanding.

**Ranges**:
- **Perfect** (0-2%): Ideal fuel mixture
- **Excellent** (2-5%): Normal operation
- **Good** (5-10%): Acceptable adjustments
- **Monitor** (10-15%): Significant adjustment, check soon
- **Check Engine** (>15%): Problem detected, service needed

## Testing & Validation

### Test Data Observed

From live monitoring session (2026-01-19):

```
Engine Running (Idle):
- RPM: 803-931 RPM ✓
- Engine Load: 17-18% ✓
- Coolant Temp: 61-74°C (warming up) ✓
- Fuel Trim: 0-2.55% (Perfect/Excellent) ✓
- Fuel Pressure: 39-41 kPa ✓
- Speed: 0-5 km/h ✓
- Fuel Level: 86% (inverted from 14%) ✓

Ignition Off:
- All OBD-II channels: NULL ✓
- Power voltage drops: 14.3V → 13.9V ✓
```

### Common Issues & Solutions

#### Issue 1: RPM shows Hz (13.5 instead of 810)
**Solution**: Use `DecimalType` instead of `QuantityType<Frequency>` with `Units.RPM`

#### Issue 2: Fuel level shows 14% when tank is nearly full
**Solution**: Invert the value: `100.0 - fuelUsed`

#### Issue 3: Fuel trim shows raw percentage without context
**Solution**: Add JS transformation to display quality indicator

#### Issue 4: Trip meters not appearing
**Solution**: Enable AVL IDs 199, 205, 389 in FMM920 Configurator under I/O Settings → OBD

## FMM920 Configuration

To enable trip meters:

1. Connect to FMM920 Configurator
2. Navigate to **I/O Settings** → **OBD**
3. Enable the following AVL IDs:
   - **199**: Trip odometer 1
   - **205**: Trip odometer 2
   - **389**: Total vehicle mileage
4. Save configuration and reboot device

## Performance Considerations

- **Update Frequency**: 2-5 seconds (depends on FMM920 configuration)
- **Data Availability**: Only when ignition ON and OBD-II dongle paired
- **Battery Impact**: Minimal (dongle powered by vehicle)
- **Bandwidth**: ~50-100 bytes per update

## Future Enhancements

Potential additional channels:
- Long-term fuel trim (io34)
- Intake air temperature (io42 - currently in experimental)
- Throttle position
- O2 sensor readings
- Engine runtime hours

## References

- [Teltonika FMM920 Manual](https://wiki.teltonika-gps.com/view/FMM920)
- [OBD-II PIDs](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [OpenHAB Units of Measurement](https://www.openhab.org/docs/concepts/units-of-measurement.html)

---

**Last Updated**: 2026-01-19  
**Author**: OpenHAB Configuration Team  
**Version**: 1.0
