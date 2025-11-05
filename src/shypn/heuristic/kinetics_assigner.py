"""
Kinetics Assigner

Main class for assigning kinetic properties to transitions based on
available data using a tiered strategy:

1. Explicit data (highest priority) - use as-is
2. Database lookup - EC number → parameters
3. Heuristic analysis - reaction structure → type
4. Default fallback - safe defaults

Core Principle: "Import as-is for curated models, enhance only when data is missing"
"""

from typing import Optional, List, Dict, Any
import logging

from .assignment_result import AssignmentResult, ConfidenceLevel, AssignmentSource
from .metadata import KineticsMetadata
from .factory import EstimatorFactory

# Import hybrid API for enzyme kinetics lookup
try:
    from shypn.data.enzyme_kinetics_api import EnzymeKineticsAPI
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


class KineticsAssigner:
    """
    Assigns kinetic properties to transitions using tiered strategy.
    
    Uses hybrid three-tier database system:
    - Tier 1: Local cache (fast, <10ms)
    - Tier 2: External APIs (BRENDA - future, comprehensive)
    - Tier 3: Fallback database (10 glycolysis enzymes, offline)
    
    Usage:
        assigner = KineticsAssigner()
        result = assigner.assign(transition, reaction, source='kegg')
        
        # Offline mode (no API calls):
        assigner = KineticsAssigner(offline_mode=True)
    """
    
    def __init__(self, offline_mode: bool = False):
        """
        Initialize kinetics assigner.
        
        Args:
            offline_mode: If True, skip API calls (use cache + fallback only)
        """
        self.logger = logging.getLogger(__name__)
        self.offline_mode = offline_mode
        
        # Initialize hybrid API database
        if API_AVAILABLE:
            self.database = EnzymeKineticsAPI(offline_mode=offline_mode)
            self.logger.info(
                f"Initialized EnzymeKineticsAPI "
                f"(offline_mode={offline_mode})"
            )
        else:
            self.database = None
            self.logger.warning(
                "EnzymeKineticsAPI not available - database lookup disabled"
            )
    
    def assign(
        self,
        transition,
        reaction,
        substrate_places: Optional[List] = None,
        product_places: Optional[List] = None,
        source: str = 'kegg'
    ) -> AssignmentResult:
        """
        Assign kinetics to transition using tiered strategy.
        
        Args:
            transition: Transition object to configure
            reaction: Reaction data (KEGG or SBML)
            substrate_places: List of substrate places
            product_places: List of product places
            source: Data source ('kegg', 'sbml', 'biomodels')
        
        Returns:
            AssignmentResult with details about the assignment
        """
        # Check if should enhance (respects user/explicit data)
        if not KineticsMetadata.should_enhance(transition):
            existing_source = KineticsMetadata.get_source(transition)
            self.logger.info(
                f"Skipping enhancement for {transition.name} "
                f"(source: {existing_source.value})"
            )
            return AssignmentResult.failed(
                f"Not enhancing: {existing_source.value} data"
            )
        
        # Save original state for potential rollback
        KineticsMetadata.save_original(transition)
        
        # Tier 1: Explicit kinetics (SBML only)
        if source == 'sbml' and self._has_explicit_kinetics(reaction):
            return self._assign_explicit(transition, reaction)
        
        # Tier 2: Database lookup (if EC number available)
        # Check transition metadata first (from KEGG EC enrichment)
        # then fallback to reaction.ec_numbers (legacy)
        has_ec = False
        if hasattr(transition, 'metadata') and 'ec_numbers' in transition.metadata:
            has_ec = bool(transition.metadata['ec_numbers'])
        elif hasattr(reaction, 'ec_numbers'):
            has_ec = bool(reaction.ec_numbers)
        
        if has_ec:
            result = self._assign_from_database(
                transition, reaction, substrate_places, product_places
            )
            if result.success:
                return result
        
        # Tier 3: Heuristic analysis
        return self._assign_heuristic(
            transition, reaction, substrate_places, product_places, source
        )
    
    def _has_explicit_kinetics(self, reaction) -> bool:
        """Check if reaction has explicit kinetic data."""
        return (
            hasattr(reaction, 'kinetic_law') and
            reaction.kinetic_law is not None
        )
    
    def _assign_explicit(self, transition, reaction) -> AssignmentResult:
        """
        Assign from explicit SBML kinetic law.
        
        This is the highest priority - use exactly as provided.
        """
        kinetic = reaction.kinetic_law
        
        # Determine type from kinetic law
        if kinetic.rate_type == "mass_action":
            # Mass action is inherently STOCHASTIC at molecular level (Gillespie algorithm)
            # For small molecule counts, stochastic simulation is more accurate
            # Uses exponential distribution: appropriate for Brownian molecular collisions
            transition.transition_type = "stochastic"
            k = kinetic.parameters.get("k", 1.0)
            transition.rate = k
            
            parameters = {'k': k}
            rate_function = str(k)
            
        elif kinetic.rate_type == "michaelis_menten":
            transition.transition_type = "continuous"
            vmax = kinetic.parameters.get("vmax", 10.0)
            km = kinetic.parameters.get("km", 5.0)
            
            # Build rate function using actual substrate place name
            # CRITICAL: Must use place.name or place.id, not literal "substrate"
            parameters = {'vmax': vmax, 'km': km}
            
            # Try to get substrate place from reaction
            substrate_places = []
            if hasattr(reaction, 'substrates'):
                substrate_places = list(reaction.substrates)
            
            if substrate_places:
                substrate_name = substrate_places[0].name
                rate_function = f"michaelis_menten({substrate_name}, {vmax}, {km})"
            else:
                # Fallback: use generic "S" but this will fail at runtime
                # Better to use a constant rate
                self.logger.warning(
                    f"No substrate place found for {transition.name}, using constant rate"
                )
                rate_function = str(vmax)  # Constant rate fallback
            
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['rate_function'] = rate_function
            
        else:
            # Unknown type - default to continuous
            transition.transition_type = "continuous"
            transition.rate = 1.0
            parameters = {'rate': 1.0}
            rate_function = "1.0"
        
        result = AssignmentResult.explicit(parameters, rate_function)
        KineticsMetadata.set_from_result(transition, result)
        
        self.logger.info(
            f"Assigned explicit kinetics to {transition.name}: "
            f"type={transition.transition_type}"
        )
        
        return result
    
    def _assign_from_database(
        self,
        transition,
        reaction,
        substrate_places: Optional[List],
        product_places: Optional[List]
    ) -> AssignmentResult:
        """
        Assign from EC number database lookup.
        
        Uses hybrid three-tier system:
        1. Local cache (SQLite) - Fast repeated lookups
        2. External API (BRENDA - future) - Comprehensive, always current
        3. Fallback database (10 glycolysis enzymes) - Offline support
        
        Returns:
            AssignmentResult with database parameters or failed result
        """
        # Check if database available
        if not self.database:
            self.logger.debug("Database not available")
            return AssignmentResult.failed("Database not available")
        
        # Extract EC number - prefer transition metadata (from KEGG enrichment)
        ec_numbers = []
        
        # First: Check transition metadata (KEGG EC enrichment)
        if hasattr(transition, 'metadata') and 'ec_numbers' in transition.metadata:
            ec_numbers = transition.metadata['ec_numbers']
            self.logger.debug(f"Using EC numbers from transition metadata: {ec_numbers}")
        
        # Fallback: Check reaction object (legacy)
        if not ec_numbers and reaction:
            ec_numbers = getattr(reaction, 'ec_numbers', [])
            if ec_numbers:
                self.logger.debug(f"Using EC numbers from reaction object: {ec_numbers}")
        
        if not ec_numbers:
            return AssignmentResult.failed("No EC number")
        
        ec_number = ec_numbers[0]  # Use first EC number
        
        # Lookup in database (tries cache → API → fallback)
        try:
            db_entry = self.database.lookup(ec_number)
        except Exception as e:
            self.logger.error(f"Database lookup error for EC {ec_number}: {e}")
            return AssignmentResult.failed(f"Database error: {e}")
        
        if not db_entry:
            self.logger.debug(
                f"EC {ec_number} not found "
                f"(tried cache + {'API + ' if not self.offline_mode else ''}fallback)"
            )
            return AssignmentResult.failed(f"EC {ec_number} not found in database")
        
        # Found in database!
        source = db_entry.get('_lookup_source', db_entry.get('source', 'database'))
        self.logger.info(
            f"Found EC {ec_number} in {source}: {db_entry.get('enzyme_name', 'Unknown')}"
        )
        
        # Extract parameters and build rate function
        params = db_entry.get('parameters', {})
        kinetic_law = db_entry.get('law', 'michaelis_menten')
        
        # Determine transition type and build rate function
        if kinetic_law == 'michaelis_menten':
            transition.transition_type = "continuous"
            
            # Get Vmax (or kcat)
            vmax = params.get('vmax', params.get('kcat', 10.0))
            
            # Get Km for substrate
            # Try to match substrate-specific Km (e.g., km_glucose)
            km = None
            if substrate_places:
                substrate_name = substrate_places[0].name.lower()
                # Try to find matching km parameter
                for key, value in params.items():
                    if key.startswith('km_') and substrate_name in key.lower():
                        km = value
                        break
            
            # Fallback to generic km
            if km is None:
                km = params.get('km', 0.5)
            
            # Build rate function
            if substrate_places:
                substrate_place = substrate_places[0]
                rate_function = f"michaelis_menten({substrate_place.name}, {vmax}, {km})"
            else:
                # No substrate places - use constant rate instead of undefined "substrate"
                self.logger.warning(
                    f"No substrate place found for {transition.name}, using constant rate {vmax}"
                )
                rate_function = str(vmax)  # Constant rate fallback
            
            # Store rate function
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['rate_function'] = rate_function
            
            # Create result
            result = AssignmentResult.from_database(
                parameters={
                    'vmax': vmax,
                    'km': km,
                    **{k: v for k, v in params.items() if k not in ['vmax', 'km']}
                },
                rate_function=rate_function,
                ec_number=ec_number
            )
            
            # Add metadata about lookup source
            result.metadata['lookup_source'] = source
            result.metadata['enzyme_name'] = db_entry.get('enzyme_name', 'Unknown')
            if 'reference' in db_entry:
                result.metadata['reference'] = db_entry['reference']
            
            # Set metadata on transition
            KineticsMetadata.set_from_result(transition, result)
            
            self.logger.info(
                f"Assigned database kinetics to {transition.name}: "
                f"EC {ec_number}, Vmax={vmax}, Km={km}, "
                f"source={source}"
            )
            
            return result
            
        elif kinetic_law == 'mass_action':
            # Mass action is STOCHASTIC (Gillespie 1977, J. Phys. Chem. 81:2340-2361)
            # Molecular collisions follow Brownian motion → exponential distribution
            # For small copy numbers (typical in BioModels), stochastic is more accurate
            transition.transition_type = "stochastic"
            k = params.get('k', params.get('rate_constant', 1.0))
            transition.rate = k
            
            result = AssignmentResult.from_database(
                parameters={'k': k},
                rate_function=str(k),
                ec_number=ec_number
            )
            
            result.metadata['lookup_source'] = source
            KineticsMetadata.set_from_result(transition, result)
            
            self.logger.info(
                f"Assigned mass action kinetics to {transition.name}: "
                f"EC {ec_number}, k={k}, source={source}"
            )
            
            return result
        
        else:
            # Unsupported kinetic law
            self.logger.warning(
                f"Unsupported kinetic law '{kinetic_law}' for EC {ec_number}"
            )
            return AssignmentResult.failed(f"Unsupported kinetic law: {kinetic_law}")
    
    def _assign_heuristic(
        self,
        transition,
        reaction,
        substrate_places: Optional[List],
        product_places: Optional[List],
        source: str
    ) -> AssignmentResult:
        """
        Assign using heuristic analysis of reaction structure.
        
        Rules:
        1. Simple reaction (A → B) → Stochastic (mass action)
        2. Has enzyme/EC number → Continuous (Michaelis-Menten)
        3. Multiple substrates → Continuous (sequential MM)
        4. Unknown → Continuous (safe default)
        """
        # Determine kinetic type
        kinetic_type, rule, confidence = self._analyze_reaction_type(
            reaction, substrate_places, product_places
        )
        
        # Get appropriate estimator
        estimator = EstimatorFactory.create(kinetic_type)
        if not estimator:
            self.logger.error(f"No estimator for type: {kinetic_type}")
            return AssignmentResult.failed(f"No estimator for {kinetic_type}")
        
        # Estimate parameters and build rate function
        try:
            parameters, rate_function = estimator.estimate_and_build(
                reaction,
                substrate_places or [],
                product_places or []
            )
        except Exception as e:
            self.logger.error(f"Estimation failed: {e}")
            return AssignmentResult.failed(str(e))
        
        # Apply to transition
        if kinetic_type in ('mass_action', 'stochastic'):
            # Mass action is STOCHASTIC (scientific basis: Gillespie algorithm)
            # Brownian collisions → exponential time distribution (not fixed delay)
            transition.transition_type = "stochastic"
            transition.rate = parameters.get('k', 1.0)
        else:  # michaelis_menten
            transition.transition_type = "continuous"
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['rate_function'] = rate_function
        
        # Create result
        result = AssignmentResult.from_heuristic(
            rule=rule,
            confidence=confidence,
            parameters=parameters,
            rate_function=rate_function
        )
        
        # Store metadata
        KineticsMetadata.set_from_result(transition, result)
        
        self.logger.info(
            f"Assigned heuristic kinetics to {transition.name}: "
            f"type={transition.transition_type}, rule={rule}, "
            f"confidence={confidence.value}"
        )
        
        return result
    
    def _analyze_reaction_type(
        self,
        reaction,
        substrate_places: Optional[List],
        product_places: Optional[List]
    ) -> tuple:
        """
        Analyze reaction to determine kinetic type.
        
        Returns:
            (kinetic_type, rule_name, confidence_level)
        """
        # Rule 1: Has EC number → Enzymatic (Michaelis-Menten)
        if hasattr(reaction, 'ec_numbers') and reaction.ec_numbers:
            return (
                'michaelis_menten',
                'enzymatic_mm',
                ConfidenceLevel.MEDIUM
            )
        
        # Rule 2: Has enzyme annotation → Michaelis-Menten
        if hasattr(reaction, 'enzyme') and reaction.enzyme:
            return (
                'michaelis_menten',
                'has_enzyme',
                ConfidenceLevel.MEDIUM
            )
        
        # Rule 3: Simple stoichiometry (1:1 or 1:n) → Mass action
        if self._is_simple_mass_action(reaction, substrate_places, product_places):
            return (
                'mass_action',
                'simple_mass_action',
                ConfidenceLevel.LOW
            )
        
        # Rule 4: Multiple substrates → Michaelis-Menten (complex kinetics)
        if substrate_places and len(substrate_places) > 1:
            return (
                'michaelis_menten',
                'multi_substrate',
                ConfidenceLevel.LOW
            )
        
        # Default: Continuous (safe fallback)
        return (
            'michaelis_menten',
            'default_continuous',
            ConfidenceLevel.LOW
        )
    
    def _is_simple_mass_action(
        self,
        reaction,
        substrate_places: Optional[List],
        product_places: Optional[List]
    ) -> bool:
        """
        Check if reaction is simple mass action.
        
        Criteria:
        - 1 or 2 substrates
        - Simple stoichiometry (all coefficients 1 or 2)
        - No enzyme annotation
        """
        # Must have substrates
        if not substrate_places:
            return False
        
        # Check enzyme annotations
        if hasattr(reaction, 'ec_numbers') and reaction.ec_numbers:
            return False  # Has enzyme, not simple mass action
        
        if hasattr(reaction, 'enzyme') and reaction.enzyme:
            return False
        
        # Check substrate count
        num_substrates = len(substrate_places)
        if num_substrates > 2:
            return False  # Too complex
        
        # Check stoichiometry (if available)
        # Handle both SBML (reactants) and KEGG (substrates)
        reactant_list = None
        if hasattr(reaction, 'reactants'):
            reactant_list = reaction.reactants  # SBML format: [(id, stoich), ...]
        elif hasattr(reaction, 'substrates'):
            # KEGG format: [KEGGSubstrate(id, name, stoichiometry), ...]
            reactant_list = [(s.id, getattr(s, 'stoichiometry', 1)) for s in reaction.substrates]
        
        if reactant_list:
            for _, stoich in reactant_list:
                if stoich > 2:
                    return False  # Complex stoichiometry
        
        # Passed all checks - likely mass action
        return True
    
    def assign_bulk(
        self,
        transitions: List,
        reactions: List,
        source: str = 'kegg'
    ) -> Dict[str, AssignmentResult]:
        """
        Assign kinetics to multiple transitions.
        
        Args:
            transitions: List of transitions
            reactions: List of corresponding reactions
            source: Data source
        
        Returns:
            Dict mapping transition.name → AssignmentResult
        """
        results = {}
        
        for i, transition in enumerate(transitions):
            reaction = reactions[i] if i < len(reactions) else None
            
            result = self.assign(
                transition,
                reaction,
                substrate_places=None,  # TODO: Extract from transition arcs
                product_places=None,
                source=source
            )
            
            results[transition.name] = result
        
        return results
