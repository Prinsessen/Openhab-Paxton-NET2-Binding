# Paxton Net2 User Activity Report Generator

## Overview
This Python script connects to the Paxton Net2 access control system API to retrieve user access events and generates a beautiful, auto-refreshing HTML report showing user activity across all doors and access points.

## Features

- 🔐 **Secure API Authentication** - Uses OAuth2 Bearer token authentication
- 📊 **Activity Statistics** - Displays total events, active users, access granted/denied counts
- 👥 **User-Organized View** - Groups events by user for easy tracking
- 🎨 **Modern UI** - Responsive, gradient-styled HTML with automatic dark mode support
- 🔄 **Auto-Refresh** - Configurable automatic page refresh for real-time monitoring
- ⏰ **Flexible Time Range** - Retrieve events from last N hours
- 📱 **Mobile Responsive** - Works on desktop, tablet, and mobile devices
- 🎯 **Event Filtering** - Shows event type, door/location, and access result
- 🕒 **Timestamp Formatting** - Human-readable date/time display

## Installation

### Prerequisites
- Python 3.6 or higher
- `requests` library

Install dependencies:
```bash
pip3 install requests
```

Or use the workspace Python environment:
```bash
python3 -m pip install requests
```

### Make Script Executable
```bash
chmod +x /etc/openhab/scripts/net2_user_activity.py
```

## Usage

### Basic Usage
Generate report for last 24 hours (default):
```bash
/etc/openhab/scripts/net2_user_activity.py
```

### With Custom Time Range
Retrieve last 48 hours of activity:
```bash
/etc/openhab/scripts/net2_user_activity.py --hours 48
```

### Custom Output Location
```bash
/etc/openhab/scripts/net2_user_activity.py --output /var/www/html/net2_report.html
```

### Custom Refresh Rate
Set auto-refresh to 30 seconds:
```bash
/etc/openhab/scripts/net2_user_activity.py --refresh 30
```

### Verbose Mode
Enable detailed logging:
```bash
/etc/openhab/scripts/net2_user_activity.py --verbose
```

### Combined Options
```bash
/etc/openhab/scripts/net2_user_activity.py --hours 12 --output /tmp/report.html --refresh 60 --verbose
```

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--hours` | int | 24 | Number of hours to retrieve events |
| `--output` | string | `/etc/openhab/html/net2_activity.html` | Output HTML file path |
| `--refresh` | int | 60 | HTML auto-refresh interval in seconds |
| `--verbose` | flag | false | Enable verbose logging output |

## Integration with OpenHAB

### Method 1: Exec Binding

1. **Add to exec whitelist** (`misc/exec.whitelist`):
```
/etc/openhab/scripts/net2_user_activity.py
```

2. **Create Thing** (`things/paxton.things`):
```openhab
Thing exec:command:net2_activity [
    command="/etc/openhab/scripts/net2_user_activity.py --hours 24",
    interval=900,
    timeout=30,
    autorun=true
]
```

3. **Create Items** (`items/paxton.items`):
```openhab
Switch net2_activity_Run       {channel="exec:command:net2_activity:run"}
String net2_activity_Output    {channel="exec:command:net2_activity:output"}
Number net2_activity_Exit      {channel="exec:command:net2_activity:exit"}
DateTime net2_activity_LastRun {channel="exec:command:net2_activity:lastexecution"}
```

4. **Add to Sitemap**:
```openhab
Webview url="/static/net2_activity.html" height=15
```

### Method 2: Cron Job

Add to crontab for automatic execution:
```bash
# Update Net2 activity report every 15 minutes
*/15 * * * * /etc/openhab/scripts/net2_user_activity.py >> /var/log/openhab/net2_activity.log 2>&1
```

### Method 3: Systemd Timer

Create service file (`/etc/systemd/system/net2-activity.service`):
```ini
[Unit]
Description=Paxton Net2 User Activity Report Generator

[Service]
Type=oneshot
User=openhab
ExecStart=/etc/openhab/scripts/net2_user_activity.py
StandardOutput=journal
StandardError=journal
```

Create timer file (`/etc/systemd/system/net2-activity.timer`):
```ini
[Unit]
Description=Net2 Activity Report Timer

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable net2-activity.timer
sudo systemctl start net2-activity.timer
```

## API Configuration

The script connects to your Paxton Net2 server at:
```
BASE_URL: https://milestone.agesen.dk:8443/api/v1
```

### Authentication Details
- **Username**: Configured in script
- **Password**: Configured in script
- **Grant Type**: password (OAuth2)
- **Client ID**: Application-specific UUID

### API Endpoints Used

1. **Authentication**
   - `POST /api/v1/authorization/tokens`
   - Returns Bearer token for subsequent requests

2. **Events Retrieval** (Primary)
   - `GET /api/v1/events`
   - Parameters: `startDate`, `endDate`, `pageSize`

3. **Events Retrieval** (Fallback)
   - `GET /api/v1/monitoring/events`
   - Used if primary endpoint returns 404

## HTML Report Features

### Dashboard Statistics
- **Total Events** - Count of all access events
- **Active Users** - Number of unique users with activity
- **Access Granted** - Successful access attempts
- **Access Denied** - Failed access attempts

### User Activity Sections
Each user section shows:
- User name with event count badge
- Collapsible event table with:
  - Timestamp (formatted as DD-MM-YYYY HH:MM:SS)
  - Event type (e.g., "Card Read", "Door Open")
  - Door/Location name
  - Result status (color-coded: green=granted, red=denied, yellow=unknown)

### Visual Design
- Gradient purple header
- Card-based statistics display
- Responsive grid layout
- Hover effects on interactive elements
- Color-coded event results
- Auto-refresh indicator in footer

## Troubleshooting

### Authentication Fails
```
ERROR: Authentication failed with status 401
```
**Solution**: Verify username, password, and client_id in script

### Connection Timeout
```
ERROR: Connection failed - timeout
```
**Solution**: Check network connectivity and server URL

### No Events Retrieved
```
WARNING: Failed to retrieve events (status 404)
```
**Solution**: 
- API endpoint may differ in your Net2 version
- Try enabling `--verbose` to see attempted endpoints
- Check Paxton Net2 API documentation for your version

### Permission Denied
```
ERROR: Failed to save HTML file - Permission denied
```
**Solution**: Ensure write permissions for output directory:
```bash
sudo chown openhab:openhab /etc/openhab/html/
```

### SSL Certificate Errors
If you get SSL certificate validation errors:
```bash
# Update CA certificates
sudo update-ca-certificates
```

Or temporarily disable SSL verification (NOT recommended for production):
```python
response = requests.post(AUTH_ENDPOINT, data=payload, verify=False)
```

## Customization

### Change Time Format
Edit `format_timestamp()` function to use different date format:
```python
return dt.strftime('%Y-%m-%d %H:%M')  # 24-hour format
return dt.strftime('%d/%m/%Y %I:%M %p')  # 12-hour format with AM/PM
```

### Modify Color Scheme
Update CSS in `generate_html()` function:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
/* Change to blue theme */
background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
```

### Add Email Notifications
Import smtplib and add email function:
```python
def send_email_alert(event_summary):
    # Email configuration
    # Send summary email
```

### Filter Specific Event Types
Modify `process_events()` to filter:
```python
if event_type not in ['Door Forced', 'Door Held']:
    continue  # Skip unwanted events
```

## Security Considerations

⚠️ **Important Security Notes**:

1. **Credentials in Script**: Currently hardcoded. Consider using:
   - Environment variables
   - Configuration file with restricted permissions
   - Secret management service

2. **HTTPS Required**: Always use HTTPS for API communication

3. **File Permissions**: Restrict script permissions:
   ```bash
   chmod 750 /etc/openhab/scripts/net2_user_activity.py
   chown openhab:openhab /etc/openhab/scripts/net2_user_activity.py
   ```

4. **HTML Output**: If accessible via web server, ensure proper authentication

## Output Example

Generated HTML includes:
- Real-time statistics dashboard
- Per-user activity timeline
- Color-coded access results
- Responsive mobile layout
- Auto-refresh capability

View the report by opening:
```
http://openhab5.agesen.dk:8080/static/net2_activity.html
```

Or embed in OpenHAB sitemap:
```openhab
Webview url="/static/net2_activity.html" height=15
```

## Related Files

- **Door Control Script**: `/etc/openhab/scripts/net2.py`
- **Existing Reports**: 
  - `/etc/openhab/html/paxton.html`
  - `/etc/openhab/html/Kirkegade 50 - Occupancy Management Report.html`
- **Items**: `/etc/openhab/items/paxton.items`
- **Things**: `/etc/openhab/things/paxton.things`

## Version History

- **v1.0.0** (2026-01-05)
  - Initial release
  - OAuth2 authentication
  - Event retrieval with time range
  - HTML report generation
  - Auto-refresh support
  - Responsive design

## Support

For issues or questions:
1. Enable `--verbose` mode to see detailed logs
2. Check Paxton Net2 API documentation
3. Verify network connectivity to server
4. Review OpenHAB logs: `/var/log/openhab/`

## License

Part of OpenHAB 5.1.0 Smart Home Configuration
