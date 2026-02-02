"""State-space exploration strategies for reachability analysis.

This package provides modular exploration strategies:
- base_explorer: Abstract base class
- sequential_explorer: Single-thread BFS
- parallel_basic_explorer: Multi-process work-stealing (Phase 1)
- parallel_maximal_explorer: Multi-process with maximal concurrent sets (Phase 2)
- maximal_sets: Independence analysis and maximal set computation
"""

from .base_explorer import StateSpaceExplorer, WorkQueue
from .maximal_sets import IndependenceAnalyzer, MaximalSetComputer

__all__ = [
    'StateSpaceExplorer',
    'WorkQueue',
    'IndependenceAnalyzer',
    'MaximalSetComputer'
]
