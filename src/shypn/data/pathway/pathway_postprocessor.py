"""
Pathway Post-Processor

Post-processes validated pathway data to prepare for visualization:
- Layout calculation using force-directed graphs
- Color assignment by compartment
- Unit normalization (concentrations → token counts)
- Name resolution (IDs → readable names)

Uses clean OOP architecture:
- BaseProcessor: Abstract base for all processors
- Specialized processors: Each handles one aspect
- PathwayPostProcessor: Minimal coordinator

Author: Shypn Development Team
Date: October 2025
"""

from typing import Dict, List, Tuple, Optional, Any
import logging
import math
from dataclasses import replace

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logging.warning("networkx not available, layout will use simple positioning")

from .pathway_data import (
    PathwayData,
    ProcessedPathwayData,
    Species,
    Reaction,
)
from .hierarchical_layout import BiochemicalLayoutProcessor
from .layout_projector import LayoutProjector


# Color palette for compartments
COMPARTMENT_COLORS = [
    "#E8F4F8",  # Light blue (cytosol)
    "#F0E8F8",  # Light purple (nucleus)
    "#F8F0E8",  # Light orange (mitochondria)
    "#E8F8F0",  # Light green (ER)
    "#F8E8E8",  # Light red (golgi)
    "#F8F8E8",  # Light yellow (peroxisome)
    "#E8E8F8",  # Light indigo (membrane)
]


class BaseProcessor:
    """
    Abstract base class for all post-processors.
    
    All specialized processors inherit from this class and implement
    the process() method.
    """
    
    def __init__(self, pathway: PathwayData):
        """
        Initialize processor.
        
        Args:
            pathway: The validated pathway data to process
        """
        self.pathway = pathway
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """
        Process the pathway data and update processed_data in place.
        
        Args:
            processed_data: The processed data to update
        """
        raise NotImplementedError("Subclasses must implement process()")


class LayoutProcessor(BaseProcessor):
    """
    Calculates layout positions for species (places) and reactions (transitions).
    
    Uses networkx force-directed layout if available, otherwise uses
    simple grid layout.
    """
    
    def __init__(self, pathway: PathwayData, spacing: float = 150.0, 
                 use_tree_layout: bool = False, use_spiral_layout: bool = False,
                 use_raw_force_directed: bool = False, layout_type: str = 'auto',
                 layout_params: dict = None):
        """
        Initialize layout processor.
        
        Args:
            pathway: The pathway data
            spacing: Distance between nodes in pixels
            use_tree_layout: If True, use tree-based aperture angle layout for hierarchical pathways
            use_spiral_layout: If True, use spiral projection (entry at center, products spiral outward)
            use_raw_force_directed: If True, skip projection (pure physics testing)
            layout_type: Layout algorithm to use ('auto', 'hierarchical', 'force_directed')
            layout_params: Dictionary of algorithm-specific parameters
        """
        super().__init__(pathway)
        self.spacing = spacing
        self.use_tree_layout = use_tree_layout
        self.use_spiral_layout = use_spiral_layout
        self.use_raw_force_directed = use_raw_force_directed
        self.layout_type = layout_type
        self.layout_params = layout_params or {}
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Calculate and assign positions.
        
        Tries layout strategies based on user selection:
        - 'auto': Automatic selection (hierarchical → force-directed → grid)
        - 'hierarchical': Top-to-bottom flow layout
        - 'force_directed': Physics-based networkx layout
        
        Note: Cross-reference layout (KEGG/Reactome coordinates) disabled - 
        hierarchical layout provides better visual consistency.
        """
        
        # User explicitly selected Force-Directed
        if self.layout_type == 'force_directed':
            if HAS_NETWORKX:
                self.logger.info("Using user-selected Force-Directed layout")
                self._calculate_force_directed_layout(processed_data)
                processed_data.metadata['layout_type'] = 'force-directed'
                self.logger.info(
                    f"✓ Force-directed layout complete for {len(processed_data.positions)} elements"
                )
                return
            else:
                self.logger.warning("NetworkX not available, falling back to hierarchical")
                self.layout_type = 'hierarchical'
        
        # User explicitly selected Hierarchical OR auto selection
        if self.layout_type in ('hierarchical', 'auto'):
            try:
                # Get hierarchical parameters from layout_params if provided
                layer_spacing = self.layout_params.get('layer_spacing', self.spacing)
                node_spacing = self.layout_params.get('node_spacing', self.spacing * 0.67)
                
                layout_processor = BiochemicalLayoutProcessor(
                    self.pathway, 
                    spacing=layer_spacing,  # Use layer_spacing for vertical spacing
                    use_tree_layout=self.use_tree_layout
                )
                layout_processor.process(processed_data)
                
                if processed_data.positions:
                    self.logger.info(
                        f"✓ Using hierarchical layout for {len(processed_data.positions)} elements "
                        f"(layer_spacing={layer_spacing}, node_spacing={node_spacing})"
                    )
                    return
            except Exception as e:
                self.logger.warning(f"Hierarchical layout failed: {e}")
                if self.layout_type == 'hierarchical':
                    # User explicitly wanted hierarchical, fall back to grid
                    self._calculate_grid_layout(processed_data)
                    processed_data.metadata['layout_type'] = 'grid'
                    return
        
        # Auto mode fallback: try force-directed
        if self.layout_type == 'auto' and HAS_NETWORKX:
            self._calculate_force_directed_layout(processed_data)
            processed_data.metadata['layout_type'] = 'force-directed'
            self.logger.info(
                f"✓ Using force-directed layout for {len(processed_data.positions)} elements"
            )
        else:
            # Last resort: Grid layout
            self._calculate_grid_layout(processed_data)
            processed_data.metadata['layout_type'] = 'grid'
            self.logger.info(
                f"✓ Using grid layout for {len(processed_data.positions)} elements"
            )
    
    def _calculate_force_directed_layout(self, processed_data: ProcessedPathwayData) -> None:
        """Calculate layout using NetworkX force-directed algorithm (Fruchterman-Reingold).
        
        Physics-based simulation using classical mechanics:
        
        TERMINOLOGY (Physics):
        - Mass nodes: All species and reactions (have mass, repel each other)
        - Springs: Arcs/edges connecting reactants↔reaction↔products (attract with force)
        - Spring strength: Proportional to stoichiometry (2A → reaction has 2× spring force)
        
        FORCES:
        - Spring attraction: Pulls connected mass nodes together (F = k × distance)
        - Electrostatic repulsion: Pushes all mass nodes apart (F = -k² / distance)
        - Equilibrium: System converges when spring forces balance repulsion forces
        
        PARAMETERS:
        - k: Optimal distance between mass nodes (spring rest length)
        - weight: Spring strength multiplier (stoichiometry-based)
        - iterations: Number of physics simulation steps
        - threshold: Convergence criterion (stop when delta < threshold)
        """
        
        # Build bipartite graph: species mass nodes + reaction mass nodes
        graph = nx.Graph()
        
        # Add species as mass nodes
        for species in self.pathway.species:
            graph.add_node(species.id, bipartite=0, node_type='species')
        
        # Add reactions as mass nodes and connect with springs (arcs)
        edges = []
        for reaction in self.pathway.reactions:
            graph.add_node(reaction.id, bipartite=1, node_type='reaction')
            
            # Create springs (arcs) from reactants to reaction
            # Spring strength = stoichiometry (2A means 2× stronger attraction)
            for species_id, stoich in reaction.reactants:
                spring_strength = max(1.0, float(stoich))  # Minimum strength 1.0
                graph.add_edge(species_id, reaction.id, weight=spring_strength)
                edges.append((species_id, reaction.id))
                self.logger.debug(f"Spring: {species_id} → {reaction.id} (strength={spring_strength:.1f})")
            
            # Create springs (arcs) from reaction to products
            for species_id, stoich in reaction.products:
                spring_strength = max(1.0, float(stoich))
                graph.add_edge(reaction.id, species_id, weight=spring_strength)
                edges.append((reaction.id, species_id))
                self.logger.debug(f"Spring: {reaction.id} → {species_id} (strength={spring_strength:.1f})")
        
        # Calculate raw positions using spring layout (force-directed physics)
        try:
            self.logger.info(f"Running force-directed layout on {len(graph.nodes())} mass nodes, {len(edges)} springs...")
            
            # Get parameters from layout_params or use defaults
            num_mass_nodes = len(graph.nodes())
            
            # User-specified parameters take precedence
            iterations = self.layout_params.get('iterations', 500)
            k_multiplier = self.layout_params.get('k_multiplier', 1.5)
            scale = self.layout_params.get('scale', 2000.0)
            
            # If no user params, use adaptive scaling
            if 'iterations' not in self.layout_params:
                iterations = min(500, 100 + num_mass_nodes * 5)
            
            if 'k_multiplier' not in self.layout_params:
                if num_mass_nodes > 20:
                    k_multiplier = 2.0
                elif num_mass_nodes > 10:
                    k_multiplier = 1.5
                else:
                    k_multiplier = 1.0
            
            if 'scale' not in self.layout_params:
                if num_mass_nodes > 20:
                    scale = 3000.0
                elif num_mass_nodes > 10:
                    scale = 2000.0
                else:
                    scale = 1000.0
            
            self.logger.info(f"Physics params: k_multiplier={k_multiplier} (spring rest length), scale={scale}px, iterations={iterations}")
            
            # Calculate k based on area and node count
            area = scale * scale
            k = math.sqrt(area / num_mass_nodes) * k_multiplier if num_mass_nodes > 0 else None
            
            # Fruchterman-Reingold force-directed layout with spring weights
            raw_pos = nx.spring_layout(
                graph,
                k=k,                  # Optimal distance between mass nodes (spring rest length)
                iterations=iterations,  # Physics simulation steps (force calculations)
                threshold=1e-6,       # Convergence: stop when max displacement < threshold
                weight='weight',      # Use spring strength (stoichiometry) in force calculation
                scale=scale,          # Output coordinate scale (canvas size)
                seed=42               # Reproducible results
            )
            
            self.logger.info(f"Force-directed physics simulation complete (threshold=1e-6)")
            
            # Convert to pixel coordinates (centered at origin)
            positions = {}
            for node_id, (x, y) in raw_pos.items():
                positions[node_id] = (
                    x + 400,  # Offset to positive coordinates
                    y + 300
                )
            
            # TESTING MODE: Pure force-directed without projection
            if self.use_raw_force_directed:
                self.logger.warning("🔬 PURE FORCE-DIRECTED MODE - No projection post-processing!")
                processed_data.positions.update(positions)
                processed_data.metadata['layout_type'] = 'force-directed-raw'
                processed_data.metadata['canvas_width'] = scale * 2 + 800
                processed_data.metadata['canvas_height'] = scale * 2 + 600
                self.logger.info(f"✓ Raw physics layout: {len(positions)} nodes positioned")
                return
            
            self.logger.info(f"Force-directed complete, projecting to 2D canvas...")
            
            # Apply 2D projection post-processing
            projector = LayoutProjector(
                layer_threshold=50.0,      # Cluster nodes within 50px Y distance
                layer_spacing=200.0,       # 200px between layers
                min_horizontal_spacing=120.0,  # 120px minimum between nodes
                canvas_width=2000.0,       # 2000px max width
                canvas_center_x=1000.0,    # Center at X=1000
                top_margin=800.0,          # Start at Y=800
                left_margin=100.0          # 100px left margin
            )
            
            # Choose projection strategy: SPIRAL or LAYERED
            if self.use_spiral_layout:
                # SPIRAL: Entry at center, products spiral outward
                self.logger.info("Using SPIRAL projection (entry → outward)")
                projected_positions, canvas_dims = projector.project_spiral(positions, edges)
                layout_type = 'force-directed-spiral'
            else:
                # LAYERED: Horizontal layers top-to-bottom
                self.logger.info("Using LAYERED projection (top → bottom)")
                projected_positions, canvas_dims = projector.project(positions, edges)
                layout_type = 'force-directed-projected'
            
            # Store canvas dimensions in metadata for proper viewport sizing
            processed_data.metadata['canvas_width'] = canvas_dims['width']
            processed_data.metadata['canvas_height'] = canvas_dims['height']
            
            self.logger.info(f"✓ Canvas dimensions: {canvas_dims['width']:.0f}x{canvas_dims['height']:.0f}px")
            
            # Update processed data
            processed_data.positions.update(projected_positions)
            processed_data.metadata['layout_type'] = layout_type
            self.logger.info(f"✓ 2D projection complete: {len(projected_positions)} nodes positioned")
        
        except Exception as e:
            self.logger.error(f"Force-directed layout failed: {e}")
            self._calculate_grid_layout(processed_data)
    
    def _position_reactions_between_compounds(self, processed_data: ProcessedPathwayData) -> None:
        """Position reactions at average of their reactants/products.
        
        Helper for cross-reference layout where only species have positions.
        """
        for reaction in self.pathway.reactions:
            x_positions = []
            y_positions = []
            
            for species_id, _ in reaction.reactants + reaction.products:
                if species_id in processed_data.positions:
                    x, y = processed_data.positions[species_id]
                    x_positions.append(x)
                    y_positions.append(y)
            
            if x_positions and y_positions:
                avg_x = sum(x_positions) / len(x_positions)
                avg_y = sum(y_positions) / len(y_positions)
                processed_data.positions[reaction.id] = (avg_x, avg_y)
    
    def _calculate_grid_layout(self, processed_data: ProcessedPathwayData) -> None:
        """Calculate simple grid layout as fallback."""
        
        # Layout species in columns by compartment
        compartment_species: Dict[str, List[Species]] = {}
        for species in self.pathway.species:
            comp = species.compartment or "default"
            if comp not in compartment_species:
                compartment_species[comp] = []
            compartment_species[comp].append(species)
        
        # Position species
        x_offset = 100
        for comp, species_list in compartment_species.items():
            y_offset = 100
            for species in species_list:
                processed_data.positions[species.id] = (x_offset, y_offset)
                y_offset += self.spacing
            x_offset += self.spacing * 2
        
        # Position reactions between their reactants/products
        for reaction in self.pathway.reactions:
            # Calculate average position of reactants and products
            x_positions = []
            y_positions = []
            
            for species_id, _ in reaction.reactants + reaction.products:
                if species_id in processed_data.positions:
                    x, y = processed_data.positions[species_id]
                    x_positions.append(x)
                    y_positions.append(y)
            
            if x_positions and y_positions:
                avg_x = sum(x_positions) / len(x_positions)
                avg_y = sum(y_positions) / len(y_positions)
                processed_data.positions[reaction.id] = (avg_x, avg_y)
            else:
                # Fallback position
                processed_data.positions[reaction.id] = (x_offset, 100)


class ColorProcessor(BaseProcessor):
    """
    Assigns colors to species based on compartments.
    
    Each compartment gets a unique color, and all species in that
    compartment share the color.
    """
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Assign colors by compartment."""
        
        # Get unique compartments
        compartments = list(self.pathway.compartments.keys())
        
        # Assign colors to compartments
        for i, comp_id in enumerate(compartments):
            color = COMPARTMENT_COLORS[i % len(COMPARTMENT_COLORS)]
            processed_data.colors[comp_id] = color
        
        # Default color for species without compartment
        if None not in processed_data.colors:
            processed_data.colors[None] = "#F5F5F5"  # Light gray
        
        self.logger.info(
            f"Assigned colors to {len(processed_data.colors)} compartments"
        )


class UnitNormalizer(BaseProcessor):
    """
    Normalizes concentration units to token counts.
    
    Converts continuous concentrations (mM, µM, etc.) to discrete
    token counts for Petri net simulation.
    """
    
    def __init__(self, pathway: PathwayData, scale_factor: float = 1.0):
        """
        Initialize unit normalizer.
        
        Args:
            pathway: The pathway data
            scale_factor: Multiplier for concentrations (e.g., 10 means 1 mM → 10 tokens)
        """
        super().__init__(pathway)
        self.scale_factor = scale_factor
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Normalize units and store token counts."""
        
        # Convert initial concentrations to token counts
        for species in processed_data.species:
            concentration = species.initial_concentration
            
            # Convert to tokens (round to nearest integer)
            tokens = max(0, round(concentration * self.scale_factor))
            
            # Update species with token count
            updated_species = replace(species, initial_tokens=tokens)
            
            # Replace in list (find and update)
            for i, s in enumerate(processed_data.species):
                if s.id == species.id:
                    processed_data.species[i] = updated_species
                    break
        
        self.logger.info(
            f"Normalized concentrations to tokens (scale={self.scale_factor})"
        )


class NameResolver(BaseProcessor):
    """
    Resolves abbreviated IDs to readable names.
    
    Ensures all species and reactions have display names,
    using IDs as fallback.
    """
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Resolve names from IDs."""
        
        resolved_count = 0
        
        # Resolve species names
        for i, species in enumerate(processed_data.species):
            if not species.name:
                # Use ID as name (capitalize and replace underscores)
                display_name = species.id.replace("_", " ").title()
                updated_species = replace(species, name=display_name)
                processed_data.species[i] = updated_species
                resolved_count += 1
        
        # Resolve reaction names
        for i, reaction in enumerate(processed_data.reactions):
            if not reaction.name:
                # Use ID as name (capitalize and replace underscores)
                display_name = reaction.id.replace("_", " ").title()
                updated_reaction = replace(reaction, name=display_name)
                processed_data.reactions[i] = updated_reaction
                resolved_count += 1
        
        if resolved_count > 0:
            self.logger.info(f"Resolved {resolved_count} missing names")


class CompartmentGrouper(BaseProcessor):
    """
    Groups species by compartment for organized display.
    
    Creates a mapping of compartment → species IDs for rendering
    compartment boundaries on canvas.
    """
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Group species by compartment."""
        
        for species in processed_data.species:
            comp = species.compartment or "default"
            
            if comp not in processed_data.compartment_groups:
                processed_data.compartment_groups[comp] = []
            
            processed_data.compartment_groups[comp].append(species.id)
        
        self.logger.info(
            f"Grouped species into {len(processed_data.compartment_groups)} compartments"
        )


class PathwayPostProcessor:
    """
    Main post-processor coordinator.
    
    Creates and delegates to specialized processors:
    - LayoutProcessor: Calculates positions
    - ColorProcessor: Assigns colors
    - UnitNormalizer: Converts concentrations to tokens
    - NameResolver: Resolves display names
    - CompartmentGrouper: Groups by compartment
    
    Minimal coordinator pattern - most logic is in specialized processors.
    """
    
    def __init__(
        self,
        spacing: float = 150.0,
        scale_factor: float = 1.0,
        use_tree_layout: bool = False,
        use_spiral_layout: bool = False,
        use_raw_force_directed: bool = False,
        layout_type: str = 'auto',
        layout_params: dict = None
    ):
        """
        Initialize post-processor.
        
        Args:
            spacing: Distance between nodes in pixels (for layout)
            scale_factor: Multiplier for concentration → tokens conversion
            use_tree_layout: If True, use tree-based aperture angle layout for hierarchical pathways
            use_spiral_layout: If True, use spiral projection (entry at center, products outward)
            use_raw_force_directed: If True, skip projection post-processing (for testing pure physics)
            layout_type: Layout algorithm to use ('auto', 'hierarchical', 'force_directed')
            layout_params: Dictionary of algorithm-specific parameters
        """
        self.spacing = spacing
        self.scale_factor = scale_factor
        self.use_tree_layout = use_tree_layout
        self.use_spiral_layout = use_spiral_layout
        self.use_raw_force_directed = use_raw_force_directed
        self.layout_type = layout_type
        self.layout_params = layout_params or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, pathway: PathwayData) -> ProcessedPathwayData:
        """
        Post-process pathway data.
        
        Args:
            pathway: The validated pathway data
        
        Returns:
            ProcessedPathwayData with layout, colors, normalized units, etc.
        """
        self.logger.info(f"Post-processing pathway: {pathway.metadata.get('name', 'Unknown')}")
        
        # Create processed data (copy of pathway data)
        processed = ProcessedPathwayData(
            species=list(pathway.species),
            reactions=list(pathway.reactions),
            compartments=dict(pathway.compartments),
            parameters=dict(pathway.parameters),
            metadata=dict(pathway.metadata),
            positions={},
            colors={},
            compartment_groups={}
        )
        
        # Create processors
        processors = [
            LayoutProcessor(pathway, self.spacing, self.use_tree_layout, 
                          self.use_spiral_layout, self.use_raw_force_directed,
                          self.layout_type, self.layout_params),
            ColorProcessor(pathway),
            UnitNormalizer(pathway, self.scale_factor),
            NameResolver(pathway),
            CompartmentGrouper(pathway),
        ]
        
        # Run all processors
        for processor in processors:
            try:
                processor.process(processed)
            except Exception as e:
                self.logger.error(
                    f"{processor.__class__.__name__} failed: {e}",
                    exc_info=True
                )
                # Continue with other processors
        
        self.logger.info("Post-processing complete")
        return processed


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("PATHWAY POST-PROCESSOR")
    print("=" * 70)
    
    # Example pathway
    from pathway_data import Species, Reaction
    
    glucose = Species(
        id="glucose",
        name="Glucose",
        compartment="cytosol",
        initial_concentration=5.0
    )
    
    atp = Species(
        id="atp",
        name="ATP",
        compartment="cytosol",
        initial_concentration=2.5
    )
    
    g6p = Species(
        id="g6p",
        compartment="cytosol",
        initial_concentration=0.0
    )
    
    hexokinase = Reaction(
        id="hexokinase",
        reactants=[("glucose", 1.0), ("atp", 1.0)],
        products=[("g6p", 1.0)]
    )
    
    pathway = PathwayData(
        species=[glucose, atp, g6p],
        reactions=[hexokinase],
        compartments={"cytosol": "Cytoplasm"}
    )
    
    # Process
    processor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = processor.process(pathway)
    
    print(f"\nProcessed pathway:")
    print(f"  Species: {len(processed.species)}")
    print(f"  Positions: {len(processed.positions)}")
    print(f"  Colors: {len(processed.colors)}")
    print(f"  Compartment groups: {len(processed.compartment_groups)}")
    
    print(f"\nToken counts (scale={processor.scale_factor}):")
    for species in processed.species:
        print(f"  {species.name}: {species.initial_tokens} tokens (from {species.initial_concentration} mM)")
    
    print(f"\nPositions:")
    for element_id, (x, y) in processed.positions.items():
        print(f"  {element_id}: ({x:.1f}, {y:.1f})")
    
    print(f"\nColors:")
    for comp, color in processed.colors.items():
        print(f"  {comp}: {color}")
    
    print("\n" + "=" * 70)
    print("Post-processor ready for use!")
    print("=" * 70)
