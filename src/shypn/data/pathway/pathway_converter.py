"""
Pathway Converter

Converts processed pathway data to DocumentModel (Petri net).

Maps biological concepts to Petri net elements:
- Species → Places (with initial tokens from concentration)
- Reactions → Transitions (with kinetic properties)
- Stoichiometry → Arc weights
- Compartments → Visual grouping (colors, positions)

Uses clean OOP architecture:
- BaseConverter: Abstract base for all converters
- Specialized converters: Each handles one type of mapping
- PathwayConverter: Minimal coordinator

Author: Shypn Development Team
Date: October 2025
"""

from typing import Dict, List, Optional
import logging

from .pathway_data import ProcessedPathwayData, Species, Reaction
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.heuristic import EstimatorFactory

# Import SBML kinetics integration service
try:
    from shypn.services.sbml_kinetics_service import SBMLKineticsIntegrationService
except ImportError:
    SBMLKineticsIntegrationService = None


class BaseConverter:
    """
    Abstract base class for all converters.
    
    All specialized converters inherit from this class and implement
    the convert() method.
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel):
        """
        Initialize converter.
        
        Args:
            pathway: The processed pathway data to convert
            document: The DocumentModel to populate
        """
        self.pathway = pathway
        self.document = document
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def convert(self) -> Dict:
        """
        Convert pathway elements to document model.
        
        Returns:
            Dictionary with mapping information (species_id → Place, etc.)
        """
        raise NotImplementedError("Subclasses must implement convert()")
    
    @staticmethod
    def sanitize_identifier(name: str) -> str:
        """
        Sanitize identifier to be Python-compatible.
        
        Replaces characters that are invalid in Python variable names:
        - Hyphens (-) → underscores (_)
        - Other invalid chars → underscores
        
        This ensures species IDs like 'MOS-P', 'Erk2-pp' become 'MOS_P', 'Erk2_pp'
        which can be used in rate expressions without syntax errors.
        
        Args:
            name: Original identifier (may contain hyphens)
            
        Returns:
            Sanitized identifier (Python-compatible)
        """
        if not name:
            return name
        
        # Replace hyphens with underscores
        sanitized = name.replace('-', '_')
        
        # Replace other problematic characters
        import re
        # Keep only alphanumeric, underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized)
        
        return sanitized


class SpeciesConverter(BaseConverter):
    """
    Converts species to places.
    
    Maps:
    - Species ID → Place name/label
    - Initial tokens → Place marking
    - Position → Place position
    - Compartment membership → Visual indicator (hexagons for non-default)
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel, 
                 default_compartment: Optional[str] = None):
        """Initialize species converter.
        
        Args:
            pathway: Processed pathway data
            document: DocumentModel to populate
            default_compartment: The default compartment (species in this compartment use circles)
        """
        super().__init__(pathway, document)
        self.default_compartment = default_compartment
    
    def convert(self) -> Dict[str, Place]:
        """
        Convert all species to places.
        
        Uses biological naming pattern:
        - Place ID: System-generated (P1, P2, ...)
        - Place name: Biological code (KEGG ID, common abbreviation, or species name)
        - Place label: Display name (compound name + concentration)
        
        Returns:
            Dictionary mapping species ID to Place object
        """
        species_to_place = {}
        
        for species in self.pathway.species:
            # Get position (from post-processor)
            if species.id not in self.pathway.positions:
                self.logger.warning(
                    f"Species '{species.id}' has no position, using fallback (100.0, 100.0)"
                )
            x, y = self.pathway.positions.get(species.id, (100.0, 100.0))
            
            # Get compartment color (from post-processor)
            compartment = species.compartment or "default"
            color_hex = self.pathway.colors.get(compartment, "#E8F4F8")
            
            # Convert hex color to RGB tuple (not used for now - colors too light)
            # border_color = self._hex_to_rgb(color_hex)
            
            # Determine biological name (following SHYPN naming pattern)
            biological_name = self._get_biological_name(species)
            
            # Sanitize name to be Python-compatible (replace hyphens with underscores)
            biological_name = self.sanitize_identifier(biological_name)
            
            # Create place with biological name
            place = self.document.create_place(
                x=x,
                y=y,
                label=species.name or species.id
            )
            
            # Override system-generated name with biological name
            place.name = biological_name
            
            # Set initial marking (from normalized tokens)
            place.set_tokens(species.initial_tokens)
            place.set_initial_marking(species.initial_tokens)
            
            # Mark non-default compartment places (extracellular, etc.)
            # Default compartment (cytosol) stays as normal black circle
            # Note: Boundary species are NOT marked as signal places here
            # They have arcs (infinite sources/sinks) unlike true signal places (no arcs)
            if species.compartment and species.compartment != self.default_compartment:
                place.is_compartment_place = True
                # Apply color schema immediately after setting semantic flag
                from shypn.utils.color_schema_manager import ColorSchemaManager
                ColorSchemaManager.reset_place_color(place)
                self.logger.debug(
                    f"Marking place '{place.name}' as non-default compartment place "
                    f"(compartment: {species.compartment}, violet border)"
                )
            
            # Keep default black border for visibility
            # TODO: Use compartment colors for fill instead of border
            # place.border_color = border_color
            
            # Store metadata for traceability
            if not hasattr(place, 'metadata'):
                place.metadata = {}
            # Sanitize species_id for use in formulas (replace hyphens with underscores)
            place.metadata['species_id'] = self.sanitize_identifier(species.id)
            place.metadata['original_species_id'] = species.id  # Keep original for reference
            place.metadata['concentration'] = species.initial_concentration
            place.metadata['compartment'] = species.compartment
            
            # Copy data_source from species if available (set by SBML parser)
            # Manual models won't have this, so they remain untagged
            if hasattr(species, 'metadata') and species.metadata:
                if 'data_source' in species.metadata:
                    place.metadata['data_source'] = species.metadata['data_source']
            
            # Transfer database IDs if available (for Report panel Database ID column)
            if hasattr(species, 'kegg_id') and species.kegg_id:
                place.metadata['kegg_id'] = species.kegg_id
                if 'db_id_source' not in place.metadata:
                    place.metadata['db_id_source'] = 'sbml_import'
            if hasattr(species, 'chebi_id') and species.chebi_id:
                place.metadata['chebi_id'] = species.chebi_id
                if 'db_id_source' not in place.metadata:
                    place.metadata['db_id_source'] = 'sbml_import'
            
            species_to_place[species.id] = place
            self.logger.debug(
                f"Converted species '{species.id}' to place '{place.name}' (ID: {place.id}) "
                f"with {place.tokens} tokens"
            )
        
        self.logger.info(f"Converted {len(species_to_place)} species to places")
        return species_to_place
    
    def _get_biological_name(self, species: Species) -> str:
        """
        Generate biological name for a place following SHYPN pattern.
        
        Priority order for SBML imports (preserve original names):
        1. Common abbreviation from species name (ATP, ADP, NAD, etc.)
        2. First word of species name (if ≤10 chars)
        3. Species ID (preserve SBML identifier)
        
        Priority order for KEGG imports (use database codes):
        1. Common abbreviation
        2. KEGG compound ID (C00002, etc.)
        3. First word of name
        
        Args:
            species: The species data
            
        Returns:
            Biological name string (e.g., "ATP", "GlcX", "Glucose")
        """
        # Detect data source (SBML vs KEGG)
        is_sbml_import = False
        if hasattr(species, 'metadata') and species.metadata:
            is_sbml_import = species.metadata.get('data_source') == 'sbml_import'
        
        # Try to extract common abbreviation from name
        if species.name:
            name_clean = species.name.strip()
            
            # Check if name is already a known abbreviation (3-6 uppercase letters)
            if len(name_clean) <= 6 and name_clean.replace('-', '').replace('+', '').isalpha():
                # Common metabolites: ATP, ADP, AMP, NAD, NADH, FAD, etc.
                return name_clean.upper()
            
            # For SBML imports, prioritize original names over KEGG IDs
            if is_sbml_import:
                # Extract first word if compound name
                first_word = name_clean.split()[0].split('(')[0].split('[')[0]
                if len(first_word) <= 10:
                    return first_word.capitalize()
                
                # Fallback to species ID (preserve original SBML identifier)
                species_base = species.id.split('_')[0].split('[')[0]
                return species_base
        
        # For KEGG imports, use KEGG ID if available (preferred database standard)
        if hasattr(species, 'kegg_id') and species.kegg_id:
            # Extract compound code (C00002 from cpd:C00002)
            kegg_clean = species.kegg_id.replace('cpd:', '').replace('gl:', '')
            return kegg_clean
        
        # Use ChEBI ID if available
        if hasattr(species, 'chebi_id') and species.chebi_id:
            # Keep full ChEBI format (CHEBI:15422)
            return species.chebi_id
        
        # Final fallback to species ID
        species_base = species.id.split('_')[0].split('[')[0]
        return species_base
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#E8F4F8")
            
        Returns:
            RGB tuple with values 0.0-1.0 (e.g., (0.91, 0.96, 0.97))
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


class ReactionConverter(BaseConverter):
    """
    Converts reactions to transitions.
    
    Maps:
    - Reaction ID → Transition name/label
    - Position → Transition position
    - Kinetic properties → Transition type and rate
    - Reversibility → Could create reverse arcs (not implemented yet)
    
    Kinetic Law Handling:
    - michaelis_menten: Creates rate_function with michaelis_menten() call
    - mass_action: Sets transition to stochastic, uses k as lambda
    - Other: Keeps continuous with simple rate
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel,
                 species_to_place: Optional[Dict[str, Place]] = None,
                 add_stochastic_noise: bool = True,
                 noise_amplitude: float = 0.1):
        """
        Initialize reaction converter.
        
        Args:
            pathway: The processed pathway data
            document: The DocumentModel to populate
            species_to_place: Optional mapping from species ID to Place (for rate functions)
            add_stochastic_noise: If True, wrap heuristic rates with wiener() noise
            noise_amplitude: Stochastic noise amplitude (default 0.1 = ±10%)
        """
        super().__init__(pathway, document)
        self.species_to_place = species_to_place or {}
        self.add_stochastic_noise = add_stochastic_noise
        self.noise_amplitude = noise_amplitude
    
    def convert(self) -> Dict[str, Transition]:
        """
        Convert all reactions to transitions.
        
        Uses biological naming pattern:
        - Transition ID: System-generated (T1, T2, ...)
        - Transition name: Biological code (EC number, KEGG reaction, or enzyme abbreviation)
        - Transition label: Display name (reaction name or equation)
        
        Returns:
            Dictionary mapping reaction ID to Transition object
        """
        reaction_to_transition = {}
        
        for reaction in self.pathway.reactions:
            # Get position (from post-processor)
            if reaction.id not in self.pathway.positions:
                self.logger.warning(
                    f"Reaction '{reaction.id}' has no position, using fallback (200.0, 200.0)"
                )
            x, y = self.pathway.positions.get(reaction.id, (200.0, 200.0))
            
            # Determine biological name for transition
            biological_name = self._get_biological_name(reaction)
            
            # Create label with reversible indicator if applicable
            base_label = reaction.name or reaction.id
            label = f"⇌ {base_label}" if reaction.reversible else base_label
            
            # Create transition with biological name
            transition = self.document.create_transition(
                x=x,
                y=y,
                label=label
            )
            
            # Override system-generated name with biological name
            transition.name = biological_name
            
            # Initialize properties dict if not exists
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            
            # Set kinetic properties based on kinetic law type
            self._configure_transition_kinetics(transition, reaction)
            
            # Store metadata for traceability
            if not hasattr(transition, 'metadata'):
                transition.metadata = {}
            transition.metadata['reaction_id'] = reaction.id
            transition.metadata['reversible'] = reaction.reversible
            transition.metadata['data_source'] = 'sbml_import'  # For Report panel colored rendering
            if reaction.kinetic_law:
                transition.metadata['kinetic_formula'] = reaction.kinetic_law.formula
                transition.metadata['kinetic_parameters'] = reaction.kinetic_law.parameters
                transition.metadata['kinetic_type'] = reaction.kinetic_law.rate_type
            
            reaction_to_transition[reaction.id] = transition
            self.logger.debug(
                f"Converted reaction '{reaction.id}' to transition '{transition.name}' (ID: {transition.id}) "
                f"(type: {transition.transition_type}, rate: {getattr(transition, 'rate', 'N/A')})"
            )
        
        self.logger.info(f"Converted {len(reaction_to_transition)} reactions to transitions")
        return reaction_to_transition
    
    def _get_biological_name(self, reaction: Reaction) -> str:
        """
        Generate biological name for a transition following SHYPN pattern.
        
        Priority order:
        1. Enzyme abbreviation from reaction name (HK, PFK, PGI, etc.)
        2. EC number from metadata (EC 2.7.1.1, EC 1.1.1.27, etc.)
        3. KEGG reaction ID (R00002, R00010, etc.)
        4. Truncated reaction name (first word, max 10 chars)
        5. Fallback to reaction ID
        
        Args:
            reaction: The reaction data
            
        Returns:
            Biological name string (e.g., "HK", "EC_2.7.1.1", "R00002")
        """
        # PRIORITY 1: Try to extract enzyme abbreviation from reaction name
        if reaction.name:
            name_clean = reaction.name.strip()
            
            # Known enzyme abbreviations (2-4 uppercase letters)
            if len(name_clean) <= 4 and name_clean.replace('-', '').isalpha():
                # Examples: HK, PFK, PGI, GAPDH, etc.
                return name_clean.upper()
            
            # Extract acronym from multi-word names (e.g., "Phosphoglucose Isomerase" → "PGI")
            words = name_clean.split()
            if len(words) >= 2 and len(words) <= 4:
                acronym = ''.join(w[0].upper() for w in words if w[0].isupper() or len(w) > 3)
                if 2 <= len(acronym) <= 5:
                    return acronym
        
        # PRIORITY 2: Check for EC number in metadata or kinetic law
        if hasattr(reaction, 'ec_number') and reaction.ec_number:
            # Format: EC_2.7.1.1 (underscore for valid Python identifier)
            return f"EC_{reaction.ec_number.replace('EC ', '').replace('EC:', '')}"
        
        # Check kinetic law metadata for EC number
        if reaction.kinetic_law and hasattr(reaction.kinetic_law, 'parameters'):
            for key, value in reaction.kinetic_law.parameters.items():
                if 'ec' in key.lower() and isinstance(value, str):
                    ec_clean = value.replace('EC ', '').replace('EC:', '').strip()
                    if ec_clean:
                        return f"EC_{ec_clean}"
        
        # PRIORITY 3: Use KEGG reaction ID if available
        if hasattr(reaction, 'kegg_id') and reaction.kegg_id:
            # Extract reaction code (R00002 from rn:R00002)
            kegg_clean = reaction.kegg_id.replace('rn:', '').replace('R:', '')
            return kegg_clean
        
        # PRIORITY 4: Extract first word if compound name
        if reaction.name:
            name_clean = reaction.name.strip()
            first_word = name_clean.split()[0].split('(')[0].split('[')[0]
            if len(first_word) <= 10:
                return first_word.capitalize()
        
        # PRIORITY 5: Fallback to reaction ID (remove pathway prefix if present)
        reaction_base = reaction.id.split('_')[0].split('[')[0]
        return reaction_base
    
    def _configure_transition_kinetics(self, transition: Transition, reaction: Reaction) -> None:
        """
        Configure transition kinetics based on reaction kinetic law.
        
        Strategies:
        - michaelis_menten: Create rate_function with michaelis_menten(substrate, Vmax, Km)
        - mass_action: Set to stochastic with lambda rate
        - No kinetic law: Use heuristic estimation (Michaelis-Menten for biochemical)
        - Other: Continuous with simple rate
        
        Args:
            transition: The transition to configure
            reaction: The reaction with kinetic law
        """
        if not reaction.kinetic_law:
            # No kinetic law - use heuristic estimation
            self._setup_heuristic_kinetics(transition, reaction)
            return
        
        kinetic = reaction.kinetic_law
        
        # MICHAELIS-MENTEN: Create rate function
        if kinetic.rate_type == "michaelis_menten":
            self._setup_michaelis_menten(transition, reaction, kinetic)
        
        # MASS ACTION: Stochastic transition
        elif kinetic.rate_type == "mass_action":
            self._setup_mass_action(transition, reaction, kinetic)
        
        # UNKNOWN/OTHER WITH FORMULA: Continuous transition with SBML formula
        # This handles complex SBML rate laws like reversible mass action:
        # e.g., comp1 * (kf_0 * B - kr_0 * BL)
        elif kinetic.formula:
            transition.transition_type = "continuous"
            transition.rate = 1.0  # Fallback rate
            
            # Store the SBML formula (will be processed by SBML kinetics service)
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            
            # The SBML kinetics service will translate this formula
            # and handle parameter substitution
            transition.properties['sbml_formula'] = kinetic.formula
            transition.properties['needs_enrichment'] = True
            transition.properties['enrichment_reason'] = f"SBML formula (type: {kinetic.rate_type})"
            
            self.logger.debug(
                f"  SBML formula: Set as continuous with formula '{kinetic.formula[:50]}...'"
            )
        
        # NO FORMULA: Continuous transition, mark for enrichment
        else:
            transition.transition_type = "continuous"
            transition.rate = 1.0
            
            # Mark for enrichment since no kinetic information
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['needs_enrichment'] = True
            transition.properties['enrichment_reason'] = f"No kinetic formula"
            
            self.logger.debug(
                f"  No kinetic formula, set as continuous and marked for enrichment"
            )
    
    def _setup_michaelis_menten(self, transition: Transition, reaction: Reaction, 
                                kinetic: 'KineticLaw') -> None:
        """
        Setup Michaelis-Menten kinetics with rate_function.
        
        For single substrate: michaelis_menten(S, Vmax, Km)
        For multiple substrates: Sequential Michaelis-Menten
          - michaelis_menten(S1, Vmax, Km1) * (S2/(Km2+S2)) * (S3/(Km3+S3)) * ...
        
        Args:
            transition: Transition to configure
            reaction: Reaction data
            kinetic: Kinetic law data
        """
        transition.transition_type = "continuous"
        
        # Extract parameters
        vmax = kinetic.parameters.get("Vmax", kinetic.parameters.get("vmax", 1.0))
        km = kinetic.parameters.get("Km", kinetic.parameters.get("km", 1.0))
        
        # Get all substrate places (use place objects, not names/IDs)
        substrate_places = []
        for species_id, stoich in reaction.reactants:
            place = self.species_to_place.get(species_id)
            if place:
                substrate_places.append(place)
        
        if not substrate_places:
            # No substrate places found, use simple rate
            transition.rate = vmax
            self.logger.warning(
                f"  Michaelis-Menten: Could not find substrate places, using Vmax={vmax} as rate"
            )
            return
        
        # Build rate function based on number of substrates with NAMED PARAMETERS
        # Use place.name for rate function string (user-editable alias like ATP, Glucose)
        if len(substrate_places) == 1:
            # Single substrate - standard Michaelis-Menten
            rate_func = f"michaelis_menten({substrate_places[0].name}, vmax={vmax}, km={km})"
            self.logger.info(
                f"  Michaelis-Menten (single substrate): rate_function = '{rate_func}'"
            )
        else:
            # Multiple substrates - Sequential Michaelis-Menten
            # Primary substrate uses full MM, others use saturation terms
            # Formula: Vmax * [S1]/(Km+[S1]) * [S2]/(Km+[S2]) * ...
            
            # Primary substrate (first reactant) with named parameters
            rate_func = f"michaelis_menten({substrate_places[0].name}, vmax={vmax}, km={km})"
            
            # Additional substrates as saturation terms
            for i, substrate_place in enumerate(substrate_places[1:], start=2):
                # Use same Km for all substrates (could be enhanced to use Km2, Km3, etc.)
                rate_func += f" * ({substrate_place.name} / ({km} + {substrate_place.name}))"
            
            self.logger.info(
                f"  Michaelis-Menten (sequential, {len(substrate_places)} substrates): "
                f"rate_function = '{rate_func}'"
            )
        
        transition.properties['rate_function'] = rate_func
        transition.rate = vmax  # Fallback for simple display
    
    def _setup_mass_action(self, transition: Transition, reaction: Reaction,
                          kinetic: 'KineticLaw') -> None:
        """
        Setup mass action kinetics (stochastic).
        
        Mass action is inherently stochastic for small molecule counts.
        Sets transition to stochastic with k as rate (lambda) parameter.
        
        Args:
            transition: Transition to configure
            reaction: Reaction data
            kinetic: Kinetic law data
        """
        # Mass action → Stochastic transition
        transition.transition_type = "stochastic"
        
        # Extract rate constant k
        k = kinetic.parameters.get("k", kinetic.parameters.get("rate_constant", 1.0))
        
        # For stochastic, rate attribute is the lambda parameter (used by StochasticBehavior)
        transition.rate = k
        
        self.logger.info(
            f"  Mass action: Set to stochastic with rate (lambda)={k}"
        )
        
        # Optional: Build rate function for multi-reactant mass action
        # Format: mass_action(reactant1, reactant2, rate_constant)
        if len(reaction.reactants) >= 2:
            reactant_places = []
            for species_id, _ in reaction.reactants[:2]:  # Up to 2 reactants
                place = self.species_to_place.get(species_id)
                if place:
                    reactant_places.append(place)
            
            if len(reactant_places) == 2:
                rate_func = f"mass_action({reactant_places[0].name}, {reactant_places[1].name}, rate_constant={k})"
                transition.properties['rate_function'] = rate_func
                self.logger.info(f"    Rate function: '{rate_func}'")
    
    def _setup_heuristic_kinetics(self, transition: Transition, reaction: Reaction) -> None:
        """
        Setup kinetics using heuristic parameter estimation.
        
        CRITICAL: Heuristics only work for MANUAL models with well-formed biological names.
        
        Why heuristics DON'T work for imports:
        - KEGG: Incomplete names (mix of enzyme names, EC numbers, IDs), no kinetics
        - SBML: Already has kinetics from curators, or intentionally missing
        
        Heuristics require:
        - Proper biological names (glucose, ATP, hexokinase)
        - Manual model creation (user-controlled naming)
        
        For imports without kinetics, mark for user enrichment instead.
        
        Args:
            transition: Transition to configure
            reaction: Reaction data (without kinetic law)
        """
        # DISABLE heuristics for ALL imports (KEGG and SBML)
        # Check if this is an imported model by looking at species metadata
        is_imported = False
        for species_id, _ in reaction.reactants + reaction.products:
            place = self.species_to_place.get(species_id)
            if place and hasattr(place, 'metadata') and place.metadata:
                data_source = place.metadata.get('data_source')
                if data_source in ('sbml_import', 'kegg_import'):
                    is_imported = True
                    break
        
        if is_imported:
            # Imported model - DO NOT apply heuristics
            # Mark for manual enrichment by user
            transition.transition_type = "continuous"
            transition.rate = 1.0
            
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['needs_enrichment'] = True
            transition.properties['enrichment_reason'] = (
                "Imported model without kinetics - requires user enrichment "
                "(heuristics unreliable with import naming conventions)"
            )
            
            self.logger.info(
                f"  Imported model without kinetics: Marked for user enrichment "
                f"(heuristics disabled for imports)"
            )
            return
        
        # Get substrate and product places (manual models only)
        substrate_places = []
        product_places = []
        
        for species_id, _ in reaction.reactants:
            place = self.species_to_place.get(species_id)
            if place:
                substrate_places.append(place)
        
        for species_id, _ in reaction.products:
            place = self.species_to_place.get(species_id)
            if place:
                product_places.append(place)
        
        if not substrate_places:
            # No substrates - use simple default
            transition.transition_type = "continuous"
            transition.rate = 1.0
            self.logger.warning(
                f"  No kinetic law and no substrates found, using default continuous rate=1.0"
            )
            return
        
        # Create Michaelis-Menten estimator (most common for biochemical reactions)
        # Enable stochastic noise to prevent steady state traps in continuous transitions
        estimator = EstimatorFactory.create(
            'michaelis_menten',
            add_stochastic_noise=self.add_stochastic_noise,
            noise_amplitude=self.noise_amplitude
        )
        
        if not estimator:
            # Fallback if factory fails
            transition.transition_type = "continuous"
            transition.rate = 1.0
            self.logger.error(
                f"  Failed to create heuristic estimator, using default continuous rate=1.0"
            )
            return
        
        try:
            # Estimate parameters and build rate function
            params, rate_func = estimator.estimate_and_build(
                reaction,
                substrate_places,
                product_places
            )
            
            # Configure transition
            transition.transition_type = "continuous"
            transition.properties['rate_function'] = rate_func
            transition.rate = params.get('vmax', 1.0)  # Fallback for display
            
            # Store heuristic parameters in metadata with units
            if not hasattr(transition, 'metadata') or transition.metadata is None:
                transition.metadata = {}
            
            transition.metadata['Vmax'] = params.get('vmax', 10.0)
            transition.metadata['Vmax_units'] = 'mM/s'
            transition.metadata['Vmax_source'] = 'kegg_heuristic'
            
            transition.metadata['Km'] = params.get('km', 5.0)
            transition.metadata['Km_units'] = 'mM'
            transition.metadata['Km_source'] = 'kegg_heuristic'
            
            transition.metadata['rate_function_source'] = 'kegg_heuristic'
            
            self.logger.info(
                f"  Heuristic estimation (Michaelis-Menten): "
                f"Vmax={params.get('vmax'):.2f} mM/s, Km={params.get('km'):.2f} mM"
            )
            self.logger.info(
                f"    Rate function: '{rate_func}'"
            )
            
        except (ValueError, KeyError, ZeroDivisionError) as e:
            # Fallback on any error
            transition.transition_type = "continuous"
            transition.rate = 1.0
            self.logger.error(
                f"  Heuristic estimation failed: {e}, using default continuous rate=1.0"
            )


class ArcConverter(BaseConverter):
    """
    Converts stoichiometric relationships to arcs.
    
    Maps:
    - Reactants → Arcs from Place to Transition (weight = stoichiometry)
    - Products → Arcs from Transition to Place (weight = stoichiometry)
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel,
                 species_to_place: Dict[str, Place],
                 reaction_to_transition: Dict[str, Transition]):
        """
        Initialize arc converter.
        
        Args:
            pathway: The processed pathway data
            document: The DocumentModel to populate
            species_to_place: Mapping from species ID to Place
            reaction_to_transition: Mapping from reaction ID to Transition
        """
        super().__init__(pathway, document)
        self.species_to_place = species_to_place
        self.reaction_to_transition = reaction_to_transition
    
    def convert(self) -> List[Arc]:
        """
        Convert all stoichiometric relationships to arcs.
        
        Returns:
            List of created Arc objects
        """
        arcs = []
        
        for reaction in self.pathway.reactions:
            transition = self.reaction_to_transition.get(reaction.id)
            if not transition:
                self.logger.warning(f"Transition not found for reaction '{reaction.id}'")
                continue
            
            # Aggregate stoichiometries for reactants (in case same species appears multiple times)
            reactant_weights = {}
            for species_id, stoichiometry in reaction.reactants:
                reactant_weights[species_id] = reactant_weights.get(species_id, 0) + stoichiometry
            
            # Create input arcs (reactants → transition)
            for species_id, total_stoichiometry in reactant_weights.items():
                place = self.species_to_place.get(species_id)
                if not place:
                    self.logger.warning(
                        f"Place not found for reactant species '{species_id}' "
                        f"in reaction '{reaction.id}'"
                    )
                    continue
                
                # Create arc from place to transition
                weight = max(1, round(total_stoichiometry))  # Convert to integer
                arc = self.document.create_arc(
                    source=place,
                    target=transition,
                    weight=weight
                )
                
                if arc:
                    arcs.append(arc)
                    self.logger.debug(
                        f"Created input arc: {place.name} → {transition.name} (weight: {weight})"
                    )
            
            # Aggregate stoichiometries for products (in case same species appears multiple times)
            product_weights = {}
            for species_id, stoichiometry in reaction.products:
                product_weights[species_id] = product_weights.get(species_id, 0) + stoichiometry
            
            # Create output arcs (transition → products)
            for species_id, total_stoichiometry in product_weights.items():
                place = self.species_to_place.get(species_id)
                if not place:
                    self.logger.warning(
                        f"Place not found for product species '{species_id}' "
                        f"in reaction '{reaction.id}'"
                    )
                    continue
                
                # Create arc from transition to place
                weight = max(1, round(total_stoichiometry))  # Convert to integer
                arc = self.document.create_arc(
                    source=transition,
                    target=place,
                    weight=weight
                )
                
                if arc:
                    arcs.append(arc)
                    self.logger.debug(
                        f"Created output arc: {transition.name} → {place.name} (weight: {weight})"
                    )
            
            # NOTE: Reversible reactions handled via rate_forward/rate_reverse formulas
            # DO NOT create bidirectional arcs - this causes Petri net deadlock!
            # SBML reversible reactions use a single transition with net rate (forward - reverse)
            # The simulation engine evaluates the rate formula which can be negative (reverse direction)
            if reaction.reversible:
                self.logger.debug(
                    f"Reaction '{reaction.id}' is reversible - "
                    f"handled via rate_forward/rate_reverse formulas, not bidirectional arcs"
                )
        
        self.logger.info(f"Created {len(arcs)} arcs")
        return arcs


class ModifierConverter(BaseConverter):
    """
    Converts modifiers (catalysts/enzymes) to test arcs.
    
    In SBML, modifiers are species that participate in reactions without being
    consumed or produced. They represent:
    - Enzymes that catalyze reactions
    - Allosteric regulators
    - Inhibitors
    
    In Biological Petri Nets, these are modeled as test arcs (read arcs):
    - Non-consuming arcs from catalyst place to transition (for THAT reaction)
    - Enable reaction without token consumption (in THAT reaction)
    - Visual: dashed line with hollow diamond
    
    Important: A species can have mixed roles across reactions:
    - Test arc (non-consuming) in one reaction (e.g., AMP → vPFK)
    - Normal arc (consuming) in another reaction (e.g., AMP → vAK)
    This is biochemically correct (e.g., AMP as allosteric activator + substrate).
    
    This implements the Σ component from the Biological PN formalization:
    Σ(t) = {p | arc(p,t) is test arc}
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel,
                 species_to_place: Dict[str, Place],
                 reaction_to_transition: Dict[str, Transition]):
        """
        Initialize modifier converter.
        
        Args:
            pathway: The processed pathway data
            document: The DocumentModel to populate
            species_to_place: Mapping from species ID to Place
            reaction_to_transition: Mapping from reaction ID to Transition
        """
        super().__init__(pathway, document)
        self.species_to_place = species_to_place
        self.reaction_to_transition = reaction_to_transition
    
    def convert(self) -> List[TestArc]:
        """
        Convert all modifiers to test arcs.
        
        Returns:
            List of created TestArc objects
        """
        test_arcs = []
        
        for reaction in self.pathway.reactions:
            transition = self.reaction_to_transition.get(reaction.id)
            if not transition:
                self.logger.warning(f"Transition not found for reaction '{reaction.id}'")
                continue
            
            # Build set of species that are reactants or products for this reaction
            # These already have normal arcs (consuming/producing)
            reactant_product_species = set()
            for species_id, _ in reaction.reactants:
                reactant_product_species.add(species_id)
            for species_id, _ in reaction.products:
                reactant_product_species.add(species_id)
            
            # Create test arcs for modifiers (catalysts/enzymes)
            for modifier_species_id in reaction.modifiers:
                # CRITICAL FIX: Species cannot have BOTH normal arc AND test arc to same transition
                # If species is already a reactant or product, it has a normal arc - skip test arc
                if modifier_species_id in reactant_product_species:
                    self.logger.warning(
                        f"Species '{modifier_species_id}' is BOTH a reactant/product AND modifier "
                        f"in reaction '{reaction.id}'. Keeping normal arc, skipping test arc. "
                        f"A place can only have ONE arc type (normal OR test) to a transition."
                    )
                    continue
                
                place = self.species_to_place.get(modifier_species_id)
                if not place:
                    self.logger.warning(
                        f"Place not found for modifier species '{modifier_species_id}' "
                        f"in reaction '{reaction.id}'"
                    )
                    continue
                
                # Mark this place as an enzyme/catalyst place
                # This helps the layout engine identify it
                place.metadata['is_enzyme'] = True
                
                # Create test arc from catalyst place to transition
                # Test arcs are non-consuming: check tokens but don't consume
                arc_id = self.document.id_manager.generate_arc_id()
                
                test_arc = TestArc(
                    source=place,
                    target=transition,
                    id=arc_id,
                    name=f"TA{arc_id[1:]}",  # TA1, TA2, etc.
                    weight=1  # Catalysts typically require 1 token to enable
                )
                
                # Add to document
                self.document.arcs.append(test_arc)
                test_arcs.append(test_arc)
                
                self.logger.info(
                    f"Created test arc (catalyst): {place.name} --[catalyst]--> {transition.name}"
                )
                self.logger.debug(
                    f"  This is a NON-CONSUMING arc (test arc/read arc)"
                )
        
        if test_arcs:
            self.logger.info(
                f"Created {len(test_arcs)} test arcs for catalysts/enzymes"
            )
            self.logger.info(
                "These test arcs implement the Σ component of Biological Petri Nets"
            )
        else:
            self.logger.info(
                "No modifiers found in SBML - no test arcs created"
            )
        
        return test_arcs


class PathwayConverter:
    """
    Main pathway converter coordinator.
    
    Converts ProcessedPathwayData to DocumentModel:
    - Creates DocumentModel instance
    - Delegates to specialized converters
    - Returns complete document ready for simulation
    
    Minimal coordinator pattern - most logic is in specialized converters.
    """
    
    def __init__(self, add_stochastic_noise: bool = True, noise_amplitude: float = 0.1):
        """Initialize pathway converter.
        
        Args:
            add_stochastic_noise: If True, wrap heuristic rates with wiener() noise (default: True)
                                 Prevents steady state traps in continuous transitions
            noise_amplitude: Stochastic noise amplitude (default 0.1 = ±10%)
                           Represents molecular noise from finite populations
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.add_stochastic_noise = add_stochastic_noise
        self.noise_amplitude = noise_amplitude
        
        if add_stochastic_noise:
            self.logger.info(
                f"Stochastic noise enabled: ±{noise_amplitude*100:.0f}% "
                f"(prevents steady state traps)"
            )
    
    # Known default compartments (cytosolic/intracellular)
    DEFAULT_COMPARTMENT_NAMES = ['cytosol', 'cytoplasm', 'cell', 'intracellular', 'default']
    
    def _create_compartment_places_if_referenced(self, pathway: ProcessedPathwayData, 
                                                  document: DocumentModel,
                                                  species_to_place: Dict[str, Place]) -> None:
        """[DEPRECATED] Create explicit places for compartments and parameters.
        
        This method is no longer used. All metadata (parameters, compartments, events,
        annotations) is now visible and editable in the SBML panel's metadata tree view.
        
        Creating hexagon places for every parameter clutters the canvas and is redundant
        now that we have a dedicated metadata inspector.
        
        Kept for reference only. Not called in conversion workflow.
        
        Previous behavior:
        - Created hexagon places for compartments used in formulas
        - Created hexagon places for global parameters
        - Created hexagon places for local reaction parameters
        
        New approach:
        - All metadata visible in SBML metadata tree (src/shypn/ui/panels/pathway_operations/sbml_category.py)
        - Canvas shows only biological entities (species, reactions)
        - Cleaner visualization
        
        Args:
            pathway: Processed pathway data
            document: DocumentModel to add places to
            species_to_place: Existing species-to-place mapping
        """
        import re
        
        # Collect all parameters referenced in formulas
        params_in_formulas = {}  # {param_id: (value, source_reaction_id)}
        
        for reaction in pathway.reactions:
            if not reaction.kinetic_law or not reaction.kinetic_law.formula:
                continue
            
            formula = reaction.kinetic_law.formula
            
            # Extract all identifiers from formula
            identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
            
            # Check compartments
            for comp_id in pathway.compartments_enhanced.keys():
                if comp_id in identifiers and comp_id not in species_to_place:
                    comp = pathway.compartments_enhanced[comp_id]
                    params_in_formulas[comp_id] = (comp.size, reaction.id, 'compartment')
            
            # Check global parameters
            for param_id, param_value in pathway.parameters.items():
                if param_id in identifiers and param_id not in species_to_place:
                    # Skip compartments (already handled above)
                    if param_id not in pathway.compartments_enhanced:
                        params_in_formulas[param_id] = (param_value, reaction.id, 'global')
            
            # Check local parameters
            if reaction.kinetic_law.parameters:
                for param_id, param_value in reaction.kinetic_law.parameters.items():
                    if param_id in identifiers and param_id not in species_to_place:
                        params_in_formulas[param_id] = (param_value, reaction.id, 'local')
        
        if not params_in_formulas:
            return  # No parameters referenced in formulas
        
        # Create hexagon places for all referenced parameters
        x_offset = 50.0
        y_offset = 50.0
        spacing = 80.0
        
        for i, (param_id, (param_value, reaction_id, param_type)) in enumerate(params_in_formulas.items()):
            # Skip if already exists as a place
            if param_id in species_to_place:
                continue
            
            # Create parameter place as hexagon (signal place)
            place = document.create_place(
                x=x_offset + (i * spacing),
                y=y_offset,
                label=f"{param_id} = {param_value}"
            )
            place.name = param_id  # Use parameter ID as place name for formula evaluation
            place.set_tokens(param_value)  # Parameter value as tokens
            place.set_initial_marking(param_value)
            place.is_signal_place = True  # Hexagon shape - shows it's a parameter, not pathway element
            # Apply color schema immediately after setting semantic flag
            from shypn.utils.color_schema_manager import ColorSchemaManager
            ColorSchemaManager.reset_place_color(place)
            
            # Mark as a parameter place
            if not hasattr(place, 'metadata'):
                place.metadata = {}
            place.metadata['is_parameter_place'] = True
            place.metadata['parameter_type'] = param_type
            place.metadata['parameter_value'] = param_value
            place.metadata['used_in_reaction'] = reaction_id
            
            # Add to species_to_place mapping so formulas can reference it
            species_to_place[param_id] = place
            
            self.logger.info(
                f"Created parameter place '{param_id}' = {param_value} ({param_type}) "
                f"- used in reaction {reaction_id}"
            )
    
    def _determine_default_compartment(self, pathway: ProcessedPathwayData) -> Optional[str]:
        """Determine which compartment should be considered 'default'.
        
        Uses heuristics:
        1. Check for known default compartment names (cytosol, cytoplasm, etc.)
        2. Use the compartment containing the most species
        3. Return None if no compartments exist
        
        Args:
            pathway: Processed pathway data
        
        Returns:
            Default compartment ID, or None
        """
        if not pathway.species:
            return None
        
        # Count species per compartment
        from collections import Counter
        compartment_counts = Counter(s.compartment for s in pathway.species if s.compartment)
        
        if not compartment_counts:
            return None
        
        # Check for known default compartment names
        for default_name in self.DEFAULT_COMPARTMENT_NAMES:
            if default_name in compartment_counts:
                self.logger.info(f"Using known default compartment: {default_name}")
                return default_name
        
        # Use most common compartment
        default_comp = compartment_counts.most_common(1)[0][0]
        count = compartment_counts[default_comp]
        self.logger.info(
            f"Using most common compartment as default: {default_comp} "
            f"({count}/{len(pathway.species)} species)"
        )
        return default_comp
    
    def _color_signal_arcs(self, document: DocumentModel) -> None:
        """Color arcs connected to signal places with light gray.
        
        Signal places (Ψ) represent information flow, not mass transfer.
        Their arcs should be visually distinct from:
        - Metabolic arcs (black)
        - Test arcs (blue dashed)
        
        This is the HIGHEST priority coloring - applied first.
        Other coloring functions check if arc is still black before coloring.
        
        Color coding:
        - LIGHT GRAY = Signal communication (information transfer)
        - BLUE DASHED = Test/catalyst arcs (non-consuming)
        - BLACK = Default metabolic reactions
        
        Args:
            document: DocumentModel with places and arcs
        """
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        SIGNAL_COLOR = (0.7, 0.7, 0.7)  # Light gray RGB for signal communication
        signal_arc_count = 0
        
        # Find all signal places
        signal_places = [p for p in document.places if p.is_signal_place]
        
        if not signal_places:
            return
        
        # Color ONLY SignalFlowArcs connected to signal places (light gray)
        # TestArcs remain blue, regular Arcs remain black per normalized color schema
        from shypn.utils.color_schema_manager import ColorSchemaManager
        for arc in document.arcs:
            if isinstance(arc, SignalFlowArc):
                if arc.source in signal_places or arc.target in signal_places:
                    ColorSchemaManager.reset_arc_color(arc)
                    signal_arc_count += 1
        
        if signal_arc_count > 0:
            self.logger.info(
                f"Colored {signal_arc_count} signal arcs (orange) for "
                f"{len(signal_places)} signal places"
            )
            
            document.metadata['has_signal_arcs'] = True
            document.metadata['signal_arc_count'] = signal_arc_count
    
    def _color_boundary_arcs(self, pathway: ProcessedPathwayData, 
                            document: DocumentModel,
                            species_to_place: Dict[str, Place]) -> None:
        """Color arcs connected to boundary species (infinite reservoirs).
        
        SBML boundary species (boundaryCondition=true) represent infinite reservoirs
        that maintain constant concentration through parameters and formulas.
        We mark them visually with blue color but do NOT create source/sink transitions.
        
        Color coding:
        - VIOLET = Non-default compartment (WHERE - spatial location)
        - BLUE = Boundary species (WHAT - infinite reservoir property)
        
        Args:
            pathway: Processed pathway data
            document: DocumentModel to add transitions/arcs to
            species_to_place: Mapping from species ID to Place
        """
        boundary_count = 0
        for species in pathway.species:
            # Check if this is a boundary species
            if hasattr(species, 'metadata') and species.metadata.get('boundary_condition'):
                boundary_count += 1
        
        if boundary_count > 0:
            self.logger.info(
                f"Found {boundary_count} boundary species (no special coloring)"
            )
            
            document.metadata['has_boundary_species'] = True
            document.metadata['boundary_species_count'] = boundary_count
    
    def _apply_transition_type_override(self, document: DocumentModel, 
                                       user_choice: str,
                                       pathway: ProcessedPathwayData) -> None:
        """Apply user-chosen transition type override after validation warnings.
        
        This is called when user saw stochastic compatibility warnings during import
        (assignment rules, reversible formulas) and chose how to proceed.
        
        Choices:
        - 'continuous': Convert ALL transitions to continuous mode (Option 1)
        - 'hybrid': Convert only problematic transitions to continuous (Option 2)
        - 'stochastic_with_reevaluation': Keep stochastic, enable runtime re-eval (Option 3)
        - 'stochastic': Keep as is (no changes)
        
        Args:
            document: DocumentModel with transitions already created
            user_choice: User's choice from validation dialog
            pathway: PathwayData with metadata about which transitions are problematic
        """
        if user_choice == 'stochastic' or user_choice == 'stochastic_with_reevaluation':
            # User chose to proceed with stochastic, no transition type changes needed
            # For Option 3, controller will handle runtime re-evaluation
            self.logger.info(
                f"User chose {user_choice} mode - no transition type changes"
            )
            return
        
        validation_issues = pathway.metadata.get('validation_issues', [])
        
        if user_choice == 'continuous':
            # Convert ALL transitions to continuous
            converted_count = 0
            for transition in document.transitions:
                if transition.transition_type == 'stochastic':
                    transition.transition_type = 'continuous'
                    converted_count += 1
                    self.logger.debug(
                        f"Converted {transition.name} from stochastic to continuous (user choice)"
                    )
            
            self.logger.info(
                f"User chose continuous mode: Converted {converted_count} "
                f"stochastic transitions to continuous"
            )
            document.metadata['conversion_mode'] = 'continuous'
            document.metadata['conversion_reason'] = 'User choice after validation warnings'
        
        elif user_choice == 'hybrid':
            # Convert only problematic transitions to continuous
            # Identify which reactions have issues based on validation
            problematic_reactions = set()
            
            # Check for assignment rules - affects transitions using rule-defined species
            has_assignment_rules = any(
                issue.get('category') == 'assignment_rules'
                for issue in validation_issues
            )
            
            # Check for reversible formulas - affects specific reactions
            reversible_issues = [
                issue for issue in validation_issues
                if issue.get('category') == 'reversible_formulas'
            ]
            
            # Option 2: Build dependency map for assignment rules
            # Identify which species have assignment rules
            rule_defined_species = set()
            if has_assignment_rules:
                assignment_rule_info = pathway.metadata.get('assignment_rules', {})
                species_rules = assignment_rule_info.get('species_rules', [])
                for rule in species_rules:
                    rule_defined_species.add(rule.get('variable'))
                
                self.logger.info(
                    f"Option 2 - Enhanced Hybrid Mode: Found {len(rule_defined_species)} "
                    f"species with assignment rules: {list(rule_defined_species)}"
                )
            
            # Build species-to-place mapping for dependency analysis
            species_to_place = {}
            for place in document.places:
                species_id = place.metadata.get('species_id') if hasattr(place, 'metadata') else None
                if species_id:
                    species_to_place[species_id] = place
                # Also map by name for fallback
                species_to_place[place.name] = place
            
            converted_count = 0
            for transition in document.transitions:
                should_convert = False
                
                # Get reaction metadata
                reaction_id = transition.metadata.get('reaction_id') if hasattr(transition, 'metadata') else None
                
                # Check if has reversible formula (stored in properties)
                if hasattr(transition, 'properties'):
                    is_reversible = transition.metadata.get('reversible', False)
                    rate_function = transition.properties.get('rate_function', '')
                    
                    # Check for subtraction or reverse rate keywords
                    has_subtraction = ' - ' in rate_function
                    has_reverse_keywords = any(
                        keyword in rate_function.lower()
                        for keyword in ['k_r', 'kr_', 'k_rev', 'krev', 'k_backward']
                    )
                    
                    if has_subtraction or has_reverse_keywords or is_reversible:
                        should_convert = True
                        problematic_reactions.add(transition.name)
                        self.logger.debug(
                            f"Transition '{transition.name}' marked for conversion: reversible formula"
                        )
                
                # Option 2: Check if transition uses rule-defined species
                if has_assignment_rules and not should_convert:
                    # Check input arcs (reactants)
                    for arc in document.arcs:
                        if arc.kind == 'normal' and arc.target_id == transition.id:
                            # Input arc - check if source place is rule-defined
                            source_place = document.get_object_by_id(arc.source_id)
                            if source_place:
                                species_id = source_place.metadata.get('species_id') if hasattr(source_place, 'metadata') else None
                                if species_id in rule_defined_species or source_place.name in rule_defined_species:
                                    should_convert = True
                                    problematic_reactions.add(transition.name)
                                    self.logger.debug(
                                        f"Transition '{transition.name}' marked for conversion: "
                                        f"uses rule-defined species '{source_place.name}' (input)"
                                    )
                                    break
                    
                    # Check rate formula for species references
                    if not should_convert and hasattr(transition, 'properties'):
                        rate_function = transition.properties.get('rate_function', '')
                        if rate_function:
                            for species_id in rule_defined_species:
                                if species_id in rate_function:
                                    should_convert = True
                                    problematic_reactions.add(transition.name)
                                    self.logger.debug(
                                        f"Transition '{transition.name}' marked for conversion: "
                                        f"rate formula references rule-defined species '{species_id}'"
                                    )
                                    break
                
                if should_convert and transition.transition_type == 'stochastic':
                    transition.transition_type = 'continuous'
                    converted_count += 1
                    self.logger.debug(
                        f"Converted {transition.name} from stochastic to continuous "
                        f"(hybrid mode - uses problematic species or reversible)"
                    )
            
            self.logger.info(
                f"Option 2 - Enhanced Hybrid Mode: Converted {converted_count} transitions "
                f"that use rule-defined species or reversible formulas. "
                f"Kept {len([t for t in document.transitions if t.transition_type == 'stochastic'])} as stochastic."
            )
            document.metadata['conversion_mode'] = 'hybrid_enhanced'
            document.metadata['conversion_reason'] = 'Option 2: Dependency tracking for assignment rules'
            document.metadata['problematic_reactions'] = list(problematic_reactions)
            document.metadata['rule_defined_species'] = list(rule_defined_species)
    
    def convert(self, pathway: ProcessedPathwayData) -> DocumentModel:
        """
        Convert processed pathway to DocumentModel.
        
        Args:
            pathway: The processed pathway data (with layout, colors, tokens, etc.)
        
        Returns:
            DocumentModel with all Petri net objects created
        """
        self.logger.info(f"Converting pathway: {pathway.metadata.get('name', 'Unknown')}")
        
        # Create empty document
        document = DocumentModel()
        
        # Store pathway metadata in document
        document.metadata = {
            "source": "biochemical_pathway",
            "pathway_name": pathway.metadata.get('name', 'Unknown'),
            "species_count": len(pathway.species),
            "reactions_count": len(pathway.reactions),
            "compartments": list(pathway.compartments.keys()),
            "layout_type": pathway.metadata.get('layout_type', 'unknown')
        }
        
        # Copy function definition metadata if present
        if 'function_definitions_count' in pathway.metadata:
            document.metadata['function_definitions_count'] = pathway.metadata['function_definitions_count']
            document.metadata['function_definitions'] = pathway.metadata['function_definitions']
        
        # Determine default compartment (most common one, or known defaults)
        default_compartment = self._determine_default_compartment(pathway)
        self.logger.info(f"Default compartment: {default_compartment}")
        
        # Convert species to places
        species_converter = SpeciesConverter(pathway, document, default_compartment)
        species_to_place = species_converter.convert()
        
        # ==============================================================================
        # PARAMETERS & COMPARTMENTS: Visible in SBML metadata tree, not as hexagons
        # ==============================================================================
        # All metadata (parameters, compartments, events, annotations) is now visible
        # and editable in the SBML panel's metadata tree view. No need to create
        # hexagon places that clutter the canvas. The canvas shows only the actual
        # pathway structure (species and reactions).
        # 
        # Removed: _create_compartment_places_if_referenced()
        # Users can view and edit all parameters in the SBML metadata inspector.
        
        # Convert reactions to transitions (pass species_to_place for rate functions)
        reaction_converter = ReactionConverter(
            pathway, document, species_to_place,
            add_stochastic_noise=self.add_stochastic_noise,
            noise_amplitude=self.noise_amplitude
        )
        reaction_to_transition = reaction_converter.convert()
        
        # ==============================================================================
        # USER CHOICE: Apply transition type override if user chose during validation
        # ==============================================================================
        # If user saw stochastic compatibility warnings (assignment rules, reversible
        # formulas) and chose to convert to continuous/hybrid mode, apply that choice now.
        user_choice = pathway.metadata.get('user_choice_transition_type')
        if user_choice:
            self._apply_transition_type_override(document, user_choice, pathway)
        
        # Convert stoichiometry to arcs
        arc_converter = ArcConverter(
            pathway, document,
            species_to_place, reaction_to_transition
        )
        arcs = arc_converter.convert()
        
        # ==============================================================================
        # SIGNAL ARCS: Color arcs connected to signal places (HIGHEST PRIORITY)
        # ==============================================================================
        # Signal places (Ψ) represent information flow, not mass transfer
        # Their arcs get orange color to distinguish from metabolic transport
        self._color_signal_arcs(document)
        
        # Apply color schema to all SignalFlowArcs to ensure correct light gray color
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        from shypn.utils.color_schema_manager import ColorSchemaManager
        for arc in document.arcs:
            if isinstance(arc, SignalFlowArc):
                ColorSchemaManager.reset_arc_color(arc)
        
        # ==============================================================================
        # BOUNDARY SPECIES: Color arcs but DO NOT create source/sink transitions
        # ==============================================================================
        # SBML models handle boundary species through parameters and formulas, not
        # explicit source/sink transitions. We only mark them visually with blue color.
        self._color_boundary_arcs(pathway, document, species_to_place)
        
        # ==============================================================================
        # BIOLOGICAL PETRI NET: Convert modifiers to test arcs (catalysts/enzymes)
        # ==============================================================================
        # Modifiers in SBML become test arcs in Biological Petri Nets
        # Test arcs are non-consuming: they check tokens but don't consume
        # This implements the Σ component: Σ(t) = {p | arc(p,t) is test arc}
        modifier_converter = ModifierConverter(
            pathway, document,
            species_to_place, reaction_to_transition
        )
        test_arcs = modifier_converter.convert()
        
        # Update metadata to indicate this is a Biological PN if test arcs exist
        if test_arcs:
            document.metadata["source"] = "sbml"  # Mark as SBML (biological model)
            document.metadata["has_test_arcs"] = True
            document.metadata["test_arcs_count"] = len(test_arcs)
            document.metadata["model_type"] = "Biological Petri Net"
            self.logger.info(
                "✓ Model identified as BIOLOGICAL PETRI NET (has test arcs/catalysts)"
            )
        
        # ==============================================================================
        # VALIDATION: Detect modeling issues
        # ==============================================================================
        self._validate_catalyst_only_transitions(document, arcs, test_arcs)
        self._validate_mixed_role_species(pathway, species_to_place)
        
        # ==============================================================================
        # INTEGRATE SBML KINETICS: Create SBMLKineticMetadata for transitions
        # ==============================================================================
        if SBMLKineticsIntegrationService is not None:
            self._integrate_sbml_kinetics(
                document,
                pathway,
                reaction_to_transition
            )
        
        # Log summary
        place_count, transition_count, arc_count = document.get_object_count()
        self.logger.info(
            f"Conversion complete: {place_count} places, "
            f"{transition_count} transitions, {arc_count} arcs"
        )
        if test_arcs:
            self.logger.info(
                f"  Including {len(test_arcs)} test arcs (catalysts/enzymes)"
            )
        
        return document
    
    def _integrate_sbml_kinetics(
        self,
        document: DocumentModel,
        pathway: ProcessedPathwayData,
        reaction_to_transition: Dict[str, Transition]
    ) -> None:
        """
        Integrate SBML kinetic metadata into transitions.
        
        Creates SBMLKineticMetadata for transitions with kinetic laws from SBML.
        Uses object references (not IDs) to map reactions to transitions.
        
        Args:
            document: DocumentModel with transitions
            pathway: ProcessedPathwayData with reactions and kinetic laws
            reaction_to_transition: Mapping from reaction.id to Transition object
        """
        # Build transition→reaction map (using object references)
        transition_reaction_map = {}
        for reaction_id, transition in reaction_to_transition.items():
            # Find corresponding reaction object
            reaction = next(
                (r for r in pathway.reactions if r.id == reaction_id),
                None
            )
            if reaction is not None:
                # Store object reference (not ID)
                transition_reaction_map[transition] = reaction
        
        # Get source file from pathway metadata
        source_file = pathway.metadata.get('source_file', 'unknown.sbml')
        
        # Create service and integrate kinetics
        service = SBMLKineticsIntegrationService()
        
        # Get all transitions from document
        transitions = document.transitions  # Use transitions list, not objects
        
        # Create a simple PathwayData wrapper (service expects this)
        from .pathway_data import PathwayData
        pathway_data_wrapper = PathwayData(
            species=pathway.species,
            reactions=pathway.reactions,
            compartments=pathway.compartments,
            parameters=pathway.parameters,
            metadata=pathway.metadata
        )
        
        # Integrate kinetics using object references
        results = service.integrate_kinetics(
            transitions,
            pathway_data_wrapper,
            transition_reaction_map=transition_reaction_map,
            source_file=source_file,
            document=document  # Pass document for species mapping
        )
        
        # Log results
        integrated = sum(1 for success in results.values() if success)
        self.logger.info(
            f"SBML kinetics integration: {integrated}/{len(results)} transitions enriched"
        )
        
        # Get summary statistics
        summary = service.get_integration_summary(transitions)
        self.logger.info(
            f"Kinetics summary: {summary['sbml_kinetics']} SBML, "
            f"{summary['without_kinetics']} without kinetics"
        )
    
    def _validate_catalyst_only_transitions(
        self,
        document: DocumentModel,
        normal_arcs: List[Arc],
        test_arcs: List[TestArc]
    ) -> None:
        """
        Detect transitions with only test arcs (catalysts) but no normal input arcs.
        
        This indicates a modeling error: transitions need substrates to fire.
        
        Args:
            document: DocumentModel with transitions
            normal_arcs: List of normal arcs
            test_arcs: List of test arcs
        """
        if not test_arcs:
            return  # No test arcs, nothing to validate
        
        for transition in document.transitions:
            # Count normal input arcs (reactants)
            normal_inputs = [
                arc for arc in normal_arcs
                if arc.target == transition and not isinstance(arc, TestArc)
            ]
            
            # Count test arcs (catalysts)
            test_inputs = [
                arc for arc in test_arcs
                if arc.target == transition
            ]
            
            # Count output arcs (products)
            outputs = [
                arc for arc in normal_arcs
                if arc.source == transition
            ]
            
            # PROBLEM PATTERN: test arcs but no normal inputs
            if test_inputs and not normal_inputs and outputs:
                # Changed to debug level to reduce console noise
                self.logger.debug(
                    f"Modeling issue: Transition '{transition.name}' has catalysts but no substrates. "
                    f"Catalysts: {[arc.source.name for arc in test_inputs]}"
                )
    
    def _validate_mixed_role_species(
        self,
        pathway: ProcessedPathwayData,
        species_to_place: Dict[str, Place]
    ) -> None:
        """
        Detect species that act as BOTH substrates AND catalysts across reactions.
        
        This can cause catalyst depletion: consuming species as substrate
        prevents it from catalyzing other reactions.
        
        Args:
            pathway: Processed pathway data
            species_to_place: Mapping from species ID to Place
        """
        # Track species roles across all reactions
        species_roles = {}  # species_id -> {reactions by role}
        
        for reaction in pathway.reactions:
            # Track reactants
            for species_id, _ in reaction.reactants:
                if species_id not in species_roles:
                    species_roles[species_id] = {
                        'reactant_reactions': [],
                        'product_reactions': [],
                        'modifier_reactions': []
                    }
                species_roles[species_id]['reactant_reactions'].append(reaction.id)
            
            # Track products
            for species_id, _ in reaction.products:
                if species_id not in species_roles:
                    species_roles[species_id] = {
                        'reactant_reactions': [],
                        'product_reactions': [],
                        'modifier_reactions': []
                    }
                species_roles[species_id]['product_reactions'].append(reaction.id)
            
            # Track modifiers
            for species_id in reaction.modifiers:
                if species_id not in species_roles:
                    species_roles[species_id] = {
                        'reactant_reactions': [],
                        'product_reactions': [],
                        'modifier_reactions': []
                    }
                species_roles[species_id]['modifier_reactions'].append(reaction.id)
        
        # Identify species with mixed roles
        mixed_role_species = []
        for species_id, roles in species_roles.items():
            has_modifier = len(roles['modifier_reactions']) > 0
            has_substrate = len(roles['reactant_reactions']) > 0 or len(roles['product_reactions']) > 0
            
            if has_modifier and has_substrate:
                mixed_role_species.append((species_id, roles))
        
        # Log warnings for mixed-role species (changed to debug level)
        if mixed_role_species:
            self.logger.debug(
                f"Found {len(mixed_role_species)} species with mixed catalyst/substrate roles. "
                f"Species: {[species_id for species_id, _ in mixed_role_species[:3]]}"
            )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    
    # Example: Load and convert pathway
    from .pathway_data import Species, Reaction, KineticLaw, PathwayData
    from .pathway_postprocessor import PathwayPostProcessor
    
    # Create example pathway
    glucose = Species(
        id="glucose",
        name="Glucose",
        compartment="cytosol",
        initial_concentration=5.0
    )
    
    atp = Species(
        id="atp",
        name="ATP",
        compartment="cytosol",
        initial_concentration=2.5
    )
    
    g6p = Species(
        id="g6p",
        name="Glucose-6-phosphate",
        compartment="cytosol",
        initial_concentration=0.0
    )
    
    hexokinase = Reaction(
        id="hexokinase",
        name="Hexokinase",
        reactants=[("glucose", 1.0), ("atp", 1.0)],
        products=[("g6p", 1.0)],
        kinetic_law=KineticLaw(
            formula="Vmax * glucose / (Km + glucose)",
            rate_type="michaelis_menten",
            parameters={"Vmax": 10.0, "Km": 0.1}
        )
    )
    
    pathway = PathwayData(
        species=[glucose, atp, g6p],
        reactions=[hexokinase],
        compartments={"cytosol": "Cytoplasm"},
        metadata={"name": "Simple Glycolysis"}
    )
    
    # Post-process
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    place_count, transition_count, arc_count = document.get_object_count()
    
    for place in document.places:
        pass  # Process place
    
    for transition in document.transitions:
        pass  # Process transition
    
    for arc in document.arcs:
        source_label = arc.source.label if hasattr(arc.source, 'label') else arc.source.name
        target_label = arc.target.label if hasattr(arc.target, 'label') else arc.target.name
    
