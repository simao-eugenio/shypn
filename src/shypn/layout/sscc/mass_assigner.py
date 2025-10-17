"""Mass Assigner - Assigns gravitational masses to Petri net objects.

This module implements the mass hierarchy system where different object
types have different masses for the gravitational simulation:
- SCCs (cycles) → Heavy (stars)
- Places → Medium (planets)
- Transitions → Light (satellites)
"""

from typing import Dict, List
from shypn.netobjs import Place, Transition
from shypn.layout.sscc.strongly_connected_component import StronglyConnectedComponent


class MassAssigner:
    """Assigns gravitational masses to objects for physics simulation.
    
    Mass hierarchy determines how strongly objects attract each other:
    - Higher mass → stronger gravitational pull
    - SCCs are massive (act as gravitational centers)
    - Places have medium mass (orbit SCCs)
    - Transitions have low mass (orbit places)
    """
    
    # Mass constants (configurable)
    MASS_SCC = 1000.0        # Stars (massive gravitational centers)
    MASS_PLACE = 100.0       # Planets (medium mass)
    MASS_TRANSITION = 50.0   # Satellites (increased from 10 for better repulsion)
    
    def __init__(self, mass_scc: float = None, mass_place: float = None, 
                 mass_transition: float = None):
        """Initialize mass assigner with optional custom masses.
        
        Args:
            mass_scc: Mass for SCCs (default: 1000.0)
            mass_place: Mass for places (default: 100.0)
            mass_transition: Mass for transitions (default: 10.0)
        """
        self.mass_scc = mass_scc if mass_scc is not None else self.MASS_SCC
        self.mass_place = mass_place if mass_place is not None else self.MASS_PLACE
        self.mass_transition = mass_transition if mass_transition is not None else self.MASS_TRANSITION
    
    def assign_masses(self, sccs: List[StronglyConnectedComponent],
                      places: List[Place], 
                      transitions: List[Transition]) -> Dict[int, float]:
        """Assign masses to all objects.
        
        Args:
            sccs: List of strongly connected components
            places: List of Place objects
            transitions: List of Transition objects
            
        Returns:
            Dict mapping object ID to mass value
        """
        masses = {}
        
        # Collect all nodes in SCCs
        scc_nodes = set()
        for scc in sccs:
            for node_id in scc.node_ids:
                scc_nodes.add(node_id)
        
        # Assign SCC mass to nodes within SCCs
        # Note: In Solar System Layout, entire SCC acts as a single "star"
        # So we give high mass to ALL nodes in the SCC
        for node_id in scc_nodes:
            masses[node_id] = self.mass_scc
        
        # Assign place mass (if not in SCC)
        for place in places:
            if place.id not in scc_nodes:
                masses[place.id] = self.mass_place
        
        # Assign transition mass (if not in SCC)
        for transition in transitions:
            if transition.id not in scc_nodes:
                masses[transition.id] = self.mass_transition
        
        return masses
    
    def get_mass(self, obj_id: int, masses: Dict[int, float]) -> float:
        """Get mass for a specific object.
        
        Args:
            obj_id: Object ID
            masses: Mass dictionary from assign_masses()
            
        Returns:
            Mass value (or 1.0 if not found)
        """
        return masses.get(obj_id, 1.0)
    
    def set_custom_masses(self, mass_scc: float, mass_place: float, 
                         mass_transition: float):
        """Update mass constants (for user configuration).
        
        Args:
            mass_scc: New SCC mass
            mass_place: New place mass
            mass_transition: New transition mass
        """
        self.mass_scc = mass_scc
        self.mass_place = mass_place
        self.mass_transition = mass_transition
    
    def get_mass_ratio(self) -> Dict[str, float]:
        """Get mass ratios relative to transitions.
        
        Returns:
            Dict with mass ratios
        """
        if self.mass_transition == 0:
            return {'scc': float('inf'), 'place': float('inf'), 'transition': 1.0}
        
        return {
            'scc': self.mass_scc / self.mass_transition,
            'place': self.mass_place / self.mass_transition,
            'transition': 1.0
        }
