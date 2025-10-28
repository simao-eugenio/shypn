# Duplicate ID Bug Fix

## Problem Description

When loading SBML models (.shy files) and then manually creating new places or transitions, the newly created objects would get duplicate IDs. This caused phantom values to appear in unconnected places during simulation.

### Root Cause

The `DocumentModel.from_dict()` method was loading objects from saved files but **not updating the ID counters** (`_next_place_id`, `_next_transition_id`, `_next_arc_id`).

Example scenario:
1. Load BIOMD0000000061.shy with places 1-25
2. ID counters remain at default value: 1
3. User manually creates a new place → gets ID 1 (duplicate!)
4. During simulation, updates to place ID=1 affect BOTH places
5. Result: Unconnected places show changing values "from nowhere"

### Code Issue

**File:** `src/shypn/data/canvas/document_model.py`

**Before (lines 434-450):**
```python
# Restore places first (they have no dependencies)
places_dict = {}
for place_data in data.get("places", []):
    place = Place.from_dict(place_data)
    document.places.append(place)
    places_dict[place.id] = place
    # Note: No longer updating _next_place_id since IDs are strings

# Similar for transitions and arcs...
```

The comment claimed "IDs are strings" as justification for not updating counters. However:
- IDs are generated as **integers** (`_next_place_id` is an int)
- They are **converted to strings** when stored in objects (`self._id = str(id)`)
- The counters must be updated after loading to prevent ID reuse

## Solution

Updated `from_dict()` to track the maximum ID for each object type and set counters accordingly:

```python
# Track maximum ID to update counter (IDs are stored as strings but generated as ints)
max_place_id = 0
for place_data in data.get("places", []):
    place = Place.from_dict(place_data)
    document.places.append(place)
    places_dict[place.id] = place
    try:
        place_id_int = int(place.id)
        max_place_id = max(max_place_id, place_id_int)
    except (ValueError, TypeError):
        pass  # Skip non-numeric IDs

# After loading all objects:
document._next_place_id = max_place_id + 1
document._next_transition_id = max_transition_id + 1
document._next_arc_id = max_arc_id + 1
```

## Verification

### Test 1: BIOMD0000000061.shy
```
Loaded: 25 places (IDs 1-25), 24 transitions (IDs 1-24), 66 arcs (IDs 1-66)
Counters: _next_place_id=26, _next_transition_id=25, _next_arc_id=67 ✓
New place: ID=26 ✓
New place: ID=27 ✓
New transition: ID=25 ✓
No duplicates ✓
```

### Test 2: Hynne2001_Glycolysis.shy
```
Loaded: 25 places (IDs 1-25), 24 transitions (IDs 1-24)
Counters: _next_place_id=26, _next_transition_id=25 ✓
New objects get unique IDs ✓
No duplicates ✓
```

### Test 3: teste.shy
```
Loaded: 2 places (IDs 1-2), 1 transition (ID 1)
Counters: _next_place_id=3, _next_transition_id=2 ✓
New place: ID=3, ID=4 ✓
New transition: ID=2 ✓
No duplicates ✓
```

## Important Notes

1. **Separate ID Spaces:** Places and transitions have independent ID counters. It's normal and correct for both Place 1 and Transition 1 to exist in the same model.

2. **String Storage:** IDs are stored as strings in the Petri net objects (for serialization) but generated and tracked as integers in DocumentModel.

3. **Backward Compatibility:** The fix handles edge cases like non-numeric IDs gracefully (though they shouldn't occur in normal operation).

## Impact

This fix resolves:
- ✓ Duplicate ID generation after loading SBML models
- ✓ Phantom values in unconnected places during simulation
- ✓ Confusion where simulation updates affect multiple objects with same ID

## Date Fixed

October 27, 2025

## Branch

File-Open-SBML-Health (commit after e63db89)
