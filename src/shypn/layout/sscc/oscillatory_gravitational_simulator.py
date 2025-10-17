"""Oscillatory Gravitational Simulator - Spring-like equilibrium forces.

This module extends the gravitational simulator with oscillatory forces that
create natural equilibrium distances between connected nodes, similar to
spring behavior in force-directed layouts.

Key differences from standard gravity:
- Attractive at distances > equilibrium (gravity dominates)
- Repulsive at distances < equilibrium (spring dominates)
- Automatic stable spacing without separate repulsion mechanism
- Mass-dependent equilibrium distances

Physical Model:
    F = gravity_attraction(r)  when r > r_equilibrium
    F = spring_repulsion(r)    when r < r_equilibrium

Where:
    r_equilibrium = f(m1, m2, arc_weight)
"""

import math
from typing import Dict, List, Tuple
from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc.gravitational_simulator import GravitationalSimulator


class OscillatoryGravitationalSimulator(GravitationalSimulator):
    """Gravitational simulator with spring-like oscillatory forces.
    
    Unlike pure Newtonian gravity (always attractive), this simulator
    combines gravitational attraction with spring repulsion to create
    natural equilibrium distances between connected nodes.
    
    This prevents node clustering and creates stable orbital patterns
    without requiring separate hub-to-hub repulsion forces.
    """
    
    # Equilibrium parameters (configurable)
    EQUILIBRIUM_SCALE = 150.0    # Base equilibrium distance (pixels)
    SPRING_CONSTANT = 800.0      # Spring repulsion strength
    MASS_EXPONENT = 0.25         # How mass affects spacing (0-1)
    ARC_WEIGHT_EXPONENT = -0.3   # How arc weight affects spacing (negative = closer for higher weight)
    
    def __init__(self, 
                 equilibrium_scale: float = None,
                 spring_constant: float = None,
                 mass_exponent: float = None,
                 arc_weight_exponent: float = None,
                 **kwargs):
        """Initialize oscillatory gravitational simulator.
        
        Args:
            equilibrium_scale: Base equilibrium distance (default: 150.0)
            spring_constant: Spring repulsion strength (default: 800.0)
            mass_exponent: Mass influence on spacing (default: 0.25)
            arc_weight_exponent: Arc weight influence (default: -0.3)
            **kwargs: Additional arguments for parent GravitationalSimulator
        """
        super().__init__(**kwargs)
        self.equilibrium_scale = equilibrium_scale if equilibrium_scale is not None else self.EQUILIBRIUM_SCALE
        self.spring_constant = spring_constant if spring_constant is not None else self.SPRING_CONSTANT
        self.mass_exponent = mass_exponent if mass_exponent is not None else self.MASS_EXPONENT
        self.arc_weight_exponent = arc_weight_exponent if arc_weight_exponent is not None else self.ARC_WEIGHT_EXPONENT
    
    def _calculate_forces(self, arcs: List[Arc], masses: Dict[int, float],
                         use_arc_weight: bool) -> Dict[int, Tuple[float, float]]:
        """Calculate oscillatory gravitational forces for all objects.
        
        Uses OBJECT REFERENCES from arcs to avoid ID conflicts.
        
        Args:
            arcs: List of Arc objects (use arc.source and arc.target objects)
            masses: Dict mapping object ID to mass
            use_arc_weight: Whether to use arc.weight as multiplier
            
        Returns:
            Dict mapping object ID to (force_x, force_y)
        """
        forces = {obj_id: (0.0, 0.0) for obj_id in self._positions}
        
        # For each arc, calculate oscillatory gravitational force
        for arc in arcs:
            # Use OBJECT REFERENCES (not IDs) to avoid conflicts
            source_obj = arc.source  # Object reference
            target_obj = arc.target  # Object reference
            
            source_id = source_obj.id
            target_id = target_obj.id
            
            if source_id not in self._positions or target_id not in self._positions:
                continue
            
            # Get positions using IDs (only after validating objects exist)
            x1, y1 = self._positions[source_id]
            x2, y2 = self._positions[target_id]
            
            # Distance vector
            dx = x2 - x1
            dy = y2 - y1
            distance = math.sqrt(dx**2 + dy**2) + self.MIN_DISTANCE
            
            # Get masses using IDs
            m1 = masses.get(source_id, 1.0)
            m2 = masses.get(target_id, 1.0)
            weight = arc.weight if use_arc_weight else 1.0
            
            # Calculate equilibrium distance for this pair
            r_equilibrium = self._calculate_equilibrium_distance(m1, m2, weight)
            
            # Calculate oscillatory force magnitude
            force_magnitude = self._calculate_oscillatory_force(
                distance, r_equilibrium, m1, m2, weight
            )
            
            # Force components (normalized by distance)
            force_x = force_magnitude * (dx / distance)
            force_y = force_magnitude * (dy / distance)
            
            # Apply force to both objects (Newton's 3rd law)
            fx1, fy1 = forces[source_id]
            forces[source_id] = (fx1 + force_x, fy1 + force_y)
            
            fx2, fy2 = forces[target_id]
            forces[target_id] = (fx2 - force_x, fy2 - force_y)
        
        return forces
    
    def _calculate_equilibrium_distance(self, m1: float, m2: float, 
                                       arc_weight: float) -> float:
        """Calculate natural equilibrium distance for a pair of connected nodes.
        
        The equilibrium distance depends on:
        - Combined mass: Heavier nodes push farther apart
        - Arc weight: Higher weight pulls nodes closer together
        
        Args:
            m1: Mass of first object
            m2: Mass of second object
            arc_weight: Weight of connecting arc
            
        Returns:
            Equilibrium distance in pixels
            
        Formula:
            r_eq = scale * (m1 + m2)^α * weight^β
            
            Where:
            - α (mass_exponent) > 0: heavier → larger spacing
            - β (arc_weight_exponent) < 0: higher weight → closer spacing
        """
        # Combined mass factor (heavier masses → larger equilibrium distance)
        mass_factor = (m1 + m2) ** self.mass_exponent
        
        # Arc weight factor (higher weight → smaller distance, stronger connection)
        weight_factor = arc_weight ** self.arc_weight_exponent
        
        # Calculate equilibrium distance
        r_eq = self.equilibrium_scale * mass_factor * weight_factor
        
        # Ensure minimum distance to avoid singularities
        r_eq = max(r_eq, 50.0)  # Minimum 50 pixels
        
        return r_eq
    
    def _calculate_oscillatory_force(self, distance: float, r_equilibrium: float,
                                    m1: float, m2: float, arc_weight: float) -> float:
        """Calculate force with oscillatory behavior around equilibrium.
        
        Args:
            distance: Current distance between nodes
            r_equilibrium: Equilibrium distance
            m1: Mass of first object
            m2: Mass of second object
            arc_weight: Weight of connecting arc
            
        Returns:
            Force magnitude (positive = attraction, negative = repulsion)
            
        Behavior:
            - distance > r_eq: Gravitational attraction (pulls together)
            - distance < r_eq: Spring repulsion (pushes apart)
            - distance = r_eq: Zero net force (stable equilibrium)
        """
        
        if distance > r_equilibrium:
            # Beyond equilibrium: Gravitational attraction
            # F = (G * weight * m1 * m2) / r²
            force_magnitude = (self.g_constant * arc_weight * m1 * m2) / (distance ** 2)
            
        else:
            # Below equilibrium: Spring repulsion (Hooke's Law)
            # F = -k * (r_eq - r)
            # 
            # The closer to equilibrium, the weaker the repulsion
            # At equilibrium: force = 0
            displacement = r_equilibrium - distance
            force_magnitude = -self.spring_constant * displacement
        
        return force_magnitude
    
    def simulate(self, places: List[Place], transitions: List[Transition],
                arcs: List[Arc], masses: Dict[int, float],
                initial_positions: Dict[int, Tuple[float, float]] = None,
                iterations: int = 1000,
                use_arc_weight: bool = True) -> Dict[int, Tuple[float, float]]:
        """Run oscillatory gravitational simulation.
        
        This overrides the parent simulate() to disable hub repulsion
        since oscillatory forces already prevent clustering.
        
        Args:
            places: List of Place objects (using object references)
            transitions: List of Transition objects (using object references)
            arcs: List of Arc objects (arc.source, arc.target are object refs)
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
            # Calculate oscillatory forces (no separate hub repulsion needed)
            forces = self._calculate_forces(arcs, masses, use_arc_weight)
            
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
        
        return self._positions
    
    def get_equilibrium_info(self, arcs: List[Arc], 
                            masses: Dict[int, float]) -> Dict[str, any]:
        """Get information about equilibrium distances in the network.
        
        Useful for debugging and parameter tuning.
        
        Args:
            arcs: List of Arc objects
            masses: Dict mapping object ID to mass
            
        Returns:
            Dict with equilibrium statistics:
                - min_equilibrium: Smallest equilibrium distance
                - max_equilibrium: Largest equilibrium distance
                - avg_equilibrium: Average equilibrium distance
                - equilibrium_distances: List of all equilibrium distances
        """
        equilibrium_distances = []
        
        for arc in arcs:
            source_id = arc.source.id
            target_id = arc.target.id
            
            m1 = masses.get(source_id, 1.0)
            m2 = masses.get(target_id, 1.0)
            weight = arc.weight
            
            r_eq = self._calculate_equilibrium_distance(m1, m2, weight)
            equilibrium_distances.append(r_eq)
        
        if not equilibrium_distances:
            return {
                'min_equilibrium': 0.0,
                'max_equilibrium': 0.0,
                'avg_equilibrium': 0.0,
                'equilibrium_distances': []
            }
        
        return {
            'min_equilibrium': min(equilibrium_distances),
            'max_equilibrium': max(equilibrium_distances),
            'avg_equilibrium': sum(equilibrium_distances) / len(equilibrium_distances),
            'equilibrium_distances': equilibrium_distances
        }
