"""Hub-Based Mass Assignment - Alternative strategy for DAG networks.

When no SCCs (cycles) are detected, this assigns higher masses to hub nodes
(nodes with high degree) to create gravitational centers in the layout.

This is an ADAPTATION for networks without feedback loops.
"""

from typing import Dict, List
from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc.strongly_connected_component import StronglyConnectedComponent


class HubBasedMassAssigner:
    """Assigns masses based on node degree (hub detection) when no SCCs exist.
    
    Strategy:
    - Calculate in-degree + out-degree for each node
    - High-degree nodes (hubs) get higher mass → become gravitational centers
    - Creates hierarchy even in DAG networks
    
    Mass tiers:
    - Super-hubs (degree ≥ 8): mass = 1000 (like SCCs/stars)
    - Major hubs (degree ≥ 5): mass = 500 (strong attraction)
    - Minor hubs (degree ≥ 3): mass = 200 (moderate attraction)
    - Regular places: mass = 100 (normal)
    - Transitions: mass = 10 (light)
    """
    
    # Mass constants (configurable)
    MASS_SCC_NODE = 1000.0       # Nodes in SCC (black hole) - Balanced for attraction without excessive repulsion
    MASS_SUPER_HUB = 300.0       # Super-hubs (≥6 connections) - REDUCED from 1000 to 300 for tighter orbits
    MASS_MAJOR_HUB = 200.0       # Major hubs (≥4 connections) - REDUCED from 500
    MASS_MINOR_HUB = 100.0       # Minor hubs (≥2 connections) - REDUCED from 200
    MASS_PLACE = 100.0           # Regular places
    MASS_TRANSITION = 50.0       # Transitions (increased from 10 for better satellite separation)
    
    # Degree thresholds
    SUPER_HUB_THRESHOLD = 6
    MAJOR_HUB_THRESHOLD = 4
    MINOR_HUB_THRESHOLD = 2
    
    def __init__(self):
        """Initialize hub-based mass assigner."""
        self.hub_stats = {}
    
    def assign_masses(self, sccs: List[StronglyConnectedComponent],
                      places: List[Place], 
                      transitions: List[Transition],
                      arcs: List[Arc]) -> Dict[int, float]:
        """Assign masses based on hub detection.
        
        Args:
            sccs: List of SCCs (will use standard SCC mass if any exist)
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects (to calculate degree)
            
        Returns:
            Dict mapping object ID to mass value
        """
        masses = {}
        
        # If SCCs exist, assign MASSIVE mass to all nodes in SCC (black hole effect)
        scc_nodes = set()
        if sccs:
            for scc in sccs:
                for node_id in scc.node_ids:
                    scc_nodes.add(node_id)
                    # BLACK HOLE MASS: 10x heavier than super-hubs
                    masses[node_id] = self.MASS_SCC_NODE
        
        # Calculate node degrees
        in_degree, out_degree = self._calculate_degrees(places, transitions, arcs)
        
        # Assign masses to places based on degree
        for place in places:
            if place.id in scc_nodes:
                continue  # Already assigned as SCC
            
            total_degree = in_degree.get(place.id, 0) + out_degree.get(place.id, 0)
            
            if total_degree >= self.SUPER_HUB_THRESHOLD:
                masses[place.id] = self.MASS_SUPER_HUB
                self.hub_stats[place.id] = ('super-hub', total_degree)
            elif total_degree >= self.MAJOR_HUB_THRESHOLD:
                masses[place.id] = self.MASS_MAJOR_HUB
                self.hub_stats[place.id] = ('major-hub', total_degree)
            elif total_degree >= self.MINOR_HUB_THRESHOLD:
                masses[place.id] = self.MASS_MINOR_HUB
                self.hub_stats[place.id] = ('minor-hub', total_degree)
            else:
                masses[place.id] = self.MASS_PLACE
                self.hub_stats[place.id] = ('regular', total_degree)
        
        # Transitions: also apply hub-based masses (NEW!)
        # High-degree transitions can also be gravitational centers
        for transition in transitions:
            if transition.id in scc_nodes:
                continue  # Already assigned as SCC
            
            total_degree = in_degree.get(transition.id, 0) + out_degree.get(transition.id, 0)
            
            # Apply same hub logic to transitions
            if total_degree >= self.SUPER_HUB_THRESHOLD:
                masses[transition.id] = self.MASS_SUPER_HUB
                self.hub_stats[transition.id] = ('super-hub-transition', total_degree)
            elif total_degree >= self.MAJOR_HUB_THRESHOLD:
                masses[transition.id] = self.MASS_MAJOR_HUB
                self.hub_stats[transition.id] = ('major-hub-transition', total_degree)
            elif total_degree >= self.MINOR_HUB_THRESHOLD:
                masses[transition.id] = self.MASS_MINOR_HUB
                self.hub_stats[transition.id] = ('minor-hub-transition', total_degree)
            else:
                masses[transition.id] = self.MASS_TRANSITION  # Light mass for regular transitions
                self.hub_stats[transition.id] = ('transition', total_degree)
        
        return masses
    
    def _calculate_degrees(self, places: List[Place], 
                          transitions: List[Transition],
                          arcs: List[Arc]) -> tuple:
        """Calculate in-degree and out-degree for all nodes.
        
        Args:
            places: List of places
            transitions: List of transitions
            arcs: List of arcs
            
        Returns:
            Tuple of (in_degree dict, out_degree dict)
        """
        in_degree = {}
        out_degree = {}
        
        # Initialize all nodes
        for obj in places + transitions:
            in_degree[obj.id] = 0
            out_degree[obj.id] = 0
        
        # Count degrees from arcs
        for arc in arcs:
            source_id = arc.source.id
            target_id = arc.target.id
            
            if source_id in out_degree:
                out_degree[source_id] += 1
            if target_id in in_degree:
                in_degree[target_id] += 1
        
        return in_degree, out_degree
    
    def get_hub_statistics(self) -> Dict[str, List[tuple]]:
        """Get hub classification statistics.
        
        Returns:
            Dict with hub categories and their nodes
        """
        super_hubs = []
        major_hubs = []
        minor_hubs = []
        regular = []
        
        for node_id, (category, degree) in self.hub_stats.items():
            # Group both place hubs and transition hubs
            if 'super-hub' in category:
                super_hubs.append((node_id, degree))
            elif 'major-hub' in category:
                major_hubs.append((node_id, degree))
            elif 'minor-hub' in category:
                minor_hubs.append((node_id, degree))
            else:  # regular or transition
                regular.append((node_id, degree))
        
        return {
            'super_hubs': sorted(super_hubs, key=lambda x: x[1], reverse=True),
            'major_hubs': sorted(major_hubs, key=lambda x: x[1], reverse=True),
            'minor_hubs': sorted(minor_hubs, key=lambda x: x[1], reverse=True),
            'regular': sorted(regular, key=lambda x: x[1], reverse=True)
        }
