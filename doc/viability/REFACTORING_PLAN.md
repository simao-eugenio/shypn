# Viability Panel Refactoring Plan
## From Current State to Tabular Subnet Experimentation

**Date**: November 13, 2025

---

## Current Architecture (What We Have)

### ✅ Working Components - REUSE THESE

1. **Locality Selection System** ✅ KEEP AS-IS
   - `selected_localities` dict tracking selected transitions
   - Right-click "Add to Viability Analysis" workflow
   - Visual highlighting (purple borders) on transitions and places
   - ListBox showing selected localities with checkboxes
   - **This stays at the top - don't change it!**

2. **Subnet Parameters Display** 🔄 REUSE + EXTEND
   - **Three separate TreeViews** (Places, Transitions, Arcs) - **KEEP THESE!**
   - **Places TreeView**: ID, Name, **Marking** (editable ⚡), Type, Label
   - **Transitions TreeView**: ID, Name, **Rate** (editable ⚡), Formula, Type, Label
   - **Arcs TreeView**: ID, From, To, **Weight** (editable ⚡), Type
   - Edit callbacks already working:
     - `_on_place_marking_edited()` ✅
     - `_on_transition_rate_edited()` ✅
     - `_on_arc_weight_edited()` ✅
   - Auto-refresh via `_refresh_subnet_parameters()` ✅
   - **Strategy**: Add simulation controls AROUND existing tables, not replace them!

3. **Data Infrastructure** ✅ REUSE
   - `DataPuller`: KB/simulation data access
   - `DataCache`: Cached pull-based data
   - `SubnetBuilder`: Connected subnet construction
   - LocalityDetector integration (diagnostic/)
   - `_get_simulation()`: Access to simulation controller

4. **Analysis Components** ✅ REUSE
   - `LocalityAnalyzer`, `DependencyAnalyzer`, `BoundaryAnalyzer`, `ConservationAnalyzer`
   - `FixSequencer`, `FixApplier`, `FixPredictor`
   - Investigation workflow with sim_data integration

5. **UI Structure (Current)**
   ```
   ViabilityPanel (Gtk.Box) - 1844 lines
   ├─ Header (title + float button)                      [KEEP]
   ├─ Section 1: Selected Localities (ListBox)           [KEEP]
   ├─ Section 2: Subnet Parameters (Expander)            [EXTEND]
   │  └─ Notebook (3 tabs: Places/Transitions/Arcs)     [KEEP + ADD TOOLBAR]
   ├─ Section 3: Diagnosis Summary (Expander)            [KEEP]
   ├─ Section 4: Structural Suggestions (Expander)       [KEEP]
   ├─ Section 5: Biological Suggestions (Expander)       [KEEP]
   └─ Section 6: Kinetic Suggestions (Expander)          [KEEP]
   ```

---

## Target Architecture (What We Need)

### New Components to Add (MINIMAL CHANGES)

1. **Experiment Column Manager** 📦 NEW MODULE
   - Store multiple parameter snapshots
   - Each "snapshot" = save/load parameter values from existing TreeViews
   - Default "Current" = read from model initially
   - Add/Remove/Copy/Export snapshots
   - **KEY**: Don't create new tables - just save/restore values in existing ones!

2. **Simulation Control Toolbar** 🎮 NEW UI (add above notebook)
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │ Experiment: [Current ▾]  [+ Add] [📋 Copy] [💾 Save]       │
   │ [▶ Run] [⏭ Step] [⏸ Pause] [⏹ Stop] [↻ Reset]             │
   │ Time: [100] s  Steps: [1000]  Method: [Gillespie ▾]        │
   │ Status: ● Ready                                             │
   └─────────────────────────────────────────────────────────────┘
   ```
   - **⏭ Step**: New! Execute single firing event, update displays
   - **▶ Run**: Execute until time limit or steady state
   - **Experiment dropdown**: Switch between saved parameter sets

3. **SubnetSimulator** 🔬 NEW MODULE
   - Extract subnet from selected localities (reuse SubnetBuilder)
   - Read parameters from existing TreeViews (Places/Transitions/Arcs)
   - Run simulation with step-by-step control
   - Return results (final markings, fluxes, viability status)
   - **Integration**: Use existing `_get_simulation()` method for sim controller

4. **Results Display** 📊 EXTEND EXISTING
   - Add new tab to existing notebook: "Results"
   - TreeView showing:
     - Final place markings (compare to initial)
     - Transition firing counts
     - Viability status (✓ Stable, ✗ Deadlock, ⚠ Unbounded)
     - Execution time
   - Auto-populate after simulation runs
   - **Reuses existing TreeView pattern!**

5. **Diagnostics Log** 📝 NEW EXPANDER (add after Section 2)
   - Collapsible like other expanders
   - TextView with auto-scroll
   - Real-time simulation feedback:
     - "T5 fired, consumed 2 tokens from P3"
     - "Reached steady state at t=8.5s"
     - "⚠ Deadlock detected"
   - Clear button

---

## Refactoring Strategy (REUSE UI, ADD CONTROLS)

### Phase 1: Add Experiment Snapshot Manager (Pure Data)

**Goal**: Save/load parameter values without changing UI

```python
class ExperimentSnapshot:
    """Single parameter configuration snapshot"""
    def __init__(self, name="Experiment 1"):
        self.name = name
        self.place_markings = {}     # {place_id: marking}
        self.arc_weights = {}         # {arc_id: weight}
        self.transition_rates = {}    # {trans_id: rate}
        self.results = None           # Populated after simulation
        
    def capture_from_treeviews(self, places_store, transitions_store, arcs_store):
        """Read current values from existing TreeViews"""
        for row in places_store:
            place_id, _, marking, _, _ = row
            self.place_markings[place_id] = marking
            
        for row in transitions_store:
            trans_id, _, rate, _, _, _ = row
            self.transition_rates[trans_id] = rate
            
        for row in arcs_store:
            arc_id, _, _, weight, _ = row
            self.arc_weights[arc_id] = weight
    
    def apply_to_treeviews(self, places_store, transitions_store, arcs_store):
        """Write values back to existing TreeViews"""
        # Update place markings
        for row in places_store:
            place_id = row[0]
            if place_id in self.place_markings:
                row[2] = self.place_markings[place_id]  # Column 2 = marking
                
        # Update transition rates
        for row in transitions_store:
            trans_id = row[0]
            if trans_id in self.transition_rates:
                row[2] = self.transition_rates[trans_id]  # Column 2 = rate
                
        # Update arc weights
        for row in arcs_store:
            arc_id = row[0]
            if arc_id in self.arc_weights:
                row[3] = self.arc_weights[arc_id]  # Column 3 = weight

class ExperimentManager:
    """Manages experiment snapshots (no UI)"""
    def __init__(self):
        self.snapshots = []  # List of ExperimentSnapshot
        self.active_index = 0
        
    def add_snapshot(self, name=None):
        """Create new snapshot"""
        name = name or f"Experiment {len(self.snapshots) + 1}"
        snapshot = ExperimentSnapshot(name)
        self.snapshots.append(snapshot)
        return snapshot
        
    def get_active_snapshot(self):
        """Get current snapshot"""
        if not self.snapshots:
            return None
        return self.snapshots[self.active_index]
        
    def switch_to(self, index):
        """Switch active snapshot"""
        if 0 <= index < len(self.snapshots):
            self.active_index = index
            return self.snapshots[index]
        return None
```

**Changes**:
- Add `self.experiment_manager = ExperimentManager()` to `ViabilityPanel.__init__()`
- Create "Current" snapshot on first locality selection
- **Zero UI changes yet - just data layer**

---

## Refactoring Strategy (Minimal Changes)

### Phase 1: Extend Data Model (Keep Existing)

**Goal**: Add experiment storage without breaking current functionality

```python
class ExperimentColumn:
    """Single experiment configuration"""
    def __init__(self, name="Experiment 1"):
        self.name = name
        self.place_markings = {}     # {place_id: marking}
        self.arc_weights = {}         # {arc_id: weight}
        self.transition_params = {}   # {trans_id: {'kcat': val, 'Km': val, ...}}
        self.results = None           # Populated after simulation

class ExperimentManager:
    """Manages multiple experiment columns"""
    def __init__(self):
        self.columns = []  # List of ExperimentColumn
        self.active_column_index = 0
        
    def add_column(self, name=None):
        """Add new experiment column"""
        
    def remove_column(self, index):
        """Remove experiment column"""
        
    def copy_column(self, source_index):
        """Duplicate experiment for variation"""
        
    def get_active_column(self):
        """Get current experiment being edited"""
        
    def populate_from_subnet(self, model, locality_data):
        """Create "Current" column from model state"""
```

**Changes**:
- Add `self.experiment_manager = ExperimentManager()` to `ViabilityPanel.__init__()`
- Keep existing `selected_localities` dict (still needed for subnet extraction)
- Keep existing TreeViews (will coexist during transition)

---

### Phase 2: Create Unified Parameter Table Widget

**Goal**: New table widget that replaces the 3-tab notebook

```python
class ExperimentTableView(Gtk.Box):
    """Multi-column editable parameter table"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Toolbar with controls
        self.toolbar = self._build_toolbar()
        self.pack_start(self.toolbar, False, False, 0)
        
        # Scrolled table
        self.scrolled = Gtk.ScrolledWindow()
        self.treeview = self._build_treeview()
        self.scrolled.add(self.treeview)
        self.pack_start(self.scrolled, True, True, 0)
        
    def _build_treeview(self):
        """Create TreeView with dynamic columns
        
        Columns:
        - Parameter Name (fixed, row labels)
        - Current (base values from model)
        - Experiment 1, 2, 3... (dynamic, editable)
        
        Rows (hierarchical):
        - PLACES
          - P3 tokens
          - P4 tokens
        - ARCS
          - P3→T5 weight
          - T5→P4 weight
        - TRANSITIONS
          - T5 kcat
          - T5 Km
          - T5 Ki
          - T6 kcat
          - T6 Km
        - RESULTS (auto-computed)
          - Final P3
          - T5 flux
          - Viability
        """
        # Use TreeStore for hierarchical rows
        store = Gtk.TreeStore(str, str, str, str, ...)  # Dynamic columns
        treeview = Gtk.TreeView(model=store)
        
        # Column 0: Parameter Name (bold for sections)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Parameter", renderer, text=0, weight=1)
        treeview.append_column(column)
        
        # Column 1+: Experiment columns (all editable)
        # Created dynamically via add_experiment_column()
        
        return treeview
        
    def add_experiment_column(self, name):
        """Add new experiment column to table"""
        
    def populate_from_locality(self, model, locality_data):
        """Fill "Current" column from model"""
        
    def update_results_section(self, column_index, results):
        """Populate results rows after simulation"""
```

**Changes**:
- Add `from .ui.experiment_table_view import ExperimentTableView` to imports
- Create `self.experiment_table = ExperimentTableView()` in `_build_content()`
- Keep existing notebook initially (both visible during testing)

---

### Phase 3: Add Simulation Engine

**Goal**: Run subnet with custom parameters

```python
class SubnetSimulator:
    """Execute subnet simulation with experiment parameters"""
    
    def __init__(self, model, subnet_builder):
        self.model = model
        self.subnet_builder = subnet_builder
        
    def extract_subnet(self, locality_data):
        """Build isolated subnet from selected localities
        
        Returns:
            subnet: Dictionary with places, transitions, arcs
        """
        
    def apply_parameters(self, subnet, experiment_column):
        """Apply experiment parameters to subnet elements"""
        
    def run_simulation(self, subnet, time_limit=100, max_steps=1000, method='gillespie'):
        """Execute simulation
        
        Args:
            subnet: Extracted subnet dict
            time_limit: Max simulation time (seconds)
            max_steps: Max firing events
            method: 'gillespie', 'ode', 'hybrid'
            
        Returns:
            SimulationResults: Final markings, fluxes, viability status
        """
        
    def analyze_viability(self, results):
        """Detect deadlocks, boundedness violations
        
        Returns:
            ViabilityStatus: ✓ Stable, ✗ Deadlock, ⚠ Unbounded
        """

class SimulationResults:
    """Container for simulation outcomes"""
    def __init__(self):
        self.final_markings = {}      # {place_id: tokens}
        self.transition_fluxes = {}   # {trans_id: firings/time}
        self.viability_status = None  # ✓/✗/⚠
        self.execution_time = 0.0     # Seconds
        self.trajectory = []          # Full time series (optional)
```

**Changes**:
- Add `self.subnet_simulator = SubnetSimulator(self.model, self.subnet_builder)` to `__init__()`
- Connect to existing `SubnetBuilder` (reuse subnet extraction logic)

---

### Phase 4: Add Simulation Controls

**Goal**: UI controls for running simulations

```python
class SimulationControlBar(Gtk.Box):
    """Toolbar with simulation controls"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Play/Pause/Stop/Reset buttons
        self.run_button = Gtk.Button(label="▶ Run")
        self.pause_button = Gtk.Button(label="⏸ Pause")
        self.stop_button = Gtk.Button(label="⏹ Stop")
        self.reset_button = Gtk.Button(label="↻ Reset")
        
        # Settings
        self.time_limit_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(100, 1, 10000, 1))
        self.max_steps_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(1000, 1, 1000000, 100))
        self.method_combo = Gtk.ComboBoxText()
        self.method_combo.append_text("Gillespie")
        self.method_combo.append_text("ODE")
        self.method_combo.append_text("Hybrid")
        self.method_combo.set_active(0)
        
        # Status indicator
        self.status_label = Gtk.Label(label="● Ready")
        
        self._layout_widgets()
```

**Changes**:
- Add `self.control_bar = SimulationControlBar()` before experiment table
- Connect signals:
  - `run_button.connect("clicked", self._on_run_simulation)`
  - `pause_button.connect("clicked", self._on_pause_simulation)`
  - `stop_button.connect("clicked", self._on_stop_simulation)`
  - `reset_button.connect("clicked", self._on_reset_simulation)`

---

### Phase 5: Add Diagnostics Log

**Goal**: Real-time simulation feedback

```python
class DiagnosticsLog(Gtk.Box):
    """Scrollable log with auto-scroll"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Header with auto-scroll toggle
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.pack_start(Gtk.Label(label="Diagnostics Log"), True, True, 0)
        
        self.autoscroll_toggle = Gtk.CheckButton(label="Auto-scroll")
        self.autoscroll_toggle.set_active(True)
        header.pack_end(self.autoscroll_toggle, False, False, 0)
        self.pack_start(header, False, False, 0)
        
        # ScrolledWindow with TextView
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_size_request(-1, 150)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textbuffer = self.textview.get_buffer()
        
        self.scrolled.add(self.textview)
        self.pack_start(self.scrolled, True, True, 0)
        
    def append_log(self, message):
        """Add timestamped log entry"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.textbuffer.insert(self.textbuffer.get_end_iter(), f"{timestamp} - {message}\n")
        
        if self.autoscroll_toggle.get_active():
            self.textview.scroll_to_iter(self.textbuffer.get_end_iter(), 0, False, 0, 0)
            
    def clear(self):
        """Clear log"""
        self.textbuffer.set_text("")
```

**Changes**:
- Add `self.diagnostics_log = DiagnosticsLog()` after experiment table
- Call `self.diagnostics_log.append_log()` from simulation callbacks

---

### Phase 6: Wire Up Simulation Workflow

**Goal**: Connect all components

```python
def _on_run_simulation(self, button):
    """Execute simulation for active experiment column"""
    
    # 1. Get active experiment
    active_column = self.experiment_manager.get_active_column()
    if not active_column:
        self.diagnostics_log.append_log("⚠ No experiment selected")
        return
        
    # 2. Extract subnet from selected localities
    subnet = self.subnet_simulator.extract_subnet(self.selected_localities)
    if not subnet:
        self.diagnostics_log.append_log("⚠ No valid subnet")
        return
        
    # 3. Apply parameters
    self.subnet_simulator.apply_parameters(subnet, active_column)
    self.diagnostics_log.append_log(f"▶ Starting simulation: {active_column.name}")
    
    # 4. Run simulation
    time_limit = self.control_bar.time_limit_entry.get_value()
    max_steps = int(self.control_bar.max_steps_entry.get_value())
    method = self.control_bar.method_combo.get_active_text().lower()
    
    results = self.subnet_simulator.run_simulation(
        subnet, time_limit=time_limit, max_steps=max_steps, method=method
    )
    
    # 5. Update results in table
    column_index = self.experiment_manager.active_column_index
    self.experiment_table.update_results_section(column_index, results)
    
    # 6. Log completion
    status = "✓ Completed" if results.viability_status == "Stable" else "✗ Failed"
    self.diagnostics_log.append_log(f"{status} in {results.execution_time:.2f}s")

def _on_parameter_edited(self, renderer, path, new_text, column_index):
    """Cell edited in experiment table - trigger auto-simulation"""
    
    # Update experiment column
    active_column = self.experiment_manager.get_active_column()
    # ... update parameter value in active_column ...
    
    # Auto-run simulation
    self._on_run_simulation(None)
```

**Changes**:
- Connect `ExperimentTableView` cell editing to `_on_parameter_edited()`
- Implement all control bar callbacks
- Keep existing `_on_diagnose_clicked()` for backward compatibility

---

### Phase 7: Transition UI Layout

**Goal**: Replace old notebook with new unified table

```python
def _build_content(self):
    """Build main content area"""
    
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    
    # === SECTION 1: Selected Localities (KEEP AS IS) ===
    # ... existing code ...
    
    # === SECTION 2: Simulation Controls (NEW) ===
    self.control_bar = SimulationControlBar()
    self.control_bar.set_margin_start(10)
    self.control_bar.set_margin_end(10)
    self.control_bar.set_margin_top(10)
    main_box.pack_start(self.control_bar, False, False, 0)
    
    # === SECTION 3: Unified Experiment Table (NEW - replaces subnet_expander) ===
    self.experiment_table = ExperimentTableView()
    self.experiment_table.set_margin_start(10)
    self.experiment_table.set_margin_end(10)
    self.experiment_table.set_margin_top(5)
    main_box.pack_start(self.experiment_table, True, True, 0)
    
    # === SECTION 4: Diagnostics Log (NEW) ===
    self.diagnostics_log = DiagnosticsLog()
    self.diagnostics_log.set_margin_start(10)
    self.diagnostics_log.set_margin_end(10)
    self.diagnostics_log.set_margin_top(10)
    self.diagnostics_log.set_margin_bottom(10)
    main_box.pack_start(self.diagnostics_log, False, False, 0)
    
    # === SECTION 5: Diagnosis Summary (KEEP for backward compatibility) ===
    # ... existing summary_expander ...
    
    # REMOVE: self.subnet_expander (3-tab notebook)
```

**Changes**:
- Comment out or remove subnet_expander creation
- Add new sections in order: controls → table → log
- Keep diagnosis summary at bottom for existing workflow

---

## Migration Path (Minimal Risk)

### Step 1: Parallel Development (No Breaking Changes)
- **Week 1**: Create new classes in separate files:
  - `experiment_manager.py`
  - `subnet_simulator.py`
  - `ui/experiment_table_view.py`
  - `ui/simulation_control_bar.py`
  - `ui/diagnostics_log.py`
- **Test**: Import and instantiate alongside existing code
- **Result**: Both old and new UIs coexist

### Step 2: Feature Toggle (Safe Rollback)
- **Week 2**: Add preference toggle:
  ```python
  self.use_experiment_table = False  # Feature flag
  
  if self.use_experiment_table:
      # New unified table
  else:
      # Old 3-tab notebook
  ```
- **Test**: Switch between modes manually
- **Result**: Easy to revert if issues found

### Step 3: Data Migration
- **Week 3**: Populate `ExperimentManager` from existing subnet parameters:
  ```python
  def _migrate_to_experiments(self):
      """Copy subnet parameters to experiment manager"""
      current_column = self.experiment_manager.add_column("Current")
      
      # Read from existing TreeView stores
      for row in self.places_store:
          place_id, _, marking, _, _ = row
          current_column.place_markings[place_id] = marking
          
      for row in self.transitions_store:
          trans_id, _, rate, _, _, _ = row
          current_column.transition_params[trans_id] = {'rate': rate}
          
      for row in self.arcs_store:
          arc_id, _, _, weight, _ = row
          current_column.arc_weights[arc_id] = weight
  ```
- **Test**: Verify data consistency
- **Result**: Seamless transition

### Step 4: Remove Legacy Code
- **Week 4**: Once stable, delete:
  - `_create_places_treeview()`
  - `_create_transitions_treeview()`
  - `_create_arcs_treeview()`
  - `self.subnet_expander` UI code
- **Keep**: 
  - `selected_localities` (still used for subnet selection)
  - `LocalityDetector` integration
  - Visual highlighting system
- **Result**: Clean codebase

---

## Reusable Components (Don't Change)

### ✅ Keep Working As-Is
1. **Locality selection**: `selected_localities` dict, right-click workflow
2. **Visual highlighting**: Purple border coloring
3. **LocalityDetector**: Arc detection algorithm
4. **SubnetBuilder**: Subnet extraction logic
5. **DataPuller/DataCache**: KB access infrastructure
6. **Clear All**: Reset functionality

### 🔄 Extend (Don't Replace)
1. **Parameter editing**: Add to new table, keep old callbacks as reference
2. **Model access**: `_get_current_model()` works for both systems
3. **Diagnosis workflow**: Keep existing analyzers, add simulation alongside

### ❌ Remove Eventually
1. **3-tab notebook**: Replaced by unified table
2. **Separate TreeViews**: Merged into single table
3. **Individual edit callbacks**: Unified in table cell editing

---

## Timeline Summary

| Phase | Duration | Deliverable | Risk |
|-------|----------|-------------|------|
| 1 | 2 days | Data model classes | Low (no UI changes) |
| 2 | 3 days | Unified table widget | Low (parallel dev) |
| 3 | 2 days | Simulation engine | Medium (new logic) |
| 4 | 1 day | Control bar UI | Low (simple widgets) |
| 5 | 1 day | Diagnostics log | Low (TextView wrapper) |
| 6 | 3 days | Wire up workflow | Medium (integration) |
| 7 | 2 days | UI transition | Low (feature toggle) |
| **Total** | **14 days** | **Full feature** | **Low overall** |

---

## Success Criteria

### Functional
- ✓ Add experiment columns dynamically
- ✓ Edit all parameters (places, arcs, kinetics) in unified table
- ✓ Run simulation per experiment
- ✓ Auto-populate results section
- ✓ Compare experiments side-by-side
- ✓ Export to CSV/JSON

### Performance
- ✓ Subnet simulation < 1s for small nets
- ✓ UI responsive during simulation
- ✓ No regression in existing locality selection

### UX
- ✓ Cleaner than 3-tab interface
- ✓ Less scrolling required
- ✓ Clear visual hierarchy (sections)
- ✓ Intuitive controls

---

## Conclusion

**This refactoring leverages existing infrastructure (locality selection, subnet builder, data puller) and adds experimentation capabilities on top without breaking current functionality. The key insight is to keep what works and extend rather than replace.**

**Next Action**: Create `experiment_manager.py` and `subnet_simulator.py` as first step?
