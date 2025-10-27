# Data Collector Wiring Bug Fix

## Problem Summary
Transitions selected for plotting were not appearing in the Analysis Panel plot. The plot canvas showed "No transition selected" despite transitions being added via context menu "Add to Analysis".

## Root Cause
The data_collector was never being wired to the right panel because of **incorrect attribute access**:

### WRONG (broken commits fb0605d - 6655e60):
```python
swissknife.widget_palette_instances.get('simulate')
```

### CORRECT (working commit 546478d, now restored):
```python
swissknife.registry.get_widget_palette_instance('simulate')
```

## Architecture
```
SwissKnifePalette
└── registry (SubPaletteRegistry)
    └── widget_palette_instances = {'simulate': SimulateToolsPaletteLoader, ...}
    └── get_widget_palette_instance(cat_id) → returns widget_palette_instances[cat_id]
```

The attribute `widget_palette_instances` exists on **registry**, not on **swissknife** directly.

## Bug Impact
- **Symptom**: plot_panel.py `_periodic_update()` skipped with "No data collector" message
- **Result**: No plots rendered despite transitions being selected
- **Duration**: Introduced in commits after 546478d (~10 hours ago), fixed in commit 7ea4d1c

## Files Modified
- `src/shypn/helpers/model_canvas_loader.py` (2 locations)
  - Line ~229: `_on_notebook_page_changed()` - wires data_collector on tab switches
  - Line ~818: `_setup_edit_palettes()` - wires data_collector on initial palette creation

## Verification Test
```python
class Registry:
    def __init__(self):
        self.widget_palette_instances = {'simulate': 'SimulateTools'}
    def get_widget_palette_instance(self, key):
        return self.widget_palette_instances.get(key)

class Swiss:
    def __init__(self):
        self.registry = Registry()

s = Swiss()

# WRONG - AttributeError: 'Swiss' object has no attribute 'widget_palette_instances'
s.widget_palette_instances.get('simulate')  # FAILS

# CORRECT - Returns 'SimulateTools'
s.registry.get_widget_palette_instance('simulate')  # WORKS
```

## Fix Commit
- **Commit**: 7ea4d1c
- **Branch**: main
- **Message**: "Fix: Correct data_collector wiring - access via registry, not swissknife directly"

## Related Commits
- **546478d** (10+ hours ago): Last working version before bug
- **fb0605d** (84 min ago): Scientific compliance fix (mass action → stochastic)
- **5361bad - 6655e60** (23-56 min ago): Multiple failed attempts on Default-Tab-Health branch

## Lessons Learned
1. **Attribute access pattern matters**: Direct attribute access (`obj.attr`) vs. method access (`obj.method()`)
2. **Test after refactoring**: The widget_palette_instances change broke existing wiring code
3. **Git archaeology helps**: Comparing working commit (546478d) to broken commits revealed the issue
4. **Rollback when lost**: User correctly requested rollback to main after 1 hour of failed fixes

## Testing Recommendations
After this fix:
1. Launch application
2. Open or create a Petri Net model
3. Add a transition via context menu "Add to Analysis"
4. Verify transition appears in plot panel with colored line
5. Run simulation and verify plot updates in real-time
