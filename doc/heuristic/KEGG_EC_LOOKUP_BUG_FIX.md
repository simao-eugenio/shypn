# Critical Bug Fix: KEGG EC Lookup Using Wrong ID

**Date**: October 19, 2025  
**Commit**: 154f8ba  
**Severity**: High (broke EC number fetching for all KEGG imports)

---

## Problem

When importing KEGG pathways, EC numbers were not being fetched correctly due to using the wrong reaction identifier.

### Symptoms

```
KEGG API error for 61: 400 Client Error: Bad Request
KEGG API error for 62: 400 Client Error: Bad Request
KEGG API error for 18: 400 Client Error: Bad Request
...
```

### Root Cause

The `reaction_mapper.py` was using `reaction.id` (internal pathway entry ID) instead of `reaction.name` (KEGG reaction ID) when calling the KEGG API.

**KEGGReaction Model**:
```python
@dataclass
class KEGGReaction:
    id: str      # Internal entry ID (e.g., "61", "62")
    name: str    # KEGG reaction ID (e.g., "rn:R00299", "rn:R00710")
    type: str
    substrates: List[KEGGSubstrate]
    products: List[KEGGProduct]
```

**Wrong Code** (before fix):
```python
# ✗ Using internal entry ID (invalid for KEGG API)
ec_numbers = fetcher.fetch_ec_numbers(reaction.id)  
# Calls: https://rest.kegg.jp/get/61 → 400 Bad Request
```

**Correct Code** (after fix):
```python
# ✅ Using KEGG reaction ID (valid for API)
ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
# Calls: https://rest.kegg.jp/get/R00299 → Success!
```

---

## Impact

### Before Fix
- ✗ No EC numbers fetched from KEGG API
- ✗ All 400 errors for valid reactions
- ✗ Kinetics enhancement fell back to heuristics (MEDIUM confidence)
- ✗ Lost the benefit of Phase 2C (KEGG EC enrichment)

### After Fix
- ✅ EC numbers correctly fetched from KEGG API
- ✅ KEGG imports get HIGH confidence kinetics
- ✅ Phase 2C working as intended
- ✅ Graceful handling of invalid IDs

---

## Changes Made

### 1. reaction_mapper.py (2 locations)

**`_create_single_transition()`**:
```python
# OLD:
ec_numbers = fetcher.fetch_ec_numbers(reaction.id)
logger.debug(f"Fetched EC numbers for {reaction.id}: {ec_numbers}")

# NEW:
ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
logger.debug(f"Fetched EC numbers for {reaction.name}: {ec_numbers}")
```

**`_create_split_reversible()`**:
```python
# OLD:
ec_numbers = fetcher.fetch_ec_numbers(reaction.id)
logger.debug(f"Fetched EC numbers for {reaction.id}: {ec_numbers}")

# NEW:
ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
logger.debug(f"Fetched EC numbers for {reaction.name}: {ec_numbers}")
```

### 2. kegg_ec_fetcher.py

**Better Error Handling**:
```python
# OLD:
except requests.exceptions.RequestException as e:
    logger.warning(f"KEGG API error for {reaction_id}: {e}")
    return []

# NEW:
except requests.exceptions.HTTPError as e:
    # 400 Bad Request is expected for invalid reaction IDs
    if e.response.status_code == 400:
        logger.debug(f"Invalid KEGG reaction ID: {reaction_id}")
    else:
        logger.warning(f"KEGG API HTTP error for {reaction_id}: {e}")
    return []
except requests.exceptions.RequestException as e:
    logger.warning(f"KEGG API error for {reaction_id}: {e}")
    return []
```

**Benefit**: Suppresses noisy warnings for expected 400 errors (invalid IDs)

---

## Testing

### Test Case 1: Valid KEGG Reaction IDs ✅

```python
fetcher = KEGGECFetcher()

# With "rn:" prefix
ec = fetcher.fetch_ec_numbers("rn:R00299")
# → ['2.7.1.1', '2.7.1.2'] ✅

# Without "rn:" prefix
ec = fetcher.fetch_ec_numbers("R00299")
# → ['2.7.1.1', '2.7.1.2'] ✅

# Enolase
ec = fetcher.fetch_ec_numbers("R00658")
# → ['4.2.1.11'] ✅
```

### Test Case 2: Invalid Entry IDs (Graceful Handling) ✅

```python
# Entry IDs (not reaction IDs)
ec = fetcher.fetch_ec_numbers("61")
# → [] (empty, no crash) ✅

ec = fetcher.fetch_ec_numbers("62")
# → [] (empty, no crash) ✅
```

### Test Case 3: Real KEGG Import ✅

Import Glycolysis pathway:
- ✅ EC numbers fetched for all enzymatic reactions
- ✅ No 400 errors
- ✅ HIGH confidence kinetics assigned

---

## Metadata Clarification

The metadata correctly stores **both** identifiers:

```python
transition.metadata = {
    'kegg_reaction_id': reaction.id,      # "61" (for internal reference)
    'kegg_reaction_name': reaction.name,  # "rn:R00299" (KEGG API ID)
    'ec_numbers': ['2.7.1.1', '2.7.1.2'], # Fetched using reaction.name
    'source': 'KEGG',
    'reversible': False
}
```

**Purpose**:
- `kegg_reaction_id`: Reference within pathway structure
- `kegg_reaction_name`: API lookup and external reference
- `ec_numbers`: Fetched from KEGG API using `kegg_reaction_name`

---

## Why This Bug Happened

### Timeline

1. **Phase 2C implemented** (commit 20e86af):
   - Added KEGG EC fetching
   - Used `reaction.id` assuming it was the KEGG reaction ID
   - **Mistake**: Didn't verify what `reaction.id` actually contains

2. **Testing**:
   - Unit tests used mock `KEGGReaction` objects
   - Mock `reaction.id` was set to "R00299" (looked correct)
   - Real KEGG pathways have `reaction.id = "61"` (internal entry ID)
   - **Gap**: No integration test with real KEGG pathway data

3. **Discovery**:
   - User ran KEGG import
   - Saw 400 errors in logs
   - Reported issue

### Lesson Learned

✅ **Always test with real data, not just mocks**
- Unit tests passed (mocks had correct structure)
- Integration test would have caught this immediately

✅ **Verify field semantics**
- `reaction.id` ≠ KEGG reaction ID
- `reaction.name` = KEGG reaction ID (surprise!)

✅ **Better naming would help**
- `entry_id` vs `reaction_id` vs `kegg_id`
- Clear documentation of field purpose

---

## Prevention

### Add Integration Test

```python
# tests/test_kegg_integration.py

def test_ec_fetch_with_real_kegg_pathway():
    """Test EC fetching with real KEGG pathway structure."""
    
    # Create reaction with real KEGG pathway structure
    reaction = KEGGReaction(
        id="61",              # Internal entry ID
        name="rn:R00299",     # KEGG reaction ID
        type="irreversible",
        substrates=[],
        products=[]
    )
    
    mapper = StandardReactionMapper()
    transition = mapper._create_single_transition(
        reaction=reaction,
        x=100.0,
        y=100.0,
        name="Hexokinase"
    )
    
    # Should fetch EC numbers using reaction.name (not reaction.id)
    assert 'ec_numbers' in transition.metadata
    assert '2.7.1.1' in transition.metadata['ec_numbers']
```

---

## Status

✅ **Bug Fixed** (commit 154f8ba)  
✅ **Tested with real KEGG reaction IDs**  
✅ **Graceful error handling for invalid IDs**  
✅ **Phase 2C now working correctly**

**Result**: KEGG pathway imports now correctly fetch EC numbers and get HIGH confidence kinetics!
