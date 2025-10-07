# Source and Sink Transition Debug Implementation

## Summary

Added comprehensive debug output for both **timed source** and **timed sink** transitions to help diagnose simulation issues.

## Changes Made

### File Modified
`src/shypn/engine/timed_behavior.py`

### Debug Output Added

#### 1. `can_fire()` Method
Added debug messages for both source AND sink transitions:

**Source Transitions:**
- When checking if a source transition can fire
- Confirmation that input arc checks are skipped (source transitions don't consume)
- Guard evaluation results
- Timing window validation
- Final enablement decision

**Sink Transitions:**
- When checking if a sink transition can fire
- Input arc token availability checks
- Guard evaluation results
- Timing window validation
- Final enablement decision

#### 2. `fire()` Method
Added debug messages for both source AND sink transitions:

**Source Transitions:**
- When firing begins (shows is_source=True)
- Confirmation that consumption is skipped
- Token production details (before/after for each place)
- Final consumed/produced maps

**Sink Transitions:**
- When firing begins (shows is_sink=True)
- Token consumption details (before/after for each place)
- Confirmation that production is skipped
- Final consumed/produced maps

## Debug Flags

Four debug flags control output (all set to `True` by default):

```python
DEBUG_SINK_CAN_FIRE = True   # Sink transition enablement checks
DEBUG_SINK = True            # Sink transition firing
DEBUG_SOURCE_CAN_FIRE = True # Source transition enablement checks
DEBUG_SOURCE = True          # Source transition firing
```

## Example Output

### Source Transition (Producing Tokens)
```
[TIMED CAN_FIRE] Checking source transition T1: is_source=True
[TIMED CAN_FIRE] Source transition - skipping input arc checks
[TIMED CAN_FIRE] CAN FIRE: elapsed=1.000, window=[1.0, 1.0]
[TIMED FIRE] Source transition T1: is_source=True, input_arcs=0, output_arcs=1
[TIMED FIRE] Skipping consumption (source transition)
[TIMED FIRE] Producing tokens to 1 output arcs
[TIMED FIRE]   Place P1: 0 tokens -> producing 3
[TIMED FIRE]   Place P1: 3 tokens (after production)
[TIMED FIRE] Fire complete: consumed={}, produced={1: 3.0}
```

### Sink Transition (Consuming Tokens)
```
[TIMED CAN_FIRE] Checking sink transition T2: is_sink=True
[TIMED CAN_FIRE] Checking 1 input arcs
[TIMED CAN_FIRE] CAN FIRE: elapsed=1.000, window=[1.0, 1.0]
[TIMED FIRE] Sink transition T2: is_sink=True, input_arcs=1, output_arcs=0
[TIMED FIRE] Consuming tokens from 1 input arcs
[TIMED FIRE]   Place P1: 3 tokens -> consuming 2
[TIMED FIRE]   Place P1: 1 tokens (after consumption)
[TIMED FIRE] Skipping production (sink transition)
[TIMED FIRE] Fire complete: consumed={1: 2.0}, produced={}
```

## Testing

### Unit Tests Created
1. **`test_timed_sink.py`** - Verifies sink transitions consume tokens without producing
2. **`test_timed_source.py`** - Verifies source transitions produce tokens without consuming

Both tests pass successfully:
- ✅ Sink transitions correctly consume tokens
- ✅ Source transitions correctly produce tokens
- ✅ Code logic is correct

## Diagnosis Guide

### Common Issues

#### Source Transition Not Producing
1. **Check `is_source` checkbox** in transition properties
2. **Verify output arcs exist** connecting transition to places
3. **Check timing window** (earliest/latest parameters)
4. **Look for debug messages**:
   - "Not enabled yet" → Enablement time not set by controller
   - "Too early/Too late" → Timing window issue
   - "Guard failed" → Guard condition blocking

#### Sink Transition Not Consuming
1. **Check `is_sink` checkbox** in transition properties
2. **Verify input arcs exist** connecting places to transition
3. **Check input places have tokens**
4. **Check timing window** (earliest/latest parameters)
5. **Look for debug messages**:
   - "Insufficient tokens" → Need more tokens in input places
   - "Not enabled yet" → Enablement time not set by controller
   - "Too early/Too late" → Timing window issue

## Documentation

Updated **`TIMED_SINK_DEBUG.md`** to cover both sink and source transitions:
- Renamed to reflect both transition types
- Added source transition debugging information
- Added configuration checklists for both types
- Added expected behavior for both types
- Added example debug output for both types

## How to Use

1. **Run your model** with source or sink transitions
2. **Watch the console** for debug messages
3. **Identify the issue** based on the messages:
   - Not firing? Check enablement messages
   - Not consuming/producing? Check the fire messages
   - Timing issues? Check elapsed vs window values
4. **Fix the configuration** based on diagnosis
5. **Disable debug output** after resolving (set flags to False)

## Benefits

- **Immediate visibility** into what's happening during simulation
- **Detailed token tracking** (before/after values)
- **Clear distinction** between source and sink behavior
- **Easy diagnosis** of configuration vs logic issues
- **No guesswork** - see exactly why transitions fire or don't fire

## Status

✅ **Implementation complete**
✅ **Unit tests passing**
✅ **Application compiles**
✅ **Application runs successfully**
✅ **Documentation updated**

Ready for user testing and diagnosis!
