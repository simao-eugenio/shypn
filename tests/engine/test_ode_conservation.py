#!/usr/bin/env python3
"""Test that ODE acceleration preserves mass conservation in closed loops.

Regression test for the clamping-induced mass drift bug: when the ODE solver
produces tiny negative overshoots on depleted species, non-negativity clamping
in Place.set_tokens() used to inject mass into the system on every step.

The fix clamps y[] to non-negative inside the generated C RHS so that rates
go to zero naturally as species deplete.  Conservation then emerges from the
topology without external bookkeeping.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.acceleration.ode_system import OdeSystemAccelerator


def _make_two_place_loop(k_fwd: float = 1.0, k_rev: float = 0.5,
                         init_a: float = 80.0, init_b: float = 0.0,
                         capacity: float = 100.0):
    """Build a minimal A ⇌ B closed loop (two continuous transitions).

    T1: A → B  rate = k_fwd * A        (drains A fast)
    T2: B → A  rate = k_rev * B        (returns to A slowly)

    Conservation: A + B = init_a + init_b  (constant).
    """
    model = DocumentModel()

    pa = Place(0, 0, "PA", "A")
    pa.initial_marking = init_a
    pa.tokens = init_a
    pa.capacity = capacity

    pb = Place(100, 0, "PB", "B")
    pb.initial_marking = init_b
    pb.tokens = init_b
    pb.capacity = capacity

    t1 = Transition.from_dict({
        "id": "T1", "name": "fwd", "x": 50, "y": -50,
        "transition_type": "continuous",
        "properties": {"rate_function": f"{k_fwd} * A"},
    })
    t2 = Transition.from_dict({
        "id": "T2", "name": "rev", "x": 50, "y": 50,
        "transition_type": "continuous",
        "properties": {"rate_function": f"{k_rev} * B"},
    })

    a1 = Arc.from_dict(
        {"id": "A1", "source_id": "PA", "target_id": "T1",
         "arc_type": "normal", "weight": 1.0},
        {"PA": pa, "PB": pb}, {"T1": t1, "T2": t2},
    )
    a2 = Arc.from_dict(
        {"id": "A2", "source_id": "T1", "target_id": "PB",
         "arc_type": "normal", "weight": 1.0},
        {"PA": pa, "PB": pb}, {"T1": t1, "T2": t2},
    )
    a3 = Arc.from_dict(
        {"id": "A3", "source_id": "PB", "target_id": "T2",
         "arc_type": "normal", "weight": 1.0},
        {"PA": pa, "PB": pb}, {"T1": t1, "T2": t2},
    )
    a4 = Arc.from_dict(
        {"id": "A4", "source_id": "T2", "target_id": "PA",
         "arc_type": "normal", "weight": 1.0},
        {"PA": pa, "PB": pb}, {"T1": t1, "T2": t2},
    )

    model.places = [pa, pb]
    model.transitions = [t1, t2]
    model.arcs = [a1, a2, a3, a4]
    return model


class TestOdeConservation:
    """Verify that RHS-clamping prevents clamping-induced mass drift."""

    def test_closed_loop_conservation_1000_steps(self):
        """A + B must remain constant over 1000 short ODE steps."""
        model = _make_two_place_loop(k_fwd=2.0, k_rev=0.3,
                                     init_a=80.0, init_b=0.0)
        expected_total = 80.0

        accel = OdeSystemAccelerator(model, lambda t: None)
        assert accel.build(), f"Build failed: {accel.build_error}"

        dt = 0.1
        for step in range(1000):
            t0 = step * dt
            t1 = t0 + dt
            ok = accel.integrate(t0, t1)
            assert ok, f"ODE step {step} failed"

        pa = next(p for p in model.places if p.id == "PA")
        pb = next(p for p in model.places if p.id == "PB")
        total = pa.tokens + pb.tokens
        error = abs(total - expected_total)
        assert error < 0.01, (
            f"Conservation violated: A={pa.tokens:.6f} B={pb.tokens:.6f} "
            f"sum={total:.6f} expected={expected_total} error={error:.6f}"
        )

    def test_asymmetric_rates_fast_drain(self):
        """Conservation holds even when one species is nearly depleted."""
        model = _make_two_place_loop(k_fwd=5.0, k_rev=0.1,
                                     init_a=100.0, init_b=0.0)
        expected_total = 100.0

        accel = OdeSystemAccelerator(model, lambda t: None)
        assert accel.build()

        dt = 0.05
        for step in range(2000):
            accel.integrate(step * dt, (step + 1) * dt)

        pa = next(p for p in model.places if p.id == "PA")
        pb = next(p for p in model.places if p.id == "PB")
        total = pa.tokens + pb.tokens
        assert abs(total - expected_total) < 0.01, (
            f"sum={total:.6f}, expected {expected_total}"
        )

    def test_places_stay_non_negative(self):
        """Token counts never go negative, even with extreme rate asymmetry."""
        model = _make_two_place_loop(k_fwd=10.0, k_rev=0.01,
                                     init_a=100.0, init_b=0.0)
        accel = OdeSystemAccelerator(model, lambda t: None)
        accel.build()

        dt = 0.1
        for step in range(500):
            accel.integrate(step * dt, (step + 1) * dt)
            pa = next(p for p in model.places if p.id == "PA")
            pb = next(p for p in model.places if p.id == "PB")
            assert pa.tokens >= 0, f"PA went negative at step {step}: {pa.tokens}"
            assert pb.tokens >= 0, f"PB went negative at step {step}: {pb.tokens}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
