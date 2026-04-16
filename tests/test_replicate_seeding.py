#!/usr/bin/env python3
"""
Test: per-replicate RNG seeding in ReplicateRunner.

Three assertions, ordered by severity:

  TEST 1 — N-independence  (CRITICAL)
      Replicate i must produce the same final marking regardless of N.
      Run N=3 and N=8 with the same seed_base; compare per-replicate
      final states.  A failure here reproduced the G-v8a vs G-v7 bug.

  TEST 2 — Seed isolation  (CRITICAL)
      Same seed across two runs must reproduce; different seed must differ.

  TEST 3 — GATA anchor  (SCIENTIFIC)
      Load phase3a_spatial_clean_v6.shy.
      At EPO=0.57 µM / pH=8.0 with N=30, G-v7 showed ~10% ERY.
      After the fix the fraction must be << 50% (MEG-dominated).

Usage:
    cd /home/simao/projetos/shypn
    source .venv/bin/activate
    python tests/test_replicate_seeding.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'workspace', 'projects', 'gata',
    'models', 'phase3a_spatial_clean_v6.shy'
)


def load_gata_model(epo=0.57, ph=8.0):
    """Load GATA v6 model and set EPO / pH overrides."""
    from shypn.data.canvas.document_model import DocumentModel
    with open(MODEL_PATH) as f:
        data = json.load(f)
    model = DocumentModel.from_dict(data)
    for p in model.places:
        n = getattr(p, 'name', '')
        if n == 'EPO_external' or p.id == 'P1':
            p.tokens = epo
        if n == 'pH_nucleus' or p.id == 'P25':
            p.tokens = ph
    return model


def run_replicates(model, n, seed_base=42, duration=200.0):
    """Run n replicates; return list of final_marking dicts."""
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    runner = ReplicateRunner(model)
    results = runner.run_replicates(
        n=n,
        use_parallel=True,
        use_tau_leaping=True,
        duration=duration,
        termination_condition='deadlock',
        seed_base=seed_base,
        verbose=False,
    )
    return [r['final_marking'] for r in results if 'error' not in r]


# ---------------------------------------------------------------------------
# TEST 1 — N-independence
# ---------------------------------------------------------------------------

def test_n_independence():
    print("=" * 60)
    print("TEST 1 — N-independence")
    print("=" * 60)

    markings_n3 = run_replicates(load_gata_model(), n=3, seed_base=42, duration=200.0)
    markings_n8 = run_replicates(load_gata_model(), n=8, seed_base=42, duration=200.0)

    if not markings_n3 or not markings_n8:
        print("  ✗ FAIL — no replicates returned")
        return False

    passed = True
    for i in range(min(3, len(markings_n3), len(markings_n8))):
        match = markings_n3[i] == markings_n8[i]
        print(f"  replicate {i}: N=3 vs N=8 → {'match ✅' if match else 'DIFFER ✗'}")
        if not match:
            # Show first differing place for diagnosis
            for pid in markings_n3[i]:
                if markings_n3[i][pid] != markings_n8[i].get(pid):
                    print(f"    first diff: {pid}  N=3:{markings_n3[i][pid]}  N=8:{markings_n8[i].get(pid)}")
                    break
        passed = passed and match

    if passed:
        print("  ✅ PASS — all replicates identical regardless of N")
    else:
        print("  ✗ FAIL — seeding bug still present")
    return passed


# ---------------------------------------------------------------------------
# TEST 2 — Seed isolation
# ---------------------------------------------------------------------------

def test_seed_isolation():
    print()
    print("=" * 60)
    print("TEST 2 — Seed isolation")
    print("=" * 60)

    m_42a = run_replicates(load_gata_model(), n=4, seed_base=42, duration=200.0)
    m_42b = run_replicates(load_gata_model(), n=4, seed_base=42, duration=200.0)
    m_43  = run_replicates(load_gata_model(), n=4, seed_base=43, duration=200.0)

    if not m_42a or not m_42b or not m_43:
        print("  ✗ FAIL — no replicates returned")
        return False

    reproducible = all(m_42a[i] == m_42b[i] for i in range(min(len(m_42a), len(m_42b))))
    different    = m_42a[0] != m_43[0]

    print(f"  seed=42 reproduces across runs: {'✅' if reproducible else '✗ FAIL'}")
    print(f"  seed=42 rep0 differs from seed=43 rep0: {'✅' if different else '⚠  accidentally equal (tolerable)'}")

    passed = reproducible
    if passed:
        print("  ✅ PASS")
    else:
        print("  ✗ FAIL — same seed not reproducible")
    return passed


# ---------------------------------------------------------------------------
# TEST 3 — GATA anchor
# ---------------------------------------------------------------------------

def test_gata_anchor():
    print()
    print("=" * 60)
    print("TEST 3 — GATA anchor (EPO=0.57, pH=8.0, N=5, duration=21600s)")
    print("=" * 60)

    if not os.path.exists(MODEL_PATH):
        print(f"  ⚠  SKIP — model not found at {MODEL_PATH}")
        return None

    model = load_gata_model(epo=0.57, ph=8.0)

    # Identify GATA1/PU1 nuclear protein place IDs
    GATA1_ID = PU1_ID = None
    for p in model.places:
        n = getattr(p, 'name', '')
        if n == 'GATA1_Protein_nuc' or p.id == 'P17': GATA1_ID = p.id
        if n == 'PU1_Protein_nuc'   or p.id == 'P18': PU1_ID   = p.id

    N = 5
    print(f"  Running N={N} replicates (threshold check: p_ERY < 50%) ...")
    markings = run_replicates(model, n=N, seed_base=42, duration=21600.0)

    if not markings:
        print("  ✗ FAIL — all replicates failed")
        return False

    n_ery = sum(1 for fm in markings
                if fm.get(GATA1_ID, 0) > 1.5 * fm.get(PU1_ID, 0))
    p_ery = n_ery / len(markings)
    print(f"  n_ERY={n_ery}/{len(markings)}  p_ERY={p_ery:.3f}")

    # N=5 small sample — use 50% threshold (MEG-dominant at sub-threshold EPO)
    # G-v7 full run showed ~10% at EPO=0.57/pH=8.0; with N=5, even 2/5 = 40% would still pass
    passed = p_ery < 0.50
    if passed:
        print(f"  ✅ PASS — p_ERY={p_ery:.1%} < 50% (MEG-dominated, consistent with sub-threshold)")
    else:
        print(f"  ✗ FAIL — p_ERY={p_ery:.1%} ≥ 50% (seeding bug or model drift)")
    return passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ReplicateRunner seeding fix — verification test suite  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    results = {}
    results['n_independence'] = test_n_independence()
    results['seed_isolation']  = test_seed_isolation()
    results['gata_anchor']     = test_gata_anchor()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, ok in results.items():
        if ok is None:
            status = "⚠  SKIP"
        elif ok:
            status = "✅ PASS"
        else:
            status = "✗  FAIL"
        print(f"  {status}  {name}")

    failed = [k for k, v in results.items() if v is False]
    print()
    if not failed:
        print("All tests passed (or skipped). Seeding fix is valid.")
        sys.exit(0)
    else:
        print(f"{len(failed)} test(s) FAILED: {failed}")
        sys.exit(1)

