"""Base classes and options for KEGG pathway conversion.

This module defines the abstract base classes and configuration options
for converting KEGG pathways to Petri net models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.netobjs import Place, Transition, Arc
    from .models import KEGGPathway, KEGGEntry, KEGGReaction


@dataclass
class ConversionOptions:
    """Configuration options for pathway conversion.
    
    Attributes:
        coordinate_scale: Factor to scale KEGG coordinates (default: 2.5)
            KEGG uses small coordinate values, so scaling improves visibility
        
        include_cofactors: Include common cofactors (ATP, NADH, etc.) (default: True)
            When False, filters out ubiquitous metabolites to reduce clutter
        
        split_reversible: Split reversible reactions into two transitions (default: False)
            When True, creates forward and backward transitions for reversible reactions
        
        add_initial_marking: Add initial tokens to places (default: True)
            When True, adds one token to each place for immediate simulation/testing
            KEGG pathways don't specify initial states, so this enables quick experimentation
        
        filter_isolated_compounds: Remove compounds not involved in any reaction (default: True)
            When True, excludes compounds that appear in KEGG but aren't connected to reactions
            This significantly reduces model size and clutter (typically removes 15-30% of compounds)
        
        enhance_kinetics: Apply heuristic kinetics enhancement to transitions (default: True)
            When True, analyzes reaction structure to assign appropriate kinetic types
            (stochastic vs continuous) and reasonable parameter defaults
            Uses the heuristic system to fill gaps since KEGG lacks explicit kinetic data
        
        center_x: X coordinate offset for positioning (default: 0.0)
        center_y: Y coordinate offset for positioning (default: 0.0)
        initial_tokens: Number of tokens to add to each place when add_initial_marking is True (default: 1)
    """
    coordinate_scale: float = 2.5
    include_cofactors: bool = True
    split_reversible: bool = False
    add_initial_marking: bool = True  # Auto-add tokens for testing/experimentation
    filter_isolated_compounds: bool = True
    enhance_kinetics: bool = True  # Auto-enhance kinetics for better simulation
    center_x: float = 0.0
    center_y: float = 0.0
    initial_tokens: int = 1


class ConversionStrategy(ABC):
    """Abstract base class for pathway conversion strategies.
    
    A conversion strategy defines how to convert a KEGG pathway into a Petri net model.
    Subclasses should implement the convert() method to perform the conversion.
    
    The strategy pattern allows different conversion algorithms while maintaining
    a consistent interface for clients.
    """
    
    def __init__(self, compound_mapper=None, reaction_mapper=None, arc_builder=None):
        """Initialize the conversion strategy.
        
        Args:
            compound_mapper: Mapper for converting compounds to places
            reaction_mapper: Mapper for converting reactions to transitions
            arc_builder: Builder for creating arcs between places and transitions
        """
        self.compound_mapper = compound_mapper
        self.reaction_mapper = reaction_mapper
        self.arc_builder = arc_builder
    
    @abstractmethod
    def convert(self, pathway: 'KEGGPathway', options: ConversionOptions) -> 'DocumentModel':
        """Convert KEGG pathway to Petri net model.
        
        Args:
            pathway: Parsed KEGG pathway to convert
            options: Conversion options controlling the conversion process
            
        Returns:
            DocumentModel containing places, transitions, and arcs
            
        Raises:
            ValueError: If the pathway structure is invalid or conversion fails
        """
        pass


class CompoundMapper(ABC):
    """Abstract base class for mapping KEGG compounds to places.
    
    A compound mapper decides which compounds should be included in the
    Petri net and how to create Place objects from compound entries.
    """
    
    @abstractmethod
    def should_include(self, entry: 'KEGGEntry', options: ConversionOptions) -> bool:
        """Determine if a compound should be included in the Petri net.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            True if the compound should be included, False otherwise
        """
        pass
    
    @abstractmethod
    def create_place(self, entry: 'KEGGEntry', options: ConversionOptions) -> 'Place':
        """Create a Place from a KEGG compound entry.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            Place object representing the compound
        """
        pass


class ReactionMapper(ABC):
    """Abstract base class for mapping KEGG reactions to transitions.
    
    A reaction mapper creates Transition objects from reaction entries,
    handling both simple and reversible reactions.
    """
    
    @abstractmethod
    def create_transitions(self, reaction: 'KEGGReaction', pathway: 'KEGGPathway',
                          options: ConversionOptions) -> List['Transition']:
        """Create Transition(s) from a KEGG reaction.
        
        Args:
            reaction: KEGG reaction to convert
            pathway: Complete pathway (for context)
            options: Conversion options
            
        Returns:
            List of Transition objects (typically one, but two for split reversible)
        """
        pass


class ArcBuilder(ABC):
    """Abstract base class for creating arcs between places and transitions.
    
    An arc builder creates the connections that represent substrate/product
    relationships in reactions, handling stoichiometry and directionality.
    """
    
    @abstractmethod
    def create_arcs(self, reaction: 'KEGGReaction', transition: 'Transition',
                   place_map: Dict[str, 'Place'], pathway: 'KEGGPathway',
                   options: ConversionOptions) -> List['Arc']:
        """Create arcs for a reaction.
        
        Args:
            reaction: KEGG reaction
            transition: Transition representing the reaction
            place_map: Mapping from KEGG entry ID to Place
            pathway: Complete pathway
            options: Conversion options
            
        Returns:
            List of Arc objects connecting places and transitions
        """
        pass
