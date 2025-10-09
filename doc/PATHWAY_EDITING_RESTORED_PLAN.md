# Pathway Editing - Restored Implementation Plan

**Date**: 2025-10-09  
**Status**: 📋 Ready to Implement  
**Source**: DUAL_EDITING_MODES_PLAN.md (October 7, 2025)

---

## 🎯 Quick Overview

The pathway editing plan consists of **8 phases** implementing dual editing modes, visual guidance, and automatic graph layout:

1. **Mode Management Infrastructure** (2 days)
2. **Hierarchy Color Coding** (2-3 days)
3. **Visual Overlay System** (3-4 days)
4. **Pathway Edit Panel** (3-4 days)
5. **Visual Effect Modes** (2-3 days)
6. **Graph Layout Algorithms** (4-5 days) ⭐ **NEW**
7. **Integration & Testing** (2 days)
8. **Documentation** (2 days)

**Total Estimated Time**: 20-25 days

---

## 🚀 Implementation Roadmap

### Phase 1: Mode Management Infrastructure (2 days) - NEXT UP

**Goal**: Basic mode switching between CREATE and PATHWAY_EDIT modes

**What we'll build**:
```python
class EditingModeManager:
    """Manages switching between creation and pathway editing modes."""
    
    def __init__(self, main_window):
        self.current_mode = 'create'  # 'create' or 'pathway_edit'
        self.overlay_renderer = None
    
    def switch_to_create_mode(self):
        """Standard editing operations, no hierarchy coloring"""
        pass
    
    def switch_to_pathway_edit_mode(self):
        """Hierarchy-aware operations, color coding, visual guidance"""
        pass
```

**UI Addition**:
```
┌────────────────────────────────────────┐
│ File  Edit  View  Simulate  Help      │
│ Mode: (●) Create  ( ) Edit Pathway    │  ← NEW TOGGLE
└────────────────────────────────────────┘
```

**Tasks**:
- [ ] User guide for pathway editing mode
- [ ] Visual effects reference (H/G/M/F shortcuts)
- [ ] Hierarchy classification explanation
- [ ] Graph layout algorithm guide
- [ ] Example pathways with screenshots
- [ ] Integration with existing documentation

**Deliverables**:
- `doc/PATHWAY_EDITING_USER_GUIDE.md` - End-user documentation
- `doc/GRAPH_LAYOUT_ALGORITHMS.md` - Algorithm reference
- `models/pathways/examples/` - Sample pathways with different layouts

---

### Phase 2: Hierarchy Color Coding (2-3 days)

**Goal**: Color objects by hierarchy level

**Color Scheme**:
```python
HIERARCHY_COLORS = {
    0: {  # Main backbone - DARK & SATURATED
        'place_fill': '#2563EB',      # Dark blue
        'transition_fill': '#059669',  # Dark green
        'arc_width': 3.0
    },
    1: {  # Primary branches - MEDIUM
        'place_fill': '#60A5FA',       # Medium blue
        'transition_fill': '#34D399',  # Medium green
        'arc_width': 2.0
    },
    2: {  # Secondary/leafs - LIGHT
        'place_fill': '#DBEAFE',       # Light blue
        'transition_fill': '#D1FAE5',  # Light green
        'arc_width': 1.0
    }
}
```

**Tasks**:
- [ ] Define hierarchy color scheme
- [ ] Implement `apply_hierarchy_colors(manager)`
- [ ] Add `hierarchy_level` metadata to imported pathways
- [ ] Test with KEGG pathways (glycolysis, TCA cycle)

**Files to create**:
- `src/shypn/visualization/hierarchy_colors.py`

**Files to modify**:
- `src/shypn/importer/kegg/pathway_converter.py` (add hierarchy on import)

---

### Phase 3: Visual Guidance Overlays (3-4 days)

**Goal**: Overlay system for visual cues

**What we'll add**:
```
┌─────────────────────────────────────────┐
│  Pathway Canvas (below)                 │
│  [Place] → (Transition) → [Place]       │
│                                          │
│  Overlay Layer (above):                 │
│  • Hierarchy labels: "Level 0", "Level 1"│
│  • Bounding boxes around groups         │
│  • Flow arrows showing main path        │
│  • Minimap in corner                    │
└─────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create `PathwayOverlayRenderer` class
- [ ] Implement bounding boxes rendering
- [ ] Implement flow arrows rendering
- [ ] Implement hierarchy labels rendering
- [ ] Implement minimap rendering
- [ ] Integrate with canvas rendering pipeline

**Files to create**:
- `src/shypn/visualization/overlay_renderer.py`

**Files to modify**:
- `src/shypn/canvas/canvas_manager.py` (add overlay rendering)

---

### Phase 4: Pathway Edit Panel (3-4 days)

**Goal**: UI controls for pathway editing

**Panel Structure**:
```
┌─────────────────────────────────┐
│ Pathway Editing                 │
├─────────────────────────────────┤
│ Visibility Control:             │
│ [✓] Level 0: Main Backbone      │
│ [✓] Level 1: Primary            │
│ [✓] Level 2: Secondary          │
│                                 │
│ Visual Mode:                    │
│ (●) Color by Hierarchy          │
│ ( ) Heatmap (Centrality)        │
│ ( ) Uniform (No colors)         │
│                                 │
│ Overlay Options:                │
│ [✓] Bounding boxes              │
│ [✓] Flow arrows                 │
│ [✓] Level labels                │
│ [✓] Minimap                     │
│                                 │
│ Actions:                        │
│ [Abstract Selected]             │
│ [Expand Abstraction]            │
│ [Re-compute Hierarchy]          │
│ [Auto-layout]                   │
│                                 │
│ Statistics:                     │
│ Main backbone: 12 nodes         │
│ Primary: 18 nodes               │
│ Secondary: 8 nodes              │
│ Hidden: 5 abstractions          │
└─────────────────────────────────┘
```

**Tasks**:
- [ ] Design `pathway_edit_panel.ui` in Glade
- [ ] Create `PathwayEditPanelLoader` class
- [ ] Implement visibility controls (checkboxes)
- [ ] Implement color mode controls (radio buttons)
- [ ] Implement overlay controls (checkboxes)
- [ ] Implement action buttons
- [ ] Implement statistics display
- [ ] Integrate with main window (right dock area)

**Files to create**:
- `ui/panels/pathway_edit_panel.ui`
- `src/shypn/helpers/pathway_edit_panel_loader.py`

**Files to modify**:
- `src/shypn.py` (wire up panel in main application)

---

### Phase 5: Visual Effect Modes (2-3 days)

**Goal**: Implement special visual modes

**Keyboard Shortcuts**:
- **H** - Highlight Mode: Dim all except selected hierarchy level
- **G** - Ghost Mode: Show hidden elements as semi-transparent
- **M** - Heatmap Mode: Color by centrality score (continuous gradient)
- **F** - Focus Mode: Blur background, focus on selected sub-pathway

**Tasks**:
- [ ] Implement `apply_highlight_mode(manager, level)`
- [ ] Implement `apply_ghost_mode(manager, show_hidden)`
- [ ] Implement `apply_heatmap_mode(manager)`
- [ ] Implement `apply_focus_mode(manager, selected)`
- [ ] Add keyboard shortcuts (H, G, M, F)
- [ ] Test visual modes work correctly

**Files to create**:
- `src/shypn/visualization/visual_modes.py`

**Files to modify**:
- `src/shypn/helpers/pathway_edit_panel_loader.py` (add mode controls)

---

### Phase 6: Graph Layout Algorithms (4-5 days) ⭐ NEW

**Goal**: Automatically arrange pathways for optimal visual clarity

**Scientific Basis**:
- Sugiyama et al. (1981) - Hierarchical layout
- Fruchterman & Reingold (1991) - Force-directed layout
- Di Battista et al. (1998) - Graph drawing algorithms

**Key Algorithms**:

1. **Hierarchical Layout (Sugiyama Framework)**
   - Best for: Linear metabolic pathways (e.g., glycolysis)
   - Method: Layer assignment → crossing reduction → coordinate assignment
   - Result: Top-to-bottom flow with minimal edge crossings

2. **Force-Directed Layout (Fruchterman-Reingold)**
   - Best for: Complex pathways with cycles
   - Method: Physics-based simulation (nodes repel, edges attract)
   - Result: Balanced distribution, natural clustering

3. **Circular Layout**
   - Best for: Cyclic pathways (e.g., TCA cycle, Calvin cycle)
   - Method: Place main cycle on circle, arrange branches outside
   - Result: Emphasizes cyclic structure

4. **Orthogonal Layout**
   - Best for: Circuit-like pathways, regulatory networks
   - Method: Horizontal/vertical edges only (Manhattan routing)
   - Result: Clean, grid-like appearance

**Tasks**:
- [ ] Install dependencies (`networkx`, optionally `pygraphviz`)
- [ ] Implement 4 layout algorithms
- [ ] Create auto-selection logic (analyze pathway topology)
- [ ] Add "Re-layout" button to pathway import panel
- [ ] Create layout algorithm picker dialog
- [ ] Test with various pathway types

**Files to Create**:
```
src/shypn/layout/
├── __init__.py
├── algorithms.py         ← All 4 layout implementations
├── selector.py          ← Auto-detect best algorithm
└── utils.py             ← Helper functions

ui/dialogs/
└── layout_picker_dialog.ui  ← UI for manual algorithm selection

tests/
└── test_layout_algorithms.py
```

**Implementation Example**:
```python
# In algorithms.py
def hierarchical_layout(pathway):
    """Sugiyama-style layered layout for directed pathways."""
    G = pathway_to_networkx(pathway)
    layers = assign_layers(G)  # Topological sort
    positions = assign_coordinates(layers)  # Minimize crossings
    return positions

def force_directed_layout(pathway, iterations=500):
    """Fruchterman-Reingold physics-based layout."""
    G = pathway_to_networkx(pathway)
    return nx.spring_layout(G, k=1.0/sqrt(len(G)), iterations=iterations)

# Auto-selection
def select_layout_algorithm(pathway):
    """Automatically choose best layout based on topology."""
    G = pathway_to_networkx(pathway)
    
    if nx.is_directed_acyclic_graph(G):
        return 'hierarchical'
    elif has_large_cycle(G):
        return 'circular'
    elif is_highly_connected(G):
        return 'force_directed'
    else:
        return 'hierarchical'
```

**UI Integration**:
- Button in pathway import panel: "Re-layout Pathway"
- Dropdown: "Auto" | "Hierarchical" | "Force-Directed" | "Circular" | "Orthogonal"
- Preview mode showing layout before applying

---

### Phase 7: Integration & Testing (2 days)

**Goal**: Ensure both modes work seamlessly

**Test Cases**:
- [ ] Switching between create and pathway edit modes
- [ ] Create mode doesn't show hierarchy colors
- [ ] Pathway edit mode works with imported pathways
- [ ] Non-pathway documents can compute hierarchy
- [ ] All visual modes and overlays work
- [ ] Performance with large pathways (1000+ nodes)

**Files to create**:
- `tests/test_editing_modes.py`
- `tests/test_visual_overlays.py`

---

### Phase 8: Documentation (2 days)

**Goal**: Document dual editing system

**Documents to create**:
- [ ] `doc/EDITING_MODES_GUIDE.md` - User guide
- [ ] `doc/PATHWAY_VISUAL_GUIDANCE.md` - Visual features guide
- [ ] Update main README with mode switching info
- [ ] Add screenshots and examples
- [ ] Create video tutorial (optional)

---

## � Current Status

**Research Phase**: ✅ COMPLETE (October 7, 2025)
- ✅ Research foundation (PATHWAY_EDITING_RESEARCH.md)
- ✅ Dual editing modes design (DUAL_EDITING_MODES_PLAN.md)
- ✅ Scientific references (13 papers)
- ✅ Graph layout algorithms (4 algorithms researched)
- ✅ Implementation roadmap

**Implementation Phase**: ⏳ NOT STARTED
- ⏳ Phase 1: Mode Management Infrastructure
- ⏳ Phase 2: Hierarchy Color Coding
- ⏳ Phase 3: Visual Overlay System
- ⏳ Phase 4: Pathway Edit Panel
- ⏳ Phase 5: Visual Effect Modes
- ⏳ Phase 6: Graph Layout Algorithms
- ⏳ Phase 7: Integration & Testing
- ⏳ Phase 8: Documentation

---

## 🎯 Recommended Next Steps

### Option 1: Start Immediately (Recommended)

Begin with Phase 1 today:

```bash
# Create the mode manager file
touch src/shypn/helpers/editing_mode_manager.py

# Start coding
code src/shypn/helpers/editing_mode_manager.py
```

**Advantages**:
- Foundation is low-risk
- Can test immediately
- Unblocks other phases

### Option 2: Quick Wins First (Graph Layout) ⭐ NEW

Start with Phase 6 (Graph Layout) if you want visible results faster:

```bash
# Install dependencies
pip install networkx

# Create the layout module
mkdir -p src/shypn/layout
touch src/shypn/layout/__init__.py
touch src/shypn/layout/algorithms.py

# Start coding
code src/shypn/layout/algorithms.py
```

**Advantages**:
- **Immediate visual feedback** - See pathways auto-organize
- **Independent from other phases** - Works with current KEGG imports
- **Practical benefit now** - Improves existing workflow
- More exciting to see results

### Option 3: Hierarchy Colors (Alternative Quick Win)

Start with Phase 2 (Hierarchy Colors) for visual results:

```bash
# Create the color scheme file
touch src/shypn/visualization/hierarchy_colors.py

# Start coding
code src/shypn/visualization/hierarchy_colors.py
```

**Advantages**:
- Immediate visual feedback
- Can test with existing KEGG imports
- Shows pathway importance visually

### Option 4: Full Planning Review

Review all documents before starting:

1. Read `doc/pathways/PATHWAY_EDITING_RESEARCH.md` (algorithms)
2. Read `doc/pathways/DUAL_EDITING_MODES_PLAN.md` (this plan)
3. Review existing code:
   - `src/shypn/importer/kegg/` (where to add hierarchy)
   - `src/shypn/canvas/` (where to add overlay)
   - `src/shypn/helpers/` (where mode manager lives)

---

## 📁 Related Documentation

All pathway editing research is in `doc/pathways/`:

```
doc/pathways/
├── DUAL_EDITING_MODES_PLAN.md          ← Current plan (YOU ARE HERE)
├── DUAL_EDITING_MODES_COMPARISON.md    ← CREATE vs PATHWAY_EDIT comparison
├── PATHWAY_EDITING_RESEARCH.md         ← Scientific algorithms & references
├── PATHWAY_EDITING_SUMMARY.md          ← Quick reference
└── README.md                            ← Index of all pathway docs
```

---

## 🔗 Dependencies

### Required Before Starting:
- ✅ KEGG import working (already complete)
- ✅ Source/sink transitions (already complete)
- ✅ Canvas rendering system (already complete)
- ✅ Transformation handlers (already complete)

### Will Enable After Completion:
- 🎯 Hierarchical pathway editing
- 🎯 Visual guidance for complex pathways
- 🎯 Progressive disclosure (hide/show levels)
- 🎯 Better understanding of imported pathways
- 🎯 Abstraction mechanisms (source/sink usage)

---

## 💡 Key Design Decisions

### Why Two Modes?

**Problem**: Editing complex imported pathways (100+ nodes) is overwhelming

**Solution**: Separate "create from scratch" from "refine imported"

**Benefits**:
- Clean separation of concerns
- Different visual cues for different contexts
- Won't clutter create mode with pathway features
- Won't limit pathway mode to simple operations

### Why Hierarchy-Based?

**Research shows** metabolic pathways have natural hierarchy:
- Main backbone (central metabolism)
- Primary branches (biosynthesis pathways)
- Secondary leafs (cofactor metabolism)

**Benefits**:
- Focus on what matters (hide secondary paths)
- Visual importance (dark = main, light = secondary)
- Progressive disclosure (reveal complexity gradually)

---

## 🚀 Let's Get Started!

**Recommendation**: Start with Phase 1 (Mode Management) - it's:
- Low risk (won't break existing features)
- Fast (2 days)
- Foundational (required for all other phases)
- Testable immediately

**Command to start**:
```bash
cd /home/simao/projetos/shypn
mkdir -p src/shypn/helpers
touch src/shypn/helpers/editing_mode_manager.py
code src/shypn/helpers/editing_mode_manager.py
```

Ready to implement? 🎯
