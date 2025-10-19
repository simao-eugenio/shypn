"""
Stochastic kinetic parameter estimator (exponential distribution).

Estimates lambda (rate) parameter for exponential transitions.
"""

from typing import Dict, List, Any
from .base import KineticEstimator


class StochasticEstimator(KineticEstimator):
    """
    Estimates parameters for stochastic (exponential) transitions.
    
    Heuristic Rules:
    - Lambda = base_rate * reactant_stoichiometry
    - Adjust for reaction complexity
    - Pre-fill exponential distribution
    """
    
    def __init__(self):
        super().__init__()
        self.default_lambda = 1.0
    
    def estimate_parameters(
        self,
        reaction,
        substrate_places: List,
        product_places: List
    ) -> Dict[str, Any]:
        """
        Estimate lambda (rate) for exponential distribution.
        
        Returns:
            {'lambda': float, 'distribution': 'exponential'}
        """
        # Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Estimate lambda
        lambda_rate = self._estimate_lambda(reaction, substrate_places)
        
        parameters = {
            'lambda': lambda_rate,
            'distribution': 'exponential'
        }
        
        # Cache results
        self.parameter_cache[cache_key] = parameters
        
        reaction_id = reaction.id if reaction and hasattr(reaction, 'id') else 'external'
        self.logger.info(
            f"Estimated stochastic parameters for {reaction_id}: "
            f"lambda={lambda_rate:.2f}"
        )
        
        return parameters
    
    def build_rate_function(
        self,
        reaction,
        substrate_places: List,
        product_places: List,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build exponential rate function.
        
        Format: "exponential(lambda_rate)"
        """
        lambda_rate = parameters['lambda']
        return f"exponential({lambda_rate})"
    
    def _estimate_lambda(
        self,
        reaction,
        substrate_places: List
    ) -> float:
        """
        Estimate lambda from reaction properties.
        
        Rules:
        - Base rate = 1.0
        - Scale by total reactant stoichiometry
        - Adjust for substrate availability
        """
        if reaction is None or not hasattr(reaction, 'reactants') or not reaction.reactants:
            # For external conversions, use substrate count
            total_stoich = len(substrate_places) if substrate_places else 1
        else:
            # Sum of reactant stoichiometries
            total_stoich = sum(stoich for _, stoich in reaction.reactants)
        
        # Base lambda scaled by stoichiometry
        lambda_rate = self.default_lambda * total_stoich
        
        # Adjust for substrate availability
        if substrate_places:
            # Get tokens, handle places with no tokens
            available_tokens = [p.tokens for p in substrate_places if hasattr(p, 'tokens') and p.tokens > 0]
            if available_tokens:
                min_tokens = min(available_tokens)
                # If substrates have low concentration, reduce rate
                if min_tokens < 10:
                    lambda_rate *= 0.5  # Slower for low concentrations
        
        return lambda_rate
