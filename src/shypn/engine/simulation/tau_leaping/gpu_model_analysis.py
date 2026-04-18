"""Static model analysis for GPU replicate engine.

Extracts the stoichiometry, rate constants, and kinetic structure
from a SHYPN model into plain NumPy arrays that can be uploaded to
the GPU once and reused across all replicates.

This module has **no** GPU dependency — it runs on CPU and produces
NumPy arrays that :class:`GPUReplicateEngine` then uploads.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass
class GPUModelAnalysis:
    """Immutable snapshot of everything the GPU kernel needs.

    All arrays are host (NumPy) arrays — the GPU engine uploads them.

    Attributes:
        n_places:       Number of places in the model.
        n_transitions:  Number of stochastic/adaptive transitions.
        place_ids:      Ordered list of place IDs (row index in S).
        transition_ids: Ordered list of transition IDs (column index in S).
        S:              Stoichiometry matrix ``[n_places, n_transitions]``.
        S_neg:          Consumption matrix ``|min(S, 0)|``  (non-negative).
        S_sq:           Element-wise ``S²`` (for Cao variance term).
        g_vec:          Per-place highest stoichiometric order (``≥ 1``).
        y0:             Initial marking ``[n_places]``.
        rate_constants: Forward rate constant per transition ``[n_transitions]``.
        rate_rev:       Reverse rate constant (``0`` if irreversible).
        is_reversible:  Boolean mask ``[n_transitions]``.
        input_stoich:   Input stoichiometry ``[n_transitions, n_places]``:
                        ``input_stoich[j, i] = |S[i,j]|`` when ``S[i,j] < 0``.
        is_mass_action: Per-transition flag — ``True`` when the rate
                        expression is a simple constant (mass-action kinetics)
                        so that ``a_j = k_j · ∏ y_i^v_ij`` holds.
    """

    n_places: int
    n_transitions: int
    place_ids: List[str]
    transition_ids: List[str]
    S: NDArray[np.float64]
    S_neg: NDArray[np.float64]
    S_sq: NDArray[np.float64]
    g_vec: NDArray[np.float64]
    y0: NDArray[np.float64]
    rate_constants: NDArray[np.float64]
    rate_rev: NDArray[np.float64]
    is_reversible: NDArray[np.bool_]
    input_stoich: NDArray[np.float64]
    is_mass_action: NDArray[np.bool_]

    @property
    def all_mass_action(self) -> bool:
        """True if every transition is simple mass-action."""
        return bool(np.all(self.is_mass_action))

    @property
    def mass_action_fraction(self) -> float:
        """Fraction of transitions that are mass-action."""
        if self.n_transitions == 0:
            return 0.0
        return float(np.sum(self.is_mass_action)) / self.n_transitions


def analyse_model(
    model: Any,
    get_behavior: Any,
    propensity_accel: Optional[Any] = None,
) -> Optional[GPUModelAnalysis]:
    """Extract GPU-ready arrays from a SHYPN model.

    Parameters
    ----------
    model:
        The loaded ``DocumentModel``.
    get_behavior:
        ``(transition) → behavior | None`` callable (usually
        ``controller._get_behavior``).
    propensity_accel:
        Optional :class:`PropensityAccelerator` — if available, the
        stoichiometry matrix and arc tables are reused instead of
        recomputed.

    Returns
    -------
    GPUModelAnalysis or None
        ``None`` when the model has no stochastic transitions.
    """
    # ── Collect stochastic/adaptive transitions ──────────────────────
    stoch_transitions: List[Any] = [
        t for t in model.transitions
        if getattr(t, "transition_type", "") in ("stochastic", "adaptive")
    ]
    if not stoch_transitions:
        return None

    # ── Place ordering ───────────────────────────────────────────────
    all_places = list(getattr(model, "places", []))
    place_ids = sorted(p.id for p in all_places if hasattr(p, "id"))
    place_idx: Dict[str, int] = {pid: i for i, pid in enumerate(place_ids)}
    n_places = len(place_ids)
    places_by_id: Dict[str, Any] = {p.id: p for p in all_places}

    # ── Transition ordering ──────────────────────────────────────────
    transition_ids = [t.id for t in stoch_transitions]
    trans_idx: Dict[str, int] = {tid: j for j, tid in enumerate(transition_ids)}
    n_trans = len(transition_ids)

    # ── Stoichiometry matrix ─────────────────────────────────────────
    if (
        propensity_accel is not None
        and getattr(propensity_accel, "ready", False)
        and propensity_accel._stoich_matrix is not None
    ):
        S = propensity_accel._stoich_matrix.copy()
        g_vec = propensity_accel._g_vec.copy()
    else:
        S = np.zeros((n_places, n_trans), dtype=np.float64)
        for arc in getattr(model, "arcs", []):
            kind = (
                getattr(arc, "kind", None)
                or (getattr(arc, "properties", None) or {}).get("kind", "normal")
                or "normal"
            )
            arc_type = getattr(arc, "arc_type", "normal")
            if kind != "normal" or arc_type in ("inhibitor", "test"):
                continue
            src = getattr(arc, "source", None)
            tgt = getattr(arc, "target", None)
            if src is None or tgt is None:
                continue
            w = float(getattr(arc, "weight", 1.0))
            # Consume arc: place → transition
            if hasattr(src, "tokens") and hasattr(tgt, "transition_type"):
                i = place_idx.get(getattr(src, "id", None))
                j = trans_idx.get(getattr(tgt, "id", None))
                if i is not None and j is not None:
                    S[i, j] -= w
            # Produce arc: transition → place
            elif hasattr(src, "transition_type") and hasattr(tgt, "tokens"):
                i = place_idx.get(getattr(tgt, "id", None))
                j = trans_idx.get(getattr(src, "id", None))
                if i is not None and j is not None:
                    S[i, j] += w
        g_vec = np.maximum(np.abs(S).max(axis=1), 1.0)

    S_neg = np.abs(np.minimum(S, 0.0))  # consumption weights (non-negative)
    S_sq = S * S

    # ── Input stoichiometry (transposed view for propensity eval) ────
    input_stoich = S_neg.T.copy()  # [n_trans, n_places]

    # ── Initial marking ──────────────────────────────────────────────
    y0 = np.zeros(n_places, dtype=np.float64)
    for pid, i in place_idx.items():
        p = places_by_id.get(pid)
        if p is not None:
            y0[i] = max(float(getattr(p, "tokens", 0.0)), 0.0)

    # ── Rate constants + reversibility detection ─────────────────────
    rate_fwd = np.ones(n_trans, dtype=np.float64)
    rate_rev = np.zeros(n_trans, dtype=np.float64)
    is_reversible = np.zeros(n_trans, dtype=np.bool_)
    is_mass_action = np.ones(n_trans, dtype=np.bool_)

    for j, t in enumerate(stoch_transitions):
        _rate, _is_ma = _extract_rate_constant(t, get_behavior)
        rate_fwd[j] = _rate
        is_mass_action[j] = _is_ma

        # Reverse component
        props = getattr(t, "properties", {}) or {}
        rev_expr = props.get("rate_reverse")
        if rev_expr is not None:
            try:
                rate_rev[j] = float(rev_expr)
                is_reversible[j] = True
            except (TypeError, ValueError):
                is_reversible[j] = True
                is_mass_action[j] = False  # non-constant reverse rate

    return GPUModelAnalysis(
        n_places=n_places,
        n_transitions=n_trans,
        place_ids=place_ids,
        transition_ids=transition_ids,
        S=S,
        S_neg=S_neg,
        S_sq=S_sq,
        g_vec=g_vec,
        y0=y0,
        rate_constants=rate_fwd,
        rate_rev=rate_rev,
        is_reversible=is_reversible,
        input_stoich=input_stoich,
        is_mass_action=is_mass_action,
    )


# ── helpers ──────────────────────────────────────────────────────────

def _extract_rate_constant(
    transition: Any,
    get_behavior: Any,
) -> Tuple[float, bool]:
    """Extract forward rate constant and mass-action flag.

    Returns ``(rate_value, is_mass_action)``.  When the rate expression
    is a plain float constant the transition is mass-action; otherwise
    the rate is set to 1.0 and ``is_mass_action=False``.
    """
    props = getattr(transition, "properties", {}) or {}

    # Try explicit forward rate
    rate_fwd_str = props.get("rate_forward") or props.get("rate_function")
    if rate_fwd_str:
        try:
            return float(rate_fwd_str), True
        except (TypeError, ValueError):
            return 1.0, False

    # Fall back to behavior object
    behavior = get_behavior(transition) if get_behavior else None
    if behavior:
        rate_expr = getattr(behavior, "rate_function_expr", None)
        if rate_expr:
            try:
                return float(rate_expr), True
            except (TypeError, ValueError):
                return 1.0, False
        rate_val = getattr(behavior, "rate", None)
        if rate_val is not None:
            try:
                return float(rate_val), True
            except (TypeError, ValueError):
                pass

    return 1.0, True  # default constant rate
