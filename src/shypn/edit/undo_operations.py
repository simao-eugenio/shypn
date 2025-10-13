"""
Undo/Redo Operation Classes

This module defines the abstract base class and concrete implementations
for all undoable/redoable operations in the Petri net editor.

Architecture:
- UndoOperation: Abstract base class defining the undo/redo interface
- Concrete subclasses: AddPlaceOperation, DeleteOperation, MoveOperation, etc.
- Each operation is self-contained and knows how to undo/redo itself
- Operations interact with ModelCanvasManager to modify the model
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class UndoOperation(ABC):
    """
    Abstract base class for all undo/redo operations.
    
    Each operation must implement:
    - undo(): Reverse the operation
    - redo(): Reapply the operation
    - __str__(): Human-readable description for debugging
    """
    
    @abstractmethod
    def undo(self, canvas_manager):
        """
        Undo this operation.
        
        Args:
            canvas_manager: ModelCanvasManager instance to modify
        """
        pass
    
    @abstractmethod
    def redo(self, canvas_manager):
        """
        Redo this operation.
        
        Args:
            canvas_manager: ModelCanvasManager instance to modify
        """
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        """Return human-readable description of operation."""
        pass


class AddPlaceOperation(UndoOperation):
    """
    Operation for adding a place to the canvas.
    
    Stores the place_id so it can be removed on undo and re-added on redo.
    Uses snapshots to preserve all place state.
    """
    
    def __init__(self, place_id: int, snapshot: Dict[str, Any]):
        """
        Args:
            place_id: ID of the added place
            snapshot: Complete state of the place (from snapshots.snapshot_place)
        """
        self.place_id = place_id
        self.snapshot = snapshot
    
    def undo(self, canvas_manager):
        """Remove the added place."""
        from shypn.edit.snapshots import remove_place_by_id
        remove_place_by_id(canvas_manager, self.place_id)
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Re-add the place from snapshot."""
        from shypn.edit.snapshots import recreate_place
        recreate_place(canvas_manager, self.snapshot)
        canvas_manager.mark_modified()
    
    def __str__(self) -> str:
        return f"AddPlace(id={self.place_id}, name={self.snapshot.get('name', '')})"


class AddTransitionOperation(UndoOperation):
    """
    Operation for adding a transition to the canvas.
    
    Stores the transition_id so it can be removed on undo and re-added on redo.
    Uses snapshots to preserve all transition state.
    """
    
    def __init__(self, transition_id: int, snapshot: Dict[str, Any]):
        """
        Args:
            transition_id: ID of the added transition
            snapshot: Complete state of the transition (from snapshots.snapshot_transition)
        """
        self.transition_id = transition_id
        self.snapshot = snapshot
    
    def undo(self, canvas_manager):
        """Remove the added transition."""
        from shypn.edit.snapshots import remove_transition_by_id
        remove_transition_by_id(canvas_manager, self.transition_id)
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Re-add the transition from snapshot."""
        from shypn.edit.snapshots import recreate_transition
        recreate_transition(canvas_manager, self.snapshot)
        canvas_manager.mark_modified()
    
    def __str__(self) -> str:
        return f"AddTransition(id={self.transition_id}, name={self.snapshot.get('name', '')})"


class AddArcOperation(UndoOperation):
    """
    Operation for adding an arc to the canvas.
    
    Stores the arc_id so it can be removed on undo and re-added on redo.
    Uses snapshots to preserve all arc state including source/target connections.
    """
    
    def __init__(self, arc_id: int, snapshot: Dict[str, Any]):
        """
        Args:
            arc_id: ID of the added arc
            snapshot: Complete state of the arc (from snapshots.snapshot_arc)
        """
        self.arc_id = arc_id
        self.snapshot = snapshot
    
    def undo(self, canvas_manager):
        """Remove the added arc."""
        from shypn.edit.snapshots import remove_arc_by_id
        remove_arc_by_id(canvas_manager, self.arc_id)
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Re-add the arc from snapshot."""
        from shypn.edit.snapshots import recreate_arc
        recreate_arc(canvas_manager, self.snapshot)
        canvas_manager.mark_modified()
    
    def __str__(self) -> str:
        return f"AddArc(id={self.arc_id}, name={self.snapshot.get('name', '')})"


class DeleteOperation(UndoOperation):
    """
    Operation for deleting objects from the canvas.
    
    Stores snapshots of all deleted objects (including connected arcs)
    so they can be fully recreated on undo.
    """
    
    def __init__(self, snapshots: List[Dict[str, Any]]):
        """
        Args:
            snapshots: List of snapshots for all deleted objects
                      (places, transitions, arcs in deletion order)
        """
        self.snapshots = snapshots
    
    def undo(self, canvas_manager):
        """Recreate all deleted objects from snapshots."""
        from shypn.edit.snapshots import recreate_from_snapshot
        
        # Recreate in order: places/transitions first, then arcs
        # (arcs need their endpoints to exist)
        for snapshot in self.snapshots:
            if snapshot['type'] in ('place', 'transition'):
                recreate_from_snapshot(canvas_manager, snapshot)
        
        for snapshot in self.snapshots:
            if snapshot['type'] == 'arc':
                recreate_from_snapshot(canvas_manager, snapshot)
        
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Re-delete all objects."""
        from shypn.edit.snapshots import remove_object_by_snapshot
        
        # Delete in reverse order: arcs first, then places/transitions
        for snapshot in reversed(self.snapshots):
            if snapshot['type'] == 'arc':
                remove_object_by_snapshot(canvas_manager, snapshot)
        
        for snapshot in reversed(self.snapshots):
            if snapshot['type'] in ('place', 'transition'):
                remove_object_by_snapshot(canvas_manager, snapshot)
        
        canvas_manager.mark_modified()
    
    def __str__(self) -> str:
        count = len(self.snapshots)
        types = ', '.join(s['type'] for s in self.snapshots)
        return f"Delete({count} objects: {types})"


class MoveOperation(UndoOperation):
    """
    Operation for moving objects on the canvas.
    
    Stores old and new positions for all moved objects.
    Supports both single-object and multi-object moves.
    """
    
    def __init__(self, move_data: List[Dict[str, Any]]):
        """
        Args:
            move_data: List of dicts with keys:
                - 'type': 'place' or 'transition'
                - 'id': object ID
                - 'old_x', 'old_y': original position
                - 'new_x', 'new_y': new position
        """
        self.move_data = move_data
        
        # Optimization: drop this operation if nothing actually moved
        self.is_noop = all(
            data['old_x'] == data['new_x'] and data['old_y'] == data['new_y']
            for data in move_data
        )
    
    def undo(self, canvas_manager):
        """Restore original positions."""
        if self.is_noop:
            return
        
        for data in self.move_data:
            obj = self._find_object(canvas_manager, data)
            if obj:
                obj.x = data['old_x']
                obj.y = data['old_y']
        
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Restore new positions."""
        if self.is_noop:
            return
        
        for data in self.move_data:
            obj = self._find_object(canvas_manager, data)
            if obj:
                obj.x = data['new_x']
                obj.y = data['new_y']
        
        canvas_manager.mark_modified()
    
    def _find_object(self, canvas_manager, data: Dict[str, Any]):
        """Find object by type and ID."""
        if data['type'] == 'place':
            return next((p for p in canvas_manager.places if p.id == data['id']), None)
        elif data['type'] == 'transition':
            return next((t for t in canvas_manager.transitions if t.id == data['id']), None)
        return None
    
    def __str__(self) -> str:
        if self.is_noop:
            return "Move(no-op)"
        count = len(self.move_data)
        return f"Move({count} object{'s' if count > 1 else ''})"


class PropertyChangeOperation(UndoOperation):
    """
    Operation for changing object properties via dialogs.
    
    Stores before/after snapshots of the modified object
    to enable full property restoration.
    """
    
    def __init__(self, old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]):
        """
        Args:
            old_snapshot: Object state before property change
            new_snapshot: Object state after property change
        """
        self.old_snapshot = old_snapshot
        self.new_snapshot = new_snapshot
        self.object_type = old_snapshot['type']
        self.object_id = old_snapshot['id']
    
    def undo(self, canvas_manager):
        """Restore original property values."""
        self._apply_snapshot(canvas_manager, self.old_snapshot)
        canvas_manager.mark_modified()
    
    def redo(self, canvas_manager):
        """Restore new property values."""
        self._apply_snapshot(canvas_manager, self.new_snapshot)
        canvas_manager.mark_modified()
    
    def _apply_snapshot(self, canvas_manager, snapshot: Dict[str, Any]):
        """Apply snapshot properties to the object."""
        obj = self._find_object(canvas_manager)
        if not obj:
            return
        
        # Apply all properties from snapshot
        if self.object_type == 'place':
            obj.name = snapshot['name']
            obj.x = snapshot['x']
            obj.y = snapshot['y']
            obj.radius = snapshot['radius']
            obj.tokens = snapshot['tokens']
            obj.marking = snapshot.get('marking', snapshot['tokens'])
            obj.capacity = snapshot.get('capacity', float('inf'))
            if hasattr(obj, 'properties'):
                obj.properties = dict(snapshot.get('properties', {}))
        
        elif self.object_type == 'transition':
            obj.name = snapshot['name']
            obj.x = snapshot['x']
            obj.y = snapshot['y']
            obj.width = snapshot['width']
            obj.height = snapshot['height']
            obj.horizontal = snapshot['horizontal']
            obj.transition_type = snapshot.get('transition_type', 'continuous')
            if 'rate' in snapshot and hasattr(obj, 'rate'):
                obj.rate = snapshot['rate']
            if 'delay' in snapshot and hasattr(obj, 'delay'):
                obj.delay = snapshot['delay']
            if 'weight' in snapshot and hasattr(obj, 'weight'):
                obj.weight = snapshot['weight']
            if hasattr(obj, 'properties'):
                obj.properties = dict(snapshot.get('properties', {}))
        
        elif self.object_type == 'arc':
            obj.name = snapshot['name']
            obj.weight = snapshot['weight']
            obj.arc_kind = snapshot.get('arc_kind', 'normal')
            if hasattr(obj, 'properties'):
                obj.properties = dict(snapshot.get('properties', {}))
    
    def _find_object(self, canvas_manager):
        """Find object by type and ID."""
        if self.object_type == 'place':
            return next((p for p in canvas_manager.places if p.id == self.object_id), None)
        elif self.object_type == 'transition':
            return next((t for t in canvas_manager.transitions if t.id == self.object_id), None)
        elif self.object_type == 'arc':
            return next((a for a in canvas_manager.arcs if a.id == self.object_id), None)
        return None
    
    def __str__(self) -> str:
        return f"PropertyChange({self.object_type} id={self.object_id})"


class GroupOperation(UndoOperation):
    """
    Operation that groups multiple operations together.
    
    Used for composite actions like paste (multiple adds)
    or multi-delete that should be undone/redone as a unit.
    """
    
    def __init__(self, operations: List[UndoOperation], description: str = "Group"):
        """
        Args:
            operations: List of operations to group
            description: Human-readable description of the group
        """
        self.operations = operations
        self.description = description
    
    def undo(self, canvas_manager):
        """Undo all operations in reverse order."""
        for op in reversed(self.operations):
            op.undo(canvas_manager)
    
    def redo(self, canvas_manager):
        """Redo all operations in original order."""
        for op in self.operations:
            op.redo(canvas_manager)
    
    def __str__(self) -> str:
        count = len(self.operations)
        return f"Group({self.description}, {count} ops)"
