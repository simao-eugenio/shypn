"""Simulation execution strategies using Strategy pattern.

Week 4 - Phase 4: Strategy pattern for simulation algorithms.

Enables easy addition of new simulation algorithms without modifying
the SimulationController. Each strategy encapsulates a different
simulation approach (Gillespie SSA, Adaptive Tau-Leaping, Hybrid, etc.).

Usage:
    strategy = GillespieStrategy(controller)
    strategy.execute_step(time_step)
    
    # Or switch strategies at runtime
    controller.set_strategy(AdaptiveStrategy(controller))
"""

from .base_strategy import SimulationStrategy
from .gillespie_strategy import GillespieStrategy
from .adaptive_strategy import AdaptiveStrategy
from .hybrid_strategy import HybridStrategy
from .continuous_strategy import ContinuousStrategy

__all__ = [
    'SimulationStrategy',
    'GillespieStrategy',
    'AdaptiveStrategy',
    'HybridStrategy',
    'ContinuousStrategy',
]
