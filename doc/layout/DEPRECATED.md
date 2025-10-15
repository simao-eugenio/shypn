# Deprecated Files - Pipeline Refactoring v2.0

**Date**: October 14, 2025  
**Branch**: feature/property-dialogs-and-simulation-palette  
**Commits**: 600f18e, bc463f6, (pending)  
**Backup Branch**: backup/old-pipeline

---

## Overview

As part of the pipeline refactoring (v2.0), we removed **1,957 lines** of legacy layout code to simplify the SBML import workflow. The old multi-algorithm approach has been replaced with a single force-directed layout that users control via Swiss Palette.

**Old Workflow**: Parse → Import (auto-selects layout: hierarchical/grid/force)  
**New Workflow**: Parse → Load (arbitrary positions) → Swiss Palette → Force-Directed

---

## Removed Files

### 1. `hierarchical_layout.py` (557 lines)

**Purpose**: Hierarchical top-to-bottom flow layout for biochemical pathways

**Features Removed**:
- BiochemicalLayoutProcessor class
- Layer-based node positioning (reactants → products)
- Source/sink detection (entry points and terminal products)
- Breadth-first traversal for layering
- Cross-layer edge minimization
- Tree-based aperture angle layout integration

**Why Removed**:
- Force-directed layout provides better universal node distribution
- Hierarchical layouts required extensive tuning per pathway
- Tree-based aperture angles added complexity without clear benefit
- User can achieve similar results with force-directed parameters

**Code Sample** (what was removed):
```python
class BiochemicalLayoutProcessor:
    """
    Hierarchical layout processor for biochemical pathways.
    
    Positions nodes in layers from top (sources) to bottom (sinks).
    Uses breadth-first traversal and edge minimization.
    """
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        # Build reaction graph
        graph = self._build_reaction_graph()
        
        # Detect sources and sinks
        sources = self._detect_sources(graph)
        sinks = self._detect_sinks(graph)
        
        # Assign layers via BFS
        layers = self._assign_layers_bfs(graph, sources)
        
        # Position nodes within layers
        self._position_nodes_in_layers(layers, processed_data)
```

**Replaced By**: ForceDirectedLayout with user-configurable parameters (iterations, k_multiplier, scale)

---

### 2. `tree_layout.py` (581 lines)

**Purpose**: Tree-based aperture angle layout for hierarchical pathways

**Features Removed**:
- TreeLayoutProcessor class
- Binary tree node positioning
- Aperture angle calculations
- Parent-child relationship tracking
- Recursive subtree positioning
- Vertical layer spacing with horizontal spread

**Why Removed**:
- Only used by hierarchical layout (which is also removed)
- Binary tree approach didn't fit biochemical network topology well
- Aperture angle calculations were complex and hard to tune
- Force-directed layout handles branching naturally via repulsion

**Code Sample** (what was removed):
```python
class TreeLayoutProcessor:
    """
    Tree-based hierarchical layout with aperture angles.
    
    Uses simple binary tree positioning instead of complex
    aperture angle calculations.
    """
    
    def calculate_tree_layout(self) -> Dict[str, Tuple[float, float]]:
        # Build dependency trees
        trees = self._build_dependency_trees()
        
        # Assign layers
        layers = self._assign_layers_to_trees(trees)
        
        # Position recursively
        for tree in trees:
            self._position_subtree_recursive(tree, x_offset, y_offset)
        
        return positions
```

**Replaced By**: Force-directed layout (no tree structure assumptions)

---

### 3. `layout_projector.py` (516 lines)

**Purpose**: 2D projection post-processing for force-directed layouts

**Features Removed**:
- LayoutProjector class
- Spiral projection (entry at center, products spiral outward)
- Layered projection (horizontal layers top-to-bottom)
- Y-coordinate clustering for layer detection
- Horizontal spacing optimization within layers
- Canvas dimension calculation

**Why Removed**:
- Added coordinate transformations (physics → projection → canvas)
- Introduced potential for coordinate corruption
- Users prefer direct physics output (no transformations)
- Swiss Palette force-directed now uses raw NetworkX output

**Code Sample** (what was removed):
```python
class LayoutProjector:
    """
    Projects force-directed positions to 2D canvas layouts.
    
    Strategies:
    - LAYERED: Cluster by Y, arrange horizontally
    - SPIRAL: Entry at center, products spiral outward
    """
    
    def project(self, positions, edges):
        # Cluster nodes by Y coordinate
        layers = self._cluster_by_y(positions)
        
        # Position nodes within layers
        projected = self._position_in_layers(layers)
        
        # Calculate canvas dimensions
        canvas_dims = self._calculate_canvas_bounds(projected)
        
        return projected, canvas_dims
```

**Replaced By**: Direct NetworkX spring_layout output (no projection)

---

### 4. `sbml_layout_resolver.py` (303 lines)

**Purpose**: Cross-reference coordinate resolution from KEGG/Reactome APIs

**Features Removed**:
- SBMLLayoutResolver class
- SBML layout extension parsing
- KEGG pathway coordinate fetching
- Reactome coordinate fetching
- Species coordinate caching
- Reaction midpoint calculation

**Why Removed**:
- External API dependencies (unreliable, rate-limited)
- Cross-reference coordinates often misaligned with local pathways
- Added complexity for marginal benefit
- Force-directed layout provides consistent results regardless of source

**Code Sample** (what was removed):
```python
class SBMLLayoutResolver:
    """
    Resolves layout coordinates from external sources.
    
    Sources:
    1. SBML layout extension (if present)
    2. KEGG pathway coordinates (if available)
    3. Reactome pathway coordinates (if available)
    """
    
    def resolve_layout(self) -> Optional[Dict[str, Tuple[float, float]]]:
        # Try SBML layout extension first
        positions = self._try_sbml_layout_extension()
        if positions:
            return positions
        
        # Try KEGG coordinates
        positions = self._try_kegg_coordinates()
        if positions:
            return positions
        
        # No external coordinates found
        return None
```

**Replaced By**: PathwayPostProcessor assigns arbitrary positions (force-directed recalculates)

---

## Methods Removed

### From `sbml_import_panel.py`

**_on_import_clicked(self, button)** (23 lines)
- Old Import button click handler
- Validated pathway, disabled buttons, called _import_pathway_background()

**_import_pathway_background(self)** (235 lines)
- Complex layout algorithm selection logic
- Auto/Hierarchical/Force-Directed branching
- Layout parameter extraction from UI
- KEGG-style enhancement pipeline
- Arc routing and optimization
- Extensive DEBUG coordinate logging

**Why Removed**: Parse button now auto-loads to canvas with new PathwayPostProcessor (v2.0)

---

## Classes Removed

### From `pathway_postprocessor.py`

**LayoutProcessor** (350+ lines)
- Multi-algorithm layout processor
- Auto-selection logic (cross-ref → hierarchical → force → grid)
- Force-directed with projection
- Grid fallback
- Parameter passing to specialized processors

**Why Removed**: Replaced with arbitrary position assignment (force-directed via Swiss Palette)

---

## Total Impact

| Category | Lines Removed | Files Removed |
|----------|---------------|---------------|
| **Legacy Layout Files** | 1,957 | 4 |
| **SBMLImportPanel Methods** | 258 | 2 methods |
| **PathwayPostProcessor** | 334 (net) | 1 class |
| **Total** | **2,549** | **4 files + 3 methods/classes** |

---

## Migration Guide

### For Users

**Old Way**:
1. Open SBML file
2. Click Parse
3. Click Import → auto-layout applied (which algorithm? unknown!)
4. Edit manually if layout is bad

**New Way**:
1. Open SBML file
2. Click Parse → pathway loads to canvas immediately
3. Swiss Palette → Layout → Force-Directed
4. Adjust parameters in SBML tab (iterations, k, scale), re-apply as needed

### For Developers

**If you were using**:
- `BiochemicalLayoutProcessor` → Use `ForceDirectedLayout` from `src/shypn/edit/graph_layout/force_directed.py`
- `TreeLayoutProcessor` → Use force-directed (no tree assumptions)
- `LayoutProjector` → Use raw NetworkX spring_layout output
- `SBMLLayoutResolver` → Assign arbitrary positions, let user apply force-directed

**Parameter Mapping**:
- `layout_type='hierarchical'` → Use force-directed with low k_multiplier (0.5-1.0)
- `layout_type='force_directed'` → Use force-directed with medium k_multiplier (1.5-2.5)
- `layout_type='grid'` → No longer needed (force-directed handles all cases)

---

## Backup & Rollback

**Backup Branch**: `backup/old-pipeline`
- All removed code preserved
- Accessible via `git checkout backup/old-pipeline`
- Tagged: (no tag, branch serves as backup)

**Old Files Preserved** (in repo):
- `pathway_postprocessor_old.py` - Old PathwayPostProcessor with LayoutProcessor

**Rollback Procedure** (if needed):
1. `git checkout backup/old-pipeline`
2. `git checkout -b restore-old-pipeline`
3. Cherry-pick specific files if needed
4. Test thoroughly before merging

---

## Rationale

### Why Remove Instead of Deprecate?

1. **Complexity Burden**: 2,549 lines of complex layout code to maintain
2. **Single Algorithm Works**: Force-directed handles all cases well
3. **User Control**: Users can tune parameters instead of system guessing
4. **No Breaking Changes**: New workflow is simpler, not more complex
5. **Clear Path Forward**: One algorithm to optimize, test, and document

### Why Force-Directed Only?

1. **Universal**: Works for any network topology (tree, mesh, cyclic)
2. **Physics-Based**: Intuitive behavior (repulsion + attraction)
3. **Configurable**: Users control spacing via iterations, k, scale
4. **Proven**: v1.0.0-force-directed-layout verified with BIOMD0000000061
5. **Swiss Palette**: Consistent with existing layout tools

---

## References

- **Planning**: `PIPELINE_REFACTORING_PLAN.md`
- **Comparison**: `PIPELINE_COMPARISON.md`
- **Summary**: `REFACTORING_EXECUTIVE_SUMMARY.md`
- **Force-Directed**: `FORCE_DIRECTED_LAYOUT_COMPLETE.md`
- **Backup Branch**: `backup/old-pipeline`

---

**Status**: Documentation Complete  
**Next**: Integration testing with BIOMD0000000061  
**Version**: v2.0.0-simplified-pipeline (pending)
