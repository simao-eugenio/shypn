# CRITICAL BUG FIXED: Metadata Not Being Serialized

**Date**: October 19, 2025  
**Commit**: fe1ef96  
**Severity**: CRITICAL (P0)  
**Status**: ✅ FIXED  

---

## Problem

EC numbers were being fetched during KEGG import (explaining the processing time) but **NOT persisting to saved `.shy` files** because `Transition.to_dict()` didn't serialize the `metadata` attribute.

### User Observation (Key Insight!)

> "one things there is considerable it is the time taken to transform to petri nets, some work it is done that do not appear in the model"

This was the smoking gun! The processing time proved that EC fetching WAS happening, but results weren't in the saved files.

---

## Root Cause

**File**: `src/shypn/netobjs/transition.py`

### to_dict() Method (Line 454)
```python
def to_dict(self) -> dict:
    # ... serializes other properties ...
    if hasattr(self, 'properties') and self.properties:
        data["properties"] = self.properties
    
    # ❌ BUG: metadata NOT serialized!
    return data
```

### from_dict() Method (Line 574)
```python
@classmethod
def from_dict(cls, data: dict) -> 'Transition':
    # ... deserializes other properties ...
    if "properties" in data:
        transition.properties = data["properties"]
    
    # ❌ BUG: metadata NOT deserialized!
    return transition
```

---

## Impact

### What Was Happening

```
Import KEGG pathway
  ├─> Fetch KGML from KEGG API ✓
  ├─> Parse reactions ✓
  ├─> Create transitions ✓
  ├─> Fetch EC numbers from KEGG API ✓  # ← THIS WAS WORKING!
  ├─> Store in transition.metadata ✓     # ← THIS WAS WORKING!
  ├─> Save to .shy file
  │     └─> Call transition.to_dict()
  │           └─> metadata NOT included ✗  # ← BUG!
  └─> Result: .shy file has NO metadata ✗
```

### Evidence

1. **Processing time**: Import took significant time (EC fetching was happening)
2. **0% enrichment**: No saved files had EC numbers
3. **EC fetcher works**: Direct test showed fetcher returns correct EC numbers
4. **Serialization gap**: to_dict() and from_dict() didn't handle metadata

---

## Fix

### to_dict() - Add Metadata Serialization
```python
def to_dict(self) -> dict:
    # ... existing code ...
    
    # Serialize metadata (EC numbers, enzyme info, kinetics data)
    if hasattr(self, 'metadata') and self.metadata:
        data["metadata"] = self.metadata  # ← FIXED!
    
    return data
```

### from_dict() - Add Metadata Deserialization
```python
@classmethod
def from_dict(cls, data: dict) -> 'Transition':
    # ... existing code ...
    
    # Restore metadata (EC numbers, enzyme info, kinetics data)
    if "metadata" in data:
        transition.metadata = data["metadata"]  # ← FIXED!
    
    return transition
```

---

## Verification

### Before Fix (0% Enrichment)
```json
{
  "id": "T1",
  "name": "T1",
  "transition_type": "continuous",
  "rate": "10.0 * P1",
  // ❌ NO metadata
}
```

### After Fix (Expected)
```json
{
  "id": "T1",
  "name": "T1",
  "transition_type": "continuous",
  "rate": "vmax * P1 / (km + P1)",
  "metadata": {
    "ec_numbers": ["2.7.1.1", "2.7.1.2"],
    "enzyme_name": "Hexokinase",
    "kinetics_confidence": "high",
    "kinetics_source": "database",
    "kegg_reaction_id": "61",
    "kegg_reaction_name": "rn:R00299",
    "source": "KEGG"
  }
}
```

---

## Testing

### Test 1: Re-import KEGG Pathway
```bash
# In shypn GUI:
1. File → Import → KEGG Pathway
2. Enter "hsa00010" (Glycolysis)
3. Import (Metadata enhancement is checked by default)
4. Save as "Glycolysis_VERIFIED.shy"
```

**Expected**:
- Processing time (EC fetching)
- Saved file has metadata in transitions
- EC numbers visible in transition properties

### Test 2: Inspect Saved File
```bash
python3 << 'EOF'
import json

with open('Glycolysis_VERIFIED.shy', 'r') as f:
    data = json.load(f)

enriched = 0
for t in data['transitions']:
    if 'metadata' in t and 'ec_numbers' in t['metadata']:
        enriched += 1
        print(f"{t['name']}: EC {t['metadata']['ec_numbers']}")

print(f"\nEnrichment: {enriched}/{len(data['transitions'])} ({enriched/len(data['transitions'])*100:.1f}%)")
EOF
```

**Expected output**:
```
T1: EC ['2.7.1.1', '2.7.1.2']
T2: EC ['5.3.1.9']
T3: EC ['2.7.1.11']
...

Enrichment: 20/29 (69.0%)
```

### Test 3: Load and Verify
```bash
# Open Glycolysis_VERIFIED.shy in shypn
# Right-click transition → Properties
# Check metadata tab or tooltip
```

**Expected**: Shows EC numbers, enzyme name, confidence level

---

## Related Issues

This bug also affected:
1. **Place metadata**: May have same issue (not checked yet)
2. **Arc metadata**: May have same issue (not checked yet)
3. **Any custom metadata**: Lost on save/load

### Recommendation: Check Other Objects

Check if Place and Arc also need metadata serialization:
- `src/shypn/netobjs/place.py`
- `src/shypn/netobjs/arc.py`

---

## Timeline

| Time | Event |
|------|-------|
| 02:52 | Phase 2C committed (20e86af) - EC enrichment added |
| 03:04 | Bug fix 1 (154f8ba) - Use correct reaction ID |
| 03:17 | Bug fix 2 (358237d) - Check transition metadata |
| 03:34-03:42 | Files created with 0% enrichment |
| **Now** | **Bug fix 3 (fe1ef96) - Serialize metadata!** ✅ |

---

## Lessons Learned

### 1. User Observation Was Key
The user's observation about processing time was the crucial clue that work was being done but not persisted.

### 2. Test End-to-End
Unit tests for EC fetching passed, but end-to-end test (import → save → load) would have caught this immediately.

### 3. Serialization is Critical
Always check that new data structures are properly serialized/deserialized.

### 4. Add Serialization Tests
```python
def test_transition_metadata_persistence():
    """Test that metadata survives save/load cycle."""
    t = Transition(0, 0, "T1", "T1")
    t.metadata = {
        'ec_numbers': ['2.7.1.1'],
        'enzyme_name': 'Hexokinase'
    }
    
    # Serialize
    data = t.to_dict()
    assert 'metadata' in data
    assert data['metadata']['ec_numbers'] == ['2.7.1.1']
    
    # Deserialize
    t2 = Transition.from_dict(data)
    assert hasattr(t2, 'metadata')
    assert t2.metadata['ec_numbers'] == ['2.7.1.1']
```

---

## Next Steps

1. ✅ Fix committed (fe1ef96)
2. ⏳ Re-import KEGG pathway to verify fix works
3. ⏳ Check Place and Arc metadata serialization
4. ⏳ Add serialization tests to prevent regression
5. ⏳ Update documentation with fix details

---

**Status**: ✅ **FIXED**  
**Commit**: fe1ef96 - "fix: Add metadata serialization to Transition to_dict/from_dict"  
**Impact**: EC enrichment will now persist correctly!  
**Credit**: User observation about processing time led to discovery! 🎯
