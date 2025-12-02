"""τ-Leaping Simulation Package for Stochastic Petri Nets.

This package implements approximate stochastic simulation using the τ-leaping
method (Gillespie 2001, Cao et al. 2006), with extensions for weak independence
and parallel execution.

Modules:
    tau_leaping_engine: Main τ-leaping execution engine
    leap_selector: Adaptive leap size selection
    poisson_sampler: Poisson random number generation
    parallel_scheduler: (Phase 3) Weak independence-aware parallel execution

Theory:
    τ-leaping approximates exact SSA by:
    1. Selecting time leap Δτ where propensities stay approximately constant
    2. Sampling number of firings for each transition from Poisson(aⱼ·Δτ)
    3. Applying all firings simultaneously (superposition)

    This provides significant speedup (10-100×) with controlled accuracy loss.

References:
    - Gillespie, D. T. (2001). Approximate accelerated stochastic simulation.
      J. Chem. Phys., 115(4), 1716-1733.
    - Cao, Y., Gillespie, D. T., & Petzold, L. R. (2006). Efficient step size
      selection for the tau-leaping simulation method. J. Chem. Phys., 124(4).

Author: Implementation based on bioinformatics paper future work section
Date: December 2025
"""

__version__ = "0.2.0"

from .tau_leaping_engine import TauLeapingEngine
from .leap_selector import LeapSelector
from .poisson_sampler import PoissonSampler
from .parallel_scheduler import ParallelStochasticScheduler

__all__ = [
    'TauLeapingEngine',
    'LeapSelector',
    'PoissonSampler',
    'ParallelStochasticScheduler',
]
