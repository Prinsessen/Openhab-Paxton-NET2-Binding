# Net2 Binding Version 5.2.0 - Release Notes

**Release Date:** January 9, 2026  
**Author:** Nanna Agesen (@Prinsessen)

## Major Feature: Hybrid Door State Synchronization

Version 5.2.0 introduces a comprehensive synchronization system that ensures OpenHAB door states always match the Net2 server, regardless of control method.

## What's New

### Real-time Synchronization
- **SignalR WebSocket** integration for instant door open notifications
- **API Polling** fallback for guaranteed state accuracy
- Both `action` and `status` channels now synchronized
- Works with any control method: OpenHAB UI, Net2 UI, card readers, physical sensors

### How It Works

```
Door Opens → SignalR Event (instant) → OpenHAB UI updates immediately
Door Closes → API Poll (≤30s) → OpenHAB UI syncs within refresh interval
```

**Why Both?**
- Net2 API's eventType 47 (door closed) is unreliable
- SignalR provides instant open detection
- API polling provides authoritative close detection
- No timer needed - real state from API

## Key Changes

### Updated Channels
- `action` (Switch): Persistent state reflecting actual door position
- `status` (Switch): Mirrors actual relay state from Net2 server
- Both channels synchronized via SignalR (opens) + API polling (closes)
- **No auto-off timer** - state changes only when door physically changes

### New Configuration
- `refreshInterval` parameter (default: 30 seconds)
- Controls API polling frequency
- Balances responsiveness vs. server load

### Technical Implementation
- Door-specific SignalR subscriptions
- EventType-based state tracking (20, 28, 46, 47)
- Parses `doorRelayOpen` field from API status
- Callback mechanism for SignalR connection ready
- Race condition fixes in initialization

## Upgrading from 5.1.0

### No Configuration Changes Required
- Existing configurations work as-is
- Synchronization enabled automatically
- Optional: Tune `refreshInterval` if needed

### What You'll Notice
- Door states stay in sync automatically
- Physical door closures now reflected in UI
- No more "stuck open" states

## Testing Performed

✅ Door opens via card reader → Instant update  
✅ Door opens via OpenHAB → Instant update  
✅ Door opens via Net2 UI → Instant update  
✅ Door closes physically → Syncs within 30s  
✅ Door closes via timeout → Syncs within 30s  
✅ Multiple doors → All synchronized independently  

## Documentation

See the following files for details:

- **[README.md](README.md)** - Updated with sync feature description
- **[CHANGELOG.md](CHANGELOG.md)** - Complete version history
- **[SYNCHRONIZATION.md](SYNCHRONIZATION.md)** - Deep dive into sync architecture

## Performance Impact

- **Network**: Minimal (1 API call per 30 seconds)
- **CPU**: Negligible event processing
- **Memory**: Single WebSocket connection per bridge
- **Result**: Production-ready with no performance concerns

## Known Limitations

1. **Close Events**: May take up to `refreshInterval` seconds to sync
   - This is by design due to Net2 API limitations
   - SignalR eventType 47 is inconsistent
   - API polling provides authoritative state
   - **No timer used** - waits for actual API confirmation

2. **Refresh Interval**: Minimum 5 seconds recommended
   - Lower values increase API load
   - 30 seconds provides good balance
   - Determines max delay for close detection

## Debug Logging

Enable detailed sync logging:
```
log:set DEBUG org.openhab.binding.net2
```

Monitor synchronization:
```bash
tail -f /var/log/openhab/openhab.log | grep -E "refreshDoorStatus|updateFromApiResponse|Door.*opened|Door.*closed"
```

## Support

- Email: author@example.com
- GitHub: https://github.com/Prinsessen
- Check logs first: Most issues show up in DEBUG logging

## Credits

**Primary Development:** Nanna Agesen  
**Testing:** Real-world production environment with 7 doors  
**Environment:** OpenHAB 5.1.0, Net2 6.6 SR5, Paxton ACU hardware  

## Next Steps

1. Deploy binding: Copy JAR to `/usr/share/openhab/addons/`
2. Monitor logs: Verify SignalR subscriptions successful
3. Test doors: Open/close and verify UI updates
4. Enjoy: Synchronization works automatically!

---

**Happy door controlling!** 🚪✨
