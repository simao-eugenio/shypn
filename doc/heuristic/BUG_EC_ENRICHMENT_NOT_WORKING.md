# CRITICAL BUG: EC Enrichment Not Working

**Date**: October 19, 2025  
**Severity**: HIGH  
**Status**: Under Investigation  

---

## Problem Statement

Despite:
1. ✅ "Metadata enhancement" checkbox checked by default in KEGG import
2. ✅ `ConversionOptions.enhance_kinetics = True` by default (line 53, converter_base.py)
3. ✅ Bug fixes applied (commits 154f8ba, 358237d)
4. ✅ Files created AFTER bug fixes

**Result**: **0% of imported KEGG pathways have EC numbers in transition metadata**

---

## Evidence

### File 1: `Glycolysis_enriched_Gluconeogenesis.shy`
- **Created**: 2025-10-19 03:42 (39 min AFTER bug fixes)
- **Transitions**: 34 total (12 continuous, 22 stochastic)
- **EC Enrichment**: **0/34 transitions** (0%)
- **Metadata check**: No `ec_numbers` found in any transition

### File 2: `Glycolysis_last_Gluconeogenesis.shy`
- **Created**: 2025-10-19 03:34 (30 min AFTER bug fixes)
- **Transitions**: 39 total (12 continuous, 27 stochastic)
- **EC Enrichment**: **0/39 transitions** (0%)
- **Metadata check**: No `ec_numbers` found in any transition

---

## Expected vs Actual

### Expected Metadata Structure
```json
{
  "metadata": {
    "ec_numbers": ["2.7.1.1", "2.7.1.2"],
    "enzyme_name": "Hexokinase",
    "kinetics_confidence": "high",
    "kinetics_source": "database",
    "kegg_reaction_id": "61",
    "kegg_reaction_name": "rn:R00299"
  }
}
```

### Actual Metadata
```json
{
  "metadata": {
    "kegg_reaction_id": "61",
    "kegg_reaction_name": "rn:R00299",
    "source": "KEGG",
    "reversible": true
    // NO ec_numbers
    // NO enzyme_name
    // NO kinetics_confidence
  }
}
```

---

## Code Flow Analysis

### 1. UI Layer
**File**: `src/shypn/helpers/kegg_import_panel.py`

**Line 98**: Checkbox widget
```python
self.enhancement_metadata_check = self.builder.get_object('enhancement_metadata_check')
```

**Line 260**: Checkbox value read
```python
enable_metadata = self.enhancement_metadata_check.get_active() if self.enhancement_metadata_check else True
```

**Line 267**: Passed to EnhancementOptions
```python
enhancement_options = EnhancementOptions(
    enable_layout_optimization=enable_layout,
    enable_arc_routing=enable_arcs,
    enable_metadata_enhancement=enable_metadata  # ← Checkbox value
)
```

**Line 272**: Conversion called
```python
document_model = convert_pathway_enhanced(
    self.current_pathway,
    coordinate_scale=coordinate_scale,
    include_cofactors=filter_cofactors,
    enhancement_options=enhancement_options
    # NOTE: estimate_kinetics NOT passed, defaults to True
)
```

### 2. Conversion Layer
**File**: `src/shypn/importer/kegg/pathway_converter.py`

**Line 399**: convert_pathway() called
```python
document = convert_pathway(
    pathway=pathway,
    coordinate_scale=coordinate_scale,
    include_cofactors=include_cofactors,
    split_reversible=split_reversible,
    add_initial_marking=add_initial_marking,
    filter_isolated_compounds=filter_isolated_compounds
    # NOTE: enhance_kinetics NOT passed, should default to True
)
```

**Line 327**: ConversionOptions created in convert_pathway()
```python
options = ConversionOptions(
    coordinate_scale=coordinate_scale,
    include_cofactors=include_cofactors,
    split_reversible=split_reversible,
    add_initial_marking=add_initial_marking,
    filter_isolated_compounds=filter_isolated_compounds
    # NOTE: enhance_kinetics NOT explicitly set, should use default=True
)
```

### 3. PathwayConverter.convert()
**File**: `src/shypn/importer/kegg/pathway_converter.py`

**Line 92**: Kinetics enhancement check
```python
# Phase 3: Enhance transitions with kinetic properties
if options.enhance_kinetics:
    self._enhance_transition_kinetics(document, reaction_transition_map, pathway)
```

### 4. Reaction Mapper (EC Fetching)
**File**: `src/shypn/importer/kegg/reaction_mapper.py`

**Line 94-103**: EC number fetching
```python
try:
    fetcher = get_default_fetcher()
    ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
    
    if ec_numbers:
        transition.metadata['ec_numbers'] = ec_numbers
        logger.debug(f"Fetched EC numbers for {reaction.name}: {ec_numbers}")
except Exception as e:
    logger.warning(f"Failed to fetch EC numbers for {reaction.name}: {e}")
```

**KEY**: This code SHOULD be executed for EVERY reaction during conversion!

### 5. Kinetics Assigner
**File**: `src/shypn/heuristic/kinetics_assigner.py`

**Line 110-125**: Database lookup based on EC numbers
```python
# Tier 2: Database lookup (if EC number available)
# Check transition metadata first (from KEGG EC enrichment)
# then fallback to reaction.ec_numbers (legacy)
has_ec = False
if hasattr(transition, 'metadata') and 'ec_numbers' in transition.metadata:
    has_ec = bool(transition.metadata['ec_numbers'])
elif hasattr(reaction, 'ec_numbers'):
    has_ec = bool(reaction.ec_numbers)

if has_ec:
    result = self._assign_from_database(...)
```

---

## Possible Causes

### 1. EC Fetching Silently Failing ⚠️ **LIKELY**
**Hypothesis**: `fetcher.fetch_ec_numbers()` is returning empty list or failing silently

**Evidence**:
- No error messages during import
- No EC numbers in ANY transition
- 100% failure rate

**Debug Steps**:
```python
# Add logging in reaction_mapper.py line 94
logger.info(f"Attempting to fetch EC for {reaction.name} (id: {reaction.id})")
ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
logger.info(f"Result: {ec_numbers}")
```

### 2. Metadata Not Being Saved
**Hypothesis**: EC numbers fetched but not persisted to file

**Evidence**:
- Would see EC numbers in memory but not in saved file
- Less likely (metadata dict is directly assigned)

**Debug Steps**:
```python
# Add logging before save
for t in document.transitions:
    if hasattr(t, 'metadata') and 'ec_numbers' in t.metadata:
        logger.info(f"{t.name} has EC: {t.metadata['ec_numbers']}")
```

### 3. enhance_kinetics Not Being Called
**Hypothesis**: The `if options.enhance_kinetics:` check is failing

**Evidence**:
- Would affect ALL imports
- Matches 100% failure rate

**Debug Steps**:
```python
# Add logging at line 92
logger.info(f"enhance_kinetics={options.enhance_kinetics}")
if options.enhance_kinetics:
    logger.info("Calling _enhance_transition_kinetics...")
```

### 4. Wrong Code Path Being Used
**Hypothesis**: `convert_pathway_enhanced()` using old `EstimatorFactory` instead of EC enrichment

**Evidence**:
- Line 407: `estimate_kinetics` parameter exists
- Line 442: Uses `EstimatorFactory` (old heuristic system)
- Does NOT use EC enrichment system

**Debug Steps**:
Check if EC fetching happens in `convert_pathway()` or `_enhance_transition_kinetics()`

---

## Investigation Plan

### Step 1: Verify EC Fetcher Works
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from shypn.data.kegg_ec_fetcher import get_default_fetcher

fetcher = get_default_fetcher()
result = fetcher.fetch_ec_numbers('rn:R00299')
print(f'EC numbers for R00299: {result}')
"
```

**Expected**: `['2.7.1.1', '2.7.1.2']`  
**If fails**: EC fetcher is broken

### Step 2: Add Debug Logging
Add comprehensive logging to trace execution:

**File**: `reaction_mapper.py` (line 94)
```python
logger.info(f"=== EC FETCH START ===")
logger.info(f"Reaction name: {reaction.name}")
logger.info(f"Reaction id: {reaction.id}")

try:
    fetcher = get_default_fetcher()
    logger.info(f"Fetcher created: {fetcher}")
    
    ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
    logger.info(f"EC numbers returned: {ec_numbers}")
    
    if ec_numbers:
        transition.metadata['ec_numbers'] = ec_numbers
        logger.info(f"✓ Saved EC to metadata: {ec_numbers}")
    else:
        logger.warning(f"✗ No EC numbers returned for {reaction.name}")
except Exception as e:
    logger.error(f"✗ Exception during EC fetch: {e}", exc_info=True)

logger.info(f"=== EC FETCH END ===")
```

### Step 3: Check enhance_kinetics Flag
**File**: `pathway_converter.py` (line 92)
```python
logger.info(f"=== KINETICS ENHANCEMENT CHECK ===")
logger.info(f"options.enhance_kinetics = {options.enhance_kinetics}")

if options.enhance_kinetics:
    logger.info("✓ Calling _enhance_transition_kinetics()")
    self._enhance_transition_kinetics(document, reaction_transition_map, pathway)
else:
    logger.warning("✗ Kinetics enhancement DISABLED")
```

### Step 4: Manual Import Test
1. Run shypn GUI
2. Import KEGG pathway hsa00010
3. Check terminal output for debug logs
4. Inspect saved file for EC numbers

---

## Workaround

Until bug is fixed, manually add EC numbers using KEGG API:

```python
import json
from shypn.data.kegg_ec_fetcher import KEGGECFetcher

# Load file
with open('model.shy', 'r') as f:
    data = json.load(f)

# Fetch EC numbers
fetcher = KEGGECFetcher()
for t in data['transitions']:
    reaction_name = t.get('metadata', {}).get('kegg_reaction_name')
    if reaction_name:
        ec_numbers = fetcher.fetch_ec_numbers(reaction_name)
        if ec_numbers:
            if 'metadata' not in t:
                t['metadata'] = {}
            t['metadata']['ec_numbers'] = ec_numbers

# Save file
with open('model_enriched.shy', 'w') as f:
    json.dump(data, f, indent=2)
```

---

## Next Steps

1. ✅ Run Step 1 (verify EC fetcher works)
2. ⏳ Add debug logging (Steps 2-3)
3. ⏳ Manual import with logging enabled
4. ⏳ Identify root cause
5. ⏳ Fix and verify

---

**Status**: 🔴 **CRITICAL BUG** - EC enrichment completely non-functional  
**Impact**: HIGH - All KEGG imports lack kinetic metadata  
**Priority**: P0 - Blocks Phase 2C completion verification
