# OpenHAB 5 Smart Home Configuration
## openhab5.agesen.dk

A comprehensive OpenHAB 2/3 smart home automation system managing heating, ventilation, energy monitoring, security, and presence detection for a Danish residence.

## 🏠 System Overview

This configuration controls a multi-zone smart home with:
- **Multi-phase energy management** with solar optimization
- **HVAC control** (Nilan ventilation + Mitsubishi heat pumps)
- **Security system** (Texecom alarm with UDP control)
- **Presence detection** (Network-based + GPS tracking + RFID)
- **PTZ camera automation**
- **Smart lighting** (Hue + Modbus-controlled)
- **Home appliances** (Dishwasher, vacuum robot)

**Location:** Kirkegade 50, Brovst, Denmark (57.0921701, 9.5245017)

---

## 📁 Architecture

### Core Components

| Directory | Purpose |
|-----------|---------|
| **items/** | Device and state definitions with channel bindings |
| **things/** | Physical device connections (Modbus, MQTT, HTTP) |
| **rules/** | Automation logic in OpenHAB DSL |
| **sitemaps/** | User interface definitions |
| **persistence/** | Data storage configuration (RRD4j for charts, InfluxDB) |
| **transform/** | Data conversion scripts (JS/MAP/JSONPATH/SCALE) |
| **html/** | Custom dashboards and embedded visualizations |
| **scripts/** | Python/shell scripts for external integrations |

### Integration Protocols

- **Modbus TCP** - Energy meters (EM24/EM111), smarthouse lighting
- **MQTT** - Mitsubishi heat pumps, Traccar GPS tracking, IoT sensors
- **HTTP/REST** - PTZ cameras, weather data, calendar integration
- **UDP** - Texecom alarm system communication

---

## 🔑 Key Features

### Energy Management System
**Files:** `items/myhouse.backup2`, `items/sma.items`, `items/Solar.items`, `rules/Solar.rules`, `rules/Bought_energy.rules`

Multi-phase monitoring with intelligent solar optimization:
- Grid consumption tracking across L1/L2/L3 phases (EM24 meter)
- SMA solar inverter integration via Modbus
- Per-phase load balancing calculations
- Automated appliance scheduling on excess solar (dishwasher, heat pump)
- Real-time energy flow visualization

**Key Items:**
```openhab
EM24_Energi_24_kW        // Total grid power
SMA_Active_Power         // Solar generation
EM24_Energy_Grid         // Net grid consumption (calculated)
```

### HVAC Control

#### Nilan Ventilation System
**Files:** `items/nilan.items`, `things/nilan.things`, `rules/nilan.rules`, `rules/nilan_highspeed.rules`

Modbus-controlled air handling unit with:
- Temperature-based fan speed automation
- Boost mode with countdown timers
- Bypass damper control for summer cooling
- Alarm monitoring and reporting
- Filter maintenance tracking

#### Mitsubishi Heat Pumps
**Files:** `items/Mitsubishi_*.items`, `things/Mitsubishi_living.things`, `rules/Mitsubishi_*.rules`

MQTT-controlled heat pumps with:
- JSON command interface
- Remote temperature sensing
- Dual setpoint system (T1/T2 modes)
- Energy consumption tracking and averaging
- Solar-powered heating optimization

**MQTT Topics:**
```
heatpump/command - Send control commands
heatpump/status  - Receive status updates
```

### Security System
**Files:** `items/Texecom.items`, `rules/Alarm.rules`, `scripts/net2.py`

Texecom alarm with UDP control:
- ARM/DISARM via timed key sequences (500ms delays required)
- Zone status monitoring
- Google Assistant integration with PIN protection
- Rate-limited LSTATUS polling to prevent flooding
- Automatic status suspension during arm/disarm operations

**Critical:** Commands must use 500ms delays between keypresses.

### Presence Detection
**Files:** `rules/Present.rules`, `items/traccar.items`

Multi-source presence system:
- Network ping detection with 5-minute grace period timer
- GPS tracking via Traccar MQTT integration
- RFID reader integration
- Presence-based automation triggers

### Access Control
**Files:** `items/paxton.items`, `scripts/Paxton/`, `rules/Paxton.rules`

Paxton Net2 door access system:
- Remote door unlock via REST API
- Token-based authentication
- Multiple location support (Kirkegade, Terndrupvej)

---

## 📊 Naming Conventions

### Item Prefixes
- `GF_` - Ground Floor (Stue Plan)
- `GC_` - Basement (Kælder)
- `GA_` - Garage
- `EM24_`, `EM111_` - Energy meter types
- `_Generated` suffix - Auto-generated chart configuration items

### Groups
All groups prefixed with `g`:
- `gNilan` - Ventilation items
- `gEnergi` - Energy monitoring
- `gHpSensor` - Heat pump sensors
- `gGF` - Ground floor rooms

### Example
```openhab
Group GF_Stue "Stue" <video> (gGF)
Number EM24_Energi_24_kW "Power [%.3f kW]" <electricity> (Energi_24) { channel="..." }
```

---

## 🔧 Configuration Patterns

### Modbus Structure
```openhab
Bridge modbus:tcp:endpoint [ host="192.168.x.x", port=502, id=1 ] {
    Bridge poller Name [ start=4000, length=37, refresh=5000, type="holding" ] {
        Thing data Device [ readStart="4000", readValueType="uint16" ]
    }
}
```

### MQTT with JSON Parsing
```openhab
Type number : temperature [ 
    stateTopic="device/status",
    transformationPattern="JSONPATH:$.roomTemperature"
]
```

### Rules Timer Management
Always cancel existing timers before creating new ones:
```openhab
var Timer myTimer = null
if(myTimer != null && !myTimer.hasTerminated) {
    myTimer.cancel
}
myTimer = createTimer(now.plusMinutes(5), [| /* action */ ])
```

### Transform Files
- **MAP** (`.map`) - Simple key-value mappings
- **JS** (`.js`) - JavaScript transformations (`divide100.js`, `multiply10.js`)
- **SCALE** (`.scale`) - Range-based value mapping
- **JSONPATH** - Inline JSON parsing in channel definitions

---

## 🎨 Dashboards

Custom HTML dashboards served at `/static/<filename>`:

| Dashboard | Purpose |
|-----------|---------|
| `Solar.html` | Real-time solar generation and consumption |
| `Mitsubishi.html` | Heat pump control and monitoring |
| `Ventilation.html` | Nilan system visualization |
| `WhosIn.html` | Presence detection status |
| `traccar.html` | GPS tracking map |
| `gcal.html` | Calendar integration |
| `Kampstrup_flow.html` | Water flow monitoring |

Embedded in sitemaps via:
```openhab
Webview url="/static/Solar.html" height=12
```

---

## ⚙️ Installation & Setup

### Prerequisites
- OpenHAB 2.x or 3.x
- Modbus TCP binding
- MQTT binding
- HTTP binding
- Python 3.x (for external scripts)

### Configuration Files
All configurations are in `/etc/openhab/`:

1. **Whitelisted Commands** - `misc/exec.whitelist`
   ```
   python /etc/openhab/scripts/net2.py %2$s
   ```

2. **Persistence** - `persistence/rrd4j.persist`
   - RRD4j for charts
   - InfluxDB for long-term storage

3. **Services** - `services/*.cfg`
   - Configure API endpoints
   - Set up cloud integration

### Device Setup

#### Energy Meters (Modbus)
- EM24: 192.168.x.x:502 (3-phase meter)
- EM111: Per-phase monitoring
- SMA Inverter: Solar generation data

#### Heat Pumps (MQTT)
- Broker: Configure in `things/Mqtt.things`
- Topics: `heatpump/command`, `heatpump/status`

#### Alarm System (UDP)
- Texecom panel IP configuration
- UDP commands on port 10001

---

## 🐛 Common Issues

### NULL States on Startup
**Solution:** Initialize virtual items in System started rules
```openhab
rule "System Startup"
when
    System started
then
    VirtualItem.postUpdate(0)
end
```

### Timer Persistence
Timers don't survive restarts. Reset timer-dependent items on startup.

### Modbus Timing
Use `timeBetweenTransactionsMillis` to prevent request flooding:
```openhab
Bridge modbus:tcp:endpoint [ timeBetweenTransactionsMillis=100 ]
```

### Texecom UDP
- Requires 500ms delays between commands
- Suspend LSTATUS queries during arm/disarm operations
- Commands must complete before status polling resumes

### MQTT Retained Messages
Can cause unexpected states on restart. Clear retained messages if needed:
```bash
mosquitto_pub -h broker -t topic -r -n
```

---

## 📦 Backup & Version Control

Backup locations:
- `items/Backup/` - Item file snapshots
- `rules/` - Rule backups inline
- `Deleted rules - items - things etc/` - Deprecated configurations

**Automated Backup:**
```bash
/etc/openhab/scripts/OHbackup.sh
```

**Git Repository:**
```bash
git remote: git@github.com:Prinsessen/Openhab5.1-Private.git
```

---

## 📝 Development Guidelines

### Testing Changes
```bash
# Check OpenHAB status
openhab-cli status

# Watch logs
tail -f /var/log/openhab/openhab.log
tail -f /var/log/openhab/events.log

# Test rules with named loggers
logInfo("RuleName", "Debug message")
```

### File Organization
- Active configs in root directories
- `Backup/` - Timestamped snapshots
- `Unused Item Files/` - Deprecated but kept for reference
- `Offline/` - Temporarily disabled configs

---

## 📈 Monitoring & Visualization

### RRD4j Charts
Configured in `persistence/rrd4j.persist` for:
- Temperature trends
- Energy consumption
- Solar production
- System performance

### InfluxDB Integration
Long-term data storage configured in:
- `persistence/influxdb.persist`
- `services/influxdb.cfg`

### Grafana Dashboards
Custom CSS and templates in `html/grafana/`

---

## 🌍 Language & Localization

Primary language: **Danish**
- UI labels in Danish
- Transform files support multilingual mappings (`transform/da.map`, `transform/en.map`)
- Astronomical calculations use local coordinates

---

## 📞 Integration APIs

### Weather Data
- OpenWeatherMap API
- Local weather station via HTTP

### Calendar
- Google Calendar via iCal binding
- Event-based automation triggers

### Notifications
- Telegram bot (configured but may be removed)
- System alarm notifications

---

## 🔐 Security Notes

- **Exec Whitelist:** Only whitelisted commands can run via `executeCommandLine()`
- **API Keys:** Stored in service configuration files (not in git)
- **Network Security:** Internal network only, or use VPN for remote access
- **Alarm PIN:** Protected in Google Assistant integration

---

## 📚 Additional Resources

- [OpenHAB Documentation](https://www.openhab.org/docs/)
- [Modbus Binding](https://www.openhab.org/addons/bindings/modbus/)
- [MQTT Binding](https://www.openhab.org/addons/bindings/mqtt/)
- [Rules DSL](https://www.openhab.org/docs/configuration/rules-dsl.html)

---

## 📄 License

Private configuration for personal use.

## 👤 Maintainer

Nanna Agesen (nanna@agesen.dk)

---

**Last Updated:** January 4, 2026
**OpenHAB Version:** 2.x/3.x
**Configuration Status:** Production
