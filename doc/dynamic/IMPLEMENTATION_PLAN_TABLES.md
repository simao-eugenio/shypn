# Implementation Plan: Essential Tables for Dynamic Analyses

## Overview
This document provides a detailed implementation plan for the two essential tables in the Report Panel's Dynamic Analyses category:
1. **Species Concentration Table** (Place-centered)
2. **Reaction Activity Table** (Transition-centered)

---

## Architecture

### Component Structure
```
src/gui/panels/report/
├── categories/
│   ├── model_structure_category.py          (existing - MODELS)
│   └── dynamic_analyses_category.py         (NEW)
├── widgets/
│   ├── species_concentration_table.py       (NEW)
│   └── reaction_activity_table.py           (NEW)
└── report_panel.py                          (modify - add new category)

src/shypn/engine/simulation/
├── data_collector.py                        (NEW - core data collection)
└── analysis/
    ├── __init__.py
    ├── species_analyzer.py                  (NEW - place metrics)
    └── reaction_analyzer.py                 (NEW - transition metrics)
```

---

## Phase 1: Data Collection Infrastructure

### 1.1 Create DataCollector Class

**File**: `src/shypn/engine/simulation/data_collector.py`

**Purpose**: Record simulation state at each time step

**Class Design**:
```python
class DataCollector:
    """Collects time-series data during simulation."""
    
    def __init__(self, model):
        self.model = model
        self.time_points = []           # List[float]
        self.place_data = {}            # {place_id: List[int]} - token counts
        self.transition_data = {}       # {transition_id: List[int]} - firing counts
        self.is_collecting = False
        
    def start_collection(self):
        """Initialize data structures and start collecting."""
        self.time_points = []
        self.place_data = {p.id: [] for p in self.model.places}
        self.transition_data = {t.id: [] for t in self.model.transitions}
        self.is_collecting = True
        
    def record_state(self, current_time: float):
        """Record current state at given time point."""
        if not self.is_collecting:
            return
            
        self.time_points.append(current_time)
        
        # Record place tokens
        for place in self.model.places:
            tokens = place.tokens
            self.place_data[place.id].append(tokens)
            
        # Record transition firing counts (cumulative)
        for transition in self.model.transitions:
            count = transition.firing_count  # Need to add this to transition
            self.transition_data[transition.id].append(count)
    
    def stop_collection(self):
        """Stop collecting data."""
        self.is_collecting = False
        
    def clear(self):
        """Clear all collected data."""
        self.time_points.clear()
        self.place_data.clear()
        self.transition_data.clear()
        self.is_collecting = False
        
    def get_place_series(self, place_id: str) -> tuple[List[float], List[int]]:
        """Get time-series for a specific place."""
        return self.time_points, self.place_data.get(place_id, [])
        
    def get_transition_series(self, transition_id: str) -> tuple[List[float], List[int]]:
        """Get time-series for a specific transition."""
        return self.time_points, self.transition_data.get(transition_id, [])
```

**Integration Points**:
1. Add `firing_count` attribute to `Transition` class
2. Increment `firing_count` in `controller.py` when transition fires
3. Reset `firing_count` when simulation resets

---

### 1.2 Integrate DataCollector into Controller

**File**: `src/shypn/engine/simulation/controller.py`

**Changes Required**:

```python
class SimulationController:
    def __init__(self, model, ...):
        # ... existing code ...
        self.data_collector = DataCollector(model)  # NEW
        
    def reset_for_new_model(self, model):
        # ... existing code ...
        self.data_collector = DataCollector(model)  # NEW
        
    def _reset_simulation(self):
        """Reset simulation to initial state."""
        # ... existing code ...
        self.data_collector.clear()  # NEW
        
    def start_simulation(self):
        """Start or resume simulation."""
        if self.state == SimulationState.IDLE:
            self.data_collector.start_collection()  # NEW
        # ... existing code ...
        
    def _simulation_step(self):
        """Execute one simulation step."""
        # ... existing code ...
        
        # Record state after step
        self.data_collector.record_state(self.current_time)  # NEW
        
    def stop_simulation(self):
        """Stop simulation."""
        # ... existing code ...
        self.data_collector.stop_collection()  # NEW
```

---

### 1.3 Add firing_count to Transition

**File**: `src/shypn/model/transition.py`

**Changes Required**:

```python
class Transition:
    def __init__(self, ...):
        # ... existing code ...
        self.firing_count = 0  # NEW - cumulative count
        
    def reset_firing_count(self):
        """Reset firing count to zero."""
        self.firing_count = 0
```

**File**: `src/shypn/engine/simulation/controller.py`

**Update firing logic**:

```python
def _fire_transition(self, transition: Transition):
    """Fire a transition."""
    # ... existing code to consume/produce tokens ...
    
    transition.firing_count += 1  # NEW - increment count
```

**Update reset logic**:

```python
def _reset_simulation(self):
    """Reset simulation to initial state."""
    # ... existing code ...
    
    # Reset firing counts
    for transition in self.model.transitions:
        transition.reset_firing_count()  # NEW
```

---

## Phase 2: Analysis Modules

### 2.1 Species Analyzer

**File**: `src/shypn/engine/simulation/analysis/species_analyzer.py`

**Purpose**: Calculate metrics for each place (species)

```python
from typing import List, Dict, Optional
import statistics

class SpeciesMetrics:
    """Metrics for a single species (place)."""
    
    def __init__(self, place_id: str, place_name: str):
        self.place_id = place_id
        self.place_name = place_name
        self.initial_tokens: int = 0
        self.final_tokens: int = 0
        self.min_tokens: int = 0
        self.max_tokens: int = 0
        self.avg_tokens: float = 0.0
        self.total_change: int = 0
        self.change_rate: float = 0.0  # tokens per time unit

class SpeciesAnalyzer:
    """Analyze place (species) data from simulation."""
    
    def __init__(self, data_collector):
        self.data_collector = data_collector
        
    def analyze_all_species(self, duration: float) -> List[SpeciesMetrics]:
        """Analyze all places and return metrics."""
        results = []
        
        for place in self.data_collector.model.places:
            metrics = self._analyze_place(place, duration)
            results.append(metrics)
            
        return results
        
    def _analyze_place(self, place, duration: float) -> SpeciesMetrics:
        """Analyze a single place."""
        metrics = SpeciesMetrics(place.id, place.label or place.id)
        
        time_points, token_series = self.data_collector.get_place_series(place.id)
        
        if not token_series:
            # No data collected
            metrics.initial_tokens = place.tokens
            metrics.final_tokens = place.tokens
            return metrics
            
        # Calculate metrics
        metrics.initial_tokens = token_series[0]
        metrics.final_tokens = token_series[-1]
        metrics.min_tokens = min(token_series)
        metrics.max_tokens = max(token_series)
        metrics.avg_tokens = statistics.mean(token_series)
        metrics.total_change = metrics.final_tokens - metrics.initial_tokens
        
        if duration > 0:
            metrics.change_rate = metrics.total_change / duration
            
        return metrics
```

---

### 2.2 Reaction Analyzer

**File**: `src/shypn/engine/simulation/analysis/reaction_analyzer.py`

**Purpose**: Calculate metrics for each transition (reaction)

```python
from typing import List, Dict, Optional
from enum import Enum

class ActivityStatus(Enum):
    """Reaction activity classification."""
    INACTIVE = "Inactive"      # Never fired
    LOW = "Low"               # Fired < 10 times
    ACTIVE = "Active"         # Fired >= 10 times
    HIGH = "High"             # Fired > 100 times

class ReactionMetrics:
    """Metrics for a single reaction (transition)."""
    
    def __init__(self, transition_id: str, transition_name: str):
        self.transition_id = transition_id
        self.transition_name = transition_name
        self.transition_type: str = "stochastic"  # or "continuous"
        self.firing_count: int = 0
        self.average_rate: float = 0.0  # firings per time unit
        self.total_flux: int = 0        # total tokens processed
        self.contribution: float = 0.0   # % of total network flux
        self.status: ActivityStatus = ActivityStatus.INACTIVE

class ReactionAnalyzer:
    """Analyze transition (reaction) data from simulation."""
    
    def __init__(self, data_collector):
        self.data_collector = data_collector
        
    def analyze_all_reactions(self, duration: float) -> List[ReactionMetrics]:
        """Analyze all transitions and return metrics."""
        results = []
        total_flux = 0
        
        # First pass: calculate individual metrics and total flux
        for transition in self.data_collector.model.transitions:
            metrics = self._analyze_transition(transition, duration)
            results.append(metrics)
            total_flux += metrics.total_flux
            
        # Second pass: calculate contributions
        if total_flux > 0:
            for metrics in results:
                metrics.contribution = (metrics.total_flux / total_flux) * 100.0
                
        return results
        
    def _analyze_transition(self, transition, duration: float) -> ReactionMetrics:
        """Analyze a single transition."""
        metrics = ReactionMetrics(
            transition.id,
            transition.label or transition.id
        )
        
        metrics.transition_type = transition.transition_type.value
        
        time_points, firing_series = self.data_collector.get_transition_series(transition.id)
        
        if not firing_series:
            # No data collected
            metrics.firing_count = transition.firing_count
        else:
            metrics.firing_count = firing_series[-1]  # Final cumulative count
            
        # Calculate average rate
        if duration > 0:
            metrics.average_rate = metrics.firing_count / duration
            
        # Calculate total flux (tokens processed)
        # For simplicity: flux = firing_count * output_tokens_per_firing
        # More accurate: sum of all tokens produced
        output_arcs = [a for a in transition.outgoing_arcs]
        tokens_per_firing = sum(arc.weight for arc in output_arcs) if output_arcs else 1
        metrics.total_flux = metrics.firing_count * tokens_per_firing
        
        # Classify activity status
        if metrics.firing_count == 0:
            metrics.status = ActivityStatus.INACTIVE
        elif metrics.firing_count < 10:
            metrics.status = ActivityStatus.LOW
        elif metrics.firing_count > 100:
            metrics.status = ActivityStatus.HIGH
        else:
            metrics.status = ActivityStatus.ACTIVE
            
        return metrics
```

---

## Phase 3: Table Widgets

### 3.1 Species Concentration Table Widget

**File**: `src/gui/panels/report/widgets/species_concentration_table.py`

**Purpose**: Display place metrics in a sortable table

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class SpeciesConcentrationTable(Gtk.ScrolledWindow):
    """Table displaying species concentration metrics."""
    
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        
        # Create tree view with columns
        self.store = Gtk.ListStore(
            str,   # Place Name
            str,   # Color (hex)
            int,   # Initial
            int,   # Final
            int,   # Min
            int,   # Max
            float, # Average
            int,   # Change (Δ)
            float  # Rate (Δ/time)
        )
        
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(0)
        
        # Add columns
        self._setup_columns()
        
        self.add(self.tree_view)
        
    def _setup_columns(self):
        """Create table columns."""
        
        # Column 0: Place Name with color indicator
        renderer_text = Gtk.CellRendererText()
        renderer_color = Gtk.CellRendererPixbuf()
        
        column = Gtk.TreeViewColumn("Species")
        column.pack_start(renderer_color, False)
        column.pack_start(renderer_text, True)
        column.add_attribute(renderer_text, "text", 0)
        # Color indicator will be set via custom cell data func
        column.set_resizable(True)
        column.set_sort_column_id(0)
        self.tree_view.append_column(column)
        
        # Column 1: Initial Tokens
        self._add_numeric_column("Initial", 2, int)
        
        # Column 2: Final Tokens
        self._add_numeric_column("Final", 3, int)
        
        # Column 3: Minimum
        self._add_numeric_column("Min", 4, int)
        
        # Column 4: Maximum
        self._add_numeric_column("Max", 5, int)
        
        # Column 5: Average
        self._add_numeric_column("Average", 6, float, format_str="{:.2f}")
        
        # Column 6: Total Change
        self._add_numeric_column("Δ", 7, int, format_str="{:+d}")
        
        # Column 7: Change Rate
        self._add_numeric_column("Rate (Δ/t)", 8, float, format_str="{:+.4f}")
        
    def _add_numeric_column(self, title: str, column_id: int, 
                           value_type: type, format_str: str = None):
        """Add a numeric column with right alignment."""
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)  # Right align
        
        column = Gtk.TreeViewColumn(title, renderer)
        
        if format_str:
            column.set_cell_data_func(renderer, self._format_cell, 
                                     (column_id, format_str))
        else:
            column.add_attribute(renderer, "text", column_id)
            
        column.set_resizable(True)
        column.set_sort_column_id(column_id)
        self.tree_view.append_column(column)
        
    def _format_cell(self, column, cell, model, iter, user_data):
        """Format cell value."""
        column_id, format_str = user_data
        value = model.get_value(iter, column_id)
        cell.set_property("text", format_str.format(value))
        
    def populate(self, species_metrics: List):
        """Populate table with species metrics."""
        self.store.clear()
        
        for metrics in species_metrics:
            self.store.append([
                metrics.place_name,
                "#000000",  # TODO: Get actual place color
                metrics.initial_tokens,
                metrics.final_tokens,
                metrics.min_tokens,
                metrics.max_tokens,
                metrics.avg_tokens,
                metrics.total_change,
                metrics.change_rate
            ])
```

---

### 3.2 Reaction Activity Table Widget

**File**: `src/gui/panels/report/widgets/reaction_activity_table.py`

**Purpose**: Display transition metrics in a sortable table

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class ReactionActivityTable(Gtk.ScrolledWindow):
    """Table displaying reaction activity metrics."""
    
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        
        # Create tree view with columns
        self.store = Gtk.ListStore(
            str,   # Transition Name
            str,   # Type (stochastic/continuous)
            int,   # Firing Count
            float, # Average Rate
            int,   # Total Flux
            float, # Contribution %
            str    # Status
        )
        
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(0)
        
        # Add columns
        self._setup_columns()
        
        self.add(self.tree_view)
        
    def _setup_columns(self):
        """Create table columns."""
        
        # Column 0: Transition Name
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Reaction", renderer, text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        self.tree_view.append_column(column)
        
        # Column 1: Type
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)  # Center align
        column = Gtk.TreeViewColumn("Type", renderer, text=1)
        column.set_resizable(True)
        column.set_sort_column_id(1)
        self.tree_view.append_column(column)
        
        # Column 2: Firing Count
        self._add_numeric_column("Firings", 2, "{:,d}")
        
        # Column 3: Average Rate
        self._add_numeric_column("Avg Rate", 3, "{:.4f}")
        
        # Column 4: Total Flux
        self._add_numeric_column("Total Flux", 4, "{:,d}")
        
        # Column 5: Contribution %
        self._add_numeric_column("Contribution", 5, "{:.2f}%")
        
        # Column 6: Status
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Status", renderer, text=6)
        column.set_resizable(True)
        column.set_sort_column_id(6)
        self.tree_view.append_column(column)
        
    def _add_numeric_column(self, title: str, column_id: int, format_str: str):
        """Add a numeric column with right alignment."""
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)  # Right align
        
        column = Gtk.TreeViewColumn(title, renderer)
        column.set_cell_data_func(renderer, self._format_cell, 
                                 (column_id, format_str))
        column.set_resizable(True)
        column.set_sort_column_id(column_id)
        self.tree_view.append_column(column)
        
    def _format_cell(self, column, cell, model, iter, user_data):
        """Format cell value."""
        column_id, format_str = user_data
        value = model.get_value(iter, column_id)
        
        # Handle percentage formatting
        if "%" in format_str:
            cell.set_property("text", format_str.replace("%", "").format(value) + "%")
        else:
            cell.set_property("text", format_str.format(value))
        
    def populate(self, reaction_metrics: List):
        """Populate table with reaction metrics."""
        self.store.clear()
        
        for metrics in reaction_metrics:
            self.store.append([
                metrics.transition_name,
                metrics.transition_type,
                metrics.firing_count,
                metrics.average_rate,
                metrics.total_flux,
                metrics.contribution,
                metrics.status.value
            ])
```

---

## Phase 4: Dynamic Analyses Category

### 4.1 Create Category Class

**File**: `src/gui/panels/report/categories/dynamic_analyses_category.py`

**Purpose**: Container for dynamic analysis widgets

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..widgets.species_concentration_table import SpeciesConcentrationTable
from ..widgets.reaction_activity_table import ReactionActivityTable

class DynamicAnalysesCategory(Gtk.Box):
    """Dynamic Analyses category for Report Panel."""
    
    def __init__(self, controller):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.controller = controller
        
        # Header
        header = Gtk.Label()
        header.set_markup("<b>Dynamic Analyses</b>")
        header.set_halign(Gtk.Align.START)
        self.pack_start(header, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>No simulation data available</i>")
        self.status_label.set_halign(Gtk.Align.START)
        self.pack_start(self.status_label, False, False, 0)
        
        # Create expanders for each table
        self._create_species_section()
        self._create_reactions_section()
        
    def _create_species_section(self):
        """Create Species Concentration table section."""
        expander = Gtk.Expander()
        expander.set_label("Species Concentration")
        expander.set_expanded(True)
        
        self.species_table = SpeciesConcentrationTable()
        expander.add(self.species_table)
        
        self.pack_start(expander, True, True, 0)
        
    def _create_reactions_section(self):
        """Create Reaction Activity table section."""
        expander = Gtk.Expander()
        expander.set_label("Reaction Activity")
        expander.set_expanded(True)
        
        self.reaction_table = ReactionActivityTable()
        expander.add(self.reaction_table)
        
        self.pack_start(expander, True, True, 0)
        
    def refresh(self):
        """Refresh tables with current simulation data."""
        data_collector = self.controller.data_collector
        
        # Check if we have data
        if not data_collector.time_points:
            self.status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.store.clear()
            self.reaction_table.store.clear()
            return
            
        # Get simulation duration
        duration = self.controller.settings.duration or 0.0
        
        # Analyze and populate species table
        from ....engine.simulation.analysis.species_analyzer import SpeciesAnalyzer
        species_analyzer = SpeciesAnalyzer(data_collector)
        species_metrics = species_analyzer.analyze_all_species(duration)
        self.species_table.populate(species_metrics)
        
        # Analyze and populate reaction table
        from ....engine.simulation.analysis.reaction_analyzer import ReactionAnalyzer
        reaction_analyzer = ReactionAnalyzer(data_collector)
        reaction_metrics = reaction_analyzer.analyze_all_reactions(duration)
        self.reaction_table.populate(reaction_metrics)
        
        # Update status
        num_species = len(species_metrics)
        num_reactions = len(reaction_metrics)
        num_time_points = len(data_collector.time_points)
        
        self.status_label.set_markup(
            f"<i>Analyzed {num_species} species and {num_reactions} reactions "
            f"over {num_time_points} time points</i>"
        )
```

---

### 4.2 Register Category in Report Panel

**File**: `src/gui/panels/report/report_panel.py`

**Modifications**:

```python
# Import new category
from .categories.dynamic_analyses_category import DynamicAnalysesCategory

class ReportPanel(Gtk.Box):
    def __init__(self, controller):
        # ... existing code ...
        
        # Add new category to stack
        self.dynamic_analyses = DynamicAnalysesCategory(controller)
        self.stack.add_titled(
            self.dynamic_analyses,
            "dynamic_analyses",
            "DYNAMIC ANALYSES"
        )
```

---

## Phase 5: Integration and Testing

### 5.1 Update Controller to Notify Report Panel

**File**: `src/shypn/engine/simulation/controller.py`

**Add callback for simulation complete**:

```python
class SimulationController:
    def __init__(self, ...):
        # ... existing code ...
        self.on_simulation_complete = None  # Callback function
        
    def _check_completion(self):
        """Check if simulation is complete."""
        if self.settings.is_complete(self.current_time):
            self.stop_simulation()
            
            # Notify listeners
            if self.on_simulation_complete:
                self.on_simulation_complete()  # NEW
```

**File**: GUI initialization (where report panel is created)

**Connect callback**:

```python
# After creating report_panel and controller
controller.on_simulation_complete = lambda: report_panel.dynamic_analyses.refresh()
```

---

### 5.2 Testing Checklist

**Unit Tests**:
- [ ] `test_data_collector.py` - Test data collection
- [ ] `test_species_analyzer.py` - Test species metrics calculation
- [ ] `test_reaction_analyzer.py` - Test reaction metrics calculation

**Integration Tests**:
- [ ] `test_dynamic_analyses_category.py` - Test category creation and refresh
- [ ] `test_simulation_with_data_collection.py` - Test full simulation with data collection

**Manual Testing**:
1. Load glycolysis model
2. Add source transitions
3. Run simulation for 60 seconds
4. Open Report Panel → DYNAMIC ANALYSES
5. Verify Species Concentration table shows:
   - Initial/Final tokens match visual state
   - Min/Max make sense
   - Changes are correct
6. Verify Reaction Activity table shows:
   - Firing counts > 0 for active transitions
   - Contribution percentages sum to ~100%
   - Status labels are appropriate

---

## Summary

**Files to Create** (10 new files):
1. `data_collector.py` - Core data collection
2. `analysis/species_analyzer.py` - Place metrics
3. `analysis/reaction_analyzer.py` - Transition metrics
4. `widgets/species_concentration_table.py` - Species table widget
5. `widgets/reaction_activity_table.py` - Reaction table widget
6. `categories/dynamic_analyses_category.py` - Category container
7. Test files (4 files)

**Files to Modify** (3 files):
1. `transition.py` - Add firing_count attribute
2. `controller.py` - Integrate DataCollector, track firings, add callback
3. `report_panel.py` - Register new category

**Estimated Effort**:
- Phase 1 (Data Collection): 2-3 hours
- Phase 2 (Analysis): 2 hours
- Phase 3 (Table Widgets): 3-4 hours
- Phase 4 (Category Integration): 1 hour
- Phase 5 (Testing): 2-3 hours
- **Total**: 10-13 hours

**Dependencies**:
- No external dependencies needed (using built-in Gtk)
- Could optionally use `pandas` for data manipulation (future enhancement)

**Next Steps After Tables**:
- Time-series plots (matplotlib/plotly integration)
- Export functionality (CSV, JSON)
- Interactive plot selection (click place to add to plot)

---

**Status**: Ready for implementation
**Priority**: High (essential for scientific analysis)
**Complexity**: Medium (well-defined structure, standard widgets)
