# Transition Engine Architecture - Visual Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TRANSITION ENGINE ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         LEGACY CODE ANALYSIS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  legacy/shypnpy/core/petri.py (2600 lines)                          │
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐                     │
│  │ _fire_immediate_   │  │ _fire_tpn_timed_  │                     │
│  │   transition()     │  │   transition()     │                     │
│  │  Lines 1908-1970   │  │  Lines 1971-2050+  │                     │
│  │                    │  │                    │                     │
│  │ • Zero delay       │  │ • TPN timing      │                     │
│  │ • Discrete tokens  │  │ • [earliest,      │                     │
│  │ • arc_weight units │  │   latest]         │                     │
│  └────────────────────┘  └────────────────────┘                     │
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐                     │
│  │ _fire_fspn_       │  │ _fire_shpn_       │                     │
│  │   stochastic_     │  │   continuous_     │                     │
│  │   transition()    │  │   transition()    │                     │
│  │  Lines 1562-1690  │  │  Lines 1691-1900  │                     │
│  │                   │  │                   │                     │
│  │ • Exponential λ   │  │ • Rate function   │                     │
│  │ • Burst firing    │  │ • RK4 integration │                     │
│  │ • 1x-8x arc_weight│  │ • dm/dt = R(m,t) │                     │
│  └────────────────────┘  └────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘

                              │
                              │ EXTRACT & REFACTOR
                              ▼

┌─────────────────────────────────────────────────────────────────────┐
│                      NEW ENGINE ARCHITECTURE                         │
│                      src/shypn/engine/                               │
└─────────────────────────────────────────────────────────────────────┘

                  ┌──────────────────────────────┐
                  │  TransitionBehavior (ABC)    │
                  │  transition_behavior.py      │
                  ├──────────────────────────────┤
                  │ + transition: Transition     │
                  │ + model: PetriNetModel       │
                  ├──────────────────────────────┤
                  │ + can_fire() → (bool, str)   │
                  │ + fire(arcs) → (bool, dict)  │
                  │ + get_type_name() → str      │
                  │ # is_enabled() → bool        │
                  │ # get_input_arcs() → List    │
                  │ # get_output_arcs() → List   │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
    ┌────────────▼──────────┐      ┌────────────▼──────────┐
    │  ImmediateBehavior    │      │   TimedBehavior       │
    │  immediate_behavior.py│      │   timed_behavior.py   │
    ├───────────────────────┤      ├───────────────────────┤
    │ Discrete firing       │      │ TPN semantics         │
    │ Zero delay            │      │ [earliest, latest]    │
    │ arc_weight tokens     │      │ Enablement tracking   │
    └───────────────────────┘      └───────────────────────┘
                 │                               │
    ┌────────────▼──────────┐      ┌────────────▼──────────┐
    │ StochasticBehavior    │      │ ContinuousBehavior    │
    │ stochastic_behavior.py│      │ continuous_behavior.py│
    ├───────────────────────┤      ├───────────────────────┤
    │ Exponential sampling  │      │ Rate function R(m,t)  │
    │ Burst calculation     │      │ RK4 integration       │
    │ 1x-8x arc_weight      │      │ Safe math eval        │
    └───────────────────────┘      └───────────────────────┘

                  ┌──────────────────────────────┐
                  │     BehaviorFactory          │
                  │     behavior_factory.py      │
                  ├──────────────────────────────┤
                  │ create_behavior(transition,  │
                  │                 model)       │
                  │   → TransitionBehavior       │
                  │                              │
                  │ Type mapping:                │
                  │ 'immediate' → Immediate      │
                  │ 'timed'     → Timed          │
                  │ 'stochastic'→ Stochastic     │
                  │ 'continuous'→ Continuous     │
                  └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          USAGE PATTERN                               │
└─────────────────────────────────────────────────────────────────────┘

    from shypn.engine import create_behavior

    # Get transition
    transition = model.transitions[transition_id]
    
    # Create appropriate behavior (factory pattern)
    behavior = create_behavior(transition, model)
    
    # Check if can fire
    can_fire, reason = behavior.can_fire()
    
    if can_fire:
        # Fire the transition
        success, details = behavior.fire(
            input_arcs=behavior.get_input_arcs(),
            output_arcs=behavior.get_output_arcs()
        )

┌─────────────────────────────────────────────────────────────────────┐
│                      IMPLEMENTATION PHASES                           │
└─────────────────────────────────────────────────────────────────────┘

Phase 1: Infrastructure (30 min)
  ├─ Create src/shypn/engine/
  ├─ Base class: TransitionBehavior
  └─ Factory skeleton

Phase 2: ImmediateBehavior (45 min)
  ├─ Extract from lines 1908-1970
  └─ Discrete token firing

Phase 3: TimedBehavior (60 min)
  ├─ Extract from lines 1971-2050+
  ├─ TPN timing windows
  └─ Enablement tracking

Phase 4: StochasticBehavior (60 min)
  ├─ Extract from lines 1562-1690
  ├─ Exponential sampling
  └─ Burst firing logic

Phase 5: ContinuousBehavior (90 min)
  ├─ Extract from lines 1691-1900
  ├─ Rate function evaluation
  └─ RK4 integration

Phase 6: Factory (30 min)
  └─ Type → Behavior mapping

Phase 7: Testing (60 min)
  └─ Unit tests for each type

Phase 8: Integration (30 min)
  └─ Connect to UI/model

Phase 9: Documentation (30 min)
  └─ Usage guides

TOTAL: 7 hours

┌─────────────────────────────────────────────────────────────────────┐
│                            BENEFITS                                  │
└─────────────────────────────────────────────────────────────────────┘

✓ Separation of Concerns    Each type has its own class
✓ Extensibility             Easy to add new types
✓ Testability              Isolated unit testing
✓ Maintainability          Clear, focused code
✓ Type Safety              Abstract interface contract
✓ Code Reuse               Common logic in base class

┌─────────────────────────────────────────────────────────────────────┐
│                       TRANSITION ATTRIBUTES                          │
└─────────────────────────────────────────────────────────────────────┘

All Types:
  • transition_type: str ('immediate', 'timed', 'stochastic', 'continuous')
  • id: int
  • name: str
  • enabled: bool

Timed Only:
  • earliest_time: float
  • latest_time: float
  • enablement_time: float
  • timed_enabled: bool

Stochastic Only:
  • rate_parameter: float (λ)
  • stochastic_enabled: bool

Continuous Only:
  • rate_function: str ("1.0", "P1 * 0.5", etc.)
  • time_step: float (default 0.1)
  • max_flow_time: float
  • continuous_enabled: bool
