# Per-Document Panel Instance Normalization Plan

**Date**: 2026-01-06  
**Branch**: Usability-and-Manuscripts  
**Architect**: GitHub Copilot  
**Objective**: Normalize all Master Palette panels to use per-document instance architecture

---

## Executive Summary

**Goal**: Convert all panels to use **per-document instances** (one panel instance per open document), matching the proven Viability/Report panel architecture.

**Current State**: 2/6 panels use per-document instances
- ✅ Viability Panel
- ✅ Report Panel
- ❌ Pathways Panel (shared instance)
- ❌ Analyses Panel (shared instance)
- ❌ Topology Panel (shared instance)
- ✅ Files Panel (stateless - no change needed)

**Target State**: 3/6 panels converted + 2 already done + 1 unchanged
- ✅ Viability Panel (no change)
- ✅ Report Panel (no change)
- 🔄 Pathways Panel → **Per-document instances**
- 🔄 Analyses Panel → **Per-document instances**
- 🔄 Topology Panel → **Per-document instances**
- ✅ Files Panel (stateless - no change)

**Estimated Scope**: 3-5 days
- Day 1: Pathways Panel
- Day 2: Analyses Panel
- Day 3: Topology Panel
- Day 4-5: Integration testing, documentation, cleanup

---

## Motivation

### Current Problems with Shared Panel Instances

#### 1. **State Loss on Tab Switch**
**Problem**: When switching tabs, panels either:
- Clear their state (Analyses Panel - loses selections)
- Update references (Pathways/Topology - but lose UI state)

**Example**: User adds 5 transitions to analysis in Tab A → switches to Tab B → loses all selections

**Solution**: Per-document instances preserve state per tab.

---

#### 2. **User Experience Inconsistency**
**Problem**: Viability and Report panels preserve state, but others don't.

**User Expectation**: "My selections should stay when I switch tabs"

**Current Reality**:
- ✅ Viability: Localities preserved per tab
- ✅ Report: Expanded categories preserved per tab
- ❌ Analyses: Selections cleared on switch
- ❌ Pathways: Form fields reset
- ❌ Topology: Must re-expand categories

**Solution**: Consistent per-document behavior across all panels.

---

#### 3. **Complexity in Tab Switching Logic**
**Problem**: Each panel has different update mechanisms:
- Viability: Instance swap
- Report: Instance swap
- Analyses: Clear selections + update reference
- Pathways: Update reference
- Topology: Update reference + cache management

**Maintenance Burden**: 5 different patterns to maintain.

**Solution**: Single unified pattern - instance swap for all.

---

#### 4. **Data Isolation Issues**
**Problem**: Shared panel instances can leak state between documents.

**Example Scenario**:
```
1. User opens Tab A (KEGG pathway hsa00010)
2. Clicks "Enrich with BRENDA" - populates EC numbers list
3. Switches to Tab B (empty model)
4. BRENDA panel still shows EC numbers from Tab A ❌
```

**Current Mitigation**: Manual state clearing on tab switch (error-prone).

**Solution**: Complete isolation - each document has its own panel instance.

---

## Benefits of Per-Document Instances

### 1. ✅ **State Preservation**
Each document preserves:
- Selected transitions/places for analysis
- Form field values (KEGG pathway ID, SBML file path)
- Expanded/collapsed categories
- Scroll positions
- Search query text
- Table filters

**User Impact**: Seamless multi-document workflow.

---

### 2. ✅ **Zero Cross-Contamination**
Complete data isolation:
- Document A's selections never appear in Document B
- No need for manual state clearing
- Predictable behavior

**Developer Impact**: Simpler code, fewer bugs.

---

### 3. ✅ **Fast Tab Switching**
No UI rebuild on switch:
- Just swap panel widgets in container
- All UI state already built and ready
- Instant response to tab changes

**Performance**: <10ms tab switch latency.

---

### 4. ✅ **Simplified Architecture**
Single pattern for all panels:
```python
# Unified tab switch handler
def _on_tab_switch(drawing_area):
    # Get this document's panel instance
    overlay_manager = self.overlay_managers[drawing_area]
    panel_loader = overlay_manager.<panel>_loader
    
    # Swap panel widget
    container.remove_all_children()
    container.pack_start(panel_loader.widget, True, True, 0)
    
    # Done! Panel already has its state
```

**Maintenance**: One pattern to understand and maintain.

---

### 5. ✅ **Future-Proof**
Easy to add new panels:
- Follow proven pattern
- Copy/paste panel loader creation
- Wire to overlay_manager

**Developer Experience**: Clear, consistent architecture.

---

## Tradeoffs & Mitigation

### ❌ Tradeoff 1: Higher Memory Usage

**Issue**: N documents × M panels = N×M panel instances in memory.

**Current State**: 2 documents × 2 panels (Viability + Report) = 4 instances
- Each Viability instance: ~5MB (TreeViews, stores, buffers)
- Each Report instance: ~3MB (categories, tables)
- Total: ~16MB for 2 documents

**After Normalization**: 2 documents × 5 panels = 10 instances
- Adding Pathways: ~2MB/instance
- Adding Analyses: ~3MB/instance (plots)
- Adding Topology: ~1MB/instance
- **Total**: ~28MB for 2 documents (+12MB = 75% increase)

**Mitigation**:
1. **Lazy creation**: Only create panel when user first opens that panel
2. **Cleanup on close**: Destroy panel instance when document closes
3. **Acceptable cost**: Modern systems have GB of RAM, 12MB is negligible

**Decision**: ✅ **ACCEPT** - Memory increase is acceptable for better UX.

---

### ❌ Tradeoff 2: More Complex Initialization

**Issue**: Creating panel instances in overlay_manager adds complexity.

**Current**: Single panel instance created in main shypn.py.

**New**: Per-document panel instances created in model_canvas_loader.py.

**Mitigation**:
1. **Factory functions**: Standardized panel creation helpers
2. **Clear documentation**: Architecture guide for developers
3. **Consistent pattern**: All panels follow same initialization flow

**Decision**: ✅ **ACCEPT** - One-time complexity for long-term maintainability.

---

### ❌ Tradeoff 3: Migration Effort

**Issue**: Refactoring 3 panels takes development time.

**Estimated Effort**:
- Pathways Panel: 6-8 hours (8 categories to wire)
- Analyses Panel: 4-6 hours (3 categories, plot management)
- Topology Panel: 5-7 hours (4 categories, cache per-instance)
- Testing: 8-10 hours (integration tests, manual QA)
- **Total**: 23-31 hours (~3-4 days)

**Mitigation**:
1. **Incremental approach**: One panel at a time, test before next
2. **Reuse existing pattern**: Copy Viability/Report implementation
3. **Automated testing**: Unit tests for each panel

**Decision**: ✅ **ACCEPT** - Investment pays off in maintainability.

---

## Architecture Design

### Per-Document Panel Instance Pattern

#### Current Architecture (Shared Instance)
```
┌─────────────────────────────────────────┐
│ shypn.py (main application)             │
│   ├─ Create pathway_panel_loader (1x)   │
│   └─ Register with master_palette       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ model_canvas_loader                     │
│   ├─ Document A (drawing_area_a)        │
│   ├─ Document B (drawing_area_b)        │
│   └─ On tab switch:                     │
│       └─ pathway_panel_loader.set_model_canvas(self)
└─────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ pathway_panel_loader (SHARED)           │
│   └─ PathwayOperationsPanel             │
│       ├─ KEGGCategory (current model)   │
│       ├─ SBMLCategory (current model)   │
│       └─ ... 6 more categories          │
└─────────────────────────────────────────┘

PROBLEM: Single panel instance serves all documents
         State is overwritten on tab switch
```

---

#### New Architecture (Per-Document Instances)
```
┌─────────────────────────────────────────────────────────┐
│ shypn.py (main application)                             │
│   ├─ Create pathway_panel_container (empty Gtk.Box)     │
│   └─ Register container with master_palette             │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ model_canvas_loader                                     │
│   ├─ add_document('doc_a'):                             │
│   │   └─ Create overlay_manager_a                       │
│   │       └─ pathway_panel_loader_a = create_pathway_panel()
│   │           └─ PathwayOperationsPanel(model=manager_a)│
│   │                                                      │
│   ├─ add_document('doc_b'):                             │
│   │   └─ Create overlay_manager_b                       │
│   │       └─ pathway_panel_loader_b = create_pathway_panel()
│   │           └─ PathwayOperationsPanel(model=manager_b)│
│   │                                                      │
│   └─ On tab switch:                                     │
│       ├─ Get overlay_manager[drawing_area]              │
│       ├─ pathway_loader = overlay_manager.pathway_panel_loader
│       ├─ Clear container                                │
│       └─ Pack pathway_loader.widget into container      │
└─────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ overlay_manager_a                                       │
│   └─ pathway_panel_loader_a (DOCUMENT A ONLY)          │
│       └─ PathwayOperationsPanel                         │
│           ├─ KEGGCategory (Doc A state)                 │
│           └─ ... 7 more categories                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ overlay_manager_b                                       │
│   └─ pathway_panel_loader_b (DOCUMENT B ONLY)          │
│       └─ PathwayOperationsPanel                         │
│           ├─ KEGGCategory (Doc B state)                 │
│           └─ ... 7 more categories                      │
└─────────────────────────────────────────────────────────┘

SOLUTION: Each document has its own panel instance
          State is completely isolated per document
```

---

### Key Components

#### 1. Panel Loader Factory
**Location**: `src/shypn/helpers/<panel>_panel_loader.py`

**Purpose**: Create panel instances with proper wiring.

**New Method**:
```python
def create_pathway_panel_for_document(model_canvas_manager, workspace_settings=None, parent_window=None):
    """Create a PathwayOperationsPanel instance for a specific document.
    
    This is called once per document when the document is created.
    The panel instance is stored in overlay_manager and swapped on tab switch.
    
    Args:
        model_canvas_manager: The ModelCanvasManager for this document
        workspace_settings: Optional workspace settings
        parent_window: Optional parent window for dialogs
        
    Returns:
        PanelLoader: Panel loader with .widget and .panel properties
    """
    panel = PathwayOperationsPanel(
        workspace_settings=workspace_settings,
        parent_window=parent_window,
        project=None,
        model_canvas=model_canvas_manager  # Already tied to this document
    )
    
    loader = PanelLoader()
    loader.panel = panel
    loader.widget = panel  # PathwayOperationsPanel is a Gtk.Box
    
    return loader
```

---

#### 2. Overlay Manager Extension
**Location**: `src/shypn/helpers/model_canvas_loader.py`

**Purpose**: Store per-document panel loaders.

**Current State** (Viability + Report only):
```python
class OverlayManager:
    def __init__(self, drawing_area):
        self.drawing_area = drawing_area
        self.canvas_manager = None
        self.simulation_controller = None
        self.viability_panel_loader = None  # ✅ Per-document
        self.report_panel_loader = None      # ✅ Per-document
        # TODO: Add other panels
```

**New State** (All panels):
```python
class OverlayManager:
    def __init__(self, drawing_area):
        self.drawing_area = drawing_area
        self.canvas_manager = None
        self.simulation_controller = None
        
        # Per-document panel instances
        self.viability_panel_loader = None  # ✅ Already implemented
        self.report_panel_loader = None      # ✅ Already implemented
        self.pathway_panel_loader = None     # 🔄 NEW
        self.analyses_panel_loader = None    # 🔄 NEW (right panel)
        self.topology_panel_loader = None    # 🔄 NEW
        # Files panel: N/A (stateless)
```

---

#### 3. Tab Switch Handler
**Location**: `src/shypn/helpers/model_canvas_loader.py` in `_on_notebook_switch_page()`

**Current Logic** (mixed patterns):
```python
def _on_notebook_switch_page(self, notebook, page, page_num):
    drawing_area = self._extract_drawing_area(page)
    
    # Pattern 1: Reference update (Analyses)
    if self.right_panel_loader:
        manager = self.canvas_managers[drawing_area]
        self.right_panel_loader.set_model(manager)
    
    # Pattern 2: Reference update (Pathways)
    if self.pathway_panel_loader:
        self.pathway_panel_loader.set_model_canvas(self)
    
    # Pattern 3: Instance swap (Viability)
    overlay_manager = self.overlay_managers[drawing_area]
    viability_loader = overlay_manager.viability_panel_loader
    self.viability_panel_container.remove_all()
    self.viability_panel_container.pack_start(viability_loader.widget)
    
    # Pattern 4: Instance swap (Report) - separate callback
```

**New Logic** (unified pattern):
```python
def _on_notebook_switch_page(self, notebook, page, page_num):
    drawing_area = self._extract_drawing_area(page)
    overlay_manager = self.overlay_managers[drawing_area]
    
    # Unified pattern: Swap panel instances for all panels
    self._swap_panel_instance('pathways', overlay_manager.pathway_panel_loader, 
                             self.pathways_panel_container)
    self._swap_panel_instance('analyses', overlay_manager.analyses_panel_loader, 
                             self.analyses_panel_container)
    self._swap_panel_instance('topology', overlay_manager.topology_panel_loader, 
                             self.topology_panel_container)
    self._swap_panel_instance('viability', overlay_manager.viability_panel_loader, 
                             self.viability_panel_container)
    self._swap_panel_instance('report', overlay_manager.report_panel_loader, 
                             self.report_panel_container)
    # Files panel: N/A (stateless)

def _swap_panel_instance(self, panel_name, panel_loader, container):
    """Swap panel instance for active document.
    
    Generic helper that works for all panels following the per-document pattern.
    """
    if not panel_loader or not container:
        return
    
    # Clear container
    for child in container.get_children():
        container.remove(child)
    
    # Remove from old parent (if any)
    current_parent = panel_loader.widget.get_parent()
    if current_parent:
        current_parent.remove(panel_loader.widget)
    
    # Pack new panel
    container.pack_start(panel_loader.widget, True, True, 0)
    panel_loader.widget.show_all()
```

---

## Implementation Plan

### Phase 1: Pathways Panel (Day 1)

**Complexity**: High (8 categories, most complex state)

**Steps**:

#### 1.1 Update OverlayManager
```python
# model_canvas_loader.py - OverlayManager class
class OverlayManager:
    def __init__(self, drawing_area):
        # ... existing code ...
        self.pathway_panel_loader = None  # NEW
```

#### 1.2 Create Panel Instance Per Document
```python
# model_canvas_loader.py - add_document() method
def add_document(self, filename='default'):
    # ... existing code creating drawing_area ...
    
    # Create overlay manager
    overlay_manager = OverlayManager(drawing_area)
    
    # ... existing code creating canvas_manager, simulation_controller ...
    
    # NEW: Create Pathways panel instance for this document
    if hasattr(self, 'workspace_settings') and hasattr(self, 'parent_window'):
        from shypn.helpers.pathway_panel_loader import create_pathway_panel_for_document
        overlay_manager.pathway_panel_loader = create_pathway_panel_for_document(
            model_canvas_manager=canvas_manager,
            workspace_settings=self.workspace_settings,
            parent_window=self.parent_window
        )
```

#### 1.3 Create Panel Container in Main App
```python
# shypn.py - Replace panel creation with container creation
# OLD CODE (remove):
# pathway_panel_loader = create_pathway_panel(model_canvas=model_canvas_loader, ...)
# model_canvas_loader.pathway_panel_loader = pathway_panel_loader

# NEW CODE:
# Create empty container (panels will be swapped in)
pathways_panel_container = main_builder.get_object('pathways_panel_container')
if not pathways_panel_container:
    pathways_panel_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    pathways_panel_container.set_name('pathways_panel_container')

# Store container reference for tab switching
model_canvas_loader.pathways_panel_container = pathways_panel_container
```

#### 1.4 Update Tab Switch Handler
```python
# model_canvas_loader.py - _on_notebook_switch_page()
def _on_notebook_switch_page(self, notebook, page, page_num):
    # ... existing code ...
    
    # Swap Pathways panel instance
    if hasattr(self, 'pathways_panel_container') and self.pathways_panel_container:
        overlay_manager = self.overlay_managers[drawing_area]
        if hasattr(overlay_manager, 'pathway_panel_loader'):
            pathway_loader = overlay_manager.pathway_panel_loader
            self._swap_panel_instance('pathways', pathway_loader, self.pathways_panel_container)
```

#### 1.5 Update Panel Loader
```python
# helpers/pathway_panel_loader.py - NEW file or update existing
class PathwayPanelLoader:
    """Loader for per-document PathwayOperationsPanel instances."""
    
    def __init__(self, panel):
        self.panel = panel
        self.widget = panel  # Panel is a Gtk.Box
        self.is_hanged = True  # Always docked (no float/detach)
        
    def add_to_stack(self, stack, container, name):
        """Legacy method for compatibility (no longer used)."""
        pass

def create_pathway_panel_for_document(model_canvas_manager, workspace_settings=None, parent_window=None):
    """Factory function for creating per-document Pathways panel."""
    panel = PathwayOperationsPanel(
        workspace_settings=workspace_settings,
        parent_window=parent_window,
        project=None,
        model_canvas=model_canvas_manager
    )
    return PathwayPanelLoader(panel)
```

#### 1.6 Testing
- [ ] Create 2 documents
- [ ] Import KEGG pathway in Document A
- [ ] Switch to Document B
- [ ] Verify: KEGG form is empty in Document B
- [ ] Switch back to Document A
- [ ] Verify: KEGG pathway ID preserved
- [ ] Test all 8 categories for state preservation

---

### Phase 2: Analyses Panel (Day 2)

**Complexity**: Medium (3 categories, plot management)

**Steps**:

#### 2.1 Update OverlayManager
```python
self.analyses_panel_loader = None  # NEW (right panel)
```

#### 2.2 Create Panel Instance Per Document
```python
# In add_document() - after simulation_controller creation
from shypn.helpers.right_panel_loader import create_analyses_panel_for_document
overlay_manager.analyses_panel_loader = create_analyses_panel_for_document(
    model=canvas_manager,
    data_collector=data_collector
)
```

#### 2.3 Create Panel Container
```python
# shypn.py - Replace right_panel_loader with container
analyses_panel_container = main_builder.get_object('analyses_panel_container')
model_canvas_loader.analyses_panel_container = analyses_panel_container
```

#### 2.4 Update Tab Switch Handler
```python
# Swap Analyses panel instance
self._swap_panel_instance('analyses', overlay_manager.analyses_panel_loader, 
                         self.analyses_panel_container)
```

#### 2.5 Update Panel Loader
```python
# helpers/right_panel_loader.py
class AnalysesPanelLoader:
    def __init__(self, panel, data_collector):
        self.panel = panel
        self.widget = panel
        self.data_collector = data_collector
        # Keep convenience accessors
        self.place_panel = panel.places_category.panel
        self.transition_panel = panel.transitions_category.panel
        self.plotting_panel = panel.plotting_category.panel

def create_analyses_panel_for_document(model, data_collector):
    panel = DynamicAnalysesPanel(model=model, data_collector=data_collector)
    return AnalysesPanelLoader(panel, data_collector)
```

#### 2.6 Remove State Clearing Logic
```python
# model_canvas_loader.py - REMOVE this logic (no longer needed):
# OLD CODE (DELETE):
# if self.right_panel_loader:
#     transition_panel = self.right_panel_loader.transition_panel
#     transition_panel.selected_objects.clear()  # No longer needed!
#     place_panel = self.right_panel_loader.place_panel
#     place_panel.selected_objects.clear()  # No longer needed!
```

#### 2.7 Testing
- [ ] Create 2 documents
- [ ] Add 3 transitions to analysis in Document A
- [ ] Switch to Document B
- [ ] Verify: Analysis list is empty (separate instance)
- [ ] Add 2 places to analysis in Document B
- [ ] Switch back to Document A
- [ ] **Verify: 3 transitions still selected** ✨ (NEW BEHAVIOR - state preserved!)

---

### Phase 3: Topology Panel (Day 3)

**Complexity**: Medium-High (4 categories, cache management per-instance)

**Steps**:

#### 3.1 Update OverlayManager
```python
self.topology_panel_loader = None  # NEW
```

#### 3.2 Create Panel Instance Per Document
```python
# In add_document()
from shypn.helpers.topology_panel_loader import create_topology_panel_for_document
overlay_manager.topology_panel_loader = create_topology_panel_for_document(
    model=canvas_manager
)
```

#### 3.3 Create Panel Container
```python
# shypn.py
topology_panel_container = main_builder.get_object('topology_panel_container')
model_canvas_loader.topology_panel_container = topology_panel_container
```

#### 3.4 Update Tab Switch Handler
```python
# Swap Topology panel instance
self._swap_panel_instance('topology', overlay_manager.topology_panel_loader, 
                         self.topology_panel_container)
```

#### 3.5 Update Topology Controller for Per-Instance Cache
```python
# topology/topology_controller.py
class TopologyController:
    def __init__(self, model):
        self.model = model
        # Cache is now per-instance (each document has its own controller)
        self.cache = {}  # No longer keyed by drawing_area - just cache results
        
    def run_structural_analysis(self):
        # Check instance cache
        if 'structural' in self.cache:
            return self.cache['structural']
        
        # Run analysis
        results = self._compute_structural_analysis()
        self.cache['structural'] = results
        return results
```

#### 3.6 Remove Global on_tab_switched Logic
```python
# shypn.py - REMOVE topology tab switching callback:
# OLD CODE (DELETE):
# def on_canvas_tab_switched(notebook, page, page_num):
#     topology_panel_loader.controller.on_tab_switched(drawing_area)
# model_canvas_loader.notebook.connect('switch-page', on_canvas_tab_switched)

# NEW: Not needed! Each document has its own controller with own cache
```

#### 3.7 Testing
- [ ] Create 2 documents
- [ ] Run Structural Analysis in Document A (takes 5 seconds)
- [ ] Switch to Document B
- [ ] Run Structural Analysis in Document B (takes 5 seconds)
- [ ] Switch back to Document A
- [ ] **Verify: Results load instantly (cached in A's controller)** ✨
- [ ] Modify Document A (add transition)
- [ ] **Verify: Cache invalidated, must re-run** ✨

---

### Phase 4: Integration & Testing (Day 4-5)

#### 4.1 Unified Tab Switch Logic
```python
# model_canvas_loader.py - Clean, unified handler
def _on_notebook_switch_page(self, notebook, page, page_num):
    """Handle tab switching - swap all panel instances."""
    drawing_area = self._extract_drawing_area(page)
    if not drawing_area:
        return
    
    overlay_manager = self.overlay_managers.get(drawing_area)
    if not overlay_manager:
        return
    
    # Swap all panel instances (single pattern for all)
    self._swap_panel_instance('pathways', overlay_manager.pathway_panel_loader, 
                             getattr(self, 'pathways_panel_container', None))
    self._swap_panel_instance('analyses', overlay_manager.analyses_panel_loader, 
                             getattr(self, 'analyses_panel_container', None))
    self._swap_panel_instance('topology', overlay_manager.topology_panel_loader, 
                             getattr(self, 'topology_panel_container', None))
    self._swap_panel_instance('viability', overlay_manager.viability_panel_loader, 
                             getattr(self, 'viability_panel_container', None))
    self._swap_panel_instance('report', overlay_manager.report_panel_loader, 
                             getattr(self, 'report_panel_container', None))
```

#### 4.2 Cleanup Old Code
- [ ] Remove shared panel instance creation from shypn.py
- [ ] Remove set_model_canvas() calls from tab switch handler
- [ ] Remove state clearing logic (no longer needed)
- [ ] Remove on_tab_switched() callbacks
- [ ] Update comments to reflect new architecture

#### 4.3 Unit Tests
```python
# tests/test_per_document_panels.py
def test_pathways_panel_per_document():
    """Each document should have its own PathwayOperationsPanel."""
    loader = ModelCanvasLoader()
    
    page_a, da_a = loader.add_document(filename='doc_a')
    page_b, da_b = loader.add_document(filename='doc_b')
    
    panel_a = loader.overlay_managers[da_a].pathway_panel_loader.panel
    panel_b = loader.overlay_managers[da_b].pathway_panel_loader.panel
    
    assert panel_a is not panel_b
    assert id(panel_a) != id(panel_b)

def test_analyses_panel_preserves_selections():
    """Analysis selections should be preserved per document."""
    loader = ModelCanvasLoader()
    
    page_a, da_a = loader.add_document(filename='doc_a')
    page_b, da_b = loader.add_document(filename='doc_b')
    
    # Add transitions to analysis in Doc A
    panel_a = loader.overlay_managers[da_a].analyses_panel_loader.panel
    manager_a = loader.canvas_managers[da_a]
    transition = manager_a.transitions[0]
    panel_a.transitions_category.panel.selected_objects.append(transition)
    
    # Switch to Doc B
    loader.notebook.set_current_page(page_b)
    
    # Doc B should have empty selections
    panel_b = loader.overlay_managers[da_b].analyses_panel_loader.panel
    assert len(panel_b.transitions_category.panel.selected_objects) == 0
    
    # Switch back to Doc A
    loader.notebook.set_current_page(page_a)
    
    # Doc A should still have its selection ✨
    assert len(panel_a.transitions_category.panel.selected_objects) == 1
    assert panel_a.transitions_category.panel.selected_objects[0] == transition
```

#### 4.4 Integration Testing
- [ ] Test with 5 open documents
- [ ] Rapid tab switching (stress test)
- [ ] Memory profiling (ensure no leaks)
- [ ] Close documents (verify cleanup)
- [ ] Save/load documents (state persistence)

#### 4.5 Documentation
- [ ] Update PANEL_TAB_SWITCHING_AUDIT.md
- [ ] Add architecture diagram to doc/
- [ ] Update developer guide
- [ ] Add code comments to overlay_manager

---

## Migration Checklist

### Pre-Migration
- [x] Audit current panel architecture (COMPLETED)
- [ ] Create normalization plan (THIS DOCUMENT)
- [ ] Review plan with maintainers
- [ ] Set up feature branch: `feature/per-document-panels`

### Phase 1: Pathways Panel
- [ ] Update OverlayManager class
- [ ] Create pathway_panel_loader factory
- [ ] Update add_document() to create per-document instances
- [ ] Update tab switch handler
- [ ] Update shypn.py to use container
- [ ] Test state preservation
- [ ] Commit: "refactor: Pathways panel per-document instances"

### Phase 2: Analyses Panel
- [ ] Update OverlayManager class
- [ ] Create analyses_panel_loader factory
- [ ] Update add_document()
- [ ] Update tab switch handler
- [ ] Remove state clearing logic
- [ ] Update shypn.py to use container
- [ ] Test selection preservation
- [ ] Commit: "refactor: Analyses panel per-document instances"

### Phase 3: Topology Panel
- [ ] Update OverlayManager class
- [ ] Create topology_panel_loader factory
- [ ] Update TopologyController for per-instance cache
- [ ] Update add_document()
- [ ] Update tab switch handler
- [ ] Remove on_tab_switched callback
- [ ] Update shypn.py to use container
- [ ] Test cache isolation
- [ ] Commit: "refactor: Topology panel per-document instances"

### Phase 4: Integration
- [ ] Unify tab switch handler (_swap_panel_instance)
- [ ] Clean up old code
- [ ] Add unit tests
- [ ] Integration testing (5+ documents)
- [ ] Memory profiling
- [ ] Update documentation
- [ ] Commit: "refactor: Unified per-document panel architecture"

### Post-Migration
- [ ] Merge feature branch to main
- [ ] Update CHANGELOG.md
- [ ] Tag release: v2.0.0 (breaking architecture change)
- [ ] Monitor for issues

---

## Risk Assessment

### High Risk: Memory Leaks

**Risk**: Panel instances not cleaned up when documents close.

**Mitigation**:
1. Add explicit cleanup in close_document()
2. Verify with memory profiler
3. Add weak references if needed

**Test**:
```python
def test_panel_cleanup_on_document_close():
    loader = ModelCanvasLoader()
    page, da = loader.add_document()
    
    # Get panel reference
    panel_id = id(loader.overlay_managers[da].pathway_panel_loader.panel)
    
    # Close document
    loader.close_document(da)
    
    # Verify panel is destroyed (garbage collected)
    import gc
    gc.collect()
    # Check if panel_id is still in memory
```

---

### Medium Risk: Backward Compatibility

**Risk**: Existing code expects shared panel instances.

**Affected Code**:
- Right-click context menus (expect single right_panel_loader)
- Report refresh callbacks (expect single pathway_panel_loader)
- External plugins (if any)

**Mitigation**:
1. Keep backward-compatible accessors:
```python
# model_canvas_loader.py
@property
def right_panel_loader(self):
    """Backward-compatible accessor for current document's analyses panel."""
    drawing_area = self.get_current_document()
    if drawing_area in self.overlay_managers:
        return self.overlay_managers[drawing_area].analyses_panel_loader
    return None

@property
def pathway_panel_loader(self):
    """Backward-compatible accessor for current document's pathways panel."""
    drawing_area = self.get_current_document()
    if drawing_area in self.overlay_managers:
        return self.overlay_managers[drawing_area].pathway_panel_loader
    return None
```

2. Add deprecation warnings
3. Update all internal usage

---

### Low Risk: Performance Degradation

**Risk**: Creating N panel instances slows down document creation.

**Measurement**:
- Current: Creating document takes ~200ms
- With 3 more panels: +50-100ms (panel instantiation)
- Total: ~300ms (still acceptable)

**Mitigation**:
1. Lazy panel creation (only when user first opens panel)
2. Progress indicator for document creation
3. Async panel creation (if needed)

**Decision**: ✅ ACCEPT - 300ms is acceptable for document creation.

---

## Success Metrics

### User Experience
- [ ] Tab switching preserves all panel state
- [ ] Consistent behavior across all panels
- [ ] No visual glitches during tab switch
- [ ] Tab switch latency < 50ms

### Code Quality
- [ ] Single unified tab switch pattern
- [ ] Test coverage > 90%
- [ ] No memory leaks (verified with profiler)
- [ ] Code reduction: -500 LOC (remove state clearing logic)

### Performance
- [ ] Document creation time < 500ms
- [ ] Memory usage increase < 50MB for 10 documents
- [ ] No degradation in simulation performance

### Maintainability
- [ ] New panels can be added in < 2 hours
- [ ] Clear architecture documentation
- [ ] No special-case logic per panel

---

## Timeline

### Week 1: Implementation
- **Day 1 (Mon)**: Phase 1 - Pathways Panel
- **Day 2 (Tue)**: Phase 2 - Analyses Panel
- **Day 3 (Wed)**: Phase 3 - Topology Panel
- **Day 4 (Thu)**: Phase 4 - Integration & cleanup
- **Day 5 (Fri)**: Testing & documentation

### Week 2: Refinement
- **Day 1 (Mon)**: Bug fixes from testing
- **Day 2 (Tue)**: Memory profiling & optimization
- **Day 3 (Wed)**: Code review & refactoring
- **Day 4 (Thu)**: Documentation finalization
- **Day 5 (Fri)**: Merge to main, release v2.0.0

---

## Alternatives Considered

### Alternative 1: Keep Current Mixed Architecture

**Pros**:
- No development time needed
- No migration risk
- Lower memory usage

**Cons**:
- Inconsistent user experience
- Complex maintenance (5 different patterns)
- State clearing bugs continue
- Cross-contamination risks

**Decision**: ❌ REJECT - Technical debt too high

---

### Alternative 2: Stateless Panels (No Per-Document State)

**Pros**:
- Lowest memory usage
- Simplest code
- Fast tab switching

**Cons**:
- Terrible user experience (lose all state on switch)
- Users must re-enter form data constantly
- No selection preservation
- Not competitive with modern IDEs

**Decision**: ❌ REJECT - UX unacceptable

---

### Alternative 3: Serialize/Deserialize State on Tab Switch

**Pros**:
- Single panel instance (lower memory)
- State preserved (serialize to dict, restore from dict)

**Cons**:
- Complex serialization code for each panel
- Slow tab switching (serialize + deserialize)
- Error-prone (miss a field = state loss)
- Still need state clearing for safety

**Decision**: ❌ REJECT - Complexity without benefits

---

### Alternative 4: Per-Document Instances (SELECTED)

**Pros**:
- ✅ Best user experience (state preservation)
- ✅ Simplest code (no serialization, no clearing)
- ✅ Fastest tab switching (just widget swap)
- ✅ Zero cross-contamination (complete isolation)
- ✅ Consistent architecture (one pattern)

**Cons**:
- ❌ Higher memory usage (+12MB for 2 docs)
- ❌ Migration effort (3-5 days)
- ❌ More complex initialization

**Decision**: ✅ **SELECTED** - Best tradeoff for long-term maintainability and UX.

---

## Conclusion

**Recommendation**: ✅ **PROCEED** with per-document panel normalization.

**Justification**:
1. **User Experience**: Consistent, predictable behavior across all panels
2. **Code Quality**: Single unified architecture, easier to maintain
3. **Performance**: Acceptable memory cost for significant UX improvement
4. **Future-Proof**: Clear pattern for adding new panels

**Next Steps**:
1. Review this plan with maintainers
2. Create feature branch: `feature/per-document-panels`
3. Begin Phase 1 implementation (Pathways Panel)

---

**Status**: ⏳ AWAITING APPROVAL

**Estimated Completion**: 2 weeks from approval

**Risk Level**: Medium (migration complexity, memory usage)

**Benefit Level**: High (UX improvement, code simplification)

---

**End of Plan**
