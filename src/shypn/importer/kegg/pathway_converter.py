"""Main pathway converter implementation."""

from typing import Dict
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place
from .converter_base import ConversionStrategy, ConversionOptions
from .models import KEGGPathway


class StandardConversionStrategy(ConversionStrategy):
    """Standard conversion strategy using composition of mapper objects.
    
    This strategy implements the main conversion algorithm by delegating
    specific mapping tasks to specialized mapper objects:
    - CompoundMapper: compounds → places
    - ReactionMapper: reactions → transitions
    - ArcBuilder: creates arcs
    """
    
    def convert(self, pathway: KEGGPathway, options: ConversionOptions) -> DocumentModel:
        """Convert KEGG pathway to Petri net model.
        
        Algorithm:
        1. Create places for all included compounds
        2. Create transitions for all reactions
        3. Create arcs connecting places and transitions
        4. Build DocumentModel with all elements
        
        Args:
            pathway: Parsed KEGG pathway
            options: Conversion options
            
        Returns:
            DocumentModel with places, transitions, arcs
        """
              f"cofactors={options.include_cofactors}, split_rev={options.split_reversible}")
        
        document = DocumentModel()
        
        # Phase 1: Create places from compounds
        place_map: Dict[str, Place] = {}
        compounds = pathway.get_compounds()
        
        for entry in compounds:
            if self.compound_mapper.should_include(entry, options):
                place = self.compound_mapper.create_place(entry, options)
                document.places.append(place)
                place_map[entry.id] = place
        
        
        # Phase 2: Create transitions and arcs from reactions
        for reaction in pathway.reactions:
            # Create transition(s)
            transitions = self.reaction_mapper.create_transitions(reaction, pathway, options)
            
            for transition in transitions:
                document.transitions.append(transition)
                
                # Create arcs for this transition
                arcs = self.arc_builder.create_arcs(
                    reaction, transition, place_map, pathway, options
                )
                document.arcs.extend(arcs)
        
        
        # Update ID counters
        if document.places:
            document._next_place_id = len(document.places) + 1
        if document.transitions:
            document._next_transition_id = len(document.transitions) + 1
        if document.arcs:
            document._next_arc_id = len(document.arcs) + 1
        
        
        return document


class PathwayConverter:
    """Main entry point for converting KEGG pathways to Petri nets.
    
    This class provides a simple interface for converting pathways
    using the standard conversion strategy.
    """
    
    def __init__(self, strategy: ConversionStrategy = None):
        """Initialize converter.
        
        Args:
            strategy: Conversion strategy to use (default: StandardConversionStrategy)
        """
        if strategy is None:
            # Create default strategy with standard mappers
            from .compound_mapper import StandardCompoundMapper
            from .reaction_mapper import StandardReactionMapper
            from .arc_builder import StandardArcBuilder
            
            strategy = StandardConversionStrategy(
                compound_mapper=StandardCompoundMapper(),
                reaction_mapper=StandardReactionMapper(),
                arc_builder=StandardArcBuilder()
            )
        
        self.strategy = strategy
    
    def convert(self, pathway: KEGGPathway,
                options: ConversionOptions = None) -> DocumentModel:
        """Convert KEGG pathway to Petri net model.
        
        Args:
            pathway: Parsed KEGG pathway
            options: Conversion options (uses defaults if None)
            
        Returns:
            DocumentModel with places, transitions, arcs
            
        Example:
            >>> converter = PathwayConverter()
            >>> options = ConversionOptions(coordinate_scale=3.0, include_cofactors=False)
            >>> document = converter.convert(pathway, options)
        """
        if options is None:
            options = ConversionOptions()
        
        return self.strategy.convert(pathway, options)


# Convenience function
def convert_pathway(pathway: KEGGPathway,
                   coordinate_scale: float = 2.5,
                   include_cofactors: bool = True,
                   split_reversible: bool = False,
                   add_initial_marking: bool = False) -> DocumentModel:
    """Quick function to convert pathway with common options.
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        split_reversible: Split reversible reactions into two transitions
        add_initial_marking: Add initial tokens to places
        
    Returns:
        DocumentModel
        
    Example:
        >>> from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway
        >>> kgml = fetch_pathway("hsa00010")
        >>> pathway = parse_kgml(kgml)
        >>> document = convert_pathway(pathway, coordinate_scale=3.0, include_cofactors=False)
    """
    options = ConversionOptions(
        coordinate_scale=coordinate_scale,
        include_cofactors=include_cofactors,
        split_reversible=split_reversible,
        add_initial_marking=add_initial_marking
    )
    
    converter = PathwayConverter()
    return converter.convert(pathway, options)
