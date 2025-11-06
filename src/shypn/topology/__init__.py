"""Topology analysis system for Petri nets.

This module provides comprehensive topology analysis capabilities for Petri nets,
including structural properties, graph analysis, behavioral properties, and
network metrics.

Architecture:
    - base/: Abstract base classes and result structures
    - structural/: P/T-invariants, siphons, traps
    - graph/: Cycles, paths, SCCs, DAG analysis
    - behavioral/: Liveness, boundedness, reachability, deadlocks
    - network/: Hubs, centrality, communities, clustering

Usage:
    from shypn.topology.graph import CycleAnalyzer
    
    analyzer = CycleAnalyzer(model)
    result = analyzer.analyze()
    
    if result.success:
        print(result.summary)
        for cycle in result.get('cycles', []):
"""

from .base import TopologyAnalyzer, AnalysisResult, TopologyError

__version__ = '0.1.0'

__all__ = [
    'TopologyAnalyzer',
    'AnalysisResult',
    'TopologyError',
]
