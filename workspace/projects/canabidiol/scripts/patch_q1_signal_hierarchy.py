"""
Patch script: canabidiol-q1-testable.shy
=========================================

Addresses the structural critique on:
  (a) over-use of remote signal sensing -> cascade transitions absent from G_s,
  (b) receptor places metadata claims hierarchy_layer=2/partition='signal'
      but is_signal_place=false (carrier inconsistency).

Fix set (curated, minimum-risk):

  1. Promote receptor places to ⬡ signal carriers, consistent with their own
     metadata (hierarchy_layer=2, partition='signal'):
        - P25 HT1A_active
        - P26 PPARg_active
        - P27 A2A_active
     Sets is_signal_place=true, signal_type='regulatory', blue border.

  2. Convert key cascade-gating test arcs from ⬡ signal sources to
     'signal_flow' arcs so the consumer transitions become vertices of G_s
     and PreemptionCheck activates against an explicit basin floor:
        A25  P30 CBD_intracellular -> T10 (PPARg activation)        L3 -> L2
        A29  P30 CBD_intracellular -> T11 (Nrf2 release modulation) L3 -> L1
        A22  P26 PPARg_active      -> T9  (NFkB inhibition)         L2 -> L1
        A42  P25 HT1A_active       -> T16 (BDNF production)         L2 -> L0
        A49  P26 PPARg_active      -> T18 (M1 -> M2 resolution)     L2 -> ...
        A50  P27 A2A_active        -> T18 (M1 -> M2 resolution)     L2 -> ...
        A95  P9  NFkB_p65          -> T42 (APP transcription)       L1 -> L0

     Weight is small (0.01) so consumption per firing is biologically
     interpretable as "receptor internalization on activation" / "TF
     turnover on promoter binding" without disturbing the rate-driven
     dynamics. Color updated to grey (signal_flow canonical color).

  3. Hub regulator reads (NF-kB p65 -> T7 cytokines, Nrf2_free -> T12
     ARE transcription, etc.) are KEPT as test arcs per the rule
     "Hub regulator with many consumers: F_s only on canonical promoter
     transitions, remote-sense everywhere else".

What is *not* patched here (deliberate, requires deeper redesign):
  - is_source flag on transducer transitions (T7, T8, T10, T12, T15,
    T16, T19, T40, T42, T43): all read inputs through test arcs (which
    do not consume), so the flag is technically defensible as
    "regulated source"; stripping it would require adding substrate
    pools (NTPs, AAs, ATP) which is out of scope for Q1.
  - Receptor desensitization sinks (T32, T33, T34): their rate is
    first-order on the receptor, not signal-regulated. Deferred.
  - Cytokine clearance regulation by PPARg/Nrf2 (T23): not added,
    requires biochemical justification.
  - CBD metabolite biology beyond CYP3A4 sink (T30, T31): out of scope.

Run:
    python workspace/projects/canabidiol/scripts/patch_q1_signal_hierarchy.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_PATH = (
    REPO_ROOT
    / "workspace"
    / "projects"
    / "canabidiol"
    / "models"
    / "canabidiol-q1-testable.shy"
)

# ---- Phase 1: receptor place promotions ----
PROMOTE_TO_SIGNAL = {
    "P25": "HT1A_active",
    "P26": "PPARg_active",
    "P27": "A2A_active",
}

# ---- Phase 2: cascade-gating arc retyping ----
# arc_id -> (source_pid, target_tid, weight, michaelis_K, expected_old_type)
RETYPE_TO_SIGNAL_FLOW = {
    "A25": ("P30", "T10", 0.01, 0.5, "test"),
    "A29": ("P30", "T11", 0.01, 0.5, "test"),
    "A22": ("P26", "T9",  0.01, 0.1, "test"),
    "A42": ("P25", "T16", 0.01, 0.1, "test"),
    "A49": ("P26", "T18", 0.01, 0.1, "test"),
    "A50": ("P27", "T18", 0.01, 0.1, "test"),
    "A95": ("P9",  "T42", 0.01, 0.5, "test"),
}

SIGNAL_FLOW_COLOR = [0.7, 0.7, 0.7]
SIGNAL_BORDER_COLOR = [0.0, 0.0, 1.0]


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"ERROR: model file not found: {MODEL_PATH}", file=sys.stderr)
        return 1

    backup = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".bak")
    shutil.copy2(MODEL_PATH, backup)
    print(f"Backup written: {backup.relative_to(REPO_ROOT)}")

    model = json.loads(MODEL_PATH.read_text())

    # ---------------- Phase 1: place promotions ----------------
    places_by_id = {p["id"]: p for p in model["places"]}
    promoted = []
    for pid, expected_name in PROMOTE_TO_SIGNAL.items():
        if pid not in places_by_id:
            raise SystemExit(f"missing place {pid}")
        p = places_by_id[pid]
        if p["name"] != expected_name:
            raise SystemExit(
                f"{pid}: expected name {expected_name!r}, got {p['name']!r}"
            )
        p["is_signal_place"] = True
        p["signal_type"] = "regulatory"
        p["border_color"] = SIGNAL_BORDER_COLOR
        if p.get("border_width", 3.0) < 4.0:
            p["border_width"] = 4.0
        promoted.append(f"  {pid} {p['name']:<20s} -> ⬡ regulatory")

    # ---------------- Phase 2: arc retyping ----------------
    arcs_by_id = {a["id"]: a for a in model["arcs"]}
    retyped = []
    for aid, (src, tgt, w, K, old_type) in RETYPE_TO_SIGNAL_FLOW.items():
        if aid not in arcs_by_id:
            raise SystemExit(f"missing arc {aid}")
        a = arcs_by_id[aid]
        if a["source_id"] != src or a["target_id"] != tgt:
            raise SystemExit(
                f"{aid}: expected {src}->{tgt}, got "
                f"{a['source_id']}->{a['target_id']}"
            )
        if a["arc_type"] != old_type:
            raise SystemExit(
                f"{aid}: expected old arc_type {old_type!r}, got {a['arc_type']!r}"
            )
        a["arc_type"] = "signal_flow"
        a["weight"] = w
        a["color"] = SIGNAL_FLOW_COLOR
        # SignalFlowArc Γ-tuple defaults: K, n=1, ε=0
        a["michaelis_K"] = K
        a["hill_n"] = 1
        a["suppression_epsilon"] = 0
        # Signal flow arcs are consumptive (mass-carrying)
        a["consumes"] = True
        a["produces"] = False
        # Arrhenius defaults
        a.setdefault("activation_energy", 0)
        a.setdefault("reference_temperature", 298.15)
        # Drop test-arc legacy fields if present
        a.pop("threshold", None)
        # Strip any properties.kind drift to avoid loader confusion
        if "properties" in a and isinstance(a["properties"], dict):
            a["properties"].pop("kind", None)
        retyped.append(
            f"  {aid:<5s} {src}->{tgt}  test -> signal_flow  W={w}  K={K}"
        )

    # ---------------- Write ----------------
    MODEL_PATH.write_text(json.dumps(model, indent=2))

    # ---------------- Roundtrip validation ----------------
    m2 = json.loads(MODEL_PATH.read_text())
    p2 = {p["id"]: p for p in m2["places"]}
    a2 = {a["id"]: a for a in m2["arcs"]}

    for pid in PROMOTE_TO_SIGNAL:
        assert p2[pid]["is_signal_place"] is True, f"{pid} promotion lost"
        assert p2[pid]["signal_type"] == "regulatory", f"{pid} signal_type wrong"

    for aid, (src, tgt, w, K, _old) in RETYPE_TO_SIGNAL_FLOW.items():
        a = a2[aid]
        assert a["arc_type"] == "signal_flow", f"{aid} arc_type lost"
        assert a["source_id"] == src and a["target_id"] == tgt
        assert a["weight"] == w, f"{aid} weight lost"
        assert a["michaelis_K"] == K, f"{aid} michaelis_K lost"
        assert a["color"] == SIGNAL_FLOW_COLOR

    # ---------------- Report ----------------
    print()
    print("Phase 1 -- promoted places to ⬡ signal carriers:")
    for line in promoted:
        print(line)
    print()
    print("Phase 2 -- retyped cascade-gating arcs to signal_flow:")
    for line in retyped:
        print(line)
    print()
    print(
        f"Wrote {MODEL_PATH.relative_to(REPO_ROOT)}  "
        f"(roundtrip validation passed)"
    )
    print(
        "REMINDER: reload the model in the GUI / restart the CLI before "
        "the next sweep -- the engine reads from the in-memory model, "
        "not from disk."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
