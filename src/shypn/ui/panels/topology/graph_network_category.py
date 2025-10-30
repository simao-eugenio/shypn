#!/usr/bin/env python3
"""Graph & Network Topology Analysis Category.

Manages graph and network property analyzers:
1. Cycles - Circular paths in the Petri net
2. Paths - Directed paths between places/transitions
3. Hubs - Highly connected nodes (network analysis)

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
from shypn.topology.graph.cycles import CycleAnalyzer
from shypn.topology.graph.paths import PathAnalyzer
from shypn.topology.network.hubs import HubAnalyzer


class GraphNetworkCategory(BaseTopologyCategory):
    """Graph & Network analysis category for Topology Panel.
    
    Contains:
    - Analysis Summary section
    - Cycles analyzer
    - Paths analyzer
    - Hubs analyzer
    """
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize graph & network category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
        """
        super().__init__(
            title="Graph & Network Analysis",
            model_canvas=model_canvas,
            expanded=expanded
        )
    
    def _get_analyzers(self):
        """Get dict of analyzer name -> AnalyzerClass.
        
        Returns:
            dict: {analyzer_name: AnalyzerClass}
        """
        return {
            'cycles': CycleAnalyzer,
            'paths': PathAnalyzer,
            'hubs': HubAnalyzer,
        }
    
    def _build_content(self):
        """Build and return the content widget.
        
        Returns:
            Gtk.Box: The content to display in this category
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Analysis Summary section
        summary_section = self._build_summary_section()
        main_box.pack_start(summary_section, False, False, 0)
        
        # 2. Individual analyzer expanders
        analyzer_expanders = self._build_analyzer_expanders()
        main_box.pack_start(analyzer_expanders, True, True, 0)
        
        return main_box
