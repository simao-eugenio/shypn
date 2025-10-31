# SBML Import → Continuous Simulation Fix

**Date:** October 30, 2025  
**Issue:** BIOMD0000000001.sbml imports successfully but does not simulate (transitions don't fire)  
**Status:** ✅ RESOLVED

---

## Problem Overview

SBML models imported from BioModels were creating valid Petri net structures but failing to simulate. The issue manifested as:
- Transitions marked as continuous with rate functions
- Initial tokens present (1 token in P6/Basal)
- No errors during import or file loading
- **But simulation doesn't progress - transitions never fire**

---

## Import Flow Analysis

### 1. **Fetch Phase** (SBML Download)
```
User → Import SBML → data/biomodels_test/BIOMD0000000001.xml
```
**Status:** ✅ Working correctly
- XML file contains valid SBML Level 2 structure
- 12 species, 17 reactions (all reversible mass action kinetics)
- Rate formulas: `comp1 * (kf_0 * substrate - kr_0 * product)`
- Initial concentrations: Only species B (Basal) = 1.66e-21 molar
- Parameters: comp1=1e-16 L, kf_0=3000, kr_0=8000, etc.

---

### 2. **Parse Phase** (SBML → PathwayData)

**File:** `src/shypn/data/formats/sbml/sbml_parser.py`

**What Happens:**
```python
# Parse SBML XML
sbml_document = libsbml.readSBML(file_path)
model = sbml_document.getModel()

# Extract species → places
for species in model.getListOfSpecies():
    place = Place(
        id=species.getId(),
        initial_concentration=species.getInitialConcentration()
    )

# Extract reactions → transitions + arcs
for reaction in model.getListOfReactions():
    transition = Transition(
        id=reaction.getId(),
        is_reversible=reaction.getReversible()
    )
    # Store kinetic formula in properties
    transition.properties['sbml_formula'] = kinetic_formula
```

**Status:** ✅ Working correctly
- All species parsed as places
- All reactions parsed as transitions with reversible flag
- Kinetic formulas stored in properties

---

### 3. **Conversion Phase** (PathwayData → DocumentModel)

**File:** `src/shypn/data/pathway/pathway_converter.py`

#### ❌ **BUG #1: All transitions marked as stochastic**

**Original Code (Lines ~260):**
```python
# Create transition
transition = Transition(
    name=trans_data.name,
    transition_type='stochastic',  # ❌ WRONG - should check formula!
    rate=1.0
)
```

**Problem:** 
- All transitions defaulted to `stochastic` type regardless of kinetic formula
- Stochastic transitions require integer tokens and probabilistic firing
- SBML reactions with formulas should be `continuous` transitions

**✅ Fix Applied (commit def3959):**
```python
# Determine transition type based on SBML formula
if hasattr(trans_data, 'properties') and trans_data.properties:
    sbml_formula = trans_data.properties.get('sbml_formula')
    if sbml_formula:
        # Has kinetic formula → continuous transition
        transition_type = 'continuous'
        transition.properties['rate_function'] = sbml_formula
    else:
        # No formula → stochastic
        transition_type = 'stochastic'
        transition.properties['rate'] = 1.0
```

**Result:** All 17 transitions now correctly set as `continuous` with rate functions

---

### 4. **Post-Processing Phase** (Token Normalization)

**File:** `src/shypn/data/pathway/pathway_postprocessor.py`

#### ❌ **BUG #2: Tiny concentrations rounded to 0 tokens**

**Original Code (Lines ~130):**
```python
class UnitNormalizer:
    def process(self, place_data):
        concentration = place_data.initial_concentration  # 1.66e-21
        tokens = int(concentration * scale_factor)  # → 0
        place_data.initial_marking = tokens
```

**Problem:**
- SBML uses molar concentrations (can be extremely small: 1e-21)
- Conversion to integer tokens loses non-zero initial conditions
- Places with `concentration > 0` but `tokens = 0` → simulation can't start

**✅ Fix Applied (commit 153d5ec):**
```python
# After token calculation
if concentration > 0 and tokens == 0:
    # Preserve non-zero initial condition
    tokens = 1
    print(f"[POSTPROCESS] {place_data.name}: {concentration:.2e} → 1 token (minimum)")

place_data.initial_marking = tokens
```

**Result:** P6 (Basal) now gets 1 token from 1.66e-21 concentration

---

### 5. **Kinetics Integration Phase** (Add Rate Functions)

**File:** `src/shypn/data/formats/sbml/sbml_kinetics_integration_service.py`

**What Happens:**
```python
# Add kinetic metadata to transitions
for transition in model.transitions:
    if transition.properties.get('rate_function'):
        # Extract parameters from SBML
        transition.kinetic_metadata = KineticMetadata(
            formula_type='mass_action_reversible',
            parameters={
                'comp1': 1e-16,
                'kf_0': 3000.0,
                'kr_0': 8000.0,
                # ...
            }
        )
```

**Status:** ✅ Working correctly
- All kinetic parameters stored
- Formulas reference place names (P5, P6) and parameters (comp1, kf_0, kr_0)

---

### 6. **Save Phase** (Write to .shy file)

**File:** `src/shypn/data/formats/shy/shy_writer.py`

**What Happens:**
```json
{
  "places": [
    {"id": "P6", "name": "P6", "initial_marking": 1}
  ],
  "transitions": [
    {
      "id": "T1",
      "type": "continuous",
      "properties": {
        "rate_function": "comp1 * (kf_0 * P6 - kr_0 * P5)"
      },
      "kinetic_metadata": {
        "parameters": {"comp1": 1e-16, "kf_0": 3000, "kr_0": 8000}
      }
    }
  ]
}
```

**Status:** ✅ Working correctly
- File structure valid
- All properties and metadata preserved

---

## Simulation Execution Issues

### 7. **Runtime Evaluation Phase** (Continuous Behavior)

**File:** `src/shypn/engine/continuous_behavior.py`

#### ❌ **BUG #3: Compartment volumes make rates near-zero**

**Problem:**
```python
# Rate formula evaluation
rate = comp1 * (kf_0 * P6 - kr_0 * P5)
     = 1e-16 * (3000 * 1 - 8000 * 0)
     = 3e-13  # Near zero!
```

- SBML `comp1=1e-16` liters (compartment volume in physical units)
- Token-based simulation uses discrete counting (no physical units)
- Multiplication by 1e-16 makes all rates essentially zero

**✅ Fix Applied (commit 525bb24):**
```python
def _compile_rate_function(self):
    # Normalize compartment volumes for token-based simulation
    if hasattr(self.transition.kinetic_metadata, 'parameters'):
        params = self.transition.kinetic_metadata.parameters.copy()
        
        for key in list(params.keys()):
            if key.startswith('comp') and len(key) > 4 and key[4:].isdigit():
                # comp1, comp2, etc. → normalize to 1.0
                params[key] = 1.0
        
        context.update(params)
```

**Result:** `rate = 1.0 * (3000 * 1 - 8000 * 0) = 3000` ✅

---

#### ❌ **BUG #4: Place names not in evaluation context**

**Problem:**
```python
# Rate formula: "comp1 * (kf_0 * P6 - kr_0 * P5)"
# Error: name 'P5' is not defined
```

- Rate formulas reference places by name (P5, P6)
- Evaluation context only had places by ID: `context['5'] = 0`
- Name lookup failed during `eval()`

**✅ Fix Applied (commit b2683ed):**
```python
# Add place tokens to context BY ID AND NAME
for place_id, place in places.items():
    # By ID
    if isinstance(place_id, str) and place_id.startswith('P'):
        context[place_id] = place.tokens  # "P105" → 0
    else:
        context[f'P{place_id}'] = place.tokens  # 5 → "P5" → 0
    
    # ALSO by name (for SBML formulas)
    if hasattr(place, 'name') and place.name:
        context[place.name] = place.tokens  # "P5" → 0
```

**Result:** Both `P5` (by ID) and place name references now work

---

#### ❌ **BUG #5: Rate formulas reference places not in transition arcs**

**Problem:**
```python
# T1 formula: "comp1 * (kf_0 * P6 - kr_0 * P5)"
# T1 arcs: P1 ← T1 → P2
# Error: P5 and P6 not in places_dict!
```

**Original Code:**
```python
def integrate_step(self, dt, input_arcs, output_arcs):
    # Only gather places from THIS transition's arcs
    places_dict = {}
    for arc in input_arcs + output_arcs:
        place = self._get_place(arc.source_id or arc.target_id)
        places_dict[place.id] = place
    
    # Evaluate rate - FAILS because P5, P6 not in places_dict
    rate = self.rate_function(places_dict, time)
```

**Why This Happens:**
- SBML reactions can reference ANY species in their kinetic formula
- Example: `T1` (reaction R1) might convert A→B but formula includes regulatory species C
- Formula: `k * C * A` where C is a catalyst not consumed
- Petri net: A ← T1 → B (no arc to C, but C in formula!)

**✅ Fix Applied (commit f7332e3) - THE CRITICAL FIX:**
```python
def integrate_step(self, dt, input_arcs, output_arcs):
    # Gather ALL places from the model, not just from arcs
    places_dict = {}
    
    if hasattr(self.model, 'places'):
        if isinstance(self.model.places, dict):
            # Dict of {place_id: place_object}
            places_dict = self.model.places.copy()
        elif isinstance(self.model.places, list):
            # List of place objects
            for place in self.model.places:
                if hasattr(place, 'id'):
                    places_dict[place.id] = place
                else:
                    # String IDs - fetch objects
                    place_obj = self._get_place(place)
                    if place_obj:
                        places_dict[place_obj.id] = place_obj
    elif hasattr(self.model, 'get_all_places'):
        for place in self.model.get_all_places():
            places_dict[place.id] = place
    else:
        # Fallback to arcs (may be incomplete)
        for arc in input_arcs + output_arcs:
            place = self._get_place(arc.source_id or arc.target_id)
            if place:
                places_dict[place.id] = place
    
    # Now ALL places available for rate evaluation
    rate = self.rate_function(places_dict, time)  # ✅ Works!
```

**Result:** 
- T1 can now access P5 and P6 for formula evaluation
- All transitions fire correctly with calculated rates
- Simulation progresses as expected

---

## Complete Fix Summary

### Changes Required for SBML → Continuous Simulation

| Phase | File | Issue | Fix | Commit |
|-------|------|-------|-----|--------|
| **3. Convert** | `pathway_converter.py` | All transitions stochastic | Check for `sbml_formula` → set type=`continuous` | def3959 |
| **4. Postprocess** | `pathway_postprocessor.py` | Tiny concentrations → 0 tokens | If `concentration > 0` and `tokens == 0` → set `tokens = 1` | 153d5ec |
| **7. Runtime** | `continuous_behavior.py` | Compartment volumes near-zero | Normalize `comp*` parameters to 1.0 | 525bb24 |
| **7. Runtime** | `continuous_behavior.py` | Place names undefined | Add places by both ID and name to context | b2683ed |
| **7. Runtime** | `continuous_behavior.py` | Formula references missing places | Gather ALL places from model, not just arcs | f7332e3 |

---

## Verification

### Before Fixes:
```
[CAN_FIRE] T1: input_arcs=1, can_fire=True
[CAN_FIRE] T6: input_arcs=1, can_fire=True
[RATE ERROR] T1: name 'P5' is not defined
[RATE ERROR] T6: name 'P4' is not defined
```
**Result:** No transitions fire, simulation frozen

### After Fixes:
```
[CAN_FIRE] T1: input_arcs=1, can_fire=True
[CAN_FIRE] T6: input_arcs=1, can_fire=True
[RATE EVAL] T1: rate=3000.0
[RATE EVAL] T6: rate=8000.0
[FIRE] T1: consumed P6=0.18, produced P5=0.18
[FIRE] T6: consumed P6=0.48, produced P4=0.48
...
[CAN_FIRE] T6: can_fire=False (P6 depleted)
[CAN_FIRE] T2: can_fire=True (P5 now available)
```
**Result:** ✅ Transitions fire, tokens flow, simulation progresses correctly

---

## Architecture Lessons

### Key Insight: SBML Kinetic Formulas ≠ Petri Net Arcs

**SBML Reaction:**
```xml
<reaction id="R1" reversible="true">
  <listOfReactants>
    <speciesReference species="A" stoichiometry="1"/>
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="B" stoichiometry="1"/>
  </listOfProducts>
  <kineticLaw>
    <math>comp1 * (kf * A * C - kr * B)</math>  <!-- C is catalyst! -->
  </kineticLaw>
</reaction>
```

**Petri Net Translation:**
```
Places: A, B, C
Arcs: A → T1 → B  (C not connected!)
Rate Function: comp1 * (kf * A * C - kr * B)  (C still referenced!)
```

**Implication:**
- Arcs define token flow (consumption/production)
- Rate formulas can reference ANY place (regulators, catalysts, inhibitors)
- Continuous behavior MUST have access to all places, not just connected ones

---

## Testing Recommendations

### Regression Test Cases

1. **Simple Mass Action**
   - Formula: `k * A`
   - Expected: Standard A → B flow

2. **Reversible Reaction**
   - Formula: `kf * A - kr * B`
   - Expected: Bidirectional flow until equilibrium

3. **Catalytic Regulation**
   - Formula: `k * C * A` (C not consumed)
   - Expected: C modulates rate but isn't depleted

4. **Competitive Inhibition**
   - Formula: `Vmax * S / (Km * (1 + I/Ki) + S)`
   - Expected: I reduces rate without being consumed

5. **Compartmentalized Model**
   - Parameters: comp1=1e-16, comp2=1e-15
   - Expected: All comp* normalized to 1.0

### Validation Criteria

✅ **Import Success:**
- All species → places with correct initial tokens
- All reactions → continuous transitions with rate functions
- All parameters stored in kinetic_metadata

✅ **Simulation Success:**
- Transitions fire when enabled
- Token counts change over time
- Conservation laws maintained (if applicable)
- No `[RATE ERROR]` messages

---

## Future Improvements

### 1. Better Compartment Handling
Instead of normalizing to 1.0, could:
- Scale all compartments relative to smallest
- Preserve concentration ratios across compartments
- Document normalization choice in model properties

### 2. Validation Warnings
Add checks during import:
```python
# Warn if formula references non-connected places
for transition in model.transitions:
    formula_places = extract_place_refs(transition.rate_function)
    arc_places = {arc.source_id for arc in transition.input_arcs}
    disconnected = formula_places - arc_places
    if disconnected:
        warn(f"{transition.name} formula references {disconnected} without arcs")
```

### 3. Performance Optimization
Current: `integrate_step()` rebuilds places_dict every call
Better: Cache all places once during model load
```python
def __init__(self, transition, model):
    self._all_places_cache = {p.id: p for p in model.places}
```

---

## Related Documentation

- [SBML Import Architecture](./SBML_IMPORT_ARCHITECTURE.md)
- [Continuous Behavior Implementation](./CONTINUOUS_BEHAVIOR.md)
- [Pathway Conversion Process](./PATHWAY_CONVERSION.md)
- [BioModels Test Suite](../data/biomodels_test/README.md)

---

**Status:** All fixes committed and tested with BIOMD0000000001  
**Next Steps:** Test with additional BioModels (BIOMD0000000002-0010) to verify robustness
