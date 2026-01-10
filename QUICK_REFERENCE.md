# Entry Logging Quick Reference

## 🎯 Quick Access After Reconnection

### Check Current Status
```bash
# View latest entry
curl -s http://localhost:8080/rest/items/Net2_Door1_EntryLog | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(json.loads(data['state']), indent=2))"

# Monitor live entries
tail -f /var/log/openhab/openhab.log | grep "Entry log"

# Check bundle status
echo "habopen" | ssh -p 8101 openhab@localhost "bundle:list | grep net2"
```

### File Locations (Memory Jogger)
| Component | Location |
|-----------|----------|
| **Source (Build)** | `/etc/openhab-addons/bundles/org.openhab.binding.net2/src/` |
| **Source (Git)** | `/etc/openhab/net2-binding/src/` |
| **Deployed JAR** | `/usr/share/openhab/addons/org.openhab.binding.net2-5.2.0-SNAPSHOT.jar` |
| **Items** | `/etc/openhab/items/net2.items` |
| **Transform** | `/etc/openhab/transform/entrylog.js` |
| **Sitemap** | `/etc/openhab/sitemaps/myhouse.sitemap` |
| **Persistence** | `/etc/openhab/persistence/influxdb.persist` |
| **Docs** | `/etc/openhab/net2-binding/*.md` |

### Rebuild & Deploy (One Command)
```bash
cd /etc/openhab-addons/bundles/org.openhab.binding.net2 && \
mvn clean package -DskipTests -Dspotless.check.skip=true -Dcheckstyle.skip=true -Dpmd.skip=true -Dspotbugs.skip=true && \
sudo cp target/*.jar /usr/share/openhab/addons/ && \
echo "habopen" | ssh -p 8101 openhab@localhost "bundle:update 360" && \
cp -r src/* /etc/openhab/net2-binding/src/ && \
echo "✅ Build, deploy, reload, and sync complete"
```

### Test Entry Logging
```bash
# 1. Swipe physical badge on any door
# 2. Check log output
tail -5 /var/log/openhab/openhab.log | grep "Entry log"

# Expected: Entry log: {"firstName":"Nanna","lastName":"Agesen",...}
```

### JSON Format Reference
```json
{
  "firstName": "Nanna",
  "lastName": "Agesen",
  "doorName": "Front Door",
  "timestamp": "2026-01-10T18:48:34",
  "doorId": 6612642
}
```

### UI Transform Output
```
Nanna Agesen entered Front Door at 18:48:34
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **ENTRY_LOGGING.md** | Complete feature guide (12KB) |
| **PROJECT_CONTEXT.md** | Full project state (27KB) |
| **DEPLOYMENT_STATUS.md** | Deployment checklist |
| **EXAMPLES.md** | Configuration examples (17KB) |

## ⚠️ Important Behaviors

- ✅ **Triggers**: Physical badge/card access (userName present)
- ❌ **Does NOT trigger**: Remote UI openings (userName is null)
- **Name Format**: Net2 "Last First" → Binding "First Last"

## 🔧 Troubleshooting

### No Entry Logs?
1. Check SignalR: `grep SignalR /var/log/openhab/openhab.log | tail -20`
2. Verify physical access (not remote UI)
3. Check userName field: `grep userName /var/log/openhab/openhab.log | tail -5`

### Wrong Names?
- Verify: `lastName = nameParts[0]`, `firstName = nameParts[1]`

### Transform Not Working?
```bash
# Check file exists
ls -l /etc/openhab/transform/entrylog.js

# Check for JS errors
grep -i javascript /var/log/openhab/openhab.log | tail -20
```

## 📊 Grafana Setup

See **ENTRY_LOGGING.md** section "Grafana Integration" for:
- InfluxDB query examples
- JSON field extraction
- Dashboard layouts
- Visualization examples

---

**Last Updated**: January 10, 2026 - 19:00  
**Status**: ✅ Fully operational  
**Version**: 5.2.0-SNAPSHOT
