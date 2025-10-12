# Diagnostic Summary: Source/Sink Recognition & Simulation Time

**Date:** 2025-10-11  
**Quick Reference Guide**

---

## ✅ What's Working

### Source/Sink Recognition
- **Definition:** ✅ `transition.is_source` and `transition.is_sink` flags work
- **Persistence:** ✅ Saved/loaded correctly in JSON
- **Behavior:** ✅ All 4 transition types (Immediate, Timed, Stochastic, Continuous) respect flags
- **Locality:** ✅ Controller recognizes minimal localities
- **Independence:** ✅ Proper independence detection
- **Validation:** ✅ `validate_source_sink_structure()` method implemented

### Simulation Time
- **Tracking:** ✅ `controller.time` advances correctly
- **Access:** ✅ All behaviors see consistent time via `model.logical_time`
- **Display:** ✅ UI shows formatted time with speed indicator
- **Timed Behaviors:** ✅ Delays and schedules work correctly
- **Data Collection:** ✅ Events logged with correct timestamps
- **Reset:** ✅ Time resets to 0.0 properly

---

## ⏳ What's Pending

### Source/Sink
1. UI validation in properties dialog
2. Arc creation blocking (prevent invalid arcs)
3. Visual warning indicators
4. Auto-fix functionality

### Time Diagnostics
1. Detailed diagnostic panel
2. Next scheduled events display
3. Enhanced status information

---

## 🔍 Quick Diagnostic Steps

### Check Source/Sink Recognition

```bash
# 1. Run unit tests
cd /home/simao/projetos/shypn
python3 tests/test_source_sink_strict.py

# Expected output: "✅ ALL TESTS PASSED!"

# 2. Check in application
python3 src/shypn.py
# → Create source transition
# → Mark as source in properties
# → Run simulation
# → Verify tokens appear without input arcs
```

### Check Simulation Time

```bash
# 1. Open application
python3 src/shypn.py

# 2. Check time display
# → Look at simulation palette: "Time: X.X s"
# → Run simulation
# → Verify time advances

# 3. Check time in controller
# → Access via: controller.time
# → Should match UI display
```

---

## 📍 Key Code Locations

### Source/Sink Recognition Points

| Location | Purpose | Line(s) |
|----------|---------|---------|
| `src/shypn/netobjs/transition.py` | Definition | 63-64 |
| `src/shypn/netobjs/transition.py` | Validation | 370-425 |
| `src/shypn/engine/simulation/controller.py` | Locality detection | 565-600 |
| `src/shypn/engine/immediate_behavior.py` | Token ops | Throughout |
| `src/shypn/engine/timed_behavior.py` | Token ops | Throughout |
| `src/shypn/engine/stochastic_behavior.py` | Token ops | Throughout |
| `src/shypn/engine/continuous_behavior.py` | Token ops | Throughout |

### Simulation Time Points

| Location | Purpose | Line(s) |
|----------|---------|---------|
| `src/shypn/engine/simulation/controller.py` | Time storage | 120 |
| `src/shypn/engine/simulation/controller.py` | Time advance | 466 |
| `src/shypn/engine/simulation/controller.py` | Time reset | 1430 |
| `src/shypn/engine/simulation/controller.py` | Time access | 84-91 |
| `src/shypn/helpers/simulate_tools_palette_loader.py` | Time display | 870-895 |

---

## 🧪 Test Coverage

### Source/Sink Tests

| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/test_source_sink.py` | Basic functionality | ✅ Pass |
| `tests/test_timed_source.py` | Timed source | ✅ Pass |
| `tests/test_timed_sink.py` | Timed sink | ✅ Pass |
| `tests/test_source_sink_strict.py` | Structural validation | ✅ Pass |

**Total:** 16/16 behavioral tests + 6/6 structural tests = **22/22 PASS** ✅

---

## 🐛 Common Issues

### Issue 1: "Tokens not moving in source/sink model"

**Symptoms:**
- Source transition doesn't produce tokens
- Sink transition doesn't consume tokens

**Diagnostic:**
```python
# Check if flag is set
print(transition.is_source)  # Should be True for source
print(transition.is_sink)    # Should be True for sink

# Check arc structure
is_valid, msg, arcs = transition.validate_source_sink_structure(model.arcs)
print(f"Valid: {is_valid}, Message: {msg}")
```

**Common Causes:**
1. Flag not set in properties dialog
2. Model loaded from old file without flags
3. Arc structure incorrect (source has input, sink has output)

**Fix:**
1. Open transition properties
2. Check "Source" or "Sink" checkbox
3. Verify arc structure matches formal definition
4. Save and reload model

### Issue 2: "Simulation time not advancing"

**Symptoms:**
- Time display shows 0.0 always
- Transitions fire but time doesn't change

**Diagnostic:**
```python
# Check controller
print(controller.time)  # Should increase each step
print(controller.settings.get_effective_dt())  # Should be > 0

# Check if running
print(controller.is_running())  # Should be True during run
```

**Common Causes:**
1. dt set to 0.0 in settings
2. Simulation not started
3. UI not updating

**Fix:**
1. Check simulation settings (dt > 0)
2. Click "Run" or "Step" button
3. Verify time display label exists

---

## 📊 Architecture Flow

### Source/Sink Recognition Flow

```
┌─────────────────────┐
│  User marks T1 as   │
│  source/sink        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  transition.is_     │
│  source = True      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Validation (opt)   │
│  checks structure   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Simulation starts  │
│  Controller inits   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Behavior created   │
│  via factory        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  fire() checks      │
│  is_source/is_sink  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Skips token ops    │
│  as appropriate     │
└─────────────────────┘
```

### Time Tracking Flow

```
┌─────────────────────┐
│  Controller init    │
│  time = 0.0         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step/Run called    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Execute enabled    │
│  transitions        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  time += dt         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Notify listeners   │
│  with new time      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  UI updates display │
│  "Time: X.X s"      │
└─────────────────────┘
```

---

## 🎯 Next Actions

### Immediate (Complete Current Work)
1. ✅ Validation method - **DONE**
2. ✅ Locality detection - **DONE**  
3. ✅ Tests - **DONE**
4. ⏳ UI integration - **PENDING**

### Short Term
1. Add validation to properties dialog
2. Block invalid arc creation
3. Add visual warnings
4. Update user documentation

### Long Term
1. Create diagnostic info panel
2. Add scheduled events viewer
3. Enhanced time visualization
4. Performance metrics

---

## 📚 Related Documentation

- **Formal Definitions:** `doc/SOURCE_SINK_FORMAL_DEFINITIONS.md`
- **Implementation Plan:** `doc/SOURCE_SINK_STRICT_IMPLEMENTATION_PLAN.md`
- **Diagnostic Path:** `doc/SOURCE_SINK_DIAGNOSTIC_PATH.md` (this document)
- **Troubleshooting:** `doc/SOURCE_SINK_TROUBLESHOOTING.md`
- **User Guide:** `doc/SOURCE_SINK_IMPLEMENTATION.md`

---

**Status:** Diagnostic paths are well-defined and working. Core implementation complete. UI integration pending.
