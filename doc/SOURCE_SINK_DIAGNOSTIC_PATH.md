# Source/Sink Diagnostic Path Review

**Date:** 2025-10-11  
**Purpose:** Document the diagnostic paths for source/sink recognition and simulation time tracking

---

## 1. Source/Sink Recognition Path

### 1.1 Where Source/Sink is Defined

**Location:** `src/shypn/netobjs/transition.py`

```python
class Transition:
    def __init__(self, ...):
        self.is_source = False  # Line 63
        self.is_sink = False    # Line 64
```

**Set via:**
- Transition properties dialog (UI)
- Model loading from JSON (`from_dict()`)
- Direct property assignment

---

### 1.2 Where Source/Sink is Validated

**Location:** `src/shypn/netobjs/transition.py`

```python
def validate_source_sink_structure(self, arcs_list) -> tuple:
    """Validate that source/sink structure matches formal definition.
    
    Returns:
        tuple: (is_valid: bool, error_message: str, incompatible_arcs: list)
    """
```

**Formal Rules Enforced:**
- **Source**: •t = ∅ (no input arcs), t• ≠ ∅ (must have output arcs)
- **Sink**: •t ≠ ∅ (must have input arcs), t• = ∅ (no output arcs)

**Status:** ✅ Implemented (not yet called from UI)

---

### 1.3 Where Source/Sink is Recognized During Simulation

#### A. Locality Detection (Independence Analysis)

**Location:** `src/shypn/engine/simulation/controller.py:565-600`

```python
def _get_all_places_for_transition(self, transition) -> set:
    """Get places involved in transition's locality.
    
    **Source/Sink Handling:**
    - Source: Only output places (locality = t•)
    - Sink: Only input places (locality = •t)
    - Normal: Both (locality = •t ∪ t•)
    """
    is_source = getattr(transition, 'is_source', False)
    is_sink = getattr(transition, 'is_sink', False)
    
    # Skip input places for source
    if not is_source:
        # Get input places...
    
    # Skip output places for sink
    if not is_sink:
        # Get output places...
```

**Purpose:** Enables proper independence detection for parallel execution  
**Status:** ✅ Implemented and tested

#### B. Token Consumption (Firing Behavior)

**Locations (4 files):**

1. **`src/shypn/engine/immediate_behavior.py`**
   ```python
   def fire(self, ...):
       is_source = getattr(self.transition, 'is_source', False)
       if not is_source:
           # Consume tokens from input places
   ```

2. **`src/shypn/engine/timed_behavior.py`**
   ```python
   def fire(self, ...):
       is_source = getattr(self.transition, 'is_source', False)
       if not is_source:
           # Consume tokens from input places
   ```

3. **`src/shypn/engine/stochastic_behavior.py`**
   ```python
   def fire(self, ...):
       is_source = getattr(self.transition, 'is_source', False)
       if not is_source:
           # Consume tokens from input places
   ```

4. **`src/shypn/engine/continuous_behavior.py`**
   ```python
   def fire(self, ...):
       is_source = getattr(self.transition, 'is_source', False)
       if not is_source:
           # Consume tokens from input places
   ```

**Purpose:** Source transitions skip token consumption (always enabled)  
**Status:** ✅ Implemented and tested (16/16 tests pass)

#### C. Token Production (Firing Behavior)

**Same 4 files as above:**

```python
def fire(self, ...):
    is_sink = getattr(self.transition, 'is_sink', False)
    if not is_sink:
        # Produce tokens to output places
```

**Purpose:** Sink transitions skip token production (tokens disappear)  
**Status:** ✅ Implemented and tested (16/16 tests pass)

---

### 1.4 Diagnostic Points for Source/Sink

#### Point 1: Model Load/Save
**File:** `src/shypn/netobjs/transition.py:474-477`
```python
if "is_source" in data:
    transition.is_source = data["is_source"]
if "is_sink" in data:
    transition.is_sink = data["is_sink"]
```
**Check:** Are source/sink flags preserved in JSON?

#### Point 2: Transition Properties
**File:** `src/shypn/netobjs/transition.py:331-332`
```python
"is_source": self.is_source,
"is_sink": self.is_sink
```
**Check:** Are properties returned correctly?

#### Point 3: Behavior Factory
**File:** `src/shypn/engine/behavior_factory.py`
```python
def get_behavior(transition, model):
    # Creates behavior instance
    # Behavior instances use getattr(transition, 'is_source', False)
```
**Check:** Is behavior accessing correct transition instance?

#### Point 4: Simulation Execution
**File:** `src/shypn/engine/simulation/controller.py:195-220`
```python
def _update_enablement_times(self):
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        # Check structural enablement
```
**Check:** Are source transitions recognized as always structurally enabled?

---

## 2. Simulation Time Diagnostic Path

### 2.1 Time Tracking

**Location:** `src/shypn/engine/simulation/controller.py`

```python
class SimulationController:
    def __init__(self, ...):
        self.time = 0.0  # Line 120 - Logical simulation time
```

**Time Advances:**
- **Step execution:** `self.time += time_step` (line 466)
- **Reset:** `self.time = 0.0` (line 1430)

---

### 2.2 Time Access Points

#### A. From Behavior Classes
**Location:** `src/shypn/engine/transition_behavior.py:208-213`

```python
def _get_current_time(self):
    """Get current simulation time from model.
    
    Returns:
        float: Current logical/simulation time
    """
    return getattr(self.model, 'logical_time', 0.0)
```

**Access Chain:**
1. Behavior calls `_get_current_time()`
2. Reads `model.logical_time` property
3. Model adapter delegates to controller: `controller.time`

#### B. From ModelAdapter
**Location:** `src/shypn/engine/simulation/controller.py:84-91`

```python
@property
def logical_time(self):
    """Get current logical time from controller.
    
    Returns:
        float: Current simulation time from controller, or 0.0 if no controller
    """
    if self._controller is not None:
        return self._controller.time
    return 0.0
```

#### C. Direct Access
**Location:** `src/shypn/engine/simulation/controller.py:1458`

```python
def get_state(self) -> Dict[str, Any]:
    """Get current simulation state information."""
    return {
        'time': self.time,
        'running': self._running,
        'enabled_transitions': len(self._find_enabled_transitions())
    }
```

---

### 2.3 Time Display (UI)

**Location:** `src/shypn/helpers/simulate_tools_palette_loader.py:870-895`

```python
def update_time_display(self):
    """Update the time display label with current simulation time."""
    settings = self.simulation.settings
    
    if settings.duration is not None:
        # Show: "Time: current / duration @ speed"
        text = TimeFormatter.format_with_duration(...)
        self.time_display_label.set_text(f"Time: {text}{speed_text}")
    else:
        # Show: "Time: current @ speed"
        time_text = TimeFormatter.format(
            self.simulation.time,  # ← Reads controller.time
            TimeUnits.SECONDS,
            include_unit=True
        )
        self.time_display_label.set_text(f"Time: {time_text}{speed_text}")
```

**Update Triggered By:**
- Step listener callbacks
- Continuous run loop
- Manual refresh

---

### 2.4 Time Used in Behaviors

#### A. Timed Transitions
**Location:** `src/shypn/engine/timed_behavior.py:94-100`

```python
def set_enablement_time(self, time: float):
    """Record when transition became enabled.
    
    Args:
        time: Current simulation time when enablement occurred
    """
    self._enablement_time = time
```

**Usage:**
```python
def is_enabled(self):
    elapsed = self._get_current_time() - self._enablement_time
    return elapsed >= self.transition.delay
```

#### B. Stochastic Transitions
**Location:** `src/shypn/engine/stochastic_behavior.py:100-105`

```python
def set_enablement_time(self, time: float):
    """Record when transition became enabled and sample firing time."""
    self._enablement_time = time
    self._sample_firing_time()  # Schedules future firing
```

#### C. Continuous Transitions
**Location:** `src/shypn/engine/continuous_behavior.py:172-175`

```python
def is_enabled(self):
    is_source = getattr(self.transition, 'is_source', False)
    if is_source:
        return True  # Always enabled
```

---

### 2.5 Diagnostic Points for Time

#### Point 1: Time Initialization
**Check:** `controller.time == 0.0` after construction and reset

#### Point 2: Time Advancement
**Check:** `controller.time` increases by `dt` each step

#### Point 3: Time Consistency
**Check:** All behaviors see same time via `model.logical_time`

#### Point 4: Time Display
**Check:** UI shows `controller.time` correctly formatted

#### Point 5: Time-Based Enablement
**Check:** Timed transitions wait for `elapsed >= delay`

#### Point 6: Time in Data Collection
**Check:** Events logged with correct `controller.time`

---

## 3. Complete Diagnostic Checklist

### Source/Sink Recognition

```
□ 1. Load model with source/sink transitions
     → Check: transition.is_source / is_sink are True

□ 2. Inspect transition properties
     → Check: Properties dialog shows source/sink status

□ 3. Start simulation
     → Check: Source transitions fire without input tokens
     → Check: Sink transitions consume tokens without producing

□ 4. Check locality detection
     → Check: Source locality = output places only
     → Check: Sink locality = input places only

□ 5. Check independence
     → Check: Two sources with different outputs are independent
     → Check: Two sources with same output are dependent

□ 6. Validate structure (new feature)
     → Check: Source with input arc fails validation
     → Check: Sink with output arc fails validation
```

### Simulation Time

```
□ 1. Check initial time
     → Expected: controller.time == 0.0

□ 2. Execute single step
     → Check: controller.time advances by dt

□ 3. Check UI display
     → Expected: Time label shows current simulation time

□ 4. Check timed transition
     → Create timed transition with delay=5.0
     → Check: Fires after 5.0 time units

□ 5. Check stochastic transition
     → Create stochastic transition
     → Check: Firing time is sampled correctly

□ 6. Check continuous transition
     → Create continuous transition
     → Check: Fires continuously with rate

□ 7. Check data collection
     → Check: Events logged with correct timestamps

□ 8. Reset simulation
     → Expected: controller.time resets to 0.0
```

---

## 4. Known Issues and Gaps

### Source/Sink

1. **✅ FIXED:** Structural validation implemented
2. **⏳ PENDING:** UI integration - validation not called from property dialog
3. **⏳ PENDING:** Arc creation blocking - can still create invalid arcs
4. **⏳ PENDING:** Visual indicators - no warning for invalid structure

### Time

1. **✅ WORKING:** Time tracking is correct
2. **✅ WORKING:** Time display updates properly
3. **✅ WORKING:** Time-based behaviors work correctly
4. **⏳ IMPROVEMENT:** Could add time diagnostic panel with:
   - Current time
   - Enabled transitions count
   - Next scheduled events
   - Time scale indicator

---

## 5. Testing Commands

### Test Source/Sink Recognition
```bash
# Run existing tests
cd /home/simao/projetos/shypn
python3 tests/test_source_sink.py
python3 tests/test_timed_source.py
python3 tests/test_timed_sink.py
python3 tests/test_source_sink_strict.py

# Expected: All tests pass
```

### Test Simulation Time
```bash
# Run controller tests
python3 tests/test_simulation_controller.py

# Check time advancement in logs
grep "time" app_debug.log | tail -20
```

### Interactive Testing
```bash
# Launch application
python3 src/shypn.py

# Create test model:
# 1. Create source transition T1
# 2. Create place P1
# 3. Create arc T1 → P1
# 4. Mark T1 as source in properties
# 5. Run simulation
# 6. Check: Tokens appear in P1 without input
```

---

## 6. Recommended Improvements

### Priority 1: Complete Strict Formalism (Current Work)
- ✅ Validation method implemented
- ⏳ Add UI validation in properties dialog
- ⏳ Block invalid arc creation
- ⏳ Add visual warnings

### Priority 2: Enhanced Diagnostics
- Add simulation info panel showing:
  - Current time
  - Enabled transitions (with source/sink indicators)
  - Next scheduled events
  - Independence information
- Add source/sink visual markers on canvas
- Add arc validation indicators

### Priority 3: Better Error Messages
- Clear messages when source/sink doesn't work
- Suggest fixes (remove incompatible arcs)
- Link to documentation

---

## 7. Architecture Summary

```
USER ACTION (mark as source/sink)
    ↓
TRANSITION OBJECT (sets is_source/is_sink flag)
    ↓
VALIDATION (optional, checks structure)
    ↓
MODEL SAVE/LOAD (persists flags in JSON)
    ↓
SIMULATION START
    ↓
CONTROLLER (updates enablement, creates behaviors)
    ↓
BEHAVIOR FACTORY (creates typed behavior instances)
    ↓
BEHAVIOR.fire() (checks is_source/is_sink)
    ↓
TOKEN OPERATIONS (skip consumption/production)
    ↓
TIME ADVANCEMENT (controller.time += dt)
    ↓
UI UPDATE (displays time and marking)
```

**Key Flow:**
1. User sets source/sink flag on transition
2. Flag is stored in transition object
3. During simulation, behaviors check flag
4. Behaviors skip token operations accordingly
5. Time advances independently
6. UI displays current state

---

## 8. Next Steps

1. **Add UI validation** - Call `validate_source_sink_structure()` from properties dialog
2. **Add arc creation blocking** - Prevent creating invalid arcs in arc handler
3. **Add visual indicators** - Show warning icon for invalid structure
4. **Create diagnostic panel** - Show detailed simulation status
5. **Update documentation** - Add troubleshooting guide

---

**Conclusion:** The diagnostic path is well-defined and working. Source/sink recognition happens at multiple levels (object, behavior, controller), and time tracking is consistent throughout. The main gap is UI-level validation to prevent invalid structures from being created.
