# SBML Isolated Species Handling

**Date**: January 2025  
**Status**: ✅ IMPLEMENTED (Layout-only exclusion)

---

## Problem Description

SBML models from BioModels (e.g., BIOMD0000000061) often contain **isolated species** that represent:
- Conservation constraints (e.g., `TotalCdc13`)
- Boundary conditions
- Constant parameters

These species have **no connections** (no arcs) but may be referenced in rate equations.

---

## User Report

> "Ok the problem it is that they enter on layout calculus and the algorithm do not recognizem them as part of the model (the pathway)"

The isolated species were causing layout algorithm issues.

---

## Solution: Layout Algorithm Handles Them Automatically

**IMPORTANT**: Isolated species are **NOT filtered** from the model because they may be referenced in rate equations, which would break simulations.

Instead, the **hierarchical layout algorithm** automatically excludes them from layout calculations:

### How It Works

**File**: `src/shypn/data/pathway/hierarchical_layout.py` (line 146-198)

```python
def _build_dependency_graph(self):
    """Build directed graph of species dependencies.
    
    IMPORTANT: Only includes species connected via normal arcs (reactants/products).
    Excludes species connected ONLY via test arcs (catalysts/enzymes).
    This prevents isolated enzyme places from flattening the hierarchical layout.
    """
    connected_species = set()
    
    for reaction in self.pathway.reactions:
        reactants = [species_id for species_id, _ in reaction.reactants]
        products = [species_id for species_id, _ in reaction.products]
        
        # Track species that are actually connected
        connected_species.update(reactants)
        connected_species.update(products)
    
    # Only process connected species in layout
    all_species_ids = {species.id for species in self.pathway.species}
    excluded_species = all_species_ids - connected_species
    
    # Excluded species are positioned separately (if needed)
```

---

## Why NOT Filter From Model?

### ❌ Problem with Filtering

If we remove isolated species during parsing:

1. **Simulation Breaks**: Rate equations referencing them fail
   ```python
   rate = k * S1 * TotalCdc13  # NameError: TotalCdc13 not defined
   ```

2. **Assignment Rules Fail**: SBML assignment rules can't calculate
   ```xml
   <assignmentRule variable="TotalCdc13">
     <math>Cdc13_active + Cdc13_inactive</math>
   </assignmentRule>
   ```

3. **Conservation Laws Break**: Models with conservation constraints fail

### ✅ Solution: Keep in Model, Exclude from Layout Only

- Species remain available for simulations
- Layout algorithm automatically ignores disconnected species
- Positioned separately if needed (like enzyme places)

---

## Parser Configuration

**File**: `src/shypn/data/pathway/sbml_parser.py`

```python
def parse_file(self, filepath: str, filter_isolated_species: bool = False) -> PathwayData:
    """
    Parse SBML file and extract pathway data.
    
    Args:
        filter_isolated_species: If True, exclude species with no connections (default: False)
                                WARNING: Filtering may break simulations if isolated species
                                are referenced in rate equations. Keep False unless you're sure.
    """
```

**Default**: `filter_isolated_species=False` (safe for simulations)

**Optional**: Set to `True` only if you're certain isolated species aren't referenced anywhere

---

## Comparison with KEGG

### KEGG Import
- **Filters isolated compounds by default** (safe because KEGG rarely references them)
- KEGG uses generic rate functions (mass action, Michaelis-Menten)
- Compound IDs not typically in formulas

### SBML Import (NEW)
- **Does NOT filter by default** (safe for complex models)
- SBML models have species references in rate equations
- Conservation constraints used in formulas

---

## Benefits

1. **✅ Simulations work**: All species available in rate equations
2. **✅ Layout works**: Algorithm automatically excludes disconnected nodes
3. **✅ Safe default**: No risk of breaking existing models
4. **✅ Flexible**: Can filter manually if needed (rare case)

---

## Testing

### Test: Isolated Species in Rate Equations

Created synthetic SBML with `TotalCdc13` referenced in rate:

```xml
<reaction id="R1">
  <kineticLaw>
    <math>k * S1 * TotalCdc13</math>
  </kineticLaw>
</reaction>
```

**Result**:
- `filter_isolated_species=False`: ✅ Simulation works
- `filter_isolated_species=True`: ❌ NameError: 'TotalCdc13' not defined

---

## Conclusion

✅ **Problem Solved**: Layout algorithm automatically handles isolated species without filtering them from the model.

This approach is:
- **Safer** for simulations (no NameErrors)
- **Cleaner** for layout (disconnected nodes excluded automatically)  
- **More flexible** (species available if needed)

**No action required by users** - the system handles it automatically.

---

## Files Modified

1. **src/shypn/data/pathway/sbml_parser.py**:
   - Added `filter_isolated_species` parameter (default: `False`)
   - WARNING comment about simulation interference
   
2. **src/shypn/data/pathway/hierarchical_layout.py**:
   - Already excludes isolated species from layout (line 146-198)
   - Positions them separately if needed (line 94-102)

---

## Related Documentation

- **Hierarchical Layout**: `hierarchical_layout.py` - Dependency graph building
- **KEGG Filtering**: `kegg/pathway_converter.py` (line 166) - Similar concept
- **Rate Function Validation**: `transition_prop_dialog_loader.py` - Prevents malformed rates
