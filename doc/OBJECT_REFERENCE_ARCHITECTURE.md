# Object Reference Architecture - Strong Rule

**Date**: October 18, 2025  
**Status**: 🔒 **ARCHITECTURAL INVARIANT** - Must Never Be Violated

## Core Principle

**Objects must ALWAYS be referenced by Python object identity (memory reference), NEVER by string IDs or names.**

This is a fundamental architectural rule that prevents:
- ID conflicts and collisions
- Name conflicts and ambiguity
- Reference integrity violations
- Synchronization bugs between different lookup mechanisms

## The Rule

### ✅ CORRECT - Object References

```python
# CORRECT: Store and use object references
place1 = Place(x=100, y=100, id=1, name="P1")
place2 = Place(x=200, y=100, id=2, name="P2")
transition = Transition(x=150, y=100, id=1, name="T1")

# Arc uses object references
arc = Arc(source=place1, target=transition, id=1, name="A1")

# Dictionary keyed by object reference
object_map = {place1: "data1", place2: "data2"}

# List of object references
selected_objects = [place1, transition]
```

### ❌ WRONG - String ID/Name Lookups

```python
# WRONG: Never do this!
place_by_id = {"1": place1, "2": place2}  # ❌ String ID keys
place_by_name = {"P1": place1, "P2": place2}  # ❌ String name keys

# WRONG: Never store IDs/names as lookup keys
arc.source_id = "1"  # ❌ Should be: arc.source = place1
arc.target_name = "T1"  # ❌ Should be: arc.target = transition
```

## Why This Matters

### Problem 1: ID Conflicts
```python
# Two objects with same ID - which one to use?
place1 = Place(id=1, name="P1")
place2 = Place(id=1, name="P2")  # Same ID!

# If using ID lookup:
lookup = {1: place1}
lookup[1] = place2  # ❌ place1 is lost!

# If using object references:
objects = [place1, place2]  # ✅ Both preserved
```

### Problem 2: Name Conflicts
```python
# Two objects with same name
place1 = Place(id=1, name="Glucose")
place2 = Place(id=2, name="Glucose")  # Same name, different compartment

# If using name lookup:
lookup = {"Glucose": place1}
lookup["Glucose"] = place2  # ❌ place1 is lost!

# If using object references:
objects = [place1, place2]  # ✅ Both preserved
```

### Problem 3: Reference Integrity
```python
# Arc created with object references
arc = Arc(source=place1, target=transition)

# Later, place1 properties change
place1.x = 300  # Position changes
place1.name = "NewName"  # Name changes
place1.id = 999  # ID changes (in theory)

# Arc still works!
print(arc.source.x)  # ✅ 300 - automatically updated
print(arc.source.name)  # ✅ "NewName" - automatically updated

# If arc stored source_id = 1:
print(arc.source_id)  # ❌ Still 1, but place1.id is now 999!
```

## Implementation Rules

### Rule 1: Object Creation
Always create objects with direct references:

```python
# ✅ CORRECT
place = Place(x=100, y=100, id=1, name="P1")
transition = Transition(x=200, y=100, id=1, name="T1")
arc = Arc(source=place, target=transition, id=1, name="A1")
```

### Rule 2: Object Storage
Store collections of objects, not IDs:

```python
# ✅ CORRECT
manager.places = [place1, place2, place3]
manager.transitions = [transition1, transition2]
manager.arcs = [arc1, arc2, arc3]

# ❌ WRONG
manager.place_ids = [1, 2, 3]  # Never store IDs separately
```

### Rule 3: Object Lookup
Use iteration or Python's identity, not ID lookup:

```python
# ✅ CORRECT - Iterate to find object
def find_place_at_position(x, y):
    for place in manager.places:
        if place.x == x and place.y == y:
            return place
    return None

# ✅ CORRECT - Use object identity
selected = place1
if selected in manager.places:
    print("Place is in manager")

# ❌ WRONG - ID-based lookup
def find_place_by_id(place_id):  # ❌ Avoid this pattern
    for place in manager.places:
        if place.id == place_id:
            return place
```

### Rule 4: Arc References
Arcs MUST store source/target as objects:

```python
# ✅ CORRECT
class Arc:
    def __init__(self, source, target, id, name):
        self.source = source  # Object reference
        self.target = target  # Object reference
        self.id = id
        self.name = name

# ❌ WRONG
class Arc:
    def __init__(self, source_id, target_id, id, name):  # ❌ Never!
        self.source_id = source_id  # ❌ String/int ID
        self.target_id = target_id  # ❌ String/int ID
```

### Rule 5: Serialization (Special Case)
**ONLY exception**: When saving to disk, serialize object references to IDs, then restore:

```python
# Serialization (save)
def serialize_arc(arc):
    return {
        "source_id": arc.source.id,  # ✅ OK for serialization only
        "target_id": arc.target.id,
        "weight": arc.weight
    }

# Deserialization (load)
def deserialize_arc(data, place_map):
    # Immediately convert IDs back to object references
    source = place_map[data["source_id"]]  # ✅ Resolve to object
    target = place_map[data["target_id"]]
    return Arc(source=source, target=target, ...)  # ✅ Store objects
```

After deserialization, **IDs are only used temporarily** and discarded.

## Code Patterns

### Pattern 1: Finding Objects
```python
# Find by property (NOT by ID)
def find_places_with_tokens(manager):
    return [p for p in manager.places if p.tokens > 0]

# Find by position
def find_object_at(manager, x, y):
    for obj in manager.get_all_objects():
        if obj.contains_point(x, y):
            return obj
    return None
```

### Pattern 2: Selection
```python
# Selection uses object references
selected_objects = []

def select_object(obj):
    if obj not in selected_objects:
        selected_objects.append(obj)

def deselect_object(obj):
    if obj in selected_objects:
        selected_objects.remove(obj)
```

### Pattern 3: Undo/Redo
```python
# Undo stores object references, not IDs
class DeleteCommand:
    def __init__(self, manager, obj):
        self.manager = manager
        self.obj = obj  # ✅ Store object reference
    
    def execute(self):
        if isinstance(self.obj, Place):
            self.manager.places.remove(self.obj)
    
    def undo(self):
        if isinstance(self.obj, Place):
            self.manager.places.append(self.obj)
```

## Benefits

1. **No ID Conflicts**: Object identity is guaranteed unique by Python
2. **No Name Conflicts**: Names can duplicate without issues
3. **Automatic Updates**: Property changes automatically propagate
4. **Type Safety**: Python type system enforces correct object types
5. **Simpler Code**: No need for ID→object lookup dictionaries
6. **Better Performance**: Object reference is O(1), ID lookup is O(n)

## Migration Guide

If you find code using ID/name lookups:

### Before (Wrong)
```python
# ❌ ID-based arc creation
arc_data = {"source_id": 1, "target_id": 2, "weight": 1.0}
source = find_place_by_id(arc_data["source_id"])
target = find_transition_by_id(arc_data["target_id"])
arc = Arc(source, target, ...)
```

### After (Correct)
```python
# ✅ Object-based arc creation
arc = Arc(source=place_obj, target=transition_obj, weight=1.0)
# Objects passed directly, no ID lookup needed
```

## Enforcement

### Code Review Checklist
- [ ] No dictionaries keyed by `id` or `name`
- [ ] No `find_by_id()` or `find_by_name()` methods (except for UI input)
- [ ] Arc `source`/`target` are objects, not IDs
- [ ] Selection lists contain objects, not IDs
- [ ] Undo commands store objects, not IDs

### Testing
```python
# Test that objects are referenced correctly
def test_arc_uses_object_references():
    place = Place(id=1, name="P1")
    transition = Transition(id=1, name="T1")
    arc = Arc(source=place, target=transition, id=1)
    
    # Verify object references
    assert arc.source is place  # ✅ Same object
    assert arc.target is transition
    
    # Verify properties accessible
    assert arc.source.name == "P1"
    assert arc.target.name == "T1"
    
    # Verify updates propagate
    place.name = "NewName"
    assert arc.source.name == "NewName"  # ✅ Automatic
```

## Summary

**Golden Rule**: Objects reference other objects, never IDs or names.

This architectural principle is **non-negotiable** and must be maintained across:
- Core data structures (Place, Transition, Arc)
- Manager classes (ModelCanvasManager)
- Import/export code (temporary ID use only during serialization)
- UI selection and interaction
- Undo/redo system

**Any violation of this rule is a bug that must be fixed immediately.**

---

**Document Version**: 1.0  
**Last Updated**: October 18, 2025  
**Status**: 🔒 Architectural Invariant  
**Applies To**: All code in shypn project
