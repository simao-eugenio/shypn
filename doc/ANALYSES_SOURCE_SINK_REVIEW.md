# Analysis Panel Source/Sink Recognition Review

**Date:** 2025-10-11  
**Purpose:** Review and improve source/sink recognition in analysis panels

---

## Executive Summary

**Current Status:**
- ✅ Search mechanism works (finds transitions/places by name/label)
- ✅ "Add to Analysis" context menu works
- ✅ Locality detection works for normal transitions
- ❌ **Source/Sink NOT recognized** - treated as invalid localities
- ❌ Matplotlib adjustments don't account for source/sink behavior

**Required Changes:**
1. Update `LocalityDetector` to recognize source/sink as valid minimal localities
2. Update search results to indicate source/sink status
3. Update matplotlib Y-axis ranges for source (unbounded) and sink (bounded) behavior
4. Update UI labels to show source/sink indicators

---

## 1. Current Flow Analysis

### 1.1 "Add to Analysis" Flow

```
USER ACTION
    │
    ├─ RIGHT-CLICK on canvas object
    │   │
    │   └─> ContextMenuHandler.add_analysis_menu_items(menu, obj)
    │       │
    │       ├─ For PLACE: Simple menu item
    │       │   └─> PlaceRatePanel.add_object(place)
    │       │
    │       └─ For TRANSITION: Locality detection
    │           │
    │           ├─> LocalityDetector.get_locality_for_transition(t)
    │           │   │
    │           │   └─> Locality(input_places, output_places)
    │           │       │
    │           │       ├─ is_valid = (len(inputs) >= 1 AND len(outputs) >= 1)
    │           │       │   ❌ PROBLEM: Source/sink fail this check!
    │           │       │
    │           │       └─ If valid: Add transition + locality places
    │           │           If invalid: Add transition only
    │           │
    │           └─> TransitionRatePanel.add_object(transition)
    │               └─> TransitionRatePanel.add_locality_places(t, locality)
    │
    └─ SEARCH in panel
        │
        └─> SearchHandler.search_transitions(model, query)
            │
            └─> Returns: List[Transition] matching query
                │
                └─> For each result:
                    │
                    ├─> LocalityDetector.get_locality_for_transition(t)
                    │   ❌ PROBLEM: Same issue - source/sink not recognized
                    │
                    └─> TransitionRatePanel.add_object(transition)
                        └─> add_locality_places(t, locality) if valid
```

---

## 2. Problem Identification

### 2.1 Locality Validation Problem

**File:** `src/shypn/diagnostic/locality_detector.py:72-81`

```python
@property
def is_valid(self) -> bool:
    """Check if locality is valid (has inputs AND outputs).
    
    A valid locality must have:
    - At least 1 input place (tokens flow TO transition)
    - At least 1 output place (tokens flow FROM transition)
    
    Returns:
        True if locality has both inputs and outputs
    """
    return len(self.input_places) >= 1 and len(self.output_places) >= 1
```

**Issue:** This definition **excludes** source and sink transitions!

- **Source transition:** No input places (•t = ∅) → `is_valid = False` ❌
- **Sink transition:** No output places (t• = ∅) → `is_valid = False` ❌

**Impact:**
- Source/sink transitions added without locality
- Missing context for analysis plots
- User doesn't see related places

---

### 2.2 Search Results Problem

**File:** `src/shypn/analyses/search_handler.py`

```python
@staticmethod
def search_transitions(model, query):
    """Search for transitions matching the query string."""
    matches = []
    for transition in model.transitions:
        # Match against name (T1, T2, etc.)
        if query_lower in transition.name.lower():
            matches.append(transition)
            continue
        
        # Match against label (user-defined text)
        if transition.label and query_lower in transition.label.lower():
            matches.append(transition)
            continue
    
    return matches
```

**Issue:** No indication of source/sink status in results!

**Missing:**
- Visual indicator (icon or badge)
- Type information in summary
- Locality type in result label

---

### 2.3 Matplotlib Scaling Problem

**File:** `src/shypn/analyses/plot_panel.py:348-352`

```python
if not self.auto_scale and self.selected_objects:
    ylim = self.axes.get_ylim()
    y_range = ylim[1] - ylim[0]
    if y_range > 0:
        self.axes.set_ylim(ylim[0] - y_range * 0.1, ylim[1] + y_range * 0.1)
```

**Issue:** Same Y-axis treatment for all transitions!

**Problem for source/sink:**

1. **Source transitions** (token generators):
   - Y-axis should accommodate **unbounded growth**
   - Need more headroom above current max
   - Suggest: +50% margin instead of +10%

2. **Sink transitions** (token consumers):
   - Y-axis should show **bounded decrease to zero**
   - Bottom should be 0 or slightly below
   - Suggest: ylim[0] = 0, ylim[1] = max * 1.2

---

## 3. Proposed Solutions

### 3.1 Fix Locality Detection

**Update `Locality` class to recognize minimal localities:**

```python
@dataclass
class Locality:
    transition: Any
    input_places: List[Any] = field(default_factory=list)
    output_places: List[Any] = field(default_factory=list)
    input_arcs: List[Any] = field(default_factory=list)
    output_arcs: List[Any] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if locality is valid.
        
        A valid locality has at least one of:
        - Input places (normal transition or sink)
        - Output places (normal transition or source)
        
        Special cases (minimal localities):
        - Source: Only outputs (•t = ∅, t• ≠ ∅)
        - Sink: Only inputs (•t ≠ ∅, t• = ∅)
        - Normal: Both inputs and outputs
        
        Returns:
            True if locality has inputs OR outputs (or both)
        """
        # Check if transition is source or sink
        is_source = getattr(self.transition, 'is_source', False)
        is_sink = getattr(self.transition, 'is_sink', False)
        
        # Source: Valid if has outputs (minimal locality = t•)
        if is_source:
            return len(self.output_places) >= 1
        
        # Sink: Valid if has inputs (minimal locality = •t)
        if is_sink:
            return len(self.input_places) >= 1
        
        # Normal: Valid if has both inputs AND outputs
        return len(self.input_places) >= 1 and len(self.output_places) >= 1
    
    @property
    def locality_type(self) -> str:
        """Get locality type.
        
        Returns:
            'source' | 'sink' | 'normal' | 'invalid'
        """
        is_source = getattr(self.transition, 'is_source', False)
        is_sink = getattr(self.transition, 'is_sink', False)
        
        if is_source:
            return 'source'
        elif is_sink:
            return 'sink'
        elif self.is_valid:
            return 'normal'
        else:
            return 'invalid'
    
    def get_summary(self) -> str:
        """Get human-readable summary.
        
        Returns:
            String like "2 inputs → TransitionName → 3 outputs"
            Or "TransitionName (source) → 2 outputs"
            Or "1 input → TransitionName (sink)"
        """
        locality_type = self.locality_type
        
        if locality_type == 'source':
            return (f"{self.transition.name} (source) → "
                    f"{len(self.output_places)} outputs")
        elif locality_type == 'sink':
            return (f"{len(self.input_places)} inputs → "
                    f"{self.transition.name} (sink)")
        else:
            return (f"{len(self.input_places)} inputs → "
                    f"{self.transition.name} → "
                    f"{len(self.output_places)} outputs")
```

---

### 3.2 Enhance Search Results

**Update `SearchHandler.format_result_summary()` to show source/sink:**

```python
@staticmethod
def format_result_summary(results, object_type):
    """Format search results with source/sink indicators.
    
    Args:
        results: List of Place or Transition objects
        object_type: String "place" or "transition"
        
    Returns:
        str: Formatted summary
    """
    if not results:
        return f"No {object_type}s found"
    
    count = len(results)
    plural = "s" if count != 1 else ""
    
    # Create list with type indicators for transitions
    names = []
    for obj in results[:10]:
        if object_type == "transition":
            # Add source/sink indicator
            is_source = getattr(obj, 'is_source', False)
            is_sink = getattr(obj, 'is_sink', False)
            
            if is_source:
                names.append(f"{obj.name}(⊙)")  # Source symbol
            elif is_sink:
                names.append(f"{obj.name}(⊗)")  # Sink symbol
            else:
                names.append(obj.name)
        else:
            names.append(obj.name)
    
    names_str = ", ".join(names)
    
    if count > 10:
        names_str += f", ... (+{count - 10} more)"
    
    return f"Found {count} {object_type}{plural}: {names_str}"
```

**Legend:**
- `⊙` = Source (generates tokens)
- `⊗` = Sink (consumes tokens)
- No symbol = Normal transition

---

### 3.3 Add Matplotlib Source/Sink Adjustments

**Update `TransitionRatePanel._update_plot()` with smart Y-axis scaling:**

```python
def _update_plot(self):
    """Update the plot with current data.
    
    Enhanced to handle source/sink transitions with appropriate Y-axis scaling.
    """
    # ... existing plotting code ...
    
    # Apply smart Y-axis scaling based on transition types
    if not self.auto_scale and self.selected_objects:
        self._apply_smart_ylim_scaling()
    
    self.figure.tight_layout()

def _apply_smart_ylim_scaling(self):
    """Apply smart Y-axis limits based on transition types.
    
    Different transitions need different scaling:
    - Source: Unbounded growth (generous upper margin)
    - Sink: Bounded to zero (lower limit at 0)
    - Normal: Balanced margins
    """
    ylim = self.axes.get_ylim()
    y_range = ylim[1] - ylim[0]
    
    if y_range <= 0:
        return
    
    # Detect if we have source or sink transitions
    has_source = False
    has_sink = False
    
    for obj in self.selected_objects:
        is_source = getattr(obj, 'is_source', False)
        is_sink = getattr(obj, 'is_sink', False)
        
        if is_source:
            has_source = True
        if is_sink:
            has_sink = True
    
    # Apply appropriate margins
    if has_source and not has_sink:
        # SOURCE: Generous upper margin for token generation
        new_lower = max(0, ylim[0] - y_range * 0.1)  # Small lower margin
        new_upper = ylim[1] + y_range * 0.5  # 50% upper margin
        self.axes.set_ylim(new_lower, new_upper)
        
    elif has_sink and not has_source:
        # SINK: Bottom at zero, modest upper margin
        new_lower = 0  # Sinks converge to zero
        new_upper = ylim[1] + y_range * 0.2  # 20% upper margin
        self.axes.set_ylim(new_lower, new_upper)
        
    elif has_source and has_sink:
        # MIXED: Balanced margins
        new_lower = max(0, ylim[0] - y_range * 0.2)
        new_upper = ylim[1] + y_range * 0.3
        self.axes.set_ylim(new_lower, new_upper)
        
    else:
        # NORMAL: Standard margins
        new_lower = ylim[0] - y_range * 0.1
        new_upper = ylim[1] + y_range * 0.1
        self.axes.set_ylim(new_lower, new_upper)
```

---

### 3.4 Update UI Labels

**Update `TransitionRatePanel._update_objects_list()` to show source/sink:**

```python
def _update_objects_list(self):
    """Update the UI list with source/sink indicators."""
    
    # ... existing code ...
    
    for i, obj in enumerate(self.selected_objects):
        color = self._get_color(i)
        obj_name = getattr(obj, 'name', f'Transition{obj.id}')
        transition_type = getattr(obj, 'transition_type', 'immediate')
        
        # Check source/sink status
        is_source = getattr(obj, 'is_source', False)
        is_sink = getattr(obj, 'is_sink', False)
        
        # Short type names for compact display
        type_abbrev = {
            'immediate': 'IMM',
            'timed': 'TIM',
            'stochastic': 'STO',
            'continuous': 'CON'
        }.get(transition_type, transition_type[:3].upper())
        
        # Add source/sink indicator
        if is_source:
            type_abbrev += '+SRC'
        elif is_sink:
            type_abbrev += '+SNK'
        
        # Build label
        label_text = f"{obj_name} [{type_abbrev}] (T{obj.id})"
        
        # ... rest of UI code ...
        
        # Add locality places with proper labels
        if obj.id in self._locality_places:
            locality_data = self._locality_places[obj.id]
            
            # For source: Only show output places
            if is_source:
                for place in locality_data['output_places']:
                    # Add place row with "→ Output:" label
                    self._add_locality_place_row(place, "→ Output:", color)
            
            # For sink: Only show input places
            elif is_sink:
                for place in locality_data['input_places']:
                    # Add place row with "← Input:" label
                    self._add_locality_place_row(place, "← Input:", color)
            
            # For normal: Show both
            else:
                for place in locality_data['input_places']:
                    self._add_locality_place_row(place, "← Input:", color)
                for place in locality_data['output_places']:
                    self._add_locality_place_row(place, "→ Output:", color)
```

---

## 4. Implementation Plan

### Phase 1: Core Locality Detection (High Priority)

**Files to modify:**
1. `src/shypn/diagnostic/locality_detector.py`
   - Update `Locality.is_valid` property
   - Add `Locality.locality_type` property
   - Update `Locality.get_summary()` method

**Testing:**
```python
# Test source locality
source = Transition(name='T1', is_source=True)
locality = detector.get_locality_for_transition(source)
assert locality.is_valid  # Should be True if has outputs
assert locality.locality_type == 'source'
assert "source" in locality.get_summary()

# Test sink locality
sink = Transition(name='T2', is_sink=True)
locality = detector.get_locality_for_transition(sink)
assert locality.is_valid  # Should be True if has inputs
assert locality.locality_type == 'sink'
assert "sink" in locality.get_summary()
```

---

### Phase 2: Search Enhancement (Medium Priority)

**Files to modify:**
1. `src/shypn/analyses/search_handler.py`
   - Update `format_result_summary()` to show indicators

**Testing:**
```python
# Test search with source/sink
results = SearchHandler.search_transitions(model, "T")
summary = SearchHandler.format_result_summary(results, "transition")
# Should show: "Found 3 transitions: T1(⊙), T2, T3(⊗)"
```

---

### Phase 3: Matplotlib Adjustments (Medium Priority)

**Files to modify:**
1. `src/shypn/analyses/transition_rate_panel.py`
   - Add `_apply_smart_ylim_scaling()` method
   - Call from `_update_plot()`

**Testing:**
```python
# Test Y-axis scaling
panel = TransitionRatePanel(data_collector)
panel.add_object(source_transition)
panel._update_plot()
ylim = panel.axes.get_ylim()
# Should have generous upper margin for source
assert ylim[1] > max_value * 1.3
```

---

### Phase 4: UI Labels (Low Priority)

**Files to modify:**
1. `src/shypn/analyses/transition_rate_panel.py`
   - Update `_update_objects_list()` to show indicators
   - Update locality place display logic

---

## 5. Testing Checklist

### Source Transition Tests

```
□ 1. Create source transition (no inputs, has outputs)
   → Should be recognized as valid locality

□ 2. Right-click source → "Add to Analysis"
   → Should add transition + output places

□ 3. Search for source by name
   → Results should show (⊙) indicator

□ 4. Add source to plot
   → Y-axis should have generous upper margin
   → Label should show "+SRC"

□ 5. Locality should show only outputs
   → No input places listed
   → Output places with "→ Output:" label
```

### Sink Transition Tests

```
□ 1. Create sink transition (has inputs, no outputs)
   → Should be recognized as valid locality

□ 2. Right-click sink → "Add to Analysis"
   → Should add transition + input places

□ 3. Search for sink by name
   → Results should show (⊗) indicator

□ 4. Add sink to plot
   → Y-axis should have lower bound at 0
   → Label should show "+SNK"

□ 5. Locality should show only inputs
   → No output places listed
   → Input places with "← Input:" label
```

### Mixed Model Tests

```
□ 1. Model with source, sink, and normal transitions
   → All should be found in search

□ 2. Add all to analysis
   → Proper Y-axis scaling for mixed types

□ 3. Each transition shows correct locality type
   → Source: outputs only
   → Sink: inputs only
   → Normal: both
```

---

## 6. Code Locations Summary

### Files Requiring Changes

| File | Changes | Priority |
|------|---------|----------|
| `src/shypn/diagnostic/locality_detector.py` | Update `Locality.is_valid`, add `locality_type`, update `get_summary()` | **HIGH** |
| `src/shypn/analyses/search_handler.py` | Add source/sink indicators to results | Medium |
| `src/shypn/analyses/transition_rate_panel.py` | Add smart Y-axis scaling method | Medium |
| `src/shypn/analyses/transition_rate_panel.py` | Update UI labels with indicators | Low |
| `src/shypn/analyses/context_menu_handler.py` | Already works, may need label updates | Low |

---

## 7. Benefits of Changes

### For Users

1. **Clear visibility** of source/sink transitions in analysis
2. **Automatic locality detection** works for all transition types
3. **Better plot visualization** with appropriate Y-axis ranges
4. **Clear indicators** showing transition specialization

### For System

1. **Consistent treatment** of minimal localities
2. **Aligned with formal definitions** (•t = ∅, t• = ∅)
3. **Better integration** between diagnostic and analysis systems
4. **Improved matplotlib behavior** for different transition types

---

## 8. Alternative Approaches

### Option A: Minimal Change (Recommended)

- Only update `Locality.is_valid` to accept source/sink
- Keep existing UI as-is
- **Pros:** Minimal code changes, immediate fix
- **Cons:** Missing visual indicators

### Option B: Full Enhancement (Ideal)

- Update all 4 components (detection, search, matplotlib, UI)
- **Pros:** Complete solution, best UX
- **Cons:** More code changes, longer testing

### Option C: Gradual Rollout

- Phase 1: Fix locality detection (critical)
- Phase 2: Add indicators (nice-to-have)
- Phase 3: Matplotlib adjustments (polish)
- **Pros:** Incremental progress, testable at each phase
- **Cons:** Longer timeline

---

## 9. Conclusion

**Current Issue:** Source and sink transitions are not properly recognized as valid localities in the analysis system, leading to incomplete analysis plots and missing context.

**Root Cause:** The `Locality.is_valid` check requires both inputs AND outputs, which excludes minimal localities (source/sink).

**Solution:** Update locality detection to recognize minimal localities per formal Petri net theory, and enhance UI/matplotlib to properly handle these special cases.

**Recommendation:** Implement Option C (Gradual Rollout) starting with Phase 1 (locality detection fix) as it's critical for functionality.

---

**Next Step:** Implement Phase 1 changes to `locality_detector.py` and test with source/sink transitions.
