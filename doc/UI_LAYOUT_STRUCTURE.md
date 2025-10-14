# SBML Import Options UI Structure

## Location
**Pathway Panel → SBML Tab → Import Options (Expander)**

## UI Hierarchy

```
SBML Tab
├── SBML Source
│   ├── Radio: Local File / BioModels Database
│   ├── File entry + Browse button (Local mode)
│   └── BioModels ID entry + Fetch button (BioModels mode)
│
├── Import Options (Expander) ← PARAMETERS ARE HERE
│   │
│   ├── Layout Algorithm: (ComboBox)
│   │   ├── Auto (Automatic Selection)
│   │   ├── Hierarchical (Layered)
│   │   └── Force-Directed (Physics-based)
│   │
│   ├── [Auto Parameters Box] (visible when Auto selected)
│   │   └── Info: "Automatic algorithm selection based on graph topology"
│   │
│   ├── [Hierarchical Parameters Box] (visible when Hierarchical selected)
│   │   ├── Layer spacing: [150] px (50-500)
│   │   └── Node spacing: [100] px (50-300)
│   │
│   ├── [Force-Directed Parameters Box] (visible when Force-Directed selected)
│   │   ├── Iterations: [500] (50-1000)
│   │   ├── Optimal distance (k): [1.5] (0.5-3.0)
│   │   └── Canvas scale: [2000] px (500-5000)
│   │
│   ├── ─────────── (separator)
│   │
│   ├── Token Conversion:
│   │   ├── Scale factor: [1.0] (0.1-10.0)
│   │   └── Example: 5 mM glucose → 5 tokens
│   │
│   └── ☐ Enrich with external data (Disabled)
│
├── Pathway Information (Preview)
│   └── [Text view showing pathway details after parsing]
│
├── Status Label
│   └── [Status messages]
│
└── Action Buttons
    ├── [Parse File]
    └── [Import to Canvas]
```

## Dynamic Behavior

### Algorithm Selection (ComboBox)
When user changes the combo box, only the relevant parameter box is shown:

- **Index 0 (Auto):** Shows `sbml_auto_params_box` (info text only)
- **Index 1 (Hierarchical):** Shows `sbml_hierarchical_params_box` (layer/node spacing)
- **Index 2 (Force-Directed):** Shows `sbml_force_params_box` (iterations/k/scale)

### Handler
```python
def _on_layout_algorithm_changed(self, combo):
    active_index = combo.get_active()
    
    # Hide all
    self.sbml_auto_params_box.set_visible(False)
    self.sbml_hierarchical_params_box.set_visible(False)
    self.sbml_force_params_box.set_visible(False)
    
    # Show selected
    if active_index == 0:
        self.sbml_auto_params_box.set_visible(True)
    elif active_index == 1:
        self.sbml_hierarchical_params_box.set_visible(True)
    elif active_index == 2:
        self.sbml_force_params_box.set_visible(True)
```

## User Workflow

### Example 1: Use Auto Layout (No parameter tuning)
1. Open Pathway Panel → SBML tab
2. Fetch or browse SBML file
3. **Import Options** expander is already expanded by default
4. Leave "Layout Algorithm" at **Auto** (default)
5. Parse → Import to Canvas
6. System automatically chooses best algorithm

### Example 2: Fine-tune Hierarchical Layout
1. Open Pathway Panel → SBML tab
2. Fetch BIOMD0000000061
3. In **Import Options**, select "Hierarchical (Layered)"
4. Adjust parameters:
   - Layer spacing: 200 px (more vertical space)
   - Node spacing: 150 px (more horizontal space)
5. Parse → Import to Canvas
6. Pathway appears with custom spacing

### Example 3: Fine-tune Force-Directed Layout
1. Open Pathway Panel → SBML tab
2. Fetch complex pathway (e.g., BIOMD0000000012)
3. In **Import Options**, select "Force-Directed (Physics-based)"
4. Adjust parameters:
   - Iterations: 800 (better convergence)
   - Optimal distance (k): 2.0 (more spread)
   - Canvas scale: 3000 (larger canvas)
5. Parse → Import to Canvas
6. Pathway appears with physics-based layout

## Widget IDs

### Container Widgets
- `sbml_options_expander` - Main expander for all import options
- `sbml_auto_params_box` - Container for Auto mode info
- `sbml_hierarchical_params_box` - Container for Hierarchical parameters
- `sbml_force_params_box` - Container for Force-Directed parameters

### Control Widgets
- `sbml_layout_algorithm_combo` - Algorithm selector (ComboBoxText)
- `sbml_layer_spacing_spin` - Hierarchical: layer spacing (SpinButton)
- `sbml_node_spacing_spin` - Hierarchical: node spacing (SpinButton)
- `sbml_iterations_spin` - Force-Directed: iterations (SpinButton)
- `sbml_k_factor_spin` - Force-Directed: k multiplier (SpinButton)
- `sbml_canvas_scale_spin` - Force-Directed: canvas scale (SpinButton)
- `sbml_scale_spin` - Token conversion scale factor (SpinButton)
- `sbml_scale_example` - Token conversion example label (Label)

### Adjustment Objects
- `sbml_layer_spacing_adjustment` - Range: 50-500, default: 150
- `sbml_node_spacing_adjustment` - Range: 50-300, default: 100
- `sbml_iterations_adjustment` - Range: 50-1000, default: 500
- `sbml_k_factor_adjustment` - Range: 0.5-3.0, default: 1.5
- `sbml_canvas_scale_adjustment` - Range: 500-5000, default: 2000
- `sbml_scale_adjustment` - Range: 0.1-10.0, default: 1.0

## Implementation Status

✅ **UI Structure:** Complete
- All widgets defined in `pathway_panel.ui`
- Proper nesting inside `sbml_options_expander`
- Dynamic visibility logic implemented

✅ **Backend Integration:** Complete
- `SBMLImportPanel._get_widgets()` - References all new widgets
- `SBMLImportPanel._connect_signals()` - Connects algorithm combo changed signal
- `SBMLImportPanel._on_layout_algorithm_changed()` - Handles dynamic visibility
- `SBMLImportPanel._import_pathway_background()` - Reads parameters and passes to processor

✅ **Processing Pipeline:** Complete
- `PathwayPostProcessor` accepts `layout_type` and `layout_params`
- `LayoutProcessor` respects user-selected algorithm
- `_calculate_force_directed_layout()` uses user parameters
- Hierarchical layout uses layer/node spacing from params

## Testing Checklist

- [ ] Open SBML tab, verify Import Options expander is visible
- [ ] Verify Layout Algorithm combo has 3 options
- [ ] Select "Auto" → verify info text appears
- [ ] Select "Hierarchical" → verify layer/node spacing controls appear
- [ ] Select "Force-Directed" → verify iterations/k/scale controls appear
- [ ] Adjust Hierarchical spacing values → verify spin buttons work
- [ ] Adjust Force-Directed parameters → verify spin buttons work
- [ ] Fetch BIOMD0000000061 with Auto → verify import works
- [ ] Fetch BIOMD0000000061 with Hierarchical (custom spacing) → verify spacing applied
- [ ] Fetch BIOMD0000000061 with Force-Directed (custom params) → verify parameters applied
- [ ] Check console for parameter logging during import

## Screenshot Mockup

```
┌─────────────────────────────────────────────────────────┐
│ Pathway Operations                                       │
├─────────────────────────────────────────────────────────┤
│ [Import] [Browse] [SBML▼] [History]                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ SBML Source                                             │
│ ⦿ Local File  ○ BioModels Database                     │
│ [/path/to/file.xml                    ] [Browse...]     │
│ ℹ Browse for a local SBML file (.sbml or .xml)         │
│                                                          │
│ ▼ Import Options                                        │
│ │                                                        │
│ │ Layout Algorithm:                                     │
│ │ [Force-Directed (Physics-based)        ▼]            │
│ │                                                        │
│ │     Iterations:            [500  ]                    │
│ │     Optimal distance (k):  [1.5  ]                    │
│ │     Canvas scale:          [2000 ]                    │
│ │                                                        │
│ │ ─────────────────────────────────────────────────     │
│ │                                                        │
│ │ Token Conversion:                                     │
│ │ Scale factor: [1.0  ]    (1 mM → X tokens)           │
│ │     Example: 5 mM glucose → 5 tokens                 │
│ │                                                        │
│ │ ☐ Enrich with external data (Disabled)               │
│ │                                                        │
│ └─────────────────────────────────────────────────      │
│                                                          │
│ Pathway Information                                     │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Pathway: Glycolysis / Gluconeogenesis            │   │
│ │                                                   │   │
│ │ Species: 25                                       │   │
│ │   cytosol: 20 species                            │   │
│ │     • Glucose (5.0 mM)                           │   │
│ │     • ATP (2.5 mM)                               │   │
│ │     ... and 18 more                              │   │
│ │                                                   │   │
│ │ Reactions: 13                                     │   │
│ │   • Hexokinase (mass_action)                     │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ✓ Parsed and validated successfully                     │
│                                                          │
│                              [Parse File] [Import▶]     │
│                                                          │
│ ℹ Import biochemical pathways from SBML files...        │
└─────────────────────────────────────────────────────────┘
```

## Summary

✅ **Layout parameters are correctly placed under "Import Options" expander**
✅ **Three algorithm choices with dynamic parameter visibility**
✅ **All parameters have proper tooltips and sensible ranges**
✅ **Backend fully integrated with processing pipeline**
✅ **User can control layout behavior before importing**

The implementation is complete and follows the requested structure!
