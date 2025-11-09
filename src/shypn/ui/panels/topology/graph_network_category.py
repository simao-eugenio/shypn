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
    
    def __init__(self, model_canvas=None, expanded=False, use_grouped_table=False):
        """Initialize graph & network category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
            use_grouped_table: If True, use grouped table instead of expanders
        """
        super().__init__(
            title="GRAPH & NETWORK ANALYSIS",
            model_canvas=model_canvas,
            expanded=expanded,
            use_grouped_table=use_grouped_table
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
        if self.use_grouped_table:
            return self._build_grouped_table()
        
        # Default: individual expanders (old mode)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Analysis Summary section
        summary_section = self._build_summary_section()
        main_box.pack_start(summary_section, False, False, 0)
        
        # 2. Individual analyzer expanders
        analyzer_expanders = self._build_analyzer_expanders()
        main_box.pack_start(analyzer_expanders, True, True, 0)
        
        return main_box
    
    def _define_table_columns(self):
        """Define columns for graph properties grouped table.
        
        Returns:
            list: List of (column_name, column_type) tuples
        """
        return [
            ('Type', str),              # Cycle, Path, Hub
            ('ID', str),                # Cycle_1, Path_1, Hub_p5
            ('Length/Degree', int),     # Path length or hub degree
            ('Nodes', str),             # Node sequence or hub name
            ('Properties', str),        # Simple/Elementary, etc.
            ('Significance', str),      # High/Medium/Low
        ]
    
    def _format_analyzer_row(self, analyzer_name, result):
        """Format graph analyzer result as table rows.
        
        Args:
            analyzer_name: Name of analyzer (cycles, paths, hubs)
            result: Analysis result data
        
        Returns:
            list: List of row tuples
        """
        rows = []
        
        if analyzer_name == 'cycles':
            # Result format: {'cycles': [{nodes: [...], properties: {...}}]}
            cycles = result.get('cycles', [])
            for i, cycle in enumerate(cycles, 1):
                nodes = cycle.get('nodes', [])
                props = cycle.get('properties', {})
                
                prop_list = []
                if props.get('simple', False):
                    prop_list.append('Simple')
                if props.get('elementary', False):
                    prop_list.append('Elementary')
                
                # Determine significance based on length
                sig = 'High' if len(nodes) > 6 else 'Medium' if len(nodes) > 3 else 'Low'
                
                rows.append((
                    'Cycle',
                    f'Cycle_{i}',
                    len(nodes),
                    '→'.join(nodes),
                    ', '.join(prop_list) if prop_list else '-',
                    sig
                ))
        
        elif analyzer_name == 'paths':
            # Result format: {'paths': [{nodes: [...], properties: {...}}]}
            paths = result.get('paths', [])
            for i, path in enumerate(paths, 1):
                nodes = path.get('nodes', [])
                props = path.get('properties', {})
                
                prop_list = []
                if props.get('longest', False):
                    prop_list.append('Longest')
                if props.get('critical', False):
                    prop_list.append('Critical')
                
                sig = 'High' if props.get('critical') else 'Medium' if len(nodes) > 5 else 'Low'
                
                rows.append((
                    'Path',
                    f'Path_{i}',
                    len(nodes),
                    '→'.join(nodes),
                    ', '.join(prop_list) if prop_list else '-',
                    sig
                ))
        
        elif analyzer_name == 'hubs':
            # Result format: {'hubs': [{node: str, degree: int, in_degree: int, out_degree: int, type: str}]}
            hubs = result.get('hubs', [])
            for hub in hubs:
                node = hub.get('node', '')
                degree = hub.get('degree', 0)
                in_deg = hub.get('in_degree', 0)
                out_deg = hub.get('out_degree', 0)
                node_type = hub.get('type', 'unknown')
                
                properties = f"{node_type.title()}, In/Out={in_deg}/{out_deg}"
                sig = 'High' if degree > 10 else 'Medium' if degree > 5 else 'Low'
                
                rows.append((
                    'Hub',
                    f'Hub_{node}',
                    degree,
                    node,
                    properties,
                    sig
                ))
        
        return rows
