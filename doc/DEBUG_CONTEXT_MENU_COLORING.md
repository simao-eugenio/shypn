# Debug Context Menu "Add to Transition Analysis" - Coloring Issue

## Problem Description
User reports that "Add to Transition Analysis" context menu is not working, and the coloring schema for selected objects is also not working.

## Debug Logging Added

### 1. Context Menu Handler (`context_menu_handler.py`)
- `[CTX_MENU]` logs show locality detection and menu creation
- `_add_transition_locality_submenu()`:
  - Logs when locality detector is created
  - Warns if model is None
  - Logs locality validity and place counts
  - Logs whether adding transition only or transition+locality

- `_add_transition_with_locality()`:
  - Logs when called with transition ID and locality validity
  - Logs when transition is added to panel
  - Logs when `add_locality_places()` is called
  - Warns if panel is missing the method

### 2. Transition Rate Panel (`transition_rate_panel.py`)
- `[COLOR]` logs show color assignment for transitions
- `add_object()`:
  - Logs index and color_hex being assigned
  - Logs RGB color values set on border_color and fill_color
  - Logs when on_changed callback is called (or warns if missing)
  - Logs when mark_needs_redraw() is called (or warns if no model_manager)

- `[LOCALITY]` logs show locality place addition
- `add_locality_places()`:
  - Logs when called with transition ID and locality validity
  - Warns if locality is invalid
  - Logs stored locality information
  - Logs transition color
  - Logs when adding places to PlaceRatePanel
  - Logs each individual place being added (input/output)
  - Warns if _place_panel is None

### 3. Place Rate Panel (`plot_panel.py`)
- `[COLOR_PLACE]` logs show color assignment for places
- `add_object()`:
  - Logs index and color_hex being assigned
  - Logs RGB color set on border_color
  - Logs when on_changed callback is called (or warns if missing)
  - Logs when mark_needs_redraw() is called (or warns if no model_manager)

### 4. Dynamic Analyses Panel (`dynamic_analyses_panel.py`)
- `[DYNAMIC_ANALYSES]` logs show context menu handler setup
- `_setup_context_menu()`:
  - Logs whether place_panel and transition_panel are available
  - Logs when place_panel is set on transitions_category
  - Logs when creating new ContextMenuHandler with model
  - Logs whether locality_detector was created

## Expected Log Flow (When Working Correctly)

### On Canvas Load/Tab Switch:
```
[DYNAMIC_ANALYSES] _setup_context_menu: place_panel=True, transition_panel=True
[DYNAMIC_ANALYSES] Set place_panel on transitions_category
[DYNAMIC_ANALYSES] Creating new ContextMenuHandler with model=True
[DYNAMIC_ANALYSES] ContextMenuHandler created, locality_detector=True
```

### On Right-Click Transition:
```
[CTX_MENU] Detecting locality for transition T1
[CTX_MENU] Locality valid=True, inputs=1, outputs=1
[CTX_MENU] Valid locality with 2 places - will add transition+locality
```

### On Click "Add to Transition Analysis":
```
[CTX_MENU] _add_transition_with_locality called: transition=T1, locality.is_valid=True, panel=TransitionRatePanel
[COLOR] add_object: transition=T1, index=0, color=#e74c3c
[COLOR] Set border_color=(0.906, 0.298, 0.235), fill_color=(0.906, 0.298, 0.235)
[COLOR] Calling on_changed callback
[COLOR] Calling mark_needs_redraw()
[CTX_MENU] Transition T1 added to panel
[CTX_MENU] Panel has add_locality_places method, calling it now...
[LOCALITY] add_locality_places called: transition=T1, locality.is_valid=True, place_panel=True
[LOCALITY] Stored locality: 1 inputs, 1 outputs
[LOCALITY] Transition color: (0.906, 0.298, 0.235)
[LOCALITY] Adding 1 input places and 1 output places to PlaceRatePanel
[LOCALITY] Adding input place P1 to place_panel
[COLOR_PLACE] add_object: obj=P1, index=0, color=#3498db
[COLOR_PLACE] Set border_color=(0.204, 0.596, 0.859) on Place P1
[COLOR_PLACE] Calling on_changed callback
[COLOR_PLACE] Calling mark_needs_redraw()
[LOCALITY] Adding output place P2 to place_panel
[COLOR_PLACE] add_object: obj=P2, index=1, color=#2ecc71
[COLOR_PLACE] Set border_color=(0.180, 0.800, 0.443) on Place P2
[COLOR_PLACE] Calling on_changed callback
[COLOR_PLACE] Calling mark_needs_redraw()
[LOCALITY] All places added to PlaceRatePanel
[CTX_MENU] panel.add_locality_places() completed successfully
```

## Potential Issues to Look For

### Issue 1: No Locality Detector
```
[CTX_MENU] No locality detector - model is None
```
**Cause**: Context menu handler created without model reference
**Fix**: Ensure `set_model()` is called on handler after model is available

### Issue 2: Invalid Locality
```
[CTX_MENU] Locality valid=False, inputs=0, outputs=0
[CTX_MENU] Invalid locality - adding transition only (no locality)
```
**Cause**: Transition has no connected places (isolated transition)
**Expected**: This is normal for isolated transitions

### Issue 3: No on_changed Callback
```
[COLOR] No on_changed callback for transition T1!
[COLOR_PLACE] No on_changed callback for Place P1!
```
**Cause**: Objects created without on_changed callback being set
**Fix**: Objects must be created via DocumentController which sets callbacks

### Issue 4: No Model Manager
```
[COLOR] No model_manager, cannot trigger redraw!
[COLOR_PLACE] No model_manager, cannot trigger redraw!
```
**Cause**: Panel created without model_manager reference
**Fix**: Ensure panel's `set_model()` is called with correct manager

### Issue 5: No Place Panel
```
[LOCALITY] _place_panel is None! Cannot add locality places to place panel
```
**Cause**: TransitionRatePanel doesn't have place_panel reference
**Fix**: Ensure `set_place_panel()` is called on transitions_category

### Issue 6: Panel Missing Method
```
[CTX_MENU] Panel missing add_locality_places method! Panel type: TransitionRatePanel
```
**Cause**: Wrong panel type or method deleted
**Fix**: Verify TransitionRatePanel has `add_locality_places()` method

## Testing Steps

1. **Clean Start**: Close and restart application
2. **Load Model**: Open a model with transitions that have connected places
3. **Check Logs**: Look for `[DYNAMIC_ANALYSES]` messages on startup
4. **Right-Click Transition**: Open context menu on a transition
5. **Check Logs**: Look for `[CTX_MENU]` messages showing locality detection
6. **Click "Add to Transition Analysis"**
7. **Check Logs**: Look for complete flow from `[CTX_MENU]` → `[COLOR]` → `[LOCALITY]` → `[COLOR_PLACE]`
8. **Verify Visual**: Transition and places should have colored borders on canvas
9. **Check Plot**: Transition and places should appear in right panel plots

## Expected Behavior

1. **Canvas**: Transition and locality places have colored borders (glow effect)
2. **Right Panel**: Transition appears in "Transitions" category with plot line
3. **Right Panel**: Locality places appear in "Places" category with plot lines
4. **UI List**: Transition and places listed in their respective panels

## Color Scheme
- Transitions: Colored borders + colored fill (e.g., red)
- Places: Colored borders only, no fill (hollow circle with colored outline)
- Arcs: Colored to match transition (if part of locality)

## Files Modified
1. `src/shypn/analyses/context_menu_handler.py` - Added `[CTX_MENU]` logging
2. `src/shypn/analyses/transition_rate_panel.py` - Added `[COLOR]` and `[LOCALITY]` logging
3. `src/shypn/analyses/plot_panel.py` - Added `[COLOR_PLACE]` logging
4. `src/shypn/ui/panels/dynamic_analyses/dynamic_analyses_panel.py` - Added `[DYNAMIC_ANALYSES]` logging
