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
    
    def __init__(self, pathway: PathwayData, spacing: float = 150.0, use_tree_layout: bool = False):
        """
        Initialize layout processor.
        
        Args:
            pathway: The pathway data
            spacing: Distance between nodes in pixels
            use_tree_layout: If True, use tree-based aperture angle layout for hierarchical pathways
        """
        super().__init__(pathway)
        self.spacing = spacing
        self.use_tree_layout = use_tree_layout
    
    def process(self, processed_data: ProcessedPathwayData) -> None:
        """Calculate and assign positions.
        
        Tries layout strategies in order of quality:
        1. Cross-reference (KEGG/Reactome coordinates) - BEST
        2. Hierarchical (top-to-bottom flow) - GOOD for metabolic pathways
        3. Force-directed (networkx) - OK for complex networks
        4. Grid (fallback) - BASIC
        """
        
        # STRATEGY 1: Try cross-reference resolution first (KEGG, etc.)
        try:
            from .sbml_layout_resolver import SBMLLayoutResolver
            resolver = SBMLLayoutResolver(self.pathway)
            positions = resolver.resolve_layout()
            
            if positions:
                processed_data.positions = positions
                # Still need to position reactions
                self._position_reactions_between_compounds(processed_data)
                # Mark as cross-reference layout (straight arcs preferred)
                processed_data.metadata['layout_type'] = 'cross-reference'
                self.logger.info(
                    f"✓ Using cross-reference layout for {len(positions)} elements"
                )
                return
        except Exception as e:
            self.logger.debug(f"Cross-reference resolution failed: {e}")
        
        # STRATEGY 2: Try hierarchical layout (biochemical top-to-bottom)
        try:
            layout_processor = BiochemicalLayoutProcessor(
                self.pathway, 
                spacing=self.spacing,
                use_tree_layout=self.use_tree_layout  # Pass through tree layout flag
            )
            layout_processor.process(processed_data)
            
            if processed_data.positions:
                # layout_type already set by BiochemicalLayoutProcessor
                self.logger.info(
                    f"✓ Using hierarchical layout for {len(processed_data.positions)} elements"
                )
                return
        except Exception as e:
            self.logger.debug(f"Hierarchical layout failed: {e}")
        
        # STRATEGY 3: Force-directed layout (requires networkx)
        if HAS_NETWORKX:
            self._calculate_force_directed_layout(processed_data)
            processed_data.metadata['layout_type'] = 'force-directed'
            self.logger.info(
                f"✓ Using force-directed layout for {len(processed_data.positions)} elements"
            )
        else:
            # STRATEGY 4: Grid layout (last resort)
            self._calculate_grid_layout(processed_data)
            processed_data.metadata['layout_type'] = 'grid'
            self.logger.info(
                f"✓ Using grid layout for {len(processed_data.positions)} elements"
            )
    
    def _calculate_force_directed_layout(self, processed_data: ProcessedPathwayData) -> None:
        """Calculate layout using networkx force-directed algorithm."""
        
        # Build bipartite graph (species + reactions)
        graph = nx.Graph()
        
        # Add species nodes
        for species in self.pathway.species:
            graph.add_node(species.id, bipartite=0)  # Species on one side
        
        # Add reaction nodes and edges
        for reaction in self.pathway.reactions:
            graph.add_node(reaction.id, bipartite=1)  # Reactions on other side
            
            # Connect reactants to reaction
            for species_id, _ in reaction.reactants:
                graph.add_edge(species_id, reaction.id)
            
            # Connect reaction to products
            for species_id, _ in reaction.products:
                graph.add_edge(reaction.id, species_id)
        
        # Calculate positions using spring layout
        try:
            pos = nx.spring_layout(
                graph,
                k=self.spacing / 50,  # Optimal distance between nodes
                iterations=50,
                scale=self.spacing * 2,  # Scale to desired spacing
                seed=42  # For reproducibility
            )
            
            # Convert to pixel coordinates (centered at origin)
            for node_id, (x, y) in pos.items():
                processed_data.positions[node_id] = (
                    x + 400,  # Offset to positive coordinates
                    y + 300
                )
        
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
        use_tree_layout: bool = False
    ):
        """
        Initialize post-processor.
        
        Args:
            spacing: Distance between nodes in pixels (for layout)
            scale_factor: Multiplier for concentration → tokens conversion
            use_tree_layout: If True, use tree-based aperture angle layout for hierarchical pathways
        """
        self.spacing = spacing
        self.scale_factor = scale_factor
        self.use_tree_layout = use_tree_layout
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
            LayoutProcessor(pathway, self.spacing, self.use_tree_layout),
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
