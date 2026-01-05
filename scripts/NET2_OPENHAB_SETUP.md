# Paxton Net2 - OpenHAB Integration Setup

## Overview
This integration synchronizes Paxton Net2 access control system with OpenHAB, providing real-time door state monitoring, user presence detection, and security event tracking.

## Current Status
✅ Integration script created: `/etc/openhab/scripts/net2_openhab_integration.py`  
✅ Items file generated: `/etc/openhab/items/net2.items` (7 doors, 31 users)  
⚠️  **OpenHAB restart required** to load new items

## Quick Start

### 1. Restart OpenHAB (Required)
```bash
sudo systemctl restart openhab
```

### 2. Verify Items Loaded
```bash
export OPENHAB_TOKEN=Ai
curl -s -H "Authorization: Bearer ${OPENHAB_TOKEN}" https://openhab5.agesen.dk/rest/items \
    | jq '.[] | select(.name | startswith("Net2")) | .name' | wc -l
```
Expected output: Should show ~75+ items (7 doors × 3 items + 31 users × 3 items + stats/security items)

### 3. Run Initial Sync
```bash
export OPENHAB_TOKEN=Ai
/etc/openhab/scripts/net2_openhab_integration.py --mode sync --verbose
```

This will:
- Fetch recent Net2 events (last 5 minutes)
- Update door states (OPEN/CLOSED/ACCESS_DENIED)
- Update user presence (ON/OFF)
- Update last access times

### 4. Start Continuous Monitoring (Optional)
```bash
export OPENHAB_TOKEN=Ai
/etc/openhab/scripts/net2_openhab_integration.py --mode monitor --interval 30 --verbose
```

Polls Net2 API every 30 seconds and updates OpenHAB items.

## Generated OpenHAB Items

### Door Items (3 per door)
```
Net2_Door_<DoorName>_State          // String: OPEN, CLOSED, ACCESS_GRANTED, ACCESS_DENIED
Net2_Door_<DoorName>_LastUser       // String: Last person who accessed door
Net2_Door_<DoorName>_LastUpdate     // DateTime: Timestamp of last event
```

### User Items (3 per user)
```
Net2_User_<UserName>_Present        // Switch: ON if seen in last 15 min, OFF otherwise
Net2_User_<UserName>_Location       // String: Last door accessed
Net2_User_<UserName>_LastSeen       // DateTime: Timestamp of last access
```

### Security Items
```
Net2_Security_LastEvent             // String: Description of last security event
Net2_Security_LastUser              // String: User involved in last security event
Net2_Security_LastTime              // DateTime: Timestamp of last security event
Net2_Security_AlertCount            // Number: Count of access denied events
```

### Statistics Items
```
Net2_Stats_EventCount               // Number: Total events processed
Net2_Stats_ActiveUsers              // Number: Users active in last 15 min
Net2_Stats_LastSync                 // DateTime: Last synchronization time
```

## 7 Doors in System
1. **Andreas Udv.Kælder** (ACU 01038236) → `Net2_Door_Andreas_UdvKaelder_ACU_01038236_*`
2. **Fordør** (ACU 6612642) → `Net2_Door_Fordoer_ACU_6612642_*`
3. **Fordør Porsevej** (ACU:967438) → `Net2_Door_Fordoer_Porsevej_ACU967438_*`
4. **Fordør Terndrupvej** (ACU:6203980) → `Net2_Door_Fordoer_Terndrupvej_ACU6203980_*`
5. **Garage Port** (ACU:7242929) → `Net2_Door_Garage_Port_ACU7242929_*`
6. **Værksted** (ACU 01265688) → `Net2_Door_Vaerksted_ACU_01265688_*`
7. **Værksted Dør** (Central 03962494) → `Net2_Door_Vaerksted_Doer_Central_03962494_*`

## Usage Examples

### Check Specific Door State
```bash
curl -s -H "Authorization: Bearer ${OPENHAB_TOKEN}" \
    https://openhab5.agesen.dk/rest/items/Net2_Door_Fordoer_ACU_6612642_State/state
```

### Check If User Is Present
```bash
curl -s -H "Authorization: Bearer ${OPENHAB_TOKEN}" \
    https://openhab5.agesen.dk/rest/items/Net2_User_Nanna_Sloth_Agesen_Present/state
```

### View Security Alerts
```bash
curl -s -H "Authorization: Bearer ${OPENHAB_TOKEN}" \
    https://openhab5.agesen.dk/rest/items/Net2_Security_AlertCount/state
```

## Integration Script Modes

### 1. Init Mode
Generates/regenerates the items file:
```bash
/etc/openhab/scripts/net2_openhab_integration.py --mode init
```

### 2. Sync Mode
One-time synchronization:
```bash
/etc/openhab/scripts/net2_openhab_integration.py --mode sync
```

Options:
- `--verbose` - Show detailed logging
- `--minutes N` - Fetch events from last N minutes (default: 5)

### 3. Monitor Mode
Continuous monitoring:
```bash
/etc/openhab/scripts/net2_openhab_integration.py --mode monitor --interval 30
```

Options:
- `--interval N` - Poll interval in seconds (default: 60)
- `--verbose` - Show detailed logging

## Next Steps

### Create OpenHAB Rules
Create `/etc/openhab/rules/net2.rules` to automate actions:

```openhab
rule "Net2 Access Denied Alert"
when
    Item Net2_Security_AlertCount changed
then
    val count = Net2_Security_AlertCount.state as Number
    if(count > 0) {
        val user = Net2_Security_LastUser.state.toString
        val event = Net2_Security_LastEvent.state.toString
        logWarn("Net2", "Security Alert: {} - {}", user, event)
        // Send notification, trigger alarm, etc.
    }
end

rule "Net2 User Arrived Home"
when
    Item Net2_User_Nanna_Sloth_Agesen_Present changed from OFF to ON
then
    val location = Net2_User_Nanna_Sloth_Agesen_Location.state.toString
    logInfo("Net2", "Nanna arrived at {}", location)
    // Turn on lights, adjust heating, etc.
end
```

### Create Sitemap
Add to your existing sitemap or create `/etc/openhab/sitemaps/net2.sitemap`:

```openhab
sitemap net2 label="Paxton Net2" {
    Frame label="Door Status" {
        Text item=Net2_Door_Fordoer_ACU_6612642_State
        Text item=Net2_Door_Fordoer_ACU_6612642_LastUser
        Text item=Net2_Door_Fordoer_ACU_6612642_LastUpdate
        
        Text item=Net2_Door_Garage_Port_ACU7242929_State
        Text item=Net2_Door_Garage_Port_ACU7242929_LastUser
        Text item=Net2_Door_Garage_Port_ACU7242929_LastUpdate
    }
    
    Frame label="User Presence" {
        Switch item=Net2_User_Nanna_Sloth_Agesen_Present
        Text item=Net2_User_Nanna_Sloth_Agesen_Location
        Text item=Net2_User_Nanna_Sloth_Agesen_LastSeen
    }
    
    Frame label="Security" {
        Text item=Net2_Security_LastEvent
        Text item=Net2_Security_LastUser
        Text item=Net2_Security_LastTime
        Text item=Net2_Security_AlertCount
    }
    
    Frame label="Statistics" {
        Text item=Net2_Stats_EventCount
        Text item=Net2_Stats_ActiveUsers
        Text item=Net2_Stats_LastSync
    }
}
```

### Setup as Systemd Service (Optional)
Create `/etc/systemd/system/net2-openhab-sync.service`:

```ini
[Unit]
Description=Paxton Net2 - OpenHAB Integration Monitor
After=openhab.service
Requires=openhab.service

[Service]
Type=simple
User=openhab
WorkingDirectory=/etc/openhab
ExecStart=/usr/bin/python3 /etc/openhab/scripts/net2_openhab_integration.py --mode monitor --interval 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable net2-openhab-sync
sudo systemctl start net2-openhab-sync
```

## Troubleshooting

### Items Not Loading
1. Check OpenHAB logs: `tail -f /var/log/openhab/openhab.log`
2. Verify items file syntax: Check for special characters in item names
3. Restart OpenHAB: `sudo systemctl restart openhab`

### 404 Errors When Syncing
- Means items haven't loaded yet - restart OpenHAB first

### Authentication Failures
- Check Net2 API credentials in script (around line 28-30)
- Verify API endpoint is accessible: `curl -k https://milestone.agesen.dk:8443/api/v1/authorization/tokens`

### No Events Retrieved
- Check time filter: Use `--minutes 60` to look further back
- Verify Net2 system is generating events
- Check API permissions for events endpoint

## Danish Character Handling
The script automatically converts Danish characters to ASCII equivalents:
- æ → ae
- ø → oe
- å → aa

Examples:
- "Fordør" → `Net2_Door_Fordoer_*`
- "Værksted" → `Net2_Door_Vaerksted_*`
- "Kælder" → `Net2_Door_Andreas_UdvKaelder_*`

## API Endpoints Used
- **POST /authorization/tokens** - OAuth2 authentication
- **GET /doors** - Retrieve door list
- **GET /users** - Retrieve user list
- **GET /events** - Retrieve access events

## Configuration
Edit the script to customize:
- `NET2_BASE_URL` (line ~19) - Net2 API endpoint
- `OPENHAB_URL` (line ~20) - OpenHAB REST API endpoint
- `CLIENT_ID`, `CLIENT_SECRET` (line ~28-30) - Net2 API credentials
- `PRESENCE_TIMEOUT` (line ~41) - User presence timeout (default: 15 minutes)

## Related Files
- **Integration script**: `/etc/openhab/scripts/net2_openhab_integration.py`
- **Items file**: `/etc/openhab/items/net2.items`
- **User activity script**: `/etc/openhab/scripts/net2_user_activity.py`
- **Activity reports**: `/etc/openhab/html/net2_activity.html` and `/etc/openhab/html/doors/*.html`
- **API documentation**: `/etc/openhab/scripts/PAXTON_NET2_API_ANALYSIS.md`

## Support
For issues or questions, check:
1. OpenHAB logs: `/var/log/openhab/openhab.log` and `events.log`
2. Net2 API documentation: `/etc/openhab/scripts/PAXTON_NET2_API_ANALYSIS.md`
3. Run scripts with `--verbose` flag for detailed output
