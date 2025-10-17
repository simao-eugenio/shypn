"""Orbit Stabilizer - Refines layout to create clean orbital structure.

This module applies post-processing constraints to create the "solar system"
visual structure where SCCs are at the center and other objects orbit them.
"""

import math
from typing import Dict, List, Tuple
from shypn.netobjs import Place, Transition
from shypn.layout.sscc.strongly_connected_component import StronglyConnectedComponent


class OrbitStabilizer:
    """Applies orbital constraints to create solar system structure.
    
    After gravitational simulation, this refines positions to ensure:
    - SCCs are pinned at origin (center)
    - Places orbit SCCs in circular patterns
    - Transitions orbit their connected places
    - No collisions/overlaps
    """
    
    # Orbital parameters (configurable)
    SCC_INTERNAL_RADIUS = 50.0   # Radius for nodes within SCC
    PLANET_ORBIT_BASE = 300.0    # Base orbital radius for places
    SATELLITE_ORBIT = 50.0       # Orbital radius for transitions around places
    MIN_NODE_SPACING = 80.0      # Minimum distance between nodes
    
    def __init__(self, scc_radius: float = None, planet_orbit: float = None,
                 satellite_orbit: float = None):
        """Initialize orbit stabilizer.
        
        Args:
            scc_radius: Radius for SCC internal layout (default: 50.0)
            planet_orbit: Base orbital radius for places (default: 300.0)
            satellite_orbit: Orbital radius for transitions (default: 50.0)
        """
        self.scc_radius = scc_radius if scc_radius is not None else self.SCC_INTERNAL_RADIUS
        self.planet_orbit = planet_orbit if planet_orbit is not None else self.PLANET_ORBIT_BASE
        self.satellite_orbit = satellite_orbit if satellite_orbit is not None else self.SATELLITE_ORBIT
    
    def stabilize(self, positions: Dict[int, Tuple[float, float]],
                  sccs: List[StronglyConnectedComponent],
                  places: List[Place],
                  transitions: List[Transition]) -> Dict[int, Tuple[float, float]]:
        """Apply orbital stabilization to positions.
        
        Args:
            positions: Current positions from simulation
            sccs: List of strongly connected components
            places: List of places
            transitions: List of transitions
            
        Returns:
            Refined positions with orbital structure
        """
        refined_positions = positions.copy()
        
        # Step 1: Pin SCCs at origin and arrange internally
        if sccs:
            refined_positions = self._pin_sccs_at_origin(refined_positions, sccs)
        
        # Step 2: Arrange places in orbital rings around SCCs
        refined_positions = self._arrange_places_in_orbits(refined_positions, sccs, places)
        
        # Step 3: Position transitions near their connected places
        refined_positions = self._position_transitions_near_places(refined_positions, transitions, places)
        
        # Step 4: Resolve collisions
        refined_positions = self._resolve_collisions(refined_positions, places, transitions)
        
        return refined_positions
    
    def _pin_sccs_at_origin(self, positions: Dict[int, Tuple[float, float]],
                            sccs: List[StronglyConnectedComponent]) -> Dict[int, Tuple[float, float]]:
        """Pin largest SCC at origin, arrange nodes in circle.
        
        Args:
            positions: Current positions
            sccs: List of SCCs
            
        Returns:
            Updated positions
        """
        if not sccs:
            return positions
        
        # Sort SCCs by size (largest first)
        sorted_sccs = sorted(sccs, key=lambda s: s.size, reverse=True)
        
        # Pin largest SCC at origin
        largest_scc = sorted_sccs[0]
        
        # Arrange SCC nodes in a circle
        for i, node_id in enumerate(largest_scc.node_ids):
            angle = (2 * math.pi * i) / len(largest_scc.node_ids)
            x = self.scc_radius * math.cos(angle)
            y = self.scc_radius * math.sin(angle)
            positions[node_id] = (x, y)
        
        # TODO: Handle multiple SCCs (position at different angles)
        
        return positions
    
    def _arrange_places_in_orbits(self, positions: Dict[int, Tuple[float, float]],
                                   sccs: List[StronglyConnectedComponent],
                                   places: List[Place]) -> Dict[int, Tuple[float, float]]:
        """Arrange places in circular orbits around SCCs.
        
        Args:
            positions: Current positions
            sccs: List of SCCs
            places: List of places
            
        Returns:
            Updated positions
        """
        # Collect nodes in SCCs
        scc_nodes = set()
        for scc in sccs:
            for node_id in scc.node_ids:
                scc_nodes.add(node_id)
        
        # Get places not in SCCs
        free_places = [p for p in places if p.id not in scc_nodes]
        
        if not free_places:
            return positions
        
        # Arrange in circle around origin
        for i, place in enumerate(free_places):
            angle = (2 * math.pi * i) / len(free_places)
            x = self.planet_orbit * math.cos(angle)
            y = self.planet_orbit * math.sin(angle)
            positions[place.id] = (x, y)
        
        return positions
    
    def _position_transitions_near_places(self, positions: Dict[int, Tuple[float, float]],
                                          transitions: List[Transition],
                                          places: List[Place]) -> Dict[int, Tuple[float, float]]:
        """Position transitions near their connected places.
        
        Args:
            positions: Current positions
            transitions: List of transitions
            places: List of places
            
        Returns:
            Updated positions
        """
        # For now, position transitions in small orbit around their place
        # TODO: Use arc connections to determine which place to orbit
        
        for i, transition in enumerate(transitions):
            # Find nearest place
            nearest_place = None
            min_distance = float('inf')
            
            for place in places:
                if place.id in positions:
                    px, py = positions[place.id]
                    tx, ty = positions.get(transition.id, (0, 0))
                    distance = math.sqrt((px - tx)**2 + (py - ty)**2)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_place = place
            
            if nearest_place:
                px, py = positions[nearest_place.id]
                angle = (2 * math.pi * i) / max(len(transitions), 1)
                tx = px + self.satellite_orbit * math.cos(angle)
                ty = py + self.satellite_orbit * math.sin(angle)
                positions[transition.id] = (tx, ty)
        
        return positions
    
    def _resolve_collisions(self, positions: Dict[int, Tuple[float, float]],
                           places: List[Place],
                           transitions: List[Transition]) -> Dict[int, Tuple[float, float]]:
        """Resolve overlapping nodes by pushing them apart.
        
        Args:
            positions: Current positions
            places: List of places
            transitions: List of transitions
            
        Returns:
            Collision-free positions
        """
        # Simple collision resolution: if two nodes are too close, push apart
        all_objects = list(places) + list(transitions)
        
        for i, obj1 in enumerate(all_objects):
            for obj2 in all_objects[i+1:]:
                if obj1.id not in positions or obj2.id not in positions:
                    continue
                
                x1, y1 = positions[obj1.id]
                x2, y2 = positions[obj2.id]
                
                dx = x2 - x1
                dy = y2 - y1
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < self.MIN_NODE_SPACING:
                    # Push nodes apart
                    push_distance = (self.MIN_NODE_SPACING - distance) / 2
                    if distance > 0:
                        push_x = push_distance * (dx / distance)
                        push_y = push_distance * (dy / distance)
                    else:
                        push_x = self.MIN_NODE_SPACING / 2
                        push_y = 0
                    
                    positions[obj1.id] = (x1 - push_x, y1 - push_y)
                    positions[obj2.id] = (x2 + push_x, y2 + push_y)
        
        return positions
