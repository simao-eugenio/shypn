# Marking vs Rate Plot Comparison

## Visual Comparison: What Changed?

### Example: Continuous Transition Draining a Place

**Petri Net**: `P1[25] --[continuous, rate=1.0]--> P2[0]`

---

### BEFORE (Rate Plot) ❌
```
Place Token Consumption/Production Rate
^
|  0 ┼─────────────────────────────────── P2 (no change)
|    │
| -1 ┼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ P1 (constant drain)
|    │
└────┴─────────────────────────────────>
     0    5    10   15   20   25  Time(s)
```

**Issues**:
- ❌ What does "-1 tokens/s" mean at t=10?
- ❌ Hard to know actual state: How many tokens in P1 at t=10?
- ❌ Rate shows consumption, but not the marking itself
- ❌ Must mentally integrate rate to estimate tokens

---

### AFTER (Marking Plot) ✅
```
Place Marking Evolution
^
| 25 ┼╲                                    P1 (draining)
|    │ ╲
| 12 ┼  ╲                                 
|    │   ╲
|  0 ┼────╲──────────────────────────── P2 (stays empty)
|    │     ╲_______(25s)
└────┴─────────────────────────────────>
     0    5    10   15   20   25  Time(s)
```

**Benefits**:
- ✅ **Direct state reading**: P1 has ~12 tokens at t=12
- ✅ **Clear visualization**: P1 drains linearly from 25 to 0
- ✅ **Intuitive**: "Place starts with 25, ends with 0"
- ✅ **No math needed**: See actual marking directly

---

## Example 2: Discrete Transitions

**Petri Net**: `P1[5] --[immediate]--> P2[0]` (fires 5 times)

### BEFORE (Rate Plot) ❌
```
^
|        ↑         ↑         ↑         ↑         ↑
| +∞ ─────┼─────────┼─────────┼─────────┼─────────┼──── P2 (spikes)
|        │         │         │         │         │
|  0 ────┼─────────┼─────────┼─────────┼─────────┼────
|        │         │         │         │         │
| -∞ ────┼─────────┼─────────┼─────────┼─────────┼──── P1 (spikes)
|        ↓         ↓         ↓         ↓         ↓
└────────┴─────────┴─────────┴─────────┴─────────┴────>
```

**Problems**:
- ❌ Infinite spikes (Dirac deltas) at firing instants
- ❌ Zero rate between firings
- ❌ Impossible to see actual state evolution
- ❌ Rate calculation artifacts (sliding window issues)

### AFTER (Marking Plot) ✅
```
^
|  5 ┼─┐  P1 (decreasing)
|  4 ┼ └─┐
|  3 ┼   └─┐
|  2 ┼     └─┐
|  1 ┼       └─┐
|  0 ┼─────────└────────────────────────────────
|    │         ┌─┐   ┌─┐   ┌─┐   ┐─┐   ┌─
|  1 ┼─────────┘ └───┘ └───┘ └───┘ └───┘  P2 (step up)
|    │
└────┴──────────────────────────────────────────>
```

**Benefits**:
- ✅ **Clear steps**: See each token move from P1 to P2
- ✅ **State at any time**: P1=3, P2=2 after 2nd firing
- ✅ **Conservation visible**: P1 + P2 = 5 always
- ✅ **Discrete nature clear**: Instantaneous jumps

---

## Example 3: Mixed System (Continuous + Discrete)

**Petri Net**: 
```
P1[20] --[continuous, rate=0.5]--> P2[0] --[stochastic, λ=2.0]--> P3[0]
```

### BEFORE (Rate Plot) ❌
```
^
| +0.5 ┼━━━━━━━━━━━━━━━━━━━━━━━━ P1 (constant rate)
|  0.0 ┼─────────────────────────
| -0.5 ┼  ┌──┐  ┌─┐ ┌─┐    ┌──┐  P2 (spiky rate)
|      │  │  │  │ │ │ │    │  │
| -∞   ┼  ↓  ↓  ↓ ↓ ↓ ↓    ↓  ↓
└──────┴──────────────────────────>
```

**Confusing**:
- ❌ Can't compare different transition types easily
- ❌ Discrete spikes dominate the plot
- ❌ Hard to see system behavior

### AFTER (Marking Plot) ✅
```
^
| 20 ┼╲                                P1 (smooth decay)
|    │ ╲___
| 10 ┼     ╲___                        P2 (sawtooth pattern)
|    │  /╲ /╲ /╲___                        - fills continuously
|  5 ┼_/  V  V      ╲__                    - empties discretely
|    │         ┌─┐  ┌─┐ ┌─┐           P3 (step up)
|  0 ┼─────────┘ └──┘ └─┘ └───
└────┴──────────────────────────>
```

**Clear**:
- ✅ **P1**: Smooth drain (continuous)
- ✅ **P2**: Sawtooth (fills continuously, empties in chunks)
- ✅ **P3**: Step increases (discrete arrivals)
- ✅ **System behavior**: Can see token flow through network

---

## Technical Comparison

| Aspect | Rate Plot (Old) | Marking Plot (New) |
|--------|----------------|-------------------|
| **Y-axis** | `d(tokens)/dt` | `tokens` |
| **Computation** | Derivative with sliding window | Direct measurement |
| **Continuous** | Horizontal line (constant rate) | Slope (growth/decay) |
| **Discrete** | Infinite spikes (Dirac deltas) | Step functions |
| **State info** | Must integrate to get marking | Direct state reading |
| **Intuition** | ⭐⭐ (requires calculus) | ⭐⭐⭐⭐⭐ (obvious) |
| **Performance** | Slower (rate calculation) | Faster (direct data) |
| **Zero line** | Meaningful (production vs consumption) | Not meaningful (removed) |

---

## When Would Rate Be Useful?

Rate plots could still be valuable for:

1. **Sensitivity Analysis**: See how small changes in arc weights affect flow
2. **Bottleneck Detection**: Identify where rates don't match (accumulation points)
3. **Steady-State Analysis**: Verify rates balance (conservation check)
4. **Derivative Information**: Understand acceleration (d²tokens/dt²)

**Future**: Could add a toggle button to switch between views!

---

## Summary

### What Users See Now ✅

- **"Place P1 has 15 tokens at time 10s"** ← Clear!
- **"Place P2 is draining from 20 to 0 over 40 seconds"** ← Visual!
- **"Place P3 jumps from 0 to 5 when transition fires"** ← Obvious!

### What Users Saw Before ❌

- **"Rate is -2.5 tokens/s"** ← Must integrate mentally
- **"Infinite spike at t=5"** ← Mathematical artifact
- **"Need sliding window of 0.1s"** ← Implementation detail

**Result**: Much more intuitive for understanding Petri net behavior! 🎉
