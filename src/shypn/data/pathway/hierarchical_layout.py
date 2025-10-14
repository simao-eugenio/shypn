"""
Hierarchical Layout Processor for Biochemical Pathways

Uses reaction ordering and precursor-product relationships to create
a hierarchical top-to-bottom layout preferred by biochemists.

Key Concepts:
1. Reactions have dependencies (precursor → product)
2. Species can be ranked by their depth in reaction chain
3. Vertical layout shows flow clearly
4. Horizontal grouping by pathway branches

Two layout modes:
- FIXED: Equal spacing within layers (current default)
- TREE: Aperture angle-based spacing (adaptive to branching)

Algorithm:
1. Build dependency graph (which reactions depend on which species)
2. Calculate "layer" for each species (topological sort)
3. Position layers vertically (top = inputs, bottom = outputs)
4. Position species horizontally (fixed spacing or tree-based angles)

Coordinate System:
- Conceptually: Cartesian coordinates (origin lower-left, Y grows up)
- Implementation: Graphics coordinates (origin top-left, Y grows down)
- See doc/COORDINATE_SYSTEM.md for details
- Result: Increasing Y values = visual descent = pathway flow

Author: Shypn Development Team
Date: October 2025
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from .pathway_data import PathwayData, ProcessedPathwayData, Species, Reaction


class HierarchicalLayoutProcessor:
    """
    Creates hierarchical top-to-bottom layout for metabolic pathways.
    
    Positions species in layers based on reaction dependencies,
    creating a clear flow from substrates to products.
    """
    
    def __init__(self, pathway: PathwayData, vertical_spacing: float = 150.0, 
                 horizontal_spacing: float = 100.0):
        """Initialize hierarchical layout processor.
        
        Args:
            pathway: Pathway data with species and reactions
            vertical_spacing: Distance between layers (vertical)
            horizontal_spacing: Distance between species in same layer
        """
        self.pathway = pathway
        self.vertical_spacing = vertical_spacing
        self.horizontal_spacing = horizontal_spacing
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate_hierarchical_layout(self) -> Dict[str, Tuple[float, float]]:
        """Calculate hierarchical positions for all species.
        
        Returns:
            Dictionary {species_id: (x, y)} with hierarchical layout
        """
        self.logger.info("Calculating hierarchical layout...")
        
        # Step 1: Build dependency graph
        graph, in_degree = self._build_dependency_graph()
        
        # Step 2: Assign layers using topological sort (Kahn's algorithm)
        layers = self._assign_layers(graph, in_degree)
        
        # Step 3: Position species in layers
        positions = self._position_layers(layers)
        
        # Step 4: Position reactions between layers
        reaction_positions = self._position_reactions(positions)
        positions.update(reaction_positions)
        
        # Step 5: Validate and normalize coordinates (ensure all positive)
        positions = self._normalize_coordinates(positions)
        
        self.logger.info(f"Hierarchical layout complete: {len(layers)} layers, {len(positions)} positioned")
        return positions
    
    def _normalize_coordinates(self, positions: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
        """Ensure all coordinates are positive by shifting if needed.
        
        Args:
            positions: Raw positions that may contain negative coordinates
            
        Returns:
            Normalized positions with all positive coordinates
        """
        if not positions:
            return positions
        
        # Find minimum coordinates
        min_x = min(x for x, y in positions.values())
        min_y = min(y for x, y in positions.values())
        max_x = max(x for x, y in positions.values())
        max_y = max(y for x, y in positions.values())
        
        # DEBUG: Always log coordinate ranges
        self.logger.warning(f"🔍 HIERARCHICAL LAYOUT COORDINATES BEFORE NORMALIZATION:")
        self.logger.warning(f"   X range: {min_x:.1f} to {max_x:.1f} (width: {max_x - min_x:.1f}px)")
        self.logger.warning(f"   Y range: {min_y:.1f} to {max_y:.1f} (height: {max_y - min_y:.1f}px)")
        
        # If any coordinate is negative, shift everything
        offset_x = max(0, 50 - min_x)  # At least 50px margin
        offset_y = max(0, 50 - min_y)
        
        if offset_x > 0 or offset_y > 0:
            self.logger.warning(f"⚠️  NORMALIZING: offset=({offset_x:.1f}, {offset_y:.1f})")
            positions = {
                element_id: (x + offset_x, y + offset_y)
                for element_id, (x, y) in positions.items()
            }
            
            # Verify after normalization
            new_min_x = min(x for x, y in positions.values())
            new_min_y = min(y for x, y in positions.values())
            self.logger.warning(f"✓ AFTER NORMALIZATION: min=({new_min_x:.1f}, {new_min_y:.1f})")
        else:
            self.logger.warning(f"✓ No normalization needed (all coordinates positive)")
        
        return positions
    
    def _build_dependency_graph(self) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Build directed graph of species dependencies.
        
        Graph structure: species_A → species_B means A is consumed to produce B
        
        Returns:
            (graph, in_degree) where:
                graph: {species_id: [dependent_species_ids]}
                in_degree: {species_id: count of incoming edges}
        """
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize all species with zero in-degree
        for species in self.pathway.species:
            in_degree[species.id] = 0
        
        # Build edges from reactions
        for reaction in self.pathway.reactions:
            reactants = [species_id for species_id, _ in reaction.reactants]
            products = [species_id for species_id, _ in reaction.products]
            
            # Each reactant → each product (dependency)
            for reactant_id in reactants:
                for product_id in products:
                    if reactant_id != product_id:  # Avoid self-loops
                        graph[reactant_id].append(product_id)
                        in_degree[product_id] += 1
        
        return dict(graph), dict(in_degree)
    
    def _assign_layers(self, graph: Dict[str, List[str]], 
                      in_degree: Dict[str, int]) -> List[List[str]]:
        """Assign species to layers using topological sort.
        
        Layer 0: Initial substrates (no predecessors)
        Layer 1: Products of layer 0
        Layer 2: Products of layer 1
        ... and so on
        
        Args:
            graph: Dependency graph
            in_degree: In-degree for each species
            
        Returns:
            List of layers, each layer is a list of species IDs
        """
        layers = []
        current_layer = []
        
        # Start with species that have no incoming edges (initial substrates)
        queue = deque()
        for species_id, degree in in_degree.items():
            if degree == 0:
                queue.append(species_id)
                current_layer.append(species_id)
        
        if not current_layer:
            # Cyclic graph or isolated species - add all to layer 0
            self.logger.warning("No initial substrates found, using all species in layer 0")
            return [[species.id for species in self.pathway.species]]
        
        layers.append(current_layer)
        
        # Process remaining species layer by layer
        while queue:
            next_layer = []
            layer_size = len(queue)
            
            for _ in range(layer_size):
                current_id = queue.popleft()
                
                # Process dependents
                for dependent_id in graph.get(current_id, []):
                    in_degree[dependent_id] -= 1
                    
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)
                        next_layer.append(dependent_id)
            
            if next_layer:
                layers.append(next_layer)
        
        # Check for unprocessed species (cycles)
        unprocessed = [sid for sid, deg in in_degree.items() if deg > 0]
        if unprocessed:
            self.logger.warning(f"Cyclic dependencies found: {len(unprocessed)} species")
            # Add to last layer
            if layers:
                layers[-1].extend(unprocessed)
            else:
                layers.append(unprocessed)
        
        return layers
    
    def _position_layers(self, layers: List[List[str]]) -> Dict[str, Tuple[float, float]]:
        """Position species within their assigned layers - SIMPLE FIXED SPACING.
        
        Uses clean, predictable layout:
        - Vertical: Fixed spacing between layers (150px)
        - Horizontal: Even distribution within each layer
        - Canvas: Centered, max width 1200px
        
        Args:
            layers: List of layers with species IDs
            
        Returns:
            Dictionary {species_id: (x, y)}
        """
        positions = {}
        
        # Layout parameters
        start_y = 100.0  # Top margin
        canvas_center_x = 600.0  # Canvas center
        max_canvas_width = 1200.0  # Maximum width
        min_spacing = 80.0  # Minimum spacing between nodes
        
        self.logger.warning(f"🔍 POSITIONING {len(layers)} LAYERS:")
        
        for layer_index, layer_species in enumerate(layers):
            # Y position for this layer
            y = start_y + layer_index * self.vertical_spacing
            
            num_species = len(layer_species)
            self.logger.warning(f"   Layer {layer_index}: {num_species} species at Y={y:.1f}")
            
            if num_species == 1:
                # Single element: center it
                x = canvas_center_x
                positions[layer_species[0]] = (x, y)
                self.logger.debug(f"      {layer_species[0]}: ({x:.1f}, {y:.1f})")
            else:
                # Multiple elements: distribute evenly
                # Calculate spacing (but don't exceed max width)
                ideal_width = (num_species - 1) * self.horizontal_spacing
                
                if ideal_width > max_canvas_width:
                    # Too wide - use max width with tighter spacing
                    actual_width = max_canvas_width
                    actual_spacing = max_canvas_width / (num_species - 1)
                    self.logger.debug(f"      Layer too wide, reducing spacing to {actual_spacing:.1f}px")
                else:
                    actual_width = ideal_width
                    actual_spacing = self.horizontal_spacing
                
                # Center the layer horizontally
                start_x = canvas_center_x - actual_width / 2
                
                for i, species_id in enumerate(layer_species):
                    x = start_x + i * actual_spacing
                    positions[species_id] = (x, y)
                    if i < 3 or i >= num_species - 1:  # Log first 3 and last
                        self.logger.debug(f"      {species_id}: ({x:.1f}, {y:.1f})")
        
        self.logger.warning(f"✓ POSITIONED {len(positions)} species")
        return positions
    
    def _position_reactions(self, species_positions: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
        """Position reactions BETWEEN layers (not on same layer as species).
        
        Places reactions vertically between their reactants and products layers,
        and horizontally offset to avoid overlapping with species.
        
        Args:
            species_positions: Positions of species
            
        Returns:
            Dictionary {reaction_id: (x, y)}
        """
        reaction_positions = {}
        
        for reaction in self.pathway.reactions:
            reactant_coords = []
            product_coords = []
            
            # Separate reactants and products
            for species_id, _ in reaction.reactants:
                if species_id in species_positions:
                    reactant_coords.append(species_positions[species_id])
            
            for species_id, _ in reaction.products:
                if species_id in species_positions:
                    product_coords.append(species_positions[species_id])
            
            # Position reaction between layers
            if reactant_coords and product_coords:
                # Average position of reactants
                reactant_x = sum(x for x, y in reactant_coords) / len(reactant_coords)
                reactant_y = sum(y for x, y in reactant_coords) / len(reactant_coords)
                
                # Average position of products
                product_x = sum(x for x, y in product_coords) / len(product_coords)
                product_y = sum(y for x, y in product_coords) / len(product_coords)
                
                # Position reaction BETWEEN layers (halfway in Y)
                avg_x = (reactant_x + product_x) / 2
                avg_y = (reactant_y + product_y) / 2
                
                reaction_positions[reaction.id] = (avg_x, avg_y)
                
            elif reactant_coords:
                # Only reactants (sink reaction)
                avg_x = sum(x for x, y in reactant_coords) / len(reactant_coords)
                avg_y = sum(y for x, y in reactant_coords) / len(reactant_coords)
                reaction_positions[reaction.id] = (avg_x, avg_y + self.vertical_spacing / 2)
                
            elif product_coords:
                # Only products (source reaction)
                avg_x = sum(x for x, y in product_coords) / len(product_coords)
                avg_y = sum(y for x, y in product_coords) / len(product_coords)
                reaction_positions[reaction.id] = (avg_x, avg_y - self.vertical_spacing / 2)
                
            else:
                # Fallback: position at center
                reaction_positions[reaction.id] = (400.0, 300.0)
        
        return reaction_positions


class BiochemicalLayoutProcessor:
    """
    Smart layout processor that chooses best strategy based on pathway type.
    
    Strategies:
    - Hierarchical: For linear/branched metabolic pathways
    - Circular: For cyclic pathways (TCA cycle, etc.)
    - Force-directed: For complex networks
    """
    
    def __init__(self, pathway: PathwayData, spacing: float = 150.0, use_tree_layout: bool = False):
        """Initialize biochemical layout processor.
        
        Args:
            pathway: Pathway data
            spacing: Base spacing between elements
            use_tree_layout: If True, use tree-based aperture angle spacing
        """
        self.pathway = pathway
        self.spacing = spacing
        self.use_tree_layout = use_tree_layout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Choose and apply best layout strategy.
        
        Args:
            processed_data: Processed pathway data (will be modified)
        """
        # Check if positions already exist (e.g., from SBML Layout extension)
        if processed_data.positions:
            self.logger.info(
                f"Positions already set ({len(processed_data.positions)} elements), "
                "skipping hierarchical layout calculation"
            )
            return
        
        # Analyze pathway structure
        pathway_type = self._analyze_pathway_type()
        
        self.logger.info(f"Detected pathway type: {pathway_type}")
        
        if pathway_type == "hierarchical":
            # Choose between fixed spacing and tree-based spacing
            if self.use_tree_layout:
                # Use tree-based aperture angle layout
                try:
                    from .tree_layout import TreeLayoutProcessor
                    processor = TreeLayoutProcessor(
                        self.pathway,
                        base_vertical_spacing=self.spacing,
                        base_aperture_angle=45.0,
                        min_horizontal_spacing=30.0  # Balance between steepness and visibility
                    )
                    positions = processor.calculate_tree_layout()
                    processed_data.positions = positions
                    processed_data.metadata['layout_type'] = 'hierarchical-tree'
                    self.logger.info("Using tree-based aperture angle layout")
                except Exception as e:
                    self.logger.warning(f"Tree layout failed: {e}, using fixed spacing")
                    self._use_fixed_spacing(processed_data)
            else:
                # Use fixed spacing layout (current default)
                self._use_fixed_spacing(processed_data)
            
        elif pathway_type == "circular":
            # Future: Implement circular layout for cyclic pathways
            self.logger.info("Circular layout not yet implemented, using force-directed")
            self._fallback_layout(processed_data)
            processed_data.metadata['layout_type'] = 'force-directed'
            
        else:  # complex
            # Use force-directed for complex networks
            self.logger.info("Using force-directed layout for complex network")
            self._fallback_layout(processed_data)
            processed_data.metadata['layout_type'] = 'force-directed'
    
    def _use_fixed_spacing(self, processed_data: ProcessedPathwayData):
        """Use fixed spacing hierarchical layout (current default)."""
        processor = HierarchicalLayoutProcessor(
            self.pathway,
            vertical_spacing=self.spacing,
            horizontal_spacing=self.spacing * 0.7
        )
        positions = processor.calculate_hierarchical_layout()
        processed_data.positions = positions
        processed_data.metadata['layout_type'] = 'hierarchical'
    
    def _analyze_pathway_type(self) -> str:
        """Analyze pathway structure to determine best layout strategy.
        
        Returns:
            "hierarchical", "circular", or "complex"
        """
        # Count reaction types
        num_reactions = len(self.pathway.reactions)
        num_species = len(self.pathway.species)
        
        if num_reactions == 0 or num_species == 0:
            return "complex"
        
        # Build simple graph
        graph = defaultdict(set)
        for reaction in self.pathway.reactions:
            reactants = {sid for sid, _ in reaction.reactants}
            products = {sid for sid, _ in reaction.products}
            for r in reactants:
                graph[r].update(products)
        
        # Check for cycles (circular pathway)
        has_cycles = self._has_cycles(graph)
        
        # Check branching factor
        avg_branching = sum(len(deps) for deps in graph.values()) / max(len(graph), 1)
        
        if has_cycles and num_reactions < 20:
            return "circular"
        elif avg_branching <= 10.0 and not has_cycles:  # Increased to 10.0 for better coverage
            return "hierarchical"
        else:
            return "complex"
    
    def _has_cycles(self, graph: Dict[str, Set[str]]) -> bool:
        """Detect cycles in directed graph using DFS.
        
        Args:
            graph: Adjacency list
            
        Returns:
            True if cycles exist
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def _fallback_layout(self, processed_data: ProcessedPathwayData) -> None:
        """Use force-directed layout as fallback.
        
        Args:
            processed_data: Processed pathway data (will be modified)
        """
        try:
            import networkx as nx
            
            # Build bipartite graph
            graph = nx.Graph()
            for species in self.pathway.species:
                graph.add_node(species.id, bipartite=0)
            
            for reaction in self.pathway.reactions:
                graph.add_node(reaction.id, bipartite=1)
                for species_id, _ in reaction.reactants:
                    graph.add_edge(species_id, reaction.id)
                for species_id, _ in reaction.products:
                    graph.add_edge(reaction.id, species_id)
            
            # Calculate layout
            pos = nx.spring_layout(
                graph,
                k=self.spacing / 50,
                iterations=50,
                scale=self.spacing * 2,
                seed=42
            )
            
            # Convert to positions dict
            for node_id, (x, y) in pos.items():
                processed_data.positions[node_id] = (x + 400, y + 300)
        
        except Exception as e:
            self.logger.error(f"Force-directed layout failed: {e}")
            # Simple grid as last resort
            self._grid_layout(processed_data)
    
    def _grid_layout(self, processed_data: ProcessedPathwayData) -> None:
        """Simple grid layout as last resort."""
        x, y = 100.0, 100.0
        for species in self.pathway.species:
            processed_data.positions[species.id] = (x, y)
            y += self.spacing
            if y > 800:
                y = 100.0
                x += self.spacing
        
        # Position reactions at center
        for reaction in self.pathway.reactions:
            processed_data.positions[reaction.id] = (400.0, 300.0)
