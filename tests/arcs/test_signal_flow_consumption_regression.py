#!/usr/bin/env python3
"""Regression: signal_flow arcs consume tokens in every firing engine.

Per the 13-tuple Bio-PN formalism (Simão 2025) and SignalFlowArc docstring,
signal_flow arcs are dual-role:

  1. Token flow — consume Ws tokens from source, produce Ws at target
     (mass-balanced, identical stoichiometry to a normal arc).
  2. Vertical information channel — visible to the signal hierarchy.

Only `test` arcs are non-consuming. signal_flow MUST consume in every
firing engine: continuous (RK4 integrate_step), stochastic burst, immediate,
and τ-leaping multi-firing.

Historical bug class: gates that read `properties['kind']` (legacy alias)
or that special-case anything other than `arc_type == 'test'` silently
drop signal_flow consumption when the .shy file omits the `kind` legacy
key, breaking mass balance for the signal place.

Topology under test:
    P_sig  --[signal_flow, w=Ws]--> T  --[normal, w=1]--> P_out
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.engine.continuous_behavior import ContinuousBehavior
from shypn.engine.immediate_behavior import ImmediateBehavior
from shypn.engine.stochastic_behavior import StochasticBehavior


# ─────────────────────────────────────────────────────────────────────────
# Fixture builder
# ─────────────────────────────────────────────────────────────────────────

class _MiniModel:
    """Minimal duck-typed model for behavior classes that only need
    .places, .transitions, .arcs."""

    def __init__(self, places, transitions, arcs):
        self.places = places
        self.transitions = transitions
        self.arcs = arcs


def _build_signal_flow_topology(
    transition_type: str,
    rate_function: str = "1.0",
    signal_initial: float = 100.0,
    signal_weight: float = 1.0,
):
    """Build P_sig --[signal_flow, w]--> T --[normal, 1]--> P_out."""
    p_sig = Place(x=0, y=0, id="P1", name="P1", label="Signal")
    p_sig.is_signal_place = True
    p_sig.signal_type = None  # regulatory; not SPATIAL
    p_sig.tokens = float(signal_initial)
    p_sig.initial_marking = float(signal_initial)

    p_out = Place(x=200, y=0, id="P2", name="P2", label="Out")
    p_out.tokens = 0.0
    p_out.initial_marking = 0.0

    t = Transition(x=100, y=0, id="T1", name="T1", label="Reaction")
    t.transition_type = transition_type
    t.rate_function = rate_function
    # Stochastic transitions sample bursts; pin a deterministic burst for the test.
    if transition_type == 'stochastic':
        t.rate = 1.0

    arc_in = SignalFlowArc(p_sig, t, "A1", "A1", weight=signal_weight)
    arc_out = Arc(t, p_out, "A2", "A2", weight=1.0)

    model = _MiniModel([p_sig, p_out], [t], [arc_in, arc_out])
    return model, p_sig, p_out, t, arc_in, arc_out


# ─────────────────────────────────────────────────────────────────────────
# 1. Continuous integrate_step (RK4)
# ─────────────────────────────────────────────────────────────────────────

def test_signal_flow_consumed_in_continuous_integrate_step():
    """Continuous transitions must drain signal_flow input over RK4 steps."""
    model, p_sig, p_out, t, arc_in, arc_out = _build_signal_flow_topology(
        transition_type='continuous',
        rate_function="1.0",   # constant unit rate
        signal_initial=100.0,
        signal_weight=2.0,     # Ws = 2 tokens per unit flow
    )
    behavior = ContinuousBehavior(t, model)
    input_arcs = [arc_in]
    output_arcs = [arc_out]

    initial_sig = p_sig.tokens
    initial_out = p_out.tokens

    # Integrate 10 steps of dt=0.1 → expected flow ≈ rate * total_dt = 1.0 * 1.0 = 1.0
    # → consumed_sig = Ws * 1.0 = 2.0; produced_out = 1.0 * 1.0 = 1.0
    for _ in range(10):
        ok, _ = behavior.integrate_step(0.1, input_arcs, output_arcs)
        assert ok, "integrate_step failed for signal_flow input"

    consumed_sig = initial_sig - p_sig.tokens
    produced_out = p_out.tokens - initial_out

    assert consumed_sig == pytest.approx(2.0, abs=1e-6), (
        f"signal_flow NOT consumed in continuous mode: "
        f"signal place lost {consumed_sig}, expected 2.0"
    )
    assert produced_out == pytest.approx(1.0, abs=1e-6)


# ─────────────────────────────────────────────────────────────────────────
# 2. Continuous predict_flow (diagnostic path)
# ─────────────────────────────────────────────────────────────────────────

def test_signal_flow_included_in_continuous_predict_flow():
    """Diagnostic predict_flow must report signal_flow consumption."""
    model, p_sig, p_out, t, arc_in, arc_out = _build_signal_flow_topology(
        transition_type='continuous',
        rate_function="1.0",
        signal_weight=1.5,
    )
    behavior = ContinuousBehavior(t, model)

    pred = behavior.predict_flow(dt=1.0)

    assert p_sig.id in pred['consumed'], (
        "predict_flow omitted signal_flow input from consumed map; "
        "this is the legacy `kind == 'normal'` gate bug."
    )
    assert pred['consumed'][p_sig.id] == pytest.approx(1.5, abs=1e-6)


# ─────────────────────────────────────────────────────────────────────────
# 3. Stochastic burst fire
# ─────────────────────────────────────────────────────────────────────────

def test_signal_flow_consumed_in_stochastic_fire():
    """Stochastic transitions must drain signal_flow with burst multiplier."""
    model, p_sig, p_out, t, arc_in, arc_out = _build_signal_flow_topology(
        transition_type='stochastic',
        rate_function="1.0",
        signal_initial=100.0,
        signal_weight=3.0,
    )
    behavior = StochasticBehavior(t, model)

    # Set deterministic state: enable now, force burst=4, force scheduled
    # fire time into the past so the timing-window check passes.
    now = behavior._get_current_time()
    behavior.set_enablement_time(now - 10.0)
    behavior._sampled_burst = 4
    behavior._scheduled_fire_time = now - 1.0

    initial_sig = p_sig.tokens
    initial_out = p_out.tokens

    ok, details = behavior.fire([arc_in], [arc_out])
    assert ok, f"stochastic fire failed: {details}"

    consumed_sig = initial_sig - p_sig.tokens
    produced_out = p_out.tokens - initial_out

    # burst=4, Ws=3 → consumed=12; output weight=1 → produced=4
    assert consumed_sig == pytest.approx(12.0, abs=1e-9), (
        f"signal_flow NOT consumed in stochastic burst: "
        f"got {consumed_sig}, expected 12.0 (=burst·Ws)"
    )
    assert produced_out == pytest.approx(4.0, abs=1e-9)


# ─────────────────────────────────────────────────────────────────────────
# 4. Immediate fire
# ─────────────────────────────────────────────────────────────────────────

def test_signal_flow_consumed_in_immediate_fire():
    """Immediate transitions must drain signal_flow on each firing."""
    model, p_sig, p_out, t, arc_in, arc_out = _build_signal_flow_topology(
        transition_type='immediate',
        rate_function="1.0",
        signal_initial=100.0,
        signal_weight=2.0,
    )
    behavior = ImmediateBehavior(t, model)

    initial_sig = p_sig.tokens

    ok, details = behavior.fire([arc_in], [arc_out])
    assert ok, f"immediate fire failed: {details}"

    consumed_sig = initial_sig - p_sig.tokens
    assert consumed_sig == pytest.approx(2.0, abs=1e-9), (
        f"signal_flow NOT consumed in immediate fire: "
        f"got {consumed_sig}, expected 2.0"
    )


# ─────────────────────────────────────────────────────────────────────────
# 5. τ-leaping multi-firing path
# ─────────────────────────────────────────────────────────────────────────

def test_signal_flow_consumed_in_tau_leaping_multi_firing():
    """τ-leaping `_fire_transition_multiple` must consume signal_flow.

    This is the historic bug site: the gate
        if kind != 'normal' or arc_type in ('inhibitor', 'test'): continue
    silently dropped signal_flow consumption when properties['kind'] was
    absent OR when the arc_type was inhibitor — both formalism violations.
    """
    from shypn.engine.simulation.tau_leaping.tau_leaping_engine import (
        TauLeapingEngine,
    )

    model, p_sig, p_out, t, arc_in, arc_out = _build_signal_flow_topology(
        transition_type='stochastic',
        rate_function="1.0",
        signal_initial=1000.0,
        signal_weight=2.0,
    )
    engine = TauLeapingEngine()

    initial_sig = p_sig.tokens
    initial_out = p_out.tokens

    consumed_map, produced_map = engine._fire_transition_multiple(
        transition=t,
        input_arcs=[arc_in],
        output_arcs=[arc_out],
        num_firings=7,
        behavior=None,  # not used by current implementation
    )

    consumed_sig = initial_sig - p_sig.tokens
    produced_out = p_out.tokens - initial_out

    # 7 firings × Ws=2 = 14 consumed; 7 × 1 = 7 produced
    assert consumed_sig == pytest.approx(14.0, abs=1e-9), (
        f"signal_flow NOT consumed in τ-leaping: got {consumed_sig}, "
        f"expected 14.0 (=N·Ws)"
    )
    assert produced_out == pytest.approx(7.0, abs=1e-9)
    assert consumed_map.get(p_sig.id) == pytest.approx(14.0, abs=1e-9), (
        "τ-leaping consumed_map omitted signal_flow contribution"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. τ-leaping must STILL skip test arcs (regression guard for over-eager fix)
# ─────────────────────────────────────────────────────────────────────────

def test_test_arcs_remain_non_consuming_in_tau_leaping():
    """τ-leaping fix must not regress: test arcs stay non-consuming."""
    from shypn.netobjs.test_arc import TestArc
    from shypn.engine.simulation.tau_leaping.tau_leaping_engine import (
        TauLeapingEngine,
    )

    p_cat = Place(x=0, y=0, id="P1", name="P1", label="Catalyst")
    p_cat.tokens = 5.0
    p_sub = Place(x=50, y=0, id="P2", name="P2", label="Substrate")
    p_sub.tokens = 100.0
    p_out = Place(x=200, y=0, id="P3", name="P3", label="Out")
    p_out.tokens = 0.0

    t = Transition(x=100, y=0, id="T1", name="T1", label="R")
    t.transition_type = 'stochastic'
    t.rate_function = "1.0"

    a_test = TestArc(p_cat, t, "A1", "A1", weight=1.0)
    a_in = Arc(p_sub, t, "A2", "A2", weight=1.0)
    a_out = Arc(t, p_out, "A3", "A3", weight=1.0)

    engine = TauLeapingEngine()
    engine._fire_transition_multiple(
        transition=t,
        input_arcs=[a_test, a_in],
        output_arcs=[a_out],
        num_firings=10,
        behavior=None,
    )

    assert p_cat.tokens == pytest.approx(5.0, abs=1e-9), (
        f"test arc was consumed in τ-leaping (regression): "
        f"P_cat went from 5.0 to {p_cat.tokens}"
    )
    assert p_sub.tokens == pytest.approx(90.0, abs=1e-9)
    assert p_out.tokens == pytest.approx(10.0, abs=1e-9)


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-v']))
