#!/usr/bin/env python3
"""Test the Phase-1 accelerability gate on OdeSystemAccelerator.

The C-compiled ODE RHS encodes only stoichiometry + the rate expression.  It
does NOT honour structural disablement guards (inhibitor arcs, θ_eff floor on
signal_flow, PreemptionCheck, transition guard, min_token_threshold, spatial
boundary).  The gate refuses to build if any continuous transition relies on
such a guard, so the engine falls back to the formalism-faithful Python path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.engine.acceleration.ode_system import OdeSystemAccelerator


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _make_minimal_continuous():
    """A→B continuous, no guards.  Should accelerate cleanly."""
    model = DocumentModel()

    pa = Place(0, 0, "PA", "A")
    pa.initial_marking = 50.0
    pa.tokens = 50.0
    pa.capacity = 100.0

    pb = Place(100, 0, "PB", "B")
    pb.initial_marking = 0.0
    pb.tokens = 0.0
    pb.capacity = 100.0

    t = Transition.from_dict({
        "id": "T1", "name": "fwd", "x": 50, "y": 0,
        "transition_type": "continuous",
        "properties": {"rate_function": "1.0 * A"},
    })

    a1 = Arc.from_dict(
        {"id": "A1", "source_id": "PA", "target_id": "T1",
         "arc_type": "normal", "weight": 1.0},
        {"PA": pa, "PB": pb}, {"T1": t},
    )
    a2 = Arc.from_dict(
        {"id": "A2", "source_id": "T1", "target_id": "PB",
         "arc_type": "normal", "weight": 1.0},
        {"PA": pa, "PB": pb}, {"T1": t},
    )

    model.places = [pa, pb]
    model.transitions = [t]
    model.arcs = [a1, a2]
    return model


def _add_inhibitor(model):
    """Add an inhibitor arc from a third place to T1."""
    pc = Place(50, 100, "PC", "C")
    pc.initial_marking = 0.0
    pc.tokens = 0.0
    pc.capacity = 100.0
    model.places.append(pc)

    t1 = next(t for t in model.transitions if t.id == "T1")
    inh = InhibitorArc(pc, t1, "AINH", "AINH", weight=10.0)
    model.arcs.append(inh)
    return model


def _add_nontrivial_guard(model):
    """Set a non-trivial string guard on T1."""
    t1 = next(t for t in model.transitions if t.id == "T1")
    t1.set_guard("A > 5.0")
    return model


def _add_min_token_threshold(model):
    t1 = next(t for t in model.transitions if t.id == "T1")
    t1.properties = dict(getattr(t1, "properties", {}))
    t1.properties["min_token_threshold"] = 1.0
    return model


def _add_signal_flow_with_theta(model):
    """Add a signal_flow arc from a regulatory ⬡ place with θ_eff > 0."""
    ps = Place(150, 0, "PS", "Regulator")
    ps.is_signal_place = True
    # keep regulatory (default) — non-spatial → also triggers preemption check
    ps.initial_marking = 5.0
    ps.tokens = 5.0
    ps.capacity = 100.0
    model.places.append(ps)

    t1 = next(t for t in model.transitions if t.id == "T1")
    sfa = SignalFlowArc(ps, t1, "ASF", "ASF", weight=1.0)
    sfa.suppression_epsilon = 0.5  # ε > 0 → θ_eff > 0
    sfa.michaelis_K = 1.0
    sfa.hill_n = 1.0
    model.arcs.append(sfa)
    return model


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

class TestAcceleratorGate:
    """Phase-1 audit refuses to build when formalism guards would be ignored."""

    def test_clean_model_builds(self):
        """Baseline: no guards → accelerator builds successfully."""
        model = _make_minimal_continuous()
        accel = OdeSystemAccelerator(model, lambda t: None)
        assert accel.build(), f"Clean model should build: {accel.build_error}"
        assert not accel._unsafe_reasons

    def test_inhibitor_arc_refused(self):
        model = _add_inhibitor(_make_minimal_continuous())
        accel = OdeSystemAccelerator(model, lambda t: None)
        assert not accel.build()
        err = (accel.build_error or "").lower()
        assert "inhibitor" in err

    def test_nontrivial_guard_refused(self):
        model = _add_nontrivial_guard(_make_minimal_continuous())
        accel = OdeSystemAccelerator(model, lambda t: None)
        assert not accel.build()
        err = (accel.build_error or "").lower()
        assert "guard" in err

    def test_min_token_threshold_refused(self):
        model = _add_min_token_threshold(_make_minimal_continuous())
        accel = OdeSystemAccelerator(model, lambda t: None)
        assert not accel.build()
        err = (accel.build_error or "").lower()
        assert "min_token_threshold" in err

    def test_signal_flow_theta_eff_refused(self):
        """signal_flow arc with ε > 0 (⇒ θ_eff > 0) is refused.

        Also triggers PreemptionCheck refusal (regulatory signal predecessor).
        Either reason is acceptable.
        """
        model = _add_signal_flow_with_theta(_make_minimal_continuous())
        accel = OdeSystemAccelerator(model, lambda t: None)
        assert not accel.build()
        err = (accel.build_error or "").lower()
        assert ("θ_eff" in err) or ("preemption" in err) or ("signal_flow" in err)

    def test_trivial_guard_values_accepted(self):
        """Guards equal to 1, True, "1", "true", "" are trivial."""
        from shypn.engine.acceleration.ode_system import _is_trivial_guard
        for g in (None, True, 1, 1.0, "", "1", "True", "true ", " 1 "):
            assert _is_trivial_guard(g), f"{g!r} should be trivial"
        for g in (False, 0, "0", "A > 5", "lambda: True", {"expr": "x"}):
            assert not _is_trivial_guard(g), f"{g!r} should NOT be trivial"


@pytest.mark.skipif(
    not Path(
        "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3_p8.shy"
    ).exists(),
    reason="canabidiol v3_p8 model not present in this checkout",
)
class TestRealModel:
    """The canabidiol v3_p8 model uses signal_flow + signal hierarchy."""

    def test_v3_p8_refused(self):
        model_path = (
            "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3_p8.shy"
        )
        model = DocumentModel.load_from_file(model_path)

        accel = OdeSystemAccelerator(model, lambda t: None)
        assert not accel.build(), (
            "v3_p8 has non-spatial signal_flow inputs — accelerator must refuse"
        )
        err = accel.build_error or ""
        # Expect at least one of the structural-guard reasons
        assert any(
            k in err.lower()
            for k in ("preemption", "θ_eff", "signal_flow", "inhibitor")
        ), f"Unexpected refusal reason: {err}"
