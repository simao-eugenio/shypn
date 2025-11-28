# Validation - Example 1: ATP Hydrolysis

## Expected Model Behavior

This document describes the expected behavior of the ATP hydrolysis model to validate correct implementation.

---

## Topology Analysis

### Expected Results

**P-invariants** (Place invariants):
```
Invariant 1: ATP + ADP = 3100 tokens (constant)
```
This represents conservation of the adenylate pool.

**T-invariants** (Transition invariants):
```
Invariant 1: ATPase = 1
```
Single pathway through the network.

**Structural Properties**:
- Bounded: Yes (maximum tokens limited by initial marking)
- Conservative: Yes (adenylate pool conserved)
- Deadlock-free: No (deadlocks when ATP = 0)
- Live: No (transition eventually becomes permanently disabled)

---

## Simulation Validation

### Immediate Mode (Discrete Tokens)

**Initial State** (t = 0):
- ATP: 3000 tokens
- ADP: 100 tokens
- Pi: 1000 tokens

**After 100 firings**:
- ATP: 2900 tokens
- ADP: 200 tokens
- Pi: 1100 tokens

**After 3000 firings** (steady state):
- ATP: 0 tokens
- ADP: 3100 tokens
- Pi: 4000 tokens

**Conservation Check**:
- Initial: ATP + ADP = 3000 + 100 = 3100 ✓
- After 100: 2900 + 200 = 3100 ✓
- Steady state: 0 + 3100 = 3100 ✓

---

### Continuous Mode (Concentrations)

Using rate law: **v = 100 × [ATP]**

This is a first-order decay: **d[ATP]/dt = -100 × [ATP]**

Solution: **[ATP](t) = [ATP]₀ × e^(-100t)**

#### Time Points

| Time (s) | [ATP] (mM) | [ADP] (mM) | [Pi] (mM) | Check Sum |
|----------|------------|------------|-----------|-----------|
| 0.000    | 3.000      | 0.100      | 1.000     | 3.100 ✓   |
| 0.005    | 1.820      | 1.280      | 2.180     | 3.100 ✓   |
| 0.010    | 1.104      | 1.996      | 2.996     | 3.100 ✓   |
| 0.020    | 0.406      | 2.694      | 3.694     | 3.100 ✓   |
| 0.050    | 0.020      | 3.080      | 4.080     | 3.100 ✓   |

#### Key Metrics

**Half-life** (t₁/₂):
```
t₁/₂ = ln(2) / k = 0.693 / 100 = 0.00693 s ≈ 6.93 ms
```

At t = 6.93 ms:
- [ATP] should be 3.0 / 2 = 1.5 mM ✓

**Time constant** (τ):
```
τ = 1 / k = 1 / 100 = 0.01 s = 10 ms
```

At t = 10 ms (one τ):
- [ATP] should be 3.0 / e = 1.104 mM ✓

**Rate at t = 0**:
```
v₀ = 100 × 3.0 = 300 mM/s
```

---

## Verification Checklist

### Model Construction
- [ ] 3 places created (ATP, ADP, Pi)
- [ ] 1 transition created (ATPase)
- [ ] 3 arcs created with correct stoichiometry
- [ ] Initial markings set correctly (3000, 100, 1000)
- [ ] Rate law defined: `100 * ATP`

### Topology Analysis
- [ ] P-invariant detected: ATP + ADP
- [ ] T-invariant detected: ATPase
- [ ] System identified as bounded
- [ ] System identified as conservative
- [ ] Deadlock detected when ATP = 0

### Immediate Simulation
- [ ] Transition fires when ATP > 0
- [ ] Transition blocked when ATP = 0
- [ ] Each firing: ATP -1, ADP +1, Pi +1
- [ ] Conservation holds after each step
- [ ] Reaches steady state with ATP = 0

### Continuous Simulation
- [ ] Exponential decay of [ATP]
- [ ] Smooth curves (no discontinuities)
- [ ] Half-life ≈ 6.93 ms
- [ ] Time constant ≈ 10 ms
- [ ] Conservation maintained throughout
- [ ] Steady state: [ATP] ≈ 0, [ADP] ≈ 3.1 mM

### Analysis Tools
- [ ] Time series plot shows exponential decay
- [ ] Rate vs. time shows exponential decrease
- [ ] Phase plot (if 2D) shows trajectory to steady state
- [ ] Conservation law verified numerically

---

## Common Issues and Troubleshooting

### Issue 1: Conservation not maintained
**Symptom**: ATP + ADP ≠ 3100 tokens
**Cause**: Incorrect arc stoichiometry
**Fix**: Verify all arcs have weight = 1

### Issue 2: Transition fires when ATP = 0
**Symptom**: Negative ATP tokens
**Cause**: Missing arc from ATP to ATPase
**Fix**: Add input arc from ATP to transition

### Issue 3: Non-exponential decay in continuous mode
**Symptom**: Linear or irregular decay curve
**Cause**: Incorrect rate law
**Fix**: Rate law must be `100 * ATP` (first-order)

### Issue 4: Steady state not reached
**Symptom**: Simulation stops before ATP ≈ 0
**Cause**: Simulation time too short
**Fix**: Increase simulation time to 0.05 s or more

### Issue 5: Wrong time scale
**Symptom**: Half-life not matching 6.93 ms
**Cause**: Rate constant k_cat incorrect
**Fix**: Verify k_cat = 100 s⁻¹ in rate law

---

## Acceptance Criteria

✓ Model loads without errors
✓ All topology checks pass
✓ Immediate simulation behaves discretely and correctly
✓ Continuous simulation shows exponential decay
✓ Conservation law verified numerically (tolerance < 0.001 mM)
✓ Half-life within 5% of theoretical value (6.93 ms)
✓ Steady state values within 1% of expected

---

## Notes

This is the simplest possible model in the series. If validation fails here, it indicates fundamental issues with model construction that must be resolved before proceeding to more complex examples.

**Pass/Fail**: _____

**Date Validated**: _____

**Validated By**: _____

**Issues Found**: _____
