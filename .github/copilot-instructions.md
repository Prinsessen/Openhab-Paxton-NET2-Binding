# OpenHAB Smart Home Configuration

This is an **OpenHAB 2/3 configuration** for a comprehensive smart home system managing heating, ventilation, energy monitoring, security, and presence detection.

## Architecture Overview

**Core Components:**
- **Items** (`items/*.items`) - State definitions and device bindings
- **Things** (`things/*.things`) - Physical device connections (Modbus, MQTT, HTTP)
- **Rules** (`rules/*.rules`) - Automation logic in OpenHAB DSL
- **Sitemaps** (`sitemaps/*.sitemap`) - UI definitions
- **Persistence** (`persistence/*.persist`) - Data storage configuration (RRD4j for charts)
- **Transforms** (`transform/`) - Data conversion scripts (JS/MAP/JSONPATH)
- **HTML** (`html/`) - Custom web dashboards and embedded visualizations

**Integration Protocols:**
- **Modbus TCP** - Primary protocol for energy meters (EM24/EM111) and smarthouse lighting
- **MQTT** - Heat pumps (Mitsubishi), GPS tracking (Traccar), IoT sensors
- **HTTP/REST** - PTZ cameras, weather stations, calendar integration
- **UDP** - Texecom alarm system communication

## Key Patterns & Conventions

### Item Naming Convention
Items follow a hierarchical naming pattern:
- `GF_` = Ground Floor (Stue Plan), `GC_` = Basement (Kælder), `GA_` = Garage
- `EM24_`, `EM111_` = Energy meter prefixes
- `_Generated` suffix = Auto-generated items for chart configuration
- Groups prefixed with `g` (e.g., `gNilan`, `gEnergi`, `gHpSensor`)

Example from `items/myhouse.items`:
```openhab
Group GF_Stue "Stue" <video> (gGF)
Number EM24_Energi_24_kW "Power [%.3f kW]" <electricity> (Energi_24)
```

### Channel Binding Syntax
Items connect to things via channel bindings:
```openhab
// Modbus with transforms
Number Light_GF_Stue { channel="modbus:data:endpointSmarthouse:Light:Light_GF_Stue:number" }

// MQTT with JSONPATH
Type number : RoomTemp [ stateTopic="heatpump/status", transformationPattern="JSONPATH:$.roomTemperature" ]
```

### Rules Structure
Rules use OpenHAB DSL with common patterns:

**Timer Management** - Cancel and recreate timers to avoid duplicates:
```openhab
var Timer presenceTimer = null
if(presenceTimer != null && !presenceTimer.hasTerminated) {
    presenceTimer.cancel
}
presenceTimer = createTimer(now.plusMinutes(5), [| /* action */ ])
```

**State Updates** - Use `postUpdate()` for virtual/calculated items, `sendCommand()` for device control:
```openhab
EM24_Energy_Grid.postUpdate((EM24_Energi_24_kW.state as DecimalType) - SMA_Active_Power.state as DecimalType)
Alarm_System_Arm_Disarm.sendCommand(ON)
```

**Energy Calculations** - Calculate averages and deltas using persistence:
```openhab
Mitsubishi_Living_Avrg_Energy.postUpdate(EM24_Energy_Grid.averageSince(now.minusMinutes(5)))
Bought_Energy.postUpdate(MeterPower.deltaSince(now.withHour(0).withMinute(0).withSecond(0)))
```

### Transform Files
Located in `transform/` - used for data conversion:
- **MAP files** (`.map`) - Simple key-value mappings (e.g., `ACMode.map`: `heat=1`)
- **JS files** (`.js`) - JavaScript transformations (`divide100.js`, `multiply10.js`)
- **SCALE files** (`.scale`) - Range-based value mapping
- **JSONPATH** - Inline in channel definitions for MQTT parsing

### Modbus Configuration
Modbus things use nested Bridge → Poller → Thing structure:

```openhab
Bridge modbus:tcp:endpointSmarthouse [ host="192.168.100.86", port=502, id=1 ] {
    Bridge poller Smarthouse_Light [ start=4000, length=37, refresh=5000, type="holding" ] {
        Thing data Light_GF_Stue [ readStart="4000", readValueType="uint16" ]
    }
}
```

### Exec Whitelist
Commands run via `executeCommandLine()` must be whitelisted in `misc/exec.whitelist`:
```
python /etc/openhab/scripts/net2.py %2$s
```
See `rules/PTZ.rules` for curl command examples.

## Critical System Integrations

### Energy Management
Multi-phase energy monitoring drives solar optimization:
- **Grid monitoring** - EM24 meter on phases L1/L2/L3
- **Solar generation** - SMA inverter via Modbus
- **Load balancing** - Rules calculate per-phase balance to optimize appliance usage
- **Smart devices** - Heat pump and dishwasher trigger on excess solar (`rules/Solar.rules`, `rules/Dishwasher_free_solar.rules`)

### HVAC Control
- **Nilan ventilation** - Modbus-controlled air handling unit with timers (`nilan.items`, `nilan.rules`)
- **Mitsubishi heat pumps** - MQTT-controlled via JSON messages with remote temperature sensing
- **Heating zones** - Dual setpoint system (T1/T2) for different operating modes

### Security System
Texecom alarm via UDP commands:
- ARM/DISARM via keyed sequences (see `rules/Texecom_Arm.rules` for timing requirements)
- Status polling via LSTATUS commands with rate limiting to prevent flooding
- Google Assistant integration with PIN protection

### Presence Detection
Network-based presence with 5-minute grace period timer (`rules/Present.rules`) combined with GPS tracking (Traccar) and RFID readers.

## Development Workflow

**Testing Configuration:**
1. Check syntax: `openhab-cli status`
2. Watch logs: `tail -f /var/log/openhab/openhab.log` and `events.log`
3. Test rules: Use log statements with named loggers: `logInfo("ruleName", "message")`

**File Organization:**
- Active configs in root directories
- `Backup/` folders contain timestamped snapshots
- `Unused Item Files/` and `Offline/` folders for deprecated configs
- `Newest Config/` appears to be staging area

**Custom Dashboards:**
HTML files in `html/` are served at `/static/<filename>` and embedded in sitemaps via Webview:
```openhab
Webview url="/static/Kampstrup_flow.html" height=12
```

## Common Issues

- **NULL states on startup** - Initialize virtual items in System started rules to avoid NULL errors
- **Timer persistence** - Timers don't survive restarts; reset timer-dependent items on startup
- **Modbus timing** - Use `timeBetweenTransactionsMillis` to prevent request flooding
- **MQTT retained messages** - Can cause unexpected state on restarts
- **Texecom UDP** - Requires 500ms delays between commands and LSTATUS query suspension during arming

## Location Context

System serves a Danish residence ("Kirkegade 50") with Danish language UI labels. Geolocation: 57.0921701,9.5245017 (Brovst area) used for astronomical calculations.
