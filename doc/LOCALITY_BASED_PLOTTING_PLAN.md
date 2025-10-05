# Locality-Based Plotting Implementation Plan

## Overview

Implement the **locality concept** from legacy code where transitions and their connected places (inputs and outputs) are plotted together in the same canvas. This provides a **transition-centered view** showing how the transition affects its immediate neighborhood.

**Core Concept** (from legacy):
> "Place-transition-place defines what is called a Locality"

A locality is:
- **Input Places** → **Transition** → **Output Places**
- Independent unit with bounded semantics
- All elements plotted together in transition's canvas

---

## Legacy Concepts to Implement

### 1. Locality Structure (from `locality.py`)

```python
class Locality:
    - places: Dict[int, Place]              # All places in locality
    - transitions: Dict[int, Transition]    # Typically 1 (central transition)
    - input_arcs: Dict[int, Arc]           # Place → Transition
    - output_arcs: Dict[int, Arc]          # Transition → Place
    
    - input_places: Set[int]               # Places that FEED the transition
    - output_places: Set[int]              # Places that RECEIVE from transition
    - central_transition: int              # The transition itself
```

**Key Insight**: Each locality has:
- **Exactly ONE central transition**
- **≥1 input places** (provide tokens TO transition)
- **≥1 output places** (receive tokens FROM transition)

### 2. Locality Detection (from `locality_manager.py`)

```python
class LocalityManager:
    def detect_localities() -> List[Locality]:
        """
        Algorithm:
        1. For each transition:
           - Find input places (arcs: place → transition)
           - Find output places (arcs: transition → place)
           - If has ≥1 input AND ≥1 output: create locality
        2. Build locality object with all connected elements
        3. Allow places to be shared between localities (organic system)
        """
```

**Key Insight**: Localities can **share places** (multiple transitions can connect to same place), but each locality is independent for firing logic.

---

## Current System Analysis

### Current Architecture

```
TransitionRatePanel (analysis panel for transitions)
├── Plots transition behavior (rate or cumulative count)
├── Uses SimulationDataCollector
└── Currently: Only shows transition data

PlaceRatePanel (analysis panel for places)
├── Plots place token evolution
├── Uses SimulationDataCollector  
└── Currently: Separate from transitions
```

**Problem**: Places and transitions are analyzed separately, losing context of their relationship.

---

## Proposed Architecture

### Enhanced TransitionRatePanel with Locality

```
TransitionRatePanel (enhanced)
├── Main plot: Transition behavior (rate/cumulative)
│   └── Primary Y-axis (left): Rate or count
│
├── Locality place plots: Token evolution
│   ├── Input places (feeding transition)
│   └── Output places (receiving from transition)
│   └── Secondary Y-axis (right): Token count
│
└── Legend distinguishes:
    ├── Transition behavior (bold line)
    ├── Input places (dashed, one color family)
    └── Output places (dashed, different color family)
```

### Visual Example

```
TransitionRatePanel for T1 (Continuous, sigmoid rate)
┌────────────────────────────────────────────┐
│  T1 (Continuous) - Locality View          │
├────────────────────────────────────────────┤
│                                            │
│  Rate (left Y)    ^                        │
│                  /│\                       │
│        sigmoid  / │ \   P1 (input)        │
│        curve   /  │  ----                  │
│              _/   │      \                 │
│            _/     │       P2 (output)      │
│          _/       │           ----         │
│  ═══════         │                        │
│  0 ─────────────────────────────► Time    │
│                                            │
│  Legend:                                   │
│  ━━━ T1 Rate       ┈┈┈ P1 Tokens         │
│                    ┈┈┈ P2 Tokens         │
└────────────────────────────────────────────┘
```

**Benefits**:
1. **Context**: See cause (input tokens) and effect (output tokens) together
2. **Debugging**: Identify why transition fires or stops
3. **Validation**: Verify token flow consistency
4. **Organic view**: Match legacy locality semantics

---

## Implementation Plan

### Phase 1: Locality Detection Module

**File**: `src/shypn/engine/locality_detector.py` (NEW)

```python
class LocalityDetector:
    """Detect localities (transition neighborhoods) in Petri net."""
    
    @staticmethod
    def get_locality_for_transition(transition, model) -> Dict[str, Any]:
        """
        Get locality information for a transition.
        
        Returns:
            {
                'transition': transition,
                'input_places': [Place, ...],  # Feed TO transition
                'output_places': [Place, ...], # Receive FROM transition
                'input_arcs': [Arc, ...],
                'output_arcs': [Arc, ...]
            }
        """
        locality = {
            'transition': transition,
            'input_places': [],
            'output_places': [],
            'input_arcs': [],
            'output_arcs': []
        }
        
        # Find all arcs for this transition
        for arc in model.arcs.values():
            # Input arc: place → transition
            if arc.target == transition:
                locality['input_arcs'].append(arc)
                locality['input_places'].append(arc.source)
            
            # Output arc: transition → place
            elif arc.source == transition:
                locality['output_arcs'].append(arc)
                locality['output_places'].append(arc.target)
        
        return locality
```

**Testing**:
```python
# Test with simple P-T-P net
detector = LocalityDetector()
locality = detector.get_locality_for_transition(t1, model)
assert len(locality['input_places']) >= 1
assert len(locality['output_places']) >= 1
```

---

### Phase 2: Enhanced TransitionRatePanel

**File**: `src/shypn/analyses/transition_rate_panel.py` (MODIFY)

#### 2.1 Add Locality Plotting

```python
class TransitionRatePanel(AnalysisPlotPanel):
    def __init__(self, data_collector, model):  # ADD model parameter
        super().__init__('transition', data_collector)
        self.model = model  # Need model for locality detection
        self.show_locality = True  # Toggle for locality plotting
        self.locality_detector = LocalityDetector()
    
    def add_object(self, transition):
        """Override to add transition AND its locality places."""
        super().add_object(transition)
        
        if self.show_locality:
            # Get locality for this transition
            locality = self.locality_detector.get_locality_for_transition(
                transition, self.model
            )
            
            # Track locality places for this transition
            if not hasattr(self, '_locality_places'):
                self._locality_places = {}
            
            self._locality_places[transition.id] = {
                'input_places': locality['input_places'],
                'output_places': locality['output_places']
            }
    
    def _plot_data(self):
        """Override to plot transition + locality places."""
        if not self.axes:
            return
        
        self.axes.clear()
        
        # Plot each transition with its locality
        for transition_id in self._tracked_objects:
            # Plot transition behavior (existing code)
            self._plot_transition_behavior(transition_id)
            
            # Plot locality places (NEW)
            if hasattr(self, '_locality_places') and transition_id in self._locality_places:
                self._plot_locality_places(transition_id)
        
        self._finalize_plot()
    
    def _plot_locality_places(self, transition_id):
        """Plot input and output places for transition's locality."""
        locality_places = self._locality_places[transition_id]
        
        # Plot input places (dashed, blue family)
        for i, place in enumerate(locality_places['input_places']):
            place_data = self.data_collector.get_place_data(place.id)
            if place_data:
                times, tokens = zip(*place_data)
                label = f"{place.name} (input)"
                self.axes.plot(times, tokens, 
                             linestyle='--', 
                             color=f'C{i}',  # Blue family
                             alpha=0.7,
                             label=label)
        
        # Plot output places (dashed, orange family)
        for i, place in enumerate(locality_places['output_places']):
            place_data = self.data_collector.get_place_data(place.id)
            if place_data:
                times, tokens = zip(*place_data)
                label = f"{place.name} (output)"
                offset = len(locality_places['input_places'])
                self.axes.plot(times, tokens,
                             linestyle=':',
                             color=f'C{offset + i}',  # Orange family
                             alpha=0.7,
                             label=label)
```

#### 2.2 Dual Y-Axis for Better Scaling

```python
def _setup_dual_y_axes(self):
    """Setup dual Y-axes: left for transition, right for places."""
    # Left Y-axis: Transition rate/count
    self.axes.set_ylabel('Transition Behavior', color='black')
    self.axes.tick_params(axis='y', labelcolor='black')
    
    # Right Y-axis: Place tokens
    self.axes2 = self.axes.twinx()
    self.axes2.set_ylabel('Place Tokens', color='gray')
    self.axes2.tick_params(axis='y', labelcolor='gray')
    
    return self.axes, self.axes2
```

---

### Phase 3: Enhanced Add-to-Analyses Dialog

**File**: `src/shypn/helpers/right_panel_loader.py` (MODIFY)

#### 3.1 Show Locality Information

```python
def _on_add_to_analysis_clicked(self, button):
    """Show dialog to add object to analysis with locality info."""
    dialog = Gtk.Dialog(
        title="Add to Analysis",
        transient_for=self.window,
        flags=0
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        "Add", Gtk.ResponseType.OK
    )
    
    content = dialog.get_content_area()
    
    # Object type selection (existing)
    type_box = self._create_type_selector()
    content.pack_start(type_box, False, False, 10)
    
    # NEW: Locality options for transitions
    locality_box = self._create_locality_options()
    content.pack_start(locality_box, False, False, 10)
    
    # Object selection (existing)
    object_box = self._create_object_selector()
    content.pack_start(object_box, False, False, 10)
    
    dialog.show_all()
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        self._add_selected_objects_with_locality()
    
    dialog.destroy()

def _create_locality_options(self):
    """Create checkbox for locality plotting."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    
    label = Gtk.Label(label="Locality Options (for transitions):")
    box.pack_start(label, False, False, 0)
    
    self.show_locality_check = Gtk.CheckButton(
        label="Include connected places (input/output)"
    )
    self.show_locality_check.set_active(True)  # Default: ON
    self.show_locality_check.set_tooltip_text(
        "Plot input and output places together with transition"
    )
    box.pack_start(self.show_locality_check, False, False, 0)
    
    # Info label explaining locality
    info = Gtk.Label()
    info.set_markup(
        "<i><small>Locality shows transition with its connected places:\n"
        "• Input places (provide tokens TO transition)\n"
        "• Output places (receive tokens FROM transition)</small></i>"
    )
    info.set_line_wrap(True)
    box.pack_start(info, False, False, 5)
    
    return box
```

---

### Phase 4: Unified Search Mechanism

**File**: `src/shypn/helpers/right_panel_loader.py` (MODIFY)

#### 4.1 Search Transition → Include Locality Places

```python
def _on_search_button_clicked(self, button):
    """Enhanced search: find transition AND its locality."""
    search_term = self.search_entry.get_text().lower()
    
    if not search_term:
        return
    
    results = []
    
    # Search transitions
    for transition in self.model.transitions.values():
        if search_term in transition.name.lower():
            results.append({
                'type': 'transition',
                'object': transition,
                'locality': None  # Will populate below
            })
    
    # For each found transition, add locality info
    detector = LocalityDetector()
    for result in results:
        if result['type'] == 'transition':
            locality = detector.get_locality_for_transition(
                result['object'], self.model
            )
            result['locality'] = locality
    
    # Also search places
    for place in self.model.places.values():
        if search_term in place.name.lower():
            results.append({
                'type': 'place',
                'object': place,
                'locality': None
            })
    
    self._display_search_results(results)

def _display_search_results(self, results):
    """Display search results with locality information."""
    # Clear previous results
    for child in self.results_box.get_children():
        self.results_box.remove(child)
    
    if not results:
        label = Gtk.Label(label="No results found")
        self.results_box.pack_start(label, False, False, 5)
        self.results_box.show_all()
        return
    
    for result in results:
        result_box = self._create_result_item(result)
        self.results_box.pack_start(result_box, False, False, 2)
    
    self.results_box.show_all()

def _create_result_item(self, result):
    """Create UI item for search result with locality info."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    box.set_margin_start(10)
    box.set_margin_end(10)
    box.set_margin_top(5)
    box.set_margin_bottom(5)
    
    # Main object info
    obj = result['object']
    obj_type = result['type']
    
    header = Gtk.Label()
    header.set_markup(f"<b>{obj.name}</b> ({obj_type})")
    header.set_xalign(0)
    box.pack_start(header, False, False, 0)
    
    # Locality info for transitions
    if obj_type == 'transition' and result['locality']:
        locality = result['locality']
        
        # Input places
        if locality['input_places']:
            input_names = ', '.join(p.name for p in locality['input_places'])
            input_label = Gtk.Label()
            input_label.set_markup(f"  <i>Inputs: {input_names}</i>")
            input_label.set_xalign(0)
            box.pack_start(input_label, False, False, 0)
        
        # Output places
        if locality['output_places']:
            output_names = ', '.join(p.name for p in locality['output_places'])
            output_label = Gtk.Label()
            output_label.set_markup(f"  <i>Outputs: {output_names}</i>")
            output_label.set_xalign(0)
            box.pack_start(output_label, False, False, 0)
    
    # Add button
    add_button = Gtk.Button(label="Add to Analysis")
    add_button.connect('clicked', self._on_add_result_to_analysis, result)
    box.pack_start(add_button, False, False, 5)
    
    # Separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(separator, False, False, 0)
    
    return box
```

---

## Testing Strategy

### Test 1: Simple P-T-P Locality

```python
def test_simple_locality():
    """Test: P1 → T1 → P2 (one input, one output)"""
    # Create model
    model = PetriNetModel()
    p1 = model.create_place(x=100, y=100, initial_tokens=10)
    t1 = model.create_transition(x=200, y=100, transition_type='continuous')
    p2 = model.create_place(x=300, y=100, initial_tokens=0)
    
    arc1 = model.create_arc(p1, t1)  # Input
    arc2 = model.create_arc(t1, p2)  # Output
    
    # Detect locality
    detector = LocalityDetector()
    locality = detector.get_locality_for_transition(t1, model)
    
    # Verify
    assert len(locality['input_places']) == 1
    assert len(locality['output_places']) == 1
    assert locality['input_places'][0] == p1
    assert locality['output_places'][0] == p2
    
    print("✓ Simple locality detected correctly")
```

### Test 2: Multiple Inputs/Outputs

```python
def test_multi_locality():
    """Test: P1, P2 → T1 → P3, P4 (multi-input, multi-output)"""
    model = PetriNetModel()
    
    p1 = model.create_place(initial_tokens=5)
    p2 = model.create_place(initial_tokens=3)
    t1 = model.create_transition(transition_type='stochastic')
    p3 = model.create_place(initial_tokens=0)
    p4 = model.create_place(initial_tokens=0)
    
    model.create_arc(p1, t1)
    model.create_arc(p2, t1)
    model.create_arc(t1, p3)
    model.create_arc(t1, p4)
    
    detector = LocalityDetector()
    locality = detector.get_locality_for_transition(t1, model)
    
    assert len(locality['input_places']) == 2
    assert len(locality['output_places']) == 2
    
    print("✓ Multi-place locality detected correctly")
```

### Test 3: Locality Plotting

```python
def test_locality_plotting():
    """Test: Transition + locality places plot together"""
    # Create model with P-T-P
    model = create_test_model()
    
    # Create panel
    data_collector = SimulationDataCollector()
    panel = TransitionRatePanel(data_collector, model)
    panel.show_locality = True
    
    # Add transition (should auto-add locality)
    t1 = model.transitions[1]
    panel.add_object(t1)
    
    # Verify locality tracked
    assert hasattr(panel, '_locality_places')
    assert t1.id in panel._locality_places
    
    # Run simulation
    controller = SimulationController(model, data_collector)
    controller.run_for_duration(10.0)
    
    # Verify plot contains transition + places
    # (Check legend labels, line count, etc.)
    
    print("✓ Locality plotting works correctly")
```

---

## File Changes Summary

### New Files:
1. **`src/shypn/engine/locality_detector.py`**
   - `LocalityDetector` class
   - `get_locality_for_transition()` method

### Modified Files:
1. **`src/shypn/analyses/transition_rate_panel.py`**
   - Add `model` parameter to `__init__`
   - Add `_locality_places` tracking
   - Add `_plot_locality_places()` method
   - Modify `_plot_data()` to include locality
   - Add dual Y-axis support

2. **`src/shypn/helpers/right_panel_loader.py`**
   - Add locality options to add-to-analyses dialog
   - Modify search to include locality info
   - Enhance result display with locality details

3. **`src/shypn/data/canvas/document_model.py`** (potentially)
   - May need to pass model reference to panel constructors

---

## Benefits

1. **Context-Aware Analysis**: See transitions with their causal context
2. **Debugging Power**: Identify token flow issues immediately
3. **Legacy Compliance**: Match organic locality semantics from legacy code
4. **Scalability**: Works for simple and complex locality patterns
5. **User-Friendly**: Search finds transitions with their neighborhoods

---

## Next Steps

1. ✅ Review legacy locality concept (DONE)
2. ⏳ Implement `LocalityDetector` class
3. ⏳ Enhance `TransitionRatePanel` with locality plotting
4. ⏳ Update add-to-analyses dialog with locality options
5. ⏳ Implement unified search with locality info
6. ⏳ Test with various net topologies
7. ⏳ Document for users

---

## Questions for User

1. **Dual Y-axis**: Should places use separate Y-axis (tokens) from transition (rate/count)?
2. **Color scheme**: Different colors for input vs output places?
3. **Toggle**: Should locality plotting be optional per transition?
4. **Search scope**: Should searching for transition auto-select locality places?
5. **Performance**: Limit number of places plotted per transition?

Ready to proceed with implementation! 🎯
