# Viability Panel Integration Test

## Test 1: Context Menu "Add to Viability"

1. Start the app:
   ```bash
   cd /home/simao/projetos/shypn && python src/shypn.py
   ```

2. Load a model (or create a simple one with a few places and transitions)

3. Right-click on a **place**:
   - Should see "Add to Viability Analysis" menu item
   - Click it → Biological category in Viability panel should expand

4. Right-click on a **transition**:
   - Should see "Add to Viability Analysis" menu item
   - Click it → Structural and Kinetic categories should expand

## Test 2: Locality Search in Diagnosis Category

1. In the Viability panel, expand the **Diagnosis** category

2. Check the "Locality" dropdown:
   - Should show transitions from the model (not "(No localities available)")
   - Should be enabled (not grayed out)

3. Select a locality from the dropdown:
   - Console should show: `[DiagnosisCategory] Selected locality: {transition_id}`

4. Run diagnosis scan:
   - Should filter results to selected locality

## Expected Debug Output

When right-clicking on objects:
```
[ContextMenuHandler] _get_current_viability_panel called
[ContextMenuHandler] model_canvas_loader: <ModelCanvasLoader object>
[ContextMenuHandler] drawing_area: <DrawingArea object>
[ContextMenuHandler] overlay_manager: <OverlayManager object>
[ContextMenuHandler] viability_loader: <ViabilityPanelLoader object>
[ContextMenuHandler] Found per-document panel: <ViabilityPanel object>
[ContextMenuHandler] Context menu for <Place/Transition>, viability_panel: <ViabilityPanel object>
```

When expanding Diagnosis category:
```
[DiagnosisCategory] _populate_localities called
[DiagnosisCategory] KB has X transitions
[DiagnosisCategory] Added locality for transition: t1
[DiagnosisCategory] Added locality for transition: t2
[DiagnosisCategory] Found localities, enabling dropdown
```

When selecting a locality:
```
[DiagnosisCategory] Selected locality: {transition_id}
```
