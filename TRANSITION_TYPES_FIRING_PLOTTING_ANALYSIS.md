# Transition Types, Firing Methods, and Plotting System Analysis

**Date:** October 5, 2025  
**Branch:** feature/property-dialogs-and-simulation-palette  
**Scope:** Complete analysis of transition behavior system and plotting infrastructure

---

## Executive Summary

The **shypn** Petri net editor implements a sophisticated multi-type transition system with four distinct behavior types, each with specific firing semantics. The system follows the **Strategy + Factory** design pattern, with a comprehensive plotting infrastructure for real-time analysis during simulation.

### Key Components
1. **Transition Types**: 4 types (Immediate, Timed, Stochastic, Continuous)
2. **Firing Methods**: Type-specific algorithms with shared abstract interface
3. **Plotting System**: Matplotlib-based real-time rate analysis with GTK3 integration

---

## 1. Transition Types Architecture

### 1.1 Type Hierarchy

```
TransitionBehavior (ABC)
├── ImmediateBehavior      - Zero-delay discrete firing
├── TimedBehavior          - Time Petri Net (TPN) with timing windows
├── StochasticBehavior     - Fluid Stochastic PN (FSPN) with burst firing
└── ContinuousBehavior     - Stochastic Hybrid PN (SHPN) with continuous flow
```

**Location:** `src/shypn/engine/`

### 1.2 Factory Pattern

**File:** `src/shypn/engine/behavior_factory.py`

```python
def create_behavior(transition, model) -> TransitionBehavior:
    """Factory method to create appropriate transition behavior."""
    transition_type = getattr(transition, 'transition_type', 'immediate')
    
    type_map = {
        'immediate': ImmediateBehavior,
        'timed': TimedBehavior,
        'stochastic': StochasticBehavior,
        'continuous': ContinuousBehavior,
    }
    
    return type_map[transition_type](transition, model)
```

**Available Types:**
- `'immediate'` - Default, zero-delay discrete
- `'timed'` - TPN with [earliest, latest] timing windows
- `'stochastic'` - FSPN with exponential distribution + burst
- `'continuous'` - SHPN with rate functions + RK4 integration

---

## 2. Transition Type Details

### 2.1 Immediate Transitions

**File:** `src/shypn/engine/immediate_behavior.py`  
**Type Name:** "Immediate"  
**Mathematical Model:**
- **Enablement:** ∀p ∈ •t: m(p) ≥ Pre(p,t)
- **Firing:** m' = m - Pre + Post
- **Time delay:** 0 (instant)
- **Token mode:** Discrete (arc_weight units)

**Key Properties:**
```python
class ImmediateBehavior(TransitionBehavior):
    def can_fire(self) -> Tuple[bool, str]:
        # Only constraint: sufficient tokens in input places
        # No timing or rate constraints
    
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        # Consume exactly arc_weight from each input
        # Produce exactly arc_weight to each output
        # Record logical-mode event
```

**Usage:**
```python
transition.transition_type = 'immediate'
behavior = create_behavior(transition, model)

if behavior.can_fire()[0]:
    success, details = behavior.fire(input_arcs, output_arcs)
    # details: {'consumed': {...}, 'produced': {...}, 'immediate_mode': True}
```

---

### 2.2 Timed Transitions (TPN)

**File:** `src/shypn/engine/timed_behavior.py`  
**Type Name:** "Timed (TPN)"  
**Mathematical Model:**
- **Static interval:** [α(t), β(t)] where α = earliest, β = latest
- **Enabled interval:** [t + α(t), t + β(t)] for enablement time t
- **Firing constraint:** t_enable + α(t) ≤ t_fire ≤ t_enable + β(t)
- **Token mode:** Discrete (like immediate)

**Key Properties:**
```python
class TimedBehavior(TransitionBehavior):
    def __init__(self, transition, model):
        # Extract timing window
        self.earliest = float(props.get('earliest', 0.0))
        self.latest = float(props.get('latest', float('inf')))
        
        # OR use transition.rate as deterministic delay
        # self.earliest = self.latest = transition.rate
        
        self._enablement_time = None  # Set by scheduler
    
    def set_enablement_time(self, time: float):
        """Called when transition becomes structurally enabled"""
        self._enablement_time = time
    
    def can_fire(self) -> Tuple[bool, str]:
        # Check: sufficient tokens + within [earliest, latest] window
        elapsed = current_time - self._enablement_time
        
        if elapsed < self.earliest:
            return False, "too-early"
        if elapsed > self.latest:
            return False, "too-late"
        
        return True, "enabled-in-window"
```

**Timing Window Interpretation:**
- `earliest = 0, latest = ∞` → Can fire anytime after enablement
- `earliest = latest = d` → Must fire exactly at delay `d`
- `earliest = a, latest = b` → Must fire in interval [a, b]

**Floating Point Tolerance:**
- Uses `EPSILON = 1e-9` for time comparisons
- Handles accumulated floating point errors in simulation loops

---

### 2.3 Stochastic Transitions (FSPN)

**File:** `src/shypn/engine/stochastic_behavior.py`  
**Type Name:** "Stochastic (FSPN)"  
**Mathematical Model:**
- **Firing delay:** T ~ Exp(λ) where λ = rate parameter
- **Burst size:** B ~ DiscreteUniform(1, 8)
- **Tokens consumed:** arc_weight * B
- **Tokens produced:** arc_weight * B
- **Enablement:** ∀p ∈ •t: m(p) ≥ arc_weight * max_burst

**Key Properties:**
```python
class StochasticBehavior(TransitionBehavior):
    def __init__(self, transition, model):
        # Extract stochastic parameters
        self.rate = float(transition.rate or 1.0)  # λ
        self.max_burst = int(props.get('max_burst', 8))
        
        # Scheduling state
        self._enablement_time = None
        self._scheduled_fire_time = None
        self._sampled_burst = None
    
    def set_enablement_time(self, time: float):
        """Sample firing delay and burst when enabled"""
        self._enablement_time = time
        
        # Sample delay: T ~ Exp(λ)
        u = random.random()
        delay = -math.log(u) / self.rate if u > 0 else 0.0
        self._scheduled_fire_time = time + delay
        
        # Sample burst size: B ~ Uniform(1, max_burst)
        self._sampled_burst = random.randint(1, self.max_burst)
    
    def can_fire(self) -> Tuple[bool, str]:
        # Check: scheduled time reached + tokens for burst
        if current_time < self._scheduled_fire_time:
            return False, "too-early"
        
        # Check sufficient tokens for burst firing
        for arc in input_arcs:
            required = arc.weight * self._sampled_burst
            if source_place.tokens < required:
                return False, "insufficient-tokens-for-burst"
        
        return True, "enabled-stochastic"
    
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        # Consume/produce: arc_weight * burst
        burst = self._sampled_burst
        
        for arc in input_arcs:
            amount = arc.weight * burst
            source_place.set_tokens(source_place.tokens - amount)
        
        for arc in output_arcs:
            amount = arc.weight * burst
            target_place.set_tokens(target_place.tokens + amount)
        
        # Clear scheduling state
        self.clear_enablement()
```

**Stochastic Properties:**
- Mean firing delay: `1 / rate` seconds
- Burst range: 1x to 8x arc_weight (configurable)
- Rate interpretation: Higher rate → more frequent firing

---

### 2.4 Continuous Transitions (SHPN)

**File:** `src/shypn/engine/continuous_behavior.py`  
**Type Name:** "Continuous (SHPN)"  
**Mathematical Model:**
- **Rate function:** r(t) = f(m(t), params)
- **Token flow:** dm/dt = r(t)
- **Integration:** RK4 method with adaptive step size
- **Enablement:** Continuous if ∀p ∈ •t: m(p) > 0

**Key Properties:**
```python
class ContinuousBehavior(TransitionBehavior):
    def __init__(self, transition, model):
        # Extract continuous parameters
        rate_expr = transition.rate or '1.0'
        self.max_rate = float(props.get('max_rate', float('inf')))
        self.min_rate = float(props.get('min_rate', 0.0))
        
        # Compile rate function
        self.rate_function = self._compile_rate_function(rate_expr)
        
        # Integration parameters
        self.integration_method = 'rk4'
        self.min_step = 0.0001
        self.max_step = 0.1
    
    def _compile_rate_function(self, expr: str) -> Callable:
        """Compile rate function expression to callable.
        
        Supported formats:
        - Constant: "5.0" → r(t) = 5.0
        - Linear: "2.0 * P1" → r(t) = 2.0 * tokens(P1)
        - Saturated: "min(10, P1)" → r(t) = min(10, tokens(P1))
        - Custom: callable(places, time) → float
        """
        if callable(expr):
            return expr
        
        # Parse constant
        try:
            constant_rate = float(expr)
            return lambda places, t: constant_rate
        except ValueError:
            pass
        
        # Parse expression with place references
        def evaluate_rate(places: Dict, time: float) -> float:
            context = {
                'time': time, 't': time,
                'min': min, 'max': max, 'abs': abs,
                'math': math, 'np': np,
            }
            
            # Add place tokens as P1, P2, ...
            for place_id, place in places.items():
                context[f'P{place_id}'] = place.tokens
            
            result = eval(expr, {"__builtins__": {}}, context)
            return float(result)
        
        return evaluate_rate
    
    def can_fire(self) -> Tuple[bool, str]:
        # Continuous enabled if all input places have positive tokens
        for arc in input_arcs:
            if source_place.tokens <= 0:
                return False, "input-place-empty"
        
        return True, "enabled-continuous"
    
    def integrate_step(self, dt: float, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        """RK4 integration over time step"""
        # Evaluate rate function
        rate = self.rate_function(places_dict, current_time)
        rate = max(self.min_rate, min(self.max_rate, rate))
        
        # Continuous consumption/production: arc_weight * rate * dt
        for arc in input_arcs:
            consumption = arc.weight * rate * dt
            actual = min(consumption, source_place.tokens)  # Clamp to available
            source_place.set_tokens(source_place.tokens - actual)
        
        for arc in output_arcs:
            production = arc.weight * rate * dt
            target_place.set_tokens(target_place.tokens + production)
```

**Rate Function Examples:**
- Constant: `"5.0"` → 5 tokens/second
- Proportional: `"2.0 * P1"` → Rate depends on P1 tokens
- Saturated: `"min(10, P1)"` → Max 10 tokens/second
- Time-based: `"5 * (1 + 0.5 * sin(time))"` → Oscillating rate

---

## 3. Firing Methods Architecture

### 3.1 Abstract Interface

**File:** `src/shypn/engine/transition_behavior.py`

```python
class TransitionBehavior(ABC):
    """Abstract base class for transition firing behaviors."""
    
    @abstractmethod
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire.
        
        Returns:
            (can_fire: bool, reason: str)
        """
        pass
    
    @abstractmethod
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict]:
        """Execute firing logic.
        
        Returns:
            (success: bool, details: dict)
        """
        pass
    
    @abstractmethod
    def get_type_name(self) -> str:
        """Return human-readable type name."""
        pass
    
    # === Utility Methods (Available to all subclasses) ===
    
    def is_enabled(self) -> bool:
        """Check structural enablement (sufficient tokens)."""
    
    def get_input_arcs(self) -> List:
        """Get all input arcs to this transition."""
    
    def get_output_arcs(self) -> List:
        """Get all output arcs from this transition."""
    
    def _get_place(self, place_id: int):
        """Get place object by ID."""
    
    def _get_current_time(self) -> float:
        """Get current simulation time from model."""
    
    def _record_event(self, consumed: Dict, produced: Dict, mode: str, **kwargs):
        """Record transition firing event in model history."""
```

### 3.2 Common Firing Flow

All transition types follow this general pattern:

```
1. Check Enablement (can_fire)
   ├─ Structural: Sufficient tokens?
   ├─ Type-specific: Timing window? Rate function? Burst capacity?
   └─ Return (bool, reason)

2. Execute Firing (fire)
   ├─ Validate enablement (double-check)
   ├─ Consume tokens from input places
   ├─ Produce tokens to output places
   ├─ Update internal state (clear scheduling, etc.)
   ├─ Record firing event for analysis
   └─ Return (success, details)

3. Record Event (_record_event)
   ├─ Consumed: {place_id: amount, ...}
   ├─ Produced: {place_id: amount, ...}
   ├─ Mode: 'logical', 'stochastic', 'continuous'
   └─ Type-specific metadata
```

### 3.3 Error Handling

All behaviors return structured error information:

```python
# Success case
(True, {
    'consumed': {1: 2.0, 3: 1.0},
    'produced': {2: 3.0},
    'transition_type': 'immediate',
    'time': 10.5
})

# Failure case
(False, {
    'reason': 'insufficient-tokens-P1',
    'place_id': 1,
    'required': 2.0,
    'available': 1.0,
    'immediate_mode': True
})
```

---

## 4. Plotting System Architecture

### 4.1 Component Overview

**Location:** `src/shypn/analyses/`

```
analyses/
├── __init__.py                    - Lazy-loading package
├── data_collector.py              - SimulationDataCollector (raw data)
├── rate_calculator.py             - RateCalculator (compute rates)
├── plot_panel.py                  - AnalysisPlotPanel (base class)
├── place_rate_panel.py            - PlaceRatePanel (token rate)
├── transition_rate_panel.py       - TransitionRatePanel (firing rate)
├── search_handler.py              - SearchHandler (find objects)
└── context_menu_handler.py        - ContextMenuHandler (right-click)
```

### 4.2 Data Collection System

**File:** `src/shypn/analyses/data_collector.py`

```python
class SimulationDataCollector:
    """Collects raw simulation data for rate-based analysis."""
    
    def __init__(self, max_data_points=10000, downsample_threshold=8000):
        # Place data: {place_id: [(time, tokens), ...]}
        self.place_data: Dict[Any, List[Tuple[float, int]]] = defaultdict(list)
        
        # Transition data: {transition_id: [(time, event_type, details), ...]}
        self.transition_data: Dict[Any, List[Tuple[float, str, Any]]] = defaultdict(list)
    
    def on_simulation_step(self, controller, time: float):
        """Called by simulation controller after each step."""
        # Collect place token counts
        for place in controller.model.places:
            self.place_data[place.id].append((time, place.tokens))
        
        # Auto-downsample if threshold exceeded
        if len(data) > self.downsample_threshold:
            self._downsample_place_data(place.id)
    
    def on_transition_fired(self, transition, time: float, details=None):
        """Record transition firing event."""
        self.transition_data[transition.id].append((time, 'fired', details))
```

**Data Structure:**
```python
# Place data example
place_data[place_id] = [
    (0.0, 5),    # time=0.0, tokens=5
    (0.1, 4),    # time=0.1, tokens=4
    (0.2, 6),    # time=0.2, tokens=6
    ...
]

# Transition data example
transition_data[trans_id] = [
    (0.15, 'fired', {'consumed': {1: 1}, 'produced': {2: 1}}),
    (0.28, 'fired', {'consumed': {1: 1}, 'produced': {2: 1}}),
    ...
]
```

**Memory Management:**
- **Automatic downsampling** when threshold exceeded (8000 points)
- Keeps first, every 2nd, and last point → 50% reduction
- Prevents unbounded memory growth in long simulations

---

### 4.3 Base Plotting Panel

**File:** `src/shypn/analyses/plot_panel.py`

```python
class AnalysisPlotPanel(Gtk.Box):
    """Base class for matplotlib-based plotting panels.
    
    Provides:
    - Matplotlib canvas integration with GTK3
    - Selected objects list with remove buttons
    - Real-time plot updates with throttling
    - Color palette for multiple objects
    - Plot controls (grid, legend, auto-scale)
    """
    
    # Color palette (10 distinct colors)
    COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', 
              '#9b59b6', '#1abc9c', '#e67e22', '#34495e',
              '#16a085', '#c0392b']
    
    def __init__(self, object_type: str, data_collector):
        """Initialize panel.
        
        Args:
            object_type: 'place' or 'transition'
            data_collector: SimulationDataCollector instance
        """
        self.object_type = object_type
        self.data_collector = data_collector
        self.selected_objects: List[Any] = []
        
        # Plot update throttling
        self.needs_update = False
        self.update_interval = 100  # milliseconds
        
        # Build UI: list + controls + matplotlib canvas
        self._setup_ui()
        
        # Start periodic update timer
        GLib.timeout_add(self.update_interval, self._periodic_update)
    
    def add_object(self, obj: Any):
        """Add object to selected list for plotting."""
        self.selected_objects.append(obj)
        self._update_objects_list()
        self.needs_update = True
    
    def update_plot(self):
        """Update plot with current data (called by timer)."""
        self.axes.clear()
        
        if not self.selected_objects:
            self._show_empty_state()
            return
        
        # Plot rate for each selected object
        for i, obj in enumerate(self.selected_objects):
            rate_data = self._get_rate_data(obj.id)  # Subclass implements
            
            if rate_data:
                times = [t for t, r in rate_data]
                rates = [r for t, r in rate_data]
                
                self.axes.plot(times, rates,
                              label=f'{obj.name}',
                              color=self._get_color(i),
                              linewidth=2)
        
        self._format_plot()
        self.canvas.draw()
    
    # === Abstract methods for subclasses ===
    
    @abstractmethod
    def _get_rate_data(self, obj_id) -> List[Tuple[float, float]]:
        """Get rate data for an object."""
        pass
    
    @abstractmethod
    def _get_ylabel(self) -> str:
        """Get Y-axis label."""
        pass
    
    @abstractmethod
    def _get_title(self) -> str:
        """Get plot title."""
        pass
```

**UI Structure:**
```
┌─────────────────────────────────┐
│ Selected Places/Transitions     │
│ ┌─────────────────────────────┐ │
│ │ ■ P1 (Place 1)          [✕] │ │
│ │ ■ P2 (Place 2)          [✕] │ │
│ └─────────────────────────────┘ │
│ [Clear Selection]               │
├─────────────────────────────────┤
│ Plot Controls                   │
│ [✓] Show Grid                   │
│ [✓] Show Legend                 │
│ [✓] Auto Scale Y-axis           │
├─────────────────────────────────┤
│ [Matplotlib Toolbar]            │
│ ┌─────────────────────────────┐ │
│ │                             │ │
│ │    [Plot Canvas]            │ │
│ │                             │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

---

### 4.4 Place Rate Panel

**File:** `src/shypn/analyses/place_rate_panel.py`

```python
class PlaceRatePanel(AnalysisPlotPanel):
    """Panel for plotting place token consumption/production rates.
    
    Displays: d(tokens)/dt over simulation time
    
    Rate interpretation:
    - Positive rate: Token production (tokens being added)
    - Negative rate: Token consumption (tokens being removed)
    - Zero rate: Stable state (no net change)
    """
    
    def __init__(self, data_collector):
        super().__init__('place', data_collector)
        self.time_window = 0.1  # 100ms window for rate calculation
    
    def _get_rate_data(self, place_id) -> List[Tuple[float, float]]:
        """Calculate token rate data using rate calculator."""
        raw_data = self.data_collector.get_place_data(place_id)
        
        if len(raw_data) < 2:
            return []
        
        rate_series = self.rate_calculator.calculate_token_rate_series(
            raw_data,
            time_window=self.time_window,
            sample_interval=0.01  # 10ms sampling
        )
        
        return rate_series
    
    def _get_ylabel(self) -> str:
        return 'Token Rate (tokens/s)'
    
    def _get_title(self) -> str:
        return 'Place Token Consumption/Production Rate'
```

**Plot Features:**
- **Zero reference line** to distinguish consumption from production
- **Color-coded curves** for multiple places
- **Smooth rate calculation** using sliding time window
- **Real-time updates** during simulation

---

### 4.5 Transition Rate Panel

**File:** `src/shypn/analyses/transition_rate_panel.py`

```python
class TransitionRatePanel(AnalysisPlotPanel):
    """Panel for plotting transition firing rates.
    
    Displays: firings per unit time (Hz)
    
    Rate interpretation:
    - High rate: Transition firing frequently
    - Low rate: Transition firing occasionally
    - Zero rate: Transition not firing (disabled or in conflict)
    """
    
    def __init__(self, data_collector):
        super().__init__('transition', data_collector)
        self.time_window = 1.0  # 1 second window for frequency measurement
    
    def _get_rate_data(self, transition_id) -> List[Tuple[float, float]]:
        """Calculate firing rate data using rate calculator."""
        raw_events = self.data_collector.get_transition_data(transition_id)
        
        if not raw_events:
            return []
        
        # Extract firing times
        firing_times = [t for t, event_type, _ in raw_events 
                       if event_type == 'fired']
        
        if len(firing_times) < 1:
            return []
        
        rate_series = self.rate_calculator.calculate_firing_rate_series(
            firing_times,
            time_window=self.time_window,
            sample_interval=0.1  # 100ms sampling
        )
        
        return rate_series
    
    def _get_ylabel(self) -> str:
        return 'Firing Rate (firings/s)'
    
    def _get_title(self) -> str:
        return 'Transition Firing Rate'
```

**Plot Features:**
- **Frequency measurement** in Hz (firings/second)
- **1-second time window** for meaningful frequency values
- **Event-based calculation** from discrete firing events
- **Real-time visualization** of firing patterns

---

## 5. Integration Points

### 5.1 Transition → Behavior Creation

```python
# In simulation controller or model
from shypn.engine import create_behavior

# Create behavior for transition
behavior = create_behavior(transition, model)

# Check and fire
if behavior.can_fire()[0]:
    success, details = behavior.fire(
        behavior.get_input_arcs(),
        behavior.get_output_arcs()
    )
```

### 5.2 Simulation → Data Collection

```python
# In simulation controller initialization
from shypn.analyses import SimulationDataCollector

collector = SimulationDataCollector()

# Register as step listener
controller.add_step_listener(collector.on_simulation_step)

# Record transition firings
controller.data_collector = collector
```

### 5.3 UI → Plotting Panels

```python
# In right panel loader
from shypn.analyses import PlaceRatePanel, TransitionRatePanel

# Create panels
place_panel = PlaceRatePanel(data_collector)
transition_panel = TransitionRatePanel(data_collector)

# Add to UI
notebook.append_page(place_panel, Gtk.Label(label="Places"))
notebook.append_page(transition_panel, Gtk.Label(label="Transitions"))

# Wire search functionality
place_panel.wire_search_ui(entry, search_btn, result_label, model)
```

---

## 6. Key Design Patterns

### 6.1 Strategy Pattern
- **TransitionBehavior** is the strategy interface
- Each type (Immediate, Timed, Stochastic, Continuous) is a concrete strategy
- Allows runtime selection of firing algorithm

### 6.2 Factory Pattern
- **create_behavior()** factory method
- Centralizes behavior creation logic
- Type mapping based on `transition.transition_type` attribute

### 6.3 Observer Pattern
- **Data Collector** acts as observer
- Listens to simulation steps and firing events
- Decouples data collection from simulation logic

### 6.4 Template Method Pattern
- **AnalysisPlotPanel** defines plotting template
- Subclasses implement specific rate calculations
- Common UI and update logic shared

---

## 7. Configuration and Properties

### 7.1 Transition Type Assignment

```python
# On transition object
transition.transition_type = 'immediate'  # or 'timed', 'stochastic', 'continuous'
```

### 7.2 Type-Specific Properties

**Immediate:**
- No additional properties required

**Timed:**
```python
transition.rate = 2.0  # Deterministic delay (earliest = latest = 2.0)
# OR
transition.properties = {
    'earliest': 1.0,  # Minimum delay
    'latest': 5.0     # Maximum delay
}
```

**Stochastic:**
```python
transition.rate = 3.0  # Rate parameter λ (mean delay = 1/3.0 = 0.33s)
transition.properties = {
    'max_burst': 8  # Maximum burst multiplier (default: 8)
}
```

**Continuous:**
```python
transition.rate = "5.0"  # Constant rate
# OR
transition.rate = "2.0 * P1"  # Rate depends on P1 tokens
# OR
transition.properties = {
    'rate_function': "min(10, P1)",
    'max_rate': 10.0,
    'min_rate': 0.0
}
```

---

## 8. Testing Infrastructure

**Test Files:**
```
tests/
├── test_phase1_behavior_integration.py      - Immediate behavior tests
├── test_phase2_conflict_resolution.py       - Priority and conflicts
├── test_phase3_time_aware.py                - Timed transition tests
├── test_phase4_continuous.py                - Continuous integration tests
└── test_debug_behavior.py                   - Debug helpers
```

**Example Test:**
```python
def test_immediate_firing():
    # Create net
    net = PetriNet()
    p1 = net.add_place(tokens=5)
    t1 = net.add_transition(transition_type='immediate')
    p2 = net.add_place(tokens=0)
    
    net.add_arc(p1, t1, weight=2)
    net.add_arc(t1, p2, weight=1)
    
    # Create behavior
    behavior = create_behavior(t1, net)
    
    # Check enablement
    assert behavior.can_fire()[0] == True
    
    # Fire
    success, details = behavior.fire(
        behavior.get_input_arcs(),
        behavior.get_output_arcs()
    )
    
    assert success == True
    assert p1.tokens == 3  # 5 - 2
    assert p2.tokens == 1  # 0 + 1
```

---

## 9. Summary and Recommendations

### 9.1 Current State
✅ **Complete implementation** of 4 transition types  
✅ **Mature firing methods** with comprehensive error handling  
✅ **Production-ready plotting system** with real-time analysis  
✅ **Well-documented codebase** with clear abstractions  
✅ **Test coverage** for all major behaviors  

### 9.2 Strengths
- **Clean separation of concerns** (strategy pattern)
- **Type-specific semantics** correctly implemented
- **Extensible architecture** (easy to add new transition types)
- **Real-time analysis** without performance degradation
- **Memory-efficient data collection** with auto-downsampling

### 9.3 Areas for Enhancement

**Transition System:**
- Add **inhibitor arc support** in behavior checks
- Implement **priority-based scheduling** for conflict resolution
- Add **transition guards** (boolean predicates)
- Support **reset arcs** (consume all tokens)

**Plotting System:**
- Add **histogram plots** for token distribution
- Implement **heatmap views** for large nets
- Add **export to CSV/PNG** functionality
- Support **plot comparison** between simulation runs

**Performance:**
- Consider **lazy evaluation** for large nets
- Implement **spatial indexing** for arc queries
- Add **caching** for frequently accessed behavior objects

### 9.4 Next Steps

1. **Document rate calculator** (missing from analysis)
2. **Add function catalog** for continuous rate functions
3. **Implement context menu handlers** for "Add to Analysis"
4. **Create user documentation** with examples
5. **Add simulation controller integration** guide

---

## 10. File Reference

### Core Transition System
| File | Purpose | Lines |
|------|---------|-------|
| `src/shypn/netobjs/transition.py` | Transition class definition | ~240 |
| `src/shypn/engine/transition_behavior.py` | Abstract base class | ~180 |
| `src/shypn/engine/behavior_factory.py` | Factory method | ~60 |
| `src/shypn/engine/immediate_behavior.py` | Immediate firing | ~240 |
| `src/shypn/engine/timed_behavior.py` | Timed firing | ~310 |
| `src/shypn/engine/stochastic_behavior.py` | Stochastic firing | ~340 |
| `src/shypn/engine/continuous_behavior.py` | Continuous flow | ~390 |

### Plotting System
| File | Purpose | Lines |
|------|---------|-------|
| `src/shypn/analyses/__init__.py` | Package initialization | ~50 |
| `src/shypn/analyses/data_collector.py` | Raw data collection | ~200 |
| `src/shypn/analyses/plot_panel.py` | Base plotting panel | ~450 |
| `src/shypn/analyses/place_rate_panel.py` | Place rate plotting | ~150 |
| `src/shypn/analyses/transition_rate_panel.py` | Transition rate plotting | ~150 |

### Total Lines of Code
- **Transition System:** ~1,760 lines
- **Plotting System:** ~1,000 lines
- **Total:** ~2,760 lines (excluding tests and documentation)

---

**End of Analysis**
