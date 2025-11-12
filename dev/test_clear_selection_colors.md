# Test: Clear Selection Resets All Colors

## Test Procedure

1. **Start Shypn**
   ```bash
   cd /home/simao/projetos/shypn
   python src/shypn.py
   ```

2. **Import a pathway**
   - Open File → Import SBML
   - Select `hsa00010` or any pathway

3. **Add transition with locality to analysis**
   - Right-click on any transition with inputs/outputs
   - Select "Add to Transition Analyses"
   - **Expected**: Transition should be added with colored border
   - **Expected**: Locality places should have colored borders
   - **Expected**: Arcs connecting them should be colored

4. **Verify colors are applied**
   - Check transition has colored border (e.g., blue)
   - Check input places have colored borders (same color)
   - Check output places have colored borders (same color)
   - Check arcs (place→transition and transition→place) are colored

5. **Clear selection**
   - Click the "Clear" button in the Transition Analysis panel
   - **Expected**: Transition border returns to default (black)
   - **Expected**: Place borders return to default (black)
   - **Expected**: Arc colors return to default (black)
   - **Expected**: All colored objects are reset

## Debug Output to Check

Look for these messages in terminal:

### When adding transition:
```
[CONTEXT_MENU] Locality detection for T1: valid=True, places=4
[CONTEXT_MENU] Valid locality with 4 places, connecting to _add_transition_with_locality
[CONTEXT_MENU] _add_transition_with_locality() called for T1
[LOCALITY] add_locality_places() called for transition T1
[LOCALITY]   Input places: [P1, P2]
[LOCALITY]   Output places: [P3, P4]
[ARC_COLOR] Coloring locality arcs for transition T1 with color (0.12, 0.47, 0.71)
```

### When clearing:
```
[CLEAR] TransitionRatePanel._on_clear_clicked() called
[CLEAR] Resetting arc colors for transition T1
[CLEAR]   Reset input arc A1: P1 → T1
[CLEAR]   Reset input arc A2: P2 → T1
[CLEAR]   Reset output arc A3: T1 → P3
[CLEAR]   Reset output arc A4: T1 → P4
[CLEAR] Locality data cleared
[CLEAR] Parent clear completed
```

## Success Criteria

✅ Transition border color resets to default (black)
✅ Place border colors reset to default (black)  
✅ Arc colors reset to default (black)
✅ No colored objects remain after clear
✅ Debug output shows arc color resetting
✅ Canvas redraws with default colors

## Known Issues

- If places were added manually (not via locality), they won't be removed from PlaceRatePanel when clearing TransitionRatePanel
- This is expected behavior - only clears the TransitionRatePanel selection

## Implementation

Modified files:
- `src/shypn/analyses/transition_rate_panel.py`: Added `_on_clear_clicked()` override
  - Resets arc colors for all locality arcs
  - Clears locality data dictionary
  - Calls parent clear for transition/place color resets
