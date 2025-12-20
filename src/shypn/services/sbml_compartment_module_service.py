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
        
        # Step 5: Detect boundary signals (cross-compartment modifiers)
        boundary_signals = self._detect_boundary_signals(
            modules, pathway, species_to_place, warnings
        )
        
        # Step 6: Apply signal detection (if enabled)
        signal_suggestions = None
        if auto_detect_signals and SignalDetectionService is not None:
            signal_suggestions = self._apply_signal_detection(
                document, modules, confidence_threshold, warnings
            )
        
        # Step 7: Validate module architecture (if enabled)
        validation_report = None
        if validate and ModuleCouplingService is not None:
            validation_report = self._validate_modules(document, modules, warnings)
        
        # Build compartment mapping for reference
        compartment_mapping = {
            comp_id: module.module_id
            for comp_id, module in modules.items()
        }
        
        # Log summary
        self.logger.info(
            f"Conversion complete: {len(modules)} modules created, "
            f"{len(boundary_signals)} boundary signals identified"
        )
        
        return {
            'success': True,
            'modules': list(modules.values()),
            'compartment_mapping': compartment_mapping,
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
        """
        compartments = {}
        
        # Try enhanced compartments first (Phase 1 parser)
        if hasattr(pathway, 'compartments_enhanced') and pathway.compartments_enhanced:
            for comp_id, comp in pathway.compartments_enhanced.items():
                compartments[comp_id] = {
                    'id': comp_id,
                    'name': comp.name,
                    'size': comp.size,
                    'spatial_dimensions': comp.spatial_dimensions,
                    'units': comp.units
                }
        # Fallback to legacy compartments dict
        elif hasattr(pathway, 'compartments') and pathway.compartments:
            for comp_id, comp_name in pathway.compartments.items():
                compartments[comp_id] = {
                    'id': comp_id,
                    'name': comp_name,
                    'size': 1.0,
                    'spatial_dimensions': 3,
                    'units': None
                }
        
        return compartments
    
    def _create_modules_from_compartments(
        self,
        document: DocumentModel,
        compartments: Dict[str, Any],
        warnings: List[str]
    ) -> Dict[str, Module]:
        """Create Module objects from compartment data.
        
        Args:
            document: DocumentModel to add modules to
            compartments: Dict of compartment data
            warnings: List to append warnings to
        
        Returns:
            Dict mapping compartment_id to Module object
        """
        modules = {}
        
        for comp_id, comp_data in compartments.items():
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
        
        Args:
            modules: Dict mapping compartment_id to Module
            pathway: ProcessedPathwayData with species info
            species_to_place: Mapping from species ID to Place object
            warnings: List to append warnings to
        """
        unassigned_places = []
        
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
        """Apply signal detection service to identify more signal places.
        
        Args:
            document: DocumentModel with places/transitions
            modules: Dict of modules
            confidence_threshold: Minimum confidence for auto-apply
            warnings: List to append warnings to
        
        Returns:
            Signal detection results dict
        """
        if SignalDetectionService is None:
            warnings.append(
                "SignalDetectionService not available, skipping signal detection"
            )
            return None
        
        self.logger.info("Applying signal detection to modular network...")
        
        service = SignalDetectionService()
        
        # Detect signals across entire network
        suggestions = service.detect_signals(
            document.places,
            document.transitions,
            document.arcs
        )
        
        # Apply suggestions above threshold
        applied_count = service.apply_signal_suggestions(
            suggestions,
            confidence_threshold=confidence_threshold,
            auto_apply=True
        )
        
        # Get report
        report = service.get_detection_report(suggestions)
        
        self.logger.info(
            f"Signal detection complete: {applied_count} signals auto-applied "
            f"(threshold: {confidence_threshold:.0%})"
        )
        
        return {
            'suggestions': suggestions,
            'applied_count': applied_count,
            'report': report
        }
    
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
