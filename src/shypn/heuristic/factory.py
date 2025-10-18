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
    def create(cls, kinetic_type: str) -> Optional[KineticEstimator]:
        """
        Create estimator for given kinetic type.
        
        Args:
            kinetic_type: 'michaelis_menten', 'stochastic', or 'mass_action'
            
        Returns:
            Estimator instance or None if type not found
        """
        estimator_class = cls._estimators.get(kinetic_type)
        if estimator_class:
            return estimator_class()
        return None
    
    @classmethod
    def available_types(cls):
        """Get list of available kinetic types."""
        return list(cls._estimators.keys())
