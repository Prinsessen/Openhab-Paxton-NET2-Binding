# Paxton Net2 Binding Troubleshooting Guide

## Common Issues and Solutions

### Server Bridge Offline or Connection Failed

#### Symptoms
- Thing status shows "OFFLINE" or "ERROR"
- Logs show connection refused or timeout
- No door events appearing

#### Diagnosis Steps

1. **Check network connectivity**:
   ```bash
   ping milestone.agesen.dk
   curl -k https://milestone.agesen.dk:8443/api/v1/version
   ```

2. **Verify credentials**:
   - Confirm username/password are correct
   - Check OAuth Client ID and Secret
   - Verify OAuth app exists on Net2 server

3. **Check firewall**:
   ```bash
   nc -zv milestone.agesen.dk 8443
   # Should output: Connection successful
   ```

4. **Enable debug logging**:
   - Add to `/etc/openhab/services/logging.cfg`:
   ```
   log4j.logger.org.openhab.binding.net2 = DEBUG
   ```
   - Restart openHAB and check logs

#### Solutions

**Invalid Credentials**
```
Error: 401 Unauthorized
```
- Double-check username and password
- Verify OAuth application is still valid (not expired)
- Request new OAuth credentials from Net2 admin
- Test manually: `curl -u admin:password https://server:8443/api/v1/doors`

**Self-Signed Certificate Error**
```
javax.net.ssl.SSLHandshakeException: CERTIFICATE_VERIFY_FAILED
```
- Net2 server uses self-signed HTTPS certificate (common)
- **Temporary workaround**: Add certificate to Java truststore
- **Better solution**: Request proper SSL certificate from Net2 admin
- Check if `useHttps=true` is correct (disable to `false` if using HTTP)

**Port or Hostname Wrong**
```
Connection refused
java.net.ConnectException: Connection refused
```
- Verify `host` setting (check DNS resolution)
- Verify `port` setting (default 8443)
- Check if Net2 service is running: `telnet milestone.agesen.dk 8443`

**Firewall Blocking**
```
Connection timed out
java.net.SocketTimeoutException
```
- Check outbound firewall rules on openHAB server
- Verify Net2 server firewall allows inbound connections
- Check if proxy is required

### OAuth Token Refresh Fails

#### Symptoms
- Binding connects initially, then goes offline after 30 minutes
- Repeated error: "Token refresh failed"
- lastAccessUser/Time items stop updating

#### Root Causes

1. **OAuth credentials incorrect or expired**
   - Client ID or Secret changed on Net2 server
   - OAuth app was deleted
   - Credentials not sent to openHAB during refresh

2. **OAuth token endpoint unreachable**
   - Network timeout
   - Net2 service restarted during token refresh
   - Firewall blocking token refresh

3. **OAuth scope missing**
   - OAuth app doesn't have required permissions
   - Token doesn't include `door:read` or `door:write` scopes

#### Solutions

**Regenerate OAuth Credentials** (Net2 Admin):
1. Go to Net2 admin panel → System → OAuth Applications
2. Find openHAB application
3. Regenerate Client Secret
4. Update openHAB configuration with new credentials
5. Restart openHAB bridge

**Check Token Expiry in Logs**:
```bash
grep -i "token\|oauth\|refresh" /var/log/openhab/openhab.log | tail -20
```

**Manual Token Refresh Test**:
```bash
# Using Basic Auth to get Bearer token
curl -u admin:password \
  -X POST \
  https://milestone.agesen.dk:8443/api/v1/auth/token \
  -k

# Response should include access_token and expires_in
```

**Verify OAuth App Scopes** (Net2 Admin):
- Confirm OAuth app has these scopes:
  - `door:read` - Access to door status
  - `access:read` - Access history
  - `door:write` (optional) - Door control

### No Real-Time Door Events (lastAccessUser/Time not updating)

#### Symptoms
- Door access happens but items don't update
- Status channel shows no activity
- Only periodic API polling shows new access

#### Root Causes

1. **WebSocket connection not established**
   - SignalR negotiation fails
   - WebSocket protocol not supported
   - Network blocking WebSocket traffic

2. **SignalR event subscription failed**
   - Event types not recognized
   - Server not sending events
   - Binding not listening

3. **API polling only** (fallback mode)
   - WebSocket disabled or unavailable
   - Updates appear only every 30 minutes (refresh interval)

#### Diagnosis

**Check WebSocket Connection Status in Logs**:
```bash
grep -i "websocket\|signalr\|connected" /var/log/openhab/openhab.log | tail -10

# Expected successful messages:
# [INFO] SignalR WebSocket connected successfully
# [INFO] Event subscription sent
# [DEBUG] SignalR message received
```

**Enable Network Trace** (advanced):
```bash
# Monitor WebSocket traffic
tcpdump -i eth0 -n 'tcp port 8443' | grep -i websocket
```

**Test WebSocket Manually**:
```bash
# Try establishing WebSocket (requires Bearer token)
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Authorization: Bearer <TOKEN>" \
  https://milestone.agesen.dk:8443/signalr/connect?connectionData=%5B%5D \
  -k
```

#### Solutions

**Firewall Blocking WebSocket**:
- Check outbound traffic on ports 8443, 443, 80
- WebSocket uses HTTP Upgrade protocol on same port
- Add firewall exception for Net2 server IP

**Net2 Server Issues**:
```
Error: SignalR negotiate failed (404)
```
- Net2 Classic SignalR 2 not enabled (`/signalr/*` endpoints missing)
- Contact Net2 admin: "Enable SignalR protocol for event streaming"
- Fallback: Binding switches to 30-minute API polling

**Event Types Not Recognized**:
- Check server logs for event codes: `[DEBUG] Unknown event type: XX`
- These are usually harmless (access types not yet in binding)
- File GitHub issue with event type code for support

**Forced WebSocket Reset**:
1. Go to Things → Net2 Server bridge
2. Click ⋮ (options) → Restart Bridge
3. Check logs for reconnection
4. If still issues, restart full openHAB: `sudo systemctl restart openhab`

### Door Status Stuck ON or OFF

#### Symptoms
- Status channel stuck as ON or OFF
- Auto-off timer not working
- Status resets only after openHAB restart

#### Root Causes

1. **Auto-off timer cancelled unexpectedly**
   - Binding restarted during timer
   - Thread pool shutdown

2. **Event processed but state not updated**
   - Channel linking issue
   - Item not linked to channel

#### Solutions

**Check Item Link**:
1. Go to Thing → Net2 Door
2. Verify each channel has an item linked
3. Click channel → select item in dropdown
4. Save and restart binding

**Manual Reset**:
```openhab
// In console or rule
Net2_Door_Status.postUpdate(OFF)
```

**Full Reset** (last resort):
1. Remove bridge and all doors from Things
2. Remove all related items
3. Restart openHAB
4. Recreate Things and Items
5. Force discovery and link channels again

### Items Show UNDEF or NULL State

#### Symptoms
- `lastAccessUser` or `lastAccessTime` show UNDEF
- Items never populate with values
- Status shows as NULL instead of ON/OFF

#### Root Causes

1. **Bridge not online**
   - Can't fetch initial API data
   - UNDEF is initial state until API responds

2. **No access events yet**
   - Door hasn't been accessed since binding started
   - API returns no data for never-accessed doors

3. **Item not properly initialized**
   - System not started rule to initialize items
   - Null pointer exception in state updates

#### Solutions

**Wait for Initial API Response**:
- Binding polls every 30 minutes by default
- First successful poll populates lastAccessUser/Time
- If still UNDEF after 35 minutes, check bridge status

**Trigger Manual API Refresh**:
1. Go to Things → Net2 Server bridge
2. Click ⋮ (options) → Manual Refresh (if available)
3. Or: Restart bridge to force immediate refresh

**Initialize Items on System Start**:
```openhab
rule "Initialize Net2 items"
when
    System started
then
    // Request current values from binding
    Net2_Door_Status.postUpdate(OFF)  // Set default to OFF
    logInfo("Net2", "Items initialized")
end
```

**Check for Exceptions in Logs**:
```bash
grep -i "exception\|error" /var/log/openhab/openhab.log | grep -i "net2\|door"
```

### Door Unlock Action Not Working

#### Symptoms
- Sending command ON to unlock channel has no effect
- No error shown but door doesn't unlock
- No response in logs

#### Root Causes

1. **Action channel is write-only**
   - Item type should be Switch, not String
   - Channel link might be one-way

2. **Binding doesn't have unlock permission**
   - OAuth app doesn't have `door:write` scope
   - Admin user doesn't have unlock permission

3. **Unlock command not reaching Net2 server**
   - Network error
   - Server offline
   - Command format incorrect

#### Solutions

**Verify Item Type**:
```openhab
// Correct:
Switch Net2_Door_Unlock { channel="net2:door:server:main:action" }

// Wrong:
String Net2_Door_Unlock { channel="..." }  // Won't work for write-only
```

**Grant Unlock Permission** (Net2 Admin):
1. Verify OAuth app has `door:write` scope
2. Verify admin user account has unlock permission
3. Test manually:
   ```bash
   curl -X PUT \
     -H "Authorization: Bearer <TOKEN>" \
     -d "" \
     https://milestone.agesen.dk:8443/api/v1/doors/main_entrance/unlock \
     -k
   ```

**Check Command in Logs**:
```bash
grep -i "unlock\|action" /var/log/openhab/openhab.log | tail -5

# Expected:
# [DEBUG] Unlock command sent to Net2 server
# [INFO] Door unlock processed
```

**Manual Test in UI**:
1. Go to Items in UI
2. Find `Net2_Door_Unlock` item
3. Click dropdown, select "ON"
4. Send command
5. Check logs immediately for response

### High CPU or Memory Usage

#### Symptoms
- openHAB process consuming excessive resources
- WebSocket repeatedly disconnecting/reconnecting
- Constant polling even when bridge appears online

#### Root Causes

1. **WebSocket reconnection loop**
   - Connection drops every few seconds
   - Binding tries to reconnect repeatedly
   - Exhausts CPU and memory

2. **Memory leak in event buffering**
   - Too many events cached
   - Not properly clearing event queue

3. **Too many Things/Items**
   - 100+ doors can create overhead
   - API polling taking too long

#### Solutions

**Check for Reconnection Loop**:
```bash
# Count reconnection messages
grep -c "WebSocket connected\|WebSocket disconnected" /var/log/openhab/openhab.log

# If alternating frequently (within seconds), investigate bridge
```

**Increase refresh interval** (reduce API polling):
- Edit bridge configuration
- Change `refreshInterval` from 30 to 60 minutes
- Restart binding
- Monitor resources

**Check Memory Usage**:
```bash
# Monitor openHAB JVM memory
ps aux | grep openhab
jmap -heap $(pidof java)
```

**Limit WebSocket Message Logging** (reduce disk I/O):
- Edit `/etc/openhab/services/logging.cfg`:
```
log4j.logger.org.openhab.binding.net2.handler.Net2SignalRClient = INFO
# Change from DEBUG to INFO to reduce message spam
```

**Restart Binding**:
1. Go to Things → Net2 Server
2. Click ⋮ → Restart
3. Monitor resource usage for 5 minutes
4. Should stabilize to normal levels

### Multiple Servers / Many Doors

#### Symptoms
- Configuration works with 1 server/5 doors
- Breaks with 2 servers/20 doors
- Random timeouts or connection issues

#### Solutions

**Stagger API Refresh**:
- Set different `refreshInterval` for each bridge
- Bridge1: 30 minutes, Bridge2: 35 minutes
- Prevents all polling at same time

**Increase Thread Pool** (for binding):
- Edit `/etc/openhab/services/runtime.cfg`:
```
org.openhab.binding.net2.thread.pool.size=10
```
- Default is 5 threads; increase if >20 doors

**Monitor Bridge Status**:
```bash
# Check if bridges dropping offline
grep "Bridge.*OFFLINE\|Bridge.*ONLINE" /var/log/openhab/openhab.log | tail -20
```

## Debug Logging Setup

Enable comprehensive logging to diagnose issues:

### Step 1: Edit logging configuration

Edit `/etc/openhab/services/logging.cfg`:

```properties
# Net2 Binding
log4j.logger.org.openhab.binding.net2 = DEBUG
log4j.logger.org.openhab.binding.net2.handler = DEBUG
log4j.logger.org.openhab.binding.net2.handler.Net2SignalRClient = DEBUG
```

### Step 2: Restart openHAB

```bash
sudo systemctl restart openhab
```

### Step 3: Reproduce Issue

- Perform action that fails (e.g., swipe door, unlock)
- Watch logs in real-time:
```bash
tail -f /var/log/openhab/openhab.log | grep -i "net2"
```

### Step 4: Collect Logs

```bash
# Save last 1000 lines of relevant logs
grep net2 /var/log/openhab/openhab.log | tail -1000 > /tmp/net2_debug.log
```

### Step 5: Disable Debug (after troubleshooting)

```properties
log4j.logger.org.openhab.binding.net2 = INFO
```

## Getting Help

### Community Support
- **openHAB Forums**: https://community.openhab.org
- Tag posts with `net2` and `paxton`
- Include:
  - openHAB version
  - Binding version
  - Relevant logs (DEBUG level)
  - Network diagram
  - Net2 server version

### GitHub Issues
- Report bugs: https://github.com/Prinsessen/Openhab-Paxton-NET2-Binding/issues
- Include:
  - Detailed error description
  - Steps to reproduce
  - Log output (DEBUG, sanitized)
  - Network setup

### Net2 Support
- Contact Paxton directly for:
  - OAuth configuration help
  - API endpoint verification
  - SignalR protocol troubleshooting
  - Certificate/SSL issues

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `401 Unauthorized` | Bad credentials | Check username/password |
| `403 Forbidden` | No permission | Check OAuth scopes |
| `404 Not Found` | Endpoint missing | SignalR not enabled |
| `Connection refused` | Server unreachable | Check host/port/firewall |
| `CERTIFICATE_VERIFY_FAILED` | SSL certificate issue | Trust self-signed cert or disable HTTPS |
| `Socket timeout` | No response from server | Check server status, network |
| `Event subscription failed` | SignalR negotiation error | Check connection logs |
| `Token refresh failed` | OAuth token endpoint error | Check OAuth app configuration |

## Performance Tuning

### Reduce Network Traffic
- Increase `refreshInterval` (fewer API polls)
- Disable WebSocket and rely on polling (remove `useSignalR` if option added)
- Filter event types in binding (ignore unused events)

### Improve Responsiveness
- Decrease `refreshInterval` (more frequent updates)
- Enable WebSocket (real-time events)
- Add more threads to executor

### Balance Resources
- Default: 30-minute polling, WebSocket enabled
- Good for: 5-10 doors, normal automation
- High-traffic: 60-minute polling, limit logging
- Real-time requirements: 5-minute polling, WebSocket only

## See Also

- [README.md](README.md) - Feature overview
- [INSTALLATION.md](INSTALLATION.md) - Setup guide
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration details
- [openHAB Troubleshooting](https://www.openhab.org/docs/troubleshooting/)
