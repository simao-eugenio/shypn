"""Solar System Layout (SSCC) - Physics-based layout for Petri nets.

This package implements a gravitational physics-based layout algorithm
where Petri net objects are assigned specific roles:
- SCCs (cycles) → Stars (massive gravitational centers)
- Places → Planets (orbit stars)
- Transitions → Satellites (orbit planets)
- Arcs → Gravitational forces (weighted by arc.weight)

Main entry point:
    from shypn.layout.sscc import SolarSystemLayoutEngine
    engine = SolarSystemLayoutEngine()
    engine.apply_layout(places, transitions, arcs)
"""

from shypn.layout.sscc.solar_system_layout_engine import SolarSystemLayoutEngine
from shypn.layout.sscc.scc_detector import SCCDetector, StronglyConnectedComponent
from shypn.layout.sscc.graph_builder import GraphBuilder
from shypn.layout.sscc.mass_assigner import MassAssigner
from shypn.layout.sscc.gravitational_simulator import GravitationalSimulator
from shypn.layout.sscc.orbit_stabilizer import OrbitStabilizer

__all__ = [
    'SolarSystemLayoutEngine',
    'SCCDetector',
    'StronglyConnectedComponent',
    'GraphBuilder',
    'MassAssigner',
    'GravitationalSimulator',
    'OrbitStabilizer',
]
