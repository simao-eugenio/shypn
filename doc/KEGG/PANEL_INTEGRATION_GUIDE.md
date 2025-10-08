# KEGG Pathway Panel - Integration Guide

## Panel Behavior

### Right Panel Toggle System

The right dock area supports **two mutually exclusive panels**:
1. **Analyses Panel** - For simulation analysis and diagnostics
2. **Pathways Panel** - For KEGG pathway import operations

**Key Behaviors**:
- Only ONE panel shows at a time in the right dock area
- Toggling one panel automatically hides the other
- This separation reflects different phases of work:
  - **Pathway Import Phase**: Fetching and importing biochemical pathways
  - **Analysis Phase**: Running simulations and analyzing results

### Button Controls

#### Header Bar Buttons:
- **"Analyses"** button - Toggles Analyses panel
- **"Pathways"** button - Toggles Pathways panel

**When you click "Pathways":**
1. Analyses panel hides (if visible)
2. Pathways panel docks to right side
3. Right paned adjusts to show 320px width

**When you click "Analyses":**
1. Pathways panel hides (if visible)
2. Analyses panel docks to right side
3. Right paned adjusts to show 280px width

#### Panel Float Button (⇲):
- Inside each panel's header
- Toggles between **docked** and **floating** states
- When floating, panel becomes a separate window
- Panel can be moved independently

#### Window Close Button (X):
- Closes the floating window
- **Automatically hides and docks the panel back** to main window
- Does not destroy the panel (prevents segmentation fault)
- Updates float button state to inactive
- Safe to use - will not crash the application

## Integration Code

### In `src/shypn.py`:

```python
def on_right_toggle(button):
    """Toggle Analyses panel (hides Pathways if active)."""
    is_active = button.get_active()
    if is_active:
        # Hide pathway panel if visible
        if pathway_toggle and pathway_toggle.get_active():
            pathway_toggle.handler_block_by_func(on_pathway_toggle)
            pathway_toggle.set_active(False)
            pathway_toggle.handler_unblock_by_func(on_pathway_toggle)
            if pathway_panel_loader:
                pathway_panel_loader.hide()
        
        # Show analyses panel
        right_panel_loader.attach_to(right_dock_area, parent_window=window)
        # ...adjust paned for 280px width
    else:
        right_panel_loader.hide()

def on_pathway_toggle(button):
    """Toggle Pathways panel (hides Analyses if active)."""
    is_active = button.get_active()
    if is_active:
        # Hide analyses panel if visible
        if right_toggle and right_toggle.get_active():
            right_toggle.handler_block_by_func(on_right_toggle)
            right_toggle.set_active(False)
            right_toggle.handler_unblock_by_func(on_right_toggle)
            right_panel_loader.hide()
        
        # Show pathway panel
        pathway_panel_loader.attach_to(right_dock_area, parent_window=window)
        # ...adjust paned for 320px width
    else:
        pathway_panel_loader.hide()
```

## Workflow Examples

### Pathway Import Workflow:
1. Click **"Pathways"** button → Analyses panel hides, Pathways panel shows
2. Enter pathway ID (e.g., "hsa00010")
3. Click "Fetch Pathway" → Downloads from KEGG
4. Review preview
5. Click "Import" → Converts to Petri net
6. Pathway loaded to canvas
7. Click **"Pathways"** button again → Panel hides

### Analysis Workflow:
1. Click **"Analyses"** button → Pathways panel hides, Analyses panel shows
2. Run simulation
3. View place/transition rates
4. Check diagnostics
5. Click **"Analyses"** button again → Panel hides

### Switching Between Workflows:
```
State 1: Both panels hidden
  → Click "Pathways" → Pathways panel docked on right

State 2: Pathways panel visible
  → Click "Analyses" → Pathways hides, Analyses docks on right

State 3: Analyses panel visible
  → Click "Pathways" → Analyses hides, Pathways docks on right

State 4: Either panel visible
  → Click float button (⇲) → Panel becomes floating window
  → Click X on floating window → Panel docks back
```

## Design Rationale

### Why Mutual Exclusivity?

1. **Different Work Phases**: Importing pathways and analyzing simulations are distinct activities
2. **Screen Real Estate**: Maximizes space for active workflow
3. **Clear Focus**: User knows which mode they're in
4. **Performance**: Only one panel's widgets active at a time

### Why Same Dock Area?

1. **Consistent Location**: Users always know where to look (right side)
2. **Similar Purpose**: Both are "information panels" (vs. left "file operations")
3. **Panel Architecture**: Reuses existing right_dock_area infrastructure

## Technical Notes

### Panel Switching Logic:
- Uses `handler_block_by_func` / `handler_unblock_by_func` to prevent recursive toggle events
- Properly hides previous panel before showing new one
- Maintains paned position consistency

### Width Requirements:
- **Analyses Panel**: 280px (compact for charts)
- **Pathways Panel**: 320px (wider for pathway info and options)

### Preserved Analyses Code:
✅ All existing Analyses panel code unchanged
✅ No modification to right_panel_loader.py
✅ No modification to right_panel.ui
✅ Original toggle behavior preserved when Pathways hidden

## Summary

✅ **Pathways** and **Analyses** panels share right dock area  
✅ **Mutually exclusive** - only one visible at a time  
✅ **Toggle buttons** automatically switch between them  
✅ **Float button (⇲)** works independently for each panel  
✅ **Close (X)** docks floating panel back  
✅ **Analyses code** completely preserved and unchanged  

This design keeps workflow phases separate while maintaining a clean, intuitive interface.
