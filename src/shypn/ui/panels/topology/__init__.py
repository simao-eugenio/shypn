#!/usr/bin/env python3
"""Topology Panel - Normalized panel with category structure.

This package contains the normalized Topology Panel implementation
following the Report Panel architecture:
- TopologyPanel: Main panel class
- BaseTopologyCategory: Base class for categories
- StructuralCategory: Structural analysis (P/T-Invariants, Siphons, Traps)
- GraphNetworkCategory: Graph & network analysis (Cycles, Paths, Hubs)
- BehavioralCategory: Behavioral analysis (Reachability, Boundedness, etc.)

Author: Simão Eugénio
Date: 2025-10-29
"""

from shypn.ui.panels.topology.topology_panel import TopologyPanel
from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
from shypn.ui.panels.topology.structural_category import StructuralCategory
from shypn.ui.panels.topology.graph_network_category import GraphNetworkCategory
from shypn.ui.panels.topology.behavioral_category import BehavioralCategory

__all__ = [
    'TopologyPanel',
    'BaseTopologyCategory',
    'StructuralCategory',
    'GraphNetworkCategory',
    'BehavioralCategory',
]
