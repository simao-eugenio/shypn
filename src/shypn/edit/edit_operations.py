#!/usr/bin/env python3
"""Edit Operations - Core editing operations (undo, redo, clipboard, etc.)."""


class EditOperations:
    """Manages editing operations for the canvas.
    
    Provides:
    - Undo/Redo history management
    - Clipboard operations (cut, copy, paste)
    - Selection modes (rectangle, lasso)
    - Object operations (duplicate, group, align)
    
    This class contains the actual business logic for operations,
    separate from UI concerns.
    """
    
    def __init__(self, canvas_manager):
        """Initialize edit operations.
        
        Args:
            canvas_manager: ModelCanvasManager instance
        """
        self.canvas_manager = canvas_manager
        
        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_levels = 50
        
        # Clipboard
        self.clipboard = []
        
        # Selection mode
        self.selection_mode = 'rectangle'  # or 'lasso'
        
        # Lasso selector (created on demand)
        self.lasso_selector = None
        
        # State change callback (for updating UI)
        self.on_state_changed = None
    
    def set_state_change_callback(self, callback):
        """Set callback for state changes.
        
        Args:
            callback: Function to call when state changes
                     Should accept (undo_available, redo_available, has_selection)
        """
        self.on_state_changed = callback
    
    def _notify_state_changed(self):
        """Notify listeners that state has changed."""
        if self.on_state_changed:
            undo_avail = self.can_undo()
            redo_avail = self.can_redo()
            has_sel = self._has_selection()
            self.on_state_changed(undo_avail, redo_avail, has_sel)
    
    def _has_selection(self):
        """Check if there are selected objects.
        
        Returns:
            bool: True if selection is not empty
        """
        if not self.canvas_manager or not self.canvas_manager.selection_manager:
            return False
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        return len(selected) > 0
    
    # Selection Modes
    def activate_select_mode(self):
        """Activate normal rectangle selection mode."""
        self.selection_mode = 'rectangle'
        # Deactivate any active tool
        if self.canvas_manager.is_tool_active():
            self.canvas_manager.set_tool('select')
    
    def activate_lasso_mode(self):
        """Activate lasso selection mode."""
        from shypn.edit.lasso_selector import LassoSelector
        self.selection_mode = 'lasso'
        if not self.lasso_selector:
            self.lasso_selector = LassoSelector(self.canvas_manager)
        # TODO: Implement lasso activation
    
    # History Operations
    def undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            return
        
        operation = self.undo_stack.pop()
        self.redo_stack.append(operation)
        
        # Apply reverse operation
        operation.undo()
        
        self._notify_state_changed()
    
    def redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            return
        
        operation = self.redo_stack.pop()
        self.undo_stack.append(operation)
        
        # Apply forward operation
        operation.redo()
        
        self._notify_state_changed()
    
    def push_operation(self, operation):
        """Add an operation to the undo stack.
        
        Args:
            operation: Operation instance with undo/redo methods
        """
        self.undo_stack.append(operation)
        self.redo_stack.clear()  # Clear redo when new operation added
        
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)
        
        self._notify_state_changed()
    
    def can_undo(self):
        """Check if undo is available.
        
        Returns:
            bool: True if can undo
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if redo is available.
        
        Returns:
            bool: True if can redo
        """
        return len(self.redo_stack) > 0
    
    # Clipboard Operations
    def cut(self):
        """Cut selected objects to clipboard."""
        if not self._has_selection():
            return
        
        self.copy()
        # Delete selected objects
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        for obj in selected:
            self.canvas_manager.delete_object(obj)
        
        self._notify_state_changed()
    
    def copy(self):
        """Copy selected objects to clipboard."""
        if not self._has_selection():
            return
        
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        self.clipboard = [self._serialize_object(obj) for obj in selected]
        
    
    def paste(self):
        """Paste objects from clipboard."""
        if not self.clipboard:
            return
        
        # Paste with offset to avoid exact overlap
        offset_x, offset_y = 20, 20
        
        # TODO: Implement object creation from clipboard data
        
        self._notify_state_changed()
    
    def _serialize_object(self, obj):
        """Serialize object to dict for clipboard.
        
        Args:
            obj: PetriNetObject instance
            
        Returns:
            dict: Serialized object data
        """
        # TODO: Implement proper serialization
        return {
            'type': type(obj).__name__,
            'x': obj.x,
            'y': obj.y,
            'data': {}
        }
    
    def _deserialize_object(self, obj_data):
        """Deserialize object from dict.
        
        Args:
            obj_data: dict with object data
            
        Returns:
            PetriNetObject: Recreated object
        """
        # TODO: Implement proper deserialization
        pass
    
    # Object Operations
    def duplicate_selection(self):
        """Duplicate selected objects."""
        if not self._has_selection():
            return
        
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        # TODO: Implement duplication with offset
        
        self._notify_state_changed()
    
    def group_selection(self):
        """Group selected objects."""
        if not self._has_selection():
            return
        
        # TODO: Implement grouping (future feature)
    
    def show_align_dialog(self):
        """Show alignment dialog for selected objects."""
        if not self._has_selection():
            return
        
        # TODO: Implement alignment dialog
