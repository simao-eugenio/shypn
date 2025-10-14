"""Document Model - Petri Net Object Storage and Queries.

This module manages the Petri net objects (Places, Transitions, Arcs) for a document.
It provides storage, queries, and basic operations without coupling to UI or rendering.

The DocumentModel is purely about data storage and retrieval - it doesn't know about
viewports, rendering, or UI interactions.
"""

from typing import List, Optional, Tuple, Set
from shypn.netobjs import Place, Transition, Arc, PetriNetObject


class DocumentModel:
    """Manages Petri net objects for a document.
    
    This class provides:
    - Object storage (places, transitions, arcs)
    - Spatial queries (objects at point, in rectangle)
    - Object lifecycle (add, remove)
    - Validation (arc connectivity rules)
    - Collection operations (get all, clear)
    
    The model is independent of viewport and rendering concerns.
    """
    
    def __init__(self):
        """Initialize empty document model."""
        self.places: List[Place] = []
        self.transitions: List[Transition] = []
        self.arcs: List[Arc] = []
        
        # Track next available IDs for objects
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        
        # View state (zoom and pan position)
        self.view_state = {
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0
        }
    
    # ============================================================================
    # Object Creation
    # ============================================================================
    
    def create_place(self, x: float, y: float, label: str = "") -> Place:
        """Create a new place at the given position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            label: Optional label for the place
            
        Returns:
            The created Place object
        """
        place_id = self._next_place_id
        place_name = f"P{place_id}"
        self._next_place_id += 1
        
        place = Place(x=x, y=y, id=place_id, name=place_name, label=label or place_name)
        self.places.append(place)
        return place
    
    def create_transition(self, x: float, y: float, label: str = "") -> Transition:
        """Create a new transition at the given position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            label: Optional label for the transition
            
        Returns:
            The created Transition object
        """
        transition_id = self._next_transition_id
        transition_name = f"T{transition_id}"
        self._next_transition_id += 1
        
        transition = Transition(x=x, y=y, id=transition_id, name=transition_name, label=label or transition_name)
        self.transitions.append(transition)
        return transition
    
    def create_arc(self, source: PetriNetObject, target: PetriNetObject, 
                   weight: int = 1) -> Optional[Arc]:
        """Create a new arc connecting source to target.
        
        Args:
            source: Source object (Place or Transition)
            target: Target object (must be different type from source)
            weight: Arc weight (default 1)
            
        Returns:
            The created Arc object, or None if connection is invalid
        """
        # Validate connection (Place→Transition or Transition→Place)
        source_is_place = isinstance(source, Place)
        target_is_place = isinstance(target, Place)
        
        if source_is_place == target_is_place:
            # Both same type → invalid
            return None
        
        arc_id = self._next_arc_id
        arc_name = f"A{arc_id}"
        self._next_arc_id += 1
        
        try:
            arc = Arc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            self.arcs.append(arc)
            return arc
        except ValueError:
            # Arc validation failed
            return None
    
    # ============================================================================
    # Object Addition (for loading existing objects)
    # ============================================================================
    
    def add_place(self, place: Place):
        """Add an existing place to the model.
        
        Args:
            place: Place object to add
        """
        if place not in self.places:
            self.places.append(place)
    
    def add_transition(self, transition: Transition):
        """Add an existing transition to the model.
        
        Args:
            transition: Transition object to add
        """
        if transition not in self.transitions:
            self.transitions.append(transition)
    
    def add_arc(self, arc: Arc):
        """Add an existing arc to the model.
        
        Args:
            arc: Arc object to add
        """
        if arc not in self.arcs:
            self.arcs.append(arc)
    
    # ============================================================================
    # Object Removal
    # ============================================================================
    
    def remove_place(self, place: Place) -> bool:
        """Remove a place and all connected arcs.
        
        Args:
            place: Place to remove
            
        Returns:
            True if removed, False if not found
        """
        if place not in self.places:
            return False
        
        # Remove all arcs connected to this place
        self.arcs = [arc for arc in self.arcs 
                     if arc.source != place and arc.target != place]
        
        self.places.remove(place)
        return True
    
    def remove_transition(self, transition: Transition) -> bool:
        """Remove a transition and all connected arcs.
        
        Args:
            transition: Transition to remove
            
        Returns:
            True if removed, False if not found
        """
        if transition not in self.transitions:
            return False
        
        # Remove all arcs connected to this transition
        self.arcs = [arc for arc in self.arcs 
                     if arc.source != transition and arc.target != transition]
        
        self.transitions.remove(transition)
        return True
    
    def remove_arc(self, arc: Arc) -> bool:
        """Remove an arc.
        
        Args:
            arc: Arc to remove
            
        Returns:
            True if removed, False if not found
        """
        if arc in self.arcs:
            self.arcs.remove(arc)
            return True
        return False
    
    def remove_object(self, obj: PetriNetObject) -> bool:
        """Remove any Petri net object (place, transition, or arc).
        
        Args:
            obj: Object to remove
            
        Returns:
            True if removed, False if not found
        """
        if isinstance(obj, Place):
            return self.remove_place(obj)
        elif isinstance(obj, Transition):
            return self.remove_transition(obj)
        elif isinstance(obj, Arc):
            return self.remove_arc(obj)
        return False
    
    # ============================================================================
    # Spatial Queries
    # ============================================================================
    
    def get_object_at_point(self, x: float, y: float, 
                           tolerance: float = 5.0) -> Optional[PetriNetObject]:
        """Find object at the given point (world coordinates).
        
        Checks in order: Places, Transitions, Arcs
        Uses object-specific hit testing.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            tolerance: Hit test tolerance in world units
            
        Returns:
            The object at the point, or None if no object found
        """
        # Check places (circular hit test)
        for place in self.places:
            dx = x - place.x
            dy = y - place.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= place.radius + tolerance:
                return place
        
        # Check transitions (rectangular hit test)
        for transition in self.transitions:
            half_w = transition.width / 2
            half_h = transition.height / 2
            if (transition.x - half_w - tolerance <= x <= transition.x + half_w + tolerance and
                transition.y - half_h - tolerance <= y <= transition.y + half_h + tolerance):
                return transition
        
        # Check arcs (line hit test - simplified)
        for arc in self.arcs:
            if self._point_near_arc(x, y, arc, tolerance):
                return arc
        
        return None
    
    def _point_near_arc(self, x: float, y: float, arc: Arc, tolerance: float) -> bool:
        """Check if point is near an arc line.
        
        Simplified version - checks distance to line segment.
        """
        # Get arc endpoints
        sx, sy = arc.source.x, arc.source.y
        tx, ty = arc.target.x, arc.target.y
        
        # Vector from source to target
        dx = tx - sx
        dy = ty - sy
        length_sq = dx * dx + dy * dy
        
        if length_sq == 0:
            # Degenerate arc (source == target)
            return False
        
        # Project point onto line segment
        t = max(0, min(1, ((x - sx) * dx + (y - sy) * dy) / length_sq))
        
        # Closest point on segment
        closest_x = sx + t * dx
        closest_y = sy + t * dy
        
        # Distance from point to closest point
        dist_sq = (x - closest_x) ** 2 + (y - closest_y) ** 2
        
        return dist_sq <= (tolerance ** 2)
    
    def get_objects_in_rectangle(self, x1: float, y1: float, 
                                 x2: float, y2: float) -> List[PetriNetObject]:
        """Find all objects within a rectangle (world coordinates).
        
        Args:
            x1: Left edge
            y1: Top edge
            x2: Right edge
            y2: Bottom edge
            
        Returns:
            List of objects within the rectangle
        """
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        objects = []
        
        # Check places
        for place in self.places:
            if (min_x <= place.x <= max_x and min_y <= place.y <= max_y):
                objects.append(place)
        
        # Check transitions
        for transition in self.transitions:
            if (min_x <= transition.x <= max_x and min_y <= transition.y <= max_y):
                objects.append(transition)
        
        # Note: Not including arcs in rectangle selection (common UX pattern)
        
        return objects
    
    # ============================================================================
    # Collection Operations
    # ============================================================================
    
    def get_all_objects(self) -> List[PetriNetObject]:
        """Get all objects in the model.
        
        Returns:
            List containing all places, transitions, and arcs
        """
        return self.places + self.transitions + self.arcs
    
    def get_connected_arcs(self, obj: PetriNetObject) -> List[Arc]:
        """Get all arcs connected to an object.
        
        Args:
            obj: Place or Transition to check
            
        Returns:
            List of connected arcs
        """
        return [arc for arc in self.arcs 
                if arc.source == obj or arc.target == obj]
    
    def clear(self):
        """Remove all objects from the model."""
        self.places.clear()
        self.transitions.clear()
        self.arcs.clear()
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
    
    # ============================================================================
    # Statistics
    # ============================================================================
    
    def get_object_count(self) -> Tuple[int, int, int]:
        """Get count of objects in the model.
        
        Returns:
            Tuple of (places_count, transitions_count, arcs_count)
        """
        return (len(self.places), len(self.transitions), len(self.arcs))
    
    def is_empty(self) -> bool:
        """Check if model has no objects.
        
        Returns:
            True if model is empty
        """
        return len(self.places) == 0 and len(self.transitions) == 0 and len(self.arcs) == 0
    
    # ============================================================================
    # Persistence (Serialization/Deserialization)
    # ============================================================================
    
    def to_dict(self) -> dict:
        """Serialize entire document to dictionary.
        
        Returns:
            Dictionary containing all document data in JSON-compatible format
        """
        from datetime import datetime
        
        return {
            "version": "2.0",
            "metadata": {
                "created": datetime.now().isoformat(),
                "object_counts": {
                    "places": len(self.places),
                    "transitions": len(self.transitions),
                    "arcs": len(self.arcs)
                }
            },
            "view_state": self.view_state,
            "places": [place.to_dict() for place in self.places],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "arcs": [arc.to_dict() for arc in self.arcs]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentModel':
        """Deserialize document from dictionary.
        
        Args:
            data: Dictionary containing document data
            
        Returns:
            DocumentModel instance with all objects restored
            
        Raises:
            ValueError: If data format is invalid
        """
        # Create empty document
        document = cls()
        
        # Check version (for future compatibility)
        version = data.get("version", "1.0")
        if not version.startswith("2."):
            pass  # Version check - could add migration logic here
        
        # Restore places first (they have no dependencies)
        places_dict = {}
        for place_data in data.get("places", []):
            place = Place.from_dict(place_data)
            document.places.append(place)
            places_dict[place.id] = place
            # Update next ID counter
            document._next_place_id = max(document._next_place_id, place.id + 1)
        
        # Restore transitions second (they have no dependencies)
        transitions_dict = {}
        for transition_data in data.get("transitions", []):
            transition = Transition.from_dict(transition_data)
            document.transitions.append(transition)
            transitions_dict[transition.id] = transition
            # Update next ID counter
            document._next_transition_id = max(document._next_transition_id, transition.id + 1)
        
        # Restore arcs last (they depend on places and transitions)
        for arc_data in data.get("arcs", []):
            arc = Arc.from_dict(arc_data, places=places_dict, transitions=transitions_dict)
            document.arcs.append(arc)
            # Update next ID counter
            document._next_arc_id = max(document._next_arc_id, arc.id + 1)
        
        # Restore view state if present
        if "view_state" in data:
            document.view_state = data["view_state"]
        
        return document
    
    def save_to_file(self, filepath: str) -> None:
        """Save document to JSON file.
        
        Args:
            filepath: Path to save file (should already have extension like .shy)
            
        Raises:
            IOError: If file cannot be written
        """
        import json
        import os
        
        # Don't modify filepath - it should already have the correct extension (.shy)
        # The .shy extension is used for SHYpn Petri net files (which are JSON internally)
        
        # Create directory if needed
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Serialize and save
        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'DocumentModel':
        """Load document from JSON file.
        
        Args:
            filepath: Path to file to load
            
        Returns:
            DocumentModel instance loaded from file
            
        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid
        """
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        document = cls.from_dict(data)
        
        return document
