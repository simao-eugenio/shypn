# SBML Import Pipeline: OLD vs NEW

**Quick Reference Guide for Understanding the Refactoring**

---

## Side-by-Side Comparison

| Aspect | **OLD Pipeline** | **NEW Pipeline** |
|--------|------------------|------------------|
| **Complexity** | 5+ layout algorithms | 1 layout algorithm |
| **Lines of Code** | ~2000 lines | ~500 lines (75% reduction) |
| **Files** | 11 files | 7 files (4 removed) |
| **Layout Trigger** | Auto on Import button | User-initiated (Swiss Palette) |
| **Position Flow** | Parse → Layout → Project → Import | Parse → Import (arbitrary) → Layout |
| **Node IDs** | Numeric (collision risk) | Object references (collision-free) |
| **Arc Types** | Auto-curved | All straight |
| **Parameters** | Hardcoded in multiple places | Centralized in UI spinners |

---

## Workflow Comparison

### OLD: Auto-Layout on Import

```
User Action          │ System Behavior
─────────────────────┼──────────────────────────────────────────
Select SBML file     │ Store filepath
                     │
Click Parse          │ ├─ Parse SBML → PathwayData
                     │ ├─ Validate
                     │ └─ Show preview
                     │
Click Import         │ ├─ Post-process (choose layout):
                     │ │  ├─ Try cross-reference coords
                     │ │  ├─ Try hierarchical layout
                     │ │  ├─ Try force-directed
                     │ │  └─ Fallback to grid
                     │ ├─ Apply projection (if force-directed)
                     │ ├─ Convert to Petri net
                     │ └─ Load to canvas
                     │
Result               │ Canvas with auto-positioned network
                     │ (user has NO control over algorithm)
```

### NEW: User-Controlled Layout

```
User Action          │ System Behavior
─────────────────────┼──────────────────────────────────────────
Select SBML file     │ Store filepath
                     │
Click Parse          │ ├─ Parse SBML → PathwayData
                     │ ├─ Validate
                     │ ├─ Assign arbitrary positions
                     │ ├─ Convert to Petri net
                     │ └─ Load to canvas
                     │
Swiss Palette:       │ ├─ Read parameters from SBML tab
Force-Directed       │ │  (iterations, k_multiplier, scale)
                     │ ├─ Build graph (object-based IDs)
                     │ ├─ Run physics simulation
                     │ └─ Apply positions directly
                     │
Result               │ Canvas with physics-based layout
                     │ (user controls k, iterations, scale)
```

---

## Code Flow Comparison

### OLD: Multi-Algorithm Decision Tree

```python
# sbml_import_panel.py: _import_pathway_background()
postprocessor = PathwayPostProcessor(
    spacing=150.0,
    scale_factor=scale_factor,
    use_tree_layout=True,        # Enable hierarchical tree
    layout_type='auto',           # Auto-select algorithm
    layout_params={}              # No user params
)
processed = postprocessor.process(parsed_pathway)

# pathway_postprocessor.py: LayoutProcessor.process()
if layout_type == 'force_directed':
    _calculate_force_directed_layout()  # Physics
    if use_spiral_layout:
        project_spiral()                 # Transform coordinates
    else:
        project_layered()                # Transform coordinates
        
elif layout_type == 'hierarchical':
    BiochemicalLayoutProcessor.process()  # Hierarchical algorithm
    if use_tree_layout:
        TreeLayoutProcessor.calculate()   # Tree-based aperture angles
        
elif layout_type == 'auto':
    try_hierarchical()
    if failed:
        try_force_directed()
        if failed:
            grid_layout()  # Last resort

# Result: Complex branching, hard to debug
```

### NEW: Single Algorithm Path

```python
# sbml_import_panel.py: _parse_pathway_background()
# Minimal post-processing (NO LAYOUT)
postprocessor = PathwayPostProcessor(scale_factor=scale_factor)
processed = postprocessor.process(parsed_pathway)
# Assigns arbitrary positions (100, 100), (110, 100), (120, 100)...

converter = PathwayConverter()
document = converter.convert(processed)  # Direct conversion

model_canvas.add_document(document)      # Load to canvas

# Later, user clicks Swiss Palette → Force-Directed
# model_canvas_loader.py: _apply_specific_layout()
params = sbml_panel.get_layout_parameters_for_algorithm('force_directed')
# params = {'iterations': 800, 'k_multiplier': 2.5, 'scale': 3000}

LayoutEngine.apply_layout(manager, 'force_directed', params)

# engine.py: build_graph()
graph = nx.Graph()
for place in manager.places:
    graph.add_node(place, type='place')  # Object reference as node ID
for arc in manager.arcs:
    graph.add_edge(arc.source, arc.target, weight=arc.weight)

# force_directed.py: compute()
positions = nx.spring_layout(graph, k=None, scale=adjusted_scale, 
                            iterations=iterations, weight='weight')

# engine.py: _apply_positions()
for obj, (x, y) in positions.items():
    obj.x = x  # Direct assignment
    obj.y = y

# Result: Single path, easy to understand
```

---

## Architecture Diagrams

### OLD: Complex Multi-Path Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SBML Source                             │
│  (Local File or BioModels API)                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │    SBML Parser         │
          │  (libsbml wrapper)     │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  PathwayValidator      │
          │  (structure checks)    │
          └────────────┬───────────┘
                       │
                       ▼
     ┌─────────────────────────────────────────┐
     │      PathwayPostProcessor               │
     │  ┌───────────────────────────────────┐  │
     │  │    LayoutProcessor (COMPLEX)      │  │
     │  │  ┌─────────────────────────────┐  │  │
     │  │  │  Try Cross-Reference Coords │  │  │
     │  │  │  (KEGG/Reactome API)        │  │  │
     │  │  └──────────┬──────────────────┘  │  │
     │  │             │ (if None)            │  │
     │  │             ▼                      │  │
     │  │  ┌─────────────────────────────┐  │  │
     │  │  │  Hierarchical Layout        │  │  │
     │  │  │  ├─ BiochemicalLayoutProc   │  │  │
     │  │  │  └─ TreeLayoutProcessor     │  │  │
     │  │  │     (aperture angles)       │  │  │
     │  │  └──────────┬──────────────────┘  │  │
     │  │             │ (if fails)           │  │
     │  │             ▼                      │  │
     │  │  ┌─────────────────────────────┐  │  │
     │  │  │  Force-Directed Layout      │  │  │
     │  │  │  ├─ NetworkX spring_layout  │  │  │
     │  │  │  └─ LayoutProjector         │  │  │
     │  │  │     ├─ Spiral projection    │  │  │
     │  │  │     └─ Layered projection   │  │  │
     │  │  └──────────┬──────────────────┘  │  │
     │  │             │ (if fails)           │  │
     │  │             ▼                      │  │
     │  │  ┌─────────────────────────────┐  │  │
     │  │  │  Grid Layout (Fallback)     │  │  │
     │  │  └─────────────────────────────┘  │  │
     │  └─────────────────────────────────┘  │
     │  ┌───────────────────────────────────┐│
     │  │ ColorProcessor                    ││
     │  │ UnitNormalizer                    ││
     │  │ NameResolver                      ││
     │  │ CompartmentGrouper                ││
     │  └───────────────────────────────────┘│
     └────────────────┬────────────────────────┘
                      │
                      ▼
          ┌────────────────────────┐
          │  PathwayConverter      │
          │  (→ Petri net)         │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Load to Canvas        │
          └────────────────────────┘
```

### NEW: Simplified Single-Path Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SBML Source                             │
│  (Local File or BioModels API)                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │    SBML Parser         │
          │  (libsbml wrapper)     │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  PathwayValidator      │
          │  (structure checks)    │
          └────────────┬───────────┘
                       │
                       ▼
     ┌─────────────────────────────────────────┐
     │      PathwayPostProcessor (MINIMAL)     │
     │  ┌───────────────────────────────────┐  │
     │  │ Assign Arbitrary Positions        │  │
     │  │ (100, 100), (110, 100), ...       │  │
     │  └───────────────────────────────────┘  │
     │  ┌───────────────────────────────────┐  │
     │  │ ColorProcessor                    │  │
     │  │ UnitNormalizer                    │  │
     │  │ NameResolver                      │  │
     │  │ CompartmentGrouper                │  │
     │  └───────────────────────────────────┘  │
     └────────────────┬────────────────────────┘
                      │
                      ▼
          ┌────────────────────────┐
          │  PathwayConverter      │
          │  (→ Petri net)         │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Load to Canvas        │
          │  (arbitrary positions) │
          └────────────┬───────────┘
                       │
                       │ USER ACTION:
                       │ Swiss Palette → Force-Directed
                       │
                       ▼
     ┌─────────────────────────────────────────┐
     │       LayoutEngine (Swiss Palette)      │
     │  ┌───────────────────────────────────┐  │
     │  │ Read parameters from SBML tab     │  │
     │  │ (iterations, k_multiplier, scale) │  │
     │  └───────────────────────────────────┘  │
     │  ┌───────────────────────────────────┐  │
     │  │ ForceDirectedLayout               │  │
     │  │ ├─ Build graph (object IDs)       │  │
     │  │ ├─ NetworkX spring_layout         │  │
     │  │ │  (universal repulsion)          │  │
     │  │ └─ Apply positions (direct)       │  │
     │  └───────────────────────────────────┘  │
     └─────────────────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Canvas Redraw         │
          │  (physics-based layout)│
          └────────────────────────┘
```

---

## Key Improvements Summary

### 1. **Simplified Decision Tree**
   - **OLD**: Try 4 algorithms in sequence (cross-ref → hierarchical → force → grid)
   - **NEW**: Single algorithm (force-directed only, user-initiated)

### 2. **Eliminated Coordinate Transformations**
   - **OLD**: Physics → Projection (spiral/layered) → Canvas
   - **NEW**: Physics → Canvas (direct assignment)

### 3. **Object-Based Node IDs**
   - **OLD**: Numeric IDs (place.id=1, transition.id=1 → collision!)
   - **NEW**: Object references (place object itself → unique by identity)

### 4. **User-Controlled Parameters**
   - **OLD**: Hardcoded in PathwayPostProcessor
   - **NEW**: UI spinners in SBML tab (iterations, k_multiplier, scale)

### 5. **Clear User Workflow**
   - **OLD**: Parse → Import (magic happens, user doesn't know which algorithm)
   - **NEW**: Parse → Load → Layout (user sees each step, controls parameters)

### 6. **Reduced Complexity**
   - **OLD**: ~2000 lines across 11 files
   - **NEW**: ~500 lines across 7 files (75% reduction)

---

## Migration Checklist

- [ ] **Phase 1**: Create backup branch (`backup/old-pipeline`)
- [ ] **Phase 2**: Rewrite PathwayPostProcessor (remove LayoutProcessor)
- [ ] **Phase 3**: Simplify PathwayConverter (remove curved arc logic)
- [ ] **Phase 4**: Update SBMLImportPanel (remove Import button)
- [ ] **Phase 5**: Delete legacy files (hierarchical, tree, projector, resolver)
- [ ] **Phase 6**: Update imports (remove references to deleted files)
- [ ] **Phase 7**: Write integration tests
- [ ] **Phase 8**: Update documentation
- [ ] **Phase 9**: Tag release (v2.0.0-simplified-pipeline)

---

**Document Status**: Reference Guide  
**Last Updated**: October 14, 2025  
**Related**: PIPELINE_REFACTORING_PLAN.md
