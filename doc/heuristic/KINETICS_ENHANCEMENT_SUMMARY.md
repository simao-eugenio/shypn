# Kinetics Enhancement Strategy - Executive Summary

**Date**: October 19, 2025  
**Principle**: "Import as-is for curated models, enhance only when data is missing"

---

## Problem Statement

**Current State**:
- ✅ **SBML imports**: Correctly assign mass_action → stochastic, michaelis_menten → continuous
- ⚠️ **KEGG imports**: All transitions default to continuous (rate=1.0) - unrealistic for simulation

**User Question**: Should we auto-assign kinetic types based on reaction analysis?

**Answer**: **YES**, but following SBML's scientific method - **never override explicit data**.

---

## Core Strategy: Tiered Enhancement

### Tier 1: Explicit Data (HIGHEST PRIORITY)
**Rule**: **Import as-is, NEVER override**

```python
if has_explicit_kinetics(reaction):  # SBML <kineticLaw>
    use_explicit_data()
    return  # Done!
```

**Examples**:
- SBML with `<kineticLaw massAction="true">`
- BioModels curated kinetics
- User-configured transitions

### Tier 2: Database Lookup
**Rule**: Use EC number to lookup literature values

```python
if reaction.has_ec_number():
    params = ENZYME_DATABASE[ec_number]  # From BRENDA/SABIO-RK
    if params:
        assign_from_database(params)  # High confidence
        return
```

**Examples**:
- EC 2.7.1.1 (Hexokinase) → Known Vmax, Km from literature
- EC 2.7.1.11 (PFK) → Curated parameters

### Tier 3: Heuristic Analysis
**Rule**: Analyze reaction structure (like SBML does for missing data)

```python
if is_simple_1_to_1_reaction():
    transition.transition_type = "stochastic"  # Mass action
    transition.rate = 1.0
elif has_enzyme_annotation():
    transition.transition_type = "continuous"  # Michaelis-Menten
    transition.rate_function = "michaelis_menten(..., 10.0, 0.5)"
else:
    transition.transition_type = "continuous"  # Safe default
    transition.rate = 1.0
```

**Confidence Levels**:
- Simple mass action → Low confidence
- Enzymatic reaction → Medium confidence
- Unknown → Low confidence

### Tier 4: User Override (ALWAYS RESPECTED)
**Rule**: User's explicit choices are sacred

```python
if transition.metadata['kinetics_source'] == 'user':
    return  # Never auto-enhance user configurations
```

---

## Implementation Phases

### Phase 1: Heuristic Enhancement (THIS WEEK)

**Goal**: KEGG imports get reasonable kinetic defaults

**Changes**:
1. Create `src/shypn/importer/kinetics_assigner.py`
2. Add metadata tracking to `Transition` class:
   ```python
   transition.metadata = {
       'kinetics_source': 'heuristic',  # 'explicit', 'database', 'heuristic', 'user'
       'kinetics_confidence': 'medium',  # 'high', 'medium', 'low'
       'kinetics_rule': 'enzymatic_mm'
   }
   ```
3. Integrate with KEGG importer
4. Test with fresh import

**Expected Result**:
```
Before: All 39 transitions → continuous (rate=1.0)
After:  15 transitions → stochastic (mass action)
        24 transitions → continuous (Michaelis-Menten)
```

### Phase 2: Database Integration (NEXT SPRINT)

**Goal**: High-confidence parameters from EC numbers

**Changes**:
1. Build enzyme kinetics database (BRENDA/SABIO-RK)
2. EC number lookup in assigner
3. Apply database values when available

**Expected Result**:
```
12 transitions with EC numbers → high-confidence parameters
27 transitions without EC → heuristic (medium/low confidence)
```

### Phase 3: User Interface (FUTURE)

**Goal**: Transparency and control

**Changes**:
1. Show confidence in properties dialog
2. Bulk enhancement tool (Tools → Enhance Kinetics)
3. Validation warnings before simulation

---

## Safety Guarantees

### 1. Never Override Rule
```python
# These are SACRED - never auto-enhance
PROTECTED_SOURCES = ['explicit', 'user', 'high_confidence_database']

if transition.metadata['kinetics_source'] in PROTECTED_SOURCES:
    return  # Don't touch!
```

### 2. Change Tracking
```python
# Save original before enhancing
transition.metadata['original_kinetics'] = {
    'transition_type': transition.transition_type,
    'rate': transition.rate,
    # ...
}

# Can rollback later
def rollback():
    restore_original_kinetics()
```

### 3. Confidence Transparency
```
Properties Dialog shows:
  ⓘ Kinetics: Heuristic (Medium confidence)
  EC 2.7.1.1 - Hexokinase
  [View Details] [Override]
```

---

## Validation Testing

### Test 1: SBML Explicit Kinetics (MUST NOT CHANGE)
```python
# Import SBML with mass_action kinetic law
model = import_sbml("curated_model.sbml")
assert transition.transition_type == "stochastic"  # From SBML
assert transition.metadata['kinetics_source'] == 'explicit'

# Try enhancement (should skip)
enhance_kinetics(model)
assert transition.transition_type == "stochastic"  # Still unchanged ✓
```

### Test 2: KEGG Missing Kinetics (SHOULD ENHANCE)
```python
# Import KEGG (no kinetics)
model = import_kegg("hsa00010")
assert all(t.transition_type == 'continuous')  # All default

# Enhance with heuristics
enhance_kinetics(model)
stochastic_count = sum(1 for t in transitions if t.transition_type == 'stochastic')
assert stochastic_count > 0  # Some are now stochastic ✓
```

### Test 3: User Configuration (MUST NOT OVERRIDE)
```python
# User sets transition manually
transition.transition_type = "stochastic"
transition.metadata['kinetics_source'] = 'user'

# Try enhancement (should skip)
enhance_kinetics(model)
assert transition.transition_type == "stochastic"  # Still user's choice ✓
```

---

## Expected Impact

### KEGG Import Workflow

**Before Enhancement**:
```
Import hsa00010 → All continuous (rate=1.0) → Poor simulation
```

**After Enhancement**:
```
Import hsa00010 → Auto-analyze reactions → 
  Simple reactions → stochastic (mass action)
  Enzymatic → continuous (Michaelis-Menten)
  → Better simulation accuracy
```

### SBML Import Workflow (NO CHANGE)

**Before and After** (same):
```
Import curated.sbml → Use explicit kinetics → Correct simulation ✓
```

---

## Heuristic Rules (Phase 1)

| Reaction Pattern | Assignment | Confidence | Rationale |
|-----------------|------------|------------|-----------|
| Simple A → B (no enzyme) | Stochastic (λ=1.0) | Low | Likely mass action |
| Has EC number | Continuous (MM) | Medium | Enzymatic |
| Multiple substrates | Continuous (sequential MM) | Medium | Complex kinetics |
| Unknown | Continuous (rate=1.0) | Low | Safe default |

---

## Database Structure (Phase 2)

```python
ENZYME_KINETICS = {
    "2.7.1.1": {  # Hexokinase
        "type": "continuous",
        "law": "michaelis_menten",
        "vmax": 10.0,  # μM/s
        "km": 0.1,     # mM
        "source": "BRENDA",
        "confidence": "high"
    },
    # More enzymes from BRENDA/SABIO-RK
}
```

---

## Migration: Existing Models

**Issue**: Old KEGG-imported models have no metadata

**Solution**: Detection + optional enhancement

```python
on_model_load():
    needs_enh = detect_default_kinetics(model)
    if needs_enh:
        show_dialog(
            f"Found {len(needs_enh)} transitions with default kinetics.\n"
            "Enhance using heuristics?",
            ["Enhance", "Review Manually", "Keep As-Is"]
        )
```

---

## Decision Tree

```
Loading Model
     ↓
Has explicit kinetics? (SBML)
  YES → Use as-is ✓
  NO ↓
     ↓
Has EC numbers? (KEGG/SBML)
  YES → Database lookup
       Found? → Use database ✓ (high confidence)
       Not found? ↓
  NO ↓
     ↓
Apply heuristics
  Simple reaction → Stochastic (low confidence)
  Enzymatic → Continuous MM (medium confidence)
  Unknown → Continuous (low confidence)
     ↓
Track in metadata ✓
```

---

## Next Actions

### Immediate (This Session/Next)
1. ✅ Document strategy (this file)
2. ⏭️ Create `kinetics_assigner.py` module
3. ⏭️ Add metadata to `Transition.__init__()`
4. ⏭️ Implement heuristic rules
5. ⏭️ Test with fresh KEGG import

### This Week
1. ⏭️ Integrate with KEGG importer
2. ⏭️ Add unit tests (3 scenarios above)
3. ⏭️ Update import documentation

### Next Sprint
1. ⏭️ Build EC kinetics database
2. ⏭️ Implement database lookup
3. ⏭️ Add UI confidence indicators

---

## Key Principles

1. **Scientific Method**: Follow SBML's approach (it works!)
2. **Never Override**: Respect explicit/curated data
3. **Transparency**: Track source and confidence
4. **User Control**: Always allow manual override
5. **Safe Defaults**: Prefer continuous if uncertain

---

**Status**: 📋 **READY TO IMPLEMENT**  
**Risk**: ✅ **LOW** (only fills gaps, never overrides)  
**Benefit**: ⭐ **HIGH** (better simulation accuracy for KEGG imports)
