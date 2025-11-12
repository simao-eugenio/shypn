# Viability Panel Refactor Plan

**Date:** November 12, 2025  
**Branch:** viability  
**Goal:** Transform Viability Panel into a locality/subnet investigation tool with on-demand analysis

---

## Overview

### Current Issues
- ❌ Reactive architecture causing performance problems
- ❌ Automatic callbacks interfering with Report Panel
- ❌ Simulation lifecycle coupling causing hangs
- ❌ Too broad "Analyze All" approach
- ❌ Complex observer pattern creating maintenance burden

### Proposed Solution
- ✅ On-demand, user-triggered analysis only
- ✅ Locality-focused investigation (1 transition)
- ✅ Subnet analysis (multiple transitions as connected subgraph)
- ✅ Multi-level analysis (local → dependencies → boundary → conservation)
- ✅ Pull-based data access (no observers/callbacks)
- ✅ Clean OOP architecture with separate modules

---

## User Workflows

### Workflow 1: Single Locality Investigation
```
1. User has doubt about transition T3
2. Right-click T3 → "Investigate Locality"
3. Viability analyzes T3 + inputs/outputs
4. Shows local issues and fixes
5. User applies fixes
```

### Workflow 2: Subnet Investigation
```
1. User selects T3 from analyses list
2. User also selects T7 from analyses list
3. User clicks "Investigate Selected"
4. System checks if T3 and T7 are CONNECTED (share places)
5. If connected:
   - Viability forms subnet and analyzes:
     • Individual locality issues
     • Inter-locality dependencies
     • Subnet boundary flow
     • Subnet conservation laws
   - Shows coordinated fixes
6. If NOT connected:
   - Shows error: "Selected localities are not connected"
   - Suggests which localities CAN form subnets together
7. User applies fixes in correct order
```

**IMPORTANT: Subnet Connectivity Requirement**
- Subnets are only formed from localities that share at least one place
- Cannot create "artificial" subnets from disconnected localities
- System validates connectivity using graph traversal (BFS)
- If user selects disconnected localities, error is shown with suggestions

---

## Architecture

### Investigation Modes

**Single Locality Mode:**
- Scope: 1 transition + direct inputs/outputs
- Analysis: Local issues only
- Fixes: Individual suggestions

**Subnet Mode:**
- Scope: N transitions + all touched places/arcs
- Analysis: 4 levels
  1. Individual locality issues (per transition)
  2. Inter-locality dependencies (flow between localities)
  3. Boundary analysis (subnet inputs/outputs)
  4. Conservation analysis (P-invariants, mass balance)
- Fixes: Coordinated suggestions with sequencing

### Module Structure

```
src/shypn/ui/panels/viability/
├── __init__.py
├── viability_panel.py              # Main panel (container/orchestrator)
├── investigation.py                # Investigation data classes
├── subnet_builder.py               # Build subnet from localities
├── analysis/
│   ├── __init__.py
│   ├── base_analyzer.py            # Base analysis interface
│   ├── locality_analyzer.py        # Level 1: Single locality
│   ├── dependency_analyzer.py      # Level 2: Dependencies
│   ├── boundary_analyzer.py        # Level 3: Boundary flow
│   └── conservation_analyzer.py    # Level 4: Conservation
├── ui/
│   ├── __init__.py
│   ├── investigation_view.py       # Single locality view
│   ├── subnet_view.py              # Subnet investigation view
│   ├── topology_viewer.py          # Mini topology canvas
│   └── suggestion_widgets.py       # Apply/Preview/Undo buttons
├── fixes/
│   ├── __init__.py
│   ├── fix_sequencer.py            # Order fixes by dependencies
│   ├── fix_applier.py              # Apply fixes to model
│   └── fix_predictor.py            # Predict fix impact
└── data/
    ├── __init__.py
    ├── data_puller.py              # Pull KB/sim data on-demand
    └── data_cache.py               # Cache for efficiency
```

---

## Data Classes

### Investigation
```python
@dataclass
class LocalityInvestigation:
    """Single locality investigation."""
    transition: Transition
    locality: Locality
    timestamp: datetime
    mode: InvestigationMode
    issues: List[Issue]
    suggestions: List[Suggestion]
    kb_snapshot: KnowledgeBase
    sim_snapshot: Optional[SimData]

@dataclass
class SubnetInvestigation:
    """Multi-locality subnet investigation."""
    localities: List[LocalityInvestigation]
    subnet: Subnet
    timestamp: datetime
    level1_issues: Dict[str, List[Issue]]  # Per locality
    level2_dependencies: List[Dependency]
    level3_boundary: BoundaryAnalysis
    level4_conservation: ConservationAnalysis
    suggestions: List[CoordinatedSuggestion]
```

### Subnet
```python
@dataclass
class Subnet:
    """Subnet extracted from multiple localities."""
    transitions: Set[Transition]
    places: Set[Place]
    arcs: Set[Arc]
    boundary_places: Set[Place]
    internal_places: Set[Place]
    boundary_inputs: List[Place]
    boundary_outputs: List[Place]
    dependencies: List[Dependency]

@dataclass
class Dependency:
    """Flow dependency between localities."""
    source_transition: Transition
    target_transition: Transition
    connecting_place: Place
    flow_rate: Optional[float]
```

---

## Phase 1: Remove Reactive Complexity

**Goal:** Stop interfering with simulation/Report Panel

**Duration:** 1 day

**Changes to `viability_panel.py`:**
1. ❌ Remove `on_simulation_complete()` method
2. ❌ Remove `set_drawing_area()` callback registration
3. ❌ Remove `_ensure_simulation_callback_registered()`
4. ❌ Remove `_pending_callback_registration` tracking
5. ❌ Remove `_feed_observer_with_kb_data()` automatic calls
6. ✅ Keep only `on_transition_selected()` as entry point

**Result:** Panel becomes completely passive

**Files Modified:**
- `viability_panel.py`

**Tests:**
- ✅ App starts without errors
- ✅ Report Panel works normally
- ✅ Simulation runs without hanging
- ✅ No automatic updates during simulation

---

## Phase 2: Subnet Construction

**Goal:** Build subnet structure from multiple localities

**Duration:** 2 days

**New Module: `subnet_builder.py`**
```python
class SubnetBuilder:
    """Extract and analyze subnet from localities."""
    
    def build_subnet(self, localities: List[Locality]) -> Subnet:
        """Build subnet from localities.
        
        Raises ValueError if localities are not connected.
        """
    
    def _are_localities_connected(self, localities) -> bool:
        """Check if localities share places (BFS connectivity check)."""
        
    def find_connected_components(self, localities) -> List[List[int]]:
        """Find connected components for error messages."""
        
    def classify_places(self, places: Set[Place], 
                       transitions: Set[Transition]) -> Tuple[Set, Set]:
        """Classify places as boundary vs internal."""
        
    def find_dependencies(self, subnet: Subnet) -> List[Dependency]:
        """Find dependencies between localities."""
        
    def analyze_topology(self, subnet: Subnet) -> Dict:
        """Analyze subnet topology properties."""
```

**New Module: `investigation.py`**
```python
class InvestigationMode(Enum):
    SINGLE_LOCALITY = "single"
    SUBNET = "subnet"

@dataclass
class LocalityInvestigation:
    """Investigation data."""
    # Fields as defined above

class InvestigationManager:
    """Manage active investigations."""
    
    def create_investigation(self, transitions, localities) -> Investigation:
        """Create new investigation."""
        
    def add_locality(self, investigation_id, transition, locality):
        """Add locality to existing investigation."""
        
    def remove_locality(self, investigation_id, transition_id):
        """Remove locality from investigation."""
```

**Files Created:**
- `investigation.py`
- `subnet_builder.py`

**Tests:**
- `tests/viability/test_subnet_builder.py`
- `tests/viability/test_investigation.py`

---

## Phase 3: Multi-Level Analysis Engine

**Goal:** Implement 4-level subnet analysis

**Duration:** 3 days

### Level 1: Locality Analyzer
**New Module: `analysis/locality_analyzer.py`**
```python
class LocalityAnalyzer(BaseAnalyzer):
    """Analyze single locality issues."""
    
    def analyze_structural(self, locality, kb) -> List[Issue]:
        """Structural issues (missing arcs, etc.)."""
        
    def analyze_biological(self, locality, kb) -> List[Issue]:
        """Biological issues (stoichiometry, etc.)."""
        
    def analyze_kinetic(self, locality, kb, sim_data) -> List[Issue]:
        """Kinetic issues (rates, etc.)."""
```

### Level 2: Dependency Analyzer
**New Module: `analysis/dependency_analyzer.py`**
```python
class DependencyAnalyzer(BaseAnalyzer):
    """Analyze dependencies between localities."""
    
    def find_flow_dependencies(self, subnet) -> List[Dependency]:
        """Find which localities feed which."""
        
    def detect_cascading_issues(self, subnet, locality_issues) -> List[Issue]:
        """Detect issues that cascade through subnet."""
        
    def analyze_fix_impacts(self, suggestion, subnet) -> List[Impact]:
        """Predict how fix affects other localities."""
```

### Level 3: Boundary Analyzer
**New Module: `analysis/boundary_analyzer.py`**
```python
class BoundaryAnalyzer(BaseAnalyzer):
    """Analyze subnet boundary flow."""
    
    def analyze_boundary_flow(self, subnet, sim_data) -> BoundaryAnalysis:
        """Check inputs/outputs over time."""
        
    def detect_accumulation(self, subnet, sim_data) -> List[Issue]:
        """Detect boundary place accumulation."""
        
    def detect_depletion(self, subnet, sim_data) -> List[Issue]:
        """Detect boundary place depletion."""
```

### Level 4: Conservation Analyzer
**New Module: `analysis/conservation_analyzer.py`**
```python
class ConservationAnalyzer(BaseAnalyzer):
    """Analyze conservation within subnet."""
    
    def check_p_invariants(self, subnet, kb) -> List[Issue]:
        """Check P-invariants internal to subnet."""
        
    def check_mass_balance(self, subnet, kb) -> List[Issue]:
        """Check mass balance across subnet."""
        
    def detect_leaks(self, subnet, kb) -> List[Issue]:
        """Detect conservation leaks."""
```

**Files Created:**
- `analysis/__init__.py`
- `analysis/base_analyzer.py`
- `analysis/locality_analyzer.py`
- `analysis/dependency_analyzer.py`
- `analysis/boundary_analyzer.py`
- `analysis/conservation_analyzer.py`

**Tests:**
- `tests/viability/test_locality_analyzer.py`
- `tests/viability/test_dependency_analyzer.py`
- `tests/viability/test_boundary_analyzer.py`
- `tests/viability/test_conservation_analyzer.py`

---

## Phase 4: Subnet UI Components

**Goal:** Render subnet investigation views

**Duration:** 2 days

### Investigation View (Single Locality)
**New Module: `ui/investigation_view.py`**
```python
class InvestigationView(Gtk.Box):
    """Single locality investigation UI."""
    
    def __init__(self, investigation: LocalityInvestigation):
        """Wayland-safe GTK construction."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.investigation = investigation
        self._build_ui()
    
    def _build_ui(self):
        """Build complete investigation view."""
        self._build_header()
        self._build_locality_overview()
        self._build_issues_section()
        self._build_suggestions_section()
```

### Subnet View (Multiple Localities)
**New Module: `ui/subnet_view.py`**
```python
class SubnetView(Gtk.Box):
    """Subnet investigation UI."""
    
    def __init__(self, investigation: SubnetInvestigation):
        """Wayland-safe GTK construction."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.investigation = investigation
        self._build_ui()
    
    def _build_ui(self):
        """Build 4-level subnet view."""
        self._build_header()
        self._build_subnet_overview()
        self._build_level1_section()  # Locality issues
        self._build_level2_section()  # Dependencies
        self._build_level3_section()  # Boundary
        self._build_level4_section()  # Conservation
        self._build_suggestions_section()
```

### Topology Viewer
**New Module: `ui/topology_viewer.py`**
```python
class TopologyViewer(Gtk.DrawingArea):
    """Mini-canvas showing subnet topology."""
    
    def __init__(self, subnet: Subnet):
        """Wayland-safe GTK construction."""
        super().__init__()
        self.subnet = subnet
        self.set_size_request(400, 300)
        self.connect('draw', self.on_draw)
    
    def on_draw(self, widget, cr):
        """Draw subnet topology with Cairo."""
        self._draw_places(cr)
        self._draw_transitions(cr)
        self._draw_arcs(cr)
        self._highlight_boundary(cr)
```

**Files Created:**
- `ui/__init__.py`
- `ui/investigation_view.py`
- `ui/subnet_view.py`
- `ui/topology_viewer.py`
- `ui/suggestion_widgets.py`

**Tests:**
- `tests/viability/test_investigation_view.py`
- `tests/viability/test_subnet_view.py`

---

## Phase 5: Fix Sequencing

**Goal:** Apply fixes in correct dependency order

**Duration:** 2 days

### Fix Sequencer
**New Module: `fixes/fix_sequencer.py`**
```python
class FixSequencer:
    """Order fixes by dependencies."""
    
    def sequence_fixes(self, suggestions: List[Suggestion], 
                      subnet: Subnet) -> List[SequencedFix]:
        """Order suggestions to avoid conflicts."""
        
    def detect_conflicts(self, suggestions: List[Suggestion]) -> List[Conflict]:
        """Find conflicting suggestions."""
        
    def build_dependency_graph(self, suggestions: List[Suggestion]) -> nx.DiGraph:
        """Build fix dependency graph."""
```

### Fix Applier
**New Module: `fixes/fix_applier.py`**
```python
class FixApplier:
    """Apply fixes to model."""
    
    def apply_fix(self, suggestion: Suggestion, model: ShypnModel) -> bool:
        """Apply single fix."""
        
    def apply_sequence(self, fixes: List[SequencedFix], 
                      model: ShypnModel) -> List[bool]:
        """Apply fixes in order."""
        
    def preview_fix(self, suggestion: Suggestion) -> str:
        """Generate preview text."""
        
    def undo_fix(self, suggestion: Suggestion, model: ShypnModel) -> bool:
        """Undo previously applied fix."""
```

### Fix Predictor
**New Module: `fixes/fix_predictor.py`**
```python
class FixPredictor:
    """Predict fix impacts."""
    
    def predict_impact(self, suggestion: Suggestion, 
                      subnet: Subnet) -> Impact:
        """Predict how fix affects subnet."""
        
    def affected_localities(self, suggestion: Suggestion, 
                           subnet: Subnet) -> List[Transition]:
        """Which localities affected by fix."""
        
    def flow_changes(self, suggestion: Suggestion, 
                    subnet: Subnet) -> Dict[Place, float]:
        """Predict flow rate changes."""
```

**Files Created:**
- `fixes/__init__.py`
- `fixes/fix_sequencer.py`
- `fixes/fix_applier.py`
- `fixes/fix_predictor.py`

**Tests:**
- `tests/viability/test_fix_sequencer.py`
- `tests/viability/test_fix_applier.py`
- `tests/viability/test_fix_predictor.py`

---

## Phase 6: Data Layer

**Goal:** On-demand data pulling with caching

**Duration:** 1 day

### Data Puller
**New Module: `data/data_puller.py`**
```python
class DataPuller:
    """Pull data on-demand (no observers)."""
    
    def __init__(self, model_canvas):
        self.model_canvas = model_canvas
        self.cache = DataCache()
    
    def pull_kb(self) -> KnowledgeBase:
        """Pull current KB state."""
        
    def pull_simulation_data(self, transition_id: str) -> Optional[SimData]:
        """Pull simulation data for transition."""
        
    def pull_locality_context(self, transition: Transition, 
                              locality: Locality) -> Dict:
        """Pull all context for locality."""
```

### Data Cache
**New Module: `data/data_cache.py`**
```python
class DataCache:
    """Cache pulled data for efficiency."""
    
    def __init__(self, ttl_seconds: int = 60):
        self._kb_cache = None
        self._sim_cache = {}
        self._cache_time = None
        self._ttl = ttl_seconds
    
    def get_kb(self, puller_func) -> KnowledgeBase:
        """Get KB with caching."""
        
    def get_sim_data(self, transition_id: str, puller_func) -> SimData:
        """Get sim data with caching."""
        
    def invalidate(self):
        """Clear cache."""
```

**Files Created:**
- `data/__init__.py`
- `data/data_puller.py`
- `data/data_cache.py`

**Tests:**
- `tests/viability/test_data_puller.py`
- `tests/viability/test_data_cache.py`

---

## Phase 7: Integration

**Goal:** Wire everything together in viability_panel.py

**Duration:** 1 day

**Refactored `viability_panel.py`:**
```python
class ViabilityPanel(Gtk.Box):
    """Viability investigation panel (on-demand only)."""
    
    def __init__(self, model=None, model_canvas=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.model = model
        self.model_canvas = model_canvas
        
        # Components (minimal, delegated)
        self.investigation_manager = InvestigationManager()
        self.subnet_builder = SubnetBuilder()
        self.data_puller = DataPuller(model_canvas)
        
        # Analyzers
        self.locality_analyzer = LocalityAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.boundary_analyzer = BoundaryAnalyzer()
        self.conservation_analyzer = ConservationAnalyzer()
        
        # Fix system
        self.fix_sequencer = FixSequencer()
        self.fix_applier = FixApplier()
        self.fix_predictor = FixPredictor()
        
        # Current view
        self.current_view = None
        
        self._build_ui()
    
    def on_transition_selected(self, transition, locality):
        """Main entry point: user right-clicked transition."""
        # Pull data
        context = self.data_puller.pull_locality_context(transition, locality)
        
        # Create investigation
        investigation = self.investigation_manager.create_investigation(
            [transition], [locality]
        )
        
        # Analyze
        self._analyze_and_display(investigation, context)
    
    def on_multiple_selected(self, transitions, localities):
        """Entry point: user selected multiple from list."""
        # Pull data
        context = self.data_puller.pull_subnet_context(transitions, localities)
        
        # Build subnet
        subnet = self.subnet_builder.build_subnet(localities)
        
        # Create subnet investigation
        investigation = self.investigation_manager.create_subnet_investigation(
            transitions, localities, subnet
        )
        
        # Analyze at 4 levels
        self._analyze_subnet_and_display(investigation, context)
```

**Files Modified:**
- `viability_panel.py` (major refactor)

**Tests:**
- `tests/viability/test_viability_panel_integration.py`

---

## Wayland Safety Checklist

✅ **All GTK widgets created in GTK thread**
- No widget creation in callbacks from other threads
- All UI updates via GLib.idle_add() if needed

✅ **No DrawingArea manipulation outside draw signal**
- All Cairo drawing in `on_draw` callback only
- No direct window access

✅ **Proper widget lifecycle**
- Always call `show_all()` on containers
- Proper parent-child relationships
- Clean up on destroy

✅ **No X11-specific APIs**
- No GdkX11 imports
- No window.get_xid() calls
- Use GtkDrawingArea for custom drawing

---

## Test Structure

```
tests/viability/
├── __init__.py
├── conftest.py                     # Pytest fixtures
├── test_investigation.py
├── test_subnet_builder.py
├── test_locality_analyzer.py
├── test_dependency_analyzer.py
├── test_boundary_analyzer.py
├── test_conservation_analyzer.py
├── test_fix_sequencer.py
├── test_fix_applier.py
├── test_fix_predictor.py
├── test_data_puller.py
├── test_data_cache.py
├── test_investigation_view.py
├── test_subnet_view.py
└── test_viability_panel_integration.py
```

---

## Success Criteria

### Performance
- ✅ No UI hanging on simulation stop
- ✅ Instant response when idle
- ✅ Panel activation < 100ms

### Functionality
- ✅ Single locality investigation works
- ✅ Subnet investigation works (2+ localities)
- ✅ All 4 analysis levels work
- ✅ Fix application works
- ✅ Fix sequencing prevents conflicts

### Architecture
- ✅ No callbacks to simulation
- ✅ No observers watching KB
- ✅ Pull-based data access only
- ✅ Clean OOP with separate modules
- ✅ 80%+ test coverage

### User Experience
- ✅ Right-click → investigate works
- ✅ Select multiple → subnet analysis works
- ✅ Clear issue/suggestion display
- ✅ Apply fixes without crashes
- ✅ Wayland-safe (no X11 dependencies)

---

## Timeline

| Phase | Duration | Days |
|-------|----------|------|
| Phase 1: Remove Reactive | 1 day | Day 1 |
| Phase 2: Subnet Construction | 2 days | Days 2-3 |
| Phase 3: Multi-Level Analysis | 3 days | Days 4-6 |
| Phase 4: Subnet UI | 2 days | Days 7-8 |
| Phase 5: Fix Sequencing | 2 days | Days 9-10 |
| Phase 6: Data Layer | 1 day | Day 11 |
| Phase 7: Integration | 1 day | Day 12 |
| **Total** | **12 days** | **~2.5 weeks** |

---

## Migration Strategy

1. ✅ Phase 1 first (fixes immediate issues)
2. ✅ Keep old code commented during refactor
3. ✅ Test after each phase
4. ✅ Commit after each phase
5. ✅ Can roll back to any phase if needed

---

## Notes

- **Focus on OOP**: Each analyzer is a separate class
- **Minimize loader code**: viability_panel.py is thin orchestrator
- **Wayland-safe**: All GTK best practices followed
- **Test coverage**: Unit tests for each module
- **Pull-based**: Zero reactive/observer coupling

---

**End of Plan**
