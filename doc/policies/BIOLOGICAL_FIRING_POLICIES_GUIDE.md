# Firing Policies for Biological Modeling

## Overview

Firing policies control **which transition fires** when multiple transitions compete for the same resources (shared input places). This guide explains when each policy is biologically appropriate.

---

## Policy Classification

### **Stochastic Policies** (Biologically Realistic for Molecular Systems)

Represent random molecular events and kinetic competition.

#### 🧬 **race** (Default - RECOMMENDED)

**Biological Meaning:** Mass action kinetics - reactions compete based on their rates.

**Mathematical Model:**
```
Probability(transition fires) ∝ exp(-delay/rate)
delay ~ Exponential(rate)
```

**When to Use:**
- ✅ Metabolic pathway branch points
- ✅ Competitive enzyme-substrate binding
- ✅ Multiple reactions consuming the same metabolite
- ✅ Enzymatic reactions with known kinetic parameters (Vmax, Km)

**Example - Glycolysis vs Pentose Phosphate Pathway:**
```
Glucose-6-P (P1)
    ↓ (T1: PFK - Glycolysis, Vmax=70, Km=0.1)
    ↓ (T2: G6PD - Pentose Phosphate, Vmax=49, Km=0.15)
    
firing_policy = 'race'
Result: T1 fires ~60% of time (proportional to rates)
```

**Biological Justification:**
- Matches Gillespie algorithm (gold standard for stochastic biochemical simulation)
- Rate-weighted probability reflects molecular collision frequencies
- Faster reactions (higher kcat) dominate naturally

---

#### 🎲 **random** (Uniform Stochastic)

**Biological Meaning:** All transitions have equal probability, regardless of rates.

**Mathematical Model:**
```
Probability(transition fires) = 1 / N_enabled
```

**When to Use:**
- ⚠️ When reaction rates are unknown or equal
- ⚠️ For exploratory modeling (test all possibilities)
- ⚠️ When modeling inherent biological noise without rate preferences

**Example - Protein Degradation Pathways:**
```
Misfolded Protein (P1)
    ↓ (T1: Proteasome pathway)
    ↓ (T2: Autophagy pathway)
    
If rates unknown: firing_policy = 'random'
Result: 50/50 split
```

**Limitations:**
- Does NOT reflect kinetic reality (all reactions rarely have equal rates)
- Use `race` with equal rates if you want stochastic but rate-agnostic behavior

---

### **Priority-Based Policies** (Regulatory Hierarchies)

Represent cellular control mechanisms that override kinetics.

#### ⚖️ **priority** (Hierarchical Control)

**Biological Meaning:** Regulatory mechanisms enforce precedence - higher priority always wins.

**Mathematical Model:**
```
Winner = max(transitions, key=priority)
Deterministic outcome
```

**When to Use:**
- ✅ Gene regulatory networks (master regulators > downstream genes)
- ✅ Cell cycle checkpoints (mandatory order enforcement)
- ✅ Metabolic switches (glucose repression, catabolite repression)
- ✅ Stress responses (DNA damage repair > normal replication)

**Example - Lac Operon Glucose Repression:**
```
cAMP-CAP (P1)
    ↓ (T1: Glucose metabolism, priority=10)
    ↓ (T2: Lactose metabolism, priority=5)
    
firing_policy = 'priority'
Result: Glucose pathway ALWAYS preferred (catabolite repression)
```

**Biological Justification:**
- Models transcriptional regulation hierarchies
- Represents allosteric control mechanisms
- Captures checkpoint enforcement (e.g., spindle assembly checkpoint)

**Warning:**
- ❌ Does NOT model kinetic competition (ignores rates)
- ❌ Deterministic - loses stochastic molecular behavior
- Use only when regulation truly overrides kinetics

---

#### 🚨 **preemptive-priority** (Emergency Override)

**Biological Meaning:** High-priority transitions can interrupt running low-priority processes.

**Mathematical Model:**
```
If high_priority enabled WHILE low_priority running:
    → Stop low_priority
    → Start high_priority
```

**When to Use:**
- ✅ Apoptosis signals interrupting growth
- ✅ DNA damage response preempting replication
- ✅ Stress responses halting normal metabolism
- ✅ Emergency shutdown pathways

**Example - Apoptosis Overriding Cell Division:**
```
Cell State (P1)
    ↓ (T1: Cell division, priority=5, running)
    ↓ (T2: Apoptosis signal, priority=10, becomes enabled)
    
firing_policy = 'preemptive-priority'
Result: T2 interrupts T1 mid-execution
```

**Current Status:**
- ⚠️ Partially implemented (treats as priority without interruption)
- TODO: Full preemption requires interrupt mechanism

---

### **Temporal Policies** (Ordered Processes)

Based on enablement timing, not rates or regulation.

#### ⏰ **earliest** (First-In-First-Out, FIFO)

**Biological Meaning:** Transition enabled first fires first.

**When to Use:**
- ⚠️ Sequential assembly processes (e.g., ribosome subunit joining)
- ⚠️ Ordered activation cascades (e.g., coagulation cascade)
- ⚠️ Queue-like cellular processes

**Example - Ribosomal Subunit Assembly:**
```
rRNA + Proteins (P1)
    ↓ (T1: Small subunit assembly, enabled at t=0)
    ↓ (T2: Large subunit assembly, enabled at t=5)
    
firing_policy = 'earliest'
Result: T1 fires first (temporal order)
```

**Limitations:**
- ❌ Ignores kinetic rates
- ❌ Rarely reflects enzymatic competition
- Use only for truly ordered biological processes

---

#### ⏱️ **latest** (Last-In-First-Out, LIFO)

**Biological Meaning:** Most recently enabled transition fires first.

**When to Use:**
- ⚠️ LIFO queue behaviors (very rare in biology)
- ⚠️ Last signal overrides earlier signals

**Biological Justification:**
- Rarely applicable to biochemical systems
- Consider if most recent signal should dominate

---

#### 📅 **age** (Same as earliest)

**Biological Meaning:** Oldest enabled transition fires (FIFO).

**Implementation:**
- Identical to `earliest` policy
- Provided for semantic clarity

---

## Recommended Defaults by System Type

| System Type | Recommended Policy | Priority | Rationale |
|-------------|-------------------|----------|-----------|
| **Metabolic Pathways** | `race` | ⭐⭐⭐⭐⭐ | Kinetic competition |
| **Enzyme Kinetics** | `race` | ⭐⭐⭐⭐⭐ | Mass action |
| **Gene Regulation** | `priority` | ⭐⭐⭐⭐ | Hierarchical control |
| **Signal Transduction** | `earliest` or `race` | ⭐⭐⭐ | Fast propagation |
| **Stochastic Expression** | `random` or `race` | ⭐⭐⭐ | Molecular noise |
| **Cell Cycle** | `priority` or `age` | ⭐⭐⭐ | Checkpoint order |
| **Stress Response** | `preemptive-priority` | ⭐⭐⭐⭐ | Emergency override |
| **General/Unknown** | `race` | ⭐⭐⭐⭐ | Safe default |

---

## Implementation Details

### How Policies Integrate with Simulation

All transition types now use firing policies:

```python
# Immediate transitions
if multiple_immediate_enabled:
    winner = _select_transition(enabled, policy)
    
# Timed transitions  
if multiple_timed_enabled:
    winner = _select_transition(enabled, policy)
    
# Stochastic transitions
if multiple_stochastic_enabled:
    winner = _select_transition(enabled, policy)
    
# Continuous transitions (NEW!)
if multiple_continuous_conflict:
    winner = _select_transition(conflict_group, policy)
```

### Continuous Transition Conflict Resolution

**Key Innovation:** Continuous transitions now participate in conflict resolution.

**Before (incorrect):**
```python
# All continuous transitions integrated simultaneously
for t in continuous_enabled:
    t.integrate_step(dt)  # No conflict checking
```

**After (correct):**
```python
# Detect conflicts (shared input places)
conflict_groups = find_conflicts(continuous_enabled)

# Resolve each conflict using firing policy
for group in conflict_groups:
    winner = select_transition(group, policy)
    winner.integrate_step(dt)  # Only winner integrates

# Non-conflicting transitions execute in parallel
for t in non_conflicting:
    t.integrate_step(dt)
```

---

## Configuration

### Setting Default Policy

**Global Default:**
```python
# In transition.py
self.firing_policy = 'race'  # Changed from 'random' to 'race'
```

**Per-Transition Override:**
```json
{
  "id": "T3",
  "firing_policy": "priority",
  "priority": 10
}
```

**UI:**
- Properties dialog → Firing Policy dropdown
- Priority Value field (visible when policy = "priority" or "preemptive-priority")

---

## Examples from Real Systems

### Example 1: Glycolysis Branch Point

**System:** Glucose-6-Phosphate can enter glycolysis OR pentose phosphate pathway

```json
{
  "T1_glycolysis": {
    "label": "PFK (Glycolysis)",
    "firing_policy": "race",
    "rate_function": "michaelis_menten(P1, vmax=70, km=0.1)"
  },
  "T2_pentose": {
    "label": "G6PD (Pentose Phosphate)",
    "firing_policy": "race",
    "rate_function": "michaelis_menten(P1, vmax=49, km=0.15)"
  }
}
```

**Result:** Rate-weighted stochastic branching (70/(70+49) ≈ 59% glycolysis)

---

### Example 2: Lac Operon Regulation

**System:** Glucose represses lactose metabolism

```json
{
  "T1_glucose_metabolism": {
    "label": "Glucose pathway",
    "firing_policy": "priority",
    "priority": 10
  },
  "T2_lactose_metabolism": {
    "label": "Lac operon expression",
    "firing_policy": "priority",
    "priority": 5
  }
}
```

**Result:** Glucose pathway always preferred (catabolite repression)

---

### Example 3: Apoptosis Override

**System:** Death signal preempts cell division

```json
{
  "T1_cell_division": {
    "label": "Mitosis progression",
    "firing_policy": "preemptive-priority",
    "priority": 5
  },
  "T2_apoptosis": {
    "label": "Apoptosis initiation",
    "firing_policy": "preemptive-priority",
    "priority": 10
  }
}
```

**Result:** Apoptosis interrupts division when triggered

---

## Policy Selection Decision Tree

```
Is this a kinetic competition between enzymes?
├─ YES → Use 'race' (rate-weighted stochastic)
└─ NO
   ├─ Is there regulatory hierarchy?
   │  ├─ YES → Use 'priority' (deterministic control)
   │  │  └─ Can it interrupt? → Use 'preemptive-priority'
   │  └─ NO
   │     ├─ Must it be ordered?
   │     │  ├─ YES → Use 'earliest' (FIFO)
   │     │  └─ NO → Use 'random' (uniform stochastic)
   │     └─ Unknown/exploratory? → Use 'race' (safe default)
```

---

## References

1. **Gillespie Algorithm:** Gillespie, D.T. (1977). "Exact stochastic simulation of coupled chemical reactions"
2. **Mass Action Kinetics:** Guldberg, C.M. & Waage, P. (1864). "Studies Concerning Affinity"
3. **Stochastic Petri Nets:** Marsan, M.A. et al. (1995). "Modelling with Generalized Stochastic Petri Nets"
4. **Systems Biology:** Kitano, H. (2002). "Systems Biology: A Brief Overview"

---

## Version History

- **2025-11-16:** Initial documentation
  - Added conflict resolution for continuous transitions
  - Changed default from `random` to `race`
  - Unified scheduler across all transition types

---

## See Also

- `doc/FIRING_POLICIES.md` - Technical specification
- `src/shypn/engine/simulation/controller.py` - Scheduler implementation
- `src/shypn/engine/continuous_behavior.py` - Continuous integration
