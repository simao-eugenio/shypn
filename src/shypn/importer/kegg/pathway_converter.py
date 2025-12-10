"""Main pathway converter implementation."""

import logging
from typing import Dict, Optional, Callable, List
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition
from shypn.netobjs.test_arc import TestArc
from .converter_base import ConversionStrategy, ConversionOptions
from .models import KEGGPathway, KEGGEntry
from shypn.crossfetch.inference import HeuristicInferenceEngine
from shypn.crossfetch.models import TransitionType
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
            arc_id = self.document.id_manager.generate_arc_id()
            
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
            
            # Build set of reaction names that are in the pathway
            # This is used to filter enzyme places - only create places for enzymes
            # whose reactions are actually in the pathway (prevents isolated enzyme places)
            pathway_reaction_names = set()
            for reaction in pathway.reactions:
                pathway_reaction_names.add(reaction.name)
            
            # Only create places for compounds used in reactions
            compounds = pathway.get_compounds()
            for entry in compounds:
                if entry.id in used_compound_ids:
                    if self.compound_mapper.should_include(entry, options):
                        place = self.compound_mapper.create_place(entry, options, document.id_manager)
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
                        # CRITICAL: Only create enzyme place if its reaction is in the pathway
                        # This prevents isolated enzyme places for reactions not in this pathway
                        if entry.reaction not in pathway_reaction_names:
                            logger.debug(
                                f"Skipping enzyme entry {entry_id} ({entry.name}): "
                                f"reaction {entry.reaction} not in pathway reactions"
                            )
                            continue
                        
                        # This is an enzyme entry that catalyzes a reaction IN THIS PATHWAY
                        # Create place using KGML coordinates (same as compounds)
                        x = entry.graphics.x * options.coordinate_scale + options.center_x
                        y = entry.graphics.y * options.coordinate_scale + options.center_y
                        
                        # Get enzyme name from graphics
                        label = entry.graphics.name if entry.graphics and entry.graphics.name else entry.name
                        label = label.replace('\n', ' ').strip()
                        
                        # Use IDManager to generate unique place ID
                        place_id = document.id_manager.generate_place_id()
                        place_name = place_id
                        
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
                    place = self.compound_mapper.create_place(entry, options, document.id_manager)
                    document.places.append(place)
                    place_map[entry.id] = place
            
            # Build set of reaction names for enzyme filtering (even when compound filtering is off)
            pathway_reaction_names = set()
            for reaction in pathway.reactions:
                pathway_reaction_names.add(reaction.name)
            
            # Create enzyme places using KGML coordinates (same as compounds)
            if options.create_enzyme_places:
                for entry_id, entry in pathway.entries.items():
                    if entry.is_gene() and entry.reaction:
                        # CRITICAL: Only create enzyme place if its reaction is in the pathway
                        if entry.reaction not in pathway_reaction_names:
                            logger.debug(
                                f"Skipping enzyme entry {entry_id} ({entry.name}): "
                                f"reaction {entry.reaction} not in pathway reactions"
                            )
                            continue
                        
                        x = entry.graphics.x * options.coordinate_scale + options.center_x
                        y = entry.graphics.y * options.coordinate_scale + options.center_y
                        
                        label = entry.graphics.name if entry.graphics and entry.graphics.name else entry.name
                        label = label.replace('\n', ' ').strip()
                        
                        # Use IDManager to generate unique place ID
                        place_id = document.id_manager.generate_place_id()
                        place_name = place_id
                        
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
        
        # Phase 1.7: Detect and document duplicate reactions (alternative enzymes/isoforms)
        # In KEGG, multiple reactions can have same substrates/products but different enzymes
        # These represent alternative pathways (isoenzymes) for the same transformation
        self._detect_duplicate_reactions(pathway)
        
        # Phase 2: Create transitions and arcs from reactions
        reaction_transition_map = {}  # Track reactions for kinetics enhancement
        reaction_name_to_transition = {}  # Map reaction names to transitions for enzyme conversion
        
        # Track reaction name occurrences for disambiguation
        reaction_name_counter = {}
        
        for reaction in pathway.reactions:
            # Track how many times we've seen this KEGG reaction name
            if reaction.name not in reaction_name_counter:
                reaction_name_counter[reaction.name] = 0
            reaction_name_counter[reaction.name] += 1
            
            # Create transition(s)
            transitions = self.reaction_mapper.create_transitions(reaction, pathway, options, document.id_manager)
            
            for transition in transitions:
                # If this KEGG reaction name appears multiple times, add suffix to label
                # to distinguish instances (e.g., R01175, R01175_2, R01175_3, etc.)
                occurrence = reaction_name_counter[reaction.name]
                if occurrence > 1:
                    # Add suffix to make label unique
                    base_label = transition.label
                    transition.label = f"{base_label}_{occurrence}"
                    logger.debug(
                        f"Disambiguated duplicate reaction {reaction.name}: "
                        f"internal ID {reaction.id} → label '{transition.label}'"
                    )
                
                document.transitions.append(transition)
                reaction_transition_map[transition] = reaction
                
                # Map reaction name (e.g., "rn:R00710") to transition for enzyme linking
                # This allows enzyme entries with reaction="rn:R00710" to find their transition
                reaction_name_to_transition[reaction.name] = transition
                
                # Create arcs for this transition
                # CRITICAL: Pass document so arc builder uses unified arc ID counter
                # This prevents ID conflicts with test arcs created later
                arcs = self.arc_builder.create_arcs(
                    reaction, transition, place_map, pathway, options, document
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
        
        # VALIDATION: Ensure bipartite property
        self._validate_bipartite_property(document, pathway)
        
        # Phase 4: Filter disconnected components if requested
        # This removes isolated micro-networks that disrupt layout
        if options.filter_isolated_compounds:  # Reuse flag for now
            self._filter_disconnected_components(document)
        
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
        
        # Use new heuristic inference engine (advanced pattern matching + stoichiometry)
        engine = HeuristicInferenceEngine(use_background_fetch=False)
        enhancement_stats = {
            'total': 0,
            'enhanced': 0,
            'skipped': 0,
            'failed': 0,
            'by_type': {
                'continuous': 0,
                'stochastic': 0,
                'timed': 0,
                'immediate': 0
            }
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
            
            # Get corresponding reaction (for metadata like EC numbers, reaction_id)
            reaction = reaction_transition_map.get(transition)
            
            # Enrich transition with reaction metadata before inference
            if reaction:
                # Set EC numbers if available
                if hasattr(reaction, 'ec_numbers') and reaction.ec_numbers:
                    if not hasattr(transition, 'metadata'):
                        transition.metadata = {}
                    transition.metadata['ec_numbers'] = reaction.ec_numbers
                    # Also set as direct attribute for new inference engine
                    transition.ec_number = reaction.ec_numbers[0] if reaction.ec_numbers else None
                
                # Set reaction ID for KEGG reactions
                if hasattr(reaction, 'id'):
                    transition.reaction_id = reaction.id
            
            # Infer parameters using new engine
            try:
                result = engine.infer_parameters(
                    transition=transition,
                    organism=pathway.org if hasattr(pathway, 'org') else "Homo sapiens",
                    use_cache=False  # Don't use cache for import (fresh inference)
                )
                
                # Apply inferred parameters to transition
                params = result.parameters
                
                # Set transition type
                if params.transition_type == TransitionType.CONTINUOUS:
                    transition.transition_type = "continuous"
                    # Set continuous parameters
                    if hasattr(params, 'vmax') and params.vmax:
                        if not hasattr(transition, 'properties'):
                            transition.properties = {}
                        transition.properties['vmax'] = params.vmax
                        transition.properties['km'] = params.km
                        # Build rate function string
                        substrate_places = [arc.source for arc in document.arcs if arc.target == transition]
                        if substrate_places:
                            s_id = substrate_places[0].id
                            rate_func = f"({params.vmax} * {s_id}) / ({params.km} + {s_id})"
                            transition.properties['rate_function'] = rate_func
                    enhancement_stats['by_type']['continuous'] += 1
                    
                elif params.transition_type == TransitionType.STOCHASTIC:
                    transition.transition_type = "stochastic"
                    if hasattr(params, 'rate') and params.rate:
                        transition.rate = params.rate
                    enhancement_stats['by_type']['stochastic'] += 1
                    
                elif params.transition_type == TransitionType.TIMED:
                    transition.transition_type = "timed"
                    if hasattr(params, 'delay') and params.delay:
                        transition.delay = params.delay
                    enhancement_stats['by_type']['timed'] += 1
                    
                elif params.transition_type == TransitionType.IMMEDIATE:
                    transition.transition_type = "immediate"
                    if hasattr(params, 'priority') and params.priority:
                        transition.priority = params.priority
                    enhancement_stats['by_type']['immediate'] += 1
                
                # Store metadata about inference
                if not hasattr(transition, 'metadata'):
                    transition.metadata = {}
                transition.metadata['kinetics_source'] = 'heuristic_import'
                transition.metadata['kinetics_confidence'] = params.confidence_score
                if hasattr(params, 'notes') and params.notes:
                    transition.metadata['kinetics_notes'] = params.notes
                
                enhancement_stats['enhanced'] += 1
                logger.debug(
                    f"Enhanced {transition.name}: {params.transition_type.value} "
                    f"(confidence={params.confidence_score:.2f})"
                )
                    
            except Exception as e:
                enhancement_stats['failed'] += 1
                logger.warning(
                    f"Failed to enhance {transition.name}: {e}",
                    exc_info=True
                )
        
        # Log summary
        logger.info(
            f"Kinetics enhancement complete: "
            f"{enhancement_stats['enhanced']}/{enhancement_stats['total']} enhanced, "
            f"continuous={enhancement_stats['by_type']['continuous']}, "
            f"stochastic={enhancement_stats['by_type']['stochastic']}, "
            f"timed={enhancement_stats['by_type']['timed']}, "
            f"immediate={enhancement_stats['by_type']['immediate']}, "
            f"{enhancement_stats['skipped']} skipped, "
            f"{enhancement_stats['failed']} failed"
        )
    
    def _filter_disconnected_components(self, document: DocumentModel):
        """Filter out small disconnected components (isolated micro-networks).
        
        KEGG pathways often contain auxiliary information as small disconnected
        sub-networks that disrupt layout. This method identifies connected components
        and removes small isolated ones, keeping only the largest component as the
        main pathway network.
        
        Strategy:
        1. Build graph of all places and transitions
        2. Find connected components using BFS/DFS
        3. Keep only the largest component
        4. Store filtered elements as metadata (not deleted, just excluded from model)
        
        Args:
            document: DocumentModel to filter (modified in place)
        """
        from collections import deque
        
        # Build adjacency list for the Petri net graph
        graph = {}  # node_id -> set of connected node_ids
        all_nodes = {}  # node_id -> actual object
        
        # Add all places and transitions to graph
        for place in document.places:
            graph[place.id] = set()
            all_nodes[place.id] = place
        
        for transition in document.transitions:
            graph[transition.id] = set()
            all_nodes[transition.id] = transition
        
        # Build edges from arcs (undirected graph for connectivity)
        for arc in document.arcs:
            source_id = arc.source.id
            target_id = arc.target.id
            graph[source_id].add(target_id)
            graph[target_id].add(source_id)
        
        # Find connected components using BFS
        visited = set()
        components = []
        
        for node_id in graph:
            if node_id in visited:
                continue
            
            # BFS to find component
            component = set()
            queue = deque([node_id])
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                
                visited.add(current)
                component.add(current)
                
                # Add neighbors
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            components.append(component)
        
        # Find largest component (main network)
        if not components:
            logger.warning("No connected components found in network")
            return
        
        largest_component = max(components, key=len)
        num_components = len(components)
        
        logger.info(
            f"Found {num_components} connected component(s): "
            f"largest has {len(largest_component)} nodes"
        )
        
        # If only one component, nothing to filter
        if num_components == 1:
            logger.info("Single connected component - no filtering needed")
            return
        
        # Filter: keep only nodes in largest component
        main_component_node_ids = largest_component
        
        # Separate places into kept and filtered
        kept_places = []
        filtered_places = []
        for place in document.places:
            if place.id in main_component_node_ids:
                kept_places.append(place)
            else:
                filtered_places.append(place)
        
        # Separate transitions into kept and filtered
        kept_transitions = []
        filtered_transitions = []
        for transition in document.transitions:
            if transition.id in main_component_node_ids:
                kept_transitions.append(transition)
            else:
                filtered_transitions.append(transition)
        
        # Filter arcs: keep only those connecting nodes in main component
        kept_arcs = []
        filtered_arcs = []
        for arc in document.arcs:
            if arc.source.id in main_component_node_ids and arc.target.id in main_component_node_ids:
                kept_arcs.append(arc)
            else:
                filtered_arcs.append(arc)
        
        # Update document with filtered elements
        document.places = kept_places
        document.transitions = kept_transitions
        document.arcs = kept_arcs
        
        # Store filtered elements in metadata for reference
        if not hasattr(document, 'metadata') or document.metadata is None:
            document.metadata = {}
        
        document.metadata['filtered_disconnected_components'] = {
            'num_components_total': num_components,
            'num_places_filtered': len(filtered_places),
            'num_transitions_filtered': len(filtered_transitions),
            'num_arcs_filtered': len(filtered_arcs),
            'filtered_place_labels': [p.label for p in filtered_places],
            'filtered_transition_labels': [t.label for t in filtered_transitions]
        }
        
        logger.info(
            f"Filtered {num_components - 1} disconnected component(s): "
            f"removed {len(filtered_places)} places, "
            f"{len(filtered_transitions)} transitions, "
            f"{len(filtered_arcs)} arcs"
        )
        
        if filtered_places:
            logger.debug(
                f"{', '.join([p.label for p in filtered_places[:5]])}"
                f"{' ...' if len(filtered_places) > 5 else ''}"
            )
    
    def _detect_duplicate_reactions(self, pathway: KEGGPathway):
        """Detect and document reactions with identical substrates/products.
        
        In KEGG pathways (especially reference pathways like rn00071), multiple
        reactions can have the same substrates and products but different reaction IDs.
        
        This represents ALTERNATIVE ENZYMES (isoenzymes/isozymes):
        - Each enzyme CAN catalyze the reaction INDEPENDENTLY
        - You only need ONE of them present for the reaction to occur
        - They are mutually exclusive alternatives (OR relationship, not AND)
        - NOT like cofactors which must all be present
        
        Common biological reasons for alternatives:
        - Tissue-specificity: Different organs use different isoforms (heart vs liver LDH)
        - Substrate specificity: Different chain lengths (ACADS/ACADM/ACADL for fatty acids)
        - Developmental stages: Fetal vs adult hemoglobin
        - Regulation: Different conditions activate different isoforms
        - Organism diversity: Reference pathways show enzymes from multiple species
        - Evolutionary redundancy: Backup enzymes for critical reactions
        
        Example from rn00071 (fatty acid degradation):
        - R00631: acyl-CoA + FAD → 2,3-dehydroacyl-CoA + FADH2  (enzyme: ACAD9)
        - R03990: acyl-CoA + FAD → 2,3-dehydroacyl-CoA + FADH2  (enzyme: ACADL)
        - R03857: acyl-CoA + FAD → 2,3-dehydroacyl-CoA + FADH2  (enzyme: ACADM)
        
        All three perform the SAME transformation but with DIFFERENT enzyme isoforms.
        The organism needs ONLY ONE of these enzymes to be present/active.
        
        In the Petri net representation:
        - Multiple parallel transitions = Alternative pathways (biological OR)
        - Tokens can flow through ANY of the transitions
        - Models biological flexibility and robustness
        - This is CORRECT behavior, not a modeling error
        
        Compare to cofactors (different concept):
        - Cofactors (ATP, NADH) must be present for reaction to occur (AND relationship)
        - Represented as input places with arcs to transitions
        - Consumed or required, not alternatives
        
        Args:
            pathway: KEGG pathway to analyze
        """
        from collections import defaultdict
        
        # Group reactions by their substrate/product signature
        reaction_signatures = defaultdict(list)
        
        for reaction in pathway.reactions:
            # Create signature: sorted tuple of (substrate_ids, product_ids)
            substrate_ids = tuple(sorted([s.id for s in reaction.substrates]))
            product_ids = tuple(sorted([p.id for p in reaction.products]))
            signature = (substrate_ids, product_ids)
            
            reaction_signatures[signature].append(reaction)
        
        # Find duplicates
        duplicates_found = 0
        total_duplicate_reactions = 0
        
        for signature, reactions in reaction_signatures.items():
            if len(reactions) > 1:
                duplicates_found += 1
                total_duplicate_reactions += len(reactions)
                
                # Get compound names for readability
                substrate_ids, product_ids = signature
                
                # Log the duplicate group
                logger.info(
                    f"Alternative enzymes detected: {len(reactions)} reactions "
                    f"with same substrates/products"
                )
                logger.debug(
                    f"  Substrates: {list(substrate_ids)}"
                )
                logger.debug(
                    f"  Products: {list(product_ids)}"
                )
                
                # Log individual reactions in the group
                for rxn in reactions:
                    enzyme_info = []
                    
                    # Try to find associated enzyme entries
                    for entry_id, entry in pathway.entries.items():
                        if entry.is_gene() and entry.reaction == rxn.name:
                            enzyme_info.append(f"{entry.name}({entry.type})")
                    
                    enzyme_str = ", ".join(enzyme_info) if enzyme_info else "unknown enzyme"
                    
                    logger.debug(
                        f"    - Reaction {rxn.name} (internal ID:{rxn.id}, type:{rxn.type}): {enzyme_str}"
                    )
                
                # Additional detail: show if same KEGG reaction ID appears multiple times
                # This happens when same reaction (e.g., R01175) is listed multiple times
                # in KGML with different internal IDs for different enzyme associations
                reaction_names = [r.name for r in reactions]
                unique_reaction_names = set(reaction_names)
                
                if len(unique_reaction_names) < len(reactions):
                    # Same KEGG reaction ID repeated
                    for rname in unique_reaction_names:
                        count = reaction_names.count(rname)
                        if count > 1:
                            logger.info(
                                f"  ⚠ KEGG reaction {rname} appears {count} times with different "
                                f"internal IDs. This is common in reference pathways where the "
                                f"same reaction is associated with multiple enzyme entries "
                                f"(isoforms, tissue-specific variants, or different organisms)."
                            )
        
        if duplicates_found > 0:
            logger.info(
                f"Found {duplicates_found} groups of alternative enzymes "
                f"(total {total_duplicate_reactions} reactions with duplicates). "
                f"These create parallel transitions in the Petri net, representing "
                f"biologically valid alternative pathways (isoenzymes)."
            )
        else:
            logger.debug("No duplicate reactions found (no alternative enzymes detected)")
    
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
                            enhancement_options: 'EnhancementOptions' = None) -> DocumentModel:
    """Convert pathway with optional post-processing enhancements.
    
    This function extends convert_pathway() with an optional enhancement
    pipeline that applies post-processing to improve the Petri net:
    - Layout optimization (reduce overlaps)
    - Arc routing (add curved arcs)
    - Metadata enrichment (KEGG data)
    - Kinetic parameter estimation (handled by convert_pathway via KineticsAssigner)
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
