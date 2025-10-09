"""
Graph Layout Module - Automatic Layout Algorithms

This module provides automatic layout algorithms for Petri nets,
particularly useful for imported biological pathways (KEGG).

Architecture:
    - LayoutAlgorithm: Abstract base class for all algorithms
    - HierarchicalLayout: Sugiyama framework (layered, directed)
    - ForceDirectedLayout: Fruchterman-Reingold (physics-based)
    - CircularLayout: For cyclic pathways (TCA, Calvin)
    - OrthogonalLayout: Manhattan routing (circuit-like)
    - LayoutSelector: Auto-detect best algorithm for topology
    - LayoutEngine: Main API orchestrator

Scientific Basis:
    - Sugiyama et al. (1981) - Hierarchical layout
    - Fruchterman & Reingold (1991) - Force-directed
    - Di Battista et al. (1998) - Graph drawing algorithms
    - Dogrusoz et al. (2009) - Biological pathway layout

Usage:
    >>> from shypn.edit.graph_layout import LayoutEngine
    >>> engine = LayoutEngine(document_manager)
    >>> engine.apply_layout('auto')  # Auto-select best algorithm
    >>> # or
    >>> engine.apply_layout('hierarchical')  # Specific algorithm
"""

from .base import LayoutAlgorithm
from .hierarchical import HierarchicalLayout
from .force_directed import ForceDirectedLayout
from .circular import CircularLayout
from .orthogonal import OrthogonalLayout
from .selector import LayoutSelector
from .engine import LayoutEngine

__all__ = [
    'LayoutAlgorithm',
    'HierarchicalLayout',
    'ForceDirectedLayout',
    'CircularLayout',
    'OrthogonalLayout',
    'LayoutSelector',
    'LayoutEngine'
]
