# Headless Simulation Test Results

**Date**: October 18, 2025  
**Test**: Headless simulation verification  
**Purpose**: Identify why simulation is not triggering transitions

## Critical Finding

🔴 **ROOT CAUSE IDENTIFIED: Transitions are not firing during simulation**

### Evidence

1. **Simulation controller runs**: `step()` returns True, time advances (0.1, 0.2, 0.3...)
2. **No token movement**: Token counts remain unchanged across all steps
3. **Simple model fails**: Even P1 → T1 → P2 with 5 tokens doesn't fire
4. **Source transitions don't work**: Stochastic sources generate 0 tokens
5. **All models affected**: Both Glycolysis models and test models show same behavior

### Test Results

```
Results: 3 passed, 4 failed, 0 skipped out of 7 tests

✓ PASS - Controller Initialization
✗ FAIL - Transition Enablement (SimulationController has no 'get_behavior' method)
✗ FAIL - Single Step Execution (tokens don't move)
✗ FAIL - Multiple Steps Execution (tokens don't move)
✓ PASS - Glycolysis Model (no sources) (loads but doesn't simulate)
✓ PASS - Glycolysis Model (with sources) (loads but doesn't simulate)
✗ FAIL - Stochastic Source Transitions (doesn't generate tokens)
```

### Detailed Observations

#### Test 3: Single Step - Simple Model
```
Model: P1(5 tokens) → T1(immediate) → P2(0 tokens)

Before step:
  P1 tokens: 5
  P2 tokens: 0
  Time: 0.0

After step:
  P1 tokens: 5  ← NO CHANGE
  P2 tokens: 0  ← NO CHANGE
  Time: 0.1     ← TIME ADVANCED
  Result: False
```

**Expected**: P1=4, P2=1 (one token moved)  
**Actual**: P1=5, P2=0 (no tokens moved)

#### Test 6: Stochastic Source
```
Model: SOURCE(stochastic, rate=1.0) → P1(0 tokens)

Step  1: P1=0 tokens, time=0.100, result=True
Step  2: P1=0 tokens, time=0.200, result=True
...
Step 10: P1=0 tokens, time=1.000, result=True
```

**Expected**: P1 should have tokens (source should generate)  
**Actual**: P1=0 (source never fires)

#### Glycolysis Model with Sources
```
Initial tokens: 26
Final tokens: 26  ← NO CHANGE
Token change: +0

5 source transitions present (rate=0.1 each)
20 simulation steps executed
Time advanced from 0.0 to 2.0

But NO tokens generated or moved!
```

## Technical Analysis

### Issue 1: Missing `get_behavior()` Method

```python
AttributeError: 'SimulationController' object has no attribute 'get_behavior'
```

The test tried to check enablement like this:
```python
behavior = controller.get_behavior(trans)
if behavior.is_structurally_enabled():
    ...
```

But `SimulationController` doesn't expose `get_behavior()` publicly.

### Issue 2: Transitions Not Firing

The `step()` method is being called and returns successfully, but:
- No tokens are consumed from input places
- No tokens are produced in output places
- Time advances (suggests loop is running)
- But transition firing logic is not executing

### Possible Root Causes

1. **Enablement check failing**: Transitions may not be detected as enabled
2. **Behavior not firing**: Even if enabled, fire() method not called
3. **Token update not happening**: fire() called but tokens not updated
4. **Model adapter issue**: SimulationController uses ModelAdapter, may not see tokens
5. **Arc connection issue**: Arcs may not be properly connected to places/transitions

## Next Steps

### Immediate Actions

1. **Check SimulationController.step() implementation**:
   - Does it check for enabled transitions?
   - Does it call behavior.fire()?
   - Does it update place markings?

2. **Check ModelAdapter**:
   - Does it properly expose places dictionary?
   - Does controller.model_adapter.places[id].marking work?

3. **Check behavior classes**:
   - Does ImmediateBehavior.is_structurally_enabled() work?
   - Does fire() method update tokens?

4. **Add debug logging to simulation loop**:
   - Log which transitions are checked
   - Log enablement status
   - Log firing attempts
   - Log token updates

###Investigation Script

Need to add comprehensive logging to understand what's happening:

```python
# In SimulationController.step()
print(f"Step start: time={self.time}")
print(f"  Places: {[(p.id, p.marking) for p in self.model.places]}")
print(f"  Checking {len(self.model.transitions)} transitions...")

for trans in self.model.transitions:
    behavior = self.get_behavior(trans)
    enabled = behavior.is_structurally_enabled()
    print(f"    {trans.name}: enabled={enabled}")
    if enabled:
        print(f"      Attempting to fire...")
        result = behavior.fire()
        print(f"      Fire result: {result}")
```

## Implications for GUI Simulation

If the core simulation engine isn't firing transitions in headless mode,
it definitely won't work in GUI mode either. This explains why you said
"simulation was not triggering on the system".

**The issue is in the simulation engine core, not the GUI layer.**

## Files for Investigation

1. `src/shypn/engine/simulation/controller.py` - SimulationController.step()
2. `src/shypn/engine/immediate_behavior.py` - ImmediateBehavior.fire()
3. `src/shypn/engine/stochastic_behavior.py` - StochasticBehavior.fire()
4. `src/shypn/engine/simulation/controller.py` - ModelAdapter

## Temporary Workaround

None available - simulation is fundamentally broken. Must fix core engine.

---

**Status**: 🔴 CRITICAL BUG - Simulation engine not firing transitions  
**Impact**: All simulation functionality non-functional  
**Priority**: HIGHEST - blocks all simulation features
