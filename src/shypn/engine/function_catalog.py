#!/usr/bin/env python3
"""Function Catalog - Ready-to-use mathematical functions for transitions.

This module provides a comprehensive catalog of common mathematical functions
that users can use in transition rate expressions, including:

- Activation functions (sigmoid, tanh, relu, etc.)
- Growth models (exponential, logistic, Gompertz, etc.)
- Kinetic models (Michaelis-Menten, Hill, etc.)
- Distribution functions (normal, exponential, gamma, etc.)
- Utility functions (step, ramp, pulse, etc.)

Usage in rate expressions:
    # Simple function call
    "sigmoid(time, 10, 0.5)"
    
    # With place references
    "michaelis_menten(P1, 10, 5)"
    
    # Combined functions
    "exponential_growth(P1, 0.1) + normal_pdf(time, 10, 2)"
    
    # Dict format
    {'rate': lambda places, t: sigmoid(t, 10, 0.5)}
"""

import numpy as np
import math
from typing import Callable, Dict, Any, Optional


# =============================================================================
# ACTIVATION FUNCTIONS (S-curves and transitions)
# =============================================================================

def sigmoid(x: float, center: float = 0.0, steepness: float = 1.0, 
            amplitude: float = 1.0) -> float:
    """Logistic sigmoid function (S-curve).
    
    Formula: σ(x) = A / (1 + e^(-k(x - x₀)))
    
    Args:
        x: Input value (time or place tokens)
        center: Midpoint/inflection point (x₀), default 0
        steepness: Slope at inflection (k), default 1
        amplitude: Maximum value (A), default 1
    
    Returns:
        Value between 0 and amplitude
    
    Example:
        # Smooth transition from 0 to 10 centered at t=20
        rate = sigmoid(time, center=20, steepness=0.5, amplitude=10)
    """
    return amplitude / (1.0 + np.exp(-steepness * (x - center)))


def tanh_activation(x: float, center: float = 0.0, steepness: float = 1.0,
                   amplitude: float = 1.0) -> float:
    """Hyperbolic tangent activation (smooth S-curve from -A to +A).
    
    Formula: A * tanh(k(x - x₀))
    
    Args:
        x: Input value
        center: Center point, default 0
        steepness: Slope factor, default 1
        amplitude: Maximum absolute value, default 1
    
    Returns:
        Value between -amplitude and +amplitude
    
    Example:
        # Transition from -5 to +5
        rate = tanh_activation(time, center=10, steepness=0.3, amplitude=5)
    """
    return amplitude * np.tanh(steepness * (x - center))


def relu(x: float, threshold: float = 0.0) -> float:
    """Rectified Linear Unit (ReLU).
    
    Formula: max(0, x - threshold)
    
    Args:
        x: Input value
        threshold: Activation threshold, default 0
    
    Returns:
        0 if x < threshold, else (x - threshold)
    
    Example:
        # Activate only when tokens > 10
        rate = relu(P1, threshold=10)
    """
    return max(0.0, x - threshold)


def leaky_relu(x: float, threshold: float = 0.0, alpha: float = 0.01) -> float:
    """Leaky ReLU (allows small negative slope).
    
    Formula: x - threshold if x > threshold, else α(x - threshold)
    
    Args:
        x: Input value
        threshold: Activation threshold, default 0
        alpha: Negative slope coefficient, default 0.01
    
    Returns:
        Linear activation with small negative slope
    
    Example:
        rate = leaky_relu(P1, threshold=5, alpha=0.1)
    """
    return (x - threshold) if x > threshold else alpha * (x - threshold)


def softplus(x: float, beta: float = 1.0) -> float:
    """Smooth approximation of ReLU.
    
    Formula: (1/β) * ln(1 + e^(βx))
    
    Args:
        x: Input value
        beta: Smoothness parameter, default 1
    
    Returns:
        Smooth positive activation
    
    Example:
        rate = softplus(P1, beta=0.5)
    """
    return (1.0 / beta) * np.log(1.0 + np.exp(beta * x))


# =============================================================================
# GROWTH MODELS (population, biological, chemical)
# =============================================================================

def exponential_growth(x: float, rate: float) -> float:
    """Exponential growth/decay.
    
    Formula: x * e^(rt) where r is growth rate
    
    Args:
        x: Current value (population, tokens)
        rate: Growth rate (positive=growth, negative=decay)
    
    Returns:
        Growth rate: dx/dt = r*x
    
    Example:
        # 10% growth rate
        rate_func = exponential_growth(P1, 0.1)
    """
    return x * np.exp(rate)


def exponential_decay(x: float, half_life: float) -> float:
    """Exponential decay with half-life.
    
    Formula: x * e^(-ln(2)*t/t_half)
    
    Args:
        x: Current value
        half_life: Time for value to halve
    
    Returns:
        Decay rate
    
    Example:
        # Half-life of 10 time units
        rate = exponential_decay(P1, half_life=10)
    """
    return x * np.exp(-np.log(2) / half_life)


def logistic_growth(x: float, carrying_capacity: float, growth_rate: float) -> float:
    """Logistic growth with carrying capacity.
    
    Formula: r * x * (1 - x/K) where K is carrying capacity
    
    Args:
        x: Current population
        carrying_capacity: Maximum sustainable population (K)
        growth_rate: Intrinsic growth rate (r)
    
    Returns:
        Growth rate: dx/dt = r*x*(1 - x/K)
    
    Example:
        # Population with capacity 100, growth rate 0.1
        rate = logistic_growth(P1, carrying_capacity=100, growth_rate=0.1)
    """
    return growth_rate * x * (1.0 - x / carrying_capacity)


def gompertz_growth(x: float, carrying_capacity: float, growth_rate: float) -> float:
    """Gompertz growth model (asymmetric S-curve).
    
    Formula: r * x * ln(K/x)
    
    Args:
        x: Current population
        carrying_capacity: Maximum population (K)
        growth_rate: Growth rate parameter (r)
    
    Returns:
        Growth rate (asymmetric sigmoid)
    
    Example:
        # Tumor growth model
        rate = gompertz_growth(P1, carrying_capacity=100, growth_rate=0.05)
    """
    if x <= 0 or x >= carrying_capacity:
        return 0.0
    return growth_rate * x * np.log(carrying_capacity / x)


# =============================================================================
# KINETIC MODELS (enzyme kinetics, reaction rates)
# =============================================================================

def michaelis_menten(substrate: float, vmax: float, km: float) -> float:
    """Michaelis-Menten enzyme kinetics.
    
    Formula: V = Vmax * [S] / (Km + [S])
    
    Args:
        substrate: Substrate concentration [S]
        vmax: Maximum reaction velocity
        km: Michaelis constant (substrate concentration at half Vmax)
    
    Returns:
        Reaction velocity
    
    Example:
        # Enzyme reaction with Vmax=10, Km=5
        rate = michaelis_menten(P1, vmax=10, km=5)
    """
    return vmax * substrate / (km + substrate)


def hill_equation(substrate: float, vmax: float, kd: float, n: float = 1.0) -> float:
    """Hill equation (cooperative binding).
    
    Formula: V = Vmax * [S]^n / (Kd^n + [S]^n)
    
    Args:
        substrate: Ligand concentration [S]
        vmax: Maximum velocity
        kd: Dissociation constant
        n: Hill coefficient (cooperativity), default 1
    
    Returns:
        Binding rate
    
    Example:
        # Cooperative binding (n=2.5)
        rate = hill_equation(P1, vmax=10, kd=5, n=2.5)
    """
    substrate_n = np.power(substrate, n)
    kd_n = np.power(kd, n)
    return vmax * substrate_n / (kd_n + substrate_n)


def competitive_inhibition(substrate: float, inhibitor: float, vmax: float,
                          km: float, ki: float) -> float:
    """Competitive enzyme inhibition.
    
    Formula: V = Vmax * [S] / (Km(1 + [I]/Ki) + [S])
    
    Args:
        substrate: Substrate concentration [S]
        inhibitor: Inhibitor concentration [I]
        vmax: Maximum velocity
        km: Michaelis constant
        ki: Inhibition constant
    
    Returns:
        Inhibited reaction velocity
    
    Example:
        rate = competitive_inhibition(P1, P2, vmax=10, km=5, ki=2)
    """
    km_apparent = km * (1.0 + inhibitor / ki)
    return vmax * substrate / (km_apparent + substrate)


def mass_action(reactant1: float, reactant2: float = 1.0, rate_constant: float = 1.0) -> float:
    """Mass action kinetics (law of mass action).
    
    Formula: k * [A] * [B]
    
    Args:
        reactant1: Concentration of first reactant [A]
        reactant2: Concentration of second reactant [B], default 1
        rate_constant: Rate constant k
    
    Returns:
        Reaction rate
    
    Example:
        # Bimolecular reaction
        rate = mass_action(P1, P2, rate_constant=0.1)
    """
    return rate_constant * reactant1 * reactant2


# =============================================================================
# DISTRIBUTION FUNCTIONS (probability densities)
# =============================================================================

def normal_pdf(x: float, mean: float = 0.0, std: float = 1.0) -> float:
    """Normal (Gaussian) probability density function.
    
    Formula: (1/σ√(2π)) * e^(-(x-μ)²/(2σ²))
    
    Args:
        x: Input value
        mean: Mean (μ), default 0
        std: Standard deviation (σ), default 1
    
    Returns:
        Probability density
    
    Example:
        # Bell curve centered at t=10 with width 2
        rate = 10 * normal_pdf(time, mean=10, std=2)
    """
    coefficient = 1.0 / (std * np.sqrt(2.0 * np.pi))
    exponent = -0.5 * np.power((x - mean) / std, 2.0)
    return coefficient * np.exp(exponent)


def exponential_pdf(x: float, rate: float = 1.0) -> float:
    """Exponential probability density function.
    
    Formula: λ * e^(-λx) for x ≥ 0
    
    Args:
        x: Input value (must be non-negative)
        rate: Rate parameter λ, default 1
    
    Returns:
        Probability density (0 if x < 0)
    
    Example:
        # Exponential distribution with λ=0.5
        rate_func = exponential_pdf(time, rate=0.5)
    """
    if x < 0:
        return 0.0
    return rate * np.exp(-rate * x)


def gamma_pdf(x: float, shape: float, scale: float = 1.0) -> float:
    """Gamma probability density function.
    
    Formula: (x^(k-1) * e^(-x/θ)) / (θ^k * Γ(k))
    
    Args:
        x: Input value (must be non-negative)
        shape: Shape parameter k (α)
        scale: Scale parameter θ (β), default 1
    
    Returns:
        Probability density
    
    Example:
        # Gamma distribution
        rate = gamma_pdf(time, shape=2.0, scale=3.0)
    """
    if x <= 0:
        return 0.0
    from scipy import special
    coefficient = 1.0 / (np.power(scale, shape) * special.gamma(shape))
    return coefficient * np.power(x, shape - 1.0) * np.exp(-x / scale)


def uniform(x: float, low: float = 0.0, high: float = 1.0) -> float:
    """Uniform distribution (constant within range).
    
    Formula: 1/(b-a) if a ≤ x ≤ b, else 0
    
    Args:
        x: Input value
        low: Lower bound (a), default 0
        high: Upper bound (b), default 1
    
    Returns:
        1/(high-low) if in range, else 0
    
    Example:
        # Constant rate between t=5 and t=15
        rate = 10 * uniform(time, low=5, high=15)
    """
    if low <= x <= high:
        return 1.0 / (high - low)
    return 0.0


# =============================================================================
# UTILITY FUNCTIONS (control, timing, shaping)
# =============================================================================

def step(x: float, threshold: float, low: float = 0.0, high: float = 1.0) -> float:
    """Step function (Heaviside function).
    
    Args:
        x: Input value
        threshold: Step threshold
        low: Value before threshold, default 0
        high: Value after threshold, default 1
    
    Returns:
        low if x < threshold, else high
    
    Example:
        # Jump from 0 to 10 at t=15
        rate = step(time, threshold=15, low=0, high=10)
    """
    return high if x >= threshold else low


def ramp(x: float, start: float, end: float, low: float = 0.0, high: float = 1.0) -> float:
    """Linear ramp function.
    
    Args:
        x: Input value
        start: Ramp start point
        end: Ramp end point
        low: Value before start, default 0
        high: Value after end, default 1
    
    Returns:
        Linearly interpolated value
    
    Example:
        # Linear increase from 0 to 10 between t=5 and t=15
        rate = ramp(time, start=5, end=15, low=0, high=10)
    """
    if x < start:
        return low
    elif x > end:
        return high
    else:
        # Linear interpolation
        fraction = (x - start) / (end - start)
        return low + fraction * (high - low)


def pulse(x: float, start: float, end: float, amplitude: float = 1.0) -> float:
    """Rectangular pulse function.
    
    Args:
        x: Input value
        start: Pulse start
        end: Pulse end
        amplitude: Pulse height, default 1
    
    Returns:
        amplitude if start ≤ x ≤ end, else 0
    
    Example:
        # Pulse of rate 10 from t=5 to t=15
        rate = pulse(time, start=5, end=15, amplitude=10)
    """
    return amplitude if start <= x <= end else 0.0


def periodic_pulse(x: float, period: float, duty_cycle: float = 0.5,
                   amplitude: float = 1.0) -> float:
    """Periodic pulse train.
    
    Args:
        x: Input value
        period: Period length
        duty_cycle: Fraction of period that's "on" (0-1), default 0.5
        amplitude: Pulse amplitude, default 1
    
    Returns:
        amplitude during "on" phase, 0 during "off" phase
    
    Example:
        # Square wave with period 10, 50% duty cycle
        rate = periodic_pulse(time, period=10, duty_cycle=0.5, amplitude=5)
    """
    phase = (x % period) / period
    return amplitude if phase < duty_cycle else 0.0


def triangle_wave(x: float, period: float, amplitude: float = 1.0) -> float:
    """Triangle wave function.
    
    Args:
        x: Input value
        period: Period length
        amplitude: Wave amplitude, default 1
    
    Returns:
        Triangular oscillation
    
    Example:
        # Triangle wave with period 20, amplitude 10
        rate = triangle_wave(time, period=20, amplitude=10)
    """
    phase = (x % period) / period
    if phase < 0.5:
        return 4.0 * amplitude * phase
    else:
        return 4.0 * amplitude * (1.0 - phase)


def sawtooth_wave(x: float, period: float, amplitude: float = 1.0) -> float:
    """Sawtooth wave function.
    
    Args:
        x: Input value
        period: Period length
        amplitude: Wave amplitude, default 1
    
    Returns:
        Sawtooth oscillation
    
    Example:
        rate = sawtooth_wave(time, period=15, amplitude=8)
    """
    phase = (x % period) / period
    return amplitude * phase


# =============================================================================
# COMBINED/COMPLEX FUNCTIONS
# =============================================================================

def double_sigmoid(x: float, center1: float, center2: float, 
                  steepness1: float = 1.0, steepness2: float = 1.0,
                  amplitude: float = 1.0) -> float:
    """Double sigmoid (two S-curves).
    
    Creates a function that rises, plateaus, then rises again.
    
    Args:
        x: Input value
        center1: First inflection point
        center2: Second inflection point
        steepness1: Slope at first inflection, default 1
        steepness2: Slope at second inflection, default 1
        amplitude: Total amplitude, default 1
    
    Returns:
        Combined sigmoid value
    
    Example:
        # Two-phase activation
        rate = double_sigmoid(time, center1=10, center2=30, amplitude=10)
    """
    sig1 = sigmoid(x, center1, steepness1, amplitude / 2.0)
    sig2 = sigmoid(x, center2, steepness2, amplitude / 2.0)
    return sig1 + sig2


def bell_curve(x: float, center: float, width: float, amplitude: float = 1.0) -> float:
    """Bell-shaped curve (Gaussian envelope).
    
    Args:
        x: Input value
        center: Peak position
        width: Curve width (standard deviation)
        amplitude: Peak amplitude, default 1
    
    Returns:
        Bell curve value
    
    Example:
        # Transient burst of activity centered at t=20
        rate = bell_curve(time, center=20, width=5, amplitude=10)
    """
    return amplitude * np.exp(-0.5 * np.power((x - center) / width, 2.0))


def bounded_linear(x: float, slope: float, intercept: float = 0.0,
                  min_val: float = 0.0, max_val: float = float('inf')) -> float:
    """Linear function with bounds.
    
    Args:
        x: Input value
        slope: Linear slope
        intercept: Y-intercept, default 0
        min_val: Minimum value, default 0
        max_val: Maximum value, default inf
    
    Returns:
        Bounded linear value
    
    Example:
        # Linear growth capped at 10
        rate = bounded_linear(P1, slope=0.5, intercept=1, min_val=0, max_val=10)
    """
    value = slope * x + intercept
    return np.clip(value, min_val, max_val)


# =============================================================================
# HELPER UTILITIES
# =============================================================================

def interpolate(x: float, x_points: list, y_points: list) -> float:
    """Linear interpolation between points.
    
    Args:
        x: Input value
        x_points: List of x coordinates (must be sorted)
        y_points: List of y coordinates
    
    Returns:
        Interpolated value
    
    Example:
        # Custom curve through points
        rate = interpolate(time, [0, 10, 20, 30], [0, 5, 8, 10])
    """
    return np.interp(x, x_points, y_points)


def smooth_threshold(x: float, threshold: float, width: float) -> float:
    """Smooth threshold function (soft step).
    
    Uses sigmoid to create smooth transition around threshold.
    
    Args:
        x: Input value
        threshold: Threshold point
        width: Transition width, default 1
    
    Returns:
        Smooth 0-to-1 transition
    
    Example:
        # Smooth activation around 10 tokens
        rate = 10 * smooth_threshold(P1, threshold=10, width=2)
    """
    steepness = 5.0 / width  # 5 = reasonable steepness factor
    return sigmoid(x, threshold, steepness, 1.0)


# =============================================================================
# STOCHASTIC FUNCTIONS (Noise and random processes)
# =============================================================================

# Global state for Wiener process (maintain continuity between calls)
_wiener_state = {}

def wiener(t: float, amplitude: float = 1.0, dt: float = 0.1, seed: int = None) -> float:
    """Wiener process (Brownian motion) - continuous stochastic process.
    
    Generates correlated random noise using discrete-time approximation:
        dW = amplitude * sqrt(dt) * N(0,1)
    
    The process maintains continuity between calls, so wiener(t) at t=1.0
    will be close to wiener(t) at t=0.9 (they differ by one random step).
    
    Args:
        t: Current time (used as key for state lookup)
        amplitude: Scale factor for noise (default 1.0)
        dt: Time step for discretization (default 0.1)
        seed: Random seed for reproducibility (optional)
    
    Returns:
        Current value of Wiener process (cumulative random walk)
    
    Note:
        This is a simplified implementation that assumes regular time steps.
        For irregular steps, use ornstein_uhlenbeck() instead.
    
    Example:
        # Add 10% Brownian noise to base rate
        rate = 1.0 * (1 + 0.1 * wiener(time))
        
        # Stronger noise
        rate = 1.0 * (1 + 0.3 * wiener(time, amplitude=1.0))
    """
    global _wiener_state
    
    # Set random seed if provided (once)
    if seed is not None and 'seed_set' not in _wiener_state:
        np.random.seed(seed)
        _wiener_state['seed_set'] = True
    
    # Round time to nearest dt to create discrete steps
    time_key = round(t / dt) * dt
    
    # If this is a new time point, generate next increment
    if time_key not in _wiener_state:
        # Get previous value (or start at 0)
        prev_time = time_key - dt
        prev_value = _wiener_state.get(prev_time, 0.0)
        
        # Wiener increment: dW = amplitude * sqrt(dt) * N(0,1)
        increment = amplitude * np.sqrt(dt) * np.random.randn()
        _wiener_state[time_key] = prev_value + increment
        
        # Clean up old values to prevent memory leak (keep last 100 steps)
        if len(_wiener_state) > 100:
            oldest_key = min(k for k in _wiener_state.keys() if isinstance(k, (int, float)))
            _wiener_state.pop(oldest_key, None)
    
    return _wiener_state[time_key]


def reset_wiener() -> None:
    """Reset the Wiener process state (for new simulations)."""
    global _wiener_state
    _wiener_state = {}


def gaussian_noise(mean: float = 0.0, std: float = 1.0) -> float:
    """Independent Gaussian noise (not time-correlated like Wiener).
    
    Returns a new random sample from N(mean, std) each time called.
    Unlike wiener(), each call is independent (no correlation between timesteps).
    
    Args:
        mean: Mean of the distribution (default 0.0)
        std: Standard deviation (default 1.0)
    
    Returns:
        Random sample from N(mean, std)
    
    Example:
        # Add independent noise to each timestep
        rate = 1.0 + 0.1 * gaussian_noise(0, 1)
        
        # Multiplicative noise
        rate = 1.0 * (1 + 0.1 * gaussian_noise())
    """
    return np.random.normal(mean, std)


def uniform_noise(low: float = 0.0, high: float = 1.0) -> float:
    """Independent uniform noise in [low, high].
    
    Args:
        low: Minimum value (default 0.0)
        high: Maximum value (default 1.0)
    
    Returns:
        Random sample from Uniform(low, high)
    
    Example:
        # Random rate between 0.5 and 1.5
        rate = uniform_noise(0.5, 1.5)
    """
    return np.random.uniform(low, high)


def poisson_noise(lam: float = 1.0) -> float:
    """Independent Poisson noise (for discrete count events).
    
    Args:
        lam: Rate parameter (mean and variance of distribution)
    
    Returns:
        Random integer from Poisson(lam) as float
    
    Example:
        # Random burst size from Poisson distribution
        burst_size = poisson_noise(lam=5.0)  # Mean 5 events
    """
    return float(np.random.poisson(lam))


def ornstein_uhlenbeck(t: float, x_current: float, theta: float = 1.0, 
                       mu: float = 0.0, sigma: float = 1.0, dt: float = 0.1) -> float:
    """Ornstein-Uhlenbeck process (mean-reverting noise).
    
    Models stochastic process that tends to drift toward mean:
        dx = theta * (mu - x) * dt + sigma * dW
    
    Args:
        t: Current time (for random seed consistency)
        x_current: Current value of the process
        theta: Mean reversion rate (higher = faster return to mean)
        mu: Long-term mean
        sigma: Volatility (noise amplitude)
        dt: Time step
    
    Returns:
        Next value of OU process
    
    Example:
        # Mean-reverting noise around rate=1.0
        # Initialize: x = 1.0
        # Update: x = ornstein_uhlenbeck(time, x, theta=0.5, mu=1.0, sigma=0.2)
        # Use: rate = x
    """
    # Mean reversion term
    drift = theta * (mu - x_current) * dt
    
    # Stochastic term
    diffusion = sigma * np.sqrt(dt) * np.random.randn()
    
    return x_current + drift + diffusion


# =============================================================================
# CATALOG DICTIONARY (for easy access)
# =============================================================================

FUNCTION_CATALOG = {
    # Activation functions
    'sigmoid': sigmoid,
    'tanh': tanh_activation,
    'relu': relu,
    'leaky_relu': leaky_relu,
    'softplus': softplus,
    
    # Growth models
    'exponential_growth': exponential_growth,
    'exponential_decay': exponential_decay,
    'logistic_growth': logistic_growth,
    'gompertz_growth': gompertz_growth,
    
    # Kinetic models
    'michaelis_menten': michaelis_menten,
    'hill_equation': hill_equation,
    'competitive_inhibition': competitive_inhibition,
    'mass_action': mass_action,
    
    # Distribution functions
    'normal_pdf': normal_pdf,
    'exponential_pdf': exponential_pdf,
    'gamma_pdf': gamma_pdf,
    'uniform': uniform,
    
    # Utility functions
    'step': step,
    'ramp': ramp,
    'pulse': pulse,
    'periodic_pulse': periodic_pulse,
    'triangle_wave': triangle_wave,
    'sawtooth_wave': sawtooth_wave,
    
    # Combined functions
    'double_sigmoid': double_sigmoid,
    'bell_curve': bell_curve,
    'bounded_linear': bounded_linear,
    
    # Helper utilities
    'interpolate': interpolate,
    'smooth_threshold': smooth_threshold,
    
    # Stochastic functions (for steady state escape, molecular noise modeling)
    'wiener': wiener,
    'reset_wiener': reset_wiener,
    'gaussian_noise': gaussian_noise,
    'uniform_noise': uniform_noise,
    'poisson_noise': poisson_noise,
    'ornstein_uhlenbeck': ornstein_uhlenbeck,
}


def get_catalog() -> Dict[str, Callable]:
    """Get the complete function catalog.
    
    Returns:
        Dictionary mapping function names to callable functions
    """
    return FUNCTION_CATALOG.copy()


def get_function(name: str) -> Optional[Callable]:
    """Get a specific function from the catalog.
    
    Args:
        name: Function name
    
    Returns:
        Function callable, or None if not found
    """
    return FUNCTION_CATALOG.get(name)


def list_functions() -> list:
    """Get list of all available function names.
    
    Returns:
        Sorted list of function names
    """
    return sorted(FUNCTION_CATALOG.keys())


def get_function_info(name: str) -> str:
    """Get documentation for a specific function.
    
    Args:
        name: Function name
    
    Returns:
        Function docstring, or error message if not found
    """
    func = get_function(name)
    if func is None:
        return f"Function '{name}' not found in catalog"
    return func.__doc__ or "No documentation available"
