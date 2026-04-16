#!/usr/bin/env python3
"""Test all transition types using the minimal P1→T1→P2 model (p-t-p.shy).

Verifies that the hybrid enablement fix (floor(tokens) for discrete transitions)
allows immediate, timed, stochastic, and adaptive transitions to fire alongside
continuous ones, including when place tokens are fractional concentrations.

Model: workspace/projects/gata/models/p-t-p.shy
  P1 (250 tokens) --[A1]--> T1 --[A2]--> P2 (0 tokens)

Tests:
  1. continuous  — ODE integration; P2 gains tokens every step
  2. immediate   — fires on step 1; discrete integer transfer
  3. timed       — fires after timing window [0, ∞]; behaves like immediate
  4. stochastic  — fires after Exp(rate) delay; fires within test window
  5. adaptive    — auto-selects mode; with 250 tokens picks continuous

All tests are run twice per type: once with integer ICs (P1=250, classic PN)
and once with fractional ICs (P1=2.7, SHPN concentration scale) to exercise
the floor() enablement path that was the root cause.
"""

import sys
import os
import math
import random

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, 'src'))

MODEL_PATH = os.path.join(
    REPO_ROOT, 'workspace', 'projects', 'gata', 'models', 'p-t-p.shy'
)

# ──────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────
from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⚠️  SKIP"

results: list[dict] = []


def load_fresh_model(p1_tokens: float = 250.0) -> DocumentModel:
    """Load p-t-p.shy and override P1 tokens to the requested value."""
    doc = DocumentModel.load_from_file(MODEL_PATH)
    p1 = next(p for p in doc.places if p.id == 'P1')
    p2 = next(p for p in doc.places if p.id == 'P2')
    p1.tokens = p1_tokens
    p1.initial_marking = p1_tokens
    p2.tokens = 0.0
    p2.initial_marking = 0.0
    return doc


def fresh_controller(doc: DocumentModel, dt: float = 0.1) -> SimulationController:
    """Create a SimulationController with fixed manual dt and disabled verbosity."""
    ctrl = SimulationController(doc, verbose=False)
    ctrl.settings.dt_auto = False
    ctrl.settings.dt_manual = dt
    # Ensure a finite duration so is_simulation_complete() never trips early
    ctrl.settings.duration = 1_000_000
    return ctrl


def run_steps(ctrl: SimulationController, n: int, dt: float = 0.1) -> tuple[float, float]:
    """Run n simulation steps and return (P1_tokens, P2_tokens) after."""
    p1 = next(p for p in ctrl.model.places if p.id == 'P1')
    p2 = next(p for p in ctrl.model.places if p.id == 'P2')
    ctrl._update_enablement_states()
    for _ in range(n):
        ctrl.step(dt)
    return p1.tokens, p2.tokens


def record(test_name: str, p1_init: float, p1_after: float, p2_after: float,
           expectation: str, passed: bool, note: str = "") -> None:
    status = PASS if passed else FAIL
    results.append({
        'name': test_name,
        'p1_init': p1_init,
        'p1_after': p1_after,
        'p2_after': p2_after,
        'status': status,
        'expectation': expectation,
        'note': note,
    })
    print(
        f"  {status}  P1: {p1_init:.2f} → {p1_after:.4f}   "
        f"P2: 0.00 → {p2_after:.4f}   [{expectation}]"
        + (f"  ({note})" if note else "")
    )


# ──────────────────────────────────────────────────────────────
# Test functions
# ──────────────────────────────────────────────────────────────

def test_continuous(p1_init: float) -> None:
    """Continuous transition: ODE integration, works with any positive float."""
    doc = load_fresh_model(p1_init)
    t1 = doc.transitions[0]
    t1.transition_type = 'continuous'
    # Make sure a rate_function exists
    t1._properties['rate_function'] = '1'

    ctrl = fresh_controller(doc, dt=0.1)
    p1_after, p2_after = run_steps(ctrl, 50, dt=0.1)

    # Continuous: tokens should flow every step; P2 > 0 after 50 steps
    passed = p2_after > 0.0
    record(f"continuous  (P1={p1_init})", p1_init, p1_after, p2_after,
           "P2 > 0 after 50 steps (ODE)", passed)


def test_immediate(p1_init: float) -> None:
    """Immediate transition: fires on first step if floor(tokens)>=weight.

    _exhaust_immediate_transitions() fires T1 repeatedly within one step
    until P1 is exhausted (floor=0) or the livelock cap (~21) triggers.
    So exactly floor(min(p1_init, ~21)) tokens move in one step.
    We just assert P2 >= 1 (at least one discrete transfer happened).
    """
    doc = load_fresh_model(p1_init)
    t1 = doc.transitions[0]
    t1.transition_type = 'immediate'

    ctrl = fresh_controller(doc, dt=0.1)
    ctrl._update_enablement_states()
    ctrl.step(0.1)  # one step exhausts immediate queue

    p1 = next(p for p in doc.places if p.id == 'P1')
    p2 = next(p for p in doc.places if p.id == 'P2')

    # P2 must receive at least floor(p1_init) tokens (or livelock cap)
    expected_p2_min = min(math.floor(p1_init), 21)  # livelock cap ~21
    passed = p2.tokens >= expected_p2_min

    record(f"immediate   (P1={p1_init})", p1_init, p1.tokens, p2.tokens,
           f"P2 >= {expected_p2_min} token(s) (floor firing, livelock cap)", passed)


def test_timed(p1_init: float) -> None:
    """Timed transition: fires when elapsed >= earliest (default 0)."""
    doc = load_fresh_model(p1_init)
    t1 = doc.transitions[0]
    t1.transition_type = 'timed'
    # Default earliest=0, latest=inf: fires as soon as enabled
    t1.earliest_time = 0.0
    t1.latest_time = float('inf')

    ctrl = fresh_controller(doc, dt=0.1)
    # Run a few steps; should fire on first eligible step
    p1_after, p2_after = run_steps(ctrl, 5, dt=0.1)

    p1 = next(p for p in doc.places if p.id == 'P1')
    p2 = next(p for p in doc.places if p.id == 'P2')

    passed = p2.tokens >= 1.0  # at least one token transferred

    record(f"timed       (P1={p1_init})", p1_init, p1.tokens, p2.tokens,
           "P2 >= 1 token after ≤5 steps", passed)


def test_stochastic(p1_init: float, seed: int = 42) -> None:
    """Stochastic transition: fires after Exp(rate) delay.

    We use rate=1000 so that:
      - Expected fire time = Exp(1000) ≈ 0.001 s (well within the test window)
      - Propensity = 1000 > critical_threshold=10 → τ-leaping fires directly,
        or exact SSA fires within 1-2 steps (SSA advances 0.001 s per step).
    """
    random.seed(seed)
    doc = load_fresh_model(p1_init)
    t1 = doc.transitions[0]
    t1.transition_type = 'stochastic'
    t1.rate = 1000.0

    ctrl = fresh_controller(doc, dt=0.1)
    p1_after, p2_after = run_steps(ctrl, 200, dt=0.1)

    p1 = next(p for p in doc.places if p.id == 'P1')
    p2 = next(p for p in doc.places if p.id == 'P2')

    # Should have fired at least once: P2 >= 1
    passed = p2.tokens >= 1.0

    record(f"stochastic  (P1={p1_init})", p1_init, p1.tokens, p2.tokens,
           "P2 >= 1 token within 200 steps (rate=1000)", passed,
           note=f"firing_count={t1.firing_count}")


def test_adaptive(p1_init: float) -> None:
    """Adaptive transition: picks continuous or stochastic mode dynamically.

    With 250 tokens (high population) it should choose continuous mode and
    integrate. With fractional tokens (low population) it may choose stochastic,
    but either way tokens should move.
    """
    doc = load_fresh_model(p1_init)
    t1 = doc.transitions[0]
    t1.transition_type = 'adaptive'
    t1._properties['rate_function'] = '1'
    t1.rate = 1.0

    ctrl = fresh_controller(doc, dt=0.1)
    p1_after, p2_after = run_steps(ctrl, 200, dt=0.1)

    p1 = next(p for p in doc.places if p.id == 'P1')
    p2 = next(p for p in doc.places if p.id == 'P2')

    passed = p2.tokens > 0.0

    record(f"adaptive    (P1={p1_init})", p1_init, p1.tokens, p2.tokens,
           "P2 > 0 after 200 steps (mode auto-selected)", passed)


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 70)
    print("Transition-type enablement test — p-t-p.shy")
    print("  Integer ICs (P1=250)  vs  Fractional ICs (P1=2.7)")
    print("=" * 70)

    # ── Integer token counts (classic PN) ──
    print("\n[A] Integer ICs  (P1 = 250 tokens — classic PN regime)")
    print("-" * 70)
    test_continuous(250.0)
    test_immediate(250.0)
    test_timed(250.0)
    test_stochastic(250.0)
    test_adaptive(250.0)

    # ── Fractional concentrations (SHPN / hybrid regime) ──
    # P1 = 2.7 means floor(2.7)=2 ≥ arc_weight(1.0) → should enable discrete transitions
    print("\n[B] Fractional ICs  (P1 = 2.7 µM — hybrid SHPN regime)")
    print("    floor(2.7) = 2 ≥ arc_weight(1.0) → discrete types must enable")
    print("-" * 70)
    test_continuous(2.7)
    test_immediate(2.7)
    test_timed(2.7)
    test_stochastic(2.7)
    test_adaptive(2.7)

    # ── Sub-integer concentrations (should NOT enable discrete) ──
    # P1 = 0.8 means floor(0.8)=0 < arc_weight(1.0) → discrete types must NOT fire
    print("\n[C] Sub-integer ICs  (P1 = 0.8 µM — below one integer unit)")
    print("    floor(0.8) = 0 < arc_weight(1.0) → discrete types must NOT enable")
    print("-" * 70)

    for ttype in ('immediate', 'timed', 'stochastic'):
        doc = load_fresh_model(0.8)
        t1 = doc.transitions[0]
        t1.transition_type = ttype
        if ttype == 'stochastic':
            t1.rate = 1.0
        elif ttype == 'timed':
            t1.earliest_time = 0.0
            t1.latest_time = float('inf')
        ctrl = fresh_controller(doc, dt=0.1)
        p1_after, p2_after = run_steps(ctrl, 50, dt=0.1)
        p2 = next(p for p in doc.places if p.id == 'P2')
        # Expect silence — discrete transition must NOT move tokens
        passed = p2.tokens == 0.0
        record(f"{ttype:<10}  (P1=0.8)", 0.8, p1_after, p2.tokens,
               "P2 stays 0 (cannot enable fractional sub-unit)", passed)

    # Continuous should still work with 0.8 (raw float ODE)
    test_continuous(0.8)

    # ── Summary ──
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    n_pass = sum(1 for r in results if r['status'] == PASS)
    n_fail = sum(1 for r in results if r['status'] == FAIL)
    n_total = len(results)
    for r in results:
        print(f"  {r['status']}  {r['name']:<30}  {r['expectation']}")
    print("-" * 70)
    print(f"  {n_pass}/{n_total} passed", end="")
    if n_fail:
        print(f"  ({n_fail} FAILED)")
    else:
        print("  — all passed")
    print("=" * 70)

    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
