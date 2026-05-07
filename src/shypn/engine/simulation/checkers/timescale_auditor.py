"""Load-time / init-time timescale audit (TMD-1).

Detects continuous & adaptive transitions whose **local timescale**
``τ_i = M_input / (W · r_i(M))`` is small relative to the integration
``dt``. The default fixed-step RK4 integrator becomes inaccurate when
``r_i · dt > 0.5`` and unstable when ``r_i · dt > 2.78``; this audit
flags transitions before the simulation runs so the operator can:

  (a) reduce dt globally,
  (b) convert the offending transition to ``transition_type='stochastic'``
      (τ-leap adapts locally), or
  (c) move to the LSODA acceleration path (best for many stiff transitions).

This is the **TMD-1** slice (static + init check). Runtime monitoring
(TMD-2) and sweep-level aggregation (TMD-3) live in separate modules.

Findings are returned as ``(code, transition_id, message)`` triples and
also logged at WARNING level. The audit never raises and never blocks
loading or simulation.

Codes
-----
* **C20 — timescale-mismatch-critical**
    ``τ_i < safety_factor · dt`` for at least one input place.
    The transition is integrated with ``r_i · dt > 1/safety_factor``
    per RK4 step; results are quantitatively unsafe.

* **C21 — stiffness-ratio-high**
    ``τ_max / τ_min > 1e4`` across the continuous transitions.
    The model is **stiff**; the canvas Play / sweep CLI fixed-step RK4
    will be inefficient or inaccurate. LSODA is recommended.

* **C22 — rate-eval-failed**
    Could not evaluate ``rate_function`` at ``M = M₀`` (missing symbol,
    division by zero, etc.). Audit could not assess this transition;
    fix the rate string before relying on simulation output.

References
----------
* ``doc/engine_stability_audit.md`` — F1–F7 + S-phases.
* ``workspace/projects/canabidiol/docs/engine_time_and_stiffness.md``
  — full TMD design and "cost of leaving as-is".
* AGENT_RULES.md §8 — sibling auditor (``arc_type_auditor.py``).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from shypn.utils.safe_eval import safe_eval_numeric

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TransitionTimescale:
    """Per-transition timescale assessment at a frozen marking."""

    transition_id: str
    transition_name: str
    transition_type: str
    rate: float
    """Evaluated rate ``r_i(M)`` (1/time units of the simulation)."""
    tau: float
    """Smallest ``M_input(P_j) / (W_ij · r_i)`` over input places.
    ``math.inf`` if the rate is non-positive or no consuming inputs."""
    limiting_place_id: Optional[str]
    """Place that determines τ (the one that empties first)."""
    rate_eval_error: Optional[str] = None
    """If non-None, rate evaluation failed; ``rate`` and ``tau`` are
    sentinel values and the transition is reported under C22."""


@dataclass
class TimescaleProfile:
    """Aggregate profile of all assessed continuous/adaptive transitions."""

    dt: float
    safety_factor: float
    transitions: List[TransitionTimescale] = field(default_factory=list)
    findings: List[Tuple[str, str, str]] = field(default_factory=list)
    """List of ``(code, transition_id, message)`` triples.
    Same convention as ``arc_type_auditor.audit_arc_types()``."""

    @property
    def tau_min(self) -> float:
        finite = [t.tau for t in self.transitions if math.isfinite(t.tau)]
        return min(finite) if finite else math.inf

    @property
    def tau_max(self) -> float:
        finite = [t.tau for t in self.transitions if math.isfinite(t.tau)]
        return max(finite) if finite else 0.0

    @property
    def stiffness_ratio(self) -> float:
        if self.tau_min <= 0 or not math.isfinite(self.tau_min):
            return 0.0
        if self.tau_max <= 0 or not math.isfinite(self.tau_max):
            return 0.0
        return self.tau_max / self.tau_min

    @property
    def critical_transitions(self) -> List[str]:
        threshold = self.safety_factor * self.dt
        return [
            t.transition_id
            for t in self.transitions
            if math.isfinite(t.tau) and t.tau < threshold
        ]

    @property
    def recommended_dt(self) -> float:
        """``safety_factor · τ_min`` — the largest dt that satisfies all
        assessed transitions."""
        if not math.isfinite(self.tau_min) or self.tau_min <= 0:
            return self.dt
        return self.safety_factor * self.tau_min

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dt": self.dt,
            "safety_factor": self.safety_factor,
            "tau_min": self.tau_min if math.isfinite(self.tau_min) else None,
            "tau_max": self.tau_max,
            "stiffness_ratio": self.stiffness_ratio,
            "recommended_dt": self.recommended_dt,
            "critical_transitions": list(self.critical_transitions),
            "n_transitions_assessed": len(self.transitions),
            "n_eval_errors": sum(1 for t in self.transitions if t.rate_eval_error),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


_CONTINUOUS_TYPES = ("continuous", "adaptive")


def audit_timescales(
    model: Any,
    dt: float,
    safety_factor: float = 0.1,
    stiffness_warn_ratio: float = 1.0e4,
) -> TimescaleProfile:
    """Audit per-transition timescales against a configured ``dt``.

    Args:
        model: a DocumentModel-like object exposing ``places`` and
            ``transitions`` iterables.
        dt: the integration step that will be used (typically
            ``settings.get_effective_dt()``).
        safety_factor: a transition is flagged C20 if
            ``τ_i < safety_factor · dt``. Default 0.1 is conservative
            and matches typical biochemistry practice.
        stiffness_warn_ratio: emit C21 if ``τ_max / τ_min`` exceeds this.

    Returns:
        TimescaleProfile with per-transition assessments and findings.
        Findings are also logged at WARNING level.

    Notes:
        * Only **continuous** and **adaptive** transitions are assessed.
          Stochastic τ-leaping adapts internally.
        * The audit is **silent on rate-formula errors** — they are
          captured as C22 findings but do not propagate exceptions.
        * Hill / Michaelis-Menten saturation is naturally accounted for
          because we evaluate the *actual* rate at ``M = M₀``, not the
          nominal rate constant.
    """
    profile = TimescaleProfile(dt=dt, safety_factor=safety_factor)

    # Build name → marking and parameter context once.
    context = _build_initial_context(model)
    place_by_id = {p.id: p for p in getattr(model, "places", []) or []}

    # Index input arcs by transition id.
    arcs_attr = getattr(model, "arcs", None)
    if arcs_attr is None:
        return profile
    arcs = list(arcs_attr.values()) if isinstance(arcs_attr, dict) else list(arcs_attr)
    inputs_by_t: Dict[str, List[Any]] = {}
    for a in arcs:
        tgt = getattr(a, "target_id", None)
        if tgt and isinstance(tgt, str) and tgt.startswith("T"):
            inputs_by_t.setdefault(tgt, []).append(a)

    transitions = list(getattr(model, "transitions", []) or [])
    for t in transitions:
        ttype = getattr(t, "transition_type", None) or ""
        if ttype not in _CONTINUOUS_TYPES:
            continue
        tid = getattr(t, "id", None)
        if not tid:
            continue
        tname = getattr(t, "name", "?")

        rate_function = _get_rate_function(t)
        if not rate_function:
            # Continuous transition with no rate function — nothing to assess.
            continue

        # Evaluate rate at M₀.
        try:
            r = float(safe_eval_numeric(rate_function, context, allow_math=True))
        except Exception as exc:  # noqa: BLE001 - audit must not raise
            ts = TransitionTimescale(
                transition_id=tid,
                transition_name=tname,
                transition_type=ttype,
                rate=float("nan"),
                tau=math.inf,
                limiting_place_id=None,
                rate_eval_error=str(exc),
            )
            profile.transitions.append(ts)
            msg = (
                f"C22 timescale audit: could not evaluate rate for "
                f"{tid} ({tname}): {exc}. Fix rate_function before "
                f"relying on simulation output."
            )
            profile.findings.append(("C22", tid, msg))
            LOGGER.warning(msg)
            continue

        # Compute τ over consuming input places.
        ins = inputs_by_t.get(tid, [])
        consuming = [
            a for a in ins
            if getattr(a, "arc_type", "normal") not in ("test", "inhibitor")
        ]

        tau = math.inf
        limiting_pid: Optional[str] = None
        if r > 0 and consuming:
            for a in consuming:
                src = getattr(a, "source_id", None)
                if not src:
                    continue
                p = place_by_id.get(src)
                if p is None:
                    continue
                m = float(getattr(p, "initial_marking", 0.0) or 0.0)
                w = float(getattr(a, "weight", 1.0) or 1.0)
                if w <= 0:
                    continue
                if m <= 0:
                    # Empty place: τ undefined here (rate will be 0 too).
                    continue
                tau_j = m / (w * r)
                if tau_j < tau:
                    tau = tau_j
                    limiting_pid = src

        ts = TransitionTimescale(
            transition_id=tid,
            transition_name=tname,
            transition_type=ttype,
            rate=r,
            tau=tau,
            limiting_place_id=limiting_pid,
        )
        profile.transitions.append(ts)

        # C20 — critical timescale mismatch.
        if math.isfinite(tau) and tau < safety_factor * dt and r > 0:
            limiting_name = (
                place_by_id[limiting_pid].name if limiting_pid in place_by_id else "?"
            )
            ratio = dt / tau if tau > 0 else float("inf")
            recipe = _decision_recipe(safety_factor * tau)
            msg = (
                f"C20 timescale-mismatch-critical: {tid} ({tname}) has "
                f"τ={tau:.3g}s on input '{limiting_name}' but dt={dt:.3g}s "
                f"({ratio:.1f}× too coarse).\n  {recipe}"
            )
            profile.findings.append(("C20", tid, msg))
            LOGGER.warning(msg)

    # C21 — model-wide stiffness.
    if (
        len(profile.transitions) >= 2
        and profile.stiffness_ratio > stiffness_warn_ratio
    ):
        msg = (
            f"C21 stiffness-ratio-high: τ_max/τ_min = "
            f"{profile.stiffness_ratio:.2e} (τ_min={profile.tau_min:.3g}s, "
            f"τ_max={profile.tau_max:.3g}s). "
            f"Recommended dt ≤ {profile.recommended_dt:.3g}s. Consider "
            f"the LSODA acceleration path for purely-continuous models."
        )
        profile.findings.append(("C21", "*", msg))
        LOGGER.warning(msg)

    return profile


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _decision_recipe(rec_dt: float) -> str:
    return (
        "Pick one: "
        f"(a) reduce dt to ≤ {rec_dt:.3g}s; "
        "(b) set transition_type='stochastic' (τ-leap adapts locally); "
        "(c) enable LSODA acceleration path (best when ≥5 stiff transitions)."
    )


def _get_rate_function(t: Any) -> Optional[str]:
    """Return the transition's rate function string, if any.

    The loader stores ``rate_function`` inside ``properties``; the
    Transition object exposes it as ``.rate_function``. Be defensive
    against either layout.
    """
    rf = getattr(t, "rate_function", None)
    if isinstance(rf, str) and rf.strip():
        return rf
    props = getattr(t, "properties", None) or {}
    if isinstance(props, dict):
        rf = props.get("rate_function")
        if isinstance(rf, str) and rf.strip():
            return rf
    return None


def _build_initial_context(model: Any) -> Dict[str, float]:
    """Build the {name: initial_marking} context for safe_eval.

    Includes regular places, signal places, spatial signal places, and
    parameter places. Uses ``initial_marking`` (canonical, per
    ``shy_loader_scopes`` policy); falls back to ``tokens`` for objects
    that only expose runtime state.
    """
    ctx: Dict[str, float] = {}
    for p in getattr(model, "places", []) or []:
        name = getattr(p, "name", None)
        if not name:
            continue
        v = getattr(p, "initial_marking", None)
        if v is None:
            v = getattr(p, "tokens", 0.0)
        try:
            ctx[name] = float(v)
        except (TypeError, ValueError):
            ctx[name] = 0.0
    # Common time symbol; rate may reference it but at t=0 it's 0.
    ctx.setdefault("t", 0.0)
    ctx.setdefault("time", 0.0)
    return ctx
