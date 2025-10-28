# Firing Policies for Transitions

## Overview

Firing policies determine how transitions compete and resolve conflicts when multiple transitions are enabled simultaneously. These policies are distinct from **behaviors** (kinetics), which are handled through rate functions and threshold values using mathematical expressions.

---

## Current Implementation

**Existing Policies:**
- `earliest` - Fire at earliest possible time in [earliest, latest] window
- `latest` - Fire at latest possible time in [earliest, latest] window

---

## Expanded Firing Policies (Biological/Biochemical Focus)

### 1. **earliest** (EXISTING)
- **Description**: Fire at the earliest time in the [earliest, latest] timing window
- **Use Case**: Deterministic minimum delay behavior
- **Application**: Immediate responses, fastest pathways
- **Implementation**: Uses `earliest` parameter from transition timing window

### 2. **latest** (EXISTING)
- **Description**: Fire at the latest time in the [earliest, latest] timing window
- **Use Case**: Deterministic maximum delay behavior
- **Application**: Delayed responses, waiting for optimal conditions
- **Implementation**: Uses `latest` parameter from transition timing window

### 3. **priority** (NEW)
- **Description**: Use transition's priority value to resolve conflicts
- **Behavior**: Higher priority transitions block lower priority transitions
- **Use Case**: Hierarchical biological processes
- **Application**: 
  - Gene regulatory hierarchies
  - DNA repair > replication
  - Survival pathways > growth pathways
  - Emergency responses > routine processes
- **Implementation**: Compare `transition.priority` values; highest priority fires first

### 4. **race** (NEW - Mass Action Kinetics)
- **Description**: All enabled transitions compete stochastically
- **Behavior**: Transitions "race" with exponentially distributed delays; fastest wins
- **Use Case**: Competitive molecular interactions
- **Application**:
  - Enzyme-substrate competitions
  - Metabolic pathway branch points
  - Concurrent biochemical reactions
  - Multiple binding sites competing
- **Implementation**: Sample exponential delays for all enabled; minimum delay wins

### 5. **age** (NEW - FIFO)
- **Description**: First In First Out - transition enabled longest fires first
- **Behavior**: Fair scheduling based on enablement timestamp
- **Use Case**: Queue management, fair resource allocation
- **Application**:
  - Resource contention resolution
  - Sequential processing
  - Cell cycle progression fairness
- **Implementation**: Track enablement time; oldest enabled transition fires

### 6. **random** (NEW)
- **Description**: Uniform random selection among enabled transitions
- **Behavior**: Non-deterministic choice with equal probability
- **Use Case**: Unbiased exploration of alternatives
- **Application**:
  - Simple conflict resolution
  - Exploratory modeling
  - Testing non-deterministic scenarios
- **Implementation**: `random.choice(enabled_transitions)`

### 7. **preemptive-priority** (NEW)
- **Description**: High priority transitions can interrupt low priority in progress
- **Behavior**: Running low-priority transition stopped if high-priority becomes enabled
- **Use Case**: Critical interrupt mechanisms
- **Application**:
  - Emergency cellular responses
  - Stress response pathways interrupting normal metabolism
  - Apoptosis signals interrupting growth
  - DNA damage response preempting replication
- **Implementation**: Check running transitions; preempt if higher priority enabled

---

## Policy Selection Guidelines

### For Biological Systems:

| System Type | Recommended Policy | Rationale |
|-------------|-------------------|-----------|
| Metabolic pathways | `race` | Competitive enzyme kinetics |
| Gene regulation | `priority` | Hierarchical control |
| Cell cycle | `age` | Sequential progression |
| Stress response | `preemptive-priority` | Emergency override |
| Stochastic expression | `random` | Inherent noise |
| Signal transduction | `earliest` | Rapid propagation |

---

## Implementation Details

### Code Locations:

1. **Policy Definition:**
   - File: `src/shypn/netobjs/transition.py`
   - Property: `transition.firing_policy`
   - Default: `'earliest'`

2. **UI Mapping:**
   - File: `src/shypn/helpers/transition_prop_dialog_loader.py`
   - Loading: Line ~150 (`policy_map`)
   - Saving: Line ~323 (`policy_list`)

3. **Policy Execution:**
   - File: `src/shypn/engine/simulation/controller.py`
   - Method: `_select_transition(enabled_transitions)`
   - Logic: Implements policy-specific selection algorithm

### Policy List Arrays:

```python
# Loading (policy string → combo index)
policy_map = {
    'earliest': 0,
    'latest': 1,
    'priority': 2,
    'race': 3,
    'age': 4,
    'random': 5,
    'preemptive-priority': 6
}

# Saving (combo index → policy string)
policy_list = [
    'earliest',              # Index 0
    'latest',                # Index 1
    'priority',              # Index 2
    'race',                  # Index 3
    'age',                   # Index 4
    'random',                # Index 5
    'preemptive-priority'    # Index 6
]
```

---

## Distinction: Policies vs. Behaviors

### **Policies** (Conflict Resolution)
- **Purpose**: Decide WHICH transition fires when multiple are enabled
- **Mechanism**: Selection algorithm
- **Examples**: priority, race, age, random
- **Implementation**: Firing policy combo box

### **Behaviors** (Kinetics)
- **Purpose**: Define HOW transition fires (rate, dynamics)
- **Mechanism**: Mathematical rate functions
- **Examples**: Mass action, Michaelis-Menten, Hill, inhibition
- **Implementation**: Rate functions with `eval()` and numpy support

**Example:**
- **Behavior**: "This enzyme follows Michaelis-Menten kinetics with Vmax=5, Km=0.1"
  - Implemented via: Rate function `rate = (5 * [S]) / (0.1 + [S])`
- **Policy**: "When this enzyme competes with another, use priority=10"
  - Implemented via: Firing policy = `priority`, priority value = 10

---

## Future Enhancements

Potential additional policies (not yet implemented):

1. **Weighted Random**: Probability proportional to rates
2. **Memory-based**: History-dependent selection
3. **Spatial**: Distance-based priority
4. **Resource-aware**: Based on available resources (ATP, enzymes)

---

## References

- **Petri Net Theory**: Peterson (1981) - Petri Net Theory and the Modeling of Systems
- **Stochastic Petri Nets**: Marsan et al. - Generalized Stochastic Petri Nets (GSPN)
- **Priority Semantics**: Wikipedia - Prioritized Petri Nets
- **Biological Modeling**: Koch et al. (2011) - Modeling in Systems Biology: The Petri Net Approach

---

## Document History

- **Created**: 2025-10-27
- **Purpose**: Define firing policy semantics for biological/biochemical Petri net modeling
- **Status**: Specification for implementation
