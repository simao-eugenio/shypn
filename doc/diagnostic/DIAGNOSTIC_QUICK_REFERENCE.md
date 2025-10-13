# Diagnostic Quick Reference Card

**For Developers & Troubleshooters**

---

## 🔍 Source/Sink Recognition - Quick Checks

### Check 1: Is the flag set?
```python
print(f"Source: {transition.is_source}")
print(f"Sink: {transition.is_sink}")
```
**Expected:** `True` for the respective type

### Check 2: Is the structure valid?
```python
is_valid, msg, arcs = transition.validate_source_sink_structure(model.arcs)
print(f"Valid: {is_valid}, Message: {msg}")
```
**Expected:** `(True, "", [])` for valid structure

### Check 3: Is it in the JSON?
```bash
grep "is_source\|is_sink" model.json
```
**Expected:** `"is_source": true` or `"is_sink": true`

### Check 4: Correct locality?
```python
places = controller._get_all_places_for_transition(transition)
print(f"Locality: {places}")
```
**Expected:** 
- Source: Only output place IDs
- Sink: Only input place IDs

### Check 5: Token operations correct?
```python
# Start simulation and observe
# Source: Should produce tokens without consuming
# Sink: Should consume tokens without producing
```

---

## ⏱️ Simulation Time - Quick Checks

### Check 1: Initial time
```python
print(f"Time: {controller.time}")
```
**Expected:** `0.0` after init or reset

### Check 2: Time advances
```python
t0 = controller.time
controller.step()
t1 = controller.time
print(f"Advanced: {t1 - t0}")
```
**Expected:** `dt` (usually 0.1)

### Check 3: UI shows time
```
Look at simulation palette: "Time: X.X s"
```
**Expected:** Matches `controller.time`

### Check 4: Timed delays work
```python
# Create timed transition with delay=5.0
# Run simulation
# Should fire after 5.0 time units
```

---

## 🐛 Common Problems

### Problem: Source doesn't produce tokens
**Check:**
1. `transition.is_source == True`? 
2. Arc structure: `T → P` (no input arcs)?
3. Transition enabled and firing?

### Problem: Sink doesn't consume tokens
**Check:**
1. `transition.is_sink == True`?
2. Arc structure: `P → T` (no output arcs)?
3. Transition enabled (has input tokens)?

### Problem: Time not advancing
**Check:**
1. `controller.settings.get_effective_dt() > 0`?
2. Simulation running (`controller.is_running()`)?
3. UI updating?

### Problem: Timed transition fires immediately
**Check:**
1. Delay set correctly?
2. Enablement time recorded?
3. `behavior._enablement_time` exists?

---

## 📍 Key File Locations

### Source/Sink
- **Definition:** `src/shypn/netobjs/transition.py:63-64`
- **Validation:** `src/shypn/netobjs/transition.py:370-425`
- **Locality:** `src/shypn/engine/simulation/controller.py:565-600`
- **Firing:** `src/shypn/engine/*_behavior.py`

### Time
- **Storage:** `src/shypn/engine/simulation/controller.py:120`
- **Advance:** `src/shypn/engine/simulation/controller.py:466`
- **Reset:** `src/shypn/engine/simulation/controller.py:1430`
- **Display:** `src/shypn/helpers/simulate_tools_palette_loader.py:880`

---

## 🧪 Quick Test Commands

```bash
# Test source/sink
cd /home/simao/projetos/shypn
python3 tests/test_source_sink_strict.py

# Test time
python3 -c "
from shypn.engine.simulation.controller import SimulationController
# (Create model, controller)
print(f'Time: {controller.time}')
controller.step()
print(f'Time: {controller.time}')
"

# Interactive test
python3 src/shypn.py
```

---

## 📊 Status Indicators

### Source/Sink Implementation
- ✅ Flag definition
- ✅ Persistence (JSON)
- ✅ Behavioral logic (all 4 types)
- ✅ Locality detection
- ✅ Validation method
- ⏳ UI validation (pending)

### Time Tracking
- ✅ Initialization
- ✅ Advancement
- ✅ Display
- ✅ Timed behaviors
- ✅ Data logging
- ✅ Reset

---

## 🎯 Test Coverage

- **Source/Sink:** 22/22 tests passing ✅
- **Time:** All functionality verified ✅

---

## 📚 Full Documentation

- `doc/SOURCE_SINK_DIAGNOSTIC_PATH.md` - Complete diagnostic path
- `doc/DIAGNOSTIC_SUMMARY.md` - Status summary
- `doc/DIAGNOSTIC_VISUALIZATION.md` - Visual flowcharts
- `doc/SOURCE_SINK_FORMAL_DEFINITIONS.md` - Formal theory
- `doc/SOURCE_SINK_TROUBLESHOOTING.md` - User guide

---

**Quick tip:** Copy this file to your workspace for easy reference during development!
