"""
Undo/Redo Manager

This module provides the UndoManager class that:
1. Manages undo/redo stacks
2. Provides push/undo/redo operations
3. Notifies listeners of state changes
4. Enforces stack size limits

The UndoManager is instantiated in ModelCanvasManager and used throughout
the application to record and execute undo/redo operations.
"""

from typing import Optional, Callable
from shypn.edit.undo_operations import UndoOperation


class UndoManager:
    """
    Manages undo/redo stacks and executes operations.
    
    The manager maintains two stacks:
    - undo_stack: Operations that can be undone
    - redo_stack: Operations that can be redone
    
    When a new operation is pushed, the redo stack is cleared.
    When undo is called, the operation is moved to redo stack.
    When redo is called, the operation is moved to undo stack.
    """
    
    def __init__(self, limit: int = 50):
        """
        Initialize the undo manager.
        
        Args:
            limit: Maximum number of operations to keep in undo stack
        """
        self.undo_stack = []
        self.redo_stack = []
        self.limit = limit
        self._state_changed_callback = None
    
    def push(self, operation: UndoOperation):
        """
        Add an operation to the undo stack.
        
        This clears the redo stack and limits the undo stack size.
        
        Args:
            operation: UndoOperation to add to stack
        """
        # Skip no-op move operations
        if hasattr(operation, 'is_noop') and operation.is_noop:
            print(f"[UndoManager] Skipping no-op operation: {operation}")
            return
        
        self.undo_stack.append(operation)
        self.redo_stack.clear()
        
        # Enforce stack size limit
        if len(self.undo_stack) > self.limit:
            removed = self.undo_stack.pop(0)
            print(f"[UndoManager] Stack limit reached, removed: {removed}")
        
        print(f"[UndoManager] Pushed: {operation} (stack size: {len(self.undo_stack)})")
        self._notify_state_changed()
    
    def undo(self, canvas_manager) -> bool:
        """
        Undo the last operation.
        
        Args:
            canvas_manager: ModelCanvasManager instance to modify
            
        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self.undo_stack:
            print("[UndoManager] Nothing to undo")
            return False
        
        operation = self.undo_stack.pop()
        print(f"[UndoManager] Undoing: {operation}")
        
        try:
            operation.undo(canvas_manager)
            self.redo_stack.append(operation)
            self._notify_state_changed()
            return True
        except Exception as e:
            print(f"[UndoManager] Error during undo: {e}")
            # Push back to undo stack on failure
            self.undo_stack.append(operation)
            return False
    
    def redo(self, canvas_manager) -> bool:
        """
        Redo the last undone operation.
        
        Args:
            canvas_manager: ModelCanvasManager instance to modify
            
        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self.redo_stack:
            print("[UndoManager] Nothing to redo")
            return False
        
        operation = self.redo_stack.pop()
        print(f"[UndoManager] Redoing: {operation}")
        
        try:
            operation.redo(canvas_manager)
            self.undo_stack.append(operation)
            self._notify_state_changed()
            return True
        except Exception as e:
            print(f"[UndoManager] Error during redo: {e}")
            # Push back to redo stack on failure
            self.redo_stack.append(operation)
            return False
    
    def can_undo(self) -> bool:
        """
        Check if undo is available.
        
        Returns:
            True if there are operations to undo
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """
        Check if redo is available.
        
        Returns:
            True if there are operations to redo
        """
        return len(self.redo_stack) > 0
    
    def clear(self):
        """
        Clear both undo and redo stacks.
        
        Called when loading a new file or clearing the canvas.
        """
        self.undo_stack.clear()
        self.redo_stack.clear()
        print("[UndoManager] Cleared all undo/redo history")
        self._notify_state_changed()
    
    def set_state_changed_callback(self, callback: Callable[[bool, bool], None]):
        """
        Set a callback to be notified when undo/redo state changes.
        
        The callback receives two arguments: (can_undo, can_redo)
        
        Args:
            callback: Function to call when state changes
        """
        self._state_changed_callback = callback
    
    def _notify_state_changed(self):
        """Notify listeners that undo/redo state has changed."""
        if self._state_changed_callback:
            self._state_changed_callback(self.can_undo(), self.can_redo())
    
    def get_undo_description(self) -> Optional[str]:
        """
        Get description of the next operation to undo.
        
        Returns:
            String description or None if nothing to undo
        """
        if not self.undo_stack:
            return None
        return str(self.undo_stack[-1])
    
    def get_redo_description(self) -> Optional[str]:
        """
        Get description of the next operation to redo.
        
        Returns:
            String description or None if nothing to redo
        """
        if not self.redo_stack:
            return None
        return str(self.redo_stack[-1])
    
    def __str__(self) -> str:
        """Return string representation for debugging."""
        return f"UndoManager(undo={len(self.undo_stack)}, redo={len(self.redo_stack)})"
