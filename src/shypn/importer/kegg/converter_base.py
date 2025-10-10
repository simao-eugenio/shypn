"""Base classes for KEGG pathway conversion strategies.

This module defines the abstract base classes for converting KEGG pathways
to Petri net models. Different conversion strategies can implement these
base classes with different mapping rules.

OOP Architecture:
- PathwayConverter: Main converter class
- ConversionStrategy: Abstract base for conversion strategies
- CompoundMapper: Maps compounds to places
- ReactionMapper: Maps reactions to transitions
- ArcBuilder: Creates arcs between elements
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from .models import KEGGPathway, KEGGEntry, KEGGReaction


@dataclass
class ConversionOptions:
    """Options for pathway conversion.
    
    Attributes:
        coordinate_scale: Scaling factor for KEGG coordinates (default: 2.5)
        include_cofactors: Include common cofactors (ATP, NAD+, etc.)
        split_reversible: Create two transitions for reversible reactions
        add_initial_marking: Add initial tokens to all places
        initial_tokens: Number of tokens if add_initial_marking is True
        include_relations: Include regulatory relations
        filter_isolated_compounds: Remove compounds not involved in reactions (default: True)
        center_x: X offset for centering the pathway
        center_y: Y offset for centering the pathway
    """
    coordinate_scale: float = 2.5
    include_cofactors: bool = True
    split_reversible: bool = False
    add_initial_marking: bool = False
    initial_tokens: int = 1
    include_relations: bool = False
    filter_isolated_compounds: bool = True
    center_x: float = 0.0
    center_y: float = 0.0


class CompoundMapper(ABC):
    """Abstract base class for mapping compounds to places."""
    
    @abstractmethod
    def should_include(self, entry: KEGGEntry, options: ConversionOptions) -> bool:
        """Determine if compound should be included in conversion.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            True if compound should be converted to place
        """
        pass
    
    @abstractmethod
    def create_place(self, entry: KEGGEntry, options: ConversionOptions) -> Place:
        """Create a Place from a compound entry.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            Place object
        """
        pass
    
    def get_compound_name(self, entry: KEGGEntry) -> str:
        """Extract display name for compound.
        
        Args:
            entry: KEGG compound entry
            
        Returns:
            Display name
        """
        name = entry.graphics.name
        # Clean up name (remove codes, take first name if multiple)
        if ',' in name:
            name = name.split(',')[0].strip()
        return name if name else entry.name


class ReactionMapper(ABC):
    """Abstract base class for mapping reactions to transitions."""
    
    @abstractmethod
    def create_transitions(self, reaction: KEGGReaction, pathway: KEGGPathway,
                          options: ConversionOptions) -> List[Transition]:
        """Create Transition(s) from a reaction.
        
        Args:
            reaction: KEGG reaction
            pathway: Complete pathway (for looking up entries)
            options: Conversion options
            
        Returns:
            List of Transition objects (1 for irreversible, 1-2 for reversible)
        """
        pass
    
    def get_reaction_name(self, reaction: KEGGReaction, pathway: KEGGPathway) -> str:
        """Extract display name for reaction.
        
        Args:
            reaction: KEGG reaction
            pathway: Complete pathway
            
        Returns:
            Display name
        """
        # Try to get enzyme name from associated entry
        if reaction.id in pathway.entries:
            entry = pathway.entries[reaction.id]
            name = entry.graphics.name
            if ',' in name:
                name = name.split(',')[0].strip()
            if name:
                return name
        
        # Fall back to reaction ID
        reaction_name = reaction.name.replace('rn:', 'R')
        return reaction_name if reaction_name else f"Reaction_{reaction.id}"
    
    def get_reaction_position(self, reaction: KEGGReaction, pathway: KEGGPathway,
                             substrates: List[KEGGEntry], products: List[KEGGEntry],
                             options: ConversionOptions) -> Tuple[float, float]:
        """Calculate position for reaction transition.
        
        Args:
            reaction: KEGG reaction
            pathway: Complete pathway
            substrates: List of substrate entries
            products: List of product entries
            options: Conversion options
            
        Returns:
            (x, y) coordinates
        """
        # Try to get position from reaction entry if it exists
        if reaction.id in pathway.entries:
            entry = pathway.entries[reaction.id]
            x = entry.graphics.x * options.coordinate_scale + options.center_x
            y = entry.graphics.y * options.coordinate_scale + options.center_y
            return (x, y)
        
        # Otherwise, position between substrates and products
        all_compounds = substrates + products
        if all_compounds:
            avg_x = sum(e.graphics.x for e in all_compounds) / len(all_compounds)
            avg_y = sum(e.graphics.y for e in all_compounds) / len(all_compounds)
            x = avg_x * options.coordinate_scale + options.center_x
            y = avg_y * options.coordinate_scale + options.center_y
            return (x, y)
        
        # Default position
        return (400.0, 400.0)


class ArcBuilder(ABC):
    """Abstract base class for creating arcs."""
    
    @abstractmethod
    def create_arcs(self, reaction: KEGGReaction, transition: Transition,
                   place_map: Dict[str, Place], pathway: KEGGPathway,
                   options: ConversionOptions) -> List[Arc]:
        """Create arcs for a reaction.
        
        Args:
            reaction: KEGG reaction
            transition: Transition representing the reaction
            place_map: Mapping from entry ID to Place
            pathway: Complete pathway
            options: Conversion options
            
        Returns:
            List of Arc objects
        """
        pass


class ConversionStrategy(ABC):
    """Abstract base class for pathway conversion strategies.
    
    A conversion strategy defines how KEGG pathway elements are mapped
    to Petri net elements. Different strategies can implement different
    mapping rules.
    """
    
    def __init__(self, compound_mapper: CompoundMapper,
                 reaction_mapper: ReactionMapper,
                 arc_builder: ArcBuilder):
        """Initialize conversion strategy.
        
        Args:
            compound_mapper: Strategy for mapping compounds
            reaction_mapper: Strategy for mapping reactions
            arc_builder: Strategy for creating arcs
        """
        self.compound_mapper = compound_mapper
        self.reaction_mapper = reaction_mapper
        self.arc_builder = arc_builder
    
    @abstractmethod
    def convert(self, pathway: KEGGPathway, options: ConversionOptions) -> DocumentModel:
        """Convert KEGG pathway to Petri net model.
        
        Args:
            pathway: Parsed KEGG pathway
            options: Conversion options
            
        Returns:
            DocumentModel with places, transitions, arcs
        """
        pass
