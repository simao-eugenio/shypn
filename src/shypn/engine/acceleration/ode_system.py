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
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

from .codegen import (
    C_HELPERS,
    CONSTANT_VALUES,
    TranspileError,
    THERMO_LOCALS,
    collect_names,
    preprocess_expr,
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
            y0[idx] = max(float(getattr(p, "tokens", 0.0)) if p else 0.0, 1e-10)
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

        # Collect continuous transitions and their specs
        specs: List[_TransitionSpec] = []
        ode_place_ids_set: Set[str] = set()

        for t in model.transitions:
            t_type = getattr(t, "transition_type", "")
            if t_type != "continuous":
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

        # Emit rate computation for each transition
        c_thermo = THERMO_LOCALS
        transpile_fails: List[str] = []

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
                transpile_fails.append(
                    f"    /* WARNING: {spec.name} transpile failed: {exc} */"
                )
                # Emit a zero rate comment — transition will not be accelerated
                lines.append(c_comment)
                lines.append(f"    double {var} = 0.0;  /* transpile failed */{transpile_fails[-1]}")
                lines.append('')
            else:
                lines.append(c_comment)
                lines.append(f"    double {var} = {c_expr};")
                lines.append(f"    if (!isfinite({var})) {var} = 0.0;")
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

        if transpile_fails:
            logger.warning(
                "ODE acceleration: %d transition(s) could not be transpiled "
                "(will contribute zero to ODE — check generated C comments).",
                len(transpile_fails),
            )

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
