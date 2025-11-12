"""
Base class for kinetic parameter estimation.

Defines the interface for all kinetic estimators.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
import logging


def add_stochastic_noise(rate_function: str, amplitude: float = 0.1) -> str:
    """Add multiplicative Wiener noise to any rate function.
    
    Wraps the entire rate expression with stochastic noise:
        original_rate → (original_rate) * (1 + amplitude * wiener(time))
    
    This works with ANY rate function:
    - Simple constants: "1.0" → "(1.0) * (1 + 0.1 * wiener(time))"
    - Michaelis-Menten: "michaelis_menten(...)" → "(michaelis_menten(...)) * (1 + 0.1 * wiener(time))"
    - Complex SBML: "kf * P1 * P2" → "(kf * P1 * P2) * (1 + 0.1 * wiener(time))"
    
    Args:
        rate_function: Original rate expression (any valid formula)
        amplitude: Noise amplitude (default 0.1 = ±10%)
                  0.05 (5%)  - High molecule counts
                  0.10 (10%) - Default, biologically realistic
                  0.15 (15%) - Medium concentrations
                  0.20 (20%) - Low concentrations
    
    Returns:
        Modified rate expression with stochastic noise
        
    Biological Rationale:
        Represents intrinsic molecular noise from finite populations.
        Prevents models from getting stuck in exact steady states.
        
    Example:
        >>> add_stochastic_noise("michaelis_menten(P17, vmax=70.0, km=0.1)")
        "(michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))"
    """
    return f"({rate_function}) * (1 + {amplitude} * wiener(time))"


class KineticEstimator(ABC):
    """
    Abstract base class for kinetic parameter estimation.
    
    All estimators must implement:
    - estimate_parameters(): Calculate kinetic parameters
    - build_rate_function(): Generate rate function string
    
    Optional features:
    - add_stochastic_noise: Set to True to automatically wrap rate functions with wiener() noise
    - noise_amplitude: Control the noise level (default 0.1 = ±10%)
    """
    
    def __init__(self, add_stochastic_noise: bool = False, noise_amplitude: float = 0.1):
        """Initialize estimator with defaults.
        
        Args:
            add_stochastic_noise: If True, wrap all rate functions with wiener() noise
            noise_amplitude: Stochastic noise amplitude (default 0.1 = ±10%)
        """
        self.logger = self._setup_logger()
        self.parameter_cache = {}
        self.add_stochastic_noise = add_stochastic_noise
        self.noise_amplitude = noise_amplitude
    
    @abstractmethod
    def estimate_parameters(
        self,
        reaction,
        substrate_places: List,
        product_places: List
    ) -> Dict[str, Any]:
        """
        Estimate kinetic parameters from reaction data.
        
        Args:
            reaction: Reaction object with stoichiometry
            substrate_places: Input places
            product_places: Output places
            
        Returns:
            Dictionary of parameter names and values
            
        Example:
            {'vmax': 10.0, 'km': 5.0}
        """
        pass
    
    @abstractmethod
    def build_rate_function(
        self,
        reaction,
        substrate_places: List,
        product_places: List,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build rate function string from parameters.
        
        Args:
            reaction: Reaction object
            substrate_places: Input places
            product_places: Output places
            parameters: Estimated parameters
            
        Returns:
            Rate function string
            
        Example:
            "michaelis_menten(P_Glucose, 10.0, 5.0)"
        """
        pass
    
    def estimate_and_build(
        self,
        reaction,
        substrate_places: List,
        product_places: List
    ) -> Tuple[Dict[str, Any], str]:
        """
        Convenience method: estimate + build in one call.
        
        If add_stochastic_noise=True, automatically wraps the rate function
        with multiplicative Wiener noise.
        
        Returns:
            (parameters_dict, rate_function_string)
        """
        parameters = self.estimate_parameters(
            reaction, substrate_places, product_places
        )
        rate_function = self.build_rate_function(
            reaction, substrate_places, product_places, parameters
        )
        
        # Apply stochastic noise if enabled
        if self.add_stochastic_noise:
            original_rate = rate_function
            rate_function = add_stochastic_noise(rate_function, self.noise_amplitude)
            self.logger.info(
                f"Applied stochastic noise (±{self.noise_amplitude*100:.0f}%): "
                f"{original_rate[:50]}... → {rate_function[:50]}..."
            )
        
        return parameters, rate_function
    
    def _make_cache_key(self, reaction) -> str:
        """Create cache key from reaction properties."""
        if reaction is None:
            # For KEGG/external conversions where we don't have Reaction objects
            import random
            return f"external_{random.randint(0, 1000000)}"
        
        # Try to build key from reaction structure
        # Handle both SBML (reactants/products as tuples) and KEGG (substrates/products as objects)
        try:
            reactants = tuple()
            products = tuple()
            
            if hasattr(reaction, 'reactants') and reaction.reactants:
                # SBML format: [(id, stoich), ...]
                reactants = tuple(sorted(rid for rid, _ in reaction.reactants))
            elif hasattr(reaction, 'substrates') and reaction.substrates:
                # KEGG format: [KEGGSubstrate(id, name, stoichiometry), ...]
                reactants = tuple(sorted(s.id for s in reaction.substrates))
            
            if hasattr(reaction, 'products') and reaction.products:
                if isinstance(reaction.products[0], tuple):
                    # SBML format
                    products = tuple(sorted(pid for pid, _ in reaction.products))
                else:
                    # KEGG format
                    products = tuple(sorted(p.id for p in reaction.products))
            
            # Use reaction ID if available, otherwise name
            reaction_id = getattr(reaction, 'id', getattr(reaction, 'name', 'unknown'))
            return f"{reaction_id}_{reactants}_{products}"
            
        except Exception:
            # Fallback to simple random key if structure parsing fails
            import random
            return f"reaction_{random.randint(0, 1000000)}"
    
    def _setup_logger(self):
        """Setup logger for this estimator."""
        return logging.getLogger(self.__class__.__name__)
