"""Build and manage the C ODE system for a SHYPN model.

This module analyses all *continuous* transitions in a model, constructs
the combined ``dy/dt = f(y, t, params)`` ODE system, generates C source
code, compiles it via gcc, and loads it via ctypes so that
``scipy.integrate.solve_ivp`` can call it with minimal Python overhead.

Memory layout
-------------
``y[]``      — tokens of every place that is an input or output of any
               continuous transition (the ODE state vector).
``extras[]`` — current tokens of every place that is *referenced* in at least
               one rate expression but has NO arc to any continuous transition
               (signal places / environmental sensors).  These are constant
               during a continuous integration interval and are written into
               the array by the Python wrapper before each ``solve_ivp`` call.
``params[]`` — thermodynamic scalars: [T, pH, ionic_strength].  Updated
               whenever the model's ``thermodynamic_settings`` change (e.g.
               when a fever event fires).

Generated C signature
---------------------
.. code-block:: c

    void ode_rhs(int n, double t, double *y, double *dydt,
                 double *extras, double *params);

The ctypes-based Python wrapper converts this to the ``(t, y) → dydt``
callable that ``scipy.integrate.solve_ivp`` expects.
"""

from __future__ import annotations

import ctypes
import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

from .codegen import (
    C_HELPERS,
    CONSTANT_VALUES,
    TranspileError,
    THERMO_LOCALS,
    collect_names,
    transpile_expression,
)
from .c_compiler import compile_ode_rhs

logger = logging.getLogger(__name__)

# Param-array layout (fixed positions)
_PARAM_T   = 0   # Temperature (K)
_PARAM_PH  = 1   # pH
_PARAM_I   = 2   # ionic strength
_N_PARAMS  = 3


# ===========================================================================
# Data class describing one continuous transition for the ODE system
# ===========================================================================

class _TransitionSpec:
    """Extracted data for one continuous transition."""

    __slots__ = (
        "name", "tid",
        "consume_arcs",   # list of (place_id, weight)
        "produce_arcs",   # list of (place_id, weight)
        "rate_expr",      # unified rate expression string (forward - reverse)
        "rate_fwd_expr",  # forward component (may be None)
        "rate_rev_expr",  # reverse component (may be None)
        "is_source",
        "is_sink",
    )

    def __init__(
        self,
        name: str,
        tid: str,
        consume_arcs: List[Tuple[str, float]],
        produce_arcs: List[Tuple[str, float]],
        rate_expr: Optional[str],
        rate_fwd_expr: Optional[str],
        rate_rev_expr: Optional[str],
        is_source: bool,
        is_sink: bool,
    ) -> None:
        self.name = name
        self.tid = tid
        self.consume_arcs = consume_arcs
        self.produce_arcs = produce_arcs
        self.rate_expr = rate_expr
        self.rate_fwd_expr = rate_fwd_expr
        self.rate_rev_expr = rate_rev_expr
        self.is_source = is_source
        self.is_sink = is_sink


# ===========================================================================
# Main OdeSystemAccelerator
# ===========================================================================

class OdeSystemAccelerator:
    """Build, compile, and drive the C ODE system for a SHYPN model.

    Parameters
    ----------
    model:
        The loaded SHYPN model object (must have ``.transitions``,
        ``.places``, ``.arcs``, and optionally ``.thermodynamic_settings``).
    get_behavior:
        Callable ``(transition) → behavior | None`` — same as controller's
        ``_get_behavior``.

    After construction call :meth:`build` to compile the C library.  If
    compilation succeeds, :attr:`ready` is *True* and :meth:`integrate` can
    be used.  If it fails (missing gcc, unsupported expression syntax, …) the
    object stays in a degraded mode and callers should use the Python fallback.
    """

    def __init__(self, model: Any, get_behavior: Callable[[Any], Any]) -> None:
        self._model = model
        self._get_behavior = get_behavior

        # State vector: place_id → index in y[]
        self._ode_place_index: Dict[str, int] = {}
        # Extras vector: place_id → index in extras[]
        self._extra_place_index: Dict[str, int] = {}
        # Ordered place IDs for state vector
        self._ode_place_ids: List[str] = []
        self._extra_place_ids: List[str] = []

        # ctypes library handle
        self._lib: Optional[ctypes.CDLL] = None
        self._c_func = None  # ctypes function pointer

        # numpy arrays kept alive between solve_ivp calls
        self._params_arr: Optional[np.ndarray] = None
        self._extras_arr: Optional[np.ndarray] = None

        # Metadata
        self._n_ode: int = 0
        self._n_extra: int = 0
        self._c_source: str = ""
        self._model_hash: str = ""

        self.ready: bool = False
        self._build_error: Optional[str] = None
        # Kinetic parameters from transition.kinetic_metadata.parameters
        self._model_kinetic_params: Dict[str, float] = {}
        # Accelerability audit (Phase-1 formalism gate): reasons collected by
        # _analyse_model.  Non-empty ⇒ build() returns False so caller falls
        # back to the Python ContinuousBehavior path.
        self._unsafe_reasons: List[str] = []
        # Inhibitor arc guards: tid → list of (source_place_id, threshold_expr).
        # Threshold may be a numeric string ("1.0") or an algebraic expression
        # ("4800 + 0.5 * ADP_pool") referencing other place names.  Encoded in
        # C as:  if (<M(src)> >= <threshold_c>) rate = 0.0;
        # This is semantically equivalent to the Python ContinuousBehavior path
        # (both evaluate at discrete dt steps).  Populated by _analyse_model,
        # consumed by _generate_c.
        self._inhibitor_guards: Dict[str, List[Tuple[str, str]]] = {}
        # PreemptionCheck specs: tid -> list of producer-predicate dicts.
        # Populated by _analyse_model for any continuous/adaptive transition
        # with at least one non-spatial signal_flow input.  Encoded in C by
        # _generate_c as a multiplicative {0.0, 1.0} gate on the rate.
        # See `_collect_preemption_specs` for structure.
        self._preemption_specs: Dict[str, List[Dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> bool:
        """Analyse model, generate C, compile, and load the .so.

        Returns True on success, False on any failure (see ``build_error``).
        """
        try:
            self._analyse_model()
            if not self._ode_place_ids:
                logger.debug("OdeSystemAccelerator: no continuous places — skipping")
                return False

            # Warn about transitions that the ODE accelerator will NOT
            # service.  Adaptive transitions in continuous mode are now
            # included in the ODE system (F2 fix); only non-continuous
            # non-adaptive transitions remain external.
            non_continuous = []
            covered_tids = {spec.tid for spec in self._specs}
            for t in getattr(self._model, "transitions", []):
                if t.id not in covered_tids:
                    t_type = getattr(t, "transition_type", "")
                    if t_type:
                        non_continuous.append(
                            f"  {getattr(t, 'name', t.id)} (type={t_type})"
                        )
            if non_continuous:
                logger.warning(
                    "ODE accelerator covers only continuous transitions.  "
                    "The following %d transition(s) require their own "
                    "execution engine (stochastic/timed/immediate/adaptive) "
                    "and will NOT fire during ODE integration:\n%s",
                    len(non_continuous),
                    "\n".join(non_continuous),
                )

            self._c_source = self._generate_c()
            self._model_hash = _short_hash(self._c_source)
            so_path = compile_ode_rhs(self._c_source, model_hash=self._model_hash)
            self._load_so(so_path)
            self._alloc_arrays()
            self.ready = True
            logger.info(
                "OdeSystemAccelerator: ready — %d ODE places, %d extras",
                self._n_ode, self._n_extra,
            )
            return True
        except Exception as exc:
            self._build_error = str(exc)
            logger.warning("OdeSystemAccelerator: build failed: %s", exc)
            return False

    @property
    def build_error(self) -> Optional[str]:
        return self._build_error

    @property
    def ode_transition_ids(self) -> List[str]:
        """IDs of transitions integrated by the C ODE RHS.

        For pure ``continuous`` transitions this is just their id.
        For ``adaptive`` transitions, only those whose configured /
        cached mode is ``continuous`` are included (i.e. they're being
        treated as ODE flows for this build).  The complementary set —
        adaptive transitions in stochastic mode — must be routed to the
        τ-leap batch by the caller, and pure ``continuous`` transitions
        must NEVER be in the τ-leap batch.

        Returns an empty list before :meth:`build` succeeds.
        """
        return [spec.tid for spec in getattr(self, "_specs", [])]

    def update_thermo_params(self) -> None:
        """Refresh the params[] array from the model's thermodynamic settings.

        Call this whenever a simulation event changes temperature or pH.
        """
        if self._params_arr is None:
            return
        settings = getattr(self._model, "thermodynamic_settings", {}) or {}
        self._params_arr[_PARAM_T]  = float(settings.get("temperature", 310.15))
        self._params_arr[_PARAM_PH] = float(settings.get("ph", 7.4))
        self._params_arr[_PARAM_I]  = float(settings.get("ionic_strength", 0.15))

    def update_extras(self) -> None:
        """Refresh extras[] from current place tokens."""
        if self._extras_arr is None:
            return
        places = _place_map(self._model)
        for pid, idx in self._extra_place_index.items():
            p = places.get(pid)
            if p is not None:
                self._extras_arr[idx] = max(float(getattr(p, "tokens", 0.0)), 1e-10)

    def get_y0(self) -> np.ndarray:
        """Return current ODE state vector from model place tokens."""
        places = _place_map(self._model)
        y0 = np.empty(self._n_ode, dtype=np.float64)
        for pid, idx in self._ode_place_index.items():
            p = places.get(pid)
            # F5 fix: use actual token value, not artificial 1e-10 floor.
            # Zero tokens means zero concentration — the ODE will produce
            # zero rates naturally without phantom initial conditions.
            tok = float(getattr(p, "tokens", 0.0)) if p else 0.0
            y0[idx] = max(tok, 0.0)
        return y0

    def write_back(self, y: np.ndarray) -> None:
        """Write ODE solution back to model place tokens."""
        places = _place_map(self._model)
        for pid, idx in self._ode_place_index.items():
            p = places.get(pid)
            if p is not None:
                val = max(float(y[idx]), 0.0)
                p.set_tokens(val)

    def make_rhs(self) -> Callable[[float, np.ndarray], np.ndarray]:
        """Return a ``fun(t, y) → dydt`` callable for ``scipy.solve_ivp``."""
        n = self._n_ode
        lib_fn = self._c_func
        params_arr = self._params_arr
        extras_arr = self._extras_arr

        # Pre-allocate output array (reused each call)
        dydt = np.empty(n, dtype=np.float64)

        def rhs(t: float, y: np.ndarray) -> np.ndarray:
            lib_fn(
                n, t,
                y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                dydt.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                extras_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                params_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            )
            return dydt.copy()

        return rhs

    def integrate(
        self,
        t_start: float,
        t_end: float,
        rtol: float = 1e-3,
        atol: float = 1e-6,
    ) -> bool:
        """Integrate from ``t_start`` to ``t_end`` and write back to model.

        Returns True on success, False if solve_ivp reported a failure.
        Extras and thermo params are refreshed before integration.
        """
        import scipy.integrate

        self.update_thermo_params()
        self.update_extras()

        y0 = self.get_y0()
        rhs = self.make_rhs()

        sol = scipy.integrate.solve_ivp(
            rhs,
            [t_start, t_end],
            y0,
            method="LSODA",   # stiff/non-stiff adaptive
            rtol=rtol,
            atol=atol,
            dense_output=False,
            max_step=(t_end - t_start),  # limit step size to reduce overshoot
        )

        if sol.success:
            self.write_back(sol.y[:, -1])
            return True
        else:
            logger.warning(
                "OdeSystemAccelerator.integrate: solve_ivp failed — %s",
                sol.message,
            )
            return False

    # ------------------------------------------------------------------
    # Internal: model analysis
    # ------------------------------------------------------------------

    def _analyse_model(self) -> None:
        """Identify continuous transitions and build place-index maps."""
        model = self._model
        places = _place_map(model)

        # Build arc lookup: {transition_id: {"in": [(place_id, weight, arc_type)], "out": [...]}}
        arc_in:  Dict[str, List[Tuple[str, float, str]]] = {}
        arc_out: Dict[str, List[Tuple[str, float, str]]] = {}
        for arc in getattr(model, "arcs", []):
            src = getattr(arc, "source_id", None)
            tgt = getattr(arc, "target_id", None)
            w   = float(getattr(arc, "weight", 1.0))
            at  = getattr(arc, "arc_type", "normal")
            if src is None or tgt is None:
                continue
            # Determine direction by checking if src/tgt are transitions
            src_is_t = _is_transition_id(src, model)
            tgt_is_t = _is_transition_id(tgt, model)
            if not src_is_t and tgt_is_t:
                # place → transition (input arc)
                arc_in.setdefault(tgt, []).append((src, w, at))
            elif src_is_t and not tgt_is_t:
                # transition → place (output arc)
                arc_out.setdefault(src, []).append((tgt, w, at))

        # Collect transitions for ODE integration.
        # Include both pure continuous and adaptive-in-continuous-mode
        # transitions so that the coupled ODE system captures ALL
        # continuous dynamics in a single solve_ivp call (F2 fix).
        specs: List[_TransitionSpec] = []
        ode_place_ids_set: Set[str] = set()

        for t in model.transitions:
            t_type = getattr(t, "transition_type", "")
            include = False
            if t_type == "continuous":
                include = True
            elif t_type == "adaptive":
                # Include adaptive transitions whose current mode is
                # continuous.  We check the behavior cache or fall back
                # to the default preference.  During ODE build the
                # controller has not yet stepped, so we inspect the
                # transition's configured preference.
                props = getattr(t, "properties", {}) or {}
                prefer = str(props.get("prefer_continuous", "true")).lower()
                # Also try to detect mode from a cached behavior if available
                _beh = getattr(t, '_behavior_cache', None)
                if _beh is not None and hasattr(_beh, '_current_mode'):
                    include = _beh._current_mode == 'continuous'
                elif _beh is not None and hasattr(_beh, '_select_mode'):
                    include = _beh._select_mode() == 'continuous'
                else:
                    # No cached behavior yet — use configured preference
                    include = prefer in ('true', '1', 'yes')
            if not include:
                continue
            props = getattr(t, "properties", {}) or {}
            rate_expr     = props.get("rate_function")
            rate_fwd_expr = props.get("rate_forward")
            rate_rev_expr = props.get("rate_reverse")

            if not rate_expr and not rate_fwd_expr and not rate_rev_expr:
                logger.debug(
                    "ODE acceleration: transition %s has no rate expression — "
                    "using 0", t.id
                )
                rate_expr = "0.0"

            tid = t.id
            consume: List[Tuple[str, float]] = []
            produce: List[Tuple[str, float]] = []

            # ── Accelerability audit (Phase-1 formalism gate) ────────
            # Inhibitor arcs: collect as C guards (if M(p) >= θ → rate=0).
            # This is equivalent to the Python ContinuousBehavior path which
            # also evaluates disablement at each discrete dt step.
            for pid, w, at in arc_in.get(tid, []):
                if "inhibitor" in at:
                    arc_obj = self._get_arc_by_endpoints(pid, tid)
                    # threshold may be numeric string or algebraic expression
                    raw_thresh = None
                    if arc_obj is not None:
                        raw_thresh = getattr(arc_obj, "threshold", None)
                    if raw_thresh is None:
                        threshold_expr = "1.0"
                    else:
                        threshold_expr = str(raw_thresh)
                    self._inhibitor_guards.setdefault(tid, []).append(
                        (pid, threshold_expr)
                    )

            # signal_flow with non-zero θ_eff or Arrhenius E_a (still unsafe —
            # basin-floor dynamics can't be inlined in the ODE C function)
            for pid, w, at in arc_in.get(tid, []):
                if at != "signal_flow":
                    continue
                arc_obj = self._get_arc_by_endpoints(pid, tid)
                if arc_obj is None:
                    continue
                theta = float(getattr(arc_obj, "theta_eff", 0.0) or 0.0)
                e_a   = float(getattr(arc_obj, "activation_energy", 0.0) or 0.0)
                if theta != 0.0 or e_a != 0.0:
                    self._unsafe_reasons.append(
                        f"  • {t.id} ({getattr(t, 'name', '')}): "
                        f"signal_flow arc from {pid} has θ_eff={theta}, "
                        f"E_a={e_a} — engine ignores basin floor"
                    )
                    break

            # PreemptionCheck non-vacuous?  Any non-spatial signal_flow
            # input.  We now ENCODE the check in C as a multiplicative
            # {0.0, 1.0} gate on the rate (see _collect_preemption_specs
            # and _generate_c).  Single-layer per the 13-tuple formalism
            # — for each producer t' of each non-spatial signal place
            # p_s ∈ •_s t, verify NormalEnabled ∧ TestEnabled ∧
            # SignalEnabled.  No recursion; cascading consistency
            # propagates naturally because each layer evaluates the same
            # check on its own predecessors.
            preempt_spec = self._collect_preemption_for_transition(
                t.id, arc_in, places, model,
            )
            if preempt_spec:
                self._preemption_specs[t.id] = preempt_spec

            # Non-trivial transition guard?
            guard = getattr(t, "guard", 1)
            if not _is_trivial_guard(guard):
                self._unsafe_reasons.append(
                    f"  • {t.id} ({getattr(t, 'name', '')}): "
                    f"non-trivial guard {guard!r} — engine never evaluates it"
                )

            # min_token_threshold > 0?
            mtt = float(props.get("min_token_threshold", 0.0) or 0.0)
            if mtt > 0.0:
                self._unsafe_reasons.append(
                    f"  • {t.id} ({getattr(t, 'name', '')}): "
                    f"min_token_threshold={mtt} > 0 — engine ignores it"
                )

            # Non-trivial spatial boundary on any arc-touched place?
            touched_pids = (
                [p for p, _, _ in arc_in.get(tid, [])]
                + [p for p, _, _ in arc_out.get(tid, [])]
            )
            for pid in touched_pids:
                p = places.get(pid)
                if p is None:
                    continue
                btype = getattr(p, "boundary_type", None)
                btype_val = getattr(btype, "value", btype)
                if btype_val not in (None, "", "permeable"):
                    self._unsafe_reasons.append(
                        f"  • {t.id} ({getattr(t, 'name', '')}): "
                        f"place {pid} has boundary_type={btype_val!r} — "
                        f"engine never invokes BoundaryValidator"
                    )
                    break
            # ── End accelerability audit ────────────────────────────

            for pid, w, at in arc_in.get(tid, []):
                # Skip inhibitor and test arcs — they don't move tokens
                if "inhibitor" in at or at == "test":
                    continue
                consume.append((pid, w))
                ode_place_ids_set.add(pid)

            for pid, w, at in arc_out.get(tid, []):
                if "inhibitor" in at:
                    continue
                produce.append((pid, w))
                ode_place_ids_set.add(pid)

            specs.append(_TransitionSpec(
                name=getattr(t, "name", tid) or tid,
                tid=tid,
                consume_arcs=consume,
                produce_arcs=produce,
                rate_expr=rate_expr,
                rate_fwd_expr=rate_fwd_expr,
                rate_rev_expr=rate_rev_expr,
                is_source=bool(getattr(t, "is_source", False)),
                is_sink=bool(getattr(t, "is_sink", False)),
            ))

        # ── Phase-1 accelerability gate ───────────────────────────────
        # Refuse to build if any continuous transition relies on a
        # structural disablement guard the C path doesn't honour.
        # Caller falls back to Python ContinuousBehavior automatically.
        if self._unsafe_reasons:
            n = len(self._unsafe_reasons)
            raise RuntimeError(
                f"ODE accelerator refuses to build: {n} formalism guard(s) "
                f"cannot be encoded in C and would silently change dynamics:\n"
                + "\n".join(self._unsafe_reasons)
                + "\n  → Falling back to Python ContinuousBehavior path "
                  "(slower but formalism-faithful)."
            )

        # Assign state-vector indices (sorted for determinism)
        self._ode_place_ids = sorted(ode_place_ids_set)
        self._ode_place_index = {pid: i for i, pid in enumerate(self._ode_place_ids)}
        self._n_ode = len(self._ode_place_ids)

        # Collect extra (signal) places referenced in rate expressions
        place_name_to_id: Dict[str, str] = {}
        for p in getattr(model, "places", []):
            if hasattr(p, "name") and p.name:
                place_name_to_id[p.name] = p.id

        extra_set: Set[str] = set()
        for spec in specs:
            for expr in [spec.rate_expr, spec.rate_fwd_expr, spec.rate_rev_expr]:
                if not expr:
                    continue
                for name in collect_names(expr):
                    pid = place_name_to_id.get(name)
                    if pid and pid not in self._ode_place_index:
                        extra_set.add(pid)

        # PreemptionCheck predicates may reference places that are NOT
        # in any rate expression (the input places of a producer
        # transition).  Add them to extras so the C runtime can read
        # their markings via extras[].
        for plist in self._preemption_specs.values():
            for prod in plist:
                for (src_pid, _w, _theta, _kind) in prod['predicates']:
                    if src_pid not in self._ode_place_index:
                        extra_set.add(src_pid)

        # Inhibitor arc guards: the source place and any places referenced
        # inside a dynamic threshold expression must be readable in C.
        for guard_list in self._inhibitor_guards.values():
            for src_pid, threshold_expr in guard_list:
                if src_pid not in self._ode_place_index:
                    extra_set.add(src_pid)
                # Add any place names used inside the threshold expression
                for name in collect_names(threshold_expr):
                    ref_pid = place_name_to_id.get(name)
                    if ref_pid and ref_pid not in self._ode_place_index:
                        extra_set.add(ref_pid)

        self._extra_place_ids = sorted(extra_set)
        self._extra_place_index = {pid: i for i, pid in enumerate(self._extra_place_ids)}
        self._n_extra = len(self._extra_place_ids)

        self._specs = specs
        self._place_name_to_id = place_name_to_id

        # Collect kinetic parameters from every transition for C const declarations.
        # These are model-specific scalars (V2f, K2Glc, cytosol, extracellular, …)
        # that appear verbatim in rate expressions and must be declared in the C.
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

    # ------------------------------------------------------------------
    # Internal: C code generation
    # ------------------------------------------------------------------

    def _generate_c(self) -> str:
        """Generate the complete C source for the ODE RHS."""
        specs = self._specs
        ode_idx  = self._ode_place_index
        extra_idx = self._extra_place_index
        places = _place_map(self._model)

        # Build name→index maps using place names (as used in rate expressions)
        name_to_ode: Dict[str, int] = {}
        name_to_extra: Dict[str, int] = {}
        for pid, idx in ode_idx.items():
            p = places.get(pid)
            if p and getattr(p, "name", None):
                name_to_ode[p.name] = idx
            name_to_ode[pid] = idx  # also map by raw id

        for pid, idx in extra_idx.items():
            p = places.get(pid)
            if p and getattr(p, "name", None):
                name_to_extra[p.name] = idx
            name_to_extra[pid] = idx

        lines: List[str] = []
        lines.append('#include <math.h>')
        lines.append('#include <string.h>')
        lines.append('')
        lines.append(C_HELPERS)
        lines.append('')
        lines.append('/* params layout: [T=0, pH=1, ionic_strength=2] */')
        lines.append('')
        lines.append(
            'void ode_rhs(int n, double t, double *y, double *dydt,'
        )
        lines.append(
            '             double *extras, double *params) {'
        )
        lines.append('    (void)t;  /* suppress unused-variable warning */')
        lines.append('')
        lines.append('    /* Thermodynamic locals */')
        lines.append('    double T            = params[0];')
        lines.append('    double Temperature  = T;')
        lines.append('    double T_celsius    = T - 273.15;')
        lines.append('    double pH           = params[1];')
        lines.append('    double ph           = pH;')
        lines.append('    double I            = params[2];')
        lines.append('    double ionic_strength = I;')
        lines.append('    (void)T_celsius; (void)ph; (void)ionic_strength;')
        lines.append('')

        # --- Model kinetic parameter declarations ---
        # These are scalars (rate constants, volumes, Km values, …) that appear
        # verbatim in rate expressions but are not place indices or thermo locals.
        _C_ID_OK = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        _known_c = (
            set(name_to_ode) | set(name_to_extra) | THERMO_LOCALS
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

        lines.append('    /* Zero out derivatives */')
        lines.append('    memset(dydt, 0, (size_t)n * sizeof(double));')
        lines.append('')

        # F4 fix: removed in-RHS non-negative clamping.
        # The previous clamp (y[i] < 0 → y[i] = 0) introduced C⁰
        # discontinuities that could confuse LSODA's adaptive step
        # controller and prevented bidirectional flow in reversible
        # reactions.  Non-negativity is now enforced ONLY in write_back()
        # after integration completes.  LSODA's internal probes may
        # temporarily visit y < 0 but the final accepted solution is
        # clamped when written back to model tokens.
        lines.append('')

        # Emit rate computation for each transition
        c_thermo = THERMO_LOCALS

        for i, spec in enumerate(specs):
            var = f"rate_{i}"
            sanitized_name = re.sub(r'[^A-Za-z0-9_]', '_', spec.name)
            c_comment = f"    /* Transition {sanitized_name} */"

            # Build the combined rate expression
            fwd = spec.rate_fwd_expr
            rev = spec.rate_rev_expr
            base = spec.rate_expr

            if fwd or rev:
                if fwd and rev:
                    combined = f"({fwd}) - ({rev})"
                elif fwd:
                    combined = fwd
                else:
                    combined = f"(-({rev}))"
            else:
                combined = base or "0.0"

            try:
                c_expr = transpile_expression(
                    combined,
                    name_to_index=name_to_ode,
                    extra_params=name_to_extra,
                    thermo_locals=c_thermo,
                )
            except TranspileError as exc:
                # A transition whose rate cannot be transpiled would silently
                # contribute zero to the ODE — corrupting the dynamics of the
                # declared transition type.  Abort the build so the engine
                # falls back to the Python eval path which handles all syntax.
                raise TranspileError(
                    f"Cannot accelerate transition '{spec.name}': {exc}.  "
                    f"The ODE accelerator will fall back to the Python path "
                    f"to preserve transition semantics."
                ) from exc
            else:
                lines.append(c_comment)
                lines.append(f"    double {var} = {c_expr};")
                lines.append(f"    if (!isfinite({var})) {var} = 0.0;")
                # ── Inhibitor arc guards (formalism §3.3 / Arc.consumes_tokens) ──
                # M(p_inhib) >= θ  →  transition disabled  →  rate set to 0.0
                # Semantically equivalent to Python ContinuousBehavior path:
                # both evaluate disablement at discrete dt steps.
                inhib_guards = self._inhibitor_guards.get(spec.tid, [])
                if inhib_guards:
                    lines.append(
                        f"    /* Inhibitor arc guard(s) for {sanitized_name} */"
                    )
                    for (src_pid, threshold_expr) in inhib_guards:
                        src_c = self._marking_c_expr(
                            src_pid, ode_idx, extra_idx
                        )
                        try:
                            thresh_c = transpile_expression(
                                threshold_expr,
                                name_to_index=name_to_ode,
                                extra_params=name_to_extra,
                                thermo_locals=c_thermo,
                            )
                        except TranspileError:
                            # Fallback: use raw expression string as-is;
                            # gcc will catch genuine syntax errors at compile
                            # time, so this is safe.
                            thresh_c = threshold_expr
                        lines.append(
                            f"    if ({src_c} >= ({thresh_c})) {var} = 0.0;"
                        )
                # ── Single-layer PreemptionCheck gate (formalism §3.3) ──
                # If this transition has any non-spatial signal_flow
                # input, every producer of those signal places must
                # satisfy NormalEnabled ∧ TestEnabled ∧ SignalEnabled at
                # the current marking.  We encode the conjunction as a
                # multiplicative {0.0, 1.0} gate on the rate.  Vacuous
                # case (no producers / spatial-only) emits no gate code.
                preempt_producers = self._preemption_specs.get(spec.tid, [])
                if preempt_producers:
                    gate = f"preempt_{i}"
                    lines.append(f"    /* PreemptionCheck for {sanitized_name} */")
                    lines.append(f"    double {gate} = 1.0;")
                    for j, prod in enumerate(preempt_producers):
                        prod_var = f"pp_{i}_{j}"
                        prod_name_san = re.sub(
                            r'[^A-Za-z0-9_]', '_', prod['producer_name'],
                        )
                        lines.append(
                            f"    /* producer {prod['producer_tid']} ({prod_name_san}) */"
                        )
                        lines.append(f"    double {prod_var} = 1.0;")
                        for (src_pid, weight, theta, kind) in prod['predicates']:
                            mexpr = self._marking_c_expr(
                                src_pid, ode_idx, extra_idx,
                            )
                            if kind == "test":
                                # M(p) >= tau_t  (tau_t stored in `weight`)
                                lines.append(
                                    f"    if ({mexpr} < {weight!r}) "
                                    f"{prod_var} = 0.0;"
                                )
                            else:
                                # M(p) >= weight + theta_eff
                                req = float(weight) + float(theta)
                                lines.append(
                                    f"    if ({mexpr} < {req!r}) "
                                    f"{prod_var} = 0.0;"
                                )
                        lines.append(
                            f"    if ({prod_var} == 0.0) {gate} = 0.0;"
                        )
                    lines.append(f"    {var} *= {gate};")
                lines.append('')

            # Arc contribution lines
            if not spec.is_source:
                for pid, w in spec.consume_arcs:
                    idx_val = ode_idx.get(pid)
                    if idx_val is not None:
                        lines.append(
                            f"    dydt[{idx_val}] -= {w!r} * (({var}) > 0.0 ? ({var}) : 0.0);"
                        )
            if not spec.is_sink:
                for pid, w in spec.produce_arcs:
                    idx_val = ode_idx.get(pid)
                    if idx_val is not None:
                        lines.append(
                            f"    dydt[{idx_val}] += {w!r} * (({var}) > 0.0 ? ({var}) : 0.0);"
                        )
            # For reverse direction (rate < 0): produce from inputs, consume outputs
            if not spec.is_source and spec.consume_arcs:
                lines.append(
                    f"    /* reverse flow when {var} < 0 */"
                )
                for pid, w in spec.consume_arcs:
                    idx_val = ode_idx.get(pid)
                    if idx_val is not None:
                        lines.append(
                            f"    dydt[{idx_val}] += {w!r} * (({var}) < 0.0 ? (-({var})) : 0.0);"
                        )
            if not spec.is_sink and spec.produce_arcs:
                for pid, w in spec.produce_arcs:
                    idx_val = ode_idx.get(pid)
                    if idx_val is not None:
                        lines.append(
                            f"    dydt[{idx_val}] -= {w!r} * (({var}) < 0.0 ? (-({var})) : 0.0);"
                        )
            lines.append('')

        lines.append('}')  # end ode_rhs

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Internal: load .so and resolve function pointer
    # ------------------------------------------------------------------

    def _load_so(self, so_path: Path) -> None:
        lib = ctypes.CDLL(str(so_path))
        fn = lib.ode_rhs
        fn.restype = None
        fn.argtypes = [
            ctypes.c_int,                             # n
            ctypes.c_double,                          # t
            ctypes.POINTER(ctypes.c_double),          # y
            ctypes.POINTER(ctypes.c_double),          # dydt
            ctypes.POINTER(ctypes.c_double),          # extras
            ctypes.POINTER(ctypes.c_double),          # params
        ]
        self._lib = lib
        self._c_func = fn

    def _alloc_arrays(self) -> None:
        self._params_arr = np.zeros(_N_PARAMS, dtype=np.float64)
        self._extras_arr = np.zeros(max(self._n_extra, 1), dtype=np.float64)
        self.update_thermo_params()
        self.update_extras()

    # ------------------------------------------------------------------
    # Internal: accelerability helpers (Phase-1 gate)
    # ------------------------------------------------------------------

    def _get_arc_by_endpoints(self, source_id: str, target_id: str) -> Any:
        """Return the first model arc with matching (source_id, target_id)."""
        for arc in getattr(self._model, "arcs", []) or []:
            if (getattr(arc, "source_id", None) == source_id
                    and getattr(arc, "target_id", None) == target_id):
                return arc
        return None

    @staticmethod
    def _marking_c_expr(
        pid: str,
        ode_idx: Dict[str, int],
        extra_idx: Dict[str, int],
    ) -> str:
        """Return the C expression that reads marking M(p) by place id.

        Used by PreemptionCheck codegen to read input markings of producer
        transitions.  Falls back to ``0.0`` when the place is in neither
        array (defensive — should not happen because
        ``_analyse_model`` adds all predicate-referenced places to
        ``extra_set``).
        """
        if pid in ode_idx:
            return f"y[{ode_idx[pid]}]"
        if pid in extra_idx:
            return f"extras[{extra_idx[pid]}]"
        return "0.0"

    # ------------------------------------------------------------------
    # Internal: PreemptionCheck collection (single-layer)
    # ------------------------------------------------------------------

    def _collect_preemption_for_transition(
        self,
        tid: str,
        arc_in: Dict[str, List[Tuple[str, float, str]]],
        places: Dict[str, Any],
        model: Any,
    ) -> List[Dict[str, Any]]:
        """Collect single-layer PreemptionCheck producers for transition *tid*.

        Mirrors :meth:`TransitionBehavior._check_preemption` /
        :meth:`_check_three_predicates_for` but produces a static spec
        consumable by C codegen.

        Returns a list of producer specs::

            [
                {
                    'producer_tid':  str,
                    'producer_name': str,            # for C comment only
                    'predicates': [
                        (src_pid, weight, theta_eff, kind)
                        # kind ∈ {'normal_or_signal', 'test'}
                        # 'normal_or_signal' requires M(p) >= weight + theta_eff
                        # 'test'             requires M(p) >= weight  (or threshold)
                    ],
                },
                ...
            ]

        Empty list ⇒ no non-spatial signal_flow inputs (PreemptionCheck
        is vacuous; no C code emitted).

        Notes
        -----
        * Inhibitor inputs of the producer are skipped (per
          ``_check_three_predicates_for``).
        * theta_eff is taken from the static ``arc.theta_eff`` attribute.
          The Phase-1 guard above already refuses to build when any
          continuous transition has a signal_flow arc with E_a ≠ 0
          (Arrhenius θ_eff(T)) — so the static value is safe.
        * Producer transitions of any type (continuous, stochastic,
          immediate, timed, adaptive) are valid; the predicate only
          checks input arc satisfaction, never the producer's own
          PreemptionCheck (single-layer rule).
        """
        # 1. Find non-spatial signal_flow input places p_s of T_i
        signal_input_pids: List[str] = []
        seen_sp: Set[str] = set()
        for src_pid, _w, at in arc_in.get(tid, []):
            if at != "signal_flow":
                continue
            p = places.get(src_pid)
            if p is None:
                continue
            stype = getattr(p, "signal_type", None)
            stype_val = getattr(stype, "value", stype)
            # Spatial signal places are environmental scalars — excluded
            # from PreemptionCheck per HPN doc §3.  None / unset is
            # treated as "non-signal place" and skipped (these are not
            # legal sources of signal_flow arcs anyway, but guard).
            if stype_val in ("spatial", "SPATIAL"):
                continue
            if stype_val is None:
                # Place lacks signal_type — could happen for a plain
                # place wrongly connected via signal_flow.  The Python
                # _check_preemption treats it as preemption-relevant
                # (the spatial filter only excludes is_signal_place +
                # SPATIAL).  Mirror that: include if not spatial.
                if not getattr(p, "is_signal_place", False):
                    continue
            if src_pid in seen_sp:
                continue
            seen_sp.add(src_pid)
            signal_input_pids.append(src_pid)

        if not signal_input_pids:
            return []

        # 2. For each signal place, find every producer t' (signal_flow
        #    arc from t' to p_s).  Build predicate list from t'
        #    input arcs.
        producer_specs: List[Dict[str, Any]] = []
        seen_producer_tids: Set[str] = set()

        # Pre-index arcs by target for producer discovery
        arcs_by_target_place: Dict[str, List[Any]] = {}
        # Collect arcs that produce into signal places.  Both straight
        # signal_flow and curved_opposite_signal_flow are output arcs from
        # transitions that carry signal tokens; either can be the producer
        # arc in a PreemptionCheck chain.
        _SIGNAL_FLOW_ARC_TYPES = ("signal_flow", "curved_opposite_signal_flow")
        for arc in getattr(model, "arcs", []) or []:
            if getattr(arc, "arc_type", "normal") not in _SIGNAL_FLOW_ARC_TYPES:
                continue
            tgt = getattr(arc, "target_id", None)
            if tgt in seen_sp:
                arcs_by_target_place.setdefault(tgt, []).append(arc)

        for sp_id in signal_input_pids:
            for cand_arc in arcs_by_target_place.get(sp_id, []):
                producer_tid = getattr(cand_arc, "source_id", None)
                if producer_tid is None:
                    continue
                if not _is_transition_id(producer_tid, model):
                    continue
                if producer_tid in seen_producer_tids:
                    continue
                seen_producer_tids.add(producer_tid)

                producer = next(
                    (t for t in model.transitions if t.id == producer_tid),
                    None,
                )
                producer_name = (
                    getattr(producer, "name", producer_tid)
                    if producer is not None else producer_tid
                )

                # Collect predicates from producer's input arcs.
                predicates: List[Tuple[str, float, float, str]] = []
                for in_pid, in_w, in_at in arc_in.get(producer_tid, []):
                    if "inhibitor" in in_at:
                        continue  # inhibitor not in three-predicates
                    arc_obj = self._get_arc_by_endpoints(in_pid, producer_tid)
                    if in_at == "test":
                        # tau_t = arc.threshold if not None else arc.weight
                        thr = getattr(arc_obj, "threshold", None) if arc_obj is not None else None
                        tau_t = float(thr) if thr is not None else float(in_w)
                        predicates.append((in_pid, tau_t, 0.0, "test"))
                    else:
                        theta = 0.0
                        if arc_obj is not None:
                            theta = float(getattr(arc_obj, "theta_eff", 0.0) or 0.0)
                        predicates.append((in_pid, float(in_w), theta, "normal_or_signal"))

                producer_specs.append({
                    'producer_tid':  producer_tid,
                    'producer_name': str(producer_name),
                    'predicates':    predicates,
                })

        return producer_specs


# ===========================================================================
# Helpers
# ===========================================================================

def _place_map(model: Any) -> Dict[str, Any]:
    """Return {place_id: place} from model."""
    places = getattr(model, "places", None)
    if isinstance(places, dict):
        return places
    if isinstance(places, (list, tuple)):
        return {p.id: p for p in places if hasattr(p, "id")}
    return {}


def _transition_ids(model: Any) -> Set[str]:
    result: Set[str] = set()
    for t in getattr(model, "transitions", []):
        if hasattr(t, "id"):
            result.add(t.id)
    return result


_TRANSITION_ID_CACHE: Dict[int, Set[str]] = {}


def _is_transition_id(node_id: str, model: Any) -> bool:
    mid = id(model)
    if mid not in _TRANSITION_ID_CACHE:
        _TRANSITION_ID_CACHE[mid] = _transition_ids(model)
    return node_id in _TRANSITION_ID_CACHE[mid]


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _is_trivial_guard(guard: Any) -> bool:
    """Return True if `guard` is one of the always-pass sentinel values.

    Trivial guards: None, True, 1, 1.0, "", "1", "True", "true".
    Anything else (string expression, callable, dict, …) is treated as
    non-trivial and the C path cannot honour it.
    """
    if guard is None or guard is True:
        return True
    if isinstance(guard, (int, float)) and guard == 1:
        return True
    if isinstance(guard, str):
        return guard.strip().lower() in ("", "1", "true")
    return False
