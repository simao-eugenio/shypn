"""ODE Acceleration Package — gcc C codegen + ctypes + scipy.solve_ivp.

Strategy
--------
For models that contain continuous transitions, the default per-transition
Python step loop (``_execute_continuous_transitions``) is replaced by a
**single** ``scipy.integrate.solve_ivp`` call per continuous interval.

The ODE right-hand-side (RHS) function is generated as C source, compiled
to a shared library with gcc at model-load time, and called via ctypes.
This eliminates the ``eval()`` / dict-building overhead inside
``ContinuousBehavior._compile_rate_function`` while keeping the clean
Python API intact.

Typical speedup: 10–50× per ODE interval for models with rich kinetics
(Arrhenius, Michaelis–Menten, Hill equations).

Public API
----------
``OdeSystemAccelerator`` — the main entry point; instantiate once per model.

Usage::

    accel = OdeSystemAccelerator(model, behavior_factory_fn)
    accel.build()                           # code-gen + compile (once)

    # Replace _execute_continuous_transitions with:
    accel.integrate(t_start, t_end)         # updates model place tokens in place
"""

from .ode_system import OdeSystemAccelerator
from .propensity_system import PropensityAccelerator

__all__ = ["OdeSystemAccelerator", "PropensityAccelerator"]
