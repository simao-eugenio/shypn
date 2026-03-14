"""Skellam Distribution Sampler for Reversible Reactions.

The Skellam distribution models the difference of two independent Poisson variables:
    X = Y₁ - Y₂  where Y₁ ~ Poisson(λ₁), Y₂ ~ Poisson(λ₂)

This is the correct distribution for reversible reactions in τ-leaping:
    Forward:  A → B  with rate k_f × [A]
    Reverse:  B → A  with rate k_r × [B]
    Net flux: k_f × [A] - k_r × [B]  ~ Skellam(k_f × [A] × τ, k_r × [B] × τ)

Properties:
    - Support: All integers (can be negative)
    - Mean: λ₁ - λ₂
    - Variance: λ₁ + λ₂
    
References:
    - Skellam, J. G. (1946). "The frequency distribution of the difference 
      between two Poisson variates belonging to different populations."
      Journal of the Royal Statistical Society, Series A.
"""

import numpy as np
from typing import Tuple, Optional


class SkellamSampler:
    """Skellam distribution sampler for reversible stochastic reactions.
    
    Samples the net number of firings from the difference of two Poisson processes:
        Net firings ~ Skellam(λ_forward, λ_reverse)
    
    where:
        λ_forward = propensity_forward × tau
        λ_reverse = propensity_reverse × tau
    
    Returns the net change (can be positive, negative, or zero).
    
    Example:
        >>> sampler = SkellamSampler(seed=42)
        >>> # Reversible reaction: A ⇌ B
        >>> forward_rate = 2.0  # A → B
        >>> reverse_rate = 1.5  # B → A
        >>> tau = 0.1
        >>> net_firings = sampler.sample(forward_rate, reverse_rate, tau)
        >>> # net_firings could be -2, -1, 0, +1, +2, ...
        >>> # Positive: net forward, Negative: net reverse
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize Skellam sampler.
        
        Args:
            seed: Random seed for reproducibility. If None, uses system entropy.
        """
        self.rng = np.random.default_rng(seed)
    
    def sample(
        self, 
        propensity_forward: float, 
        propensity_reverse: float, 
        tau: float
    ) -> int:
        """Sample net firings from Skellam distribution.
        
        Args:
            propensity_forward: Forward reaction propensity (k_f × [reactants])
            propensity_reverse: Reverse reaction propensity (k_r × [products])
            tau: Time leap size
        
        Returns:
            Net number of firings (positive = forward, negative = reverse)
        
        Raises:
            ValueError: If propensities or tau are negative
        """
        if propensity_forward < 0:
            raise ValueError(f"Forward propensity must be non-negative: {propensity_forward}")
        if propensity_reverse < 0:
            raise ValueError(f"Reverse propensity must be non-negative: {propensity_reverse}")
        if tau < 0:
            raise ValueError(f"Time leap must be non-negative: {tau}")
        
        # Poisson parameters
        lambda_forward = propensity_forward * tau
        lambda_reverse = propensity_reverse * tau
        
        # Special cases for efficiency
        if lambda_forward == 0 and lambda_reverse == 0:
            return 0
        
        if lambda_forward == 0:
            # Only reverse reaction possible
            return -int(self.rng.poisson(lambda_reverse))
        
        if lambda_reverse == 0:
            # Only forward reaction possible
            return int(self.rng.poisson(lambda_forward))
        
        # General case: sample both and compute difference
        forward_firings = int(self.rng.poisson(lambda_forward))
        reverse_firings = int(self.rng.poisson(lambda_reverse))
        
        return forward_firings - reverse_firings
    
    def sample_batch(
        self,
        propensities_forward: np.ndarray,
        propensities_reverse: np.ndarray,
        tau: float
    ) -> np.ndarray:
        """Sample net firings for multiple reversible reactions simultaneously.
        
        Args:
            propensities_forward: Array of forward propensities
            propensities_reverse: Array of reverse propensities
            tau: Time leap size (same for all reactions)
        
        Returns:
            Array of net firings (can contain negative values)
        """
        # Validate inputs
        if len(propensities_forward) != len(propensities_reverse):
            raise ValueError("Forward and reverse propensity arrays must have same length")
        
        # Compute Poisson parameters
        lambdas_forward = propensities_forward * tau
        lambdas_reverse = propensities_reverse * tau
        
        # Sample both directions
        forward_firings = self.rng.poisson(lambdas_forward).astype(int)
        reverse_firings = self.rng.poisson(lambdas_reverse).astype(int)
        
        # Return net change
        return forward_firings - reverse_firings
    
    @staticmethod
    def detect_reversible_formula(formula: str) -> Tuple[bool, str, str]:
        """Detect if a rate formula represents a reversible reaction.
        
        Looks for patterns like: k_f * A - k_r * B
        
        Args:
            formula: Rate formula string
        
        Returns:
            Tuple of (is_reversible, forward_expr, reverse_expr)
            If not reversible, forward_expr = formula, reverse_expr = '0'
        
        Example:
            >>> detect_reversible_formula("comp1 * (kf_0 * A - kr_0 * B)")
            (True, "comp1 * kf_0 * A", "comp1 * kr_0 * B")
        """
        if not isinstance(formula, str):
            return (False, str(formula), '0')
        
        formula_clean = formula.strip()
        
        # Check for forward/reverse rate constant naming
        has_kf = ('kf_' in formula_clean.lower() or 'k_f' in formula_clean.lower() or 
                 'k_forward' in formula_clean.lower())
        has_kr = ('kr_' in formula_clean.lower() or 'k_r' in formula_clean.lower() or 
                 'k_reverse' in formula_clean.lower())
        
        if not (has_kf and has_kr and ' - ' in formula_clean):
            return (False, formula_clean, '0')
        
        import re
        
        # Pattern 1: Parenthesized subtraction "comp1 * (kf * A - kr * B)"
        pattern1 = r'(.+?)\s*\*\s*\(([^)]+)\s*-\s*([^)]+)\)'
        match = re.search(pattern1, formula_clean)
        if match:
            multiplier = match.group(1).strip()
            forward_term = match.group(2).strip()
            reverse_term = match.group(3).strip()
            
            # Reconstruct with multiplier
            forward_expr = f"{multiplier} * {forward_term}"
            reverse_expr = f"{multiplier} * {reverse_term}"
            return (True, forward_expr, reverse_expr)
        
        # Pattern 2: Direct subtraction "kf * A - kr * B"  
        # Split on the last occurrence of ' - ' to handle complex expressions
        parts = formula_clean.rsplit(' - ', 1)
        if len(parts) == 2:
            forward_expr = parts[0].strip()
            reverse_expr = parts[1].strip()
            return (True, forward_expr, reverse_expr)
        
        # Not reversible
        return (False, formula_clean, '0')
