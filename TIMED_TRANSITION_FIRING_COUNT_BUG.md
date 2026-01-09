# Bug Report: Timed Transitions Do Not Record Firing Counts

## Issue
Timed transitions fire correctly (tokens flow as expected) but their firing counts are NOT recorded in CSV output.

## Evidence
Test model: `test_pulse_circuit.shy`
- 3 timed transitions (T1/T2/T3) with 10s delays each
- Visual confirmation: Tokens flow correctly through Phase_Rest → Phase_Pulse → Phase_Recovery → Phase_Rest
- CSV output: All firing counts = 0 despite visible token flow

## Root Cause Analysis

### Code Flow
1. **Timed transitions ARE processed**: `controller.py` line 1196-1205
   ```python
   timed_transitions = [t for t in self.model.transitions if t.transition_type == 'timed']
   enabled_timed = [t for t in timed_transitions if self._is_transition_enabled(t)]
   if enabled_timed:
       transition = self._select_transition(enabled_timed)
       self._fire_transition(transition)  # Line 1203
   ```

2. **Firing count SHOULD be incremented**: `controller.py` line 1424
   ```python
   def _fire_transition(self, transition):
       behavior = self._get_behavior(transition)
       success, details = behavior.fire(input_arcs, output_arcs)
       if success:
           transition.firing_count += 1  # Line 1424 - SHOULD increment
   ```

3. **Timed behavior returns success**: `timed_behavior.py` line 297
   ```python
   return (True, {'consumed': consumed_map, 'produced': produced_map, ...})
   ```

4. **CSV export reads firing_count**: `data_collector.py` line 98
   ```python
   count = getattr(transition, 'firing_count', 0)
   self.transition_data[transition.id].append((current_time, count))
   ```

### Possible Causes
1. **`_fire_transition()` not being called** for timed transitions (different code path?)
2. **`firing_count` being reset** after increment (during state update?)
3. **Transition object mismatch** (behavior operates on copy, not original?)
4. **Exception silently caught** preventing increment
5. **Timing issue**: Firing happens but count snapshot occurs before increment

## Impact
- Cannot validate pulse circuit timing from CSV (transitions T23/T24/T25 show 0 firings)
- Must rely on place states (Phase_Pulse) to infer pulse timing
- Breaks adaptation analysis that depends on transition firing counts

## Workaround
Use **Phase_Pulse place state** instead of transition firings to determine pulse timing:
```python
pulse_active = df['Phase_Pulse (mM)'] > 0.5
pulse_start = df[pulse_active]['Time (s)'].iloc[0]
pulse_end = df[pulse_active]['Time (s)'].iloc[-1]
```

## Reproduction
1. Load `workspace/projects/My_Project/mapk/models/test_pulse_circuit.shy`
2. Run simulation for 60 seconds
3. Export CSV
4. Check `Start_Pulse (firings)`, `End_Pulse (firings)`, `Reset_Phase (firings)` columns
5. Result: All show 0 despite visible token flow

## Fix Required
Investigate why line 1424 in `controller.py` doesn't execute for timed transitions, or why the increment is not persisted.
