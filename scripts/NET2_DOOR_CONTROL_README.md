# Net2 Door Control Script

Complete Python script for controlling Paxton Net2 access control doors via the Local Web API.

## Overview

`net2_toggle_door.py` provides comprehensive control of Paxton Net2 doors with three modes of operation:
- **Interactive Mode**: Lists all doors, shows current status, and prompts for action
- **Semi-Interactive Mode**: Specify door ID, script checks status and prompts for action
- **Command-Line Mode**: Direct execution with full command-line arguments

## Features

✓ **Door Control**
  - Hold door open indefinitely
  - Close/secure door
  - Real-time status checking

✓ **API Integration**
  - Automatic door discovery via `/api/v1/doors`
  - Real-time status via `/api/v1/doors/status`
  - Hold open via `/api/v1/commands/door/holdopen`
  - Close via `/api/v1/commands/door/close`

✓ **User-Friendly**
  - Clear status display (HELD OPEN / CLOSED/NORMAL)
  - Informative success/error messages
  - Visual formatting with Unicode characters
  - Door name and ID display

✓ **State Tracking**
  - Local state file (`.door_state.json`) for fallback
  - Always queries API for current status first
  - Automatic state synchronization

## Requirements

### Python Dependencies
```
Python 3.6 or higher
requests >= 2.31.0
urllib3 >= 2.0.0
```

### API Requirements
- Paxton Net2 system with Local Web API enabled
- Valid API credentials (username, password, client_id)
- Network access to Net2 server (HTTPS)

### Installation
```bash
pip install -r requirements.txt
```

## Configuration

### config file: `net2_config.json`
```json
{
  "base_url": "https://your-server:8443/api/v1",
  "username": "Your Name",
  "password": "your_password",
  "grant_type": "password",
  "client_id": "your-client-id-from-licence-file"
}
```

**Important**: The config file must be in the same directory as the script.

### Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| `base_url` | Net2 API base URL (must include /api/v1) | `https://milestone.agesen.dk:8443/api/v1` |
| `username` | Net2 operator name (First Last) | `John Smith` |
| `password` | Operator password | `YourPassword123` |
| `grant_type` | OAuth2 grant type (always "password") | `password` |
| `client_id` | From API licence file | `00aab996-6439-4f16-89b4-6c0cc851e8f3` |

## Usage

### Interactive Mode (No Arguments)
Lists all available doors and prompts for selection and action:
```bash
python3 net2_toggle_door.py
```

**Example Output:**
```
Fetching available doors...

Available doors:
1. Reception Entrance (ID: 6203980)
2. Main Gate (ID: 6612642)
3. Warehouse Door (ID: 7123456)

Select door number (or press Enter to cancel): 1

✓ Selected: Reception Entrance (ID: 6203980)

═══ Current Door Status ═══
Door ID: 6203980
Checking status...
Current state: CLOSED/NORMAL

What would you like to do?
1. Open (hold door open)
2. Close
3. Status
4. Cancel

Enter choice (1-4): 1

═══ Opening Door ═══
Door ID: 6203980
Action: Hold door open indefinitely...

✓ SUCCESS: Door is now held open
  The door will remain open until you run the close command
```

### Semi-Interactive Mode (Door ID Only)
Specify door ID, script checks status and prompts for action:
```bash
python3 net2_toggle_door.py <door_id>
```

**Example:**
```bash
python3 net2_toggle_door.py 6203980
```

### Command-Line Mode (Full Arguments)
Direct execution for automation and scripting:

**Hold Door Open:**
```bash
python3 net2_toggle_door.py <door_id> open
```

**Close Door:**
```bash
python3 net2_toggle_door.py <door_id> close
```

**Check Status:**
```bash
python3 net2_toggle_door.py <door_id> status
```

**Examples:**
```bash
# Hold door 6203980 open
python3 net2_toggle_door.py 6203980 open

# Close door 6203980
python3 net2_toggle_door.py 6203980 close

# Check status of door 6203980
python3 net2_toggle_door.py 6203980 status
```

## Status Output

The status command displays comprehensive door information:

```
═══ Door Status ═══
Checking status for door 6203980...

Door Name: Fordør Terndrupvej - ACU:6203980
Door ID: 6203980
Relay Status: HELD OPEN
Door Contact: OPEN

Full status: {
  "name": "Fordør Terndrupvej - ACU:6203980",
  "id": 6203980,
  "status": {
    "intruderAlarmArmed": false,
    "psuContactClosed": true,
    "tamperContactClosed": true,
    "doorContactClosed": false,
    "alarmTripped": false,
    "doorRelayOpen": true
  }
}
```

### Status Fields Explained

| Field | Values | Description |
|-------|--------|-------------|
| `Relay Status` | HELD OPEN / CLOSED/NORMAL | Whether door is held open by relay |
| `Door Contact` | OPEN / CLOSED | Physical door position sensor |
| `doorRelayOpen` | true / false | Relay is holding door open |
| `doorContactClosed` | true / false | Physical door is closed |
| `alarmTripped` | true / false | Door alarm status |
| `tamperContactClosed` | true / false | Tamper sensor status |

## API Endpoints Used

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/authorization/tokens` | POST | Authenticate and get access token | JWT token (30 min) |
| `/api/v1/doors` | GET | List all available doors | Array of door objects |
| `/api/v1/doors/status` | GET | Get current status of all doors | Array with status info |
| `/api/v1/commands/door/holdopen` | POST | Hold door open indefinitely | FireAndForget command |
| `/api/v1/commands/door/close` | POST | Close/secure door | FireAndForget command |

### Request Format Example

**Hold Door Open:**
```json
POST /api/v1/commands/door/holdopen
Authorization: Bearer <token>
Content-Type: application/json

{
  "DoorId": 6203980
}
```

**Response:**
```json
{
  "commandName": "HoldDoorOpen",
  "input": {"doorId": 6203980},
  "output": {
    "status": "FireAndForget",
    "errors": null
  },
  "id": null
}
```

## Integration with OpenHAB

### Direct Execution from Rules
```java
rule "Open Front Door"
when
    Item FrontDoor_Open received command ON
then
    executeCommandLine(Duration.ofSeconds(10), 
        "python3", "/etc/openhab/scripts/net2_toggle_door.py", "6203980", "open")
end

rule "Close Front Door"
when
    Item FrontDoor_Close received command ON
then
    executeCommandLine(Duration.ofSeconds(10),
        "python3", "/etc/openhab/scripts/net2_toggle_door.py", "6203980", "close")
end
```

### Check Status and Update Item
```java
rule "Update Door Status"
when
    Time cron "0 * * * * ?" // Every minute
then
    val result = executeCommandLine(Duration.ofSeconds(10),
        "python3", "/etc/openhab/scripts/net2_toggle_door.py", "6203980", "status")
    
    if (result.contains("HELD OPEN")) {
        FrontDoor_Status.postUpdate("OPEN")
    } else {
        FrontDoor_Status.postUpdate("CLOSED")
    }
end
```

### Items Configuration
```
Switch FrontDoor_Open "Hold Front Door Open" <door>
Switch FrontDoor_Close "Close Front Door" <door>
String FrontDoor_Status "Front Door Status [%s]" <status>
```

### Sitemap Configuration
```
Switch item=FrontDoor_Open mappings=[ON="Hold Open"]
Switch item=FrontDoor_Close mappings=[ON="Close"]
Text item=FrontDoor_Status
```

## Windows Deployment

### Building Executable
1. Copy all files to Windows PC:
   - `net2_toggle_door.py`
   - `net2_config.json`
   - `requirements.txt`
   - `build_windows_exe.bat`

2. Run `build_windows_exe.bat`

3. Find executable in `dist\net2_toggle_door.exe`

### Windows Usage
```cmd
REM Interactive mode
net2_toggle_door.exe

REM Command line mode
net2_toggle_door.exe 6203980 open
net2_toggle_door.exe 6203980 close
net2_toggle_door.exe 6203980 status
```

### Windows Shortcuts (Optional)
Create `.bat` files for quick access:

**Open_Door_6203980.bat:**
```batch
@echo off
net2_toggle_door.exe 6203980 open
pause
```

**Close_Door_6203980.bat:**
```batch
@echo off
net2_toggle_door.exe 6203980 close
pause
```

## Troubleshooting

### Connection Issues

**Problem:** "Authentication failed"
- **Solution**: Verify username, password, and client_id in `net2_config.json`
- **Check**: Username format should be "First Last" (with space)

**Problem:** "Failed to list doors: HTTP 404"
- **Solution**: Verify `base_url` includes `/api/v1` at the end
- **Example**: `https://server:8443/api/v1` (not `https://server:8443`)

**Problem:** SSL certificate warnings
- **Solution**: Script already uses `verify=False` to bypass self-signed certificates
- **Note**: This is normal for local API installations

### Door Control Issues

**Problem:** Door opens but won't close
- **Solution**: Ensure you're using the correct door ID
- **Check**: Run status command to verify door is actually held open
- **API**: Verify `/api/v1/commands/door/close` endpoint is available

**Problem:** Status shows wrong state
- **Solution**: Script now uses `doorRelayOpen` field from API
- **Check**: Compare with Net2 software UI
- **Debug**: Use status command to see full API response

**Problem:** "User not permitted through door"
- **Solution**: Check operator permissions in Net2 Configuration
- **Required**: Operator must have door control rights
- **Check**: Test with Net2 web interface first

### Permission Issues (Linux)

**Problem:** Script can't write state file
- **Solution**: Ensure write permissions in script directory
- **Fix**: `chmod +x net2_toggle_door.py`
- **Fix**: `chmod 644 .door_state.json` (if exists)

## File Structure

```
/etc/openhab/scripts/
├── net2_toggle_door.py          # Main script
├── net2_config.json             # API credentials (required)
├── .door_state.json             # State tracking (auto-created)
├── requirements.txt             # Python dependencies
├── build_windows_exe.bat        # Windows build script
├── BUILD_WINDOWS_EXE.md         # Windows build instructions
└── net2_door_control_windows.zip # Complete package
```

## Security Considerations

1. **Credentials**: The `net2_config.json` file contains sensitive credentials
   - Set permissions: `chmod 600 net2_config.json`
   - Never commit to version control
   - Add to `.gitignore`

2. **SSL Verification**: Script uses `verify=False` for self-signed certificates
   - Acceptable for local networks
   - For production, use proper SSL certificates

3. **API Access**: Limit operator permissions in Net2
   - Only grant necessary door access
   - Use dedicated API operator account
   - Regularly rotate passwords

## Advanced Usage

### Batch Operations
```bash
#!/bin/bash
# Open multiple doors
for door_id in 6203980 6612642 7123456; do
    python3 net2_toggle_door.py $door_id open
    sleep 1
done
```

### Status Monitoring
```bash
#!/bin/bash
# Monitor door status every 30 seconds
while true; do
    python3 net2_toggle_door.py 6203980 status | grep "Relay Status"
    sleep 30
done
```

### Cron Jobs
```cron
# Open door at 8 AM
0 8 * * 1-5 python3 /etc/openhab/scripts/net2_toggle_door.py 6203980 open

# Close door at 6 PM
0 18 * * 1-5 python3 /etc/openhab/scripts/net2_toggle_door.py 6203980 close
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (authentication, API call, or user cancelled) |
| 130 | User interrupted (Ctrl+C) |

## Version History

- **v1.0** - Initial release with toggle functionality
- **v1.1** - Added door listing and interactive mode
- **v1.2** - Fixed status detection (doorRelayOpen field)
- **v1.3** - Added comprehensive output messages
- **v1.4** - Windows executable support

## Support

For issues or questions:
1. Check the Paxton Net2 API documentation at your server: `https://your-server:8443/webapihelp/`
2. Verify API endpoints are accessible
3. Check Net2 operator permissions
4. Review script output for error messages

## License

This script interfaces with Paxton Net2 API. Ensure you have proper licensing and permissions for API access from Paxton Access Ltd.
