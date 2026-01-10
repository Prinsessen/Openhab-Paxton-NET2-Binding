# Door State Synchronization

## Overview

The Net2 binding implements a **hybrid synchronization system** that combines SignalR real-time events with API polling to ensure door states in OpenHAB always match the actual Net2 server state, regardless of how doors are controlled.

## Architecture

### Dual Synchronization Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                     Net2 Server                                 │
│  ┌──────────────────────┐      ┌─────────────────────────────┐ │
│  │  SignalR LiveEvents  │      │   REST API                   │ │
│  │  WebSocket           │      │   /api/v1/doors/status       │ │
│  └──────────┬───────────┘      └──────────┬──────────────────┘ │
└─────────────┼────────────────────────────┼────────────────────┘
              │ Real-time Events            │ Polling (30s)
              │ (Instant)                   │ (Guaranteed)
              ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OpenHAB Binding                             │
│  ┌────────────────────┐         ┌──────────────────────────┐   │
│  │  SignalR Client    │         │  API Polling             │   │
│  │  - Door-specific   │         │  - Read doorRelayOpen    │   │
│  │    subscriptions   │         │  - Update both channels  │   │
│  │  - EventType 20/28 │         │  - Every 30 seconds      │   │
│  │  - Instant notify  │         │  - Fallback guarantee    │   │
│  └─────────┬──────────┘         └──────────┬───────────────┘   │
│            └────────────┬──────────────────┘                    │
│                         ▼                                        │
│            ┌─────────────────────────┐                          │
│            │  Door Handler           │                          │
│            │  - action channel       │                          │
│            │  - status channel       │                          │
│            └─────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Why Hybrid?

### SignalR Limitations
- Net2 API documentation mentions `doorEvents` and `doorStatusEvents` hubs
- **Reality**: Only `LiveEvents` hub is implemented
- Events are generic with `eventType` codes, not door-specific
- EventType 47 (door closed) is **inconsistently sent** by the server
- Physical door closures may not generate events

### API Polling Benefits
- Reads actual `doorRelayOpen` status directly
- Guaranteed state accuracy within refresh interval
- Works regardless of event reliability
- Provides synchronization baseline

### Combined Strength
- **SignalR**: Instant updates when doors open (no delay)
- **API Polling**: Guaranteed correctness (30-second accuracy)
- **Result**: Best of both worlds - responsive + reliable

## Signal Flow

### Door Opening Sequence

1. **User Opens Door** (any method: OpenHAB, Net2 UI, card reader)
2. **SignalR Event** (within 1 second)
   - Event received: `eventType: 20` (or 28, 46)
   - `applyEvent()` called in door handler
   - Both `action` and `status` channels → ON
   - OpenHAB UI updates immediately
3. **API Poll** (within 30 seconds)
   - `refreshDoorStatus()` called
   - API returns: `{"id": doorId, "status": {"doorRelayOpen": true}}`
   - `updateFromApiResponse()` confirms state
   - Both channels remain ON (already set by SignalR)

### Door Closing Sequence

1. **Door Closes** (timer expires, manual close, or physical sensor)
2. **SignalR Event** (may or may not arrive)
   - If eventType 47 received: Both channels → OFF immediately
   - If NO event: State remains ON in OpenHAB (desynchronized)
3. **API Poll** (within 30 seconds - guaranteed)
   - `refreshDoorStatus()` called
   - API returns: `{"id": doorId, "status": {"doorRelayOpen": false}}`
   - `updateFromApiResponse()` detects mismatch
   - Both `action` and `status` channels → OFF
   - OpenHAB UI synchronized within 30 seconds

## Implementation Details

### SignalR Integration

**Connection Establishment:**
```java
// Net2ServerHandler.java
signalRClient = new Net2SignalRClient(config.hostname, config.port, ...);
signalRClient.setOnConnectedCallback(this::onSignalRConnected);
signalRClient.connect();
```

**Door Subscription Callback:**
```java
private void onSignalRConnected() {
    getThing().getThings().forEach(childThing -> {
        Net2DoorHandler handler = (Net2DoorHandler) childThing.getHandler();
        if (handler != null) {
            handler.subscribeToSignalREvents();
        }
    });
}
```

**Door-Specific Subscription:**
```java
// Net2DoorHandler.java
public void subscribeToSignalREvents() {
    Net2SignalRClient client = serverHandler.getSignalRClient();
    if (client != null && client.isConnected()) {
        client.subscribeToDoorEvents(doorId);
        logger.info("Subscribed to door events for door ID {}", doorId);
    }
}
```

### Event Processing

**LiveEvents Handler:**
```java
if ("LiveEvents".equalsIgnoreCase(target)) {
    int eventType = payload.get("eventType").getAsInt();
    
    if (eventType == 47) {
        // Door closed - update both channels
        updateState(CHANNEL_DOOR_ACTION, OnOffType.OFF);
        updateState(CHANNEL_DOOR_STATUS, OnOffType.OFF);
        logger.info("Door {} closed (eventType 47)", doorId);
    } 
    else if (eventType == 28 || eventType == 46 || eventType == 20) {
        // Door opened - update both channels instantly
        updateState(CHANNEL_DOOR_STATUS, OnOffType.ON);
        updateState(CHANNEL_DOOR_ACTION, OnOffType.ON);
        // No timer - API polling handles door close detection
        logger.info("Door {} opened (eventType {})", doorId, eventType);
    }
}
```

### API Polling

**Scheduled Refresh:**
```java
// Net2ServerHandler.java
int refreshInterval = config.refreshInterval > 0 ? config.refreshInterval : 30;
refreshJob = scheduler.scheduleWithFixedDelay(
    this::refreshDoorStatus, 
    0, 
    refreshInterval,
    TimeUnit.SECONDS
);
```

**Status Update:**
```java
// Net2DoorHandler.java
public void updateFromApiResponse(JsonArray doorStatusArray) {
    for (JsonObject doorStatus : doorStatusArray) {
        if (doorStatus.get("id").getAsInt() == doorId) {
            JsonObject statusObj = doorStatus.get("status").getAsJsonObject();
            boolean doorRelayOpen = statusObj.get("doorRelayOpen").getAsBoolean();
            OnOffType status = doorRelayOpen ? OnOffType.ON : OnOffType.OFF;
            
            // Update BOTH channels to sync with server
            updateState(CHANNEL_DOOR_ACTION, status);
            updateState(CHANNEL_DOOR_STATUS, status);
            
            logger.info("Door {} doorRelayOpen={} -> {}", doorId, doorRelayOpen, status);
        }
    }
}
```

## Event Types

| EventType | Description | Action | Reliability |
|-----------|-------------|--------|-------------|
| 20 | Access Granted | Door opens via card reader | ✅ Reliable |
| 28 | Door Relay Opened | Timed door control activated | ✅ Reliable |
| 46 | Door Forced/Held | Door held open or forced | ✅ Reliable |
| 47 | Door Closed/Secured | Door physically closed | ⚠️ Inconsistent |

## Channel Behavior

### `action` Channel (Switch, RW)
- **Purpose**: Control door state (send commands)
- **Behavior**: Persistent state
- **Synchronization**: 
  - Set to ON when door opens (SignalR or API)
  - Set to OFF when door closes (API polling guaranteed)
  - Represents intended/actual door state
- **Use Case**: Automation rules that need to know if door is currently open

### `status` Channel (Switch, RO)
- **Purpose**: Monitor door relay status
- **Behavior**: Mirrors actual door state from Net2 server
- **Synchronization**: 
  - Set to ON instantly via SignalR when door opens
  - Set to OFF by API polling when door closes (within refresh interval)
  - Always reflects actual `doorRelayOpen` status
- **Use Case**: UI display of real-time door status

## Configuration

### Refresh Interval

**Default:** 30 seconds  
**Minimum:** 5 seconds (not recommended - API load)  
**Recommended:** 15-60 seconds

```
Bridge net2:net2server:myserver [
    hostname="net2.example.com",
    port=8443,
    refreshInterval=30,  // Seconds between API polls
    ...
]
```

**Considerations:**
- Shorter interval = faster sync, more API load
- 30 seconds provides good balance
- SignalR handles real-time opens; polling only catches closes
- Net2 API has no documented rate limits, but be considerate

## Debugging

### Enable Debug Logging

**Log Levels:**
```
log:set DEBUG org.openhab.binding.net2
```

### Key Log Messages

**SignalR Connection:**
```
[INFO] Net2SignalRClient - Connected to SignalR
[INFO] Net2DoorHandler - Subscribed to door events for door ID 6612642
```

**Real-time Events:**
```
[INFO] Net2DoorHandler - Door 6612642 opened (eventType 20)
[INFO] Net2DoorHandler - Door 6612642 closed (eventType 47)
```

**API Polling:**
```
[DEBUG] Net2ServerHandler - refreshDoorStatus: Starting API poll
[DEBUG] Net2ServerHandler - refreshDoorStatus: Parsed array with 7 doors
[INFO] Net2DoorHandler - updateFromApiResponse: Door 6612642 doorRelayOpen=false -> OFF
```

### Filtering Logs

**Monitor synchronization:**
```bash
tail -f /var/log/openhab/openhab.log | grep -E "refreshDoorStatus|updateFromApiResponse|SignalR event|Door.*opened|Door.*closed"
```

**Check API responses:**
```bash
grep "Got API response" /var/log/openhab/openhab.log | tail -1
```

**Verify SignalR subscriptions:**
```bash
grep "Subscribed to door events" /var/log/openhab/openhab.log
```

## Troubleshooting

### Door state not syncing

**Symptoms:**
- OpenHAB shows door open, but it's actually closed
- UI doesn't update when door closes physically

**Check:**
1. Verify bridge is ONLINE
2. Check SignalR connection in logs: `grep "Connected to SignalR" openhab.log`
3. Verify API polling is running: `grep "refreshDoorStatus" openhab.log`
4. Check refresh interval isn't too long
5. Test API directly: `curl -k https://host:8443/api/v1/doors/status` (with auth)

**Solution:**
- API polling will sync within `refreshInterval` seconds
- Reduce `refreshInterval` if faster sync needed
- Verify network connectivity to Net2 server

### SignalR events not received

**Symptoms:**
- Door opens not shown in real-time
- Only API polling updates work

**Check:**
1. WebSocket connection: `grep "SignalR" openhab.log`
2. Door subscriptions: `grep "Subscribed to door events" openhab.log`
3. Firewall not blocking WebSocket traffic
4. Net2 server SignalR is enabled

**Workaround:**
- API polling provides fallback
- Reduce `refreshInterval` for faster updates without SignalR
- Events are enhancement; polling ensures functionality

### EventType 47 never appears

**Expected Behavior:**
- EventType 47 (door closed) is known to be inconsistent
- This is a Net2 API limitation, not a binding bug

**Mitigation:**
- API polling provides guaranteed close detection
- Synchronization happens within `refreshInterval`
- Hybrid approach specifically designed for this issue

## Performance

### Resource Usage

**SignalR Connection:**
- 1 WebSocket per Net2 server bridge
- Low bandwidth (events only)
- Persistent connection
- Automatic reconnection on disconnect

**API Polling:**
- 1 HTTP request per refresh cycle
- Response size: ~200-500 bytes per door
- Default: 1 request every 30 seconds
- Negligible network impact

**CPU/Memory:**
- Minimal overhead
- Event processing is lightweight
- JSON parsing is efficient
- No significant impact on OpenHAB

## Best Practices

1. **Use Default Refresh Interval (30s)**
   - Good balance between responsiveness and efficiency
   - SignalR handles real-time opens anyway

2. **Monitor Logs Initially**
   - Verify SignalR subscriptions successful
   - Check API polling is running
   - Confirm door state changes appear in logs

3. **Trust the Hybrid System**
   - SignalR provides instant open notifications
   - API polling guarantees correctness
   - No manual intervention needed

4. **Design Automation Accordingly**
   - Don't rely solely on instant close notifications
   - Account for up to 30-second sync delay on closes
   - Use `action` channel for persistent state checks

## Future Enhancements

### Potential Improvements

- **Adaptive Polling**: Increase frequency when doors active, decrease when idle
- **Event Caching**: Store recent events to detect patterns
- **Predictive Sync**: Anticipate closes based on typical door timing
- **WebSocket Monitoring**: Auto-adjust polling if SignalR disconnects

### Net2 API Wishlist

- Implement documented `doorEvents` hub
- Reliable eventType 47 (door closed) events
- Direct door status push notifications
- Reduced polling necessity

## Author

**Nanna Agesen** (@Prinsessen)
- Email: nanna@agesen.dk
- GitHub: https://github.com/Prinsessen

## Version

Synchronization system implemented in binding version 5.2.0 (January 9, 2026)
