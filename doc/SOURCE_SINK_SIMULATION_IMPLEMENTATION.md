# Source/Sink Simulation Implementation

## Overview
Implemented source/sink transition behavior in the simulation engine. Source and sink transitions interface with external systems:
- **Source transitions**: Generate tokens from external sources (don't consume from input places)
- **Sink transitions**: Consume tokens to external sinks (don't produce to output places)

## Changes Summary

### 1. Immediate Transitions (`src/shypn/engine/immediate_behavior.py`)

**can_fire() method:**
- Added check for `is_source` attribute on transition
- Source transitions return `(True, "enabled-source")` immediately (always enabled)
- Skip token availability checks for source transitions

**fire() method:**
- Skip Phase 1 (token consumption) if `is_source = True`
- Skip Phase 2 (token production) if `is_sink = True`
- Consumed/produced maps remain empty for skipped phases

### 2. Timed Transitions (`src/shypn/engine/timed_behavior.py`)

**can_fire() method:**
- Source transitions always structurally enabled
- Skip input token checks for source transitions
- Still respect timing windows (earliest/latest)
- Return `(True, "enabled-source (elapsed=X.XXX)")` for source transitions

**fire() method:**
- Skip token consumption from input arcs if `is_source = True`
- Skip token production to output arcs if `is_sink = True`
- Timing behavior (enablement tracking) unchanged

### 3. Stochastic Transitions (`src/shypn/engine/stochastic_behavior.py`)

**can_fire() method:**
- Source transitions always structurally enabled
- Skip burst token availability checks for source transitions
- Still respect scheduled fire time from exponential distribution
- Return `(True, "enabled-source (burst=X)")` for source transitions

**fire() method:**
- Skip Phase 1 (burst token consumption) if `is_source = True`
- Skip Phase 2 (burst token production) if `is_sink = True`
- Burst multiplier still applies (but only to one side)

### 4. Continuous Transitions (`src/shypn/engine/continuous_behavior.py`)

**can_fire() method:**
- Source transitions always enabled (return immediately)
- Skip input place positive token checks for source transitions
- Return `(True, "enabled-source")` for source transitions

**integrate_step() method:**
- Skip Phase 1 (continuous consumption) if `is_source = True`
- Skip Phase 2 (continuous production) if `is_sink = True`
- Rate function evaluation unchanged
- Integration method (RK4 approximation) unchanged

## Behavioral Properties

### Source Transitions
- **Enablement**: Always enabled (no input tokens required)
- **Firing**: Produces tokens to output places without consuming from inputs
- **Use cases**: 
  - External arrivals (customers, jobs, messages)
  - Token generation from outside the system
  - Constant rate sources (combined with timed/stochastic/continuous)

### Sink Transitions
- **Enablement**: Requires sufficient input tokens (normal rules apply)
- **Firing**: Consumes tokens from input places without producing to outputs
- **Use cases**:
  - External departures (completed jobs, serviced customers)
  - Token removal from the system
  - Resource consumption endpoints

### Combined Source + Sink
- Transitions can be both source AND sink (acts as a passthrough/converter)
- Neither consumes nor produces tokens
- Can still respect timing, stochastic delays, or continuous rates
- Useful for modeling transitions that trigger effects outside the Petri net

## Integration with Existing Code

### Model Layer
- `Transition.is_source` and `Transition.is_sink` boolean properties (already implemented)
- Default values: `False` (backward compatible)
- Serialization: Full support in `to_dict()` and `from_dict()`

### UI Layer
- Checkboxes in transition properties dialog (Basic Properties tab)
- Visual indicators: Arrows on transition edges (→| for source, |→ for sink)
- No changes to property dialog behavior needed

### Simulation Layer
- All four transition types updated: immediate, timed, stochastic, continuous
- Enablement logic respects source property
- Firing logic skips consumption/production based on source/sink flags
- Event recording unchanged (records actual consumed/produced amounts)

## Testing Notes

### Test Coverage Needed
1. **Source Immediate**: Should fire without input tokens, produce to output
2. **Source Timed**: Should respect timing window, produce without consuming
3. **Source Stochastic**: Should sample delay, produce with burst, no consumption
4. **Source Continuous**: Should integrate continuously, produce without consuming
5. **Sink Immediate**: Should consume input tokens, produce nothing
6. **Sink Timed**: Should consume with timing, produce nothing
7. **Sink Stochastic**: Should consume with burst, produce nothing
8. **Sink Continuous**: Should consume continuously, produce nothing
9. **Reset Behavior**: Source transitions should work correctly after simulation reset
10. **Combined Source+Sink**: Neither consume nor produce

### Known Issues
- User reported: "source does not reset count on reset" - need to verify enablement state after reset
- User reported: "sink works only for immediate" - should be fixed now for all types

## Implementation Status

✅ **Complete**: 
- Immediate source/sink behavior
- Timed source/sink behavior
- Stochastic source/sink behavior
- Continuous source/sink behavior
- UI visual markers
- Model serialization

⏳ **Pending Testing**:
- Simulation reset behavior for source transitions
- Verify sink works for timed, stochastic, continuous

## Files Modified

1. `src/shypn/engine/immediate_behavior.py` - Source/sink logic in can_fire() and fire()
2. `src/shypn/engine/timed_behavior.py` - Source/sink logic in can_fire() and fire()
3. `src/shypn/engine/stochastic_behavior.py` - Source/sink logic in can_fire() and fire()
4. `src/shypn/engine/continuous_behavior.py` - Source/sink logic in can_fire() and integrate_step()

## Next Steps

1. Test all transition types with source marker
2. Test all transition types with sink marker  
3. Verify simulation reset behavior
4. Add unit tests for source/sink firing logic
5. Update user documentation with source/sink examples

