# Net2 Timed Door Control Channel Examples

## Default Door Control (Hold Open/Close)

The standard `action` channel allows you to hold a door open or close it immediately. Example item and sitemap usage:

**Items:**
```openhab
Switch Net2_Door1_Action "Door 1 Action" { channel="net2:door:server:door1:action" }
```

**Sitemap:**
```openhab
Switch item=Net2_Door1_Action label="Door 1 (Hold Open/Close)"
```

- Sending `ON` will hold the door open (until manually closed or timeout in Net2 config).
- Sending `OFF` will close/lock the door.

## Advanced Timed Door Control (controlTimed Channel)

The new `controlTimed` channel allows you to trigger a door open for a specific time (server-side timing) and optionally customize the payload (e.g., LED flash).

**Items:**
```openhab
Number Net2_Door1_ControlTimed "Door 1 Timed Open" { channel="net2:door:server:door1:controlTimed" }
```

**Sitemap:**
```openhab
Switch item=Net2_Door1_ControlTimed label="Door 1 Timed Open (5s)" mappings=[1="Open 5s"]
```

- Sending `1` will trigger a timed open (default 5 seconds, as set in the handler or thing config).
- You can use rules to send custom values for different open times:

```openhab
rule "Open Door 1 for 10 seconds"
when
    Item Some_Trigger received command ON
then
    Net2_Door1_ControlTimed.sendCommand(10) // Opens for 10 seconds
end
```

### Custom Payload (Advanced)

If you want to send a custom payload (e.g., different LED flash count), you can extend the handler or use a rule to send a specific value. The handler will map the number to the correct JSON payload for the API:

```json
{
  "DoorId": "6612642",
  "RelayFunction": {
    "RelayId": "Relay1",
    "RelayAction": "TimedOpen",
    "RelayOpenTime": 1000 // milliseconds
  },
  "LedFlash": 3
}
```

- The value you send (e.g., `10`) is interpreted as seconds and converted to milliseconds in the payload.
- LED flash and other advanced options can be set in the handler or by extending the rule logic.

## Summary Table

| Channel         | Item Type | Usage Example                | Description                                 |
|----------------|-----------|------------------------------|---------------------------------------------|
| action         | Switch    | ON/OFF                       | Hold open/close door                        |
| controlTimed   | Number    | 1, 5, 10 (seconds)           | Timed open with server-side timing          |

## Author

- Nanna Agesen (@Prinsessen)
- Email: nanna@agesen.dk
- GitHub: https://github.com/Prinsessen
