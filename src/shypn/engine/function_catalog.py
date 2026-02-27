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
from typing import Callable, Dict, Any, Optional, cast


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
_wiener_state: Dict[Any, Any] = {}

def wiener(t: float, amplitude: float = 1.0, dt: float = 0.1, seed: Optional[int] = None) -> float:
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
# BIOPHYSICAL / THERMODYNAMIC FUNCTIONS
# =============================================================================

def celsius_to_kelvin(celsius: float) -> float:
    """Convert Celsius to Kelvin.
    
    Formula: K = °C + 273.15
    
    Args:
        celsius: Temperature in Celsius
    
    Returns:
        Temperature in Kelvin
    
    Example:
        T_kelvin = celsius_to_kelvin(37)  # 310.15 K
    """
    return celsius + 273.15


def kelvin_to_celsius(kelvin: float) -> float:
    """Convert Kelvin to Celsius.
    
    Formula: °C = K - 273.15
    
    Args:
        kelvin: Temperature in Kelvin
    
    Returns:
        Temperature in Celsius
    
    Example:
        T_celsius = kelvin_to_celsius(310.15)  # 37°C
    """
    return kelvin - 273.15


def arrhenius(T: float, Ea: float, A: float = 1.0, T0: float = 310.15, celsius: bool = False) -> float:
    """Arrhenius equation for temperature-dependent reaction rates.
    
    Formula: k(T) = A * exp(-Ea / (R * T))
    Relative form: k(T) / k(T0) = exp(-Ea/R * (1/T - 1/T0))
    
    Args:
        T: Temperature (in Kelvin by default, or Celsius if celsius=True)
        Ea: Activation energy in kJ/mol
        A: Pre-exponential factor (default 1.0 for relative rates)
        T0: Reference temperature (same units as T, default 310.15 K = 37°C)
        celsius: If True, treat T and T0 as Celsius (default False=Kelvin)
    
    Returns:
        Rate constant at temperature T
    
    Example:
        # Using Kelvin (traditional thermodynamics)
        rate = k_base * arrhenius(T=[Temperature], Ea=50, T0=310) * [Substrate]
        
        # Using Celsius (more intuitive for biology)
        rate = k_base * arrhenius(T=37, Ea=50, T0=37, celsius=True) * [Substrate]
        
        # With Ea=50 kJ/mol at body temp reference:
        # T=25°C → factor=0.77 (slower at room temp)
        # T=37°C → factor=1.00 (reference, body temp)
        # T=40°C → factor=1.14 (fever)
    
    Note:
        R = 0.008314 kJ/(mol·K) is the gas constant
        Typical enzyme Ea: 40-80 kJ/mol
        Diffusion Ea: 10-30 kJ/mol
        Q10 ≈ exp(Ea/R * 10/T^2) ≈ 2 for Ea~50 kJ/mol
    """
    R = 0.008314  # kJ/(mol·K)
    
    # Convert to Kelvin if needed
    if celsius:
        T = celsius_to_kelvin(T)
        T0 = celsius_to_kelvin(T0)
    
    # Prevent division by zero
    if T <= 0:
        return 0.0
    
    # Relative rate (normalized to T0)
    return A * np.exp(-Ea / R * (1.0/T - 1.0/T0))


def nernst_potential(z: float, C_out: float, C_in: float, T: float = 310.15, celsius: bool = False) -> float:
    """Nernst equation for equilibrium potential of an ion.
    
    Formula: E = (RT / zF) * ln(C_out / C_in)
           ≈ (26.7 mV / z) * log10(C_out / C_in)  at 37°C
    
    Args:
        z: Ion charge (e.g., +1 for Na+, -1 for Cl-, +2 for Ca2+)
        C_out: Extracellular concentration (mM)
        C_in: Intracellular concentration (mM)
        T: Temperature (Kelvin by default, Celsius if celsius=True, default 310.15K = 37°C)
        celsius: If True, treat T as Celsius (default False=Kelvin)
    
    Returns:
        Equilibrium potential in millivolts (mV)
    
    Example:
        # Calculate Na+ equilibrium potential at body temp
        E_Na = nernst_potential(z=1, C_out=145, C_in=12)  # ≈ +67 mV
        
        # Using Celsius
        E_Na = nernst_potential(z=1, C_out=145, C_in=12, T=37, celsius=True)
        
        # Use in driving force calculation
        driving_force = [Membrane_potential] - nernst_potential(1, 145, 12)
        rate = g_Na * driving_force * [Na_channel_open]
    
    Note:
        R = 8.314 J/(mol·K), F = 96485 C/mol
        At T=310K: RT/F ≈ 26.7 mV
        Typical values:
        - Na+: E_Na ≈ +67 mV
        - K+:  E_K  ≈ -90 mV
        - Ca2+: E_Ca ≈ +123 mV
        - Cl-: E_Cl ≈ -60 mV
    """
    R = 8.314  # J/(mol·K)
    F = 96485  # C/mol
    
    # Convert to Kelvin if needed
    if celsius:
        T = celsius_to_kelvin(T)
    
    if z == 0 or C_in <= 0 or C_out <= 0:
        return 0.0
    
    # Nernst potential in mV
    E = (R * T / (z * F)) * np.log(C_out / C_in) * 1000  # Convert V to mV
    
    return E


def goldman_equation(P_Na: float, P_K: float, P_Cl: float,
                    Na_out: float, Na_in: float,
                    K_out: float, K_in: float,
                    Cl_out: float, Cl_in: float,
                    T: float = 310.15, celsius: bool = False) -> float:
    """Goldman-Hodgkin-Katz equation for membrane potential.
    
    Calculates membrane potential from multiple ion gradients and permeabilities.
    
    Formula: V_m = (RT/F) * ln((P_Na[Na]_o + P_K[K]_o + P_Cl[Cl]_i) / 
                                 (P_Na[Na]_i + P_K[K]_i + P_Cl[Cl]_o))
    
    Args:
        P_Na, P_K, P_Cl: Relative permeabilities (typically P_K=1.0)
        Na_out, Na_in: Sodium concentrations (mM)
        K_out, K_in: Potassium concentrations (mM)
        Cl_out, Cl_in: Chloride concentrations (mM)
        T: Temperature (Kelvin by default, Celsius if celsius=True, default 310.15K)
        celsius: If True, treat T as Celsius (default False=Kelvin)
    
    Returns:
        Membrane potential in millivolts (mV)
    
    Example:
        # Resting potential with typical permeabilities
        V_m = goldman_equation(
            P_Na=0.04, P_K=1.0, P_Cl=0.45,  # Relative permeabilities
            Na_out=145, Na_in=12,
            K_out=4, K_in=155,
            Cl_out=110, Cl_in=4,
            T=37, celsius=True  # Use Celsius
        )  # ≈ -70 mV
    """
    R = 8.314
    F = 96485
    
    # Convert to Kelvin if needed
    if celsius:
        T = celsius_to_kelvin(T)
    
    numerator = P_Na * Na_out + P_K * K_out + P_Cl * Cl_in
    denominator = P_Na * Na_in + P_K * K_in + P_Cl * Cl_out
    
    if denominator <= 0:
        return 0.0
    
    V_m = (R * T / F) * np.log(numerator / denominator) * 1000  # mV
    
    return V_m


def ph_to_concentration(pH: float) -> float:
    """Convert pH to H+ concentration.
    
    Formula: [H+] = 10^(-pH) mol/L
    
    Args:
        pH: pH value (typically 0-14)
    
    Returns:
        H+ concentration in molar (M)
    
    Example:
        # Cytoplasmic pH 7.2
        H_conc = ph_to_concentration(7.2)  # 6.31e-8 M = 63.1 nM
        
        # Use in rate function
        rate = k_acid * ph_to_concentration([pH_cytoplasm]) * [Substrate]
    """
    return 10.0 ** (-pH)


def concentration_to_ph(H_conc: float) -> float:
    """Convert H+ concentration to pH.
    
    Formula: pH = -log10([H+])
    
    Args:
        H_conc: H+ concentration in molar (M)
    
    Returns:
        pH value
    
    Example:
        # Calculate pH from proton marking
        pH = concentration_to_ph([H+_cytoplasm] * 1e-9)  # If in nM
    """
    if H_conc <= 0:
        return 14.0  # Maximum pH
    
    return -np.log10(H_conc)


def henderson_hasselbalch(pH: float, pKa: float) -> float:
    """Henderson-Hasselbalch equation for acid/base equilibrium.
    
    Calculates fraction in deprotonated form.
    
    Formula: α = 1 / (1 + 10^(pKa - pH))
    
    Args:
        pH: Solution pH
        pKa: Acid dissociation constant
    
    Returns:
        Fraction deprotonated (0 to 1)
    
    Example:
        # Drug ionization state (pKa = 7.4)
        # At pH 7.4: 50% ionized
        # At pH 6.4: 10% ionized (more protonated)
        # At pH 8.4: 90% ionized (more deprotonated)
        fraction_ionized = henderson_hasselbalch([pH_cytoplasm], pKa=7.4)
        
        # Ionized form has different permeability
        rate_passive = k_neutral * (1 - fraction_ionized) * [Drug_ext]
    """
    return 1.0 / (1.0 + 10.0 ** (pKa - pH))


def thermo_driving_force(delta_g: float, T: float = 310.15, celsius: bool = False) -> float:
    """Thermodynamic driving force from Gibbs free energy.
    
    Calculates the factor by which forward rate exceeds reverse rate
    at equilibrium.
    
    Formula: Γ = 1 - exp(ΔG / RT)
    
    When ΔG < 0 (exergonic): Γ > 0 (forward favored)
    When ΔG > 0 (endergonic): Γ < 0 (reverse favored)
    When ΔG = 0 (equilibrium): Γ = 0 (no net flux)
    
    Args:
        delta_g: Gibbs free energy change in kJ/mol
        T: Temperature (Kelvin by default, Celsius if celsius=True, default 310.15K)
        celsius: If True, treat T as Celsius (default False=Kelvin)
    
    Returns:
        Driving force factor (-∞ to 1)
    
    Example:
        # ATP hydrolysis: ΔG ≈ -50 kJ/mol (very favorable)
        # When [ATP]=5000 µM, [ADP]=1000 µM, [Pi]=1000 µM:
        # ΔG' = -30.5 + RT*ln([ADP][Pi]/[ATP])
        delta_g_actual = -30.5 + 8.314*310/1000 * log([ADP_pool]*[Pi_pool]/[ATP_pool])
        drive = thermo_driving_force(delta_g_actual, T=37, celsius=True)
        rate = k_base * drive * [Enzyme]
        
        # When ATP is high: ΔG very negative, drive ≈ 1.0
        # When ATP is low: ΔG less negative, drive approaches 0
    
    Note:
        R = 0.008314 kJ/(mol·K)
        At T=310K (37°C): RT ≈ 2.58 kJ/mol
        ΔG = -2.58 kJ/mol → 1.7× faster than reverse
        ΔG = -5.16 kJ/mol → 7.4× faster (one order magnitude)
    """
    R = 0.008314  # kJ/(mol·K)
    
    # Convert to Kelvin if needed
    if celsius:
        T = celsius_to_kelvin(T)
    
    # Prevent overflow for very negative ΔG
    exponent = delta_g / (R * T)
    if exponent > 100:  # exp(100) ≈ 2.7e43, practically infinite
        return 1.0
    
    return 1.0 - np.exp(exponent)


def atp_gibbs_free_energy(ATP: float, ADP: float, Pi: float, 
                          T: float = 310.15, pH: float = 7.0, celsius: bool = False) -> float:
    """Calculate actual Gibbs free energy of ATP hydrolysis.
    
    ATP + H2O → ADP + Pi
    
    Formula: ΔG = ΔG°' + RT*ln([ADP][Pi] / [ATP])
    
    Args:
        ATP: ATP concentration (µM)
        ADP: ADP concentration (µM)
        Pi: Inorganic phosphate concentration (µM)
        T: Temperature (Kelvin by default, Celsius if celsius=True, default 310.15K)
        pH: pH value (affects ΔG°')
        celsius: If True, treat T as Celsius (default False=Kelvin)
    
    Returns:
        ΔG in kJ/mol (negative = exergonic)
    
    Example:
        # Cellular conditions using Celsius
        delta_g = atp_gibbs_free_energy(
            ATP=[ATP_pool], ADP=[ADP_pool], Pi=[Pi_pool],
            T=37, pH=7.2, celsius=True
        )  # Typically -50 to -55 kJ/mol
        
        # Use in P-gp efflux (consumes 4 ATP per drug)
        delta_g_total = 4 * delta_g
        drive = thermo_driving_force(delta_g_total, T=37, celsius=True)
        rate = k_efflux * drive * [ATP_pool]**4 / (Km**4 + [ATP_pool]**4)
    
    Note:
        ΔG°' ≈ -30.5 kJ/mol at pH 7.0, 25°C
        Under cellular conditions: ΔG ≈ -50 to -55 kJ/mol
        When ATP/ADP ratio drops (hypoxia): ΔG less negative
    """
    R = 0.008314  # kJ/(mol·K)
    
    # Convert to Kelvin if needed
    if celsius:
        T = celsius_to_kelvin(T)
    
    # Standard free energy (pH and temperature corrected)
    # ΔG°' ≈ -30.5 kJ/mol at pH 7.0, 298K
    delta_g_standard = -30.5
    
    # pH correction (roughly -5.7 kJ/mol per pH unit)
    delta_g_standard += -5.7 * (pH - 7.0)
    
    # Prevent log of zero or negative concentrations
    if ATP <= 0 or ADP <= 0 or Pi <= 0:
        return delta_g_standard
    
    # Concentration correction (convert µM to M for proper thermodynamics)
    ATP_M = ATP * 1e-6
    ADP_M = ADP * 1e-6
    Pi_M = Pi * 1e-6
    
    Q = (ADP_M * Pi_M) / ATP_M  # Reaction quotient
    
    delta_g = delta_g_standard + R * T * np.log(Q)
    
    return delta_g


def electro_driving_force(V_m: float, z: float, E_ion: float) -> float:
    """Electrochemical driving force for ion transport.
    
    Calculates the driving force as departure from equilibrium.
    
    Formula: Driving force = V_m - E_ion
    
    Args:
        V_m: Membrane potential (mV)
        z: Ion charge
        E_ion: Nernst potential for the ion (mV)
    
    Returns:
        Driving force in mV
    
    Example:
        # Na+ influx driven by both concentration and voltage
        E_Na = nernst_potential(1, 145, 12)  # +67 mV
        drive = electro_driving_force([Membrane_potential], 1, E_Na)
        # At V_m=-70 mV: drive = -70 - 67 = -137 mV (large inward drive)
        
        rate_Na_influx = g_Na * abs(drive) * [Na_channel_open]
    """
    return V_m - E_ion


# =============================================================================
# CATALOG DICTIONARY (for easy access)
# =============================================================================

FUNCTION_CATALOG: Dict[str, Callable[..., Any]] = {
    # Basic math functions (from Python math module)
    'exp': math.exp,
    'log': math.log,
    'log10': math.log10,
    'sqrt': math.sqrt,
    'pow': math.pow,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'floor': math.floor,
    'ceil': math.ceil,
    'abs': abs,
    'min': min,
    'max': max,
    
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
    
    # Biophysical / Thermodynamic functions
    'celsius_to_kelvin': celsius_to_kelvin,
    'kelvin_to_celsius': kelvin_to_celsius,
    'arrhenius': arrhenius,
    'nernst_potential': nernst_potential,
    'goldman_equation': goldman_equation,
    'ph_to_concentration': ph_to_concentration,
    'concentration_to_ph': concentration_to_ph,
    'henderson_hasselbalch': henderson_hasselbalch,
    'thermo_driving_force': thermo_driving_force,
    'atp_gibbs_free_energy': atp_gibbs_free_energy,
    'electro_driving_force': electro_driving_force,
}


def get_catalog() -> Dict[str, Callable[..., Any]]:
    """Get the complete function catalog.
    
    Returns:
        Dictionary mapping function names to callable functions
    """
    return dict(FUNCTION_CATALOG)


def get_function(name: str) -> Optional[Callable[..., Any]]:
    """Get a specific function from the catalog.
    
    Args:
        name: Function name
    
    Returns:
        Function callable, or None if not found
    """
    return cast(Optional[Callable[..., Any]], FUNCTION_CATALOG.get(name))


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
