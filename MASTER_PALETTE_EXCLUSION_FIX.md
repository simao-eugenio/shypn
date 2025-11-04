# Master Palette Button Exclusion - Fix Documentation

## Issue
The Master Palette button exclusion logic was disrupted after recent Pathway panel refactoring. When clicking different panel buttons, multiple panels could appear simultaneously instead of maintaining mutual exclusivity.

## Root Cause
The Pathway panel's float/attach callbacks were not wired in `src/shypn.py`, causing the panel state to become desynchronized with the Master Palette button state when the panel was detached and reattached.

## Fix Applied

### File: `src/shypn.py`
**Location:** Lines 927-950 (approximately)

Added missing float/attach callbacks for the Pathway panel:

```python
# Define float/attach callbacks for pathway panel
def on_pathway_float():
    """Collapse left paned when Pathways panel floats."""
    if left_paned:
        try:
            left_paned.set_position(0)
        except Exception:
            pass  # Ignore paned errors
    # NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks

def on_pathway_attach():
    """Expand left paned when Pathways panel attaches."""
    if left_paned:
        try:
            left_paned.set_position(270)
        except Exception:
            pass  # Ignore paned errors
    # NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks

# Wire up callbacks (ADDED pathway_panel_loader wiring)
if pathway_panel_loader:
    pathway_panel_loader.on_float_callback = on_pathway_float
    pathway_panel_loader.on_attach_callback = on_pathway_attach
```

## How Button Exclusion Works

### Architecture
1. **Master Palette** (`src/shypn/ui/master_palette.py`)
   - Manages 5 toggle buttons: Files, Pathways, Analyses, Topology, Report
   - Each button has a `toggled` signal handler with re-entrance protection
   - `set_active()` method allows programmatic state changes

2. **Panel Loaders** (`src/shypn/helpers/*_panel_loader.py`)
   - Each panel has `show_in_stack()` and `hide_in_stack()` methods
   - Panels can be "hanged" (attached) or "floating" (detached)
   - Float/attach callbacks manage paned position without triggering recursion

3. **Toggle Handlers** (`src/shypn.py`)
   - Each `on_*_toggle(is_active)` handler implements exclusion logic
   - When activated: deactivates all other buttons using `palette.set_active(other, False)`
   - When deactivated: hides panel and collapses paned to 0

### Exclusion Logic Flow
```
User clicks "Pathways" button
  ↓
on_pathway_toggle(True) called
  ↓
Deactivate other buttons:
  palette.set_active('files', False)      → on_left_toggle(False) → hide Files panel
  palette.set_active('analyses', False)   → on_right_toggle(False) → hide Analyses panel
  palette.set_active('topology', False)   → on_topology_toggle(False) → hide Topology panel
  palette.set_active('report', False)     → on_report_toggle(False) → hide Report panel
  ↓
Show Pathways panel:
  pathway_panel_loader.show_in_stack()
  left_paned.set_position(270)  # Expand to show panel
```

### Re-entrance Protection
The `MasterPalette` class uses a per-button `_in_handler` flag to prevent infinite recursion:

```python
def protected_callback(active):
    if self._in_handler.get(category, False):
        # Already in this button's handler - don't trigger nested calls
        return
    
    self._in_handler[category] = True
    try:
        callback(active)
    finally:
        self._in_handler[category] = False
```

This allows:
- ✅ Button A's handler to deactivate Button B (different handler)
- ✅ Button A's handler to be called with `False` (different state)
- ❌ Button A's handler to reactivate Button A (same button, prevents recursion)

## Wayland Safety

### Critical Rules Followed
1. **No circular `master_palette.set_active()` calls from float/attach callbacks**
   - Float/attach callbacks only manage paned position
   - They do NOT call `master_palette.set_active()` to avoid recursion

2. **Panel state changes during toggle handlers**
   - Toggle handlers call `show_in_stack()` / `hide_in_stack()`
   - These methods manage panel visibility without creating new surfaces

3. **GtkStack visibility management**
   - Stack is shown when any panel becomes active
   - Stack is hidden when last panel is deactivated
   - This avoids Wayland Error 71 from rapid show/hide cycles

## Testing

### Unit Tests
**File:** `test_palette_exclusion.py`
- Verifies Master Palette button exclusion logic in isolation
- Tests activation, deactivation, and state transitions
- All tests pass ✅

### Integration Tests
**File:** `test_master_palette_integration.py`
- Tests Master Palette with real panel loaders
- Verifies panel visibility matches button state
- Tests rapid toggling (stress test)
- All tests pass ✅

### Manual Testing Checklist
- [x] Click Files button → Files panel appears, others hidden
- [x] Click Pathways button → Pathways panel appears, Files hidden
- [x] Click Analyses button → Analyses panel appears, Pathways hidden
- [x] Click Topology button → Topology panel appears, Analyses hidden
- [x] Click Report button → Report panel appears, Topology hidden
- [x] Click active button again → Panel hides, no panel visible
- [x] Rapid clicking between buttons → No Wayland errors
- [x] Float/detach Pathways → Panel becomes floating window
- [x] Reattach Pathways → Panel docks back to stack
- [x] Click different button while floating → Floating panel closes, new panel appears

## Related Commits

### Working Implementation
- `9f72dd2` - "Restore master palette button exclusivity"
  - Original working implementation after multi-panel floating was removed

### Recent Refactoring
- `344d4f8` - "refactor: Move Pathway panel header into panel class"
  - Moved float button from loader to panel (broke callback wiring)
- `bf5301e` - "fix: Pathway panel float/detach properly moves content"
  - Fixed panel content movement but didn't restore callback wiring

### This Fix
- Restores pathway panel float/attach callback wiring
- Maintains Wayland safety (no circular calls)
- Preserves button exclusion logic from commit `9f72dd2`

## Verification
```bash
# Run unit tests
python test_palette_exclusion.py

# Run integration tests
python test_master_palette_integration.py

# Run full application
python src/shypn.py
# Click Master Palette buttons: Files → Pathways → Analyses → Topology → Report
# Verify only one panel is visible at a time
# Verify no Wayland Error 71 appears in console
```

## Summary
The Master Palette button exclusion logic was working correctly at the core level. The issue was simply missing callback wiring for the Pathway panel after recent refactoring. By adding the float/attach callbacks (matching the pattern used for Files, Analyses, and Topology panels), the exclusion behavior is now fully restored while maintaining Wayland safety.
