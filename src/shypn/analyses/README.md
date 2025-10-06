# Analysis Modules

This directory contains modules for static and dynamic analysis of Petri Net models, including structural analysis, behavioral properties, and diagnostic tools.

## Analysis Modules

### `context_menu_handler.py`
**Context Menu Integration**

Handles right-click context menu for analysis operations:
- Quick access to object-specific analyses
- Place-specific analysis options
- Transition-specific analysis options
- Global analysis menu items
- Integration with analysis panels

### `data_collector.py`
**Simulation Data Collection**

Collects and stores simulation data for analysis:
- **Marking History**: Track token counts over time
- **Transition Firings**: Record when transitions fire
- **Event Timeline**: Chronological event log
- **Statistics**: Aggregate statistics (mean, variance, etc.)
- **Export**: Export data for external analysis

**Data Collection:**
```python
collector.record_marking(time, place, tokens)
collector.record_firing(time, transition)
collector.get_marking_history(place) -> List[Tuple[time, tokens]]
collector.get_statistics() -> Dict
```

**Use Cases:**
- Performance analysis
- Bottleneck identification
- Throughput calculation
- Resource utilization

### `diagnostics_panel.py`
**Diagnostics Panel UI**

Main panel for displaying analysis results:
- **Structural Properties**: P-invariants, T-invariants, siphons, traps
- **Behavioral Properties**: Liveness, boundedness, reachability
- **Performance Metrics**: Throughput, cycle time, utilization
- **Visualization**: Charts and graphs of results
- **Export Results**: Save analysis results to file

**Panel Sections:**
1. **Structural Analysis**
   - Place invariants
   - Transition invariants
   - Siphons and traps
   - Structural boundedness

2. **Behavioral Analysis**
   - Liveness classes
   - Boundedness verification
   - Reachability analysis
   - Deadlock detection

3. **Performance Analysis**
   - Throughput rates
   - Cycle times
   - Resource utilization
   - Queue lengths

### `place_rate_panel.py`
**Place Rate Analysis Panel**

Analyzes token flow rates for places:
- **Token Arrival Rate**: Tokens added per time unit
- **Token Departure Rate**: Tokens removed per time unit
- **Average Marking**: Mean number of tokens over time
- **Variance**: Token count variance
- **Visualization**: Time series plots of marking

**Metrics:**
```python
arrival_rate = tokens_added / time_interval
departure_rate = tokens_removed / time_interval
avg_marking = sum(markings) / num_samples
utilization = avg_marking / capacity
```

**Use Cases:**
- Buffer sizing
- Capacity planning
- Bottleneck identification
- Load balancing

### `plot_panel.py`
**Plotting and Visualization**

Creates charts and plots for analysis results:
- **Time Series Plots**: Marking over time
- **Bar Charts**: Transition firing counts
- **Histograms**: Token distribution
- **Gantt Charts**: Event timelines
- **State Space Diagrams**: Reachability graph

**Plot Types:**
- Line plots (marking history)
- Bar charts (firing counts)
- Scatter plots (state space)
- Heat maps (correlation)
- Box plots (statistics)

**Integration:**
- Uses matplotlib for rendering
- Embedded in GTK panels
- Export to PNG, SVG, PDF
- Interactive zoom and pan

### `rate_calculator.py`
**Rate Calculation Engine**

Calculates various rates and metrics:
- **Firing Rates**: Transition firing frequency
- **Flow Rates**: Token flow through arcs
- **Utilization Rates**: Resource usage percentage
- **Throughput**: System output rate
- **Cycle Time**: Time to complete cycle

**Calculations:**
```python
firing_rate = firings / time_interval
throughput = output_tokens / time_interval
utilization = busy_time / total_time
cycle_time = completion_time - start_time
```

### `search_handler.py`
**Analysis Search and Query**

Search functionality for analysis results:
- **Find Places**: Search by name, marking, properties
- **Find Transitions**: Search by type, rate, properties
- **Filter Results**: Filter analysis results by criteria
- **Query Engine**: SQL-like queries on model data

**Search Queries:**
```python
# Find places with high marking
places = search.find_places(lambda p: p.tokens > 10)

# Find enabled transitions
transitions = search.find_transitions(enabled=True)

# Find arcs with high weight
arcs = search.find_arcs(lambda a: a.weight > 5)
```

### `transition_rate_panel.py`
**Transition Rate Analysis Panel**

Analyzes transition firing rates:
- **Firing Frequency**: How often transition fires
- **Enabled Time**: How long transition is enabled
- **Firing Time**: Time taken to fire
- **Utilization**: Percentage of time firing
- **Conflict Analysis**: Conflicts with other transitions

**Metrics:**
```python
firing_frequency = num_firings / time_interval
enabled_ratio = enabled_time / total_time
avg_firing_time = sum(firing_times) / num_firings
conflict_rate = conflicts / num_firings
```

**Use Cases:**
- Process optimization
- Resource allocation
- Conflict resolution
- Throughput improvement

## Structural Analysis

### P-Invariants (Place Invariants)
Linear combinations of place markings that remain constant:
- Identifies conservation laws
- Verifies token conservation
- Detects structural properties

**Example:**
```
For places P1, P2, P3:
If P1 + P2 = constant, then {P1, P2} is a P-invariant
```

### T-Invariants (Transition Invariants)
Firing sequences that return to initial marking:
- Identifies cycles in behavior
- Verifies reproducibility
- Detects repetitive patterns

**Example:**
```
If firing T1, T2, T1 returns to initial state,
then [2, 1] is a T-invariant (T1 fires twice, T2 once)
```

### Siphons
Sets of places that, once empty, remain empty:
- Identifies potential deadlocks
- Verifies liveness properties
- Detects resource starvation

### Traps
Sets of places that, once marked, stay marked:
- Identifies persistent resources
- Verifies safety properties
- Detects accumulation

## Behavioral Analysis

### Liveness
Classification of how transitions can fire:
- **L0 (Dead)**: Never fires
- **L1**: Can fire at least once
- **L2**: Can fire arbitrarily often (from some state)
- **L3**: Can fire arbitrarily often (from any state)
- **L4**: Can fire immediately (live)

### Boundedness
Maximum number of tokens in places:
- **k-bounded**: At most k tokens in any place
- **Safe**: 1-bounded (binary places)
- **Unbounded**: No upper limit

### Reachability
States accessible from initial marking:
- **Reachability Set**: All reachable markings
- **Reachability Graph**: State space diagram
- **Coverability**: Generalized reachability for unbounded nets

### Deadlock Detection
Identify states with no enabled transitions:
- **Total Deadlock**: No transitions enabled
- **Partial Deadlock**: Some transitions never enable
- **Livelock**: Infinite loop without progress

## Performance Analysis

### Throughput Analysis
System output rate:
- Tokens produced per time unit
- Jobs completed per time unit
- Requests served per time unit

### Cycle Time Analysis
Time to complete operations:
- Average cycle time
- Minimum/maximum cycle time
- Cycle time distribution

### Utilization Analysis
Resource usage:
- Place occupancy (tokens/capacity)
- Transition firing (busy/idle time)
- Arc flow (tokens/time)

### Bottleneck Analysis
Identify performance bottlenecks:
- Highest utilization resources
- Longest queues
- Slowest transitions
- Conflict hotspots

## Integration with UI

### Right Panel (Dynamic Analyses)
- Load analysis panel via `right_panel_loader.py`
- Display analysis results
- Interactive visualization
- Export functionality

### Context Menu
- Right-click objects for quick analysis
- "Analyze Place" → Place rate panel
- "Analyze Transition" → Transition rate panel
- "Show Diagnostics" → Diagnostics panel

### Toolbar
- Analysis tools in toolbar
- Quick access to common analyses
- Status indicators for analysis progress

## Import Patterns

```python
from shypn.analyses.data_collector import DataCollector
from shypn.analyses.rate_calculator import RateCalculator
from shypn.analyses.diagnostics_panel import DiagnosticsPanel
from shypn.analyses.place_rate_panel import PlaceRatePanel
from shypn.analyses.transition_rate_panel import TransitionRatePanel
from shypn.analyses.plot_panel import PlotPanel
```

## Future Analysis Features

- **Model Checking**: Temporal logic verification (CTL, LTL)
- **Optimization**: Suggest model improvements
- **Comparison**: Compare different models
- **Sensitivity Analysis**: Parameter variation impact
- **Monte Carlo**: Statistical analysis of stochastic nets
- **What-If Analysis**: Scenario testing
