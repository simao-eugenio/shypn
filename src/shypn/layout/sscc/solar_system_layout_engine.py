"""Solar System Layout Engine - Main orchestrator for SSCC layout algorithm.

This is the main entry point for the Solar System Layout algorithm.
It coordinates all components to apply the layout to a Petri net.
"""

from typing import Dict, List, Optional, Tuple, Callable
from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc.graph_builder import GraphBuilder
from shypn.layout.sscc.scc_detector import SCCDetector
from shypn.layout.sscc.mass_assigner import MassAssigner
from shypn.layout.sscc.hub_based_mass_assigner import HubBasedMassAssigner
from shypn.layout.sscc.unified_physics_simulator import UnifiedPhysicsSimulator
from shypn.layout.sscc.orbit_stabilizer import OrbitStabilizer
from shypn.layout.sscc.strongly_connected_component import StronglyConnectedComponent


class SolarSystemLayoutEngine:
    """Main orchestrator for Solar System Layout algorithm.
    
    This algorithm creates a "solar system" structure where:
    - Strongly connected components (cycles) are massive "stars" at the center
    - High-degree nodes (hubs) can also become gravitational centers
    - Places are "planets" orbiting the stars/hubs
    - Transitions are "satellites" orbiting planets
    - Arcs create gravitational forces (weighted by arc.weight)
    
    The algorithm has three phases:
    1. Structure Analysis: Build graph, detect SCCs, assign masses (hub-based or simple)
    2. Physics Simulation: Apply gravitational forces for N iterations
    3. Orbital Stabilization: Refine positions for clean orbital structure
    
    Hub-Based Mass Assignment (NEW):
    - When enabled (default), high-degree nodes get higher masses
    - Super-hubs (≥6 connections): mass = 1000 (like stars)
    - Major hubs (≥4 connections): mass = 500
    - Minor hubs (≥2 connections): mass = 200
    - Creates hierarchy even in DAG networks without cycles
    """
    
    def __init__(self,
                 iterations: int = 1000,
                 use_arc_weight: bool = True,
                 use_hub_masses: bool = True,
                 scc_radius: float = 50.0,
                 planet_orbit: float = 300.0,
                 satellite_orbit: float = 50.0,
                 progress_callback: Optional[Callable[[str, float], None]] = None):
        """Initialize Solar System Layout engine.
        
        Args:
            iterations: Number of simulation iterations (default: 1000)
            use_arc_weight: Use arc.weight in force calculation (default: True)
            use_hub_masses: Use hub-based masses for high-degree nodes (default: True)
            scc_radius: Radius for SCC internal layout (default: 50.0)
            planet_orbit: Base orbital radius for places (default: 300.0)
            satellite_orbit: Orbital radius for transitions (default: 50.0)
            progress_callback: Optional callback(stage, progress) for UI updates
        """
        self.iterations = iterations
        self.use_arc_weight = use_arc_weight
        self.use_hub_masses = use_hub_masses
        self.scc_radius = scc_radius
        self.planet_orbit = planet_orbit
        self.satellite_orbit = satellite_orbit
        self.progress_callback = progress_callback
        
        # Initialize components
        self.graph_builder = GraphBuilder()
        self.scc_detector = SCCDetector()
        self.mass_assigner = MassAssigner()
        self.hub_mass_assigner = HubBasedMassAssigner()  # Hub-based mass assignment
        
        # Unified physics simulator (combines all forces)
        self.simulator = UnifiedPhysicsSimulator(
            enable_oscillatory=True,   # Arc-based forces with equilibrium
            enable_proximity=True,      # Hub-to-hub repulsion
            enable_ambient=True         # Global spacing
        )
        
        self.stabilizer = OrbitStabilizer(
            scc_radius=scc_radius,
            planet_orbit=planet_orbit,
            satellite_orbit=satellite_orbit
        )
        
        # State (for debugging/inspection)
        self.sccs: List[StronglyConnectedComponent] = []
        self.masses: Dict[int, float] = {}
        self.positions: Dict[int, Tuple[float, float]] = {}
    
    def apply_layout(self,
                     places: List[Place],
                     transitions: List[Transition],
                     arcs: List[Arc],
                     initial_positions: Optional[Dict[int, Tuple[float, float]]] = None) -> Dict[int, Tuple[float, float]]:
        """Apply Solar System Layout to Petri net.
        
        Args:
            places: List of places in the Petri net
            transitions: List of transitions in the Petri net
            arcs: List of arcs in the Petri net
            initial_positions: Optional initial positions (default: random)
            
        Returns:
            Dictionary mapping object ID to (x, y) position
        """
        # Phase 1: Structure Analysis
        self._report_progress("Structure Analysis", 0.0)
        self._analyze_structure(places, transitions, arcs)
        self._report_progress("Structure Analysis", 1.0)
        
        # Phase 2: Physics Simulation
        self._report_progress("Physics Simulation", 0.0)
        self._run_simulation(places, transitions, arcs, initial_positions)
        self._report_progress("Physics Simulation", 1.0)
        
        # Phase 3: Orbital Stabilization (DISABLED - let physics work naturally)
        # The orbit stabilizer was imposing geometric layouts and overwriting physics results
        # For hub-based layouts with proper force tuning, we skip this step
        self._report_progress("Orbital Stabilization", 0.0)
        self._report_progress("Orbital Stabilization", 1.0)
        
        return self.positions
    
    def _analyze_structure(self, places: List[Place], transitions: List[Transition], arcs: List[Arc]):
        """Phase 1: Analyze graph structure and assign masses.
        
        Args:
            places: List of places
            transitions: List of transitions
            arcs: List of arcs
        """
        # Build directed graph
        graph = self.graph_builder.build_graph(places, transitions, arcs)
        id_to_object = self.graph_builder.id_to_object
        
        # Detect strongly connected components (cycles)
        self.sccs = self.scc_detector.find_sccs(graph, id_to_object)
        
        # Assign gravitational masses
        if self.use_hub_masses:
            # NEW: Use hub-based mass assignment
            # High-degree nodes get higher masses, making them gravitational centers
            self.masses = self.hub_mass_assigner.assign_masses(self.sccs, places, transitions, arcs)
        else:
            # Original: Simple SCC-based mass assignment
            self.masses = self.mass_assigner.assign_masses(self.sccs, places, transitions)
    
    def _run_simulation(self,
                        places: List[Place],
                        transitions: List[Transition],
                        arcs: List[Arc],
                        initial_positions: Optional[Dict[int, Tuple[float, float]]]):
        """Phase 2: Run gravitational physics simulation.
        
        Args:
            places: List of places
            transitions: List of transitions
            arcs: List of arcs
            initial_positions: Optional initial positions
        """
        # Initialize positions from object coordinates if not provided
        if initial_positions:
            positions = initial_positions
        elif self.positions:
            positions = self.positions
        else:
            # Extract current positions from objects
            positions = {}
            for p in places:
                positions[p.id] = (p.x, p.y)
            for t in transitions:
                positions[t.id] = (t.x, t.y)
        
        # Call unified physics simulator with correct signature
        self.positions = self.simulator.simulate(
            positions=positions,
            arcs=arcs,
            masses=self.masses,
            iterations=self.iterations,
            progress_callback=self.progress_callback,
            sccs=self.sccs  # Pass SCCs for cohesion forces (black hole effect)
        )
    
    def _stabilize_orbits(self, places: List[Place], transitions: List[Transition]):
        """Phase 3: Apply orbital stabilization.
        
        Args:
            places: List of places
            transitions: List of transitions
        """
        self.positions = self.stabilizer.stabilize(
            positions=self.positions,
            sccs=self.sccs,
            places=places,
            transitions=transitions
        )
    
    def _report_progress(self, stage: str, progress: float):
        """Report progress to callback if available.
        
        Args:
            stage: Current stage name
            progress: Progress within stage (0.0 to 1.0)
        """
        if self.progress_callback:
            self.progress_callback(stage, progress)
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the layout process.
        
        Returns:
            Dictionary with statistics:
                - num_sccs: Number of SCCs found
                - num_nodes_in_sccs: Total nodes in SCCs
                - num_free_places: Places not in SCCs
                - num_transitions: Total transitions
                - avg_mass: Average mass
                - hub_stats: Hub classification (if using hub masses)
        """
        num_nodes_in_sccs = sum(scc.size for scc in self.sccs)
        num_free_places = sum(1 for obj_id, mass in self.masses.items() 
                             if mass == MassAssigner.MASS_PLACE)
        num_transitions = sum(1 for obj_id, mass in self.masses.items()
                             if mass == MassAssigner.MASS_TRANSITION)
        avg_mass = sum(self.masses.values()) / len(self.masses) if self.masses else 0
        
        stats = {
            'num_sccs': len(self.sccs),
            'num_nodes_in_sccs': num_nodes_in_sccs,
            'num_free_places': num_free_places,
            'num_transitions': num_transitions,
            'avg_mass': avg_mass,
            'total_nodes': len(self.positions),
            'physics_model': 'Unified Physics (Oscillatory + Proximity + Ambient)'
        }
        
        # Add hub statistics if using hub-based masses
        if self.use_hub_masses and hasattr(self.hub_mass_assigner, 'hub_stats'):
            stats['hub_stats'] = self.hub_mass_assigner.get_hub_statistics()
        
        return stats
