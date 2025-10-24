# Canvas Wiring - Quick Reference

## Summary
All 7 canvas creation scenarios now properly wire data_collector to Dynamic Analyses Panel.

## Implementation (3 changes)

### 1. Always Create Panels
**File:** `src/shypn/helpers/right_panel_loader.py:94`
```python
self._setup_plotting_panels()  # No condition check
```

### 2. Unified Registry Path
**Files:** `model_canvas_loader.py` (2 locations)
```python
simulate_tools_palette = swissknife.registry.get_widget_palette_instance('simulate')
```

### 3. Retroactive Wiring
**File:** `src/shypn.py:378`
```python
model_canvas_loader.wire_existing_canvases_to_right_panel()
```

## Test Command
```bash
python3 tests/canvas_state/test_canvas_wiring_manual.py
```

## Verify Working
1. Launch app
2. Create P-T-P on startup canvas
3. Right-click transition → "Add to Analysis"
4. Go to Dynamic Analyses panel
5. Click "Simulate"
6. ✅ Plot should appear

## All Scenarios
1. ✅ Startup canvas
2. ✅ File → New
3. ✅ File → Open
4. ✅ File Explorer double-click
5. ✅ Import SBML
6. ✅ Import KEGG
7. ✅ Tab switching

## Files Modified
- `src/shypn.py`
- `src/shypn/helpers/model_canvas_loader.py`
- `src/shypn/helpers/right_panel_loader.py`
- `src/shypn/analyses/{plot_panel,transition_rate_panel,place_rate_panel}.py`

## Documentation
- **Full Guide:** `doc/canvas_state/CANVAS_WIRING_ALL_SCENARIOS.md`
- **Investigation:** `doc/canvas_state/ANALYSES_PANEL_WIRING_STATUS.md`
- **Tests:** `tests/canvas_state/test_canvas_wiring_manual.py`
