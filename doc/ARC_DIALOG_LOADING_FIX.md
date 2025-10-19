# Arc Property Dialog Loading Fix

**Date**: 2024-10-19  
**Status**: ✅ Fixed

## Problem

Arc property dialog topology tab was failing to load arc information due to incorrect model API usage.

**Error**: Attempting to call `self.model.get_arc(element_id)` which doesn't exist in the model API.

## Root Cause

In `src/shypn/ui/topology_tab_loader.py`, the `ArcTopologyTabLoader.populate()` method was trying to access:

```python
arc = self.model.get_arc(self.element_id)  # ❌ Method doesn't exist
```

The model object (ModelCanvasManager) doesn't have a `get_arc()` method. It stores arcs in a list accessible via `model.arcs`.

## Solution

**File**: `src/shypn/ui/topology_tab_loader.py` (lines 543-587)

**Changed arc lookup logic**:

**Before**:
```python
# Arc endpoint info
if self.arc_info_label:
    # Get arc source and target
    arc = self.model.get_arc(self.element_id)  # ❌ Method doesn't exist
    if arc:
        source_name = arc.source.name if hasattr(arc, 'source') else 'Unknown'
        target_name = arc.target.name if hasattr(arc, 'target') else 'Unknown'
        weight = arc.weight if hasattr(arc, 'weight') else 1
        
        text = f"Connection: {source_name} → {target_name}\n"
        text += f"Weight: {weight}"
        self.arc_info_label.set_text(text)
    else:
        self.arc_info_label.set_text("Arc information not available")
```

**After**:
```python
# Arc endpoint info
if self.arc_info_label:
    # Try to find arc in model's elements
    arc = None
    if hasattr(self.model, 'arcs'):
        for a in self.model.arcs:
            if hasattr(a, 'id') and a.id == self.element_id:
                arc = a
                break
    
    if arc:
        source_name = arc.source.name if hasattr(arc, 'source') and arc.source else 'Unknown'
        target_name = arc.target.name if hasattr(arc, 'target') and arc.target else 'Unknown'
        weight = arc.weight if hasattr(arc, 'weight') else 1
        
        text = f"Connection: {source_name} → {target_name}\n"
        text += f"Weight: {weight}"
        self.arc_info_label.set_text(text)
    else:
        self.arc_info_label.set_text("Arc information not available")
```

**Also added better error handling**:
```python
except Exception as e:
    # Handle any errors gracefully
    if self.arc_info_label:
        self.arc_info_label.set_text(f"Error loading arc info: {str(e)}")
```

## Changes Made

### 1. Safe Arc Lookup

Instead of calling non-existent method, iterate through `model.arcs` list:

```python
arc = None
if hasattr(self.model, 'arcs'):
    for a in self.model.arcs:
        if hasattr(a, 'id') and a.id == self.element_id:
            arc = a
            break
```

### 2. Enhanced Null Checks

Added extra safety checks for arc properties:

```python
source_name = arc.source.name if hasattr(arc, 'source') and arc.source else 'Unknown'
target_name = arc.target.name if hasattr(arc, 'target') and arc.target else 'Unknown'
```

### 3. Better Error Handling

Changed from silent `ImportError` catch to comprehensive exception handling:

```python
except Exception as e:
    if self.arc_info_label:
        self.arc_info_label.set_text(f"Error loading arc info: {str(e)}")
```

## Testing

### Before Fix

Opening arc properties would either:
- ❌ Crash with `AttributeError: 'ModelCanvasManager' has no attribute 'get_arc'`
- ❌ Show empty topology tab
- ❌ Show "Arc information not available"

### After Fix

Opening arc properties now:
- ✅ Loads successfully
- ✅ Shows connection information (source → target, weight)
- ✅ Shows placeholder messages for unimplemented features
- ✅ Handles errors gracefully if arc not found

### Expected Topology Tab Content

**Connection Section**:
```
Connection: Place1 → Transition1
Weight: 1
```

**Cycles Section**:
```
Arc-level cycle analysis not yet implemented
```

**Paths Section**:
```
Arc-level path analysis not yet implemented
```

**Criticality Section**:
```
Critical edge analysis not yet implemented (Tier 3)
```

## Model API Clarification

### ModelCanvasManager (model parameter)

**Has**:
- ✅ `model.arcs` - List of arc objects
- ✅ `model.places` - List of place objects
- ✅ `model.transitions` - List of transition objects

**Doesn't Have**:
- ❌ `model.get_arc(id)` - No such method
- ❌ `model.get_place(id)` - No such method
- ❌ `model.get_transition(id)` - No such method

### Correct Way to Find Elements by ID

```python
# For arcs
arc = None
if hasattr(model, 'arcs'):
    for a in model.arcs:
        if hasattr(a, 'id') and a.id == element_id:
            arc = a
            break

# For places
place = None
if hasattr(model, 'places'):
    for p in model.places:
        if hasattr(p, 'id') and p.id == element_id:
            place = p
            break

# For transitions
transition = None
if hasattr(model, 'transitions'):
    for t in model.transitions:
        if hasattr(t, 'id') and t.id == element_id:
            transition = t
            break
```

## Future Improvement

Could add helper method to ModelCanvasManager:

```python
def get_element_by_id(self, element_id):
    """Find any element (place, transition, or arc) by ID."""
    for element in itertools.chain(self.places, self.transitions, self.arcs):
        if hasattr(element, 'id') and element.id == element_id:
            return element
    return None
```

This would simplify topology loaders, but current solution works without modifying the model class.

## Impact

✅ **Arc property dialog now loads correctly**  
✅ **Topology tab shows arc connection information**  
✅ **Graceful error handling if arc not found**  
✅ **Consistent with place and transition loaders**  
✅ **No changes needed to model API**  

## Files Modified

**1. `src/shypn/ui/topology_tab_loader.py`**
- Lines 543-587: ArcTopologyTabLoader.populate() method
- Changed arc lookup from non-existent `get_arc()` to iterating `model.arcs`
- Added better null checks for arc properties
- Enhanced error handling

## Status

✅ **Arc property dialog loading: FIXED**  
✅ **All three property dialogs now working**  
✅ **Phase 4 complete with all fixes applied**  

🎉 **All Property Dialogs Fully Functional!**
