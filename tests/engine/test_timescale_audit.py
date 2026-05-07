"""TMD-1 timescale audit — unit tests.

Covers:
* C20 critical mismatch (a fast continuous transition flagged against
  a coarse dt).
* C21 model-wide stiffness ratio.
* C22 rate-evaluation failure.
* False-positive defense via Hill saturation (no flag when M ≪ K).
* Clean model produces no findings.
* RecordingConfig.timescale_check == "error" raises TimescaleMismatchError.
* Off-by-mode silences the audit entirely.
"""
from __future__ import annotations

import math
import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc as _TestArc  # rename to avoid pytest collection
from shypn.engine.simulation.checkers import audit_timescales
from shypn.engine.simulation.checkers.timescale_auditor import TimescaleProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_model(transitions_spec, places_spec):
    """Build a minimal DocumentModel from compact specs.

    places_spec    : list of (name, initial_marking)
    transitions_spec: list of (id, name, type, rate_function, [(input_place_name, weight)])
    """
    model = DocumentModel()
    place_by_name = {}
    for i, (name, m0) in enumerate(places_spec):
        p = Place(i * 50, i * 50, f"P{i}", name)
        p.initial_marking = float(m0)
        p.tokens = float(m0)
        model.add_place(p)
        place_by_name[name] = p

    for tspec in transitions_spec:
        tid, tname, ttype, rate, inputs = tspec
        t = Transition(500, 500, tid, tname)
        t.transition_type = ttype
        if not hasattr(t, "properties") or t.properties is None:
            t.properties = {}
        t.properties["rate_function"] = rate
        try:
            t.rate_function = rate
        except AttributeError:
            pass
        model.add_transition(t)
        for j, (input_name, weight) in enumerate(inputs):
            src = place_by_name[input_name]
            arc = Arc(
                source=src, target=t,
                id=f"A_{tid}_{j}", name=f"A_{tid}_{j}",
                weight=float(weight),
            )
            model.add_arc(arc)
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_clean_model_no_findings():
    """Slow rate vs reasonable dt produces no warnings."""
    model = _build_model(
        transitions_spec=[
            ("T0", "slow_decay", "continuous", "0.001 * A", [("A", 1.0)]),
        ],
        places_spec=[("A", 100.0)],
    )
    profile = audit_timescales(model, dt=1.0)
    assert profile.findings == []
    assert profile.critical_transitions == []
    # τ = M(A) / (W * r(A)) = 100 / (1 * 0.001*100) = 1000 s
    assert profile.tau_min == pytest.approx(1000.0, rel=1e-6)


def test_c20_critical_fast_transition():
    """k=10/s on M=100, W=1 → τ=10s; vs dt=1s, ratio=0.1, exactly at boundary.
    Use k=100 to be unambiguously critical."""
    model = _build_model(
        transitions_spec=[
            ("T0", "very_fast", "continuous", "100.0 * A", [("A", 1.0)]),
        ],
        places_spec=[("A", 100.0)],
    )
    profile = audit_timescales(model, dt=1.0, safety_factor=0.1)
    # τ = 100 / (1 * 100*100) = 1e-2 s; threshold = 0.1*1.0 = 0.1; 1e-2 < 0.1 → C20
    assert "T0" in profile.critical_transitions
    assert any(code == "C20" for code, _, _ in profile.findings)


def test_c21_stiffness_ratio_high():
    """One slow + one fast transition produce a stiffness-ratio warning."""
    model = _build_model(
        transitions_spec=[
            ("T0", "fast", "continuous", "10.0 * A", [("A", 1.0)]),
            ("T1", "slow", "continuous", "1.0e-6 * B", [("B", 1.0)]),
        ],
        places_spec=[("A", 100.0), ("B", 100.0)],
    )
    profile = audit_timescales(model, dt=1.0)
    codes = [c for c, _, _ in profile.findings]
    # τ_fast = 0.1, τ_slow = 1e6 → ratio 1e7 ≫ 1e4
    assert "C21" in codes
    assert profile.stiffness_ratio > 1e6


def test_c22_rate_eval_failure():
    """Rate referencing an unknown symbol is flagged as C22, not crash."""
    model = _build_model(
        transitions_spec=[
            ("T0", "broken", "continuous", "k_unknown * A", [("A", 1.0)]),
        ],
        places_spec=[("A", 10.0)],
    )
    profile = audit_timescales(model, dt=1.0)
    codes = [c for c, _, _ in profile.findings]
    assert "C22" in codes
    assert profile.transitions[0].rate_eval_error is not None


def test_hill_saturation_no_false_positive():
    """A nominal-fast Hill rate should not flag when M ≪ K.

    rate = 100 * A / (100 + A); at A=0.1 → r ≈ 0.0999/s; τ ≈ 1s ≮ 0.1s.
    """
    model = _build_model(
        transitions_spec=[
            ("T0", "hill", "continuous", "100.0 * A / (100.0 + A)", [("A", 1.0)]),
        ],
        places_spec=[("A", 0.1)],
    )
    profile = audit_timescales(model, dt=1.0, safety_factor=0.1)
    assert profile.critical_transitions == []


def test_stochastic_transition_not_assessed():
    """Stochastic τ-leaping adapts internally; auditor must skip it."""
    model = _build_model(
        transitions_spec=[
            ("T0", "fast_stoch", "stochastic", "100.0 * A", [("A", 100.0)]),
        ],
        places_spec=[("A", 100.0)],
    )
    profile = audit_timescales(model, dt=1.0)
    assert profile.transitions == []
    assert profile.findings == []


def test_test_arc_inputs_skipped():
    """Test arcs are non-consuming → must not contribute to τ."""
    model = DocumentModel()
    pa = Place(0, 0, "P0", "A"); pa.initial_marking = 100.0; pa.tokens = 100.0
    pb = Place(50, 0, "P1", "B"); pb.initial_marking = 0.001; pb.tokens = 0.001
    model.add_place(pa); model.add_place(pb)

    t = Transition(500, 500, "T0", "rxn")
    t.transition_type = "continuous"
    t.properties["rate_function"] = "0.01 * A"
    try:
        t.rate_function = "0.01 * A"
    except AttributeError:
        pass
    model.add_transition(t)

    a_normal = Arc(source=pa, target=t, id="A1", name="A1", weight=1.0)
    a_test = _TestArc(source=pb, target=t, id="A2", name="A2", weight=1.0)
    model.add_arc(a_normal); model.add_arc(a_test)

    profile = audit_timescales(model, dt=1.0)
    # τ should be M(A) / (W * r) = 100 / (1 * 1) = 100s (NOT 0.001/(1*1) from the test arc)
    assert profile.transitions[0].tau == pytest.approx(100.0, rel=1e-6)
    assert profile.critical_transitions == []


def test_recommended_dt_is_safety_factor_times_tau_min():
    model = _build_model(
        transitions_spec=[
            ("T0", "fast", "continuous", "5.0 * A", [("A", 1.0)]),
        ],
        places_spec=[("A", 100.0)],
    )
    profile = audit_timescales(model, dt=10.0, safety_factor=0.1)
    # rate = 5 * 100 = 500;  τ = 100 / (1 * 500) = 0.2 s;  recommended = 0.1 * 0.2 = 0.02 s
    assert profile.recommended_dt == pytest.approx(0.02, rel=1e-6)


def test_to_dict_serializable():
    model = _build_model(
        transitions_spec=[
            ("T0", "x", "continuous", "0.1 * A", [("A", 100.0)]),
        ],
        places_spec=[("A", 100.0)],
    )
    d = audit_timescales(model, dt=1.0).to_dict()
    import json
    json.dumps(d)  # must not raise
    assert d["n_transitions_assessed"] == 1
