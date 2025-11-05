"""Document controller for Petri net object management.

Manages Petri net objects (places, transitions, arcs) and document state.
Handles object creation, deletion, ID generation, and document metadata.

This is a stateful controller managing object collections and document state.
"""

from datetime import datetime
from shypn.netobjs import Place, Arc, Transition
from shypn.data.canvas.id_manager import IDManager


class DocumentController:
    """Controller for Petri net document state and objects.
    
    Responsibilities:
    - Object collections (places, transitions, arcs)
    - Object creation with auto ID generation
    - Object removal with cascade (remove connected arcs)
    - Object lookup (find at position, get all objects)
    - Document metadata (filename, modified state, timestamps)
    - Document operations (create new, clear, reset)
    - ID counter management
    
    State managed:
    - places: List of Place instances
    - transitions: List of Transition instances
    - arcs: List of Arc instances
    - id_manager: Centralized IDManager for consistent ID generation
    - filename: Document base filename (without extension)
    - modified: Document modified flag
    - created_at, modified_at: Timestamps
    
    Design notes:
    - Objects are created with auto-incrementing IDs (P1, P2, T1, T2, A1, A2)
    - Removing nodes cascades to connected arcs
    - Rendering order: arcs → places → transitions (arcs behind nodes)
    - Hit testing order: transitions → places → arcs (easier to click nodes)
    """
    
    def __init__(self, filename="default"):
        """Initialize document controller.
        
        Args:
            filename: Base filename for document (without extension).
        """
        # Petri net object collections
        self.places = []  # List of Place instances
        self.transitions = []  # List of Transition instances
        self.arcs = []  # List of Arc instances
        
        # Centralized ID management
        self.id_manager = IDManager()
        
        # Document metadata
        self.filename = filename
        self.modified = False
        self.created_at = datetime.now()
        self.modified_at = None
        
        # Dirty flag for redraw tracking
        self._needs_redraw = True
        
        # Change callback (set by parent to mark modified)
        self._on_change_callback = None
    
    # ==================== Object Creation ====================
    
    def add_place(self, x, y, **kwargs):
        """Create and add a Place at the specified position.
        
        Args:
            x: X coordinate in world space.
            y: Y coordinate in world space.
            **kwargs: Additional Place parameters (radius, label, etc.).
            
        Returns:
            Place: The newly created place instance.
        """
        place_id = self.id_manager.generate_place_id()
        place_name = place_id  # Name matches ID
        
        place = Place(x, y, place_id, place_name, **kwargs)
        if self._on_change_callback:
            place.on_changed = self._on_change_callback
        self.places.append(place)
        
        self.mark_modified()
        return place
    
    def add_transition(self, x, y, **kwargs):
        """Create and add a Transition at the specified position.
        
        Args:
            x: X coordinate in world space.
            y: Y coordinate in world space.
            **kwargs: Additional Transition parameters (width, height, label, etc.).
            
        Returns:
            Transition: The newly created transition instance.
        """
        transition_id = self.id_manager.generate_transition_id()
        transition_name = transition_id  # Name matches ID
        
        transition = Transition(x, y, transition_id, transition_name, **kwargs)
        if self._on_change_callback:
            transition.on_changed = self._on_change_callback
        self.transitions.append(transition)
        
        self.mark_modified()
        return transition
    
    def add_arc(self, source, target, **kwargs):
        """Create and add an Arc between two objects.
        
        Args:
            source: Source object instance (Place or Transition).
            target: Target object instance (Place or Transition).
            **kwargs: Additional Arc parameters (weight, etc.).
            
        Returns:
            Arc: The newly created arc instance.
        """
        arc_id = self.id_manager.generate_arc_id()
        arc_name = arc_id  # Name matches ID
        
        arc = Arc(source, target, arc_id, arc_name, **kwargs)
        if self._on_change_callback:
            arc.on_changed = self._on_change_callback
        self.arcs.append(arc)
        
        self.mark_modified()
        return arc
    
    # ==================== Object Removal ====================
    
    def remove_place(self, place):
        """Remove a place from the model.
        
        Also removes all arcs connected to this place (cascade delete).
        
        Args:
            place: Place instance to remove.
        """
        if place in self.places:
            # Remove connected arcs
            self.arcs = [arc for arc in self.arcs 
                        if arc.source != place and arc.target != place]
            
            self.places.remove(place)
            self.mark_modified()
    
    def remove_transition(self, transition):
        """Remove a transition from the model.
        
        Also removes all arcs connected to this transition (cascade delete).
        
        Args:
            transition: Transition instance to remove.
        """
        if transition in self.transitions:
            # Remove connected arcs
            self.arcs = [arc for arc in self.arcs 
                        if arc.source != transition and arc.target != transition]
            
            self.transitions.remove(transition)
            self.mark_modified()
    
    def remove_arc(self, arc):
        """Remove an arc from the model.
        
        Args:
            arc: Arc instance to remove.
        """
        if arc in self.arcs:
            self.arcs.remove(arc)
            self.mark_modified()
    
    def replace_arc(self, old_arc, new_arc):
        """Replace an arc with a different type (for arc transformations).
        
        Used when transforming arcs via context menu:
        - Straight ↔ Curved
        - Normal ↔ Inhibitor
        
        The new arc maintains the same ID and properties but has a different
        class type (Arc, InhibitorArc, CurvedArc, or CurvedInhibitorArc).
        
        Args:
            old_arc: Arc instance to replace.
            new_arc: New arc instance (different class, same ID/properties).
        """
        try:
            index = self.arcs.index(old_arc)
            self.arcs[index] = new_arc
            
            # Ensure new arc has change callback
            if self._on_change_callback:
                new_arc.on_changed = self._on_change_callback
            
            self.mark_modified()
        except ValueError:
            # Arc not found in list - may have been deleted
            pass
    
    # ==================== Object Lookup ====================
    
    def get_all_objects(self):
        """Get all Petri net objects in rendering order.
        
        Rendering order: Arcs (behind) → Places and Transitions (on top).
        Arcs render first so they appear behind the nodes.
        
        Returns:
            list: All objects in rendering order.
        """
        return list(self.arcs) + list(self.places) + list(self.transitions)
    
    def find_object_at_position(self, x, y):
        """Find the topmost object at the given world position.
        
        Hit testing order (reverse of rendering): Transitions → Places → Arcs.
        Nodes are easier to click and should be prioritized.
        
        Args:
            x: X coordinate in world space.
            y: Y coordinate in world space.
            
        Returns:
            Place, Transition, Arc, or None: The object at the position, or None.
        """
        # Check in reverse rendering order (top to bottom)
        # Transitions and places are checked first (easier to click)
        for transition in reversed(self.transitions):
            if transition.contains_point(x, y):
                return transition
        
        for place in reversed(self.places):
            if place.contains_point(x, y):
                return place
        
        # Arcs are thinner and harder to click, check them last
        for arc in reversed(self.arcs):
            if arc.contains_point(x, y):
                return arc
        
        return None
    
    def get_object_count(self):
        """Get count of objects by type.
        
        Returns:
            dict: Object counts {'places': int, 'transitions': int, 'arcs': int}.
        """
        return {
            'places': len(self.places),
            'transitions': len(self.transitions),
            'arcs': len(self.arcs),
        }
    
    # ==================== Document Operations ====================
    
    def create_new_document(self, filename="default"):
        """Initialize a new document with default state.
        
        Args:
            filename: Base filename without extension.
        """
        # Clear all objects
        self.clear_all_objects()
        
        # Reset document metadata
        self.filename = filename
        self.modified = False
        self.created_at = datetime.now()
        self.modified_at = None
        
        self.mark_dirty()
    
    def clear_all_objects(self):
        """Remove all Petri net objects from the model.
        
        Resets collections and ID counters to fresh state.
        """
        self.places.clear()
        self.transitions.clear()
        self.arcs.clear()
        
        # Reset ID counters
        self.id_manager.reset()
        
        self.mark_dirty()
    
    def create_test_objects(self):
        """Create test objects for debugging rendering.
        
        Creates a simple Petri net: P1 → T1 → P2
        """
        # Create places
        p1 = self.add_place(-100, 0, label="P1")
        p2 = self.add_place(100, 0, label="P2")
        p1.set_tokens(2)
        p1.set_initial_marking(2)  # Set initial marking for proper reset
        
        # Create transition
        t1 = self.add_transition(0, 0, label="T1")
        
        # Create arcs
        self.add_arc(p1, t1, weight=1)
        self.add_arc(t1, p2, weight=1)
    
    # ==================== Document Metadata ====================
    
    def mark_modified(self):
        """Mark document as modified."""
        if not self.modified:
            self.modified = True
            self.modified_at = datetime.now()
        self.mark_dirty()  # Always mark dirty, even if already modified
    
    def mark_clean(self):
        """Mark document as clean (saved)."""
        self.modified = False
    
    def set_filename(self, filename):
        """Set the document filename.
        
        Args:
            filename: Base filename without extension.
        """
        if filename != self.filename:
            self.filename = filename
            self.mark_modified()
    
    def is_default_filename(self):
        """Check if document has the default filename (unsaved state).
        
        Returns:
            bool: True if filename is "default", False otherwise.
        """
        return self.filename == "default"
    
    def get_document_info(self):
        """Get document metadata for debugging.
        
        Returns:
            dict: Document information.
        """
        return {
            'filename': self.filename,
            'modified': self.modified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'object_count': self.get_object_count(),
        }
    
    # ==================== Redraw Management ====================
    
    def needs_redraw(self):
        """Check if document needs redrawing.
        
        Returns:
            bool: True if redraw is needed.
        """
        return self._needs_redraw
    
    def mark_dirty(self):
        """Mark document as dirty (needs redraw)."""
        self._needs_redraw = True
    
    def mark_redraw_clean(self):
        """Mark document as clean (drawn)."""
        self._needs_redraw = False
    
    # ==================== Callbacks ====================
    
    def set_change_callback(self, callback):
        """Set callback to be called when objects change.
        
        Args:
            callback: Function to call on object changes.
        """
        self._on_change_callback = callback
        
        # Update existing objects
        for obj in self.get_all_objects():
            obj.on_changed = callback
