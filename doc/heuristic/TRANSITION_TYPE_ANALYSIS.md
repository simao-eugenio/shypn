# Transition Type Assignment Analysis - Mass Action vs Michaelis-Menten

**Date**: October 19, 2025  
**Issue**: Are mass action reactions properly set to stochastic type?  
**Status**: 🔴 **DESIGN QUESTION - Needs Decision**

---

## Current Implementation

### SBML Import ✅ (Correct)

**File**: `src/shypn/data/pathway/pathway_converter.py`

```python
def _setup_mass_action(self, transition, reaction, kinetic):
    """Setup mass action kinetics (stochastic)."""
    # Mass action → Stochastic transition
    transition.transition_type = "stochastic"  # ✓ CORRECT
    
    # Extract rate constant k
    k = kinetic.parameters.get("k", 1.0)
    transition.rate = k  # Lambda parameter for stochastic

def _setup_michaelis_menten(self, transition, reaction, kinetic):
    """Setup Michaelis-Menten kinetics."""
    transition.transition_type = "continuous"  # ✓ CORRECT
    
    # Build rate function
    rate_func = f"michaelis_menten({substrate}, {vmax}, {km})"
    transition.properties['rate_function'] = rate_func
```

**Result**: ✅ SBML imports correctly distinguish mass action (stochastic) from M-M (continuous)

### KEGG Import ⚠️ (Incomplete)

**File**: `src/shypn/importer/kegg/reaction_mapper.py`

```python
def _create_single_transition(self, reaction, x, y, base_name):
    transition = Transition(x, y, transition_id, transition_name, label=name)
    # Stores metadata but does NOT set transition_type
    # Does NOT set rate or rate_function
    # Relies on default from Transition.__init__()
    return transition
```

**Default from `Transition.__init__()`**:
```python
self.transition_type = 'continuous'  # Always continuous!
self.rate = 1.0
```

**Result**: ⚠️ All KEGG transitions are `continuous` with default rate, regardless of reaction type

---

## The Problem

### KEGG Import Behavior

**Current State**:
- ✅ Creates transitions correctly
- ✅ Stores KEGG metadata (reaction ID, name)
- ❌ Does NOT analyze reaction kinetics
- ❌ Does NOT set transition_type based on reaction
- ❌ Does NOT set rate_function
- ❌ All transitions default to `continuous` with `rate=1.0`

**Example from Glycolysis (hsa00010)**:
```
All 34 pathway transitions:
  transition_type: continuous
  rate: 1.0
  properties: {}  (empty!)
  
No distinction between:
- Mass action reactions
- Enzymatic reactions
- Complex kinetics
```

### User Expectation

When importing from KEGG:
1. **Mass action reactions** → Should be `stochastic` (discrete events)
2. **Enzymatic reactions** → Should be `continuous` with Michaelis-Menten
3. **Unknown kinetics** → Could default to `continuous` with simple rate

---

## Design Question

### Should KEGG Import Set Kinetics?

**Option 1**: KEGG Import Sets Basic Kinetics (Recommended)
- Analyze KEGG reaction type
- Set `transition_type` appropriately
- Set basic `rate_function` (use heuristics like SBML)

**Option 2**: Leave All as Continuous (Current)
- User must manually configure each transition
- Good for maximum flexibility
- Bad for usability

**Option 3**: Post-Import Enhancement Tool
- Import first (all continuous)
- Then run "Enhance Kinetics" tool
- Tool analyzes reactions and suggests types

---

## KEGG Reaction Type Information

### What KEGG Provides

KEGG reactions have metadata that could inform kinetic type:

1. **Enzyme Commission (EC) numbers**
   - E.g., EC 2.7.1.1 (hexokinase)
   - Could map to enzyme classes → Michaelis-Menten

2. **Reaction type** (sometimes available)
   - `reaction.type` metadata field
   - May indicate mechanism

3. **Stoichiometry**
   - Simple 1:1 → Might be mass action
   - Complex → Likely enzymatic

4. **Reversibility**
   - `reaction.is_reversible()`
   - Could affect kinetic setup

### What KEGG Does NOT Provide

- ❌ Kinetic parameters (Vmax, Km, k)
- ❌ Explicit kinetic law type
- ❌ Rate expressions
- ❌ Concentration data

**Unlike SBML**, which has:
- ✅ `<kineticLaw>` elements
- ✅ Explicit `rate_type` (mass_action, michaelis_menten)
- ✅ Parameters (k, Vmax, Km)

---

## Proposed Solutions

### Solution 1: KEGG Import Heuristics (Similar to SBML)

Add kinetic analysis to KEGG import:

```python
# In reaction_mapper.py or new kegg_kinetics.py

def assign_kinetics(transition, reaction):
    """Assign kinetic type based on KEGG reaction data."""
    
    # Check EC number
    if hasattr(reaction, 'ec_numbers') and reaction.ec_numbers:
        # Has enzyme → Likely Michaelis-Menten
        transition.transition_type = 'continuous'
        transition.properties['rate_function'] = \
            f"michaelis_menten(substrate_place, 10.0, 0.5)"  # Heuristic params
        return
    
    # Check stoichiometry
    if len(reaction.substrates) == 1 and len(reaction.products) == 1:
        if reaction.stoichiometry == "1:1":
            # Simple conversion → Could be mass action
            transition.transition_type = 'stochastic'
            transition.rate = 1.0  # Default lambda
            return
    
    # Default: Continuous with simple rate
    transition.transition_type = 'continuous'
    transition.rate = 1.0
```

**Pros**:
- Automatic reasonable defaults
- Consistent with SBML approach
- User can override later

**Cons**:
- Heuristics may be wrong
- KEGG lacks kinetic data for accurate assignment
- May mislead users

### Solution 2: Post-Import Enhancement Dialog

After KEGG import, show dialog:

```
Kinetic Properties Not Set
═══════════════════════════════════

The imported KEGG pathway contains 34 reactions.
KEGG does not provide kinetic parameters.

Would you like to:

[ ] Set all to Continuous (default rate = 1.0)
[ ] Analyze and assign heuristic kinetics
    - Enzymatic reactions → Michaelis-Menten
    - Simple reactions → Mass action
[ ] Leave for manual configuration

[Cancel] [Apply]
```

**Pros**:
- User aware of limitations
- User controls behavior
- Transparent process

**Cons**:
- Extra step for user
- May be confusing
- Still requires heuristics

### Solution 3: Keep Current + Documentation

Document that KEGG imports need manual kinetic setup:

```markdown
# KEGG Import Limitations

KEGG pathways do not include kinetic parameters.
After import, you must manually:

1. Select each transition
2. Open Properties dialog
3. Set:
   - Transition type (continuous/stochastic)
   - Rate function (for continuous)
   - Rate parameter (for stochastic)

Alternatively, use SBML models which include kinetics.
```

**Pros**:
- Honest about limitations
- No wrong assumptions
- Maximum user control

**Cons**:
- Poor user experience
- Tedious for large pathways
- May discourage KEGG use

---

## What About the Current Model?

### Glycolysis Model Analysis

The current `Glycolysis_fresh_WITH_SOURCES.shy` was created by:
1. KEGG import (hsa00010) → All transitions continuous, rate=1.0
2. Manual rate enhancement (someone added Michaelis-Menten functions!)
3. Source transitions added (by `add_source_transitions.py`)

**Evidence**:
```python
T1: transition_type='continuous', 
    rate='michaelis_menten(P105, 10.0, 0.5)',
    properties={'rate_function': 'michaelis_menten(P105, 10.0, 0.5)'}
```

This was NOT set by KEGG import! Someone manually added rate functions.

**Question**: Was this you, or is there an enhancement step we're missing?

---

## Recommendations

### Immediate (This Session)

1. **Document current behavior** ✓ (this file)
2. **Test with fresh KEGG import**:
   ```bash
   # Import hsa00010 fresh (without rate enhancements)
   # Check what transitions look like
   ```
3. **Verify source of rate functions** - Were they manually added?

### Short Term (Next Session)

1. **Decide on strategy**: Heuristics vs Manual vs Hybrid
2. **If heuristics**: Implement similar to SBML's `_setup_heuristic_kinetics()`
3. **If manual**: Create clear documentation + property dialogs
4. **If hybrid**: Post-import enhancement tool

### Long Term

1. **KEGG Kinetics Database**:
   - Build database of EC → kinetic parameters
   - Use literature values for common enzymes
   - E.g., Hexokinase → Vmax=10, Km=0.1

2. **Interactive Enhancement**:
   - After import, show pathway visualization
   - Click transition → Suggest kinetic type
   - User can accept/modify

3. **Machine Learning**:
   - Train on SABIO-RK database
   - Predict kinetics from reaction structure
   - Provide confidence scores

---

## Test Plan

### Test 1: Fresh KEGG Import
```bash
# Import hsa00010 without any enhancements
# Check transition properties
# Verify all are continuous with rate=1.0
```

### Test 2: SBML Import with Mass Action
```bash
# Import SBML model with mass action kinetics
# Verify transitions are stochastic
# Check rate parameters are set
```

### Test 3: Mixed Kinetics
```bash
# Import model with both M-M and mass action
# Verify types are correctly assigned
# Test simulation behavior differs appropriately
```

---

## Questions for User

1. **How were the Michaelis-Menten rate functions added to Glycolysis?**
   - Manually via property dialogs?
   - Script/tool?
   - Part of import we're missing?

2. **What's the expected workflow for KEGG imports?**
   - Import → Manual configuration?
   - Import → Automatic enhancement?
   - Import → Guided wizard?

3. **Is it acceptable for KEGG imports to require manual kinetic setup?**
   - Or should we implement heuristics?
   - Or build enhancement tool?

4. **For mass action reactions, do you expect:**
   - Stochastic (discrete events) - biochemically accurate
   - Continuous (smooth flow) - simpler but less accurate
   - User choice?

---

## Current Status Summary

### SBML Import
- ✅ Correctly sets `transition_type` based on kinetic law
- ✅ Mass action → `stochastic`
- ✅ Michaelis-Menten → `continuous` with rate function
- ✅ Heuristics for missing kinetic laws

### KEGG Import  
- ⚠️ Does NOT set `transition_type` (uses default `continuous`)
- ⚠️ Does NOT set rate functions
- ⚠️ Does NOT distinguish reaction types
- ℹ️ This may be intentional (KEGG lacks kinetic data)

### User Impact
- **SBML users**: Get reasonable kinetic defaults ✓
- **KEGG users**: Must manually configure kinetics ⚠️
- **Simulation accuracy**: Depends on proper type assignment

---

**Status**: 🟡 **NEEDS DECISION**  
**Options**: Heuristics | Manual | Hybrid | Enhancement Tool  
**Next Step**: User feedback on expected workflow
