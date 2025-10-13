# Complete Diagnostic Flow - NetObjects, Property Dialogs, and Real-Time Panel

**Date**: October 12, 2025  
**Status**: Complete Reference  
**Scope**: All diagnostic flows for Places, Transitions, Arcs, and Real-Time Monitoring

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
└───────────┬─────────────────────────────────────┬───────────────────┘
            │                                     │
    ┌───────▼────────┐                   ┌────────▼──────────┐
    │  Property      │                   │  Real-Time        │
    │  Dialogs       │                   │  Diagnostic Panel │
    │  (Static)      │                   │  (Dynamic)        │
    └───────┬────────┘                   └────────┬──────────┘
            │                                     │
    ┌───────▼────────────────────────────────────▼───────────┐
    │           NET OBJECT ATTRIBUTES                         │
    │  - Places: tokens, initial_marking, capacity            │
    │  - Transitions: type, rate, guards, source/sink         │
    │  - Arcs: weight, threshold, arc_type                    │
    └───────┬─────────────────────────────────────────────────┘
            │
    ┌───────▼────────────────────────────────────────────────┐
    │           DIAGNOSTIC SUBSYSTEMS                         │
    │  - LocalityDetector: Structure detection               │
    │  - LocalityAnalyzer: Static analysis                   │
    │  - LocalityRuntimeAnalyzer: Runtime metrics            │
    │  - SimulationDataCollector: Event tracking             │
    └───────┬─────────────────────────────────────────────────┘
            │
    ┌───────▼────────────────────────────────────────────────┐
    │           SIMULATION ENGINE                             │
    │  - Behavior execution                                   │
    │  - Token flow                                           │
    │  - Event logging                                        │
    └─────────────────────────────────────────────────────────┘
```

---

## Part 1: NetObject Property Dialogs (Static Configuration)

### 1.1 Place Properties Dialog

**File**: `src/shypn/helpers/place_prop_dialog_loader.py`  
**UI File**: `ui/dialogs/place_prop_dialog.ui`

#### Properties Exposed:

| Property | Type | Description | Default | Diagnostic Use |
|----------|------|-------------|---------|----------------|
| `name` | str | System name (P1, P2, ...) | Auto-generated | Identification |
| `label` | str | User label | "" | Display name |
| `tokens` | float | Current token count | 0 | Runtime state |
| `initial_marking` | float | Initial tokens | 0 | Reset baseline |
| `capacity` | int/None | Max tokens (None = ∞) | None | Constraint checking |
| `border_color` | RGB tuple | Circle border color | (0,0,0) | Visual identification |
| `radius` | float | Circle radius | 25.0 | Size |

#### Diagnostic Flow:

```
1. User double-clicks Place or right-click → Properties
   ↓
2. PlacePropDialogLoader.__init__(place_obj)
   ↓
3. _load_ui() - Load place_prop_dialog.ui
   ↓
4. _populate_fields() - Read current Place attributes
   ↓
5. Display dialog (user edits fields)
   ↓
6. User clicks OK → _on_response()
   ↓
7. _save_properties() - Write back to Place object
   ↓
8. emit('properties-changed') signal
   ↓
9. persistency_manager.mark_dirty() - Flag for save
   ↓
10. Canvas redraws with new properties
```

#### Key Methods:

```python
def _populate_fields(self):
    """Read Place attributes and populate UI fields."""
    name_entry.set_text(self.place_obj.name)
    tokens_spin.set_value(self.place_obj.tokens)
    initial_marking_spin.set_value(self.place_obj.initial_marking)
    capacity_spin.set_value(self.place_obj.capacity or 0)

def _save_properties(self):
    """Write UI fields back to Place object."""
    self.place_obj.label = label_entry.get_text()
    self.place_obj.tokens = tokens_spin.get_value()
    self.place_obj.initial_marking = initial_marking_spin.get_value()
    self.place_obj.capacity = capacity if capacity > 0 else None
    self.place_obj.border_color = self.color_picker.get_selected_color()
```

---

### 1.2 Transition Properties Dialog

**File**: `src/shypn/helpers/transition_prop_dialog_loader.py`  
**UI File**: `ui/dialogs/transition_prop_dialog.ui`

#### Properties Exposed:

| Property | Type | Description | Default | Diagnostic Use |
|----------|------|-------------|---------|----------------|
| `name` | str | System name (T1, T2, ...) | Auto-generated | Identification |
| `label` | str | User label | "" | Display name |
| `transition_type` | str | Type (continuous/immediate/timed/stochastic) | **'continuous'** ⭐ | Behavior selection |
| `rate` | float | Rate parameter | 1.0 | Flow/firing rate |
| `rate_function` | str | Rate expression (continuous) | None | Dynamic rate |
| `earliest` | float | Min delay (timed) | 0.0 | Delay window |
| `latest` | float | Max delay (timed) | 1.0 | Delay window |
| `guard` | str | Guard expression | None | Enablement condition |
| `priority` | int | Firing priority | 0 | Conflict resolution |
| `is_source` | bool | Source transition flag | False | Token generation |
| `is_sink` | bool | Sink transition flag | False | Token consumption |
| `border_color` | RGB tuple | Rectangle border color | (0,0,0) | Visual identification |

#### Diagnostic Flow:

```
1. User double-clicks Transition or right-click → Properties
   ↓
2. TransitionPropDialogLoader.__init__(transition_obj)
   ↓
3. _load_ui() - Load transition_prop_dialog.ui
   ↓
4. _populate_fields() - Read current Transition attributes
   ├─ Set type combo box (default index 3 = continuous)
   ├─ Load rate/rate_function based on type
   ├─ Load earliest/latest for timed
   └─ Load guard expression
   ↓
5. _wire_type_change_handler() - Handle type dropdown changes
   ↓
6. Display dialog (user edits fields)
   ↓
7. User clicks OK → _on_response()
   ↓
8. _save_properties() - Write back to Transition object
   ├─ Save type (invalidates behavior cache if changed)
   ├─ Save type-specific properties (rate_function, delays, etc.)
   └─ Parse and validate guard expression
   ↓
9. emit('properties-changed') signal
   ↓
10. simulation_controller.invalidate_behavior_cache(transition.id)
   ↓
11. persistency_manager.mark_dirty()
   ↓
12. Canvas redraws with new properties
```

#### Key Methods:

```python
def _populate_fields(self):
    """Read Transition attributes and populate UI fields."""
    type_combo.set_active(type_map.get(transition_type, 3))  # Default continuous
    
    if self.transition_obj.transition_type == 'continuous':
        rate_function_entry.set_text(self.transition_obj.rate_function or "")
        rate_function_entry.show()
    
    guard_entry.set_text(self.transition_obj.guard or "")
    priority_spin.set_value(self.transition_obj.priority)

def _save_properties(self):
    """Write UI fields back to Transition object."""
    old_type = self.transition_obj.transition_type
    new_type = ['immediate', 'timed', 'stochastic', 'continuous'][type_combo.get_active()]
    
    self.transition_obj.transition_type = new_type
    
    if new_type == 'continuous':
        self.transition_obj.rate_function = rate_function_entry.get_text()
    elif new_type == 'timed':
        self.transition_obj.earliest = earliest_spin.get_value()
        self.transition_obj.latest = latest_spin.get_value()
    elif new_type == 'stochastic':
        self.transition_obj.rate = rate_spin.get_value()
    
    self.transition_obj.guard = guard_entry.get_text() or None
    
    # Invalidate behavior cache if type changed
    if old_type != new_type:
        simulation.invalidate_behavior_cache(self.transition_obj.id)
```

#### Type-Specific UI Sections:

**Continuous** (default):
- Rate Function entry: Expression using `P1`, `P2`, `t`, `math.*`
- Examples: `5.0`, `0.5 * P1`, `sigmoid(t, 10, 0.5)`

**Immediate**:
- No additional properties (fires instantly when enabled)

**Timed**:
- Earliest: Minimum delay (float)
- Latest: Maximum delay (float)

**Stochastic**:
- Rate: λ parameter (exponential distribution)

---

### 1.3 Arc Properties Dialog

**File**: `src/shypn/helpers/arc_prop_dialog_loader.py`  
**UI File**: `ui/dialogs/arc_prop_dialog.ui`

#### Properties Exposed:

| Property | Type | Description | Default | Diagnostic Use |
|----------|------|-------------|---------|----------------|
| `arc_type` | str | Type (normal/inhibitor/reset/read) | 'normal' | Behavior type |
| `weight` | int | Token multiplier | 1 | Flow rate |
| `threshold` | str/int/func | Enablement threshold | weight | Dynamic threshold |
| `bidirectional` | bool | Two-way arc | False | Visual |

#### Diagnostic Flow:

```
1. User double-clicks Arc or right-click → Properties
   ↓
2. ArcPropDialogLoader.__init__(arc_obj)
   ↓
3. _load_ui() - Load arc_prop_dialog.ui
   ↓
4. _populate_fields() - Read current Arc attributes
   ├─ Set type combo box
   ├─ Set weight spinner
   └─ Set threshold expression
   ↓
5. Display dialog (user edits fields)
   ↓
6. User clicks OK → _on_response()
   ↓
7. _save_properties() - Write back to Arc object
   ├─ Save arc_type
   ├─ Save weight
   └─ Parse and validate threshold expression
   ↓
8. emit('properties-changed') signal
   ↓
9. persistency_manager.mark_dirty()
   ↓
10. Canvas redraws with new arc appearance
```

#### Key Methods:

```python
def _populate_fields(self):
    """Read Arc attributes and populate UI fields."""
    arc_type_combo.set_active(type_map[self.arc_obj.arc_type])
    weight_spin.set_value(self.arc_obj.weight)
    
    # Threshold can be int, str, or callable
    threshold_entry.set_text(str(self.arc_obj.threshold))

def _save_properties(self):
    """Write UI fields back to Arc object."""
    types = ['normal', 'inhibitor', 'reset', 'read']
    self.arc_obj.arc_type = types[arc_type_combo.get_active()]
    self.arc_obj.weight = int(weight_spin.get_value())
    
    # Parse threshold (can be expression like "P1.tokens * 0.3")
    threshold_text = threshold_entry.get_text().strip()
    if threshold_text:
        try:
            # Try as number first
            self.arc_obj.threshold = int(threshold_text)
        except ValueError:
            # Store as expression string
            self.arc_obj.threshold = threshold_text
```

---

## Part 2: Real-Time Diagnostic Panel (Dynamic Monitoring)

### 2.1 Diagnostics Panel Architecture

**File**: `src/shypn/analyses/diagnostics_panel.py`  
**Location**: Right panel → Diagnostics tab

#### Purpose:
Real-time runtime diagnostics for selected transitions during simulation, showing:
- Locality structure and analysis
- Recent firing events
- Throughput calculations
- Dynamic enablement state
- Token flow visualization

Unlike property dialogs (static configuration), this panel **updates continuously** during simulation.

---

### 2.2 Diagnostic Components

#### Component 1: LocalityDetector

**File**: `src/shypn/diagnostic/locality_detector.py`

**Purpose**: Detect spatial locality patterns for a transition

**Methods**:
```python
def get_locality_for_transition(self, transition):
    """Detect locality structure for transition.
    
    Returns:
        Locality object with:
        - input_places: List of input places
        - output_places: List of output places
        - input_arcs: List of input arcs
        - output_arcs: List of output arcs
        - is_valid: True if locality is well-formed
    """
```

**Diagnostic Use**:
- Identify P-T-P (Place-Transition-Place) patterns
- Detect source transitions (no inputs)
- Detect sink transitions (no outputs)
- Verify structural correctness

---

#### Component 2: LocalityAnalyzer

**File**: `src/shypn/diagnostic/locality_analyzer.py`

**Purpose**: Static analysis of locality structure

**Methods**:
```python
def analyze_locality(self, locality):
    """Analyze locality structure.
    
    Returns:
        Analysis object with:
        - total_input_tokens: Sum of tokens in input places
        - total_output_tokens: Sum of tokens in output places
        - input_weights: Sum of input arc weights
        - output_weights: Sum of output arc weights
        - is_balanced: input_weights == output_weights
        - capacity_violations: Places exceeding capacity
    """
```

**Diagnostic Output**:
```
Structure:
  Type: Normal P-T-P
  Input Places: 2 (P1, P2)
  Output Places: 1 (P3)
  
Tokens:
  Input: 15 tokens (P1=10, P2=5)
  Output: 3 tokens (P3=3)
  
Weights:
  Input: 3 (arc weights sum)
  Output: 2 (arc weights sum)
  Balance: UNBALANCED (3 ≠ 2)
```

---

#### Component 3: LocalityRuntimeAnalyzer

**File**: `src/shypn/diagnostic/locality_runtime.py`

**Purpose**: Runtime execution metrics during simulation

**Methods**:
```python
def analyze_runtime_metrics(self, transition, locality, time_window=None):
    """Analyze runtime execution metrics.
    
    Returns:
        RuntimeMetrics object with:
        - total_firings: Total firing count
        - recent_firings: Firings in time window
        - throughput: Firings per second
        - last_firing_time: Time of last firing
        - is_enabled: Current enablement state
        - enablement_reason: Why enabled/disabled
    """
```

**Diagnostic Output**:
```
Runtime Metrics (last 10s):
  Total Firings: 47
  Recent Firings: 8
  Throughput: 0.8 firings/second
  Last Fired: 2.3s ago
  
Enablement:
  Status: ENABLED ✓
  Reason: All input places have sufficient tokens
  
  Input Check:
    P1: 10 >= 3 (required) ✓
    P2: 5 >= 2 (required) ✓
```

---

### 2.3 Diagnostic Panel Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User selects transition (click or search)                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  DiagnosticsPanel.set_transition(transition)                │
│    ├─ Stop previous update timer                            │
│    ├─ Detect locality: LocalityDetector.get_locality()      │
│    ├─ Analyze structure: LocalityAnalyzer.analyze()         │
│    └─ Start update timer (500ms interval)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Periodic Update (every 500ms)                              │
│    ├─ Check if simulation running                           │
│    ├─ Get runtime metrics: RuntimeAnalyzer.analyze()        │
│    ├─ Format diagnostic text                                │
│    └─ Update TextView display                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Display Sections:                                           │
│    1. Transition Info (name, type, source/sink)            │
│    2. Locality Structure (inputs, outputs, balance)         │
│    3. Static Analysis (tokens, weights)                     │
│    4. Runtime Metrics (firings, throughput, enablement)     │
│    5. Recent Events (last N firing times)                   │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.4 Diagnostic Panel Methods

**File**: `src/shypn/analyses/diagnostics_panel.py`

#### Key Methods:

```python
def set_transition(self, transition):
    """Set transition to diagnose.
    
    Args:
        transition: Transition object to analyze
        
    Flow:
        1. Stop previous update timer
        2. Detect locality structure
        3. Perform static analysis
        4. Start periodic update timer
        5. Display initial diagnostics
    """
    # Stop previous timer
    if self.update_timer:
        GLib.source_remove(self.update_timer)
    
    self.current_transition = transition
    
    # Detect locality
    self.locality = self.detector.get_locality_for_transition(transition)
    
    # Static analysis
    if self.locality.is_valid:
        self.static_analysis = self.analyzer.analyze_locality(self.locality)
    
    # Start periodic updates (500ms)
    self.update_timer = GLib.timeout_add(500, self._update_display)
    
    # Initial display
    self._update_display()

def _update_display(self):
    """Update diagnostic display (called every 500ms).
    
    Returns:
        bool: True to continue periodic updates
    """
    if not self.current_transition:
        return False
    
    # Get runtime metrics
    if self.runtime_analyzer:
        metrics = self.runtime_analyzer.analyze_runtime_metrics(
            self.current_transition,
            self.locality,
            time_window=10.0  # Last 10 seconds
        )
    else:
        metrics = None
    
    # Format diagnostic text
    text = self._format_diagnostics(metrics)
    
    # Update TextView
    buffer = self.textview.get_buffer()
    buffer.set_text(text)
    
    return True  # Continue updates

def _format_diagnostics(self, metrics):
    """Format diagnostic information as text.
    
    Args:
        metrics: RuntimeMetrics object or None
        
    Returns:
        str: Formatted diagnostic text
    """
    lines = []
    
    # Section 1: Transition Info
    lines.append("=== TRANSITION INFO ===")
    lines.append(f"Name: {self.current_transition.name}")
    lines.append(f"Label: {self.current_transition.label or '(none)'}")
    lines.append(f"Type: {self.current_transition.transition_type.upper()}")
    
    if self.current_transition.is_source:
        lines.append("Special: SOURCE (generates tokens)")
    elif self.current_transition.is_sink:
        lines.append("Special: SINK (consumes tokens)")
    
    lines.append("")
    
    # Section 2: Locality Structure
    lines.append("=== LOCALITY STRUCTURE ===")
    if self.locality.is_valid:
        lines.append(f"Input Places: {len(self.locality.input_places)}")
        for place in self.locality.input_places:
            lines.append(f"  • {place.name}: {place.tokens} tokens")
        
        lines.append(f"Output Places: {len(self.locality.output_places)}")
        for place in self.locality.output_places:
            lines.append(f"  • {place.name}: {place.tokens} tokens")
    else:
        lines.append("⚠ Invalid locality structure")
    
    lines.append("")
    
    # Section 3: Static Analysis
    if hasattr(self, 'static_analysis') and self.static_analysis:
        lines.append("=== STATIC ANALYSIS ===")
        lines.append(f"Total Input Tokens: {self.static_analysis.total_input_tokens}")
        lines.append(f"Total Output Tokens: {self.static_analysis.total_output_tokens}")
        lines.append(f"Input Weights: {self.static_analysis.input_weights}")
        lines.append(f"Output Weights: {self.static_analysis.output_weights}")
        
        if self.static_analysis.is_balanced:
            lines.append("Balance: ✓ BALANCED")
        else:
            lines.append("Balance: ⚠ UNBALANCED")
        
        lines.append("")
    
    # Section 4: Runtime Metrics
    if metrics:
        lines.append("=== RUNTIME METRICS ===")
        lines.append(f"Total Firings: {metrics.total_firings}")
        lines.append(f"Recent Firings (10s): {metrics.recent_firings}")
        lines.append(f"Throughput: {metrics.throughput:.2f} firings/s")
        
        if metrics.last_firing_time is not None:
            time_since = metrics.current_time - metrics.last_firing_time
            lines.append(f"Last Fired: {time_since:.2f}s ago")
        else:
            lines.append("Last Fired: Never")
        
        lines.append("")
        lines.append(f"Enablement: {'✓ ENABLED' if metrics.is_enabled else '✗ DISABLED'}")
        lines.append(f"Reason: {metrics.enablement_reason}")
        
        lines.append("")
    
    # Section 5: Recent Events
    if metrics and metrics.recent_events:
        lines.append("=== RECENT EVENTS ===")
        for i, (time, event_type) in enumerate(metrics.recent_events[-10:]):
            lines.append(f"{i+1}. t={time:.2f}s - {event_type}")
    
    return "\n".join(lines)
```

---

### 2.5 Integration with Right Panel

**File**: `src/shypn/helpers/right_panel_loader.py`

**Setup Flow**:
```python
def _setup_plotting_panels(self):
    """Set up plotting panels including diagnostics."""
    
    # ... place_panel and transition_panel setup ...
    
    # Diagnostics Panel (NEW)
    diagnostics_container = self.builder.get_object('diagnostics_content_container')
    diagnostics_selection_label = self.builder.get_object('diagnostics_selection_label')
    diagnostics_placeholder = self.builder.get_object('diagnostics_placeholder')
    
    if diagnostics_container:
        # Instantiate diagnostics panel
        self.diagnostics_panel = DiagnosticsPanel(self.model, self.data_collector)
        self.diagnostics_panel.setup(
            diagnostics_container,
            selection_label=diagnostics_selection_label,
            placeholder_label=diagnostics_placeholder
        )
```

**Wiring to Context Menu**:
```python
# In model_canvas_loader.py context menu
def _on_show_diagnostics(self, menu_item, transition, manager):
    """Show diagnostics for selected transition."""
    if self.right_panel_loader and self.right_panel_loader.diagnostics_panel:
        # Switch to diagnostics tab
        notebook = self.builder.get_object('right_notebook')
        notebook.set_current_page(2)  # Diagnostics tab
        
        # Set transition
        self.right_panel_loader.diagnostics_panel.set_transition(transition)
```

---

## Part 3: Data Flow Integration

### 3.1 Property Dialog → NetObject → Simulation

```
Property Dialog Change
        ↓
Update NetObject Attribute (place.tokens = 10)
        ↓
Emit 'properties-changed' Signal
        ↓
persistency_manager.mark_dirty() - Document modified
        ↓
simulation_controller.invalidate_behavior_cache() - If transition type changed
        ↓
Canvas Redraw - Visual update
        ↓
Simulation Uses New Values - Next step/firing uses updated attributes
```

---

### 3.2 Simulation → Data Collector → Diagnostic Panel

```
Simulation Step
        ↓
Transition Fires
        ↓
data_collector.on_transition_fired(transition, time, details)
        ↓
Store Event: (time, 'fired', {'rate': 2.5, 'consumed': {...}, 'produced': {...}})
        ↓
Periodic Update Timer (500ms)
        ↓
LocalityRuntimeAnalyzer.analyze_runtime_metrics()
        ├─ Query data_collector.get_transition_data(transition.id)
        ├─ Calculate throughput
        ├─ Check enablement
        └─ Format diagnostics
        ↓
DiagnosticsPanel._update_display()
        ↓
TextView Updates - User sees real-time metrics
```

---

### 3.3 Context Menu Integration

**Transition Context Menu**:
```
Right-click Transition
        ↓
Context Menu Shows:
  ├─ Properties... → TransitionPropDialogLoader (static config)
  ├─ Change Type ► → Submenu (immediate/timed/stochastic/continuous)
  ├─ Transform ►   → Submenu (source/sink/normal)
  └─ Show Diagnostics → DiagnosticsPanel (real-time monitoring)
```

**Place Context Menu**:
```
Right-click Place
        ↓
Context Menu Shows:
  ├─ Properties... → PlacePropDialogLoader (static config)
  └─ Add to Analysis → PlaceRatePanel (token evolution plot)
```

**Arc Context Menu**:
```
Right-click Arc
        ↓
Context Menu Shows:
  ├─ Properties... → ArcPropDialogLoader (static config)
  └─ Change Type ► → Submenu (normal/inhibitor/reset/read)
```

---

## Part 4: Default Values Summary

### 4.1 Updated Defaults (October 12, 2025)

**Transition Type Default Changed**:
- **Old Default**: `'immediate'`
- **New Default**: `'continuous'` ⭐
- **Rationale**: Better for biochemical pathways and hybrid systems

**Files Updated**:
- `netobjs/transition.py` - Core Transition class
- `engine/behavior_factory.py` - Behavior creation
- `edit/snapshots.py` - Snapshot defaults
- `edit/undo_operations.py` - Undo/redo defaults
- `helpers/model_canvas_loader.py` - Context menu
- `helpers/transition_prop_dialog_loader.py` - Dialog default selection (index 3)
- `engine/simulation/controller.py` - Simulation controller
- `analyses/plot_panel.py` - Plot display
- `analyses/transition_rate_panel.py` - Rate panel
- `diagnostic/locality_runtime.py` - Runtime diagnostics

### 4.2 All Default Values

| Object | Property | Default | Changed? |
|--------|----------|---------|----------|
| **Place** | tokens | 0 | No |
| | initial_marking | 0 | No |
| | capacity | None (∞) | No |
| | radius | 25.0 | No |
| | border_color | (0,0,0) | No |
| **Transition** | transition_type | **'continuous'** | ✅ YES |
| | rate | 1.0 | No |
| | rate_function | None | No |
| | earliest | 0.0 | No |
| | latest | 1.0 | No |
| | guard | None | No |
| | priority | 0 | No |
| | is_source | False | No |
| | is_sink | False | No |
| | width | 50.0 | No |
| | height | 25.0 | No |
| | border_color | (0,0,0) | No |
| **Arc** | arc_type | 'normal' | No |
| | weight | 1 | No |
| | threshold | weight | No |
| | bidirectional | False | No |

---

## Part 5: Diagnostic Features by Object Type

### 5.1 Place Diagnostics

**Property Dialog**:
- Token count (current runtime value)
- Initial marking (reset baseline)
- Capacity constraint

**Real-Time Panel** (when input/output of selected transition):
- Current token count
- Token flow direction (input ← or → output)
- Capacity violations (if any)

**Analysis Panel**:
- Token evolution plot (Place Rate Panel)
- Time series of token count

---

### 5.2 Transition Diagnostics

**Property Dialog**:
- Type selection (continuous/immediate/timed/stochastic)
- Type-specific parameters (rate_function, delays, rate)
- Guard expression
- Priority
- Source/Sink flags

**Real-Time Panel** (Diagnostics Panel):
- Locality structure (inputs/outputs)
- Static analysis (weights, balance)
- Runtime metrics (firings, throughput)
- Enablement state and reason
- Recent firing events

**Analysis Panel**:
- Behavior evolution plot (Transition Rate Panel)
- Rate curves (continuous) or cumulative firings (discrete)
- Locality places overlay (input/output token counts)

---

### 5.3 Arc Diagnostics

**Property Dialog**:
- Arc type (normal/inhibitor/reset/read)
- Weight (token multiplier)
- Threshold (enablement check)

**Real-Time Panel**:
- Shows in locality structure
- Weight displayed
- Threshold evaluation

**Visual Indicators**:
- Normal: Solid arrow
- Inhibitor: Circle endpoint
- Reset: Diamond arrowhead
- Read: Double arrow

---

## Part 6: Testing Checklist

### Test 1: Property Dialog Flow
1. ✅ Create transition (verify default type = continuous)
2. ✅ Double-click → Properties dialog opens
3. ✅ Change type to immediate → OK
4. ✅ Verify behavior changes in simulation
5. ✅ Undo → Verify type reverts to continuous
6. ✅ Check persistency marked dirty

### Test 2: Diagnostic Panel Flow
1. ✅ Select transition
2. ✅ Right-click → "Show Diagnostics"
3. ✅ Verify locality structure displayed
4. ✅ Run simulation
5. ✅ Verify runtime metrics update every 500ms
6. ✅ Verify firing events appear
7. ✅ Stop simulation
8. ✅ Verify final metrics displayed

### Test 3: Integration Flow
1. ✅ Create P1 → T1 → P2 net
2. ✅ Set P1.tokens = 10
3. ✅ Set T1.type = continuous, rate_function = "2.0"
4. ✅ Show diagnostics for T1
5. ✅ Run simulation
6. ✅ Verify:
   - T1 fires continuously
   - Diagnostics show throughput ~2 firings/s
   - P1 tokens decrease, P2 tokens increase
   - Analysis panel shows rate curve

### Test 4: Source/Sink Diagnostics
1. ✅ Create source transition (no inputs)
2. ✅ Right-click → Transform → Source
3. ✅ Show diagnostics
4. ✅ Verify "SOURCE (generates tokens)" displayed
5. ✅ Verify locality shows only output places
6. ✅ Run simulation
7. ✅ Verify tokens generated

---

## Part 7: Files Summary

### Core Files:
- `src/shypn/netobjs/place.py` - Place object
- `src/shypn/netobjs/transition.py` - Transition object (default type = continuous)
- `src/shypn/netobjs/arc.py` - Arc object

### Property Dialog Loaders:
- `src/shypn/helpers/place_prop_dialog_loader.py`
- `src/shypn/helpers/transition_prop_dialog_loader.py`
- `src/shypn/helpers/arc_prop_dialog_loader.py`

### Diagnostic Subsystem:
- `src/shypn/diagnostic/locality_detector.py` - Structure detection
- `src/shypn/diagnostic/locality_analyzer.py` - Static analysis
- `src/shypn/diagnostic/locality_runtime.py` - Runtime metrics
- `src/shypn/diagnostic/locality_info_widget.py` - GTK widget

### Real-Time Panel:
- `src/shypn/analyses/diagnostics_panel.py` - Main panel
- `src/shypn/analyses/data_collector.py` - Event storage
- `src/shypn/helpers/right_panel_loader.py` - Integration

### UI Files:
- `ui/dialogs/place_prop_dialog.ui`
- `ui/dialogs/transition_prop_dialog.ui`
- `ui/dialogs/arc_prop_dialog.ui`
- `ui/panels/right_panel.ui` (contains diagnostics tab)

---

**Document Complete**: October 12, 2025  
**Status**: Complete diagnostic flow documented  
**Next**: User testing and feedback incorporation
