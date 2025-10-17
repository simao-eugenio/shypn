# Continuous Transition Validation

**Transition Type:** Continuous  
**Status:** Not Yet Planned  
**Priority:** Phase 4

---

## Overview

This directory will contain validation documentation and test plans for **continuous transitions** in SHYpn Petri nets.

**Continuous transitions** enable continuous token flow, modeled by ordinary differential equations (ODEs).

---

## Coming Soon

- Benchmark plan with test categories
- Properties specific to continuous transitions
- Rate function validation
- ODE solver integration testing
- Time-dependent behavior validation

---

## Continuous Transition Characteristics

**Key Properties:**
- `transition_type` = 'continuous'
- `rate` - Can be constant or function expression
- `properties['rate_function']` - String expression for dynamic rates
- `guard` - Enable condition (can be time-dependent)

**Rate Function Types:**
- **Constant:** `1.0`
- **Linear:** `"2*t"`
- **Sigmoid:** `"sigmoid(P1, 50, 10)"`
- **Exponential:** `"exp(-0.5*t)"`
- **Custom:** Any mathematical expression

**Behavior:**
- Continuous token flow (not discrete firings)
- Rate determines flow speed
- ODE integration over time
- Can depend on time, place tokens, and custom functions

---

## Status

🔜 **Planning not yet started**

Will be addressed after immediate, timed, and stochastic transition validation.

---

## Related

- [Immediate Transitions](../immediate/) - Current focus
- [Timed Transitions](../timed/) - Phase 2
- [Stochastic Transitions](../stochastic/) - Phase 3
- Main validation framework: [../README.md](../README.md)
- Rate function documentation: `/doc/GUARD_RATE_PERSISTENCE_FIX.md`
