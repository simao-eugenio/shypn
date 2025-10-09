# Quick Reference Card - Transitions & Arcs

**One-page guide for common configurations**

---

## 🎯 Transition Types Quick Select

| I Want To... | Use This Type | Set These Properties |
|--------------|---------------|---------------------|
| Fire instantly | **Immediate** | *(no properties needed)* |
| Fire after delay | **Timed** | `earliest` = min delay<br>`latest` = max delay |
| Fire randomly | **Stochastic** | `rate` = λ parameter |
| Flow continuously | **Continuous** | `rate_function` = expression |

---

## 📊 Common Rate Functions (Copy-Paste Ready)

**For Continuous Transitions**

| What You Want | Paste This |
|---------------|------------|
| Constant flow | `5.0` |
| Proportional to place | `0.5 * P1` |
| Capped maximum | `min(10, P1)` |
| Increases over time | `2.0 * t` |
| S-curve growth | `sigmoid(t, 10, 0.5)` |
| Exponential growth | `math.exp(0.1 * t)` |
| Exponential decay | `math.exp(-0.1 * t)` |
| Enzyme kinetics | `michaelis_menten(P1, vmax=10, km=5)` |
| Cooperativity | `hill_equation(P1, vmax=10, kd=5, n=2)` |

**Variables available**: `P1`, `P2`, ... (place names), `t` (time)

---

## 🚦 Common Guard Functions (Copy-Paste Ready)

**For Conditional Enablement**

| Condition | Paste This |
|-----------|------------|
| Place has enough tokens | `P1 > 5` |
| Multiple conditions | `P1 >= 2 and P2 > 0` |
| After time passes | `t > 10` |
| Time window | `t >= 5 and t <= 15` |
| Token + time | `P1 > 0 and t > 5` |
| Ratio check | `P1 / P2 > 0.5 if P2 > 0 else False` |
| Sum constraint | `P1 + P2 < 10` |

---

## ⚖️ Arc Weight Options

| Method | When to Use | Example |
|--------|-------------|---------|
| **Simple Number** | Fixed weight | `weight = 5` |
| **Expression** | Dynamic based on places | `threshold = "P1.tokens * 0.3"` |
| **Function** | Complex logic | `threshold = lambda arc, mgr: ...` |

**Important**: `threshold` OVERRIDES `weight` for enablement checking!

---

## 🔧 How to Configure

### Step 1: Select Object
- **Single click** to select
- Or **Ctrl+Click** to multi-select

### Step 2: Open Properties
- **Right-click** → "Properties"
- Or **Double-click** object

### Step 3: Set Properties
**In the dialog:**
1. **Transition Type** dropdown → Select type
2. **Guard Function** field → Enter condition (optional)
3. **Rate Function** field → Enter formula (Continuous only)
4. **Earliest/Latest** fields → Enter delays (Timed only)
5. **Rate** field → Enter λ value (Stochastic only)

### Step 4: Save
Click **OK** to apply changes

---

## 🎨 Editing Tips

### Resize Objects
1. **Double-click** to enter edit mode
2. **Drag handles** to resize
   - Places: All handles change radius
   - Transitions: Edge=1D, Corner=2D

### Exit Edit Mode
- **Single click** outside object
- Or press **Escape**

---

## 📚 Full Documentation

| Topic | File |
|-------|------|
| All transition types | `TRANSITION_BEHAVIORS_SUMMARY.md` |
| Arc thresholds | `ARC_THRESHOLD_SYSTEM.md` |
| Guard functions | `GUARD_FUNCTION_GUIDE.md` |
| Rate functions | `RATE_FUNCTION_EXAMPLES.md` |
| Timed behavior | `TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md` |
| Math formulas | `FORMAL_TRANSITION_TYPES_COMPARISON.md` |

All files in: `doc/behaviors/`

---

## 🚀 Quick Examples

### Example 1: Manufacturing with Delay
```
Transition type: Timed
Earliest: 5.0
Latest: 7.0
→ Parts take 5-7 seconds to manufacture
```

### Example 2: Random Customer Arrivals
```
Transition type: Stochastic
Rate: 0.5
→ Average 0.5 customers/second (1 every 2 seconds)
```

### Example 3: Population Growth
```
Transition type: Continuous
Rate function: sigmoid(t, 10, 0.5) * Population
→ S-curve growth proportional to population
```

### Example 4: Conditional Processing
```
Guard function: P1 > 10 and t > 5
→ Fire only after time 5 AND when P1 has >10 tokens
```

### Example 5: Dynamic Arc Weight
```
Arc threshold: P1.tokens * 0.3
→ Requires 30% of P1's current token count
```

---

**Print this page for quick reference!**
