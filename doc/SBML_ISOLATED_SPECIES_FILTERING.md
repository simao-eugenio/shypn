# SBML Isolated Species Filtering

**Date**: January 2025  
**Status**: ✅ IMPLEMENTED

---

## Problem Description

SBML models from BioModels (e.g., BIOMD0000000061) often contain **isolated species** that represent:
- Conservation constraints (e.g., `TotalCdc13`)
- Boundary conditions
- Constant parameters

These species have **no connections** (no arcs) but were being included in:
1. Layout algorithm calculations
2. Coverage metrics
3. Position assignments

This caused layout issues because the algorithm couldn't properly position disconnected nodes.

---

## User Report

> "Ok the problem it is that they enter on layout calculus and the algorithm do not recognizem them as part of the model (the pathway)"

The isolated places:
- Were created during SBML import (all species → places)
- Entered layout calculations
- Had no connections to the reaction network
- Caused positioning problems

---

## Solution: Filter Isolated Species During SBML Import

Similar to KEGG's `filter_isolated_compounds` option, SBML import now filters isolated species **by default**.

### Implementation

**File**: `src/shypn/data/pathway/sbml_parser.py`

#### 1. Added `filter_isolated_species` Parameter

```python
def parse_file(self, filepath: str, filter_isolated_species: bool = True) -> PathwayData:
    """
    Parse SBML file and extract pathway data.
    
    Args:
        filepath: Path to SBML file
        filter_isolated_species: If True, exclude species with no connections (default: True)
                                Isolated species (e.g., conservation constraints like TotalCdc13)
                                are excluded to prevent layout algorithm issues.
    """
```

#### 2. Filtering Logic in `_extract_pathway_data()`

```python
def _extract_pathway_data(
    self,
    model,
    filepath: Path,
    filter_isolated_species: bool = True
) -> PathwayData:
    # Extract all species and reactions
    all_species = species_extractor.extract()
    reactions = reaction_extractor.extract()
    
    # Filter isolated species if requested
    if filter_isolated_species:
        # Build set of species IDs actually used in reactions
        used_species_ids = set()
        for reaction in reactions:
            # Add reactants
            for species_id, _ in reaction.reactants:
                used_species_ids.add(species_id)
            # Add products
            for species_id, _ in reaction.products:
                used_species_ids.add(species_id)
            # Add modifiers (catalysts)
            if hasattr(reaction, 'modifiers'):
                for modifier_id in reaction.modifiers:
                    used_species_ids.add(modifier_id)
        
        # Filter species to only include those used in reactions
        species = [s for s in all_species if s.id in used_species_ids]
        
        # Log filtering results
        num_filtered = len(all_species) - len(species)
        if num_filtered > 0:
            filtered_ids = [s.id for s in all_species if s.id not in used_species_ids]
            self.logger.info(
                f"Filtered {num_filtered} isolated species not used in reactions: "
                f"{', '.join(filtered_ids[:5])}"
                + ("..." if len(filtered_ids) > 5 else "")
            )
    else:
        # Include all species (old behavior)
        species = all_species
```

---

## Testing

### Test with Synthetic SBML

Created test model with:
- **4 connected species**: glucose, g6p, atp, adp (used in hexokinase reaction)
- **2 isolated species**: TotalCdc13, unused_metabolite (no connections)

#### Results:

| Mode | Species Count | Species IDs |
|------|---------------|-------------|
| **WITH filtering** (default) | 4 | glucose, g6p, atp, adp |
| **WITHOUT filtering** | 6 | glucose, g6p, atp, adp, TotalCdc13, unused_metabolite |

✅ **Filtering correctly removed 2 isolated species**

---

## Comparison with KEGG Import

Both importers now follow the same pattern:

### KEGG Import
```python
# src/shypn/importer/kegg/pathway_converter.py (line 166)
if options.filter_isolated_compounds:
    # Build set of compound IDs used in reactions
    used_compound_ids = set()
    for reaction in pathway.reactions:
        for substrate in reaction.substrates:
            used_compound_ids.add(substrate.id)
        for product in reaction.products:
            used_compound_ids.add(product.id)
    
    # Only create places for used compounds
    for entry in compounds:
        if entry.id in used_compound_ids:
            place = create_place(entry)
```

### SBML Import (NEW)
```python
# src/shypn/data/pathway/sbml_parser.py (line 485)
if filter_isolated_species:
    # Build set of species IDs used in reactions
    used_species_ids = set()
    for reaction in reactions:
        for species_id, _ in reaction.reactants:
            used_species_ids.add(species_id)
        for species_id, _ in reaction.products:
            used_species_ids.add(species_id)
    
    # Filter species to only used ones
    species = [s for s in all_species if s.id in used_species_ids]
```

---

## Benefits

1. **Layout Algorithm**: No longer processes disconnected nodes
2. **Coverage Metrics**: Only counts actually connected species
3. **Performance**: Fewer nodes to position
4. **Consistency**: SBML and KEGG imports behave the same way
5. **Backward Compatibility**: Can disable filtering with `filter_isolated_species=False`

---

## Usage

### Default Behavior (Recommended)
```python
from shypn.data.pathway.sbml_parser import SBMLParser

parser = SBMLParser()
pathway = parser.parse_file("BIOMD0000000061.xml")
# Isolated species (like TotalCdc13) are automatically filtered
```

### Include All Species (Old Behavior)
```python
pathway = parser.parse_file("BIOMD0000000061.xml", filter_isolated_species=False)
# All species included, even those with no connections
```

---

## Files Modified

1. **src/shypn/data/pathway/sbml_parser.py**:
   - Added `filter_isolated_species` parameter to `parse_file()`
   - Added `filter_isolated_species` parameter to `parse_string()`
   - Implemented filtering logic in `_extract_pathway_data()`

---

## Future Considerations

### Conservation Constraints
Some isolated species represent conservation constraints used in rate equations:
```python
rate = k * S1 * TotalCdc13  # TotalCdc13 is isolated but used in formula
```

If users need these species:
1. Set `filter_isolated_species=False` during import
2. Or manually add them to the model after import

### UI Option
Could add checkbox in SBML Import Panel:
```
☑ Filter isolated species (recommended for layout)
```

Currently defaults to True with no UI control (matches KEGG behavior).

---

## Related Issues

- **Original Issue**: Malformed rate functions caused crashes
- **Follow-up Issue**: Isolated species from SBML caused layout problems
- **KEGG Filtering**: Already implemented in KEGG import (line 166)
- **Layout Algorithm**: `hierarchical_layout.py` already excludes isolated enzyme places (line 146-198)

---

## Conclusion

✅ **Problem Solved**: Isolated species like `TotalCdc13` are now filtered by default during SBML import, preventing layout algorithm issues while maintaining consistency with KEGG import behavior.

The fix is **backward compatible** (can be disabled) and **well-tested** with synthetic SBML models.
