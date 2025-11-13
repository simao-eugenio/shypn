# Viability Panel Refactoring Plan V2
## REUSE Existing UI + ADD Simulation Controls with Step Functionality

**Date**: November 13, 2025  
**Strategy**: Extend, don't replace. Keep all working UI. Add simulation layer.

---

## Core Principle: **MAXIMUM UI REUSE**

### ✅ What We KEEP (100% unchanged):

1. **Section 1: Selected Localities ListBox** - Works perfectly, don't touch!
2. **Section 2: Subnet Parameters Notebook** - 3 tabs with editable TreeViews
   - Places tab (marking editable)
   - Transitions tab (rate editable)
   - Arcs tab (weight editable)
   - **These are our parameter input interface - perfect as-is!**
3. **Sections 3-6**: All suggestion expanders (Diagnosis/Structural/Biological/Kinetic)
4. **All existing algorithms**: LocalityDetector, SubnetBuilder, analyzers

### 🆕 What We ADD (minimal new code):

1. **Simulation Control Toolbar** (between Section 1 and Section 2)
2. **Results Tab** (4th tab in existing notebook)
3. **Diagnostics Log Expander** (after Section 2, before Section 3)
4. **SubnetSimulator Module** (backend only)
5. **ExperimentManager Module** (save/load parameter snapshots)

---

## Architecture: Layered Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                     VIABILITY PANEL                              │
├─────────────────────────────────────────────────────────────────┤
│ Section 1: Selected Localities [EXISTING - KEEP]                │
│   - ListBox with transitions                                     │
│   - Visual purple highlighting                                   │
├─────────────────────────────────────────────────────────────────┤
│ Simulation Controls [NEW - ADD TOOLBAR]                         │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │ Experiment: [Current ▾] [+ Add] [📋 Copy] [💾 Save]      │ │
│   │ [▶ Run] [⏭ Step] [⏸ Pause] [⏹ Stop] [↻ Reset]           │ │
│   │ Time: [100]s  Steps: [1000]  Method: [Gillespie ▾]       │ │
│   │ Status: ● Ready                                            │ │
│   └───────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ Section 2: Subnet Parameters [EXISTING - ADD 4TH TAB]           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ [Places] [Transitions] [Arcs] [Results] ← NEW TAB       │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │ Existing TreeViews (editable parameters)                │   │
│   │ OR                                                       │   │
│   │ New Results TreeView (read-only computed values)        │   │
│   └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ Diagnostics Log [NEW - ADD EXPANDER]                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ ▼ SIMULATION LOG                                        │   │
│   │ 13:45:02 - Simulation started                           │   │
│   │ 13:45:02 - Step 1: T5 fired, P3: 5→3, P4: 2→3         │   │
│   │ 13:45:02 - Step 2: T6 fired, P4: 3→2, P3: 3→4         │   │
│   │ 13:45:03 - Reached steady state                         │   │
│   │ [Clear Log]                                             │   │
│   └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ Section 3-6: Diagnosis/Suggestions [EXISTING - KEEP]            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Experiment Snapshot Manager (Pure Backend)

**File**: `src/shypn/ui/panels/viability/experiment_manager.py`

```python
"""Experiment snapshot management for viability panel."""

class ExperimentSnapshot:
    """Single parameter configuration snapshot.
    
    Captures/restores values from existing TreeViews without changing UI.
    """
    def __init__(self, name="Experiment 1"):
        self.name = name
        self.place_markings = {}     # {place_id: marking}
        self.arc_weights = {}         # {arc_id: weight}
        self.transition_rates = {}    # {trans_id: rate}
        self.results = None           # SimulationResults after run
        self.timestamp = None
        
    def capture_from_treeviews(self, places_store, transitions_store, arcs_store):
        """Read current parameter values from existing TreeViews."""
        self.place_markings.clear()
        self.transition_rates.clear()
        self.arc_weights.clear()
        
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
        """Write snapshot values back to existing TreeViews."""
        for row in places_store:
            place_id = row[0]
            if place_id in self.place_markings:
                row[2] = self.place_markings[place_id]
                
        for row in transitions_store:
            trans_id = row[0]
            if trans_id in self.transition_rates:
                row[2] = self.transition_rates[trans_id]
                
        for row in arcs_store:
            arc_id = row[0]
            if arc_id in self.arc_weights:
                row[3] = self.arc_weights[arc_id]
    
    def to_dict(self):
        """Serialize for export."""
        return {
            'name': self.name,
            'place_markings': self.place_markings,
            'arc_weights': self.arc_weights,
            'transition_rates': self.transition_rates,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize from import."""
        snapshot = cls(data['name'])
        snapshot.place_markings = data['place_markings']
        snapshot.arc_weights = data['arc_weights']
        snapshot.transition_rates = data['transition_rates']
        snapshot.timestamp = data.get('timestamp')
        return snapshot


class ExperimentManager:
    """Manages multiple experiment snapshots."""
    
    def __init__(self):
        self.snapshots = []
        self.active_index = 0
        
    def add_snapshot(self, name=None):
        """Create new snapshot."""
        if name is None:
            name = f"Experiment {len(self.snapshots) + 1}"
        snapshot = ExperimentSnapshot(name)
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_active_snapshot(self):
        """Get currently active snapshot."""
        if not self.snapshots:
            return None
        return self.snapshots[self.active_index]
    
    def switch_to(self, index):
        """Switch active snapshot and return it."""
        if 0 <= index < len(self.snapshots):
            self.active_index = index
            return self.snapshots[index]
        return None
    
    def remove_snapshot(self, index):
        """Remove snapshot at index."""
        if 0 <= index < len(self.snapshots):
            del self.snapshots[index]
            if self.active_index >= len(self.snapshots):
                self.active_index = max(0, len(self.snapshots) - 1)
    
    def copy_snapshot(self, source_index):
        """Duplicate snapshot for variation."""
        if 0 <= source_index < len(self.snapshots):
            source = self.snapshots[source_index]
            copy_snapshot = ExperimentSnapshot(f"{source.name} (Copy)")
            copy_snapshot.place_markings = source.place_markings.copy()
            copy_snapshot.arc_weights = source.arc_weights.copy()
            copy_snapshot.transition_rates = source.transition_rates.copy()
            self.snapshots.append(copy_snapshot)
            return copy_snapshot
        return None
    
    def export_to_json(self, filepath):
        """Save all snapshots to JSON file."""
        import json
        data = {
            'snapshots': [s.to_dict() for s in self.snapshots],
            'active_index': self.active_index
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filepath):
        """Load snapshots from JSON file."""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.snapshots = [ExperimentSnapshot.from_dict(s) for s in data['snapshots']]
        self.active_index = data.get('active_index', 0)
```

**Integration in viability_panel.py**:
```python
# In __init__():
from .experiment_manager import ExperimentManager
self.experiment_manager = ExperimentManager()
```

---

### Phase 2: Subnet Simulator with Step Control

**File**: `src/shypn/ui/panels/viability/subnet_simulator.py`

```python
"""Subnet simulation engine with step-by-step control."""

class SimulationState:
    """Current state of subnet simulation."""
    def __init__(self):
        self.current_markings = {}      # {place_id: tokens}
        self.firing_counts = {}          # {trans_id: count}
        self.time = 0.0
        self.step_count = 0
        self.enabled_transitions = []
        self.is_running = False
        self.is_paused = False
        self.trajectory = []             # List of (time, markings) tuples


class SimulationResults:
    """Complete simulation outcomes."""
    def __init__(self):
        self.final_markings = {}         # {place_id: tokens}
        self.firing_counts = {}          # {trans_id: count}
        self.fluxes = {}                 # {trans_id: firings/time}
        self.viability_status = "Unknown"  # ✓ Stable / ✗ Deadlock / ⚠ Unbounded
        self.execution_time = 0.0
        self.trajectory = []
        self.deadlocked = False
        self.unbounded_places = []


class SubnetSimulator:
    """Execute subnet simulation with step control.
    
    Integrates with existing:
    - SubnetBuilder (subnet extraction)
    - _get_simulation() (simulation controller)
    - TreeViews (parameter source)
    """
    
    def __init__(self, viability_panel):
        self.panel = viability_panel
        self.state = None
        self.subnet = None
        
    def initialize_simulation(self):
        """Extract subnet and prepare for simulation.
        
        Returns:
            bool: True if initialization successful
        """
        # 1. Get model
        model = self.panel._get_current_model()
        if not model:
            return False
        
        # 2. Extract subnet from selected localities (reuse existing logic)
        subnet = self._extract_subnet()
        if not subnet:
            return False
        
        # 3. Read parameters from TreeViews
        self._apply_parameters_from_treeviews(subnet)
        
        # 4. Initialize state
        self.state = SimulationState()
        self.subnet = subnet
        
        # Copy initial markings
        for place in subnet['places']:
            self.state.current_markings[place.id] = place.marking
            
        for trans in subnet['transitions']:
            self.state.firing_counts[trans.id] = 0
        
        return True
    
    def _extract_subnet(self):
        """Extract subnet from selected localities.
        
        Reuses existing SubnetBuilder logic.
        """
        model = self.panel._get_current_model()
        subnet = {
            'places': [],
            'transitions': [],
            'arcs': []
        }
        
        # Collect all elements from selected localities
        for transition_id, data in self.panel.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            
            # Get transition object
            trans_obj = next((t for t in model.transitions if t.id == transition_id), None)
            if trans_obj and trans_obj not in subnet['transitions']:
                subnet['transitions'].append(trans_obj)
            
            # Get place objects
            for place_id in locality.input_places + locality.output_places:
                place_obj = next((p for p in model.places if p.id == place_id), None)
                if place_obj and place_obj not in subnet['places']:
                    subnet['places'].append(place_obj)
            
            # Get arc objects
            for arc_id in locality.input_arcs + locality.output_arcs:
                arc_obj = next((a for a in model.arcs if a.id == arc_id), None)
                if arc_obj and arc_obj not in subnet['arcs']:
                    subnet['arcs'].append(arc_obj)
        
        return subnet if subnet['transitions'] else None
    
    def _apply_parameters_from_treeviews(self, subnet):
        """Read edited parameters from TreeViews and apply to subnet elements."""
        # Update place markings
        for row in self.panel.places_store:
            place_id, _, marking, _, _ = row
            place_obj = next((p for p in subnet['places'] if p.id == place_id), None)
            if place_obj:
                place_obj.marking = marking
        
        # Update transition rates
        for row in self.panel.transitions_store:
            trans_id, _, rate, _, _, _ = row
            trans_obj = next((t for t in subnet['transitions'] if t.id == trans_id), None)
            if trans_obj:
                trans_obj.rate = rate
        
        # Update arc weights
        for row in self.panel.arcs_store:
            arc_id, _, _, weight, _ = row
            arc_obj = next((a for a in subnet['arcs'] if a.id == arc_id), None)
            if arc_obj:
                arc_obj.weight = weight
    
    def step(self):
        """Execute single firing event.
        
        Returns:
            dict: Step info with {
                'fired_transition': transition_id or None,
                'time_delta': dt,
                'marking_changes': {place_id: (old, new)},
                'enabled_transitions': [trans_ids],
                'deadlocked': bool
            }
        """
        if not self.state or not self.subnet:
            return None
        
        # 1. Check enabled transitions
        enabled = self._get_enabled_transitions()
        self.state.enabled_transitions = enabled
        
        if not enabled:
            # Deadlock
            return {
                'fired_transition': None,
                'time_delta': 0.0,
                'marking_changes': {},
                'enabled_transitions': [],
                'deadlocked': True
            }
        
        # 2. Select transition (random for Gillespie, deterministic for others)
        import random
        selected_trans = random.choice(enabled)
        
        # 3. Calculate time delta (Gillespie: exponential, ODE: fixed step)
        dt = self._calculate_time_delta(enabled)
        
        # 4. Fire transition
        marking_changes = self._fire_transition(selected_trans)
        
        # 5. Update state
        self.state.time += dt
        self.state.step_count += 1
        self.state.firing_counts[selected_trans.id] += 1
        self.state.trajectory.append((self.state.time, self.state.current_markings.copy()))
        
        return {
            'fired_transition': selected_trans.id,
            'time_delta': dt,
            'marking_changes': marking_changes,
            'enabled_transitions': [t.id for t in enabled],
            'deadlocked': False
        }
    
    def _get_enabled_transitions(self):
        """Find transitions with sufficient input tokens."""
        enabled = []
        for trans in self.subnet['transitions']:
            # Check input places
            can_fire = True
            for arc in self.subnet['arcs']:
                if arc.target == trans:  # Input arc
                    place = arc.source
                    required = arc.weight
                    available = self.state.current_markings.get(place.id, 0)
                    if available < required:
                        can_fire = False
                        break
            if can_fire:
                enabled.append(trans)
        return enabled
    
    def _fire_transition(self, transition):
        """Execute transition firing, update markings.
        
        Returns:
            dict: {place_id: (old_marking, new_marking)}
        """
        changes = {}
        
        # Consume from input places
        for arc in self.subnet['arcs']:
            if arc.target == transition:
                place = arc.source
                old_marking = self.state.current_markings[place.id]
                new_marking = old_marking - arc.weight
                self.state.current_markings[place.id] = new_marking
                changes[place.id] = (old_marking, new_marking)
        
        # Produce to output places
        for arc in self.subnet['arcs']:
            if arc.source == transition:
                place = arc.target
                old_marking = self.state.current_markings.get(place.id, 0)
                new_marking = old_marking + arc.weight
                self.state.current_markings[place.id] = new_marking
                if place.id in changes:
                    # Update if already recorded
                    changes[place.id] = (changes[place.id][0], new_marking)
                else:
                    changes[place.id] = (old_marking, new_marking)
        
        return changes
    
    def _calculate_time_delta(self, enabled_transitions):
        """Calculate time until next event (Gillespie algorithm)."""
        import random
        import math
        
        # Sum of propensities (rates)
        total_rate = sum(t.rate if hasattr(t, 'rate') else 1.0 for t in enabled_transitions)
        
        if total_rate == 0:
            return 0.0
        
        # Exponential waiting time
        return -math.log(random.random()) / total_rate
    
    def run_to_completion(self, max_time=100, max_steps=1000, log_callback=None):
        """Run simulation until deadlock or limits reached.
        
        Args:
            max_time: Maximum simulation time
            max_steps: Maximum firing events
            log_callback: Function to call with log messages
            
        Returns:
            SimulationResults
        """
        import time
        start_real_time = time.time()
        
        self.state.is_running = True
        
        while self.state.is_running:
            if self.state.time >= max_time or self.state.step_count >= max_steps:
                if log_callback:
                    log_callback("⏱ Reached time/step limit")
                break
            
            step_info = self.step()
            
            if step_info['deadlocked']:
                if log_callback:
                    log_callback("✗ Deadlock detected - no enabled transitions")
                break
            
            if log_callback:
                trans_id = step_info['fired_transition']
                changes_str = ", ".join([
                    f"{pid}: {old}→{new}"
                    for pid, (old, new) in step_info['marking_changes'].items()
                ])
                log_callback(f"Step {self.state.step_count}: {trans_id} fired ({changes_str})")
        
        self.state.is_running = False
        
        # Create results
        results = SimulationResults()
        results.final_markings = self.state.current_markings.copy()
        results.firing_counts = self.state.firing_counts.copy()
        results.execution_time = time.time() - start_real_time
        results.trajectory = self.state.trajectory.copy()
        results.deadlocked = len(self._get_enabled_transitions()) == 0
        
        # Calculate fluxes
        if self.state.time > 0:
            for trans_id, count in self.state.firing_counts.items():
                results.fluxes[trans_id] = count / self.state.time
        
        # Viability status
        if results.deadlocked:
            results.viability_status = "✗ Deadlock"
        elif any(m > 1000 for m in results.final_markings.values()):
            results.viability_status = "⚠ Unbounded"
            results.unbounded_places = [
                pid for pid, m in results.final_markings.items() if m > 1000
            ]
        else:
            results.viability_status = "✓ Stable"
        
        return results
    
    def reset(self):
        """Reset simulation to initial state."""
        if self.subnet:
            self.initialize_simulation()
```

**Integration in viability_panel.py**:
```python
# In __init__():
from .subnet_simulator import SubnetSimulator
self.subnet_simulator = SubnetSimulator(self)
```

---

### Phase 3: Simulation Control Toolbar UI

**File**: `src/shypn/ui/panels/viability/ui/simulation_control_toolbar.py`

```python
"""Simulation control toolbar widget."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class SimulationControlToolbar(Gtk.Box):
    """Toolbar for experiment management and simulation control."""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self._build_experiment_row()
        self._build_simulation_row()
        
        # Style
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(5)
        
        # Add border
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        # Move children to frame (or wrap in frame - simplified here)
    
    def _build_experiment_row(self):
        """Row 1: Experiment management."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        row.pack_start(Gtk.Label(label="Experiment:"), False, False, 0)
        
        self.experiment_combo = Gtk.ComboBoxText()
        self.experiment_combo.append_text("Current")
        self.experiment_combo.set_active(0)
        row.pack_start(self.experiment_combo, False, False, 0)
        
        self.add_exp_button = Gtk.Button(label="+ Add")
        self.add_exp_button.set_tooltip_text("Create new experiment")
        row.pack_start(self.add_exp_button, False, False, 0)
        
        self.copy_exp_button = Gtk.Button(label="📋 Copy")
        self.copy_exp_button.set_tooltip_text("Duplicate current experiment")
        row.pack_start(self.copy_exp_button, False, False, 0)
        
        self.save_exp_button = Gtk.Button(label="💾 Save")
        self.save_exp_button.set_tooltip_text("Export experiments to JSON")
        row.pack_start(self.save_exp_button, False, False, 0)
        
        self.load_exp_button = Gtk.Button(label="📂 Load")
        self.load_exp_button.set_tooltip_text("Import experiments from JSON")
        row.pack_start(self.load_exp_button, False, False, 0)
        
        self.pack_start(row, False, False, 0)
    
    def _build_simulation_row(self):
        """Row 2: Simulation controls."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Control buttons
        self.run_button = Gtk.Button(label="▶ Run")
        self.run_button.set_tooltip_text("Run simulation to completion")
        self.run_button.get_style_context().add_class("suggested-action")
        row.pack_start(self.run_button, False, False, 0)
        
        self.step_button = Gtk.Button(label="⏭ Step")
        self.step_button.set_tooltip_text("Execute single firing event")
        row.pack_start(self.step_button, False, False, 0)
        
        self.pause_button = Gtk.Button(label="⏸ Pause")
        self.pause_button.set_tooltip_text("Pause simulation")
        self.pause_button.set_sensitive(False)
        row.pack_start(self.pause_button, False, False, 0)
        
        self.stop_button = Gtk.Button(label="⏹ Stop")
        self.stop_button.set_tooltip_text("Stop and reset")
        self.stop_button.set_sensitive(False)
        row.pack_start(self.stop_button, False, False, 0)
        
        self.reset_button = Gtk.Button(label="↻ Reset")
        self.reset_button.set_tooltip_text("Reset to initial state")
        row.pack_start(self.reset_button, False, False, 0)
        
        row.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 5)
        
        # Settings
        row.pack_start(Gtk.Label(label="Time:"), False, False, 0)
        self.time_spinbutton = Gtk.SpinButton(adjustment=Gtk.Adjustment(100, 0.1, 10000, 1, 10))
        self.time_spinbutton.set_width_chars(5)
        self.time_spinbutton.set_tooltip_text("Maximum simulation time (seconds)")
        row.pack_start(self.time_spinbutton, False, False, 0)
        row.pack_start(Gtk.Label(label="s"), False, False, 0)
        
        row.pack_start(Gtk.Label(label="  Steps:"), False, False, 0)
        self.steps_spinbutton = Gtk.SpinButton(adjustment=Gtk.Adjustment(1000, 1, 1000000, 100, 1000))
        self.steps_spinbutton.set_width_chars(6)
        self.steps_spinbutton.set_tooltip_text("Maximum firing events")
        row.pack_start(self.steps_spinbutton, False, False, 0)
        
        row.pack_start(Gtk.Label(label="  Method:"), False, False, 0)
        self.method_combo = Gtk.ComboBoxText()
        self.method_combo.append_text("Gillespie")
        self.method_combo.append_text("ODE")
        self.method_combo.append_text("Hybrid")
        self.method_combo.set_active(0)
        self.method_combo.set_tooltip_text("Simulation algorithm")
        row.pack_start(self.method_combo, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="● Ready")
        self.status_label.set_halign(Gtk.Align.END)
        self.status_label.set_margin_start(10)
        row.pack_end(self.status_label, True, True, 0)
        
        self.pack_start(row, False, False, 0)
    
    def set_status(self, text, status_type="ready"):
        """Update status label.
        
        Args:
            text: Status text
            status_type: "ready", "running", "paused", "success", "error"
        """
        symbols = {
            "ready": "●",
            "running": "⏵",
            "paused": "⏸",
            "success": "✓",
            "error": "✗"
        }
        symbol = symbols.get(status_type, "●")
        self.status_label.set_label(f"{symbol} {text}")
```

**Integration in viability_panel.py**:
```python
# In _build_content(), after Section 1 (Selected Localities):

# === SIMULATION CONTROLS (NEW) ===
from .ui.simulation_control_toolbar import SimulationControlToolbar
self.simulation_toolbar = SimulationControlToolbar()
main_box.pack_start(self.simulation_toolbar, False, False, 0)

# Connect signals
self.simulation_toolbar.run_button.connect("clicked", self._on_run_simulation)
self.simulation_toolbar.step_button.connect("clicked", self._on_step_simulation)
self.simulation_toolbar.pause_button.connect("clicked", self._on_pause_simulation)
self.simulation_toolbar.stop_button.connect("clicked", self._on_stop_simulation)
self.simulation_toolbar.reset_button.connect("clicked", self._on_reset_simulation)

self.simulation_toolbar.add_exp_button.connect("clicked", self._on_add_experiment)
self.simulation_toolbar.copy_exp_button.connect("clicked", self._on_copy_experiment)
self.simulation_toolbar.save_exp_button.connect("clicked", self._on_save_experiments)
self.simulation_toolbar.load_exp_button.connect("clicked", self._on_load_experiments)
self.simulation_toolbar.experiment_combo.connect("changed", self._on_experiment_changed)

# Then existing Section 2 (Subnet Parameters)...
```

---

### Phase 4: Results Tab + Diagnostics Log

**Add Results tab to existing notebook**:

```python
# In _build_content(), after creating arcs tab:

# Results tab (NEW)
results_scroll = Gtk.ScrolledWindow()
results_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
results_scroll.set_size_request(-1, 200)

self.results_treeview, self.results_store = self._create_results_treeview()
results_scroll.add(self.results_treeview)
self.subnet_notebook.append_page(results_scroll, Gtk.Label(label="Results"))
```

**New method**:
```python
def _create_results_treeview(self):
    """Create TreeView for simulation results display.
    
    Columns: Element, Initial, Final, Change, Notes
    """
    store = Gtk.ListStore(str, str, str, str, str)
    
    treeview = Gtk.TreeView(model=store)
    treeview.set_enable_search(False)
    
    # Columns
    for idx, (title, width) in enumerate([
        ("Element", 150),
        ("Initial", 80),
        ("Final", 80),
        ("Change", 80),
        ("Notes", 200)
    ]):
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(title, renderer, text=idx)
        column.set_resizable(True)
        column.set_min_width(width)
        treeview.append_column(column)
    
    return treeview, store
```

**Diagnostics Log Expander** (after Section 2):

```python
# === DIAGNOSTICS LOG (NEW) ===
self.diagnostics_expander = Gtk.Expander()
self.diagnostics_expander.set_expanded(True)
self.diagnostics_expander.set_margin_start(10)
self.diagnostics_expander.set_margin_end(10)
self.diagnostics_expander.set_margin_top(10)

diag_label = Gtk.Label()
diag_label.set_xalign(0)
diag_label.set_markup("<b>SIMULATION LOG</b>")
self.diagnostics_expander.set_label_widget(diag_label)

diag_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
diag_box.set_margin_start(12)
diag_box.set_margin_top(6)
diag_box.set_margin_bottom(6)

# Scrolled TextView
log_scroll = Gtk.ScrolledWindow()
log_scroll.set_size_request(-1, 150)
log_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

self.diagnostics_textview = Gtk.TextView()
self.diagnostics_textview.set_editable(False)
self.diagnostics_textview.set_wrap_mode(Gtk.WrapMode.WORD)
self.diagnostics_textbuffer = self.diagnostics_textview.get_buffer()
log_scroll.add(self.diagnostics_textview)
diag_box.pack_start(log_scroll, True, True, 0)

# Clear button
clear_log_btn = Gtk.Button(label="Clear Log")
clear_log_btn.connect("clicked", self._on_clear_diagnostics_log)
diag_box.pack_start(clear_log_btn, False, False, 0)

self.diagnostics_expander.add(diag_box)
main_box.pack_start(self.diagnostics_expander, False, False, 0)

# Then existing Section 3 (Diagnosis Summary)...
```

---

### Phase 5: Connect Simulation Callbacks

**In viability_panel.py**:

```python
def _append_diagnostics_log(self, message):
    """Add timestamped message to diagnostics log."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_message = f"{timestamp} - {message}\n"
    
    self.diagnostics_textbuffer.insert(
        self.diagnostics_textbuffer.get_end_iter(),
        full_message
    )
    
    # Auto-scroll
    self.diagnostics_textview.scroll_to_iter(
        self.diagnostics_textbuffer.get_end_iter(),
        0, False, 0, 0
    )

def _on_clear_diagnostics_log(self, button):
    """Clear diagnostics log."""
    self.diagnostics_textbuffer.set_text("")

def _on_run_simulation(self, button):
    """Run simulation to completion."""
    # 1. Initialize
    if not self.subnet_simulator.initialize_simulation():
        self._append_diagnostics_log("✗ Failed to initialize simulation (no subnet)")
        return
    
    self._append_diagnostics_log("▶ Simulation started")
    self.simulation_toolbar.set_status("Running...", "running")
    
    # 2. Run
    max_time = self.simulation_toolbar.time_spinbutton.get_value()
    max_steps = int(self.simulation_toolbar.steps_spinbutton.get_value())
    
    results = self.subnet_simulator.run_to_completion(
        max_time=max_time,
        max_steps=max_steps,
        log_callback=self._append_diagnostics_log
    )
    
    # 3. Display results
    self._update_results_display(results)
    
    # 4. Update status
    self.simulation_toolbar.set_status(
        results.viability_status,
        "success" if "✓" in results.viability_status else "error"
    )
    
    self._append_diagnostics_log(
        f"Completed in {results.execution_time:.2f}s "
        f"({results.step_count} steps, {results.viability_status})"
    )

def _on_step_simulation(self, button):
    """Execute single firing event."""
    # 1. Initialize if needed
    if not self.subnet_simulator.state:
        if not self.subnet_simulator.initialize_simulation():
            self._append_diagnostics_log("✗ Failed to initialize")
            return
        self._append_diagnostics_log("⏭ Step mode started")
    
    # 2. Execute step
    step_info = self.subnet_simulator.step()
    
    if not step_info:
        self._append_diagnostics_log("✗ Step failed")
        return
    
    # 3. Log step
    if step_info['deadlocked']:
        self._append_diagnostics_log("✗ Deadlock - no enabled transitions")
        self.simulation_toolbar.set_status("Deadlocked", "error")
    else:
        trans_id = step_info['fired_transition']
        changes_str = ", ".join([
            f"{pid}: {old}→{new}"
            for pid, (old, new) in step_info['marking_changes'].items()
        ])
        self._append_diagnostics_log(
            f"Step {self.subnet_simulator.state.step_count}: "
            f"{trans_id} fired ({changes_str})"
        )
        
        # Update live markings in Places tab (optional)
        self._update_live_markings()
    
    # 4. Update status
    if not step_info['deadlocked']:
        enabled_count = len(step_info['enabled_transitions'])
        self.simulation_toolbar.set_status(
            f"Step {self.subnet_simulator.state.step_count} (t={self.subnet_simulator.state.time:.2f}s, "
            f"{enabled_count} enabled)",
            "running"
        )

def _on_pause_simulation(self, button):
    """Pause running simulation."""
    if self.subnet_simulator.state:
        self.subnet_simulator.state.is_paused = True
        self._append_diagnostics_log("⏸ Paused")
        self.simulation_toolbar.set_status("Paused", "paused")

def _on_stop_simulation(self, button):
    """Stop and reset simulation."""
    if self.subnet_simulator.state:
        self.subnet_simulator.state.is_running = False
    self.subnet_simulator.reset()
    self._append_diagnostics_log("⏹ Stopped and reset")
    self.simulation_toolbar.set_status("Ready", "ready")

def _on_reset_simulation(self, button):
    """Reset simulation to initial state."""
    self.subnet_simulator.reset()
    self._append_diagnostics_log("↻ Reset to initial state")
    self.simulation_toolbar.set_status("Ready", "ready")
    self.results_store.clear()

def _update_results_display(self, results):
    """Populate Results tab with simulation outcomes."""
    self.results_store.clear()
    
    # Header
    self.results_store.append([
        "=== SIMULATION RESULTS ===",
        "", "", "", f"Status: {results.viability_status}"
    ])
    
    # Place markings
    self.results_store.append(["", "", "", "", ""])
    self.results_store.append(["PLACE MARKINGS", "Initial", "Final", "Δ", ""])
    
    for place_id, final_marking in results.final_markings.items():
        # Get initial from subnet
        place_obj = next((p for p in self.subnet_simulator.subnet['places'] if p.id == place_id), None)
        initial = place_obj.marking if place_obj else 0
        delta = final_marking - initial
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        
        self.results_store.append([
            f"  {place_id}",
            str(initial),
            str(final_marking),
            delta_str,
            ""
        ])
    
    # Transition firings
    self.results_store.append(["", "", "", "", ""])
    self.results_store.append(["TRANSITION FIRINGS", "Count", "Flux", "", ""])
    
    for trans_id, count in results.firing_counts.items():
        flux = results.fluxes.get(trans_id, 0)
        self.results_store.append([
            f"  {trans_id}",
            str(count),
            f"{flux:.3f}",
            "",
            f"{count} firings"
        ])
    
    # Viability
    self.results_store.append(["", "", "", "", ""])
    self.results_store.append([
        "VIABILITY",
        "", "", "",
        results.viability_status
    ])
    
    if results.unbounded_places:
        self.results_store.append([
            "  Unbounded places:",
            "", "", "",
            ", ".join(results.unbounded_places)
        ])
    
    # Switch to Results tab
    self.subnet_notebook.set_current_page(3)  # Tab index 3

def _update_live_markings(self):
    """Update Places tab with current simulation markings (live view)."""
    if not self.subnet_simulator.state:
        return
    
    for row in self.places_store:
        place_id = row[0]
        current_marking = self.subnet_simulator.state.current_markings.get(place_id)
        if current_marking is not None:
            row[2] = current_marking  # Column 2 = marking

def _on_add_experiment(self, button):
    """Create new experiment snapshot."""
    snapshot = self.experiment_manager.add_snapshot()
    
    # Capture current TreeView values
    snapshot.capture_from_treeviews(
        self.places_store,
        self.transitions_store,
        self.arcs_store
    )
    
    # Add to combo
    self.simulation_toolbar.experiment_combo.append_text(snapshot.name)
    self.simulation_toolbar.experiment_combo.set_active(len(self.experiment_manager.snapshots) - 1)
    
    self._append_diagnostics_log(f"✓ Created experiment: {snapshot.name}")

def _on_copy_experiment(self, button):
    """Duplicate current experiment."""
    active_index = self.simulation_toolbar.experiment_combo.get_active()
    snapshot = self.experiment_manager.copy_snapshot(active_index)
    
    if snapshot:
        self.simulation_toolbar.experiment_combo.append_text(snapshot.name)
        self.simulation_toolbar.experiment_combo.set_active(len(self.experiment_manager.snapshots) - 1)
        self._append_diagnostics_log(f"✓ Copied experiment: {snapshot.name}")

def _on_save_experiments(self, button):
    """Export experiments to JSON file."""
    dialog = Gtk.FileChooserDialog(
        title="Save Experiments",
        action=Gtk.FileChooserAction.SAVE
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_SAVE, Gtk.ResponseType.OK
    )
    dialog.set_current_name("viability_experiments.json")
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filepath = dialog.get_filename()
        self.experiment_manager.export_to_json(filepath)
        self._append_diagnostics_log(f"💾 Saved experiments to {filepath}")
    
    dialog.destroy()

def _on_load_experiments(self, button):
    """Import experiments from JSON file."""
    dialog = Gtk.FileChooserDialog(
        title="Load Experiments",
        action=Gtk.FileChooserAction.OPEN
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filepath = dialog.get_filename()
        self.experiment_manager.import_from_json(filepath)
        
        # Rebuild combo
        self.simulation_toolbar.experiment_combo.remove_all()
        for snapshot in self.experiment_manager.snapshots:
            self.simulation_toolbar.experiment_combo.append_text(snapshot.name)
        self.simulation_toolbar.experiment_combo.set_active(0)
        
        self._append_diagnostics_log(f"📂 Loaded experiments from {filepath}")
    
    dialog.destroy()

def _on_experiment_changed(self, combo):
    """Switch between experiment snapshots."""
    index = combo.get_active()
    snapshot = self.experiment_manager.switch_to(index)
    
    if snapshot:
        # Apply snapshot values to TreeViews
        snapshot.apply_to_treeviews(
            self.places_store,
            self.transitions_store,
            self.arcs_store
        )
        
        self._append_diagnostics_log(f"Switched to: {snapshot.name}")
```

---

## Summary: What Changed vs What Stayed

### ✅ Kept 100% (Zero Changes):
- Section 1: Selected Localities ListBox
- Section 2: 3-tab notebook (Places/Transitions/Arcs TreeViews)
- Sections 3-6: All suggestion expanders
- All edit callbacks (`_on_place_marking_edited`, etc.)
- `_refresh_subnet_parameters()` logic
- LocalityDetector, SubnetBuilder, analyzers
- Visual highlighting system

### 🆕 Added (New Code):
1. **3 new Python modules** (~600 lines total):
   - `experiment_manager.py` (~150 lines)
   - `subnet_simulator.py` (~300 lines)
   - `ui/simulation_control_toolbar.py` (~150 lines)

2. **UI additions** in `viability_panel.py`:
   - Simulation toolbar (1 new section, ~20 lines)
   - Results tab (1 new tab in existing notebook, ~50 lines)
   - Diagnostics log expander (1 new section, ~40 lines)
   - Simulation callbacks (~200 lines)

3. **Total new code**: ~900 lines
4. **Modified existing code**: ~50 lines (integration points)

### Result:
**90% code reuse, 10% new additions. All existing UI preserved and enhanced with simulation layer on top.**

---

## Next Steps

Ready to implement:
1. **Phase 1**: Create `experiment_manager.py`
2. **Phase 2**: Create `subnet_simulator.py`
3. **Phase 3**: Create `ui/simulation_control_toolbar.py`
4. **Phase 4**: Add Results tab + Diagnostics log to `viability_panel.py`
5. **Phase 5**: Wire up callbacks in `viability_panel.py`

Start with Phase 1?
