"""
Michaelis-Menten kinetic parameter estimator.

Estimates Vmax and Km from reaction stoichiometry and substrate concentrations.
"""

from typing import Dict, List, Any
from .base import KineticEstimator


class MichaelisMentenEstimator(KineticEstimator):
    """
    Estimates Michaelis-Menten parameters (Vmax, Km).
    
    Heuristic Rules:
    - Vmax = 10.0 * max(product_stoichiometry)
    - Km = mean(substrate_concentrations) / 2
    - Adjustments for reversibility
    """
    
    def __init__(self, add_stochastic_noise: bool = False, noise_amplitude: float = 0.1):
        super().__init__(add_stochastic_noise=add_stochastic_noise, 
                        noise_amplitude=noise_amplitude)
        self.default_vmax = 10.0
        self.default_km = 5.0
    
    def estimate_parameters(
        self,
        reaction,
        substrate_places: List,
        product_places: List
    ) -> Dict[str, Any]:
        """
        Estimate Vmax and Km.
        
        Returns:
            {'vmax': float, 'km': float}
        """
        # Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Estimate Vmax
        vmax = self._estimate_vmax(reaction, product_places)
        
        # Estimate Km
        km = self._estimate_km(reaction, substrate_places)
        
        parameters = {'vmax': vmax, 'km': km}
        
        # Cache results
        self.parameter_cache[cache_key] = parameters
        
        reaction_id = reaction.id if reaction and hasattr(reaction, 'id') else 'external'
        self.logger.info(
            f"Estimated MM parameters for {reaction_id}: "
            f"Vmax={vmax:.2f}, Km={km:.2f}"
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
        Build Michaelis-Menten rate function.
        
        Single substrate:
            michaelis_menten(S, Vmax, Km)
        
        Multiple substrates (sequential):
            michaelis_menten(S1, Vmax, Km) * (S2/(Km+S2)) * (S3/(Km+S3))
        """
        if not substrate_places:
            raise ValueError("No substrate places for Michaelis-Menten")
        
        vmax = parameters['vmax']
        km = parameters['km']
        
        # Single substrate - standard MM with named parameters
        if len(substrate_places) == 1:
            return f"michaelis_menten({str(substrate_places[0].name)}, vmax={vmax}, km={km})"
        
        # Multiple substrates - sequential MM with named parameters
        rate_func = f"michaelis_menten({str(substrate_places[0].name)}, vmax={vmax}, km={km})"
        
        for substrate in substrate_places[1:]:
            rate_func += f" * ({str(substrate.name)} / ({km} + {str(substrate.name)}))"
        
        return rate_func
    
    def _estimate_vmax(
        self,
        reaction,
        product_places: List
    ) -> float:
        """
        Estimate Vmax from product stoichiometry.
        
        Rule: Vmax = 10.0 * max(product_stoichiometry)
        """
        if reaction is None or not hasattr(reaction, 'products') or not reaction.products:
            # For external conversions (KEGG), use default based on product count
            if product_places:
                return self.default_vmax * len(product_places)
            return self.default_vmax
        
        # Get maximum product stoichiometry
        # Handle both SBML (products as tuples) and KEGG (products as objects)
        max_stoich = 1
        for product in reaction.products:
            if isinstance(product, tuple):
                # SBML format: (id, stoichiometry)
                max_stoich = max(max_stoich, product[1])
            elif hasattr(product, 'stoichiometry'):
                # KEGG format: KEGGProduct with stoichiometry attribute
                max_stoich = max(max_stoich, product.stoichiometry)
        
        # Base Vmax
        vmax = self.default_vmax * max_stoich
        
        # Adjust for reversibility
        if hasattr(reaction, 'reversible') and reaction.reversible:
            vmax *= 0.8  # Reversible reactions slightly slower
        elif hasattr(reaction, 'is_reversible') and callable(reaction.is_reversible):
            if reaction.is_reversible():
                vmax *= 0.8
        
        return vmax
    
    def _estimate_km(
        self,
        reaction,
        substrate_places: List
    ) -> float:
        """
        Estimate Km from substrate concentrations.
        
        Rule: Km ≈ mean(substrate_concentrations) / 2
        """
        if not substrate_places:
            return self.default_km
        
        # Get concentrations (tokens)
        concentrations = [
            p.tokens for p in substrate_places
            if p.tokens > 0
        ]
        
        if not concentrations:
            return self.default_km
        
        # Mean concentration / 2
        mean_conc = sum(concentrations) / len(concentrations)
        km = mean_conc / 2.0
        
        # Ensure minimum
        km = max(0.5, km)
        
        return km
