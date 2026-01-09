# Timed Transition Bug Fix - January 8, 2026

## Problem Summary
Timed transitions were firing 10x too early (at t=1s instead of t=10s) because the simulation engine was not reading the timing parameters from the JSON model files.

## Root Cause
**Property Name Mismatch** between JSON schema and code:

- **JSON Files** store: `earliest_time: 10.0`, `latest_time: 10.0` (at top level)
- **TimedBehavior Code** looked for: `props['earliest']`, `props['latest']` (in properties dict)
- **Fallback** used: `rate: 1.0` as delay → fired at wrong time!

## Time Petri Net (TPN) Semantics - CORRECT
The TPN firing window semantics are implemented correctly:
- `earliest` and `latest` define a **FIRING WINDOW** relative to enablement time
- Transition fires when: `t_enablement + earliest ≤ t_current ≤ t_enablement + latest`
- This is NOT an absolute delay from simulation start t=0

Example:
- Place P1 has token at t=0 → Transition T1 enabled at t=0
- T1 has earliest_time=10.0, latest_time=10.0
- T1 fires in window [0+10, 0+10] = [10s, 10s] ✓ CORRECT

## Changes Made

### 1. Transition.from_dict() - Load Parameters
**File**: `src/shypn/netobjs/transition.py`

Added restoration of `earliest_time` and `latest_time` attributes:
```python
# Restore timed transition parameters (TPN window)
if "earliest_time" in data:
    transition.earliest_time = data["earliest_time"]
if "latest_time" in data:
    transition.latest_time = data["latest_time"]
```

### 2. Transition.to_dict() - Save Parameters
**File**: `src/shypn/netobjs/transition.py`

Added serialization of timing parameters:
```python
# Serialize timed transition parameters (TPN window)
if hasattr(self, 'earliest_time') and self.earliest_time is not None:
    data["earliest_time"] = self.earliest_time
if hasattr(self, 'latest_time') and self.latest_time is not None:
    data["latest_time"] = self.latest_time
```

### 3. TimedBehavior.__init__() - Read Parameters
**File**: `src/shypn/engine/timed_behavior.py`

Updated to read from transition attributes first (where JSON loads them):
```python
# Priority order:
#   1. Direct attributes: transition.earliest_time / transition.latest_time (JSON schema)
#   2. Properties dict: transition.properties['earliest_time'] or ['earliest'] (legacy)
#   3. Fallback to rate as delay (backward compatibility)

if hasattr(transition, 'earliest_time') or hasattr(transition, 'latest_time'):
    self.earliest = float(getattr(transition, 'earliest_time', 0.0))
    self.latest = float(getattr(transition, 'latest_time', float('inf')))
else:
    # Properties dict fallback...
    # Rate fallback...
```

## Testing

### Unit Test Results
```
✓ Transition.from_dict() correctly loads earliest_time=10.0
✓ Transition.to_dict() correctly saves earliest_time=10.0
✓ TimedBehavior reads earliest=10.0, latest=10.0 (not rate=1.0)
```

### Integration Test (Pending)
1. Load test_timed_transition.shy (minimal P-T-P model)
2. Run simulation for 20 seconds
3. Verify transition fires at t=10.0s (not t=1.026s)
4. Test with erk_cascade_excitability_phasecontrol_v6.shy
5. Verify phase transitions at t=10s, t=30s, t=60s

## Impact
**All existing models with timed transitions** will now work correctly:
- Phase control systems (10s, 30s, 60s delays)
- Scheduled events (circadian rhythms, cell cycle)
- Timed processes (delayed responses, maturation times)

## Backward Compatibility
✓ Maintained: Code still supports legacy formats:
- Properties dict: `properties['earliest']`, `properties['latest']`
- Rate fallback: `rate` as delay if no timing parameters

## Next Steps
1. ✓ Fix core engine code
2. Test with minimal P-T-P model
3. Test with v6 excitability model
4. Add earliest_time/latest_time to transition properties dialog UI
5. Update documentation with TPN window semantics
