"""
Pathway Post-Processor (Simplified v2.0)

Minimal post-processing for SBML pathways:
- Arbitrary position assignment (force-directed layout will recalculate via Swiss Palette)
- Color assignment by compartment
- Unit normalization (concentrations → token counts)
- Name resolution (IDs → readable names)

NO LAYOUT ALGORITHMS - Layout is now user-initiated via Swiss Palette → Force-Directed

Architecture:
- BaseProcessor: Abstract base for all processors
- ColorProcessor: Assigns colors by compartment
- UnitNormalizer: Converts concentrations to tokens
- NameResolver: Resolves display names
- CompartmentGrouper: Groups species by compartment
- PathwayPostProcessor: Minimal coordinator

Author: Shypn Development Team
Date: October 2025
Version: 2.0 (Simplified Pipeline)
"""

from typing import Dict, List
import logging
from dataclasses import replace

from .pathway_data import (
    PathwayData,
    ProcessedPathwayData,
    Species,
    Reaction,
)


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
    Minimal post-processor coordinator (v2.0 Simplified).
    
    NO LAYOUT CALCULATION - Layout is now user-initiated via Swiss Palette → Force-Directed.
    
    This processor only:
    - Assigns ARBITRARY positions (force-directed will recalculate everything)
    - Assigns colors by compartment
    - Normalizes concentrations to tokens
    - Resolves display names
    - Groups by compartment
    
    Delegates to specialized processors:
    - ColorProcessor: Assigns colors
    - UnitNormalizer: Converts concentrations to tokens
    - NameResolver: Resolves display names
    - CompartmentGrouper: Groups by compartment
    """
    
    def __init__(self, scale_factor: float = 1.0):
        """
        Initialize post-processor.
        
        Args:
            scale_factor: Multiplier for concentration → tokens conversion
        """
        self.scale_factor = scale_factor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, pathway: PathwayData) -> ProcessedPathwayData:
        """
        Post-process pathway data (minimal).
        
        Args:
            pathway: The validated pathway data
        
        Returns:
            ProcessedPathwayData with colors, normalized units, and ARBITRARY positions
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
        
        # Assign ARBITRARY positions (force-directed will recalculate everything)
        # These positions are just placeholders so the converter doesn't complain
        self.logger.info("Assigning arbitrary positions (force-directed will recalculate)")
        
        base_x, base_y = 100.0, 100.0
        offset = 0.0
        
        # All species at similar positions (force-directed will spread them)
        for species in processed.species:
            processed.positions[species.id] = (base_x + offset, base_y + offset)
            offset += 10.0  # Small offset to avoid exact overlap
        
        # All reactions at similar positions (force-directed will spread them)
        offset = 0.0
        for reaction in processed.reactions:
            processed.positions[reaction.id] = (base_x + 50.0 + offset, base_y + 50.0 + offset)
            offset += 10.0
        
        self.logger.info(
            f"Assigned {len(processed.positions)} arbitrary positions "
            f"(Swiss Palette force-directed will replace these)"
        )
        
        # Mark as arbitrary (no real layout applied)
        processed.metadata['layout_type'] = 'arbitrary'
        processed.metadata['layout_note'] = 'Use Swiss Palette → Force-Directed to apply physics-based layout'
        
        # Create processors (NO LAYOUT PROCESSOR - that's gone!)
        processors = [
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
        
        self.logger.info("Post-processing complete (positions are arbitrary)")
        return processed


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    
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
    processor = PathwayPostProcessor(scale_factor=2.0)
    processed = processor.process(pathway)
    
    
    for species in processed.species:
        pass  # Process species
    
    for element_id, (x, y) in list(processed.positions.items())[:5]:
        pass  # Process positions
    
    for comp, color in processed.colors.items():
        pass  # Process colors
    
