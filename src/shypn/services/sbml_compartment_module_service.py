#!/usr/bin/env python3
"""SBML Compartment to Module Conversion Service.

Automatically converts SBML compartments to modular Bio-PN architecture.

Conversion Strategy:
- Maps SBML compartments → Module objects
- Assigns places to modules based on species compartment
- Assigns transitions to modules based on reaction location
- Identifies boundary signals (modifiers crossing compartments)
- Applies signal detection to identify information flow
- Validates resulting modular architecture

Integration Point:
- Called by PathwayConverter after standard conversion
- Enhances DocumentModel with modular structure
- Preserves backward compatibility (optional enhancement)

Design Principles:
- Object-oriented: Works with Module, Place, Transition objects
- Non-destructive: Adds modular structure without changing existing data
- Dual-path compatible: Works for SBML import and manual models
- Service orchestration: Coordinates signal detection and validation

Author: Shypn Development Team
Date: December 2025
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict
import logging

from shypn.data.canvas.document_model import DocumentModel
from shypn.data.pathway.pathway_data import ProcessedPathwayData
from shypn.netobjs import Module, Place, Transition, Arc
from shypn.netobjs.signal_type import SignalType

# Import detection and validation services
try:
    from shypn.services.signal_detection_service import SignalDetectionService
    from shypn.services.module_coupling_service import ModuleCouplingService
except ImportError:
    SignalDetectionService = None
    ModuleCouplingService = None

# Import new signal classification system (December 2024)
try:
    from shypn.analysis.signal_classification import SignalClassifierManager
except ImportError:
    SignalClassifierManager = None


class SBMLCompartmentModuleService:
    """Service for converting SBML compartments to modular Bio-PN architecture.
    
    Conversion pipeline:
    1. Extract compartment information from pathway data
    2. Create Module objects for each compartment
    3. Assign places/transitions to modules
    4. Detect boundary signals (cross-compartment communication)
    5. Apply signal detection to identify signal places
    6. Validate modular architecture integrity
    7. Generate conversion report
    """
    
    def __init__(self):
        """Initialize the service."""
        self.logger = logging.getLogger(__name__)
    
    def convert_compartments_to_modules(
        self,
        document: DocumentModel,
        pathway: ProcessedPathwayData,
        species_to_place: Dict[str, Any],  # species_id → Place
        reaction_to_transition: Dict[str, Any],  # reaction_id → Transition
        auto_detect_signals: bool = True,
        confidence_threshold: float = 0.75,
        validate: bool = True
    ) -> Dict[str, Any]:
        """Convert SBML compartments to modular architecture.
        
        Args:
            document: DocumentModel to enhance with modules
            pathway: ProcessedPathwayData with SBML information
            species_to_place: Mapping from species ID to Place object
            reaction_to_transition: Mapping from reaction ID to Transition object
            auto_detect_signals: If True, apply signal detection automatically
            confidence_threshold: Minimum confidence for auto-applying signals (0-1)
            validate: If True, validate module architecture after conversion
        
        Returns:
            Conversion report dict with:
                - success: bool
                - modules: List[Module]
                - compartment_mapping: Dict[compartment_id, module_id]
                - boundary_signals: List[Place] (cross-compartment signals)
                - signal_suggestions: Dict (if auto_detect_signals=True)
                - validation: Dict (if validate=True)
                - warnings: List[str]
        """
        self.logger.info("Converting SBML compartments to modules...")
        
        warnings = []
        
        # Step 1: Extract compartments from pathway
        compartments = self._extract_compartments(pathway)
        
        if not compartments:
            self.logger.warning("No compartments found in pathway data")
            return {
                'success': False,
                'error': 'No compartments found',
                'warnings': ['SBML model has no compartments defined']
            }
        
        self.logger.info(f"Found {len(compartments)} compartments")
        
        # Step 2: Create modules from compartments
        modules = self._create_modules_from_compartments(
            document, compartments, warnings
        )
        
        # Step 3: Assign places to modules based on species compartment
        self._assign_places_to_modules(
            modules, pathway, species_to_place, warnings
        )
        
        # Step 4: Assign transitions to modules based on reaction location
        self._assign_transitions_to_modules(
            modules, pathway, reaction_to_transition, species_to_place, warnings
        )
        
        # Step 5: Detect energy currency molecules (ATP, NAD, etc.)
        energy_signals = self._detect_energy_currency_signals(
            document, modules, pathway, species_to_place, warnings
        )
        
        # Step 6: Detect boundary signals (cross-compartment modifiers)
        boundary_signals = self._detect_boundary_signals(
            modules, pathway, species_to_place, warnings
        )
        
        # Step 7: Apply signal detection (if enabled) - BOTH legacy and NEW systems
        signal_suggestions = None
        if auto_detect_signals:
            signal_suggestions = self._apply_signal_detection(
                document, modules, confidence_threshold, warnings
            )
        
        # Step 8: Validate module architecture (if enabled)
        validation_report = None
        if validate and ModuleCouplingService is not None:
            validation_report = self._validate_modules(document, modules, warnings)
        
        # Build compartment mapping for reference
        compartment_mapping = {
            comp_id: module.module_id
            for comp_id, module in modules.items()
        }
        
        # Log summary with signal detection details
        signal_count_msg = ""
        if signal_suggestions:
            combined_count = signal_suggestions.get('combined_applied_count', 0)
            legacy_count = signal_suggestions.get('legacy_detection', {}).get('applied_count', 0) if signal_suggestions.get('legacy_detection') else 0
            new_count = signal_suggestions.get('new_classification', {}).get('applied_count', 0) if signal_suggestions.get('new_classification') else 0
            
            signal_count_msg = (
                f", {combined_count} total signals detected "
                f"(legacy: {legacy_count}, rate-based: {new_count})"
            )
        
        self.logger.info(
            f"Conversion complete: {len(modules)} modules created, "
            f"{len(energy_signals)} energy currency, "
            f"{len(boundary_signals)} boundary signals{signal_count_msg}"
        )
        
        return {
            'success': True,
            'modules': list(modules.values()),
            'compartment_mapping': compartment_mapping,
            'energy_signals': energy_signals,
            'boundary_signals': boundary_signals,
            'signal_suggestions': signal_suggestions,
            'validation': validation_report,
            'warnings': warnings
        }
    
    def _extract_compartments(
        self,
        pathway: ProcessedPathwayData
    ) -> Dict[str, Any]:
        """Extract compartment information from pathway data.
        
        Args:
            pathway: ProcessedPathwayData with compartment info
        
        Returns:
            Dict mapping compartment_id to compartment data
            Note: Compartments with spatial_dimensions == 0 are marked as 'is_spatial_marker'
        """
        compartments = {}
        
        # Try enhanced compartments first (Phase 1 parser)
        if hasattr(pathway, 'compartments_enhanced') and pathway.compartments_enhanced:
            for comp_id, comp in pathway.compartments_enhanced.items():
                # Check if this is a spatial marker (point compartment)
                is_spatial_marker = comp.spatial_dimensions == 0
                
                compartments[comp_id] = {
                    'id': comp_id,
                    'name': comp.name,
                    'size': comp.size,
                    'spatial_dimensions': comp.spatial_dimensions,
                    'units': comp.units,
                    'is_spatial_marker': is_spatial_marker
                }
        # Fallback to legacy compartments dict
        elif hasattr(pathway, 'compartments') and pathway.compartments:
            for comp_id, comp_name in pathway.compartments.items():
                compartments[comp_id] = {
                    'id': comp_id,
                    'name': comp_name,
                    'size': 1.0,
                    'spatial_dimensions': 3,
                    'units': None,
                    'is_spatial_marker': False
                }
        
        return compartments
    
    def _create_modules_from_compartments(
        self,
        document: DocumentModel,
        compartments: Dict[str, Any],
        warnings: List[str]
    ) -> Dict[str, Module]:
        """Create Module objects from compartment data.
        
        Skips spatial marker compartments (spatial_dimensions == 0),
        as these represent positional information rather than physical modules.
        
        Args:
            document: DocumentModel to add modules to
            compartments: Dict of compartment data
            warnings: List to append warnings to
        
        Returns:
            Dict mapping compartment_id to Module object
        """
        modules = {}
        
        for comp_id, comp_data in compartments.items():
            # Skip spatial marker compartments (e.g., spatial_dimensions == 0)
            if comp_data.get('is_spatial_marker', False):
                self.logger.info(
                    f"Skipping spatial marker compartment '{comp_id}' "
                    f"({comp_data['name']}, spatial_dimensions={comp_data['spatial_dimensions']})"
                )
                continue
            
            # Create module via DocumentModel
            module = document.create_module(
                name=comp_data['name'],
                compartment_id=comp_id
            )
            
            # Store module reference
            modules[comp_id] = module
            
            self.logger.info(
                f"Created module {module.module_id} for compartment '{comp_id}' "
                f"({comp_data['name']})"
            )
        
        return modules
    
    def _assign_places_to_modules(
        self,
        modules: Dict[str, Module],
        pathway: ProcessedPathwayData,
        species_to_place: Dict[str, Any],
        warnings: List[str]
    ) -> None:
        """Assign places to modules based on species compartment.
        
        Species in spatial marker compartments (spatial_dimensions == 0)
        are marked as SPATIAL signal places instead of being assigned to modules.
        
        Args:
            modules: Dict mapping compartment_id to Module
            pathway: ProcessedPathwayData with species info
            species_to_place: Mapping from species ID to Place object
            warnings: List to append warnings to
        """
        unassigned_places = []
        spatial_signal_places = []
        
        # Get compartment metadata
        compartments = {}
        if hasattr(pathway, 'compartments_enhanced') and pathway.compartments_enhanced:
            compartments = pathway.compartments_enhanced
        
        for species in pathway.species:
            place = species_to_place.get(species.id)
            if not place:
                warnings.append(
                    f"Place not found for species '{species.id}', skipping"
                )
                continue
            
            # Get species compartment
            compartment_id = species.compartment
            
            if not compartment_id:
                unassigned_places.append(place.name)
                warnings.append(
                    f"Species '{species.id}' has no compartment assignment"
                )
                continue
            
            # Check if compartment is a spatial marker (spatial_dimensions == 0)
            compartment_obj = compartments.get(compartment_id)
            is_spatial_marker = (compartment_obj and 
                               compartment_obj.spatial_dimensions == 0)
            
            if is_spatial_marker:
                # Mark as SPATIAL signal place
                place.is_signal_place = True
                place.signal_type = SignalType.SPATIAL
                spatial_signal_places.append(place.name)
                
                # Store compartment metadata on place
                if not hasattr(place, 'metadata'):
                    place.metadata = {}
                place.metadata['compartment_id'] = compartment_id
                place.metadata['compartment_name'] = compartment_obj.name
                place.metadata['spatial_dimensions'] = compartment_obj.spatial_dimensions
                
                self.logger.info(
                    f"Marked place '{place.name}' as SPATIAL signal "
                    f"(spatial marker compartment '{compartment_id}', "
                    f"spatial_dimensions={compartment_obj.spatial_dimensions})"
                )
                continue
            
            # Find corresponding module
            module = modules.get(compartment_id)
            if not module:
                unassigned_places.append(place.name)
                warnings.append(
                    f"Module not found for compartment '{compartment_id}' "
                    f"(species: {species.id})"
                )
                continue
            
            # Assign place to module
            module.add_place(place)
            
            self.logger.debug(
                f"Assigned place '{place.name}' to module {module.name} "
                f"(compartment: {compartment_id})"
            )
        
        if spatial_signal_places:
            self.logger.info(
                f"Detected {len(spatial_signal_places)} SPATIAL signal places from "
                f"spatial marker compartments: {', '.join(spatial_signal_places)}"
            )
        
        if unassigned_places:
            self.logger.warning(
                f"{len(unassigned_places)} places could not be assigned to modules"
            )
    
    def _assign_transitions_to_modules(
        self,
        modules: Dict[str, Module],
        pathway: ProcessedPathwayData,
        reaction_to_transition: Dict[str, Any],
        species_to_place: Dict[str, Any],
        warnings: List[str]
    ) -> None:
        """Assign transitions to modules based on reaction location.
        
        Strategy:
        - If all reactants/products in same compartment → assign to that module
        - If reactants/products span compartments → assign to primary compartment
        - Primary compartment = compartment with most reactants
        
        Args:
            modules: Dict mapping compartment_id to Module
            pathway: ProcessedPathwayData with reaction info
            reaction_to_transition: Mapping from reaction ID to Transition object
            species_to_place: Mapping from species ID to Place object
            warnings: List to append warnings to
        """
        unassigned_transitions = []
        cross_compartment_reactions = []
        
        for reaction in pathway.reactions:
            transition = reaction_to_transition.get(reaction.id)
            if not transition:
                warnings.append(
                    f"Transition not found for reaction '{reaction.id}', skipping"
                )
                continue
            
            # Collect compartments of all reactants and products
            involved_compartments = []
            
            for species_id, _ in reaction.reactants + reaction.products:
                # Find species compartment
                species = next(
                    (s for s in pathway.species if s.id == species_id),
                    None
                )
                if species and species.compartment:
                    involved_compartments.append(species.compartment)
            
            if not involved_compartments:
                unassigned_transitions.append(transition.name)
                warnings.append(
                    f"Reaction '{reaction.id}' has no compartment information"
                )
                continue
            
            # Check if reaction spans multiple compartments
            unique_compartments = set(involved_compartments)
            
            if len(unique_compartments) > 1:
                # Cross-compartment reaction
                cross_compartment_reactions.append(reaction.id)
                
                # Assign to primary compartment (most reactants)
                from collections import Counter
                compartment_counts = Counter(involved_compartments)
                primary_compartment = compartment_counts.most_common(1)[0][0]
                
                self.logger.info(
                    f"Cross-compartment reaction '{reaction.id}' spans "
                    f"{unique_compartments}, assigning to primary: {primary_compartment}"
                )
            else:
                # Single compartment reaction
                primary_compartment = involved_compartments[0]
            
            # Find module and assign
            module = modules.get(primary_compartment)
            if not module:
                unassigned_transitions.append(transition.name)
                warnings.append(
                    f"Module not found for compartment '{primary_compartment}' "
                    f"(reaction: {reaction.id})"
                )
                continue
            
            # Assign transition to module
            module.add_transition(transition)
            
            self.logger.debug(
                f"Assigned transition '{transition.name}' to module {module.name} "
                f"(compartment: {primary_compartment})"
            )
        
        if unassigned_transitions:
            self.logger.warning(
                f"{len(unassigned_transitions)} transitions could not be assigned"
            )
        
        if cross_compartment_reactions:
            self.logger.info(
                f"Found {len(cross_compartment_reactions)} cross-compartment reactions "
                f"(transport/signaling)"
            )
    
    def _detect_energy_currency_signals(
        self,
        document: DocumentModel,
        modules: Dict[str, Module],
        pathway: ProcessedPathwayData,
        species_to_place: Dict[str, Place],
        warnings: List[str]
    ) -> List[Place]:
        """Detect and mark energy currency molecules as signal places (Ψₑ).
        
        Energy currency molecules (ATP, ADP, AMP, NAD, NADH, NADP, NADPH, 
        FAD, FADH2, CoA, etc.) represent energy transfer and redox state.
        They couple multiple reactions through shared energy/redox pools
        and should be marked as Energy signals (Ψₑ).
        
        Detection strategy:
        1. Name/ID pattern matching (ATP, NAD, etc.)
        2. ChEBI ID matching for known energy carriers
        3. High connectivity (modifier in multiple reactions)
        
        Args:
            modules: Dict of Module objects
            pathway: ProcessedPathwayData with species/reactions
            species_to_place: Mapping from species ID to Place
            warnings: List to append warnings to
        
        Returns:
            List of Place objects identified as energy signals
        """
        # Known energy currency molecule patterns
        ENERGY_CURRENCY_PATTERNS = {
            # Adenylates (energy charge)
            'ATP', 'ADP', 'AMP', 'cAMP', 'dATP', 'dADP', 'dAMP',
            # NAD/NADP (redox)
            'NAD', 'NADH', 'NAD+', 'NADP', 'NADPH', 'NADP+',
            # FAD (redox)
            'FAD', 'FADH', 'FADH2',
            # Coenzyme A
            'CoA', 'CoASH', 'Acetyl-CoA', 'AcCoA',
            # GTP/GDP (G-proteins, translation)
            'GTP', 'GDP', 'GMP', 'dGTP', 'dGDP',
            # UTP/UDP (glycosylation)
            'UTP', 'UDP', 'UMP', 'dUTP', 'dUDP',
            # CTP/CDP (phospholipids)
            'CTP', 'CDP', 'CMP', 'dCTP', 'dCDP',
            # Inorganic phosphate
            'Pi', 'PPi', 'Phosphate',
        }
        
        # ChEBI IDs for energy currencies (subset)
        ENERGY_CURRENCY_CHEBI = {
            'CHEBI:15422',  # ATP
            'CHEBI:456216', # ADP
            'CHEBI:456215', # AMP
            'CHEBI:57540',  # NAD+
            'CHEBI:57945',  # NADH
            'CHEBI:58349',  # NADP+
            'CHEBI:57783',  # NADPH
            'CHEBI:57692',  # FAD
            'CHEBI:57618',  # FADH2
            'CHEBI:57287',  # CoA
            'CHEBI:15377',  # H2O
            'CHEBI:18009',  # Inorganic phosphate
        }
        
        energy_signals = []
        
        # Iterate through all species
        for species in pathway.species:
            place = species_to_place.get(species.id)
            if not place:
                continue
            
            # Skip if already marked as signal
            if place.is_signal_place:
                continue
            
            is_energy_currency = False
            detection_reason = None
            
            # Check 1: Name/ID pattern matching (case-insensitive)
            species_name_upper = species.name.upper() if species.name else ''
            species_id_upper = species.id.upper()
            
            for pattern in ENERGY_CURRENCY_PATTERNS:
                # Exact match or as part of compound name
                if pattern in species_name_upper or pattern in species_id_upper:
                    # Avoid false positives like "ATPASE" (enzyme, not ATP)
                    if pattern + 'ASE' not in species_name_upper and pattern + 'ASE' not in species_id_upper:
                        is_energy_currency = True
                        detection_reason = f"name pattern '{pattern}'"
                        break
            
            # Check 2: ChEBI ID matching
            if not is_energy_currency and hasattr(species, 'chebi_id') and species.chebi_id:
                if species.chebi_id in ENERGY_CURRENCY_CHEBI:
                    is_energy_currency = True
                    detection_reason = f"ChEBI ID {species.chebi_id}"
            
            # Check 3: High connectivity as modifier (heuristic)
            # Energy carriers are often modifiers in many reactions
            if not is_energy_currency:
                modifier_count = sum(
                    1 for rxn in pathway.reactions 
                    if species.id in rxn.modifiers
                )
                # If modifier in 5+ reactions, likely a cofactor
                if modifier_count >= 5:
                    is_energy_currency = True
                    detection_reason = f"modifier in {modifier_count} reactions"
            
            # Mark as energy signal if detected
            if is_energy_currency:
                place.is_signal_place = True
                place.signal_type = SignalType.ENERGY  # Ψₑ
                energy_signals.append(place)
                
                self.logger.info(
                    f"Detected energy signal: '{place.name}' (Ψₑ) - {detection_reason}"
                )
        
        if energy_signals:
            self.logger.info(
                f"Energy currency detection: {len(energy_signals)} signals identified"
            )
            
            # Re-color arcs for newly detected signal places
            self._recolor_signal_arcs(document, energy_signals)
        
        return energy_signals
    
    def _recolor_signal_arcs(self, document: DocumentModel, signal_places: List[Place]) -> None:
        """Re-color arcs connected to signal places with orange.
        
        This is called after signal detection to update arc colors for newly
        identified signal places (e.g., energy currencies detected by heuristics).
        
        Args:
            document: DocumentModel with arcs
            signal_places: List of newly detected signal places
        """
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        from shypn.utils.color_schema_manager import ColorSchemaManager
        
        recolored_count = 0
        
        # Color ONLY SignalFlowArcs (light gray)
        # TestArcs remain blue, regular Arcs remain black per normalized color schema
        for arc in document.arcs:
            if isinstance(arc, SignalFlowArc):
                # Color if connected to a signal place
                if arc.source in signal_places or arc.target in signal_places:
                    ColorSchemaManager.reset_arc_color(arc)
                    recolored_count += 1
        
        if recolored_count > 0:
            self.logger.info(
                f"Re-colored {recolored_count} arcs to light gray for {len(signal_places)} signal places"
            )
    
    def _detect_boundary_signals(
        self,
        modules: Dict[str, Module],
        pathway: ProcessedPathwayData,
        species_to_place: Dict[str, Any],
        warnings: List[str]
    ) -> List[Place]:
        """Detect boundary signals (cross-compartment modifiers).
        
        SBML modifiers that act on reactions in different compartments
        are strong candidates for signal places (information flow).
        
        Args:
            modules: Dict mapping compartment_id to Module
            pathway: ProcessedPathwayData with reaction info
            species_to_place: Mapping from species ID to Place object
            warnings: List to append warnings to
        
        Returns:
            List of Place objects identified as boundary signals
        """
        boundary_signals = []
        
        for reaction in pathway.reactions:
            # Get reaction compartment (from reactants)
            reaction_compartments = set()
            for species_id, _ in reaction.reactants + reaction.products:
                species = next(
                    (s for s in pathway.species if s.id == species_id),
                    None
                )
                if species and species.compartment:
                    reaction_compartments.add(species.compartment)
            
            if not reaction_compartments:
                continue
            
            # Check modifiers for cross-compartment signaling
            for modifier_species_id in reaction.modifiers:
                # Get modifier compartment
                modifier_species = next(
                    (s for s in pathway.species if s.id == modifier_species_id),
                    None
                )
                
                if not modifier_species or not modifier_species.compartment:
                    continue
                
                # Check if modifier is from different compartment
                if modifier_species.compartment not in reaction_compartments:
                    # Cross-compartment modifier = boundary signal
                    place = species_to_place.get(modifier_species_id)
                    if place and place not in boundary_signals:
                        boundary_signals.append(place)
                        
                        # Mark as signal place
                        place.is_signal_place = True
                        place.signal_type = SignalType.REGULATORY  # Cross-compartment modifiers typically regulatory
                        
                        # Add to boundary_signals of relevant modules
                        for comp_id in reaction_compartments:
                            module = modules.get(comp_id)
                            if module:
                                module.add_boundary_signal(place)
                        
                        # Also add to modifier's own module
                        modifier_module = modules.get(modifier_species.compartment)
                        if modifier_module:
                            modifier_module.add_boundary_signal(place)
                        
                        self.logger.info(
                            f"Detected boundary signal: '{place.name}' "
                            f"(modifier from {modifier_species.compartment} "
                            f"→ reaction in {reaction_compartments})"
                        )
        
        return boundary_signals
    
    def _apply_signal_detection(
        self,
        document: DocumentModel,
        modules: Dict[str, Module],
        confidence_threshold: float,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Apply signal detection to identify signal places.
        
        Uses TWO complementary detection systems:
        1. Legacy SignalDetectionService: Simple heuristics (modifier-only, name patterns)
        2. NEW ClassifierManager: Rate function analysis (Michaelis-Menten, Hill, etc.)
        
        The new system analyzes kinetic expressions from SBML rate laws,
        which is more accurate for complex biochemical models.
        
        Args:
            document: DocumentModel with places/transitions
            modules: Dict of modules
            confidence_threshold: Minimum confidence for auto-apply
            warnings: List to append warnings to
        
        Returns:
            Signal detection results dict with both legacy and new results
        """
        results = {
            'legacy_detection': None,
            'new_classification': None,
            'combined_applied_count': 0
        }
        
        # ========================================================================
        # LEGACY DETECTION: Heuristic-based (modifier-only, name patterns)
        # ========================================================================
        if SignalDetectionService is not None:
            self.logger.info("Applying legacy signal detection (heuristic-based)...")
            
            service = SignalDetectionService()
            
            # Detect signals across entire network
            legacy_suggestions = service.detect_signals(
                document.places,
                document.transitions,
                document.arcs
            )
            
            # Apply suggestions above threshold
            legacy_applied = service.apply_signal_suggestions(
                legacy_suggestions,
                confidence_threshold=confidence_threshold,
                auto_apply=True
            )
            
            # Get report
            legacy_report = service.get_detection_report(legacy_suggestions)
            
            results['legacy_detection'] = {
                'suggestions': legacy_suggestions,
                'applied_count': legacy_applied,
                'report': legacy_report
            }
            
            self.logger.info(
                f"Legacy detection: {legacy_applied} signals auto-applied "
                f"(threshold: {confidence_threshold:.0%})"
            )
        else:
            warnings.append(
                "SignalDetectionService not available, skipping legacy detection"
            )
        
        # ========================================================================
        # NEW CLASSIFICATION: Rate function analysis (Michaelis-Menten, Hill, etc.)
        # ========================================================================
        if SignalClassifierManager is not None:
            self.logger.info("Applying NEW signal classification (rate function analysis)...")
            
            try:
                # Create classifier manager (needs a model-like object with places/transitions/arcs)
                # Build a temporary model wrapper
                class ModelWrapper:
                    def __init__(self, places, transitions, arcs):
                        self.places = places
                        self.transitions = transitions
                        self.arcs = arcs
                
                model_wrapper = ModelWrapper(
                    document.places,
                    document.transitions,
                    document.arcs
                )
                
                manager = SignalClassifierManager(model_wrapper)
                
                # Classify all places (not just existing signal places)
                classifications = manager.classify_all_signals(signal_places_only=False)
                
                # Apply classifications above threshold - convert to expected format
                new_applied = 0
                for place_name, (signal_type, confidence) in classifications.items():
                    if confidence >= confidence_threshold:
                        # Find place by name
                        place = next((p for p in document.places if p.name == place_name), None)
                        if place:
                            # Set signal type on place
                            place.signal_type = signal_type
                            new_applied += 1
                        
                        self.logger.debug(
f"Classified {place.name} as {signal_type if isinstance(signal_type, str) else signal_type.name} "
                            f"(confidence: {confidence:.2f})"
                        )
                
                # Generate summary directly from classifications dict
                # (generate_report method does not exist)
                summary_lines = []
                for place_name, (sig_type, conf) in classifications.items():
                    type_str = sig_type if isinstance(sig_type, str) else sig_type.name
                    summary_lines.append(f"  {place_name}: {type_str} ({conf:.0%})")
                new_report = "\n".join(summary_lines) if summary_lines else "No classifications"
                
                results['new_classification'] = {
                    'classifications': classifications,
                    'applied_count': new_applied,
                    'report': new_report
                }
                
                self.logger.info(
                    f"NEW classification: {new_applied} signals classified "
                    f"(threshold: {confidence_threshold:.0%})"
                )
                
                # Calculate combined count (avoid double-counting)
                results['combined_applied_count'] = (
                    results.get('legacy_detection', {}).get('applied_count', 0) +
                    new_applied
                )
                
            except Exception as e:
                import traceback
                self.logger.error(f"Error in new signal classification: {e}")
                traceback.print_exc()
                warnings.append(f"NEW signal classification failed: {str(e)}")
        else:
            warnings.append(
                "SignalClassifierManager not available, skipping new classification. "
                "The new rate function-based classification system provides more "
                "accurate signal detection for SBML models with kinetic expressions."
            )
        
        return results
    
    def _validate_modules(
        self,
        document: DocumentModel,
        modules: Dict[str, Module],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Validate modular architecture integrity.
        
        Args:
            document: DocumentModel with all objects
            modules: Dict of modules
            warnings: List to append warnings to
        
        Returns:
            Validation results dict
        """
        if ModuleCouplingService is None:
            warnings.append(
                "ModuleCouplingService not available, skipping validation"
            )
            return None
        
        self.logger.info("Validating modular architecture...")
        
        service = ModuleCouplingService()
        
        # Validate coupling
        validation = service.validate_coupling(
            list(modules.values()),
            document.places,
            document.transitions,
            document.arcs
        )
        
        # Log validation results
        if validation['valid']:
            self.logger.info(
                f"✓ Validation passed - Independence score: "
                f"{validation['independence_score']:.1%}"
            )
        else:
            self.logger.warning(
                f"✗ Validation failed - {len(validation['violations'])} violations"
            )
            
            # Add critical violations to warnings
            for violation in validation['violations'][:3]:  # First 3 violations
                warnings.append(f"Module violation: {violation['message']}")
        
        return validation
    
    def get_conversion_report(self, conversion_result: Dict[str, Any]) -> str:
        """Generate human-readable conversion report.
        
        Args:
            conversion_result: Dict from convert_compartments_to_modules()
        
        Returns:
            Formatted text report
        """
        lines = ["SBML Compartment to Module Conversion Report"]
        lines.append("=" * 70)
        
        # Status
        status = "✓ SUCCESS" if conversion_result.get('success') else "✗ FAILED"
        lines.append(f"\nStatus: {status}")
        
        # Modules created
        modules = conversion_result.get('modules', [])
        if modules:
            lines.append(f"\nModules Created ({len(modules)}):")
            for module in modules:
                place_count = len(module.places)
                transition_count = len(module.transitions)
                signal_count = len(module.boundary_signals)
                lines.append(
                    f"  {module.module_id}: {module.name} "
                    f"({place_count} places, {transition_count} transitions, "
                    f"{signal_count} signals)"
                )
        
        # Energy signals
        energy_signals = conversion_result.get('energy_signals', [])
        if energy_signals:
            lines.append(f"\nEnergy Signals (Ψₑ) ({len(energy_signals)}):")
            for signal in energy_signals[:10]:  # First 10
                lines.append(f"  {signal.name}")
            if len(energy_signals) > 10:
                lines.append(f"  ... and {len(energy_signals) - 10} more")
        
        # Boundary signals
        boundary_signals = conversion_result.get('boundary_signals', [])
        if boundary_signals:
            lines.append(f"\nBoundary Signals ({len(boundary_signals)}):")
            for signal in boundary_signals[:5]:  # First 5
                lines.append(f"  {signal.name} ({signal.signal_type.value})")
            if len(boundary_signals) > 5:
                lines.append(f"  ... and {len(boundary_signals) - 5} more")
        
        # Signal detection results
        signal_suggestions = conversion_result.get('signal_suggestions')
        if signal_suggestions:
            applied = signal_suggestions.get('applied_count', 0)
            lines.append(f"\nSignal Detection: {applied} signals auto-applied")
        
        # Validation results
        validation = conversion_result.get('validation')
        if validation:
            score = validation.get('independence_score', 0)
            violations = validation.get('violations', [])
            lines.append(f"\nValidation:")
            lines.append(f"  Independence Score: {score:.1%}")
            lines.append(f"  Violations: {len(violations)}")
        
        # Warnings
        warnings = conversion_result.get('warnings', [])
        if warnings:
            lines.append(f"\nWarnings ({len(warnings)}):")
            for warning in warnings[:3]:  # First 3
                lines.append(f"  {warning}")
            if len(warnings) > 3:
                lines.append(f"  ... and {len(warnings) - 3} more")
        
        return "\n".join(lines)
