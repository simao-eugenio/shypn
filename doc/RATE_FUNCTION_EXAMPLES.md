# Rate Function Examples - Copy & Paste Reference

**For Continuous Transitions in SHYPN**

This guide provides ready-to-use rate function expressions that you can copy and paste directly into the "Rate Function" field of continuous transition property dialogs.

---

## 📋 Quick Reference

### Basic Functions

| Function Type | Copy-Paste Expression | Description |
|--------------|----------------------|-------------|
| Constant | `5.0` | Fixed rate (5 tokens/second) |
| Linear | `0.5 * P1` | Proportional to place P1 |
| Saturated | `min(10, P1)` | Capped at maximum |
| Time-based | `2.0 * t` | Increases with time |

### Advanced Functions

| Function Type | Copy-Paste Expression | What It Does |
|--------------|----------------------|--------------|
| **Sigmoid** | `sigmoid(t, 10, 0.5)` | S-curve (logistic growth) |
| **Exponential Growth** | `math.exp(0.1 * t)` | Rapid increase |
| **Exponential Decay** | `math.exp(-0.1 * t)` | Gradual decrease |
| **Hill (Cooperativity)** | `hill(P1, 5, 2)` | Enzyme kinetics |
| **Michaelis-Menten** | `michaelis_menten(P1, 10, 5)` | Saturation kinetics |

---

## 🔢 Detailed Examples

### 1. Sigmoid Function (Logistic Curve)

**📋 Copy-Paste**:
```
sigmoid(t, 10, 0.5)
```

**Parameters**:
- `t` = time variable (always use lowercase `t`)
- `10` = midpoint (when does curve reach 50%?)
- `0.5` = steepness (higher = sharper transition)

**What it does**:
- Creates an S-shaped curve from 0 to 1
- Starts slow, accelerates, then saturates
- Perfect for: startup behavior, logistic growth, saturation

**Variations**:
```
sigmoid(t, 5, 1.0)      # Earlier midpoint (t=5), steeper
sigmoid(t, 20, 0.2)     # Later midpoint (t=20), gentler
5.0 * sigmoid(t, 10, 0.5)  # Scale to 0→5 range
```

**Visual**:
```
Rate
  1 ┼              ╭───────  (saturates at 1)
0.5 ┼          ╭───          (midpoint at t=10)
  0 ┼──────╭───
    └──────┴──────┴─────> Time
          10     20
```

---

### 2. Sigmoid Based on Place Tokens (State-Dependent)

**📋 Copy-Paste**:
```
sigmoid(P1, 50, 0.1)
```

**Parameters**:
- `P1` = number of tokens in Place 1
- `50` = half-saturation point (50 tokens)
- `0.1` = steepness

**What it does**:
- Rate depends on how many tokens are in P1
- Low tokens → low rate
- High tokens → high rate (saturated)
- Perfect for: feedback regulation, saturation effects

**Example Scenario**:
```
Enzyme Reaction:
Substrate (P1) → [continuous, sigmoid(P1, 50, 0.1)] → Product (P2)

When P1 < 50: slow reaction
When P1 ≈ 50: medium speed (inflection point)
When P1 > 50: fast reaction (saturated)
```

---

### 3. Exponential Growth

**📋 Copy-Paste**:
```
math.exp(0.1 * t)
```

**Parameters**:
- `0.1` = growth rate constant
- Higher value = faster growth

**What it does**:
- Rate increases exponentially over time
- Starts slow, becomes very fast
- **Warning**: Can explode to infinity!
- Use with `max_rate` property to cap it

**Variations**:
```
math.exp(0.05 * t)      # Slower growth
math.exp(0.2 * t)       # Faster growth
2.0 * math.exp(0.1 * t) # Scaled exponential
```

**Set max_rate**:
In properties dialog, also set:
- `max_rate: 100.0` (prevents infinite rate)

---

### 4. Exponential Decay

**📋 Copy-Paste**:
```
math.exp(-0.1 * t)
```

**Parameters**:
- `-0.1` = decay rate constant (negative!)
- More negative = faster decay

**What it does**:
- Rate starts at 1.0, decreases exponentially
- Approaches 0 but never reaches it
- Perfect for: radioactive decay, cooldown, dissipation

**Scaled Version**:
```
10.0 * math.exp(-0.1 * t)
```
Starts at 10, decays to ~0

**Visual**:
```
Rate
 10 ┼╲
    │ ╲___
  5 ┼     ╲___
    │         ╲___
  0 ┼─────────────╲______
    └──────┴──────┴─────> Time
          10     20
```

---

### 5. State-Dependent Linear Rate

**📋 Copy-Paste**:
```
0.5 * P1
```

**What it does**:
- Rate proportional to tokens in P1
- As P1 drains, rate decreases
- Creates exponential decay in token count
- Perfect for: first-order reactions, proportional flow

**Example**:
```
P1[100] → [continuous, rate='0.5 * P1'] → P2[0]

t=0:  P1=100 → rate = 50 tokens/s
t=5:  P1=80  → rate = 40 tokens/s
t=10: P1=60  → rate = 30 tokens/s
(Exponential decay curve)
```

---

### 6. Hill Function (Cooperativity)

**📋 Copy-Paste**:
```
hill(P1, 5, 2)
```

**Parameters**:
- `P1` = substrate concentration (place tokens)
- `5` = K (half-saturation constant)
- `2` = n (Hill coefficient, cooperativity)

**What it does**:
- Sigmoidal response to substrate concentration
- n > 1: positive cooperativity (sharp switch)
- n = 1: Michaelis-Menten (hyperbolic)
- n < 1: negative cooperativity (gradual)

**Variations**:
```
hill(P1, 5, 1)    # No cooperativity (same as MM)
hill(P1, 5, 4)    # Strong cooperativity (switch-like)
10.0 * hill(P1, 5, 2)  # Scaled to max rate of 10
```

**Use Cases**:
- Enzyme kinetics with multiple binding sites
- Gene regulation (transcription factors)
- Allosteric effects

---

### 7. Michaelis-Menten (Enzyme Saturation)

**📋 Copy-Paste**:
```
michaelis_menten(P1, 10, 5)
```

**Parameters**:
- `P1` = substrate concentration (place tokens)
- `10` = V_max (maximum rate)
- `5` = K_m (Michaelis constant)

**What it does**:
- Classic enzyme kinetics
- Rate = V_max * [S] / (K_m + [S])
- Hyperbolic saturation curve
- Perfect for: enzyme reactions, catalysis

**Visual**:
```
Rate
 10 ┼        ╭──────────  (V_max)
    │      ╭─
  5 ┼    ╭─              (at Km, rate = V_max/2)
    │  ╭─
  0 ┼──
    └──┴──┴──┴──┴──┴──> Substrate (P1)
       5  10 15 20
```

---

### 8. Piecewise / Conditional Rates

**📋 Copy-Paste**:
```
10.0 if t < 10 else 2.0
```

**What it does**:
- High rate (10) for first 10 seconds
- Then drops to low rate (2) forever
- Perfect for: mode changes, step responses

**Variations**:
```
5.0 if P1 > 50 else 1.0        # High rate when P1 full
(2.0 if t < 5 else 0.5) * P1   # Combined with state
```

---

### 9. Oscillating Rate (Sine Wave)

**📋 Copy-Paste**:
```
5.0 + 3.0 * math.sin(0.5 * t)
```

**Parameters**:
- `5.0` = baseline (average rate)
- `3.0` = amplitude (oscillation magnitude)
- `0.5` = frequency (radians per second)

**What it does**:
- Rate oscillates around baseline
- Creates periodic behavior
- Perfect for: circadian rhythms, periodic input

**Visual**:
```
Rate
  8 ┼    ╭─╮    ╭─╮
  5 ┼───╯   ╰───╯   ╰───  (baseline)
  2 ┼
    └──┴──┴──┴──┴──┴──> Time
```

---

### 10. Ramp Function (Linear Increase)

**📋 Copy-Paste**:
```
min(10, 0.5 * t)
```

**What it does**:
- Rate increases linearly with time
- Capped at maximum of 10
- Starts at 0, increases by 0.5 per second
- Reaches 10 at t=20, stays there

**Variations**:
```
min(20, t)          # Ramp to 20 at 1 unit/sec
min(5, 0.1 * t)     # Slow ramp to 5
```

---

### 11. Step Function (Sudden Change)

**📋 Copy-Paste**:
```
0.0 if t < 10 else 5.0
```

**What it does**:
- Rate is 0 for first 10 seconds
- Jumps to 5 at t=10
- Perfect for: delayed start, external input

**Visual**:
```
Rate
  5 ┼          ┌─────────
    │          │
  0 ┼──────────┘
    └──────┴───┴────> Time
          10   20
```

---

### 12. Complex Combined Function

**📋 Copy-Paste**:
```
min(10, P1) * sigmoid(t, 5, 0.5)
```

**What it does**:
- Product of saturation (capped at 10 or P1) and sigmoid
- Rate starts slow (sigmoid near 0)
- Accelerates (sigmoid rising)
- Saturates when P1 runs low or sigmoid reaches 1
- Perfect for: startup + depletion dynamics

**Another Example**:
```
(2.0 + 3.0 * sigmoid(t, 10, 0.3)) * (P1 / (50 + P1))
```
- Combines sigmoid time-dependent activation
- With Michaelis-Menten substrate dependence
- Very realistic biochemical dynamics!

---

## 🎓 Function Catalog Reference

All functions available in rate expressions:

### Mathematical Functions
```python
math.sin(x)      # Sine
math.cos(x)      # Cosine
math.tan(x)      # Tangent
math.exp(x)      # e^x
math.log(x)      # Natural logarithm
math.sqrt(x)     # Square root
math.pow(x, y)   # x^y
abs(x)           # Absolute value
min(a, b, ...)   # Minimum
max(a, b, ...)   # Maximum
```

### Special Functions (Built-in)
```python
sigmoid(x, midpoint, steepness)
hill(substrate, K, n)
michaelis_menten(substrate, Vmax, Km)
```

### Variables Available
```python
t          # Current simulation time
time       # Alias for t
P1         # Tokens in place with ID=1
P2         # Tokens in place with ID=2
P<N>       # Tokens in place with ID=N
```

---

## 🔧 How to Use

### Step-by-Step:

1. **Select Transition**
   - Right-click transition on canvas
   - Choose "Properties"

2. **Set Transition Type**
   - Change type to: `continuous`

3. **Enter Rate Function**
   - Find the field labeled "Rate Function:" or "Rate:"
   - Copy one of the expressions above
   - Paste into the field

4. **Optional: Set Bounds**
   - `max_rate`: 100.0 (prevents infinite rates)
   - `min_rate`: 0.0 (prevents negative flow)

5. **Save and Simulate**
   - Click "Apply" or "OK"
   - Add transition to analysis panel
   - Run simulation
   - **See your curve!** 📈

---

## 📊 Comparison Table

| Curve Type | Best For | Shape | Example |
|-----------|----------|-------|---------|
| **Sigmoid** | Startup, saturation | S-curve | `sigmoid(t, 10, 0.5)` |
| **Exponential Growth** | Population, compound interest | J-curve | `math.exp(0.1 * t)` |
| **Exponential Decay** | Radioactive, cooldown | Decreasing | `math.exp(-0.1 * t)` |
| **Linear** | Constant change | Straight line | `2.0 * t` |
| **Michaelis-Menten** | Enzymes | Hyperbolic | `michaelis_menten(P1, 10, 5)` |
| **Hill** | Gene regulation | Sharp switch | `hill(P1, 5, 4)` |
| **Oscillating** | Rhythms, cycles | Wave | `5 + 3*math.sin(t)` |
| **Step** | On/off control | Square wave | `5.0 if t<10 else 0.0` |

---

## 🎯 Real-World Examples

### Example 1: Enzyme Reaction with Substrate Depletion
```
Substrate (P1[100]) → [continuous] → Product (P2[0])

Rate function: michaelis_menten(P1, 10, 20)

Result: Classic MM curve, rate decreases as P1 depletes
```

### Example 2: Bacterial Growth with Lag Phase
```
Bacteria (P1[10]) → [continuous] → MoreBacteria (P2[0])

Rate function: P1 * sigmoid(t, 5, 0.5)

Result: Lag phase (0-5s), then exponential growth
```

### Example 3: Drug Metabolism (First-Order)
```
Drug (P1[50]) → [continuous] → Metabolite (P2[0])

Rate function: 0.1 * P1

Result: Exponential decay, classic pharmacokinetics
```

### Example 4: Gene Expression with Activation
```
mRNA (P1[0]) ← [continuous] ← Activator (P2[varying])

Rate function: 10.0 * hill(P2, 5, 3)

Result: Sharp ON/OFF switch based on activator level
```

---

## ⚠️ Common Pitfalls

### 1. Unbounded Exponential Growth
```
❌ BAD:  math.exp(0.5 * t)  # Can reach infinity!
✅ GOOD: min(100, math.exp(0.5 * t))  # Capped at 100
```
**Or** set `max_rate: 100.0` in properties

### 2. Negative Rates
```
❌ BAD:  P1 - 50  # Negative when P1 < 50
✅ GOOD: max(0, P1 - 50)  # Never negative
```
**Or** set `min_rate: 0.0` in properties

### 3. Division by Zero
```
❌ BAD:  P1 / P2  # Error when P2 = 0!
✅ GOOD: P1 / (P2 + 0.01)  # Safe denominator
```

### 4. Wrong Variable Name
```
❌ BAD:  sigmoid(time, 10, 0.5)  # 'time' might not work
✅ GOOD: sigmoid(t, 10, 0.5)  # Always use lowercase 't'
```

### 5. Forgetting Place ID
```
❌ BAD:  0.5 * P_substrate  # Named references don't work
✅ GOOD: 0.5 * P1  # Use numeric IDs (P1, P2, ...)
```

---

## 🔍 Debugging Tips

### Check Your Function in Python Console

Before using in simulation, test it:
```python
import math

# Test sigmoid
t = 10
result = 1 / (1 + math.exp(-0.5 * (t - 10)))
print(result)  # Should be ~0.5 at midpoint
```

### Enable Debug Logging

In continuous_behavior.py, set:
```python
DEBUG_RATE_EVAL = True
```
Then watch console for rate values during simulation.

---

## 📚 Further Reading

### Sigmoid Function Theory
- Logistic function: `f(x) = 1 / (1 + e^(-k(x - x₀)))`
- Used in: neural networks, population dynamics, S-curves

### Hill Equation
- Originally for hemoglobin oxygen binding
- Used in: biochemistry, gene regulation, cooperativity

### Michaelis-Menten Kinetics
- Enzyme kinetics: `v = Vmax[S] / (Km + [S])`
- Used in: biochemistry, pharmacology, catalysis

---

## 🎉 Quick Start

**Want to see a sigmoid NOW?**

1. Create transition (any type)
2. Right-click → Properties
3. Change to `continuous`
4. Paste: `sigmoid(t, 10, 0.5)`
5. Click OK
6. Add to analysis panel
7. Run simulation for 20+ seconds
8. **Enjoy your S-curve!** 🎊

---

## 💡 Pro Tips

### Tip 1: Scale Output
Sigmoid outputs 0-1, but you want 0-10?
```
10.0 * sigmoid(t, 10, 0.5)  # Scales to 0-10
```

### Tip 2: Shift Midpoint
Want sigmoid centered at t=5 instead of t=10?
```
sigmoid(t, 5, 0.5)  # Just change second parameter
```

### Tip 3: Combine Effects
Product of time activation × substrate availability:
```
sigmoid(t, 5, 1.0) * michaelis_menten(P1, 10, 20)
```

### Tip 4: Use Parentheses
Complex expressions need grouping:
```
(2.0 + 3.0 * sigmoid(t, 10, 0.5)) * (P1 / (P1 + 50))
```

### Tip 5: Test with Constants First
Before using places, verify with constants:
```
sigmoid(t, 10, 0.5)  # Works!
Then: sigmoid(P1, 50, 0.1)  # Add complexity
```

---

## ✨ Summary

Most useful functions:
1. **`sigmoid(t, 10, 0.5)`** - S-curve startup
2. **`0.5 * P1`** - First-order kinetics
3. **`michaelis_menten(P1, 10, 5)`** - Enzyme saturation
4. **`math.exp(-0.1 * t)`** - Exponential decay

**Copy, paste, simulate!** 🚀
