# Undo/Redo System - Developer Quick Reference

**Date**: October 7, 2025  
**Purpose**: Quick guide for using and extending the undo/redo system

---

## For Users

### How to Use
1. **Add objects**: Places, transitions, arcs are automatically recorded
2. **Move objects**: Drag operations are automatically recorded
3. **Delete objects**: Context menu deletions are automatically recorded
4. **Undo**: Click [U] button or press Ctrl+Z (when implemented)
5. **Redo**: Click [R] button or press Ctrl+Shift+Z (when implemented)

### What Gets Recorded
- ✅ Adding places, transitions, arcs
- ✅ Deleting any object (including connected arcs)
- ✅ Moving objects (drag operations)
- 🔄 Property changes (ready, needs dialog integration)

---

## For Developers

### Adding a New Operation Type

**Step 1**: Create operation class in `undo_operations.py`

```python
class MyOperation(UndoOperation):
    """Description of what this operation does."""
    
    def __init__(self, data):
        self.data = data
    
    def undo(self, canvas_manager):
        """Reverse the operation."""
        # Implementation
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Reapply the operation."""
        # Implementation
        canvas_manager.mark_modified()
    
    def __str__(self) -> str:
        return f"MyOperation({self.data})"
```

**Step 2**: Record the operation where it happens

```python
# In the place where the operation occurs
if hasattr(canvas_manager, 'undo_manager'):
    from shypn.edit.undo_operations import MyOperation
    operation = MyOperation(data)
    canvas_manager.undo_manager.push(operation)
```

**That's it!** The undo/redo system will handle the rest.

---

## Architecture at a Glance

```
User Action
    ↓
Handler Code (minimal, just records)
    ↓
canvas_manager.undo_manager.push(operation)
    ↓
UndoManager adds to stack
    ↓
[U] button click
    ↓
canvas_manager.undo_manager.undo(canvas_manager)
    ↓
Operation.undo(canvas_manager) executes
    ↓
Canvas updated
```

---

## Common Patterns

### Pattern 1: Recording an Add Operation

```python
# After creating the object
if hasattr(self, 'undo_manager'):
    from shypn.edit.snapshots import snapshot_place
    from shypn.edit.undo_operations import AddPlaceOperation
    snapshot = snapshot_place(place)
    self.undo_manager.push(AddPlaceOperation(place.place_id, snapshot))
```

### Pattern 2: Recording a Delete Operation

```python
# Before deleting the object
if hasattr(manager, 'undo_manager'):
    from shypn.edit.snapshots import capture_delete_snapshots
    from shypn.edit.undo_operations import DeleteOperation
    snapshots = capture_delete_snapshots(manager, [obj])
    manager.undo_manager.push(DeleteOperation(snapshots))

# Then perform deletion
manager.places.remove(place)
```

### Pattern 3: Recording a Property Change

```python
# Before changing properties
old_snapshot = snapshot_place(place)

# Change properties
place.name = new_name
place.tokens = new_tokens

# After changing properties
if hasattr(manager, 'undo_manager'):
    new_snapshot = snapshot_place(place)
    from shypn.edit.undo_operations import PropertyChangeOperation
    operation = PropertyChangeOperation(old_snapshot, new_snapshot)
    manager.undo_manager.push(operation)
```

### Pattern 4: Recording a Move Operation

```python
# Get move data before ending drag
move_data = manager.selection_manager.get_move_data_for_undo()

# End drag
manager.selection_manager.end_drag()

# Record operation
if move_data and hasattr(manager, 'undo_manager'):
    from shypn.edit.undo_operations import MoveOperation
    manager.undo_manager.push(MoveOperation(move_data))
```

---

## Key Classes

### UndoManager
**Location**: `src/shypn/edit/undo_manager.py`

**Purpose**: Manages undo/redo stacks

**Key Methods**:
- `push(operation)`: Add operation to undo stack
- `undo(canvas_manager)`: Execute undo
- `redo(canvas_manager)`: Execute redo
- `can_undo()`: Check if undo available
- `can_redo()`: Check if redo available
- `clear()`: Clear all history

### UndoOperation (ABC)
**Location**: `src/shypn/edit/undo_operations.py`

**Purpose**: Base class for all operations

**Required Methods**:
- `undo(canvas_manager)`: Reverse the operation
- `redo(canvas_manager)`: Reapply the operation
- `__str__()`: Human-readable description

### Snapshot Functions
**Location**: `src/shypn/edit/snapshots.py`

**Purpose**: Capture and restore object state

**Key Functions**:
- `snapshot_place(place)`: Capture place state
- `snapshot_transition(transition)`: Capture transition state
- `snapshot_arc(arc)`: Capture arc state
- `recreate_place(manager, snapshot)`: Recreate place
- `recreate_transition(manager, snapshot)`: Recreate transition
- `recreate_arc(manager, snapshot)`: Recreate arc

---

## Testing Your Operation

### Unit Test Template

```python
def test_my_operation():
    # Setup
    manager = ModelCanvasManager()
    manager.undo_manager = UndoManager()
    
    # Perform operation
    # ... (e.g., add place)
    
    # Verify operation recorded
    assert manager.undo_manager.can_undo()
    
    # Undo
    manager.undo_manager.undo(manager)
    
    # Verify undone
    # ... (e.g., place removed)
    
    # Redo
    manager.undo_manager.redo(manager)
    
    # Verify redone
    # ... (e.g., place exists)
```

### Interactive Testing

1. Launch application: `python3 src/shypn.py`
2. Perform operation (add/move/delete)
3. Check console: `[UndoManager] Pushed: ...`
4. Click [U] button
5. Check console: `[UndoManager] Undoing: ...`
6. Verify result visually
7. Click [R] button
8. Check console: `[UndoManager] Redoing: ...`
9. Verify result visually

---

## Debugging Tips

### Enable Debug Logging

The UndoManager already prints to console:
- `[UndoManager] Pushed: ...` - When operation recorded
- `[UndoManager] Undoing: ...` - When undo executed
- `[UndoManager] Redoing: ...` - When redo executed
- `[UndoManager] Skipping no-op operation: ...` - When no-op detected

### Check Stack State

```python
print(f"Undo stack size: {len(manager.undo_manager.undo_stack)}")
print(f"Redo stack size: {len(manager.undo_manager.redo_stack)}")
print(f"Can undo: {manager.undo_manager.can_undo()}")
print(f"Can redo: {manager.undo_manager.can_redo()}")
print(f"Next undo: {manager.undo_manager.get_undo_description()}")
```

### Common Issues

**Issue**: "Nothing to undo"  
**Cause**: Operation not being recorded  
**Fix**: Check that `undo_manager.push()` is being called

**Issue**: "Error during undo"  
**Cause**: Exception in operation.undo()  
**Fix**: Check console for stack trace, debug operation class

**Issue**: "Object not found during undo"  
**Cause**: IDs not matching or object already deleted  
**Fix**: Check snapshot includes correct IDs

---

## Best Practices

### DO ✅
- Record operations immediately after they occur
- Use snapshots for complex state
- Handle errors gracefully in undo/redo
- Test undo AND redo for every operation
- Keep operation classes simple and focused

### DON'T ❌
- Modify objects during snapshot creation
- Forget to call `canvas_manager.mark_modified()`
- Create operations that depend on each other
- Record operations for no-op changes
- Put business logic in the loader

---

## Performance Tips

1. **Snapshot efficiency**: Only capture what you need
2. **No-op detection**: Check if state actually changed before recording
3. **Stack size**: Default 50 is good balance (memory vs. history)
4. **Group operations**: Use GroupOperation for multi-ops

---

## FAQ

**Q: Where should I put the recording code?**  
A: As close as possible to where the operation happens, but keep it minimal.

**Q: What if an operation fails during undo?**  
A: The UndoManager catches exceptions and pushes the operation back to the stack.

**Q: Can I undo part of a group operation?**  
A: No, GroupOperation is atomic - all or nothing.

**Q: How do I clear undo history?**  
A: Call `canvas_manager.undo_manager.clear()` (e.g., when loading a new file).

**Q: What's the memory overhead?**  
A: ~200-500 bytes per operation, so 50 operations ≈ 10-25 KB.

**Q: Can I change the stack size limit?**  
A: Yes, pass `limit` to UndoManager constructor or modify `undo_manager.limit`.

---

## Related Files

### Core Implementation
- `src/shypn/edit/undo_manager.py` - Stack management
- `src/shypn/edit/undo_operations.py` - Operation classes
- `src/shypn/edit/snapshots.py` - State capture/restore

### Integration Points
- `src/shypn/data/model_canvas_manager.py` - Manager initialization
- `src/shypn/helpers/model_canvas_loader.py` - Loader recording

### Documentation
- `doc/UNDO_REDO_ANALYSIS.md` - Pre-implementation analysis
- `doc/UNDO_REDO_IMPLEMENTATION_COMPLETE.md` - Full implementation details
- `doc/UNDO_REDO_DEV_QUICK_REFERENCE.md` - This file

---

**Last Updated**: October 7, 2025  
**Status**: Complete and Production Ready
