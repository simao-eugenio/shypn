"""Poisson Random Number Sampler for τ-Leaping.

Provides efficient Poisson random number generation for sampling transition
firings within a time leap.

For a transition with propensity a and time leap τ, the number of firings
follows: K ~ Poisson(a·τ)

Implementation uses NumPy's optimized Poisson generator for performance.
"""

import numpy as np
from typing import Union, List


class PoissonSampler:
    """Efficient Poisson random number generator for τ-leaping.
    
    Samples number of transition firings from Poisson distribution:
        K ~ Poisson(λ) where λ = propensity × time_leap
    
    Uses NumPy's random.poisson() which handles both small and large λ
    efficiently (Ahrens-Dieter algorithm for λ < 10, ratio-of-uniforms for λ >= 10).
    
    Example:
        >>> sampler = PoissonSampler(seed=42)
        >>> firings = sampler.sample(propensity=2.5, tau=0.1)  # λ = 0.25
        >>> firings  # 0, 1, or rarely 2
        
        >>> # Batch sampling for multiple transitions
        >>> propensities = [1.0, 2.0, 0.5]
        >>> tau = 0.2
        >>> firings = sampler.sample_batch(propensities, tau)
        >>> firings  # [0, 1, 0] for example
    """
    
    def __init__(self, seed: int = None):
        """Initialize Poisson sampler.
        
        Args:
            seed: Random seed for reproducibility. If None, uses system entropy.
        """
        self.rng = np.random.default_rng(seed)
    
    def sample(self, propensity: float, tau: float) -> int:
        """Sample number of firings for one transition.
        
        Args:
            propensity: Current propensity (rate) of transition
            tau: Time leap size
        
        Returns:
            Number of firings (non-negative integer)
        
        Raises:
            ValueError: If propensity or tau is negative
        """
        if propensity < 0:
            raise ValueError(f"Propensity must be non-negative: {propensity}")
        if tau < 0:
            raise ValueError(f"Time leap must be non-negative: {tau}")
        
        # Special case: zero propensity → no firings
        if propensity == 0:
            return 0
        
        # Poisson parameter λ = propensity × tau
        lambda_param = propensity * tau
        
        # Sample from Poisson(λ)
        return int(self.rng.poisson(lambda_param))
    
    def sample_batch(self, propensities: List[float], tau: float) -> np.ndarray:
        """Sample firings for multiple transitions simultaneously.
        
        More efficient than calling sample() in a loop due to NumPy vectorization.
        
        Args:
            propensities: List of propensities for each transition
            tau: Time leap size (same for all transitions)
        
        Returns:
            NumPy array of firing counts (one per transition)
        
        Example:
            >>> sampler.sample_batch([1.0, 2.0, 0.5], tau=0.1)
            array([0, 0, 0])  # Low propensities × small tau → mostly zeros
        """
        if tau < 0:
            raise ValueError(f"Time leap must be non-negative: {tau}")
        
        propensities = np.array(propensities)
        
        if np.any(propensities < 0):
            raise ValueError("All propensities must be non-negative")
        
        # Vectorized: λ_i = a_i × τ for all i
        lambda_params = propensities * tau
        
        # Vectorized Poisson sampling
        firings = self.rng.poisson(lambda_params)
        
        return firings.astype(int)
    
    def sample_conditional(self, propensity: float, tau: float, max_firings: int) -> int:
        """Sample firings with upper bound constraint.
        
        Useful for transitions with limited tokens available. Ensures
        sampled firings don't exceed what's physically possible.
        
        Args:
            propensity: Transition propensity
            tau: Time leap
            max_firings: Maximum allowed firings (based on available tokens)
        
        Returns:
            min(Poisson(propensity × tau), max_firings)
        """
        firings = self.sample(propensity, tau)
        return min(firings, max_firings)
    
    def set_seed(self, seed: int):
        """Reset random seed for reproducibility.
        
        Args:
            seed: New random seed
        """
        self.rng = np.random.default_rng(seed)
    
    def estimate_mean_firings(self, propensity: float, tau: float) -> float:
        """Calculate expected number of firings (theoretical mean).
        
        For Poisson(λ), E[K] = λ = propensity × tau
        
        Useful for leap size selection and validation.
        
        Args:
            propensity: Transition propensity
            tau: Time leap
        
        Returns:
            Expected number of firings
        """
        return propensity * tau
    
    def estimate_variance(self, propensity: float, tau: float) -> float:
        """Calculate variance of firings (theoretical).
        
        For Poisson(λ), Var[K] = λ = propensity × tau
        
        Args:
            propensity: Transition propensity
            tau: Time leap
        
        Returns:
            Variance of firing count
        """
        return propensity * tau
