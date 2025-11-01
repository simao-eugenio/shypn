# Inhibitor Arc Behavior: Canonical vs SHYPN Implementation

## Current Status: CANONICAL (Read-Only) Implementation ✓

After code analysis, **SHYPN currently uses CANONICAL inhibitor semantics**, not the living systems semantics described in some documentation.

### Actual Implementation

```python
# In immediate_behavior.py line 140:
for arc in input_arcs:
    # Skip inhibitor arcs (they don't consume)
    kind = getattr(arc, 'kind', ...)
    if kind != 'normal':
        continue  # Inhibitor arcs are skipped for token consumption
```

**Result:** Inhibitor arcs DO NOT consume tokens (read-only, like test arcs)

## Comparison: Three Semantics

### 1. Classical Petri Net (Manufacturing)
**Logic:** Enable when tokens **< threshold** (absence detection)
```
if tokens < weight:
    enabled = True  # Fire when resource is LOW
consumption = 0     # Never consumes
```

**Use Case:** Manufacturing - disable process when material present
**Example:** "Stop conveyor when bin is full"

---

### 2. Canonical Petri Net (Standard)
**Logic:** Enable when tokens **≥ threshold** (presence detection)
```
if tokens >= weight:
    enabled = True  # Fire when resource is PRESENT
consumption = 0     # Never consumes (read-only)
```

**Use Case:** Standard inhibitor - check condition without consuming
**Example:** "Process data only when buffer has ≥ 10 items" (buffer unchanged)

**✓ THIS IS WHAT SHYPN CURRENTLY IMPLEMENTS**

---

### 3. Living Systems / Cooperation (Proposed)
**Logic:** Enable when tokens **> threshold** (strict surplus)
```
if tokens > weight:
    enabled = True  # Fire when surplus EXISTS
consumption = weight  # YES, consumes tokens
```

**Use Case:** Biological cooperation - share only when surplus exists
**Example:** "Cell exports nutrients only when reserves > 5" (reserves decrease)

---

## Biological Analogy: Protein Active Sites

### Allosteric Regulation Comparison

| Protein Mechanism | Petri Net Arc | Behavior |
|-------------------|---------------|----------|
| **Allosteric Activator** | Test Arc | Binds without being consumed, enables reaction |
| **Allosteric Inhibitor (Negative Feedback)** | Inhibitor Arc (Canonical) | Binds without being consumed, checks threshold |
| **Substrate Consumption** | Normal Arc | Consumed during reaction |
| **Cofactor Consumption** | Normal Arc | Consumed and must be regenerated |

### Protein Active Site Activation/Deactivation

#### Case 1: Enzyme Activation by Cofactor (Test Arc)
```
ATP (cofactor) --[test, w=1]--> Kinase_Active
                                    ↓
                             Phosphorylation

Behavior:
- ATP must be present (>= 1 molecule)
- ATP is NOT consumed (acts as activator)
- Kinase fires repeatedly while ATP present
- Like allosteric activator binding
```

**Biological Reality:** Some cofactors are consumed, some are not. Test arcs model non-consumed cofactors (e.g., Mg²⁺ in many enzymes).

#### Case 2: Feedback Inhibition (Inhibitor Arc - Canonical)
```
Product --[inhibitor, w=10]--> Enzyme_Pathway
                                    ↓
                            (pathway blocked)

Behavior:
- When Product >= 10, enzyme is INACTIVE
- Product is NOT consumed by this check
- Classic negative feedback
- Like competitive inhibitor occupying active site
```

**Biological Reality:** End product accumulation blocks enzyme without being consumed by the blocking mechanism itself.

#### Case 3: Substrate Competition (Normal Arc)
```
Substrate_A --[normal, w=1]--> Enzyme → Product_A
Substrate_B --[normal, w=1]--> Enzyme → Product_B

Behavior:
- Each substrate consumed during reaction
- Enzyme can process either substrate
- Direct consumption model
```

**Biological Reality:** Most enzyme reactions consume substrates.

---

## Why Inhibitor ≠ Test Arc?

### Semantic Differences

**Test Arc (Catalyst/Cofactor):**
- **Purpose**: Check condition, enable reaction
- **Enablement**: tokens **≥** weight
- **Biological**: Non-consumed cofactors, allosteric activators
- **Example**: Mg²⁺ in DNA polymerase

**Inhibitor Arc (Negative Feedback):**
- **Purpose**: Check threshold, disable when exceeded
- **Enablement**: tokens **≥** weight (canonical) or **>** weight (living systems)
- **Biological**: Product inhibition, competitive inhibitors
- **Example**: ATP inhibiting glycolysis

### Key Distinction
- **Test arc**: "Fire BECAUSE resource is present"
- **Inhibitor arc**: "Fire ONLY IF resource is present" (threshold check)

In proteins:
- **Activator binding**: Lowers activation energy → test arc
- **Inhibitor binding**: Raises threshold for activity → inhibitor arc

---

## Analysis of Interactive.shy Model

### Current Structure
```
T11 (timed source) → P5 --[inhibitor, w=5]--> T9 → P2
                                rate: 1.0 * (1 - P2/10)
```

### Behavior with Canonical Semantics (Current)
1. T11 fires periodically, adds 1 token to P5
2. When P5 ≥ 5: T9 enabled (can produce to P2)
3. When P5 < 5: T9 disabled
4. **P5 never consumed** - just accumulates
5. T9 produces to P2 continuously (rate-limited by P2 level)

### Biological Interpretation
**This models regulatory threshold without consumption:**
- P5 = Regulatory molecule concentration
- T9 = Metabolic pathway
- Pathway active only when regulator ≥ 5 units
- Regulator itself not consumed by activation check

**Example:** cAMP activating PKA:
- cAMP accumulates from adenylyl cyclase
- When cAMP ≥ threshold, PKA active
- PKA activity doesn't consume cAMP
- cAMP degraded by separate pathway (phosphodiesterase)

### Why No Reserve Behavior?
Because inhibitor arc **doesn't consume**! The "reserve" concept only applies if the arc consumes tokens:
- **With consumption**: Must keep reserve (weight) → need strict surplus (>)
- **Without consumption**: No reserve needed → presence check (≥)

---

## Protein Activation States: Detailed Analysis

### 1. Reversible Activation (Non-Consuming)

**Biological Example:** Calmodulin-activated enzymes
```
Ca²⁺ --[test, w=4]--> Calmodulin → Activated_Enzyme

Behavior:
- 4 Ca²⁺ ions bind to calmodulin
- Calmodulin changes conformation
- Enzyme activated while Ca²⁺ bound
- Ca²⁺ NOT consumed (reversible binding)
- When Ca²⁺ unbinds, enzyme deactivates
```

**Petri Net Model:**
```
Calcium(10) --[test, w=4]--> Activate_CaM_Kinase
                                    ↓
                            Phosphorylate_Target

Model semantics:
- Test arc: Calcium present but not consumed
- Activation reversible
- Enzyme active only while Ca²⁺ > 4
```

### 2. Threshold-Based Activation (Inhibitor Arc)

**Biological Example:** Quorum sensing in bacteria
```
Autoinducer --[inhibitor, w=100]--> Virulence_Genes
                                            ↓
                                    Toxin_Production

Behavior:
- Bacteria produce autoinducer continuously
- When population density high (autoinducer ≥ 100), genes activate
- Autoinducer NOT consumed by sensing
- Threshold detection, not substrate consumption
```

**Petri Net Model:**
```
Autoinducer(0→150) --[inhibitor, w=100]--> Express_Toxins
                                                    ↓
                                            Toxin(accumulating)

Model semantics:
- Inhibitor checks threshold (≥ 100)
- No consumption of autoinducer
- Population-level coordination
- "Critical mass" activation
```

### 3. Substrate Consumption (Normal Arc)

**Biological Example:** ATP hydrolysis
```
ATP --[normal, w=1]--> ATPase → ADP + Pi + Energy

Behavior:
- ATP consumed during reaction
- Energy released
- ADP produced
- Irreversible consumption
```

**Petri Net Model:**
```
ATP(50) --[normal, w=1]--> Hydrolyze → ADP(50) + Energy(50)

Model semantics:
- Normal arc: direct consumption
- Each firing: ATP decreases, products increase
- Conservation of mass
```

---

## Recommendation for Interactive.shy

### Current Model Intent
Based on the structure, the model appears to demonstrate:
1. **Threshold-based activation** (inhibitor arc)
2. **Continuous production** (T9 continuous transition)
3. **Negative feedback** (rate decreases as P2 increases)

### If You Want Consumption from P5
Add a normal arc:
```
P5 --[inhibitor, w=5]--> T9 → P2
   --[normal, w=1]------>
```

Now:
- Inhibitor: Checks P5 ≥ 5 (threshold)
- Normal: Consumes 1 from P5 (depletion)
- Result: P5 oscillates between 5-6 tokens

### If You Want Pure Threshold (Current)
Keep as is:
```
P5 --[inhibitor, w=5]--> T9 → P2
```

Result:
- P5 accumulates until ≥ 5
- T9 activates and stays active
- P5 continues accumulating (no consumption)
- Models regulatory switch

---

## Protein Active Site Summary

| Mechanism | Arc Type | Consumption | Biological Example |
|-----------|----------|-------------|--------------------|
| **Allosteric Activation** | Test | No | Ca²⁺ + Calmodulin |
| **Cofactor Requirement** | Test | No | Mg²⁺ in polymerase |
| **Feedback Inhibition** | Inhibitor | No | ATP inhibiting PFK |
| **Quorum Sensing** | Inhibitor | No | Autoinducer threshold |
| **Substrate Processing** | Normal | Yes | ATP → ADP + Pi |
| **Competitive Inhibition** | Inhibitor | No* | Product blocking enzyme |

*Competitive inhibitor consumed separately, not by inhibition check itself

### Activation vs Inhibition

**Activation (Test Arc):**
- Lowers energy barrier
- Enables reaction
- "Green light" signal
- Example: Kinase activation by cAMP

**Inhibition (Inhibitor Arc):**
- Requires threshold to be OFF
- Prevents reaction below threshold
- "Minimum required" signal
- Example: Cell cycle checkpoint (wait for all conditions)

**Both are non-consuming checks in canonical semantics!**

---

## Conclusion

### Current SHYPN Behavior
**Inhibitor arcs use CANONICAL semantics:**
- Enable when tokens ≥ weight
- Do NOT consume tokens
- Check threshold without depletion
- Equivalent to regulatory threshold detection

### Biological Mapping
This correctly models:
- ✓ Allosteric regulation (binding without consumption)
- ✓ Threshold-based activation (quorum sensing)
- ✓ Feedback inhibition (product accumulation)
- ✓ Checkpoint mechanisms (all conditions met)

### What It Doesn't Model
- ✗ Resource sharing with starvation prevention
- ✗ Cooperation with consumption
- ✗ Token depletion with reserves

For those behaviors, use **normal arcs with explicit reserve modeling**.

---

## Implementation Status

- ✅ **Canonical semantics**: Currently implemented (read-only)
- ✅ **Enablement logic**: tokens > weight (strict surplus check added)
- ✅ **No consumption**: Matches biological threshold detection
- ⏳ **Living systems semantics**: Documented but not implemented
- ⏳ **Consumption toggle**: Could add as optional behavior

## Next Steps (If Consumption Desired)

1. Add `consumes_tokens()` method to InhibitorArc
2. Make consumption optional via property
3. Update behavior classes to handle inhibitor consumption
4. Document two modes: threshold-only vs cooperation

For now, **current implementation is biologically correct** for threshold-based regulation!
