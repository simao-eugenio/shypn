# Simulation Engine

This directory contains the simulation engine and transition behavior implementations for Petri Net execution.

## Transition Behaviors

### `transition_behavior.py`
**Base Transition Behavior Interface**

Abstract base class for all transition behavior types:
- Defines common interface for transition firing
- Enables/disables transition based on arc conditions
- Manages token consumption and production
- Provides hooks for behavior-specific logic

### `immediate_behavior.py`
**Immediate Transitions**

Zero-delay transitions that fire instantly when enabled:
- **Priority-based**: Higher priority transitions fire first
- **Conflict Resolution**: Handles conflicting transitions
- **Deterministic**: Fires immediately in simulation step
- **Use Cases**: Logical decisions, routing, choice points

**Behavior:**
```python
if enabled and highest_priority:
    consume_input_tokens()
    produce_output_tokens()
```

### `timed_behavior.py`
**Timed Transitions**

Transitions with deterministic delays:
- **Fixed Delay**: Specified time delay before firing
- **Deterministic**: Always fires after exact delay
- **Time Tracking**: Maintains firing schedule
- **Use Cases**: Timeouts, scheduled events, fixed processing times

**Behavior:**
```python
if enabled:
    schedule_firing(current_time + delay)
    # Fire when scheduled time reached
```

### `stochastic_behavior.py`
**Stochastic Transitions**

Transitions with probabilistic firing delays:
- **Exponential Distribution**: Rate parameter λ (lambda)
- **Memoryless Property**: Probability independent of time already waited
- **Random Delays**: Sampling from exponential distribution
- **Use Cases**: Random failures, arrivals, service times

**Behavior:**
```python
if enabled:
    delay = random.exponential(1.0 / rate)
    schedule_firing(current_time + delay)
```

### `continuous_behavior.py`
**Continuous Transitions**

Transitions with continuous firing rates:
- **Rate Functions**: Flow rate as function of markings
- **Differential Equations**: Token flow modeled as ODE
- **Time-driven**: Fires continuously over time
- **Use Cases**: Fluid models, population dynamics, chemical reactions

**Behavior:**
```python
rate = evaluate_rate_function(markings)
token_delta = rate * time_delta
update_markings(token_delta)
```

### `behavior_factory.py`
**Behavior Factory**

Factory for creating transition behavior instances:
- Maps transition types to behavior classes
- Instantiates correct behavior based on type
- Provides centralized behavior creation
- Supports behavior registration and extension

**Usage:**
```python
behavior = BehaviorFactory.create(transition_type, transition)
```

### `function_catalog.py`
**Rate Function Catalog**

Catalog of predefined rate functions for continuous/stochastic transitions:
- **Constant Rate**: Fixed rate
- **Mass Action**: Rate proportional to reactant markings
- **Michaelis-Menten**: Enzyme kinetics
- **Hill Function**: Cooperative binding
- **Custom Functions**: User-defined rate expressions

**Function Format:**
```python
rate = function(marking_dict, parameters)
```

## Simulation Controller

### `simulation/controller.py`
**Simulation Controller**

Main simulation execution engine:
- **Event Scheduling**: Priority queue for timed events
- **State Management**: Current marking, simulation time, event queue
- **Step Execution**: Single-step and continuous simulation
- **Conflict Resolution**: Handles conflicting transitions
- **Statistics Collection**: Transition firing counts, marking history
- **Reset Functionality**: Return to initial marking

**Simulation Modes:**
1. **Step Mode**: Execute one transition firing
2. **Run Mode**: Continuous execution until stopped
3. **Time-driven**: Advance simulation clock
4. **Event-driven**: Execute next scheduled event

**Key Methods:**
```python
controller.step()           # Execute one step
controller.run()            # Run until stopped
controller.stop()           # Stop simulation
controller.reset()          # Reset to initial marking
controller.get_statistics() # Get simulation stats
```

### `simulation/conflict_policy.py`
**Conflict Resolution Policies**

Strategies for resolving conflicting transitions:
- **Priority-based**: Highest priority fires first
- **Random Selection**: Random choice among conflicts
- **Age-based**: Oldest enabled transition fires first
- **User-defined**: Custom conflict resolution

**Conflict Scenarios:**
- Multiple immediate transitions enabled
- Insufficient tokens for all enabled transitions
- Transitions competing for same resources

## Simulation Algorithm

### Initialization
```python
1. Load Petri Net model
2. Set initial markings (from places)
3. Initialize event queue
4. Create behavior instances for transitions
```

### Step Execution
```python
1. Check enabled transitions
2. Apply conflict resolution if needed
3. Select transition to fire
4. Consume input tokens (via arcs)
5. Execute behavior-specific logic
6. Produce output tokens (via arcs)
7. Update simulation time
8. Schedule future events (for timed/stochastic)
9. Update statistics
```

### Reset
```python
1. Restore all places to initial_marking
2. Clear event queue
3. Reset simulation time to 0
4. Clear statistics
```

## Integration with Petri Net Objects

### Arc Weight Evaluation
```python
# Normal arc
tokens_consumed = arc.weight
tokens_produced = arc.weight

# Inhibitor arc
if place.tokens >= arc.weight:
    transition.enabled = False
```

### Token Operations
```python
# Consume tokens
place.set_tokens(place.tokens - arc.weight)

# Produce tokens
place.set_tokens(place.tokens + arc.weight)

# Check capacity
if place.capacity and tokens > place.capacity:
    raise CapacityExceeded()
```

## Use Cases

### Manufacturing Systems
- Jobs (tokens in places)
- Machines (transitions)
- Processing times (timed transitions)
- Failures (stochastic transitions)

### Communication Protocols
- Messages (tokens)
- Protocol states (places)
- Timeouts (timed transitions)
- Message loss (stochastic transitions)

### Biological Systems
- Molecules (tokens)
- Reactions (transitions)
- Reaction rates (continuous transitions)
- Catalysis (rate functions)

## Import Patterns

```python
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.immediate_behavior import ImmediateBehavior
from shypn.engine.timed_behavior import TimedBehavior
from shypn.engine.stochastic_behavior import StochasticBehavior
from shypn.engine.continuous_behavior import ContinuousBehavior
from shypn.engine.behavior_factory import BehaviorFactory
from shypn.engine.function_catalog import FunctionCatalog
```

## Performance Considerations

- **Event Queue**: Efficient priority queue for timed events
- **Enabled Transition Caching**: Cache enabled transitions
- **Incremental Updates**: Update only affected transitions
- **Sparse Marking Representation**: For large nets with few tokens
- **Conflict Set Optimization**: Fast conflict detection

## Debugging and Validation

- **Trace Generation**: Log all transition firings
- **Marking History**: Track marking evolution
- **Deadlock Detection**: Identify states with no enabled transitions
- **Liveness Analysis**: Check if transitions can fire
- **Boundedness Checking**: Verify token limits not exceeded
