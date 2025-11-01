# KEGG vs SBML Import: Arc Creation Analysis

## Date
November 1, 2025

## Executive Summary

Comparison of KEGG and SBML import flows regarding the three critical issues found in SBML:
1. **Arc Duplication** - KEGG: ✅ NOT VULNERABLE | SBML: ❌ FIXED
2. **Catalyst-Only Transitions** - KEGG: ✅ VALIDATES | SBML: ✅ NOW VALIDATES
3. **Mixed-Role Species** - KEGG: ⚠️ PARTIALLY VULNERABLE | SBML: ✅ NOW VALIDATES

---

## Issue 1: Arc Duplication (Same Species Multiple Times)

### SBML Flow (FIXED)

**Problem Pattern:**
```python
# SBML allows same species multiple times in reaction:
reaction.reactants = [("AMP", 1.0), ("AMP", 1.0)]  # DUPLICATE!
reaction.products = [("ATP", 2.0), ("ATP", 1.0)]   # DUPLICATE!

# OLD CODE (BUGGY):
for species_id, stoichiometry in reaction.reactants:
    arc = create_arc(place, transition, weight=stoichiometry)
    # Creates 2 separate arcs for AMP! ❌
```

**Fix Applied (Commit f37a58a):**
```python
# NEW CODE (FIXED):
reactant_weights = {}
for species_id, stoichiometry in reaction.reactants:
    reactant_weights[species_id] = reactant_weights.get(species_id, 0) + stoichiometry

for species_id, total_stoichiometry in reactant_weights.items():
    arc = create_arc(place, transition, weight=total_stoichiometry)
    # Creates 1 arc with aggregated weight ✅
```

### KEGG Flow (NOT VULNERABLE)

**Data Structure:**
```python
@dataclass
class KEGGSubstrate:
    id: str          # Entry ID (e.g., "5")
    name: str        # KEGG compound ID (e.g., "cpd:C00002")
    stoichiometry: int = 1

@dataclass
class KEGGReaction:
    substrates: List[KEGGSubstrate]  # Each substrate is separate object
    products: List[KEGGProduct]
```

**Arc Creation:**
```python
# KEGG arc_builder.py lines 67-98
for substrate in reaction.substrates:
    place = place_map.get(substrate.id)  # Maps to entry ID
    arc = Arc(place, transition, weight=substrate.stoichiometry)
    arcs.append(arc)
```

**Why KEGG is Safe:**

1. **KGML Format**: Each substrate/product is a separate XML element with unique entry ID
   ```xml
   <reaction id="rn1" name="rn:R00710" type="reversible">
     <substrate id="5" name="cpd:C00002"/>   <!-- Entry ID: 5 -->
     <substrate id="5" name="cpd:C00002"/>   <!-- SAME entry ID! -->
     <!-- This would be data error in KGML, extremely rare -->
   </reaction>
   ```

2. **Entry-Based Mapping**: KEGG uses entry IDs (not compound IDs) for mapping
   - Each visual node (entry) on KEGG map has unique ID
   - Even if same compound appears twice on map, they are different entries
   - `place_map` uses entry ID as key, not compound ID

3. **Real-World KEGG Data**: KEGG curators don't create duplicate entries
   - If compound participates multiple times, they use stoichiometry attribute
   - Example: `<substrate id="5" name="cpd:C00002" stoichiometry="2"/>`
   - NOT: Two separate `<substrate>` elements with same ID

**Conclusion**: ✅ **KEGG is NOT vulnerable** to arc duplication due to entry-based architecture.

---

## Issue 2: Catalyst-Only Transitions

### SBML Flow (NOW VALIDATED)

**Detection Added (Commit 09b82ec):**
```python
# PathwayConverter._validate_catalyst_only_transitions()
for transition in document.transitions:
    normal_inputs = [arc for arc in arcs if arc.target == transition and not isinstance(arc, TestArc)]
    test_inputs = [arc for arc in test_arcs if arc.target == transition]
    outputs = [arc for arc in arcs if arc.source == transition]
    
    if test_inputs and not normal_inputs and outputs:
        # WARNING: Transition has catalysts but no substrates!
```

**Found in curated SBML sources!**

### KEGG Flow (NATURALLY VALIDATED)

**KEGG Enzyme Converter:**
```python
# kegg/pathway_converter.py lines 51-133
class KEGGEnzymeConverter:
    def convert(self) -> List[TestArc]:
        for entry_id, entry in self.pathway.entries.items():
            if not entry.is_gene():  # Skip if not enzyme
                continue
            
            if not entry.reaction:   # Skip if no reaction attribute
                continue
            
            # Get transition for the reaction this enzyme catalyzes
            reaction_transition = self.reaction_name_to_transition.get(entry.reaction)
            if not reaction_transition:
                # No transition found → skip test arc creation
                continue
            
            # Create test arc: enzyme_place → reaction_transition
```

**Why KEGG Handles This Better:**

1. **Separate Reaction Objects**: KEGG reactions have explicit substrates/products
   ```xml
   <entry id="12" name="rn:R00710" type="map" reaction="rn:R00710">
     <!-- This is the REACTION entry -->
   </entry>
   
   <reaction id="rn1" name="rn:R00710" type="reversible">
     <substrate id="5" name="cpd:C00002"/>  <!-- MUST have substrates -->
     <product id="7" name="cpd:C00668"/>
   </reaction>
   
   <entry id="8" name="hsa:226" type="gene" reaction="rn:R00710">
     <!-- This is the ENZYME entry, links to reaction above -->
   </entry>
   ```

2. **Enzyme-Reaction Linkage**: Enzyme entries link to reactions that already exist
   - Enzyme converter only creates test arcs for reactions that already have transitions
   - Those transitions already have substrate/product arcs from reaction conversion
   - **Impossible to have enzyme test arc without substrate arcs**

3. **Validation by Architecture**:
   - Reactions converted first → transitions with normal arcs
   - Enzymes converted second → test arcs added to existing transitions
   - Order guarantees substrate arcs exist before test arcs added

**Conclusion**: ✅ **KEGG architecture naturally prevents catalyst-only transitions**

**However**: KEGG doesn't have explicit validation logging. Consider adding:
```python
# After enzyme conversion
if test_arcs:
    self.logger.info(f"Created {len(test_arcs)} enzyme test arcs")
    # Could add: verify all test arc targets have normal input arcs
```

---

## Issue 3: Mixed-Role Species (Substrate AND Catalyst)

### SBML Flow (NOW VALIDATED)

**Detection Added (Commit 09b82ec):**
```python
# PathwayConverter._validate_mixed_role_species()
species_roles = {}
for reaction in pathway.reactions:
    for species_id, _ in reaction.reactants:
        species_roles[species_id]['reactant_reactions'].append(reaction.id)
    for species_id, _ in reaction.products:
        species_roles[species_id]['product_reactions'].append(reaction.id)
    for species_id in reaction.modifiers:
        species_roles[species_id]['modifier_reactions'].append(reaction.id)

# Check for mixed roles
for species_id, roles in species_roles.items():
    if has_modifier and (has_reactant or has_product):
        # WARNING: Species is BOTH substrate AND catalyst!
```

**Example Warning:**
```
⚠️  Species 'AMP' has MIXED ROLES:
    - CATALYST in reactions: [R5, R12]
    - REACTANT in reactions: [R3, R7]
    
    Consuming as substrate depletes catalyst pool!
```

### KEGG Flow (PARTIALLY VULNERABLE)

**KEGG Enzyme Architecture:**
```python
# Enzyme entries link to reactions
entry.type = "gene"
entry.reaction = "rn:R00710"  # Links to one reaction

# That reaction has substrates/products
reaction.substrates = [substrate1, substrate2]
reaction.products = [product1, product2]
```

**Potential Issue:**

KEGG enzymes typically **don't appear as substrates** in the same pathway, BUT:

1. **Cofactor Compounds CAN be both**:
   ```xml
   <!-- ATP as substrate in Reaction A -->
   <reaction id="rn1" name="rn:R00761">
     <substrate id="5" name="cpd:C00002"/>  <!-- ATP consumed -->
     <product id="7" name="cpd:C00008"/>    <!-- ADP produced -->
   </reaction>
   
   <!-- ATP compound as "enzyme" link in Reaction B (rare but possible) -->
   <entry id="5" name="cpd:C00002" type="compound" reaction="rn:R00710">
     <!-- Compound linked to reaction → could create test arc -->
   </entry>
   ```

2. **KEGG Typically Doesn't Model This Way**:
   - Enzymes are `type="gene"` entries
   - Compounds are `type="compound"` entries
   - Compounds rarely have `reaction` attribute (used for allosteric regulation)
   - But **technically possible** in KGML format

**Current KEGG Code:**
```python
# KEGGEnzymeConverter only processes gene entries
if not entry.is_gene():  # Checks if type in ("gene", "enzyme", "ortholog")
    continue
```

**Vulnerability Check:**
- ✅ Gene entries won't be substrates (genes aren't consumed)
- ⚠️ **IF** KEGG uses compound entries with `reaction` attribute
- ⚠️ **AND** that compound is also a substrate/product
- ⚠️ **THEN** same catalyst depletion issue could occur

**Recommendation**: Add same validation to KEGG converter:
```python
# In KEGG PathwayConverter, after enzyme conversion
def _validate_mixed_role_compounds(self):
    """Check if any compounds act as both substrate/product AND catalyst."""
    compound_roles = {}
    
    for reaction in pathway.reactions:
        for substrate in reaction.substrates:
            # Check if this compound entry has reaction attribute
            entry = pathway.entries.get(substrate.id)
            if entry and entry.reaction:
                # This compound acts as catalyst for another reaction!
                compound_roles[substrate.id] = {
                    'substrate_in': reaction.name,
                    'catalyst_for': entry.reaction
                }
    
    if compound_roles:
        logger.warning(f"Found {len(compound_roles)} compounds with mixed roles")
```

**Conclusion**: ⚠️ **KEGG is PARTIALLY vulnerable** but extremely rare in practice.

---

## Implementation Recommendations

### For KEGG Converter

1. **Add Mixed-Role Validation** (Low Priority - Rare)
   ```python
   # In kegg/pathway_converter.py
   def _validate_mixed_role_compounds(self, pathway, document):
       """Detect compounds acting as both substrates and catalysts."""
       # Similar logic to SBML validation
   ```

2. **Add Explicit Validation Logging** (Nice-to-Have)
   ```python
   # After enzyme test arc creation
   logger.info(f"Verified {len(test_arcs)} enzymes have substrate arcs")
   ```

3. **No Arc Duplication Fix Needed** ✅
   - Architecture prevents it

### For SBML Converter

1. ✅ **Arc Duplication** - FIXED (Commit f37a58a)
2. ✅ **Catalyst-Only Detection** - IMPLEMENTED (Commit 09b82ec)
3. ✅ **Mixed-Role Detection** - IMPLEMENTED (Commit 09b82ec)

---

## Summary Table

| Issue | SBML Status | KEGG Status | Priority |
|-------|-------------|-------------|----------|
| **Arc Duplication** | ✅ Fixed | ✅ Not Vulnerable | N/A |
| **Catalyst-Only Transitions** | ✅ Validates | ✅ Architecture Prevents | Low (add logging) |
| **Mixed-Role Species** | ✅ Validates | ⚠️ Possible but Rare | Low (add validation) |

---

## Files Referenced

**SBML Import:**
- `src/shypn/data/pathway/pathway_converter.py` - Main converter with fixes
- `src/shypn/data/pathway/sbml_parser.py` - SBML XML parsing

**KEGG Import:**
- `src/shypn/importer/kegg/pathway_converter.py` - Main converter
- `src/shypn/importer/kegg/arc_builder.py` - Arc creation logic
- `src/shypn/importer/kegg/models.py` - Data structures
- `src/shypn/importer/kegg/kgml_parser.py` - KGML XML parsing

**Related Documentation:**
- `doc/SBML_MODELING_ERROR_CATALYST_ONLY.md` - SBML issues documentation

---

**Status**: Analysis complete  
**Next Steps**: Consider adding mixed-role validation to KEGG (low priority)
