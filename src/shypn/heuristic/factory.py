"""
Factory for creating appropriate kinetic estimators.

Simple facade for selecting estimator based on kinetic type.
"""

from typing import Optional
from .base import KineticEstimator
from .michaelis_menten import MichaelisMentenEstimator
from .stochastic import StochasticEstimator
from .mass_action import MassActionEstimator


class EstimatorFactory:
    """
    Factory for creating kinetic estimators.
    
    Usage:
        estimator = EstimatorFactory.create('michaelis_menten')
        params, rate_func = estimator.estimate_and_build(...)
    """
    
    # Registry of estimators
    _estimators = {
        'michaelis_menten': MichaelisMentenEstimator,
        'stochastic': StochasticEstimator,
        'mass_action': MassActionEstimator,
    }
    
    @classmethod
    def create(cls, kinetic_type: str, add_stochastic_noise: bool = False, 
               noise_amplitude: float = 0.1) -> Optional[KineticEstimator]:
        """
        Create estimator for given kinetic type.
        
        Args:
            kinetic_type: 'michaelis_menten', 'stochastic', or 'mass_action'
            add_stochastic_noise: If True, wrap rate functions with wiener() noise
            noise_amplitude: Stochastic noise amplitude (default 0.1 = ±10%)
            
        Returns:
            Estimator instance or None if type not found
            
        Example:
            # Without noise
            estimator = EstimatorFactory.create('michaelis_menten')
            
            # With ±10% stochastic noise (prevents steady state traps)
            estimator = EstimatorFactory.create('michaelis_menten', 
                                               add_stochastic_noise=True, 
                                               noise_amplitude=0.1)
        """
        estimator_class = cls._estimators.get(kinetic_type)
        if estimator_class:
            return estimator_class(
                add_stochastic_noise=add_stochastic_noise,
                noise_amplitude=noise_amplitude
            )
        return None
    
    @classmethod
    def available_types(cls):
        """Get list of available kinetic types."""
        return list(cls._estimators.keys())
