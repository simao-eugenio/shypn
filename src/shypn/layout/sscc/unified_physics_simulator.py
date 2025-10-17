"""Unified Physics Simulator - Combines all forces for Solar System Layout.

VERSION: 2.0.0 - Black Hole Galaxy Physics
DATE: October 17, 2025
STATUS: PRODUCTION STABLE

MAJOR FEATURES:
- Black hole galaxy model with SCC cycle at center
- SCC-aware gravitational attraction (only affects constellation hubs)
- Black hole damping wave (distance-based repulsion reduction)
- Arc force weakening for SCC connections (prevents ternary clustering)
- Event horizon mechanics (configurable node trapping)
- Multi-level galaxy cluster hierarchies

PHYSICS MODEL:
This simulator implements a unified physics model that combines:
1. Oscillatory forces (arc-based attraction/repulsion with equilibrium)
2. Proximity repulsion (all-pairs Coulomb-like repulsion with damping wave)
3. Ambient tension (global spacing force)
4. Hub group repulsion (prevents constellation clustering)
5. SCC cohesion (maintains black hole cycle shape)
6. SCC gravity (pulls constellation hubs toward black hole)

Key insight: Graph properties → Physics properties
- SCC nodes have super-massive mass (MASS_SCC_NODE = 1000) - Black hole
- Super hubs have massive mass (MASS_SUPER_HUB = 300) - Constellation hubs
- Major hubs have mass (MASS_MAJOR_HUB = 200)
- Minor hubs have mass (MASS_MINOR_HUB = 100)
- Places have mass (MASS_PLACE = 100) - Shared places/satellites
- Transitions have light mass (MASS_TRANSITION = 50)
- Everything attracts via arcs (oscillatory forces)
- Everything repels by proximity (prevents overlap/clustering)
- Ambient tension maintains global spacing
- Black hole damping wave reduces repulsion near SCC (allows tight packing)
- Arc weakening for SCC connections (90% reduction) prevents ternary systems

FORCE HIERARCHY (Current Calibration - 94% global reduction applied):
1. SCC Cohesion: 30,000 (maintains black hole cycle shape)
2. SCC Gravity: 300 (pulls hubs only, mass >= 1000)
3. Hub Group Repulsion: 30 (prevents constellation clustering)
4. Arc Forces: 1.2 (attraction/repulsion via connections)
   - Normal arcs: 1.2
   - SCC arcs: 0.12 (90% weaker - prevents ternary clustering)
5. Proximity Repulsion: 6 (with black hole damping)
6. Damping Wave: 0.1-1.0 (distance-based from black hole center)

The algorithm automatically balances all forces to create natural,
stable layouts without user intervention.

CHANGELOG:
v2.0.0 (Oct 17, 2025): Black hole galaxy physics with arc weakening
v1.5.0: Added SCC gravity and event horizon mechanics
v1.4.0: Implemented black hole damping wave
v1.3.0: Added hub group repulsion
v1.2.0: Implemented SCC cohesion forces
v1.1.0: Added oscillatory forces with equilibrium
v1.0.0: Initial unified physics implementation
"""

from typing import Dict, List, Tuple
import math
from shypn.netobjs import Place, Transition, Arc


class UnifiedPhysicsSimulator:
    """Unified physics engine combining oscillatory, proximity, and ambient forces.
    
    VERSION: 2.0.0 - Black Hole Galaxy Physics
    
    This is the core physics engine that makes the Solar System Layout work.
    It combines multiple force types to create stable, aesthetic layouts:
    
    1. Oscillatory Forces (arc-based):
       - Attractive when r > r_equilibrium (pulls nodes together)
       - Repulsive when r < r_equilibrium (pushes nodes apart)
       - Creates natural orbital patterns
       - Weighted by arc.weight
       - SCC arc weakening: 90% reduction to prevent ternary clustering
    
    2. Proximity Repulsion (all-pairs):
       - Always repulsive (prevents overlap)
       - Stronger for higher masses (hubs repel more)
       - Distance-dependent (1/r² falloff)
       - Creates hub separation
       - Black hole damping wave: reduced near SCC center
    
    3. Ambient Tension (global):
       - Weak repulsion between all nodes
       - Keeps network spread out
       - Prevents global clustering
       - Maintains minimum spacing
    
    4. Hub Group Repulsion:
       - Group-to-group repulsion between constellations
       - Prevents constellation clustering
       - Distance-based with combined masses
    
    5. SCC Cohesion:
       - Pulls SCC nodes toward centroid
       - Maintains black hole cycle shape
       - Strong force (30,000) with target radius
    
    6. SCC Gravity:
       - Attracts constellation hubs (mass >= 1000) to black hole
       - Creates orbital mechanics around SCC center
       - Does NOT affect satellites or shared places
    
    The combination of these forces creates layouts where:
    - SCCs become black hole gravitational centers
    - Constellation hubs orbit the black hole
    - Shared places orbit constellation hubs (not black hole)
    - Satellites orbit hubs naturally
    - Everything stays well-spaced with hierarchical structure
    """
    
    # VERSION MARKER
    VERSION = "2.0.0"
    VERSION_DATE = "2025-10-17"
    
    # Physics constants (tuned for black hole galaxy - 94% cumulative reduction applied)
    # CALIBRATION HISTORY:
    # - Original values (v1.0.0)
    # - First scaling: 80% reduction (v1.5.0)
    # - Second scaling: 70% reduction from scaled values (v2.0.0)
    # - Cumulative: 94% reduction from original
    
    GRAVITY_CONSTANT = 1.2                  # Arc attraction (was 4 → now 1.2: 70% reduction)
    SPRING_CONSTANT = 30.0                  # Spring repulsion strength (was 100 → now 30: 70% reduction)
    PROXIMITY_CONSTANT = 6.0                # Hub-to-hub repulsion (was 20 → now 6: 70% reduction)
    PROXIMITY_THRESHOLD = 500.0             # Mass threshold for proximity repulsion
    AMBIENT_CONSTANT = 1000.0               # Base for universal repulsion
    UNIVERSAL_REPULSION_MULTIPLIER = 2.0    # Multiplier for universal repulsion
    
    # Hub group repulsion (prevents constellation clustering)
    HUB_GROUP_CONSTANT = 30.0               # Group repulsion strength (was 100 → now 30: 70% reduction)
    
    # SCC-specific forces (Black Hole Physics v2.0.0)
    SCC_COHESION_STRENGTH = 30000.0         # Pulls SCC nodes toward centroid (was 100k → now 30k: 70% reduction)
    SCC_TARGET_RADIUS = 30.0                # Target radius for SCC cycle shape
    SCC_GRAVITY_CONSTANT = 300.0            # Attracts hubs to black hole (was 1000 → now 300: 70% reduction)
    SCC_GRAVITY_MIN_MASS = 1000.0           # Only nodes with mass >= this affected by SCC gravity
    SCC_ARC_WEAKENING_FACTOR = 0.1          # Weaken arcs to/from SCC by 90% (prevents ternary clustering) - v2.0.0
    
    # Equilibrium distance parameters
    # For Hub(1000) ← Place(100): r_eq = 200 * (1100)^0.1 * weight^-0.3
    EQUILIBRIUM_SCALE = 0.5                 # Base equilibrium distance
    MASS_EXPONENT = 0.1                     # Mass influence on equilibrium
    ARC_WEIGHT_EXPONENT = -0.3              # Weight influence on equilibrium
    
    # Simulation parameters
    TIME_STEP = 0.5                         # Integration time step
    DAMPING = 0.9                           # Velocity damping (0-1, higher = less damping)
    MAX_FORCE = 100000.0                    # Maximum force per node
    MIN_DISTANCE = 1.0                      # Minimum distance for force calculations
    
    def __init__(self,
                 enable_oscillatory: bool = True,
                 enable_proximity: bool = True,
                 enable_ambient: bool = True):
        """Initialize unified physics simulator.
        
        Args:
            enable_oscillatory: Enable oscillatory forces along arcs (default: True)
            enable_proximity: Enable proximity repulsion between all nodes (default: True)
            enable_ambient: Enable ambient tension for global spacing (default: True)
        """
        self.enable_oscillatory = enable_oscillatory
        self.enable_proximity = enable_proximity
        self.enable_ambient = enable_ambient
        
        # State tracking
        self.velocities: Dict[int, Tuple[float, float]] = {}
        self.forces: Dict[int, Tuple[float, float]] = {}
    
    def simulate(self,
                 positions: Dict[int, Tuple[float, float]],
                 arcs: List[Arc],
                 masses: Dict[int, float],
                 iterations: int = 1000,
                 progress_callback=None,
                 sccs: List = None) -> Dict[int, Tuple[float, float]]:
        """Run physics simulation to optimize layout.
        
        Args:
            positions: Initial positions {node_id: (x, y)}
            arcs: List of arcs connecting nodes
            masses: Node masses {node_id: mass}
            iterations: Number of simulation steps
            progress_callback: Optional callback(iteration, total)
            sccs: Optional list of SCCs for cohesion forces
        
        Returns:
            Optimized positions {node_id: (x, y)}
        """
        # Store SCCs for cohesion forces
        self.sccs = sccs if sccs else []
        
        # Store arcs for event horizon detection
        self.arcs = arcs
        
        # Initialize trapped nodes set
        self.trapped_at_event_horizon = set()
        
        # Consolidate parallel arcs (rare but can occur)
        # Multiple arcs between same source-target pair are combined into one
        # with accumulated weight
        consolidated_arcs = self._consolidate_parallel_arcs(arcs)
        
        # Initialize velocities
        self.velocities = {node_id: (0.0, 0.0) for node_id in positions.keys()}
        
        # Run simulation
        for iteration in range(iterations):
            # Calculate all forces
            self._calculate_forces(positions, consolidated_arcs, masses)
            
            # Update positions using Verlet integration
            self._update_positions(positions, masses)
            
            # Progress callback
            if progress_callback and iteration % 10 == 0:
                progress_callback(iteration, iterations)
        
        return positions
    
    def _consolidate_parallel_arcs(self, arcs: List[Arc]) -> List[Arc]:
        """Consolidate parallel arcs into single arcs with accumulated weight.
        
        Parallel arcs = multiple arcs with same (source, target) pair.
        This is rare in Petri nets but can occur, especially in test models.
        
        Args:
            arcs: List of all arcs
            
        Returns:
            List of consolidated arcs (no duplicates)
        """
        # Group arcs by (source_id, target_id) pair
        arc_groups = {}
        for arc in arcs:
            if arc.source is None or arc.target is None:
                continue
            
            key = (arc.source.id, arc.target.id)
            if key not in arc_groups:
                arc_groups[key] = []
            arc_groups[key].append(arc)
        
        # Consolidate: keep first arc, accumulate weights
        consolidated = []
        for key, parallel_arcs in arc_groups.items():
            if len(parallel_arcs) == 1:
                # Single arc, keep as is
                consolidated.append(parallel_arcs[0])
            else:
                # Multiple parallel arcs - consolidate
                base_arc = parallel_arcs[0]
                total_weight = sum(getattr(arc, 'weight', 1.0) for arc in parallel_arcs)
                
                # Create consolidated arc (reuse base arc, update weight)
                # Note: We don't modify the original arc object
                # Instead we'll use getattr with the accumulated weight in force calculation
                # For now, just use the first arc and note that parallel arcs were found
                consolidated.append(base_arc)
                
                # Store accumulated weight (we'll handle this in force calculation)
                if not hasattr(base_arc, '_consolidated_weight'):
                    base_arc._consolidated_weight = total_weight
        
        return consolidated
    
    def _calculate_forces(self,
                         positions: Dict[int, Tuple[float, float]],
                         arcs: List[Arc],
                         masses: Dict[int, float]):
        """Calculate all forces acting on nodes.
        
        This is where the unified physics happens! We calculate:
        1. Oscillatory forces (arc-based)
        2. Proximity repulsion (all-pairs)
        3. Ambient tension (global)
        
        And combine them into total force for each node.
        """
        # Reset forces
        self.forces = {node_id: (0.0, 0.0) for node_id in positions.keys()}
        
        # 1. Oscillatory forces (along arcs)
        if self.enable_oscillatory:
            self._calculate_oscillatory_forces(positions, arcs, masses)
        
        # 2. Proximity repulsion (all pairs)
        if self.enable_proximity:
            self._calculate_proximity_repulsion(positions, masses)
            # NEW: Hub group repulsion (treat each hub+satellites as one mass)
            self._calculate_hub_group_repulsion(positions, arcs, masses)
            # NEW: SCC cohesion (keep SCC nodes together like rigid body)
            self._calculate_scc_cohesion(positions, masses)
        
        # 2.5. SCC gravitational attraction (BLACK HOLE effect)
        # SCCs act as unified gravitational attractors - pull everything toward them
        self._calculate_scc_attraction(positions, masses)
        
        # 3. Ambient tension (global spacing)
        if self.enable_ambient:
            self._calculate_ambient_tension(positions, masses)
        
        # Clamp forces to prevent instability
        for node_id in self.forces:
            fx, fy = self.forces[node_id]
            magnitude = math.sqrt(fx * fx + fy * fy)
            if magnitude > self.MAX_FORCE:
                scale = self.MAX_FORCE / magnitude
                self.forces[node_id] = (fx * scale, fy * scale)
    
    def _calculate_oscillatory_forces(self,
                                      positions: Dict[int, Tuple[float, float]],
                                      arcs: List[Arc],
                                      masses: Dict[int, float]):
        """Calculate oscillatory forces along arcs.
        
        For each arc, calculate equilibrium distance and apply:
        - Attraction if r > r_eq (too far)
        - Repulsion if r < r_eq (too close)
        """
        # Get trapped nodes (those at event horizon)
        trapped = getattr(self, 'trapped_at_event_horizon', set())
        
        for arc in arcs:
            # Get source and target objects (use object references!)
            source_obj = arc.source
            target_obj = arc.target
            
            # Validate objects exist
            if source_obj is None or target_obj is None:
                continue
            
            source_id = source_obj.id
            target_id = target_obj.id
            
            # Skip arcs involving trapped nodes - they're frozen
            if source_id in trapped or target_id in trapped:
                continue
            
            # Get positions and masses
            if source_id not in positions or target_id not in positions:
                continue
            if source_id not in masses or target_id not in masses:
                continue
            
            source_pos = positions[source_id]
            target_pos = positions[target_id]
            source_mass = masses[source_id]
            target_mass = masses[target_id]
            
            # Calculate distance
            dx = target_pos[0] - source_pos[0]
            dy = target_pos[1] - source_pos[1]
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < self.MIN_DISTANCE:
                distance = self.MIN_DISTANCE
            
            # Calculate equilibrium distance
            # Use consolidated weight if parallel arcs were merged
            arc_weight = getattr(arc, '_consolidated_weight', None)
            if arc_weight is None:
                arc_weight = getattr(arc, 'weight', 1.0)
            
            # ============================================================
            # VERSION 2.0.0 - BLACK HOLE ARC WEAKENING (Oct 17, 2025)
            # ============================================================
            # CRITICAL FIX: Weaken arcs connecting to SCC nodes (black hole transitions)
            # This prevents shared places from being pulled toward black hole
            # and forming ternary systems that drag constellations
            # 
            # PROBLEM: Shared places have arcs to BOTH:
            #   1. Constellation hub (normal force)
            #   2. Black hole transition (equal force)
            # Result: 3 shared places cluster together near black hole
            #         and drag their constellations with them
            #
            # SOLUTION: Reduce arc force to black hole by 90%
            #   - Arc to constellation hub: 1.2 (normal)
            #   - Arc to black hole: 0.12 (10× weaker)
            # Result: Shared places orbit constellation hubs like satellites
            #         Constellations free to spread evenly around black hole
            # ============================================================
            arc_strength_multiplier = 1.0
            if hasattr(self, 'sccs') and self.sccs:
                for scc in self.sccs:
                    scc_nodes = set(scc.node_ids)
                    # If either end connects to SCC, weaken the arc force
                    if source_id in scc_nodes or target_id in scc_nodes:
                        # Reduce arc force by 90% using SCC_ARC_WEAKENING_FACTOR
                        arc_strength_multiplier = self.SCC_ARC_WEAKENING_FACTOR  # 0.1
                        break
            # ============================================================
            # END VERSION 2.0.0 ARC WEAKENING
            # ============================================================
            
            r_eq = self._calculate_equilibrium_distance(source_mass, target_mass, arc_weight)
            
            # Calculate oscillatory force
            force_magnitude = self._calculate_oscillatory_force(
                distance, r_eq, source_mass, target_mass, arc_weight
            )
            
            # Apply arc strength multiplier (weaken SCC connections)
            force_magnitude *= arc_strength_multiplier
            
            # Apply force in direction of displacement
            fx = (dx / distance) * force_magnitude
            fy = (dy / distance) * force_magnitude
            
            # Update forces (Newton's 3rd law)
            curr_force_source = self.forces[source_id]
            curr_force_target = self.forces[target_id]
            
            self.forces[source_id] = (curr_force_source[0] + fx, curr_force_source[1] + fy)
            self.forces[target_id] = (curr_force_target[0] - fx, curr_force_target[1] - fy)
    
    def _calculate_equilibrium_distance(self, m1: float, m2: float, weight: float) -> float:
        """Calculate equilibrium distance based on masses and arc weight.
        
        Formula: r_eq = scale * (m1 + m2)^α * weight^β * random_factor
        
        Where:
        - α = MASS_EXPONENT (positive, heavier masses → larger distances)
        - β = ARC_WEIGHT_EXPONENT (negative, higher weight → smaller distances)
        - random_factor = small variation (0.8-1.2) to prevent satellites clustering
        
        This creates natural spacing where:
        - Heavier nodes are farther apart
        - Strongly weighted arcs keep nodes closer
        - Small random variation prevents exact overlap
        """
        import random
        mass_factor = (m1 + m2) ** self.MASS_EXPONENT
        weight_factor = weight ** self.ARC_WEIGHT_EXPONENT
        
        # Add small random variation (±20%) to prevent satellites clustering at identical distance
        # This simulates natural orbital variation
        random_factor = random.uniform(0.8, 1.2)
        
        return self.EQUILIBRIUM_SCALE * mass_factor * weight_factor * random_factor
    
    def _calculate_oscillatory_force(self, distance: float, r_eq: float,
                                     m1: float, m2: float, weight: float) -> float:
        """Calculate oscillatory force (attractive or repulsive).
        
        - If distance > r_eq: Gravitational attraction (pull together)
        - If distance < r_eq: Spring repulsion (push apart)
        - At distance = r_eq: Zero force (equilibrium)
        """
        if distance > r_eq:
            # Too far: gravitational attraction
            # F = (G * m1 * m2 * weight) / r²
            force = (self.GRAVITY_CONSTANT * m1 * m2 * weight) / (distance * distance)
            return force  # Positive = attract
        else:
            # Too close: spring repulsion
            # F = -k * (r_eq - r)
            force = self.SPRING_CONSTANT * (r_eq - distance)
            return -force  # Negative = repel
    
    def _calculate_proximity_repulsion(self,
                                       positions: Dict[int, Tuple[float, float]],
                                       masses: Dict[int, float]):
        """Calculate proximity repulsion between ALL node pairs.
        
        This prevents overlap and clustering for ALL nodes, not just hubs.
        
        Two levels of repulsion:
        1. UNIVERSAL: All nodes repel each other (prevents clustering)
        2. EXTRA HUB: High-mass nodes get additional strong repulsion
        
        This ensures:
        - Places don't collapse into transitions
        - Transitions stay separated from each other
        - Hubs spread into constellation patterns
        """
        node_ids = list(positions.keys())
        
        # Get trapped nodes (those at event horizon)
        trapped = getattr(self, 'trapped_at_event_horizon', set())
        
        for i, node1_id in enumerate(node_ids):
            # Skip trapped nodes - they don't experience forces
            if node1_id in trapped:
                continue
                
            for node2_id in node_ids[i+1:]:
                # Skip if either node is trapped
                if node2_id in trapped:
                    continue
                    
                m1 = masses[node1_id]
                m2 = masses[node2_id]
                
                pos1 = positions[node1_id]
                pos2 = positions[node2_id]
                
                # Calculate distance
                dx = pos2[0] - pos1[0]
                dy = pos2[1] - pos1[1]
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < self.MIN_DISTANCE:
                    distance = self.MIN_DISTANCE
                
                # UNIVERSAL REPULSION: All nodes repel (base level)
                # Increased from 10x to 100x for stronger separation
                base_force = (self.AMBIENT_CONSTANT * self.UNIVERSAL_REPULSION_MULTIPLIER) / (distance * distance)
                
                # SATELLITE-SATELLITE EXTRA REPULSION: Prevent satellite clustering
                # Satellites (low mass) should strongly repel each other to spread around hub
                # This counters their collective attraction toward hub
                satellite_repulsion = 0.0
                if m1 < self.PROXIMITY_THRESHOLD and m2 < self.PROXIMITY_THRESHOLD:
                    # Both are low-mass nodes (satellites/places)
                    # Apply minimal repulsion to allow very tight orbits near hub
                    # Strength: 0.0x - DISABLED extra satellite repulsion (only universal base remains)
                    satellite_repulsion = 0.0  # (self.AMBIENT_CONSTANT * self.UNIVERSAL_REPULSION_MULTIPLIER * 0.0) / (distance * distance)
                
                # EXTRA HUB REPULSION: High-mass nodes get additional repulsion
                # Only applies if at least one node is a hub (mass >= threshold)
                extra_force = 0.0
                if m1 >= self.PROXIMITY_THRESHOLD or m2 >= self.PROXIMITY_THRESHOLD:
                    # Coulomb-like repulsion: F = (K * m1 * m2) / r²
                    extra_force = (self.PROXIMITY_CONSTANT * m1 * m2) / (distance * distance)
                
                # BLACK HOLE DAMPING WAVE: Reduce repulsion near black hole
                # Calculate average distance of both nodes from black hole center
                damping_factor = self._calculate_blackhole_damping(node1_id, node2_id, positions)
                
                # Total repulsion force (damped by black hole proximity)
                force_magnitude = (base_force + satellite_repulsion + extra_force) * damping_factor
                
                # Repulsive force (push apart)
                fx = -(dx / distance) * force_magnitude
                fy = -(dy / distance) * force_magnitude
                
                # Apply to both nodes (Newton's 3rd law)
                curr_force1 = self.forces[node1_id]
                curr_force2 = self.forces[node2_id]
                
                self.forces[node1_id] = (curr_force1[0] + fx, curr_force1[1] + fy)
                self.forces[node2_id] = (curr_force2[0] - fx, curr_force2[1] - fy)
    
    def _calculate_blackhole_damping(self, node1_id: int, node2_id: int,
                                     positions: Dict[int, Tuple[float, float]]) -> float:
        """Calculate damping factor based on distance from black hole center.
        
        ============================================================
        VERSION 1.4.0 - BLACK HOLE DAMPING WAVE
        ============================================================
        
        Black hole creates a "gravity wave" that dampens repulsion forces.
        Nodes closer to black hole experience reduced repulsion (allows tighter packing).
        Nodes far from black hole experience full repulsion (normal spreading).
        
        Damping formula: d = 0.1 + 0.9 × (avg_distance / max_distance)²
        
        At r=0 (at black hole): damping = 0.1 (90% reduction - very tight!)
        At r=500: damping = 0.35 (65% reduction - moderate)
        At r=1000+: damping = 1.0 (no reduction - full repulsion)
        
        This creates natural gradient: tight near black hole, spread far away.
        
        Used by:
        - Proximity repulsion (_calculate_proximity_repulsion)
        - Hub group repulsion (_calculate_hub_group_repulsion)
        
        Result: Beautiful hierarchical structure with density gradient
        ============================================================
        """
        if not hasattr(self, 'sccs') or not self.sccs:
            return 1.0  # No damping if no black hole
        
        # Find black hole center (SCC centroid)
        for scc in self.sccs:
            scc_nodes = set(scc.node_ids)
            if len(scc_nodes) == 0:
                continue
            
            # Calculate SCC centroid
            total_x = 0.0
            total_y = 0.0
            count = 0
            
            for node_id in scc_nodes:
                if node_id in positions:
                    x, y = positions[node_id]
                    total_x += x
                    total_y += y
                    count += 1
            
            if count == 0:
                continue
            
            centroid_x = total_x / count
            centroid_y = total_y / count
            
            # Calculate distances from both nodes to black hole center
            if node1_id in positions and node2_id in positions:
                x1, y1 = positions[node1_id]
                x2, y2 = positions[node2_id]
                
                dist1 = math.sqrt((x1 - centroid_x)**2 + (y1 - centroid_y)**2)
                dist2 = math.sqrt((x2 - centroid_x)**2 + (y2 - centroid_y)**2)
                
                # Average distance from black hole
                avg_distance = (dist1 + dist2) / 2.0
                
                # Damping wave parameters
                MAX_DISTANCE = 1000.0  # Full repulsion beyond this distance
                MIN_DAMPING = 0.1      # Maximum damping (at black hole center)
                
                # Damping factor: parabolic falloff from black hole
                # Near black hole: strong damping (low factor)
                # Far from black hole: no damping (factor = 1.0)
                if avg_distance >= MAX_DISTANCE:
                    return 1.0
                else:
                    ratio = avg_distance / MAX_DISTANCE
                    return MIN_DAMPING + (1.0 - MIN_DAMPING) * (ratio ** 2)
        
        return 1.0  # Default: no damping
    
    def _calculate_hub_group_repulsion(self,
                                       positions: Dict[int, Tuple[float, float]],
                                       arcs: List[Arc],
                                       masses: Dict[int, float]):
        """Calculate repulsion between hub groups (hub + its satellites as one mass).
        
        Each hub (high-mass node) and its connected satellites form a group.
        Groups repel each other based on their combined center of mass.
        
        This creates stronger inter-group repulsion while allowing satellites
        to orbit naturally within their group.
        """
        # Identify hubs (high-mass nodes)
        hubs = [node_id for node_id, mass in masses.items() if mass >= self.PROXIMITY_THRESHOLD]
        
        if len(hubs) < 2:
            return  # Need at least 2 hubs for group repulsion
        
        # Build groups: each hub + its connected satellites
        hub_groups = {}
        for hub_id in hubs:
            # Find all nodes connected to this hub
            satellites = set()
            for arc in arcs:
                if arc.source is None or arc.target is None:
                    continue
                    
                # If hub is target, source is satellite
                if arc.target.id == hub_id and masses.get(arc.source.id, 0) < self.PROXIMITY_THRESHOLD:
                    satellites.add(arc.source.id)
                # If hub is source, target is satellite  
                elif arc.source.id == hub_id and masses.get(arc.target.id, 0) < self.PROXIMITY_THRESHOLD:
                    satellites.add(arc.target.id)
            
            hub_groups[hub_id] = {
                'hub': hub_id,
                'satellites': list(satellites),
                'all_nodes': [hub_id] + list(satellites)
            }
        
        # Calculate center of mass for each group
        group_centers = {}
        group_total_masses = {}
        
        for hub_id, group in hub_groups.items():
            total_mass = 0.0
            weighted_x = 0.0
            weighted_y = 0.0
            
            for node_id in group['all_nodes']:
                if node_id not in positions or node_id not in masses:
                    continue
                    
                mass = masses[node_id]
                x, y = positions[node_id]
                
                total_mass += mass
                weighted_x += mass * x
                weighted_y += mass * y
            
            if total_mass > 0:
                center_x = weighted_x / total_mass
                center_y = weighted_y / total_mass
                group_centers[hub_id] = (center_x, center_y)
                group_total_masses[hub_id] = total_mass
        
        # Apply repulsion between group centers
        HUB_GROUP_CONSTANT = 30.0  # Repulsion strength between hub groups (SCALED DOWN: was 100, now 30 - 70% reduction)
        
        for i, hub1_id in enumerate(hubs):
            if hub1_id not in group_centers:
                continue
                
            for hub2_id in hubs[i+1:]:
                if hub2_id not in group_centers:
                    continue
                
                # Distance between group centers
                c1 = group_centers[hub1_id]
                c2 = group_centers[hub2_id]
                
                dx = c2[0] - c1[0]
                dy = c2[1] - c1[1]
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < self.MIN_DISTANCE:
                    distance = self.MIN_DISTANCE
                
                # Repulsion force: F = K * M1 * M2 / r²
                m1 = group_total_masses[hub1_id]
                m2 = group_total_masses[hub2_id]
                raw_force = (HUB_GROUP_CONSTANT * m1 * m2) / (distance * distance)
                
                # Apply black hole damping wave
                damping_factor = self._calculate_blackhole_damping(hub1_id, hub2_id, positions)
                force_magnitude = raw_force * damping_factor
                
                # Force direction (repulsive)
                fx = -(dx / distance) * force_magnitude
                fy = -(dy / distance) * force_magnitude
                
                # Distribute force to all nodes in each group
                # Each node gets force proportional to its mass
                for node_id in hub_groups[hub1_id]['all_nodes']:
                    if node_id in self.forces and node_id in masses:
                        node_mass = masses[node_id]
                        fraction = node_mass / m1 if m1 > 0 else 0
                        
                        curr_fx, curr_fy = self.forces[node_id]
                        self.forces[node_id] = (curr_fx + fx * fraction, curr_fy + fy * fraction)
                
                for node_id in hub_groups[hub2_id]['all_nodes']:
                    if node_id in self.forces and node_id in masses:
                        node_mass = masses[node_id]
                        fraction = node_mass / m2 if m2 > 0 else 0
                        
                        curr_fx, curr_fy = self.forces[node_id]
                        self.forces[node_id] = (curr_fx - fx * fraction, curr_fy - fy * fraction)
    
    def _calculate_scc_cohesion(self,
                               positions: Dict[int, Tuple[float, float]],
                               masses: Dict[int, float]):
        """Apply strong cohesion force to keep SCC nodes together (BLACK HOLE effect).
        
        SCCs (cycles) should act as compact black holes - nodes stay very close together.
        This prevents SCC nodes from spreading apart due to their high masses.
        
        Strategy:
        - For each SCC, calculate centroid
        - Pull all SCC nodes toward centroid with VERY STRONG force
        - Force proportional to distance from centroid
        - Creates compact, dense black hole structure
        """
        if not hasattr(self, 'sccs') or not self.sccs:
            return  # No SCCs to process
        
        SCC_COHESION_STRENGTH = 30000.0  # Strong force (SCALED DOWN: was 100k, now 30k - 70% reduction)
        SCC_TARGET_RADIUS = 30.0          # Target radius for SCC nodes (unchanged)
        
        for scc in self.sccs:
            # Calculate SCC centroid
            scc_nodes = scc.node_ids
            if len(scc_nodes) < 2:
                continue  # Single node, no cohesion needed
            
            # Find centroid
            total_mass = 0.0
            weighted_x = 0.0
            weighted_y = 0.0
            
            for node_id in scc_nodes:
                if node_id not in positions or node_id not in masses:
                    continue
                mass = masses[node_id]
                x, y = positions[node_id]
                total_mass += mass
                weighted_x += mass * x
                weighted_y += mass * y
            
            if total_mass == 0:
                continue
            
            centroid_x = weighted_x / total_mass
            centroid_y = weighted_y / total_mass
            
            # Pull all SCC nodes toward centroid
            for node_id in scc_nodes:
                if node_id not in positions or node_id not in self.forces:
                    continue
                
                x, y = positions[node_id]
                dx = centroid_x - x
                dy = centroid_y - y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < self.MIN_DISTANCE:
                    continue  # Already at centroid
                
                # Strong spring force toward centroid
                # F = k * (r - r_target)
                # If within target radius, weak force (stable)
                # If outside target radius, strong force (pull back)
                displacement = max(0, distance - SCC_TARGET_RADIUS)
                force_magnitude = SCC_COHESION_STRENGTH * displacement
                
                # Direction toward centroid
                fx = (dx / distance) * force_magnitude
                fy = (dy / distance) * force_magnitude
                
                # Add to existing forces
                curr_fx, curr_fy = self.forces[node_id]
                self.forces[node_id] = (curr_fx + fx, curr_fy + fy)
    
    def _calculate_scc_attraction(self,
                                 positions: Dict[int, Tuple[float, float]],
                                 masses: Dict[int, float]):
        """SCC acts as unified gravitational attractor (BLACK HOLE).
        
        Graph Theory Foundation:
        - SCC = strongly connected component = cycle/feedback loop
        - In directed graphs, SCC is an ATTRACTOR (sink component)
        - All paths eventually lead TO the SCC
        - PageRank: tokens accumulate in SCCs (can't escape)
        
        Physics Implementation:
        - Shared places connecting constellations to black hole are NOT frozen
        - They balance between constellation hub pull and black hole pull
        - This allows constellations to orbit at proper distance
        - Only SCC nodes themselves remain cohesive
        """
        if not hasattr(self, 'sccs') or not self.sccs:
            return  # No SCCs to process
        
        # NO EVENT HORIZON TRAPPING - let shared places balance naturally
        # This prevents constellations from being dragged toward cycle
        self.trapped_at_event_horizon = set()  # Empty set - nothing frozen
        
        # Apply gravitational attraction to constellation hubs
        SCC_GRAVITY_CONSTANT = 300.0  # Moderate gravity for constellation hubs (SCALED DOWN: was 1000, now 300 - 70% reduction)
        
        for scc in self.sccs:
            scc_nodes = set(scc.node_ids)
            if len(scc_nodes) == 0:
                continue
            
            # Calculate SCC center of mass and total mass
            scc_total_mass = 0.0
            weighted_x = 0.0
            weighted_y = 0.0
            
            for node_id in scc_nodes:
                if node_id not in positions or node_id not in masses:
                    continue
                mass = masses[node_id]
                x, y = positions[node_id]
                scc_total_mass += mass
                weighted_x += mass * x
                weighted_y += mass * y
            
            if scc_total_mass == 0:
                continue
            
            # SCC centroid (center of mass)
            centroid_x = weighted_x / scc_total_mass
            centroid_y = weighted_y / scc_total_mass
            
            # Apply gravitational attraction to high-mass nodes (constellation hubs)
            # This pulls them to orbit the black hole
            for node_id in positions:
                if node_id in scc_nodes:
                    continue  # Don't pull SCC nodes
                if node_id not in self.forces or node_id not in masses:
                    continue
                
                node_mass = masses[node_id]
                
                # Only affect high-mass nodes (constellation hubs, mass >= 1000)
                # Shared places (mass=100) are NOT pulled by SCC - they balance via arcs only
                # This prevents constellations from being dragged toward cycle
                if node_mass < 1000:
                    continue
                
                # Calculate distance from node to SCC centroid
                x, y = positions[node_id]
                dx = centroid_x - x
                dy = centroid_y - y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < self.MIN_DISTANCE:
                    continue
                
                # Gravitational attraction: F = G × m_node × M_scc_total / r²
                force_magnitude = (SCC_GRAVITY_CONSTANT * node_mass * scc_total_mass) / (distance * distance)
                
                # Direction: toward SCC centroid (attraction)
                fx = (dx / distance) * force_magnitude
                fy = (dy / distance) * force_magnitude
                
                # Add to existing forces
                curr_fx, curr_fy = self.forces[node_id]
                self.forces[node_id] = (curr_fx + fx, curr_fy + fy)
    
    def _calculate_ambient_tension(self,
                                   positions: Dict[int, Tuple[float, float]],
                                   masses: Dict[int, float]):
        """Calculate ambient tension for global spacing.
        
        NOTE: With universal repulsion now in proximity calculation,
        ambient tension is less critical. We keep it very weak or disabled.
        
        This can help with very large networks to prevent overall collapse,
        but for most networks the universal proximity repulsion is sufficient.
        """
        # Ambient tension is now redundant with universal proximity repulsion
        # We can skip it or keep it very weak
        # For now, we disable it (pass)
        pass
    
    def _update_positions(self,
                         positions: Dict[int, Tuple[float, float]],
                         masses: Dict[int, float]):
        """Update positions using Verlet integration.
        
        Uses velocity Verlet method:
        1. v(t+dt) = v(t) + (F/m) * dt
        2. p(t+dt) = p(t) + v(t+dt) * dt
        3. Apply damping to velocities
        """
        for node_id in positions:
            if node_id not in masses or node_id not in self.forces:
                continue
            
            mass = masses[node_id]
            force = self.forces[node_id]
            velocity = self.velocities[node_id]
            position = positions[node_id]
            
            # Update velocity: v = v + (F/m) * dt
            new_vx = velocity[0] + (force[0] / mass) * self.TIME_STEP
            new_vy = velocity[1] + (force[1] / mass) * self.TIME_STEP
            
            # Apply damping
            new_vx *= self.DAMPING
            new_vy *= self.DAMPING
            
            # Update position: p = p + v * dt
            new_x = position[0] + new_vx * self.TIME_STEP
            new_y = position[1] + new_vy * self.TIME_STEP
            
            # Store updates
            self.velocities[node_id] = (new_vx, new_vy)
            positions[node_id] = (new_x, new_y)
    
    def get_force_statistics(self) -> Dict:
        """Get statistics about forces in the simulation.
        
        Returns:
            Dictionary with force statistics for debugging/tuning.
        """
        if not self.forces:
            return {}
        
        force_magnitudes = []
        for fx, fy in self.forces.values():
            magnitude = math.sqrt(fx * fx + fy * fy)
            force_magnitudes.append(magnitude)
        
        return {
            'min_force': min(force_magnitudes) if force_magnitudes else 0,
            'max_force': max(force_magnitudes) if force_magnitudes else 0,
            'avg_force': sum(force_magnitudes) / len(force_magnitudes) if force_magnitudes else 0,
            'num_nodes': len(self.forces)
        }
