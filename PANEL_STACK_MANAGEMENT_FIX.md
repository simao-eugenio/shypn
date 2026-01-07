# Panel Stack Management Fix

## Problem

The Master Palette toggle handlers (Pathways, Analyses buttons) were manually managing all stack visibility, panel content, and container logic directly in `shypn.py`. This was complex, error-prone, and inconsistent with the stable v2.5.4 architecture where loaders encapsulated this logic.

### Root Causes

1. **Per-document panels** (`PathwayPanelLoader`, `AnalysesPanelLoader`) inherited from `PerDocumentPanelLoader` but didn't have `show_in_stack()` / `hide_in_stack()` methods
2. **Property naming inconsistency**: Some code checked `is_attached`, other code checked `is_hanged`
3. **Manual stack management**: Toggle handlers manually manipulated containers, stack visibility, and panel content instead of delegating to loaders

## Solution

### 1. Added Stack Management Methods to Base Class

Added `show_in_stack()` and `hide_in_stack()` methods to `PerDocumentPanelLoader` in `base_panel_loader.py`:

```python
def show_in_stack(self) -> None:
    """Show this panel in the GtkStack (called by Master Palette toggle).
    
    Handles both docked and floating states:
    - If docked (is_hanged=True): Show in stack
    - If floating (is_hanged=False): Show window
    """
    # Implementation handles stack visibility, parent_container, panel.show_all()

def hide_in_stack(self) -> None:
    """Hide this panel in the GtkStack (called by Master Palette toggle).
    
    Handles both docked and floating states:
    - If docked (is_hanged=True): Hide in stack
    - If floating (is_hanged=False): Hide window
    """
    # Implementation handles hiding logic
```

### 2. Added Property Alias for Backward Compatibility

Added `is_hanged` as an alias for `is_attached` in `PerDocumentPanelLoader`:

```python
@property
def is_hanged(self) -> bool:
    """Alias for is_attached (backward compatibility with legacy loaders)."""
    return self._is_attached

@is_hanged.setter
def is_hanged(self, value: bool) -> None:
    """Set attached state via legacy property name."""
    self._is_attached = value
```

### 3. Simplified Toggle Handlers

Restored stable v2.5.4 pattern in `shypn.py` toggle handlers:

**Before (complex manual management)**:
```python
def on_pathway_toggle(is_active):
    if is_active:
        if pathway_loader.is_hanged:
            if pathways_panel_container:
                pathways_panel_container.set_visible(True)
                if pathway_loader.panel:
                    pathway_loader.panel.show_all()
            if left_dock_stack:
                left_dock_stack.set_visible(True)
                left_dock_stack.set_visible_child_name('pathways')
            # ... more manual logic
        else:
            pathway_loader.show_window()
    else:
        if pathway_loader.is_hanged:
            # ... complex hiding logic
        else:
            pathway_loader.hide_window()
```

**After (simple delegation)**:
```python
def on_pathway_toggle(is_active):
    if is_active:
        # Deactivate others
        master_palette.set_active('files', False)
        master_palette.set_active('analyses', False)
        # ... other deactivations
        
        # Show this panel (loader handles docked vs floating)
        pathway_loader.show_in_stack()
        
        # Expand paned if docked
        if pathway_loader.is_hanged and left_paned:
            left_paned.set_position(250)
    else:
        pathway_loader.hide_in_stack()
        # Collapse paned
        if left_dock_stack:
            left_dock_stack.set_visible(False)
        if left_paned:
            left_paned.set_position(0)
```

## Benefits

1. **Encapsulation**: Stack management logic lives in panel loaders where it belongs
2. **Consistency**: All panel types (global and per-document) use same pattern
3. **Maintainability**: Changes to stack management happen in one place (base class)
4. **Simplicity**: Toggle handlers reduced from ~80 lines to ~20 lines each
5. **Backward compatibility**: `is_hanged` property works for legacy code

## Architecture Comparison

### Stable v2.5.4 Pattern (Restored)
```
Master Palette → Toggle Handler → Loader.show_in_stack() → (Internal management)
```

### Complex Manual Pattern (Removed)
```
Master Palette → Toggle Handler → Manual container manipulation
                                 → Manual stack visibility
                                 → Manual panel.show_all()
                                 → Manual paned positioning
```

## Testing

1. **Syntax verification**: ✅ `python -m py_compile src/shypn.py`
2. **Functional testing**: Launch app, test all Master Palette buttons
3. **Per-document testing**: Switch between tabs, verify correct panels show
4. **Float/dock testing**: Float a panel, verify toggle button still works

## Files Modified

- `src/shypn/helpers/base_panel_loader.py` (+82 lines)
  - Added `show_in_stack()` method
  - Added `hide_in_stack()` method
  - Added `is_hanged` property alias

- `src/shypn.py` (-120 lines, +20 lines)
  - Simplified `on_pathway_toggle()` handler
  - Simplified `on_right_toggle()` handler
  - Removed manual container/stack management logic

## Next Steps

Consider applying same pattern to:
- `on_topology_toggle()` (if it has manual management)
- `on_report_toggle()` (check if it needs simplification)
- `on_viability_toggle()` (check if it needs simplification)

## References

- Git tag: `v2.5.4` (stable version with simple toggle handlers)
- Commit: `dd2935c` (last stable before per-document panel issues)
