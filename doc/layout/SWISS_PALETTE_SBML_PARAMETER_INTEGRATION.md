# Swiss Palette - SBML Parameter Integration

## Overview

The Swiss Palette Layout tools now read layout parameters from the SBML Import Options panel. This ensures consistent behavior whether you:
1. Import with layout (SBML tab → Parse → Import)
2. Apply layout post-import (Swiss Palette → Layout → Force-Directed)

## Test Flow

### Workflow 1: Import with Parameters
```
SBML Tab
  → Set Force-Directed parameters (iterations=800, k=2.0, scale=3000)
  → Fetch BIOMD0000000061
  → Parse
  → Import to Canvas
  ✓ Pathway appears with user-specified parameters
```

### Workflow 2: Swiss Palette with Parameters
```
SBML Tab
  → Set Force-Directed parameters (iterations=800, k=2.0, scale=3000)
  → Fetch BIOMD0000000061
  → Parse (loads to canvas with arbitrary positions)
Swiss Palette
  → Layout → Force-Directed
  ✓ Layout engine reads parameters from SBML tab
  ✓ Same parameters applied as import would use
```

## Implementation Details

### Parameter Flow

```
1. User sets parameters in SBML Import Options
   ↓
2. Parameters stored in UI spin buttons:
   - sbml_iterations_spin
   - sbml_k_factor_spin
   - sbml_canvas_scale_spin
   ↓
3. SBMLImportPanel.get_layout_parameters_for_algorithm()
   Reads values from spin buttons
   Returns dict: {iterations: 800, k_multiplier: 2.0, scale: 3000}
   ↓
4. ModelCanvasLoader._apply_specific_layout()
   Checks if sbml_panel exists
   Calls sbml_panel.get_layout_parameters_for_algorithm('force_directed')
   Passes parameters to LayoutEngine.apply_layout()
   ↓
5. LayoutEngine.apply_layout(algorithm='force_directed', **params)
   Passes parameters to ForceDirectedLayout.compute()
   ↓
6. ForceDirectedLayout.compute(iterations=800, k_multiplier=2.0, scale=3000)
   Uses user parameters for physics simulation
```

### Code Changes

**1. SBMLImportPanel (sbml_import_panel.py)**
```python
def get_layout_parameters_for_algorithm(self, algorithm: str) -> dict:
    """Get layout parameters from UI for the specified algorithm."""
    params = {}
    
    if algorithm == 'force_directed':
        if self.sbml_iterations_spin:
            params['iterations'] = int(self.sbml_iterations_spin.get_value())
        if self.sbml_k_factor_spin:
            params['k_multiplier'] = self.sbml_k_factor_spin.get_value()
        if self.sbml_canvas_scale_spin:
            params['scale'] = self.sbml_canvas_scale_spin.get_value()
    
    return params
```

**2. PathwayPanelLoader (pathway_panel_loader.py)**
```python
def set_model_canvas(self, model_canvas):
    """Wire SBML panel to model canvas."""
    # ... existing code ...
    
    # Wire SBML panel so Swiss Palette can read parameters
    if model_canvas and self.sbml_import_controller:
        model_canvas.sbml_panel = self.sbml_import_controller
```

**3. ModelCanvasLoader (model_canvas_loader.py)**
```python
def _apply_specific_layout(self, manager, drawing_area, algorithm, algorithm_name):
    """Apply layout with parameters from SBML panel if available."""
    
    # Try to get layout parameters from SBML Import panel
    layout_params = {}
    if hasattr(self, 'sbml_panel') and self.sbml_panel:
        layout_params = self.sbml_panel.get_layout_parameters_for_algorithm(algorithm)
        if layout_params:
            print(f"🎛️ Using SBML Import Options parameters: {layout_params}")
    
    # Apply layout with parameters
    engine = LayoutEngine(manager)
    result = engine.apply_layout(algorithm, **layout_params)
```

**4. ForceDirectedLayout (force_directed.py)**
```python
def compute(self, graph, iterations=500, k=None, k_multiplier=1.5, scale=2000.0, **kwargs):
    """Accept k_multiplier parameter from SBML panel."""
    
    if k is None:
        # Calculate k using multiplier
        area = scale * scale
        k = math.sqrt(area / graph.number_of_nodes()) * k_multiplier
```

## Testing

### Test Case 1: Force-Directed with Custom Parameters

**Setup:**
1. Launch shypn
2. Open Pathway Panel → SBML tab
3. Expand "Import Options"
4. Select "Force-Directed (Physics-based)"
5. Set parameters:
   - Iterations: 800
   - Optimal distance (k): 2.5
   - Canvas scale: 3500

**Test A: Import Flow**
1. Fetch BIOMD0000000061
2. Parse
3. Import to Canvas
4. Check console for: "Physics params: k_multiplier=2.5, scale=3500px, iterations=800"
5. Verify layout is spacious (high k causes more spread)

**Test B: Swiss Palette Flow**
1. Fetch BIOMD0000000061
2. Parse (quick load with arbitrary positions)
3. Swiss Palette → Layout → Force-Directed
4. Check console for:
   - "🎛️ Using SBML Import Options parameters: {'iterations': 800, 'k_multiplier': 2.5, 'scale': 3500.0}"
   - "Auto k = XXX.X (scale=3500, nodes=25, multiplier=2.5)"
5. Verify layout matches Test A (same parameters applied)

### Test Case 2: Hierarchical with Custom Parameters

**Setup:**
1. Open Pathway Panel → SBML tab
2. Select "Hierarchical (Layered)"
3. Set parameters:
   - Layer spacing: 200
   - Node spacing: 150

**Test A: Import Flow**
1. Fetch BIOMD0000000061
2. Import to Canvas
3. Verify spacious layered layout

**Test B: Swiss Palette Flow**
1. Fetch BIOMD0000000061
2. Parse
3. Swiss Palette → Layout → Hierarchical
4. Check console for: "Using SBML Import Options parameters: {'layer_spacing': 200.0, 'node_spacing': 150.0}"
5. Verify layout matches Test A

### Test Case 3: Parameter Changes Between Layouts

**Flow:**
1. Set Force-Directed: iterations=200, k=1.0, scale=1000
2. Fetch → Parse
3. Swiss Palette → Layout → Force
4. Observe compact layout
5. **Change SBML parameters**: iterations=800, k=3.0, scale=4000
6. Swiss Palette → Layout → Force (again)
7. Observe spacious layout
8. Check console shows new parameters used

**Expected Result:**
- First layout: Compact (k=1.0, scale=1000)
- Second layout: Very spacious (k=3.0, scale=4000)
- Console shows different parameters for each run

### Test Case 4: Default Behavior (No SBML Panel)

**Setup:**
1. Create minimal test that doesn't load Pathway Panel
2. Apply Swiss Palette layout

**Expected:**
- ModelCanvasLoader._apply_specific_layout() catches exception
- Falls back to LayoutEngine default parameters
- Layout still works, just with defaults

### Test Case 5: Multi-Tab Consistency

**Flow:**
1. Set SBML parameters: Force-Directed, iterations=1000
2. Import pathway A to Tab 1
3. Import pathway B to Tab 2
4. Switch to Tab 1, apply Swiss Palette Force
5. Switch to Tab 2, apply Swiss Palette Force

**Expected:**
- Both tabs use iterations=1000
- SBML parameters are global (same for all tabs)
- Console shows same parameters for both applications

## Console Output Examples

### Successful Parameter Integration
```
🎛️ Using SBML Import Options parameters: {'iterations': 800, 'k_multiplier': 2.5, 'scale': 3500.0}
🔬 Force-directed: Input graph type = DiGraph
🔬 Force-directed: Is DiGraph? True
🔬 Force-directed: ✓ Converted DiGraph → Graph for universal repulsion
🔬 Force-directed: Output graph type = Graph
🔬 Force-directed: 12 places, 13 transitions
🔬 Force-directed: 50 edges (springs)
🔬 Force-directed: Auto k = 442.7 (scale=3500, nodes=25, multiplier=2.5)
🔬 Force-directed: Using arc weights as spring strength
```

### Fallback to Defaults
```
Note: Could not get layout parameters from SBML panel: 'ModelCanvasLoader' object has no attribute 'sbml_panel'
🔬 Force-directed: Auto k = 187.1 (scale=2000, nodes=25, multiplier=1.5)
```

## Benefits

1. **Consistency:** Same parameters whether importing or post-layout
2. **Flexibility:** Users can tweak parameters and re-apply layout
3. **Discoverability:** Parameters in SBML tab affect Swiss Palette
4. **Testing:** Easy to test different parameter combinations
5. **Workflow:** Fits natural workflow (set params → import/layout)

## Known Limitations

1. **Global Parameters:** SBML parameters apply to all tabs (not per-canvas)
2. **No Live Update:** Must re-apply layout to see parameter changes
3. **Fallback Mode:** If SBML panel not loaded, uses defaults silently

## Future Enhancements

1. **Per-Canvas Parameters:** Store parameters per canvas tab
2. **Parameter Dialog:** Right-click layout tool → "Parameters..." dialog
3. **Presets:** Add "Compact/Balanced/Spacious" preset buttons
4. **Live Preview:** Show layout preview before applying
5. **History:** Remember last-used parameters per algorithm

## Troubleshooting

### Problem: Swiss Palette not using SBML parameters

**Symptom:** Console doesn't show "Using SBML Import Options parameters"

**Causes:**
1. sbml_panel not wired to model_canvas_loader
2. PathwayPanelLoader.set_model_canvas() not called
3. SBML panel widgets not initialized

**Debug:**
```python
# Add to _apply_specific_layout:
print(f"Has sbml_panel? {hasattr(self, 'sbml_panel')}")
if hasattr(self, 'sbml_panel'):
    print(f"sbml_panel value: {self.sbml_panel}")
    if self.sbml_panel:
        params = self.sbml_panel.get_layout_parameters_for_algorithm(algorithm)
        print(f"Got parameters: {params}")
```

### Problem: Parameters not changing layout

**Symptom:** Layout looks same regardless of parameter values

**Causes:**
1. Parameters not passed to algorithm
2. Algorithm using hardcoded defaults
3. k_multiplier vs k confusion

**Debug:**
```python
# Check ForceDirectedLayout.compute:
print(f"Received parameters: iterations={iterations}, k_multiplier={k_multiplier}, scale={scale}")
print(f"Calculated k={k}")
```

### Problem: Wrong algorithm getting parameters

**Symptom:** Force-Directed parameters applied to Hierarchical

**Cause:** Algorithm name mismatch ('force_directed' vs 'force-directed')

**Fix:** Check algorithm names are consistent:
- Swiss Palette calls: 'force_directed'
- SBML panel expects: 'force_directed'
- Both use underscore, not hyphen

## Documentation References

- `doc/SBML_LAYOUT_PARAMETERS.md` - UI parameter details
- `doc/UI_LAYOUT_STRUCTURE.md` - UI widget structure
- `src/shypn/edit/graph_layout/force_directed.py` - Algorithm implementation
- `src/shypn/helpers/sbml_import_panel.py` - Parameter reading
- `src/shypn/helpers/model_canvas_loader.py` - Parameter application
