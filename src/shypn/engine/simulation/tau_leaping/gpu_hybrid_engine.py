"""GPU-parallel hybrid ODE + τ-leaping engine.

Runs *N* independent replicates simultaneously on the GPU for models
that contain **both** continuous (ODE) and stochastic transitions.

Architecture::

    Host (Python)                  Device (CuPy/CUDA)
    ─────────────                  ──────────────────
    for step in range(max_steps):
        ode_rhs_batch(y)      →    evaluate dy/dt for [N] replicates (CPU→GPU)
        rk4_update(y, dydt)   →    RK4 state update            [N × P_ode]
        propensities(y)       →    mass-action or CPU callback  [N × M]
        tau_select(…)         →    Cao τ-selection              [N]
        sample(…)             →    cupy.random.poisson          [N × M]
        update(…)             →    y += S @ k                   [N × P]
        snapshot(…)           →    conditional copy             [N × P]

The ODE RHS is evaluated using the pre-compiled C function from
:class:`OdeSystemAccelerator` (called N times vectorized on CPU),
then the RK4 update is performed on GPU.  The stochastic part reuses
the same τ-leaping machinery as :class:`GPUReplicateEngine`.

This engine handles the CBD v2 model profile:
    37 continuous + 7 stochastic + 1 adaptive = 45 transitions

Requirements
~~~~~~~~~~~~
``cupy-cuda12x`` and a compiled ODE system (via OdeSystemAccelerator).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from shypn.engine.acceleration.gpu.base import GPUBackend

logger = logging.getLogger(__name__)

try:
    import cupy as cp
    _CUPY_AVAILABLE = True
except ImportError:
    cp = None  # type: ignore[assignment]
    _CUPY_AVAILABLE = False


class GPUHybridEngine:
    """Run N hybrid ODE+stochastic replicates in parallel using GPU.

    The engine splits the model into:
    - **Continuous part**: ODE integration (RK4) for continuous transitions,
      evaluated on CPU (compiled C) and updated on GPU.
    - **Stochastic part**: τ-leaping for stochastic transitions, entirely
      on GPU (propensity → τ-select → Poisson → state update).

    Both parts share the same state vector y[N, P] on device.  Each
    time-step first advances the ODE, then fires stochastic transitions.

    Parameters
    ----------
    ode_rhs_fn:
        Callable ``(y: ndarray[P_ode], t: float) → ndarray[P_ode]``
        — the compiled ODE RHS function (from OdeSystemAccelerator.make_rhs()).
    ode_place_indices:
        Mapping from ODE place index (in the ODE state vector) to the
        global place index (in the full y[P] vector).
    stoch_analysis:
        GPUModelAnalysis for the stochastic transitions only.
    n_places:
        Total number of places.
    place_ids:
        Ordered list of all place IDs.
    y0:
        Initial marking [P].
    backend:
        CuPy GPU backend.
    extra_place_indices:
        Mapping from extra-place index to global place index (for signal
        places referenced in ODE rates but not in ODE state).
    epsilon, max_tau, min_tau:
        τ-leaping parameters.
    """

    def __init__(
        self,
        ode_rhs_fn: Callable,
        ode_place_indices: List[int],
        stoch_S: NDArray[np.float64],
        stoch_rate_constants: NDArray[np.float64],
        stoch_input_stoich: NDArray[np.float64],
        stoch_is_reversible: NDArray[np.bool_],
        stoch_rate_rev: NDArray[np.float64],
        n_places: int,
        place_ids: List[str],
        y0: NDArray[np.float64],
        backend: GPUBackend,
        extra_place_indices: Optional[List[int]] = None,
        *,
        epsilon: float = 0.03,
        max_tau: float = 0.1,
        min_tau: float = 1e-6,
        stoch_propensity_fn: Optional[Callable] = None,
        events: Optional[List[Any]] = None,
        place_name_to_index: Optional[Dict[str, int]] = None,
        stoch_transition_ids: Optional[List[str]] = None,
        inhibitor_constraints: Optional[List] = None,
    ) -> None:
        if not _CUPY_AVAILABLE:
            raise RuntimeError("CuPy is required for GPUHybridEngine")

        self._ode_rhs_fn = ode_rhs_fn
        self._ode_indices = np.array(ode_place_indices, dtype=np.int64)
        self._extra_indices = np.array(extra_place_indices or [], dtype=np.int64)
        self._P = n_places
        self._P_ode = len(ode_place_indices)
        self._place_ids = place_ids
        self._y0 = y0.copy()
        self._backend = backend
        self._epsilon = epsilon
        self._max_tau = max_tau
        self._min_tau = min_tau

        # Stochastic transition matrices (upload to GPU)
        self._M_stoch = stoch_S.shape[1]
        self._d_S_stoch = cp.asarray(stoch_S)  # [P, M_stoch]
        self._d_S_stoch_sq = cp.asarray(stoch_S ** 2)
        self._d_S_stoch_neg = cp.asarray(np.abs(np.minimum(stoch_S, 0)))
        self._d_input_stoich = cp.asarray(stoch_input_stoich)  # [M_stoch, P]
        self._d_rate_fwd = cp.asarray(stoch_rate_constants)  # [M_stoch]
        self._d_rate_rev = cp.asarray(stoch_rate_rev)  # [M_stoch]
        self._d_is_rev = cp.asarray(stoch_is_reversible)  # [M_stoch]

        # Optional CPU propensity callback for symbolic (non-mass-action) rates.
        # Signature: (y: ndarray[N, P], t: ndarray[N]) → (a_fwd[N, M], a_rev[N, M])
        self._stoch_propensity_fn = stoch_propensity_fn

        # Stochastic transition IDs in column-order of S_stoch (for total_firings)
        self._stoch_transition_ids: List[str] = list(stoch_transition_ids or [])

        # Inhibitor arc predicates: list of (place_global_idx, threshold, trans_col_idx).
        # Enforces the formalism rule M(p) >= threshold → transition disabled,
        # matching the CPU τ-leap path.  Stored as separate 1-D arrays for
        # efficient GPU broadcast masking.
        if inhibitor_constraints:
            _inh = np.array(inhibitor_constraints, dtype=np.float64)  # [K, 3]
            self._inh_place_idx  = cp.asarray(_inh[:, 0].astype(np.int64))  # [K]
            self._inh_thresholds = cp.asarray(_inh[:, 1])                   # [K]
            self._inh_trans_idx  = cp.asarray(_inh[:, 2].astype(np.int64))  # [K]
        else:
            self._inh_place_idx  = None
            self._inh_thresholds = None
            self._inh_trans_idx  = None

        # g_vec for tau-selection (max stoich order per place)
        g_vec = np.ones(n_places, dtype=np.float64)
        if self._M_stoch > 0:
            for i in range(n_places):
                col_max = np.max(np.abs(stoch_S[i, :]))
                if col_max > 1:
                    g_vec[i] = col_max
        self._d_g_vec = cp.asarray(g_vec)

        logger.info(
            "GPUHybridEngine: %d ODE places, %d stochastic transitions, "
            "%d total places → device %s",
            self._P_ode, self._M_stoch, self._P,
            backend.device_info.device_name,
        )

        # ---- Environment events (parity with controller._evaluate_environment_events) ----
        # `events` is a list of Event-like objects (id, trigger, delay,
        # assignments dict {place_name_or_id: expr_str}). Triggers are
        # Python expressions over `t` and place names/ids.
        self._events_raw: List[Any] = list(events or [])
        self._place_name_to_index: Dict[str, int] = dict(place_name_to_index or {})
        # Also map place IDs (the engine's canonical key)
        self._place_id_to_index: Dict[str, int] = {
            pid: i for i, pid in enumerate(place_ids)
        }
        # Pre-compile each event's trigger + assignments. Compilation
        # failures are logged and the offending event is dropped.
        self._events_compiled: List[Dict[str, Any]] = []
        for ev in self._events_raw:
            trig = (getattr(ev, 'trigger', '') or '').strip()
            if not trig:
                continue
            try:
                trig_code = compile(trig, f"<event {getattr(ev, 'id', '?')} trigger>", 'eval')
            except Exception as exc:
                logger.warning(
                    "GPUHybridEngine: skipping event %r — trigger compile failed: %s",
                    getattr(ev, 'id', '?'), exc,
                )
                continue
            assignments = dict(getattr(ev, 'assignments', {}) or {})
            assign_compiled: Dict[int, Any] = {}
            for tgt_name, expr in assignments.items():
                # Resolve target → global place index
                gi = self._place_name_to_index.get(tgt_name)
                if gi is None:
                    gi = self._place_id_to_index.get(tgt_name)
                if gi is None:
                    logger.warning(
                        "GPUHybridEngine: event %r assignment target %r not found in places",
                        getattr(ev, 'id', '?'), tgt_name,
                    )
                    continue
                try:
                    expr_code = compile(str(expr), f"<event {getattr(ev, 'id', '?')} assign {tgt_name}>", 'eval')
                except Exception as exc:
                    logger.warning(
                        "GPUHybridEngine: event %r assignment %r compile failed: %s",
                        getattr(ev, 'id', '?'), tgt_name, exc,
                    )
                    continue
                assign_compiled[gi] = expr_code
            if not assign_compiled:
                logger.warning(
                    "GPUHybridEngine: event %r has no usable assignments — skipped",
                    getattr(ev, 'id', '?'),
                )
                continue
            self._events_compiled.append({
                'id': getattr(ev, 'id', f'evt_{len(self._events_compiled)}'),
                'trigger': trig_code,
                'trigger_str': trig,
                'delay': float(getattr(ev, 'delay', 0.0) or 0.0),
                'assignments': assign_compiled,
            })
        if self._events_compiled:
            logger.info(
                "GPUHybridEngine: %d environment event(s) registered: %s",
                len(self._events_compiled),
                [f"{e['id']}@({e['trigger_str']})" for e in self._events_compiled],
            )

    def _estimate_vram_per_replicate(self) -> float:
        """Estimate GPU VRAM usage per replicate in bytes.

        Accounts for:
        - State vector d_y: P × 8
        - Time + active flags: 8 + 1
        - Intermediate arrays during step computation:
          d_log_y [P], d_log_a [M], d_a_fwd [M], d_a_rev [M],
          d_a_net [M], d_lam_fwd [M], d_k [M×8], d_delta [P×8],
          d_mu [P], d_sigma_sq [P], d_tau_* [P], d_dy_ode [P_ode×8]
        - Safety factor 1.5× for CuPy workspace/fragmentation
        """
        P = self._P
        M = self._M_stoch
        P_ode = self._P_ode

        state = P * 8 + 8 + 1  # d_y row + d_t + d_active
        intermediates = (
            P * 8 +       # d_log_y
            M * 8 * 5 +   # d_log_a, d_a_fwd, d_a_rev, d_a_net, d_lam_fwd
            M * 8 +       # d_k (int64)
            P * 8 +       # d_delta
            P * 8 * 3 +   # d_mu, d_sigma_sq, d_eps_y
            P * 8 * 3 +   # d_tau_mu, d_tau_sigma, d_tau_per_place
            P_ode * 8     # d_dy_ode_masked
        )
        per_rep = state + intermediates
        return per_rep * 1.5  # safety factor

    def _max_batch_for_vram(self, n_requested: int) -> int:
        """Compute max replicates that fit in GPU VRAM.

        Reserves 1 GB for CuPy overhead, driver, and other allocations.
        """
        try:
            free, total = cp.cuda.Device().mem_info
        except Exception:
            # Can't query — assume 8 GB total, 6 GB usable
            free = 6 * 1024**3

        reserved = 1 * 1024**3  # 1 GB for driver/overhead
        usable = max(free - reserved, 512 * 1024**2)

        per_rep = self._estimate_vram_per_replicate()
        max_reps = max(1, int(usable / per_rep))

        if max_reps < n_requested:
            logger.info(
                "VRAM limit: %.1f GB free, %.0f B/rep → batching %d/%d",
                free / 1024**3, per_rep, max_reps, n_requested,
            )

        return min(max_reps, n_requested)

    def run_batch(
        self,
        n_replicates: int,
        duration: float,
        dt: float,
        seed_base: int = 42,
        *,
        snapshot_interval: int = 1,
        verbose: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Run N hybrid replicates in parallel.

        Each replicate shares the same ODE dynamics but has independent
        stochastic noise (different random seeds).  The ODE is advanced
        with RK4 on dt-sized steps; stochastic transitions fire with
        adaptive τ ≤ dt within each step.

        If N exceeds GPU VRAM capacity, replicates are split into
        sub-batches automatically.

        Returns list of result dicts compatible with ReplicateRunner format.
        """
        batch_size = self._max_batch_for_vram(n_replicates)

        if batch_size >= n_replicates:
            # All fit in one batch
            return self._run_sub_batch(
                n_replicates, duration, dt, seed_base,
                snapshot_interval=snapshot_interval,
                verbose=verbose,
                progress_callback=progress_callback,
            )

        # Split into sub-batches
        all_results: List[Dict[str, Any]] = []
        offset = 0
        batch_idx = 0
        while offset < n_replicates:
            chunk = min(batch_size, n_replicates - offset)
            if verbose:
                print(f"  GPU VRAM batch {batch_idx + 1}: "
                      f"replicates {offset}–{offset + chunk - 1} "
                      f"(of {n_replicates})")

            sub_results = self._run_sub_batch(
                chunk, duration, dt, seed_base + offset,
                snapshot_interval=snapshot_interval,
                verbose=verbose,
                progress_callback=progress_callback,
            )
            # Fix replicate IDs to be globally sequential
            for i, r in enumerate(sub_results):
                r["replicate_id"] = offset + i
                r["seed"] = seed_base + offset + i
            all_results.extend(sub_results)
            offset += chunk
            batch_idx += 1

        return all_results

    def _run_sub_batch(
        self,
        n_replicates: int,
        duration: float,
        dt: float,
        seed_base: int = 42,
        *,
        snapshot_interval: int = 1,
        verbose: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Run a single sub-batch of N replicates (must fit in VRAM)."""
        N = n_replicates
        P = self._P
        P_ode = self._P_ode
        M = self._M_stoch
        max_steps = int(duration / dt)

        if verbose:
            print(f"  GPU hybrid: {N} replicates × {max_steps} steps "
                  f"({P_ode} ODE places, {M} stochastic transitions)")
            if self._events_compiled:
                ev_summary = ", ".join(
                    f"{e['id']}@({e['trigger_str']})" for e in self._events_compiled
                )
                print(f"  GPU hybrid: {len(self._events_compiled)} environment event(s) active: {ev_summary}")

        t0_wall = time.time()

        # ── Device state ─────────────────────────────────────────────
        d_y = cp.tile(cp.asarray(self._y0), (N, 1))  # [N, P]
        d_t = cp.zeros(N, dtype=cp.float64)
        d_active = cp.ones(N, dtype=cp.bool_)

        # ── Host result buffers ──────────────────────────────────────
        record_capacity = max_steps // snapshot_interval + 2
        h_time_points = np.zeros((N, record_capacity), dtype=np.float64)
        h_trajectories = np.zeros((N, record_capacity, P), dtype=np.float32)
        record_idx = np.zeros(N, dtype=np.int64)

        # Record t=0
        y0_f32 = self._y0.astype(np.float32)
        for r in range(N):
            h_trajectories[r, 0, :] = y0_f32
        record_idx[:] = 1

        # ── RNG ──────────────────────────────────────────────────────
        cp.random.seed(seed_base)

        # ── Environment-event per-batch state ───────────────────────
        # Edge tracking: True if the trigger was True on the previous step
        # for replicate r and event e. Shape [N, n_events].
        n_events = len(self._events_compiled)
        if n_events > 0:
            event_last = np.zeros((N, n_events), dtype=np.bool_)
            # Deferred assignments: list of (fire_at_time, replicate_idx, {gi: value})
            # Resolved values are floats so the GPU writeback is trivial.
            event_pending: List[Tuple[float, int, Dict[int, float]]] = []
        else:
            event_last = None
            event_pending = []

        # ── ODE index arrays ─────────────────────────────────────────
        ode_idx = self._ode_indices  # numpy array of global indices
        extra_idx = self._extra_indices

        stopped_reasons = ["duration"] * N

        # Firing count accumulator: [N, M_stoch] — incremented each τ-leap step
        d_firings_total = cp.zeros((N, M), dtype=cp.int64)

        # ── Main step loop ───────────────────────────────────────────
        step = 0
        for step in range(max_steps):
            if not cp.any(d_active):
                break

            # Current time (scalar — all replicates are synchronised)
            t_now = float(d_t[0].get()) if cp.any(d_active) else 0.0

            # ════════════════════════════════════════════════════════════
            # PHASE 1: ODE integration (RK4, dt step)
            # ════════════════════════════════════════════════════════════
            # Download ODE state for all replicates to host
            h_y_full = d_y.get()  # [N, P]

            # RK4 for each replicate (batched on CPU using the compiled C RHS)
            h_y_ode = h_y_full[:, ode_idx]  # [N, P_ode]
            h_dydt_batch = self._batch_ode_rhs(h_y_full, h_y_ode, t_now, dt)

            # Upload and apply RK4 result
            d_dy_ode = cp.asarray(h_dydt_batch)  # [N, P_ode]
            d_ode_idx = cp.asarray(ode_idx)
            # Scatter-add the ODE delta into the full state
            # d_y[:, ode_idx] += d_dy_ode (only for active replicates)
            active_mask = d_active[:, cp.newaxis]  # [N, 1]
            d_dy_ode_masked = cp.where(
                cp.broadcast_to(active_mask, d_dy_ode.shape),
                d_dy_ode, 0.0
            )
            # Use advanced indexing for scatter update
            d_y[:, d_ode_idx] += d_dy_ode_masked
            cp.clip(d_y, 0.0, None, out=d_y)

            # ════════════════════════════════════════════════════════════
            # PHASE 2: Stochastic τ-leaping (within same dt)
            # ════════════════════════════════════════════════════════════
            if M > 0:
                # Propensities — use CPU callback if available (symbolic
                # rate expressions), otherwise GPU mass-action.
                if self._stoch_propensity_fn is not None:
                    h_y_phase2 = d_y.get()  # [N, P]
                    h_t_phase2 = d_t.get()  # [N]
                    h_a_fwd, h_a_rev = self._stoch_propensity_fn(
                        h_y_phase2, h_t_phase2,
                    )
                    d_a_fwd = cp.asarray(h_a_fwd)  # [N, M]
                    d_a_rev = cp.asarray(h_a_rev)  # [N, M]
                else:
                    # GPU mass-action propensities
                    d_y_safe = cp.maximum(d_y, 1e-30)
                    d_log_y = cp.log(d_y_safe)  # [N, P]
                    d_log_a = d_log_y @ self._d_input_stoich.T  # [N, M]
                    d_log_k = cp.log(cp.maximum(self._d_rate_fwd, 1e-30))
                    d_a_fwd = cp.exp(d_log_a + d_log_k[cp.newaxis, :])  # [N, M]

                    d_a_rev = cp.zeros_like(d_a_fwd)
                    if cp.any(self._d_is_rev):
                        d_log_kr = cp.log(cp.maximum(self._d_rate_rev, 1e-30))
                        d_S_pos = cp.maximum(self._d_S_stoch, 0.0).T  # [M, P]
                        d_log_a_rev = d_log_y @ d_S_pos.T
                        d_a_rev_all = cp.exp(d_log_a_rev + d_log_kr[cp.newaxis, :])
                        d_a_rev = cp.where(
                            self._d_is_rev[cp.newaxis, :], d_a_rev_all, 0.0
                        )

                d_a_net = d_a_fwd - d_a_rev  # [N, M]

                # ── Inhibitor arc predicate enforcement (formalism §Enabled) ──
                # Rule: M(p) >= threshold → transition disabled (propensity = 0)
                # This mirrors the CPU τ-leap path and must be applied on every
                # step so the GPU batch obeys the same enablement semantics.
                if self._inh_place_idx is not None:
                    # d_y shape: [N, P];  _inh_place_idx shape: [K]
                    # tokens[n, k] = d_y[n, _inh_place_idx[k]]
                    inh_tokens = d_y[:, self._inh_place_idx]          # [N, K]
                    inh_disabled = inh_tokens >= self._inh_thresholds  # [N, K] bool
                    # For each inhibitor k, zero the propensity of its transition
                    # column.  Scatter: for each k, d_a_fwd[:, trans_idx[k]] *= ~inh_disabled[:, k]
                    K = self._inh_place_idx.shape[0]
                    for _k in range(K):
                        _col = int(self._inh_trans_idx[_k].get())
                        _mask = ~inh_disabled[:, _k]                   # [N] bool
                        d_a_fwd[:, _col] = cp.where(_mask, d_a_fwd[:, _col], 0.0)
                        d_a_net[:, _col] = cp.where(_mask, d_a_net[:, _col], 0.0)

                # Tau selection (cap at dt to stay synchronised with ODE)
                d_tau = self._select_tau_batch(d_y, d_a_net, d_a_fwd)
                d_tau = cp.minimum(d_tau, dt)
                d_tau = cp.maximum(d_tau, self._min_tau)
                d_tau = cp.where(d_active, d_tau, 0.0)

                # Poisson sampling
                d_lam_fwd = d_a_fwd * d_tau[:, cp.newaxis]
                d_lam_fwd = cp.maximum(d_lam_fwd, 0.0)
                d_k = cp.zeros((N, M), dtype=cp.int64)
                # Accumulate firing counts (initialised once before inner loop)

                irrev_mask = ~self._d_is_rev
                if cp.any(irrev_mask):
                    irrev_idx = irrev_mask.get()
                    lam_irrev = cp.clip(d_lam_fwd[:, irrev_idx], 0.0, 1e8)
                    d_k[:, irrev_idx] = cp.random.poisson(lam_irrev).astype(cp.int64)

                if cp.any(self._d_is_rev):
                    rev_idx = self._d_is_rev.get()
                    lam_f = cp.clip(d_lam_fwd[:, rev_idx], 0.0, 1e8)
                    lam_r = cp.clip(
                        d_a_rev[:, rev_idx] * d_tau[:, cp.newaxis], 0.0, 1e8
                    )
                    k_fwd = cp.random.poisson(lam_f)
                    k_rev = cp.random.poisson(lam_r)
                    d_k[:, rev_idx] = (k_fwd - k_rev).astype(cp.int64)

                # State update: y += k @ S^T
                d_delta = d_k.astype(cp.float64) @ self._d_S_stoch.T  # [N, P]
                d_y += d_delta
                cp.clip(d_y, 0.0, None, out=d_y)
                d_firings_total += cp.maximum(d_k, 0)

                # Deadlock detection (all stochastic propensities ≤ 0)
                d_total_a = cp.sum(cp.maximum(d_a_net, 0.0), axis=1)
                newly_dead = d_active & (d_total_a <= 0.0)
                if cp.any(newly_dead):
                    dead_idx = cp.where(newly_dead)[0].get()
                    for r in dead_idx:
                        stopped_reasons[int(r)] = "deadlock"
                d_active &= (d_total_a > 0.0)

            # ════════════════════════════════════════════════════════════
            # Advance time
            # ════════════════════════════════════════════════════════════
            d_t += dt
            newly_done = d_active & (d_t >= duration - 1e-12)
            d_active &= ~newly_done

            # ════════════════════════════════════════════════════════════
            # PHASE 3: Environment events (parity with CPU controller)
            # Evaluated after time advances so trigger expressions like
            # `t > 5400` see the new t. Per-replicate edge-triggered;
            # writes assignments back into d_y.
            # ════════════════════════════════════════════════════════════
            if n_events > 0:
                self._evaluate_events_batch(
                    d_y, d_t, d_active, event_last, event_pending,
                )

            # Snapshot
            if step % snapshot_interval == 0:
                h_t = d_t.get()
                h_y = d_y.get().astype(np.float32)
                for r in range(N):
                    ri = record_idx[r]
                    if ri < record_capacity:
                        h_time_points[r, ri] = h_t[r]
                        h_trajectories[r, ri, :] = h_y[r, :]
                        record_idx[r] = ri + 1

            # Progress
            if progress_callback and step % 50 == 0:
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
            print(f"  GPU hybrid done in {elapsed:.1f}s "
                  f"({step + 1} steps, {N} replicates)")

        # ── Convert to ReplicateRunner format ────────────────────────
        results: List[Dict[str, Any]] = []
        for r in range(N):
            n_rec = int(record_idx[r])
            tp = h_time_points[r, :n_rec].tolist()
            traj = h_trajectories[r, :n_rec, :]

            place_data: Dict[str, List[float]] = {}
            for i, pid in enumerate(self._place_ids):
                place_data[pid] = traj[:, i].tolist()

            final_marking: Dict[str, float] = {}
            for i, pid in enumerate(self._place_ids):
                final_marking[pid] = float(h_y[r, i])

            results.append({
                "replicate_id": r,
                "seed": seed_base + r,
                "time_points": tp,
                "place_data": place_data,
                "transition_data": {},
                "transition_rates": {},
                "final_marking": final_marking,
                "total_firings": {
                    tid: int(d_firings_total[r, j].get())
                    for j, tid in enumerate(self._stoch_transition_ids)
                } if self._stoch_transition_ids else {},
                "stopped_reason": stopped_reasons[r],
                "elapsed_time": elapsed / N,
            })

        return results

    # ── Batched ODE RHS with RK4 ────────────────────────────────────

    def _batch_ode_rhs(
        self,
        h_y_full: NDArray,     # [N, P] full state
        h_y_ode: NDArray,      # [N, P_ode] ODE state slice
        t_now: float,
        dt: float,
    ) -> NDArray:
        """Evaluate RK4 step for all N replicates using the compiled C RHS.

        The C function signature is ``(t, y) → dydt`` for a single system.
        We call it N times (vectorized loop). For 30 replicates with
        34 ODE places, this is ~30 × 0.01ms ≈ 0.3ms per step — negligible
        compared to GPU kernel overhead.

        Returns the delta (y_new - y_old) for the ODE places: [N, P_ode].
        """
        N = h_y_ode.shape[0]
        P_ode = self._P_ode
        delta = np.zeros((N, P_ode), dtype=np.float64)

        for r in range(N):
            y_r = h_y_ode[r].copy()
            # Update extras (signal places) from full state
            self._update_extras_from_state(h_y_full[r])

            # RK4
            k1 = np.array(self._ode_rhs_fn(t_now, y_r))
            k2 = np.array(self._ode_rhs_fn(t_now + dt / 2, y_r + dt / 2 * k1))
            k3 = np.array(self._ode_rhs_fn(t_now + dt / 2, y_r + dt / 2 * k2))
            k4 = np.array(self._ode_rhs_fn(t_now + dt, y_r + dt * k3))

            delta[r] = (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        return delta

    def _update_extras_from_state(self, h_y_r: NDArray) -> None:
        """Write signal-place tokens into the ODE extras array.

        The ODE RHS function reads 'extras' for places that appear in
        rate expressions but aren't part of the ODE state vector.
        """
        if len(self._extra_indices) == 0:
            return
        # The ODE accelerator's extras array is a reference that the
        # RHS closure reads.  We update it in-place.
        if hasattr(self._ode_rhs_fn, '_extras_arr'):
            extras = self._ode_rhs_fn._extras_arr
            for i, global_idx in enumerate(self._extra_indices):
                extras[i] = h_y_r[global_idx]

    # ── Tau selection (same as GPUReplicateEngine) ───────────────────

    def _evaluate_events_batch(
        self,
        d_y: Any,                                # cupy [N, P]  state
        d_t: Any,                                # cupy [N]     time per replicate
        d_active: Any,                           # cupy [N]     active mask
        event_last: NDArray[np.bool_],           # [N, n_events]
        event_pending: List[Tuple[float, int, Dict[int, float]]],
    ) -> None:
        """Per-step environment-event evaluation across all replicates.

        Mirrors :meth:`SimulationController._evaluate_environment_events`
        but vectorises across the N parallel replicates that share this
        GPU batch. Events are edge-triggered per replicate; assignments
        write the resolved float values back into ``d_y`` in-place.

        Run after time has been advanced for the current step so that
        triggers like ``t > 5400`` see the new ``t``.
        """
        if not self._events_compiled:
            return

        # Bring state to host. The hot path is small: N<=128, P<~100.
        # We have to do this anyway for trigger evaluation in Python.
        h_y = d_y.get()                          # [N, P] float64
        h_t = d_t.get()                          # [N]    float64
        h_active = d_active.get()                # [N]    bool
        N = h_y.shape[0]

        # Track which replicate rows we modify so we only re-upload those
        dirty_rows: List[int] = []
        # Pre-build per-place name list for namespace construction
        # (fast: use plain attribute lookup at module import time)
        place_id_to_index = self._place_id_to_index
        name_to_index = self._place_name_to_index

        # ---- 1. Resolve any pending (delayed) assignments whose time has come
        if event_pending:
            still_pending: List[Tuple[float, int, Dict[int, float]]] = []
            for fire_at, r, assigns in event_pending:
                if r >= N or not h_active[r]:
                    # Replicate is no longer active — drop the deferral
                    continue
                if h_t[r] >= fire_at:
                    for gi, val in assigns.items():
                        h_y[r, gi] = float(val)
                    if r not in dirty_rows:
                        dirty_rows.append(r)
                else:
                    still_pending.append((fire_at, r, assigns))
            event_pending[:] = still_pending

        # ---- 2. Evaluate triggers + apply assignments per replicate
        for r in range(N):
            if not h_active[r]:
                continue
            # Build evaluation namespace for this replicate
            row = h_y[r]
            t_r = float(h_t[r])
            ns: Dict[str, Any] = {'t': t_r}
            # Bind both place names and place IDs to current values
            for nm, gi in name_to_index.items():
                ns[nm] = float(row[gi])
            for pid, gi in place_id_to_index.items():
                ns[pid] = float(row[gi])

            for e_idx, ev in enumerate(self._events_compiled):
                try:
                    fired = bool(eval(ev['trigger'], {"__builtins__": {}}, ns))  # noqa: S307
                except Exception as exc:
                    logger.debug(
                        "[GPU_EVENT] trigger eval failed for event %r rep %d: %s",
                        ev['id'], r, exc,
                    )
                    continue

                prev = bool(event_last[r, e_idx])
                event_last[r, e_idx] = fired

                if not (fired and not prev):
                    continue  # not a rising edge

                # Resolve assignments now (snapshot semantics: values
                # captured at trigger time, matching the GUI default
                # `use_values_from_trigger_time=True`).
                resolved: Dict[int, float] = {}
                for gi, expr_code in ev['assignments'].items():
                    try:
                        v = eval(expr_code, {"__builtins__": {}}, ns)  # noqa: S307
                        resolved[gi] = float(v)
                    except Exception as exc:
                        logger.debug(
                            "[GPU_EVENT] assignment eval failed event=%r rep=%d gi=%d: %s",
                            ev['id'], r, gi, exc,
                        )

                if not resolved:
                    continue

                if ev['delay'] > 0.0:
                    event_pending.append((t_r + ev['delay'], r, resolved))
                else:
                    for gi, val in resolved.items():
                        h_y[r, gi] = val
                        # Update namespace so later assignments in the
                        # same step see the freshly-written value
                        for nm, g in name_to_index.items():
                            if g == gi:
                                ns[nm] = val
                        for pid, g in place_id_to_index.items():
                            if g == gi:
                                ns[pid] = val
                    if r not in dirty_rows:
                        dirty_rows.append(r)

        # ---- 3. Push dirty rows back to GPU
        if dirty_rows:
            # Single transfer for the whole [N, P] array is simpler and,
            # for the small batches we use, faster than per-row scatter.
            d_y[...] = cp.asarray(h_y)

    # ── Tau selection (same as GPUReplicateEngine) ───────────────────

    def _select_tau_batch(
        self,
        d_y: Any,       # [N, P]
        d_a_net: Any,   # [N, M]
        d_a_fwd: Any,   # [N, M]
    ) -> Any:           # [N]
        """Cao et al. (2006) τ-selection vectorised across replicates."""
        eps = self._epsilon
        M = self._M_stoch

        # μ_i = Σ_j S[i,j] · a_net[r,j]  → [N, P]
        d_mu = d_a_net @ self._d_S_stoch.T  # [N, M] @ [M, P] → [N, P]
        # Wait — S is [P, M], so S.T is [M, P]. We want [N, P]:
        # Actually d_a_net is [N, M], S is [P, M] → need (d_a_net @ S^T) but S^T is [M, P]
        # So d_mu = d_a_net @ S^T → [N, M] @ [M, P] → [N, P] ✓ (already correct above)

        # σ²_i = Σ_j S²[i,j] · a_fwd[r,j]  → [N, P]
        d_sigma_sq = d_a_fwd @ self._d_S_stoch_sq.T  # [N, P]

        # ε_i = max(ε · y / g, 1)
        d_eps_y = eps * d_y / self._d_g_vec[cp.newaxis, :]
        d_eps_y = cp.maximum(d_eps_y, 1.0)  # [N, P]

        # τ candidates: min(ε_i/|μ_i|, ε_i²/σ²_i) per place
        d_mu_abs = cp.abs(d_mu) + 1e-30  # avoid div by zero
        d_sigma_sq_safe = d_sigma_sq + 1e-30

        d_tau_mu = d_eps_y / d_mu_abs  # [N, P]
        d_tau_sigma = (d_eps_y ** 2) / d_sigma_sq_safe  # [N, P]
        d_tau_per_place = cp.minimum(d_tau_mu, d_tau_sigma)  # [N, P]

        # τ[r] = min over places
        d_tau = cp.min(d_tau_per_place, axis=1)  # [N]
        d_tau = cp.clip(d_tau, self._min_tau, self._max_tau)

        return d_tau
