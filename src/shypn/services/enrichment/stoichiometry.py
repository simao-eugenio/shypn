"""KEGG stoichiometry enricher for completing reaction networks.

This module enriches KEGG-imported models by fetching complete reaction
stoichiometry from the KEGG REACTION database and adding missing cofactors
(ATP, NADH, CoA, etc.) to enable signal hierarchy and thermodynamic analysis.
"""

import re
import time
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.signal_type import SignalType
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.data.canvas.document_model import DocumentModel
from shypn.importer.kegg.api_client import KEGGAPIClient
from .base import BaseEnricher, EnrichmentResult
from .rate_inhibition_extractor import RateInhibitionExtractor
from .signal_source_sink_builder import SignalSourceSinkBuilder
from .obsolete_reactions import is_obsolete, get_current_reaction, get_obsolescence_reason, suggest_alternatives

import logging
logger = logging.getLogger(__name__)


@dataclass
class CompoundStoich:
    """Stoichiometry information for a compound in a reaction.
    
    Attributes:
        compound_id: KEGG compound ID (e.g., "C00002")
        coefficient: Stoichiometric coefficient (default: 1)
        name: Compound name if available
    """
    compound_id: str
    coefficient: int = 1
    name: Optional[str] = None


@dataclass
class ReactionStoichiometry:
    """Complete stoichiometry for a KEGG reaction.
    
    Attributes:
        reaction_id: KEGG reaction ID (e.g., "R00200")
        equation: Reaction equation string
        substrates: List of substrate compounds with coefficients
        products: List of product compounds with coefficients
        is_reversible: Whether reaction is reversible
        enzyme_names: List of enzyme names if available
    """
    reaction_id: str
    equation: str
    substrates: List[CompoundStoich] = field(default_factory=list)
    products: List[CompoundStoich] = field(default_factory=list)
    is_reversible: bool = False
    enzyme_names: List[str] = field(default_factory=list)


class KEGGStoichiometryEnricher(BaseEnricher):
    """Enriches KEGG models with complete reaction stoichiometry.
    
    KEGG KGML pathway files simplify reactions by omitting common cofactors
    (ATP, NADH, CoA, H2O, etc.). This makes models unsuitable for:
    - Signal hierarchy analysis (no energy/redox coupling detection)
    - Thermodynamic analysis (incomplete ΔG calculations)
    - Proper biochemical simulation (mass balance violations)
    
    This enricher:
    1. Queries KEGG REACTION database for complete stoichiometry
    2. Identifies missing compounds not in the model
    3. Creates places for missing cofactors
    4. Adds input/output arcs with correct stoichiometry
    
    Usage:
        enricher = KEGGStoichiometryEnricher()
        result = enricher.enrich_document(document)
        print(result.get_summary())
    
    Attributes:
        api_client: KEGG API client for fetching reactions
        cache: Cache of fetched reaction stoichiometries
        position_strategy: Strategy for positioning new places
                          ('cluster' | 'kgml' | 'region')
    """
    
    # Compounds to always filter (not biochemically meaningful in models)
    ALWAYS_FILTER = {
        'C00080',  # H+ (proton)
        'C00001',  # H2O (water) - ubiquitous, rarely limiting
    }
    
    # Key cofactors for signal hierarchy (always include these)
    KEY_COFACTORS = {
        'C00002',  # ATP
        'C00008',  # ADP
        'C00020',  # AMP
        'C00003',  # NAD+
        'C00004',  # NADH
        'C00006',  # NADP+
        'C00005',  # NADPH
        'C00010',  # CoA
        'C00024',  # Acetyl-CoA
        'C00016',  # FAD
        'C00044',  # GTP
        'C00035',  # GDP
        'C00063',  # CTP
        'C00009',  # Orthophosphate (Pi)
        'C00013',  # Diphosphate (PPi)
    }
    
    def __init__(self, 
                 api_client: Optional[KEGGAPIClient] = None,
                 progress_callback=None,
                 position_strategy: str = 'cluster',
                 include_water: bool = False,
                 include_protons: bool = False):
        """Initialize KEGG stoichiometry enricher.
        
        Args:
            api_client: KEGG API client (creates new if None)
            progress_callback: Progress callback function
            position_strategy: How to position new places:
                - 'cluster': Near transition (default)
                - 'kgml': Use KGML coordinates if available
                - 'region': Separate cofactor region
            include_water: Whether to include H2O (default: False)
            include_protons: Whether to include H+ (default: False)
        """
        super().__init__(progress_callback)
        self.api_client = api_client or KEGGAPIClient()
        self.cache: Dict[str, ReactionStoichiometry] = {}
        self.position_strategy = position_strategy
        self.include_water = include_water
        self.include_protons = include_protons
        self.inhibition_extractor = RateInhibitionExtractor()  # Extract inhibitions from rate functions
        self.signal_source_sink_builder = SignalSourceSinkBuilder()  # Build signal source/sink network
        
        # Build filter set
        self.filter_compounds = self.ALWAYS_FILTER.copy()
        if not include_water:
            self.filter_compounds.add('C00001')
        if not include_protons:
            self.filter_compounds.add('C00080')
    
    def get_enricher_name(self) -> str:
        """Get enricher name."""
        return "KEGG Stoichiometry Enricher"
    
    def validate_document(self, document: DocumentModel) -> tuple[bool, List[str]]:
        """Validate if document can be enriched.
        
        Args:
            document: Document to validate
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Get metadata safely (might not exist after fresh load)
        metadata = getattr(document, 'metadata', None)
        
        # Check if document is from KEGG (check document metadata OR places' metadata)
        is_kegg = False
        if metadata and metadata.get('data_source') == 'kegg_import':
            is_kegg = True
        else:
            # Fallback: check if places have KEGG metadata
            if document.places:
                first_place_meta = getattr(document.places[0], 'metadata', None)
                if first_place_meta and first_place_meta.get('data_source') == 'kegg_import':
                    is_kegg = True
                    # Set document metadata for future reference
                    if not hasattr(document, 'metadata'):
                        document.metadata = {}
                    document.metadata['data_source'] = 'kegg_import'
        
        if not is_kegg:
            issues.append("Document is not from KEGG import")
        
        # Check if already enriched
        if metadata and metadata.get('stoichiometry_enriched'):
            issues.append("Document already has stoichiometry enrichment")
        
        # Check if there are transitions with reaction IDs
        reactions_found = sum(1 for t in document.transitions 
                            if hasattr(t, 'metadata') and t.metadata 
                            and t.metadata.get('kegg_reaction_id'))
        
        if reactions_found == 0:
            issues.append("No transitions with KEGG reaction IDs found")
        
        return (len(issues) == 0, issues)
    
    def enrich_document(self, document: DocumentModel) -> EnrichmentResult:
        """Enrich document with complete stoichiometry.
        
        Args:
            document: DocumentModel to enrich (modified in place)
        
        Returns:
            EnrichmentResult with statistics
        """
        start_time = time.time()
        
        # Validate
        is_valid, issues = self.validate_document(document)
        if not is_valid:
            return self._create_failure_result(
                "Document validation failed",
                errors=issues
            )
        
        self.logger.info(f"Starting stoichiometry enrichment for {len(document.transitions)} transitions")
        
        # Collect statistics
        stats = {
            'reactions_processed': 0,
            'reactions_enriched': 0,
            'places_added': 0,
            'arcs_added': 0,
            'inhibitor_arcs_added': 0,
            'signal_sources_added': 0,
            'signal_sinks_added': 0,
            'api_calls': 0,
            'cofactors_by_type': defaultdict(int),
        }
        
        result = EnrichmentResult(success=True, message="Enrichment in progress")
        
        # Process each transition
        transitions_with_reactions = [
            t for t in document.transitions 
            if hasattr(t, 'metadata') and t.metadata 
            and t.metadata.get('kegg_reaction_id')
        ]
        
        total_reactions = len(transitions_with_reactions)
        
        for idx, transition in enumerate(transitions_with_reactions):
            if self.is_cancelled():
                result.success = False
                result.message = "Enrichment cancelled by user"
                break
            
            reaction_id = transition.metadata['kegg_reaction_id']
            self.report_progress(idx, total_reactions, f"Processing {reaction_id}")
            
            # Check if reaction is obsolete
            if is_obsolete(reaction_id):
                # Handle obsolete reactions
                current_id = get_current_reaction(reaction_id)
                reason = get_obsolescence_reason(reaction_id)
                
                if current_id:
                    # Has replacement - update transition metadata and continue
                    self.logger.info(f"{reaction_id} is obsolete, using replacement {current_id}")
                    transition.metadata['kegg_reaction_id'] = current_id
                    transition.metadata['obsolete_reaction_id'] = reaction_id
                    reaction_id = current_id  # Use replacement for enrichment
                else:
                    # No replacement - skip with detailed warning
                    alternatives = suggest_alternatives(reaction_id)
                    warning_msg = f"{reaction_id}: Obsolete KEGG reaction (removed from database)"
                    if reason:
                        warning_msg += f" - {reason}"
                    if alternatives:
                        warning_msg += f". Consider alternatives: {', '.join(alternatives)}"
                    
                    result.add_warning(warning_msg)
                    self.logger.warning(warning_msg)
                    stats['reactions_processed'] += 1
                    continue  # Skip this reaction
            
            try:
                # Fetch stoichiometry
                stoich = self._fetch_reaction_stoichiometry(reaction_id)
                if 'api_call' in locals():
                    stats['api_calls'] += 1
                
                # Enrich transition
                added = self._enrich_transition(document, transition, stoich, result)
                
                stats['reactions_processed'] += 1
                if added['places'] > 0 or added['arcs'] > 0:
                    stats['reactions_enriched'] += 1
                    stats['places_added'] += added['places']
                    stats['arcs_added'] += added['arcs']
                    
                    # Track cofactor types
                    for compound_id in added['compound_ids']:
                        if compound_id in self.KEY_COFACTORS:
                            stats['cofactors_by_type'][compound_id] += 1
                
            except ValueError as e:
                # Likely a 404 - reaction not found in KEGG (not in obsolete list yet)
                error_msg = f"{reaction_id}: {str(e)}"
                result.add_warning(error_msg)
                self.logger.warning(error_msg)  # Just warning, no stack trace
                stats['reactions_processed'] += 1  # Count as processed even if failed
            except Exception as e:
                # Unexpected error - log with stack trace
                error_msg = f"Failed to enrich {reaction_id}: {str(e)}"
                result.add_error(error_msg)
                self.logger.error(error_msg, exc_info=True)
                stats['reactions_processed'] += 1
        
        # Phase 2: Extract Hill inhibition terms from rate functions and create inhibitor arcs
        # This ensures signal hierarchy compliance by moving inhibition logic from rate formulas to topology
        self.logger.info("Phase 2: Extracting inhibition terms from rate functions")
        inhibition_stats = self._extract_and_create_inhibitor_arcs(document, result)
        stats['inhibitor_arcs_added'] = inhibition_stats['arcs_created']
        
        # Phase 3: Build signal source/sink network for signal places
        # Signal places are consumed, so they need source (regeneration) and sink (clearance) transitions
        self.logger.info("Phase 3: Building signal source/sink network")
        signal_network_stats = self.signal_source_sink_builder.build_signal_network(document)
        stats['signal_sources_added'] = signal_network_stats.sources_added
        stats['signal_sinks_added'] = signal_network_stats.sinks_added
        stats['arcs_added'] += signal_network_stats.arcs_added  # Add to total arc count
        
        # Finalize
        duration = time.time() - start_time
        result.duration_seconds = duration
        
        # Update document metadata
        if result.success:
            if not hasattr(document, 'metadata') or not document.metadata:
                document.metadata = {}
            document.metadata['stoichiometry_enriched'] = True
            document.metadata['enrichment_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            result.message = (
                f"Successfully enriched {stats['reactions_enriched']}/{stats['reactions_processed']} reactions. "
                f"Added {stats['places_added']} places, {stats['arcs_added']} arcs, "
                f"{stats['inhibitor_arcs_added']} inhibitor arcs, "
                f"{stats['signal_sources_added']} signal sources, and {stats['signal_sinks_added']} signal sinks."
            )
        
        # Add statistics
        for key, value in stats.items():
            if key == 'cofactors_by_type':
                result.add_statistic(key, dict(value))
            else:
                result.add_statistic(key, value)
        
        self.logger.info(f"Enrichment completed in {duration:.2f}s: {result.message}")
        
        return result
    
    def _fetch_reaction_stoichiometry(self, reaction_id: str) -> ReactionStoichiometry:
        """Fetch and parse reaction stoichiometry from KEGG.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00200")
        
        Returns:
            ReactionStoichiometry object
        
        Raises:
            ValueError: If reaction not found or parsing fails
        """
        # Check cache
        if reaction_id in self.cache:
            return self.cache[reaction_id]
        
        # Normalize reaction ID
        normalized_id = reaction_id
        if reaction_id.startswith("rn:"):
            normalized_id = reaction_id[3:]
        
        # Ensure it has R prefix for KEGG API
        if not normalized_id.startswith("R"):
            # Pad with zeros to 5 digits: 143 -> R00143
            if normalized_id.isdigit():
                normalized_id = f"R{int(normalized_id):05d}"
            else:
                # Already has R prefix or invalid format
                pass
        
        self.logger.debug(f"Fetching stoichiometry for {normalized_id} (original: {reaction_id})")
        
        try:
            # Query KEGG API
            url = f"https://rest.kegg.jp/get/{normalized_id}"
            with urllib.request.urlopen(url, timeout=10) as response:
                text = response.read().decode('utf-8')
            
            # Parse response
            stoich = self._parse_kegg_reaction(normalized_id, text)
            
            # Cache result
            self.cache[reaction_id] = stoich
            self.cache[normalized_id] = stoich
            
            return stoich
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(f"Reaction {normalized_id} not found in KEGG")
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            raise ValueError(f"Failed to fetch {normalized_id}: {str(e)}")
    
    def _parse_kegg_reaction(self, reaction_id: str, text: str) -> ReactionStoichiometry:
        """Parse KEGG reaction response text.
        
        Args:
            reaction_id: Reaction ID
            text: KEGG API response text
        
        Returns:
            ReactionStoichiometry object
        """
        stoich = ReactionStoichiometry(reaction_id=reaction_id, equation="")
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.rstrip()
            
            # Detect sections
            if line.startswith('EQUATION'):
                current_section = 'equation'
                equation = line[12:].strip()
                stoich.equation = equation
                stoich.is_reversible = '<=>' in equation
                
                # Parse equation
                self._parse_equation(equation, stoich)
                
            elif line.startswith('ENZYME'):
                current_section = 'enzyme'
                enzymes = line[12:].strip()
                stoich.enzyme_names = [e.strip() for e in enzymes.split()]
            
            elif line.startswith(' ' * 12) and current_section == 'equation':
                # Continuation of equation
                equation_cont = line[12:].strip()
                stoich.equation += ' ' + equation_cont
                self._parse_equation(equation_cont, stoich)
        
        return stoich
    
    def _parse_equation(self, equation: str, stoich: ReactionStoichiometry):
        """Parse reaction equation and extract compounds.
        
        Args:
            equation: Equation string (e.g., "2 C00002 + C00031 <=> C00008 + C00085")
            stoich: ReactionStoichiometry to populate
        """
        # Split by reaction arrow
        if '<=>' in equation:
            left, right = equation.split('<=>')
        elif '=' in equation:
            left, right = equation.split('=')
        elif '->' in equation:
            left, right = equation.split('->')
        else:
            return  # Can't parse
        
        # Parse substrates (left side)
        for compound_str in left.split('+'):
            compound = self._parse_compound_str(compound_str.strip())
            if compound and compound not in stoich.substrates:
                stoich.substrates.append(compound)
        
        # Parse products (right side)
        for compound_str in right.split('+'):
            compound = self._parse_compound_str(compound_str.strip())
            if compound and compound not in stoich.products:
                stoich.products.append(compound)
    
    def _parse_compound_str(self, compound_str: str) -> Optional[CompoundStoich]:
        """Parse compound string with optional coefficient.
        
        Args:
            compound_str: String like "2 C00002" or "C00031"
        
        Returns:
            CompoundStoich or None if parsing fails
        """
        if not compound_str:
            return None
        
        # Pattern: optional coefficient + compound ID
        match = re.match(r'(?:(\d+)\s+)?([CG]\d{5})', compound_str)
        if not match:
            return None
        
        coeff_str, compound_id = match.groups()
        coefficient = int(coeff_str) if coeff_str else 1
        
        return CompoundStoich(compound_id=compound_id, coefficient=coefficient)
    
    def _enrich_transition(self, 
                          document: DocumentModel,
                          transition: Transition,
                          stoich: ReactionStoichiometry,
                          result: EnrichmentResult) -> Dict[str, any]:
        """Enrich a single transition with missing compounds.
        
        Args:
            document: Document model
            transition: Transition to enrich
            stoich: Reaction stoichiometry
            result: Result object for warnings
        
        Returns:
            Dict with 'places', 'arcs', 'compound_ids' counts
        """
        stats = {'places': 0, 'arcs': 0, 'compound_ids': []}
        
        # Get existing compounds connected to transition
        existing_compounds = self._get_connected_compounds(document, transition)
        
        # Process substrates
        for substrate in stoich.substrates:
            if substrate.compound_id not in existing_compounds:
                if self._should_add_compound(substrate.compound_id):
                    place, was_created = self._find_or_create_place(document, substrate, transition)
                    if place:
                        # Add input arc with unique ID
                        # FORMALISM-COMPLIANT: coefficient=0 → TestArc, signal place + coef>0 → SignalFlowArc
                        arc_id = document.document_controller.id_manager.generate_arc_id()
                        if substrate.coefficient == 0:
                            # Catalyst/cofactor: Use TestArc (non-consuming)
                            from shypn.netobjs.test_arc import TestArc
                            arc = TestArc(
                                source=place,
                                target=transition,
                                id=arc_id,
                                name=arc_id,
                                weight=1.0  # Test arcs use weight=1 for threshold
                            )
                        elif getattr(place, 'is_signal_place', False):
                            # Signal place with weight>0: Use SignalFlowArc
                            arc = SignalFlowArc(
                                source=place,
                                target=transition,
                                id=arc_id,
                                name=arc_id,
                                weight=substrate.coefficient
                            )
                        else:
                            # Normal place: Use regular Arc
                            arc = Arc(
                                source=place,
                                target=transition,
                                id=arc_id,
                                name=arc_id,
                                weight=substrate.coefficient
                            )
                        document.arcs.append(arc)
                        stats['arcs'] += 1
                        stats['compound_ids'].append(substrate.compound_id)
                        if was_created:
                            stats['places'] += 1
        
        # Process products
        for product in stoich.products:
            if product.compound_id not in existing_compounds:
                if self._should_add_compound(product.compound_id):
                    place, was_created = self._find_or_create_place(document, product, transition)
                    if place:
                        # Add output arc with unique ID
                        # FORMALISM-COMPLIANT: coefficient=0 → TestArc, signal place + coef>0 → SignalFlowArc
                        arc_id = document.document_controller.id_manager.generate_arc_id()
                        if product.coefficient == 0:
                            # Catalyst/cofactor: Use TestArc (non-consuming)
                            from shypn.netobjs.test_arc import TestArc
                            arc = TestArc(
                                source=transition,
                                target=place,
                                id=arc_id,
                                name=arc_id,
                                weight=1.0  # Test arcs use weight=1 for threshold
                            )
                        elif getattr(place, 'is_signal_place', False):
                            # Signal place with weight>0: Use SignalFlowArc
                            arc = SignalFlowArc(
                                source=transition,
                                target=place,
                                id=arc_id,
                                name=arc_id,
                                weight=product.coefficient
                            )
                        else:
                            # Normal place: Use regular Arc
                            arc = Arc(
                                source=transition,
                                target=place,
                                id=arc_id,
                                name=arc_id,
                                weight=product.coefficient
                            )
                        document.arcs.append(arc)
                        stats['arcs'] += 1
                        if product.compound_id not in stats['compound_ids']:
                            stats['compound_ids'].append(product.compound_id)
                        if was_created:
                            stats['places'] += 1
        
        return stats
    
    def _get_connected_compounds(self, document: DocumentModel, transition: Transition) -> Set[str]:
        """Get set of compound IDs already connected to transition.
        
        Args:
            document: Document model
            transition: Transition to check
        
        Returns:
            Set of KEGG compound IDs
        """
        compounds = set()
        
        for arc in document.arcs:
            # Input arcs
            if arc.target == transition:
                place = arc.source
                if hasattr(place, 'metadata') and place.metadata:
                    compound_id = place.metadata.get('kegg_id') or place.metadata.get('compound_id')
                    if compound_id:
                        # Extract C00002 from cpd:C00002
                        if ':' in compound_id:
                            compound_id = compound_id.split(':')[-1]
                        compounds.add(compound_id)
            
            # Output arcs
            elif arc.source == transition:
                place = arc.target
                if hasattr(place, 'metadata') and place.metadata:
                    compound_id = place.metadata.get('kegg_id') or place.metadata.get('compound_id')
                    if compound_id:
                        if ':' in compound_id:
                            compound_id = compound_id.split(':')[-1]
                        compounds.add(compound_id)
        
        return compounds
    
    def _should_add_compound(self, compound_id: str) -> bool:
        """Check if compound should be added to model.
        
        Args:
            compound_id: KEGG compound ID
        
        Returns:
            True if compound should be added
        """
        # Always filter certain compounds
        if compound_id in self.filter_compounds:
            return False
        
        # Always include key cofactors
        if compound_id in self.KEY_COFACTORS:
            return True
        
        # Include other compounds by default
        return True
    
    def _find_or_create_place(self,
                             document: DocumentModel,
                             compound: CompoundStoich,
                             near_transition: Transition) -> Tuple[Optional[Place], bool]:
        """Find existing place or create new one for compound.
        
        Args:
            document: Document model
            compound: Compound stoichiometry
            near_transition: Transition to position near
        
        Returns:
            Tuple of (Place object or None if creation failed, was_created boolean)
        """
        # Check if place already exists for this compound
        for place in document.places:
            if hasattr(place, 'metadata') and place.metadata:
                compound_id = place.metadata.get('kegg_id') or place.metadata.get('compound_id')
                if compound_id:
                    if ':' in compound_id:
                        compound_id = compound_id.split(':')[-1]
                    if compound_id == compound.compound_id:
                        return place, False  # Found existing
        
        # Create new place
        place_id = document.document_controller.id_manager.generate_place_id()
        
        # Get name from compound mapper or use ID
        place_name = self._get_compound_name(compound.compound_id)
        
        # Position based on strategy
        x, y = self._calculate_position(document, near_transition, compound.compound_id)
        
        place = Place(
            x=x,
            y=y,
            id=place_id,
            name=place_name,
            label=place_name
        )
        
        # Set initial tokens
        place.tokens = 1
        place.initial_marking = 1
        
        # Add metadata
        if not hasattr(place, 'metadata'):
            place.metadata = {}
        place.metadata['kegg_id'] = compound.compound_id
        place.metadata['compound_id'] = compound.compound_id
        place.metadata['source'] = 'stoichiometry_enrichment'
        place.metadata['data_source'] = 'kegg_enrichment'
        
        # Mark energy metabolites as signal places (Ψₑ)
        if self._is_energy_metabolite(compound.compound_id):
            place.is_signal_place = True
            place.signal_type = SignalType.ENERGY
            if not hasattr(place, 'metadata'):
                place.metadata = {}
            place.metadata['signal_type'] = 'Ψₑ'  # Energy signal type
            place.metadata['is_energy_signal'] = True
            place.metadata['hierarchy_layer'] = 0  # Layer 0: Energy signals
            place.metadata['layer_name'] = 'Layer 0 (Energy)'
            # Apply signal place blue border
            from shypn.utils.color_schema_manager import ColorSchemaManager
            ColorSchemaManager.reset_place_color(place)
            self.logger.debug(
                f"Marked {place_name} ({compound.compound_id}) as energy signal place (Ψₑ, Layer 0)"
            )
        
        document.places.append(place)
        
        return place, True  # Created new
    
    def _get_compound_name(self, compound_id: str) -> str:
        """Get biological name for compound using multi-source strategy.
        
        Priority order:
        1. Cross-reference database (comprehensive, includes KEGG/ChEBI/BiGG)
        2. KEGG API name fetch (real-time compound info)
        3. Common abbreviations (ATP, ADP, NAD+, etc.)
        4. Fallback to descriptive ID (Compound_C00002)
        
        Args:
            compound_id: KEGG compound ID (e.g., C00002)
        
        Returns:
            Biological name or descriptive ID
        """
        # Normalize compound ID (remove prefixes)
        clean_id = compound_id
        if ':' in clean_id:
            clean_id = clean_id.split(':')[-1]
        
        # 1. Try cross-reference database first (most comprehensive)
        try:
            from shypn.thermodynamics.compound_resolver import CompoundResolver
            resolver = CompoundResolver()
            identity = resolver.resolve(clean_id)
            if identity and identity.names:
                # Use primary name
                name = identity.primary_name
                # Prefer shorter abbreviations (ATP vs Adenosine triphosphate)
                if len(identity.names) > 1:
                    short_names = [n for n in identity.names if n and len(n) <= 20]
                    if short_names:
                        name = min(short_names, key=len)
                self.logger.debug(f"Resolved {clean_id} → {name} (via cross-ref DB)")
                return name
        except Exception as e:
            self.logger.debug(f"Cross-ref lookup failed for {clean_id}: {e}")
        
        # 2. Try fetching from KEGG API (real-time name lookup)
        try:
            name = self._fetch_compound_name_from_kegg(clean_id)
            if name:
                self.logger.debug(f"Resolved {clean_id} → {name} (via KEGG API)")
                return name
        except Exception as e:
            self.logger.debug(f"KEGG API lookup failed for {clean_id}: {e}")
        
        # 3. Try common abbreviations (static fallback)
        try:
            from shypn.importer.kegg.compound_mapper import StandardCompoundMapper
            mapper = StandardCompoundMapper()
            if hasattr(mapper, 'COMMON_ABBREVIATIONS'):
                if clean_id in mapper.COMMON_ABBREVIATIONS:
                    name = mapper.COMMON_ABBREVIATIONS[clean_id]
                    self.logger.debug(f"Resolved {clean_id} → {name} (via abbreviations)")
                    return name
        except ImportError:
            pass
        
        # 4. Fallback to descriptive ID
        self.logger.debug(f"Using fallback name for {clean_id}")
        return f"Compound_{clean_id}"
    
    def _fetch_compound_name_from_kegg(self, compound_id: str) -> Optional[str]:
        """Fetch compound name from KEGG API.
        
        Makes an additional API call to get the official KEGG compound name.
        Results are cached to avoid redundant queries.
        
        Args:
            compound_id: KEGG compound ID (C00002)
        
        Returns:
            Primary compound name or None if fetch failed
        """
        # Check cache first
        cache_key = f"name_{compound_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Normalize ID format
        normalized_id = compound_id
        if not normalized_id.startswith("C"):
            if normalized_id.isdigit():
                normalized_id = f"C{int(normalized_id):05d}"
        
        # Query KEGG API
        url = f"https://rest.kegg.jp/get/{normalized_id}"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                text = response.read().decode('utf-8')
                
                # Parse NAME field from KEGG response
                # Format: "NAME    Compound Name; Synonym1; Synonym2"
                for line in text.split('\n'):
                    if line.startswith('NAME'):
                        name_line = line[4:].strip()  # Remove "NAME" prefix
                        # Take first name (before semicolon)
                        primary_name = name_line.split(';')[0].strip()
                        if primary_name:
                            # Clean up the name
                            # Remove trailing commas, periods
                            primary_name = primary_name.rstrip('.,;:')
                            # Prefer abbreviations over long names
                            # Take first word if very long
                            if len(primary_name) > 30 and ' ' in primary_name:
                                primary_name = primary_name.split()[0]
                            
                            # Cache and return
                            self._cache[cache_key] = primary_name
                            return primary_name
        except Exception as e:
            self.logger.debug(f"KEGG name fetch failed for {normalized_id}: {e}")
        
        return None
    
    def _is_energy_metabolite(self, compound_id: str) -> bool:
        """Check if a compound is an energy metabolite that should be a signal place.
        
        Energy metabolites (Ψₑ) are cofactors that:
        - Participate in energy transfer (ATP, ADP, AMP)
        - Participate in redox reactions (NAD+, NADH, NADP+, NADPH)
        - Act as universal currency metabolites
        
        These should be signal places because they:
        - Couple multiple pathways (energy orchestration)
        - Enable hierarchical signal detection
        - Are read-only in thermodynamic analysis
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00002")
        
        Returns:
            True if compound should be marked as energy signal place
        """
        # Remove prefix if present
        clean_id = compound_id.split(':')[-1] if ':' in compound_id else compound_id
        
        # Check if compound is in KEY_COFACTORS (energy metabolites)
        return clean_id in self.KEY_COFACTORS
    
    def _calculate_position(self,
                            document: DocumentModel,
                            near_transition: Transition,
                            compound_id: str) -> Tuple[float, float]:
        """Calculate position for new place based on strategy.
        
        Args:
            document: Document model
            near_transition: Transition to position near
            compound_id: Compound ID
        
        Returns:
            Tuple of (x, y) coordinates
        """
        if self.position_strategy == 'cluster':
            # Position near transition
            offset_x = 80 + (hash(compound_id) % 40)
            offset_y = -60 + (hash(compound_id) % 120)
            return (near_transition.x + offset_x, near_transition.y + offset_y)
        
        elif self.position_strategy == 'region':
            # Separate cofactor region at top
            base_x = 100
            base_y = 50
            index = len([p for p in document.places 
                        if p.metadata and p.metadata.get('source') == 'stoichiometry_enrichment'])
            return (base_x + (index * 60), base_y)
        
        else:  # 'kgml' or default
            # Try to use KGML coordinates, fall back to cluster
            # TODO: Check if compound exists in original KGML
            return self._calculate_position(
                document, near_transition, compound_id
            )
    
    def _extract_and_create_inhibitor_arcs(self, 
                                            document: DocumentModel,
                                            result: EnrichmentResult) -> Dict[str, int]:
        """Extract Hill inhibition terms from rate functions and create inhibitor arcs.
        
        This ensures signal hierarchy compliance by moving inhibition logic from
        rate formulas to network topology (inhibitor arcs with thresholds).
        
        For each transition with a rate function:
        1. Extract Hill inhibition terms (e.g., "/ (1 + (ATP/2.5)^4)")
        2. Find or create inhibitor place
        3. Create InhibitorArc with threshold=Ki
        4. Store Hill coefficient in arc metadata
        5. Update transition rate function (remove inhibition term)
        
        Args:
            document: Document model
            result: Enrichment result for logging warnings
        
        Returns:
            Dict with statistics: {'arcs_created': int, 'transitions_modified': int}
        """
        stats = {'arcs_created': 0, 'transitions_modified': 0}
        
        for transition in document.transitions:
            # Get rate function
            rate_func = None
            if hasattr(transition, 'properties') and transition.properties:
                rate_func = transition.properties.get('rate_function')
            
            if not rate_func or not isinstance(rate_func, str):
                continue
            
            # Extract all inhibition terms
            inhibitions, simplified_rate = self.inhibition_extractor.extract_all(rate_func)
            
            if not inhibitions:
                continue
            
            # Process each inhibition term
            for inhibition in inhibitions:
                # Find inhibitor place by name
                inhibitor_place = self._find_place_by_name(document, inhibition.inhibitor_place)
                
                if not inhibitor_place:
                    warning = (
                        f"Transition {transition.name}: Inhibitor place '{inhibition.inhibitor_place}' "
                        f"not found in model. Skipping inhibitor arc creation."
                    )
                    result.add_warning(warning)
                    self.logger.warning(warning)
                    continue
                
                # Check if inhibitor arc already exists
                if self._has_inhibitor_arc(document, inhibitor_place, transition):
                    self.logger.debug(
                        f"Inhibitor arc {inhibitor_place.name} ⊣ {transition.name} already exists"
                    )
                    continue
                
                # Create inhibitor arc
                arc_id = document.document_controller.id_manager.generate_arc_id()
                inhibitor_arc = InhibitorArc(
                    source=inhibitor_place,
                    target=transition,
                    id=arc_id,
                    name=arc_id,
                    weight=1  # Weight not used for inhibitors
                )
                
                # Set threshold to Ki value
                inhibitor_arc.threshold = inhibition.ki_value
                
                # Store Hill coefficient in metadata
                if not hasattr(inhibitor_arc, 'metadata'):
                    inhibitor_arc.metadata = {}
                inhibitor_arc.metadata['hill_coefficient'] = inhibition.hill_coefficient
                inhibitor_arc.metadata['ki_value'] = inhibition.ki_value
                inhibitor_arc.metadata['source'] = 'rate_function_extraction'
                inhibitor_arc.metadata['original_term'] = inhibition.original_term
                
                document.arcs.append(inhibitor_arc)
                stats['arcs_created'] += 1
                
                self.logger.info(
                    f"Created inhibitor arc: {inhibitor_place.name} ⊣ {transition.name} "
                    f"(Ki={inhibition.ki_value}, n={inhibition.hill_coefficient})"
                )
            
            # Update transition rate function (remove inhibition terms)
            if simplified_rate != rate_func:
                if not hasattr(transition, 'properties'):
                    transition.properties = {}
                transition.properties['rate_function'] = simplified_rate
                stats['transitions_modified'] += 1
                
                self.logger.debug(
                    f"Simplified rate function for {transition.name}: "
                    f"{rate_func} → {simplified_rate}"
                )
        
        if stats['arcs_created'] > 0:
            self.logger.info(
                f"Inhibition extraction complete: {stats['arcs_created']} inhibitor arcs created, "
                f"{stats['transitions_modified']} rate functions simplified"
            )
        
        return stats
    
    def _find_place_by_name(self, document: DocumentModel, place_name: str) -> Optional[Place]:
        """Find a place by its name or label.
        
        Args:
            document: Document model
            place_name: Place name to search for
        
        Returns:
            Place object or None if not found
        """
        for place in document.places:
            if place.name == place_name or place.label == place_name:
                return place
            # Also check ID (e.g., "P1", "P2")
            if place.id == place_name:
                return place
        return None
    
    def _has_inhibitor_arc(self, 
                           document: DocumentModel,
                           source_place: Place,
                           target_transition: Transition) -> bool:
        """Check if inhibitor arc already exists between place and transition.
        
        Args:
            document: Document model
            source_place: Source place
            target_transition: Target transition
        
        Returns:
            True if inhibitor arc exists
        """
        for arc in document.arcs:
            if (isinstance(arc, InhibitorArc) and 
                arc.source == source_place and 
                arc.target == target_transition):
                return True
        return False
