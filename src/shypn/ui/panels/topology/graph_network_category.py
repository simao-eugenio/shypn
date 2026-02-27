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
from shypn.topology.network.centrality import CentralityAnalyzer
from shypn.topology.network.communities import CommunitiesAnalyzer
from shypn.topology.network.clustering import ClusteringAnalyzer


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
            'centrality': CentralityAnalyzer,
            'communities': CommunitiesAnalyzer,
            'clustering': ClusteringAnalyzer,
        }
    
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
            # Result format: {'cycles': [{nodes: [...], names: [...], length: int, type: str}]}
            cycles = result.get('cycles', [])
            for i, cycle in enumerate(cycles, 1):
                nodes = cycle.get('nodes', [])
                names = cycle.get('names', [])
                cycle_type = cycle.get('type', 'unknown')
                place_count = cycle.get('place_count', 0)
                transition_count = cycle.get('transition_count', 0)
                
                # Use names if available
                nodes_str = '→'.join(names) if names else '→'.join(map(str, nodes))
                
                properties = f'{cycle_type}, P:{place_count} T:{transition_count}'
                
                # Determine significance based on length
                sig = 'High' if len(nodes) > 6 else 'Medium' if len(nodes) > 3 else 'Low'
                
                rows.append((
                    'Cycle',
                    f'Cycle_{i}',
                    len(nodes),
                    nodes_str,
                    properties,
                    sig
                ))
        
        elif analyzer_name == 'paths':
            # Result format: {'paths': [{nodes: [...], names: [...], length: int, type: str}]}
            paths = result.get('paths', [])
            for i, path in enumerate(paths, 1):
                nodes = path.get('nodes', [])
                names = path.get('names', [])
                path_type = path.get('type', 'path')
                
                # Use names if available
                nodes_str = '→'.join(names) if names else '→'.join(map(str, nodes))
                
                properties = path_type.replace('_', ' ').title()
                
                # Longest paths have higher significance
                sig = 'High' if 'longest' in path_type.lower() else 'Medium' if len(nodes) > 5 else 'Low'
                
                rows.append((
                    'Path',
                    f'Path_{i}',
                    len(nodes),
                    nodes_str,
                    properties,
                    sig
                ))
        
        elif analyzer_name == 'hubs':
            # Result format: {'hubs': [{id: int, name: str, type: str, degree: int, in_degree: int, out_degree: int}]}
            hubs = result.get('hubs', [])
            for hub in hubs:
                node_id = hub.get('id', '')
                name = hub.get('name', str(node_id))
                node_type = hub.get('type', 'unknown')
                degree = hub.get('degree', 0)
                in_deg = hub.get('in_degree', 0)
                out_deg = hub.get('out_degree', 0)
                
                properties = f"{node_type.title()}, In/Out={in_deg}/{out_deg}"
                sig = 'High' if degree > 10 else 'Medium' if degree > 5 else 'Low'
                
                rows.append((
                    'Hub',
                    f'Hub_{name}',
                    degree,
                    name,
                    properties,
                    sig
                ))
        
        elif analyzer_name == 'centrality':
            # Result format: {'measures': {measure_name: {node_id: score}}, 'top_nodes': {measure: [nodes]}}
            top_nodes = result.get('top_nodes', {})
            for measure_name, nodes in top_nodes.items():
                for i, node_info in enumerate(nodes[:10], 1):  # Top 10 per measure
                    node_id = node_info.get('id', '')
                    name = node_info.get('name', str(node_id))
                    score = node_info.get('score', 0.0)
                    node_type = node_info.get('type', 'unknown')
                    
                    properties = f"{measure_name.replace('_', ' ').title()}, {node_type.title()}"
                    sig = 'High' if i <= 3 else 'Medium' if i <= 7 else 'Low'
                    
                    rows.append((
                        'Centrality',
                        f'{measure_name}_{i}',
                        int(score * 100) if score < 1 else int(score),
                        name,
                        properties,
                        sig
                    ))
        
        elif analyzer_name == 'communities':
            # Result format: {'communities': [{id, nodes, size, modularity}], 'modularity': float}
            communities = result.get('communities', [])
            for comm in communities:
                comm_id = comm.get('id', 0)
                size = comm.get('size', 0)
                nodes = comm.get('nodes', [])
                mod = comm.get('modularity_contribution', 0.0)
                
                # Get node names
                node_names = [n.get('name', str(n.get('id', ''))) for n in nodes[:5]]
                nodes_str = ', '.join(node_names)
                if len(nodes) > 5:
                    nodes_str += f' (+{len(nodes)-5} more)'
                
                properties = f"Modularity: {mod:.3f}"
                sig = 'High' if size > 10 else 'Medium' if size > 5 else 'Low'
                
                rows.append((
                    'Community',
                    f'Comm_{comm_id}',
                    size,
                    nodes_str,
                    properties,
                    sig
                ))
        
        elif analyzer_name == 'clustering':
            # Result format: {'clustering': {node_id: coefficient}, 'top_nodes': [nodes], 'global_clustering': float}
            top_nodes = result.get('top_nodes', [])
            global_cc = result.get('global_clustering', 0.0)
            
            # Add global clustering row
            rows.append((
                'Global',
                'Global_Clustering',
                int(global_cc * 100),
                'Network-wide',
                f'Transitivity: {result.get("transitivity", 0.0):.3f}',
                'High' if global_cc > 0.5 else 'Medium' if global_cc > 0.2 else 'Low'
            ))
            
            # Add top clustered nodes
            for i, node_info in enumerate(top_nodes[:10], 1):
                node_id = node_info.get('id', '')
                name = node_info.get('name', str(node_id))
                coeff = node_info.get('clustering', 0.0)
                node_type = node_info.get('type', 'unknown')
                triangles = node_info.get('triangles', 0)
                
                properties = f"{node_type.title()}, Triangles: {triangles}"
                sig = 'High' if coeff > 0.7 else 'Medium' if coeff > 0.4 else 'Low'
                
                rows.append((
                    'Clustering',
                    f'Node_{i}',
                    int(coeff * 100),
                    name,
                    properties,
                    sig
                ))
        
        return rows
