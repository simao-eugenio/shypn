"""Main pathway converter implementation."""

import logging
from typing import Dict, Optional, Callable, List
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition
from shypn.netobjs.test_arc import TestArc
from .converter_base import ConversionStrategy, ConversionOptions
from .models import KEGGPathway, KEGGEntry
from shypn.heuristic import KineticsAssigner
from shypn.data.kegg_ec_fetcher import fetch_ec_numbers_parallel

# Set up logging
logger = logging.getLogger(__name__)


class KEGGEnzymeConverter:
    """Converts KEGG enzyme entries to test arcs (Biological Petri Net).
    
    In KEGG pathways, enzyme entries (type="gene", "enzyme", "ortholog") have a
    'reaction' attribute linking them to the reactions they catalyze. This converter
    implements the Σ component of Biological Petri Nets:
    
    Σ: T → 2^P (maps transitions to their regulatory/catalyst places)
    
    For each enzyme entry with a reaction attribute:
    - enzyme_entry.type in ("gene", "enzyme", "ortholog")
    - enzyme_entry.reaction = "rn:R00710" (KEGG reaction ID)
    - Create test arc: enzyme_place → reaction_transition
    
    Test arcs are non-consuming (catalysts enable reactions without depletion).
    """
    
    def __init__(self, pathway: KEGGPathway, document: DocumentModel,
                 entry_to_place: Dict[str, Place],
                 reaction_name_to_transition: Dict[str, Transition]):
        """Initialize KEGG enzyme converter.
        
        Args:
            pathway: KEGG pathway with entries and reactions
            document: Target document model
            entry_to_place: Mapping from entry ID to Place object
            reaction_name_to_transition: Mapping from reaction name (e.g., "rn:R00710") to Transition
        """
        self.pathway = pathway
        self.document = document
        self.entry_to_place = entry_to_place
        self.reaction_name_to_transition = reaction_name_to_transition
        self.logger = logging.getLogger(__name__)
    
    def convert(self) -> List[TestArc]:
        """Convert enzyme entries to test arcs.
        
        Returns:
            List of TestArc objects created
        """
        test_arcs = []
        enzyme_count = 0
        skipped_no_place = 0
        skipped_no_transition = 0
        
        # Scan all entries for enzymes
        for entry_id, entry in self.pathway.entries.items():
            # Check if this is an enzyme entry with a reaction
            if not entry.is_gene():
                continue
            
            if not entry.reaction:
                continue
            
            enzyme_count += 1
            
            # Get the place for this enzyme entry
            enzyme_place = self.entry_to_place.get(entry_id)
            if not enzyme_place:
                skipped_no_place += 1
                self.logger.debug(
                    f"Skipping enzyme entry {entry_id} ({entry.name}): "
                    f"no place created (filtered out)"
                )
                continue
            
            # Get the transition for the reaction this enzyme catalyzes
            # entry.reaction is typically "rn:R00710" format
            reaction_transition = self.reaction_name_to_transition.get(entry.reaction)
            if not reaction_transition:
                skipped_no_transition += 1
                self.logger.debug(
                    f"Skipping enzyme entry {entry_id} ({entry.name}): "
                    f"reaction {entry.reaction} not found in transitions"
                )
                continue
            
            # Create test arc: enzyme_place → reaction_transition
            arc_id = f"A{self.document._next_arc_id}"
            self.document._next_arc_id += 1
            
            test_arc = TestArc(
                source=enzyme_place,
                target=reaction_transition,
                id=arc_id,
                name=f"TA{arc_id[1:]}",  # TA1, TA2, etc.
                weight=1
            )
            
            # Add metadata
            test_arc.metadata = {
                'source': 'kegg_enzyme',
                'kegg_entry_id': entry_id,
                'kegg_entry_name': entry.name,
                'kegg_entry_type': entry.type,
                'kegg_reaction': entry.reaction,
                'catalyst_type': 'enzyme'
            }
            
            self.document.arcs.append(test_arc)
            test_arcs.append(test_arc)
            
            self.logger.debug(
                f"Created test arc: {enzyme_place.label} → {reaction_transition.label} "
                f"(enzyme {entry.name} catalyzes {entry.reaction})"
            )
        
        # Log summary
        self.logger.info(
            f"KEGG enzyme conversion: {len(test_arcs)} test arcs created from "
            f"{enzyme_count} enzyme entries "
            f"(skipped: {skipped_no_place} no place, {skipped_no_transition} no transition)"
        )
        
        return test_arcs


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
        
        # Phase 1: Create places from compounds AND enzyme entries
        # Strategy: Only create places for compounds used in reactions + enzyme entries with reactions
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
            
            # NEW: Optionally create places for enzyme entries (gene, enzyme, ortholog types)
            # These represent catalysts in Biological Petri Nets
            # Set options.create_enzyme_places = True to enable biological analysis
            # Set False (default) to maintain clean KEGG layout
            # DESIGN: Enzyme places use KGML coordinates and participate in normal layout
            # (not positioned separately above reactions - let them be part of the network)
            if options.create_enzyme_places:
                for entry_id, entry in pathway.entries.items():
                    if entry.is_gene() and entry.reaction:
                        # This is an enzyme entry that catalyzes a reaction
                        # Create place using KGML coordinates (same as compounds)
                        x = entry.graphics.x * options.coordinate_scale + options.center_x
                        y = entry.graphics.y * options.coordinate_scale + options.center_y
                        
                        # Get enzyme name from graphics
                        label = entry.graphics.name if entry.graphics and entry.graphics.name else entry.name
                        label = label.replace('\n', ' ').strip()
                        
                        place_id = f"P{entry.id}"
                        place_name = f"P{entry.id}"
                        
                        # Create enzyme place (participates in network like any other place)
                        place = Place(x, y, place_id, place_name, label=label)
                        place.tokens = 1  # Enzymes typically have 1 token (present/active)
                        place.initial_marking = 1
                        
                        # CRITICAL: Mark as catalyst for layout algorithm exclusion
                        # Catalysts are NOT input places - they're "decorations" that indicate
                        # presence/absence of enzymes. Layout algorithms should exclude them
                        # from dependency graphs to prevent treating them as network inputs.
                        place.is_catalyst = True  # Direct attribute for fast checking
                        
                        # Mark as enzyme in metadata
                        if not hasattr(place, 'metadata'):
                            place.metadata = {}
                        place.metadata['kegg_id'] = entry.name
                        place.metadata['kegg_entry_id'] = entry.id
                        place.metadata['kegg_type'] = entry.type
                        place.metadata['source'] = 'KEGG'
                        place.metadata['is_enzyme'] = True
                        place.metadata['is_catalyst'] = True  # Redundant but explicit
                        place.metadata['catalyzes_reaction'] = entry.reaction
                        
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
            
            # Create enzyme places using KGML coordinates (same as compounds)
            if options.create_enzyme_places:
                for entry_id, entry in pathway.entries.items():
                    if entry.is_gene() and entry.reaction:
                        x = entry.graphics.x * options.coordinate_scale + options.center_x
                        y = entry.graphics.y * options.coordinate_scale + options.center_y
                        
                        label = entry.graphics.name if entry.graphics and entry.graphics.name else entry.name
                        label = label.replace('\n', ' ').strip()
                        
                        place_id = f"P{entry.id}"
                        place_name = f"P{entry.id}"
                        
                        place = Place(x, y, place_id, place_name, label=label)
                        place.tokens = 1
                        place.initial_marking = 1
                        
                        # CRITICAL: Mark as catalyst for layout algorithm exclusion
                        place.is_catalyst = True  # Direct attribute for fast checking
                        
                        if not hasattr(place, 'metadata'):
                            place.metadata = {}
                        place.metadata['kegg_id'] = entry.name
                        place.metadata['kegg_entry_id'] = entry.id
                        place.metadata['kegg_type'] = entry.type
                        place.metadata['source'] = 'KEGG'
                        place.metadata['is_enzyme'] = True
                        place.metadata['is_catalyst'] = True  # Redundant but explicit
                        place.metadata['catalyzes_reaction'] = entry.reaction
                        
                        document.places.append(place)
                        place_map[entry.id] = place
        
        
        # Phase 1.5: Pre-fetch EC numbers in parallel (if metadata enhancement enabled)
        if options.enhance_kinetics:
            reaction_ids = [r.name for r in pathway.reactions]
            logger.info(f"Pre-fetching EC numbers for {len(reaction_ids)} reactions...")
            
            try:
                # Fetch all EC numbers in parallel
                ec_cache = fetch_ec_numbers_parallel(
                    reaction_ids,
                    max_workers=5,
                    progress_callback=None  # TODO: Add UI progress callback
                )
                
                # Pass cache to reaction mapper
                self.reaction_mapper.set_ec_cache(ec_cache)
                logger.info(f"Pre-fetched EC numbers for {len(ec_cache)} reactions")
            except Exception as e:
                logger.warning(f"Failed to pre-fetch EC numbers: {e}")
                logger.info("Will fall back to fetching EC numbers individually")
        
        # Phase 2: Create transitions and arcs from reactions
        reaction_transition_map = {}  # Track reactions for kinetics enhancement
        reaction_name_to_transition = {}  # Map reaction names to transitions for enzyme conversion
        
        for reaction in pathway.reactions:
            # Create transition(s)
            transitions = self.reaction_mapper.create_transitions(reaction, pathway, options)
            
            for transition in transitions:
                document.transitions.append(transition)
                reaction_transition_map[transition] = reaction
                
                # Map reaction name (e.g., "rn:R00710") to transition for enzyme linking
                # This allows enzyme entries with reaction="rn:R00710" to find their transition
                reaction_name_to_transition[reaction.name] = transition
                
                # Create arcs for this transition
                arcs = self.arc_builder.create_arcs(
                    reaction, transition, place_map, pathway, options
                )
                document.arcs.extend(arcs)
        
        # Phase 2.5: Convert enzyme entries to test arcs (Biological Petri Net)
        # ONLY if create_enzyme_places option is enabled
        # KEGG enzyme entries (type="gene"/"enzyme"/"ortholog") with reaction attribute
        # become test arcs connecting enzyme places to reaction transitions
        # NOTE: Enzyme places are created earlier in Phase 1 using KGML coordinates,
        # so they participate in the network naturally (not isolated above)
        if options.create_enzyme_places:
            enzyme_converter = KEGGEnzymeConverter(
                pathway=pathway,
                document=document,
                entry_to_place=place_map,
                reaction_name_to_transition=reaction_name_to_transition
            )
            test_arcs = enzyme_converter.convert()
            
            # Mark document as Biological Petri Net if test arcs were created
            if test_arcs:
                if not hasattr(document, 'metadata') or document.metadata is None:
                    document.metadata = {}
                document.metadata['source'] = 'kegg'
                document.metadata['has_test_arcs'] = True
                document.metadata['model_type'] = 'Biological Petri Net'
                document.metadata['test_arc_count'] = len(test_arcs)
                logger.info(
                    f"Created Biological Petri Net with {len(test_arcs)} test arcs "
                    f"(enzymes/catalysts)"
                )
        
        # Phase 3: Enhance transitions with kinetic properties
        if options.enhance_kinetics:
            self._enhance_transition_kinetics(document, reaction_transition_map, pathway)
        
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
                    f"{str(arc.source.label)} → {str(arc.target.label)}"
                ))
            
            # Check for transition-to-transition (INVALID)
            elif isinstance(arc.source, Transition) and isinstance(arc.target, Transition):
                invalid_arcs.append((
                    arc,
                    "Transition→Transition",
                    f"{str(arc.source.label)} → {str(arc.target.label)}"
                ))
        
        if invalid_arcs:
            error_msg = f"Bipartite property violation in pathway {pathway.name}:\n"
            for arc, violation_type, arc_str in invalid_arcs:
                error_msg += f"  - {violation_type}: {arc_str} (Arc ID: {arc.id})\n"
            error_msg += "\nPetri nets must be bipartite: only Place↔Transition connections allowed."
            
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _enhance_transition_kinetics(self, document: DocumentModel,
                                     reaction_transition_map: Dict,
                                     pathway: KEGGPathway):
        """Enhance transitions with kinetic properties using heuristics.
        
        This method applies the kinetics assignment system to transitions
        created from KEGG reactions. Since KEGG lacks explicit kinetic data,
        heuristics are used to assign reasonable defaults based on reaction
        structure and annotations.
        
        Args:
            document: DocumentModel with transitions to enhance
            reaction_transition_map: Mapping of transitions to their source reactions
            pathway: Original KEGG pathway
        """
        logger.info(f"Enhancing kinetics for {len(document.transitions)} transitions")
        
        assigner = KineticsAssigner()
        enhancement_stats = {
            'total': 0,
            'enhanced': 0,
            'skipped': 0,
            'failed': 0,
            'by_confidence': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for transition in document.transitions:
            # Skip source/sink transitions
            if hasattr(transition, 'is_source') and transition.is_source:
                enhancement_stats['skipped'] += 1
                continue
            if hasattr(transition, 'is_sink') and transition.is_sink:
                enhancement_stats['skipped'] += 1
                continue
            
            enhancement_stats['total'] += 1
            
            # Get corresponding reaction
            reaction = reaction_transition_map.get(transition)
            
            # Get substrate and product places from arcs
            substrate_places = []
            product_places = []
            
            for arc in document.arcs:
                if arc.target == transition:
                    # Input arc: Place → Transition
                    substrate_places.append(arc.source)
                elif arc.source == transition:
                    # Output arc: Transition → Place
                    product_places.append(arc.target)
            
            # Assign kinetics
            try:
                result = assigner.assign(
                    transition=transition,
                    reaction=reaction,
                    substrate_places=substrate_places,
                    product_places=product_places,
                    source='kegg'
                )
                
                if result.success:
                    enhancement_stats['enhanced'] += 1
                    enhancement_stats['by_confidence'][result.confidence.value] += 1
                    logger.debug(
                        f"Enhanced {transition.name}: {result.confidence.value} "
                        f"confidence, rule={result.rule}"
                    )
                else:
                    enhancement_stats['skipped'] += 1
                    logger.debug(f"Skipped {transition.name}: {result.message}")
                    
            except Exception as e:
                enhancement_stats['failed'] += 1
                logger.warning(
                    f"Failed to enhance {transition.name}: {e}",
                    exc_info=True
                )
        
        # Log summary
        logger.info(
            f"Kinetics enhancement complete: "
            f"{enhancement_stats['enhanced']}/{enhancement_stats['total']} enhanced "
            f"(High: {enhancement_stats['by_confidence']['high']}, "
            f"Medium: {enhancement_stats['by_confidence']['medium']}, "
            f"Low: {enhancement_stats['by_confidence']['low']}), "
            f"{enhancement_stats['skipped']} skipped, "
            f"{enhancement_stats['failed']} failed"
        )
    
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
                   filter_isolated_compounds: bool = True,
                   create_enzyme_places: bool = False) -> DocumentModel:
    """Quick function to convert pathway with common options.
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        split_reversible: Split reversible reactions into two transitions
        add_initial_marking: Add initial tokens to places (default: False - KEGG has no concentrations)
        filter_isolated_compounds: Remove compounds not involved in any reaction
        create_enzyme_places: Create explicit places for enzymes and test arcs (default: False)
            When False: Clean KEGG layout, classical PN (recommended for visualization)
            When True: Biological PN with enzyme places and test arcs (recommended for analysis)
        
    Returns:
        DocumentModel
        
    Example:
        >>> from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway
        >>> kgml = fetch_pathway("hsa00010")
        >>> pathway = parse_kgml(kgml)
        >>> 
        >>> # Clean layout (default - recommended)
        >>> document = convert_pathway(pathway, coordinate_scale=3.0, include_cofactors=False)
        >>> 
        >>> # Biological analysis (with enzyme places)
        >>> document = convert_pathway(pathway, create_enzyme_places=True)
    """
    options = ConversionOptions(
        coordinate_scale=coordinate_scale,
        include_cofactors=include_cofactors,
        split_reversible=split_reversible,
        add_initial_marking=add_initial_marking,
        filter_isolated_compounds=filter_isolated_compounds,
        create_enzyme_places=create_enzyme_places
    )
    
    converter = PathwayConverter()
    return converter.convert(pathway, options)


def convert_pathway_enhanced(pathway: KEGGPathway,
                            coordinate_scale: float = 2.5,
                            include_cofactors: bool = True,
                            split_reversible: bool = False,
                            add_initial_marking: bool = False,
                            filter_isolated_compounds: bool = True,
                            create_enzyme_places: bool = False,
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
        add_initial_marking: Add initial tokens to places (default: False - KEGG has no concentrations)
        filter_isolated_compounds: Remove compounds not involved in any reaction
        create_enzyme_places: Create explicit places for enzymes and test arcs (default: False)
            When False: Clean KEGG layout, classical PN (recommended for visualization)
            When True: Biological PN with enzyme places and test arcs (recommended for analysis)
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
        filter_isolated_compounds=filter_isolated_compounds,
        create_enzyme_places=create_enzyme_places
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
