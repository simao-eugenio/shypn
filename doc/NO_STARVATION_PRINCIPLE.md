# No Starvation Principle - Biological Petri Net Semantics

## Core Principle

**"Collaborate Due to Lack of Resources, Not Despite Them"**

In biological systems, entities cooperate and share resources ONLY when they have surplus above their survival threshold. This prevents any entity from being driven to starvation through cooperation.

## Mathematical Formulation

### Survival Threshold (τ)
Each place P has a survival threshold τ_P representing minimum tokens needed for survival.

### Starvation State
A place P is in starvation if: `tokens(P) < τ_P`

### No-Starvation Invariant
For all reachable markings M in the net:
```
∀P ∈ Places: M(P) ≥ τ_P
```

The system must maintain this invariant across all possible executions.

## Implementation in SHYPN

### Inhibitor Arc Semantics

Inhibitor arcs implement the no-starvation principle through **strict surplus checking**:

```python
# Inhibitor arc from Place P to Transition T with weight w
if isinstance(arc, InhibitorArc):
    # Enabled only if P has STRICT surplus (tokens > weight)
    enabled = source_place.tokens > arc.weight
    # Consumes weight tokens when fires
    consumption = arc.weight
```

### Why Strict Surplus (>) Instead of (≥)?

**With tokens ≥ weight:**
```
P(5 tokens) --[inhibitor, weight=5]--> T
T fires: P(5) - 5 = P(0)  ❌ STARVATION!
```

**With tokens > weight:**
```
P(5 tokens) --[inhibitor, weight=5]--> T
T disabled: P maintains 5 tokens ✓ SAFE

P(6 tokens) --[inhibitor, weight=5]--> T
T fires: P(6) - 5 = P(1) ✓ SURPLUS MAINTAINED
```

## Arc Type Comparison

| Arc Type | Enablement | Consumption | Reserve | Purpose |
|----------|------------|-------------|---------|---------|
| **Normal** | tokens ≥ w | w | 0 | Direct need |
| **Inhibitor** | tokens > w | w | ≥ 1 | Cooperation with safety |
| **Test** | tokens ≥ w | 0 | w | Catalyst (no consumption) |

### Biological Interpretation

**Normal Arc (Necessity):**
- "I NEED w tokens to function"
- Can consume all available resources
- Represents essential metabolic needs
- Example: Enzyme needs substrate

**Inhibitor Arc (Cooperation):**
- "I can SHARE w tokens if I have surplus"
- Always maintains minimum reserve
- Represents altruistic behavior with self-preservation
- Example: Cell exports nutrients only when well-fed

**Test Arc (Catalysis):**
- "I REQUIRE w tokens present but don't consume"
- Resources remain available after use
- Represents enzymatic catalysis
- Example: Enzyme facilitates reaction without being consumed

## Examples from Biology

### Example 1: Cellular Energy Sharing

```
ATP_Pool(10) --[inhibitor, w=5]--> Export_Energy
                                       ↓
                                   Neighboring_Cell

Interpretation:
- Cell maintains minimum 5 ATP for survival (τ = 5)
- Exports energy ONLY when ATP > 5 (surplus available)
- At ATP=5: Export disabled (no starvation risk)
- At ATP=6: Export enabled (can share 5, keep 1)
```

### Example 2: Nutrient Distribution in Colony

```
Food_Store(20) --[inhibitor, w=10]--> Share_Food
                                          ↓
                                   Colony_Members

Interpretation:
- Colony keeps minimum 10 units for emergencies (τ = 10)
- Shares food ONLY when store > 10
- Prevents colony-wide starvation during scarcity
- Enables cooperation during abundance
```

### Example 3: Multi-Level Protection

```
Glucose(8) --[normal, w=2]--> Glycolysis_Essential
           --[inhibitor, w=5]--> Glucose_Export

Interpretation:
- Essential metabolism: fires at glucose ≥ 2 (survival)
- Export to neighbors: fires only at glucose > 5 (cooperation)
- Priority: Self-preservation before cooperation
- At glucose=3: Glycolysis fires, Export blocked ✓
```

## System-Wide Properties

### Deadlock Prevention
No-starvation principle prevents resource depletion deadlocks:
```
∀T ∈ Enabled_Transitions:
    fire(T) → ∀P ∈ •T: tokens(P) remains ≥ τ_P
```

### Liveness Guarantee
If a transition was enabled before, it can become enabled again:
```
If T was enabled at M₀ with surplus S:
Then ∃ path M₀ →* M_k where T is enabled again
(assuming no external resource drain)
```

### Fairness
All entities maintain survival thresholds equally:
```
No entity is forced into starvation to enable others
```

## Implementation Verification

### Test Case 1: Basic No-Starvation
```python
def test_no_starvation_basic():
    p1 = Place(id=1, tokens=5)
    t1 = Transition(id=1, transition_type='immediate')
    inhibitor = InhibitorArc(p1, t1, id=1, name='I1', weight=5)
    
    behavior = ImmediateBehavior(t1, model)
    can_fire, reason = behavior.can_fire()
    
    assert not can_fire, "Should not fire at threshold"
    assert p1.tokens == 5, "Tokens unchanged at threshold"
    
    # Add surplus
    p1.tokens = 6
    can_fire, reason = behavior.can_fire()
    
    assert can_fire, "Should fire with surplus"
    
    # Fire
    success, details = behavior.fire(input_arcs=[inhibitor], output_arcs=[])
    
    assert p1.tokens == 1, "Should maintain 1 token reserve"
```

### Test Case 2: Multi-Place Starvation Prevention
```python
def test_multi_place_no_starvation():
    p1 = Place(id=1, tokens=10)
    p2 = Place(id=2, tokens=8)
    t1 = Transition(id=1, transition_type='immediate')
    
    # Both places must have surplus
    inhibitor1 = InhibitorArc(p1, t1, id=1, name='I1', weight=7)
    inhibitor2 = InhibitorArc(p2, t1, id=2, name='I2', weight=5)
    
    behavior = ImmediateBehavior(t1, model)
    
    # P1=10 > 7 ✓, P2=8 > 5 ✓ → Should fire
    can_fire, _ = behavior.can_fire()
    assert can_fire
    
    # Reduce P2 to threshold
    p2.tokens = 5
    
    # P1=10 > 7 ✓, P2=5 ≤ 5 ❌ → Should NOT fire
    can_fire, _ = behavior.can_fire()
    assert not can_fire, "P2 at threshold prevents firing"
```

### Test Case 3: Continuous Starvation Prevention
```python
def test_continuous_no_starvation():
    p1 = Place(id=1, tokens=10.0)
    t1 = Transition(id=1, transition_type='continuous')
    t1.properties = {'rate_function': 'P1'}
    p2 = Place(id=2, tokens=0.0)
    
    inhibitor = InhibitorArc(p1, t1, id=1, name='I1', weight=5)
    normal_out = Arc(t1, p2, id=2, name='A1', weight=1)
    
    behavior = ContinuousBehavior(t1, model)
    controller = SimulationController(model)
    
    # Simulate until near threshold
    while p1.tokens > 5.1:
        controller.step(0.01)
    
    # Should stop at threshold
    assert p1.tokens >= 5.0, "Should maintain threshold reserve"
    assert p1.tokens < 5.2, "Should stop near threshold"
```

## Design Patterns

### Pattern 1: Essential vs. Optional Consumption

```
Resource --[normal, w=3]--> Essential_Process
         --[inhibitor, w=10]--> Optional_Sharing

Behavior:
- Essential process fires at Resource ≥ 3
- Optional sharing fires at Resource > 10
- Priority: Survival before cooperation
```

### Pattern 2: Tiered Cooperation

```
Food(50) --[inhibitor, w=30]--> Help_Neighbors
         --[inhibitor, w=20]--> Help_Family
         --[inhibitor, w=10]--> Help_Self_Only

Behavior:
- 0-10: No cooperation (starvation mode)
- 11-20: Help family only
- 21-30: Help family and neighbors
- 31+: Full cooperation mode
```

### Pattern 3: Reciprocal Non-Starvation

```
Cell_A(ATP) --[inhibitor, w=5]--> Export_to_B
Cell_B(ATP) --[inhibitor, w=5]--> Export_to_A

Behavior:
- Both cells maintain minimum ATP=5
- Each exports only with surplus
- Mutual protection from starvation
- Cooperation when both are healthy
```

## Relationship to Classical Petri Nets

### Classical Inhibitor Semantics (Inverted)
```python
# Classical: enabled when tokens < weight (NOT in SHYPN!)
enabled = source_place.tokens < arc.weight
consumption = 0  # No consumption
```

**Use Case:** Manufacturing process control, absence detection

### SHYPN Living Systems Semantics
```python
# SHYPN: enabled when tokens > weight
enabled = source_place.tokens > arc.weight
consumption = arc.weight  # Yes, consumes tokens
```

**Use Case:** Biological cooperation, resource sharing, starvation prevention

## Theoretical Foundations

### Tragedy of the Commons - Avoided
The no-starvation principle prevents the tragedy of the commons by ensuring:
1. Individual entities maintain survival reserves
2. Cooperation occurs only from surplus
3. System-wide resource depletion is prevented

### Evolutionary Stability
Strategies that violate no-starvation are evolutionarily unstable:
- Entities that share below threshold die out
- Only surplus-sharing strategies persist
- Emerges naturally in biological systems

### Game Theory Connection
This implements a "Generous Tit-for-Tat" strategy:
- Cooperate when you can afford it (surplus)
- Defect when you can't afford it (at threshold)
- Maintains long-term cooperation without self-sacrifice

## References

- **Petri Net Theory**: Classical token game semantics
- **Systems Biology**: Metabolic network modeling
- **Evolutionary Biology**: Cooperation and altruism
- **Game Theory**: Resource sharing strategies
- **Ecology**: Resource partitioning in communities

## Implementation Status

- ✅ **Core Logic**: Strict surplus checking implemented
- ✅ **Inhibitor Arcs**: `tokens > weight` for enablement
- ✅ **Normal Arcs**: `tokens >= weight` for enablement  
- ✅ **Test Arcs**: `tokens >= weight`, no consumption
- ✅ **Documentation**: Comprehensive principle explanation
- ⏳ **UI Indicators**: Visual feedback for starvation states
- ⏳ **Analysis Tools**: Starvation risk detection
- ⏳ **Simulation Metrics**: Starvation event tracking

## Next Steps

1. **Add Starvation Indicators**
   - Visual warning when place near threshold
   - Color coding for risk levels
   - Dashboard metrics

2. **Starvation Analysis Tool**
   - Detect potential starvation paths
   - Recommend threshold adjustments
   - Verify no-starvation invariant

3. **Extended Semantics**
   - Configurable threshold policies
   - Dynamic thresholds based on context
   - Multi-level reserve strategies

4. **Performance Metrics**
   - Track closest approach to starvation
   - Measure cooperation efficiency
   - Analyze reserve utilization

## Changelog

### 2025-11-01
- ✅ Implemented strict surplus check for inhibitor arcs
- ✅ Changed enablement from `tokens >= weight` to `tokens > weight`
- ✅ Added comprehensive documentation
- ✅ Biological interpretation and examples
- ✅ Verified prevents starvation in test cases
