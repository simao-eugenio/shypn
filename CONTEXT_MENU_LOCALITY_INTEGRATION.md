# Context Menu Locality Integration - Implementation Summary

## Overview
Successfully integrated automatic locality detection into the context menu's "Add to Transition Analysis" feature, matching the behavior of the search UI.

## Implementation Date
October 5, 2025

## Problem Statement
When right-clicking on a transition and selecting "Add to Transition Analysis", only the transition was added to the analysis plot. The locality places (inputs and outputs) were not automatically included, unlike the search UI which automatically added them.

## Root Cause
The `ContextMenuHandler` was initialized with `model=None` during the right panel setup, and when the model was later set via `RightPanelLoader.set_model()`, the context menu handler's `locality_detector` was never updated.

**Initialization Flow (Before Fix):**
```
1. RightPanelLoader.__init__() → creates panels
2. _setup_plotting_panels() → creates ContextMenuHandler(panels, model=None)
3. ContextMenuHandler.__init__() → locality_detector = None ❌
4. Later: set_model(model) called → updates self.model
5. BUT: context_menu_handler.locality_detector stays None ❌
```

## Solution

### Changes Made

#### 1. **Fixed Plot Rendering Bug** (`src/shypn/analyses/transition_rate_panel.py`)
Fixed tuple unpacking error where place data format is `(time, tokens)` but code expected 3 values:

```python
# Lines 568-569 (input places) - FIXED
times = [t for t, tokens in place_data]  # Was: t, tokens, _
tokens = [tok for t, tok in place_data]  # Was: tok, _, _

# Lines 594-595 (output places) - FIXED  
times = [t for t, tokens in place_data]  # Was: t, tokens, _
tokens = [tok for t, tok in place_data]  # Was: tok, _, _
```

#### 2. **Updated Context Menu Logic** (`src/shypn/analyses/context_menu_handler.py`)
Changed from submenu with two options to single automatic action:

**Before:**
- Right-click → Submenu with:
  - "Transition Only"
  - "With Locality (N places)"

**After:**
- Right-click → Single item: "Add to Transition Analysis"
- Automatically includes locality if valid

```python
def _add_transition_locality_submenu(self, menu, transition, panel):
    """Add menu item for transition - automatically includes locality if valid."""
    locality = self.locality_detector.get_locality_for_transition(transition)
    
    if not locality.is_valid:
        # No valid locality, add simple menu item
        menu_item = Gtk.MenuItem(label=f"Add to Transition Analysis")
        menu_item.connect("activate", 
                        lambda w: self._on_add_to_analysis_clicked(transition, panel))
    else:
        # Create menu item that automatically adds transition + locality
        menu_item = Gtk.MenuItem(label=f"Add to Transition Analysis")
        menu_item.connect("activate",
                         lambda w: self._add_transition_with_locality(transition, locality, panel))
    
    menu_item.show()
    menu.append(menu_item)
```

#### 3. **Fixed Model Propagation** (`src/shypn/helpers/right_panel_loader.py`)
Updated `set_model()` to propagate model to context menu handler:

```python
def set_model(self, model):
    """Set the model for search functionality."""
    self.model = model
    
    # ✅ NEW: Update context menu handler's model for locality detection
    if self.context_menu_handler:
        self.context_menu_handler.set_model(model)
        print("[RightPanelLoader] Context menu handler model updated for locality detection")
    
    # Wire search UI
    if self.builder is not None and (self.place_panel or self.transition_panel):
        self._wire_search_ui()
        print("[RightPanelLoader] Model set and search UI wired")
```

#### 4. **Added Debug Logging** (for troubleshooting)
Enhanced debug output to trace initialization and locality detection flow:

```python
# In __init__
if model:
    self.locality_detector = LocalityDetector(model)
    print(f"[ContextMenuHandler] __init__ - Locality detector created with model")
else:
    print(f"[ContextMenuHandler] __init__ - No model provided, locality detector is None")

# In add_analysis_menu_items
if isinstance(obj, Transition) and self.locality_detector:
    print(f"[ContextMenuHandler] Transition detected with locality_detector - calling _add_transition_locality_submenu")
    self._add_transition_locality_submenu(menu, obj, panel)
else:
    if isinstance(obj, Transition):
        print(f"[ContextMenuHandler] Transition detected but locality_detector={self.locality_detector} - using simple menu")
```

## Files Modified

1. **src/shypn/analyses/transition_rate_panel.py**
   - Fixed place data unpacking (lines 568-569, 594-595)

2. **src/shypn/analyses/context_menu_handler.py**
   - Simplified menu from submenu to single automatic action
   - Added comprehensive debug logging
   - Enhanced `_add_transition_with_locality()` with detailed output

3. **src/shypn/helpers/right_panel_loader.py**
   - Added model propagation to context menu handler in `set_model()`

## Behavior

### Current Implementation

**When right-clicking on a transition:**

1. **Transition with valid locality:**
   - Menu shows: "Add to Transition Analysis"
   - Click → Automatically adds:
     - The transition (solid line)
     - Input places (dashed lines, lighter color)
     - Output places (dotted lines, darker color)
   - Log: `"Added T1 with locality (1 inputs, 1 outputs)"`

2. **Transition without valid locality:**
   - Menu shows: "Add to Transition Analysis"
   - Click → Adds just the transition
   - Log: `"Transition T1 has no valid locality"`

### Consistent User Experience

✅ **Search for transition** → Auto-adds with locality
✅ **Right-click "Add to Analysis"** → Auto-adds with locality
✅ **Objects list** → Shows transition + nested places with hierarchy arrows (↓ inputs, ↑ outputs)
✅ **Plot** → Renders all objects together with distinct line styles

## Debug Output Example

```
[ContextMenuHandler] __init__ - No model provided, locality detector is None
[RightPanelLoader] Context menu handler created with model support
[RightPanelLoader] Context menu handler model updated for locality detection
[ContextMenuHandler] Model and locality detector set
...
[ContextMenuHandler] Transition detected with locality_detector - calling _add_transition_locality_submenu
[ContextMenuHandler] Creating menu for transition T1
[ContextMenuHandler] Locality detected - valid: True, places: 2
[ContextMenuHandler] Menu item created for T1 - will auto-add locality with 2 places
...
[ContextMenuHandler] _add_transition_with_locality called for T1
[ContextMenuHandler]   Locality valid: True
[ContextMenuHandler]   Input places: 1
[ContextMenuHandler]   Output places: 1
[ContextMenuHandler]   Panel type: TransitionRatePanel
[ContextMenuHandler]   Has add_locality_places: True
[TransitionRatePanel] Added transition 1 to analysis
[ContextMenuHandler] Transition T1 added to panel
[TransitionRatePanel] Locality registered for T1: 1 inputs, 1 outputs
[ContextMenuHandler] Successfully added T1 with locality (1 inputs, 1 outputs)
```

## Testing

### Test Case 1: Simple Model (P1 → T1 → P2)
✅ Right-click T1 → "Add to Transition Analysis"
✅ Result: T1, P1 (input), P2 (output) all plotted
✅ Objects list: Shows "T1" with nested "↓ P1" and "↑ P2"

### Test Case 2: Transition Without Locality
✅ Right-click T_isolated → "Add to Transition Analysis"
✅ Result: Only T_isolated plotted
✅ Log: "Transition has no valid locality"

### Test Case 3: Search vs Context Menu Consistency
✅ Search for "T1" → Auto-adds locality
✅ Right-click T1 → Auto-adds locality
✅ Both produce identical results

## Related Features

This implementation builds on the existing locality-based analysis system:

- **Locality Detection** (`src/shypn/diagnostic/locality_detector.py`)
- **Locality Analysis** (`src/shypn/diagnostic/locality_analyzer.py`)
- **Locality Info Widget** (`src/shypn/diagnostic/locality_info_widget.py`)
- **Search UI Integration** (`src/shypn/analyses/transition_rate_panel.py` - `wire_search_ui()`)
- **Plot Rendering** (`src/shypn/analyses/transition_rate_panel.py` - `_plot_locality_places()`)

## Benefits

1. **Consistency**: Context menu now behaves like search UI
2. **Efficiency**: Users don't need to manually select locality places
3. **Discoverability**: Automatic behavior makes locality feature more visible
4. **Simplicity**: Single menu item instead of confusing submenu options

## Future Enhancements

Possible improvements for future consideration:

1. **Optional Toggle**: Add preference to disable automatic locality inclusion
2. **Visual Feedback**: Highlight locality places on canvas when hovering menu item
3. **Batch Operations**: Right-click multiple transitions → add all with localities
4. **Smart Deduplication**: If multiple transitions share places, plot places only once

## Conclusion

The context menu now provides a seamless, intuitive way to analyze transitions with their localities, matching the behavior users already experience with the search functionality. The fix ensures proper model propagation through the initialization chain, enabling locality detection to work correctly from any entry point.
