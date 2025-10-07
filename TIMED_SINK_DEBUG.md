# Timed Sink and Source Transition Debugging

## Issue Reports
1. User reports: "sink still not consumes during timed transition simulation"
2. User reports: "source timed transition is not producing tokens"

## Investigation Summary

### Code Review
The timed behavior code appears to be correct:

1. **Fire Method Logic**:
   ```python
   # Consume tokens from input places (skip if source transition)
   if not is_source:
       ...consume tokens...
   else:
       # Source transition - no consumption
   
   # Produce tokens to output places (skip if sink transition)
   if not is_sink:
       ...produce tokens...
   else:
       # Sink transition - no production
   ```
   
   This means:
   - **Sink transitions**: WILL consume tokens, will NOT produce tokens
   - **Source transitions**: Will NOT consume tokens, WILL produce tokens

2. **Enablement Checking**:
   - Sink transitions require input arcs with sufficient tokens
   - Source transitions are always structurally enabled (no input check)
   - Both must be within the timing window [earliest, latest]
   - Enablement time must be set by the simulation controller

### Test Results
Created unit tests that demonstrate:
- ✅ Timed sink transitions correctly consume tokens without producing (`test_timed_sink.py`)
- ✅ Timed source transitions correctly produce tokens without consuming (`test_timed_source.py`)
- ✅ The fire() method works as expected for both types

### Debug Output Added
Added extensive debug logging to help diagnose issues for BOTH sink and source transitions:

1. **In `can_fire()` method**:
   - Logs when checking sink OR source transitions
   - Shows guard evaluation
   - Shows token availability checks (sink) or skip message (source)
   - Shows timing window checks
   - Identifies exact failure reason

2. **In `fire()` method**:
   - Logs when firing sink OR source transitions
   - Shows token consumption details (sink) or skip message (source)
   - Shows token production details (source) or skip message (sink)
   - Shows final consumed/produced maps

### How to Use Debug Output

1. **Run your model with the sink or source transition**:
   ```bash
   python3 src/shypn.py
   ```

2. **Look for debug messages in the console**:
   
   **For SINK transitions:**
   ```
   [TIMED CAN_FIRE] Checking sink transition T1: is_sink=True
   [TIMED CAN_FIRE] Checking 1 input arcs
   [TIMED CAN_FIRE] CAN FIRE: elapsed=1.000, window=[1.0, 1.0]
   [TIMED FIRE] Sink transition T1: is_sink=True, input_arcs=1, output_arcs=0
   [TIMED FIRE] Consuming tokens from 1 input arcs
   [TIMED FIRE]   Place P1: 5 tokens -> consuming 2
   [TIMED FIRE]   Place P1: 3 tokens (after consumption)
   [TIMED FIRE] Skipping production (sink transition)
   [TIMED FIRE] Fire complete: consumed={1: 2.0}, produced={}
   ```
   
   **For SOURCE transitions:**
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

3. **Common Issues to Check**:

   a. **Transition not firing at all**:
      - Check if you see `[TIMED CAN_FIRE]` messages
      - If you see "Not enabled yet (enablement_time is None)", the simulation controller hasn't recognized the transition as enabled
      - If you see "Too early" or "Too late", the timing window is wrong

   b. **Insufficient tokens (SINK only)**:
      - Look for "Insufficient tokens: P{id} has X, needs Y"
      - Make sure the input places have enough tokens

   c. **No output arcs (SOURCE only)**:
      - Check that source transition has output arcs connected to places
      - Source transitions need output arcs to produce tokens

   d. **Guard failures**:
      - Look for "Guard failed: {reason}"
      - Check the transition's guard condition

   e. **Wrong timing**:
      - Check the "elapsed" time vs the timing window
      - Make sure earliest ≤ elapsed ≤ latest

### Expected Behavior

#### Sink Transitions
A properly configured timed sink transition should:

1. **Have input arcs** from places (tokens to consume)
2. **Have NO output arcs** (or they will be ignored during firing)
3. **Have `is_sink = True`** set in properties dialog
4. **Have timing parameters** (earliest, latest) configured
5. **Fire when**:
   - Input places have sufficient tokens
   - Current time is within the timing window after enablement
   - Guard condition passes (if defined)

#### Source Transitions
A properly configured timed source transition should:

1. **Have NO input arcs** (or they will be ignored during firing)
2. **Have output arcs** to places (tokens to produce)
3. **Have `is_source = True`** set in properties dialog
4. **Have timing parameters** (earliest, latest) configured
5. **Fire when**:
   - Current time is within the timing window after enablement
   - Guard condition passes (if defined)
   - No token availability check (source is always enabled structurally)

### Configuration Checklist

#### For Sink Transitions
To verify your sink transition is correctly configured:

1. Open the Transition Properties dialog
2. Check the "Sink" checkbox is enabled
3. Set the transition type to "Timed"
4. Configure timing parameters (e.g., earliest=1.0, latest=1.0)
5. Verify input arcs are connected from places
6. Verify NO output arcs are connected (or disconnect them)

#### For Source Transitions
To verify your source transition is correctly configured:

1. Open the Transition Properties dialog
2. Check the "Source" checkbox is enabled
3. Set the transition type to "Timed"
4. Configure timing parameters (e.g., earliest=1.0, latest=1.0)
5. Verify NO input arcs are connected (or disconnect them)
6. Verify output arcs are connected to places

### Next Steps

1. Run your model with debug output enabled
2. Look for the `[TIMED CAN_FIRE]` and `[TIMED FIRE]` messages
3. Share the debug output to identify the exact issue
4. Common fixes:
   - Ensure `is_sink` checkbox is checked in properties
   - Verify timing parameters are correct
   - Make sure input places have tokens
   - Check that simulation is actually running (not paused)

## To Disable Debug Output

Once the issues are resolved, you can disable debug output by changing:
```python
DEBUG_SINK_CAN_FIRE = True  → False
DEBUG_SINK = True           → False
DEBUG_SOURCE_CAN_FIRE = True → False
DEBUG_SOURCE = True          → False
```

In `/home/simao/projetos/shypn/src/shypn/engine/timed_behavior.py`

## Summary

The code is correct and should work. The issues are likely one of:

**For Sink Transitions:**
1. Configuration error (is_sink not set, or wrong timing)
2. Model structure issue (no input arcs, or disconnected)
3. Simulation not running properly (paused, or controller issue)

**For Source Transitions:**
1. Configuration error (is_source not set, or wrong timing)
2. Model structure issue (no output arcs, or disconnected)
3. Simulation not running properly (paused, or controller issue)
4. Enablement time not being set (controller not tracking source transitions)

The debug output will help identify the exact cause.
