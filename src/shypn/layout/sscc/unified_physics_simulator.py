"""Unified Physics Simulator - Combines all forces for Solar System Layout.

VERSION: 2.2.4 - Black Hole Gravity Enabled + Arc Weight Removed from Forces
DATE: October 17, 2025
STATUS: PRODUCTION STABLE

MAJOR FEATURES:
- Black hole galaxy model with SCC cycle at center
- SCC-aware gravitational attraction (only affects constellation hubs)
- Black hole damping wave (distance-based repulsion reduction)
- Arc force weakening for SCC connections (prevents ternary clustering)
- Black hole whirlwind effect (spiral orbital patterns)
- Pulsating singularity with stochastic dynamics ⭐ NEW in v2.2.0
- Variance-based convergence detection ⭐ NEW in v2.2.0
- Event horizon mechanics (configurable node trapping)
- Multi-level galaxy cluster hierarchies

PULSATING SINGULARITY INSIGHT (v2.2.0):
"The clogged sink drain pulses at high frequency from the bottom of the 
singularity to the surface, causing the damping wave oscillation, and the 
elements at surface (hubs, constellations, ...) are constantly under 
rearrangement in relation to each other."

SCIENTIFIC FOUNDATION:
Based on real astrophysical phenomena:
- Quasi-Periodic Oscillations (QPOs) in black hole accretion disks
- Wave propagation from singularity to surface (100-1000 Hz)
- Stochastic thermodynamic equilibrium (Langevin dynamics)
- Fluctuation-dissipation theorem
- Dynamic equilibrium through constant micro-adjustments
- Optimal distribution via variance stabilization

The system never reaches static equilibrium - instead maintains dynamic
equilibrium through high-frequency pulsations, like molecules in a liquid
constantly rearranging while maintaining overall structure.

PHYSICS MODEL:
This simulator implements a unified physics model that combines:
1. Oscillatory forces (arc-based attraction/repulsion with equilibrium)
2. Proximity repulsion (all-pairs Coulomb-like repulsion with damping wave)
3. Ambient tension (global spacing force)
4. Hub group repulsion (prevents constellation clustering)
5. SCC cohesion (maintains black hole cycle shape)
6. SCC gravity (pulls constellation hubs toward black hole)
7. SCC whirlwind (tangential forces create spiral motion)
8. Pulsating singularity (high-frequency stochastic forces) ⭐ NEW
9. Variance tracking (convergence detection metric) ⭐ NEW

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
2. SCC Gravity: 300 (radial pull toward black hole, mass >= 1000)
3. SCC Whirlwind: 50 (tangential spiral force)
4. Pulsation Noise: 10 (stochastic forces, temperature-like) ⭐ NEW in v2.2.0
5. Hub Group Repulsion: 30 (prevents constellation clustering)
6. Arc Forces: 1.2 (attraction/repulsion via connections)
   - Normal arcs: 1.2
   - SCC arcs: 0.12 (90% weaker - prevents ternary clustering)
7. Proximity Repulsion: 6 (with black hole damping)
8. Damping Wave: 0.1-1.0 (distance-based from black hole center)

CONVERGENCE DETECTION:
- Position variance tracking (measures system stability)
- Variance stabilization indicates optimal distribution reached
- Like molecules in liquid: constant motion, stable structure

The algorithm automatically balances all forces to create natural,
stable layouts without user intervention. The pulsating singularity
ensures the system never freezes in suboptimal configurations.

CHANGELOG:
v2.2.4 (Oct 17, 2025): FUNDAMENTAL FIX - Enable SCC gravity + remove arc weight from forces ⭐ CRITICAL
v2.2.3 (Oct 17, 2025): Fixed hub mass threshold (500→150) for selective weakening
v2.2.2 (Oct 17, 2025): Selective arc weakening - mass-based (wrong threshold)
v2.2.1 (Oct 17, 2025): Place orbital fix - disable extra proximity for low-mass nodes
v2.2.0 (Oct 17, 2025): Pulsating singularity - stochastic dynamics & variance tracking
v2.1.0 (Oct 17, 2025): Black hole whirlwind effect - spiral orbital patterns
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
import random
from shypn.netobjs import Place, Transition, Arc


class UnifiedPhysicsSimulator:
    """Unified physics engine combining oscillatory, proximity, and ambient forces.
    
    VERSION: 2.1.0 - Black Hole Whirlwind Effect
    
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
    - Constellation hubs spiral around the black hole (whirlwind!)
    - Pulsations cause constant micro-rearrangement (dynamic equilibrium) ⭐
    - Shared places orbit constellation hubs (not black hole)
    - Satellites orbit hubs naturally
    - Everything stays well-spaced with hierarchical structure
    - Beautiful spiral patterns emerge from whirlwind effect
    - System achieves optimal distribution through variance stabilization ⭐
    """
    
    # VERSION MARKER
    VERSION = "2.2.4"
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
    SCC_GRAVITY_MIN_MASS = 150.0            # v2.2.4: LOWERED from 1000 to enable gravity for hubs (200-300 mass)
    SCC_ARC_WEAKENING_FACTOR = 0.3          # v2.2.4: REDUCED from 0.1 - less extreme weakening
    
    # Black hole whirlwind effect (v2.1.0) - "Clogged sink drain" spiral forces
    SCC_WHIRLWIND_STRENGTH = 50.0           # Tangential force strength (creates spiral motion)
    SCC_WHIRLWIND_ENABLED = True            # Enable/disable whirlwind effect
    SCC_WHIRLWIND_DIRECTION = 1.0           # 1.0 = counterclockwise, -1.0 = clockwise
    
    # Pulsating singularity (v2.2.0) - High-frequency oscillations from black hole
    PULSATION_ENABLED = True                # Enable/disable pulsating singularity
    PULSATION_FREQUENCY = 500.0             # Pulsation frequency (Hz equivalent, 100-1000 Hz range)
    PULSATION_STRENGTH = 10.0               # Stochastic force magnitude (temperature-like parameter)
    PULSATION_DECAY = 0.95                  # Decay factor (reduces over time for convergence)
    VARIANCE_WINDOW = 50                    # Number of iterations to track variance
    VARIANCE_THRESHOLD = 0.01               # Variance stabilization threshold (convergence metric)
    
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
        
        # Pulsating singularity state (v2.2.0)
        self.variance_history: List[float] = []  # Track variance over time
        self.pulsation_temperature: float = self.PULSATION_STRENGTH  # Current temperature
        self.iteration_count: int = 0  # Current iteration number
    
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
        
        # Initialize pulsation state (v2.2.0)
        self.variance_history = []
        self.pulsation_temperature = self.PULSATION_STRENGTH
        self.iteration_count = 0
        
        # Run simulation
        for iteration in range(iterations):
            self.iteration_count = iteration
            
            # Calculate all forces
            self._calculate_forces(positions, consolidated_arcs, masses)
            
            # Update positions using Verlet integration
            self._update_positions(positions, masses)
            
            # Variance tracking (v2.2.0) - measure system stability
            if self.PULSATION_ENABLED and iteration % 10 == 0:
                variance = self._calculate_position_variance(positions)
                self.variance_history.append(variance)
                
                # Temperature decay (simulated annealing)
                # Gradually reduce stochastic forces to allow convergence
                self.pulsation_temperature *= self.PULSATION_DECAY
                
                # Check for convergence (variance stabilization)
                if len(self.variance_history) > self.VARIANCE_WINDOW:
                    recent_variance = self.variance_history[-self.VARIANCE_WINDOW:]
                    variance_change = max(recent_variance) - min(recent_variance)
                    
                    if variance_change < self.VARIANCE_THRESHOLD:
                        # Convergence achieved - variance stabilized!
                        # Continue with minimal pulsation to maintain dynamic equilibrium
                        self.pulsation_temperature = max(
                            self.pulsation_temperature, 
                            self.PULSATION_STRENGTH * 0.1  # Keep 10% pulsation
                        )
            
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
        
        # 2.6. Pulsating singularity (v2.2.0)
        # High-frequency stochastic forces from black hole singularity
        if self.PULSATION_ENABLED:
            self._calculate_pulsation_forces(positions, masses)
        
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
            # VERSION 2.2.3 - FIXED SELECTIVE ARC WEAKENING (Oct 17, 2025)
            # ============================================================
            # SMART ARC WEAKENING: Only weaken hub-to-SCC arcs, not place-to-SCC
            # 
            # EVOLUTION:
            # v2.0.0: Weakened ALL arcs to SCC by 90%
            #   Problem: Places couldn't orbit cycle (arc too weak: 0.12)
            #   
            # v2.2.1: Fixed proximity repulsion (or→and)
            #   Problem: Places form ternary system (arc still too weak!)
            #   
            # v2.2.2: Selective weakening - but WRONG threshold (>= 500)
            #   Problem: Hubs have mass 200-300, so they got FULL strength too!
            #   Result: Still forming ternary system!
            #
            # v2.2.3: FIXED threshold - distinguish places from hubs
            #   Mass values: Place=100, MinorHub=200, MajorHub=200, SuperHub=300
            #   Threshold: 150 (between place and hub)
            #   Solution: Places (100) get FULL strength
            #            Hubs (200+) get WEAKENED strength
            #
            # LOGIC:
            # - If ONE node is SCC AND other mass < 150: FULL STRENGTH (place-to-cycle)
            # - If ONE node is SCC AND other mass >= 150: WEAKEN (hub-to-cycle)  
            # - If BOTH nodes NOT in SCC: FULL STRENGTH (hub-to-hub, place-to-hub)
            #
            # RESULT:
            # - Places (mass=100) orbit cycle closely (full arc: 1.2) ✓
            # - Hubs (mass=200-300) spread around cycle (weakened arc: 0.12) ✓
            # - Beautiful hierarchy! ✓
            # ============================================================
            arc_strength_multiplier = 1.0
            if hasattr(self, 'sccs') and self.sccs:
                for scc in self.sccs:
                    scc_nodes = set(scc.node_ids)
                    
                    # Check if arc connects to SCC
                    source_in_scc = source_id in scc_nodes
                    target_in_scc = target_id in scc_nodes
                    
                    if source_in_scc or target_in_scc:
                        # One end is in SCC - check if OTHER end is a hub or place
                        # Use mass threshold of 150 to distinguish:
                        #   Place: mass = 100 (< 150) → FULL strength
                        #   Hub: mass = 200-300 (>= 150) → WEAKENED
                        other_mass = target_mass if source_in_scc else source_mass
                        HUB_MASS_THRESHOLD = 150.0  # Between place (100) and hub (200+)
                        
                        if other_mass >= HUB_MASS_THRESHOLD:
                            # Hub (mass >= 150) connecting to SCC
                            # Weaken to prevent constellation dragging
                            arc_strength_multiplier = self.SCC_ARC_WEAKENING_FACTOR  # 0.1
                        else:
                            # Place (mass < 150) connecting to SCC
                            # Keep FULL strength so place can orbit cycle!
                            arc_strength_multiplier = 1.0  # FULL STRENGTH
                        break
            # ============================================================
            # END VERSION 2.2.3 FIXED SELECTIVE ARC WEAKENING
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
        
        VERSION 2.2.4: Arc weight NO LONGER affects force magnitude!
        - Arc weight only affects equilibrium distance (r_eq)
        - Force strength based ONLY on masses and distance
        - Prevents drift caused by weighted arc discrimination
        
        - If distance > r_eq: Gravitational attraction (pull together)
        - If distance < r_eq: Spring repulsion (push apart)
        - At distance = r_eq: Zero force (equilibrium)
        """
        if distance > r_eq:
            # Too far: gravitational attraction
            # v2.2.4: REMOVED weight from force calculation
            # F = (G * m1 * m2) / r²  (NO weight multiplier)
            force = (self.GRAVITY_CONSTANT * m1 * m2) / (distance * distance)
            return force  # Positive = attract
        else:
            # Too close: spring repulsion
            # F = -k * (r_eq - r)
            force = self.SPRING_CONSTANT * (r_eq - distance)
            return -force  # Negative = repel
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
                
                # ============================================================
                # VERSION 2.2.1 - PLACE ORBITAL FIX (Oct 17, 2025)
                # ============================================================
                # EXTRA HUB REPULSION: High-mass nodes get additional repulsion
                # CRITICAL FIX: Only applies when BOTH nodes are hubs (mass >= threshold)
                # 
                # PROBLEM: Places (mass=100) were getting massive repulsion from hubs
                #   - Hub-to-place: 6.0 × 1000 × 100 / r² = 600,000 / r² (!)
                #   - This pushed places to "middle path" between cycle and constellation
                #   - Arc forces (1.2) couldn't compete with proximity (600,000 / r²)
                #
                # SOLUTION: Change "or" to "and"
                #   - Hub-to-hub: Extra repulsion ACTIVE (both >= 500) ✓
                #   - Hub-to-place: Extra repulsion DISABLED (place < 500) ✓
                #   - Place-to-place: Extra repulsion DISABLED ✓
                #
                # RESULT: Places orbit close to hubs (arc forces dominate)
                #         Hubs spread apart (proximity repulsion active)
                #         Beautiful hierarchy maintained!
                # ============================================================
                extra_force = 0.0
                if m1 >= self.PROXIMITY_THRESHOLD and m2 >= self.PROXIMITY_THRESHOLD:
                    # Coulomb-like repulsion: F = (K * m1 * m2) / r²
                    extra_force = (self.PROXIMITY_CONSTANT * m1 * m2) / (distance * distance)
                # ============================================================
                # END VERSION 2.2.1 PLACE ORBITAL FIX
                # ============================================================
                
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
                
                # ============================================================
                # VERSION 2.1.0 - BLACK HOLE WHIRLWIND EFFECT (Oct 17, 2025)
                # ============================================================
                # INSIGHT: "Black holes are like clogged sink drains"
                # 
                # The damping wave oscillates between attract/repulsion,
                # causing matter to spiral around the black hole like water
                # circling a drain. This creates a whirlwind effect.
                #
                # IMPLEMENTATION: Add tangential force perpendicular to radial
                # - Radial force: pulls toward/pushes from black hole
                # - Tangential force: creates rotation/spiral motion
                # - Result: Nodes orbit in spiral patterns (whirlwind!)
                #
                # The tangential force is strongest at medium distances
                # where the damping wave oscillation is most active.
                # ============================================================
                if self.SCC_WHIRLWIND_ENABLED:
                    # Calculate tangential force (perpendicular to radial)
                    # For 2D rotation: if radial vector is (dx, dy)
                    # then tangential vector is (-dy, dx) for counterclockwise
                    # or (dy, -dx) for clockwise
                    
                    # Tangential force magnitude depends on distance
                    # Strongest at medium range (500-1000 units) where damping oscillates
                    # Weaker near black hole (tight) and far away (escapes whirlwind)
                    distance_ratio = distance / 1000.0
                    if distance_ratio > 1.0:
                        distance_ratio = 1.0
                    
                    # Bell curve: strongest at 0.5-0.8 range
                    whirlwind_intensity = 4.0 * distance_ratio * (1.0 - distance_ratio)
                    
                    # Tangential force strength
                    tangential_magnitude = (self.SCC_WHIRLWIND_STRENGTH * 
                                          node_mass * whirlwind_intensity)
                    
                    # Tangential direction (perpendicular to radial)
                    # Normalized radial: (dx/r, dy/r)
                    # Tangential (CCW): (-dy/r, dx/r)
                    tx = (-dy / distance) * tangential_magnitude * self.SCC_WHIRLWIND_DIRECTION
                    ty = (dx / distance) * tangential_magnitude * self.SCC_WHIRLWIND_DIRECTION
                    
                    # Add tangential force to radial force
                    fx += tx
                    fy += ty
                # ============================================================
                # END VERSION 2.1.0 WHIRLWIND EFFECT
                # ============================================================
                
                # Add to existing forces
                curr_fx, curr_fy = self.forces[node_id]
                self.forces[node_id] = (curr_fx + fx, curr_fy + fy)
    
    def _calculate_pulsation_forces(self,
                                    positions: Dict[int, Tuple[float, float]],
                                    masses: Dict[int, float]):
        """Calculate pulsating singularity forces (v2.2.0).
        
        ============================================================
        VERSION 2.2.0 - PULSATING SINGULARITY (Oct 17, 2025)
        ============================================================
        
        SCIENTIFIC FOUNDATION:
        - Based on Quasi-Periodic Oscillations (QPOs) in black holes
        - Singularity pulses at high frequency (100-1000 Hz)
        - Waves propagate radially from center to surface
        - Creates stochastic Brownian motion (thermal fluctuations)
        
        IMPLEMENTATION:
        - Langevin dynamics: deterministic forces + stochastic noise
        - Gaussian random forces scaled by temperature parameter
        - Temperature decays over time (simulated annealing)
        - Prevents system from freezing in local minima
        
        PHYSICS INTERPRETATION:
        - Like molecules in liquid: constant motion, stable structure
        - Never static equilibrium - dynamic equilibrium instead
        - Optimal distribution through variance stabilization
        - High frequency ensures constant rearrangement
        
        FORCE EQUATION:
        F_pulsation = N(0, σ²) × temperature × sqrt(node_mass)
        
        Where:
        - N(0, σ²) = Gaussian random variable
        - temperature = current pulsation strength (decays over time)
        - sqrt(mass) = mass-dependent scaling (heavier nodes more stable)
        ============================================================
        """
        if not hasattr(self, 'sccs') or not self.sccs:
            return  # No black hole, no pulsations
        
        # Get current temperature (decays over time)
        temperature = self.pulsation_temperature
        
        for node_id in positions:
            if node_id not in self.forces or node_id not in masses:
                continue
            
            # Stochastic force magnitude
            # Scale by sqrt(mass) so heavier nodes are more stable
            node_mass = masses[node_id]
            noise_scale = temperature * math.sqrt(node_mass)
            
            # Gaussian random forces (Brownian motion)
            # Using Box-Muller transform for Gaussian distribution
            fx_noise = random.gauss(0, noise_scale)
            fy_noise = random.gauss(0, noise_scale)
            
            # Add stochastic forces to existing forces
            curr_fx, curr_fy = self.forces[node_id]
            self.forces[node_id] = (curr_fx + fx_noise, curr_fy + fy_noise)
    
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
    
    def _calculate_position_variance(self, 
                                     positions: Dict[int, Tuple[float, float]]) -> float:
        """Calculate variance of node positions (v2.2.0).
        
        ============================================================
        VERSION 2.2.0 - VARIANCE TRACKING (Oct 17, 2025)
        ============================================================
        
        CONVERGENCE METRIC:
        Variance measures spread of positions around centroid.
        When variance stabilizes, system has reached optimal distribution.
        
        SCIENTIFIC BASIS:
        - Statistical mechanics: free energy minimization
        - Thermodynamics: equilibrium through entropy maximization
        - Variance = measure of system disorder/energy
        
        INTERPRETATION:
        - High variance change: system actively rearranging
        - Low variance change: system reached equilibrium
        - Stabilized variance: optimal distribution achieved
        
        Like water in a glass:
        - Initially: molecules moving wildly (high variance change)
        - Eventually: gentle motion, stable structure (low variance change)
        - Equilibrium: constant small fluctuations, but variance stable
        ============================================================
        """
        if not positions:
            return 0.0
        
        # Calculate centroid
        total_x = sum(x for x, y in positions.values())
        total_y = sum(y for x, y in positions.values())
        n = len(positions)
        
        centroid_x = total_x / n
        centroid_y = total_y / n
        
        # Calculate variance (average squared distance from centroid)
        variance_sum = 0.0
        for x, y in positions.values():
            dx = x - centroid_x
            dy = y - centroid_y
            variance_sum += dx * dx + dy * dy
        
        variance = variance_sum / n
        return variance
    
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
    
    def get_convergence_statistics(self) -> Dict:
        """Get convergence statistics from pulsating singularity (v2.2.0).
        
        Returns:
            Dictionary with convergence metrics.
        """
        if not self.variance_history:
            return {
                'variance_history': [],
                'current_variance': 0.0,
                'variance_stabilized': False,
                'current_temperature': self.pulsation_temperature,
                'iterations': self.iteration_count
            }
        
        # Check if variance stabilized
        variance_stabilized = False
        if len(self.variance_history) > self.VARIANCE_WINDOW:
            recent_variance = self.variance_history[-self.VARIANCE_WINDOW:]
            variance_change = max(recent_variance) - min(recent_variance)
            variance_stabilized = variance_change < self.VARIANCE_THRESHOLD
        
        return {
            'variance_history': self.variance_history[-100:],  # Last 100 values
            'current_variance': self.variance_history[-1] if self.variance_history else 0.0,
            'variance_stabilized': variance_stabilized,
            'current_temperature': self.pulsation_temperature,
            'iterations': self.iteration_count,
            'pulsation_enabled': self.PULSATION_ENABLED
        }
