# SBML Modeling Error: Catalyst-Only Transitions

## Discovery Date
November 1, 2025

## Issue Description

Found a **modeling error in curated SBML sources** where transitions have:
- ✅ Test arcs from catalyst/enzyme places (modifiers)
- ❌ **NO normal input arcs** (no reactant/substrate arcs)
- ✅ Output arcs to product places

This creates **blocked transitions** that cannot fire in Petri net simulation.

## Example from Imported Model

```
AMP Place (1 token)
    |
    | [test arc - dashed line with diamond]
    ↓
Transition (Aldolase...)
    |
    | [normal arc - solid line]
    ↓
Product Place
```

**Problem**: The transition has a catalyst (AMP via test arc) but **no substrate** (no normal input arcs). The test arc is non-consuming, so:
1. Test arc checks: "Does AMP have ≥1 token?" → YES ✓
2. Normal input arcs: NONE → Transition **cannot fire** ❌

## Biochemical Interpretation

This represents one of two scenarios:

### Scenario 1: Missing Substrate (Modeling Error)
The SBML model is **incomplete** - it should have reactants but they're missing:

```xml
<reaction id="R123">
  <listOfModifiers>
    <modifierSpeciesReference species="AMP"/>  <!-- Catalyst present -->
  </listOfModifiers>
  <listOfReactants>
    <!-- MISSING: Should have substrate here! -->
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="Product" stoichiometry="1"/>
  </listOfProducts>
</reaction>
```

**Fix**: Add missing reactants to SBML model.

### Scenario 2: Source Transition (Correct, but needs marking)
The reaction represents **external input** (de novo synthesis, import from environment):

```xml
<reaction id="R123">
  <listOfModifiers>
    <modifierSpeciesReference species="AMP"/>  <!-- Rate modulator -->
  </listOfModifiers>
  <listOfReactants>
    <!-- Intentionally empty - external source -->
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="Product" stoichiometry="1"/>
  </listOfProducts>
</reaction>
```

**Fix**: Mark transition as `is_source=True` in Petri net to enable continuous firing.

## Impact on Petri Net Simulation

### Current Behavior
- Transition is created with test arc from catalyst
- Transition has no normal input arcs
- **Transition is permanently disabled** (enablement rule requires input tokens)
- Simulation cannot progress through this transition

### Expected Behavior (if source)
- Transition should be marked as source
- Transition fires continuously (catalyst modulates rate)
- Produces tokens to output places

### Expected Behavior (if error)
- Warning logged during import
- User notified of incomplete model
- Suggest adding substrates or marking as source

## Detection Strategy

In `PathwayConverter`, after creating arcs and test arcs:

```python
# Detect transitions with only test arcs (no normal input arcs)
for transition in document.transitions:
    # Count normal input arcs
    normal_inputs = [arc for arc in document.arcs 
                    if arc.target == transition 
                    and not isinstance(arc, TestArc)]
    
    # Count test arcs
    test_inputs = [arc for arc in document.arcs 
                  if arc.target == transition 
                  and isinstance(arc, TestArc)]
    
    # Count output arcs
    outputs = [arc for arc in document.arcs 
              if arc.source == transition]
    
    # PROBLEM PATTERN: test arcs but no normal inputs
    if test_inputs and not normal_inputs and outputs:
        self.logger.warning(
            f"⚠️  MODELING ERROR: Transition '{transition.name}' has:\n"
            f"    - {len(test_inputs)} catalyst/modifier arcs (test arcs)\n"
            f"    - 0 reactant arcs (normal input arcs)\n"
            f"    - {len(outputs)} product arcs (output arcs)\n"
            f"    This transition CANNOT FIRE (no substrates to consume)!\n"
            f"    \n"
            f"    Possible fixes:\n"
            f"    1. Add missing reactant species to SBML model\n"
            f"    2. Mark transition as SOURCE if this represents external input\n"
            f"    3. Check if catalyst should be a reactant instead of modifier"
        )
```

## Validation Rules

### Valid Patterns

✅ **Normal transition with catalyst:**
```
Substrate --[normal]--> Transition --> Product
Enzyme   --[test]---↗
```

✅ **Source transition (no inputs):**
```
                        Transition --> Product
(is_source=True)
```

✅ **Source transition with catalyst modulation:**
```
Enzyme --[test]--> Transition --> Product
                   (is_source=True)
```

### Invalid Patterns

❌ **Catalyst-only (blocked):**
```
Enzyme --[test]--> Transition --> Product
(is_source=False, no normal inputs)
```

## Recommendation

**Implement detection and warning system** in next import iteration:
1. Scan all transitions after conversion
2. Identify catalyst-only pattern
3. Log warning with actionable suggestions
4. Consider adding UI dialog for user decision:
   - "Mark as source transition?"
   - "Review SBML model for missing substrates?"

## Related Files

- `src/shypn/data/pathway/pathway_converter.py` - Main converter
- `src/shypn/netobjs/test_arc.py` - Test arc implementation
- `src/shypn/netobjs/transition.py` - Transition with source/sink markers

## Related Issue: Catalyst Depletion Conflict

### Problem Pattern
When the SAME species has **BOTH roles** across different reactions:
- **Substrate/Product** in some reactions (normal arcs - consuming)
- **Catalyst/Modifier** in other reactions (test arcs - non-consuming)

### Example

```
Reaction A:
  AMP --[normal arc]--> Transition A --> Product1
  (AMP consumed as reactant)

Reaction B:
  AMP --[test arc]--> Transition B --> Product2
  (AMP acts as catalyst)
```

### Conflict Scenario

```
Time T0: AMP has 1 token

Step 1: Reaction A fires
  - Consumes AMP via normal arc
  - AMP tokens: 1 → 0

Step 2: Reaction B tries to fire
  - Test arc checks: "AMP ≥ 1 token?"
  - Result: FALSE (AMP has 0 tokens)
  - Reaction B is DISABLED ❌
```

**Problem**: Consuming AMP as substrate **depletes the catalyst pool**, preventing catalyzed reactions from firing!

### Biochemical Interpretation

**Two possibilities:**

1. **Modeling Error** - Species should be split:
   ```
   AMP_free (used as substrate)
   AMP_enzyme_bound (acts as catalyst)
   → Should be separate places in model
   ```

2. **Correct Model** - Real resource competition:
   ```
   Limited pool of AMP molecules
   Compete for use as:
   - Substrate (consumed in energy reactions)
   - Allosteric regulator (modulates enzyme activity)
   
   When depleted as substrate → regulation fails
   This IS realistic for cofactors like ATP/AMP!
   ```

### Detection Strategy

Check for species with **mixed roles** across reactions:

```python
# Track species roles across all reactions
species_roles = {}

for reaction in pathway.reactions:
    # Track reactants
    for species_id, _ in reaction.reactants:
        species_roles.setdefault(species_id, set()).add('reactant')
    
    # Track products
    for species_id, _ in reaction.products:
        species_roles.setdefault(species_id, set()).add('product')
    
    # Track modifiers
    for species_id in reaction.modifiers:
        species_roles.setdefault(species_id, set()).add('modifier')

# Identify mixed-role species
for species_id, roles in species_roles.items():
    if 'modifier' in roles and ('reactant' in roles or 'product' in roles):
        # WARN: Species acts as BOTH substrate AND catalyst
        logger.warning(f"Species '{species_id}' has mixed roles: {roles}")
```

### Warning Message

```
⚠️  Species 'AMP' has MIXED ROLES:
    - Acts as CATALYST (modifier) in reactions: [R5, R12]
    - Acts as SUBSTRATE (reactant) in reactions: [R3, R7]
    - Acts as PRODUCT in reactions: [R1, R9]
    
    ⚠️  POTENTIAL ISSUE: Consuming this species as substrate
    will DEPLETE the catalyst pool, disabling catalyzed reactions!
    
    This may represent:
    1. ✅ Correct model (resource competition for limited cofactor)
    2. ❌ Modeling error (should be separate species/compartments)
    
    Review SBML model to verify intended semantics.
```

## Examples in Wild

Found in: **[Specify SBML model where this was discovered]**
- Model name: [TBD]
- Reaction ID: [TBD]
- Species involved: AMP (catalyst), [Product]

---

**Status**: Issues documented, detection implementation in progress  
**Priority**: High (affects simulation correctness and biological accuracy)  
**Next Steps**: 
1. ✅ Implement catalyst-only transition detection
2. ✅ Implement mixed-role species detection
3. Commit both validation warnings
