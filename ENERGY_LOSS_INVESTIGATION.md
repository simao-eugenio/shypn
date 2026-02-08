# Energy Loss Investigation - Drug Discovery Model

**Date:** February 7, 2026  
**Model:** `macrocycle_transport_normal_nme_0_enhanced.shy`  
**Issue:** Progressive energy pool loss (ATP+ADP+Pi) during adaptive hybrid simulation

## Observed Behavior

### 60s Simulation
- Initial: ATP=5.0, ADP=5.0, Pi=5.0, **Total=15.0 mM**
- Final: ATP=6.8, ADP=3.2, Pi=3.2, **Total=13.2 mM**
- **Loss: 1.77 mM (11.8%)**

### 300s Simulation
- Initial: ATP=5.0, ADP=5.0, Pi=5.0, **Total=15.0 mM**
- Final: ATP=8.9, ADP=1.1, Pi=1.1, **Total=11.1 mM**
- **Loss: 3.94 mM (26.3%)**

### Progressive Loss Pattern
```
Time    Total Pool   Loss      Rate
  0s    15.000 mM    0.000 mM  
 60s    13.172 mM    1.828 mM  0.0305 mM/s
300s    11.058 mM    3.942 mM  0.0131 mM/s
```

**Linear accumulation** despite perfect stoichiometry in model definition.

## Stoichiometry Verification

All transitions maintain perfect 1:1:1 ATP ↔ ADP + Pi conservation:

| Transition | ATP In | ADP Out | Pi Out | Balance |
|------------|--------|---------|--------|---------|
| active_transport | 2.0 | 2.0 | 2.0 | ✅ |
| ABC_efflux | 1.0 | 1.0 | 1.0 | ✅ |
| basal_ATPase | 1.0 | 1.0 | 1.0 | ✅ |
| facilitated_diffusion | 0.5 | 0.5 | 0.5 | ✅ |
| proteasomal | 4.0 | 4.0 | 4.0 | ✅ |
| lysosomal | 2.0 | 2.0 | 2.0 | ✅ |
| **ATP_synthesis** | - | - | - | ✅ Consumes ADP+Pi 1:1, produces ATP 1 |

## ATP Flux Paradox (300s)

| Metric | Value |
|--------|-------|
| ATP Production | 5,004 firings (16.68 Hz) |
| ATP Consumption | 2,254 firings (7.51 Hz) |
| **Net ATP Flux** | **+2,750 ATP (+9.17 Hz)** |
| Actual ATP Change | +3.94 mM |
| **Pool Loss** | **-3.94 mM** |

The net ATP flux predicts accumulation, but the **total pool shrinks by exactly the ATP increase amount**.

## Arc Type Analysis

### ATP_synthesis (T10) - The Critical Transition

**INPUT ARCS:**
- A36: ADP_pool → ATP_synthesis (weight=1.0, type=**normal**)
- A37: Pi_pool → ATP_synthesis (weight=1.0, type=**normal**)

**OUTPUT ARC:**
- A40: ATP_synthesis → ATP_pool (weight=1.0, type=**signal_flow**) ⚠️

### Signal Flow Arc Semantics

Confirmed from code analysis:
1. **Signal flow arcs DO consume tokens** on input (`consumes_tokens() = True`)
2. **Signal flow arcs DO produce tokens** on output (no filtering in production loops)
3. They represent **information/regulatory control**, not read-only testing
4. Mechanically identical to normal arcs for token transfer

## Code Analysis Findings

### 1. AdaptiveHybridBehavior (`adaptive_hybrid_behavior.py`)

**Mode Selection** (lines 180-230):
```python
def _select_mode(self) -> str:
    places = self._get_connected_places()
    use_stochastic, details = self.volume_selector.analyze_transition(places, [])
    mode = 'stochastic' if use_stochastic else 'continuous'
    return mode
```

**Mode Switch Handling** (lines 232-260):
```python
def _handle_mode_change(self, new_mode: str):
    if self._current_mode == new_mode:
        return  # No change
    
    # Log mode change
    # Clear stochastic scheduling state
    if old_mode == 'stochastic' and new_mode == 'continuous':
        self.stochastic_behavior.clear_enablement()
```

**❌ NO VOLUME CORRECTIONS OR TOKEN ADJUSTMENTS DURING MODE SWITCH**

### 2. ContinuousBehavior Token Production (`continuous_behavior.py`, lines 779-790)

```python
# Phase 3: Produce tokens continuously
if not is_sink and actual_flow > 0:
    for arc in produce_arcs:
        place_id = arc.target_id if not reverse_direction else arc.source_id
        target_place = self._get_place(place_id)
        if target_place is None:
            continue
        
        # Continuous production: arc_weight * actual_flow
        production = arc.weight * actual_flow
        
        if production > 0:
            target_place.set_tokens(target_place.tokens + production)
            produced_map[place_id] = production
```

**No arc type filtering - all arcs produce tokens equally.**

### 3. StochasticBehavior Token Production (`stochastic_behavior.py`, lines 804-815)

```python
# Phase 2: Produce tokens with burst multiplier
if not is_sink:
    for arc in output_arcs:
        target_place = self._get_place(arc.target_id)
        if target_place is None:
            continue
        
        amount = arc.weight * burst
        
        # Burst production
        target_place.set_tokens(target_place.tokens + amount)
        produced_map[arc.target_id] = float(amount)
```

**Again, no arc type filtering - signal_flow arcs treated identically to normal arcs.**

### 4. TauLeapingEngine (`tau_leaping_engine.py`, lines 687-693)

```python
# Phase 2: Produce tokens (skip if sink)
if not is_sink:
    for arc in output_arcs:
        target_place = arc.target
        if target_place is None:
            continue
        
        amount = arc.weight * num_firings
        target_place.set_tokens(target_place.tokens + amount)
        produced_map[target_place.id] = float(amount)
```

**Same pattern - no special handling.**

## Suspected Root Causes

### Hypothesis 1: Floating-Point Accumulation
- 5,004 ATP_synthesis firings in 300s
- 58,320+ chameleon fold/unfold transitions
- Each firing involves multiple `set_tokens()` operations
- Potential loss: ~0.001% per operation × 60,000+ operations = **significant error**

### Hypothesis 2: RK4 Integration Error in Continuous Mode
- Continuous mode uses RK4 integration with `dt` steps
- Adaptive transitions switch between continuous and stochastic
- RK4 may accumulate error when:
  - Flow rates are high (chameleon: 194 Hz)
  - Mode switches occur mid-step
  - No explicit mass conservation enforcement

### Hypothesis 3: Signal Flow Arc Handling in Adaptive Mode
- ATP_synthesis produces ATP via **signal_flow arc A40**
- During mode switches:
  - **No volume corrections applied**
  - **No token conservation checks**
  - Tokens may be lost/gained during continuous→stochastic transitions

### Hypothesis 4: Lack of Explicit Conservation Enforcement
- No post-step conservation checks in any engine
- No automatic correction of mass balance drift
- Errors accumulate unbounded over long simulations

## Proposed Test Strategy

### Minimal Test Model

Create a simplified model to isolate the issue:

**Places:**
- P1: ATP (initial: 5.0 mM)
- P2: ADP (initial: 5.0 mM)
- P3: Pi (initial: 5.0 mM)

**Transitions:**
- T1: ATP_synthesis (stochastic, rate=10 Hz)
  - Inputs: ADP + Pi (normal arcs)
  - Output: ATP (**signal_flow arc** ← test this)
- T2: ATPase (stochastic, rate=10 Hz)
  - Input: ATP (**signal_flow arc** ← test this)
  - Outputs: ADP + Pi (normal arcs)

**Configuration:**
- Duration: 3000s (50 minutes)
- Adaptive mode: volume threshold = 1.0 fL
- Track: ATP+ADP+Pi total at each timepoint

**Expected:** Total = 15.0 mM (conserved)  
**Predicted:** Total decreases ~10% over 3000s

### Test Variations

1. **Baseline:** All normal arcs
2. **Test 1:** ATP_synthesis output as signal_flow arc
3. **Test 2:** ATPase input as signal_flow arc
4. **Test 3:** Both as signal_flow arcs
5. **Test 4:** Pure stochastic mode (no adaptive)
6. **Test 5:** Pure continuous mode (no adaptive)

## Next Steps

1. ✅ **Create minimal test model**
2. Run 3000s simulations for all variations
3. Compare energy conservation
4. Identify which arc type/mode combination causes loss
5. Implement fix (likely in adaptive mode switch or production phase)
6. Validate fix with full drug discovery model

## Code Locations for Potential Fix

1. **AdaptiveHybridBehavior._handle_mode_change()** - Add conservation check
2. **ContinuousBehavior.integrate_step()** - Add post-step mass balance verification
3. **StochasticBehavior.fire()** - Add conservation assertion
4. **Place.set_tokens()** - Track cumulative delta for debugging
