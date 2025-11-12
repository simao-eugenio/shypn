"""
Mass action kinetic parameter estimator.

Estimates rate constant k for mass action kinetics.
"""

from typing import Dict, List, Any
from .base import KineticEstimator


class MassActionEstimator(KineticEstimator):
    """
    Estimates rate constant for mass action kinetics.
    
    Heuristic Rules:
    - k = base_rate / number_of_reactants
    - Bimolecular reactions slower than unimolecular
    """
    
    def __init__(self, add_stochastic_noise: bool = False, noise_amplitude: float = 0.1):
        super().__init__(add_stochastic_noise=add_stochastic_noise, 
                        noise_amplitude=noise_amplitude)
        self.default_k = 1.0
    
    def estimate_parameters(
        self,
        reaction,
        substrate_places: List,
        product_places: List
    ) -> Dict[str, Any]:
        """
        Estimate rate constant k.
        
        Returns:
            {'k': float}
        """
        # Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Estimate k
        k = self._estimate_k(reaction, substrate_places)
        
        parameters = {'k': k}
        
        # Cache results
        self.parameter_cache[cache_key] = parameters
        
        reaction_id = reaction.id if reaction and hasattr(reaction, 'id') else 'external'
        self.logger.info(
            f"Estimated mass action parameter for {reaction_id}: k={k:.2f}"
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
        Build mass action rate function.
        
        Format: "mass_action(R1, R2, rate_constant=k)"
        """
        k = parameters['k']
        
        # Build rate function based on number of substrates with named parameters
        if len(substrate_places) >= 2:
            return f"mass_action({str(substrate_places[0].name)}, {str(substrate_places[1].name)}, rate_constant={k})"
        elif len(substrate_places) == 1:
            return f"mass_action({str(substrate_places[0].name)}, reactant2=1.0, rate_constant={k})"
        else:
            return f"{k}"
    
    def _estimate_k(
        self,
        reaction,
        substrate_places: List
    ) -> float:
        """
        Estimate rate constant k.
        
        Rules:
        - Unimolecular: k = 1.0
        - Bimolecular: k = 0.1 (slower)
        - Trimolecular: k = 0.01 (much slower)
        """
        if reaction is None:
            # For external conversions, use substrate count
            num_reactants = len(substrate_places) if substrate_places else 1
        elif hasattr(reaction, 'reactants'):
            # SBML format
            num_reactants = len(reaction.reactants)
        elif hasattr(reaction, 'substrates'):
            # KEGG format
            num_reactants = len(reaction.substrates)
        else:
            num_reactants = 1
        
        if num_reactants == 1:
            return 1.0  # Unimolecular
        elif num_reactants == 2:
            return 0.1  # Bimolecular
        else:
            return 0.01  # Trimolecular or more
