# SwissKnifePalette Signal Compatibility Mapping

## Overview

This document maps old palette signals to new SwissKnifePalette signals and documents
the required changes for integration into `model_canvas_loader.py`.

## Signal Comparison Table

| Old Signal | Old Source | Parameters | New Signal | New Source | Parameters | Status |
|------------|------------|------------|------------|------------|------------|--------|
| `tool-selected` | ToolsPalette | `(str)` tool_name | `tool-activated` | SwissKnifePalette | `(str)` tool_id | ⚠️ Name change |
| `operation-triggered` | OperationsPalette | `(str)` operation | `tool-activated` | SwissKnifePalette | `(str)` tool_id | ⚠️ Merge needed |
| `step-executed` | SimulateToolsPaletteLoader | `(float)` time | `simulation-step-executed` | SwissKnifePalette | `(float)` time | ✅ Forwarded |
| `reset-executed` | SimulateToolsPaletteLoader | `()` | `simulation-reset-executed` | SwissKnifePalette | `()` | ✅ Forwarded |
| `settings-changed` | SimulateToolsPaletteLoader | `()` | `simulation-settings-changed` | SwissKnifePalette | `()` | ✅ Forwarded |
| N/A | N/A | N/A | `mode-change-requested` | SwissKnifePalette | `(str)` mode | ✨ NEW |
| N/A | N/A | N/A | `category-selected` | SwissKnifePalette | `(str)` category_id | ✨ NEW |
| N/A | N/A | N/A | `sub-palette-shown` | SwissKnifePalette | `(str)` palette_id | ✨ NEW |
| N/A | N/A | N/A | `sub-palette-hidden` | SwissKnifePalette | `(str)` palette_id | ✨ NEW |

## Integration Strategy

### Phase 1: Unified Tool Handler

**Concept:** Merge `tool-selected` and `operation-triggered` into single `tool-activated` handler.

**Old Code (model_canvas_loader.py):**
```python
# Two separate handlers
def _on_palette_tool_selected(self, tools_palette, tool_name, canvas_manager, drawing_area):
    """Handle tool selection from ToolsPalette."""
    if tool_name == 'select':
        canvas_manager.clear_tool()
    else:
        canvas_manager.set_tool(tool_name)
    drawing_area.queue_draw()

def _on_palette_operation_triggered(self, operations_palette, operation, canvas_manager, drawing_area):
    """Handle operation from OperationsPalette."""
    if operation == 'select':
        canvas_manager.clear_tool()
        drawing_area.queue_draw()
    elif operation == 'lasso':
        # Lasso logic...
    elif operation == 'undo':
        # Undo logic...
    elif operation == 'redo':
        # Redo logic...
```

**New Code (unified handler):**
```python
def _on_swissknife_tool_activated(self, palette, tool_id, canvas_manager, drawing_area):
    """Handle tool activation from SwissKnifePalette.
    
    Unified handler for all tool types:
    - Drawing tools: place, transition, arc
    - Selection tools: select, lasso
    - Layout tools: layout_auto, layout_hierarchical, layout_force
    
    Args:
        palette: SwissKnifePalette instance
        tool_id: Tool identifier string
        canvas_manager: ModelCanvasManager instance
        drawing_area: GtkDrawingArea widget
    """
    # Drawing tools (place, transition, arc)
    if tool_id in ('place', 'transition', 'arc'):
        canvas_manager.set_tool(tool_id)
        drawing_area.queue_draw()
    
    # Selection tools
    elif tool_id == 'select':
        canvas_manager.clear_tool()
        drawing_area.queue_draw()
    
    elif tool_id == 'lasso':
        # Existing lasso logic from _on_palette_operation_triggered
        from shypn.edit.lasso_selector import LassoSelector
        # ... (copy lasso implementation)
    
    # Layout tools
    elif tool_id == 'layout_auto':
        # Call auto layout
        canvas_manager.apply_auto_layout()
        drawing_area.queue_draw()
    
    elif tool_id == 'layout_hierarchical':
        # Call hierarchical layout
        canvas_manager.apply_hierarchical_layout()
        drawing_area.queue_draw()
    
    elif tool_id == 'layout_force':
        # Call force-directed layout
        canvas_manager.apply_force_directed_layout()
        drawing_area.queue_draw()
```

### Phase 2: Mode Change Handler (NEW)

**Purpose:** Handle mode switching between Edit and Simulate modes.

**New Handler:**
```python
def _on_swissknife_mode_change_requested(self, palette, requested_mode, canvas_manager, drawing_area):
    """Handle mode change request from SwissKnifePalette.
    
    This is called when user clicks Edit or Simulate category buttons.
    Currently, all categories (Edit, Simulate, Layout) are in 'edit' mode,
    so this handler may not trigger mode switches until Simulate mode is separated.
    
    Args:
        palette: SwissKnifePalette instance
        requested_mode: 'edit' or 'simulate'
        canvas_manager: ModelCanvasManager instance
        drawing_area: GtkDrawingArea widget
    """
    current_mode = self._get_current_mode(drawing_area)
    
    if requested_mode != current_mode:
        # Switch mode
        self._switch_canvas_mode(drawing_area, requested_mode)
```

### Phase 3: Signal Connections

**Old Wiring (ToolsPalette + OperationsPalette):**
```python
# In _add_palettes_to_canvas()
tools_palette = ToolsPalette()
operations_palette = OperationsPalette()

# Connect signals
tools_palette.connect('tool-selected', self._on_palette_tool_selected, canvas_manager, drawing_area)
operations_palette.connect('operation-triggered', self._on_palette_operation_triggered, canvas_manager, drawing_area)
```

**New Wiring (SwissKnifePalette):**
```python
# In _add_palettes_to_canvas()
from shypn.ui.swissknife_palette import SwissKnifePalette

swissknife_palette = SwissKnifePalette(
    mode='edit',
    model=canvas_manager.petri_net_model
)

# Connect unified tool handler
swissknife_palette.connect('tool-activated', 
    self._on_swissknife_tool_activated, canvas_manager, drawing_area)

# Connect mode change handler
swissknife_palette.connect('mode-change-requested',
    self._on_swissknife_mode_change_requested, canvas_manager, drawing_area)

# Connect simulation signals (forwarded from SimulateToolsPaletteLoader)
swissknife_palette.connect('simulation-step-executed',
    self._on_simulation_step, canvas_manager, drawing_area)
swissknife_palette.connect('simulation-reset-executed',
    self._on_simulation_reset, canvas_manager, drawing_area)
swissknife_palette.connect('simulation-settings-changed',
    self._on_simulation_settings_changed, canvas_manager, drawing_area)

# Optional: Connect informational signals
swissknife_palette.connect('category-selected',
    lambda p, cat_id: print(f"[DEBUG] Category selected: {cat_id}"))
swissknife_palette.connect('sub-palette-shown',
    lambda p, pal_id: print(f"[DEBUG] Sub-palette shown: {pal_id}"))
swissknife_palette.connect('sub-palette-hidden',
    lambda p, pal_id: print(f"[DEBUG] Sub-palette hidden: {pal_id}"))
```

## Tool ID Mapping

### Drawing Tools
| Old Name | Old Source | New Tool ID | Handler Action |
|----------|------------|-------------|----------------|
| `place` | ToolsPalette | `place` | `canvas_manager.set_tool('place')` |
| `transition` | ToolsPalette | `transition` | `canvas_manager.set_tool('transition')` |
| `arc` | ToolsPalette | `arc` | `canvas_manager.set_tool('arc')` |

### Selection Tools
| Old Name | Old Source | New Tool ID | Handler Action |
|----------|------------|-------------|----------------|
| `select` | ToolsPalette | `select` | `canvas_manager.clear_tool()` |
| `select` | OperationsPalette | `select` | `canvas_manager.clear_tool()` |
| `lasso` | OperationsPalette | `lasso` | `LassoSelector` logic |

### Edit Operations (NOW tools in Edit sub-palette)
| Old Operation | Old Source | New Tool ID | Handler Action |
|---------------|------------|-------------|----------------|
| `undo` | OperationsPalette | ~~removed~~ | Keep old [U] button separate |
| `redo` | OperationsPalette | ~~removed~~ | Keep old [R] button separate |

**Note:** Undo/Redo buttons remain in old OperationsPalette for now. SwissKnifePalette focuses on drawing/selection/layout tools.

### Layout Tools (NEW)
| Tool ID | Sub-Palette | Handler Action |
|---------|-------------|----------------|
| `layout_auto` | Layout | `canvas_manager.apply_auto_layout()` |
| `layout_hierarchical` | Layout | `canvas_manager.apply_hierarchical_layout()` |
| `layout_force` | Layout | `canvas_manager.apply_force_directed_layout()` |

## Implementation Checklist

### In model_canvas_loader.py

- [ ] Add import: `from shypn.ui.swissknife_palette import SwissKnifePalette`
- [ ] Create new handler: `_on_swissknife_tool_activated()`
- [ ] Create new handler: `_on_swissknife_mode_change_requested()`
- [ ] In `_add_palettes_to_canvas()`:
  - [ ] Create SwissKnifePalette instance
  - [ ] Connect `tool-activated` signal
  - [ ] Connect `mode-change-requested` signal
  - [ ] Connect simulation signals (forwarded)
  - [ ] Position palette (overlay, margins, alignment)
  - [ ] Hide initially (show on mode change)
- [ ] Keep old OperationsPalette for Undo/Redo temporarily
- [ ] Update `_on_mode_changed()` to show/hide SwissKnifePalette

### In SwissKnifePalette (swissknife_palette.py)

- [x] All signals defined ✅
- [x] Widget palette integration working ✅
- [x] Animations working ✅
- [x] CSS applied ✅
- [ ] Tool implementations (Task 4)

### In ToolRegistry (swissknife_tool_registry.py)

- [x] Basic structure ✅
- [ ] Real tool implementations (Task 4)
- [ ] Canvas manager connection (Task 4)
- [ ] Layout algorithm wiring (Task 8)

## Backward Compatibility

**During Integration:**
- Keep old ToolsPalette and OperationsPalette code
- Run both systems in parallel initially
- Test SwissKnifePalette thoroughly
- Switch over when validated
- Remove old code (Task 9)

**Signal Compatibility:**
- Old handlers remain untouched until switch-over
- New handlers tested independently
- No conflicts - different signal names

## Testing Strategy

### Unit Tests
1. Verify `tool-activated` signal emits correctly for each tool
2. Verify `mode-change-requested` signal emits on Edit/Simulate clicks
3. Verify simulation signals forwarded correctly

### Integration Tests
1. Connect SwissKnifePalette to test canvas
2. Verify drawing tools work (P/T/A)
3. Verify selection tools work (S/L)
4. Verify layout tools trigger algorithms
5. Verify mode switching works
6. Verify simulation palette appears and functions

### Regression Tests
1. Ensure old palettes still work during transition
2. Verify no signal conflicts
3. Verify no CSS conflicts
4. Verify no layout issues

## Risk Mitigation

**Medium Risk:** Signal name changes
- **Mitigation:** Keep old handlers, test new system separately

**Low Risk:** Simulation signals (already forwarded correctly)
- **Mitigation:** Already tested in test bed

**Low Risk:** CSS conflicts
- **Mitigation:** SwissKnife uses unique class names (swissknife-*)

## Next Steps

After Task 3 (this analysis):
1. **Task 4:** Implement real tools in ToolRegistry
2. **Task 5:** Integrate into model_canvas_loader.py
3. **Task 6:** Wire mode switching
4. **Task 7:** Test with real Petri net model
5. **Task 8:** Wire layout algorithms
6. **Task 9:** Remove old palette code
7. **Task 10:** Full workflow testing

---
*Document Version: 1.0*
*Last Updated: 2025-10-09*
*Status: Analysis Complete - Ready for Task 4*
