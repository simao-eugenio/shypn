#!/usr/bin/env python3
"""
Refactor canabidiol-phase-0-v2.shy → canabidiol-q1-testable.shy.

Goal: make the Q1 wet-lab anchor (CBD IC50 ≈ 1 µM on NFκB; Kozela 2010,
Esposito 2006) empirically testable. v1/v2 reproduced this. v3-phase-0-v2
has the *topology* (GPR3, Gamma_Secretase, PPARg_active, APP, full
Aβ→IKK→NFκB cascade) but the cascade never ignites because:

  - Abeta_Monomer.initial_marking = 0.05 (T4 aggregation rate
    0.05 * Aβ² ≈ 1.25e-4/s, dominated by clearance)
  - Disease install events deliver +0.125 token/DSEV unit
    (Aβ_Mono), +12.5 token/DSEV (NFkB_p65) — both verified
    sub-threshold by phase-2 (run_20260428_232310, bit-identical
    downstream across 2000× sweep)

Patch (Pattern-A clean — events read only DISEASE_SEVERITY ▢):

  1. Abeta_Monomer.initial_marking 0.05 → 0.5
     (so even at DSEV=0 the T4 quadratic can fire: rate ≈ 0.0125/s,
     comparable to T25 clearance ≈ 0.021/s — keeps healthy baseline
     bounded but no longer at noise floor).

  2. Resize disease-install events so DSEV=1 produces a
     self-sustaining diseased fixed point above the aggregation
     ignition threshold:

        Abeta_Monomer:  +0.125  →  +5.0   per DSEV
        NFkB_p65:       +12.5   →  +20.0
        ROS:            +2.0    →  +5.0
        Microglia_M1:   +10.0   →  +15.0
        Microglia_M2:   −7.5    →  −10.0
        Neuron_Health:  −2.5    →  −5.0
        Abeta_Oligomer: +7.25   →  +2.0   (downsized — let aggregation
                                            produce most of it)

     All other install deltas left unchanged (cytokines, Glutathione,
     APP_mRNA, Plaque). Pattern A preserved: every RHS still reads
     only DISEASE_SEVERITY.

Acceptance criterion (to be tested by sweep, not by this patch):
  - At DSEV = 0.5, CBD = 0:  NFkB_p65 endpoint > 50  (inflammation ignites)
  - At DSEV = 0.5, CBD = 1:  NFkB_p65 endpoint < 5   (CBD IC50 holds)

Failure mode for this patch (silent no-op): if Abeta_Monomer M0 lands
on top-level but the loader prefers a properties.initial_marking,
the change is ignored. Loader audit (place.py::Place.from_dict):
  initial_marking is read top-level only, with legacy 'marking'
  fallback. Roundtrip assertion below verifies post-write.
"""

import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "models" / "canabidiol-phase-0-v2.shy"
DST  = ROOT / "models" / "canabidiol-q1-testable.shy"

# ---- Patch payload ----

NEW_ABETA_MONO_M0 = 0.5

EVENT_RESIZE = {
    "evt_install_Abeta_Monomer":   ("Abeta_Monomer",  "Abeta_Monomer + DISEASE_SEVERITY * 5.0000"),
    "evt_install_Abeta_Oligomer":  ("Abeta_Oligomer", "Abeta_Oligomer + DISEASE_SEVERITY * 2.0000"),
    "evt_install_NFkB_p65":        ("NFkB_p65",       "NFkB_p65 + DISEASE_SEVERITY * 20.0000"),
    "evt_install_ROS":             ("ROS",            "ROS + DISEASE_SEVERITY * 5.0000"),
    "evt_install_Microglia_M1":    ("Microglia_M1",   "Microglia_M1 + DISEASE_SEVERITY * 15.0000"),
    "evt_install_Microglia_M2":    ("Microglia_M2",   "Microglia_M2 + DISEASE_SEVERITY * -10.0000"),
    "evt_install_Neuron_Health":   ("Neuron_Health",  "Neuron_Health + DISEASE_SEVERITY * -5.0000"),
}

# ---- Apply ----

def main() -> int:
    src_bytes = SRC.read_bytes()
    src_sha   = hashlib.sha256(src_bytes).hexdigest()
    print(f"src: {SRC.name}  sha256={src_sha[:12]}…")
    m = json.loads(src_bytes)

    # 1. Bump Abeta_Monomer initial marking (top-level — loader scope).
    abeta_mono = next(p for p in m["places"] if p["name"] == "Abeta_Monomer")
    old_m0 = abeta_mono.get("initial_marking", 0.0)
    abeta_mono["initial_marking"] = NEW_ABETA_MONO_M0
    print(f"  Abeta_Monomer.initial_marking: {old_m0} → {NEW_ABETA_MONO_M0}")
    # Strip any legacy 'marking' or 'tokens' that could shadow on re-load.
    abeta_mono.pop("marking", None)
    abeta_mono.pop("tokens", None)

    # 2. Resize disease-install events.
    by_name = {e["name"]: e for e in m.get("events", [])}
    for ev_name, (target, new_rhs) in EVENT_RESIZE.items():
        if ev_name not in by_name:
            print(f"  WARNING: event {ev_name} not found; skipping", file=sys.stderr)
            continue
        ev = by_name[ev_name]
        # Pattern A audit: RHS must only reference target + ▢ params.
        # Use word-boundary regex to avoid substring false positives
        # (e.g. "Abeta" matching "Abeta_Monomer").
        import re as _re
        forbidden = ["NFkB_p65", "ROS", "Abeta_Monomer", "Abeta_Oligomer",
                     "Abeta_Plaque", "Microglia_M1", "Microglia_M2",
                     "Neuron_Health", "Glutathione", "TNFa",
                     "IL1b", "IL6", "COX2", "APP_mRNA",
                     "Temperature_factor", "Age_factor",
                     "pH_acidosis", "pH_neutrality"]
        bad = [tok for tok in forbidden
               if tok != target
               and _re.search(rf"\b{_re.escape(tok)}\b", new_rhs)]
        assert not bad, f"Pattern A violation in {ev_name}: RHS reads non-target state place(s) {bad}"
        old_rhs = ev["assignments"].get(target, "<missing>")
        ev["assignments"] = {target: new_rhs}
        print(f"  {ev_name:<30} {target}: {old_rhs!r} → {new_rhs!r}")

    # ---- Write ----
    DST.write_text(json.dumps(m, indent=2))
    dst_bytes = DST.read_bytes()
    dst_sha   = hashlib.sha256(dst_bytes).hexdigest()
    print(f"dst: {DST.name}  sha256={dst_sha[:12]}…")

    # ---- Roundtrip validation ----
    m2 = json.loads(dst_bytes)

    # 1. Aβ_Mono initial_marking lands at the loader's read scope.
    abeta = next(p for p in m2["places"] if p["name"] == "Abeta_Monomer")
    assert abeta["initial_marking"] == NEW_ABETA_MONO_M0, \
        f"Aβ_Mono initial_marking did not persist: {abeta.get('initial_marking')}"
    assert "marking" not in abeta and "tokens" not in abeta, \
        "Legacy marking/tokens field reintroduced — would shadow initial_marking"

    # 2. Each resized event's RHS is exactly what we set.
    by_name2 = {e["name"]: e for e in m2.get("events", [])}
    for ev_name, (target, expected_rhs) in EVENT_RESIZE.items():
        if ev_name not in by_name2:
            continue
        got = by_name2[ev_name]["assignments"].get(target)
        assert got == expected_rhs, \
            f"Event {ev_name} did not roundtrip: got {got!r}"

    # 3. Pattern A holistic re-check on every event after write.
    state_places = {p["name"] for p in m2["places"]
                    if not p.get("is_parameter_place")}
    for ev in m2.get("events", []):
        for tgt, rhs in ev.get("assignments", {}).items():
            for tok in state_places - {tgt}:
                # crude word-boundary check: allow substrings inside other identifiers
                import re
                if re.search(rf"\b{re.escape(tok)}\b", rhs):
                    print(f"  Pattern-A NOTICE: {ev['name']} target={tgt} RHS reads {tok}",
                          file=sys.stderr)

    print()
    print("✓ all roundtrip assertions passed.")
    print(f"  {len(m2['places'])}P / {len(m2['transitions'])}T / "
          f"{len(m2['arcs'])}A / {len(m2.get('events', []))} events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
