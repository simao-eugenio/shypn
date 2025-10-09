"""
Circular Layout Algorithm

Implements circular arrangement for cyclic pathways.
Best for pathways with prominent cycles (TCA, Calvin cycle, urea cycle).

Based on:
    Six & Tollis (1999) - "A framework for circular drawings of networks"
    
Algorithm:
    1. Detect main cycle in the graph
    2. Arrange cycle nodes on a circle
    3. Place non-cycle nodes outside the circle using force-directed
    4. Optionally arrange in concentric rings for complex cycles
"""

from typing import Dict, Tuple, List, Optional
import networkx as nx
import math
from .base import LayoutAlgorithm
from .force_directed import ForceDirectedLayout


class CircularLayout(LayoutAlgorithm):
    """
    Circular layout for cyclic pathways.
    
    Arranges main cycle nodes on a circle, with branches placed outside.
    Emphasizes cyclic structure and metabolic loops.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Circular Layout"
        self.description = "Circular arrangement for cyclic pathways"
        self.best_for = "Cyclic pathways (TCA cycle, Calvin cycle, urea cycle)"
    
    def compute(
        self,
        graph: nx.DiGraph,
        radius: float = 300.0,
        center: Tuple[float, float] = (0.0, 0.0),
        arrange_branches: bool = True,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute circular layout positions.
        
        Args:
            graph: NetworkX directed graph
            radius: Radius of the main circle
            center: Center point of the circle
            arrange_branches: If True, use force-directed for branch nodes
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        if graph.number_of_nodes() == 1:
            # Single node at center
            return {list(graph.nodes())[0]: center}
        
        # Find main cycle
        main_cycle = self.find_main_cycle(graph)
        
        if not main_cycle:
            # No cycle found, fall back to simple circular arrangement
            return self._simple_circular(graph, radius, center)
        
        # Arrange cycle nodes on circle
        positions = self._arrange_cycle_on_circle(main_cycle, radius, center)
        
        # Handle non-cycle nodes
        cycle_set = set(main_cycle)
        non_cycle_nodes = [n for n in graph.nodes() if n not in cycle_set]
        
        if non_cycle_nodes and arrange_branches:
            # Use force-directed for branches, keeping cycle fixed
            branch_positions = self._arrange_branches(
                graph,
                non_cycle_nodes,
                positions,
                radius
            )
            positions.update(branch_positions)
        elif non_cycle_nodes:
            # Simple radial placement
            for i, node in enumerate(non_cycle_nodes):
                angle = (2 * math.pi * i) / len(non_cycle_nodes)
                r = radius * 1.5  # Outside main circle
                x = center[0] + r * math.cos(angle)
                y = center[1] + r * math.sin(angle)
                positions[node] = (x, y)
        
        return positions
    
    def _simple_circular(
        self,
        graph: nx.DiGraph,
        radius: float,
        center: Tuple[float, float]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Simple circular arrangement of all nodes.
        Used when no cycle is detected.
        """
        nodes = list(graph.nodes())
        n = len(nodes)
        
        positions = {}
        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / n
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            positions[node] = (x, y)
        
        return positions
    
    def _arrange_cycle_on_circle(
        self,
        cycle: List[str],
        radius: float,
        center: Tuple[float, float]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Arrange cycle nodes evenly on a circle.
        
        Args:
            cycle: List of node IDs forming the cycle
            radius: Circle radius
            center: Circle center
            
        Returns:
            Positions for cycle nodes
        """
        positions = {}
        n = len(cycle)
        
        for i, node in enumerate(cycle):
            # Evenly space around circle
            angle = (2 * math.pi * i) / n
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            positions[node] = (x, y)
        
        return positions
    
    def _arrange_branches(
        self,
        graph: nx.DiGraph,
        branch_nodes: List[str],
        fixed_positions: Dict[str, Tuple[float, float]],
        inner_radius: float
    ) -> Dict[str, Tuple[float, float]]:
        """
        Arrange branch nodes outside the main cycle using force-directed.
        
        Args:
            graph: Full graph
            branch_nodes: Nodes not in main cycle
            fixed_positions: Fixed positions for cycle nodes
            inner_radius: Radius of main cycle (branches go outside)
            
        Returns:
            Positions for branch nodes
        """
        # Create subgraph including branches and their connections to cycle
        subgraph_nodes = set(branch_nodes) | set(fixed_positions.keys())
        subgraph = graph.subgraph(subgraph_nodes)
        
        # Use force-directed layout with cycle nodes fixed
        force_layout = ForceDirectedLayout()
        
        # Scale for branch area (ring around cycle)
        scale = inner_radius * 3  # Branches go up to 3x radius
        
        all_positions = force_layout.compute_with_fixed_nodes(
            subgraph,
            fixed_positions,
            scale=scale
        )
        
        # Extract only branch positions
        branch_positions = {
            node: pos for node, pos in all_positions.items()
            if node in branch_nodes
        }
        
        return branch_positions
    
    def compute_concentric(
        self,
        graph: nx.DiGraph,
        base_radius: float = 200.0,
        ring_spacing: float = 150.0,
        center: Tuple[float, float] = (0.0, 0.0),
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute concentric circular layout with multiple rings.
        
        Arranges nodes in concentric circles based on their distance
        from the main cycle.
        
        Args:
            graph: NetworkX directed graph
            base_radius: Radius of innermost circle
            ring_spacing: Space between rings
            center: Center point
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Find main cycle
        main_cycle = self.find_main_cycle(graph)
        
        if not main_cycle:
            # No cycle, use simple circular
            return self._simple_circular(graph, base_radius, center)
        
        # Assign nodes to rings based on distance from cycle
        cycle_set = set(main_cycle)
        ring_assignment = {node: 0 for node in main_cycle}  # Ring 0 = main cycle
        
        # BFS to assign other nodes to rings
        current_ring = 0
        processed = set(main_cycle)
        frontier = list(main_cycle)
        
        while frontier:
            next_frontier = []
            current_ring += 1
            
            for node in frontier:
                # Check neighbors (both predecessors and successors)
                neighbors = set(graph.predecessors(node)) | set(graph.successors(node))
                
                for neighbor in neighbors:
                    if neighbor not in processed:
                        ring_assignment[neighbor] = current_ring
                        processed.add(neighbor)
                        next_frontier.append(neighbor)
            
            frontier = next_frontier
        
        # Group nodes by ring
        rings = {}
        for node, ring in ring_assignment.items():
            if ring not in rings:
                rings[ring] = []
            rings[ring].append(node)
        
        # Arrange each ring
        positions = {}
        for ring_idx, ring_nodes in rings.items():
            ring_radius = base_radius + ring_idx * ring_spacing
            ring_positions = self._arrange_cycle_on_circle(
                ring_nodes,
                ring_radius,
                center
            )
            positions.update(ring_positions)
        
        return positions
    
    def compute_with_subcycles(
        self,
        graph: nx.DiGraph,
        radius: float = 300.0,
        center: Tuple[float, float] = (0.0, 0.0),
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute layout for graphs with multiple cycles.
        
        Places largest cycle in center, smaller cycles around it.
        
        Args:
            graph: NetworkX directed graph
            radius: Base radius
            center: Center point
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Find all cycles
        try:
            all_cycles = list(nx.simple_cycles(graph))
        except:
            all_cycles = []
        
        if not all_cycles:
            return self._simple_circular(graph, radius, center)
        
        # Sort by length (largest first)
        all_cycles.sort(key=len, reverse=True)
        
        # Main cycle in center
        main_cycle = all_cycles[0]
        positions = self._arrange_cycle_on_circle(main_cycle, radius, center)
        
        # Place other cycles around the main one
        main_cycle_set = set(main_cycle)
        processed = main_cycle_set.copy()
        
        for i, cycle in enumerate(all_cycles[1:], start=1):
            # Skip if cycle overlaps with already processed nodes
            cycle_set = set(cycle)
            if cycle_set & processed:
                continue
            
            # Place this cycle at distance from center
            angle = (2 * math.pi * i) / len(all_cycles)
            distance = radius * 2
            cycle_center = (
                center[0] + distance * math.cos(angle),
                center[1] + distance * math.sin(angle)
            )
            
            # Arrange cycle nodes
            cycle_radius = radius * 0.5  # Smaller cycles
            cycle_positions = self._arrange_cycle_on_circle(
                cycle,
                cycle_radius,
                cycle_center
            )
            
            positions.update(cycle_positions)
            processed.update(cycle_set)
        
        # Handle remaining nodes with force-directed
        remaining = [n for n in graph.nodes() if n not in processed]
        if remaining:
            branch_positions = self._arrange_branches(
                graph,
                remaining,
                positions,
                radius
            )
            positions.update(branch_positions)
        
        return positions
