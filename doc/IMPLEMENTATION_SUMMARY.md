"""
Implementation Summary: Petri Net Connection Rules
===================================================

Date: October 3, 2025
Branch: restructure-project

## What Was Learned from Legacy Code

### 1. Bipartite Graph Property (from `legacy/shypnpy/core/model.py`)

The core validation logic enforces the bipartite property:

```python
def add_arc(self, source_id: int, target_id: int, weight: int = 1) -> Arc:
    # ...validation...
    
    # Enforce bipartite property
    src_is_place = source_id in self.places
    tgt_is_place = target_id in self.places
    if src_is_place == tgt_is_place:
        raise ValueError("Arcs must connect place to transition")
```

**Key Insight**: The check `src_is_place == tgt_is_place` is elegant:
- If both are True (both places) → invalid
- If both are False (both transitions) → invalid
- If different (one place, one transition) → valid

### 2. Connection Types

From legacy code analysis:

**Valid Connections:**
- Place → Transition (P→T): Input arcs
- Transition → Place (T→P): Output arcs

**Invalid Connections:**
- Place → Place (P→P): Violates bipartite property
- Transition → Transition (T→T): Violates bipartite property

### 3. Arc Storage (from `legacy/shypnpy/core/petri.py`)

Legacy Arc class stores:
```python
class Arc(PetriNetElement):
    def __init__(self, arc_id, source_id, target_id, weight=1, ...):
        self.source_id = source_id  # ID reference
        self.target_id = target_id  # ID reference
        self.weight = int(weight)
        self.kind = "normal"  # or "inhibitor"
```

**Our Implementation**: Uses object references instead of IDs:
```python
class Arc(PetriNetObject):
    def __init__(self, source, target, id, name, weight=1):
        self.source = source  # Object reference
        self.target = target  # Object reference
        self.weight = weight
```

This is more Pythonic and allows direct access without lookups.

### 4. Default Colors

From legacy renderer analysis (`legacy/shypnpy/ui/renderer.py`):

- **Places**: White fill `(1.0, 1.0, 1.0)`, black border `(0.0, 0.0, 0.0)`
- **Transitions**: Black fill `(0.0, 0.0, 0.0)`, colored borders (customizable)
- **Arcs**: Black lines `(0.0, 0.0, 0.0)`, width 3.0

**User Requirement**: "Default color to all objects is black"
- Interpreted as: All strokes/borders/lines should be black
- Places: White fill (standard for Petri nets), black border ✓
- Transitions: Black fill and border ✓
- Arcs: Black lines ✓

## What Was Implemented

### 1. Connection Validation (`src/shypn/api/arc.py`)

Added `_validate_connection()` static method to Arc class:

```python
@staticmethod
def _validate_connection(source, target):
    """Validate that connection follows bipartite property."""
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    source_is_place = isinstance(source, Place)
    target_is_place = isinstance(target, Place)
    
    if source_is_place == target_is_place:
        # Both same type → invalid
        raise ValueError(
            f"Invalid connection: {source_type} → {target_type}. "
            f"Arcs must connect Place↔Transition (bipartite property)."
        )
```

Called in `__init__` before creating the arc:
```python
def __init__(self, source, target, id, name, weight=1):
    self._validate_connection(source, target)  # Validate first
    # ...rest of initialization...
```

### 2. Inherited Validation

InhibitorArc automatically inherits validation:
```python
class InhibitorArc(Arc):
    def __init__(self, source, target, id, name, weight=1):
        super().__init__(source, target, id, name, weight)
        # Validation happens in Arc.__init__
```

### 3. Documentation (`doc/CONNECTION_RULES.md`)

Created comprehensive documentation covering:
- Bipartite graph theory
- Valid/invalid connection types
- Implementation reference from legacy
- Visual representation
- Default colors
- Special arc types (InhibitorArc)

### 4. Test Coverage (`tests/test_connection_rules.py`)

Complete test suite with 6 tests:
1. ✓ Valid: Place → Transition
2. ✓ Valid: Transition → Place
3. ✓ Invalid: Place → Place (blocked with clear error)
4. ✓ Invalid: Transition → Transition (blocked with clear error)
5. ✓ InhibitorArc validation (inherits from Arc)
6. ✓ Default colors verification

**All tests pass** ✓

## Code Preservation Rules

The implementation preserves current code structure:

1. **Object References vs IDs**: Kept object references (more Pythonic)
2. **Immutable IDs**: Maintained via @property decorators
3. **Base Class Pattern**: Used PetriNetObject inheritance
4. **Independent Modules**: Each class in separate file
5. **Cairo Rendering**: Preserved render(cr, transform) signature
6. **Default Colors**: Confirmed black as primary color

## Verification

Run tests:
```bash
python3 tests/test_connection_rules.py
```

Results:
```
✓ Place → Transition (valid)
✓ Transition → Place (valid)
✗ Place → Place (blocked)
✗ Transition → Transition (blocked)
✓ InhibitorArc follows same rules
✓ All objects use black default color
```

## Files Modified

1. **src/shypn/api/arc.py**
   - Added `_validate_connection()` method
   - Updated `__init__()` to call validation
   - Enhanced docstrings

2. **doc/CONNECTION_RULES.md** (new)
   - Comprehensive connection rules documentation
   - Legacy code references
   - Visual diagrams
   - Examples

3. **tests/test_connection_rules.py** (new)
   - Complete test coverage
   - Clear success/failure messages
   - Verification of all connection types

## Next Steps

The foundation is now solid with:
- ✓ Valid connections enforced (P↔T only)
- ✓ Invalid connections blocked with clear errors
- ✓ InhibitorArc follows same rules
- ✓ Default black colors confirmed
- ✓ Documentation complete
- ✓ Tests passing

Ready for:
- Canvas interaction tools for creating arcs
- Visual feedback during arc creation
- Manager-level validation (when creating via tools)
- Serialization/deserialization with validation
"""
