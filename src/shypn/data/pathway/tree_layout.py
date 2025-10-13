"""
Tree-Based Hierarchical Layout - Simple Binary Tree Approach

Treats biochemical pathways as trees/forests where:
- Each species is a node
- Each reaction creates edges between nodes
- Children are positioned directly below parents
- Siblings spread horizontally with fixed spacing

Algorithm:
1. Build tree structure (identify roots, branches, leaves)
2. Position nodes vertically (parent → child)
3. Spread siblings horizontally with equal spacing
4. Center each parent above its children

This creates clean vertical layouts where:
- Single chains stay vertical (same X coordinate)
- Branching spreads horizontally with fixed spacing
- Tree grows straight down (no oblique angles)
- Simple and predictable structure

Coordinate System:
- Conceptually: Cartesian coordinates with origin at lower-left, Y grows upward
- Implementation: Graphics coordinates with origin at top-left, Y grows downward
- See doc/COORDINATE_SYSTEM.md for complete details
- In this file: Y increases = visual descent = pathway progression

Author: Shypn Development Team
Date: October 2025
"""

import logging
import math
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from .pathway_data import PathwayData, ProcessedPathwayData, Species, Reaction


class TreeNode:
    """Represents a node in the pathway tree structure."""
    
    def __init__(self, species_id: str, layer: int):
        self.species_id = species_id
        self.layer = layer  # Depth in tree
        self.children: List['TreeNode'] = []
        self.parent: Optional['TreeNode'] = None
        self.aperture_angle: float = 0.0  # Total angular spread for children (radians)
        self.my_angle: float = 0.0  # My angle relative to parent (radians)
        self.x: float = 0.0
        self.y: float = 0.0
        
    def add_child(self, child: 'TreeNode'):
        """Add a child node."""
        self.children.append(child)
        child.parent = self
    
    def is_leaf(self) -> bool:
        """Check if node is a leaf (no children)."""
        return len(self.children) == 0
    
    def is_root(self) -> bool:
        """Check if node is a root (no parent)."""
        return self.parent is None


class TreeLayoutProcessor:
    """
    Layout processor using tree structure and aperture angles.
    
    Dynamically calculates spacing based on pathway branching:
    - Narrow angle for linear chains
    - Wide angle for branching points
    - Natural spreading for complex structures
    """
    
    def __init__(self, pathway: PathwayData, 
                 base_vertical_spacing: float = 150.0,
                 base_aperture_angle: float = 45.0,
                 min_horizontal_spacing: float = 150.0):
        """Initialize tree-based layout processor.
        
        Args:
            pathway: Pathway data
            base_vertical_spacing: Base distance between layers
            base_aperture_angle: Default aperture angle in degrees
            min_horizontal_spacing: Minimum spacing between siblings (increased for visibility)
        """
        self.pathway = pathway
        self.base_vertical_spacing = base_vertical_spacing
        self.base_aperture_angle = math.radians(base_aperture_angle)
        self.min_horizontal_spacing = min_horizontal_spacing
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate_tree_layout(self) -> Dict[str, Tuple[float, float]]:
        """Calculate positions using tree structure and aperture angles.
        
        Returns:
            Dictionary {species_id: (x, y)} with tree-based layout
        """
        self.logger.info("Calculating tree-based layout with aperture angles...")
        
        # Step 1: Build dependency graph and assign layers
        graph, in_degree = self._build_dependency_graph()
        layers = self._assign_layers(graph, in_degree)
        
        # Step 2: Build tree structure
        trees = self._build_trees(layers, graph)
        
        # Step 3: Skip aperture angle calculation (using simple binary tree layout)
        # self._calculate_aperture_angles(trees)
        
        # Step 4: Position nodes using simple vertical tree layout
        positions = self._position_trees(trees)
        
        # Step 5: Position reactions between species
        reaction_positions = self._position_reactions(positions)
        positions.update(reaction_positions)
        
        self.logger.info(f"Tree layout complete: {len(trees)} trees, {len(layers)} layers")
        return positions
    
    def _build_dependency_graph(self) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Build directed graph of species dependencies."""
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for species in self.pathway.species:
            in_degree[species.id] = 0
        
        for reaction in self.pathway.reactions:
            reactants = [species_id for species_id, _ in reaction.reactants]
            products = [species_id for species_id, _ in reaction.products]
            
            for reactant_id in reactants:
                for product_id in products:
                    if reactant_id != product_id:
                        graph[reactant_id].append(product_id)
                        in_degree[product_id] += 1
        
        return dict(graph), dict(in_degree)
    
    def _assign_layers(self, graph: Dict[str, List[str]], 
                      in_degree: Dict[str, int]) -> List[List[str]]:
        """Assign species to layers using topological sort."""
        layers = []
        current_layer = []
        
        queue = deque()
        for species_id, degree in in_degree.items():
            if degree == 0:
                queue.append(species_id)
                current_layer.append(species_id)
        
        if not current_layer:
            # Fallback: all species in one layer
            return [[species.id for species in self.pathway.species]]
        
        layers.append(current_layer)
        
        while queue:
            next_layer = []
            layer_size = len(queue)
            
            for _ in range(layer_size):
                current_id = queue.popleft()
                
                for dependent_id in graph.get(current_id, []):
                    in_degree[dependent_id] -= 1
                    
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)
                        next_layer.append(dependent_id)
            
            if next_layer:
                layers.append(next_layer)
        
        # Handle cycles
        unprocessed = [sid for sid, deg in in_degree.items() if deg > 0]
        if unprocessed:
            if layers:
                layers[-1].extend(unprocessed)
            else:
                layers.append(unprocessed)
        
        return layers
    
    def _build_trees(self, layers: List[List[str]], 
                    graph: Dict[str, List[str]]) -> List[TreeNode]:
        """Build tree structures from layers and graph.
        
        IMPORTANT: Biochemical pathways are DAGs (can have multiple parents),
        not strict trees. We build a tree approximation by:
        1. Tracking ALL parents (for layer validation)
        2. Using FIRST parent as primary for positioning
        3. Adjusting positions based on all incoming/outgoing connections
        
        Returns:
            List of root nodes (forest if multiple roots)
        """
        # Create nodes for all species
        nodes: Dict[str, TreeNode] = {}
        for layer_idx, layer_species in enumerate(layers):
            for species_id in layer_species:
                nodes[species_id] = TreeNode(species_id, layer_idx)
        
        # Build parent-child relationships
        roots = []
        for species_id, node in nodes.items():
            children_ids = graph.get(species_id, [])
            
            if not children_ids:
                # This is a leaf node
                pass
            else:
                # Add children
                for child_id in children_ids:
                    if child_id in nodes:
                        child_node = nodes[child_id]
                        
                        # Only add as child if it doesn't already have a parent
                        if child_node.parent is None:
                            node.add_child(child_node)
            
            # If no parent, it's a root
            if node.parent is None and node.layer == 0:
                roots.append(node)
        
        # If no roots found, use all layer 0 nodes
        if not roots:
            roots = [node for node in nodes.values() if node.layer == 0]
        
        return roots
    
    def _calculate_aperture_angles(self, roots: List[TreeNode]):
        """Calculate aperture angles for each node based on branching.
        
        The aperture angle determines how wide the fan-out is.
        
        CRITICAL RULES:
        1. Parent's aperture angle is translated to space for children
        2. Each child gets an angular slice within parent's aperture
        3. Children's positions respect their angular constraints
        4. **SIBLINGS COORDINATION**: Sibling with most children determines aperture
           for ALL siblings at that level (layer coordination)
        
        The magnitude of the angle is guided by:
        1. Number of children at each bifurcation
        2. Required horizontal distance to separate siblings
        3. Parent's angular constraints (inherited cone)
        4. Maximum branching factor among siblings (coordination)
        """
        def calculate_base_aperture(num_children: int) -> float:
            """Calculate aperture angle based on locality and natural spacing.
            
            LOCALITY PRINCIPLE: Each node determines its aperture based only on
            its immediate children count and spacing requirements. The effect
            propagates downstream naturally through angular inheritance (Rule 1).
            
            For oblique tree visualization:
            - Use moderate angles (15-30° per child) for natural appearance
            - Each level spreads horizontally relative to parent
            - Creates clear hierarchical flow with oblique branches
            
            The aperture grows with num_children but uses reasonable angles
            to maintain clear vertical hierarchy while showing horizontal spread.
            """
            if num_children <= 1:
                return 0.0
            
            # Use SMALL angles for steep vertical descent with Y depth
            # With 150px vertical spacing:
            #   4° → ~10px offset each side → ~20px natural spacing (min=30px enforced)
            #   This creates ~84° angle from horizontal (steep descent with good spacing)
            if num_children <= 3:
                angle_per_child_deg = 4.0  # Small angles for steep vertical tree
            else:
                angle_per_child_deg = 3.5  # Even smaller for higher branching
            
            # Total aperture: angle × number of gaps between children
            aperture_deg = angle_per_child_deg * (num_children - 1)
            
            # Cap at 170° to avoid tan() domain violation
            # This ensures all child angles stay within (-85°, +85°)
            MAX_APERTURE_DEG = 170.0
            safe_aperture_deg = min(aperture_deg, MAX_APERTURE_DEG)
            
            return math.radians(safe_aperture_deg)
        
        def coordinate_siblings_aperture(parent: TreeNode):
            """Coordinate aperture angles among siblings.
            
            COORDINATION RULE: The sibling with the most children determines
            the aperture angle for ALL siblings at this level.
            
            This ensures visual consistency within each layer.
            """
            if not parent.children:
                return
            
            # Find maximum number of children among all siblings
            max_children_count = 0
            for sibling in parent.children:
                num_grandchildren = len(sibling.children)
                if num_grandchildren > max_children_count:
                    max_children_count = num_grandchildren
            
            # Calculate coordinated aperture based on maximum branching
            coordinated_aperture = calculate_base_aperture(max_children_count)
            
            # Apply coordinated aperture to ALL siblings
            for sibling in parent.children:
                if len(sibling.children) > 0:
                    # This sibling has children, use coordinated aperture
                    sibling.aperture_angle = coordinated_aperture
                else:
                    # Leaf node, no aperture needed
                    sibling.aperture_angle = 0.0
        
        def traverse_and_coordinate(node: TreeNode):
            """Traverse tree, coordinate siblings, then recurse.
            
            Process:
            1. Look at this node's children (siblings to each other)
            2. Find max branching factor among those siblings
            3. Set coordinated aperture for all siblings
            4. Recurse to next level
            """
            if node.children:
                # Coordinate aperture angles among this node's children
                coordinate_siblings_aperture(node)
                
                # Recurse to next level
                for child in node.children:
                    traverse_and_coordinate(child)
        
        # Start from each root
        for root in roots:
            # Calculate root's own aperture (not coordinated with other roots)
            root.aperture_angle = calculate_base_aperture(len(root.children))
            
            # Coordinate descendants
            traverse_and_coordinate(root)
    
    def _position_trees(self, roots: List[TreeNode]) -> Dict[str, Tuple[float, float]]:
        """Position nodes using aperture angles and tree structure.
        
        Uses angular positioning where each child is placed at an angle
        relative to its parent, creating natural spreading.
        
        Root nodes start at angle 0 (vertical downward).
        """
        positions = {}
        
        # Canvas parameters
        canvas_center_x = 400.0
        start_y = 100.0
        min_tree_gap = 100.0  # Minimum gap between trees
        
        # First pass: calculate width of each tree
        tree_widths = []
        for root in roots:
            width = self._calculate_subtree_width(root)
            tree_widths.append(width)
            self.logger.debug(f"Tree '{root.species_id}' calculated width: {width:.1f}px")
        
        # Position each tree (forest)
        tree_offset = 0.0
        
        for tree_idx, root in enumerate(roots):
            tree_width = tree_widths[tree_idx]
            
            # Calculate horizontal offset for this tree
            # First tree: center at canvas_center_x
            # Subsequent trees: offset by previous tree's half-width + gap + this tree's half-width
            if tree_idx == 0:
                tree_center_x = canvas_center_x
            else:
                prev_half_width = tree_widths[tree_idx - 1] / 2
                curr_half_width = tree_width / 2
                tree_offset += prev_half_width + min_tree_gap + curr_half_width
                tree_center_x = canvas_center_x + tree_offset
            
            # Position root
            root.x = tree_center_x
            root.y = start_y
            root.my_angle = 0.0  # Root starts at vertical (0 radians)
            positions[root.species_id] = (root.x, root.y)
            
            # Position descendants
            self._position_subtree(root, positions, tree_center_x)
        
        return positions
    
    def _position_subtree(self, node: TreeNode, positions: Dict[str, Tuple[float, float]],
                         parent_x: float):
        """Recursively position a subtree using simple binary tree layout.
        
        Children are positioned directly below parent with fixed horizontal spacing:
        - Single child: centered below parent (same X)
        - Multiple children: spread evenly with fixed spacing, centered on parent
        
        This creates a clean vertical tree structure without oblique angles.
        """
        if not node.children:
            return
        
        num_children = len(node.children)
        
        # Calculate Y position for children (next layer DOWN in graphics coords)
        # COORDINATE SYSTEM NOTE:
        # - Graphics: Y increases downward (Cairo/GTK standard)
        # - Conceptual: Y growth = pathway descent/progression
        # - child_y > parent_y means "child is below parent" visually
        # - child_y > parent_y means "child at higher Y value" mathematically
        # Both interpretations are consistent: increasing Y = descended child
        child_y = node.y + self.base_vertical_spacing
        
        if num_children == 1:
            # Single child: place directly below parent (same X, increasing Y)
            child = node.children[0]
            child.x = node.x
            child.y = child_y
            positions[child.species_id] = (child.x, child.y)
            
            # Recurse
            self._position_subtree(child, positions, child.x)
            
        else:
            # Multiple children: First, recursively calculate subtree widths
            # Then position children left-to-right with proper spacing
            
            # Calculate width needed for each child's subtree
            child_widths = []
            for child in node.children:
                width = self._calculate_subtree_width(child)
                child_widths.append(max(width, self.min_horizontal_spacing))
            
            # Calculate total width needed
            total_width = sum(child_widths)
            
            # Start position (leftmost child center)
            start_x = node.x - total_width / 2
            
            # Position each child
            current_x = start_x
            for i, child in enumerate(node.children):
                # Place child at center of its allocated width
                child.x = current_x + child_widths[i] / 2
                child.y = child_y
                
                # Validation: check for unreasonable coordinates
                if child.x < -1000 or child.x > 10000:
                    self.logger.warning(
                        f"Unusual X coordinate for '{child.species_id}': {child.x:.1f} "
                        f"(parent at {node.x:.1f}, child_width={child_widths[i]:.1f})"
                    )
                
                positions[child.species_id] = (child.x, child.y)
                
                # Move to next child's position
                current_x += child_widths[i]
            
            # Now recurse for each child's subtree
            for child in node.children:
                self._position_subtree(child, positions, child.x)
    
    def _calculate_subtree_width(self, node: TreeNode) -> float:
        """Calculate the width needed for a subtree.
        
        Returns the minimum horizontal space needed to layout this node
        and all its descendants without overlap.
        """
        if not node.children:
            # Leaf node: needs minimum spacing
            return self.min_horizontal_spacing
        
        # Has children: width is sum of children's widths
        child_widths = []
        for child in node.children:
            width = self._calculate_subtree_width(child)
            child_widths.append(max(width, self.min_horizontal_spacing))
        
        return sum(child_widths)
    
    def _position_reactions(self, species_positions: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
        """Position reactions between their reactants and products.
        
        Simple midpoint positioning:
        1. Calculate average position of all reactants
        2. Calculate average position of all products
        3. Place reaction at midpoint between reactant center and product center
        
        This creates clean vertical tree structure.
        """
        reaction_positions = {}
        
        for reaction in self.pathway.reactions:
            reactant_coords = []
            product_coords = []
            missing_reactants = []
            missing_products = []
            
            # Collect reactant positions
            for species_id, _ in reaction.reactants:
                if species_id in species_positions:
                    reactant_coords.append(species_positions[species_id])
                else:
                    missing_reactants.append(species_id)
            
            # Collect product positions
            for species_id, _ in reaction.products:
                if species_id in species_positions:
                    product_coords.append(species_positions[species_id])
                else:
                    missing_products.append(species_id)
            
            # Warn about missing species
            if missing_reactants:
                self.logger.warning(
                    f"Reaction '{reaction.id}' missing reactant positions: {missing_reactants}"
                )
            if missing_products:
                self.logger.warning(
                    f"Reaction '{reaction.id}' missing product positions: {missing_products}"
                )
            
            if reactant_coords and product_coords:
                # Calculate average reactant position
                reactant_x = sum(x for x, y in reactant_coords) / len(reactant_coords)
                reactant_y = sum(y for x, y in reactant_coords) / len(reactant_coords)
                
                # Calculate average product position
                product_x = sum(x for x, y in product_coords) / len(product_coords)
                product_y = sum(y for x, y in product_coords) / len(product_coords)
                
                # For X: use average of reactants and products
                reaction_x = (reactant_x + product_x) / 2
                
                # For Y: Use layer-aware positioning
                # If reactants and products are at different layers, place reaction
                # at the LAYER BOUNDARY between them (not average of actual Y values)
                # This ensures reactions align with the grid structure
                
                # Find the min/max Y among all reactants and products
                all_y_coords = [y for x, y in reactant_coords] + [y for x, y in product_coords]
                min_y = min(all_y_coords)
                max_y = max(all_y_coords)
                
                # If all on same layer (within tolerance), place reaction below
                if max_y - min_y < self.base_vertical_spacing * 0.5:
                    # All species roughly at same layer
                    reaction_y = reactant_y + self.base_vertical_spacing / 2
                else:
                    # Species span multiple layers - use midpoint between min and max
                    reaction_y = (min_y + max_y) / 2
                
                reaction_positions[reaction.id] = (reaction_x, reaction_y)
                
            elif reactant_coords:
                # Only reactants: place reaction below them
                avg_x = sum(x for x, y in reactant_coords) / len(reactant_coords)
                avg_y = sum(y for x, y in reactant_coords) / len(reactant_coords)
                reaction_positions[reaction.id] = (avg_x, avg_y + self.base_vertical_spacing / 2)
                
            elif product_coords:
                # Only products: place reaction above them
                avg_x = sum(x for x, y in product_coords) / len(product_coords)
                avg_y = sum(y for x, y in product_coords) / len(product_coords)
                reaction_positions[reaction.id] = (avg_x, avg_y - self.base_vertical_spacing / 2)
                
            else:
                # No valid connections: use default position
                # Log warning so user knows there's an issue
                self.logger.warning(
                    f"Reaction '{reaction.id}' has no valid connections, "
                    f"using fallback position (400.0, 300.0)"
                )
                reaction_positions[reaction.id] = (400.0, 300.0)
        
        return reaction_positions
