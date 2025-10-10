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
        
        
        # Phase 3: Filter out isolated places (compounds not involved in any reaction)
        if options.filter_isolated_compounds:
            # Build set of place IDs that have at least one arc
            connected_place_ids = set()
            for arc in document.arcs:
                if arc.source_id.startswith('P'):  # Place ID
                    connected_place_ids.add(arc.source_id)
                if arc.target_id.startswith('P'):  # Place ID
                    connected_place_ids.add(arc.target_id)
            
            # Keep only connected places
            original_place_count = len(document.places)
            document.places = [p for p in document.places if p.id in connected_place_ids]
            
            if original_place_count > len(document.places):
                isolated_count = original_place_count - len(document.places)
                # Note: Could add logging here if verbose mode is enabled
        
        
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
                   add_initial_marking: bool = False,
                   filter_isolated_compounds: bool = True) -> DocumentModel:
    """Quick function to convert pathway with common options.
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        split_reversible: Split reversible reactions into two transitions
        add_initial_marking: Add initial tokens to places
        filter_isolated_compounds: Remove compounds not involved in any reaction
        
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
        add_initial_marking=add_initial_marking,
        filter_isolated_compounds=filter_isolated_compounds
    )
    
    converter = PathwayConverter()
    return converter.convert(pathway, options)


def convert_pathway_enhanced(pathway: KEGGPathway,
                            coordinate_scale: float = 2.5,
                            include_cofactors: bool = True,
                            split_reversible: bool = False,
                            add_initial_marking: bool = False,
                            filter_isolated_compounds: bool = True,
                            enhancement_options: 'EnhancementOptions' = None) -> DocumentModel:
    """Convert pathway with optional post-processing enhancements.
    
    This function extends convert_pathway() with an optional enhancement
    pipeline that applies post-processing to improve the Petri net:
    - Layout optimization (reduce overlaps)
    - Arc routing (add curved arcs)
    - Metadata enrichment (KEGG data)
    - Visual validation (optional)
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        split_reversible: Split reversible reactions into two transitions
        add_initial_marking: Add initial tokens to places
        filter_isolated_compounds: Remove compounds not involved in any reaction
        enhancement_options: Options for post-processing pipeline.
            If None, standard enhancements are applied.
            Set enable_enhancements=False to skip all enhancements.
        
    Returns:
        DocumentModel (optionally enhanced)
        
    Example:
        >>> from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced
        >>> from shypn.pathway import EnhancementOptions
        >>> 
        >>> kgml = fetch_pathway("hsa00010")
        >>> pathway = parse_kgml(kgml)
        >>> 
        >>> # With standard enhancements
        >>> options = EnhancementOptions.get_standard_options()
        >>> document = convert_pathway_enhanced(pathway, enhancement_options=options)
        >>> 
        >>> # With custom enhancements
        >>> options = EnhancementOptions(
        ...     enable_layout_optimization=True,
        ...     enable_arc_routing=False,
        ...     layout_min_spacing=80.0
        ... )
        >>> document = convert_pathway_enhanced(pathway, enhancement_options=options)
    """
    # Standard conversion
    document = convert_pathway(
        pathway=pathway,
        coordinate_scale=coordinate_scale,
        include_cofactors=include_cofactors,
        split_reversible=split_reversible,
        add_initial_marking=add_initial_marking,
        filter_isolated_compounds=filter_isolated_compounds
    )
    
    # Apply enhancements if requested
    if enhancement_options is None:
        # Import here to avoid circular dependencies
        from shypn.pathway.options import EnhancementOptions
        enhancement_options = EnhancementOptions.get_standard_options()
    
    if enhancement_options.enable_enhancements:
        from shypn.pathway.pipeline import EnhancementPipeline
        from shypn.pathway.layout_optimizer import LayoutOptimizer
        from shypn.pathway.arc_router import ArcRouter
        from shypn.pathway.metadata_enhancer import MetadataEnhancer
        from shypn.pathway.visual_validator import VisualValidator
        
        # Build pipeline
        pipeline = EnhancementPipeline(enhancement_options)
        
        # Add enabled processors
        if enhancement_options.enable_layout_optimization:
            pipeline.add_processor(LayoutOptimizer(enhancement_options))
        
        if enhancement_options.enable_arc_routing:
            pipeline.add_processor(ArcRouter(enhancement_options))
        
        if enhancement_options.enable_metadata_enhancement:
            pipeline.add_processor(MetadataEnhancer(enhancement_options))
        
        if enhancement_options.enable_visual_validation:
            pipeline.add_processor(VisualValidator(enhancement_options))
        
        # Process document through pipeline
        document = pipeline.process(document, pathway)
        
        # Print report if verbose
        if enhancement_options.verbose:
            pipeline.print_report()
    
    return document
