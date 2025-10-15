"""Selection Manager for Petri Net Objects.

Manages selection state and provides queries for selected objects.

Selection Modes:
- NORMAL: Selection for operations (arc creation, dragging, grouping)
           Shows basic blue highlight only
- EDIT:   Selection for transformation (resize, rotate, scale)
           Shows blue highlight + transform handles
"""
from typing import List, Optional, Tuple, Set
from enum import Enum


class SelectionMode(Enum):
    """Selection mode enumeration."""
    NORMAL = "normal"  # Selection for operations (arc creation, drag, etc.)
    EDIT = "edit"      # Selection for editing/transformation (resize, rotate, etc.)


class SelectionManager:
    """Manages selection state for canvas objects."""
    
    def __init__(self):
        """Initialize selection manager."""
        self.selected_objects: Set[int] = set()  # Set of selected object IDs
        self._selection_history: List[Set[int]] = []  # For undo (future feature)
        self.selection_mode = SelectionMode.NORMAL  # Current selection mode
        self.edit_target = None  # Object currently in edit mode (only one at a time)
    
    def select(self, obj, multi: bool = False, manager=None):
        """Select an object.
        
        Args:
            obj: Object to select (PetriNetObject)
            multi: If True, add to selection (Ctrl+Click). If False, replace selection.
            manager: Canvas manager (needed to clear other objects' selected flags)
        """
        if not multi:
            # Clear other selections
            if manager:
                # Properly clear all object selected flags
                for other_obj in manager.get_all_objects():
                    if other_obj != obj:
                        other_obj.selected = False
            self.selected_objects.clear()
        
        obj.selected = True
        self.selected_objects.add(id(obj))
    
    def deselect(self, obj):
        """Deselect an object.
        
        Args:
            obj: Object to deselect (PetriNetObject)
        """
        obj.selected = False
        self.selected_objects.discard(id(obj))
    
    def toggle_selection(self, obj, multi: bool = False, manager=None):
        """Toggle object selection state.
        
        Single-click behavior:
        - If multi=False (no Ctrl): Select only this object (clear others)
        - If multi=True (Ctrl held): Toggle this object in/out of group selection
        
        Args:
            obj: Object to toggle (PetriNetObject)
            multi: If True, toggle within multi-selection mode (Ctrl+Click)
            manager: Canvas manager (needed to clear other objects when multi=False)
        """
        if multi:
            # Multi-select mode (Ctrl): Toggle the object in/out
            if obj.selected:
                self.deselect(obj)
            else:
                self.select(obj, multi=True, manager=manager)
        else:
            # Single-select mode: Always select this object (clear others if needed)
            if obj.selected and len(self.selected_objects) == 1:
                # Already the only selected object - keep it selected
                pass
            else:
                # Either not selected, or other objects are selected too
                # Clear all and select only this one
                self.select(obj, multi=False, manager=manager)
    
    def clear_selection(self):
        """Clear all selections.
        
        Note: This requires iterating through objects to clear their state.
        Call this with manager.clear_all_selections() which handles the iteration.
        """
        self.selected_objects.clear()
    
    def get_selected_objects(self, manager) -> List:
        """Get list of currently selected objects.
        
        Args:
            manager: Canvas manager to query objects from
            
        Returns:
            List of selected PetriNetObject instances
        """
        selected = []
        for obj in manager.get_all_objects():
            if obj.selected:
                selected.append(obj)
        return selected
    
    def get_selection_bounds(self, manager) -> Optional[Tuple[float, float, float, float]]:
        """Calculate bounding box of selected objects.
        
        Args:
            manager: Canvas manager to query objects from
        
        Returns:
            (min_x, min_y, max_x, max_y) in world coordinates, or None if no selection
        """
        from shypn.netobjs import Place, Transition, Arc
        
        selected = self.get_selected_objects(manager)
        if not selected:
            return None
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for obj in selected:
            if isinstance(obj, Place):
                # Circle bounds
                min_x = min(min_x, obj.x - obj.radius)
                min_y = min(min_y, obj.y - obj.radius)
                max_x = max(max_x, obj.x + obj.radius)
                max_y = max(max_y, obj.y + obj.radius)
            elif isinstance(obj, Transition):
                # Rectangle bounds
                w = obj.width if obj.horizontal else obj.height
                h = obj.height if obj.horizontal else obj.width
                half_w = w / 2
                half_h = h / 2
                min_x = min(min_x, obj.x - half_w)
                min_y = min(min_y, obj.y - half_h)
                max_x = max(max_x, obj.x + half_w)
                max_y = max(max_y, obj.y + half_h)
            elif isinstance(obj, Arc):
                # Arc bounds: bounding box of source and target endpoints
                src_x, src_y = obj.source.x, obj.source.y
                tgt_x, tgt_y = obj.target.x, obj.target.y
                min_x = min(min_x, src_x, tgt_x)
                min_y = min(min_y, src_y, tgt_y)
                max_x = max(max_x, src_x, tgt_x)
                max_y = max(max_y, src_y, tgt_y)
        
        return (min_x, min_y, max_x, max_y)
    
    def has_selection(self) -> bool:
        """Check if any objects are selected.
        
        Returns:
            True if at least one object is selected
        """
        return len(self.selected_objects) > 0
    
    def selection_count(self) -> int:
        """Get number of selected objects.
        
        Returns:
            Count of selected objects
        """
        return len(self.selected_objects)
    
    def enter_edit_mode(self, obj, manager=None):
        """Enter edit mode for a single object.
        
        Edit mode shows transform handles and allows transformation operations.
        Only one object can be in edit mode at a time.
        
        Args:
            obj: Object to enter edit mode for
            manager: Canvas manager (needed to clear other selections)
        """
        # Exit any previous edit mode
        self.exit_edit_mode()
        
        # Enter edit mode
        self.selection_mode = SelectionMode.EDIT
        self.edit_target = obj
        
        # Make sure object is selected
        if not obj.selected:
            self.select(obj, multi=False, manager=manager)
    
    def exit_edit_mode(self):
        """Exit edit mode and return to normal selection mode."""
        self.selection_mode = SelectionMode.NORMAL
        self.edit_target = None
    
    def is_edit_mode(self) -> bool:
        """Check if currently in edit mode.
        
        Returns:
            True if in edit mode, False if in normal mode
        """
        return self.selection_mode == SelectionMode.EDIT
    
    def is_normal_mode(self) -> bool:
        """Check if currently in normal selection mode.
        
        Returns:
            True if in normal mode, False if in edit mode
        """
        return self.selection_mode == SelectionMode.NORMAL
    
    def get_edit_target(self):
        """Get the object currently in edit mode.
        
        Returns:
            Object in edit mode, or None if not in edit mode
        """
        return self.edit_target if self.is_edit_mode() else None
    
    # ==================== Drag Support ====================
    
    def __init_drag_controller(self):
        """Lazy initialize drag controller."""
        if not hasattr(self, '_drag_controller'):
            from shypn.edit.drag_controller import DragController
            self._drag_controller = DragController()
    
    def start_drag(self, clicked_obj, screen_x: float, screen_y: float, manager):
        """Start dragging selected objects if clicking on a selected object.
        
        Args:
            clicked_obj: The object that was clicked
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate  
            manager: Canvas manager for getting selected objects
            
        Returns:
            True if drag started, False otherwise
        """
        # Only drag if clicking on a selected object
        if clicked_obj and clicked_obj.selected:
            self.__init_drag_controller()
            selected_objs = self.get_selected_objects(manager)
            
            # Filter to only draggable objects (Places and Transitions)
            # Arcs don't have x,y coordinates - they follow their source/target
            from shypn.netobjs.place import Place
            from shypn.netobjs.transition import Transition
            draggable_objs = [obj for obj in selected_objs 
                            if isinstance(obj, (Place, Transition))]
            
            if hasattr(clicked_obj, 'name'):
                pass  # Debug info removed
            
            # Only start drag if there are draggable objects
            if draggable_objs:
                self._drag_controller.start_drag(draggable_objs, screen_x, screen_y)
                return True
        return False
    
    def update_drag(self, screen_x: float, screen_y: float, canvas):
        """Update drag positions during motion.
        
        Args:
            screen_x: Current screen X coordinate
            screen_y: Current screen Y coordinate
            canvas: Canvas/manager with screen_to_world method
            
        Returns:
            True if drag was updated, False if not dragging
        """
        if hasattr(self, '_drag_controller') and self._drag_controller.is_dragging():
            self._drag_controller.update_drag(screen_x, screen_y, canvas)
            return True
        return False
    
    def end_drag(self):
        """End the current drag operation.
        
        Returns:
            True if drag was ended, False if wasn't dragging
        """
        if hasattr(self, '_drag_controller') and self._drag_controller.is_dragging():
            self._drag_controller.end_drag()
            return True
        return False
    
    def cancel_drag(self):
        """Cancel drag and restore original positions.
        
        Returns:
            True if drag was cancelled, False if wasn't dragging
        """
        if hasattr(self, '_drag_controller') and self._drag_controller.is_dragging():
            self._drag_controller.cancel_drag()
            return True
        return False
    
    def is_dragging(self) -> bool:
        """Check if currently dragging objects.
        
        Returns:
            True if dragging, False otherwise
        """
        return hasattr(self, '_drag_controller') and self._drag_controller.is_dragging()
    
    def get_move_data_for_undo(self):
        """Get move data for undo operation.
        
        Returns initial positions of currently dragged objects for undo support.
        This should be called BEFORE end_drag() to capture the move operation.
        
        Returns:
            Dictionary mapping object id() to (initial_x, initial_y) tuples,
            or empty dict if not dragging
        """
        if hasattr(self, '_drag_controller') and self._drag_controller.is_dragging():
            return self._drag_controller.get_initial_positions()
        return {}
