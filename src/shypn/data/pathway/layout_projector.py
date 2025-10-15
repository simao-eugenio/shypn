"""
Layout Projector - 2D Projection Post-Processor

Takes force-directed layout results and projects them onto a clean 2D canvas
with proper layering, alignment, and downward flow (substrates top → products bottom).

Coordinate System: Cartesian First Quadrant
- Origin (0,0) at bottom-left
- Y increases upward (coordinate space)
- Visual flow downward (biochemical convention: substrates at top)

Author: Shypn Development Team
Date: October 2025
"""

import logging
import math
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class LayoutProjector:
    """Projects force-directed layout onto organized 2D canvas.
    
    Applies 6-step pipeline:
    1. Flow direction detection
    2. Flip to ensure downward visual flow
    3. Layer detection (Y-clustering)
    4. Layer assignment (top to bottom)
    5. Horizontal alignment and spacing
    6. Canvas fitting and normalization
    """
    
    def __init__(self, 
                 layer_threshold: float = 50.0,  # Increased for better clustering
                 layer_spacing: float = 200.0,    # Increased vertical spacing
                 min_horizontal_spacing: float = 120.0,  # Increased horizontal spacing
                 canvas_width: float = 2000.0,    # Increased canvas width
                 canvas_center_x: float = 1000.0,  # Adjusted center
                 top_margin: float = 800.0,        # Higher top margin
                 left_margin: float = 100.0):      # More left margin
        """Initialize layout projector.
        
        Args:
            layer_threshold: Max Y-distance to group nodes in same layer
            layer_spacing: Vertical distance between layers (downward)
            min_horizontal_spacing: Minimum horizontal spacing between nodes
            canvas_width: Maximum canvas width
            canvas_center_x: Horizontal center point
            top_margin: Y position of top layer (substrates)
            left_margin: X margin from left edge
        """
        self.layer_threshold = layer_threshold
        self.layer_spacing = layer_spacing
        self.min_horizontal_spacing = min_horizontal_spacing
        self.canvas_width = canvas_width
        self.canvas_center_x = canvas_center_x
        self.top_margin = top_margin
        self.left_margin = left_margin
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def project(self, 
                positions: Dict[str, Tuple[float, float]], 
                edges: List[Tuple[str, str]]) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, float]]:
        """Project force-directed positions onto organized 2D canvas.
        
        Args:
            positions: Raw positions from force-directed layout {node_id: (x, y)}
            edges: List of edges [(source_id, target_id)]
            
        Returns:
            Tuple of:
            - Organized positions {node_id: (x, y)} with proper layering
            - Canvas dimensions {'width': float, 'height': float}
        """
        if not positions or not edges:
            self.logger.warning("Empty positions or edges, returning unchanged")
            return positions, {'width': self.canvas_width, 'height': 1000.0}
        
        self.logger.info(f"Projecting {len(positions)} nodes with {len(edges)} edges")
        
        # Step 1: Detect flow direction
        avg_dy = self._detect_flow_direction(edges, positions)
        self.logger.info(f"Flow direction: avg_dy = {avg_dy:.2f} ({'downward ✓' if avg_dy < 0 else 'upward (will flip)'})")
        
        # Step 2: Ensure downward flow (substrates at top)
        positions = self._ensure_downward_flow(positions, avg_dy)
        
        # Step 3: Detect layers by Y-coordinate clustering
        layers = self._detect_layers(positions)
        self.logger.info(f"Detected {len(layers)} layers")
        
        # Step 4: Assign layers from top to bottom with X normalization
        # This now calculates required canvas height
        positions, required_height = self._assign_layers_top_to_bottom(positions, layers)
        
        # Step 5: Fit to canvas bounds
        positions = self._fit_to_canvas(positions)
        
        # Calculate final canvas dimensions
        canvas_dims = {
            'width': self.canvas_width,
            'height': required_height
        }
        
        self.logger.info(f"Projection complete: canvas = {canvas_dims['width']:.0f}x{canvas_dims['height']:.0f}px")
        return positions, canvas_dims
    
    def _detect_flow_direction(self, 
                               edges: List[Tuple[str, str]], 
                               positions: Dict[str, Tuple[float, float]]) -> float:
        """Detect average flow direction (upward or downward).
        
        Args:
            edges: List of edges [(source_id, target_id)]
            positions: Current positions {node_id: (x, y)}
            
        Returns:
            Average dy: negative = downward, positive = upward
        """
        y_deltas = []
        
        for source_id, target_id in edges:
            if source_id not in positions or target_id not in positions:
                continue
            
            source_y = positions[source_id][1]
            target_y = positions[target_id][1]
            dy = target_y - source_y
            y_deltas.append(dy)
        
        if not y_deltas:
            return 0.0
        
        avg_dy = sum(y_deltas) / len(y_deltas)
        return avg_dy
    
    def _ensure_downward_flow(self, 
                              positions: Dict[str, Tuple[float, float]], 
                              avg_dy: float) -> Dict[str, Tuple[float, float]]:
        """Flip coordinates if flow is upward to ensure downward visual flow.
        
        Args:
            positions: Current positions
            avg_dy: Average flow direction
            
        Returns:
            Positions with downward flow (substrates at top, products at bottom)
        """
        if avg_dy > 0:
            # Flow is upward, flip Y coordinates
            self.logger.info("Flipping Y coordinates to ensure downward flow")
            max_y = max(y for x, y in positions.values())
            min_y = min(y for x, y in positions.values())
            
            flipped = {}
            for node_id, (x, y) in positions.items():
                # Flip: new_y = max_y - (y - min_y)
                flipped[node_id] = (x, max_y - y + min_y)
            
            return flipped
        else:
            # Flow already downward
            self.logger.debug("Flow already downward, no flip needed")
            return positions
    
    def _detect_layers(self, 
                       positions: Dict[str, Tuple[float, float]]) -> List[List[str]]:
        """Group nodes into layers by Y-coordinate clustering.
        
        Args:
            positions: Current positions
            
        Returns:
            List of layers, each containing node IDs
            layers[0] = top layer (highest Y)
            layers[-1] = bottom layer (lowest Y)
        """
        # Get all unique Y coordinates, sorted descending (top to bottom)
        y_coords_map = defaultdict(list)
        for node_id, (x, y) in positions.items():
            y_coords_map[y].append(node_id)
        
        sorted_ys = sorted(y_coords_map.keys(), reverse=True)  # Descending
        
        if not sorted_ys:
            return []
        
        # Cluster nearby Y values into layers
        layers = []
        current_layer_nodes = y_coords_map[sorted_ys[0]]
        current_layer_y = sorted_ys[0]
        
        for y in sorted_ys[1:]:
            # If Y is within threshold of current layer, add to it
            if abs(current_layer_y - y) < self.layer_threshold:
                current_layer_nodes.extend(y_coords_map[y])
            else:
                # Start new layer
                layers.append(current_layer_nodes)
                current_layer_nodes = y_coords_map[y]
                current_layer_y = y
        
        # Add final layer
        layers.append(current_layer_nodes)
        
        self.logger.debug(f"Layer sizes: {[len(layer) for layer in layers]}")
        return layers
    
    def _assign_layers_top_to_bottom(self, 
                                      positions: Dict[str, Tuple[float, float]], 
                                      layers: List[List[str]]) -> Tuple[Dict[str, Tuple[float, float]], float]:
        """Assign discrete Y positions to layers, starting from top.
        
        Also normalizes X coordinates within each layer to prevent stretching.
        
        UNSTACKING STRATEGY:
        - Each layer gets its own vertical space
        - Dynamic spacing based on number of layers to ensure visibility
        - Maintains ordering: layers[0] (top/substrates) → layers[-1] (bottom/products)
        
        Args:
            positions: Current positions
            layers: Detected layers (layer[0] = top)
            
        Returns:
            Tuple of:
            - Positions with aligned Y coordinates and normalized X
            - Required canvas height (float)
        """
        aligned = {}
        
        # Calculate dynamic layer spacing to ensure full visibility
        num_layers = len(layers)
        bottom_margin = 50.0  # Space at bottom
        
        # Total vertical space needed
        total_height_needed = self.top_margin + (num_layers * self.layer_spacing) + bottom_margin
        
        self.logger.info(f"Unstacking {num_layers} layers: total_height = {total_height_needed:.1f}px")
        
        for layer_idx, layer_nodes in enumerate(layers):
            # Calculate Y position: top_margin - (layer_idx * spacing)
            # This creates downward flow: layer 0 at top, layer N at bottom
            layer_y = self.top_margin - (layer_idx * self.layer_spacing)
            
            self.logger.debug(f"Layer {layer_idx}: Y={layer_y:.1f}, nodes={len(layer_nodes)}")
            
            # Get X coordinates for this layer and normalize them
            layer_x_coords = []
            for node_id in layer_nodes:
                if node_id in positions:
                    layer_x_coords.append((node_id, positions[node_id][0]))
            
            # Sort by X to maintain relative ordering
            layer_x_coords.sort(key=lambda item: item[1])
            
            # Normalize X coordinates to prevent stretching
            if len(layer_x_coords) == 1:
                # Single node: center it
                node_id = layer_x_coords[0][0]
                aligned[node_id] = (self.canvas_center_x, layer_y)
            else:
                # Multiple nodes: map to bounded range
                raw_x_values = [x for _, x in layer_x_coords]
                min_x = min(raw_x_values)
                max_x = max(raw_x_values)
                x_range = max_x - min_x
                
                if x_range > 0:
                    # Normalize to fit within canvas_width
                    target_width = min((len(layer_x_coords) - 1) * self.min_horizontal_spacing, 
                                     self.canvas_width)
                    start_x = self.canvas_center_x - target_width / 2
                    
                    for i, (node_id, raw_x) in enumerate(layer_x_coords):
                        # Map from raw range to target range
                        normalized_position = (raw_x - min_x) / x_range  # 0 to 1
                        new_x = start_x + normalized_position * target_width
                        aligned[node_id] = (new_x, layer_y)
                else:
                    # All nodes at same X, distribute evenly
                    target_width = min((len(layer_x_coords) - 1) * self.min_horizontal_spacing,
                                     self.canvas_width)
                    start_x = self.canvas_center_x - target_width / 2
                    spacing = target_width / (len(layer_x_coords) - 1) if len(layer_x_coords) > 1 else 0
                    
                    for i, (node_id, _) in enumerate(layer_x_coords):
                        new_x = start_x + i * spacing
                        aligned[node_id] = (new_x, layer_y)
        
        return aligned, total_height_needed
    
    def _fit_to_canvas(self, 
                       positions: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
        """Ensure all coordinates are positive and within canvas bounds.
        
        Args:
            positions: Current positions
            
        Returns:
            Normalized positions in first quadrant
        """
        if not positions:
            return positions
        
        # Find bounds
        min_x = min(x for x, y in positions.values())
        min_y = min(y for x, y in positions.values())
        max_x = max(x for x, y in positions.values())
        max_y = max(y for x, y in positions.values())
        
        self.logger.info(f"Raw bounds: X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}]")
        
        # Calculate offsets to ensure positive coordinates with margins
        offset_x = max(0, self.left_margin - min_x)
        offset_y = max(0, 50 - min_y)  # Bottom margin
        
        # Apply offsets if needed
        if offset_x > 0 or offset_y > 0:
            self.logger.info(f"Applying offset: ({offset_x:.1f}, {offset_y:.1f})")
            normalized = {
                node_id: (x + offset_x, y + offset_y)
                for node_id, (x, y) in positions.items()
            }
        else:
            normalized = positions
        
        # Verify final bounds
        final_min_x = min(x for x, y in normalized.values())
        final_min_y = min(y for x, y in normalized.values())
        final_max_x = max(x for x, y in normalized.values())
        final_max_y = max(y for x, y in normalized.values())
        
        self.logger.info(f"Final bounds: X=[{final_min_x:.1f}, {final_max_x:.1f}], Y=[{final_min_y:.1f}, {final_max_y:.1f}]")
        
        return normalized

    def project_spiral(self, 
                      positions: Dict[str, Tuple[float, float]], 
                      edges: List[Tuple[str, str]],
                      entry_nodes: List[str] = None) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, float]]:
        """Project force-directed positions onto spiral layout.
        
        SPIRAL STRATEGY:
        - Entry point (substrates/sources) at spiral center
        - Products spiral outward following reaction flow
        - Natural directionality: center → periphery
        - Maintains topological distances from force-directed
        
        Args:
            positions: Raw positions from force-directed layout {node_id: (x, y)}
            edges: List of edges [(source_id, target_id)]
            entry_nodes: Optional list of entry point node IDs (auto-detected if None)
            
        Returns:
            Tuple of:
            - Spiral positions {node_id: (x, y)}
            - Canvas dimensions {'width': float, 'height': float}
        """
        if not positions or not edges:
            self.logger.warning("Empty positions or edges, returning unchanged")
            return positions, {'width': self.canvas_width, 'height': self.canvas_width}
        
        self.logger.info(f"Projecting {len(positions)} nodes onto spiral layout")
        
        # Step 1: Find entry points (sources with no incoming edges)
        if entry_nodes is None:
            entry_nodes = self._find_entry_points(edges, positions)
            self.logger.info(f"Auto-detected {len(entry_nodes)} entry points: {entry_nodes}")
        
        # Step 2: Calculate distance from entry for each node (BFS)
        distances = self._calculate_flow_distances(edges, entry_nodes)
        max_distance = max(distances.values()) if distances else 1
        
        self.logger.info(f"Max flow distance: {max_distance}")
        
        # Step 3: Convert force-directed (x,y) to polar (radius, angle)
        # Use distance from entry as radius multiplier
        center_x = self.canvas_width / 2
        center_y = self.canvas_width / 2  # Square canvas for spiral
        spiral_positions = {}
        
        # Group nodes by distance (layers)
        distance_groups = defaultdict(list)
        for node_id, dist in distances.items():
            distance_groups[dist].append(node_id)
        
        # Sort distances
        sorted_distances = sorted(distance_groups.keys())
        
        # Spiral parameters
        spiral_tightness = 0.5  # How fast radius grows
        base_radius = 100.0     # Starting radius for entry nodes
        angle_step = 2 * math.pi / 8  # Base angle step between nodes
        
        cumulative_angle = 0.0  # Track cumulative angle for continuous spiral
        
        for dist_idx, distance in enumerate(sorted_distances):
            nodes_at_distance = distance_groups[distance]
            
            # Calculate radius for this distance tier
            radius = base_radius + (distance * 150.0 * spiral_tightness)
            
            # Distribute nodes at this distance around spiral
            for node_idx, node_id in enumerate(nodes_at_distance):
                # Get original position to maintain relative angular position
                orig_x, orig_y = positions[node_id]
                
                # Calculate angle from original force-directed position
                dx = orig_x - center_x
                dy = orig_y - center_y
                orig_angle = math.atan2(dy, dx)
                
                # Combine spiral progression with original angle
                angle = cumulative_angle + orig_angle
                
                # Convert to Cartesian
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                spiral_positions[node_id] = (x, y)
                
                # Increment angle for next node (creates spiral)
                cumulative_angle += angle_step / len(nodes_at_distance)
        
        # Step 4: Ensure positive coordinates
        min_x = min(x for x, y in spiral_positions.values())
        min_y = min(y for x, y in spiral_positions.values())
        
        offset_x = max(0, self.left_margin - min_x)
        offset_y = max(0, 50 - min_y)
        
        if offset_x > 0 or offset_y > 0:
            spiral_positions = {
                node_id: (x + offset_x, y + offset_y)
                for node_id, (x, y) in spiral_positions.items()
            }
        
        # Calculate canvas dimensions
        max_x = max(x for x, y in spiral_positions.values())
        max_y = max(y for x, y in spiral_positions.values())
        
        canvas_dims = {
            'width': max_x + self.left_margin,
            'height': max_y + 50  # Bottom margin
        }
        
        self.logger.info(f"✓ Spiral projection complete: {canvas_dims['width']:.0f}x{canvas_dims['height']:.0f}px")
        
        return spiral_positions, canvas_dims
    
    def _find_entry_points(self, 
                          edges: List[Tuple[str, str]], 
                          positions: Dict[str, Tuple[float, float]]) -> List[str]:
        """Find entry points (nodes with no incoming edges).
        
        Args:
            edges: List of edges [(source_id, target_id)]
            positions: Node positions
            
        Returns:
            List of entry node IDs
        """
        all_nodes = set(positions.keys())
        target_nodes = set(target for _, target in edges)
        
        # Nodes that are never targets = entry points (sources)
        entry_nodes = all_nodes - target_nodes
        
        if not entry_nodes:
            # Fallback: use nodes with most outgoing edges
            outgoing_counts = defaultdict(int)
            for source, _ in edges:
                outgoing_counts[source] += 1
            
            if outgoing_counts:
                max_outgoing = max(outgoing_counts.values())
                entry_nodes = {node for node, count in outgoing_counts.items() 
                             if count == max_outgoing}
        
        return list(entry_nodes) if entry_nodes else [list(all_nodes)[0]]
    
    def _calculate_flow_distances(self, 
                                  edges: List[Tuple[str, str]], 
                                  entry_nodes: List[str]) -> Dict[str, int]:
        """Calculate distance from entry points using BFS.
        
        Args:
            edges: List of edges [(source_id, target_id)]
            entry_nodes: List of entry node IDs
            
        Returns:
            Dictionary {node_id: distance_from_entry}
        """
        # Build adjacency list
        graph = defaultdict(list)
        for source, target in edges:
            graph[source].append(target)
        
        # BFS from all entry nodes
        distances = {}
        queue = [(node, 0) for node in entry_nodes]
        
        for node in entry_nodes:
            distances[node] = 0
        
        while queue:
            current, dist = queue.pop(0)
            
            for neighbor in graph[current]:
                if neighbor not in distances:
                    distances[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))
        
        return distances
