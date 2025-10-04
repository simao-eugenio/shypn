# Transition Types Engine Architecture Plan

## Executive Summary

Create a clean OOP structure for transition firing behaviors under `src/shypn/engine/` to replace the monolithic legacy firing logic. This will separate concerns, improve maintainability, and enable easier extension for new transition types.

---

## 1. Legacy Code Analysis

### 1.1 Identified Transition Types

From analysis of `legacy/shypnpy/core/petri.py` and test files:

| Type | Description | Key Characteristics |
|------|-------------|---------------------|
| **Immediate** | Fire instantly if enabled | Zero time delay, discrete tokens (arc_weight units) |
| **Timed** | TPN-compliant timed transitions | Timing intervals [earliest, latest], discrete firing |
| **Stochastic** | FSPN probabilistic transitions | Exponential distribution, burst firing (1x-8x arc_weight) |
| **Continuous** | SHPN continuous flow | Rate functions, RK4 integration, dm/dt = R(m,t) |

### 1.2 Key Legacy Methods Found

**Location**: `legacy/shypnpy/core/petri.py`

- `_fire_immediate_transition()` - Lines 1908-1970
- `_fire_tpn_timed_transition()` - Lines 1971-2050+
- `_fire_fspn_stochastic_transition()` - Lines 1562-1690
- `_fire_shpn_continuous_transition()` - Lines 1691-1900

### 1.3 Transition Attributes (from legacy)

```python
# Base attributes (all types)
transition.id                    # int
transition.name                  # str
transition.transition_type       # str: 'immediate', 'timed', 'stochastic', 'continuous'
transition.enabled               # bool

# Type-specific enable flags
transition.timed_enabled         # bool
transition.stochastic_enabled    # bool  
transition.continuous_enabled    # bool

# Timed transition attributes
transition.earliest_time         # float (TPN timing window start)
transition.latest_time           # float (TPN timing window end)
transition.enablement_time       # float (when transition became enabled)
transition.timed_enabled         # bool

# Stochastic transition attributes
transition.rate_parameter        # float (λ for exponential distribution)
transition.stochastic_enabled    # bool

# Continuous transition attributes
transition.rate_function         # str (mathematical expression: "1.0", "P1 * 0.5", etc.)
transition.time_step             # float (integration dt, default 0.1)
transition.max_flow_time         # float (max continuous flow duration)
transition.continuous_enabled    # bool
```

---

## 2. Proposed Architecture

### 2.1 Directory Structure

```
src/shypn/engine/
├── __init__.py
├── transition_behavior.py          # Abstract base class
├── immediate_behavior.py           # Immediate firing logic
├── timed_behavior.py               # TPN timed firing logic
├── stochastic_behavior.py          # FSPN stochastic firing logic
├── continuous_behavior.py          # SHPN continuous firing logic
└── behavior_factory.py             # Factory to create appropriate behavior
```

### 2.2 Class Hierarchy

```
TransitionBehavior (ABC)
    ├── ImmediateBehavior
    ├── TimedBehavior
    ├── StochasticBehavior
    └── ContinuousBehavior
```

### 2.3 Base Class Interface

```python
# src/shypn/engine/transition_behavior.py

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Any

class TransitionBehavior(ABC):
    """Abstract base class for transition firing behaviors.
    
    Each transition type (immediate, timed, stochastic, continuous) 
    implements its own firing semantics by subclassing this.
    """
    
    def __init__(self, transition, model):
        """Initialize behavior with transition and model context.
        
        Args:
            transition: Transition object (from netobjs)
            model: PetriNetModel instance (for accessing places, arcs, time)
        """
        self.transition = transition
        self.model = model
    
    @abstractmethod
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire according to type-specific rules.
        
        Returns:
            (can_fire: bool, reason: str)
        """
        pass
    
    @abstractmethod
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict]:
        """Execute firing logic for this transition type.
        
        Args:
            input_arcs: List of incoming arcs
            output_arcs: List of outgoing arcs
        
        Returns:
            (success: bool, details: dict)
        """
        pass
    
    @abstractmethod
    def get_type_name(self) -> str:
        """Return human-readable type name."""
        pass
    
    # Common utility methods
    def is_enabled(self) -> bool:
        """Check basic structural enablement (enough tokens)."""
        return self.model.is_transition_enabled_logical(self.transition.id)
    
    def get_input_arcs(self) -> List:
        """Get all input arcs to this transition."""
        return [arc for arc in self.model.arcs.values() 
                if arc.target_id == self.transition.id]
    
    def get_output_arcs(self) -> List:
        """Get all output arcs from this transition."""
        return [arc for arc in self.model.arcs.values() 
                if arc.source_id == self.transition.id]
```

---

## 3. Implementation Plan

### Phase 1: Setup Infrastructure (30 minutes)

**Tasks:**
1. ✅ Analyze legacy code (DONE)
2. Create `src/shypn/engine/` directory
3. Create `__init__.py` with exports
4. Create `transition_behavior.py` with base class
5. Create `behavior_factory.py` skeleton

**Files to create:**
- `src/shypn/engine/__init__.py`
- `src/shypn/engine/transition_behavior.py`
- `src/shypn/engine/behavior_factory.py`

### Phase 2: Implement ImmediateBehavior (45 minutes)

**Source**: `legacy/shypnpy/core/petri.py:1908-1970`

**Logic to extract:**
- Check sufficient tokens for all input arcs
- Consume exactly `arc.weight` tokens from each input place
- Produce exactly `arc.weight` tokens to each output place
- Record firing event
- Zero time delay

**File to create:**
- `src/shypn/engine/immediate_behavior.py`

**Key methods:**
```python
class ImmediateBehavior(TransitionBehavior):
    def can_fire(self) -> Tuple[bool, str]:
        """Immediate fires if enabled (enough tokens)."""
        
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        """Execute immediate discrete firing."""
```

### Phase 3: Implement TimedBehavior (60 minutes)

**Source**: `legacy/shypnpy/core/petri.py:1971-2050+`

**Logic to extract:**
- TPN timing window management [earliest_time, latest_time]
- Enablement tracking (when did transition become enabled)
- Check if current time is within firing window
- Discrete token consumption/production (like immediate)
- Update enablement status after firing

**File to create:**
- `src/shypn/engine/timed_behavior.py`

**Key methods:**
```python
class TimedBehavior(TransitionBehavior):
    def can_fire(self) -> Tuple[bool, str]:
        """Check enablement + timing window."""
        
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        """Execute timed discrete firing with TPN semantics."""
        
    def is_within_timing_window(self) -> Tuple[bool, bool, str]:
        """Check [earliest, latest] constraints."""
        
    def update_enablement_tracking(self):
        """Update enablement time when status changes."""
```

### Phase 4: Implement StochasticBehavior (60 minutes)

**Source**: `legacy/shypnpy/core/petri.py:1562-1690`

**Logic to extract:**
- Exponential distribution sampling for holding time
- Burst size calculation (1x to 8x arc_weight based on holding time)
- Check maximum possible bursts given available tokens
- Iterative burst firing (multiple arc_weight units)
- Balance constraint: consumed = produced

**File to create:**
- `src/shypn/engine/stochastic_behavior.py`

**Key methods:**
```python
class StochasticBehavior(TransitionBehavior):
    def can_fire(self) -> Tuple[bool, str]:
        """Check if any tokens available for burst."""
        
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        """Execute stochastic burst firing."""
        
    def sample_holding_time(self) -> float:
        """Sample from exponential distribution."""
        
    def calculate_burst_size(self, holding_time: float) -> int:
        """Convert holding time to burst multiplier."""
```

### Phase 5: Implement ContinuousBehavior (90 minutes)

**Source**: `legacy/shypnpy/core/petri.py:1691-1900`

**Logic to extract:**
- Rate function evaluation (mathematical expression parser)
- RK4 (Runge-Kutta 4th order) numerical integration
- Variable mapping (place tokens → P1, P2, ..., time → t)
- Safe evaluation environment (math, numpy functions)
- Integration loop with time stepping
- Flow amount calculation and token updates

**File to create:**
- `src/shypn/engine/continuous_behavior.py`

**Key methods:**
```python
class ContinuousBehavior(TransitionBehavior):
    def can_fire(self) -> Tuple[bool, str]:
        """Check if enabled and rate > 0."""
        
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        """Execute continuous flow with RK4 integration."""
        
    def evaluate_rate_function(self, marking: Dict, time: float) -> float:
        """Evaluate rate function R(m,t) at current state."""
        
    def rk4_step(self, marking: Dict, time: float, dt: float) -> float:
        """Single RK4 integration step for dm/dt = R(m,t)."""
```

### Phase 6: Implement BehaviorFactory (30 minutes)

**Purpose**: Create appropriate behavior instance based on transition type

**File to create:**
- `src/shypn/engine/behavior_factory.py`

**Key method:**
```python
def create_behavior(transition, model) -> TransitionBehavior:
    """Factory method to create appropriate behavior.
    
    Args:
        transition: Transition object
        model: PetriNetModel instance
        
    Returns:
        Appropriate TransitionBehavior subclass instance
        
    Raises:
        ValueError: If transition_type is unknown
    """
    type_map = {
        'immediate': ImmediateBehavior,
        'timed': TimedBehavior,
        'stochastic': StochasticBehavior,
        'continuous': ContinuousBehavior
    }
    
    transition_type = getattr(transition, 'transition_type', 'immediate')
    behavior_class = type_map.get(transition_type)
    
    if behavior_class is None:
        raise ValueError(f"Unknown transition type: {transition_type}")
    
    return behavior_class(transition, model)
```

### Phase 7: Testing (60 minutes)

**Test files to create:**
- `tests/test_immediate_behavior.py`
- `tests/test_timed_behavior.py`
- `tests/test_stochastic_behavior.py`
- `tests/test_continuous_behavior.py`
- `tests/test_behavior_factory.py`

**Test scenarios:**
1. Each behavior type in isolation
2. Behavior switching (same transition, different types)
3. Edge cases (no tokens, invalid rate functions, etc.)
4. Integration with existing model/canvas

### Phase 8: Integration (30 minutes)

**Tasks:**
1. Update `src/shypn/netobjs/transition.py` to support type attributes
2. Add `transition_type` property with validation
3. Add type-specific properties (rate_parameter, rate_function, etc.)
4. Update transition property dialogs to use new behaviors
5. Update documentation

### Phase 9: Documentation (30 minutes)

**Documents to create:**
- `doc/ENGINE_ARCHITECTURE.md` - Overview and usage guide
- `doc/TRANSITION_TYPES_REFERENCE.md` - Detailed type specifications
- Update `doc/API_FLATTENING_PLAN.md` to include engine

---

## 4. Code Extraction Strategy

### 4.1 Immediate Behavior Extraction

**From**: `legacy/shypnpy/core/petri.py:1908-1970`

**Extract:**
1. Token sufficiency check loop
2. Token consumption loop (subtract arc.weight)
3. Token production loop (add arc.weight)
4. Event recording
5. Success/failure return logic

**Cleanup:**
- Remove global scheduler dependencies
- Remove model-specific logging
- Make pure function (inputs → outputs)

### 4.2 Timed Behavior Extraction

**From**: `legacy/shypnpy/core/petri.py:1971-2050+`

**Extract:**
1. TPN enablement status update
2. Timing window validation
3. Token firing logic (same as immediate)
4. Enablement time tracking

**Cleanup:**
- Separate timing logic from firing logic
- Remove legacy timed transition references
- Use only TPN semantics

### 4.3 Stochastic Behavior Extraction

**From**: `legacy/shypnpy/core/petri.py:1562-1690`

**Extract:**
1. Exponential sampling algorithm
2. Burst size calculation logic
3. Maximum burst validation
4. Iterative burst firing loop
5. Balance verification

**Cleanup:**
- Separate distribution sampling from firing
- Make burst calculation configurable
- Remove commented-out alternative strategies

### 4.4 Continuous Behavior Extraction

**From**: `legacy/shypnpy/core/petri.py:1691-1900`

**Extract:**
1. Safe evaluation environment setup
2. Variable context building (P1, P2, t)
3. RK4 integration algorithm
4. Rate function evaluation
5. Flow amount accumulation

**Cleanup:**
- Separate rate evaluation from integration
- Make integration method configurable (RK4, Euler, etc.)
- Add error handling for invalid rate functions

---

## 5. Dependencies & Imports

### Required External Modules

```python
# Standard library
import math
import random
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional, Any

# Third-party (for continuous transitions)
import numpy as np  # For advanced math in rate functions
```

### Internal Dependencies

```python
# From shypn
from shypn.netobjs import Transition, Place, Arc
# Model will be passed as parameter, not imported directly
```

---

## 6. Usage Example (After Implementation)

```python
from shypn.engine import create_behavior

# Given a transition and model
transition = model.transitions[transition_id]

# Create appropriate behavior
behavior = create_behavior(transition, model)

# Check if can fire
can_fire, reason = behavior.can_fire()
if can_fire:
    # Execute firing
    success, details = behavior.fire(
        input_arcs=behavior.get_input_arcs(),
        output_arcs=behavior.get_output_arcs()
    )
    
    if success:
        print(f"Fired {behavior.get_type_name()}: {details}")
    else:
        print(f"Failed: {details.get('reason')}")
else:
    print(f"Cannot fire: {reason}")
```

---

## 7. Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Infrastructure | 30 min | None |
| Phase 2: Immediate | 45 min | Phase 1 |
| Phase 3: Timed | 60 min | Phase 1, 2 |
| Phase 4: Stochastic | 60 min | Phase 1, 2 |
| Phase 5: Continuous | 90 min | Phase 1, 2 |
| Phase 6: Factory | 30 min | Phase 1-5 |
| Phase 7: Testing | 60 min | Phase 1-6 |
| Phase 8: Integration | 30 min | Phase 1-7 |
| Phase 9: Documentation | 30 min | Phase 1-8 |
| **Total** | **7 hours** | |

---

## 8. Benefits of This Architecture

### 8.1 Separation of Concerns
- Each transition type has its own class
- No more monolithic `fire_transition()` with huge if-else chains
- Easy to understand and maintain

### 8.2 Extensibility
- Adding new transition types: just create new behavior subclass
- No need to modify existing code
- Open/Closed Principle compliance

### 8.3 Testability
- Each behavior can be tested in isolation
- Mock model easily for unit tests
- Clear interfaces make testing straightforward

### 8.4 Code Reuse
- Common logic in base class
- Type-specific logic in subclasses
- Factory pattern for clean instantiation

### 8.5 Type Safety
- Abstract methods enforce interface contract
- IDE autocomplete and type checking
- Clear documentation through method signatures

---

## 9. Migration Strategy

### 9.1 Phase 1: Parallel Implementation
- Keep legacy firing logic intact
- Implement new engine alongside
- Add feature flag to switch between old/new

### 9.2 Phase 2: Testing & Validation
- Run both implementations side-by-side
- Compare results for correctness
- Fix any discrepancies

### 9.3 Phase 3: Gradual Migration
- Migrate one transition type at a time
- Start with immediate (simplest)
- End with continuous (most complex)

### 9.4 Phase 4: Legacy Removal
- Remove old firing methods
- Clean up monolithic code
- Update all references

---

## 10. Success Criteria

✅ **All 4 transition types implemented**
✅ **Tests passing with >90% coverage**
✅ **No regressions in existing functionality**
✅ **Performance equal or better than legacy**
✅ **Documentation complete and clear**
✅ **Code review approved**
✅ **Integration with UI working**

---

## 11. Next Steps

1. **Review this plan** - Confirm architecture approach
2. **Start Phase 1** - Create directory structure and base class
3. **Iterate through phases** - Implement each behavior type
4. **Test continuously** - Don't wait until the end
5. **Document as you go** - Keep docs in sync with code

---

## Appendix A: Legacy Code References

### Key Legacy Files
- `legacy/shypnpy/core/petri.py` - Main firing logic (2600 lines)
- `legacy/shypnpy/interface/dialogs.py` - Transition type UI
- `legacy/shypnpy/test_on_new_scenario.py` - Type switching tests
- `legacy/shypnpy/analyze_scheduler_independence.py` - Scheduler analysis

### Key Legacy Concepts
- **TPN** (Time Petri Net) - Merlin & Farber 1976
- **FSPN** (Fluid Stochastic Petri Net) - Burst firing
- **SHPN** (Stochastic Hybrid Petri Net) - Continuous flow
- **RK4** (Runge-Kutta 4th order) - Numerical integration

---

**Document Created**: October 3, 2025
**Status**: Ready for implementation
**Estimated Completion**: 7 hours of focused work
