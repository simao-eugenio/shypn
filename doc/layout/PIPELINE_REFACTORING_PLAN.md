# SBML Import Pipeline Refactoring Plan

**Date**: October 14, 2025  
**Status**: Planning Phase  
**Goal**: Replace OLD complex pipeline with NEW simplified force-directed flow

---

## Executive Summary

The current SBML import pipeline has accumulated multiple layout strategies over time:
- Hierarchical layout with tree-based aperture angles
- Grid layout fallback
- Force-directed with spiral/layered projection
- Cross-reference coordinate resolution (KEGG/Reactome)

**Problem**: Complexity, maintainability, coordinate corruption bugs

**Solution**: **Simplify to SINGLE force-directed layout path with configurable parameters**

The recent force-directed implementation (v1.0.0-force-directed-layout) proves this approach works perfectly:
- Object-based node IDs (no collisions)
- Universal repulsion (all nodes repel)
- Arc weights (stoichiometry-based springs)
- User-configurable parameters (iterations, k_multiplier, scale)

---

## Current Pipeline (OLD - To Be Replaced)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SBML Import Panel (UI)                       │
├─────────────────────────────────────────────────────────────────┤
│  1. Fetch Source                                                │
│     - Local file picker                                         │
│     - BioModels API (download to temp)                          │
│                                                                  │
│  2. Parse Button → _parse_pathway_background()                  │
│     - SBMLParser.parse_file() → PathwayData                     │
│     - PathwayValidator.validate() → ValidationResult            │
│     - Quick Load (TESTING): Arbitrary positions → canvas        │
│                                                                  │
│  3. Import Button → _import_pathway_background()                │
│     - PathwayPostProcessor.process() → ProcessedPathwayData     │
│        ├─ LayoutProcessor (COMPLEX BRANCHING)                   │
│        │  ├─ Cross-reference (KEGG/Reactome coords)             │
│        │  ├─ Hierarchical (BiochemicalLayoutProcessor)          │
│        │  │  └─ TreeLayoutProcessor (aperture angles)           │
│        │  ├─ Force-directed (NetworkX spring_layout)            │
│        │  │  ├─ LayoutProjector (spiral/layered)                │
│        │  │  └─ Raw physics (testing mode)                      │
│        │  └─ Grid (fallback)                                    │
│        ├─ ColorProcessor (compartment colors)                   │
│        ├─ UnitNormalizer (concentration → tokens)               │
│        ├─ NameResolver (ID → readable name)                     │
│        └─ CompartmentGrouper (visual grouping)                  │
│     - PathwayConverter.convert() → DocumentModel               │
│     - Load to canvas (new tab)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Code Structure (OLD)

**Files Involved**:
- `src/shypn/helpers/sbml_import_panel.py` - UI controller (434 lines)
- `src/shypn/data/pathway/pathway_postprocessor.py` - Post-processing (650+ lines)
- `src/shypn/data/pathway/pathway_converter.py` - Petri net conversion (520+ lines)
- `src/shypn/data/pathway/hierarchical_layout.py` - Hierarchical algorithm
- `src/shypn/data/pathway/tree_layout.py` - Tree-based aperture angles
- `src/shypn/data/pathway/layout_projector.py` - 2D projection (spiral/layered)
- `src/shypn/data/pathway/sbml_layout_resolver.py` - Cross-reference coords

**Layout Decision Tree** (pathway_postprocessor.py LayoutProcessor.process()):

```python
if layout_type == 'force_directed':
    # User explicitly selected Force-Directed
    _calculate_force_directed_layout()
    if use_raw_force_directed:
        # Pure physics (no projection)
        return raw_pos
    else:
        # Apply projection post-processing
        if use_spiral_layout:
            project_spiral()
        else:
            project_layered()
    
elif layout_type in ('hierarchical', 'auto'):
    try:
        # Hierarchical layout
        BiochemicalLayoutProcessor.process()
        if use_tree_layout:
            TreeLayoutProcessor.calculate_tree_layout()
    except:
        if layout_type == 'hierarchical':
            _calculate_grid_layout()  # Fallback
        
if layout_type == 'auto' and HAS_NETWORKX:
    _calculate_force_directed_layout()  # Fallback
else:
    _calculate_grid_layout()  # Last resort
```

### Problems with OLD Pipeline

1. **Complexity**: 5+ layout algorithms, 3+ fallback paths
2. **Coordinate Corruption**: Multiple transformations (physics → projection → canvas)
3. **Parameter Coupling**: Layout params spread across multiple classes
4. **Maintenance Burden**: 2000+ lines across 7 files
5. **Testing Difficulty**: Hard to isolate which algorithm was used
6. **Node ID Collisions**: Fixed only recently (object-based IDs)
7. **Curved Arc Issues**: Auto-conversion caused coordinate problems

---

## New Pipeline (SIMPLIFIED - Target Architecture)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SBML Import Panel (UI)                       │
├─────────────────────────────────────────────────────────────────┤
│  1. Fetch Source (UNCHANGED)                                    │
│     - Local file picker                                         │
│     - BioModels API (download to temp)                          │
│                                                                  │
│  2. Parse Button → Pure SBML to Petri Net                       │
│     - SBMLParser.parse_file() → PathwayData                     │
│     - PathwayValidator.validate() → ValidationResult            │
│     - Create ProcessedPathwayData (NO layout yet)               │
│     - Convert to DocumentModel (arbitrary positions)            │
│     - Load to canvas (new tab)                                  │
│                                                                  │
│  3. Swiss Palette → Force-Directed Layout                       │
│     - User clicks "Force-Directed" in Swiss Palette             │
│     - LayoutEngine.apply_layout(force_directed)                 │
│       └─ ForceDirectedLayout.compute(params from UI)            │
│          ├─ Build graph (object-based node IDs)                 │
│          ├─ NetworkX spring_layout (physics simulation)         │
│          └─ Apply positions (direct x,y assignment)             │
│     - Canvas redraws with new positions                         │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow (NEW)

**STEP 1: Fetch** (No changes)
- User browses local file OR enters BioModels ID
- File downloaded to temp if from BioModels

**STEP 2: Parse** (Pure SBML → Petri Net)
```python
# Parse SBML to PathwayData
pathway_data = SBMLParser.parse_file(filepath)

# Validate
validation_result = PathwayValidator.validate(pathway_data)

# Create ProcessedPathwayData with MINIMAL processing
processed = ProcessedPathwayData(
    species=pathway_data.species,
    reactions=pathway_data.reactions,
    metadata=pathway_data.metadata
)

# Assign ARBITRARY positions (force-directed will recalculate)
for i, species in enumerate(processed.species):
    processed.positions[species.id] = (100.0 + i*10, 100.0)
for i, reaction in enumerate(processed.reactions):
    processed.positions[reaction.id] = (150.0 + i*10, 150.0)

# Assign compartment colors (keep this - visual aid)
ColorProcessor(pathway_data).process(processed)

# Normalize units (keep this - concentrations → tokens)
UnitNormalizer(pathway_data, scale_factor).process(processed)

# Convert to Petri net
document = PathwayConverter().convert(processed)

# Load to canvas (new tab)
model_canvas.add_document(document)
```

**STEP 3: Force-Directed Layout** (Swiss Palette)
```python
# User clicks Swiss Palette → Layout → Force-Directed
# ModelCanvasLoader reads parameters from sbml_panel
params = sbml_panel.get_layout_parameters_for_algorithm('force_directed')
# params = {'iterations': 800, 'k_multiplier': 2.5, 'scale': 3000}

# Apply layout
LayoutEngine.apply_layout(manager, 'force_directed', params)

# Inside LayoutEngine:
graph = build_graph(manager.places, manager.transitions, manager.arcs)
# Uses object references as node IDs (no collisions)

positions = ForceDirectedLayout.compute(graph, **params)
# NetworkX spring_layout with universal repulsion

_apply_positions(manager, positions)
# Direct assignment: obj.x = x, obj.y = y
```

### Code Structure (NEW - Simplified)

**Files to Keep**:
- `src/shypn/helpers/sbml_import_panel.py` - UI controller (SIMPLIFIED)
- `src/shypn/data/pathway/sbml_parser.py` - SBML parsing (UNCHANGED)
- `src/shypn/data/pathway/pathway_validator.py` - Validation (UNCHANGED)
- `src/shypn/data/pathway/pathway_data.py` - Data structures (UNCHANGED)
- `src/shypn/data/pathway/pathway_converter.py` - Petri net conversion (SIMPLIFIED)
- `src/shypn/edit/graph_layout/engine.py` - Layout engine (ALREADY NEW)
- `src/shypn/edit/graph_layout/force_directed.py` - Force-directed (ALREADY NEW)

**Files to Remove** (Legacy):
- `src/shypn/data/pathway/pathway_postprocessor.py` - Replace with minimal version
- `src/shypn/data/pathway/hierarchical_layout.py` - Remove entirely
- `src/shypn/data/pathway/tree_layout.py` - Remove entirely
- `src/shypn/data/pathway/layout_projector.py` - Remove entirely
- `src/shypn/data/pathway/sbml_layout_resolver.py` - Remove entirely

**New Minimal Post-Processor** (pathway_postprocessor.py - REWRITTEN):
```python
class PathwayPostProcessor:
    """Minimal post-processor: colors + unit normalization only.
    
    NO LAYOUT CALCULATION - that's done by Swiss Palette force-directed.
    """
    
    def __init__(self, scale_factor: float = 1.0):
        self.scale_factor = scale_factor
    
    def process(self, pathway: PathwayData) -> ProcessedPathwayData:
        processed = ProcessedPathwayData(
            species=list(pathway.species),
            reactions=list(pathway.reactions),
            metadata=dict(pathway.metadata)
        )
        
        # Assign ARBITRARY positions (force-directed will recalculate)
        for i, species in enumerate(processed.species):
            processed.positions[species.id] = (100.0 + i*10, 100.0)
        for i, reaction in enumerate(processed.reactions):
            processed.positions[reaction.id] = (150.0 + i*10, 150.0)
        
        # Color by compartment (visual aid)
        ColorProcessor(pathway).process(processed)
        
        # Normalize concentrations to tokens
        UnitNormalizer(pathway, self.scale_factor).process(processed)
        
        # Resolve names
        NameResolver(pathway).process(processed)
        
        # Group by compartment
        CompartmentGrouper(pathway).process(processed)
        
        return processed
```

---

## Benefits of New Pipeline

### Simplicity
- **1 layout algorithm** instead of 5+
- **No fallback chains** (force-directed works universally)
- **No projection** (direct physics output)
- **Clear flow**: Parse → Load → Layout (user-initiated)

### Correctness
- **Object-based node IDs** (no collisions)
- **No coordinate transformations** (physics → canvas direct)
- **No curved arc auto-conversion** (stay straight)
- **Universal repulsion** (all nodes repel via Graph)

### Flexibility
- **User controls layout** (Swiss Palette, not auto-applied)
- **Parameter experimentation** (UI spinners in SBML tab)
- **Reproducible** (same params → same layout)

### Maintainability
- **~2000 → ~500 lines of code** (75% reduction)
- **4 files removed** (hierarchical, tree, projector, resolver)
- **Single algorithm to test** (force-directed only)
- **Clear architecture** (fetch → parse → import → layout)

---

## Migration Strategy

### Phase 1: Documentation (This Document)
- ✅ Analyze current pipeline
- ✅ Design new architecture
- ✅ Identify files to remove
- ⏳ Create migration checklist

### Phase 2: Code Refactoring
1. **Backup current state** (create branch `backup/old-pipeline`)
2. **Rewrite PathwayPostProcessor** (minimal version)
3. **Simplify PathwayConverter** (remove curved arc logic)
4. **Update SBMLImportPanel** (remove Import button, keep Parse only)
5. **Remove legacy layout files** (hierarchical, tree, projector, resolver)
6. **Update imports** (remove references to deleted files)

### Phase 3: Testing
1. **Unit tests**: Test each component (parser, converter, layout engine)
2. **Integration tests**: End-to-end workflow (BIOMD0000000061)
3. **Parameter tests**: Verify different k/iterations/scale values
4. **Regression tests**: Compare with known-good layouts

### Phase 4: Documentation Update
1. **Update README.md** (new workflow description)
2. **Update doc/layout/*.md** (remove old algorithm docs)
3. **Create DEPRECATED.md** (list removed files and reasons)
4. **Update API docs** (reflect new class signatures)

### Phase 5: Release
1. **Tag version** (v2.0.0-simplified-pipeline)
2. **Create release notes** (breaking changes, migration guide)
3. **Update CHANGELOG.md**
4. **Push to GitHub**

---

## Breaking Changes

### Removed Features
- ❌ Hierarchical layout (with tree-based aperture angles)
- ❌ Grid layout fallback
- ❌ Spiral projection
- ❌ Layered projection
- ❌ Cross-reference coordinate resolution (KEGG/Reactome)
- ❌ Automatic layout on import (now user-initiated via Swiss Palette)

### Changed Behavior
- **Import button removed** (Parse loads with arbitrary positions)
- **Layout user-initiated** (Swiss Palette → Force-Directed)
- **Parameters from UI** (SBML tab spinners control force-directed)

### Migration Path for Users
**Old workflow**:
1. File → Open → Select SBML
2. Click Parse
3. Click Import (auto-applies hierarchical layout)
4. Edit manually if needed

**New workflow**:
1. File → Open → Select SBML
2. Click Parse (loads to canvas with arbitrary positions)
3. Swiss Palette → Force-Directed (apply physics layout)
4. Adjust parameters in SBML tab if needed, re-apply

---

## Risk Assessment

### Low Risk
- ✅ Force-directed already proven (v1.0.0)
- ✅ Object-based IDs tested (no collisions)
- ✅ Parameter flow verified (SBML tab → Swiss Palette)

### Medium Risk
- ⚠️ Users expect auto-layout on import (need docs)
- ⚠️ Hierarchical users may prefer old layout (force-directed is better!)

### High Risk
- 🔴 Breaking changes for existing workflows (need migration guide)

### Mitigation
- Keep old pipeline in `backup/old-pipeline` branch
- Provide clear migration docs
- Add release notes with examples
- Consider feature flag for transition period

---

## Timeline Estimate

| Phase | Tasks | Estimated Time | Status |
|-------|-------|----------------|--------|
| **Phase 1** | Documentation | 2 hours | ✅ In Progress |
| **Phase 2** | Code Refactoring | 6-8 hours | ⏳ Not Started |
| **Phase 3** | Testing | 4-6 hours | ⏳ Not Started |
| **Phase 4** | Documentation Update | 2-3 hours | ⏳ Not Started |
| **Phase 5** | Release | 1 hour | ⏳ Not Started |
| **Total** | | **15-20 hours** | |

---

## Success Criteria

### Code Quality
- ✅ <500 lines total (down from ~2000)
- ✅ Single layout algorithm (force-directed only)
- ✅ No coordinate transformations
- ✅ All tests passing

### Functionality
- ✅ Parse SBML to canvas (arbitrary positions)
- ✅ Swiss Palette force-directed works
- ✅ Parameters flow from UI
- ✅ Object references (no ID collisions)
- ✅ Arc weights (stoichiometry-based)

### User Experience
- ✅ Clear workflow (Parse → Layout)
- ✅ Parameter control (SBML tab spinners)
- ✅ Predictable results (reproducible)
- ✅ Good performance (<2s for 50 nodes)

### Documentation
- ✅ Migration guide complete
- ✅ API docs updated
- ✅ Examples provided
- ✅ Release notes published

---

## Next Steps

1. **Review this plan** - Get stakeholder approval
2. **Create backup branch** - Preserve old pipeline
3. **Start Phase 2** - Rewrite PathwayPostProcessor
4. **Update todo list** - Track progress

---

## Appendix: File Inventory

### Files to Modify

**src/shypn/helpers/sbml_import_panel.py**
- Remove: `_import_pathway_background()` method
- Simplify: `_quick_load_to_canvas()` (remove testing flag)
- Remove: Import button and related code
- Keep: Parse button, fetch, UI parameter reading

**src/shypn/data/pathway/pathway_postprocessor.py**
- Rewrite: Remove LayoutProcessor entirely
- Keep: ColorProcessor, UnitNormalizer, NameResolver, CompartmentGrouper
- Simplify: PathwayPostProcessor to minimal coordinator
- Remove: All layout algorithm code (hierarchical, grid, force-directed, projection)

**src/shypn/data/pathway/pathway_converter.py**
- Remove: Curved arc logic (force all straight)
- Simplify: Direct position mapping (no transformation)
- Remove: Cross-reference coordinate handling
- Keep: Species→Place, Reaction→Transition, Stoichiometry→Arc

### Files to Delete

1. `src/shypn/data/pathway/hierarchical_layout.py` - Hierarchical algorithm
2. `src/shypn/data/pathway/tree_layout.py` - Tree-based aperture angles
3. `src/shypn/data/pathway/layout_projector.py` - Spiral/layered projection
4. `src/shypn/data/pathway/sbml_layout_resolver.py` - Cross-reference coords

### Files to Keep (Unchanged)

- `src/shypn/data/pathway/sbml_parser.py` - SBML parsing
- `src/shypn/data/pathway/pathway_validator.py` - Validation
- `src/shypn/data/pathway/pathway_data.py` - Data structures
- `src/shypn/edit/graph_layout/engine.py` - Layout engine (NEW)
- `src/shypn/edit/graph_layout/force_directed.py` - Force-directed (NEW)
- `src/shypn/helpers/model_canvas_loader.py` - Swiss Palette integration (NEW)

---

**Document Status**: Draft  
**Last Updated**: October 14, 2025  
**Author**: Shypn Development Team  
**Version**: 1.0
