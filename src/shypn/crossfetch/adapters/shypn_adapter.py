"""Adapter for integrating CrossFetch with Shypn pathway model.

This adapter provides a bridge between CrossFetch enrichers and the actual
Shypn model classes (Place, Transition, Arc). It ensures that enrichers
can work with real Shypn objects instead of mock objects.

Architecture:
    CrossFetch Enrichers → ShypnPathwayAdapter → Place/Transition/Arc objects
    
Example:
    from shypn.netobjs import Place, Transition
    from shypn.crossfetch.adapters import ShypnPathwayAdapter
    
    # Create adapter from Shypn objects
    places = [Place(x=100, y=100, id=1, name="P1", label="Glucose")]
    transitions = [Transition(x=200, y=100, id=1, name="T1", label="Hexokinase")]
    arcs = []
    
    adapter = ShypnPathwayAdapter(places, transitions, arcs)
    
    # Use with enrichers
    enricher = ConcentrationEnricher()
    result = enricher.apply(adapter, fetch_result)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path


class ShypnPathwayAdapter:
    """Adapter that makes Shypn pathways compatible with CrossFetch enrichers.
    
    CrossFetch enrichers expect pathway objects with:
    - places: list of objects with .id, .name, .tokens, .initial_marking
    - transitions: list of objects with .id, .name, .transition_type, .rate
    - arcs: list of objects with .source, .target, .weight
    
    Shypn already has these! This adapter just provides a clean interface.
    
    Attributes:
        places: List of Place objects from Shypn model
        transitions: List of Transition objects from Shypn model
        arcs: List of Arc objects from Shypn model
        pathway_id: Optional ID for this pathway
        pathway_file: Optional Path to .shy file
    """
    
    def __init__(
        self,
        places: List[Any],
        transitions: List[Any],
        arcs: List[Any],
        pathway_id: Optional[str] = None,
        pathway_file: Optional[Path] = None
    ):
        """Initialize adapter with Shypn model objects.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects
            pathway_id: Optional pathway identifier
            pathway_file: Optional path to source .shy file
        """
        self.places = places
        self.transitions = transitions
        self.arcs = arcs
        self.pathway_id = pathway_id or "unknown"
        self.pathway_file = pathway_file
        
        # Cache for lookups
        self._place_by_id = {p.id: p for p in places}
        self._place_by_name = {p.name: p for p in places}
        self._transition_by_id = {t.id: t for t in transitions}
        self._transition_by_name = {t.name: t for t in transitions}
    
    def get_place_by_id(self, place_id: int) -> Optional[Any]:
        """Get place by ID.
        
        Args:
            place_id: Place ID
            
        Returns:
            Place object or None
        """
        return self._place_by_id.get(place_id)
    
    def get_place_by_name(self, place_name: str) -> Optional[Any]:
        """Get place by name.
        
        Args:
            place_name: Place name (e.g., "P1", "P2")
            
        Returns:
            Place object or None
        """
        return self._place_by_name.get(place_name)
    
    def get_transition_by_id(self, transition_id: int) -> Optional[Any]:
        """Get transition by ID.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            Transition object or None
        """
        return self._transition_by_id.get(transition_id)
    
    def get_transition_by_name(self, transition_name: str) -> Optional[Any]:
        """Get transition by name.
        
        Args:
            transition_name: Transition name (e.g., "T1", "T2")
            
        Returns:
            Transition object or None
        """
        return self._transition_by_name.get(transition_name)
    
    def find_place_by_label(self, label: str) -> Optional[Any]:
        """Find place by label (case-insensitive partial match).
        
        Useful for matching biological names from external data.
        Example: "glucose" matches Place with label="Glucose"
        
        Args:
            label: Label to search for
            
        Returns:
            First matching Place or None
        """
        label_lower = label.lower()
        for place in self.places:
            if place.label and label_lower in place.label.lower():
                return place
        return None
    
    def find_transition_by_label(self, label: str) -> Optional[Any]:
        """Find transition by label (case-insensitive partial match).
        
        Useful for matching biological names from external data.
        Example: "hexokinase" matches Transition with label="Hexokinase"
        
        Args:
            label: Label to search for
            
        Returns:
            First matching Transition or None
        """
        label_lower = label.lower()
        for transition in self.transitions:
            if transition.label and label_lower in transition.label.lower():
                return transition
        return None
    
    def add_arc(self, source: Any, target: Any, weight: float = 1.0):
        """Add new arc between source and target.
        
        Note: This method signature is adapter-compatible but you'll need
        to import your actual Arc class to create the arc.
        
        Args:
            source: Source object (Place or Transition)
            target: Target object (Place or Transition)
            weight: Arc weight (default: 1.0)
        """
        # This is where you'd create an actual Arc object
        # For now, just document the interface
        raise NotImplementedError(
            "Arc creation requires importing shypn.netobjs.arc.Arc. "
            "Implement in subclass or provide Arc class to constructor."
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize pathway state for persistence.
        
        Returns:
            dict: Dictionary containing all pathway data
        """
        arcs_data = []
        if self.arcs and len(self.arcs) > 0 and hasattr(self.arcs[0], 'to_dict'):
            arcs_data = [a.to_dict() for a in self.arcs]
        
        return {
            'pathway_id': self.pathway_id,
            'places': [p.to_dict() for p in self.places],
            'transitions': [t.to_dict() for t in self.transitions],
            'arcs': arcs_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], place_class, transition_class, arc_class) -> 'ShypnPathwayAdapter':
        """Create adapter from serialized data.
        
        Args:
            data: Dictionary containing pathway data
            place_class: Place class for deserialization
            transition_class: Transition class for deserialization
            arc_class: Arc class for deserialization
            
        Returns:
            ShypnPathwayAdapter instance
        """
        places = [place_class.from_dict(p) for p in data.get('places', [])]
        transitions = [transition_class.from_dict(t) for t in data.get('transitions', [])]
        arcs = [arc_class.from_dict(a) for a in data.get('arcs', [])]
        
        return cls(
            places=places,
            transitions=transitions,
            arcs=arcs,
            pathway_id=data.get('pathway_id')
        )
    
    def __repr__(self) -> str:
        return (
            f"ShypnPathwayAdapter("
            f"places={len(self.places)}, "
            f"transitions={len(self.transitions)}, "
            f"arcs={len(self.arcs)}, "
            f"pathway_id={self.pathway_id!r})"
        )


def create_adapter_from_shypn_objects(
    places: List[Any],
    transitions: List[Any],
    arcs: List[Any],
    pathway_id: Optional[str] = None
) -> ShypnPathwayAdapter:
    """Convenience function to create adapter from Shypn objects.
    
    Args:
        places: List of Place objects
        transitions: List of Transition objects
        arcs: List of Arc objects
        pathway_id: Optional pathway identifier
        
    Returns:
        ShypnPathwayAdapter instance ready for enrichment
    """
    return ShypnPathwayAdapter(
        places=places,
        transitions=transitions,
        arcs=arcs,
        pathway_id=pathway_id
    )
