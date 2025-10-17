"""Gravitational Simulator - Physics engine for Solar System Layout.

This module implements a gravitational N-body simulation where:
- Forces are determined by arc connections (not all-pairs)
- Arc weights multiply the gravitational force
- Integration uses Velocity Verlet method for stability
"""

import math
import random
from typing import Dict, List, Tuple
from shypn.netobjs import Place, Transition, Arc


class GravitationalSimulator:
    """Physics engine for gravitational simulation of Petri net layout.
    
    Unlike force-directed algorithms (springs + coulombic repulsion),
    this uses Newtonian gravity with arc-weighted forces PLUS hub repulsion.
    
    Forces:
    1. Gravitational attraction (along arcs): F = (G * arc.weight * m1 * m2) / r²
    2. Hub-to-hub repulsion (high-mass nodes): F = (K * m1 * m2) / r²
    
    Hub repulsion prevents high-mass nodes from clustering together,
    creating a spread-out constellation of gravitational centers.
    """
    
    # Physics constants (configurable)
    GRAVITATIONAL_CONSTANT = 1000.0  # G
    DAMPING_FACTOR = 0.95            # Velocity damping (0.9-0.99)
    TIME_STEP = 0.01                 # Integration time step
    MIN_DISTANCE = 1.0               # Minimum distance to avoid singularities
    
    # Hub repulsion (NEW)
    HUB_REPULSION_CONSTANT = 50000.0  # Repulsion strength between high-mass nodes
    HUB_MASS_THRESHOLD = 500.0        # Nodes with mass ≥ this repel each other
    
    def __init__(self, g_constant: float = None, damping: float = None,
                 time_step: float = None, hub_repulsion: float = None,
                 hub_mass_threshold: float = None):
        """Initialize gravitational simulator.
        
        Args:
            g_constant: Gravitational constant (default: 1000.0)
            damping: Velocity damping factor (default: 0.95)
            time_step: Integration time step (default: 0.01)
            hub_repulsion: Repulsion constant between hubs (default: 50000.0)
            hub_mass_threshold: Mass threshold for hub repulsion (default: 500.0)
        """
        self.g_constant = g_constant if g_constant is not None else self.GRAVITATIONAL_CONSTANT
        self.damping = damping if damping is not None else self.DAMPING_FACTOR
        self.time_step = time_step if time_step is not None else self.TIME_STEP
        self.hub_repulsion = hub_repulsion if hub_repulsion is not None else self.HUB_REPULSION_CONSTANT
        self.hub_mass_threshold = hub_mass_threshold if hub_mass_threshold is not None else self.HUB_MASS_THRESHOLD
        
        # Simulation state
        self._positions: Dict[int, Tuple[float, float]] = {}
        self._velocities: Dict[int, Tuple[float, float]] = {}
    
    def simulate(self, places: List[Place], transitions: List[Transition],
                arcs: List[Arc], masses: Dict[int, float],
                initial_positions: Dict[int, Tuple[float, float]] = None,
                iterations: int = 1000,
                use_arc_weight: bool = True) -> Dict[int, Tuple[float, float]]:
        """Run gravitational simulation.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects (define gravitational forces)
            masses: Dict mapping object ID to mass
            initial_positions: Optional initial positions (random if None)
            iterations: Number of simulation iterations
            use_arc_weight: Whether to use arc.weight as force multiplier
            
        Returns:
            Dict mapping object ID to final (x, y) position
        """
        # Initialize positions
        if initial_positions:
            self._positions = initial_positions.copy()
        else:
            self._positions = self._initialize_random_positions(places, transitions)
        
        # Initialize velocities to zero
        self._velocities = {}
        for obj_id in self._positions:
            self._velocities[obj_id] = (0.0, 0.0)
        
        # Run simulation loop
        for iteration in range(iterations):
            self._simulation_step(arcs, masses, use_arc_weight)
        
        return self._positions
    
    def _initialize_random_positions(self, places: List[Place], 
                                     transitions: List[Transition],
                                     width: float = 2000.0,
                                     height: float = 2000.0) -> Dict[int, Tuple[float, float]]:
        """Initialize random positions for all objects.
        
        Args:
            places: List of places
            transitions: List of transitions
            width: Canvas width
            height: Canvas height
            
        Returns:
            Dict mapping object ID to (x, y) position
        """
        positions = {}
        
        for place in places:
            positions[place.id] = (
                random.uniform(-width/2, width/2),
                random.uniform(-height/2, height/2)
            )
        
        for transition in transitions:
            positions[transition.id] = (
                random.uniform(-width/2, width/2),
                random.uniform(-height/2, height/2)
            )
        
        return positions
    
    def _simulation_step(self, arcs: List[Arc], masses: Dict[int, float],
                        use_arc_weight: bool):
        """Execute one simulation step (Velocity Verlet integration).
        
        Args:
            arcs: List of arcs (gravitational connections)
            masses: Object masses
            use_arc_weight: Use arc weight as force multiplier
        """
        # Calculate forces for all objects
        forces = self._calculate_forces(arcs, masses, use_arc_weight)
        
        # Add hub-to-hub repulsion (NEW)
        hub_repulsion_forces = self._calculate_hub_repulsion(masses)
        for obj_id in forces:
            if obj_id in hub_repulsion_forces:
                fx, fy = forces[obj_id]
                rfx, rfy = hub_repulsion_forces[obj_id]
                forces[obj_id] = (fx + rfx, fy + rfy)
        
        # Update velocities and positions
        for obj_id in self._positions:
            if obj_id not in masses:
                continue
            
            mass = masses[obj_id]
            force_x, force_y = forces.get(obj_id, (0.0, 0.0))
            
            # F = ma → a = F/m
            ax = force_x / mass
            ay = force_y / mass
            
            # Get current velocity
            vx, vy = self._velocities[obj_id]
            
            # Update velocity with damping
            vx = vx * self.damping + ax * self.time_step
            vy = vy * self.damping + ay * self.time_step
            self._velocities[obj_id] = (vx, vy)
            
            # Update position
            x, y = self._positions[obj_id]
            x += vx * self.time_step
            y += vy * self.time_step
            self._positions[obj_id] = (x, y)
    
    def _calculate_forces(self, arcs: List[Arc], masses: Dict[int, float],
                         use_arc_weight: bool) -> Dict[int, Tuple[float, float]]:
        """Calculate gravitational forces for all objects.
        
        Args:
            arcs: List of arcs (define connections)
            masses: Object masses
            use_arc_weight: Use arc weight as multiplier
            
        Returns:
            Dict mapping object ID to (force_x, force_y)
        """
        forces = {obj_id: (0.0, 0.0) for obj_id in self._positions}
        
        # For each arc, calculate gravitational force
        for arc in arcs:
            source_id = arc.source.id
            target_id = arc.target.id
            
            if source_id not in self._positions or target_id not in self._positions:
                continue
            
            # Distance vector
            x1, y1 = self._positions[source_id]
            x2, y2 = self._positions[target_id]
            dx = x2 - x1
            dy = y2 - y1
            distance = math.sqrt(dx**2 + dy**2) + self.MIN_DISTANCE
            
            # Gravitational force magnitude
            # F = G * arc.weight * m1 * m2 / r²
            m1 = masses.get(source_id, 1.0)
            m2 = masses.get(target_id, 1.0)
            weight = arc.weight if use_arc_weight else 1.0
            
            force_magnitude = (self.g_constant * weight * m1 * m2) / (distance ** 2)
            
            # Force components (normalized by distance)
            force_x = force_magnitude * (dx / distance)
            force_y = force_magnitude * (dy / distance)
            
            # Apply force to both objects (Newton's 3rd law)
            fx1, fy1 = forces[source_id]
            forces[source_id] = (fx1 + force_x, fy1 + force_y)
            
            fx2, fy2 = forces[target_id]
            forces[target_id] = (fx2 - force_x, fy2 - force_y)
        
        return forces
    
    def get_current_positions(self) -> Dict[int, Tuple[float, float]]:
        """Get current positions during simulation.
        
        Returns:
            Dict mapping object ID to (x, y) position
        """
        return self._positions.copy()
    
    def _calculate_hub_repulsion(self, masses: Dict[int, float]) -> Dict[int, Tuple[float, float]]:
        """Calculate repulsion forces between hub nodes.
        
        Hub nodes (high mass) repel each other to prevent clustering.
        Uses Coulomb-like repulsion: F = K * m1 * m2 / r²
        
        Args:
            masses: Object masses
            
        Returns:
            Dict mapping object ID to (repulsion_x, repulsion_y)
        """
        repulsion_forces = {obj_id: (0.0, 0.0) for obj_id in self._positions}
        
        # Identify hub nodes (high mass)
        hub_ids = [obj_id for obj_id, mass in masses.items() 
                   if mass >= self.hub_mass_threshold]
        
        if len(hub_ids) < 2:
            return repulsion_forces  # No repulsion needed
        
        # Calculate pairwise repulsion between hubs
        for i, hub1_id in enumerate(hub_ids):
            for hub2_id in hub_ids[i+1:]:
                if hub1_id not in self._positions or hub2_id not in self._positions:
                    continue
                
                # Distance vector
                x1, y1 = self._positions[hub1_id]
                x2, y2 = self._positions[hub2_id]
                dx = x2 - x1
                dy = y2 - y1
                distance = math.sqrt(dx**2 + dy**2) + self.MIN_DISTANCE
                
                # Repulsion force magnitude
                # F = K * m1 * m2 / r² (Coulomb-like)
                m1 = masses.get(hub1_id, 1.0)
                m2 = masses.get(hub2_id, 1.0)
                
                repulsion_magnitude = (self.hub_repulsion * m1 * m2) / (distance ** 2)
                
                # Force components (normalized by distance)
                # Repulsion pushes nodes APART (opposite direction of gravity)
                repulsion_x = repulsion_magnitude * (dx / distance)
                repulsion_y = repulsion_magnitude * (dy / distance)
                
                # Apply repulsion to both hubs (Newton's 3rd law)
                # Hub1 is pushed AWAY from Hub2 (negative direction)
                fx1, fy1 = repulsion_forces[hub1_id]
                repulsion_forces[hub1_id] = (fx1 - repulsion_x, fy1 - repulsion_y)
                
                # Hub2 is pushed AWAY from Hub1 (positive direction)
                fx2, fy2 = repulsion_forces[hub2_id]
                repulsion_forces[hub2_id] = (fx2 + repulsion_x, fy2 + repulsion_y)
        
        return repulsion_forces
    
    def get_kinetic_energy(self, masses: Dict[int, float]) -> float:
        """Calculate total kinetic energy of system.
        
        Useful for checking if simulation has converged.
        
        Args:
            masses: Object masses
            
        Returns:
            Total kinetic energy
        """
        total_ke = 0.0
        
        for obj_id, (vx, vy) in self._velocities.items():
            mass = masses.get(obj_id, 1.0)
            speed_squared = vx**2 + vy**2
            total_ke += 0.5 * mass * speed_squared
        
        return total_ke
