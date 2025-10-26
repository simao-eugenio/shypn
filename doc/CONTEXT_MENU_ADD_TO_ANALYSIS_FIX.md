# Context Menu "Add to Analysis" Restoration

## Issue

The "Add to Analysis" option disappeared from the netobjects (Place/Transition) context menus.

## Root Cause

The `context_menu_handler` was only being created when `data_collector` was provided during initialization. However, in the main application (`shypn.py`), the right panel is created without a `data_collector`:

```python
right_panel_loader = create_right_panel()  # No data_collector!
```

The `data_collector` is only set later when tabs are switched (from `model_canvas_loader.py`). This meant:

1. Right panel loads without data_collector
2. Plotting panels are not created
3. Context menu handler is not created
4. `model_canvas_loader.set_context_menu_handler()` never gets called (because handler is None)
5. Context menu items are never added to object menus

## Solution

Modified `right_panel_loader.py` to create the `context_menu_handler` early, even when panels don't exist yet:

### Change 1: Create handler immediately (line ~94)
```python
# Initialize plotting panels if data_collector is available
if self.data_collector is not None:
    self._setup_plotting_panels()
else:
    # Create context menu handler even without data_collector
    # It will be configured with panels later when data_collector is set
    from shypn.analyses import ContextMenuHandler
    self.context_menu_handler = ContextMenuHandler(
        place_panel=None,
        transition_panel=None,
        model=self.model,
        diagnostics_panel=None
    )
```

### Change 2: Update handler instead of creating new one (line ~247)
```python
# Update existing context menu handler with the new panels
if self.context_menu_handler and self.place_panel and self.transition_panel:
    self.context_menu_handler.set_panels(self.place_panel, self.transition_panel)
    # Update diagnostics panel reference
    if self.diagnostics_panel:
        self.context_menu_handler.diagnostics_panel = self.diagnostics_panel
```

## How It Works Now

1. **Application starts** → `create_right_panel()` called without data_collector
2. **Right panel loads** → Creates `context_menu_handler` immediately (with None panels)
3. **Main app wires** → `model_canvas_loader.set_context_menu_handler()` succeeds (handler exists!)
4. **First tab switch** → `set_data_collector()` called → Panels created → Handler updated with panels
5. **Context menu shown** → Handler.add_analysis_menu_items() adds "Add to Analysis" options

## Verification

Test script: `test_context_menu_handler.py`

```
✅ context_menu_handler exists immediately (even without data_collector)
✅ Panels created when data_collector is set
✅ context_menu_handler updated with panels
```

## Result

- ✅ "Add to Analysis" option now appears in Place context menus
- ✅ "Add to Analysis" option now appears in Transition context menus
- ✅ Right-click → Add to Analysis → Object appears in plotting panel
- ✅ Works for both places and transitions
- ✅ Locality detection works for transitions (auto-adds connected places)

## Files Modified

- `src/shypn/helpers/right_panel_loader.py` (2 changes)
  - Line ~94: Create handler early in `load()` method
  - Line ~247: Update handler in `set_data_collector()` method

## Testing

1. Start application
2. Create or load a model with places and transitions
3. Right-click on a place → Should see "Add to Place Analysis"
4. Right-click on a transition → Should see "Add to Transition Analysis"
5. Click menu item → Object should appear in right panel plotting area
