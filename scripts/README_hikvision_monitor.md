# Hikvision NAS Body Detection Monitor

## Overview

This Python script monitors Hikvision camera detection files stored on a NAS and extracts body/face detection snapshots with detailed person analysis metadata. It uses OCR to extract 11 data fields from the camera's AI analysis overlay and updates OpenHAB smart home items in real-time.

### Key Features

- **Real-time Detection Monitoring**: Watches `.pic` container files for size changes (new detections added)
- **High-Resolution Image Extraction**: Extracts largest JPEG from each detection (up to 2560x1696)
- **AI Analysis OCR**: Reads 11 fields from camera's analysis overlay using Tesseract OCR
- **OpenHAB Integration**: Updates 11 smart home items via REST API
- **Web Dashboard Support**: Saves images and JSON data for web viewing
- **Robust OCR Correction**: Handles common OCR character misreads in datetime fields

### Extracted Detection Data (11 Fields)

1. **Capture Time** - Detection timestamp from camera
2. **Enter Direction** - Entry direction (Up/Down/Left/Right)
3. **Leave Direction** - Exit direction
4. **Top Color** - Upper body clothing color
5. **Bottom Color** - Lower body clothing color
6. **Top Type** - Upper garment type (Long Sleeve/Short Sleeve/etc.)
7. **Bottom Type** - Lower garment type (trousers/skirt/etc.)
8. **Has Backpack** - Boolean backpack detection
9. **Carrying Things** - Boolean carrying objects detection
10. **Has Hat** - Boolean hat detection
11. **Entry Time** - Timestamp when person entered frame
12. **Exit Time** - Timestamp when person left frame
13. **Camera** - Camera identifier (e.g., "Entrance")

---

## System Requirements

### Hardware
- Linux system (tested on Debian/Ubuntu)
- Network access to Hikvision NAS
- Sufficient RAM for Tesseract OCR (~50MB per detection)
- Storage for detection images (~500KB per detection)

### Software Dependencies

#### Required Packages
```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    cifs-utils \
    curl

# Optional: Image viewer for manual verification
sudo apt-get install -y feh
```

#### Python Dependencies
- Python 3.8 or higher
- See `requirements.txt` for complete list

---

## Installation

### 1. Clone or Download Script

```bash
cd /etc/openhab/scripts
# Script should be: hikvision_nas_monitor.py
```

### 2. Create Python Virtual Environment

```bash
cd /etc/openhab
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install pillow requests
```

Verify Tesseract installation:
```bash
tesseract --version
# Should show: tesseract 5.x.x
```

### 4. Create Configuration File

**IMPORTANT**: Do not hardcode sensitive information in the script!

Create configuration file:
```bash
nano /etc/openhab/scripts/hikvision_monitor_config.json
```

Add your settings (see Configuration section below).

### 5. Set Permissions

```bash
chmod +x /etc/openhab/scripts/hikvision_nas_monitor.py
chmod 600 /etc/openhab/scripts/hikvision_monitor_config.json  # Protect sensitive data
```

### 6. Mount NAS Share

Create mount point:
```bash
sudo mkdir -p /mnt/camera_nas
```

Create credentials file for secure mounting:
```bash
sudo nano /etc/camera_nas_credentials
```

Add (replace with your values):
```
username=YOUR_NAS_USERNAME
password=YOUR_NAS_PASSWORD
domain=WORKGROUP
```

Protect credentials file:
```bash
sudo chmod 600 /etc/camera_nas_credentials
```

Mount NAS manually (test):
```bash
sudo mount -t cifs //YOUR_NAS_IP/YOUR_SHARE_NAME /mnt/camera_nas \
    -o credentials=/etc/camera_nas_credentials,vers=3.0,uid=openhab,gid=openhab
```

**Persistent Mount**: Add to `/etc/fstab`:
```bash
sudo nano /etc/fstab
```

Add line:
```
//YOUR_NAS_IP/YOUR_SHARE_NAME /mnt/camera_nas cifs credentials=/etc/camera_nas_credentials,vers=3.0,uid=openhab,gid=openhab,_netdev 0 0
```

Apply fstab:
```bash
sudo mount -a
```

Verify mount:
```bash
ls -lh /mnt/camera_nas/Camera
# Should show .pic files
```

### 7. Configure OpenHAB Items

Create items file: `/etc/openhab/items/hikvision_detection.items`

```java
// Camera Body Detection Items
Group gCameraDetection "Camera Detection" <camera>

String Camera_Detection_Capture_Time "Capture Time [%s]" <time> (gCameraDetection)
String Camera_Detection_Enter_Direction "Enter Direction [%s]" <motion> (gCameraDetection)
String Camera_Detection_Leave_Direction "Leave Direction [%s]" <motion> (gCameraDetection)
String Camera_Detection_Top_Color "Top Color [%s]" <colorpicker> (gCameraDetection)
String Camera_Detection_Bottom_Color "Bottom Color [%s]" <colorpicker> (gCameraDetection)
String Camera_Detection_Top_Type "Top Type [%s]" <text> (gCameraDetection)
String Camera_Detection_Bottom_Type "Bottom Type [%s]" <text> (gCameraDetection)
Switch Camera_Detection_Has_Backpack "Has Backpack" <bag> (gCameraDetection)
Switch Camera_Detection_Carrying_Things "Carrying Things" <bag> (gCameraDetection)
Switch Camera_Detection_Has_Hat "Has Hat" <text> (gCameraDetection)
DateTime Camera_Detection_Entry_Time "Entry Time [%1$tF %1$tR]" <time> (gCameraDetection)
DateTime Camera_Detection_Exit_Time "Exit Time [%1$tF %1$tR]" <time> (gCameraDetection)
String Camera_Detection_Camera "Camera [%s]" <camera> (gCameraDetection)
```

Restart OpenHAB:
```bash
sudo systemctl restart openhab
```

Verify items exist:
```bash
curl http://localhost:8080/rest/items/Camera_Detection_Bottom_Color
```

### 8. Test Script Manually

```bash
cd /etc/openhab/scripts
source /etc/openhab/.venv/bin/activate
python3 hikvision_nas_monitor.py
```

Walk past camera and verify:
- Detection appears in console
- Image saved to `/etc/openhab/html/hikvision_latest.jpg`
- JSON saved to `/etc/openhab/html/hikvision_latest_analysis.json`
- OpenHAB items update (check Basic UI)

Press `Ctrl+C` to stop.

### 9. Create Systemd Service

Create service file:
```bash
sudo nano /etc/systemd/system/hikvision-monitor.service
```

Add content:
```ini
[Unit]
Description=Hikvision Body Detection Monitor
After=network.target openhab.service
Requires=network.target

[Service]
Type=simple
User=openhab
Group=openhab
WorkingDirectory=/etc/openhab/scripts
Environment="PYTHONUNBUFFERED=1"
ExecStartPre=/bin/sleep 5
ExecStart=/etc/openhab/.venv/bin/python3 -u /etc/openhab/scripts/hikvision_nas_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hikvision-monitor
sudo systemctl start hikvision-monitor
```

Check status:
```bash
sudo systemctl status hikvision-monitor
```

View logs:
```bash
sudo journalctl -u hikvision-monitor -f
```

---

## Configuration

### Configuration File Format

Create `/etc/openhab/scripts/hikvision_monitor_config.json`:

```json
{
  "nas": {
    "mount_path": "/mnt/camera_nas/Camera",
    "check_interval": 2,
    "comment": "Path to mounted NAS camera folder"
  },
  "openhab": {
    "rest_url": "http://localhost:8080/rest/items",
    "html_path": "/etc/openhab/html",
    "comment": "OpenHAB REST API endpoint"
  },
  "ocr": {
    "tesseract_timeout": 5,
    "panel_crop_height": 600,
    "comment": "OCR processing settings"
  },
  "output": {
    "temp_path": "/tmp",
    "image_filename": "hikvision_latest.jpg",
    "json_filename": "hikvision_latest_analysis.json",
    "timestamp_filename": "hikvision_latest_time.txt"
  }
}
```

### Configuration Parameters

#### NAS Settings
- `mount_path`: Full path to NAS Camera folder (must be mounted before script starts)
- `check_interval`: Seconds between file checks (default: 2)

#### OpenHAB Settings
- `rest_url`: OpenHAB REST API URL (default: http://localhost:8080/rest/items)
- `html_path`: Directory for web-served files (default: /etc/openhab/html)

#### OCR Settings
- `tesseract_timeout`: Max seconds for OCR processing (default: 5)
- `panel_crop_height`: Pixels to crop from bottom for analysis panel (default: 600)

#### Output Settings
- `temp_path`: Directory for temporary files (default: /tmp)
- `image_filename`: Latest detection image filename
- `json_filename`: Latest detection JSON filename
- `timestamp_filename`: Timestamp file for web display

---

## How It Works

### Detection Pipeline

1. **File Monitoring**
   - Scans all `.pic` files in NAS camera folder
   - Tracks file sizes to detect new detections
   - File size increase = new detection added to container

2. **Image Extraction**
   - Reads last 3MB of `.pic` container file
   - Locates JPEG markers (SOI: 0xFFD8, EOI: 0xFFD9)
   - Extracts largest JPEG from last 3 images (highest resolution)
   - Typical high-res image: 2560x1696 pixels (~500KB)

3. **OCR Text Extraction**
   - Crops bottom 600 pixels (analysis overlay panel)
   - Normalizes whitespace (handles OCR line wrapping)
   - Applies character corrections (common OCR errors):
     - `"2026-02-O07"` → `"2026-02-07"` (O→0 in dates)
     - `"O?"` → `"07"` (common misread)
     - `"Bottom Co lor:"` → normalized (split words)
   - Extracts 11 fields using regex patterns

4. **Data Processing**
   - Converts boolean fields (Yes/No → true/false)
   - Formats datetime strings to ISO 8601
   - Validates and cleanses data

5. **OpenHAB Updates**
   - POSTs each field to OpenHAB REST API
   - Updates all 11 items atomically
   - Logs update count and status

6. **Web Output**
   - Saves high-res JPEG to `/etc/openhab/html/`
   - Saves JSON metadata for dashboards
   - Updates timestamp file with camera capture time

### OCR Challenges & Solutions

#### Problem: Character Misreading
Tesseract sometimes reads:
- Zero `0` as letter `O` in dates: `"2026-02-O07"`
- Seven `7` as question mark: `"O?"`

**Solution**: Pre-correction regex patterns:
```python
# Fix O followed by 2 digits: "2026-02-O07" → "2026-02-07"
text = re.sub(r'(\d{4}[-/]\d{2}[-/])O(\d{2})', r'\g<1>\g<2>', text)

# Fix dash+space+O?: "- O?" → "-07"
text = re.sub(r'[-/]\s*O\?', r'-07', text)
```

#### Problem: Word Splitting
Camera overlay text wraps with extreme spacing:
```
"Bottom
 Co                                                                           
lor: Black"
```

**Solution**: Whitespace normalization + flexible regex:
```python
# Collapse all whitespace to single spaces
text = re.sub(r'\s+', ' ', text)

# Match "Bottom" + anything + "lor:" (handles "Co lor:")
pattern = r'Bottom[^:]*?(?:Co\s+)?(?:o)?lor\s*:\s*(\w+)'
```

### File Format: Hikvision ATTACHIF

- Container format storing multiple detections
- Each detection adds ~500KB to file
- Files grow to 100+ MB over time
- JPEG images stored sequentially with markers
- No compression or efficient random access
- Script reads only TAIL (last 3MB) for performance

---

## Troubleshooting

### Service Not Starting

Check logs:
```bash
sudo journalctl -u hikvision-monitor -n 50
```

Common issues:
- **"NAS path not mounted"**: Mount NAS share first
- **"Module not found"**: Activate venv and install dependencies
- **"Permission denied"**: Check file ownership and permissions

### No Detections Appearing

1. Verify NAS mount:
   ```bash
   ls -lh /mnt/camera_nas/Camera/*.pic
   ```

2. Check file sizes changing:
   ```bash
   watch -n 1 'ls -lh /mnt/camera_nas/Camera/hiv00025.pic'
   # Walk past camera, size should increase
   ```

3. Test script manually:
   ```bash
   cd /etc/openhab/scripts
   source /etc/openhab/.venv/bin/activate
   python3 hikvision_nas_monitor.py
   ```

### OCR Extraction Failing

1. Verify Tesseract installed:
   ```bash
   tesseract --version
   which tesseract
   ```

2. Check OCR output manually:
   ```bash
   tesseract /tmp/ocr_panel.jpg stdout
   # Should show analysis text
   ```

3. Verify image quality:
   ```bash
   feh /tmp/ocr_panel.jpg
   # Visual inspection of cropped panel
   ```

### OpenHAB Items Not Updating

1. Verify items exist:
   ```bash
   curl http://localhost:8080/rest/items | grep Camera_Detection
   ```

2. Check REST API access:
   ```bash
   curl -X PUT http://localhost:8080/rest/items/Camera_Detection_Top_Color/state \
        -H "Content-Type: text/plain" \
        --data "TestValue"
   ```

3. Check service logs for errors:
   ```bash
   sudo journalctl -u hikvision-monitor -f | grep -i error
   ```

### Fields Missing from JSON

Check which fields are NULL:
```bash
jq '.' /etc/openhab/html/hikvision_latest_analysis.json
```

Common issues:
- **bottom_color missing**: OCR struggling with split word "Bottom Color"
  - Solution: Improved regex pattern handles `"Bottom Co lor:"`
  
- **entry_time/exit_time missing**: OCR misreading dates
  - Solution: Character correction patterns fix `"O07"` → `"07"`

Enable debug to see raw OCR:
```bash
tesseract /tmp/ocr_panel.jpg stdout
```

### High CPU Usage

OCR is CPU-intensive. To reduce load:

1. Increase `CHECK_INTERVAL` in config (default: 2 seconds)
2. Limit Tesseract threads:
   ```bash
   export OMP_THREAD_LIMIT=2
   ```
3. Use systemd CPUQuota:
   ```ini
   [Service]
   CPUQuota=50%
   ```

---

## Performance & Optimization

### Resource Usage

- **CPU**: ~10-20% spike during OCR (2-3 seconds per detection)
- **Memory**: ~50MB base + ~20MB per OCR operation
- **Disk I/O**: ~500KB write per detection
- **Network**: Minimal (only REST API calls)

### Optimization Tips

1. **Reduce Check Interval**: Set to 5 seconds if detections are infrequent
2. **Limit File Scanning**: Script tracks 3000+ files efficiently using size cache
3. **OCR Caching**: Consider caching identical panels (advanced)
4. **Batch Updates**: Already optimized - single REST call per item

### Scaling Considerations

- **Multiple Cameras**: Run separate service per camera with different config
- **High Detection Volume**: Consider async processing with queue
- **Historical Data**: Script only tracks latest detection (by design)

---

## Integration Examples

### OpenHAB Sitemap

```java
sitemap camera label="Camera Detection" {
    Frame label="Latest Detection" {
        Image url="/static/hikvision_latest.jpg" refresh=2000
        
        Text item=Camera_Detection_Capture_Time
        Text item=Camera_Detection_Camera
        
        Text label="Person Details" icon="boy" {
            Text item=Camera_Detection_Top_Color
            Text item=Camera_Detection_Top_Type
            Text item=Camera_Detection_Bottom_Color
            Text item=Camera_Detection_Bottom_Type
            Switch item=Camera_Detection_Has_Backpack
            Switch item=Camera_Detection_Carrying_Things
            Switch item=Camera_Detection_Has_Hat
        }
        
        Text label="Movement" icon="motion" {
            Text item=Camera_Detection_Enter_Direction
            Text item=Camera_Detection_Leave_Direction
            Text item=Camera_Detection_Entry_Time
            Text item=Camera_Detection_Exit_Time
        }
    }
}
```

### OpenHAB Rules

```java
rule "Person Detected - Send Notification"
when
    Item Camera_Detection_Entry_Time changed
then
    var topColor = Camera_Detection_Top_Color.state.toString
    var bottomColor = Camera_Detection_Bottom_Color.state.toString
    var hasBackpack = Camera_Detection_Has_Backpack.state == ON
    
    var msg = "Person detected: " + topColor + " top, " + bottomColor + " bottom"
    if (hasBackpack) msg = msg + " (with backpack)"
    
    sendNotification("your@email.com", msg)
end
```

### Home Assistant Webhook

See script modification to POST to Home Assistant REST API:
```python
# Add to update_openhab_items function
ha_url = "http://homeassistant.local:8123/api/webhook/camera_detection"
requests.post(ha_url, json=analysis)
```

---

## Security Considerations

### Sensitive Data Protection

1. **Never commit config file to git**:
   ```bash
   echo "hikvision_monitor_config.json" >> .gitignore
   ```

2. **Protect credentials file**:
   ```bash
   sudo chmod 600 /etc/camera_nas_credentials
   sudo chown root:root /etc/camera_nas_credentials
   ```

3. **Restrict config file access**:
   ```bash
   chmod 600 /etc/openhab/scripts/hikvision_monitor_config.json
   chown openhab:openhab /etc/openhab/scripts/hikvision_monitor_config.json
   ```

4. **Use separate user for service**:
   - Script runs as `openhab` user (limited privileges)
   - Cannot access other system files

### Network Security

- OpenHAB REST API runs on localhost (not exposed externally)
- If exposing web images, use HTTPS reverse proxy
- Consider VPN for NAS access

### Privacy Considerations

- Detection images contain person appearance data
- Consider data retention policy
- Implement auto-deletion of old detections
- Comply with local privacy laws (GDPR, etc.)

---

## Development & Debugging

### Enable Debug Mode

Modify script to add verbose logging:
```python
# Add after imports
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test OCR Patterns

```python
# Test regex patterns
import re
text = "Entry Time:2026-02-O07 09:35:14"
text = re.sub(r'(\d{4}[-/]\d{2}[-/])O(\d{2})', r'\g<1>\g<2>', text)
print(text)  # Should show: "Entry Time:2026-02-07 09:35:14"
```

### Manual Image Testing

```bash
# Extract image manually
dd if=/mnt/camera_nas/Camera/hiv00025.pic skip=132M bs=1M count=1 of=/tmp/test.jpg

# Test OCR
tesseract /tmp/test.jpg stdout
```

---

## Maintenance

### Log Rotation

Service logs to systemd journal. Configure retention:
```bash
sudo nano /etc/systemd/journald.conf
```

Set:
```ini
SystemMaxUse=500M
MaxRetentionSec=1month
```

Apply:
```bash
sudo systemctl restart systemd-journald
```

### Cleaning Old Detections

Create cleanup script:
```bash
#!/bin/bash
# Delete detection snapshots older than 7 days
find /tmp -name "hikvision_detection_*.jpg" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
0 2 * * * /path/to/cleanup.sh
```

### Updating Script

1. Stop service:
   ```bash
   sudo systemctl stop hikvision-monitor
   ```

2. Backup current script:
   ```bash
   cp hikvision_nas_monitor.py hikvision_nas_monitor.py.backup
   ```

3. Update script

4. Test manually:
   ```bash
   python3 hikvision_nas_monitor.py
   ```

5. Restart service:
   ```bash
   sudo systemctl start hikvision-monitor
   ```

---

## FAQ

### Q: Can I run multiple instances for different cameras?
**A**: Yes. Create separate config files and systemd services with different names.

### Q: Does it store historical detections?
**A**: No, only the latest detection is kept. Implement database storage if needed.

### Q: What cameras are supported?
**A**: Any Hikvision camera that saves to ATTACHIF format (.pic files) with AI analysis overlay.

### Q: Can I disable specific fields?
**A**: Yes, modify the `item_mapping` dictionary in `update_openhab_items()` function.

### Q: How to add more fields?
**A**: Add regex pattern in `extract_analysis_text()`, update JSON structure, create OpenHAB item.

### Q: Is there a web dashboard?
**A**: Basic files are served from `/etc/openhab/html/`. Build custom dashboard using the JSON feed.

---

## Support & Contributing

### Reporting Issues

Include:
1. Full error message
2. Output of `sudo journalctl -u hikvision-monitor -n 100`
3. OCR test: `tesseract /tmp/ocr_panel.jpg stdout`
4. Python version: `python3 --version`
5. Tesseract version: `tesseract --version`

### Known Limitations

- Only monitors one NAS mount point
- OCR requires high-quality images
- No historical data storage
- Single-threaded processing

---

## License

[Specify your license here]

## Credits

- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- OpenHAB: https://www.openhab.org/
- Hikvision ATTACHIF format reverse engineering

---

## Version History

- **v1.0.0** (2026-02-07) - Initial release with 11-field extraction
  - High-res image extraction
  - OCR character correction
  - OpenHAB REST API integration
  - Systemd service support
