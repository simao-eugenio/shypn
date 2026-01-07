# Core Foundations Audit Plan
**Date**: January 5, 2026  
**Purpose**: Validate theoretical foundations and core functionality for manuscript submission  
**Status**: PLANNED

---

## 🎯 Audit Objectives

Systematically validate:
1. **Weak Independence Theory** - Transitions fire independently based on local enabling conditions
2. **Signal Hierarchy Theory** - Signal places modify transition rates without being consumed
3. **Type System Integrity** - All combinations of place/transition/arc types behave correctly
4. **Stoichiometric Correctness** - Token flow follows arc weights precisely
5. **Rate Function Semantics** - All transition types compute rates correctly

---

## 📋 Phase 1: Place Type Validation

### Test Matrix: Place Types
| Place Type | Token Type | Behavior | Test Case |
|------------|------------|----------|-----------|
| Normal     | Integer    | Consumed by transitions | ✓ Basic Petri net |
| Normal     | Continuous | Consumed by transitions | ✓ Continuous model |
| Signal     | Integer    | NOT consumed (hierarchy) | ⚠ CRITICAL |
| Signal     | Continuous | NOT consumed (hierarchy) | ⚠ CRITICAL |
| Source     | Unbounded  | Always enabled | ✓ Boundary |
| Sink       | Unbounded  | Always accepts | ✓ Boundary |

### Validation Tests:
```python
# Test 1: Normal place consumption
def test_normal_place_consumption():
    """Verify normal places lose tokens when transition fires"""
    place = Place(type='normal', tokens=5)
    transition = Transition(type='stochastic')
    arc = Arc(place, transition, weight=2)
    
    # Fire transition
    fire(transition)
    
    assert place.tokens == 3  # 5 - 2 = 3
    
# Test 2: Signal place NON-consumption (WEAK INDEPENDENCE)
def test_signal_place_non_consumption():
    """Verify signal places keep tokens (signal hierarchy theory)"""
    signal_place = Place(type='signal', tokens=10)
    substrate = Place(type='normal', tokens=5)
    transition = Transition(type='stochastic', rate='0.1*S1')
    
    arc1 = Arc(signal_place, transition, weight=1, arc_type='read')
    arc2 = Arc(substrate, transition, weight=1)
    
    # Fire transition
    fire(transition)
    
    assert signal_place.tokens == 10  # UNCHANGED (signal hierarchy)
    assert substrate.tokens == 4       # CONSUMED (normal place)
    
# Test 3: Source place unbounded supply
def test_source_place_infinite():
    """Verify source places never deplete"""
    source = Place(type='source', tokens=1)
    transition = Transition(type='stochastic')
    arc = Arc(source, transition, weight=1)
    
    for _ in range(100):
        assert transition.is_enabled()
        fire(transition)
        assert source.tokens >= 1  # Never depletes
```

---

## 📋 Phase 2: Transition Type Validation

### Test Matrix: Transition Types
| Type        | Rate Function | Firing Rule | Dependencies | Test Case |
|-------------|---------------|-------------|--------------|-----------|
| Stochastic  | Constant/Expression | Gillespie SSA | Token count | ⚠ CRITICAL |
| Continuous  | Rate function | Deterministic ODE | Token count | ⚠ CRITICAL |
| Immediate   | Priority-based | Zero delay | Conflicts | ✓ Standard |
| Timed       | Delay parameter | Fixed delay | None | ✓ Standard |

### Validation Tests:
```python
# Test 4: Stochastic transition propensity
def test_stochastic_propensity():
    """Verify stochastic transitions use mass action kinetics"""
    P1 = Place(tokens=10)
    P2 = Place(tokens=5)
    T = Transition(type='stochastic', rate=0.5)
    
    Arc(P1, T, weight=2)
    Arc(P2, T, weight=1)
    
    # Propensity = rate * binomial(P1, 2) * binomial(P2, 1)
    expected = 0.5 * (10 * 9 / 2) * 5
    assert T.calculate_propensity() == expected

# Test 5: Continuous transition rate evaluation
def test_continuous_rate_function():
    """Verify continuous transitions evaluate rate functions correctly"""
    P1 = Place(tokens=20.5)
    T = Transition(type='continuous', rate='0.1 * P1')
    
    Arc(P1, T, weight=1)
    
    # Rate should be 0.1 * 20.5 = 2.05
    assert T.evaluate_rate() == 2.05
    
# Test 6: Signal hierarchy in rate functions
def test_signal_hierarchy_rate_modulation():
    """CRITICAL: Verify signal places modulate rates without consumption"""
    substrate = Place(type='normal', tokens=100)
    signal = Place(type='signal', tokens=10)  # e.g., ATP
    product = Place(type='normal', tokens=0)
    
    # Rate depends on signal but doesn't consume it
    T = Transition(type='continuous', rate='0.5 * ATP * S1')
    
    Arc(signal, T, weight=0, arc_type='read')  # Signal (not consumed)
    Arc(substrate, T, weight=1)                 # Consumed
    Arc(T, product, weight=1)                   # Produced
    
    initial_signal = signal.tokens
    simulate(T, duration=1.0)
    
    # CRITICAL CHECKS:
    assert signal.tokens == initial_signal  # Signal unchanged
    assert substrate.tokens < 100           # Substrate consumed
    assert product.tokens > 0               # Product created
    assert T.rate == 0.5 * initial_signal * substrate.tokens
```

---

## 📋 Phase 3: Arc Type Validation

### Test Matrix: Arc Types
| Arc Type   | Behavior | Token Test | Enabling | Test Case |
|------------|----------|------------|----------|-----------|
| Normal     | Consume/Produce | Subtract/Add | Sufficient tokens | ✓ Basic |
| Test       | Test only | No change | Sufficient tokens | ⚠ CRITICAL |
| Inhibitor  | Inverse enable | No change | Insufficient tokens | ⚠ CRITICAL |
| Read       | Read tokens | No change | Any tokens | ⚠ CRITICAL |

### Validation Tests:
```python
# Test 7: Test arc (non-consuming read)
def test_test_arc_non_consuming():
    """Verify test arcs check tokens without consuming"""
    place = Place(tokens=5)
    transition = Transition()
    arc = Arc(place, transition, weight=3, arc_type='test')
    
    assert transition.is_enabled()  # 5 >= 3
    fire(transition)
    assert place.tokens == 5  # UNCHANGED
    
# Test 8: Inhibitor arc (inverse enabling)
def test_inhibitor_arc_inverse():
    """Verify inhibitor arcs prevent firing when tokens present"""
    place = Place(tokens=5)
    transition = Transition()
    arc = Arc(place, transition, weight=3, arc_type='inhibitor')
    
    assert not transition.is_enabled()  # 5 >= 3, so inhibited
    
    place.tokens = 2
    assert transition.is_enabled()  # 2 < 3, so NOT inhibited
    
# Test 9: Read arc (signal hierarchy implementation)
def test_read_arc_signal_hierarchy():
    """CRITICAL: Verify read arcs implement signal hierarchy correctly"""
    signal = Place(type='signal', tokens=10)
    substrate = Place(type='normal', tokens=20)
    transition = Transition(type='continuous', rate='k * Signal')
    
    arc_signal = Arc(signal, transition, weight=1, arc_type='read')
    arc_substrate = Arc(substrate, transition, weight=1, arc_type='normal')
    
    # Transition should be enabled by signal but not consume it
    assert transition.is_enabled()
    initial_signal = signal.tokens
    
    fire(transition)
    
    assert signal.tokens == initial_signal  # Signal hierarchy preserved
    assert substrate.tokens == 19           # Normal consumption
```

---

## 📋 Phase 4: Weak Independence Theory

### Core Principle
"Transitions fire independently based on LOCAL enabling conditions. Global state changes only through token flow."

### Validation Tests:
```python
# Test 10: Local enabling independence
def test_weak_independence_local_enabling():
    """Verify transitions fire based ONLY on local place tokens"""
    # Network: P1 -> T1 -> P2 -> T2 -> P3
    P1 = Place(tokens=10)
    P2 = Place(tokens=0)
    P3 = Place(tokens=0)
    
    T1 = Transition(rate=1.0)
    T2 = Transition(rate=1.0)
    
    Arc(P1, T1, weight=1)
    Arc(T1, P2, weight=1)
    Arc(P2, T2, weight=1)
    Arc(T2, P3, weight=1)
    
    # Initially: T1 enabled, T2 disabled
    assert T1.is_enabled()
    assert not T2.is_enabled()
    
    # Fire T1: P2 gains token, enabling T2
    fire(T1)
    
    assert P2.tokens == 1
    assert T2.is_enabled()  # Now enabled due to token flow
    assert T1.is_enabled()  # Still enabled (P1 has tokens)
    
    # This proves: enabling is LOCAL, not global

# Test 11: Concurrent enabling (no mutual exclusion without arcs)
def test_weak_independence_concurrent_enabling():
    """Verify independent transitions can fire concurrently"""
    P1 = Place(tokens=10)
    P2 = Place(tokens=10)
    
    T1 = Transition()
    T2 = Transition()
    
    Arc(P1, T1, weight=1)
    Arc(P2, T2, weight=1)
    
    # Both should be enabled simultaneously
    assert T1.is_enabled()
    assert T2.is_enabled()
    
    # Firing T1 should NOT affect T2's enabling
    fire(T1)
    assert T2.is_enabled()  # WEAK INDEPENDENCE

# Test 12: Shared place creates dependency
def test_weak_independence_shared_place_dependency():
    """Verify shared places create proper dependencies"""
    shared = Place(tokens=1)
    
    T1 = Transition()
    T2 = Transition()
    
    Arc(shared, T1, weight=1)
    Arc(shared, T2, weight=1)
    
    # Both enabled initially
    assert T1.is_enabled()
    assert T2.is_enabled()
    
    # Fire T1: consumes token, disabling T2
    fire(T1)
    
    assert not T2.is_enabled()  # Dependency through token flow
```

---

## 📋 Phase 5: Signal Hierarchy Theory

### Core Principle
"Signal places modulate transition rates WITHOUT being consumed. They represent regulatory molecules (ATP, cofactors, signals) that catalyze reactions without being depleted."

### Validation Tests:
```python
# Test 13: Signal carrier distinction
def test_signal_vs_carrier():
    """CRITICAL: Distinguish signal carriers from signal places"""
    # ATP is signal (not consumed)
    ATP = Place(type='signal', tokens=1000)
    
    # Glucose is carrier (consumed and produced)
    Glucose = Place(type='normal', tokens=100)
    G6P = Place(type='normal', tokens=0)
    
    # Reaction: Glucose + ATP -> G6P + ATP (ATP recycled)
    T = Transition(rate='k * ATP * Glucose')
    
    Arc(ATP, T, weight=1, arc_type='read')      # ATP: signal
    Arc(Glucose, T, weight=1)                   # Consumed
    Arc(T, G6P, weight=1)                       # Produced
    # Note: ATP is NOT produced explicitly (it's a signal)
    
    simulate(T, duration=10)
    
    # CRITICAL: ATP unchanged (signal hierarchy)
    assert ATP.tokens == 1000
    assert Glucose.tokens < 100
    assert G6P.tokens > 0

# Test 14: Hierarchical signal cascade
def test_signal_hierarchy_cascade():
    """Verify cascading signal modulation"""
    # Cascade: Signal1 -> T1 -> Signal2 -> T2 -> Product
    Signal1 = Place(type='signal', tokens=10)
    Signal2 = Place(type='signal', tokens=0)
    Substrate = Place(type='normal', tokens=100)
    Product = Place(type='normal', tokens=0)
    
    T1 = Transition(rate='k1 * S1')  # Activated by Signal1
    T2 = Transition(rate='k2 * S2')  # Activated by Signal2
    
    # T1 creates Signal2 (signal propagation)
    Arc(Signal1, T1, arc_type='read')
    Arc(T1, Signal2, weight=1)  # Signal2 produced
    
    # T2 uses Signal2
    Arc(Signal2, T2, arc_type='read')
    Arc(Substrate, T2, weight=1)
    Arc(T2, Product, weight=1)
    
    simulate([T1, T2], duration=10)
    
    # Both signals should persist
    assert Signal1.tokens == 10  # Unchanged (original signal)
    assert Signal2.tokens > 0    # Produced and preserved
    assert Product.tokens > 0    # Final product created

# Test 15: Signal vs substrate stoichiometry
def test_signal_hierarchy_stoichiometry():
    """CRITICAL: Verify stoichiometry respects signal hierarchy"""
    # Enzyme-catalyzed reaction: S + E -> P + E
    # E is enzyme (signal), S is substrate (carrier)
    
    Enzyme = Place(type='signal', tokens=1)
    Substrate = Place(type='normal', tokens=100)
    Product = Place(type='normal', tokens=0)
    
    T = Transition(rate='kcat * E * S / (Km + S)')  # Michaelis-Menten
    
    Arc(Enzyme, T, arc_type='read', weight=1)
    Arc(Substrate, T, weight=1)
    Arc(T, Product, weight=1)
    
    simulate(T, duration=100)
    
    # Mass balance: S + P = 100 (conserved)
    assert Substrate.tokens + Product.tokens == 100
    
    # Enzyme unchanged (signal hierarchy)
    assert Enzyme.tokens == 1
```

---

## 📋 Phase 6: Integration Tests

### Test 16: Complete Metabolic Pathway
```python
def test_glycolysis_signal_hierarchy():
    """Real-world test: Glycolysis with ATP as signal carrier"""
    
    # Metabolites (carriers - consumed/produced)
    Glucose = Place(type='normal', tokens=100)
    G6P = Place(type='normal', tokens=0)
    F6P = Place(type='normal', tokens=0)
    F16BP = Place(type='normal', tokens=0)
    
    # Cofactors (signals - NOT consumed)
    ATP = Place(type='signal', tokens=1000)
    ADP = Place(type='signal', tokens=100)
    
    # Reactions with signal hierarchy
    Hexokinase = Transition(rate='Vmax_HK * ATP * Glucose')
    PGI = Transition(rate='k_PGI * G6P')
    PFK = Transition(rate='Vmax_PFK * ATP * F6P / (Km + F6P)')
    
    # Build network with signal arcs
    # HK: Glucose + ATP -> G6P + ADP (ATP signal)
    Arc(Glucose, Hexokinase, weight=1)
    Arc(ATP, Hexokinase, arc_type='read')
    Arc(Hexokinase, G6P, weight=1)
    Arc(Hexokinase, ADP, weight=1)  # ADP produced
    
    # Continue network...
    
    simulate([Hexokinase, PGI, PFK], duration=100)
    
    # Validate conservation laws
    assert ATP.tokens + ADP.tokens == 1100  # Total adenosine conserved
    assert Glucose.tokens + G6P.tokens + F6P.tokens + F16BP.tokens == 100
```

---

## 🔧 Implementation Plan

### Step 1: Create Test Infrastructure (Day 1)
```bash
mkdir -p tests/core_foundations
touch tests/core_foundations/__init__.py
touch tests/core_foundations/test_place_types.py
touch tests/core_foundations/test_transition_types.py
touch tests/core_foundations/test_arc_types.py
touch tests/core_foundations/test_weak_independence.py
touch tests/core_foundations/test_signal_hierarchy.py
touch tests/core_foundations/test_integration.py
```

### Step 2: Implement Tests (Day 2-3)
- Write all 15 core tests
- Add integration test (glycolysis)
- Document expected vs actual behavior

### Step 3: Run Audit (Day 4)
```bash
python -m pytest tests/core_foundations/ -v --tb=short
```

### Step 4: Fix Failures (Day 5-6)
- Document each failure
- Fix root cause
- Re-test until all pass

### Step 5: Regression Suite (Day 7)
- Add tests to CI/CD
- Create "Foundation Tests" badge
- Run before every release

---

## 📊 Audit Metrics

| Category | Tests | Pass | Fail | Critical |
|----------|-------|------|------|----------|
| Place Types | 3 | ? | ? | 2 |
| Transition Types | 3 | ? | ? | 3 |
| Arc Types | 3 | ? | ? | 3 |
| Weak Independence | 3 | ? | ? | 3 |
| Signal Hierarchy | 3 | ? | ? | 3 |
| Integration | 1 | ? | ? | 1 |
| **TOTAL** | **16** | **0** | **0** | **15** |

**Pass Threshold for Manuscript**: 15/16 critical tests (93.75%)

---

## 🚨 Known Risks

1. **Signal Hierarchy Implementation**
   - Risk: Read arcs may actually consume tokens
   - Test: #9, #13, #15
   - Impact: INVALIDATES core theory

2. **Weak Independence Violations**
   - Risk: Global state affects local enabling
   - Test: #10, #11, #12
   - Impact: Non-Markovian behavior

3. **Rate Function Evaluation**
   - Risk: Signal places consumed in continuous transitions
   - Test: #6, #14
   - Impact: Incorrect dynamics

4. **Stoichiometric Violations**
   - Risk: Token counts don't balance
   - Test: #16
   - Impact: Violates conservation laws

---

## 📝 Documentation Requirements

After audit completion:
1. **Test Report**: Document all results
2. **Theory Validation**: Confirm weak independence + signal hierarchy
3. **Known Limitations**: Document any failures
4. **Manuscript Addendum**: Add "Theoretical Validation" section

---

## ✅ Sign-Off Criteria

Before manuscript submission:
- [ ] All 15 critical tests pass
- [ ] Integration test (glycolysis) passes
- [ ] No stoichiometric violations detected
- [ ] Signal hierarchy verified in 3+ scenarios
- [ ] Weak independence verified in 3+ scenarios
- [ ] Test suite runs in <60 seconds
- [ ] CI/CD pipeline includes foundation tests
- [ ] Documentation updated with validation results

---

**Audit Owner**: [Your Name]  
**Review Date**: TBD  
**Manuscript Deadline**: TBD
