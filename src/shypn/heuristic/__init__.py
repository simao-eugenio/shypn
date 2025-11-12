"""
Kinetic Parameter Heuristics Package

Provides intelligent estimation of kinetic parameters from stoichiometry
and automatic assignment of kinetic properties to transitions.

Usage (Low-level - Estimators):
    from shypn.heuristic import EstimatorFactory
    
    estimator = EstimatorFactory.create('michaelis_menten')
    params, rate_func = estimator.estimate_and_build(reaction, substrates, products)
    
    # With automatic stochastic noise (prevents steady state traps)
    estimator = EstimatorFactory.create('michaelis_menten', 
                                       add_stochastic_noise=True, 
                                       noise_amplitude=0.1)
    params, rate_func = estimator.estimate_and_build(reaction, substrates, products)

Usage (High-level - Auto-assignment):
    from shypn.heuristic import KineticsAssigner
    
    assigner = KineticsAssigner()
    result = assigner.assign(transition, reaction, source='kegg')

Core Principle:
    "Import as-is for curated models, enhance only when data is missing"
"""

from .base import KineticEstimator, add_stochastic_noise
from .michaelis_menten import MichaelisMentenEstimator
from .stochastic import StochasticEstimator
from .mass_action import MassActionEstimator
from .factory import EstimatorFactory
from .kinetics_assigner import KineticsAssigner
from .assignment_result import AssignmentResult, ConfidenceLevel, AssignmentSource
from .metadata import KineticsMetadata

__all__ = [
    # Estimators (low-level)
    'KineticEstimator',
    'MichaelisMentenEstimator',
    'StochasticEstimator',
    'MassActionEstimator',
    'EstimatorFactory',
    # Utility
    'add_stochastic_noise',
    # Assignment (high-level)
    'KineticsAssigner',
    'AssignmentResult',
    'ConfidenceLevel',
    'AssignmentSource',
    'KineticsMetadata',
]
