"""τ-Leaping Simulation Package for Stochastic Petri Nets.

This package implements approximate stochastic simulation using the τ-leaping
method (Gillespie 2001, Cao et al. 2006), with extensions for weak independence,
parallel execution, and reversible reactions.

Modules:
    tau_leaping_engine: Main τ-leaping execution engine
    leap_selector: Adaptive leap size selection
    poisson_sampler: Poisson random number generation (irreversible reactions)
    skellam_sampler: Skellam distribution sampling (reversible reactions)
    parallel_scheduler: (Phase 3) Weak independence-aware parallel execution

Theory:
    τ-leaping approximates exact SSA by:
    1. Selecting time leap Δτ where propensities stay approximately constant
    2. Sampling number of firings:
       - Irreversible: Kⱼ ~ Poisson(aⱼ·Δτ)
       - Reversible: ΔKⱼ ~ Skellam(a_forward·Δτ, a_reverse·Δτ)
    3. Applying all firings simultaneously (superposition)

    This provides significant speedup (10-100×) with controlled accuracy loss.

References:
    - Gillespie, D. T. (2001). Approximate accelerated stochastic simulation.
      J. Chem. Phys., 115(4), 1716-1733.
    - Cao, Y., Gillespie, D. T., & Petzold, L. R. (2006). Efficient step size
      selection for the tau-leaping simulation method. J. Chem. Phys., 124(4).
    - Skellam, J. G. (1946). The frequency distribution of the difference
      between two Poisson variates belonging to different populations.

Author: Implementation based on bioinformatics paper future work section
Date: December 2025
"""

__version__ = "0.3.0"  # Added Skellam distribution support

from .tau_leaping_engine import TauLeapingEngine
from .leap_selector import LeapSelector
from .poisson_sampler import PoissonSampler
from .skellam_sampler import SkellamSampler
from .parallel_scheduler import ParallelStochasticScheduler

__all__ = [
    'TauLeapingEngine',
    'LeapSelector',
    'PoissonSampler',
    'SkellamSampler',
    'ParallelStochasticScheduler',
]
