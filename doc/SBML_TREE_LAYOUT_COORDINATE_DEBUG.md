# SBML Tree Layout Coordinate Debugging

**Date**: October 12, 2025  
**Issue**: Some places and transitions getting spurious coordinates during SBML import  
**Status**: ✅ Diagnostic logging added, fallback coordinates identified

## Problem Analysis

During SBML import with tree layout, some objects were receiving "spurious" or unexpected coordinates. These are typically fallback/default coordinates used when the layout algorithm cannot calculate proper positions.

## Fallback Coordinates Identified

### Species (Places)
- **Fallback**: `(100.0, 100.0)`
- **When used**: Species ID not found in `processed.positions` dictionary
- **File**: `pathway_converter.py` line 83
- **Now logs**: ⚠️ Warning when fallback is used

### Reactions (Transitions)
- **Fallback 1**: `(200.0, 200.0)`
  - When used: Reaction ID not found in `processed.positions` dictionary
  - File: `pathway_converter.py` line 163
  - Now logs: ⚠️ Warning when fallback is used

- **Fallback 2**: `(400.0, 300.0)`
  - When used: Reaction has no valid connections (no reactants or products with positions)
  - File: `tree_layout.py` line 516
  - Now logs: ⚠️ Warning when fallback is used

## Root Causes

### 1. Missing Species Positions
**Cause**: Layout algorithm didn't process all species in pathway

**Possible reasons**:
- Species not connected to any reaction (isolated)
- Species in cyclic dependencies that break topological sort
- Species not in dependency graph

**Detection**: Now logged with warning message

### 2. Missing Reaction Positions  
**Cause**: Reaction positions not calculated by tree layout

**Possible reasons**:
- Reactants or products missing from `species_positions`
- Reaction has no reactants or products
- Reaction references species not in pathway

**Detection**: Now logged with detailed warnings:
- Missing reactant positions
- Missing product positions
- No valid connections

### 3. Isolated or Boundary Species
**Symptoms**: Species at `(100.0, 100.0)` or reactions at `(200.0, 200.0)` or `(400.0, 300.0)`

**Common in**:
- SBML models with boundary/external species
- Models with enzymatic modifiers not connected through stoichiometry
- Cofactors that appear in many reactions but aren't consumed/produced

## Fixes Applied

### 1. Added Diagnostic Logging

**Species Converter** (`pathway_converter.py`):
```python
if species.id not in self.pathway.positions:
    self.logger.warning(
        f"Species '{species.id}' has no position, using fallback (100.0, 100.0)"
    )
```

**Reaction Converter** (`pathway_converter.py`):
```python
if reaction.id not in self.pathway.positions:
    self.logger.warning(
        f"Reaction '{reaction.id}' has no position, using fallback (200.0, 200.0)"
    )
```

**Reaction Positioning** (`tree_layout.py`):
```python
# Warn about missing species
if missing_reactants:
    self.logger.warning(
        f"Reaction '{reaction.id}' missing reactant positions: {missing_reactants}"
    )
if missing_products:
    self.logger.warning(
        f"Reaction '{reaction.id}' missing product positions: {missing_products}"
    )

# ...

else:
    # No valid connections: use default position
    self.logger.warning(
        f"Reaction '{reaction.id}' has no valid connections, "
        f"using fallback position (400.0, 300.0)"
    )
```

### 2. Created Diagnostic Tool

**File**: `test_sbml_coordinates.py`

**Usage**:
```bash
# Test with internal pathway
python3 test_sbml_coordinates.py

# Test with SBML file
python3 test_sbml_coordinates.py data/my_pathway.xml
```

**Checks for**:
- Invalid coordinates (NaN, Inf)
- Statistical outliers (> 3 std devs)
- Default/fallback coordinates (100,100), (200,200), (400,300)
- Overlapping coordinates
- Full coordinate listing

## How to Use

### Step 1: Import SBML with logging
```bash
cd /home/simao/projetos/shypn
PYTHONPATH=src:$PYTHONPATH python3 -c "
import logging
logging.basicConfig(level=logging.WARNING)

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor

parser = SBMLParser()
pathway = parser.parse('path/to/your/file.xml')

postprocessor = PathwayPostProcessor(use_tree_layout=True)
processed = postprocessor.process(pathway)

print(f'Processed {len(processed.species)} species')
print(f'Positioned {len(processed.positions)} objects')
"
```

### Step 2: Check warnings
Look for warning messages like:
- `⚠️  Species 'X' has no position, using fallback (100.0, 100.0)`
- `⚠️  Reaction 'R1' missing reactant positions: ['species_5']`
- `⚠️  Reaction 'R2' has no valid connections, using fallback position (400.0, 300.0)`

### Step 3: Analyze with diagnostic tool
```bash
python3 test_sbml_coordinates.py your_file.xml
```

This will show:
- Which objects got fallback coordinates
- Statistical analysis of coordinate distribution
- Potential overlaps or outliers

## Solutions for Common Issues

### Issue: Isolated Species
**Symptom**: Species at (100, 100) with no connections

**Solutions**:
1. **Remove from SBML**: If truly isolated, remove from model
2. **Add connections**: Connect to pathway if meant to be included
3. **Accept fallback**: If it's a boundary species, fallback may be acceptable
4. **Manual positioning**: After import, manually reposition in UI

### Issue: Enzymatic Modifiers
**Symptom**: Enzymes/cofactors at (100, 100) or reactions at (400, 300)

**SBML problem**: Modifiers aren't reactants/products, so they don't create edges in dependency graph

**Solutions**:
1. **Use boundary species flag**: Mark as boundary species
2. **Position near reactions**: After import, manually place near relevant reactions
3. **Future enhancement**: Add modifier positioning logic to tree layout

### Issue: Cyclic Pathways
**Symptom**: Some species in last layer instead of proper cycle position

**Tree layout limitation**: Tree algorithm assumes acyclic structure

**Solutions**:
1. **Use force-directed layout**: Better for cyclic pathways
2. **Break cycles**: Identify and break feedback loops conceptually
3. **Future enhancement**: Implement circular layout option

### Issue: Boundary/External Species
**Symptom**: Source/sink species at (100, 100)

**Expected behavior**: Boundary species may not be in dependency graph

**Solutions**:
1. **Mark as boundary**: Use SBML boundaryCondition attribute
2. **Position at edges**: After import, place at top (sources) or bottom (sinks)
3. **Future enhancement**: Detect boundary species and position automatically

## Testing

### Test 1: Simple Linear Pathway
```python
from shypn.data.pathway.pathway_data import Species, Reaction, PathwayData
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor

s1 = Species(id='s1', name='S1', initial_concentration=10.0)
s2 = Species(id='s2', name='S2', initial_concentration=0.0)
s3 = Species(id='s3', name='S3', initial_concentration=0.0)

r1 = Reaction(id='r1', name='R1', reactants=[('s1', 1.0)], products=[('s2', 1.0)])
r2 = Reaction(id='r2', name='R2', reactants=[('s2', 1.0)], products=[('s3', 1.0)])

pathway = PathwayData(species=[s1, s2, s3], reactions=[r1, r2], compartments={}, metadata={'name': 'Linear'})
postprocessor = PathwayPostProcessor(use_tree_layout=True)
processed = postprocessor.process(pathway)

# Should show: s1 → r1 → s2 → r2 → s3 vertically
# Expected: No warnings
```

### Test 2: Branching Pathway
```python
# Test included in test_sbml_coordinates.py
# Run: python3 test_sbml_coordinates.py
# Expected: No warnings, proper tree structure
```

### Test 3: With Isolated Species
```python
s1 = Species(id='s1', name='S1', initial_concentration=10.0)
s2 = Species(id='s2', name='S2', initial_concentration=0.0)
isolated = Species(id='isolated', name='Isolated', initial_concentration=5.0)  # Not in any reaction

r1 = Reaction(id='r1', name='R1', reactants=[('s1', 1.0)], products=[('s2', 1.0)])

pathway = PathwayData(species=[s1, s2, isolated], reactions=[r1], compartments={}, metadata={'name': 'With Isolated'})
postprocessor = PathwayPostProcessor(use_tree_layout=True)
processed = postprocessor.process(pathway)

# Expected: ⚠️ Warning about 'isolated' using fallback (100.0, 100.0)
```

## Future Enhancements

### Priority 1: Boundary Species Detection
- Detect species with boundaryCondition=true
- Position sources at top, sinks at bottom
- Use different visual markers

### Priority 2: Modifier Positioning
- Extract modifier relationships from SBML
- Position modifiers near their reactions
- Use different arc type (dashed/colored)

### Priority 3: Circular Layout Option
- Detect cyclic pathways (TCA cycle, etc.)
- Implement circular/radial layout
- Auto-select based on pathway topology

### Priority 4: Manual Override
- Allow user to specify positions for specific species
- Respect manual positions during layout
- Save manual adjustments with model

## Related Documentation

- `doc/SBML_IMPORT_FLOW_ANALYSIS.md` - SBML import pipeline
- `doc/COORDINATE_SYSTEM.md` - Coordinate system details
- `src/shypn/data/pathway/tree_layout.py` - Tree layout implementation
- `src/shypn/data/pathway/pathway_converter.py` - Pathway to Petri net conversion
- `src/shypn/data/pathway/hierarchical_layout.py` - Layout processor coordination

## Files Modified

1. **`src/shypn/data/pathway/tree_layout.py`**
   - Added warning for reactions with no valid connections
   - Added warnings for missing reactant/product positions

2. **`src/shypn/data/pathway/pathway_converter.py`**
   - Added warning for species with no position
   - Added warning for reactions with no position

3. **`test_sbml_coordinates.py`** (new)
   - Diagnostic tool for analyzing coordinates
   - Detects outliers, defaults, overlaps, invalid values

---

**Status**: Diagnostic logging complete  
**Next**: User testing with actual SBML files to identify specific cases  
**Action**: Run `python3 test_sbml_coordinates.py your_file.xml` to diagnose coordinate issues
