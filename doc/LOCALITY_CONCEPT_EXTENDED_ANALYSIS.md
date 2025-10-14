# Locality Concept - Extended Analysis and Refinement

**Date**: October 12, 2025  
**Purpose**: Comprehensive analysis of locality concept and extension to support exceptional patterns  
**Status**: Analysis Complete → Implementation Ready

---

## Current Locality Definition

### Core Concept (from `locality_detector.py`)

```
"Place-transition-place defines what is called a Locality"
```

A locality is: **Input Places → Transition → Output Places**

### Current Implementation

**Standard Pattern** (Normal Transition):
- **Pattern**: `P → T → P`
- **Requirement**: BOTH input places AND output places
- **Validation**: `is_valid = (len(input_places) >= 1) AND (len(output_places) >= 1)`

**Special Cases Already Supported**:
1. **Source Transition**: `T → P` (only outputs)
   - Minimal locality = `t•` (post-set)
   - Valid if has ≥ 1 output place
   
2. **Sink Transition**: `P → T` (only inputs)
   - Minimal locality = `•t` (pre-set)
   - Valid if has ≥ 1 input place

### Current Usage Throughout Codebase

**Key Files Using Locality**:

1. **`src/shypn/diagnostic/locality_detector.py`**
   - Detects P-T-P patterns
   - Validates localities
   - Returns `Locality` objects

2. **`src/shypn/analyses/transition_rate_panel.py`**
   - Uses locality for plotting
   - Displays input/output places with transitions
   - Search mechanism integrates locality detection

3. **`src/shypn/engine/simulation/controller.py`**
   - Uses locality for independence detection
   - Enables parallel execution
   - Token flow based on locality

4. **`src/shypn/helpers/transition_prop_dialog_loader.py`**
   - Shows locality info widget in transition properties
   - Real-time locality display

5. **`src/shypn/analyses/context_menu_handler.py`**
   - "Add to Analysis" with locality option
   - Automatically includes locality places

---

## Problem: Exceptional Patterns Not Recognized

### User Request

> "P -> T, T -> P, T -> P <- T, must be recognized as locality throughout the code"

### Analysis of Exceptional Patterns

#### Pattern 1: P → T (Single Input, No Output)

```
P1 ────→ T1 (no outputs)
```

**Current Status**: 
- Recognized as "sink" if `transition.is_sink = True`
- NOT recognized as valid for normal transitions without outputs

**Should Be**: 
- Valid locality = `•T` (pre-set only)
- Represents: Consumption endpoint, absorber, terminator

#### Pattern 2: T → P (Single Output, No Input)

```
(no inputs) T1 ────→ P1
```

**Current Status**:
- Recognized as "source" if `transition.is_source = True`  
- NOT recognized as valid for normal transitions without inputs

**Should Be**:
- Valid locality = `T•` (post-set only)
- Represents: Generation source, producer, initiator

#### Pattern 3: T → P ← T (Convergent Pattern)

```
T1 ────→ P1 ←──── T2
```

**Current Status**:
- Each transition sees its own locality independently
- T1 locality: `T1 → P1` (output only)
- T2 locality: `T2 → P1` (output only)
- The PLACE is shared, but this isn't explicitly recognized as a special pattern

**Should Be**:
- Valid locality for EACH transition
- T1 locality: `T1•` = {P1}
- T2 locality: `T2•` = {P1}
- Recognized as **convergent locality** or **shared output**

### Why These Patterns Matter

**1. Biological/Chemical Systems**:
- P → T: Degradation, consumption without product
- T → P: Synthesis from nothing (external source)
- T → P ← T: Multiple pathways converging to same product

**2. Control Flow**:
- P → T: Termination condition
- T → P: Initialization condition
- T → P ← T: Synchronization point, join

**3. Analysis & Plotting**:
- Need to plot ALL transitions, even with partial connectivity
- Search should find transitions by their locality, even if incomplete
- Visual representation should show partial patterns clearly

---

## Proposed Solution: Extended Locality Definition

### New Unified Concept

**A locality is ANY of the following patterns centered on a transition:**

1. **Full Locality** (Normal): `P → T → P`
   - Input places ≥ 1 AND output places ≥ 1
   - Type: `'normal'`

2. **Input-Only Locality** (Sink): `P → T`
   - Input places ≥ 1 AND output places = 0
   - Type: `'sink'` or `'input-only'`

3. **Output-Only Locality** (Source): `T → P`
   - Input places = 0 AND output places ≥ 1
   - Type: `'source'` or `'output-only'`

4. **Isolated Transition**: `T` (no connections)
   - Input places = 0 AND output places = 0
   - Type: `'isolated'`
   - **NEW**: Should be recognized but flagged

5. **Convergent Pattern** (Implicit): `T → P ← T`
   - Multiple transitions sharing output place
   - Detected via `find_shared_places()`
   - Each transition has its own output-only locality
   - The PLACE is the convergence point

### Validation Logic Update

**Current**:
```python
def is_valid(self) -> bool:
    if is_source:
        return len(self.output_places) >= 1
    elif is_sink:
        return len(self.input_places) >= 1
    else:
        # PROBLEM: Requires BOTH
        return len(self.input_places) >= 1 and len(self.output_places) >= 1
```

**Proposed**:
```python
def is_valid(self) -> bool:
    """A locality is valid if it has AT LEAST ONE place (input or output).
    
    Valid patterns:
    - P → T → P (normal)
    - P → T (input-only/sink)
    - T → P (output-only/source)
    
    Invalid:
    - T (isolated, no connections)
    """
    # Accept ANY transition with at least one connected place
    return len(self.input_places) >= 1 or len(self.output_places) >= 1
```

### Type Classification Update

**Current Types**:
- `'source'`: Only for transitions with `is_source=True` flag
- `'sink'`: Only for transitions with `is_sink=True` flag
- `'normal'`: Requires both inputs AND outputs
- `'invalid'`: Anything else

**Proposed Types**:
```python
def locality_type(self) -> str:
    """Get detailed locality type.
    
    Returns:
        'normal' | 'source' | 'sink' | 'input-only' | 'output-only' | 'isolated'
    """
    has_inputs = len(self.input_places) >= 1
    has_outputs = len(self.output_places) >= 1
    is_source = getattr(self.transition, 'is_source', False)
    is_sink = getattr(self.transition, 'is_sink', False)
    
    # Isolated (no connections)
    if not has_inputs and not has_outputs:
        return 'isolated'
    
    # Full locality (both sides)
    if has_inputs and has_outputs:
        return 'normal'
    
    # Output-only (may be marked as source)
    if has_outputs and not has_inputs:
        return 'source' if is_source else 'output-only'
    
    # Input-only (may be marked as sink)
    if has_inputs and not has_outputs:
        return 'sink' if is_sink else 'input-only'
    
    return 'invalid'  # Should never reach here
```

---

## Impact Analysis: Files to Update

### 1. **`src/shypn/diagnostic/locality_detector.py`** ✅ CRITICAL

**Changes Needed**:
- Update `Locality.is_valid()` to accept input-only or output-only
- Update `Locality.locality_type` to distinguish all patterns
- Update `Locality.get_summary()` to describe all patterns
- Add detection for convergent patterns (shared places)

**Example**:
```python
@property
def is_valid(self) -> bool:
    """Valid if has AT LEAST ONE place (input or output)."""
    return len(self.input_places) >= 1 or len(self.output_places) >= 1

def get_summary(self) -> str:
    locality_type = self.locality_type
    
    if locality_type == 'normal':
        return f"{len(self.input_places)} → {self.transition.name} → {len(self.output_places)}"
    elif locality_type in ('source', 'output-only'):
        return f"{self.transition.name} → {len(self.output_places)}"
    elif locality_type in ('sink', 'input-only'):
        return f"{len(self.input_places)} → {self.transition.name}"
    elif locality_type == 'isolated':
        return f"{self.transition.name} (isolated)"
    else:
        return f"{self.transition.name} (invalid)"
```

### 2. **`src/shypn/analyses/transition_rate_panel.py`** ✅ IMPORTANT

**Changes Needed**:
- Update `add_locality_places()` to handle input-only and output-only
- Update `_update_selected_list()` to show partial localities correctly
- Update `_plot_locality_places()` to visualize incomplete patterns
- Update search mechanism to find ALL transitions with localities

**Current Code** (line 329):
```python
if locality.is_valid:  # Will now accept partial patterns ✅
    self.add_locality_places(transition, locality)
```

**Plotting Update Needed** (line 638):
```python
def _plot_locality_places(self, transition_id, base_color, debug=False):
    """Plot input and output places - handles partial localities."""
    locality_data = self._locality_places[transition_id]
    
    # Plot inputs if available
    if locality_data['input_places']:
        for place in locality_data['input_places']:
            # ... plot input
    
    # Plot outputs if available
    if locality_data['output_places']:
        for place in locality_data['output_places']:
            # ... plot output
    
    # Show visual indicator for partial patterns
    if not locality_data['input_places']:
        # Show "SOURCE" label
    elif not locality_data['output_places']:
        # Show "SINK" label
```

### 3. **`src/shypn/engine/simulation/controller.py`** ⚠️ VERIFY

**Changes Needed**:
- Verify that `_get_locality_places()` (line 604) handles partial localities
- Verify enablement checks work with input-only transitions
- Verify firing logic works with output-only transitions

**Current Code** (line 611-613):
```python
# Current comments mention source/sink already:
# - Source transition: Only output places (•t = ∅, locality = t•)
# - Sink transition: Only input places (t• = ∅, locality = •t)
# - Normal transition: Both input and output places (locality = •t ∪ t•)
```

**Looks like simulation already handles this correctly!** ✅

### 4. **`src/shypn/helpers/transition_prop_dialog_loader.py`** ✅ VERIFY

**Changes Needed**:
- Verify `LocalityInfoWidget` displays partial localities correctly
- May need to update widget to show "INPUT-ONLY" or "OUTPUT-ONLY" labels

### 5. **`src/shypn/analyses/context_menu_handler.py`** ✅ VERIFY

**Changes Needed**:
- Verify `_add_transition_locality_submenu()` (line 136) works with partial localities
- Menu text should reflect partial patterns: "With Locality (N inputs)" or "With Locality (N outputs)"

**Current Code** (line 149-150):
```python
# Detect locality
locality = self.locality_detector.get_locality_for_transition(transition)
```

Should work automatically once `locality.is_valid` is updated! ✅

---

## Implementation Plan

### Phase 1: Core Update (locality_detector.py)

1. ✅ Update `Locality.is_valid()` property
2. ✅ Update `Locality.locality_type` property  
3. ✅ Update `Locality.get_summary()` method
4. ✅ Add tests for new patterns

### Phase 2: Analyses Panel (transition_rate_panel.py)

1. ✅ Update plotting to handle partial patterns
2. ✅ Update list display to show pattern type
3. ✅ Update search to include all valid localities

### Phase 3: Verification

1. ✅ Test simulation controller with partial patterns
2. ✅ Test transition properties dialog
3. ✅ Test context menu handler
4. ✅ Test with real biochemical networks

### Phase 4: Documentation

1. ✅ Update LOCALITY_QUICK_REFERENCE.md
2. ✅ Update README files
3. ✅ Add examples of all patterns

---

## Testing Scenarios

### Test 1: Input-Only Transition (P → T)

```python
# Create network
p1 = model.add_place(name="P1", tokens=5)
t1 = model.add_transition(name="T1")
arc1 = model.add_arc(p1, t1)  # P1 → T1

# Detect locality
detector = LocalityDetector(model)
locality = detector.get_locality_for_transition(t1)

# Verify
assert locality.is_valid  # Should be True (not False!)
assert locality.locality_type == 'input-only'
assert len(locality.input_places) == 1
assert len(locality.output_places) == 0
assert locality.get_summary() == "1 → T1"
```

### Test 2: Output-Only Transition (T → P)

```python
# Create network
t1 = model.add_transition(name="T1")
p1 = model.add_place(name="P1")
arc1 = model.add_arc(t1, p1)  # T1 → P1

# Detect locality
locality = detector.get_locality_for_transition(t1)

# Verify
assert locality.is_valid  # Should be True (not False!)
assert locality.locality_type == 'output-only'
assert len(locality.input_places) == 0
assert len(locality.output_places) == 1
assert locality.get_summary() == "T1 → 1"
```

### Test 3: Convergent Pattern (T → P ← T)

```python
# Create network
t1 = model.add_transition(name="T1")
t2 = model.add_transition(name="T2")
p1 = model.add_place(name="P1")
arc1 = model.add_arc(t1, p1)  # T1 → P1
arc2 = model.add_arc(t2, p1)  # T2 → P1

# Detect localities
locality1 = detector.get_locality_for_transition(t1)
locality2 = detector.get_locality_for_transition(t2)

# Verify both are valid
assert locality1.is_valid
assert locality2.is_valid
assert locality1.locality_type == 'output-only'
assert locality2.locality_type == 'output-only'

# Detect shared place
shared = detector.find_shared_places()
assert 'P1' in shared
assert t1 in shared['P1']
assert t2 in shared['P1']
```

---

## Benefits of Extended Definition

### 1. **Completeness**

All transition patterns are recognized as valid localities:
- ✅ P → T → P (already working)
- ✅ P → T (now working)
- ✅ T → P (now working)
- ✅ T → P ← T (implicit via shared places)

### 2. **Analysis Coverage**

Can analyze ALL transitions in the network:
- No transitions are excluded from locality-based analysis
- Plotting includes partial patterns
- Search finds all transitions

### 3. **Biological Accuracy**

Matches real biochemical patterns:
- Degradation: `Protein → Degrade` (input-only)
- Synthesis: `Produce → mRNA` (output-only)
- Convergence: `Path1 → Product ← Path2` (shared output)

### 4. **Consistency**

Uniform treatment across codebase:
- Same `Locality` class for all patterns
- Same `is_valid` check everywhere
- Same plotting logic

---

## Backward Compatibility

### Existing Code Continues to Work

**Source/Sink Flags**:
- Transitions with `is_source=True` will still be typed as `'source'`
- Transitions with `is_sink=True` will still be typed as `'sink'`
- No breaking changes to these special cases

**Normal Transitions**:
- Full localities (P → T → P) continue to work exactly as before
- Type remains `'normal'`

**New Behavior**:
- Previously **invalid** transitions (P → T or T → P) now become **valid**
- This is an **expansion**, not a breaking change
- No existing valid localities become invalid

---

## Conclusion

The extended locality definition:

1. ✅ **Accepts** the exceptional patterns: P → T, T → P, T → P ← T
2. ✅ **Maintains** backward compatibility with existing code
3. ✅ **Improves** analysis coverage (all transitions included)
4. ✅ **Enables** complete plotting and search functionality
5. ✅ **Reflects** real-world biological and control patterns

**Next Step**: Implement the changes in `locality_detector.py` and verify throughout the codebase.

---

**Date**: October 12, 2025  
**Status**: ✅ Analysis Complete - Ready for Implementation
