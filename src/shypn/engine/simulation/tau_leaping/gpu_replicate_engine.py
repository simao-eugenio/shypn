"""GPU-parallel replicate engine using CuPy.

Runs *N* independent τ-leaping replicates simultaneously on the GPU.
Each CUDA thread-block processes one replicate; the time-stepping
loop is driven from the host so that per-step GPU kernel launches
cover all replicates at once.

Architecture::

    Host (Python/CuPy)          Device (CUDA)
    ──────────────────          ──────────────
    for step in range(max_steps):
        propensities(…)   ──►  mass-action kernel [N × M]
        tau_select(…)     ──►  Cao τ-selection   [N]
        sample(…)         ──►  cupy.random.poisson [N × M]
        update(…)         ──►  y += S @ k         [N × P]
        snapshot(…)       ──►  conditional copy   [N × P]

Supported models
~~~~~~~~~~~~~~~~
Phase 2 supports **mass-action kinetics** (``a_j = k_j · ∏ y_i^v_ij``).
Non-mass-action transitions cause a graceful fallback to the CPU path
in :class:`ReplicateRunner`.

Requirements
~~~~~~~~~~~~
``cupy-cuda12x`` (or matching CUDA variant).  Import errors are caught
at the class level so the module can always be imported.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from shypn.engine.acceleration.gpu.base import GPUBackend
from .gpu_model_analysis import GPUModelAnalysis

logger = logging.getLogger(__name__)

# CuPy is optional — guard all device code behind this flag.
try:
    import cupy as cp

    _CUPY_AVAILABLE = True
except ImportError:
    cp = None  # type: ignore[assignment]
    _CUPY_AVAILABLE = False


class GPUReplicateEngine:
    """Run N τ-leaping replicates in parallel on a CUDA GPU.

    Parameters
    ----------
    analysis:
        Pre-computed :class:`GPUModelAnalysis` (host arrays).
    backend:
        An initialised :class:`GPUBackend` (must be CuPy for Phase 2).
    epsilon, max_tau, min_tau, n_critical:
        Cao et al. (2006) τ-leaping parameters (same semantics as
        :class:`TauLeapingEngine`).
    """

    def __init__(
        self,
        analysis: GPUModelAnalysis,
        backend: GPUBackend,
        *,
        epsilon: float = 0.03,
        max_tau: float = 0.1,
        min_tau: float = 1e-6,
        n_critical: int = 10,
    ) -> None:
        if not _CUPY_AVAILABLE:
            raise RuntimeError("CuPy is required for GPUReplicateEngine")
        if backend.name != "cupy":
            raise TypeError(
                f"GPUReplicateEngine requires CuPyBackend, got {backend.name}"
            )

        self._analysis = analysis
        self._backend = backend
        self._epsilon = epsilon
        self._max_tau = max_tau
        self._min_tau = min_tau
        self._n_critical = n_critical

        # Upload constant model data to device (done once)
        self._d_S = cp.asarray(analysis.S)                    # [P, M]
        self._d_S_sq = cp.asarray(analysis.S_sq)              # [P, M]
        self._d_S_neg = cp.asarray(analysis.S_neg)            # [P, M]
        self._d_g_vec = cp.asarray(analysis.g_vec)            # [P]
        self._d_input_stoich = cp.asarray(analysis.input_stoich)  # [M, P]
        self._d_rate_fwd = cp.asarray(analysis.rate_constants)    # [M]
        self._d_rate_rev = cp.asarray(analysis.rate_rev)          # [M]
        self._d_is_rev = cp.asarray(analysis.is_reversible)       # [M] bool

        self._P = analysis.n_places
        self._M = analysis.n_transitions

        logger.info(
            "GPUReplicateEngine: uploaded model (%d places, %d transitions) "
            "to device %s",
            self._P, self._M, backend.device_info.device_name,
        )

    # ── public API ───────────────────────────────────────────────────

    def run_batch(
        self,
        n_replicates: int,
        duration: float,
        dt: float,
        seed_base: int = 42,
        *,
        snapshot_interval: int = 1,
        verbose: bool = False,
        progress_callback: Optional[Any] = None,
        propensity_fn: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Run *n_replicates* τ-leaping simulations in parallel on the GPU.

        Parameters
        ----------
        n_replicates:
            Number of independent replicates (N).
        duration:
            Maximum simulation time.
        dt:
            Recording time-step (governs ``max_steps``).
        seed_base:
            Replicate *i* uses ``seed_base + i``.
        snapshot_interval:
            Record state every this many τ-steps (1 = every step).
        verbose:
            Print progress to stdout.
        progress_callback:
            ``(fraction: float) → None`` called periodically.
        propensity_fn:
            Optional CPU callback for hybrid mode.  Signature::

                (y: ndarray[N, P], t: ndarray[N])
                    → (a_fwd: ndarray[N, M], a_rev: ndarray[N, M])

            When provided, propensities are evaluated on CPU and uploaded
            to the GPU each step.  This enables models with arbitrary
            (non-mass-action) rate expressions to use the GPU for the
            expensive τ-selection, Poisson sampling, and state-update
            phases.  When ``None``, the engine uses the built-in GPU
            mass-action propensity kernel (faster for pure mass-action
            models).

        Returns
        -------
        list[dict]
            One dict per replicate, compatible with
            ``ReplicateRunner.run_replicates()`` output format.
        """
        N = n_replicates
        P = self._P
        M = self._M
        max_steps = int(duration / dt)

        _hybrid = propensity_fn is not None
        if verbose:
            _mode_tag = "hybrid CPU+GPU" if _hybrid else "GPU mass-action"
            print(f"  GPU batch ({_mode_tag}): {N} replicates × {max_steps} "
                  f"steps ({P} places, {M} transitions)")

        t0_wall = time.time()

        # ── Allocate device state ────────────────────────────────────
        # y_all[N, P] — current token state for each replicate
        d_y = cp.tile(cp.asarray(self._analysis.y0), (N, 1))  # [N, P]
        # t_all[N] — current simulation time per replicate
        d_t = cp.zeros(N, dtype=cp.float64)
        # active[N] — True while replicate is still running
        d_active = cp.ones(N, dtype=cp.bool_)

        # ── Host-side result buffers ─────────────────────────────────
        # Pre-allocate trajectory storage (host, float32 to save memory)
        record_capacity = max_steps // snapshot_interval + 2
        h_time_points = np.zeros((N, record_capacity), dtype=np.float64)
        h_trajectories = np.zeros(
            (N, record_capacity, P), dtype=np.float32,
        )
        record_idx = np.zeros(N, dtype=np.int64)  # next write position

        # Record initial state (t=0)
        y0_host = self._analysis.y0.astype(np.float32)
        for r in range(N):
            h_trajectories[r, 0, :] = y0_host
        record_idx[:] = 1

        # ── Per-replicate RNG seed ───────────────────────────────────
        # CuPy uses a single device RNG — we re-seed per batch, not per
        # replicate.  Independence comes from the same Poisson λ matrix
        # sampled with different draw indices (cuRAND counter-based).
        cp.random.seed(seed_base)

        # ── Stopped reason tracking (host) ───────────────────────────
        stopped_reasons = ["duration"] * N

        # ── Step loop (host-driven, GPU-parallel per step) ───────────
        step = 0
        for step in range(max_steps):
            if not cp.any(d_active):
                break

            # 1. Propensities — hybrid (CPU callback) or GPU mass-action
            if _hybrid:
                # Download state to host, evaluate on CPU, upload result
                h_y_now = d_y.get()  # [N, P] → numpy
                h_t_now = d_t.get()  # [N]   → numpy
                h_a_fwd, h_a_rev = propensity_fn(h_y_now, h_t_now)
                d_a_fwd = cp.asarray(h_a_fwd)  # [N, M]
                d_a_rev = cp.asarray(h_a_rev)  # [N, M]
            else:
                # GPU mass-action: a_j = k_j · ∏ y_i^v_ij  (log-space)
                d_y_safe = cp.maximum(d_y, 1e-30)
                d_log_y = cp.log(d_y_safe)  # [N, P]
                d_log_a = d_log_y @ self._d_input_stoich.T  # [N, M]
                d_log_k = cp.log(cp.maximum(self._d_rate_fwd, 1e-30))
                d_a_fwd = cp.exp(d_log_a + d_log_k[cp.newaxis, :])  # [N, M]

                d_a_rev = cp.zeros_like(d_a_fwd)
                if cp.any(self._d_is_rev):
                    d_log_kr = cp.log(cp.maximum(self._d_rate_rev, 1e-30))
                    d_S_pos = cp.maximum(self._d_S, 0.0).T  # [M, P]
                    d_log_a_rev = d_log_y @ d_S_pos.T  # [N, M]
                    d_a_rev_all = cp.exp(d_log_a_rev + d_log_kr[cp.newaxis, :])
                    d_a_rev = cp.where(self._d_is_rev[cp.newaxis, :],
                                       d_a_rev_all, 0.0)

            d_a_net = d_a_fwd - d_a_rev  # [N, M]

            # 2. Cao τ-selection (vectorised across replicates)
            d_tau = self._select_tau_batch(d_y, d_a_net, d_a_fwd)  # [N]

            # Clamp to remaining time
            d_remaining = duration - d_t
            d_tau = cp.minimum(d_tau, d_remaining)
            d_tau = cp.maximum(d_tau, self._min_tau)
            # Zero out tau for finished replicates
            d_tau = cp.where(d_active, d_tau, 0.0)

            # 3. Poisson/Skellam sampling
            d_lam_fwd = d_a_fwd * d_tau[:, cp.newaxis]  # [N, M]
            d_lam_fwd = cp.maximum(d_lam_fwd, 0.0)
            d_k = cp.zeros((N, M), dtype=cp.int64)

            # Irreversible: k ~ Poisson(a_fwd · τ)
            irrev_mask = ~self._d_is_rev  # [M]
            if cp.any(irrev_mask):
                lam_irrev = d_lam_fwd[:, irrev_mask.get()]
                lam_irrev_safe = cp.clip(lam_irrev, 0.0, 1e8)
                k_irrev = cp.random.poisson(lam_irrev_safe)
                d_k[:, irrev_mask.get()] = k_irrev.astype(cp.int64)

            # Reversible: k ~ Poisson(a_fwd·τ) - Poisson(a_rev·τ)
            if cp.any(self._d_is_rev):
                rev_idx = self._d_is_rev.get()
                lam_f = cp.clip(d_lam_fwd[:, rev_idx], 0.0, 1e8)
                lam_r = cp.clip(
                    d_a_rev[:, rev_idx] * d_tau[:, cp.newaxis], 0.0, 1e8
                )
                k_fwd = cp.random.poisson(lam_f)
                k_rev_samp = cp.random.poisson(lam_r)
                d_k[:, rev_idx] = (k_fwd - k_rev_samp).astype(cp.int64)

            # 4. State update: y += k @ S^T  (k[N,M] @ S^T[M,P] → [N,P])
            d_k_f = d_k.astype(cp.float64)
            d_delta = d_k_f @ self._d_S.T  # [N, P]
            d_y += d_delta
            cp.clip(d_y, 0.0, None, out=d_y)

            # 5. Advance time
            d_t += d_tau

            # 6. Detect deadlock: all propensities ≤ 0 for a replicate
            d_total_a = cp.sum(cp.maximum(d_a_net, 0.0), axis=1)  # [N]
            newly_dead = d_active & (d_total_a <= 0.0)
            if cp.any(newly_dead):
                dead_idx = cp.where(newly_dead)[0].get()
                for r in dead_idx:
                    stopped_reasons[int(r)] = "deadlock"
            d_active &= (d_total_a > 0.0)

            # 7. Detect time exhaustion
            newly_done = d_active & (d_t >= duration - 1e-12)
            d_active &= ~newly_done

            # 8. Snapshot (download to host every snapshot_interval steps)
            if step % snapshot_interval == 0:
                h_t = d_t.get()       # [N]
                h_y = d_y.get().astype(np.float32)  # [N, P]
                for r in range(N):
                    ri = record_idx[r]
                    if ri < record_capacity:
                        h_time_points[r, ri] = h_t[r]
                        h_trajectories[r, ri, :] = h_y[r, :]
                        record_idx[r] = ri + 1

            # Progress
            if progress_callback and step % 100 == 0:
                progress_callback(step / max_steps)

        # ── Final snapshot ───────────────────────────────────────────
        cp.cuda.Device().synchronize()
        h_t = d_t.get()
        h_y = d_y.get().astype(np.float32)
        for r in range(N):
            ri = record_idx[r]
            if ri < record_capacity:
                h_time_points[r, ri] = h_t[r]
                h_trajectories[r, ri, :] = h_y[r, :]
                record_idx[r] = ri + 1

        elapsed = time.time() - t0_wall
        if verbose:
            print(f"  GPU batch done in {elapsed:.1f}s "
                  f"({step + 1} steps, {N} replicates)")

        # ── Convert to ReplicateRunner result format ─────────────────
        results: List[Dict[str, Any]] = []
        for r in range(N):
            n_rec = int(record_idx[r])
            tp = h_time_points[r, :n_rec].tolist()
            traj = h_trajectories[r, :n_rec, :]  # [n_rec, P]

            place_data: Dict[str, List[float]] = {}
            for i, pid in enumerate(self._analysis.place_ids):
                place_data[pid] = traj[:, i].tolist()

            final_marking: Dict[str, float] = {}
            for i, pid in enumerate(self._analysis.place_ids):
                final_marking[pid] = float(h_y[r, i])

            results.append({
                "replicate_id": r,
                "seed": seed_base + r,
                "time_points": tp,
                "place_data": place_data,
                "transition_data": {},  # not tracked per-step on GPU
                "transition_rates": {},
                "final_marking": final_marking,
                "total_firings": {},   # aggregate not tracked on GPU
                "stopped_reason": stopped_reasons[r],
                "elapsed_time": elapsed / N,  # amortised
            })

        return results

    # ── internal: batched Cao τ-selection ────────────────────────────

    def _select_tau_batch(
        self,
        d_y: Any,        # [N, P]
        d_a_net: Any,    # [N, M]
        d_a_fwd: Any,    # [N, M]
    ) -> Any:  # returns [N]
        """Vectorised Cao et al. (2006) τ-selection across all replicates.

        For each replicate *r* and place *i*:
            μ_i = Σ_j S[i,j] · a_nc[r,j]
            σ²_i = Σ_j S²[i,j] · a_nc[r,j]
            ε_i = max(ε · y[r,i] / g[i], 1)
            τ_candidate = min(ε_i/|μ_i|, ε_i²/σ²_i)

        τ[r] = min over all places i.

        The critical-reaction classification (Cao N_c) is applied
        per-transition first, zeroing out propensities of critical
        reactions.
        """
        N = d_y.shape[0]
        P = self._P
        M = self._M
        eps = self._epsilon
        n_c = self._n_critical

        # ── Critical reaction classification ─────────────────────────
        # L_j = min_i floor(y_i / |S_neg[i,j]|) for consuming arcs
        # Non-critical if L_j >= n_critical
        # d_S_neg: [P, M], d_y: [N, P]
        # For each (r, j): L_j(r) = min_i(y[r,i] / S_neg[i,j]) over i where S_neg[i,j] > 0
        d_S_neg_t = self._d_S_neg.T  # [M, P]
        # Mask: where S_neg > 0 (consuming)
        consuming = (d_S_neg_t > 0)  # [M, P]

        # Compute y / S_neg for all (r, i, j) — use broadcasting
        # d_y[:, cp.newaxis, :] → [N, 1, P]
        # d_S_neg_t[cp.newaxis, :, :] → [1, M, P]
        # Result → [N, M, P]
        # This could be memory-intensive for large models; ok for P,M < 100
        d_y_exp = d_y[:, cp.newaxis, :]           # [N, 1, P]
        d_sneg_exp = d_S_neg_t[cp.newaxis, :, :]  # [1, M, P]
        d_sneg_safe = cp.where(consuming, d_sneg_exp, 1.0)  # avoid /0
        d_firings_possible = cp.floor(d_y_exp / d_sneg_safe)  # [N, M, P]
        # Set non-consuming entries to a large number
        d_firings_possible = cp.where(
            consuming[cp.newaxis, :, :],
            d_firings_possible,
            float(n_c),  # large → non-limiting
        )
        d_Lj = cp.min(d_firings_possible, axis=2)  # [N, M]
        d_non_critical = (d_Lj >= n_c)  # [N, M] bool

        # a_nc: zero out critical transitions
        d_a_nc = cp.where(d_non_critical, d_a_net, 0.0)  # [N, M]

        # ── Drift and variance per place ─────────────────────────────
        # μ_i = Σ_j S[i,j] · a_nc[r,j]  → d_a_nc[N, M] @ S^T → wrong shape
        # S: [P, M], a_nc: [N, M]
        # mu: [N, P] = a_nc @ S^T  ... S^T is [M, P] → a_nc[N,M] @ S.T[M,P] = [N,P]
        d_mu = d_a_nc @ self._d_S.T     # [N, P]
        d_var = d_a_nc @ self._d_S_sq.T  # [N, P]

        # ── ε bounds ─────────────────────────────────────────────────
        d_eps_i = cp.maximum(eps * d_y / self._d_g_vec[cp.newaxis, :], 1.0)

        # τ from drift: ε_i / |μ_i|
        d_abs_mu = cp.abs(d_mu)
        d_tau_mu = cp.where(d_abs_mu > 0, d_eps_i / d_abs_mu, self._max_tau)

        # τ from variance: ε_i² / σ²_i
        d_tau_var = cp.where(d_var > 0, d_eps_i ** 2 / d_var, self._max_tau)

        # Per-place minimum
        d_tau_per_place = cp.minimum(d_tau_mu, d_tau_var)  # [N, P]

        # Global minimum across places
        d_tau = cp.min(d_tau_per_place, axis=1)  # [N]

        # Clamp
        d_tau = cp.clip(d_tau, self._min_tau, self._max_tau)

        return d_tau
