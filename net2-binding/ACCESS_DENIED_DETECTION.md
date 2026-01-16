# Access Denied Detection

Comprehensive guide for implementing security alerts using the Net2 binding's access denied detection feature.

## Overview

The `accessDenied` channel monitors Net2 SignalR LiveEvents for unauthorized access attempts (eventType 23). When an invalid card or token is presented to any Net2 reader, the binding captures:

- Token/card number that was rejected
- Door name where the attempt occurred  
- Exact timestamp of the attempt
- Net2 door ID for correlation

This enables real-time security monitoring and automated alerting via email, SMS, push notifications, or integration with security systems.

## Architecture

### Event Flow

```
Net2 Reader → Net2 Controller → Net2 Server → SignalR → OpenHAB Binding → accessDenied Channel → Rules → Alerts
```

1. **Detection**: Invalid card presented to Net2 reader
2. **Net2 Processing**: Controller sends eventType 23 to Net2 server
3. **SignalR Streaming**: Server broadcasts LiveEvents over SignalR connection
4. **Binding Processing**: Handler detects eventType 23, builds JSON payload
5. **Channel Update**: `accessDenied` channel receives JSON data
6. **Rule Trigger**: OpenHAB rule processes the event
7. **Alert Dispatch**: Email/SMS/webhook sent to security team

### Why This Matters

Traditional Net2 systems only log denied access attempts in the database. This binding provides **real-time** detection and alerting, enabling:

- Immediate security response to unauthorized access attempts
- Integration with existing security systems (cameras, alarms)
- Custom alerting workflows (escalation, on-call rotation)
- Analytics and pattern detection (repeated attempts, suspicious tokens)

## Configuration

### Step 1: Items Definition

Create items for each door you want to monitor:

**File: items/net2.items**

```openhab
// Access Denied Detection
String Net2_Door1_AccessDenied "Front Door Access Denied" { channel="net2:door:server:door1:accessDenied" }
String Net2_Door2_AccessDenied "Side Door Access Denied" { channel="net2:door:server:door2:accessDenied" }
String Net2_Door3_AccessDenied "Garage Access Denied" { channel="net2:door:server:door3:accessDenied" }
String Net2_Door4_AccessDenied "Basement Access Denied" { channel="net2:door:server:door4:accessDenied" }
String Net2_Door5_AccessDenied "Back Door Access Denied" { channel="net2:door:server:door5:accessDenied" }
```

**Channel Binding Format:**
- `channel="net2:door:<bridge-id>:<thing-id>:accessDenied"`
- Replace `<bridge-id>` with your Net2 server bridge ID (e.g., `server`)
- Replace `<thing-id>` with your door thing ID (e.g., `door1`, `door2`)

### Step 2: Rule Implementation

#### Multi-Door Alert Rule (Production-Ready)

This rule handles all doors and uses timestamp comparison to identify the triggering door:

**File: rules/net2_access_denied.rules**

```openhab
rule "Alert on Access Denied - All Doors"
when
    Item Net2_Door1_AccessDenied received update or
    Item Net2_Door2_AccessDenied received update or
    Item Net2_Door3_AccessDenied received update or
    Item Net2_Door4_AccessDenied received update or
    Item Net2_Door5_AccessDenied received update
then
    // Find the door with the most recent access denied event by comparing timestamps
    var String jsonData = ""
    var String latestTimestamp = ""
    
    // Check Door 1
    var state1 = Net2_Door1_AccessDenied.state.toString()
    if (state1 != "NULL" && state1.contains("tokenNumber")) {
        try {
            var ts1 = transform("JSONPATH", "$.timestamp", state1)
            if (latestTimestamp == "" || ts1 > latestTimestamp) {
                latestTimestamp = ts1
                jsonData = state1
            }
        } catch (Exception e) {}
    }
    
    // Check Door 2
    var state2 = Net2_Door2_AccessDenied.state.toString()
    if (state2 != "NULL" && state2.contains("tokenNumber")) {
        try {
            var ts2 = transform("JSONPATH", "$.timestamp", state2)
            if (latestTimestamp == "" || ts2 > latestTimestamp) {
                latestTimestamp = ts2
                jsonData = state2
            }
        } catch (Exception e) {}
    }
    
    // Check Door 3
    var state3 = Net2_Door3_AccessDenied.state.toString()
    if (state3 != "NULL" && state3.contains("tokenNumber")) {
        try {
            var ts3 = transform("JSONPATH", "$.timestamp", state3)
            if (latestTimestamp == "" || ts3 > latestTimestamp) {
                latestTimestamp = ts3
                jsonData = state3
            }
        } catch (Exception e) {}
    }
    
    // Check Door 4
    var state4 = Net2_Door4_AccessDenied.state.toString()
    if (state4 != "NULL" && state4.contains("tokenNumber")) {
        try {
            var ts4 = transform("JSONPATH", "$.timestamp", state4)
            if (latestTimestamp == "" || ts4 > latestTimestamp) {
                latestTimestamp = ts4
                jsonData = state4
            }
        } catch (Exception e) {}
    }
    
    // Check Door 5
    var state5 = Net2_Door5_AccessDenied.state.toString()
    if (state5 != "NULL" && state5.contains("tokenNumber")) {
        try {
            var ts5 = transform("JSONPATH", "$.timestamp", state5)
            if (latestTimestamp == "" || ts5 > latestTimestamp) {
                latestTimestamp = ts5
                jsonData = state5
            }
        } catch (Exception e) {}
    }
    
    if (jsonData == "") {
        logWarn("net2_access_denied", "No valid access denied data found")
        return
    }
    
    // Parse JSON to extract details
    try {
        val doorName = transform("JSONPATH", "$.doorName", jsonData)
        val tokenNumber = transform("JSONPATH", "$.tokenNumber", jsonData)
        val timestamp = transform("JSONPATH", "$.timestamp", jsonData)
        val doorId = transform("JSONPATH", "$.doorId", jsonData)
        
        // Extract time from timestamp (HH:mm:ss)
        val timeStr = timestamp.substring(11, 19)
        
        val alertMessage = "⚠️ UNAUTHORIZED ACCESS ATTEMPT at " + doorName + 
                          "\nToken/Card: " + tokenNumber + 
                          "\nTime: " + timeStr + 
                          "\nDoor ID: " + doorId
        
        logWarn("net2_access_denied", alertMessage)
        
        // Send email notifications (requires mail binding)
        val mailActions = getActions("mail", "mail:smtp:samplesmtp")
        
        // Email 1: Detailed notification to security team
        val success1 = mailActions.sendMail(
            "security@example.com",
            "⚠️ Net2 Unauthorized Access Alert",
            "SECURITY ALERT: Unauthorized Access Attempt\n\n" +
            "Door: " + doorName + "\n" +
            "Token/Card Number: " + tokenNumber + "\n" +
            "Time: " + timeStr + "\n" +
            "Door ID: " + doorId + "\n\n" +
            "An invalid card or token was presented to the reader.\n" +
            "Please review security footage and door logs.\n\n" +
            "This is an automated alert from OpenHAB Net2 Binding."
        )
        logInfo("net2_access_denied", "Email sent to security@example.com - Status: " + success1)
        
        // Email 2: SMS via email-to-SMS gateway
        val success2 = mailActions.sendMail(
            "1234567890@sms.gateway.com",
            "Net2 Alert",
            "SECURITY: Unauthorized access at " + doorName + " - Token " + tokenNumber + " at " + timeStr
        )
        logInfo("net2_access_denied", "SMS sent - Status: " + success2)
        
    } catch (Exception e) {
        logError("net2_access_denied", "Error processing access denied event: " + e.getMessage())
    }
end
```

#### Single-Door Simplified Rule

For monitoring just one door:

```openhab
rule "Alert on Front Door Access Denied"
when
    Item Net2_Door1_AccessDenied received update
then
    val jsonData = Net2_Door1_AccessDenied.state.toString()
    
    if (jsonData == "NULL" || !jsonData.contains("tokenNumber")) {
        return
    }
    
    try {
        val doorName = transform("JSONPATH", "$.doorName", jsonData)
        val tokenNumber = transform("JSONPATH", "$.tokenNumber", jsonData)
        val timestamp = transform("JSONPATH", "$.timestamp", jsonData)
        
        logWarn("net2_security", "Access DENIED at " + doorName + ": Token " + tokenNumber)
        
        // Send notification
        val mailActions = getActions("mail", "mail:smtp:samplesmtp")
        mailActions.sendMail(
            "security@example.com",
            "Security Alert - " + doorName,
            "Invalid token " + tokenNumber + " presented at " + timestamp
        )
    } catch (Exception e) {
        logError("net2_security", "Error: " + e.getMessage())
    }
end
```

### Step 3: Mail Binding Configuration

Configure the Mail binding for email/SMS delivery:

**Option A: Via Configuration File**

**File: services/mail.cfg**

```properties
# SMTP Server Configuration
smtp.server=smtp.gmail.com
smtp.port=587
smtp.username=your-email@gmail.com
smtp.password=your-app-password
smtp.from=openhab@example.com
smtp.tls=true
smtp.auth=true
```

**Option B: Via UI**

1. Settings → Things → Add Thing → Mail Binding
2. Create SMTP Server thing
3. Configure hostname, port, credentials
4. Save configuration

**Gmail Setup:**
- Use App Passwords (not your regular password)
- Generate at: https://myaccount.google.com/apppasswords
- Enable 2FA if not already enabled

## JSON Payload Format

When access is denied, the channel receives this JSON structure:

```json
{
  "tokenNumber": "1234567",
  "doorName": "Front Door",
  "timestamp": "2026-01-16T17:26:50",
  "doorId": 6612642
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `tokenNumber` | String | The card/token number that was rejected |
| `doorName` | String | Human-readable door name (from thing label) |
| `timestamp` | String | ISO 8601 timestamp of the denied access attempt |
| `doorId` | Number | Net2 internal door ID (serial number) |

### Parsing with JSONPATH

Use the JSONPATH transformation to extract fields:

```openhab
val doorName = transform("JSONPATH", "$.doorName", jsonData)
val tokenNumber = transform("JSONPATH", "$.tokenNumber", jsonData)
val timestamp = transform("JSONPATH", "$.timestamp", jsonData)
val doorId = transform("JSONPATH", "$.doorId", jsonData)
```

## Advanced Use Cases

### Integration with Camera System

Trigger camera recording when access is denied:

```openhab
rule "Record Camera on Access Denied"
when
    Item Net2_Door1_AccessDenied received update
then
    val jsonData = Net2_Door1_AccessDenied.state.toString()
    if (jsonData == "NULL" || !jsonData.contains("tokenNumber")) return
    
    // Trigger camera recording (example for Hikvision/Dahua)
    sendCommand(SecurityCamera_Door1_Record, ON)
    
    // Or via HTTP binding
    sendHttpGetRequest("http://camera-ip/api/startRecording?door=1")
end
```

### Pattern Detection (Repeated Attempts)

Detect multiple failed attempts within a time window:

```openhab
var Timer repeatAlertTimer = null
var int attemptCount = 0
var String lastToken = ""

rule "Detect Repeated Access Attempts"
when
    Item Net2_Door1_AccessDenied received update
then
    val jsonData = Net2_Door1_AccessDenied.state.toString()
    if (jsonData == "NULL" || !jsonData.contains("tokenNumber")) return
    
    val tokenNumber = transform("JSONPATH", "$.tokenNumber", jsonData)
    
    if (tokenNumber == lastToken) {
        attemptCount = attemptCount + 1
        
        if (attemptCount >= 3) {
            logError("net2_security", "⚠️⚠️⚠️ REPEATED ACCESS ATTEMPTS: Token " + tokenNumber + " attempted " + attemptCount + " times!")
            
            // Send high-priority alert
            val mailActions = getActions("mail", "mail:smtp:samplesmtp")
            mailActions.sendMail(
                "security@example.com",
                "🚨 URGENT: Repeated Unauthorized Access Attempts",
                "Token " + tokenNumber + " has attempted access " + attemptCount + " times in quick succession.\n\nPossible security breach in progress!"
            )
        }
    } else {
        lastToken = tokenNumber
        attemptCount = 1
    }
    
    // Reset counter after 5 minutes
    if (repeatAlertTimer !== null) repeatAlertTimer.cancel()
    repeatAlertTimer = createTimer(now.plusMinutes(5), [ |
        attemptCount = 0
        lastToken = ""
    ])
end
```

### SMS via Different Providers

#### Uni-Tel (Denmark)
```openhab
mailActions.sendMail("phonenumber@sms.uni-tel.dk", "Subject", "Message")
```

#### Twilio Email-to-SMS
```openhab
mailActions.sendMail("phonenumber@txt.voice.google.com", "Subject", "Message")
```

#### AT&T
```openhab
mailActions.sendMail("phonenumber@txt.att.net", "Subject", "Message")
```

#### Verizon
```openhab
mailActions.sendMail("phonenumber@vtext.com", "Subject", "Message")
```

### Webhook Integration (Slack/Discord/Teams)

Send alerts to team chat:

```openhab
rule "Send Slack Alert on Access Denied"
when
    Item Net2_Door1_AccessDenied received update
then
    val jsonData = Net2_Door1_AccessDenied.state.toString()
    if (jsonData == "NULL" || !jsonData.contains("tokenNumber")) return
    
    val doorName = transform("JSONPATH", "$.doorName", jsonData)
    val tokenNumber = transform("JSONPATH", "$.tokenNumber", jsonData)
    val timestamp = transform("JSONPATH", "$.timestamp", jsonData)
    
    val slackPayload = '{' +
        '"text": "🚨 Security Alert",' +
        '"blocks": [{' +
            '"type": "section",' +
            '"text": {' +
                '"type": "mrkdwn",' +
                '"text": "*Unauthorized Access Attempt*\\n*Door:* ' + doorName + '\\n*Token:* ' + tokenNumber + '\\n*Time:* ' + timestamp + '"' +
            '}' +
        '}]' +
    '}'
    
    sendHttpPostRequest("https://hooks.slack.com/services/YOUR/WEBHOOK/URL", "application/json", slackPayload)
end
```

## Troubleshooting

### No Events Received

**Check binding logs:**
```bash
grep "Access DENIED" /var/log/openhab/openhab.log
```

**Verify SignalR connection:**
```bash
grep "SignalR.*Connected\|SignalR.*Subscribed" /var/log/openhab/openhab.log
```

**Test with invalid card:**
- Present an expired/deleted card to a reader
- Check logs immediately

### Wrong Door Reported

**Issue:** Email says "Front Door" but you tested at "Garage Door"

**Cause:** Multi-door rule not comparing timestamps correctly

**Solution:** Verify timestamp comparison logic includes all doors

### Emails Not Sending

**Check mail binding status:**
```bash
openhab-cli console
> bundle:list | grep mail
```

**Test mail binding:**
```bash
curl -X POST "http://localhost:8080/rest/items/TestMail" \
  -H "Content-Type: text/plain" \
  -d "test@example.com|Test Subject|Test Message"
```

**Check logs:**
```bash
grep "mail" /var/log/openhab/openhab.log | tail -20
```

### Rule Not Triggering

**Verify item is receiving updates:**
```bash
grep "Net2_Door.*AccessDenied.*received update" /var/log/openhab/events.log
```

**Check rule syntax:**
```bash
openhab-cli console
> log:tail
# Look for rule compilation errors
```

## Testing

### Test Procedure

1. **Create test token** in Net2 with expired date
2. **Present token** to reader
3. **Check binding logs** for event detection
4. **Verify rule execution** in openhab.log
5. **Confirm alert delivery** (email/SMS)

### Expected Log Output

```
2026-01-16 17:26:50.450 [WARN ] [binding.net2.handler.Net2DoorHandler] - Access DENIED at door Front Door: Token 1234567 at 2026-01-16T17:26:50
2026-01-16 17:26:50.628 [WARN ] [core.model.script.net2_access_denied] - ⚠️ UNAUTHORIZED ACCESS ATTEMPT at Front Door
2026-01-16 17:26:55.005 [INFO ] [core.model.script.net2_access_denied] - Email sent to security@example.com - Status: true
2026-01-16 17:26:57.055 [INFO ] [core.model.script.net2_access_denied] - SMS sent - Status: true
```

## Performance Considerations

- **Event frequency**: Net2 can generate many events; consider rate limiting for high-traffic scenarios
- **Email quotas**: Check SMTP provider limits (Gmail: 500/day, Office365: varies)
- **Rule execution time**: JSONPATH transforms are fast (<10ms), but network calls (email/HTTP) can take 1-2 seconds
- **State persistence**: Access denied JSON persists in item state; no database persistence needed for real-time alerts

## Security Best Practices

1. **Secure SMTP credentials**: Use app passwords, not primary passwords
2. **Rate limiting**: Implement cooldown periods for repeated alerts
3. **Alert escalation**: Different recipients based on time/severity
4. **Log retention**: Consider persistence for access denied events for auditing
5. **Separate alert channels**: Email for detailed logs, SMS for urgent alerts

## Related Documentation

- [EXAMPLES.md](EXAMPLES.md) - Complete configuration examples
- [ENTRY_LOGGING.md](ENTRY_LOGGING.md) - Authorized access logging
- [README.md](README.md) - Binding overview and installation

## Support

For issues or questions:
- Check logs: `/var/log/openhab/openhab.log` and `events.log`
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if available
- OpenHAB Community Forum: https://community.openhab.org/
