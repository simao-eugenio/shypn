"""Main pathway converter implementation."""

import logging
from typing import Dict
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition
from .converter_base import ConversionStrategy, ConversionOptions
from .models import KEGGPathway

# Set up logging
logger = logging.getLogger(__name__)


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
        # Strategy: Only create places for compounds used in reactions
        place_map: Dict[str, Place] = {}
        
        if options.filter_isolated_compounds:
            # Build set of compound entry IDs that are actually used in reactions
            used_compound_ids = set()
            for reaction in pathway.reactions:
                for substrate in reaction.substrates:
                    used_compound_ids.add(substrate.id)
                for product in reaction.products:
                    used_compound_ids.add(product.id)
            
            # Only create places for compounds used in reactions
            compounds = pathway.get_compounds()
            for entry in compounds:
                if entry.id in used_compound_ids:
                    if self.compound_mapper.should_include(entry, options):
                        place = self.compound_mapper.create_place(entry, options)
                        document.places.append(place)
                        place_map[entry.id] = place
        else:
            # Create places for all compounds (old behavior when filtering disabled)
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
        
        # VALIDATION: Ensure bipartite property
        self._validate_bipartite_property(document, pathway)
        
        # LOGGING: Log conversion statistics
        self._log_conversion_statistics(document, pathway)
        
        return document
    
    def _validate_bipartite_property(self, document: DocumentModel, pathway: KEGGPathway):
        """Validate that all arcs satisfy bipartite property.
        
        This is a critical validation step to ensure the Petri net structure
        is correct. All arcs must be either Place→Transition or Transition→Place.
        
        Args:
            document: DocumentModel to validate
            pathway: Original KEGG pathway (for error messages)
            
        Raises:
            ValueError: If any arc violates bipartite property
        """
        invalid_arcs = []
        
        for arc in document.arcs:
            source_type = type(arc.source).__name__
            target_type = type(arc.target).__name__
            
            # Check for place-to-place (INVALID)
            if isinstance(arc.source, Place) and isinstance(arc.target, Place):
                invalid_arcs.append((
                    arc,
                    "Place→Place",
                    f"{arc.source.label} → {arc.target.label}"
                ))
            
            # Check for transition-to-transition (INVALID)
            elif isinstance(arc.source, Transition) and isinstance(arc.target, Transition):
                invalid_arcs.append((
                    arc,
                    "Transition→Transition",
                    f"{arc.source.label} → {arc.target.label}"
                ))
        
        if invalid_arcs:
            error_msg = f"Bipartite property violation in pathway {pathway.name}:\n"
            for arc, violation_type, arc_str in invalid_arcs:
                error_msg += f"  - {violation_type}: {arc_str} (Arc ID: {arc.id})\n"
            error_msg += "\nPetri nets must be bipartite: only Place↔Transition connections allowed."
            
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _log_conversion_statistics(self, document: DocumentModel, pathway: KEGGPathway):
        """Log conversion statistics for debugging and monitoring.
        
        Args:
            document: Converted DocumentModel
            pathway: Original KEGG pathway
        """
        # Conversion complete - statistics available in document
        pass


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
                            enhancement_options: 'EnhancementOptions' = None,
                            estimate_kinetics: bool = True) -> DocumentModel:
    """Convert pathway with optional post-processing enhancements.
    
    This function extends convert_pathway() with an optional enhancement
    pipeline that applies post-processing to improve the Petri net:
    - Layout optimization (reduce overlaps)
    - Arc routing (add curved arcs)
    - Metadata enrichment (KEGG data)
    - Kinetic parameter estimation (automatic for enzyme reactions)
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
        estimate_kinetics: If True, automatically estimate kinetic parameters
            for transitions based on reaction type (default: True)
        
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
    
    # Apply kinetic parameter estimation if requested
    if estimate_kinetics:
        from shypn.heuristic.factory import EstimatorFactory
        
        logger.info(f"Estimating kinetic parameters for {len(document.transitions)} transitions...")
        estimated_count = 0
        
        for transition in document.transitions:
            # Get connected places (substrates and products)
            substrate_places = []
            product_places = []
            
            for arc in document.arcs:
                if arc.target == transition:
                    # Arc from place to transition (substrate)
                    substrate_places.append(arc.source)
                elif arc.source == transition:
                    # Arc from transition to place (product)
                    product_places.append(arc.target)
            
            # Skip if no substrates or products
            if not substrate_places and not product_places:
                continue
            
            # Determine reaction type from transition type
            # KEGG reactions are typically enzyme-catalyzed
            t_type = getattr(transition, 'type', None)
            
            # Get estimator based on transition type
            if t_type in ['enzyme', 'irreversible'] or t_type is None:
                # Most KEGG reactions are enzyme-catalyzed
                estimator_type = 'michaelis_menten'
            elif t_type == 'reversible':
                estimator_type = 'mass_action'
            else:
                # For other types, use stochastic as fallback
                estimator_type = 'stochastic'
            
            # Create estimator and generate parameters
            try:
                estimator = EstimatorFactory.create(estimator_type)
                # Pass None for reaction since we don't have Reaction objects from PathwayData
                params = estimator.estimate_parameters(
                    reaction=None,
                    substrate_places=substrate_places,
                    product_places=product_places
                )
                
                # Build rate function
                rate_function = estimator.build_rate_function(
                    reaction=None,
                    substrate_places=substrate_places,
                    product_places=product_places,
                    parameters=params
                )
                
                # Apply rate function to transition
                if rate_function:
                    transition.set_rate(rate_function)
                    estimated_count += 1
                
                # Store additional metadata
                if not hasattr(transition, 'metadata') or transition.metadata is None:
                    transition.metadata = {}
                transition.metadata['kinetic_estimator'] = estimator_type
                transition.metadata['estimated_parameters'] = params
                
            except Exception as e:
                transition_name = getattr(transition, 'name', 'unknown')
                logger.warning(f"Failed to estimate parameters for transition {transition_name}: {e}")
                continue
        
        logger.info(f"Estimated kinetic parameters for {estimated_count}/{len(document.transitions)} transitions")
    
    # Apply enhancements if requested
    if enhancement_options is None:
        # Import here to avoid circular dependencies
        from shypn.pathway.options import get_standard_options
        enhancement_options = get_standard_options()
    
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
