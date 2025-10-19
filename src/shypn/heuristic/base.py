"""
Base class for kinetic parameter estimation.

Defines the interface for all kinetic estimators.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
import logging


class KineticEstimator(ABC):
    """
    Abstract base class for kinetic parameter estimation.
    
    All estimators must implement:
    - estimate_parameters(): Calculate kinetic parameters
    - build_rate_function(): Generate rate function string
    """
    
    def __init__(self):
        """Initialize estimator with defaults."""
        self.logger = self._setup_logger()
        self.parameter_cache = {}
    
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
        
        Returns:
            (parameters_dict, rate_function_string)
        """
        parameters = self.estimate_parameters(
            reaction, substrate_places, product_places
        )
        rate_function = self.build_rate_function(
            reaction, substrate_places, product_places, parameters
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
