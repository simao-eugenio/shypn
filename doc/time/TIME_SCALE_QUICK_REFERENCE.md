# Time Scale - Quick Reference Card

**Date**: October 11, 2025  
**For**: Users and Developers

---

## 🎯 What It Does

**Watch simulations at different speeds**

- Real-time (1x)
- Fast forward (10x, 60x, 288x)
- Custom speed (any value)

---

## 🚀 How To Use

### 1. Set Duration
```
Duration: [60] [seconds ▼]
```

### 2. Open Settings
```
Click [⚙] button
```

### 3. Choose Speed
```
PLAYBACK SPEED:
[0.1x] [0.5x] [1x] [10x] [60x] Custom:[__]
```

### 4. Run Simulation
```
Click [R] button
Watch: "Time: 27.5 / 60.0 s @ 60x"
```

---

## 📊 Speed Presets

| Preset | Effect | Example |
|--------|--------|---------|
| 0.1x | 10x slower (slow motion) | 10s → 100s ⚠️ Phase 2 |
| 0.5x | 2x slower | 10s → 20s ⚠️ Phase 2 |
| **1x** | **Real-time baseline** | 10s → 10s ✅ |
| **10x** | **10x faster** | 10s → 1s ✅ |
| **60x** | **60x faster** | 1hr → 1min ✅ |

**Custom**: Type any value (0.01 to 1000.0)

---

## 💡 Real-World Examples

### Manufacturing: 8 Hours in 8 Minutes
```
Duration: 8 hours
Speed: 60x
Result: Watch full shift in 8 minutes ✅
```

### Biology: 24 Hours in 5 Minutes
```
Duration: 24 hours  
Speed: 288x
Result: See cell cycle compressed ✅
```

### Network: 1 Hour in 1 Minute
```
Duration: 1 hour
Speed: 60x
Result: Analyze traffic patterns quickly ✅
```

---

## ⚙️ For Developers

### Time Scale Property
```python
simulation.settings.time_scale = 60.0  # 60x faster
```

### How It Works
```python
# GUI updates every 100ms
# Calculate model time per update
model_time = 0.1 × time_scale

# Execute enough steps
steps = model_time / dt
```

### Files Modified
```
src/shypn/engine/simulation/controller.py
src/shypn/helpers/simulate_tools_palette_loader.py
```

---

## ✅ Status

| Feature | Status |
|---------|--------|
| Speedup (1x - 1000x) | ✅ Working |
| Slow motion (< 1x) | ⚠️ Phase 2 |
| Dynamic changes | ✅ Working |
| Display indicator | ✅ Working |
| Safety capping | ✅ Working |

---

## 📖 Full Documentation

1. `REAL_WORLD_TIME_PLAYBACK_ANALYSIS.md` - Complete analysis
2. `ANALYSIS_SUMMARY.md` - Quick summary
3. `TIME_PLAYBACK_VISUAL_GUIDE.md` - Visual diagrams
4. `TIME_SCALE_PHASE1_COMPLETE.md` - Implementation details
5. `TIME_SCALE_FINAL_SUMMARY.md` - Session summary

---

## 🎉 Ready To Use!

**Launch**: `python3 shypn.py`  
**Test**: Create model → Set duration → Choose speed → Run!  
**Result**: Watch simulations at any speed ✅
