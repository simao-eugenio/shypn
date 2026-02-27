"""Main pathway converter implementation."""

import logging
from typing import Dict, Optional, Callable, List
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
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


class KEGGRelationConverter:
    """Converts KEGG relations to signal arcs (Information Flow - Signal Partition Theory).
    
    In KEGG pathways, relation elements represent regulatory/signal interactions distinct
    from material flow (reactions). This converter implements signal place architecture:
    
    Relations → Signal Arcs:
    - ECrel: Enzyme-enzyme relations (activation/inhibition)
    - PPrel: Protein-protein interactions
    - GErel: Gene expression control
    - PCrel: Protein-compound interactions
    
    Subtypes → Arc Types:
    - activation, expression, indirect effect → Test arc (enabling)
    - inhibition, repression → Inhibitor arc (suppression)
    - compound → Material flow (already handled by reactions)
    
    Signal Place Marking:
    - Enzyme/gene/protein entries → Signal places (Ψ_regulatory)
    - Mark as is_signal_place=True
    - Apply signal_type='Ψ_regulatory'
    - Orange arc coloring per SIGNAL_VISUAL_CODING.md
    
    Theoretical Foundation:
    - Material flow (P_m): Compounds connected by regular arcs
    - Information flow (P_s ⊆ Ψ): Enzymes/genes connected by signal arcs
    - Partition constraint: P_m ∩ P_s = ∅
    """
    
    def __init__(self, pathway: KEGGPathway, document: DocumentModel,
                 entry_to_place: Dict[str, Place],
                 entry_to_transition: Dict[str, Transition]):
        """Initialize KEGG relation converter.
        
        Args:
            pathway: KEGG pathway with entries and relations
            document: Target document model
            entry_to_place: Mapping from entry ID to Place object (for enzymes/proteins)
            entry_to_transition: Mapping from entry ID to Transition object (for reactions)
        """
        self.pathway = pathway
        self.document = document
        self.entry_to_place = entry_to_place
        self.entry_to_transition = entry_to_transition
        self.logger = logging.getLogger(__name__)
    
    def convert(self) -> List[TestArc]:
        """Convert KEGG relations to signal arcs.
        
        Returns:
            List of signal arcs (TestArc or InhibitorArc) created
        """
        signal_arcs = []
        relation_count = 0
        skipped_no_source = 0
        skipped_no_target = 0
        skipped_no_subtype = 0
        skipped_compound_only = 0
        
        activation_types = {'activation', 'expression', 'indirect effect', 'state change'}
        inhibition_types = {'inhibition', 'repression'}
        
        # Process all relations
        for relation in self.pathway.relations:
            relation_count += 1
            
            # Get source entry (regulator: enzyme, gene, protein)
            source_entry = self.pathway.entries.get(relation.entry1)
            if not source_entry:
                skipped_no_source += 1
                self.logger.debug(f"Skipping relation: entry1 {relation.entry1} not found")
                continue
            
            # Get target entry (regulated: enzyme, gene, protein, compound)
            target_entry = self.pathway.entries.get(relation.entry2)
            if not target_entry:
                skipped_no_target += 1
                self.logger.debug(f"Skipping relation: entry2 {relation.entry2} not found")
                continue
            
            # Check if relation has regulatory subtypes (not just compound)
            subtype_names = relation.get_subtype_names()
            if not subtype_names:
                skipped_no_subtype += 1
                self.logger.debug(f"Skipping relation {relation.entry1}→{relation.entry2}: no subtypes")
                continue
            
            # Skip relations that only have 'compound' subtype (these are material flow, handled by reactions)
            regulatory_subtypes = [st for st in subtype_names if st not in ['compound', 'binding', 'association', 'dissociation']]
            if not regulatory_subtypes:
                skipped_compound_only += 1
                self.logger.debug(f"Skipping relation {relation.entry1}→{relation.entry2}: only compound/binding subtypes")
                continue
            
            # Get source place (enzyme/protein/gene acting as regulator)
            source_place = self.entry_to_place.get(relation.entry1)
            if not source_place:
                # Source might not have a place if it was filtered out
                self.logger.debug(
                    f"Skipping relation: source entry {relation.entry1} ({source_entry.name}) "
                    f"has no place (filtered or not created)"
                )
                skipped_no_source += 1
                continue
            
            # Mark source place as signal place (Ψ_regulatory)
            source_place.is_signal_place = True
            # Apply color schema immediately after setting semantic flag
            from shypn.utils.color_schema_manager import ColorSchemaManager
            ColorSchemaManager.reset_place_color(source_place)
            if not hasattr(source_place, 'metadata'):
                source_place.metadata = {}
            source_place.metadata['signal_type'] = 'Ψ_regulatory'
            source_place.metadata['is_regulator'] = True
            
            # Get target (could be transition for metabolic pathways, or place for signaling pathways)
            target_transition = None
            target_place = self.entry_to_place.get(relation.entry2)
            
            # CASE 1: Target is an enzyme with a reaction (metabolic pathway)
            # Find the transition that the enzyme catalyzes
            if target_entry.is_gene() and target_entry.reaction:
                # Find transition corresponding to this reaction
                for transition in self.document.transitions:
                    if hasattr(transition, 'metadata') and transition.metadata:
                        if transition.metadata.get('kegg_reaction_name') == target_entry.reaction:
                            target_transition = transition
                            break
            
            # CASE 2: Target is a protein/gene in signaling pathway (no reaction)
            # In signaling pathways, proteins regulate other proteins directly
            # We need to create a "dummy" transition representing the protein's activity
            # This transition is then regulated by signal arcs
            elif target_place and target_entry.is_gene():
                # For signaling pathways: create transition representing protein activity
                # This allows protein A to activate/inhibit protein B's activity
                # Find or create transition for this protein
                transition_id = self.document.id_manager.generate_transition_id()
                transition_name = transition_id
                label = f"{target_place.label}_activity"
                
                # Position transition near the target place
                x = target_place.x
                y = target_place.y + 50  # Offset below the place
                
                target_transition = Transition(x, y, transition_id, transition_name, label=label)
                target_transition.metadata = {
                    'source': 'kegg_signaling',
                    'kegg_entry_id': relation.entry2,
                    'kegg_entry_name': target_entry.name,
                    'protein_activity': True,
                    'regulated_protein': target_place.label
                }
                
                # Add transition to document
                self.document.transitions.append(target_transition)
                
                # Create arcs: target_place → transition → target_place (protein cycle)
                # This represents protein being active/inactive
                arc_id_in = self.document.id_manager.generate_arc_id()
                
                # Auto-detect signal places and create SignalFlowArc if needed
                if getattr(target_place, 'is_signal_place', False):
                    from shypn.netobjs.signal_flow_arc import SignalFlowArc
                    arc_in = SignalFlowArc(
                        source=target_place,
                        target=target_transition,
                        id=arc_id_in,
                        name=f"A{arc_id_in[1:]}",
                        weight=1
                    )
                else:
                    arc_in = Arc(
                        source=target_place,
                        target=target_transition,
                        id=arc_id_in,
                        name=f"A{arc_id_in[1:]}",
                        weight=1
                    )
                self.document.arcs.append(arc_in)
                
                arc_id_out = self.document.id_manager.generate_arc_id()
                
                # Auto-detect signal places and create SignalFlowArc if needed
                if getattr(target_place, 'is_signal_place', False):
                    from shypn.netobjs.signal_flow_arc import SignalFlowArc
                    arc_out = SignalFlowArc(
                        source=target_transition,
                        target=target_place,
                        id=arc_id_out,
                        name=f"A{arc_id_out[1:]}",
                        weight=1
                    )
                else:
                    arc_out = Arc(
                        source=target_transition,
                        target=target_place,
                        id=arc_id_out,
                        name=f"A{arc_id_out[1:]}",
                        weight=1
                    )
                self.document.arcs.append(arc_out)
            
            # CASE 3: Target is compound (less common, skip for now)
            elif target_place and not target_entry.is_gene():
                # If target is a compound, we need to find transitions that consume/produce it
                # For now, we'll skip these - relations between genes/enzymes and compounds
                # are typically handled differently (they affect enzyme activity, not compound)
                self.logger.debug(
                    f"Skipping relation {relation.entry1}→{relation.entry2}: "
                    f"target is compound, not gene/enzyme"
                )
                continue
            
            if not target_transition:
                self.logger.debug(
                    f"Skipping relation {relation.entry1}→{relation.entry2}: "
                    f"no target transition found"
                )
                skipped_no_target += 1
                continue
            
            # Create signal arcs based on subtype
            for subtype in regulatory_subtypes:
                if subtype in activation_types:
                    # Activation: test arc (enables transition)
                    arc_id = self.document.id_manager.generate_arc_id()
                    arc = TestArc(
                        source=source_place,
                        target=target_transition,
                        id=arc_id,
                        name=f"TA{arc_id[1:]}",
                        weight=1
                    )
                    arc.metadata = {
                        'source': 'kegg_relation',
                        'relation_type': relation.type,
                        'subtype': subtype,
                        'entry1_id': relation.entry1,
                        'entry1_name': source_entry.name,
                        'entry2_id': relation.entry2,
                        'entry2_name': target_entry.name,
                        'signal_type': 'Ψ_regulatory',
                        'regulatory_effect': 'activation'
                    }
                    self.document.arcs.append(arc)
                    signal_arcs.append(arc)
                    
                    self.logger.debug(
                        f"Created activation test arc: {source_place.label} → {target_transition.label} "
                        f"({relation.type}: {subtype})"
                    )
                
                elif subtype in inhibition_types:
                    # Inhibition: inhibitor arc (suppresses transition)
                    arc_id = self.document.id_manager.generate_arc_id()
                    arc = InhibitorArc(
                        source=source_place,
                        target=target_transition,
                        id=arc_id,
                        name=f"I{arc_id[1:]}",
                        weight=1
                    )
                    arc.metadata = {
                        'source': 'kegg_relation',
                        'relation_type': relation.type,
                        'subtype': subtype,
                        'entry1_id': relation.entry1,
                        'entry1_name': source_entry.name,
                        'entry2_id': relation.entry2,
                        'entry2_name': target_entry.name,
                        'signal_type': 'Ψ_regulatory',
                        'regulatory_effect': 'inhibition'
                    }
                    self.document.arcs.append(arc)
                    signal_arcs.append(arc)
                    
                    self.logger.debug(
                        f"Created inhibition arc: {source_place.label} ⊣ {target_transition.label} "
                        f"({relation.type}: {subtype})"
                    )
        
        # Log summary
        self.logger.info(
            f"KEGG relation conversion: {len(signal_arcs)} signal arcs created from "
            f"{relation_count} relations "
            f"(skipped: {skipped_no_source} no source, {skipped_no_target} no target, "
            f"{skipped_no_subtype} no subtype, {skipped_compound_only} compound-only)"
        )
        
        return signal_arcs


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
        
        # Initialize document metadata for KEGG import
        if not hasattr(document, 'metadata') or document.metadata is None:
            document.metadata = {}
        document.metadata['data_source'] = 'kegg_import'
        document.metadata['source'] = 'kegg'
        
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
            # These represent catalysts in Biological Petri Nets (metabolic pathways)
            # OR regulatory proteins in signaling pathways (protein-protein interactions)
            # Set options.create_enzyme_places = True to enable biological analysis
            # DESIGN: Enzyme/protein places use KGML coordinates and participate in normal layout
            if options.create_enzyme_places:
                # Check if this is a signaling pathway (no reactions, only protein interactions)
                is_signaling_pathway = len(pathway.reactions) == 0 and len(pathway.relations) > 0
                
                for entry_id, entry in pathway.entries.items():
                    if entry.is_gene():
                        # For metabolic pathways: only create places for enzymes with reactions
                        # For signaling pathways: create places for all proteins/genes
                        if not is_signaling_pathway and not entry.reaction:
                            continue
                        
                        # For metabolic pathways: ensure reaction is in this pathway
                        if entry.reaction and entry.reaction not in pathway_reaction_names:
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
                        
                        # Mark as enzyme and signal place (Ψ_regulatory) for signal partition theory
                        place.is_signal_place = True  # Information flow, not mass transfer
                        place.shape = 'hexagon'  # Hexagonal shape for visual distinction
                        from shypn.utils.color_schema_manager import ColorSchemaManager
                        ColorSchemaManager.reset_place_color(place)  # Apply blue border for signal places
                        if not hasattr(place, 'metadata'):
                            place.metadata = {}
                        place.metadata['kegg_id'] = entry.name
                        place.metadata['kegg_entry_id'] = entry.id
                        place.metadata['kegg_type'] = entry.type
                        place.metadata['source'] = 'KEGG'
                        place.metadata['is_enzyme'] = True
                        place.metadata['catalyzes_reaction'] = entry.reaction
                        place.metadata['signal_type'] = 'Ψ_regulatory'  # Regulatory signal place
                        
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
                        
                        # Mark as signal place (Ψ_regulatory) for signal partition theory
                        place.is_signal_place = True  # Information flow, not mass transfer
                        place.shape = 'hexagon'  # Hexagonal shape for visual distinction
                        from shypn.utils.color_schema_manager import ColorSchemaManager
                        ColorSchemaManager.reset_place_color(place)  # Apply blue border for signal places
                        if not hasattr(place, 'metadata'):
                            place.metadata = {}
                        place.metadata['kegg_id'] = entry.name
                        place.metadata['kegg_entry_id'] = entry.id
                        place.metadata['kegg_type'] = entry.type
                        place.metadata['source'] = 'KEGG'
                        place.metadata['is_enzyme'] = True
                        place.metadata['catalyzes_reaction'] = entry.reaction
                        place.metadata['signal_type'] = 'Ψ_regulatory'  # Regulatory signal place
                        
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
            except (ConnectionError, TimeoutError, ValueError, AttributeError) as e:
                logger.warning(f"Failed to pre-fetch EC numbers: {e}")
                logger.info("Will fall back to fetching EC numbers individually")
        
        # Phase 1.7: Detect and document duplicate reactions (alternative enzymes/isoforms)
        # In KEGG, multiple reactions can have same substrates/products but different enzymes
        # These represent alternative pathways (isoenzymes) for the same transformation
        self._detect_duplicate_reactions(pathway)
        
        # Phase 2: Create transitions and arcs from reactions
        reaction_transition_map = {}  # Track reactions for kinetics enhancement
        reaction_name_to_transition = {}  # Map reaction names to transitions for enzyme conversion
        entry_to_transition = {}  # Map entry IDs to transitions for relation conversion
        
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
                
                # Store reaction name in transition metadata for relation converter
                if not hasattr(transition, 'metadata'):
                    transition.metadata = {}
                transition.metadata['kegg_reaction_name'] = reaction.name
                transition.metadata['kegg_reaction_id'] = reaction.id
                
                # Map entry IDs to transitions for relation converter (if entry has this reaction)
                # Find all entries that reference this reaction
                for entry_id, entry in pathway.entries.items():
                    if entry.reaction == reaction.name:
                        entry_to_transition[entry_id] = transition
                
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
                document.metadata['data_source'] = 'kegg_import'  # For stoichiometry enrichment
                document.metadata['has_test_arcs'] = True
                document.metadata['model_type'] = 'Biological Petri Net'
                document.metadata['test_arc_count'] = len(test_arcs)
                logger.info(
                    f"Created Biological Petri Net with {len(test_arcs)} test arcs "
                    f"(enzymes/catalysts)"
                )
        
        # Phase 2.7: Convert KEGG relations to signal arcs (Information Flow - Signal Partition Theory)
        # Relations represent regulatory/signal interactions distinct from material flow
        # - activation, expression → test arcs (enabling)
        # - inhibition, repression → inhibitor arcs (suppression)
        # NOTE: This creates arcs from regulatory places (enzymes/genes) to transitions
        # Enzymes/genes are marked as signal places (Ψ_regulatory) - information, not mass
        if pathway.relations:
            relation_converter = KEGGRelationConverter(
                pathway=pathway,
                document=document,
                entry_to_place=place_map,
                entry_to_transition=entry_to_transition
            )
            relation_arcs = relation_converter.convert()
            
            # Update document metadata
            if relation_arcs:
                if not hasattr(document, 'metadata') or document.metadata is None:
                    document.metadata = {}
                document.metadata['has_relations'] = True
                document.metadata['relation_arc_count'] = len(relation_arcs)
                
                # Count activation vs inhibition
                activation_count = sum(1 for arc in relation_arcs if isinstance(arc, TestArc))
                inhibition_count = sum(1 for arc in relation_arcs if isinstance(arc, InhibitorArc))
                document.metadata['activation_count'] = activation_count
                document.metadata['inhibition_count'] = inhibition_count
                
                logger.info(
                    f"Converted {len(relation_arcs)} KEGG relations to signal arcs "
                    f"({activation_count} activation, {inhibition_count} inhibition)"
                )
        
        # Phase 2.8: Color signal arcs (orange) per Signal Visual Coding System
        # Signal places (Ψ) represent information flow, distinct from mass transfer
        # Orange arcs = information/regulatory, Violet = compartment transport, Blue = boundary
        self._color_signal_arcs(document)
        
        # Apply color schema to all SignalFlowArcs to ensure correct light gray color
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        from shypn.utils.color_schema_manager import ColorSchemaManager
        for arc in document.arcs:
            if isinstance(arc, SignalFlowArc):
                ColorSchemaManager.reset_arc_color(arc)
        
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
        
        # Phase 5: Set initial viewport to center on model
        # KEGG pathways are positioned in world coordinates (e.g., 400-2000 range)
        # GUI needs to know where to center the viewport
        self._set_initial_viewport(document)
        
        return document
    
    def _color_signal_arcs(self, document: DocumentModel) -> None:
        """Color arcs connected to signal places (test arcs blue, others black).
        
        Signal places (Ψ) represent information flow, not mass transfer.
        They are visually distinct through hexagonal shape with blue borders.
        
        Normalized color scheme (2025-12-31):
        - All net objects: Black by default (0.0, 0.0, 0.0)
        - Signal places: Hexagonal shape with blue borders (0.0, 0.4, 0.8)
        - Test arcs: Blue (0.0, 0.0, 1.0) - colored for visibility
        - Signal flow arcs: Light gray (0.7, 0.7, 0.7) - signal communication
        - Inhibitor arcs: Black (0.0, 0.0, 0.0)
        """
        from shypn.netobjs.test_arc import TestArc
        
        BLUE_COLOR = (0.0, 0.0, 1.0)  # Blue for test arcs
        BLACK_COLOR = (0.0, 0.0, 0.0)  # Black for other arcs (normalized schema)
        test_arc_count = 0
        other_arc_count = 0
        
        # Find all signal places
        signal_places = [p for p in document.places if getattr(p, 'is_signal_place', False)]
        
        if not signal_places:
            return
        
        # Color arcs connected to signal places
        for arc in document.arcs:
            # Check if arc connects to signal place
            is_signal_arc = False
            if hasattr(arc, 'source') and arc.source in signal_places:
                is_signal_arc = True
            elif hasattr(arc, 'target') and hasattr(arc.target, '__class__') and arc.target.__class__.__name__ == 'Place':
                # For arcs where target is a place (though typically signal arcs go Place→Transition)
                if arc.target in signal_places:
                    is_signal_arc = True
            
            if is_signal_arc:
                # Use ColorSchemaManager to assign type-appropriate colors
                from shypn.utils.color_schema_manager import ColorSchemaManager
                ColorSchemaManager.reset_arc_color(arc)
                
                if isinstance(arc, TestArc):
                    test_arc_count += 1
                else:
                    other_arc_count += 1
        
        logger.info(
            f"Colored {test_arc_count} test arcs (blue) and {other_arc_count} other signal arcs (black) for "
            f"{len(signal_places)} signal places (Ψ_regulatory)"
        )
    
    def _set_initial_viewport(self, document: DocumentModel) -> None:
        """Set initial viewport to center on the model.
        
        KEGG pathways have objects positioned in KEGG coordinate space
        (typically 400-2000 range). GUI needs viewport centered on model.
        
        Sets document.view_state['pan_x'] and ['pan_y'] to model center.
        """
        if not document.places and not document.transitions:
            return
        
        # Calculate bounding box of all objects
        all_objects = []
        for place in document.places:
            all_objects.append((place.x, place.y))
        for transition in document.transitions:
            all_objects.append((transition.x, transition.y))
        
        if not all_objects:
            return
        
        # Find bounds
        xs = [obj[0] for obj in all_objects]
        ys = [obj[1] for obj in all_objects]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Set viewport to center on model
        # Note: pan values are typically negative (viewport center in world coords)
        document.view_state['pan_x'] = center_x
        document.view_state['pan_y'] = center_y
        
        # Also store model bounds in metadata for reference
        if not hasattr(document, 'metadata') or document.metadata is None:
            document.metadata = {}
        
        document.metadata['model_bounds'] = {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y,
            'center_x': center_x,
            'center_y': center_y
        }
        
        logger.info(
            f"Set initial viewport to center ({center_x:.1f}, {center_y:.1f}), "
            f"model bounds: {max_x - min_x:.1f}x{max_y - min_y:.1f}"
        )
    
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
            parts = [f"Bipartite property violation in pathway {pathway.name}:\n"]
            for arc, violation_type, arc_str in invalid_arcs:
                parts.append(f"  - {violation_type}: {arc_str} (Arc ID: {arc.id})\n")
            parts.append("\nPetri nets must be bipartite: only Place↔Transition connections allowed.")
            error_msg = "".join(parts)
            
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
                    
            except (AttributeError, ValueError, KeyError) as e:
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
                   create_enzyme_places: bool = True) -> DocumentModel:
    """Quick function to convert pathway with common options.
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        split_reversible: Split reversible reactions into two transitions
        add_initial_marking: Add initial tokens to places (default: False - KEGG has no concentrations)
        filter_isolated_compounds: Remove compounds not involved in any reaction
        create_enzyme_places: Create explicit places for enzymes and test arcs (default: True)
            When True: Biological PN with enzyme places and signal arcs (biological correctness)
            When False: Classical PN without enzymes (simplified visualization only)
        
    Returns:
        DocumentModel
        
    Example:
        >>> from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway
        >>> kgml = fetch_pathway("hsa00010")
        >>> pathway = parse_kgml(kgml)
        >>> 
        >>> # Biological model with enzymes and signal arcs (default - recommended)
        >>> document = convert_pathway(pathway, coordinate_scale=3.0, include_cofactors=False)
        >>> 
        >>> # Simplified visualization without enzymes (classical PN)
        >>> document = convert_pathway(pathway, create_enzyme_places=False)
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
                            create_enzyme_places: bool = True,
                            enhancement_options: 'EnhancementOptions' = None,
                            auto_classify_signals: bool = True,
                            signal_confidence_threshold: float = 0.70) -> DocumentModel:
    """Convert pathway with optional post-processing enhancements.
    
    This function extends convert_pathway() with an optional enhancement
    pipeline that applies post-processing to improve the Petri net:
    - Layout optimization (reduce overlaps)
    - Arc routing (add curved arcs)
    - Metadata enrichment (KEGG data)
    - Kinetic parameter estimation (handled by convert_pathway via KineticsAssigner)
    - Signal classification (NEW - December 2024)
    - Visual validation (optional)
    
    NOTE: KEGG models are topological with limited kinetic metadata.
    Signal classification works but with lower confidence than SBML models.
    Classification relies more on name patterns and topology than rate functions.
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        split_reversible: Split reversible reactions into two transitions
        add_initial_marking: Add initial tokens to places (default: False - KEGG has no concentrations)
        filter_isolated_compounds: Remove compounds not involved in any reaction
        create_enzyme_places: Create explicit places for enzymes and test arcs (default: True)
            When True: Biological PN with enzyme places and signal arcs (biological correctness)
            When False: Classical PN without enzymes (simplified visualization only)
        enhancement_options: Options for post-processing pipeline.
            If None, standard enhancements are applied.
            Set enable_enhancements=False to skip all enhancements.
        auto_classify_signals: If True, automatically classify signal types (default: True)
            Uses name patterns and topology since KEGG has limited kinetic metadata
        signal_confidence_threshold: Minimum confidence for signal classification (0-1, default: 0.70)
            Lower than SBML (0.75) because KEGG has less kinetic information
        
    Returns:
        DocumentModel (optionally enhanced)
        
    Example:
        >>> from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced
        >>> from shypn.pathway import EnhancementOptions
        >>> 
        >>> kgml = fetch_pathway("hsa00010")
        >>> pathway = parse_kgml(kgml)
        >>> 
        >>> # With standard enhancements + signal classification
        >>> options = EnhancementOptions.get_standard_options()
        >>> document = convert_pathway_enhanced(pathway, 
        ...                                     enhancement_options=options,
        ...                                     auto_classify_signals=True)
        >>> 
        >>> # With custom enhancements (disable signal classification)
        >>> options = EnhancementOptions(
        ...     enable_layout_optimization=True,
        ...     enable_arc_routing=False,
        ...     layout_min_spacing=80.0
        ... )
        >>> document = convert_pathway_enhanced(pathway, 
        ...                                     enhancement_options=options,
        ...                                     auto_classify_signals=False)
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
    
    # ========================================================================
    # Signal Classification (NEW - December 2024)
    # ========================================================================
    # Apply signal classification after enhancements
    # NOTE: KEGG models have limited kinetic metadata, so classification
    # relies more on name patterns and topology than rate functions
    if auto_classify_signals:
        try:
            from shypn.analysis.signal_classification import SignalClassifierManager
            
            import logging
            logger = logging.getLogger("KEGGConverter")
            logger.info("Applying signal classification to KEGG pathway...")
            logger.info(f"Note: KEGG models have limited kinetic metadata. "
                       f"Classification uses name patterns and topology primarily.")
            
            # Create model wrapper for classifier
            class ModelWrapper:
                """Lightweight model container satisfying SignalClassifierManager's interface."""

                def __init__(self, places, transitions, arcs):
                    self.places = places
                    self.transitions = transitions
                    self.arcs = arcs
            
            model_wrapper = ModelWrapper(
                document.places,
                document.transitions,
                document.arcs
            )
            
            # Run classification
            manager = SignalClassifierManager(model_wrapper, confidence_threshold=signal_confidence_threshold)
            classifications = manager.classify_all_signals(signal_places_only=True)
            
            # Apply results
            classified_count = 0
            for place_name, (signal_type, confidence) in classifications.items():
                # Find place by name
                place = next((p for p in document.places if p.name == place_name), None)
                if place:
                    # Convert string signal_type to enum if needed
                    from shypn.netobjs.signal_type import SignalType
                    if isinstance(signal_type, str):
                        signal_type = SignalType[signal_type.upper()]
                    
                    place.signal_type = signal_type
                    classified_count += 1
                    
                    logger.debug(
                        f"Classified {place.name} as {signal_type.name if hasattr(signal_type, 'name') else signal_type} "
                        f"(confidence: {confidence:.2f})"
                    )
            
            logger.info(
                f"Signal classification complete: {classified_count} signals classified "
                f"(threshold: {signal_confidence_threshold:.0%})"
            )
            
            # Generate simple summary from classifications
            summary = {}
            for place_name, (sig_type, confidence) in classifications.items():
                type_key = sig_type.upper() if isinstance(sig_type, str) else sig_type.name.upper()
                summary[type_key] = summary.get(type_key, 0) + 1
            
            if summary:
                logger.info(
                    f"Classification summary: "
                    f"ENERGY: {summary.get('ENERGY', 0)}, "
                    f"SPATIAL: {summary.get('SPATIAL', 0)}, "
                    f"QUORUM: {summary.get('QUORUM', 0)}, "
                    f"REGULATORY: {summary.get('REGULATORY', 0)}"
                )
            
        except ImportError as e:
            import logging
            logger = logging.getLogger("KEGGConverter")
            logger.warning(
                f"Signal classification not available: {e}. "
                f"Install signal classification package to enable this feature."
            )
        except (AttributeError, ValueError, KeyError) as e:
            import logging
            logger = logging.getLogger("KEGGConverter")
            logger.error(f"Signal classification failed: {e}")
            import traceback
            traceback.print_exc()
    
    # === SIGNAL HIERARCHY LAYER INFERENCE ===
    # Assign hierarchical layers to signal places based on signal type
    # This enables preemption mechanism and layer-aware analysis
    try:
        _infer_signal_hierarchy_layers(document)
    except (AttributeError, ValueError, KeyError) as e:
        logger.warning(f"Signal hierarchy layer inference failed: {e}")
    
    return document


def _infer_signal_hierarchy_layers(document: DocumentModel) -> Dict[str, int]:
    """Infer and assign hierarchical layers to signal places.
    
    Signal Hierarchy Theory (Simão, 2025):
    - Layer 0: ENERGY signals (ATP, NADH) - Universal metabolic orchestrators
    - Layer 1: SPATIAL signals (compartments, membranes) - Structural constraints
    - Layer 2: QUORUM signals (AHL, autoinducers) - Population context
    - Layer 3: REGULATORY signals (transcription factors) - Decision variables
    
    Higher layers can preempt lower layers through signal flow arcs.
    
    Args:
        document: Document model with signal places
        
    Returns:
        Dict mapping place_id to layer number
    """
    from shypn.netobjs.signal_type import SignalType
    
    logger = logging.getLogger("KEGGConverter")
    layers = {}
    layer_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # Get all signal places
    signal_places = [p for p in document.places if getattr(p, 'is_signal_place', False)]
    
    if not signal_places:
        logger.debug("No signal places found for layer inference")
        return layers
    
    # Assign layers based on signal type
    for place in signal_places:
        signal_type = getattr(place, 'signal_type', None)
        
        if not signal_type:
            continue
        
        # Determine layer from signal type
        layer = None
        if signal_type == SignalType.ENERGY:
            layer = 0
        elif signal_type == SignalType.SPATIAL:
            layer = 1
        elif signal_type == SignalType.QUORUM:
            layer = 2
        elif signal_type == SignalType.REGULATORY:
            layer = 3
        
        if layer is not None:
            # Store layer in place metadata
            if not hasattr(place, 'metadata') or place.metadata is None:
                place.metadata = {}
            place.metadata['hierarchy_layer'] = layer
            place.metadata['layer_name'] = f"Layer {layer}"
            
            layers[place.id] = layer
            layer_counts[layer] += 1
            
            logger.debug(f"Assigned {place.name} to Layer {layer} ({signal_type.name})")
    
    # Store hierarchy summary in document metadata
    if not hasattr(document, 'metadata') or document.metadata is None:
        document.metadata = {}
    
    document.metadata['signal_hierarchy'] = {
        'has_hierarchy': len(layers) > 0,
        'layer_count': sum(1 for count in layer_counts.values() if count > 0),
        'layer_distribution': layer_counts,
        'total_signal_places': len(signal_places),
        'layered_signal_places': len(layers),
    }
    
    # Log summary
    if layers:
        logger.info(
            f"Signal hierarchy: {len(layers)} places assigned to "
            f"{document.metadata['signal_hierarchy']['layer_count']} layers "
            f"(L0:{layer_counts[0]}, L1:{layer_counts[1]}, L2:{layer_counts[2]}, L3:{layer_counts[3]})"
        )
    
    return layers

