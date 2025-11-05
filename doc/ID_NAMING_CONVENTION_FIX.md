# ID Naming Convention - Root Cause Analysis and Prevention Strategy

## Problem Summary

Model file `hsa00010.shy` contained objects with IDs missing proper prefixes:
- **5 Transitions**: `36`, `37`, `38`, `39`, `41` (should be `T36`-`T41`)
- **1 Place**: `151` (should be `P151`)
- **6 Arcs**: `114`-`120` (should be `A114`-`A120`)

This caused:
1. Confusion when debugging (hard to identify object types)
2. Potential ID conflicts between categories
3. Simulation issues (T41 appeared as "41", making it hard to track)

## Root Cause Analysis

### Where IDs Are Generated

#### ✅ CORRECT: Document Model (document_model.py)
```python
def create_place(self, x, y, label=""):
    place_id = self._next_place_id
    place_name = f"P{place_id}"  # ✓ Properly prefixed
    self._next_place_id += 1
    place = Place(x, y, place_id, place_name, label)
```

**Problem**: `place_id` is stored as **integer** but later converted to string.

#### ✅ CORRECT: KEGG Importer (pathway_converter.py)
```python
place_id = f"P{entry.id}"  # ✓ Properly prefixed
place_name = f"P{entry.id}"
place = Place(x, y, place_id, place_name, label)
```

#### ✅ CORRECT: Reaction Mapper (reaction_mapper.py)
```python
transition_id = f"T{self.transition_counter}"  # ✓ Properly prefixed
transition_name = f"T{self.transition_counter}"
transition = Transition(x, y, transition_id, transition_name, label)
```

#### ✅ CORRECT: Arc Builder (arc_builder.py)
```python
arc_id = f"A{self.arc_counter}"  # ✓ Properly prefixed
arc = Arc(place, transition, arc_id, "", weight)
```

### Where the Bug Occurred

The problematic IDs came from **serialization/deserialization inconsistency**:

1. **Object Creation**: ID created as **integer** (e.g., `41`)
2. **to_dict()**: ID stored as-is (becomes string `"41"` in JSON)
3. **from_dict()**: ID loaded as string `"41"` (missing "T" prefix)

#### The Critical Code Path

**netobjs/place.py** (Line 237):
```python
@classmethod
def from_dict(cls, data: dict) -> 'Place':
    # IDs are now always strings - just convert to string
    place_id = str(data.get("id"))  # ⚠️ If data["id"] = 41, this becomes "41" not "P41"
```

**netobjs/transition.py** (Line 607):
```python
@classmethod  
def from_dict(cls, data: dict) -> 'Transition':
    # IDs are now always strings - just convert to string
    transition_id = str(data.get("id"))  # ⚠️ Same issue
```

### Why This Happened

Old workflow (before proper ID management):
1. Objects created with numeric IDs: `place.id = 41`
2. Saved to JSON: `{"id": 41}` or `{"id": "41"}`
3. Loaded back: `place.id = "41"` (string, no prefix)

New workflow (with proper ID management):
1. Objects created with prefixed IDs: `place.id = "P41"`
2. Saved to JSON: `{"id": "P41"}`
3. Loaded back: `place.id = "P41"` ✓

The bug occurred because **old model files** were saved before the ID prefixing was implemented consistently across all code paths.

## Prevention Strategy

### 1. Enforce ID Prefixes at Object Creation ✅

**Status**: Already implemented correctly in all creation paths.

### 2. Validate IDs at Serialization

Add validation in `to_dict()` methods:

```python
def to_dict(self) -> dict:
    # Validate ID format before serializing
    if not self.id.startswith('P'):
        raise ValueError(f"Place ID must start with 'P', got: {self.id}")
    
    data = super().to_dict()
    data.update({
        "object_type": "place",
        "id": str(self.id),  # Ensure string format
        ...
    })
    return data
```

### 3. Validate and Fix IDs at Deserialization

Add validation/fixing in `from_dict()` methods:

```python
@classmethod
def from_dict(cls, data: dict) -> 'Place':
    place_id = str(data.get("id"))
    
    # CRITICAL: Validate/fix ID format
    if not place_id.startswith('P'):
        if place_id.isdigit():
            # Auto-fix old format
            place_id = f"P{place_id}"
            logger.warning(f"Fixed place ID format: {data.get('id')} → {place_id}")
        else:
            raise ValueError(f"Invalid place ID format: {place_id}")
    
    place = cls(
        x=float(data["x"]),
        y=float(data["y"]),
        id=place_id,  # ✓ Guaranteed to have prefix
        ...
    )
    return place
```

### 4. Add ID Validation to DocumentModel

Add post-load validation:

```python
@classmethod
def from_dict(cls, data: dict) -> 'DocumentModel':
    document = cls()
    
    # ... load objects ...
    
    # CRITICAL: Validate all IDs after loading
    document._validate_id_conventions()
    
    return document

def _validate_id_conventions(self):
    """Validate that all IDs follow naming conventions."""
    violations = []
    
    for place in self.places:
        if not str(place.id).startswith('P'):
            violations.append(f"Place ID invalid: {place.id}")
    
    for transition in self.transitions:
        if not str(transition.id).startswith('T'):
            violations.append(f"Transition ID invalid: {transition.id}")
    
    for arc in self.arcs:
        if not str(arc.id).startswith('A'):
            violations.append(f"Arc ID invalid: {arc.id}")
    
    if violations:
        raise ValueError(f"ID naming violations: {violations}")
```

### 5. Add Pre-Save Validation Hook

```python
def save_to_file(self, filepath: str) -> None:
    # Validate IDs before saving
    self._validate_id_conventions()
    
    # Serialize and save
    data = self.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
```

## Implementation Plan

### Phase 1: Fix Existing Models ✅
- [x] Create `fix_id_naming_conventions.py` script
- [x] Fix `hsa00010.shy` model file
- [ ] Scan and fix all other .shy files in workspace

### Phase 2: Add Runtime Validation (RECOMMENDED)
- [ ] Add validation to `Place.from_dict()`
- [ ] Add validation to `Transition.from_dict()`
- [ ] Add validation to `Arc.from_dict()`
- [ ] Add `DocumentModel._validate_id_conventions()`
- [ ] Call validation in `DocumentModel.from_dict()` and `save_to_file()`

### Phase 3: Add Auto-Fixing (OPTIONAL)
- [ ] Auto-fix numeric IDs on load with warning
- [ ] Log all auto-fixes for user review
- [ ] Option to disable auto-fixing (strict mode)

### Phase 4: Add Tests
- [ ] Test ID validation rejects invalid IDs
- [ ] Test auto-fixing converts numeric IDs correctly
- [ ] Test ID conventions enforced across all import paths (KEGG, SBML, File→New)

## Files to Modify

### High Priority (Runtime Validation)
1. `src/shypn/netobjs/place.py` - Add validation to `from_dict()`
2. `src/shypn/netobjs/transition.py` - Add validation to `from_dict()`
3. `src/shypn/netobjs/arc.py` - Add validation to `from_dict()`
4. `src/shypn/data/canvas/document_model.py` - Add `_validate_id_conventions()`

### Medium Priority (Prevention)
5. `src/shypn/netobjs/place.py` - Add validation to `to_dict()`
6. `src/shypn/netobjs/transition.py` - Add validation to `to_dict()`
7. `src/shypn/netobjs/arc.py` - Add validation to `to_dict()`

### Low Priority (Testing)
8. Create `test_id_naming_conventions.py`

## Example Validation Code

```python
# netobjs/place.py

ID_PREFIX = 'P'  # Class-level constant

@classmethod
def from_dict(cls, data: dict) -> 'Place':
    place_id = str(data.get("id"))
    
    # Validate and fix ID format
    if not place_id.startswith(cls.ID_PREFIX):
        if place_id.isdigit():
            # Auto-fix: numeric ID → prefixed ID
            old_id = place_id
            place_id = f"{cls.ID_PREFIX}{place_id}"
            import logging
            logging.warning(
                f"Auto-fixed Place ID format: '{old_id}' → '{place_id}'. "
                f"Please re-save this model to update the file."
            )
        else:
            raise ValueError(
                f"Invalid Place ID: '{place_id}'. "
                f"Place IDs must start with '{cls.ID_PREFIX}' followed by a number."
            )
    
    # Validate ID is properly formatted (Pxx where xx is a number)
    if not place_id[1:].isdigit():
        raise ValueError(
            f"Invalid Place ID format: '{place_id}'. "
            f"Expected format: '{cls.ID_PREFIX}<number>' (e.g., 'P101')"
        )
    
    name = str(data.get("name", place_id))
    
    place = cls(
        x=float(data["x"]),
        y=float(data["y"]),
        id=place_id,
        name=name,
        ...
    )
    return place
```

## Testing Strategy

```python
def test_place_id_validation():
    """Test that Place IDs are validated correctly."""
    
    # Valid ID
    data = {"id": "P101", "x": 0, "y": 0, ...}
    place = Place.from_dict(data)
    assert place.id == "P101"
    
    # Auto-fix numeric ID
    data = {"id": "101", "x": 0, "y": 0, ...}
    with pytest.warns(UserWarning, match="Auto-fixed Place ID"):
        place = Place.from_dict(data)
    assert place.id == "P101"
    
    # Reject invalid ID
    data = {"id": "T101", "x": 0, "y": 0, ...}  # Wrong prefix
    with pytest.raises(ValueError, match="Invalid Place ID"):
        Place.from_dict(data)
    
    data = {"id": "Pabc", "x": 0, "y": 0, ...}  # Non-numeric suffix
    with pytest.raises(ValueError, match="Invalid Place ID format"):
        Place.from_dict(data)
```

## Conclusion

The ID naming convention issue was caused by **inconsistent serialization/deserialization** of IDs between old and new code. The current code generates IDs correctly, but old model files may contain improperly formatted IDs.

**Solution**:
1. ✅ Fix existing model files with `fix_id_naming_conventions.py`
2. 🔧 Add runtime validation to prevent future issues
3. 🚀 Auto-fix with warnings for backward compatibility

This ensures **all future models** will have properly formatted IDs, and **old models** will be automatically fixed on load with clear warnings.
