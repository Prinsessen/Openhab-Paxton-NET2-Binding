# Paxton Net2 Binding Installation Guide

## Prerequisites

- openHAB 5.1.0 or later (installed and running)
- Net2 server with WebAPI enabled
- OAuth credentials (Client ID & Secret) from Net2 administrator
- Admin username/password for Net2 server
- Java 11+

## Step 1: Obtain the Binding JAR

### Option A: Download Pre-built JAR
Download the latest release from [GitHub Releases](https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding/releases):
- `org.openhab.binding.net2-5.1.0.jar`

### Option B: Build from Source

```bash
# Clone repository
git clone https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding.git
cd Openhab-Paxton-NET2-Binding

# Build with Maven
mvn clean install -DskipTests

# JAR will be created at: target/org.openhab.binding.net2-5.1.0.jar
```

## Step 2: Deploy the Binding

### On Linux/Docker

```bash
# Copy JAR to addons directory
sudo cp org.openhab.binding.net2-5.1.0.jar /usr/share/openhab/addons/

# Verify file ownership (if needed)
sudo chown openhab:openhab /usr/share/openhab/addons/org.openhab.binding.net2-5.1.0.jar

# Restart openHAB
sudo systemctl restart openhab
```

### Verification

Check that binding loaded successfully:

```bash
# View openHAB logs
tail -f /var/log/openhab/openhab.log | grep -i net2

# Expected output should contain:
# [INFO ] ... STARTED Net2 Binding
# [INFO ] ... SignalR client initialized
```

Or check via openHAB UI:
- Go to **Settings → Add-ons → Installed**
- Search for "Net2" or "Paxton"
- Should appear in the list (note: manually deployed jars don't show in UI but are active)

## Step 3: Create Server Bridge

### Via UI

1. Go to **Things → + Create New Thing**
2. Select binding: **Paxton Net2**
3. Create thing type: **Net2 Server**
4. Enter configuration:

| Field | Example | Notes |
|-------|---------|-------|
| Host | `milestone.agesen.dk` | Net2 server hostname/IP |
| Port | `8443` | WebAPI port (usually 8443 for HTTPS) |
| Use HTTPS | ☑ checked | Enable for secure connection |
| Username | `admin` | Net2 admin account |
| Password | `****` | Admin password |
| Client ID | `openhab_client` | OAuth app client ID |
| Client Secret | `****` | OAuth app secret |

5. Click **Create Thing**

### Via things file

Create `/etc/openhab/things/net2.things`:

```openhab
Bridge net2:server:server [ 
    host="milestone.agesen.dk",
    port=8443,
    useHttps=true,
    username="admin",
    password="your-password",
    clientId="openhab_client",
    clientSecret="your-secret"
] {
    // Door things will be auto-discovered or added here
}
```

### Obtain OAuth Credentials

Contact your Net2 administrator to:
1. Create an OAuth application in Net2
2. Set redirect URI: `http://openhab:8080/` (or your openHAB IP)
3. Generate Client ID and Secret
4. Grant access to door events API
5. Provide credentials to openHAB

**Note**: Basic authentication is NOT used for API calls; OAuth tokens are generated and refreshed automatically.

## Step 4: Discover Doors (Auto-Discovery)

### Method 1: UI Discovery

1. Go to **Things → Discover** (or **+ New Things**)
2. In discovery dialog, select **Net2 Door Discovery**
3. Wait for scan to complete (10-30 seconds)
4. Available doors appear in Inbox
5. Click **Accept** on each door to create Thing

### Method 2: Manual Door Addition

1. Go to **Things → + Create New Thing**
2. Select binding: **Paxton Net2**
3. Create thing type: **Net2 Door**
4. Parent: Select your **Net2 Server** bridge
5. Enter Door ID (e.g., `door1`, `main_entrance`)
6. Click **Create Thing**

### Method 3: things File

Edit `/etc/openhab/things/net2.things`:

```openhab
Bridge net2:server:server [ host="...", ... ] {
    Thing door door1 "Front Door" [ doorId="front_main" ]
    Thing door door2 "Back Door" [ doorId="back_patio" ]
    Thing door door3 "Office" [ doorId="office_access" ]
}
```

## Step 5: Create Items and Link Channels

### Via UI

1. Go to **Settings → Items → + Create New Item**
2. For each door, create items:
   - **Type**: Switch, **Channel**: `net2:door:server:door1:status`
   - **Type**: Switch, **Channel**: `net2:door:server:door1:action`
   - **Type**: String, **Channel**: `net2:door:server:door1:lastAccessUser`
   - **Type**: DateTime, **Channel**: `net2:door:server:door1:lastAccessTime`

### Via items File

Create `/etc/openhab/items/net2.items`:

```openhab
// Front Door
Switch Net2_FrontDoor_Status "Front Door [%s]" <door> (gDoors) { channel="net2:door:server:door1:status" }
Switch Net2_FrontDoor_Unlock "Unlock Front Door" (gDoors) { channel="net2:door:server:door1:action" }
String Net2_FrontDoor_User "Last User [%s]" (gDoors) { channel="net2:door:server:door1:lastAccessUser" }
DateTime Net2_FrontDoor_Time "Last Access [%1$td.%1$tm.%1$tY %1$tH:%1$tM]" (gDoors) { channel="net2:door:server:door1:lastAccessTime" }

// Back Door
Switch Net2_BackDoor_Status "Back Door [%s]" <door> (gDoors) { channel="net2:door:server:door2:status" }
Switch Net2_BackDoor_Unlock "Unlock Back Door" (gDoors) { channel="net2:door:server:door2:action" }
String Net2_BackDoor_User "Last User [%s]" (gDoors) { channel="net2:door:server:door2:lastAccessUser" }
DateTime Net2_BackDoor_Time "Last Access [%1$td.%1$tm.%1$tY %1$tH:%1$tM]" (gDoors) { channel="net2:door:server:door2:lastAccessTime" }
```

## Step 6: Verify Connection

### Check Thing Status

1. Go to **Things** → Find your **Net2 Server** bridge
2. Should show status: **Online** (green)
3. Child Door things should also show **Online**

### Test Real-Time Events

1. Swipe card or unlock door on Net2 system
2. Observe item changes:
   - `Net2_FrontDoor_Status` should turn ON briefly (5 seconds) then OFF
   - `Net2_FrontDoor_User` and `Net2_FrontDoor_Time` should update

### Check Logs

```bash
tail -f /var/log/openhab/openhab.log | grep -i "net2\|signalr"

# Expected messages:
# [INFO ] - Net2 Server handler initialized
# [INFO ] - SignalR WebSocket connected successfully
# [INFO ] - Event subscription sent
# [DEBUG] - SignalR message received: ...
```

## Troubleshooting Installation

### Binding not loading
- Check `/usr/share/openhab/addons/` exists
- Verify JAR file is readable by openhab user
- Check logs: `grep -i "error\|exception" /var/log/openhab/openhab.log`

### Server bridge stays offline
- Verify hostname/port are correct
- Check credentials (username/password/OAuth)
- Ensure HTTPS certificate is valid (or disable certificate verification)
- Check network connectivity: `ping milestone.agesen.dk`
- Verify Net2 WebAPI is running on server

### OAuth authentication fails
- Confirm Client ID and Secret are correct
- Verify OAuth app exists on Net2 server
- Check redirect URI matches openHAB URL
- Confirm app has permission to access door events

### WebSocket connection fails
- Net2 server must have `/signalr/*` endpoints accessible
- Check firewall rules allow WebSocket traffic (port 8443)
- Verify Classic SignalR 2 is enabled (not SignalR Core)
- Enable debug logging to see negotiation details

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.

## Post-Installation

- Create automation rules to handle door events (e.g., log access, notify user)
- Configure persistence to record access history
- Create sitemaps for mobile/desktop control
- Set up alerts for unauthorized access attempts
- Link unlock switches to Google Home/Alexa if desired

## Uninstall

```bash
# Remove binding
sudo rm /usr/share/openhab/addons/org.openhab.binding.net2-5.1.0.jar

# Remove things/items (optional)
sudo rm /etc/openhab/things/net2.things
sudo rm /etc/openhab/items/net2.items

# Restart openHAB
sudo systemctl restart openhab
```
