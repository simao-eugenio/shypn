# SBML Import Arc ID Analysis

**Date**: December 2024  
**Context**: Following the fix for duplicate arc ID bug in JSON import (commit 15be809), analyzing SBML import flow for similar issues.

## Executive Summary

✅ **SBML import is SAFE** from the duplicate arc ID bug that affected JSON import.

The arc ID assignment uses a sequential counter that makes duplicate IDs impossible during fresh SBML-to-Petri-net conversion.

## Architecture Analysis

### Arc Creation in SBML Import

**Flow**: SBML XML → PathwayData → ProcessedPathwayData → DocumentModel (Petri net)

**Key Components**:
1. `SBMLParser` (sbml_parser.py): Extracts species, reactions, modifiers from SBML
2. `PathwayConverter` (pathway_converter.py): Converts to Petri net objects
3. `DocumentModel` (document_model.py): Manages arc ID counter

### Arc ID Assignment Mechanism

#### For Normal Arcs (Reactants/Products)

```python
# src/shypn/data/canvas/document_model.py:107-109
arc_id = self._next_arc_id
arc_name = f"A{arc_id}"
self._next_arc_id += 1
```

Called via:
```python
# pathway_converter.py:537
arc = self.document.create_arc(
    source=place,
    target=transition,
    weight=weight
)
```

#### For Test Arcs (Modifiers/Catalysts)

```python
# pathway_converter.py:666-667
arc_id = f"A{self.document._next_arc_id}"
self.document._next_arc_id += 1

test_arc = TestArc(
    source=place,
    target=transition,
    id=arc_id,
    name=f"TA{arc_id[1:]}",
    weight=1
)
```

**Critical Feature**: Both arc types use the **same counter** (`document._next_arc_id`), ensuring globally unique IDs.

### Counter Initialization & Reset

```python
# document_model.py:36 - Initial state
self._next_arc_id = 1

# document_model.py:473 - After loading from file
document._next_arc_id = max_arc_id + 1  # Prevents collisions with existing arcs
```

## Why Duplicate IDs Cannot Occur in SBML Import

1. **Sequential Assignment**: Arc IDs are assigned from a single incrementing counter
2. **Atomic Increment**: Each arc creation increments the counter immediately
3. **No SBML ID Reuse**: Arc IDs are never derived from SBML reaction/species IDs
4. **Shared Counter**: Normal arcs and test arcs use the same counter

## Comparison: JSON Import vs SBML Import

| Aspect | JSON Import (HAD BUG) | SBML Import (SAFE) |
|--------|----------------------|-------------------|
| **Source** | Saved .shy file | SBML XML file |
| **Arc IDs** | Deserialized from JSON | Generated sequentially |
| **Bug Mechanism** | Duplicate IDs in source → dict collision | Impossible (counter) |
| **Fix Applied** | Use `id(arc)` instead of `arc.id` | No fix needed |

### The Bug in JSON Import (Fixed)

```python
# OLD (BUGGY): src/shypn/engine/simulation/controller.py:77
@property
def arcs(self):
    return {a.id: a for a in self.canvas_manager.arcs}  # Dict collision!
```

**Problem**: If JSON file contained duplicate arc IDs (like A5, A5), later arc overwrote earlier one.

**Fix** (commit 15be809):
```python
# NEW (FIXED): Use Python object ID
@property
def arcs(self):
    return {id(a): a for a in self.canvas_manager.arcs}  # Unique per object!
```

## Residual Risks for SBML Models

While fresh SBML import is safe, SBML-imported models can still encounter the bug in these scenarios:

### Risk 1: Save & Reload Cycle ✅ PROTECTED

**Scenario**: Import SBML → Save as .shy → Reload from .shy

**Protection**: The fix using `id(arc)` instead of `arc.id` as dictionary key protects against any duplicate arc IDs in the saved file.

**Example**:
```python
# Even if hsa00010.shy has duplicate arc IDs:
# A5: P101 -> T3
# A5: P50 -> T4 (duplicate!)

# OLD: arcs_dict = {a.id: a for a in arcs}
# → 73 arcs in dict (39 lost to collisions)

# NEW: arcs_dict = {id(a): a for a in arcs}
# → 112 arcs in dict (all preserved!)
```

### Risk 2: Manual Editing ⚠️ LOW RISK

**Scenario**: User manually edits saved .shy JSON and creates duplicate arc IDs

**Protection**: Fix handles this at runtime, but prevention is better:

**Recommendation**: Consider adding validation during file load:
```python
def from_dict(cls, data: dict) -> "DocumentModel":
    # ... existing code ...
    
    # Validate unique arc IDs
    arc_ids = [a.id for a in document.arcs]
    duplicates = [id for id in arc_ids if arc_ids.count(id) > 1]
    if duplicates:
        logger.warning(
            f"Duplicate arc IDs found: {set(duplicates)} - "
            f"all arcs preserved using object identity"
        )
```

### Risk 3: Corrupted SBML File ⚠️ VERY LOW RISK

**Scenario**: Malformed SBML causes converter to generate duplicate IDs

**Protection**: Counter mechanism makes this nearly impossible unless:
- Bug in `create_arc()` that doesn't increment counter
- Counter manually reset mid-conversion
- Concurrent arc creation (not applicable in single-threaded Python)

**Likelihood**: Extremely low, would require code bug

## Code Verification

Verified the following code paths are safe:

### 1. Normal Arc Creation (pathway_converter.py:520-580)
```python
# Input arcs (reactants → transition)
for species_id, total_stoichiometry in reactant_weights.items():
    arc = self.document.create_arc(
        source=place,
        target=transition,
        weight=weight
    )  # Uses counter, increments automatically

# Output arcs (transition → products)  
for species_id, total_stoichiometry in product_weights.items():
    arc = self.document.create_arc(
        source=transition,
        target=place,
        weight=weight
    )  # Uses same counter, continues sequence
```

### 2. Test Arc Creation (pathway_converter.py:666-678)
```python
for modifier_species_id in reaction.modifiers:
    # Generate ID from counter
    arc_id = f"A{self.document._next_arc_id}"
    self.document._next_arc_id += 1  # Increment immediately
    
    test_arc = TestArc(
        source=place,
        target=transition,
        id=arc_id,
        name=f"TA{arc_id[1:]}",
        weight=1
    )
    self.document.arcs.append(test_arc)
```

**Key observation**: Both use the same `document._next_arc_id` counter, ensuring global uniqueness.

### 3. Counter Reset After Load (document_model.py:455-473)
```python
# Track maximum arc ID when loading from file
max_arc_id = 0
for arc_data in data.get("arcs", []):
    arc = Arc.from_dict(arc_data, ...)
    document.arcs.append(arc)
    try:
        arc_id_int = int(arc.id)
        max_arc_id = max(max_arc_id, arc_id_int)
    except (ValueError, TypeError):
        pass

# Set counter above maximum to prevent collisions with new arcs
document._next_arc_id = max_arc_id + 1
```

**Purpose**: When loading a model with 112 arcs (max ID = 112), next created arc gets ID 113, avoiding collisions.

## Related Issues

### Original Bug Report
- Model: `workspace/projects/Interactive/models/hsa00010.shy`
- Symptom: T3 and T4 transitions wouldn't fire after loading
- Root Cause: 39 duplicate arc IDs (A1-A39 appeared twice each)
- Dictionary collision: 112 arcs → 73 unique IDs = 39 lost arcs
- Impact: Missing input arcs made transitions appear to have no inputs

### Fix Commits
- `864ae92`: Fixed behavior cache persistence bug
- `15be809`: Fixed duplicate arc ID bug using Python `id()` function

## Recommendations

### For Development

1. ✅ **Current fix is sufficient** for SBML import
2. ✅ **Counter mechanism is robust** and should be maintained
3. ⚠️ **Consider adding validation** during file load (log warnings for duplicates)

### For Testing

Add test case for SBML import → save → reload cycle:

```python
def test_sbml_import_save_reload_preserves_arcs():
    """Test that SBML import → save → reload preserves all arcs."""
    # Import from SBML
    parser = SBMLParser()
    pathway = parser.parse_file('test_model.sbml')
    converter = PathwayConverter()
    doc1 = converter.convert(pathway)
    arc_count_1 = len(doc1.arcs)
    
    # Save to file
    doc1.save_to_file('test_output.shy')
    
    # Reload from file
    doc2 = DocumentModel.from_file('test_output.shy')
    arc_count_2 = len(doc2.arcs)
    
    # Verify all arcs preserved
    assert arc_count_1 == arc_count_2, \
        f"Arc count changed: {arc_count_1} → {arc_count_2}"
```

### For Documentation

1. ✅ Add note in SBML import documentation: "Arc IDs are auto-generated sequentially"
2. ✅ Add note in file format documentation: "Duplicate arc IDs are tolerated (using object identity)"

## Conclusion

**SBML import is architecturally safe** from duplicate arc ID issues due to its sequential counter mechanism. The fix applied to JSON import (using Python `id()`) also protects SBML-imported models when they are saved and reloaded.

**No action required** for SBML import code itself. The current implementation is robust and follows best practices.

**Optional enhancement**: Add duplicate ID validation/warning during file load for better diagnostics.

---

**Related Documents**:
- [BEHAVIOR_CACHE_BUG_FIX.md](./BEHAVIOR_CACHE_BUG_FIX.md) - Behavior cache persistence fix
- [ARC_THRESHOLD_USAGE_GUIDE.md](./ARC_THRESHOLD_USAGE_GUIDE.md) - Arc weight vs threshold documentation
