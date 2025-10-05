# Data Collector Tuple Unpacking Bug Fix

## Problem
The diagnostics panel auto-tracking was not working because `get_recent_events()` in `LocalityRuntimeAnalyzer` had a tuple unpacking bug that caused it to silently fail and return empty event lists.

## Symptoms
- Simulation running correctly
- Data collector being notified: `[CONTINUOUS] data_collector notified`
- Transitions integrating: `[CONTINUOUS] ✓ T1 integrated at t=X.XXX`
- But panel showing: `[DiagnosticsPanel] Checked 1 transitions, no activity found yet`
- `last_fired` was always `None` for all transitions

## Root Cause

The `SimulationDataCollector` stores transition data as **3-tuples**:
```python
data.append((time, 'fired', details))  # 3 elements
```

But `LocalityRuntimeAnalyzer.get_recent_events()` was unpacking as **2-tuples**:
```python
for time, event_type in transition_data[-window:]:  # ❌ WRONG - missing 'details'
```

This caused a `ValueError: too many values to unpack` which was caught by the try/except block and returned an empty list silently.

## The Fix

**File**: `src/shypn/diagnostic/locality_runtime.py`

**Before** (line 177):
```python
for time, event_type in transition_data[-window:]:
    event = {
        'time': time,
        'type': event_type,
        'transition_id': transition_id,
    }
    events.append(event)
```

**After**:
```python
for entry in transition_data[-window:]:
    time, event_type, details = entry  # Unpack all 3 elements
    event = {
        'time': time,
        'type': event_type,
        'transition_id': transition_id,
    }
    # Add details if available
    if details:
        event['details'] = details
    events.append(event)
```

## Impact

With this fix:
1. ✅ `get_recent_events()` now correctly unpacks the 3-tuple from data collector
2. ✅ Returns actual firing events instead of empty list
3. ✅ `last_fired` is populated with the actual last firing time
4. ✅ Auto-tracking can now detect active transitions
5. ✅ Panel will automatically show diagnostics for recently fired transitions

## Testing

After applying this fix, restart the application and:

1. Load a model (e.g., `models/simple.shy`)
2. Open Diagnostics tab
3. Start simulation (click [R])
4. Watch terminal output - should see:
   ```
   [DiagnosticsPanel] Checked 1 transitions, no activity found yet
   [DiagnosticsPanel] Auto-selected transition: T1, last_fired=X.XXs
   ```
5. Panel should switch from "Waiting for simulation activity..." to showing full diagnostics

## Related Files

- `src/shypn/analyses/data_collector.py` - Stores data as 3-tuples
- `src/shypn/diagnostic/locality_runtime.py` - Fixed to unpack 3-tuples correctly
- `src/shypn/analyses/diagnostics_panel.py` - Uses get_recent_events() for auto-tracking

## Lesson Learned

When data structures evolve (e.g., adding a `details` field to events), all code that unpacks or iterates those structures must be updated. The silent failure due to try/except made this bug difficult to spot without detailed debugging.

Adding explicit tuple unpacking (`entry = ...; time, type, details = entry`) is safer than inline unpacking when the tuple size might change.
