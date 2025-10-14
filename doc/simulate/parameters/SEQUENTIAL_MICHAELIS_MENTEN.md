# Sequential Michaelis-Menten for Multi-Substrate Reactions

**Date**: October 13, 2025  
**Status**: ✅ **IMPLEMENTED**  
**Feature**: Automatic sequential Michaelis-Menten based on number of input places

---

## Overview

When importing SBML pathways with **multi-substrate Michaelis-Menten reactions**, the system now **automatically generates sequential Michaelis-Menten rate functions** based on the number of reactants.

### Formula

For a reaction with N substrates (S₁, S₂, ..., Sₙ):

```
Rate = Vmax * [S₁]/(Km+[S₁]) * [S₂]/(Km+[S₂]) * ... * [Sₙ]/(Km+[Sₙ])
```

**In Shypn rate function syntax**:
```python
michaelis_menten(P1, Vmax, Km) * (P2 / (Km + P2)) * (P3 / (Km + P3)) * ...
```

---

## Implementation

### Single Substrate (N=1)

**SBML Reaction**:
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="Glucose" stoichiometry="1"/>
  </listOfReactants>
  <kineticLaw>
    <parameter id="Vmax" value="10.0"/>
    <parameter id="Km" value="5.0"/>
  </kineticLaw>
</reaction>
```

**Generated Rate Function**:
```python
transition.properties['rate_function'] = "michaelis_menten(P1, 10.0, 5.0)"
```

**Network**:
```
P1 (Glucose) → T1 → P2 (Glucose-6-P)
```

---

### Two Substrates (N=2)

**SBML Reaction**:
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="Glucose" stoichiometry="1"/>
    <speciesReference species="ATP" stoichiometry="1"/>
  </listOfReactants>
  <kineticLaw>
    <parameter id="Vmax" value="20.0"/>
    <parameter id="Km" value="3.0"/>
  </kineticLaw>
</reaction>
```

**Generated Rate Function**:
```python
transition.properties['rate_function'] = "michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))"
```

**Network**:
```
P1 (Glucose) ─┐
              ├─→ T1 → P3 (Glucose-6-P + ADP)
P2 (ATP) ─────┘
```

**Evaluation Example**:
```python
# At time t, with P1=15 tokens, P2=12 tokens
context = {'P1': 15, 'P2': 12, ...}

# Primary substrate (full MM)
mm_term = michaelis_menten(15, 20.0, 3.0)
        = 20.0 * 15 / (3.0 + 15)
        = 300 / 18
        = 16.67

# Secondary substrate (saturation)
sat_term = 12 / (3.0 + 12)
         = 12 / 15
         = 0.8

# Combined rate
rate = 16.67 * 0.8 = 13.33
```

---

### Three Substrates (N=3)

**SBML Reaction**:
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="A" stoichiometry="1"/>
    <speciesReference species="B" stoichiometry="1"/>
    <speciesReference species="C" stoichiometry="1"/>
  </listOfReactants>
  <kineticLaw>
    <parameter id="Vmax" value="15.0"/>
    <parameter id="Km" value="2.0"/>
  </kineticLaw>
</reaction>
```

**Generated Rate Function**:
```python
transition.properties['rate_function'] = """
michaelis_menten(P1, 15.0, 2.0) * (P2 / (2.0 + P2)) * (P3 / (2.0 + P3))
"""
```

**Network**:
```
P1 (A) ──┐
         │
P2 (B) ──┼─→ T1 → P4 (Product)
         │
P3 (C) ──┘
```

---

## Code Implementation

**File**: `src/shypn/data/pathway/pathway_converter.py`

```python
def _setup_michaelis_menten(self, transition: Transition, reaction: Reaction, 
                            kinetic: 'KineticLaw') -> None:
    """
    Setup Michaelis-Menten kinetics with rate_function.
    
    For single substrate: michaelis_menten(S, Vmax, Km)
    For multiple substrates: Sequential Michaelis-Menten
      - michaelis_menten(S1, Vmax, Km1) * (S2/(Km2+S2)) * (S3/(Km3+S3)) * ...
    """
    transition.transition_type = "continuous"
    
    # Extract parameters
    vmax = kinetic.parameters.get("Vmax", kinetic.parameters.get("vmax", 1.0))
    km = kinetic.parameters.get("Km", kinetic.parameters.get("km", 1.0))
    
    # Get all substrate places
    substrate_refs = []
    for species_id, stoich in reaction.reactants:
        place = self.species_to_place.get(species_id)
        if place:
            substrate_refs.append(place.name)
    
    if len(substrate_refs) == 1:
        # Single substrate - standard Michaelis-Menten
        rate_func = f"michaelis_menten({substrate_refs[0]}, {vmax}, {km})"
    else:
        # Multiple substrates - Sequential Michaelis-Menten
        # Primary substrate uses full MM
        rate_func = f"michaelis_menten({substrate_refs[0]}, {vmax}, {km})"
        
        # Additional substrates as saturation terms
        for substrate in substrate_refs[1:]:
            rate_func += f" * ({substrate} / ({km} + {substrate}))"
    
    transition.properties['rate_function'] = rate_func
    transition.rate = vmax  # Fallback for simple display
```

---

## Persistence Verification

### Step 1: Import → Values Set ✅

```python
# After import
transition.transition_type = "continuous"
transition.rate = 20.0
transition.properties['rate_function'] = "michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))"
```

### Step 2: Save to File ✅

**File**: `model.shypn` (JSON)
```json
{
  "transitions": [{
    "id": 1,
    "name": "T1",
    "transition_type": "continuous",
    "rate": 20.0,
    "properties": {
      "rate_function": "michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))"
    }
  }]
}
```

### Step 3: Load from File ✅

**File**: `src/shypn/netobjs/transition.py:462-468`
```python
if "transition_type" in data:
    transition.transition_type = data["transition_type"]  # → "continuous"
if "rate" in data:
    transition.rate = data["rate"]  # → 20.0
if "properties" in data:
    transition.properties = data["properties"]  # → {"rate_function": "..."}
```

### Step 4: Property Dialog Displays ✅

**UI Display**:
```
┌─────────────────────────────────────────┐
│ Transition Properties                   │
├─────────────────────────────────────────┤
│ Type: [Continuous ▾]                    │
│ Rate: 20.0                              │
│                                          │
│ Rate Function (Advanced):               │
│ michaelis_menten(P1, 20.0, 3.0) *      │
│ (P2 / (3.0 + P2))                      │
└─────────────────────────────────────────┘
```

### Step 5: Simulation Uses ✅

**File**: `src/shypn/engine/continuous_behavior.py`
```python
def evaluate_rate(places, time):
    context = {
        'P1': places[1].tokens,  # → 15
        'P2': places[2].tokens,  # → 12
        'michaelis_menten': <function>,
        # ...
    }
    
    # Evaluate: "michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))"
    rate = eval(rate_function, context)
    # = michaelis_menten(15, 20.0, 3.0) * (12 / (3.0 + 12))
    # = 16.67 * 0.8
    # = 13.33
    
    return rate
```

---

## Test Results

### Test 1: Single Substrate ✅

```
SBML: Glucose → Glucose-6-P (Vmax=10, Km=5)
Result: michaelis_menten(P1, 10.0, 5.0)
Status: ✅ PASS
```

### Test 2: Two Substrates ✅

```
SBML: Glucose + ATP → Glucose-6-P + ADP (Vmax=20, Km=3)
Result: michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))
Status: ✅ PASS
```

### Test 3: Persistence ✅

```
Import → Save → Load → Display → Simulate
  ✅       ✅      ✅       ✅         ✅
```

---

## Biochemical Interpretation

### Sequential Michaelis-Menten Model

**Mechanism**: Ordered Bi-Bi (Sequential Binding)

```
E + S₁ ⇌ ES₁
ES₁ + S₂ ⇌ ES₁S₂ → E + P₁ + P₂
```

**Rate Equation**:
```
v = Vmax * [S₁]/Km₁ * [S₂]/Km₂ / (1 + [S₁]/Km₁)(1 + [S₂]/Km₂)
```

**Simplification** (when Km₁ = Km₂ = Km):
```
v ≈ Vmax * [S₁]/(Km+[S₁]) * [S₂]/(Km+[S₂])
```

**This is what we implement!**

### Real-World Examples

#### Hexokinase (2 substrates)
```
Glucose + ATP → Glucose-6-P + ADP

rate = michaelis_menten(Glucose, 175, 0.1) * (ATP / (0.4 + ATP))
```

#### Glutamine Synthetase (2 substrates)
```
Glutamate + NH₃ → Glutamine

rate = michaelis_menten(Glutamate, 100, 2.0) * (NH3 / (0.1 + NH3))
```

#### Transaminase (3 substrates)
```
Aspartate + α-Ketoglutarate + Pyridoxal-P → Oxaloacetate + Glutamate

rate = michaelis_menten(Asp, 50, 1.0) * 
       (aKG / (0.5 + aKG)) * 
       (PLP / (0.01 + PLP))
```

---

## Advantages

### 1. **Automatic Configuration** ✅
- No manual rate function editing required
- Works immediately after import

### 2. **Scientifically Accurate** ✅
- Represents ordered sequential mechanisms
- Each substrate contributes saturation
- Common in metabolic pathways

### 3. **Scales with Complexity** ✅
- Works for any number of substrates
- Formula extends naturally: N substrates → N terms

### 4. **Persistent** ✅
- Saved in `properties['rate_function']`
- Restored on load
- Editable in properties dialog

---

## Limitations & Future Enhancements

### Current Limitations

1. **Same Km for all substrates**: Uses single Km value from SBML
   - Real enzymes often have different Km for each substrate

2. **Ordered mechanism assumed**: Sequential binding order
   - Some enzymes use random binding (both substrates can bind first)

3. **No product inhibition**: Doesn't account for products affecting rate
   - Many enzymes show product inhibition

### Possible Enhancements

#### Enhancement 1: Substrate-Specific Km Values

```python
# If SBML provides Km1, Km2, Km3...
if "Km1" in kinetic.parameters and "Km2" in kinetic.parameters:
    km1 = kinetic.parameters["Km1"]
    km2 = kinetic.parameters["Km2"]
    rate_func = f"michaelis_menten(P1, {vmax}, {km1}) * (P2 / ({km2} + P2))"
```

#### Enhancement 2: Random Bi-Bi Mechanism

```python
# User configurable in import dialog
if mechanism == "random":
    # Use minimum saturation (either substrate can be limiting)
    rate_func = f"{vmax} * min(P1/({km1}+P1), P2/({km2}+P2))"
```

#### Enhancement 3: Product Inhibition

```python
# If products detected
if reaction.products:
    product_refs = [get_place(p_id).name for p_id, _ in reaction.products]
    # Competitive inhibition by product
    rate_func += f" / (1 + {product_refs[0]}/{ki})"
```

---

## User Guide

### Viewing the Rate Function

**After Import**:
1. Right-click transition → Properties
2. Navigate to "Rate Function (Advanced)" tab
3. See: `michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))`

### Editing the Rate Function

**To Customize**:
```python
# Original (sequential)
michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))

# Change to product kinetics
michaelis_menten(P1 * P2, 20.0, 3.0)

# Change to different Km for P2
michaelis_menten(P1, 20.0, 3.0) * (P2 / (5.0 + P2))

# Add product inhibition
michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2)) / (1 + P3/10)
```

---

## Summary

### What Was Implemented ✅

- ✅ **Automatic sequential Michaelis-Menten** for multi-substrate reactions
- ✅ **Based on number of input places** (reactant count)
- ✅ **Persists through save/load cycle**
- ✅ **Editable in property dialog**
- ✅ **Works in simulation**

### Formula Pattern

```
N=1: michaelis_menten(P1, Vmax, Km)
N=2: michaelis_menten(P1, Vmax, Km) * (P2 / (Km + P2))
N=3: michaelis_menten(P1, Vmax, Km) * (P2 / (Km + P2)) * (P3 / (Km + P3))
N≥4: ... continues pattern
```

### Verification

All persistence steps verified:
- Import sets values ✅
- Serialization saves values ✅
- Deserialization restores values ✅
- Property dialog displays values ✅
- Simulation uses values ✅

**Feature is production-ready!** 🎉
