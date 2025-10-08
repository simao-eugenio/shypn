# Pathway and Analyses Panel Mutual Exclusivity

## Overview

The right dock area now supports **two mutually exclusive panels**:
1. **Pathways Panel** - KEGG pathway import operations
2. **Analyses Panel** - Simulation analysis and diagnostics

## Key Design Decision

**Why Mutual Exclusivity?**
- Different work phases (importing vs. analyzing)
- Maximizes screen space for active workflow
- Clear focus on current task
- Performance optimization

## Implementation

### Files Modified

**`src/shypn.py`**: Added mutual exclusivity logic in two toggle handlers

### Toggle Handler Logic

```python
def on_pathway_toggle(button):
    """Show Pathways panel, hide Analyses if visible."""
    is_active = button.get_active()
    if is_active:
        # Step 1: Hide analyses panel if visible
        if right_toggle and right_toggle.get_active():
            right_toggle.handler_block_by_func(on_right_toggle)  # Prevent recursion
            right_toggle.set_active(False)
            right_toggle.handler_unblock_by_func(on_right_toggle)
            right_panel_loader.hide()
        
        # Step 2: Show pathway panel docked on right
        pathway_panel_loader.attach_to(right_dock_area, parent_window=window)
        
        # Step 3: Adjust paned position for 320px width
        if right_paned:
            paned_width = right_paned.get_width()
            if paned_width > 320:
                right_paned.set_position(paned_width - 320)
    else:
        # Hide pathway panel
        pathway_panel_loader.hide()
        # Reset paned to full width
        if right_paned:
            paned_width = right_paned.get_width()
            right_paned.set_position(paned_width)

def on_right_toggle(button):
    """Show Analyses panel, hide Pathways if visible."""
    is_active = button.get_active()
    if is_active:
        # Step 1: Hide pathway panel if visible
        if pathway_toggle and pathway_toggle.get_active():
            pathway_toggle.handler_block_by_func(on_pathway_toggle)  # Prevent recursion
            pathway_toggle.set_active(False)
            pathway_toggle.handler_unblock_by_func(on_pathway_toggle)
            pathway_panel_loader.hide()
        
        # Step 2: Show analyses panel
        right_panel_loader.attach_to(right_dock_area, parent_window=window)
        # ...rest of analyses code (unchanged)
```

## Behavior States

### State Transitions

```
┌─────────────────────────┐
│   Both Panels Hidden    │
└─────────┬───────────────┘
          │
          ├─[Click "Pathways"]────→ Pathways visible, Analyses hidden
          │                            │
          │                            ├─[Click "Analyses"]─→ Analyses visible, Pathways hidden
          │                            │
          └─[Click "Analyses"]────→ Analyses visible, Pathways hidden
                                       │
                                       └─[Click "Pathways"]─→ Pathways visible, Analyses hidden
```

### Float/Dock Independence

Each panel can independently:
- **Float button (⇲)**: Toggle between docked and floating window
- **Close (X)**: Close floating window (docks panel back)
- **Toggle button**: Show/hide panel (always hides the other)

## Technical Details

### Handler Blocking

**Purpose**: Prevent infinite recursion when one toggle handler modifies another toggle button

**Pattern**:
```python
# Block handler before changing state
toggle_button.handler_block_by_func(handler_function)
toggle_button.set_active(False)
toggle_button.handler_unblock_by_func(handler_function)
```

Without blocking, changing a toggle button's state would trigger its handler, which would change the other toggle, triggering its handler, creating infinite recursion.

### Paned Position Management

**Pathways Panel**: 320px width (wider for pathway info)
**Analyses Panel**: 280px width (compact for charts)

Both panels adjust `right_paned` position when docked:
```python
if right_paned:
    paned_width = right_paned.get_width()
    if paned_width > panel_width:
        right_paned.set_position(paned_width - panel_width)
```

### Shared Dock Area

Both panels attach to the **same** `right_dock_area`:
```python
# Pathways panel
pathway_panel_loader.attach_to(right_dock_area, parent_window=window)

# Analyses panel
right_panel_loader.attach_to(right_dock_area, parent_window=window)
```

Only one can be attached at a time due to mutual exclusivity logic.

## Code Preservation

### Analyses Panel Code - ✅ UNCHANGED

**Critical Requirement**: All existing Analyses panel code must remain unchanged.

**What Was Preserved**:
- ✅ `right_panel_loader.py` - No modifications
- ✅ `right_panel.ui` - No modifications
- ✅ Original `on_right_toggle()` logic - Only added mutual exclusivity check at beginning
- ✅ Paned position management - Original logic preserved
- ✅ Float/dock behavior - Original behavior preserved

**What Was Added**:
- New check at beginning of `on_right_toggle()`: hide pathway panel if visible
- New `on_pathway_toggle()` handler: mirror logic for pathway panel

## User Experience

### Workflow Example 1: Importing Pathways

```
1. User clicks "Pathways" button
   → Analyses panel (if visible) hides
   → Pathways panel docks on right side
   
2. User enters pathway ID "hsa00010"
3. User clicks "Fetch Pathway"
   → Preview appears
   
4. User clicks "Import"
   → Pathway loaded to canvas
   
5. User clicks "Pathways" button again
   → Pathways panel hides
   → Canvas has full width
```

### Workflow Example 2: Analyzing Simulations

```
1. User clicks "Analyses" button
   → Pathways panel (if visible) hides
   → Analyses panel docks on right side
   
2. User runs simulation
3. User views place/transition rates
4. User checks diagnostics
5. User clicks "Analyses" button again
   → Analyses panel hides
```

### Workflow Example 3: Switching Between Panels

```
Start: Both panels hidden

User clicks "Pathways"
→ Pathways panel appears docked

User clicks "Analyses"
→ Pathways panel hides automatically
→ Analyses panel appears docked

User clicks "Pathways" again
→ Analyses panel hides automatically
→ Pathways panel appears docked

User clicks float button (⇲) on Pathways
→ Pathways becomes floating window
→ Can be moved independently

User clicks "Analyses"
→ Pathways floating window hides
→ Analyses panel appears docked

User clicks "Pathways"
→ Analyses panel hides
→ Pathways appears docked (not floating anymore)
```

## Testing Checklist

### Manual Testing Steps

- [ ] **Basic Toggle**:
  - [ ] Click "Pathways" → Panel appears docked on right
  - [ ] Click "Pathways" again → Panel hides
  - [ ] Click "Analyses" → Panel appears docked on right
  - [ ] Click "Analyses" again → Panel hides

- [ ] **Mutual Exclusivity**:
  - [ ] With Pathways visible, click "Analyses" → Pathways hides, Analyses shows
  - [ ] With Analyses visible, click "Pathways" → Analyses hides, Pathways shows
  - [ ] Verify buttons update correctly (one ON, one OFF)

- [ ] **Float/Dock**:
  - [ ] Click "Pathways", then float button (⇲) → Becomes floating window
  - [ ] Click X on floating window → Docks back
  - [ ] Click "Analyses" with floating Pathways → Pathways hides, Analyses docks
  - [ ] Same tests for Analyses panel

- [ ] **Paned Position**:
  - [ ] Verify Pathways panel width ≈ 320px
  - [ ] Verify Analyses panel width ≈ 280px
  - [ ] Hiding panel → Canvas expands to full width
  - [ ] Showing panel → Canvas shrinks appropriately

- [ ] **No Regressions**:
  - [ ] Analyses panel functions exactly as before
  - [ ] No errors in console
  - [ ] No UI glitches
  - [ ] Panel states persist correctly

## Summary

✅ **Mutual exclusivity implemented** - Only one panel visible at a time  
✅ **Handler blocking prevents recursion** - Clean toggle logic  
✅ **Analyses code preserved** - Zero modifications to existing panel  
✅ **Paned positions managed** - Proper width for each panel  
✅ **Float/dock independent** - Each panel can float separately  
✅ **Clean separation of concerns** - Import phase vs. analysis phase  

**Ready for testing**: Launch `python3 src/shypn.py` and test workflows! 🚀
