"""Layout algorithms for Petri net visualization.

This package provides automatic layout algorithms for Petri nets:
- Solar System Layout: Physics-based orbital layout using SCCs as gravitational centers
- (Future) Hierarchical Layout: Top-down tree-based layout
- (Future) Circular Layout: Nodes arranged in circular patterns
"""

from shypn.layout.sscc import SolarSystemLayoutEngine

__all__ = [
    'SolarSystemLayoutEngine',
]
