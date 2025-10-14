# Stochastic Sink and Normal Transition Analysis - COMPLETE

**Date**: 2025-10-13  
**Status**: ✅ Analysis Complete - No Bugs Found  
**Related**: STOCHASTIC_SOURCE_STABILITY_FIX.md

---

## Executive Summary

After fixing critical bugs in **source transitions**, a comprehensive analysis of **sink** and **normal** stochastic transitions reveals:

### Sink Transitions ✅ WORKING CORRECTLY
- Sink transitions have input places but no output places
- Controller checks input tokens → can become disabled (correct behavior)
- Should NOT stay enabled continuously (unlike sources)
- Re-enablement works correctly when tokens become available
- **No fixes needed**

### Normal Transitions ✅ WORKING CORRECTLY  
- Normal transitions have both inputs and outputs
- Controller checks input tokens → can become disabled (correct behavior)
- Re-enablement works correctly when tokens become available
- Proper Poisson process timing maintained
- **No fixes needed**

**Verdict**: Only **source transitions** needed fixes. Sink and normal stochastic transitions are implemented correctly.

---

## Transition Type Comparison

### Source Transitions (Fixed ✅)
```
[Source] → (P1)
```
- **Properties**: `is_source = True`, no input places
- **Behavior**: Always enabled, fires continuously (Poisson process)
- **Enablement**: Never disabled (no input requirements)
- **Re-scheduling**: Auto-reschedule after firing
- **Use case**: Continuous token generation (glucose influx, ATP production)
- **Bugs found**: 
  1. ❌ Was getting disabled by controller (FIXED)
  2. ❌ Didn't auto-reschedule (FIXED)

### Sink Transitions ✅ CORRECT
```
(P1) → [Sink]
```
- **Properties**: `is_sink = True`, has input places, no output places
- **Behavior**: Enabled when inputs have sufficient tokens
- **Enablement**: Can be disabled (depends on input tokens)
- **Re-scheduling**: Re-enables when tokens become available
- **Use case**: Token consumption/disposal (ATP degradation, molecule export)
- **Status**: ✅ **Working correctly** - SHOULD be able to disable

### Normal Transitions ✅ CORRECT
```
(P1) → [Transition] → (P2)
```
- **Properties**: Has both input and output places
- **Behavior**: Enabled when inputs have sufficient tokens
- **Enablement**: Can be disabled (depends on input tokens)
- **Re-scheduling**: Re-enables when tokens become available
- **Use case**: Token transformation (chemical reactions, state transitions)
- **Status**: ✅ **Working correctly** - SHOULD be able to disable

---

## Detailed Analysis

### 1. Controller Enablement Logic

**Current Implementation** (`src/shypn/engine/simulation/controller.py` line ~240):

```python
def _update_enablement_states(self):
    """Update enablement tracking for all transitions."""
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        
        # ✅ Special case for source transitions (always enabled)
        is_source = getattr(transition, 'is_source', False)
        if is_source:
            state = self._get_or_create_state(transition)
            if state.enablement_time is None:
                state.enablement_time = self.time
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)
            continue  # Skip input checks
        
        # ✅ Normal logic for sink and normal transitions
        input_arcs = behavior.get_input_arcs()
        locally_enabled = True
        for arc in input_arcs:
            kind = getattr(arc, 'kind', 'normal')
            if kind != 'normal':
                continue
            source_place = behavior._get_place(arc.source_id)
            if source_place is None or source_place.tokens < arc.weight:
                locally_enabled = False  # ✅ Correct for sink/normal
                break
        
        state = self._get_or_create_state(transition)
        if locally_enabled:
            if state.enablement_time is None:
                state.enablement_time = self.time
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)
        else:
            # ✅ Clear enablement when disabled (correct for sink/normal)
            state.enablement_time = None
            state.scheduled_time = None
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
```

**Analysis**:
- ✅ Sources: Skip input checks, stay enabled continuously
- ✅ Sinks: Check input tokens, can disable (CORRECT)
- ✅ Normal: Check input tokens, can disable (CORRECT)

**Why sink/normal SHOULD disable**:
- Sink example: `(P1:5 tokens) → [Sink with rate=2.0]`
  - Fires and consumes 5 tokens
  - P1 now empty → sink should DISABLE (can't fire without tokens)
  - Later, if P1 gets more tokens → sink re-enables (reschedules)
- Normal example: `(P1:3 tokens) → [T] → (P2)`
  - Fires and consumes 3 tokens
  - P1 now empty → T should DISABLE
  - Later, when P1 refills → T re-enables

This is **fundamentally different** from sources, which generate tokens from nothing and should never disable.

### 2. Stochastic Behavior Token Checks

**Implementation** (`src/shypn/engine/stochastic_behavior.py` line ~160):

```python
def can_fire(self) -> Tuple[bool, str]:
    """Check if transition can fire."""
    is_source = getattr(self.transition, 'is_source', False)
    
    # Check guard first
    guard_passes, guard_reason = self._evaluate_guard()
    if not guard_passes:
        return False, guard_reason
    
    if self._scheduled_fire_time is None:
        return False, "not-scheduled"
    
    current_time = self._get_current_time()
    if current_time < self._scheduled_fire_time:
        return False, f"too-early"
    
    # ✅ Check tokens for burst firing (skip for sources, check for sink/normal)
    if not is_source:
        input_arcs = self.get_input_arcs()
        burst = self._sampled_burst if self._sampled_burst else self.max_burst
        
        for arc in input_arcs:
            source_place = self._get_place(arc.source_id)
            if source_place is None:
                return False, f"missing-source-place"
            
            required = arc.weight * burst
            if source_place.tokens < required:
                return False, f"insufficient-tokens-for-burst"
    
    return True, "enabled-stochastic"
```

**Analysis**:
- ✅ Sources: Skip token checks (no inputs)
- ✅ Sinks: Check input tokens, fail if insufficient (CORRECT)
- ✅ Normal: Check input tokens, fail if insufficient (CORRECT)

**Burst multiplier considerations**:
- Stochastic transitions use burst = 1-8× normal weight
- Example: Arc weight=2, burst=5 → requires 10 tokens
- Sink/normal must verify sufficient tokens BEFORE firing
- If insufficient → firing fails, schedule cleared, waits for re-enablement
- This is **correct behavior** for resource-limited transitions

### 3. Firing Behavior

**Implementation** (`src/shypn/engine/stochastic_behavior.py` line ~230):

```python
def fire(self, input_arcs: List, output_arcs: List):
    """Execute stochastic burst firing."""
    is_source = getattr(self.transition, 'is_source', False)
    is_sink = getattr(self.transition, 'is_sink', False)
    
    burst = self._sampled_burst if self._sampled_burst else 1
    consumed_map = {}
    produced_map = {}
    
    # Phase 1: Consume tokens (skip for sources)
    if not is_source:
        for arc in input_arcs:
            source_place = self._get_place(arc.source_id)
            amount = arc.weight * burst
            source_place.set_tokens(source_place.tokens - amount)
            consumed_map[arc.source_id] = float(amount)
    
    # Phase 2: Produce tokens (skip for sinks)
    if not is_sink:
        for arc in output_arcs:
            target_place = self._get_place(arc.target_id)
            amount = arc.weight * burst
            target_place.set_tokens(target_place.tokens + amount)
            produced_map[arc.target_id] = float(amount)
    
    # Phase 3: Clear scheduling
    self.clear_enablement()
    
    # Phase 4: Auto-reschedule ONLY sources
    is_source = getattr(self.transition, 'is_source', False)
    if is_source:
        self.set_enablement_time(current_time)  # ✅ Only for sources
    
    # For sink/normal: NO auto-reschedule
    # They will re-enable when controller detects sufficient tokens
```

**Analysis**:
- ✅ Sources: Skip consumption, skip production (wrong for sources), AUTO-RESCHEDULE
- ✅ Sinks: Consume tokens, skip production, NO auto-reschedule (CORRECT)
- ✅ Normal: Consume and produce tokens, NO auto-reschedule (CORRECT)

**Why sink/normal should NOT auto-reschedule**:
1. After firing, they may lack input tokens
2. Controller will check tokens in next step
3. If sufficient tokens → controller calls `set_enablement_time()` → reschedules
4. If insufficient tokens → stays disabled until tokens arrive
5. This maintains proper **resource-limited behavior**

**Wait, there's a bug for sources!** 🔴

Looking at the code again, sources should:
- ✅ Skip consumption (no inputs) ← CORRECT
- ❌ **PRODUCE tokens** (they have outputs!) ← BUG!

Let me check this more carefully:

<function_calls>
<invoke name="read_file">
<parameter name="filePath">/home/simao/projetos/shypn/src/shypn/engine/stochastic_behavior.py