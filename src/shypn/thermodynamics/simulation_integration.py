"""Thermodynamic validation integration for simulation.

This module provides integration between the thermodynamics engine and
the simulation framework, validating that kinetic rate constants are
consistent with thermodynamic equilibrium constants.

Architecture (Feb 2026 refactoring):
- Uses ThermodynamicContext dataclass (single source of truth)
- Place-aware: reads pH/T from spatial places dynamically
- Compartment-aware: different conditions per compartment
- Backward compatible: falls back to document settings
"""

import logging
from typing import List, Dict, Tuple, Optional
import warnings

from shypn.thermodynamics.gibbs_calculator import GibbsCalculator
from shypn.thermodynamics.validators.equilibrium_validator import EquilibriumValidator
from shypn.thermodynamics.database.multi_source_provider import MultiSourceProvider
from shypn.thermodynamics.compound_resolver import CompoundResolver
from shypn.thermodynamics.models import ThermodynamicValidation
from shypn.thermodynamics.context import ThermodynamicContext, ThermodynamicSource


logger = logging.getLogger(__name__)


class ThermodynamicSimulationValidator:
    """Validates reversible reactions for thermodynamic consistency.
    
    This validator checks that kinetic rate ratios (k_forward/k_reverse)
    match thermodynamic equilibrium constants derived from Gibbs free energy.
    
    It can be integrated with:
    - SBML import workflow
    - Simulation initialization
    - τ-leaping reversible reactions (Skellam distribution)
    
    Attributes:
        calculator: GibbsCalculator for thermodynamic calculations
        validator: EquilibriumValidator for k_f/k_r vs K_eq checks
        resolver: CompoundResolver for KEGG/ChEBI ID mapping
        tolerance: Validation tolerance (default 0.5 = ±1 order of magnitude)
        emit_warnings: Whether to emit Python warnings (default True)
        
    Example:
        >>> validator = ThermodynamicSimulationValidator(tolerance=0.5)
        >>> 
        >>> # Validate a single reversible reaction
        >>> result = validator.validate_reversible_reaction(
        ...     reaction_id="R00001",
        ...     k_forward=1e6,
        ...     k_reverse=1e3,
        ...     reactants={"C00002": 1},  # ATP
        ...     products={"C00008": 1}     # ADP
        ... )
        >>> 
        >>> if not result.is_valid:
        ...     print(f"Warning: {result.message}")
    """
    
    def __init__(
        self,
        tolerance: float = None,
        enable_web: bool = False,
        emit_warnings: bool = True,
        document = None,
        use_dynamic_places: bool = True
    ):
        """Initialize thermodynamic validator.
        
        Args:
            tolerance: Validation tolerance (0.0 to 1.0, default 0.5). 
                      If None and document provided, reads from document.thermodynamic_settings
            enable_web: Enable eQuilibrator API access (default False for offline)
            emit_warnings: Emit Python warnings for violations (default True)
            document: DocumentModel to read settings from (optional)
            use_dynamic_places: If True, read pH/T from spatial places (default True)
        """
        # Store document reference and dynamic places flag
        self.document = document
        self.use_dynamic_places = use_dynamic_places
        
        # Create default context from document settings
        if document is not None:
            self.default_context = ThermodynamicContext.from_document_settings(document)
            if tolerance is None:
                tolerance = document.get_thermodynamic_setting('tolerance', 0.5)
            if not document.get_thermodynamic_setting('enable_validation', True):
                logger.info("Thermodynamic validation disabled in document settings")
        else:
            # Use hard-coded defaults
            self.default_context = ThermodynamicContext()
            if tolerance is None:
                tolerance = 0.5
        
        # Initialize thermodynamics engine
        self.provider = MultiSourceProvider(enable_web=enable_web)
        self.calculator = GibbsCalculator(self.provider)
        self.validator = EquilibriumValidator(self.calculator, tolerance=tolerance)
        self.resolver = CompoundResolver()
        
        self.tolerance = tolerance
        self.emit_warnings = emit_warnings
        
        logger.info(
            f"ThermodynamicSimulationValidator initialized "
            f"(tolerance={tolerance:.1%}, {self.default_context}, "
            f"dynamic_places={use_dynamic_places}, web={enable_web})"
        )
    
    def get_context_for_transition(
        self,
        transition = None,
        model = None,
        compartment: Optional[str] = None,
        ph: Optional[float] = None,
        temperature: Optional[float] = None
    ) -> ThermodynamicContext:
        """Get thermodynamic context for a transition.
        
        Priority order:
        1. Explicit pH/temperature arguments (backward compatibility)
        2. Dynamic places (if use_dynamic_places=True and model provided)
        3. Transition compartment property
        4. Default context from document settings
        
        Args:
            transition: Transition object (optional, for compartment lookup)
            model: PetriNet or DocumentModel with places (optional)
            compartment: Explicit compartment name (optional)
            ph: Explicit pH value (optional, overrides all)
            temperature: Explicit temperature value (optional, overrides all)
        
        Returns:
            ThermodynamicContext: Context with appropriate pH/T values
        """
        # If explicit values provided, use them (backward compatibility)
        if ph is not None or temperature is not None:
            return self.default_context.copy_with_overrides(
                ph=ph if ph is not None else self.default_context.ph,
                temperature=temperature if temperature is not None else self.default_context.temperature,
                source=ThermodynamicSource.CALCULATED
            )
        
        # Determine compartment
        if compartment is None and transition is not None:
            # Try to get from transition properties
            compartment = getattr(transition, 'compartment', None)
            if compartment is None and hasattr(transition, 'properties'):
                compartment = transition.properties.get('compartment')
        
        # If dynamic places enabled and model available, read from places
        if self.use_dynamic_places and model is not None:
            try:
                return ThermodynamicContext.from_places(model, compartment=compartment)
            except Exception as e:
                logger.debug(f"Could not read from places: {e}, using default context")
                return self.default_context
        
        # Fall back to default context
        return self.default_context
    
    def validate_reversible_reaction(
        self,
        reaction_id: str,
        k_forward: float,
        k_reverse: float,
        reactants: Dict[str, int],
        products: Dict[str, int],
        transition = None,
        model = None,
        compartment: Optional[str] = None,
        ph: float = None,
        temperature: float = None,
        suppress_warnings: bool = False
    ) -> ThermodynamicValidation:
        """Validate a single reversible reaction.
        
        Args:
            reaction_id: Reaction identifier
            k_forward: Forward rate constant
            k_reverse: Reverse rate constant
            reactants: {compound_id: stoichiometry}
            products: {compound_id: stoichiometry}
            transition: Transition object (optional, for place-aware lookup)
            model: PetriNet/DocumentModel with places (optional)
            compartment: Compartment name (optional)
            ph: pH value (default None = use context)
            temperature: Temperature in K (default None = use context)
            suppress_warnings: Skip warning emission for this call
            
        Returns:
            ThermodynamicValidation with validation results
        """
        # Get thermodynamic context (place-aware!)
        context = self.get_context_for_transition(
            transition=transition,
            model=model,
            compartment=compartment,
            ph=ph,
            temperature=temperature
        )
        
        # Log if using dynamic places
        if context.source == ThermodynamicSource.PLACE and context.place_names:
            logger.debug(
                f"Validating {reaction_id} with dynamic context: {context} "
                f"(places: {context.place_names})"
            )
        
        # Validate the reaction - catch errors for missing data
        try:
            validation = self.validator.validate_reversible_reaction(
                k_forward=k_forward,
                k_reverse=k_reverse,
                reactants=reactants,
                products=products,
                ph=context.ph,
                temperature=context.temperature,
                metadata={
                    "reaction_id": reaction_id,
                    "compartment": context.compartment,
                    "context_source": context.source.value,
                    "place_names": context.place_names
                }
            )
        except (ValueError, KeyError) as e:
            # Missing compound data or other error
            validation = ThermodynamicValidation(
                is_valid=False,
                message=f"Cannot validate {reaction_id}: {str(e)}",
                delta_g_reaction=None,
                k_eq=None,
                details={
                    "reaction_id": reaction_id,
                    "error": str(e),
                    "k_forward": k_forward,
                    "k_reverse": k_reverse
                }
            )
        
        # Emit warning if validation failed and warnings enabled
        if not validation.is_valid and self.emit_warnings and not suppress_warnings:
            warnings.warn(
                f"Thermodynamic inconsistency in {reaction_id}: {validation.message}",
                UserWarning,
                stacklevel=2
            )
            logger.warning(f"Reaction {reaction_id}: {validation.message}")
        
        return validation
    
    def validate_sbml_reactions(
        self,
        reactions: List,
        species_to_compound: Optional[Dict[str, str]] = None
    ) -> Dict[str, ThermodynamicValidation]:
        """Validate reversible reactions from SBML import.
        
        Args:
            reactions: List of SBML reaction objects with rate constants
            species_to_compound: Mapping from SBML species to KEGG compound IDs
                               If None, attempts to resolve from species names
            
        Returns:
            Dictionary mapping reaction_id to validation results
        """
        results = {}
        
        for reaction in reactions:
            # Skip if not reversible
            if not getattr(reaction, 'reversible', False):
                continue
            
            # Extract rate constants
            k_forward = getattr(reaction, 'k_forward', None)
            k_reverse = getattr(reaction, 'k_reverse', None)
            
            if k_forward is None or k_reverse is None:
                logger.debug(
                    f"Skipping {reaction.id}: missing directional rate constants"
                )
                continue
            
            # Map species to compounds
            try:
                reactants, products = self._extract_stoichiometry(
                    reaction, species_to_compound
                )
            except Exception as e:
                logger.warning(
                    f"Could not extract stoichiometry for {reaction.id}: {e}"
                )
                continue
            
            # Validate
            validation = self.validate_reversible_reaction(
                reaction_id=reaction.id,
                k_forward=k_forward,
                k_reverse=k_reverse,
                reactants=reactants,
                products=products
            )
            
            results[reaction.id] = validation
        
        return results
    
    def validate_transition(
        self,
        transition,
        compound_mapping: Optional[Dict[str, str]] = None
    ) -> Optional[ThermodynamicValidation]:
        """Validate a Petri net transition (reversible reaction).
        
        Args:
            transition: Transition object with rate_forward, rate_reverse
            compound_mapping: Mapping from place names to compound IDs
            
        Returns:
            ThermodynamicValidation if reversible, None otherwise
        """
        # Check if transition is reversible
        if not getattr(transition, 'properties', {}).get('is_reversible', False):
            return None
        
        # Get rate constants
        k_forward = getattr(transition, 'rate_forward', None)
        k_reverse = getattr(transition, 'rate_reverse', None)
        
        if k_forward is None or k_reverse is None:
            logger.debug(
                f"Transition {transition.name}: missing directional rates"
            )
            return None
        
        # Extract stoichiometry from arcs
        try:
            reactants, products = self._extract_transition_stoichiometry(
                transition, compound_mapping
            )
        except Exception as e:
            logger.warning(
                f"Could not extract stoichiometry for {transition.name}: {e}"
            )
            return None
        
        # Validate
        return self.validate_reversible_reaction(
            reaction_id=transition.name,
            k_forward=k_forward,
            k_reverse=k_reverse,
            reactants=reactants,
            products=products
        )
    
    def validate_model_transitions(
        self,
        transitions: List,
        compound_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, ThermodynamicValidation]:
        """Validate all reversible transitions in a model.
        
        Args:
            transitions: List of transition objects
            compound_mapping: Optional place name → compound ID mapping
            
        Returns:
            Dictionary mapping transition name to validation results
        """
        results = {}
        reversible_count = 0
        validated_count = 0
        
        for transition in transitions:
            validation = self.validate_transition(transition, compound_mapping)
            
            if validation is not None:
                reversible_count += 1
                results[transition.name] = validation
                
                if validation.is_valid:
                    validated_count += 1
        
        logger.info(
            f"Validated {reversible_count} reversible transitions: "
            f"{validated_count} consistent, {reversible_count - validated_count} inconsistent"
        )
        
        return results
    
    def _extract_stoichiometry(
        self,
        reaction,
        species_to_compound: Optional[Dict[str, str]]
    ) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Extract stoichiometry from SBML reaction.
        
        Args:
            reaction: SBML reaction object
            species_to_compound: Species ID → compound ID mapping
            
        Returns:
            (reactants, products) as {compound_id: stoichiometry}
        """
        reactants = {}
        products = {}
        
        # Extract reactants
        for species_ref in getattr(reaction, 'reactants', []):
            species_id = species_ref.species
            stoich = int(species_ref.stoichiometry)
            
            # Map to compound ID
            if species_to_compound:
                compound_id = species_to_compound.get(species_id, species_id)
            else:
                # Attempt to resolve from species name
                compound_id = self._resolve_species_to_compound(species_id)
            
            reactants[compound_id] = stoich
        
        # Extract products
        for species_ref in getattr(reaction, 'products', []):
            species_id = species_ref.species
            stoich = int(species_ref.stoichiometry)
            
            if species_to_compound:
                compound_id = species_to_compound.get(species_id, species_id)
            else:
                compound_id = self._resolve_species_to_compound(species_id)
            
            products[compound_id] = stoich
        
        return reactants, products
    
    def _extract_transition_stoichiometry(
        self,
        transition,
        compound_mapping: Optional[Dict[str, str]]
    ) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Extract stoichiometry from Petri net transition.
        
        Args:
            transition: Transition object with input/output arcs
            compound_mapping: Place name → compound ID mapping
            
        Returns:
            (reactants, products) as {compound_id: stoichiometry}
        """
        reactants = {}
        products = {}
        
        # Get input arcs (reactants)
        for arc in getattr(transition, 'input_arcs', []):
            place = arc.source
            weight = int(arc.weight) if hasattr(arc, 'weight') else 1
            
            # Map place to compound
            if compound_mapping:
                compound_id = compound_mapping.get(place.name, place.name)
            else:
                compound_id = self._resolve_species_to_compound(place.name)
            
            reactants[compound_id] = weight
        
        # Get output arcs (products)
        for arc in getattr(transition, 'output_arcs', []):
            place = arc.target
            weight = int(arc.weight) if hasattr(arc, 'weight') else 1
            
            if compound_mapping:
                compound_id = compound_mapping.get(place.name, place.name)
            else:
                compound_id = self._resolve_species_to_compound(place.name)
            
            products[compound_id] = weight
        
        return reactants, products
    
    def _resolve_species_to_compound(self, species_id: str) -> str:
        """Attempt to resolve species ID to compound ID.
        
        Args:
            species_id: SBML species ID or place name
            
        Returns:
            Compound ID (KEGG C-number) or original species_id if not found
        """
        # Try direct resolution
        result = self.resolver.resolve(species_id)
        if result and result.kegg_id:
            return result.kegg_id
        
        # Try with common prefixes removed
        clean_id = species_id.replace('_', ' ').strip()
        result = self.resolver.resolve(clean_id)
        if result and result.kegg_id:
            return result.kegg_id
        
        # Return as-is if not found
        return species_id
    
    def get_validation_summary(
        self,
        validations: Dict[str, ThermodynamicValidation]
    ) -> Dict[str, int]:
        """Generate summary statistics for validation results.
        
        Args:
            validations: Dictionary of validation results
            
        Returns:
            Dictionary with counts: total, valid, invalid, missing_data
        """
        total = len(validations)
        valid = sum(1 for v in validations.values() if v.is_valid)
        invalid = sum(1 for v in validations.values() if not v.is_valid and v.k_eq is not None)
        missing_data = sum(1 for v in validations.values() if v.k_eq is None)
        
        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'missing_data': missing_data
        }
