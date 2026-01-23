# OpenHAB 5.1.0 Smart Home Configuration

**Last Auto-Update: 2026-01-23 18:30:13
## openhab5.agesen.dk

A comprehensive OpenHAB smart home automation system managing heating, ventilation, energy monitoring, security, and presence detection for a Danish residence.

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
**Files:** `items/paxton.items`, `scripts/Paxton/`, `rules/Paxton.rules`, `scripts/net2_openhab_integration.py`

Paxton Net2 door access system:
- Remote door unlock via REST API
- Token-based authentication
- Multiple location support (Kirkegade, Terndrupvej)
- **OpenHAB sync:**
        - As of 2026-01-05, the Net2/OpenHAB integration is triggered by a cron job every 30 minutes:
            ```
            */30 * * * * /usr/bin/python3 /etc/openhab/scripts/net2_openhab_integration.py --mode sync >> /var/log/net2_openhab_integration_cron.log 2>&1
            ```
        - This replaces the previous systemd service approach. The script runs once per interval and exits, ensuring no duplicate or lingering processes.
        - Output and errors are logged to `/var/log/net2_openhab_integration_cron.log`.

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

## ⚙️ System Specifications

### Software Environment
- **OpenHAB Version:** 5.1.0 (Build)
- **Operating System:** Debian GNU/Linux 13 (trixie)
- **Linux Kernel:** 6.12.57+deb13-amd64
- **Python:** 3.13.5
- **Java Runtime:** OpenJDK (bundled with OpenHAB)

### System Directories
- **OPENHAB_HOME:** `/usr/share/openhab`
- **OPENHAB_CONF:** `/etc/openhab` (this repository)
- **OPENHAB_USERDATA:** `/var/lib/openhab`
- **OPENHAB_LOGDIR:** `/var/log/openhab`
- **OPENHAB_BACKUPS:** `/var/lib/openhab/backups`

### Network Configuration
- **HTTP Interface:** http://10.0.5.21:8080
- **HTTPS Interface:** https://10.0.5.21:8443
- **Public URL:** openhab5.agesen.dk

### Installed Bindings & Add-ons
- **Modbus TCP Binding** - Industrial automation protocol for energy meters and lighting
- **MQTT Binding** - Message broker for heat pumps, sensors, and IoT devices
- **HTTP Binding** - REST API integration for cameras and external services
- **Astro Binding** - Sun/moon position calculations for automation
- **iCalendar Binding** - Google Calendar integration
- **Weather Binding** - Local weather station and forecast data
- **Hue Binding** - Philips Hue smart lighting control
- **Home Connect Binding** - BSH appliance integration (dishwasher)

### Persistence Services
- **RRD4j** - Round Robin Database for charts and graphs (default)
- **InfluxDB** - Time-series database for long-term historical data

### Transformation Services
- **JSONPATH** - JSON data extraction from MQTT/REST APIs
- **MAP** - Key-value mapping for state translations
- **SCALE** - Range-based value mapping
- **JavaScript** - Custom data transformations

---

## ⚙️ Installation & Setup

### Prerequisites
- **OpenHAB:** 5.1.0 or later
- **Operating System:** Linux (Debian 13+ recommended)
- **Python:** 3.13.5 or compatible version for external scripts
- **Java:** OpenJDK 17 or later (included with OpenHAB)
- **Network:** Static IP recommended for reliable device communication

### Required OpenHAB Bindings
Install via Paper UI (http://10.0.5.21:8080) or configure in `services/addons.cfg`:
- modbus
- mqtt
- http
- astro
- icalendar
- weather
- hue
- homeconnect

### Required Transformation Services
- jsonpath
- map
- scale
- js (JavaScript)


### Configuration Files
All configurations are in `/etc/openhab/`:

1. **Whitelisted Commands** - `misc/exec.whitelist`
    ```
    python /etc/openhab/scripts/net2.py %2$s
    ```
    Required for alarm system control via Python script execution.

2. **Net2/OpenHAB Integration Cron Job**
    - The Net2/OpenHAB sync is now triggered by a cron job (see Access Control above).
    - To edit the schedule, run `crontab -e` as the admin user.
    - Example entry:
      ```
      */30 * * * * /usr/bin/python3 /etc/openhab/scripts/net2_openhab_integration.py --mode sync >> /var/log/net2_openhab_integration_cron.log 2>&1
      ```

3. **Persistence Configuration**
    - `persistence/rrd4j.persist` - Chart generation with RRD4j Round Robin Database
    - `persistence/influxdb.persist` - Long-term time-series storage in InfluxDB
    - `services/rrd4j.cfg` - RRD4j service configuration
    - `services/influxdb.cfg` - InfluxDB connection settings

4. **Service Configuration** - `services/*.cfg`
    - `addons.cfg` - Binding and add-on management
    - `basicui.cfg` - Basic UI customization
    - `openhabcloud.cfg` - myopenHAB cloud connector settings
    - `runtime.cfg` - Runtime system properties

### Device Setup

#### Energy Meters (Modbus TCP)
- **EM24 (3-phase meter):** Modbus TCP endpoint (see `things/myhouse.things`)
- **EM111 (single-phase meters):** Per-phase monitoring
- **SMA Solar Inverter:** Modbus TCP for solar generation data (see `things/sma.things`)
- **Protocol:** Modbus TCP on port 502
- **Refresh Rate:** 5000ms (5 seconds)

#### Mitsubishi Heat Pumps (MQTT)
- **Broker Configuration:** Defined in `things/Mqtt.things`
- **Command Topic:** `heatpump/command` (JSON format)
- **Status Topic:** `heatpump/status` (JSON with JSONPATH transforms)
- **Protocol:** MQTT v3.1.1
- **Supported Units:** Living room and server room heat pumps

#### Nilan Ventilation System (Modbus TCP)
- **Configuration:** `things/nilan.things`
- **Protocol:** Modbus TCP on port 502
- **Features:** Temperature control, fan speed, bypass damper, filter monitoring

#### Texecom Alarm System (UDP)
- **Protocol:** UDP commands on port 10001
- **Python Script:** `/etc/openhab/scripts/net2.py`
- **Command Timing:** 500ms delays required between keypresses
- **Status Polling:** Rate-limited LSTATUS queries

#### Smart Lighting
- **Philips Hue:** HTTP API (see `things/hue.things`)
- **Modbus Lighting:** Smarthouse controller (see `things/smarthouse.things`)
- **Protocol:** Hue Bridge API v2, Modbus TCP

#### Other Integrations
- **PTZ Cameras:** HTTP/REST API control
- **Traccar GPS:** MQTT tracking integration
- **Weather Station:** HTTP polling (see `things/weather.things`)
- **Kamstrup Flow Meter:** Modbus TCP (see `things/kamstrup.things`)
- **Paxton Net2:** REST API for door access (see `things/paxton.things`)

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

### Backup Strategy
Multiple backup locations for different purposes:
- **items/Backup/** - Timestamped snapshots of item configuration files
- **things/Backup/** - Thing configuration backups
- **Unused Item Files/** - Deprecated but preserved for reference
- **Deleted rules - items - things etc/** - Archive of removed configurations
- **Offline/** - Temporarily disabled configurations

### System Backups
- **Location:** `/var/lib/openhab/backups/`
- **Automated Backup Script:** `/etc/openhab/scripts/OHbackup.sh`
- **Permissions:** root:root (requires elevated privileges)

### Git Version Control
- **Repository:** git@github.com:Prinsessen/Openhab5.1-Private.git
- **Branch:** main (default)
- **Configuration Path:** `/etc/openhab/` (OPENHAB_CONF)
- **Tracking:** Items, things, rules, sitemaps, transforms, HTML, scripts

### Git Workflow
```bash
# Check status
cd /etc/openhab
git status

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "Update configuration - description"

# Push to remote
git push origin main

# Pull latest changes
git pull origin main
```

**Note:** Sensitive files (API keys, passwords) are excluded via `.gitignore` and stored in `services/*.cfg`

---

## 📝 Development Guidelines

### Testing Changes
```bash
# Check OpenHAB service status
openhab-cli status

# Get detailed system information
openhab-cli info

# Watch main log (errors, warnings, info)
tail -f /var/log/openhab/openhab.log

# Watch event bus (item state changes, commands)
tail -f /var/log/openhab/events.log

# Test rules with named loggers (recommended)
logInfo("RuleName", "Debug message with value: {}", variableName)
logWarn("RuleName", "Warning message")
logError("RuleName", "Error occurred: {}", errorDetails)

# Clear Karaf cache (if strange behavior occurs)
openhab-cli clean-cache

# Restart OpenHAB service
sudo systemctl restart openhab
```

### Rule Development Best Practices
1. **Use named loggers** - Include rule name for easier troubleshooting
2. **NULL handling** - Always check for NULL states before operations
3. **Timer cleanup** - Cancel existing timers before creating new ones
4. **Persistence queries** - Use `.averageSince()`, `.deltaSince()` for historical data
5. **State vs Command** - Use `postUpdate()` for virtual items, `sendCommand()` for devices

### Debugging Modbus Issues
```bash
# Enable Modbus debug logging in Karaf console
log:set DEBUG org.openhab.binding.modbus

# Check Modbus connection status in logs
tail -f /var/log/openhab/openhab.log | grep -i modbus

# Verify network connectivity to Modbus devices
nc -zv <device-ip> 502
```

### MQTT Debugging
```bash
# Subscribe to all topics (if MQTT client installed)
mosquitto_sub -h <broker-ip> -t '#' -v

# Enable MQTT debug logging
log:set DEBUG org.openhab.binding.mqtt

# Check MQTT broker connection
tail -f /var/log/openhab/openhab.log | grep -i mqtt
```

### File Organization
- **Active configs** - Root directories (`items/`, `things/`, `rules/`, etc.)
- **Backup/** folders - Timestamped configuration snapshots
- **Unused Item Files/** - Deprecated items kept for historical reference
- **Offline/** - Temporarily disabled configurations (excluded from loading)
- **Newest Config/** - Staging area for testing new configurations

### Configuration Validation
```bash
# Validate items syntax (check for parse errors on startup)
grep -i "error.*items" /var/log/openhab/openhab.log

# Validate things syntax
grep -i "error.*things" /var/log/openhab/openhab.log

# Validate rules syntax
grep -i "error.*rules" /var/log/openhab/openhab.log

# Check for NULL pointer exceptions
grep -i "nullpointer" /var/log/openhab/openhab.log
```

---

## 📈 Monitoring & Visualization

### RRD4j Charts
Configured in `persistence/rrd4j.persist` for real-time and historical charts:
- **Temperature trends** - All thermostats and sensors
- **Energy consumption** - Grid, solar, and per-device monitoring
- **Solar production** - Generation curves and efficiency
- **System performance** - Heat pump COP, ventilation efficiency
- **Data retention:** Configurable intervals (minute, hour, day, week, month)

### InfluxDB Integration
Long-term time-series data storage:
- **Configuration:** `persistence/influxdb.persist` and `services/influxdb.cfg`
- **Database:** High-resolution metrics for extended historical analysis
- **Retention policies:** Customizable data retention periods
- **Queries:** Support for advanced analytics and reporting

### Grafana Dashboards
Custom visualization framework:
- **Templates:** `html/grafana/` directory
- **CSS Styling:** `html/grafana.light.css`
- **Integration:** Embedded via Webview in sitemaps
- **Data source:** Queries InfluxDB directly for time-series visualization

### Custom HTML Dashboards
Real-time visualization served at `/static/<filename>`:
- **Solar Dashboard** - `Solar.html` / `Solar1.html`
- **Heat Pump Monitoring** - `Mitsubishi.html` / `Mitsubishi_living.html`
- **Ventilation System** - `Ventilation.html` / `ventilator_speed.html`
- **Energy Flow** - `Heatpump_Energy.html`
- **Presence Tracking** - `WhosIn.html` / `OwnTracks*.html`
- **Calendar Integration** - `gcal.html`
- **GPS Tracking** - `traccar.html` / `map.html`
- **Water Flow** - `Kampstrup_flow.html`
- **Air Quality** - `Carbondioxide.html`

### Chart Styling
- **Shared CSS:** `charts.css` / `charts1.css`
- **Custom styles:** `Style.css` / `OMRStyles.css`
- **Responsive design:** Mobile and desktop optimized

---

## 🌍 Language & Localization

### Primary Configuration
- **Language:** Danish (da-DK)
- **UI Labels:** Danish text in sitemaps and items
- **Time Zone:** Europe/Copenhagen (CET/CEST)
- **Date Format:** DD-MM-YYYY (European standard)

### Multilingual Support
Transform files for language mappings:
- `transform/da.map` - Danish translations
- `transform/en.map` - English translations (where applicable)
- Mode and state mappings support multiple languages

### Geographic Configuration
- **Location:** Kirkegade 50, 9460 Brovst, Denmark
- **Coordinates:** 57.0921701°N, 9.5245017°E
- **Astronomical Calculations:** Used for sunrise/sunset automation triggers
- **Astro Binding:** Configured with local coordinates for sun position

---

## 📞 Integration APIs

### Weather Services
- **Provider:** OpenWeatherMap API
- **Configuration:** `things/weather.things`
- **Local Weather Station:** HTTP polling for hyperlocal data
- **Data Points:** Temperature, humidity, pressure, wind, precipitation

### Calendar Integration
- **Service:** Google Calendar via iCalendar binding
- **Configuration:** `things/icalendar.things`
- **Automation:** Event-based triggers for presence and scheduling
- **Dashboard:** `html/gcal.html` for calendar visualization

### GPS Tracking
- **Service:** Traccar GPS tracking platform
- **Protocol:** MQTT integration (see `items/traccar.items`)
- **Dashboards:** Multiple user-specific tracking views
  - `html/traccar.html` - Combined tracking map
  - `html/OwnTracks*.html` - Individual user tracking
  - `html/Nanna_Tracker.html` - Specific user dashboard

### Notification Services
- **Telegram Bot:** Configured in `things/Telegram.things` (may be legacy)
- **System Notifications:** Alarm events, error conditions
- **Email:** Mail binding for critical alerts (see `things/mail.things`)

### Cloud Services
- **myopenHAB Cloud:** Configured in `services/openhabcloud.cfg`
- **Remote Access:** Secure cloud connector for external access
- **Voice Assistants:** Google Assistant integration for alarm control

---

## 🔐 Security Notes

### Command Execution Security
- **Exec Whitelist:** Only commands listed in `misc/exec.whitelist` can run via `executeCommandLine()`
- **Python Scripts:** Whitelisted for alarm system control (`scripts/net2.py`)
- **Path Validation:** All script paths must be absolute and verified

### API Keys & Credentials
- **Storage:** Service configuration files in `services/*.cfg`
- **Version Control:** Excluded from git via `.gitignore`
- **Access Control:** File permissions restricted to openhab user (openhab:openhab)

### Network Security
- **Internal Network:** System designed for private network operation
- **Remote Access:** Use VPN or myopenHAB cloud connector for external access
- **HTTPS:** Enabled on port 8443 with SSL certificates
- **HTTP:** Available on port 8080 (consider disabling if not needed)

### Alarm System Security
- **Texecom Alarm:** UDP control with PIN protection
- **Google Assistant:** PIN required for disarm operations
- **Command Validation:** Rate limiting and sequence validation in rules
- **Status Monitoring:** Automated zone breach detection

### User Access Control
- **OpenHAB Users:** Managed via built-in authentication
- **RFID Access:** Door access logged and monitored (see `items/Rfid.items`)
- **Paxton Net2:** Token-based door access with audit trail
- **Presence Detection:** Multiple authentication layers (network, GPS, RFID)

### Best Practices
1. Keep OpenHAB updated to latest stable version
2. Regular security audits of whitelisted commands
3. Monitor logs for unauthorized access attempts
4. Use strong passwords for all services
5. Backup configuration regularly
6. Restrict SSH access to authorized keys only

---

## 📚 Additional Resources

### Official Documentation
- [OpenHAB Documentation](https://www.openhab.org/docs/) - Complete reference guide
- [Modbus Binding](https://www.openhab.org/addons/bindings/modbus/) - Modbus TCP/RTU configuration
- [MQTT Binding](https://www.openhab.org/addons/bindings/mqtt/) - MQTT broker and thing configuration
- [Rules DSL](https://www.openhab.org/docs/configuration/rules-dsl.html) - Scripting language reference
- [HTTP Binding](https://www.openhab.org/addons/bindings/http/) - REST API integration
- [Astro Binding](https://www.openhab.org/addons/bindings/astro/) - Astronomical calculations

### Persistence & Visualization
- [RRD4j Persistence](https://www.openhab.org/addons/persistence/rrd4j/) - Chart database
- [InfluxDB Persistence](https://www.openhab.org/addons/persistence/influxdb/) - Time-series storage
- [Grafana Integration](https://grafana.com/docs/) - Advanced visualization

### Community Resources
- [OpenHAB Community Forum](https://community.openhab.org/) - Support and discussions
- [GitHub Repository](https://github.com/openhab) - Source code and issues

### Device-Specific Documentation
- **Mitsubishi Heat Pumps:** MQTT protocol implementation
- **Texecom Alarm Systems:** UDP command protocol
- **Paxton Net2:** REST API documentation
- **Nilan Ventilation:** Modbus register mappings
- **SMA Solar Inverters:** Modbus register documentation

### System Administration
- [Debian 13 (Trixie)](https://www.debian.org/releases/trixie/) - Operating system documentation
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemctl.html) - Service control
- [Git Version Control](https://git-scm.com/doc) - Repository management

---

## 📄 License

Private configuration for personal use. Not licensed for redistribution.

## 👤 Maintainer

**Nanna Agesen**  
Email: nanna@agesen.dk  
Location: Kirkegade 50, 9460 Brovst, Denmark

---

## 📋 Document Information

**Last Updated:** January 4, 2026  
**OpenHAB Version:** 5.1.0 (Build)  
**Operating System:** Debian GNU/Linux 13 (trixie)  
**Python Version:** 3.13.5  
**Configuration Status:** Production  
**Repository:** git@github.com:Prinsessen/Openhab5.1-Private.git

---

## 🔄 Changelog

### 2026-01-04 - Version 5.1.0
- Updated to OpenHAB 5.1.0
- Migrated to Debian 13 (trixie)
- Updated Python to 3.13.5
- Enhanced documentation with precise version information
- Improved system specifications section
- Added detailed device configuration documentation

### Previous Versions
See `CHANGELOG.md` for historical changes and migration notes from OpenHAB 2.x/3.x to 5.x.
