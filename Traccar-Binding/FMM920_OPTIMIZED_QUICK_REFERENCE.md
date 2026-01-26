# FMM920 Configuration - Quick Reference Card
**Config:** `FMM920 OPTIMIZED FAST 26-01-2026.cfg`  
**Date:** January 26, 2026

---

## 🚀 What Changed?

### **POSITION UPDATES (While Moving)**
```
300 seconds → 3 seconds  (100x FASTER!)
```
- Updates every **3 seconds** OR **20 meters** OR **15° turn**
- Zero buffering - sent immediately to server
- Expected: **1-3 second effective update rate** depending on speed

### **MOVEMENT DETECTION**
```
30 seconds → 0 seconds  (INSTANT WAKE!)
```
- Device wakes **instantly** from sleep when movement detected
- 3-second stop delay prevents false triggers

### **SLEEP MODE**
```
Mode 5 (Unknown) → GPS Sleep Mode (1)
```
- GPS turns off after 5 minutes of no movement
- GSM stays active for SMS/remote config
- **Fast wake** - no reregistration delay

### **FLESPI SERVER**
```
ch1253843.flespi.gw → DISABLED
```
- Only primary server `gps.agesen.dk:5027` now active

---

## 📊 Expected Performance

| Scenario | Update Rate | Data Usage |
|----------|-------------|------------|
| **Highway driving (100 km/h)** | ~1.1 sec | High |
| **City driving (50 km/h)** | ~1.4 sec | High |
| **Slow driving (20 km/h)** | ~3 sec | Medium |
| **Parked (stopped)** | 60 sec | Low |
| **Sleep mode (>5 min)** | GPS OFF | Minimal |

---

## ⚙️ Key Parameter Values

| Parameter | Value | Description |
|-----------|-------|-------------|
| `10000` | **3** | Min Period Moving (seconds) |
| `10001` | **20** | Min Distance Moving (meters) |
| `10002` | **15** | Min Angle Moving (degrees) |
| `10004` | **1** | Min Saved Records (no buffer) |
| `10005` | **3** | Send Period Moving (seconds) |
| `10050` | **60** | Min Period Stopped (seconds) |
| `10055` | **30** | Send Period Stopped (seconds) |
| `1000` | **300** | Sleep Timeout (5 minutes) |
| `1001` | **1** | Sleep Mode (GPS Sleep) |
| `137` | **0** | Movement Start Delay (instant) |
| `139` | **3** | Movement Stop Delay (seconds) |
| `2010` | **0** | Secondary Server (disabled) |

---

## 🔋 Power Considerations

- **Moving:** ~70-80 mA (GPS + GPRS active)
- **Stopped:** ~30-40 mA (periodic sampling)
- **Sleep:** ~10-15 mA (GPS off, GSM on)

---

## 📱 Upload via SMS

```
getfile FMM920_OPTIMIZED_FAST_26-01-2026.cfg
```

---

## ⚠️ Important Notes

1. **High data usage** when driving - ensure adequate data plan
2. **Monitor first 24 hours** to verify behavior
3. **Battery:** Sleep mode activates after 5 min stationary
4. **Can adjust:** If 3 sec too fast, increase to 5-10 sec

---

**Ready to upload!** 🎯
