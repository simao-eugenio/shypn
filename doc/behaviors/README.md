# Transition and Arc Behaviors - User Documentation

This directory contains **user-facing guides** for understanding and configuring transition behaviors, arc thresholds, guard functions, and rate functions in SHYPN.

---

## 📚 Quick Navigation

### 🎯 Getting Started

**New to SHYPN?** Start here:

1. **[Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md)** - Overview of all 4 transition types
2. **[Transformation Handlers Usage Guide](TRANSFORMATION_HANDLERS_USAGE_GUIDE.md)** - How to resize and edit objects

### 🔧 Configuration Guides

**How to configure specific features:**

| Feature | Guide | What You'll Learn |
|---------|-------|-------------------|
| **Arc Weights & Thresholds** | [Arc Threshold System](ARC_THRESHOLD_SYSTEM.md) | How to set simple weights, expressions, and functions for arcs |
| **Guard Functions** | [Guard Function Guide](GUARD_FUNCTION_GUIDE.md) | How to add enable/disable conditions to transitions |
| **Rate Functions** | [Rate Function Examples](RATE_FUNCTION_EXAMPLES.md) | Copy-paste formulas for continuous transitions |
| **Timed Transitions** | [Timed Transition Behavior](TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md) | Understanding timing windows and delays |

### 📖 Reference Documentation

**Deep dives and formal definitions:**

| Document | Purpose |
|----------|---------|
| [Formal Transition Types Comparison](FORMAL_TRANSITION_TYPES_COMPARISON.md) | Mathematical definitions and theory |

---

## 🎓 Learning Paths

### Path 1: Basic Petri Nets (Discrete Models)

**Goal**: Create simple token-based models

1. Read: [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) → Section 1.1 (Immediate Behavior)
2. Learn: [Arc Threshold System](ARC_THRESHOLD_SYSTEM.md) → "Simple Numeric" section
3. Practice: Create a model with immediate transitions and fixed arc weights

**Skills gained**: Basic place-transition nets, token flow, structural enablement

---

### Path 2: Timed Models

**Goal**: Add time constraints to transitions

1. Read: [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) → Section 1.2 (Timed Behavior)
2. Deep dive: [Timed Transition Behavior Explained](TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md)
3. Learn: How to set `earliest` and `latest` properties
4. Practice: Create a model with timed transitions (e.g., manufacturing process)

**Skills gained**: Time Petri nets, timing windows, deterministic delays

---

### Path 3: Stochastic Models

**Goal**: Model probabilistic behavior

1. Read: [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) → Section 1.3 (Stochastic Behavior)
2. Learn: How to set `rate` property (λ parameter)
3. Understand: Exponential distributions and random delays
4. Practice: Create a model with stochastic transitions (e.g., queueing systems)

**Skills gained**: Stochastic Petri nets, probabilistic modeling, statistical analysis

---

### Path 4: Continuous Models

**Goal**: Model fluid-like systems

1. Read: [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) → Section 1.4 (Continuous Behavior)
2. Study: [Rate Function Examples](RATE_FUNCTION_EXAMPLES.md) - all sections
3. Learn: How to write rate function expressions
4. Practice: Create a model with continuous transitions (e.g., chemical reactions, population dynamics)

**Skills gained**: Continuous Petri nets, rate functions, differential equations, Michaelis-Menten kinetics

---

### Path 5: Advanced Features

**Goal**: Use guards, thresholds, and complex formulas

1. Read: [Guard Function Guide](GUARD_FUNCTION_GUIDE.md)
2. Study: [Arc Threshold System](ARC_THRESHOLD_SYSTEM.md) - "Expression" and "Function" sections
3. Learn: How to write Python expressions for dynamic behavior
4. Practice: Create a model with guards, dynamic thresholds, and complex rate functions

**Skills gained**: Conditional enablement, dynamic cooperation, adaptive systems

---

## 📋 Feature Reference

### Arc Weight Specification

**File**: [ARC_THRESHOLD_SYSTEM.md](ARC_THRESHOLD_SYSTEM.md)

**Methods**:
1. **Simple Numeric** - Fixed integer weights (e.g., `5`)
2. **Expression** - Dynamic formulas (e.g., `"P1.tokens * 0.3"`)
3. **Function** - Python callables (e.g., `lambda arc, manager: ...`)

**When to use**:
- Simple: Most basic models
- Expression: Context-dependent cooperation (e.g., "need 30% of P1's tokens")
- Function: Complex computational logic

---

### Guard Functions

**File**: [GUARD_FUNCTION_GUIDE.md](GUARD_FUNCTION_GUIDE.md)

**Types**:
1. **Boolean** - Direct True/False
2. **Numeric Threshold** - Value > 0 passes
3. **Expression** - String evaluated (e.g., `"P1 > 5 and t > 10"`)
4. **Function** - Python callable

**Common use cases**:
- Token-based: `"P1 > 5"` (fire only when place has enough tokens)
- Time-based: `"t > 10"` (fire only after time passes)
- Combined: `"P1 > 0 and t > 5"` (both conditions)
- Ratio: `"P1 / P2 > 0.5"` (proportional condition)

---

### Rate Functions

**File**: [RATE_FUNCTION_EXAMPLES.md](RATE_FUNCTION_EXAMPLES.md)

**Categories**:
1. **Constant** - Fixed rate (e.g., `5.0`)
2. **Linear** - Proportional to places (e.g., `0.5 * P1`)
3. **Saturated** - Capped maximum (e.g., `min(10, P1)`)
4. **Time-dependent** - Changes over time (e.g., `2.0 * t`)
5. **Sigmoid** - S-curve growth (e.g., `sigmoid(t, 10, 0.5)`)
6. **Exponential** - Growth/decay (e.g., `math.exp(0.1 * t)`)
7. **Michaelis-Menten** - Enzyme kinetics (e.g., `michaelis_menten(P1, 10, 5)`)
8. **Hill** - Cooperativity (e.g., `hill(P1, 5, 2)`)

**Ready-to-use examples**: All functions in the guide are copy-paste ready!

---

### Transition Types

**File**: [TRANSITION_BEHAVIORS_SUMMARY.md](TRANSITION_BEHAVIORS_SUMMARY.md)

| Type | Time Model | When Fires | Use Case |
|------|------------|------------|----------|
| **Immediate** | Zero delay | Instantly when enabled | Default, simple logic |
| **Timed** | Deterministic delay | After [earliest, latest] window | Manufacturing, scheduling |
| **Stochastic** | Random delay | After exponential delay | Queueing, random events |
| **Continuous** | Continuous flow | Flows while enabled | Chemical reactions, populations |

---

## 🔍 How to Find What You Need

### "How do I...?"

| Question | Answer |
|----------|--------|
| **"How do I make a transition fire only when a place has > 5 tokens?"** | Use a **guard function**: `"P1 > 5"` → [Guard Function Guide](GUARD_FUNCTION_GUIDE.md) |
| **"How do I make an arc require 30% of a place's tokens?"** | Use **threshold expression**: `"P1.tokens * 0.3"` → [Arc Threshold System](ARC_THRESHOLD_SYSTEM.md) |
| **"How do I model exponential growth?"** | Use **rate function**: `math.exp(0.1 * t)` → [Rate Function Examples](RATE_FUNCTION_EXAMPLES.md) |
| **"How do I add a time delay to a transition?"** | Set **transition type to Timed** and set `earliest`/`latest` → [Timed Transition Behavior](TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md) |
| **"How do I make a transition fire randomly?"** | Set **transition type to Stochastic** and set `rate` → [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) |
| **"How do I model continuous flow?"** | Set **transition type to Continuous** and set `rate_function` → [Rate Function Examples](RATE_FUNCTION_EXAMPLES.md) |

---

## 🎨 UI Interaction Guide

**File**: [TRANSFORMATION_HANDLERS_USAGE_GUIDE.md](TRANSFORMATION_HANDLERS_USAGE_GUIDE.md)

### How to Edit Properties

1. **Double-click** a place or transition to enter edit mode
2. **Right-click** → "Properties" to open properties dialog
3. In the dialog:
   - Set **transition type** (Immediate, Timed, Stochastic, Continuous)
   - Enter **guard function** (if needed)
   - Enter **rate function** (for Continuous)
   - Set **earliest/latest** (for Timed)
   - Set **rate** (for Stochastic)

### How to Resize Objects

1. **Double-click** to enter edit mode
2. **Drag handles** to resize:
   - **Places**: All handles change radius uniformly
   - **Transitions**: Edge handles resize one dimension, corner handles resize both

---

## 📚 Additional Resources

### Related Documentation

Outside this directory:
- **Installation**: `doc/INSTALLATION.md`
- **General Usage**: `doc/EDITING_OPERATIONS_PALETTE_GUIDE.md`
- **Undo/Redo**: `doc/UNDO_REDO_DEV_QUICK_REFERENCE.md`
- **File Operations**: `doc/FILE_EXPLORER_RESEARCH.md`

### Developer Documentation

For implementation details:
- **Behavior Classes**: `src/shypn/behaviors/`
- **Simulation Engine**: `src/shypn/simulation/`
- **Property Dialogs**: `ui/dialogs/`

---

## 🚀 Quick Start Examples

### Example 1: Simple Producer-Consumer

```
Model: [Buffer] --1--> (Consumer)
       (Producer) --1--> [Buffer]

Setup:
- Producer: Immediate transition (fires instantly)
- Consumer: Timed transition (earliest=2.0, latest=3.0)
- Buffer: Place with initial tokens=5
- All arcs: weight=1

Behavior:
- Producer fires instantly, adding tokens to Buffer
- Consumer waits 2-3 seconds after enablement, then consumes
```

**Files to read**: 
- [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) sections 1.1 and 1.2

---

### Example 2: Population Growth (Continuous)

```
Model: [Population] --1--> (Growth) --1--> [Population]

Setup:
- Growth: Continuous transition
- Rate function: sigmoid(t, 10, 0.5) * Population
- Initial tokens in Population: 100

Behavior:
- Tokens flow continuously from Population through Growth back to Population
- Flow rate starts slow, accelerates around t=10, then saturates
- Models logistic growth with carrying capacity
```

**Files to read**:
- [Rate Function Examples](RATE_FUNCTION_EXAMPLES.md) → Sigmoid section
- [Transition Behaviors Summary](TRANSITION_BEHAVIORS_SUMMARY.md) → Section 1.4

---

### Example 3: Conditional Firing (Guards)

```
Model: [P1] --1--> (T1) --1--> [P2]
       [P2] --1--> (T2) --1--> [P1]

Setup:
- T1: Guard = "P2 < 10" (fire only if P2 has < 10 tokens)
- T2: Guard = "P1 > 5" (fire only if P1 has > 5 tokens)
- Initial: P1=10, P2=0

Behavior:
- T1 fires, moving tokens from P1 to P2, until P2 reaches 10
- Then T2 fires, moving tokens back, until P1 drops to 5
- System oscillates between states
```

**Files to read**:
- [Guard Function Guide](GUARD_FUNCTION_GUIDE.md) → Expression Guard section

---

## 📞 Support

**Found an issue?** Check existing documentation first:
1. Search this README for keywords
2. Check the specific guide for your feature
3. Review [Formal Transition Types](FORMAL_TRANSITION_TYPES_COMPARISON.md) for theory

**Still stuck?** Look at:
- Example models in `models/` directory
- Test files in `tests/` directory
- Source code in `src/shypn/`

---

## 🗺️ Document Map

```
doc/behaviors/
├── README.md (this file)
│
├── 🎯 Getting Started
│   ├── TRANSITION_BEHAVIORS_SUMMARY.md
│   └── TRANSFORMATION_HANDLERS_USAGE_GUIDE.md
│
├── 🔧 Configuration Guides
│   ├── ARC_THRESHOLD_SYSTEM.md
│   ├── GUARD_FUNCTION_GUIDE.md
│   ├── RATE_FUNCTION_EXAMPLES.md
│   └── TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md
│
└── 📖 Reference
    └── FORMAL_TRANSITION_TYPES_COMPARISON.md
```

---

**Last Updated**: October 7, 2025  
**Maintained by**: SHYPN Development Team
