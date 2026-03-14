"""
SBML Kinetics Integration Service

Service for integrating SBML kinetic data into Petri net transitions.

Architecture:
- Uses object references (not IDs) to avoid ID conflicts
- Creates SBMLKineticMetadata for transitions with kinetic laws
- Respects existing metadata (never overwrites SBML or manual data)
- Thin service layer - delegates to domain classes

Design Principles:
- Object-oriented: Works with Transition objects directly
- Reference-based: Passes object references, not string IDs
- Immutable source: SBML kinetics are locked by default
- Separation of concerns: Service orchestrates, metadata classes handle logic
"""

from typing import List, Dict, Optional, Tuple
import logging

from shypn.data.pathway.pathway_data import PathwayData, Reaction, KineticLaw
from shypn.data.kinetics import (
    SBMLKineticMetadata,
    KineticMetadata,
    ConfidenceLevel,
    KineticSource
)
from shypn.thermodynamics.simulation_integration import ThermodynamicSimulationValidator
from shypn.thermodynamics.sbml_compound_mapper import SBMLCompoundMapper


class SBMLKineticsIntegrationService:
    """
    Service for integrating SBML kinetic data into transitions.
    
    Uses object references to map reactions to transitions.
    Creates SBMLKineticMetadata for definitive kinetic tracking.
    """
    
    def __init__(self, enable_thermodynamic_validation: bool = True):
        """
        Initialize the service.
        
        Args:
            enable_thermodynamic_validation: Enable automatic thermodynamic validation
                                           for reversible reactions (default: True)
        """
        self.logger = logging.getLogger(__name__)
        self.enable_thermodynamic_validation = enable_thermodynamic_validation
        
        # Initialize thermodynamic validator (lazy instantiation)
        self._thermodynamic_validator = None
        self._compound_mapper = None
    
    def integrate_kinetics(
        self,
        transitions: List,  # List of Transition objects
        pathway_data: PathwayData,
        transition_reaction_map: Optional[Dict] = None,
        source_file: Optional[str] = None,
        document: Optional = None  # DocumentModel for place access
    ) -> Dict[str, bool]:
        """
        Integrate SBML kinetic laws into transitions.
        
        Uses object references to map transitions to reactions.
        Only integrates kinetics that don't already exist (preservation logic).
        
        Args:
            transitions: List of Transition objects to enhance
            pathway_data: PathwayData with reactions and kinetic laws
            transition_reaction_map: Optional dict mapping transition object → reaction object
                                    If None, uses transition.name to match reaction.id
            source_file: SBML source filename (for metadata tracking)
            document: Optional DocumentModel for accessing places (needed for species mapping)
        
        Returns:
            Dict mapping transition.name → success (True/False)
        """
        if not transitions:
            self.logger.warning("No transitions to integrate")
            return {}
        
        # Store pathway_data for access to global parameters and compartments
        self.pathway_data = pathway_data
        
        # Build species-to-place name mapping if document provided
        self.species_to_place_map = {}
        if document:
            self.species_to_place_map = self._build_species_to_place_map(document)
            self.logger.info(f"Built species mapping for {len(self.species_to_place_map)} species")
        
        self.logger.info(f"Integrating SBML kinetics for {len(transitions)} transitions")
        
        # Build mapping if not provided (uses object references)
        if transition_reaction_map is None:
            transition_reaction_map = self._build_transition_reaction_map(
                transitions,
                pathway_data.reactions
            )
        
        results = {}
        integrated_count = 0
        skipped_count = 0
        
        for transition in transitions:
            # Skip source/sink transitions
            if transition.is_source or transition.is_sink:
                self.logger.debug(f"Skipping source/sink transition: {transition.name}")
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Check if should preserve existing kinetics
            if self._should_preserve_existing(transition):
                self.logger.debug(
                    f"Preserving existing kinetics for {transition.name} "
                    f"(source: {transition.kinetic_metadata.source.value})"
                )
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Get corresponding reaction (using object reference from map)
            reaction = transition_reaction_map.get(transition)
            if reaction is None:
                self.logger.debug(f"No reaction found for transition: {transition.name}")
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Check if reaction has kinetic law
            if reaction.kinetic_law is None:
                self.logger.debug(f"No kinetic law for reaction: {reaction.id}")
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Integrate the kinetic law
            success = self._integrate_kinetic_law(
                transition,
                reaction,
                reaction.kinetic_law,
                source_file
            )
            
            results[transition.name] = success
            if success:
                integrated_count += 1
            else:
                skipped_count += 1
        
        self.logger.info(
            f"SBML kinetics integration complete: "
            f"{integrated_count} integrated, {skipped_count} skipped"
        )
        
        # NOTE: Removed automatic transition type conversion (validate_and_fix_transition_types)
        # Validation issues are now presented to user in import dialog for informed decision.
        # User can choose: auto-convert to continuous | use hybrid | proceed anyway | cancel
        # This prevents silent behavior modifications that change modeler's intent.
        
        return results
    
    def _build_transition_reaction_map(
        self,
        transitions: List,
        reactions: List[Reaction]
    ) -> Dict:
        """
        Build mapping from transition objects to reaction objects.
        
        Uses object references (not IDs) to avoid ID conflicts.
        Matches by name: transition.name → reaction.id
        
        Args:
            transitions: List of Transition objects
            reactions: List of Reaction objects
        
        Returns:
            Dict mapping transition object → reaction object
        """
        # Create reaction lookup by ID (for matching)
        reaction_by_id = {reaction.id: reaction for reaction in reactions}
        
        # Build object reference map
        transition_reaction_map = {}
        
        for transition in transitions:
            # Try to match transition.name to reaction.id
            # (Common convention: transition name matches reaction ID)
            reaction = reaction_by_id.get(transition.name)
            
            if reaction is not None:
                # Store object reference (not ID string)
                transition_reaction_map[transition] = reaction
            else:
                self.logger.debug(
                    f"No reaction match for transition: {transition.name}"
                )
        
        self.logger.info(
            f"Built transition→reaction map: "
            f"{len(transition_reaction_map)}/{len(transitions)} matched"
        )
        
        return transition_reaction_map
    
    def _build_species_to_place_map(self, document) -> Dict[str, str]:
        """
        Build mapping from SBML species IDs to Petri net place names.
        
        For SBML imports, place names are biological identifiers (e.g., "Glucose", "ATP", "GlcX")
        not system IDs (e.g., "P1", "P2"), matching manual model behavior.
        
        Uses place.metadata['species_id'] to map species IDs → place names.
        
        Args:
            document: DocumentModel with places
        
        Returns:
            Dict mapping species_id (e.g., "GlcX") → place_name (e.g., "GlcX" or "Glucose")
        """
        species_map = {}
        
        for place in document.places:
            # Check if place has species_id in metadata
            if hasattr(place, 'metadata') and 'species_id' in place.metadata:
                species_id = place.metadata['species_id']
                place_name = place.name  # Biological name (e.g., "Glucose", "GlcX", "ATP")
                species_map[species_id] = place_name
                
                self.logger.debug(f"Mapped species '{species_id}' → place '{place_name}'")
        
        return species_map
    
    def _translate_formula_to_petri_net(self, formula: str) -> str:
        """
        Translate SBML formula from species IDs to Petri net place names.
        
        For SBML imports with data_source='sbml_import', place names are biological
        identifiers (e.g., "Glucose", "ATP", "GlcX"), matching manual model behavior.
        
        This ensures SBML formulas work the same way as manually created models:
        - Manual model: "Glucose * ATP" (uses place.name directly)
        - SBML import: "GlcX * ATP" (species.id mapped to place.name)
        
        Also converts SBML math operators to Python:
        - ^ (exponentiation) → ** (Python power operator)
        
        IMPORTANT: Species IDs with hyphens (e.g., MOS-P, Erk2-pp) are sanitized
        to underscores (MOS_P, Erk2_pp) for Python compatibility.
        
        Example:
            Input:  "cytosol * V10m * ADP^2 / ((K10PEP + PEP) * (K10ADP + ADP))"
            Output: "cytosol * V10m * ADP**2 / ((K10PEP + PEP) * (K10ADP + ADP))"
            (Note: If ADP's place.name is "ADP", formula uses "ADP" not "P5")
        
        Args:
            formula: SBML formula with species IDs and SBML operators
        
        Returns:
            Translated formula with place names and Python operators
        """
        if not formula:
            return formula
        
        translated = formula
        
        # First, sanitize any hyphens in the formula to underscores
        # This handles species IDs that appear in the formula before replacement
        import re
        
        # Replace species names with place names
        if self.species_to_place_map:
            # Sort species by length (descending) to avoid partial replacements
            # Example: Replace "ATP" before "AT" to avoid "ATP" → "P3P"
            sorted_species = sorted(self.species_to_place_map.keys(), key=len, reverse=True)
            
            for species_id in sorted_species:
                place_name = self.species_to_place_map[species_id]
                
                # Handle both original (with hyphens) and sanitized (with underscores) versions
                # Original: MOS-P, Sanitized: MOS_P
                species_id_sanitized = species_id.replace('-', '_')
                
                # Use word boundary replacement to avoid partial matches
                # Replace "ADP" but not "ADPK" or "mADP"
                # Try sanitized version first (what's in the formula)
                pattern_sanitized = r'\b' + re.escape(species_id_sanitized) + r'\b'
                translated = re.sub(pattern_sanitized, place_name, translated)
                
                # Also try original version (for backwards compatibility)
                pattern_original = r'\b' + re.escape(species_id) + r'\b'
                translated = re.sub(pattern_original, place_name, translated)
        
        # Convert SBML operators to Python operators
        # ^ (exponentiation) → ** (Python power)
        translated = translated.replace('^', '**')
        
        return translated
    
    def _should_preserve_existing(self, transition) -> bool:
        """
        Check if existing kinetics should be preserved.
        
        Preserves:
        - SBML kinetics (definitive)
        - Manual kinetics (high confidence)
        - Locked metadata
        
        Args:
            transition: Transition object
        
        Returns:
            True if should preserve, False if can overwrite
        """
        if not hasattr(transition, 'kinetic_metadata') or transition.kinetic_metadata is None:
            return False
        
        return KineticMetadata.should_preserve(transition.kinetic_metadata)
    
    def _integrate_kinetic_law(
        self,
        transition,
        reaction: Reaction,
        kinetic_law: KineticLaw,
        source_file: Optional[str]
    ) -> bool:
        """
        Integrate kinetic law into transition with metadata.
        
        Sets:
        - transition.kinetic_metadata: SBMLKineticMetadata object with formula and parameters
        - transition.properties['rate_function']: SBML formula for evaluation during simulation
        - transition.rate: Fallback numeric rate (Vmax for MM, k for mass action)
        
        The rate_function is the SBML formula that can be evaluated with Python/numpy
        during simulation, using place names (concentrations) as variables.
        
        Args:
            transition: Transition object (passed by reference)
            reaction: Reaction object (passed by reference)
            kinetic_law: KineticLaw from SBML
            source_file: SBML source filename
        
        Returns:
            True if integrated successfully
        """
        try:
            # Extract SBML metadata from kinetic law (if available)
            sbml_metadata = getattr(kinetic_law, 'sbml_metadata', {})
            
            # Merge parameters: global parameters (includes compartment sizes) + local kinetic law parameters
            all_parameters = {}
            global_params = set()
            local_params = set()
            
            # 1. Add global parameters from SBML model (includes compartment sizes)
            if hasattr(self, 'pathway_data') and self.pathway_data.parameters:
                all_parameters.update(self.pathway_data.parameters)
                global_params = set(self.pathway_data.parameters.keys())
                self.logger.debug(f"  Added {len(self.pathway_data.parameters)} global parameters (incl. compartments)")
            
            # 2. Add local kinetic law parameters (these override globals if duplicate)
            if kinetic_law.parameters:
                local_params = set(kinetic_law.parameters.keys())
                overridden = global_params & local_params
                if overridden:
                    self.logger.debug(f"  Local parameters override globals: {overridden}")
                all_parameters.update(kinetic_law.parameters)
                self.logger.debug(f"  Added {len(kinetic_law.parameters)} local parameters")
            
            # Create SBMLKineticMetadata with all parameters
            metadata = SBMLKineticMetadata(
                source_file=source_file,
                rate_type=kinetic_law.rate_type,
                formula=kinetic_law.formula,
                parameters=all_parameters,
                sbml_level=sbml_metadata.get('sbml_level'),
                sbml_version=sbml_metadata.get('sbml_version'),
                sbml_reaction_id=sbml_metadata.get('sbml_reaction_id'),
                sbml_model_id=sbml_metadata.get('sbml_model_id'),
            )
            
            # Attach metadata to transition (object reference, no ID storage)
            transition.kinetic_metadata = metadata
            
            # Set rate_function from SBML formula for evaluation during simulation
            # Store formulas using biological place names (matching manual model behavior)
            if kinetic_law.formula:
                # Translate formula to use place names (e.g., "GlcX", "ATP", "Glucose")
                # NOT system IDs (P1, P2, P3), matching how manual models work
                translated_formula = self._translate_formula_to_petri_net(kinetic_law.formula)
                
                # Store in transition.rate (like manual models do)
                # This makes SBML imports consistent with interactive creation
                transition.rate = translated_formula
                
                # Also store in properties for backward compatibility
                transition.properties['rate_function'] = translated_formula
                
                # Store original SBML formula for reference (display in UI)
                transition.properties['rate_function_display'] = kinetic_law.formula
                
                # Store species mapping for reference
                if self.species_to_place_map:
                    transition.properties['species_map'] = self.species_to_place_map.copy()
                
                self.logger.debug(
                    f"Set rate formulas for {transition.name}:"
                )
                self.logger.debug(f"  Original SBML: {kinetic_law.formula[:60]}...")
                self.logger.debug(f"  Petri net: {translated_formula[:60]}...")
                
                # Mark reversible reactions in properties (but don't set directional rates)
                # SBML reversible reactions use net rate formula (forward - reverse combined)
                # Setting rate_forward = rate_reverse = formula would give net = 0!
                if reaction.reversible:
                    if not hasattr(transition, 'properties'):
                        transition.properties = {}
                    transition.properties['is_reversible'] = True
                    transition.properties['reversible_note'] = (
                        "SBML reversible reaction - formula represents net rate (forward - reverse). "
                        "Negative rates indicate reverse flow. "
                        "Use properties dialog to split into separate rate_forward/rate_reverse if needed."
                    )
                    
                    self.logger.debug(
                        "  Reversible reaction - marked in properties (net rate formula)"
                    )
                    
                    # Validate thermodynamic consistency of reversible reaction
                    validation_result = self._validate_reversible_reaction(
                        reaction,
                        transition,
                        kinetic_law
                    )
                    
                    if validation_result:
                        transition.properties['thermodynamic_validation'] = validation_result
                        
                        # Log validation status
                        status = validation_result.get('status', 'unknown')
                        if status == 'valid':
                            self.logger.debug(
                                f"  Thermodynamic validation: PASSED "
                                f"(deviation: {validation_result.get('deviation', 'N/A')})"
                            )
                        elif status == 'warning':
                            self.logger.warning(
                                f"  Thermodynamic validation: WARNING for {transition.name} - "
                                f"{validation_result.get('message', 'Unknown issue')}"
                            )
                        elif status == 'violation':
                            self.logger.warning(
                                f"  Thermodynamic validation: VIOLATION for {transition.name} - "
                                f"deviation: {validation_result.get('deviation', 'N/A')}"
                            )
                        else:
                            self.logger.debug(
                                f"  Thermodynamic validation: {status.upper()}"
                            )
            
            # Also update transition.rate if parameters available
            if kinetic_law.parameters:
                # For Michaelis-Menten, use Vmax as rate
                if kinetic_law.rate_type == 'michaelis_menten':
                    vmax = kinetic_law.parameters.get('Vmax') or kinetic_law.parameters.get('vmax')
                    if vmax is not None:
                        transition.rate = vmax
                # For mass action, use rate constant
                elif kinetic_law.rate_type == 'mass_action':
                    k = kinetic_law.parameters.get('k') or kinetic_law.parameters.get('k1')
                    if k is not None:
                        transition.rate = k
            
            self.logger.debug(
                f"Integrated {kinetic_law.rate_type} kinetics for {transition.name} "
                f"(formula: {kinetic_law.formula[:50]}...)"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to integrate kinetics for {transition.name}: {e}"
            )
            return False
    
    def validate_and_fix_transition_types(self, transitions: List) -> Dict[str, int]:
        """
        Validate transition types based on rate_function formulas.
        
        Stochastic transitions CANNOT handle negative rates (reversible reactions).
        This method detects stochastic transitions with formulas containing subtraction
        and converts them to continuous type.
        
        Detection patterns:
        - Subtraction operators: ' - '
        - Reverse rate constants: 'k_r', 'kr_', 'k_rev'
        - Reversible mass action: 'k_f * A - k_r * B'
        
        Args:
            transitions: List of Transition objects to validate
        
        Returns:
            Dict with conversion statistics:
                - total: Total transitions checked
                - converted: Number converted from stochastic to continuous
                - already_continuous: Number already continuous with formulas
                - stochastic_safe: Stochastic without problematic formulas
        """
        stats = {
            'total': len(transitions),
            'converted': 0,
            'already_continuous': 0,
            'stochastic_safe': 0
        }
        
        for transition in transitions:
            # Check if has rate_function
            if not hasattr(transition, 'properties') or 'rate_function' not in transition.properties:
                continue
            
            formula = transition.properties.get('rate_function', '')
            if not formula or not isinstance(formula, str):
                continue
            
            # Get transition type
            t_type = getattr(transition, 'transition_type', 'continuous')
            
            if t_type == 'continuous':
                stats['already_continuous'] += 1
                continue
            
            # Check if stochastic transition has problematic formula
            if t_type == 'stochastic':
                # Detect reversible reaction patterns
                has_subtraction = ' - ' in formula
                has_reverse_rate = any(pattern in formula.lower() for pattern in ['k_r', 'kr_', 'k_rev', 'krev'])
                
                if has_subtraction or has_reverse_rate:
                    # Convert to continuous
                    transition.transition_type = 'continuous'
                    
                    # Mark conversion for tracking
                    if not hasattr(transition, 'properties'):
                        transition.properties = {}
                    transition.properties['needs_enrichment'] = True
                    transition.properties['enrichment_reason'] = 'Converted from stochastic (reversible formula detected)'
                    
                    stats['converted'] += 1
                    
                    self.logger.warning(
                        f"Converted {transition.name} from stochastic to continuous: "
                        f"Formula contains reversible reaction pattern (can produce negative rates)"
                    )
                else:
                    stats['stochastic_safe'] += 1
        
        # Log summary
        if stats['converted'] > 0:
            self.logger.info(
                f"Transition type validation: Converted {stats['converted']}/{stats['total']} "
                f"stochastic transitions to continuous (reversible formulas detected)"
            )
        else:
            self.logger.debug(
                f"Transition type validation: All {stats['total']} transitions have appropriate types"
            )
        
        return stats
    
    def get_integration_summary(self, transitions: List) -> Dict[str, int]:
        """
        Get summary statistics of kinetic integration.
        
        Args:
            transitions: List of Transition objects
        
        Returns:
            Dict with statistics
        """
        total = len(transitions)
        with_sbml_kinetics = 0
        with_manual_kinetics = 0
        with_other_kinetics = 0
        without_kinetics = 0
        
        for transition in transitions:
            if not hasattr(transition, 'kinetic_metadata') or transition.kinetic_metadata is None:
                without_kinetics += 1
            elif transition.kinetic_metadata.source == KineticSource.SBML:
                with_sbml_kinetics += 1
            elif transition.kinetic_metadata.source == KineticSource.MANUAL:
                with_manual_kinetics += 1
            else:
                with_other_kinetics += 1
        
        return {
            'total': total,
            'sbml_kinetics': with_sbml_kinetics,
            'manual_kinetics': with_manual_kinetics,
            'other_kinetics': with_other_kinetics,
            'without_kinetics': without_kinetics,
        }
    
    def _get_thermodynamic_validator(self) -> ThermodynamicSimulationValidator:
        """
        Get or create thermodynamic validator (lazy instantiation).
        
        Returns:
            Configured ThermodynamicSimulationValidator
        """
        if self._thermodynamic_validator is None:
            self._thermodynamic_validator = ThermodynamicSimulationValidator()
            self.logger.debug("Initialized thermodynamic validator")
        
        return self._thermodynamic_validator
    
    def _get_compound_mapper(self) -> SBMLCompoundMapper:
        """
        Get or create compound mapper (lazy instantiation).
        
        Returns:
            Configured SBMLCompoundMapper
        """
        if self._compound_mapper is None:
            self._compound_mapper = SBMLCompoundMapper(
                use_cache=True,
                use_name_fallback=True
            )
            self.logger.debug("Initialized SBML compound mapper")
        
        return self._compound_mapper
    
    def _validate_reversible_reaction(
        self,
        reaction: Reaction,
        transition,
        kinetic_law: KineticLaw
    ) -> Optional[Dict]:
        """
        Validate thermodynamic consistency of reversible reaction.
        
        Checks if forward/reverse rate constants are consistent with
        equilibrium constant derived from Gibbs free energy.
        
        Args:
            reaction: SBML Reaction object
            transition: Petri net Transition object
            kinetic_law: KineticLaw with rate constants
        
        Returns:
            Validation result dict or None if validation disabled/failed
        """
        if not self.enable_thermodynamic_validation:
            return None
        
        try:
            # Get validator and mapper
            validator = self._get_thermodynamic_validator()
            mapper = self._get_compound_mapper()
            
            # Map reactants and products to KEGG compound IDs
            reactant_ids = []
            product_ids = []
            
            for reactant in reaction.reactants:
                # Handle both SpeciesReference objects and tuples
                if hasattr(reactant, 'species'):
                    species_id = reactant.species
                elif isinstance(reactant, tuple) and len(reactant) >= 1:
                    species_id = reactant[0]  # (species_id, stoichiometry) tuple
                else:
                    continue
                
                # Get species object from pathway_data
                species = self._find_species(species_id)
                if species:
                    compound_id = mapper.map_species(species)
                    if compound_id:
                        reactant_ids.append(compound_id)
            
            for product in reaction.products:
                # Handle both SpeciesReference objects and tuples
                if hasattr(product, 'species'):
                    species_id = product.species
                elif isinstance(product, tuple) and len(product) >= 1:
                    species_id = product[0]  # (species_id, stoichiometry) tuple
                else:
                    continue
                
                species = self._find_species(species_id)
                if species:
                    compound_id = mapper.map_species(species)
                    if compound_id:
                        product_ids.append(compound_id)
            
            # Check if we have enough data for validation
            if not reactant_ids or not product_ids:
                self.logger.debug(
                    f"Cannot validate {transition.name}: "
                    f"insufficient compound mappings "
                    f"(reactants: {len(reactant_ids)}, products: {len(product_ids)})"
                )
                return {
                    'status': 'insufficient_data',
                    'message': 'Could not map species to KEGG compounds',
                    'reactants_mapped': len(reactant_ids),
                    'products_mapped': len(product_ids)
                }
            
            # Extract rate constants from kinetic law
            k_forward = None
            k_reverse = None
            
            # Try to extract from parameters
            if kinetic_law.parameters:
                # Common forward rate constant names
                for k_name in ['k_f', 'kf', 'k1', 'k_forward', 'kforward']:
                    if k_name in kinetic_law.parameters:
                        k_forward = kinetic_law.parameters[k_name]
                        break
                
                # Common reverse rate constant names
                for k_name in ['k_r', 'kr', 'k2', 'k_reverse', 'kreverse', 'k_rev']:
                    if k_name in kinetic_law.parameters:
                        k_reverse = kinetic_law.parameters[k_name]
                        break
            
            # If rate constants not found, validation not possible
            if k_forward is None or k_reverse is None:
                self.logger.debug(
                    f"Cannot validate {transition.name}: "
                    f"rate constants not found in kinetic law parameters"
                )
                return {
                    'status': 'no_rate_constants',
                    'message': 'Could not extract k_forward and k_reverse from kinetic law',
                    'parameters': list(kinetic_law.parameters.keys()) if kinetic_law.parameters else []
                }
            
            # Perform validation
            result = validator.validate_reversible_transition(
                reactant_ids=reactant_ids,
                product_ids=product_ids,
                k_forward=k_forward,
                k_reverse=k_reverse,
                transition_name=transition.name
            )
            
            self.logger.debug(
                f"Validated {transition.name}: "
                f"status={result.get('is_valid', False)}, "
                f"deviation={result.get('deviation', 'N/A')}"
            )
            
            return result
            
        except Exception as e:
            self.logger.warning(
                f"Thermodynamic validation failed for {transition.name}: {e}"
            )
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _find_species(self, species_id: str):
        """
        Find species object by ID in pathway_data.
        
        Args:
            species_id: Species identifier
        
        Returns:
            Species object or None
        """
        if not hasattr(self, 'pathway_data'):
            return None
        
        if not hasattr(self.pathway_data, 'species'):
            return None
        
        for species in self.pathway_data.species:
            if getattr(species, 'id', None) == species_id:
                return species
        
        return None


# Convenience function for importers

def integrate_sbml_kinetics(
    transitions: List,
    pathway_data: PathwayData,
    source_file: Optional[str] = None
) -> Dict[str, bool]:
    """
    Convenience function to integrate SBML kinetics.
    
    Usage in SBML importer:
        from shypn.services.sbml_kinetics_service import integrate_sbml_kinetics
        
        results = integrate_sbml_kinetics(transitions, pathway_data, "model.sbml")
    
    Args:
        transitions: List of Transition objects
        pathway_data: PathwayData from SBML parser
        source_file: SBML source filename
    
    Returns:
        Dict mapping transition.name → success
    """
    service = SBMLKineticsIntegrationService()
    return service.integrate_kinetics(transitions, pathway_data, None, source_file)
