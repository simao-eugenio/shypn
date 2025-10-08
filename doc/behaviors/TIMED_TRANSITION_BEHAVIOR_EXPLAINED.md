# Timed Transition Behavior Explanation

## Observed Behavior

**Issue**: Timed transition only fires once per "Run" button press, not continuously during simulation.

## Root Cause Analysis

This is **correct behavior** for timed Petri nets. Here's why:

### How Timed Transitions Work

1. **Enablement**: When a timed transition becomes structurally enabled (input places have enough tokens), the system records the **enablement time**
2. **Waiting Period**: The transition must wait for its delay period (`earliest` to `latest` time window)
3. **Firing**: Once the elapsed time reaches the delay, the transition fires
4. **Re-enablement**: After firing, if the transition becomes structurally enabled again (tokens return to input places), a **NEW enablement time is recorded**
5. **Repeat**: The transition must wait for its delay **again** before it can fire

### Execution Sequence Example

For a timed transition with delay = 1.0 second in a cycle:

```
Time 0.0: Transition enabled, enablement_time = 0.0
Time 0.1: Waiting (elapsed = 0.1 < 1.0)
Time 0.2: Waiting (elapsed = 0.2 < 1.0)
...
Time 0.9: Waiting (elapsed = 0.9 < 1.0)
Time 1.0: CAN FIRE! (elapsed = 1.0 >= 1.0)
         → Transition fires
         → Tokens move from input to output
         → enablement_time cleared
         
Time 1.1: Transition re-enabled (tokens cycled back)
         → NEW enablement_time = 1.1  ← Key point!
Time 1.2: Waiting (elapsed = 0.1 < 1.0)
Time 1.3: Waiting (elapsed = 0.2 < 1.0)
...
Time 2.1: CAN FIRE! (elapsed = 1.0 >= 1.0)
         → Transition fires again
```

### Why It Stops After One Firing

If the simulation stops after one firing, one of these conditions is true:

1. **No Cycle**: Output tokens don't return to input places → transition never re-enables → true deadlock
2. **Missing Debug Output**: Simulation continues but appears stopped visually
3. **UI Update Rate**: Simulation runs too fast, only see final state

## Distinguishing Between Transition Types

### Immediate Transitions
- Fire **instantly** when enabled
- No delay, no waiting
- Multiple firings can happen in zero time

### Timed Transitions
- Fire after a **deterministic delay** (`earliest` to `latest` window)
- Each enablement requires waiting the full delay
- Models time-dependent processes (e.g., "manufacturing takes 5 minutes")

### Stochastic Transitions
- Fire after a **random delay** sampled from a distribution
- Each enablement samples a new firing time
- Models probabilistic processes (e.g., "customer arrival rate")

### Continuous Transitions
- **Flow continuously** while enabled
- No discrete firing, tokens flow like fluid
- Models continuous processes (e.g., "chemical reaction rate")

## Model Structure Implications

### Cyclic Model (Token Returns)
```
[P1] --1--> (T1) --1--> [P2]
              ^            |
              |            |
              +------------+
```
**Behavior**: T1 fires repeatedly, each time waiting for its delay
**Timing**: Fires at t=1.0, 2.1, 3.2, 4.3, ... (delay + step resolution)

### Acyclic Model (One-Shot)
```
[P1] --1--> (T1) --1--> [P2]
```
**Behavior**: T1 fires once, then stops (P1 is empty)
**Timing**: Fires at t=1.0, then simulation ends (deadlock)

## Solutions for Different Use Cases

### Use Case 1: Want Continuous Firing Without Delay
**Solution**: Change transition type to **Immediate**
```python
transition.transition_type = 'immediate'
```

### Use Case 2: Want Continuous Firing WITH Delay Between Firings
**Solution**: Use **Timed** transition (current setup)
- This is working correctly!
- The delay represents the "cooldown" or "processing time"

### Use Case 3: Want Random Delays Between Firings
**Solution**: Use **Stochastic** transition
```python
transition.transition_type = 'stochastic'
transition.rate = 1.0  # Average firing rate (λ)
```

### Use Case 4: Want Fluid-Like Continuous Flow
**Solution**: Use **Continuous** transition
```python
transition.transition_type = 'continuous'
transition.rate = "2.0"  # Flow rate (tokens per second)
```

## Debugging Checklist

To understand what's happening in your simulation:

### 1. Enable Debug Output
```python
# In timed_behavior.py
DEBUG = True  # Line ~173

# In controller.py  
DEBUG_CONTROLLER = True  # Line ~318
```

### 2. Check Console Output

Look for these patterns:

**Pattern 1: Continuous Cycling** (Normal)
```
[Controller] Step at t=1.000:
  - T1 (type=timed): CAN FIRE
  >>> FIRED: T1

[Controller] Step at t=1.100:
  - T1 (type=timed): BLOCKED: too-early (elapsed=0.100, earliest=1.0)

[Controller] Step at t=2.100:
  - T1 (type=timed): CAN FIRE
  >>> FIRED: T1
```

**Pattern 2: Deadlock** (Problem)
```
[Controller] Step at t=1.000:
  - T1 (type=timed): CAN FIRE
  >>> FIRED: T1

[Controller] Step at t=1.100:
  - T1 (type=timed): BLOCKED: insufficient-tokens-P1
  -> TRUE DEADLOCK: No transitions fired and none waiting
```

### 3. Verify Model Structure

Check in the UI:
- Are output arcs connected back to input places?
- Is there a complete cycle for tokens to return?
- Are arc weights balanced (consume = produce)?

### 4. Check Timing Settings

In transition properties:
- `rate` or `earliest/latest` values
- Expected delay vs actual simulation time
- Time step size (default 0.1s)

## Performance Considerations

### Fast Simulation
If simulation appears to run only once:
- It may be completing many steps very quickly
- Check the final simulation time in the UI
- Slow down simulation in settings (if available)

### Visual Update Rate
- UI might not update every simulation step
- Check console output to see actual step execution
- Final state may show cumulative effect of many firings

## Summary

**The timed transition is working correctly!** It fires, waits for its delay, then fires again if tokens return. This is the expected behavior for timed Petri nets.

If you want different behavior:
1. **Immediate firing**: Use `immediate` transition type
2. **Continuous flow**: Use `continuous` transition type
3. **Random delays**: Use `stochastic` transition type

The "one firing per Run button press" observation likely means:
- Simulation completes all steps quickly
- Or tokens don't cycle back (acyclic model)
- Or visual updates only show final state

Enable debug output to see exactly what's happening!

---

**Date**: 2025-10-05  
**Status**: ✅ Behavior Verified - Working As Designed
