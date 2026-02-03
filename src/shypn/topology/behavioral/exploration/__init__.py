"""State-space exploration strategies for reachability analysis.

This package provides modular exploration strategies:
- base_explorer: Abstract base class
- sequential_explorer: Single-thread BFS
- parallel_basic_explorer: Multi-process work-stealing (Phase 1)
- parallel_maximal_explorer: Multi-process with maximal concurrent sets (Phase 2)
- hierarchical_explorer: Layer-by-layer signal hierarchy exploration (Phase 3)
- maximal_sets: Independence analysis and maximal set computation
- signal_layer_detector: Signal hierarchy layer detection
- transition_partitioner: Transition grouping by signal layer
"""

from .base_explorer import StateSpaceExplorer, WorkQueue
from .maximal_sets import IndependenceAnalyzer, MaximalSetComputer
from .signal_layer_detector import SignalLayerDetector
from .transition_partitioner import TransitionPartitioner
from .hierarchical_explorer import HierarchicalExplorer

__all__ = [
    'StateSpaceExplorer',
    'WorkQueue',
    'IndependenceAnalyzer',
    'MaximalSetComputer',
    'SignalLayerDetector',
    'TransitionPartitioner',
    'HierarchicalExplorer'
]
