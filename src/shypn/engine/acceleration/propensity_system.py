"""Build and manage the C propensity function for the stochastic hot path.

This module analyses all *stochastic* and *adaptive* transitions in a model,
generates a C function that evaluates the **entire propensity vector** in a
single call, compiles it via gcc, and loads it via ctypes.

The generated function replaces the per-transition Python loop:
    behavior._evaluate_rate_at_enablement(time)  ← called N×2 times per step
with one C call that fills an array of propensities for all N transitions.

Memory layout
-------------
``y[]``      — current token counts for ALL model places, sorted by place id.
               These are copied from ``model.places`` before each call.
``a_net[i]`` — net propensity for transition i  (forward − reverse).
``a_fwd[i]`` — forward propensity for transition i.
``a_rev[i]`` — reverse propensity for transition i (0 for irreversible).
``params[]`` — thermodynamic scalars: [T, pH, ionic_strength].

For non-reversible transitions: ``a_fwd[i] == a_net[i]``, ``a_rev[i] == 0``.
For reversible transitions   : ``a_net[i] = a_fwd[i] − a_rev[i]``.

Generated C signature
---------------------
.. code-block:: c

    void propensity_fn(int n, double t, double *y,
                       double *a_net, double *a_fwd, double *a_rev,
                       double *params);

Integration points
------------------
``TauLeapingEngine.execute_step()``
    Calls ``compute(t)`` once before ``select_tau`` and caches propensities
    in ``self._accel_props`` so that both ``LeapSelector`` and
    ``_sample_firings`` avoid the second Python eval.

``LeapSelector.select_tau()``
    Accepts a ``propensity_hint`` dict ``{transition_id: (net, fwd, rev)}``
    and uses it instead of calling ``_evaluate_rate_at_enablement``.
"""

from __future__ import annotations

import ctypes
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

from .codegen import (
    C_HELPERS,
    CONSTANT_VALUES,
    THERMO_LOCALS,
    TranspileError,
    preprocess_expr,
    transpile_expression,
)
from .c_compiler import compile_c_lib

logger = logging.getLogger(__name__)

_PARAM_T  = 0
_PARAM_PH = 1
_PARAM_I  = 2
_N_PARAMS = 3


# ---------------------------------------------------------------------------
# Small data class for one stochastic/adaptive transition spec
# ---------------------------------------------------------------------------

class _StochasticSpec:
    """Extracted data for one stochastic/adaptive transition."""

    __slots__ = (
        "name", "tid",
        "rate_expr",      # net expression (or forward if reversible)
        "rate_fwd_expr",  # forward component (may equal rate_expr)
        "rate_rev_expr",  # reverse component (None if irreversible)
        "is_reversible",
    )

    def __init__(
        self,
        name: str,
        tid: str,
        rate_expr: Optional[str],
        rate_fwd_expr: Optional[str],
        rate_rev_expr: Optional[str],
        is_reversible: bool,
    ) -> None:
        self.name = name
        self.tid = tid
        self.rate_expr = rate_expr
        self.rate_fwd_expr = rate_fwd_expr
        self.rate_rev_expr = rate_rev_expr
        self.is_reversible = is_reversible


# ---------------------------------------------------------------------------
# PropensityAccelerator
# ---------------------------------------------------------------------------

class PropensityAccelerator:
    """Build, compile, and drive the C propensity function for a SHYPN model.

    Handles *stochastic* and *adaptive* transition types — the same set that
    ``TauLeapingEngine`` and ``LeapSelector`` operate on.

    Parameters
    ----------
    model:
        The loaded SHYPN model object.
    get_behavior:
        ``(transition) → behavior | None`` — same callable as the controller's
        ``_get_behavior``.

    Typical use
    -----------
    ::

        accel = PropensityAccelerator(model, controller._get_behavior)
        accel.build()                    # once per model load

        # Inside TauLeapingEngine.execute_step():
        accel.update_y_from_model()
        accel.update_thermo_params()
        a_net, a_fwd, a_rev = accel.compute(current_time)
    """

    # Class-level flag: prune the on-disk cache at most once per interpreter
    # session (avoids repeated filesystem scans when many instances are created,
    # as happens in parallel sweep workers).
    _cache_pruned: bool = False

    def __init__(self, model: Any, get_behavior: Callable[[Any], Any]) -> None:
        self._model = model
        self._get_behavior = get_behavior

        # All-place index: place_id → index in y[]
        self._all_place_index: Dict[str, int] = {}
        self._all_place_ids: List[str] = []

        # Ordered stochastic transition specs (same order as output arrays)
        self._specs: List[_StochasticSpec] = []
        # Corresponding transition objects (real model objects, same order)
        self._transitions: List[Any] = []

        # Public: sorted list of transition ids (same order as compute() output)
        self.transition_ids_order: List[str] = []
        # Public: bool array aligned with transition_ids_order
        self.is_reversible: np.ndarray = np.array([], dtype=bool)

        self._lib: Optional[ctypes.CDLL] = None
        self._c_func = None

        # Pre-allocated numpy arrays
        self._y_arr: Optional[np.ndarray] = None
        self._a_net_arr: Optional[np.ndarray] = None
        self._a_fwd_arr: Optional[np.ndarray] = None
        self._a_rev_arr: Optional[np.ndarray] = None
        self._params_arr: Optional[np.ndarray] = None

        self._n_transitions: int = 0
        self._n_places: int = 0
        self._c_source: str = ""
        self._model_hash: str = ""

        self.ready: bool = False
        self._build_error: Optional[str] = None
        # Kinetic parameters from transition.kinetic_metadata.parameters
        self._model_kinetic_params: Dict[str, float] = {}

        # Phase 2.1: Precomputed arc lookup table built once in _analyse_model().
        # transition_id → [(place_object, consume_weight), ...] (normal arcs only).
        # Shared with LeapSelector to eliminate O(|arcs|) scan per τ-step.
        self._input_arc_table: Dict[str, List[Tuple[Any, float]]] = {}
        # Direct place lookup by id for update_y_partial().
        self._places_by_id: Dict[str, Any] = {}

        # Phase 3: stoichiometry matrix S[n_places × n_transitions] built in
        # _analyse_model().  S[i,j] = net token change in place i per single
        # firing of transition j (negative = consume, positive = produce).
        # S_sq = S² element-wise — precomputed for the Cao variance term.
        # g_vec = per-place highest stoichiometric order (≥ 1).
        # output_arc_table mirrors _input_arc_table for produce arcs.
        self._stoich_matrix: Optional[np.ndarray] = None
        self._stoich_matrix_sq: Optional[np.ndarray] = None
        self._g_vec: Optional[np.ndarray] = None
        self._output_arc_table: Dict[str, List[Tuple[Any, float]]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def build_error(self) -> Optional[str]:
        return self._build_error

    def build(self) -> bool:
        """Analyse model, generate C, compile, and load the .so.

        Returns True on success, False on any failure.
        """
        try:
            # Prune stale cache entries once per interpreter session so the
            # ~/.cache/shypn/ode_accel/ directory does not grow unboundedly.
            if not PropensityAccelerator._cache_pruned:
                PropensityAccelerator._cache_pruned = True
                try:
                    from shypn.engine.acceleration.c_compiler import prune_cache
                    prune_cache()
                except Exception:
                    pass
            self._analyse_model()
            if not self._specs:
                logger.debug(
                    "PropensityAccelerator: no stochastic transitions — skipping"
                )
                return False
            self._c_source = self._generate_c()
            import hashlib
            self._model_hash = hashlib.sha256(
                self._c_source.encode()
            ).hexdigest()[:16]
            so_path = compile_c_lib(
                self._c_source,
                lib_name="propensity_fn",
                model_hash=self._model_hash,
            )
            try:
                self._load_so(so_path)
            except (OSError, AttributeError) as load_exc:
                # .so exists but symbol is missing or the file is corrupt
                # (e.g. a previous process crashed mid-rename).  Delete and
                # force a fresh compilation, then try once more.
                logger.warning(
                    "PropensityAccelerator: cached .so failed to load (%s); "
                    "deleting and recompiling …", load_exc,
                )
                so_path.unlink(missing_ok=True)
                so_path = compile_c_lib(
                    self._c_source,
                    lib_name="propensity_fn",
                    model_hash=self._model_hash,
                    force=True,
                )
                # dlopen(3) caches library handles keyed by the absolute path
                # string.  After unlink + recompile to the same canonical path
                # in the same process, a subsequent ctypes.CDLL() call returns
                # the stale in-memory handle for the now-deleted library, so
                # the missing-symbol error would repeat.  Loading via a unique
                # per-call copy bypasses the cache; the copy is removed once
                # the handle is open (the kernel keeps the mapping alive until
                # self._lib goes out of scope).
                import os as _os
                import shutil
                import tempfile
                _fd, _tmp = tempfile.mkstemp(
                    suffix=".so", dir=str(so_path.parent)
                )
                _tmp_path = Path(_tmp)
                try:
                    _os.close(_fd)
                    shutil.copy2(so_path, _tmp_path)
                    self._load_so(_tmp_path)  # re-raise if still broken
                finally:
                    _tmp_path.unlink(missing_ok=True)
            self._alloc_arrays()
            self.ready = True
            logger.info(
                "PropensityAccelerator: ready — %d stochastic transitions, "
                "%d places (y[] size)",
                self._n_transitions,
                self._n_places,
            )
            return True
        except Exception as exc:
            self._build_error = str(exc)
            logger.warning("PropensityAccelerator: build failed: %s", exc)
            return False

    def update_y_from_model(self) -> None:
        """Copy ALL place tokens into y[] (full sync). Used on the first step
        and whenever a complete refresh is required (e.g. exact-SSA fallback)."""
        if self._y_arr is None:
            return
        places = _place_map(self._model)
        for pid, idx in self._all_place_index.items():
            p = places.get(pid)
            if p is not None:
                self._y_arr[idx] = max(
                    float(getattr(p, "tokens", 0.0)), 0.0
                )

    def update_y_partial(self, changed_ids: Set[str]) -> None:
        """Copy only the places in *changed_ids* into y[] (partial sync).

        Faster than :meth:`update_y_from_model` when just a few places
        changed during the previous τ-step.  The caller is responsible for
        ensuring *changed_ids* lists every place whose ``tokens`` attribute
        was modified since the last sync.

        Phase 2.2 optimisation — called by :class:`TauLeapingEngine` after
        every firing step instead of the full update.
        """
        if self._y_arr is None:
            return
        for pid in changed_ids:
            idx = self._all_place_index.get(pid)
            if idx is None:
                continue
            place = self._places_by_id.get(pid)
            if place is not None:
                self._y_arr[idx] = max(
                    float(getattr(place, "tokens", 0.0)), 0.0
                )

    def update_thermo_params(self) -> None:
        """Refresh params[] from model.thermodynamic_settings."""
        if self._params_arr is None:
            return
        settings = getattr(self._model, "thermodynamic_settings", {}) or {}
        self._params_arr[_PARAM_T]  = float(settings.get("temperature", 310.15))
        self._params_arr[_PARAM_PH] = float(settings.get("ph", 7.4))
        self._params_arr[_PARAM_I]  = float(settings.get("ionic_strength", 0.15))

    def compute(self, t: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate the full propensity vector at time *t*.

        **Call ``update_y_from_model()`` and ``update_thermo_params()``
        before every ``compute()`` call.**

        Returns
        -------
        a_net, a_fwd, a_rev
            Three numpy float64 arrays of length ``n_transitions``,
            aligned with ``transition_ids_order``.
        """
        n = self._n_transitions
        self._c_func(
            n,
            ctypes.c_double(t),
            self._y_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            self._a_net_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            self._a_fwd_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            self._a_rev_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            self._params_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        return self._a_net_arr, self._a_fwd_arr, self._a_rev_arr

    def compute_batch(
        self,
        t_batch: np.ndarray,            # [N] float64, replicate times
        y_batch: np.ndarray,            # [N, P] float64, full place markings
        a_fwd_out: np.ndarray,          # [N, M] float64, written in-place
        a_rev_out: np.ndarray,          # [N, M] float64, written in-place
    ) -> None:
        """Evaluate propensities for N replicates in a single C call.

        Hot-path entry for ``GPUHybridEngine``.  Replaces a ``for r in
        range(N): self.compute(...)`` Python loop (~µs per iteration in
        ctypes overhead alone) with one batched dispatch.

        ``y_batch`` columns must be aligned with ``self._all_place_index``
        — the caller is expected to have done the place-id remap once
        at setup time using fancy indexing.

        ``a_fwd_out`` and ``a_rev_out`` columns are aligned with
        ``self.transition_ids_order`` (i.e. the C function's spec
        order).  No remap is performed here; the caller's hybrid
        engine builds its stoichiometry against the same order.

        ``update_thermo_params()`` should be called once per dt step
        before this method (params are constant across replicates).
        """
        N, P = y_batch.shape
        M = self._n_transitions
        # Lazily allocate / resize the per-call a_net scratch.
        scratch = getattr(self, "_a_net_scratch", None)
        if scratch is None or scratch.shape[0] != M:
            scratch = np.zeros(max(M, 1), dtype=np.float64)
            self._a_net_scratch = scratch

        # Ensure C-contiguous float64 input (most callers already are).
        if not y_batch.flags["C_CONTIGUOUS"] or y_batch.dtype != np.float64:
            y_batch = np.ascontiguousarray(y_batch, dtype=np.float64)
        if not t_batch.flags["C_CONTIGUOUS"] or t_batch.dtype != np.float64:
            t_batch = np.ascontiguousarray(t_batch, dtype=np.float64)

        self._c_func_batch(
            ctypes.c_int(N),
            ctypes.c_int(M),
            ctypes.c_int(P),
            t_batch.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            y_batch.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            a_fwd_out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            a_rev_out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            self._params_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            scratch.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

    # ------------------------------------------------------------------
    # Internal: model analysis
    # ------------------------------------------------------------------

    def _analyse_model(self) -> None:
        """Build place index and stochastic transition spec list."""
        model = self._model

        # All places → y[] index (sorted for determinism)
        all_places = list(getattr(model, "places", []))
        self._all_place_ids = sorted(
            p.id for p in all_places if hasattr(p, "id")
        )
        self._all_place_index = {
            pid: i for i, pid in enumerate(self._all_place_ids)
        }
        self._n_places = len(self._all_place_ids)

        # Place name / id → y[] index (for transpilation)
        place_map = _place_map(model)
        name_to_index: Dict[str, int] = {}
        for pid, idx in self._all_place_index.items():
            name_to_index[pid] = idx
            p = place_map.get(pid)
            if p and getattr(p, "name", None):
                name_to_index[p.name] = idx

        self._name_to_index = name_to_index

        # Collect stochastic/adaptive transitions
        specs: List[_StochasticSpec] = []
        transitions: List[Any] = []

        for t in model.transitions:
            t_type = getattr(t, "transition_type", "")
            if t_type not in ("stochastic", "adaptive"):
                continue

            rate_expr, rate_fwd, rate_rev = self._extract_rate(t)
            is_reversible = rate_rev is not None

            specs.append(_StochasticSpec(
                name=getattr(t, "name", t.id) or t.id,
                tid=t.id,
                rate_expr=rate_expr,
                rate_fwd_expr=rate_fwd,
                rate_rev_expr=rate_rev,
                is_reversible=is_reversible,
            ))
            transitions.append(t)

        self._specs = specs
        self._transitions = transitions
        self._n_transitions = len(specs)
        self.transition_ids_order = [s.tid for s in specs]
        self.is_reversible = np.array(
            [s.is_reversible for s in specs], dtype=bool
        )

        # Collect kinetic parameters from every transition for C const declarations.
        model_params: Dict[str, float] = {}
        for t in getattr(model, "transitions", []):
            km = getattr(t, "kinetic_metadata", None)
            if km is not None:
                raw = getattr(km, "parameters", None) or {}
                for k, v in raw.items():
                    if k not in model_params:
                        try:
                            model_params[k] = float(v)
                        except (TypeError, ValueError):
                            pass
        self._model_kinetic_params = model_params

        # Phase 2.1: build input arc lookup table and place-by-id map.
        # Done here (after all_places is built) so place objects are live refs.
        places_by_id: Dict[str, Any] = {
            p.id: p for p in all_places if hasattr(p, "id")
        }
        input_arc_table: Dict[str, List[Tuple[Any, float]]] = {}
        for _arc in getattr(model, "arcs", []):
            _target = getattr(_arc, "target", None)
            if _target is None or not hasattr(_target, "transition_type"):
                continue
            _tid = getattr(_target, "id", None)
            if _tid is None:
                continue
            # Skip non-consuming arcs (test, inhibitor, and all curved
            # variants).  Arc.consumes_tokens() is the single source of truth
            # per the 13-tuple Bio-PN formalism (workspace instructions §
            # "Consumption semantics by arc type") — using it here is
            # generic and correct for any current or future arc subclass.
            if not _arc.consumes_tokens():
                continue
            _source = getattr(_arc, "source", None)
            if _source is None or not hasattr(_source, "tokens"):
                continue
            _weight = float(getattr(_arc, "weight", 1.0))
            input_arc_table.setdefault(_tid, []).append((_source, _weight))
        self._input_arc_table = input_arc_table
        self._places_by_id = places_by_id

        # Phase 3: stoichiometry matrix S[n_places × n_transitions].
        # Only covers the stochastic/adaptive transitions (same set as the
        # C propensity function).
        _tid_to_j: Dict[str, int] = {
            tid: j for j, tid in enumerate(self.transition_ids_order)
        }
        _S = np.zeros((self._n_places, self._n_transitions), dtype=np.float64)
        _out_tbl: Dict[str, List[Tuple[Any, float]]] = {}
        for _arc in getattr(model, "arcs", []):
            # Skip non-consuming arcs (test, inhibitor, curved_inhibitor_arc,
            # etc.).  Arc.consumes_tokens() is the single source of truth per
            # the 13-tuple Bio-PN formalism — generic for any arc subclass.
            if not _arc.consumes_tokens():
                continue
            _src = getattr(_arc, "source", None)
            _tgt = getattr(_arc, "target", None)
            if _src is None or _tgt is None:
                continue
            _w = float(getattr(_arc, "weight", 1.0))
            # Consume arc: place → transition  (negative stoichiometry)
            if hasattr(_src, "tokens") and hasattr(_tgt, "transition_type"):
                _pid = getattr(_src, "id", None)
                _tid = getattr(_tgt, "id", None)
                _i = self._all_place_index.get(_pid)
                _j = _tid_to_j.get(_tid)
                if _i is not None and _j is not None:
                    _S[_i, _j] -= _w
            # Produce arc: transition → place  (positive stoichiometry)
            elif hasattr(_src, "transition_type") and hasattr(_tgt, "tokens"):
                _pid = getattr(_tgt, "id", None)
                _tid = getattr(_src, "id", None)
                _i = self._all_place_index.get(_pid)
                _j = _tid_to_j.get(_tid)
                if _i is not None and _j is not None:
                    _S[_i, _j] += _w
                if _tid is not None:
                    _out_tbl.setdefault(_tid, []).append((_tgt, _w))

        self._stoich_matrix = _S
        self._stoich_matrix_sq = _S * _S  # element-wise; used for Cao variance term
        # g_i: conservative approx — max |v_{ij}| for place i.
        # Bounded below at 1.0 (first-order minimum; prevents /0).
        self._g_vec = np.maximum(np.abs(_S).max(axis=1), 1.0)
        self._output_arc_table = _out_tbl

    def _extract_rate(
        self, transition: Any
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Return (net_expr, forward_expr, reverse_expr) for a transition.

        Tries in order:
        1. Explicit ``rate_forward`` / ``rate_reverse`` properties
        2. ``rate_function`` property with reversibility detection
        3. Behaviour object's ``rate_function_expr``
        4. Behaviour's constant ``rate`` attribute
        5. Default ``'1.0'``

        Returns
        -------
        (net_expr, fwd_expr, rev_expr)
            *rev_expr* is ``None`` for irreversible reactions.
        """
        props = getattr(transition, "properties", {}) or {}

        # Explicit forward/reverse split
        rate_fwd = props.get("rate_forward")
        rate_rev_p = props.get("rate_reverse")
        if rate_fwd:
            return (None, rate_fwd, rate_rev_p or None)

        # Single formula — try reversibility detection
        rate_expr: Optional[str] = props.get("rate_function")

        # Fall back to behavior object
        if not rate_expr:
            behavior = self._get_behavior(transition)
            if behavior:
                rate_expr = getattr(behavior, "rate_function_expr", None)
                if not rate_expr:
                    rate_val = getattr(behavior, "rate", None)
                    if rate_val is not None:
                        rate_expr = str(float(rate_val))

        if not rate_expr:
            return ("1.0", "1.0", None)

        # Pre-process bracket notation
        rate_expr = preprocess_expr(rate_expr)

        # Try reversibility detection via SkellamSampler
        try:
            from shypn.engine.simulation.tau_leaping.skellam_sampler import (
                SkellamSampler,
            )
            is_rev, fwd_str, rev_str = SkellamSampler.detect_reversible_formula(
                rate_expr
            )
            if is_rev:
                return (None, fwd_str, rev_str)
        except Exception:
            pass

        return (rate_expr, rate_expr, None)

    # ------------------------------------------------------------------
    # Internal: C code generation
    # ------------------------------------------------------------------

    def _generate_c(self) -> str:
        """Generate the complete C source for the propensity function.

        Emits three symbols:

        * ``static inline _propensity_one(...)`` — per-replicate body,
          contains thermo + kinetic-param decls + the per-spec rate
          expressions.  The compiler inlines this into both entry
          points at -O3.
        * ``propensity_fn(...)`` — single-replicate ABI (legacy).
        * ``propensity_fn_batch(...)`` — N-replicate batched ABI.
          Used by ``compute_batch()`` to evaluate all replicates of a
          single hybrid step in one C call (eliminates the Python
          per-replicate dispatch overhead, ~10⁶ calls/sim).
        """
        name_to_index = self._name_to_index
        c_thermo = THERMO_LOCALS

        lines: List[str] = []
        lines.append("#include <math.h>")
        lines.append("#include <stddef.h>")
        lines.append("")
        lines.append(C_HELPERS)
        lines.append("")
        lines.append("/* params: [T=0, pH=1, ionic_strength=2] */")
        lines.append("")
        # ── per-replicate helper ─────────────────────────────────────
        lines.append("static inline void _propensity_one(")
        lines.append("        double t, const double *y,")
        lines.append("        double *a_net, double *a_fwd, double *a_rev,")
        lines.append("        const double *params)")
        lines.append("{")
        lines.append("    (void)t;")
        lines.append("")
        lines.append("    /* Thermodynamic locals */")
        lines.append("    double T            = params[0];")
        lines.append("    double Temperature  = T;")
        lines.append("    double T_celsius    = T - 273.15;")
        lines.append("    double pH           = params[1];")
        lines.append("    double ph           = pH;")
        lines.append("    double I            = params[2];")
        lines.append("    double ionic_strength = I;")
        lines.append(
            "    (void)T_celsius; (void)ph; (void)ionic_strength;"
        )
        lines.append("")

        # --- Model kinetic parameter declarations ---
        _C_ID_OK = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        _known_c = (
            set(name_to_index) | c_thermo
            | set(CONSTANT_VALUES) | {'pi', 'e', 'time', 't', 'n'}
        )
        kp_lines = [
            f'    const double {pk} = {pv!r};'
            for pk, pv in sorted(self._model_kinetic_params.items())
            if pk not in _known_c and _C_ID_OK.match(pk)
        ]
        if kp_lines:
            lines.append('    /* Model kinetic parameters */')
            lines.extend(kp_lines)
            lines.append('')

        for i, spec in enumerate(self._specs):
            sanitized = re.sub(r"[^A-Za-z0-9_]", "_", spec.name)
            lines.append(f"    /* [{i}] {sanitized} */")
            lines.append("    {")

            # ---- forward propensity ----
            fwd_src = spec.rate_fwd_expr or spec.rate_expr or "1.0"
            try:
                c_fwd = transpile_expression(
                    fwd_src,
                    name_to_index=name_to_index,
                    extra_params={},      # all places already in y[]
                    thermo_locals=c_thermo,
                )
            except TranspileError as exc:
                raise TranspileError(
                    f"Cannot accelerate stochastic transition '{spec.name}' "
                    f"(forward rate): {exc}.  The propensity accelerator "
                    f"will fall back to the Python eval path to preserve "
                    f"transition semantics."
                ) from exc

            lines.append(f"        double _fwd = {c_fwd};")
            lines.append(
                "        if (!isfinite(_fwd) || _fwd < 0.0) _fwd = 0.0;"
            )

            # ---- reverse propensity ----
            if spec.is_reversible and spec.rate_rev_expr:
                try:
                    c_rev = transpile_expression(
                        spec.rate_rev_expr,
                        name_to_index=name_to_index,
                        extra_params={},
                        thermo_locals=c_thermo,
                    )
                except TranspileError as exc:
                    raise TranspileError(
                        f"Cannot accelerate stochastic transition '{spec.name}' "
                        f"(reverse rate): {exc}.  The propensity accelerator "
                        f"will fall back to the Python eval path to preserve "
                        f"transition semantics."
                    ) from exc
            else:
                c_rev = "0.0"

            lines.append(f"        double _rev = {c_rev};")
            lines.append(
                "        if (!isfinite(_rev) || _rev < 0.0) _rev = 0.0;"
            )
            lines.append(f"        a_fwd[{i}] = _fwd;")
            lines.append(f"        a_rev[{i}] = _rev;")
            lines.append(f"        a_net[{i}] = _fwd - _rev;")
            lines.append("    }")
            lines.append("")

        lines.append("}")  # end _propensity_one
        lines.append("")

        # ── Single-replicate entry (legacy ABI) ───────────────────────
        lines.append("#if defined(__GNUC__)")
        lines.append("__attribute__((visibility(\"default\")))")
        lines.append("#endif")
        lines.append(
            "void propensity_fn(int n, double t, double *y,"
        )
        lines.append(
            "                   double *a_net, double *a_fwd, double *a_rev,"
        )
        lines.append("                   double *params) {")
        lines.append("    (void)n;")
        lines.append(
            "    _propensity_one(t, y, a_net, a_fwd, a_rev, params);"
        )
        lines.append("}")
        lines.append("")

        # ── Batched entry: N replicates in one C call ─────────────────
        # Layout: y_batch is [N, P] row-major, a_*_batch are [N, M].
        # a_net_scratch is a caller-provided [M] buffer used per
        # replicate (we don't return a_net to the batched caller —
        # the GPU hybrid path doesn't need it; tau-leap consumes
        # a_fwd / a_rev separately).
        lines.append("#if defined(__GNUC__)")
        lines.append("__attribute__((visibility(\"default\")))")
        lines.append("#endif")
        lines.append("void propensity_fn_batch(")
        lines.append("        int N, int M, int P,")
        lines.append("        const double *t_batch,")
        lines.append("        const double *y_batch,")
        lines.append("        double *a_fwd_batch,")
        lines.append("        double *a_rev_batch,")
        lines.append("        const double *params,")
        lines.append("        double *a_net_scratch)")
        lines.append("{")
        lines.append("    for (int r = 0; r < N; r++) {")
        lines.append("        const double *y_r = y_batch + (size_t)r * (size_t)P;")
        lines.append("        double *af_r = a_fwd_batch + (size_t)r * (size_t)M;")
        lines.append("        double *ar_r = a_rev_batch + (size_t)r * (size_t)M;")
        lines.append("        _propensity_one(t_batch[r], y_r,")
        lines.append("                        a_net_scratch, af_r, ar_r, params);")
        lines.append("    }")
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal: load .so and wire ctypes
    # ------------------------------------------------------------------

    def _load_so(self, so_path: Path) -> None:
        lib = ctypes.CDLL(str(so_path))
        fn = lib.propensity_fn
        fn.restype = None
        fn.argtypes = [
            ctypes.c_int,                            # n
            ctypes.c_double,                         # t
            ctypes.POINTER(ctypes.c_double),         # y
            ctypes.POINTER(ctypes.c_double),         # a_net
            ctypes.POINTER(ctypes.c_double),         # a_fwd
            ctypes.POINTER(ctypes.c_double),         # a_rev
            ctypes.POINTER(ctypes.c_double),         # params
        ]
        # Batched entry — one C call evaluates N replicates.
        fn_b = lib.propensity_fn_batch
        fn_b.restype = None
        fn_b.argtypes = [
            ctypes.c_int,                            # N
            ctypes.c_int,                            # M
            ctypes.c_int,                            # P
            ctypes.POINTER(ctypes.c_double),         # t_batch [N]
            ctypes.POINTER(ctypes.c_double),         # y_batch [N*P]
            ctypes.POINTER(ctypes.c_double),         # a_fwd_batch [N*M]
            ctypes.POINTER(ctypes.c_double),         # a_rev_batch [N*M]
            ctypes.POINTER(ctypes.c_double),         # params [3]
            ctypes.POINTER(ctypes.c_double),         # a_net_scratch [M]
        ]
        self._lib = lib
        self._c_func = fn
        self._c_func_batch = fn_b

    def _alloc_arrays(self) -> None:
        n = self._n_transitions
        m = max(self._n_places, 1)
        self._y_arr      = np.zeros(m, dtype=np.float64)
        self._a_net_arr  = np.zeros(max(n, 1), dtype=np.float64)
        self._a_fwd_arr  = np.zeros(max(n, 1), dtype=np.float64)
        self._a_rev_arr  = np.zeros(max(n, 1), dtype=np.float64)
        self._params_arr = np.zeros(_N_PARAMS, dtype=np.float64)
        self.update_thermo_params()
        self.update_y_from_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _place_map(model: Any) -> Dict[str, Any]:
    places = getattr(model, "places", None)
    if isinstance(places, dict):
        return places
    if isinstance(places, (list, tuple)):
        return {p.id: p for p in places if hasattr(p, "id")}
    return {}
