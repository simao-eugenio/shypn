# Refactor Plan: Dynamic Analyses Category

## Current State Analysis

### Existing Structure
```
Report Panel
└── DYNAMIC ANALYSES (parameters_category.py)
    ├── Summary (always visible)
    ├── Show Enrichment Details (expander)
    ├── Show Parameter Sources & Citations (expander)
    └── Simulation Results (expander, placeholder)
```

**Issues with Current Design:**
1. ❌ Named `parameters_category.py` but class is `DynamicAnalysesCategory` (confusing)
2. ❌ "Simulation Results" is just a placeholder label
3. ❌ No actual simulation data collection or analysis
4. ❌ Mixed concerns: Enrichments + Parameters + Simulation (should be separate)
5. ❌ Uses simple TextViews instead of proper tables with sortable columns

---

## Refactored Structure

### New Organization
```
Report Panel
└── DYNAMIC ANALYSES (dynamic_analyses_category.py)
    ├── Summary (always visible - overall stats)
    │
    ├── 📊 Simulation Data (NEW - expander)
    │   ├── Species Concentration Table (sortable, 8 columns)
    │   └── Reaction Activity Table (sortable, 7 columns)
    │
    ├── 📈 Time Series Plots (FUTURE - expander)
    │   ├── Interactive matplotlib plots
    │   └── Click place/transition to add to plot
    │
    ├── 🧪 Kinetic Parameters (EXISTING - refactored expander)
    │   ├── Parameter values table (Km, Vmax, Kcat, Ki)
    │   └── Color-coded by source (Database/Heuristic/Manual)
    │
    └── 📚 Enrichment & Citations (EXISTING - expander)
        ├── BRENDA enrichment details
        └── Parameter sources and citations
```

---

## File Structure Refactoring

### Phase 1: Rename and Reorganize Files

**BEFORE:**
```
src/shypn/ui/panels/report/
├── parameters_category.py          (RENAME → dynamic_analyses_category.py)
├── model_structure_category.py
├── topology_analyses_category.py
└── provenance_category.py
```

**AFTER:**
```
src/shypn/ui/panels/report/
├── dynamic_analyses_category.py    (RENAMED from parameters_category.py)
├── model_structure_category.py
├── topology_analyses_category.py
├── provenance_category.py
└── widgets/
    ├── __init__.py
    ├── species_concentration_table.py    (NEW)
    ├── reaction_activity_table.py        (NEW)
    ├── time_series_plot.py               (FUTURE)
    └── kinetic_parameters_table.py       (NEW - extract from old code)
```

---

## Phase 2: Create Core Data Infrastructure

### New Engine Modules
```
src/shypn/engine/simulation/
├── data_collector.py               (NEW - collects time-series during simulation)
└── analysis/
    ├── __init__.py                 (NEW)
    ├── species_analyzer.py         (NEW - calculates place metrics)
    └── reaction_analyzer.py        (NEW - calculates transition metrics)
```

### New Report Modules
```
src/shypn/report/
├── __init__.py                     (NEW)
├── data_models.py                  (NEW - SpeciesMetrics, ReactionMetrics classes)
└── formatters.py                   (NEW - HTML/CSV/JSON export formatters)
```

---

## Phase 3: Refactor Dynamic Analyses Category

### 3.1 Extract Existing Sub-Categories

**Create: `widgets/kinetic_parameters_table.py`**
- Extract kinetic parameters display from old `parameters_category.py`
- Use proper GTK TreeView with sortable columns
- Color-code rows by source (green=database, yellow=heuristic, orange=manual)

**Create: `widgets/enrichment_details_view.py`**
- Extract enrichment details from old `parameters_category.py`
- Keep TextBuffer format but improve formatting
- Add export to CSV functionality

---

### 3.2 Create New Sub-Categories

**Create: `widgets/species_concentration_table.py`**
```python
class SpeciesConcentrationTable(Gtk.ScrolledWindow):
    """Sortable table for species concentration metrics.
    
    Columns:
    1. Species Name (with color indicator)
    2. Initial Tokens
    3. Final Tokens
    4. Min
    5. Max
    6. Average
    7. Δ (Total Change)
    8. Rate (Δ/time)
    """
    
    def __init__(self):
        # GTK TreeView with ListStore
        # Sortable columns
        # Color indicators for places
        
    def populate(self, species_metrics: List[SpeciesMetrics]):
        # Fill table from analyzer results
        
    def export_csv(self) -> str:
        # Export to CSV format
```

**Create: `widgets/reaction_activity_table.py`**
```python
class ReactionActivityTable(Gtk.ScrolledWindow):
    """Sortable table for reaction activity metrics.
    
    Columns:
    1. Reaction Name
    2. Type (Stochastic/Continuous)
    3. Firing Count
    4. Avg Rate
    5. Total Flux
    6. Contribution %
    7. Status (Inactive/Low/Active/High)
    """
    
    def __init__(self):
        # GTK TreeView with ListStore
        # Sortable columns
        
    def populate(self, reaction_metrics: List[ReactionMetrics]):
        # Fill table from analyzer results
        
    def export_csv(self) -> str:
        # Export to CSV format
```

---

### 3.3 Refactor Category Class

**File: `dynamic_analyses_category.py`**

```python
class DynamicAnalysesCategory(BaseReportCategory):
    """Dynamic Analyses report category.
    
    Displays:
    - Summary: Overall stats (places, transitions, enrichments, simulations)
    - Simulation Data: Species concentration + Reaction activity tables
    - Time Series Plots: Interactive plots (FUTURE)
    - Kinetic Parameters: Parameter values table
    - Enrichment & Citations: BRENDA/SABIO-RK details
    """
    
    def __init__(self, project=None, model_canvas=None):
        super().__init__(
            title="DYNAMIC ANALYSES",
            project=project,
            model_canvas=model_canvas,
            expanded=False
        )
        
        # Panel references
        self.controller = None  # Simulation controller
        
    def _build_content(self):
        """Build category content with sub-expanders."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Summary (always visible)
        self._create_summary_section(box)
        
        # Sub-expander 1: Simulation Data (NEW)
        self._create_simulation_data_section(box)
        
        # Sub-expander 2: Time Series Plots (FUTURE)
        # self._create_time_series_section(box)
        
        # Sub-expander 3: Kinetic Parameters (REFACTORED)
        self._create_kinetic_parameters_section(box)
        
        # Sub-expander 4: Enrichment & Citations (EXISTING)
        self._create_enrichment_section(box)
        
        return box
        
    def _create_summary_section(self, container):
        """Create summary frame (always visible)."""
        frame = Gtk.Frame(label="Summary")
        
        self.summary_label = Gtk.Label()
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        
        frame.add(self.summary_label)
        container.pack_start(frame, False, False, 0)
        
    def _create_simulation_data_section(self, container):
        """Create simulation data expander with tables."""
        expander = Gtk.Expander(label="📊 Simulation Data")
        expander.set_expanded(False)
        
        tables_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Species concentration table
        species_label = Gtk.Label()
        species_label.set_markup("<b>Species Concentration</b>")
        species_label.set_xalign(0)
        tables_box.pack_start(species_label, False, False, 0)
        
        self.species_table = SpeciesConcentrationTable()
        self.species_table.set_size_request(-1, 200)
        tables_box.pack_start(self.species_table, True, True, 0)
        
        # Reaction activity table
        reaction_label = Gtk.Label()
        reaction_label.set_markup("<b>Reaction Activity</b>")
        reaction_label.set_xalign(0)
        tables_box.pack_start(reaction_label, False, False, 0)
        
        self.reaction_table = ReactionActivityTable()
        self.reaction_table.set_size_request(-1, 200)
        tables_box.pack_start(self.reaction_table, True, True, 0)
        
        expander.add(tables_box)
        container.pack_start(expander, True, True, 0)
        
    def _create_kinetic_parameters_section(self, container):
        """Create kinetic parameters expander with table."""
        expander = Gtk.Expander(label="🧪 Kinetic Parameters")
        expander.set_expanded(False)
        
        self.parameters_table = KineticParametersTable()
        self.parameters_table.set_size_request(-1, 200)
        
        expander.add(self.parameters_table)
        container.pack_start(expander, False, False, 0)
        
    def _create_enrichment_section(self, container):
        """Create enrichment details expander."""
        expander = Gtk.Expander(label="📚 Enrichment & Citations")
        expander.set_expanded(False)
        
        # Keep existing TextBuffer implementation
        # (can refactor to table later if needed)
        
        expander.add(textview)
        container.pack_start(expander, False, False, 0)
        
    def refresh(self):
        """Refresh all data from controller and model."""
        self._refresh_summary()
        self._refresh_simulation_data()
        self._refresh_kinetic_parameters()
        self._refresh_enrichment_details()
        
    def _refresh_simulation_data(self):
        """Refresh simulation data tables."""
        if not self.controller or not self.controller.data_collector:
            # No simulation data available
            self.species_table.clear()
            self.reaction_table.clear()
            return
            
        data_collector = self.controller.data_collector
        
        # Check if we have collected data
        if not data_collector.time_points:
            self.species_table.clear()
            self.reaction_table.clear()
            return
            
        # Get duration
        duration = self.controller.settings.duration or 0.0
        
        # Analyze species
        species_analyzer = SpeciesAnalyzer(data_collector)
        species_metrics = species_analyzer.analyze_all_species(duration)
        self.species_table.populate(species_metrics)
        
        # Analyze reactions
        reaction_analyzer = ReactionAnalyzer(data_collector)
        reaction_metrics = reaction_analyzer.analyze_all_reactions(duration)
        self.reaction_table.populate(reaction_metrics)
        
    def set_controller(self, controller):
        """Set simulation controller reference.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
        
        # Register callback for simulation complete
        if controller:
            controller.on_simulation_complete = lambda: self.refresh()
```

---

## Phase 4: Integration Points

### 4.1 Controller Integration

**Modify: `src/shypn/engine/simulation/controller.py`**

```python
class SimulationController:
    def __init__(self, model, ...):
        # ... existing code ...
        self.data_collector = DataCollector(model)
        self.on_simulation_complete = None  # Callback
        
    def start_simulation(self):
        if self.state == SimulationState.IDLE:
            self.data_collector.start_collection()
        # ... existing code ...
        
    def _simulation_step(self):
        # ... existing code ...
        self.data_collector.record_state(self.current_time)
        
    def stop_simulation(self):
        # ... existing code ...
        self.data_collector.stop_collection()
        
        # Notify report panel
        if self.on_simulation_complete:
            self.on_simulation_complete()
```

### 4.2 Report Panel Integration

**Modify: `src/shypn/ui/panels/report/report_panel.py`**

```python
class ReportPanel(Gtk.Box):
    def __init__(self, ...):
        # ... existing code ...
        
    def set_simulation_controller(self, controller):
        """Set simulation controller for dynamic analyses.
        
        Args:
            controller: SimulationController instance
        """
        # Find dynamic analyses category and set controller
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.set_controller(controller)
                break
```

### 4.3 Loader Integration

**Modify: `src/shypn/helpers/report_panel_loader.py`**

```python
def load_report_panel(..., controller):
    """Load report panel.
    
    Args:
        controller: SimulationController instance
    """
    # ... existing code ...
    
    # Wire up controller reference
    report_panel.set_simulation_controller(controller)
    
    return report_panel
```

---

## Phase 5: Data Models

### Create: `src/shypn/report/data_models.py`

```python
"""Data models for report generation."""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ActivityStatus(Enum):
    """Reaction activity classification."""
    INACTIVE = "Inactive"
    LOW = "Low"
    ACTIVE = "Active"
    HIGH = "High"


@dataclass
class SpeciesMetrics:
    """Metrics for a single species (place)."""
    place_id: str
    place_name: str
    initial_tokens: int = 0
    final_tokens: int = 0
    min_tokens: int = 0
    max_tokens: int = 0
    avg_tokens: float = 0.0
    total_change: int = 0
    change_rate: float = 0.0  # tokens per time unit
    color: str = "#000000"  # Place color


@dataclass
class ReactionMetrics:
    """Metrics for a single reaction (transition)."""
    transition_id: str
    transition_name: str
    transition_type: str = "stochastic"
    firing_count: int = 0
    average_rate: float = 0.0
    total_flux: int = 0
    contribution: float = 0.0  # percentage
    status: ActivityStatus = ActivityStatus.INACTIVE


@dataclass
class KineticParameter:
    """Single kinetic parameter with metadata."""
    transition_id: str
    transition_name: str
    parameter_name: str  # "Km", "Vmax", "Kcat", "Ki"
    value: float
    units: str
    source: str  # "Database", "Heuristic", "Manual", "Default"
    ec_number: Optional[str] = None
    substrate: Optional[str] = None
    organism: Optional[str] = None
    citation: Optional[str] = None
```

---

## Implementation Order

### Sprint 1: Core Infrastructure (3-4 hours)
1. ✅ Create `data_collector.py`
2. ✅ Create `analysis/species_analyzer.py`
3. ✅ Create `analysis/reaction_analyzer.py`
4. ✅ Create `report/data_models.py`
5. ✅ Add `firing_count` to `Transition` class
6. ✅ Integrate `DataCollector` into `controller.py`

### Sprint 2: Table Widgets (3-4 hours)
7. ✅ Create `widgets/species_concentration_table.py`
8. ✅ Create `widgets/reaction_activity_table.py`
9. ✅ Create `widgets/kinetic_parameters_table.py` (extract from old code)

### Sprint 3: Category Refactoring (2-3 hours)
10. ✅ Rename `parameters_category.py` → `dynamic_analyses_category.py`
11. ✅ Refactor category with new sub-expanders
12. ✅ Integrate new tables into category
13. ✅ Extract enrichment details into separate view

### Sprint 4: Integration (1-2 hours)
14. ✅ Update `report_panel.py` to set controller reference
15. ✅ Update `report_panel_loader.py` to pass controller
16. ✅ Wire up simulation complete callback
17. ✅ Test end-to-end flow

### Sprint 5: Testing & Polish (2-3 hours)
18. ✅ Write unit tests for analyzers
19. ✅ Write integration test for full flow
20. ✅ Manual testing with glycolysis model
21. ✅ Add export functionality (CSV)
22. ✅ Documentation updates

---

## Benefits of Refactoring

### Code Quality
- ✅ **Separation of Concerns**: Data collection, analysis, and display are separate
- ✅ **Reusability**: Analyzers can be used outside Report Panel
- ✅ **Testability**: Each component can be unit tested
- ✅ **Maintainability**: Clear file structure with single responsibility

### User Experience
- ✅ **Professional Tables**: Sortable columns, proper formatting
- ✅ **Clear Organization**: Logical grouping of related data
- ✅ **Export Capability**: Scientists can export data for external analysis
- ✅ **Real-time Updates**: Auto-refresh on simulation complete

### Scientific Value
- ✅ **Quantitative Analysis**: Precise metrics instead of vague summaries
- ✅ **Data Export**: CSV export for further analysis in R/Python/Excel
- ✅ **Reproducibility**: All parameters and results documented
- ✅ **Publication Ready**: Tables suitable for scientific papers

---

## Wayland Safety Considerations

### GTK3 Best Practices
1. ✅ Use `Gtk.TreeView` with `Gtk.ListStore` (standard, safe)
2. ✅ Avoid custom drawing on canvas (not needed for tables)
3. ✅ Use standard GTK widgets (Button, Label, Frame, Expander)
4. ✅ No X11-specific calls
5. ✅ No direct window manipulation

### Tested Patterns
- All widgets inherit from standard GTK classes
- No custom rendering or painting
- No clipboard manipulation that's X11-specific
- Use `Gtk.Clipboard` API (Wayland-safe)

---

## File Checklist

### Files to Create (14 new files)
- [ ] `src/shypn/engine/simulation/data_collector.py`
- [ ] `src/shypn/engine/simulation/analysis/__init__.py`
- [ ] `src/shypn/engine/simulation/analysis/species_analyzer.py`
- [ ] `src/shypn/engine/simulation/analysis/reaction_analyzer.py`
- [ ] `src/shypn/report/__init__.py`
- [ ] `src/shypn/report/data_models.py`
- [ ] `src/shypn/report/formatters.py`
- [ ] `src/shypn/ui/panels/report/widgets/__init__.py`
- [ ] `src/shypn/ui/panels/report/widgets/species_concentration_table.py`
- [ ] `src/shypn/ui/panels/report/widgets/reaction_activity_table.py`
- [ ] `src/shypn/ui/panels/report/widgets/kinetic_parameters_table.py`
- [ ] `tests/test_data_collector.py`
- [ ] `tests/test_species_analyzer.py`
- [ ] `tests/test_reaction_analyzer.py`

### Files to Rename (1 file)
- [ ] `src/shypn/ui/panels/report/parameters_category.py` → `dynamic_analyses_category.py`

### Files to Modify (4 files)
- [ ] `src/shypn/model/transition.py` (add firing_count)
- [ ] `src/shypn/engine/simulation/controller.py` (integrate DataCollector)
- [ ] `src/shypn/ui/panels/report/report_panel.py` (set_controller method)
- [ ] `src/shypn/helpers/report_panel_loader.py` (pass controller)

---

## Summary

**What We're Doing:**
- ✅ Rename confusing `parameters_category.py` → `dynamic_analyses_category.py`
- ✅ Add proper **Simulation Data** expander with sortable tables
- ✅ Refactor **Kinetic Parameters** into proper table widget
- ✅ Keep **Enrichment & Citations** expander but improve formatting
- ✅ Create data collection infrastructure for real-time simulation analysis
- ✅ Maintain existing enrichment functionality (BRENDA, citations)

**What We're NOT Doing:**
- ❌ Not removing existing enrichment features
- ❌ Not breaking existing BRENDA integration
- ❌ Not changing Report Panel top-level structure
- ❌ Not modifying other categories (Models, Topology, Provenance)

**Effort Estimate:**
- **Total**: 11-16 hours over 5 sprints
- **Priority**: High (essential for scientific analysis)
- **Risk**: Low (well-defined structure, standard widgets)

**Status**: Ready for implementation ✅
