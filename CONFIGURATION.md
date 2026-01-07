# Paxton Net2 Binding Configuration Guide

## Overview

This guide covers detailed configuration of the Net2 binding for openHAB, including server bridge setup, door thing configuration, and item linking.

## Server Bridge Configuration

### Configuration Parameters

The **Net2 Server** bridge requires the following settings:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | String | Yes | — | Net2 server hostname or IP address |
| `port` | Integer | No | `8443` | Net2 WebAPI port |
| `useHttps` | Boolean | No | `true` | Use HTTPS for API calls |
| `username` | String | Yes | — | Net2 admin username |
| `password` | String | Yes | — | Net2 admin password |
| `clientId` | String | Yes | — | OAuth application client ID |
| `clientSecret` | String | Yes | — | OAuth application secret |
| `refreshInterval` | Integer | No | `30` | Door status refresh interval (minutes) |

### Example Bridge Configuration

#### Via things file

```openhab
Bridge net2:server:server "Net2 Server" [
    host="milestone.agesen.dk",
    port=8443,
    useHttps=true,
    username="admin@company.com",
    password="securePassword123!",
    clientId="openhab_app",
    clientSecret="abc123def456xyz",
    refreshInterval=30
]
```

#### Via openHAB UI

1. Go to **Things** and create a new Thing
2. Select **Paxton Net2 Binding**
3. Choose **Net2 Server** thing type
4. Fill in all required fields (credentials will be encrypted)

### OAuth Configuration

#### Creating OAuth Application (Net2 Admin)

1. Log in to Net2 admin panel
2. Navigate to **System → OAuth Applications**
3. Click **Create New Application**
4. Configure:
   - **Name**: `openHAB Integration`
   - **Redirect URI**: `http://<openhab-ip>:8080/` (or your openHAB URL)
   - **Scopes**: Request access to:
     - `door:read` - Read door status
     - `door:write` - Control door unlock
     - `access:read` - Read access logs
   - **Token Expiry**: (usually 30 minutes, system default)

5. Save and generate credentials:
   - **Client ID**: Copy this value
   - **Client Secret**: Copy this value (save securely!)

6. Provide these credentials to openHAB configuration

#### Token Lifecycle

- **Initial Token**: Obtained on bridge startup via Bearer token request
- **Token Lifetime**: ~30 minutes (Net2 server dependent)
- **Auto-Refresh**: Binding refreshes at ~25 minutes to prevent expiry
- **Failed Refresh**: Binding reconnects and re-authenticates

## Door Thing Configuration

### Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `doorId` | String | Yes | — | Net2 door identifier (from API) |

### Example Door Configuration

#### Via things file

```openhab
Bridge net2:server:server [ ... ] {
    Thing door main_entrance "Main Entrance" [ doorId="MAIN_001" ]
    Thing door back_door "Back Entrance" [ doorId="BACK_001" ]
    Thing door office "Office Access" [ doorId="OFFICE_001" ]
}
```

#### Via openHAB UI

1. Go to **Things** and select your Net2 Server bridge
2. Click **+ Add Child Thing**
3. Choose **Net2 Door**
4. Enter **Door ID** (obtained from Net2 system)
5. Click **Create Thing**

### Finding Door IDs

#### Method 1: Auto-Discovery

Use the **Net2 Door Discovery Service**:
1. Go to **Things → Discover**
2. Select **Net2 Door Discovery**
3. Wait for scan to complete
4. Available doors appear in Inbox with their IDs

#### Method 2: Via openHAB Logs

Enable debug logging and check logs for discovered doors:
```
[DEBUG] - Available doors from API: {MAIN_001=Main Entrance, BACK_001=Back Entrance, ...}
```

#### Method 3: Manual Query

Query Net2 API directly:
```bash
curl -H "Authorization: Bearer <TOKEN>" \
  https://milestone.agesen.dk:8443/api/v1/doors \
  -k (if self-signed cert)
```

## Channels and Items

### Available Channels

Each Door thing provides 4 channels:

#### 1. Status Channel
- **Channel ID**: `status`
- **Item Type**: `Switch`
- **Access**: Read-only
- **Description**: Door activity indicator (ON/OFF pulse)
- **Behavior**: 
  - ON when door access event detected
  - Auto-OFF after 5 seconds
  - Useful for visual indication of door activity

**Item Example**:
```openhab
Switch Net2_Door_Status "Door Activity [%s]" <door> { 
    channel="net2:door:server:main_entrance:status" 
}
```

#### 2. Action Channel
- **Channel ID**: `action`
- **Item Type**: `Switch`
- **Access**: Write-only
- **Description**: Door unlock command
- **Behavior**:
  - Send command ON to unlock
  - Sends unlock command to Net2 server
  - Respects door's access control settings

**Item Example**:
```openhab
Switch Net2_Door_Unlock "Unlock Door" {
    channel="net2:door:server:main_entrance:action"
}
```

**Rule Example**:
```openhab
rule "Unlock door on request"
when
    Item MyRequest received command ON
then
    Net2_Door_Unlock.sendCommand(ON)
    logInfo("Door", "Door unlock requested")
end
```

#### 3. Last Access User Channel
- **Channel ID**: `lastAccessUser`
- **Item Type**: `String`
- **Access**: Read-only
- **Description**: Name of person who last accessed the door
- **Source**: Real-time event (via SignalR) or API polling

**Item Example**:
```openhab
String Net2_Door_User "Last User [%s]" {
    channel="net2:door:server:main_entrance:lastAccessUser"
}
```

#### 4. Last Access Time Channel
- **Channel ID**: `lastAccessTime`
- **Item Type**: `DateTime`
- **Access**: Read-only
- **Description**: Timestamp of last door access
- **Format**: ISO 8601 timestamp
- **Source**: Real-time event (via SignalR) or API polling

**Item Example**:
```openhab
DateTime Net2_Door_Time "Last Access [%1$td.%1$tm.%1$tY %1$tH:%1$tM:%1$tS]" {
    channel="net2:door:server:main_entrance:lastAccessTime"
}
```

## Item Configuration Examples

### Complete Door Setup

```openhab
// Front Door Group
Group GF_FrontDoor "Front Door" <door>

// Status - visual indicator
Switch GF_FrontDoor_Status "Activity [MAP(door_status.map):%s]" <door> (GF_FrontDoor) {
    channel="net2:door:server:main_entrance:status"
}

// Unlock command
Switch GF_FrontDoor_Unlock "Unlock" (GF_FrontDoor) {
    channel="net2:door:server:main_entrance:action"
}

// Access logging
String GF_FrontDoor_User "Last Person [%s]" (GF_FrontDoor, gLogging) {
    channel="net2:door:server:main_entrance:lastAccessUser"
}

DateTime GF_FrontDoor_Time "Last Access Time [%1$td.%1$tm.%1$tY %1$tH:%1$tM]" (GF_FrontDoor, gLogging) {
    channel="net2:door:server:main_entrance:lastAccessTime"
}

// Calculated - time since last access (using persistence)
String GF_FrontDoor_TimeSince "Time Since Access [%s]" (GF_FrontDoor)
```

### Transform Files

#### door_status.map

```map
ON=ACTIVITY
OFF=IDLE
UNDEF=UNKNOWN
```

## Automation Rules

### Log All Door Access

```openhab
rule "Log door access"
when
    Item GF_FrontDoor_User changed
then
    val user = GF_FrontDoor_User.state
    val time = GF_FrontDoor_Time.state
    logInfo("Access", "Door accessed by " + user + " at " + time)
end
```

### Alert on After-Hours Access

```openhab
rule "Alert on after-hours access"
when
    Item GF_FrontDoor_Time changed
then
    val currentTime = now.getHourOfDay()
    if (currentTime < 6 || currentTime > 22) {
        logWarn("Security", "After-hours access: " + GF_FrontDoor_User.state)
        // Send notification, email, etc.
    }
end
```

### Unlock on Remote Request

```openhab
rule "Remote unlock via Telegram"
when
    Item TelegramCommand changed to "unlock"
then
    logInfo("Door", "Unlock command received via Telegram")
    GF_FrontDoor_Unlock.sendCommand(ON)
    
    // Confirm after 2 seconds
    createTimer(now.plusSeconds(2), [|
        logInfo("Door", "Door unlock executed")
    ])
end
```

### Presence-Based Auto-Lock

```openhab
rule "Auto-lock on absence"
when
    Item Presence changed to OFF
then
    Thread::sleep(300000)  // 5 minute grace period
    if (Presence.state == OFF) {
        logInfo("Door", "No presence detected, securing doors")
        // Send lock command (if binding supports it in future)
    }
end
```

## Persistence & History

### Storing Access Events

Configure RRD4j persistence for access logging:

**persistence/net2.persist**:
```
Items {
    GF_FrontDoor_User, GF_FrontDoor_Time : strategy = everyChange
}
```

### Querying History

```openhab
// Get last 10 accesses (in rule)
val lastAccess = GF_FrontDoor_Time.lastUpdate
val lastUser = GF_FrontDoor_User.state

// Chart setup for influxDB (optional)
Strategies {
    everyChange : "everyChange"
    hourly : "0 0 * * * ?"
}

Items {
    GF_FrontDoor_* : strategy = everyChange, hourly
}
```

## Advanced Configuration

### Multiple Servers

```openhab
Bridge net2:server:server1 [ host="server1.example.com", ... ] {
    Thing door door1 [ doorId="DOOR1" ]
}

Bridge net2:server:server2 [ host="server2.example.com", ... ] {
    Thing door door2 [ doorId="DOOR2" ]
}

// Items for each server
Switch Door1_Status { channel="net2:door:server1:door1:status" }
Switch Door2_Status { channel="net2:door:server2:door2:status" }
```

### Custom Item Formatting

```openhab
// Custom date/time format
DateTime GF_FrontDoor_Time_Custom "Last Access [%1$tA %1$tB %1$td, %1$tI:%1$tM %1$tp]" {
    channel="net2:door:server:main_entrance:lastAccessTime"
}

// Example output: Monday January 07, 03:45 PM
```

### Rule-Based Rate Limiting

```openhab
var Boolean doorUnlockAllowed = true

rule "Rate limit unlock commands"
when
    Item GF_FrontDoor_Unlock received command ON
then
    if (doorUnlockAllowed) {
        doorUnlockAllowed = false
        logInfo("Door", "Processing unlock")
        
        createTimer(now.plusSeconds(5), [|
            doorUnlockAllowed = true
            logInfo("Door", "Unlock command accepted again")
        ])
    } else {
        logWarn("Door", "Unlock rate limited - try again shortly")
    }
end
```

## Sitemaps

### Simple Door Control

```openhab
sitemap doors label="Door Control" {
    Frame label="Front Door" {
        Switch item=GF_FrontDoor_Status label="Activity"
        Switch item=GF_FrontDoor_Unlock label="Unlock"
        Text item=GF_FrontDoor_User
        Text item=GF_FrontDoor_Time
    }
    
    Frame label="Back Door" {
        Switch item=GF_BackDoor_Status label="Activity"
        Switch item=GF_BackDoor_Unlock label="Unlock"
        Text item=GF_BackDoor_User
        Text item=GF_BackDoor_Time
    }
}
```

## See Also

- [README.md](README.md) - Feature overview
- [INSTALLATION.md](INSTALLATION.md) - Setup instructions
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [openHAB Docs](https://www.openhab.org/docs/)
