# Michaelis-Menten Auto-Parameterization for Biochemical Pathways

**Created**: October 18, 2025  
**Status**: 📋 PLANNING PHASE  
**Priority**: HIGH (Biochemical Realism)  
**Complexity**: 🔴 CHALLENGING

---

## Executive Summary

Enhance SBML import to **automatically infer** Michaelis-Menten parameters (Vmax, Km) from stoichiometry and pathway context, and **pre-fill** the rate function field in transition dialogs with biochemically realistic formulas.

### Key Requirements

1. ✅ **Already Implemented**: Michaelis-Menten equations generated on import
2. 🆕 **New**: Auto-parameterization from stoichiometry
3. 🆕 **New**: Pre-fill rate function in transition dialog
4. 🆕 **New**: Context-aware (input/output places)
5. 🆕 **New**: Infer Vmax, Km from pathway structure

---

## Problem Statement

### Current State ✅

**File**: `src/shypn/data/pathway/pathway_converter.py:266-325`

```python
def _setup_michaelis_menten(self, transition, reaction, kinetic):
    """Setup Michaelis-Menten kinetics with rate_function."""
    
    # Extract parameters FROM SBML
    vmax = kinetic.parameters.get("Vmax", kinetic.parameters.get("vmax", 1.0))
    km = kinetic.parameters.get("Km", kinetic.parameters.get("km", 1.0))
    
    # Build rate function
    if len(substrate_places) == 1:
        rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
    else:
        # Sequential Michaelis-Menten for multiple substrates
        rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
        for substrate_place in substrate_places[1:]:
            rate_func += f" * ({substrate_place.name} / ({km} + {substrate_place.name}))"
    
    transition.properties['rate_function'] = rate_func
```

**✅ Works when SBML has Vmax/Km**  
**❌ Fails when SBML lacks kinetic parameters**

### User Requirements 🎯

1. **Biochemical Reactions**: Almost all are Michaelis-Menten
2. **Auto-Set on Import**: Continuous transitions automatically get MM
3. **Pre-filled Dialog**: Rate function field shows MM formula
4. **Context-Aware**: Consider input/output places (locality)
5. **Infer Parameters**: Vmax, Km from stoichiometry

---

## Challenge Analysis

### Challenge 1: Missing Kinetic Parameters

**Problem**: Many SBML files lack Vmax/Km values

**Example**:
```xml
<reaction id="R1" name="Glucose_Phosphorylation">
  <listOfReactants>
    <speciesReference species="Glucose" stoichiometry="1"/>
    <speciesReference species="ATP" stoichiometry="1"/>
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="G6P" stoichiometry="1"/>
    <speciesReference species="ADP" stoichiometry="1"/>
  </listOfProducts>
  <!-- NO KINETIC LAW! -->
</reaction>
```

**Current Behavior**:
```python
transition.transition_type = "continuous"
transition.rate = 1.0  # Generic default
# No rate_function generated
```

**Desired Behavior**:
```python
transition.transition_type = "continuous"
transition.rate = 10.0  # Inferred Vmax
transition.properties['rate_function'] = "michaelis_menten(P_Glucose, 10.0, 5.0)"
# Parameters inferred from stoichiometry
```

### Challenge 2: Parameter Inference from Stoichiometry

**Question**: How to estimate Vmax and Km?

#### Strategy A: Heuristic Rules (Simple)

```python
def infer_mm_parameters(reaction, substrate_places, product_places):
    """Infer Michaelis-Menten parameters from stoichiometry.
    
    Heuristic Rules:
    - Vmax ≈ 10 * max(product_stoichiometry)
    - Km ≈ mean(substrate_initial_concentrations) / 2
    """
    
    # Rule 1: Vmax from product stoichiometry
    max_product_stoich = max(s for _, s in reaction.products)
    vmax = 10.0 * max_product_stoich
    
    # Rule 2: Km from substrate concentrations
    substrate_concentrations = [p.tokens for p in substrate_places]
    mean_concentration = sum(substrate_concentrations) / len(substrate_concentrations)
    km = mean_concentration / 2.0
    
    # Ensure reasonable values
    vmax = max(1.0, vmax)  # At least 1.0
    km = max(0.1, km)       # At least 0.1
    
    return vmax, km
```

**Pros**: Simple, fast, always produces values  
**Cons**: Not biochemically accurate

#### Strategy B: Database Lookup (Accurate but Complex)

```python
def lookup_kinetic_parameters(reaction, species_ids):
    """Look up known kinetic parameters from biochemical databases.
    
    Sources:
    - BRENDA (enzyme database)
    - SABIO-RK (kinetic parameters)
    - KEGG (enzyme properties)
    """
    
    # Try to identify enzyme from reaction name
    enzyme_ec = identify_enzyme_ec_number(reaction.name)
    
    if enzyme_ec:
        # Query BRENDA for Vmax/Km
        params = brenda_api.get_kinetic_parameters(enzyme_ec, organism="Human")
        if params:
            return params['vmax'], params['km']
    
    # Fallback to heuristics
    return infer_from_heuristics(reaction)
```

**Pros**: Biochemically accurate  
**Cons**: Requires external API, slow, complex

#### Strategy C: Hybrid Approach (Recommended) ⭐

```python
def estimate_mm_parameters(reaction, substrate_places, product_places):
    """Estimate Michaelis-Menten parameters using hybrid approach.
    
    Priority:
    1. Use SBML values if present (already implemented)
    2. Try local parameter database (cached from previous lookups)
    3. Use stoichiometry-based heuristics
    4. Provide reasonable defaults
    """
    
    # STEP 1: Check SBML (already done in current code)
    if has_sbml_parameters(reaction):
        return sbml_vmax, sbml_km
    
    # STEP 2: Check local cache (new)
    cached = get_cached_parameters(reaction.name, reaction.reactants)
    if cached:
        return cached['vmax'], cached['km']
    
    # STEP 3: Stoichiometry heuristics (new)
    vmax, km = infer_from_stoichiometry(reaction, substrate_places, product_places)
    
    return vmax, km
```

### Challenge 3: Context-Aware Rate Functions

**Requirement**: "Taking locality in context, the function must consider input places and output places"

**Interpretation**: Rate function should reference **actual place names** in the network.

**Current Implementation**: ✅ Already does this!

```python
# Current code in pathway_converter.py:304
rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
# Uses actual place name: P_Glucose, not generic "substrate"
```

**Enhancement**: Consider products for **product inhibition**

```python
def build_context_aware_rate_function(substrate_places, product_places, vmax, km):
    """Build rate function considering both substrates and products.
    
    Formula variations:
    1. Simple MM: michaelis_menten(S, Vmax, Km)
    2. With product inhibition: michaelis_menten(S, Vmax, Km) / (1 + P/Ki)
    3. With allosteric regulation: michaelis_menten(S, Vmax, Km) * hill(A, 1, Kd, n)
    """
    
    # Base formula
    base = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
    
    # Add product inhibition if reversible
    if has_product_inhibition(reaction):
        ki = km * 2.0  # Assume Ki ≈ 2*Km
        base += f" / (1 + {product_places[0].name}/{ki})"
    
    return base
```

### Challenge 4: Pre-filling Dialog

**Current Dialog State**:

**File**: `src/shypn/helpers/transition_prop_dialog_loader.py:174-180`

```python
# Rate function (TextView)
rate_textview = self.builder.get_object('rate_textview')
if rate_textview and hasattr(self.transition_obj, 'rate'):
    buffer = rate_textview.get_buffer()
    rate_value = self.transition_obj.rate  # ← Gets rate attribute
    if rate_value is not None:
        buffer.set_text(str(rate_value))  # Shows "10.0" not formula
```

**Problem**: Shows `rate` attribute (10.0), not `properties['rate_function']`

**Solution**: Prioritize `rate_function` from properties

```python
# Enhanced version
rate_textview = self.builder.get_object('rate_textview')
if rate_textview:
    buffer = rate_textview.get_buffer()
    
    # PRIORITY 1: Check if rate_function exists in properties
    if 'rate_function' in self.transition_obj.properties:
        rate_func = self.transition_obj.properties['rate_function']
        buffer.set_text(rate_func)  # Shows "michaelis_menten(P1, 10, 5)"
    
    # PRIORITY 2: Fall back to rate attribute
    elif hasattr(self.transition_obj, 'rate') and self.transition_obj.rate is not None:
        buffer.set_text(str(self.transition_obj.rate))  # Shows "10.0"
```

---

## Implementation Plan

### Phase 1: Parameter Inference System (Week 1)

**Goal**: Create system to estimate Vmax/Km when missing

#### Task 1.1: Create Parameter Estimator Module

**File**: `src/shypn/data/pathway/kinetic_parameter_estimator.py` (NEW)

```python
"""
Kinetic Parameter Estimator

Estimates Michaelis-Menten parameters (Vmax, Km) from:
- Reaction stoichiometry
- Initial concentrations
- Biochemical heuristics
"""

from typing import Tuple, List
from shypn.netobjs.place import Place
from shypn.data.pathway.pathway_data import Reaction


class KineticParameterEstimator:
    """Estimates kinetic parameters for reactions without explicit kinetics."""
    
    def __init__(self):
        self.default_vmax = 10.0
        self.default_km = 5.0
        self.parameter_cache = {}  # Cache for frequently used enzymes
    
    def estimate_michaelis_menten(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Tuple[float, float]:
        """
        Estimate Vmax and Km for a reaction.
        
        Strategy:
        1. Check cache for known enzyme
        2. Use stoichiometry-based heuristics
        3. Use substrate concentrations
        4. Fall back to defaults
        
        Args:
            reaction: Reaction object
            substrate_places: Input places
            product_places: Output places
            
        Returns:
            (vmax, km) tuple
        """
        
        # Step 1: Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Step 2: Estimate from stoichiometry
        vmax = self._estimate_vmax(reaction, product_places)
        km = self._estimate_km(reaction, substrate_places)
        
        # Step 3: Cache for future use
        self.parameter_cache[cache_key] = (vmax, km)
        
        return vmax, km
    
    def _estimate_vmax(self, reaction: Reaction, product_places: List[Place]) -> float:
        """
        Estimate Vmax from reaction stoichiometry and products.
        
        Heuristic Rules:
        - For 1:1 reactions → Vmax = 10.0
        - For N:M reactions → Vmax = 10.0 * max(product_stoichiometry)
        - Adjust based on reaction reversibility
        """
        if not reaction.products:
            return self.default_vmax
        
        # Get maximum product stoichiometry
        max_stoich = max(stoich for _, stoich in reaction.products)
        
        # Base Vmax scales with stoichiometry
        vmax = 10.0 * max_stoich
        
        # Adjust for reversibility
        if reaction.reversible:
            vmax *= 0.8  # Reversible reactions are slightly slower
        
        return vmax
    
    def _estimate_km(self, reaction: Reaction, substrate_places: List[Place]) -> float:
        """
        Estimate Km from substrate concentrations.
        
        Heuristic: Km ≈ mean(substrate_concentrations) / 2
        
        Rationale: Km is the substrate concentration at half-maximum velocity.
        For typical cellular conditions, Km is often around half the
        substrate concentration.
        """
        if not substrate_places:
            return self.default_km
        
        # Get substrate concentrations (tokens)
        concentrations = [p.tokens for p in substrate_places if p.tokens > 0]
        
        if not concentrations:
            return self.default_km
        
        # Mean concentration / 2
        mean_concentration = sum(concentrations) / len(concentrations)
        km = mean_concentration / 2.0
        
        # Ensure minimum value
        km = max(0.5, km)  # At least 0.5
        
        return km
    
    def _make_cache_key(self, reaction: Reaction) -> str:
        """Create cache key from reaction properties."""
        # Use reaction name and reactant/product IDs
        reactants = tuple(sorted(rid for rid, _ in reaction.reactants))
        products = tuple(sorted(pid for pid, _ in reaction.products))
        return f"{reaction.name}_{reactants}_{products}"
```

**Tests**: `tests/test_kinetic_parameter_estimator.py`

```python
def test_estimate_vmax_from_stoichiometry():
    """Test Vmax estimation from product stoichiometry."""
    reaction = Reaction(
        id="R1",
        name="Test",
        reactants=[("S1", 1.0)],
        products=[("P1", 2.0)]  # 2:1 stoichiometry
    )
    
    estimator = KineticParameterEstimator()
    vmax, km = estimator.estimate_michaelis_menten(reaction, [], [])
    
    assert vmax == 20.0  # 10.0 * 2.0

def test_estimate_km_from_concentrations():
    """Test Km estimation from substrate concentrations."""
    place1 = Place(x=0, y=0, id=1, name="S1")
    place1.tokens = 10.0
    
    place2 = Place(x=0, y=0, id=2, name="S2")
    place2.tokens = 20.0
    
    reaction = Reaction(
        id="R1",
        name="Test",
        reactants=[("S1", 1.0), ("S2", 1.0)],
        products=[("P1", 1.0)]
    )
    
    estimator = KineticParameterEstimator()
    vmax, km = estimator.estimate_michaelis_menten(reaction, [place1, place2], [])
    
    # Mean concentration = (10 + 20) / 2 = 15
    # Km = 15 / 2 = 7.5
    assert km == 7.5
```

#### Task 1.2: Integrate Estimator into PathwayConverter

**File**: `src/shypn/data/pathway/pathway_converter.py`

**Enhancement**:

```python
from shypn.data.pathway.kinetic_parameter_estimator import KineticParameterEstimator

class ReactionConverter(BaseConverter):
    def __init__(self, pathway, document, species_to_place=None):
        super().__init__(pathway, document)
        self.species_to_place = species_to_place or {}
        self.parameter_estimator = KineticParameterEstimator()  # NEW
    
    def _configure_transition_kinetics(self, transition, reaction):
        """Configure transition kinetics based on reaction kinetic law."""
        
        if not reaction.kinetic_law:
            # NO KINETIC LAW → Assume Michaelis-Menten and estimate parameters
            self._setup_michaelis_menten_estimated(transition, reaction)  # NEW
            return
        
        # Rest of existing code...
    
    def _setup_michaelis_menten_estimated(self, transition, reaction):
        """
        Setup Michaelis-Menten without explicit kinetic law.
        
        NEW METHOD: Estimates parameters when SBML lacks kinetics.
        """
        transition.transition_type = "continuous"
        
        # Get substrate and product places
        substrate_places = []
        for species_id, stoich in reaction.reactants:
            place = self.species_to_place.get(species_id)
            if place:
                substrate_places.append(place)
        
        product_places = []
        for species_id, stoich in reaction.products:
            place = self.species_to_place.get(species_id)
            if place:
                product_places.append(place)
        
        if not substrate_places:
            transition.rate = 1.0
            self.logger.warning(
                f"  No substrates found for {reaction.id}, using default rate"
            )
            return
        
        # ESTIMATE PARAMETERS (NEW)
        vmax, km = self.parameter_estimator.estimate_michaelis_menten(
            reaction, substrate_places, product_places
        )
        
        self.logger.info(
            f"  Estimated Michaelis-Menten parameters: Vmax={vmax}, Km={km}"
        )
        
        # Build rate function (same as before)
        if len(substrate_places) == 1:
            rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
        else:
            rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
            for substrate_place in substrate_places[1:]:
                rate_func += f" * ({substrate_place.name} / ({km} + {substrate_place.name}))"
        
        transition.properties['rate_function'] = rate_func
        transition.rate = vmax
```

**Enhancement to existing `_setup_michaelis_menten()`**:

```python
def _setup_michaelis_menten(self, transition, reaction, kinetic):
    """Setup Michaelis-Menten kinetics with rate_function."""
    transition.transition_type = "continuous"
    
    # Extract parameters from SBML
    vmax = kinetic.parameters.get("Vmax", kinetic.parameters.get("vmax", None))
    km = kinetic.parameters.get("Km", kinetic.parameters.get("km", None))
    
    # NEW: If parameters missing, estimate them
    if vmax is None or km is None:
        substrate_places = [
            self.species_to_place.get(sid)
            for sid, _ in reaction.reactants
            if self.species_to_place.get(sid)
        ]
        product_places = [
            self.species_to_place.get(sid)
            for sid, _ in reaction.products
            if self.species_to_place.get(sid)
        ]
        
        vmax_est, km_est = self.parameter_estimator.estimate_michaelis_menten(
            reaction, substrate_places, product_places
        )
        
        vmax = vmax if vmax is not None else vmax_est
        km = km if km is not None else km_est
        
        self.logger.info(
            f"  Estimated missing parameters: Vmax={vmax}, Km={km}"
        )
    
    # Rest of existing code unchanged...
```

---

### Phase 2: Dialog Pre-filling (Week 2)

**Goal**: Pre-fill rate function field in transition dialog

#### Task 2.1: Enhance Dialog Loader

**File**: `src/shypn/helpers/transition_prop_dialog_loader.py:174-180`

**Current Code**:
```python
# Rate function (TextView)
rate_textview = self.builder.get_object('rate_textview')
if rate_textview and hasattr(self.transition_obj, 'rate'):
    buffer = rate_textview.get_buffer()
    rate_value = self.transition_obj.rate
    if rate_value is not None:
        buffer.set_text(str(rate_value))
```

**Enhanced Code**:
```python
# Rate function (TextView) - ENHANCED to check properties first
rate_textview = self.builder.get_object('rate_textview')
if rate_textview:
    buffer = rate_textview.get_buffer()
    
    # PRIORITY 1: Check if rate_function exists in properties
    if 'rate_function' in self.transition_obj.properties:
        rate_func = self.transition_obj.properties['rate_function']
        buffer.set_text(str(rate_func))
        self.logger.debug(f"Loaded rate_function from properties: {rate_func}")
    
    # PRIORITY 2: Fall back to rate attribute
    elif hasattr(self.transition_obj, 'rate') and self.transition_obj.rate is not None:
        rate_value = self.transition_obj.rate
        buffer.set_text(str(rate_value))
        self.logger.debug(f"Loaded rate from attribute: {rate_value}")
    
    # PRIORITY 3: Empty (new transition)
    else:
        buffer.set_text("")
```

#### Task 2.2: Add Context-Aware Template

**Enhancement**: When creating new continuous transition, suggest Michaelis-Menten template

```python
def _populate_fields(self):
    """Populate dialog fields from transition object."""
    
    # ... existing code ...
    
    # Rate function (TextView)
    rate_textview = self.builder.get_object('rate_textview')
    if rate_textview:
        buffer = rate_textview.get_buffer()
        
        # Check if rate_function exists
        if 'rate_function' in self.transition_obj.properties:
            rate_func = self.transition_obj.properties['rate_function']
            buffer.set_text(str(rate_func))
        
        # NEW: For continuous transitions without rate_function, suggest template
        elif self.transition_obj.transition_type == 'continuous':
            # Get connected input places
            input_places = self._get_input_places()
            
            if input_places:
                # Suggest Michaelis-Menten template
                template = self._generate_mm_template(input_places)
                buffer.set_text(template)
                
                # Add helpful comment
                comment = "# Template: Edit Vmax and Km values\n"
                buffer.insert(buffer.get_start_iter(), comment)
        
        # Fall back to rate attribute
        elif hasattr(self.transition_obj, 'rate') and self.transition_obj.rate is not None:
            buffer.set_text(str(self.transition_obj.rate))

def _get_input_places(self):
    """Get places connected to this transition as inputs."""
    input_places = []
    
    # Iterate through all arcs in the document
    for arc in self.transition_obj.document.arcs:
        if arc.target == self.transition_obj:
            # Arc points to this transition → source is input place
            input_places.append(arc.source)
    
    return input_places

def _generate_mm_template(self, input_places):
    """Generate Michaelis-Menten template based on input places."""
    if len(input_places) == 1:
        return f"michaelis_menten({input_places[0].name}, vmax=10.0, km=5.0)"
    elif len(input_places) == 2:
        # Sequential MM for two substrates
        return (
            f"michaelis_menten({input_places[0].name}, vmax=10.0, km=5.0) * "
            f"({input_places[1].name} / (5.0 + {input_places[1].name}))"
        )
    else:
        # Generic template
        return "michaelis_menten(substrate_place, vmax=10.0, km=5.0)"
```

---

### Phase 3: Product Inhibition Support (Week 3 - Optional)

**Goal**: Consider output places for product inhibition

#### Task 3.1: Detect Reversible Reactions

```python
def _build_context_aware_rate_function(
    self,
    substrate_places,
    product_places,
    vmax,
    km,
    reaction
):
    """
    Build rate function considering substrates, products, and reversibility.
    
    Formulas:
    1. Simple MM: michaelis_menten(S, Vmax, Km)
    2. Reversible (product inhibition): 
       michaelis_menten(S, Vmax, Km) / (1 + P/Ki)
    """
    
    # Base Michaelis-Menten
    base = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
    
    # Add sequential saturation for multiple substrates
    for substrate in substrate_places[1:]:
        base += f" * ({substrate.name} / ({km} + {substrate.name}))"
    
    # Add product inhibition if reversible
    if reaction.reversible and product_places:
        ki = km * 2.0  # Assume Ki ≈ 2*Km (typical)
        base += f" / (1 + {product_places[0].name}/{ki})"
        
        self.logger.info(
            f"    Added product inhibition: Ki={ki}"
        )
    
    return base
```

---

## Summary Plan

### Phase 1: Parameter Estimation (Week 1)

| Task | File | Lines | Status |
|------|------|-------|--------|
| 1.1 Create KineticParameterEstimator | `src/shypn/data/pathway/kinetic_parameter_estimator.py` | ~200 | 📋 TODO |
| 1.2 Integrate into PathwayConverter | `src/shypn/data/pathway/pathway_converter.py` | ~50 | 📋 TODO |
| 1.3 Add tests | `tests/test_kinetic_parameter_estimator.py` | ~100 | 📋 TODO |

**Deliverable**: SBML import estimates Vmax/Km when missing

### Phase 2: Dialog Pre-filling (Week 2)

| Task | File | Lines | Status |
|------|------|-------|--------|
| 2.1 Enhance dialog loader | `src/shypn/helpers/transition_prop_dialog_loader.py` | ~30 | 📋 TODO |
| 2.2 Add template generation | `src/shypn/helpers/transition_prop_dialog_loader.py` | ~50 | 📋 TODO |
| 2.3 Test dialog pre-filling | `tests/validation/ui/test_rate_function_prefill.py` | ~80 | 📋 TODO |

**Deliverable**: Transition dialog shows Michaelis-Menten formula

### Phase 3: Product Inhibition (Week 3 - Optional)

| Task | File | Lines | Status |
|------|------|-------|--------|
| 3.1 Detect reversibility | `src/shypn/data/pathway/pathway_converter.py` | ~40 | 📋 TODO |
| 3.2 Add product inhibition | `src/shypn/data/pathway/pathway_converter.py` | ~20 | 📋 TODO |
| 3.3 Test reversible reactions | `tests/test_reversible_reactions.py` | ~60 | 📋 TODO |

**Deliverable**: Reversible reactions include product inhibition

---

## Expected Results

### Before Enhancement

**SBML without kinetics**:
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="Glucose" stoichiometry="1"/>
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="G6P" stoichiometry="1"/>
  </listOfProducts>
</reaction>
```

**Result**:
```python
transition.transition_type = "continuous"
transition.rate = 1.0  # Generic
# NO rate_function
```

**Dialog**: Rate function field is empty

---

### After Enhancement ✨

**SBML without kinetics** (same):
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="Glucose" stoichiometry="1"/>
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="G6P" stoichiometry="1"/>
  </listOfProducts>
</reaction>
```

**Result**:
```python
transition.transition_type = "continuous"
transition.rate = 10.0  # Estimated Vmax
transition.properties['rate_function'] = "michaelis_menten(P_Glucose, 10.0, 5.0)"
# Parameters estimated from stoichiometry
```

**Dialog**: Rate function field shows:
```
michaelis_menten(P_Glucose, 10.0, 5.0)
```

**User can now**:
- See the formula immediately
- Edit Vmax/Km values
- Add complexity (product inhibition, etc.)
- Understand the reaction kinetics

---

## Testing Strategy

### Unit Tests

1. **Parameter Estimation**:
   ```python
   test_estimate_vmax_from_stoichiometry()
   test_estimate_km_from_concentrations()
   test_default_parameters_when_no_data()
   test_parameter_caching()
   ```

2. **Dialog Pre-filling**:
   ```python
   test_rate_function_from_properties()
   test_fallback_to_rate_attribute()
   test_template_generation()
   test_context_aware_suggestions()
   ```

3. **Integration**:
   ```python
   test_sbml_import_estimates_parameters()
   test_dialog_shows_estimated_formula()
   test_reversible_reactions_include_inhibition()
   ```

### Manual Testing

1. Import SBML without kinetics → Check if MM formula generated
2. Open transition dialog → Check if rate function pre-filled
3. Edit Vmax/Km → Check if formula updates
4. Save/reload → Check if formula persists

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Estimated parameters unrealistic | MEDIUM | MEDIUM | Provide UI to edit, document assumptions |
| Dialog doesn't update correctly | LOW | HIGH | Comprehensive UI tests |
| Performance impact on large pathways | LOW | LOW | Cache parameters, lazy evaluation |

### Biological Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Heuristics don't match real kinetics | HIGH | MEDIUM | Document as "estimates", allow user editing |
| Sequential MM not appropriate for all reactions | MEDIUM | LOW | Provide alternative formulas in catalog |

---

## Future Enhancements

1. **Database Lookup**: Query BRENDA/SABIO-RK for real kinetic parameters
2. **Machine Learning**: Train model to predict Vmax/Km from reaction characteristics
3. **Allosteric Regulation**: Support hill_equation for cooperative binding
4. **Competitive Inhibition**: Add competitive_inhibition() formula option

---

## Conclusion

This plan provides a comprehensive approach to:
1. ✅ **Auto-parameterize** Michaelis-Menten from stoichiometry
2. ✅ **Pre-fill** rate function dialog with realistic formulas
3. ✅ **Context-aware** using input/output places
4. ✅ **Infer** Vmax, Km from pathway structure

**Estimated Effort**: 2-3 weeks  
**Complexity**: HIGH (requires careful biochemical modeling)  
**Value**: HIGH (makes imported pathways immediately simulatable)

---

**Document Version**: 1.0  
**Last Updated**: October 18, 2025  
**Status**: 📋 PLANNING - Ready for Implementation
