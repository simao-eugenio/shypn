"""Numba JIT kernel for the τ-leaping inner step.

Provides a compiled implementation of the two most compute-intensive Python
portions of ``TauLeapingEngine.execute_step()``:

1. **Cao et al. (2006) τ selection** — iterates over all (place × transition)
   pairs to compute the drift (μ) and variance (σ²) terms, then takes the
   minimum bound across places.

2. **Poisson / Skellam firing sampling** — samples ``k_j ~ Poisson(a_j·τ)``
   for each irreversible transition and
   ``k_j ~ Poisson(a_fwd·τ) - Poisson(a_rev·τ)`` for reversible ones.

The compiled function replaces:
- Python dict comprehension to build ``accel_props`` (≈ 29 entries per step)
- ``LeapSelector.select_tau()`` Python overhead + numpy op dispatch
- ``_sample_firings()`` loop to build rate lists + individual Poisson calls

**Availability:** Import succeeds if ``numba >= 0.59`` is installed, otherwise
``NUMBA_AVAILABLE`` is ``False`` and both exported symbols are ``None``.
``TauLeapingEngine`` checks ``NUMBA_AVAILABLE`` before using the kernel, so the
package works correctly without Numba.

Usage::

    from shypn.engine.simulation.tau_leaping.jit_kernel import (
        NUMBA_AVAILABLE, tau_step_kernel, seed_kernel,
    )

    if NUMBA_AVAILABLE:
        tau, k_arr = tau_step_kernel(
            a_net, a_fwd, a_rev, g_vec, y_snap,
            S, S_sq,
            critical_threshold, epsilon, max_tau, min_tau,
        )
"""

from __future__ import annotations

import logging

__all__ = ["NUMBA_AVAILABLE", "tau_step_kernel", "seed_kernel"]

_log = logging.getLogger(__name__)

NUMBA_AVAILABLE: bool = False
tau_step_kernel = None   # type: ignore[assignment]
seed_kernel = None       # type: ignore[assignment]

try:
    import numba as nb
    import numpy as np

    @nb.njit(cache=True)
    def _tau_and_sample(  # type: ignore[misc]
        a_net,              # float64[n_trans] — net propensities from C accel
        a_fwd,              # float64[n_trans] — forward propensities
        a_rev,              # float64[n_trans] — reverse propensities (>0 = reversible)
        g_vec,              # float64[n_places] — Cao highest-order factor per place
        y_snap,             # float64[n_places] — place populations (read-only snapshot)
        S,                  # float64[n_places, n_trans] — stoichiometry matrix
        S_sq,               # float64[n_places, n_trans] — S element-wise squared
        critical_threshold, # float — propensity below this → critical (skip)
        epsilon,            # float — Cao ε parameter
        max_tau,            # float — upper bound on τ
        min_tau,            # float — lower bound on τ (numerical floor)
    ):
        """JIT-compiled τ selection + Poisson/Skellam sampling.

        Returns
        -------
        tau : float
            Selected leap size.  ``0.0`` means all transitions are critical;
            caller should fall back to exact SSA.
        k_arr : int64[n_trans]
            Sampled firing counts aligned with the stoichiometry matrix columns.
        """
        n_trans = S.shape[1]

        # ── 1. Build non-critical propensity vector ────────────────────────────
        a_nc = np.empty(n_trans, dtype=np.float64)
        any_nc = False
        for j in range(n_trans):
            if a_net[j] >= critical_threshold:
                a_nc[j] = a_net[j]
                any_nc = True
            else:
                a_nc[j] = 0.0

        if not any_nc:
            # All critical — signal SSA fallback via tau = 0
            return 0.0, np.zeros(n_trans, dtype=np.int64)

        # ── 2. Cao et al. (2006) τ selection ──────────────────────────────────
        # For each place i, bound τ by ε_i / |μ_i| and ε_i² / σ²_i.
        n_places = S.shape[0]
        tau = max_tau

        for i in range(n_places):
            mu_i = 0.0
            var_i = 0.0
            for j in range(n_trans):
                anc_j = a_nc[j]
                mu_i  += S[i, j]    * anc_j
                var_i += S_sq[i, j] * anc_j

            if mu_i == 0.0 and var_i == 0.0:
                continue  # place not affected by any non-critical transition

            # Effective relative tolerance: ε_i = max(ε·x_i / g_i, 1)
            eps_i = epsilon * y_snap[i] / g_vec[i]
            if eps_i < 1.0:
                eps_i = 1.0

            abs_mu = abs(mu_i)
            if abs_mu > 0.0:
                cand = eps_i / abs_mu
                if cand < tau:
                    tau = cand

            if var_i > 0.0:
                cand = eps_i * eps_i / var_i
                if cand < tau:
                    tau = cand

        # Apply floor (prevents tiny τ from stalling)
        if tau < min_tau:
            tau = min_tau

        # ── 3. Sample firings for each transition ──────────────────────────────
        k_arr = np.zeros(n_trans, dtype=np.int64)

        for j in range(n_trans):
            lam = a_net[j] * tau
            if lam <= 0.0:
                continue

            if a_rev[j] > 0.0:
                # Reversible: Skellam = Poisson(fwd·τ) − Poisson(rev·τ)
                lam_f = a_fwd[j] * tau
                if lam_f < 0.0:
                    lam_f = 0.0
                lam_r = a_rev[j] * tau
                if lam_r < 0.0:
                    lam_r = 0.0
                k_arr[j] = (
                    np.random.poisson(lam_f) - np.random.poisson(lam_r)
                )
            else:
                k_arr[j] = np.random.poisson(lam)

        return tau, k_arr

    @nb.njit(cache=True)
    def _seed(seed: int) -> None:  # type: ignore[misc]
        """Seed the Numba/NumPy RNG used inside JIT functions."""
        np.random.seed(seed)

    tau_step_kernel = _tau_and_sample
    seed_kernel = _seed
    NUMBA_AVAILABLE = True
    _log.debug("Phase 6: Numba JIT τ-step kernel loaded (numba %s)", nb.__version__)

except ImportError:
    _log.debug(
        "Phase 6: numba not installed — JIT kernel unavailable. "
        "Set use_jit_kernel=True only after installing numba>=0.59."
    )
except Exception as _exc:  # noqa: BLE001
    _log.warning("Phase 6: JIT kernel compilation failed (%s); falling back to Python path.", _exc)
