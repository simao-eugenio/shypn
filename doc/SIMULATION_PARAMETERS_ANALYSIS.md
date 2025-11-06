# Simulation Parameters - Comprehensive Analysis
**Date:** November 6, 2025  
**Branch:** swiss-palette-refactor  
**Scope:** Atomic Persistence, Precision, Progress Bar

---

## Executive Summary

This document provides a complete analysis of all simulation parameters across the SHYPN application, focusing on:
1. **Atomic Persistence** - Transaction-safe parameter updates
2. **Precision** - Numerical accuracy and validation
3. **Progress Bar** - Progress tracking and display

The simulation system uses a **sophisticated buffered settings architecture** that provides atomic updates with rollback guarantees, comprehensive validation, and thread-safe operations.

---

## 1. SIMULATION PARAMETERS INVENTORY

### 1.1 Core Parameters (SimulationSettings)

Located in: `src/shypn/engine/simulation/settings.py`

| Parameter | Type | Default | Range/Validation | Description |
|-----------|------|---------|------------------|-------------|
| **time_units** | `TimeUnits` enum | SECONDS | {MILLISECONDS, SECONDS, MINUTES, HOURS, DAYS} | Model time interpretation |
| **duration** | `Optional[float]` | None | > 0 or None | Simulation duration in time_units (None = indefinite) |
| **dt_auto** | `bool` | True | True/False | Auto-calculate time step |
| **dt_manual** | `float` | 0.1 | > 0, validated | Manual time step override (seconds) |
| **time_scale** | `float` | 1.0 | > 0 | Real-world playback speed multiplier |

**Target Steps for Auto Mode:** 1000 (duration / 1000 = dt)

### 1.2 UI Parameters (Simulation Tools Palette)

Located in: `ui/simulate/simulate_tools_palette.ui`

| Widget | Parameter | Control Type | Purpose |
|--------|-----------|--------------|---------|
| `duration_entry` | duration value | GtkEntry | Set simulation duration |
| `time_units_combo` | time_units | GtkComboBoxText | Select time units (ms/s/min/h/d) |
| `simulation_progress_bar` | - | GtkProgressBar | Display simulation progress |
| `time_display_label` | - | GtkLabel | Show current/total time |

### 1.3 Settings Panel Parameters

Located in: `ui/palettes/simulate/settings_sub_palette.ui`

| Section | Parameters | Control Type | Status |
|---------|------------|--------------|--------|
| **TIME STEP** | dt_auto (Auto/Manual radio), dt_manual (entry) | GtkRadioButton, GtkEntry | ✅ Active |
| **PLAYBACK SPEED** | time_scale | GtkSpinButton | ✅ Active |
| **CONFLICT POLICY** | - | GtkComboBoxText | ❌ Removed (commit 6658373) |
| **ACTION BUTTONS** | Apply/Reset | GtkButton | ❌ Removed (commit 6658373) |

---

## 2. ATOMIC PERSISTENCE ARCHITECTURE

### 2.1 Buffered Settings System

**Architecture:** Three-layer design for transaction-safe updates

```
┌─────────────────────────────────────────────────┐
│          UI Layer (Widgets)                     │
│  - GtkEntry, GtkSpinButton, GtkComboBox         │
└───────────────────┬─────────────────────────────┘
                    │ writes to buffer
                    ▼
┌─────────────────────────────────────────────────┐
│   BufferedSimulationSettings (Transaction)      │
│  - Write buffer                                 │
│  - Validation before commit                     │
│  - Atomic apply (all-or-nothing)                │
│  - Rollback support                             │
│  - Thread-safe (mutex lock)                     │
└───────────────────┬─────────────────────────────┘
                    │ commit()
                    ▼
┌─────────────────────────────────────────────────┐
│   SimulationSettings (Live Settings)            │
│  - Used by SimulationController                 │
│  - Property validation on setters               │
│  - Read by simulation engine                    │
└─────────────────────────────────────────────────┘
```

### 2.2 Key Files

| File | Purpose | Atomic Features |
|------|---------|-----------------|
| `engine/simulation/buffered/buffered_settings.py` | Transaction wrapper | Write buffering, atomic commits, rollback |
| `engine/simulation/buffered/transaction.py` | Context manager | Automatic commit/rollback with `with` statement |
| `engine/simulation/buffered/base.py` | Interfaces | ValidationError, ChangeListener |
| `engine/simulation/settings.py` | Live settings | Property validation, serialization |
| `engine/simulation/controller.py` | Simulation engine | Uses BufferedSimulationSettings |

### 2.3 Atomic Operations Flow

**Safe Parameter Update Process:**

1. **User Action** → UI widget changed (e.g., time_scale spinner)
2. **Buffer Write** → Change written to `buffered.buffer` (NOT live settings)
3. **Mark Dirty** → `buffered.mark_dirty()` flags pending changes
4. **Validation** → On commit, ALL values validated BEFORE any changes
5. **Atomic Commit** → If valid, ALL changes applied together atomically
6. **Rollback** → If invalid, NO changes applied, buffer restored

**Code Example:**
```python
# Transaction-safe update
buffered = BufferedSimulationSettings(controller.settings)

# Write to buffer (not live)
buffered.buffer.time_scale = 10.0
buffered.buffer.duration = 60.0
buffered.mark_dirty()

# Commit atomically (all-or-nothing)
if buffered.commit():
    print("✅ All changes applied atomically")
else:
    print("❌ Validation failed - no changes applied")
```

### 2.4 Thread Safety

**Lock Protection:** `threading.Lock()` in BufferedSimulationSettings

```python
with self._lock:
    # Step 1: Validate ALL buffered values
    self._validate_buffer()
    
    # Step 2: Track what's changing
    self._track_changes()
    
    # Step 3: Apply atomically (all or nothing)
    self._apply_buffer_to_live()
    
    # Step 4: Notify listeners
    self._notify_commit()
```

**Guarantees:**
- ✅ No race conditions during rapid UI changes
- ✅ No partial updates (all properties or none)
- ✅ Consistent state always maintained
- ✅ Safe for concurrent access from multiple threads

### 2.5 Current Implementation Status

| Component | Atomic Support | Status |
|-----------|----------------|--------|
| **SimulationSettings** | Property validation | ✅ Implemented |
| **BufferedSimulationSettings** | Transaction wrapper | ✅ Implemented |
| **Transaction Context Manager** | `with` statement support | ✅ Implemented |
| **SimulationController** | Uses buffered settings | ✅ Implemented |
| **Settings Dialog** | Uses buffered updates | ✅ Implemented |
| **Settings Sub-Palette** | Direct manipulation | ⚠️ Partially Implemented |

**Gap Identified:** Settings sub-palette (inline parameters panel) does NOT currently use BufferedSimulationSettings. The `_on_speed_changed` handler directly modifies simulation without buffering.

---

## 3. PRECISION ANALYSIS

### 3.1 Numerical Precision Settings

| Component | Precision Setting | Value | Purpose |
|-----------|------------------|-------|---------|
| **Time Comparison Epsilon** | TIME_EPSILON | 1e-9 seconds | Prevent floating-point errors in duration checks |
| **Time Step Validation** | Minimum dt | 1e-9 seconds | Prevent division by zero |
| **Time Step Validation** | Maximum dt | 1e6 seconds | Prevent excessive steps |
| **Continuous Behavior** | MIN_FLOW | 1e-10 | Prevent numerical precision issues in flow |
| **Progress Calculation** | Clamping | min(progress, 1.0) | Prevent overshoot |
| **Step Count Limit** | Maximum steps | 1,000,000 | Prevent memory exhaustion |

### 3.2 Time Step Calculation Precision

**Auto Mode Formula:**
```python
dt = duration_seconds / 1000  # Target: 1000 steps
```

**Validation Chain:**
```python
# 1. Property Setter Validation (SimulationSettings)
@dt_manual.setter
def dt_manual(self, value: float):
    is_valid, error = TimeValidator.validate_time_step(value)
    if not is_valid:
        raise ValueError(f"Invalid time step: {error}")
    self._dt_manual = value

# 2. Cross-Validation (BufferedSimulationSettings)
step_count = int(duration_seconds / dt)
if step_count > 1_000_000:
    raise ValidationError("Too many steps")
```

### 3.3 Progress Calculation Precision

**Progress Fraction:**
```python
def calculate_progress(self, current_time_seconds: float) -> float:
    """Calculate simulation progress as fraction [0.0, 1.0]."""
    duration_seconds = self.get_duration_seconds()
    
    if duration_seconds is None or duration_seconds <= 0:
        return 0.0  # Unknown duration
    
    progress = current_time_seconds / duration_seconds
    return min(progress, 1.0)  # Clamp to prevent overshoot
```

**Display Precision:**
- Progress Bar: Integer percentage (0-100%)
- Time Display: 4 decimal places (e.g., "12.3456 s")

### 3.4 Precision Guarantees

| Aspect | Guarantee | Implementation |
|--------|-----------|----------------|
| **Time Step** | dt ≥ 1e-9 seconds | TimeValidator.validate_time_step() |
| **Duration** | duration > 0 or None | SimulationSettings.duration setter |
| **Time Scale** | scale > 0 | SimulationSettings.time_scale setter |
| **Progress** | 0.0 ≤ progress ≤ 1.0 | min(progress, 1.0) clamping |
| **Step Count** | steps ≤ 1,000,000 | BufferedSimulationSettings._validate_buffer() |
| **Completion Check** | Uses epsilon tolerance | is_complete() uses TIME_EPSILON = 1e-9 |

### 3.5 Simulation Ending Precision

**Critical Issue:** Floating-point arithmetic can cause simulation to:
1. **Overshoot duration** - `time` slightly exceeds `duration` due to time step granularity
2. **Never reach duration** - Accumulated rounding errors prevent exact equality

**Solution Implemented:** Epsilon tolerance in `is_complete()` method

```python
# Before (PROBLEMATIC):
return current_time_seconds >= duration_seconds  # Exact comparison

# After (FIXED):
TIME_EPSILON = 1e-9  # 1 nanosecond tolerance
return current_time_seconds >= (duration_seconds - TIME_EPSILON)
```

**Effect:**
- ✅ Simulation completes when `time ≥ duration - 1e-9`
- ✅ Handles undershooting: `59.999999999 >= 60.0 - 1e-9` → True
- ✅ Handles overshooting: `60.000000001 >= 60.0 - 1e-9` → True
- ✅ Prevents infinite loops from never reaching exact duration
- ✅ Prevents premature stopping from floating-point errors

**Example Scenarios:**
```python
duration = 60.0 seconds, dt = 0.06 seconds (auto, 1000 steps)

# Ideal case: 60.0 / 0.06 = 1000 steps exactly
step 1000: time = 60.0 → complete ✓

# Rounding error case: accumulated error from 1000 additions
step 1000: time = 59.999999998 → complete ✓ (within epsilon)
step 1001: time = 60.059999998 → would overshoot, but already stopped

# Overshoot case: time step doesn't divide duration evenly
duration = 60.0, dt = 0.07 (manual)
step 857: time = 59.99 → not complete (> epsilon away)
step 858: time = 60.06 → complete ✓ (overshoots but within check)
```

---

## 4. PROGRESS BAR ANALYSIS

### 4.1 Progress Bar Architecture

**Widget:** `GtkProgressBar` (id: `simulation_progress_bar`)  
**Location:** `ui/simulate/simulate_tools_palette.ui`  
**Update Frequency:** Every simulation step via `_on_simulation_step()` callback

**Data Flow:**
```
SimulationController.time
         ↓
SimulationController.get_progress()
         ↓
SimulationSettings.calculate_progress(time)
         ↓
SimulateToolsPaletteLoader._update_progress_display()
         ↓
progress_bar.set_fraction(progress)
progress_bar.set_text(f"{int(progress * 100)}%")
```

### 4.2 Progress Bar Properties

| Property | Type | Purpose | Current Value |
|----------|------|---------|---------------|
| `fraction` | float | Progress value [0.0, 1.0] | Calculated from time/duration |
| `show-text` | bool | Display percentage | True (when duration set) |
| `text` | string | Custom label | "0%", "50%", "100%" or "Ready" |
| `pulse` | - | Indeterminate mode | Not used (duration always known or 0%) |

### 4.3 Progress Bar Update Logic

Located in: `src/shypn/helpers/simulate_tools_palette_loader.py`

```python
def _update_progress_display(self):
    """Update progress bar and time display label."""
    if not self.progress_bar or not self.time_display_label:
        return
    
    if not self.simulation:
        return
    
    settings = self.simulation.settings
    
    # Update progress bar
    if settings.duration is not None:
        progress = self.simulation.get_progress()  # Calls settings.calculate_progress()
        self.progress_bar.set_fraction(min(progress, 1.0))
        self.progress_bar.set_text(f"{int(progress * 100)}%")
        self.progress_bar.set_show_text(True)
    else:
        # No duration = indefinite run
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(False)
```

### 4.4 Progress Bar States

| State | Condition | Fraction | Text | Show Text |
|-------|-----------|----------|------|-----------|
| **Ready** | No simulation | 0.0 | "Ready" | True |
| **Running (Duration Set)** | time < duration | time/duration | "0%" - "100%" | True |
| **Complete** | time ≥ duration | 1.0 | "100%" | True |
| **Indefinite** | duration = None | 0.0 | - | False |

### 4.5 Progress Bar Triggers

**Update Triggers:**
1. **Simulation Step** → `_on_simulation_step()` → `_update_progress_display()`
2. **Duration Changed** → `_on_duration_changed()` → `_update_progress_display()`
3. **Reset Simulation** → `_on_reset_clicked()` → `_update_progress_display()`
4. **Stop Simulation** → `_on_stop_clicked()` → `_update_progress_display()`

**Frequency:** Every simulation step (can be 1000 steps for typical 60s simulation)

### 4.6 Time Display Label

**Widget:** `GtkLabel` (id: `time_display_label`)  
**Format:** "Time: {current} / {duration} {units}"  
**Example:** "Time: 23.4567 / 60.0 s"

**Formatter:** `TimeFormatter.format_progress(time, duration, units)`

```python
# Update time display
if settings.duration is not None:
    text, _ = TimeFormatter.format_progress(
        self.simulation.time,
        settings.get_duration_seconds(),
        settings.time_units
    )
    self.time_display_label.set_text(text)
```

### 4.7 Progress Bar CSS Styling

Located in: `src/shypn/helpers/simulate_tools_palette_loader.py` (embedded CSS)

```css
/* Progress bar */
.sim-progress-bar {
    min-height: 24px;
    font-size: 11px;
}

.sim-progress-bar progress {
    background-color: #4a90e2;
}

.sim-progress-bar trough {
    background-color: #2d2d2d;
}
```

### 4.8 Progress Bar Issues & Debugging

**Debug Logging:** Extensive logging in `_update_progress_display()`:
```python
print(f"[PROGRESS] _update_progress_display called")
print(f"[PROGRESS] progress_bar exists: {self.progress_bar is not None}")
print(f"[PROGRESS] progress_bar visible: {self.progress_bar.get_visible()}")
print(f"[PALETTE._update_progress_display] Progress bar: {progress*100:.1f}%")
```

**Known Checks:**
- Widget existence validation
- Parent widget verification
- Visibility checks
- Simulation controller availability

---

## 5. PARAMETER VALIDATION SUMMARY

### 5.1 Validation Layers

| Layer | Scope | Type | Location |
|-------|-------|------|----------|
| **1. Property Setters** | Individual property | Type, range, nullability | SimulationSettings |
| **2. TimeValidator** | Time-related values | Format, range, reasonableness | utils/time_utils.py |
| **3. Cross-Validation** | Multiple properties | Step count, consistency | BufferedSimulationSettings |
| **4. UI Validation** | User input | Format, parsing | Dialogs, palette loaders |

### 5.2 Validation Rules Matrix

| Parameter | Type Check | Range Check | Cross-Validation | Error Handling |
|-----------|------------|-------------|------------------|----------------|
| **time_units** | ✅ Must be TimeUnits enum | N/A | - | TypeError |
| **duration** | ✅ float or None | ✅ > 0 or None | ✅ Step count check | ValueError |
| **dt_auto** | ✅ bool | N/A | - | TypeError |
| **dt_manual** | ✅ float | ✅ 1e-9 ≤ dt ≤ 1e6 | ✅ Step count check | ValueError |
| **time_scale** | ✅ float | ✅ > 0 | - | ValueError |

### 5.3 Step Count Validation

**Critical Check:** Prevents memory exhaustion

```python
# In BufferedSimulationSettings._validate_buffer()
step_count = int(duration_seconds / dt)

if step_count > 1_000_000:
    raise ValidationError(
        f"Duration {duration} {time_units} with dt={dt}s "
        f"would require {step_count:,} steps. "
        f"Maximum allowed: 1,000,000 steps."
    )
```

**Example Scenarios:**
- ✅ 60s duration, auto dt (0.06s) → 1000 steps ✓
- ✅ 1 hour, 1s dt → 3600 steps ✓
- ❌ 1 day, 0.001s dt → 86,400,000 steps ✗ REJECTED

---

## 6. PERSISTENCE (SERIALIZATION)

### 6.1 Settings Serialization

**Format:** JSON-compatible dictionary

```python
def to_dict(self) -> dict:
    """Serialize settings to dictionary."""
    return {
        'time_units': self._time_units.full_name,  # e.g., "seconds"
        'duration': self._duration,                # float or None
        'dt_auto': self._dt_auto,                  # bool
        'dt_manual': self._dt_manual,              # float
        'time_scale': self._time_scale             # float
    }
```

**Deserialization:**
```python
@classmethod
def from_dict(cls, data: dict) -> 'SimulationSettings':
    """Deserialize settings from dictionary."""
    settings = cls()
    
    if 'time_units' in data:
        settings.time_units = TimeUnits.from_string(data['time_units'])
    
    if 'duration' in data:
        settings.duration = data['duration']
    
    # ... load other properties with validation
    
    return settings
```

### 6.2 Persistence Locations

| Storage | Format | Scope | Location |
|---------|--------|-------|----------|
| **Workspace Settings** | JSON | Per-workspace | workspace/.shypn/settings.json |
| **Document Model** | Internal | Per-document | PetriNetModel._simulation_settings |
| **File Format** | XML/JSON | Saved files | .shypn file format |

**Note:** Simulation settings are NOT currently persisted to workspace settings (opportunity for enhancement).

---

## 7. RECOMMENDATIONS

### 7.1 Critical Issues

#### Issue 1: Simulation Ending Precision ✅ FIXED
**Impact:** CRITICAL  
**Risk:** Simulation never reaches exact duration or overshoots unpredictably

**Problem:** Floating-point arithmetic causes accumulated rounding errors. With duration=60.0 and dt=0.06, after 1000 steps, time might be 59.999999998 or 60.000000002 instead of exactly 60.0.

**Fix Applied:** Added `TIME_EPSILON = 1e-9` constant and modified `is_complete()`:
```python
# Now uses epsilon tolerance (1 nanosecond)
return current_time_seconds >= (duration_seconds - TIME_EPSILON)
```

**Status:** ✅ FIXED in this commit

#### Issue 2: Settings Sub-Palette Not Using Buffered Updates
**Impact:** HIGH  
**Risk:** Race conditions, inconsistent state during rapid UI changes

**Current Code (Non-Atomic):**
```python
# src/shypn/helpers/simulate_tools_palette_loader.py
def _on_speed_changed(self, spin):
    """Handle playback speed spinner change."""
    if self.simulation:
        # PROBLEM: Direct modification without buffering
        was_running = self.simulation.is_running()
        if was_running:
            self.simulation.stop()
            time_step = self.simulation.get_effective_dt()
            self.simulation.run(time_step=time_step)
```

**Recommended Fix:**
```python
def _on_speed_changed(self, spin):
    """Handle playback speed spinner change (buffered)."""
    if self.simulation and self.buffered_settings:
        # Write to buffer
        self.buffered_settings.buffer.time_scale = spin.get_value()
        self.buffered_settings.mark_dirty()
        
        # Commit atomically
        if self.buffered_settings.commit():
            # Restart if was running
            if self.simulation.is_running():
                self.simulation.stop()
                            self.simulation.run(self.simulation.get_effective_dt())
```

**Status:** ⚠️ PENDING

#### Issue 3: Progress Bar Update Overhead
**Impact:** MEDIUM  
**Risk:** Performance degradation with high step counts

**Problem:** `_update_progress_display()` called on EVERY simulation step (1000+ times per typical simulation)

**Recommendation:** Throttle updates:
```python
# Update progress bar only every N steps or every X milliseconds
self._last_progress_update = 0
UPDATE_INTERVAL_MS = 100  # Update every 100ms

def _update_progress_display(self):
    now = time.time() * 1000
    if now - self._last_progress_update < UPDATE_INTERVAL_MS:
        return  # Skip update (too soon)
    
    self._last_progress_update = now
    # ... existing update code
```

**Status:** ⚠️ PENDING
```

**Status:** ⚠️ PENDING

#### Issue 3: Progress Bar Update Overhead
**Impact:** MEDIUM  
**Risk:** Performance degradation with high step counts

**Problem:** `_update_progress_display()` called on EVERY simulation step (1000+ times per typical simulation)

**Recommendation:** Throttle updates:
```python
# Update progress bar only every N steps or every X milliseconds
self._last_progress_update = 0
UPDATE_INTERVAL_MS = 100  # Update every 100ms

def _update_progress_display(self):
    now = time.time() * 1000
    if now - self._last_progress_update < UPDATE_INTERVAL_MS:
        return  # Skip update (too soon)
    
    self._last_progress_update = now
    # ... existing update code
```

### 7.2 Enhancement Opportunities

#### Enhancement 1: Workspace Persistence for Simulation Settings
**Priority:** MEDIUM

Add simulation settings to workspace persistence:
```python
# In workspace_settings.py
def save_simulation_defaults(self, settings: SimulationSettings):
    """Save default simulation settings for workspace."""
    self._data['simulation'] = settings.to_dict()
    self._save()

def load_simulation_defaults(self) -> SimulationSettings:
    """Load default simulation settings from workspace."""
    if 'simulation' in self._data:
        return SimulationSettings.from_dict(self._data['simulation'])
    return SimulationSettings()  # Defaults
```

#### Enhancement 2: Precision Configuration
**Priority:** LOW

Allow users to configure precision settings:
```python
class PrecisionSettings:
    MIN_DT = 1e-9
    MAX_DT = 1e6
    MAX_STEPS = 1_000_000
    MIN_FLOW = 1e-10
    PROGRESS_DECIMALS = 4
```

#### Enhancement 3: Progress Bar Modes
**Priority:** LOW

Add indeterminate mode for indefinite simulations:
```python
if settings.duration is None:
    # Indeterminate mode - pulse animation
    self.progress_bar.pulse()
    self.progress_bar.set_text("Running...")
```

### 7.3 Documentation Needs

1. **User Guide:** How to configure simulation parameters
2. **Developer Guide:** How to use BufferedSimulationSettings in UI code
3. **API Reference:** SimulationSettings and BufferedSimulationSettings classes
4. **Validation Rules:** Complete list of parameter constraints

---

## 8. CONCLUSIONS

### 8.1 Strengths

✅ **Robust Atomic Architecture:** BufferedSimulationSettings provides excellent transaction safety  
✅ **Comprehensive Validation:** Multi-layer validation prevents invalid states  
✅ **Thread Safety:** Mutex locks protect concurrent access  
✅ **Progress Tracking:** Accurate progress calculation with clamping  
✅ **Serialization Support:** Settings can be saved/restored  

### 8.2 Weaknesses

⚠️ **Inconsistent Buffering:** Settings sub-palette doesn't use buffered updates  
⚠️ **Performance:** Progress bar updated too frequently (every step)  
⚠️ **Limited Persistence:** Simulation settings not saved to workspace  
⚠️ **Debug Logging:** Excessive print statements in production code  

**Fixed in this session:**
✅ **Simulation Ending Precision:** Added TIME_EPSILON tolerance to prevent floating-point errors  

### 8.3 Overall Assessment

The simulation parameter system demonstrates **excellent architectural design** with atomic updates, comprehensive validation, and thread safety. However, **implementation gaps** exist where inline UI controls bypass the buffered settings architecture, creating potential race conditions.

**Priority Actions:**
1. ✅ **COMPLETED:** Add TIME_EPSILON tolerance for simulation ending precision
2. **HIGH:** Integrate BufferedSimulationSettings into settings sub-palette
3. **MEDIUM:** Throttle progress bar updates (every 100ms instead of every step)
4. **MEDIUM:** Add workspace persistence for simulation defaults
5. **LOW:** Remove debug print statements

---

## 9. APPENDIX

### 9.1 File Reference

**Core Engine:**
- `src/shypn/engine/simulation/settings.py` - SimulationSettings class
- `src/shypn/engine/simulation/controller.py` - SimulationController
- `src/shypn/engine/simulation/buffered/buffered_settings.py` - BufferedSimulationSettings
- `src/shypn/engine/simulation/buffered/transaction.py` - Transaction context manager
- `src/shypn/engine/simulation/buffered/base.py` - Interfaces

**UI:**
- `ui/simulate/simulate_tools_palette.ui` - Main simulation tools UI
- `ui/palettes/simulate/settings_sub_palette.ui` - Inline settings panel UI
- `src/shypn/helpers/simulate_tools_palette_loader.py` - Palette loader logic
- `src/shypn/dialogs/simulation_settings_dialog.py` - Settings dialog

**Utilities:**
- `src/shypn/utils/time_utils.py` - TimeUnits, TimeConverter, TimeValidator

### 9.2 Key Constants

```python
# SimulationSettings
DEFAULT_TIME_UNITS = TimeUnits.SECONDS
DEFAULT_DURATION = None
DEFAULT_DT_AUTO = True
DEFAULT_DT_MANUAL = 0.1
DEFAULT_TIME_SCALE = 1.0
DEFAULT_STEPS_TARGET = 1000
TIME_EPSILON = 1e-9  # Precision tolerance for time comparisons

# Validation
MIN_TIME_STEP = 1e-9
MAX_TIME_STEP = 1e6
MAX_STEP_COUNT = 1_000_000
MIN_FLOW = 1e-10

# UI
PROGRESS_UPDATE_FREQUENCY = every step (needs throttling)
PROGRESS_DECIMALS = 0 (percentage)
TIME_DISPLAY_DECIMALS = 4
```

### 9.3 Changes in This Session

**Commit 1:** Added playback speed spinner to parameters panel (fe223d3)
**Commit 2:** Created comprehensive analysis document (e3e9f5a)
**Commit 3:** Fixed simulation ending precision with TIME_EPSILON (current)

### 9.4 References

- **Commit 9d52da2:** Removed playback speed preset buttons
- **Commit 6658373:** Removed Conflict Policy and action buttons
- **Commit fe223d3:** Added playback speed spinner
- **Tag v0.9.0-global-sync-multi-canvas:** Stable baseline

---

**END OF ANALYSIS**
