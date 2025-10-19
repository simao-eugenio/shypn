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


class KineticsAssigner:
    """
    Assigns kinetic properties to transitions using tiered strategy.
    
    Usage:
        assigner = KineticsAssigner()
        result = assigner.assign(transition, reaction, source='kegg')
    """
    
    def __init__(self):
        """Initialize kinetics assigner."""
        self.logger = logging.getLogger(__name__)
        self.database = None  # Future: EC number database
    
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
        if hasattr(reaction, 'ec_numbers') and reaction.ec_numbers:
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
            transition.transition_type = "stochastic"
            k = kinetic.parameters.get("k", 1.0)
            transition.rate = k
            
            parameters = {'k': k}
            rate_function = str(k)
            
        elif kinetic.rate_type == "michaelis_menten":
            transition.transition_type = "continuous"
            vmax = kinetic.parameters.get("vmax", 10.0)
            km = kinetic.parameters.get("km", 5.0)
            
            # Build rate function (simplified - full implementation in pathway_converter)
            parameters = {'vmax': vmax, 'km': km}
            rate_function = f"michaelis_menten(substrate, {vmax}, {km})"
            
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
        
        Future implementation: Query BRENDA/SABIO-RK for kinetic parameters.
        """
        # Future: Implement database lookup
        # For now, return failure to fall through to heuristics
        
        self.logger.debug(
            f"Database lookup not yet implemented for {transition.name}"
        )
        
        return AssignmentResult.failed("Database lookup not implemented")
    
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
