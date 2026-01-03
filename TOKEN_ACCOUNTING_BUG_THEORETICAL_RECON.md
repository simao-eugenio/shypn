# Token Accounting Bug - Theoretical Reconnaissance

**Date:** January 3, 2026  
**Status:** 🔍 Investigation Phase  
**Severity:** CRITICAL - 50% systematic token loss  
**Branch:** Thermodynamic-Constraints-Gibbs-Free-Energy

---

## Executive Summary

**Bug Confirmed:** Test model with 2 stochastic transitions shows **exactly 50% token loss** (352 actual vs 704 expected tokens).

**Critical Finding:** `Actual change = (Production - Consumption) / 2`

This systematic 50% error suggests a fundamental architectural issue where the core engine is applying **half the expected net token change**, pointing to either:
1. Double processing with averaging
2. Incorrect time step integration  
3. Hybrid model interference (continuous/stochastic interaction)

---

## Theoretical Foundations Review

### 1. τ-Leaping Theory (Gillespie 2001, Cao et al. 2006)

**Core Algorithm:**
```
FOR each time leap τ:
  1. Calculate propensities aⱼ for each transition j
  2. Sample firings: Kⱼ ~ Poisson(aⱼ·τ)
  3. Update tokens: Δxᵢ = Σⱼ νᵢⱼ·Kⱼ
     where νᵢⱼ = stoichiometry (arc weight)
```

**Expected Behavior:**
- Tokens consumed = Σ(firings × input_arc.weight)
- Tokens produced = Σ(firings × output_arc.weight)
- Net change = produced - consumed

**Observed Behavior:**
- Net change = (produced - consumed) / 2 ❌

**Implication:** Either step 2 or 3 is being applied incorrectly.

---

### 2. Weak Independence Theory (Parallel Stochastic)

**Principle:**
```
Independent transitions (non-overlapping localities) can fire concurrently:
  t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅

Implementation: Parallel Poisson sampling
  K₁ ~ Poisson(a₁·τ)  } Can be sampled
  K₂ ~ Poisson(a₂·τ)  } simultaneously
```

**Location:** `src/shypn/engine/simulation/tau_leaping/parallel_scheduler.py`

**Status:** Phase 3 complete, uses ThreadPoolExecutor

**Potential Issue:**
- If tokens are updated in **separate threads** for parallel transitions
- AND results are **averaged or merged incorrectly**
- Could explain 50% loss in token accounting

**Test Case Relevance:**
- Test model has T1→P1 and T2→P1 (both affect same place)
- These are NOT independent (competitive coupling)
- Should use sequential execution, not parallel
- **Question:** Is parallel scheduler being invoked incorrectly?

---

### 3. Signal Hierarchy Theory (Simão 2025)

**Principle:**
```
Information flow (signal places) decoupled from mass flow (regular places):
  - Signal places (Ψ): Information sensing, no stoichiometry
  - Regular places (P): Material/token flow with arc weights
  - Signal flow arcs: Don't consume tokens
```

**Implementation:** `src/shypn/netobjs/signal_flow_arc.py`

**Relevance to Bug:**
- Test model uses regular places and normal arcs
- Signal hierarchy should NOT affect this test
- **However:** Signal flow arcs checked with `hasattr(arc, 'consumes_tokens')`
- If regular arcs incorrectly flagged, could skip consumption

**Code Location:** `tau_leaping_engine.py:677`
```python
if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
    continue  # Skip test arcs
```

**Question:** Are normal arcs being misclassified?

---

### 4. Continuous/Stochastic Parallelism (Hybrid Models)

**Architecture:**
```
Simulation step structure (controller.py:1050-1230):
  Phase 1: Immediate transitions (deterministic)
  Phase 2: Window-crossing transitions (timed)
  Phase 3: Continuous transitions (integrate_step with dt)
  Phase 4: Advance time (self.time += time_step)
  Phase 5: Stochastic transitions (τ-leaping)
```

**Critical Discovery:**
- Line 1111: τ-leaping engine filters `transition_type == 'stochastic'`
- Continuous transitions processed separately via `behavior.integrate_step(dt)`
- **Both phases update same places**

**Potential Conflict:**
```
IF continuous transition T_cont produces tokens to place P:
  1. Phase 3: P.tokens += weight × rate × dt
  2. Phase 5: τ-leaping also updates P.tokens
  3. BUT if τ-leaping sees "already updated" state...
     Could apply correction factor (divide by 2)?
```

**Test Case:**
- User initially created both T1 and T2 as continuous (rate=1.0)
- This would fire every timestep (1000 Hz at dt=0.001)
- User changed to stochastic but maybe simulation ran both?

**Hypothesis:** **Hybrid execution path bug**
- Controller runs continuous phase (produces half the tokens)
- Controller runs stochastic phase (produces other half)
- Net: Correct total but wrong attribution

---

### 5. Time Step Integration

**Continuous Transitions:**
```python
# continuous_behavior.py
tokens_to_flow = rate × dt × arc.weight
place.tokens += tokens_to_flow
```

**Stochastic Transitions:**
```python
# tau_leaping_engine.py
firings ~ Poisson(rate × τ)
tokens_change = firings × arc.weight
place.tokens += tokens_change
```

**Potential Issue:**
- If τ-leaping uses `τ = dt/2` instead of `dt`
- Would cause exactly 50% token loss
- Need to check `LeapSelector.select_tau()`

**Code Check Required:**
- `src/shypn/engine/simulation/tau_leaping/leap_selector.py`
- Verify no hardcoded `/2` in tau calculation

---

## Code Paths to Investigate

### Priority 1: Token Update Logic

**File:** `tau_leaping_engine.py`
**Method:** `_fire_transition_multiple()` (lines 640-695)

**Current Code:**
```python
# Phase 1: Consume
for arc in input_arcs:
    amount = arc.weight * num_firings
    source_place.set_tokens(source_place.tokens - amount)
    consumed_map[source_place.id] = float(amount)

# Phase 2: Produce  
for arc in output_arcs:
    amount = arc.weight * num_firings
    target_place.set_tokens(target_place.tokens + amount)
    produced_map[target_place.id] = float(amount)
```

**Verification Needed:**
- ✅ Code looks correct (weight × firings)
- ❓ Is this method called twice per transition?
- ❓ Is `set_tokens()` modifying values unexpectedly?

---

### Priority 2: Hybrid Model Detection

**File:** `controller.py`
**Lines:** 1203-1213

**Code:**
```python
is_pure_stochastic = all(
    t.transition_type == 'stochastic' 
    for t in self.model.transitions 
    if hasattr(t, 'transition_type')
)

if is_pure_stochastic:
    self._tau_leaping_engine.execute_step(self)
else:
    # Hybrid model: clamp tau to dt
    ...
```

**Question:** 
- Is test model being detected as hybrid?
- Does hybrid path apply different token update rules?

---

### Priority 3: Parallel Scheduler Invocation

**File:** `tau_leaping_engine.py`
**Method:** `_sample_firings()` (lines 195-380)

**Code:**
```python
if self.use_parallel and len(transitions) >= 4:
    if self._parallel_scheduler:
        return self._parallel_scheduler.sample_parallel(...)
```

**Test Model:**
- Only 2 transitions (< 4 threshold)
- Should use sequential path
- **Verify:** Parallel path not being triggered

---

### Priority 4: Source Transition Handling

**File:** `tau_leaping_engine.py`  
**Method:** `_fire_transition_multiple()` (line 667)

**Code:**
```python
is_source = getattr(transition, 'is_source', False)

if not is_source:
    # Consume tokens
    ...
```

**Test Model:**
- T2 is marked `is_source=True`
- Should skip consumption phase
- **Verify:** Production still happening correctly

---

### Priority 5: Continuous Transition Interference

**File:** `controller.py`
**Lines:** 1064-1110

**Code:**
```python
continuous_transitions = [t for t in self.model.transitions 
                         if t.transition_type == 'continuous']

for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
    success, details = behavior.integrate_step(dt=time_step, ...)
    if success:
        continuous_active += 1
        transition.firing_count += 1
```

**Question:**
- Even if transitions are stochastic, is there a code path where continuous behavior is invoked?
- Check if `behavior.integrate_step()` is being called for stochastic transitions

---

## Empirical Evidence

### Test Model Configuration
```
Place: P1 (ATP_pool, initial=1000)
Transition T1: type=stochastic, rate=5.0, is_source=False
Transition T2: type=stochastic, rate=10.0, is_source=True
Arc A1: P1 → T1 (weight=3.0, normal)
Arc A2: T2 → P1 (weight=5.0, normal)
```

### Simulation Results (10 seconds)
```
T1 firings: 82 (actual: 8.2 Hz, expected: 5.0 Hz)
T2 firings: 190 (actual: 19.0 Hz, expected: 10.0 Hz)

Consumed: 82 × 3 = 246 tokens
Produced: 190 × 5 = 950 tokens
Expected net: +704 tokens
Actual net: +352 tokens

Discrepancy: 352 tokens (EXACTLY 50%)
```

### Mathematical Pattern
```
352 = 704 / 2
352 = (950 - 246) / 2
352 = net_change / 2

This is NOT a rounding error - it's systematic division by 2
```

---

## Hypotheses Ranked by Likelihood

### 1. Hybrid Model Path Bug (HIGH PROBABILITY)
**Hypothesis:** Controller executes both continuous AND stochastic phases, tokens updated twice with different logic

**Evidence:**
- Firing rates ~2× expected (8.2 vs 5, 19 vs 10)
- Exactly 50% token loss
- Hybrid detection code exists

**Test:**
- Add debug logging to `controller.py` phases
- Check if both continuous and stochastic paths execute

---

### 2. Time Step Halving (MEDIUM PROBABILITY)
**Hypothesis:** τ-leaping uses `τ = dt/2` instead of `dt`

**Evidence:**
- Would explain 50% loss
- Hybrid model clamps tau: `min(time_step, original_max_tau)`

**Test:**
- Log tau values in `_sample_firings()`
- Compare to expected time_step

---

### 3. Double Execution with Averaging (LOW PROBABILITY)
**Hypothesis:** Transitions fire twice, results averaged

**Evidence:**
- Firing counts ~2× expected
- But CSV shows single firing count per transition

**Counter-Evidence:**
- `firing_count` incremented once per `_fire_transition_multiple()`

---

### 4. Arc Weight Halving (VERY LOW PROBABILITY)
**Hypothesis:** Arc weights divided by 2 somewhere

**Evidence:**
- Would explain 50% loss

**Counter-Evidence:**
- Code shows `arc.weight * num_firings` (no division)
- Model file shows weight=3.0 and 5.0 (correct values)

---

## Diagnostic Action Plan

### Step 1: Add Comprehensive Logging
**File:** `tau_leaping_engine.py`
**Location:** `_fire_transition_multiple()` entry

```python
self.logger.warning(
    f"[TOKEN_DEBUG] Firing {transition.name} × {num_firings}\n"
    f"  Before: P1={place.tokens}\n"
    f"  Consume: {[(a.source.name, a.weight*num_firings) for a in input_arcs]}\n"
    f"  Produce: {[(a.target.name, a.weight*num_firings) for a in output_arcs]}\n"
    f"  Expected after: {place.tokens - sum_consumed + sum_produced}"
)
```

### Step 2: Check Hybrid Detection
**File:** `controller.py`
**Location:** Line 1203

```python
is_pure_stochastic = all(...)
self.logger.warning(f"[HYBRID_DEBUG] Pure stochastic: {is_pure_stochastic}")
self.logger.warning(f"[HYBRID_DEBUG] Transition types: {[t.transition_type for t in self.model.transitions]}")
```

### Step 3: Verify Single Execution Path
**File:** `controller.py`
**Location:** Phase 3 (continuous) and Phase 5 (stochastic)

```python
# Phase 3
for transition in continuous_transitions:
    self.logger.warning(f"[PHASE3] Continuous: {transition.name}")

# Phase 5  
if enabled_stochastic:
    self.logger.warning(f"[PHASE5] Stochastic: {[t.name for t in enabled_stochastic]}")
```

### Step 4: Tau Value Inspection
**File:** `tau_leaping_engine.py`
**Location:** `_sample_firings()` call

```python
self.logger.warning(f"[TAU_DEBUG] tau={tau}, time_step={time_step}, tau/time_step={tau/time_step if time_step else 'N/A'}")
```

---

## Next Steps

1. **Add diagnostic logging** to key code paths
2. **Run test simulation** with logging enabled
3. **Analyze logs** to identify execution flow
4. **Propose fix** based on findings
5. **Validate fix** with test model
6. **Apply fix** to bacillus model
7. **Update documentation** with architectural corrections

---

## References

- Gillespie, D. T. (2001). Approximate accelerated stochastic simulation. J. Chem. Phys., 115(4), 1716-1733.
- Cao, Y., Gillespie, D. T., & Petzold, L. R. (2006). Efficient step size selection for the tau-leaping simulation method.
- `doc/PARALLEL_EXECUTION_OVERVIEW.md` - Weak independence theory
- `doc/signal_hierarchy/SIGNAL_HIERARCHY_THEORY.md` - Signal hierarchy formalism
- `src/shypn/engine/simulation/tau_leaping/__init__.py` - τ-leaping architecture
- `src/shypn/engine/simulation/controller.py` - Hybrid model execution phases

---

**Status:** Ready for diagnostic logging implementation and root cause analysis.
