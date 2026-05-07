#!/usr/bin/env python3
"""Add a minimal energy currency pool to ``canabidiol-q1-testable-pk.shy``.

Rationale
---------
The Q1 model has no `is_energy_place=true` carriers; ATP/NADPH are
implicit in lumped k constants. For a 4-h *acute* horizon that is
defensible, but it eliminates a key AD positive-feedback loop:

    Aβ_Oligomer ↑ → mitochondrial dysfunction → NADPH/PPP capacity ↓
        → Glutathione_Reductase stalls → GSSG ↑, GSH ↓
            → Antioxidant_Scavenging ↓ → ROS ↑
                → more Aβ damage / Nrf2 sequestration

Without an explicit reducing-equivalent pool the Glutathione_Reductase
rate (0.06 · GSSG) is *unbounded by cofactor availability*; it fires
~18 000 times per 4 h regardless of energy state. The current run
shows GSH/GSSG drop 7.0 → 2.66 *despite* infinite NADPH — with the
real loop closed, the collapse should accelerate sharply once Aβ
crosses ~1–2 mM.

Minimal addition (fewest topology changes for maximal effect)
-------------------------------------------------------------
Two new ○ regular places (``is_energy_place=True``), one new
continuous transition, two new arcs, and one rate-function tweak:

    + Place NADPH       (is_energy_place=True, M0=100 mM)
    + Place NADP_plus   (is_energy_place=True, M0=10  mM)
    + Transition NADPH_Regeneration (continuous, PPP-like):
        IN  : NADP_plus  W=1 normal
        OUT : NADPH      W=1 normal
        rate: 1.0 * NADP_plus / (5 + NADP_plus)
              * (1 - 0.5 * Abeta_Oligomer / (50 + Abeta_Oligomer))
              * Temperature_factor
        — Aβ suppresses the PPP via the Hill-suppression term, the
          canonical AD mitochondrial-dysfunction signature.
    ~ Glutathione_Reductase:
        + IN arc NADPH→reductase  W=1 normal
        + OUT arc reductase→NADP_plus  W=1 normal
        rate becomes:
            0.06 * GSSG * NADPH / (50 + NADPH)
          (Michaelis-Menten on NADPH so the reaction stalls when
           the pool is depleted).
    + Test arc (NADPH→NADPH_Regeneration_inhibitor) — none needed; the
      Aβ_Oligomer dependence inside the rate uses Pattern A "remote
      sensing" (Aβ_Oligomer is a regular ○ with its own arcs, so this
      is legal per AGENT_RULES §C9 — no F_t arc to Aβ required, but we
      add a test arc so the engine's PreemptionCheck is informed).

Conservation: NADPH + NADP_plus = 110 mM (initial total) maintained by
the cycle; no source/sink leaks.

Output: ``canabidiol-q1-testable-pk-energy.shy``. The original is
untouched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "models" / "canabidiol-q1-testable-pk.shy"
DST = ROOT / "models" / "canabidiol-q1-testable-pk-energy.shy"


def _next_id(items: list, prefix: str) -> int:
    used = [int(it["id"][len(prefix):])
            for it in items
            if isinstance(it.get("id"), str) and it["id"].startswith(prefix)
            and it["id"][len(prefix):].isdigit()]
    return (max(used) if used else 0) + 1


def _place_template(pid: str, name: str, x: float, y: float,
                    initial_marking: float,
                    is_energy_place: bool = True) -> dict:
    return {
        "id": pid,
        "name": name,
        "x": x,
        "y": y,
        "radius": 22.0,
        "label": name,
        "initial_marking": initial_marking,
        "is_catalyst": False,
        "is_signal_place": False,
        "is_energy_place": is_energy_place,
        "is_compartment_place": False,
        "is_regulatory_place": False,
        "is_parameter_place": False,
        "capacity": 0,
        "border_color": [0.0, 0.5, 0.0],
        "border_width": 2.0,
        "compartment": "cytoplasm",
        "metadata": {
            "kind": "energy_currency",
            "added_by": "add_energy_pool.py",
        },
        "properties": {},
    }


def _trans_template(tid: str, name: str, x: float, y: float,
                    rate_function: str) -> dict:
    return {
        "id": tid,
        "name": name,
        "x": x,
        "y": y,
        "width": 30.0,
        "height": 14.0,
        "label": name,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.7, 0.9, 0.7],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 1.5,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "single",
        "guard": "",
        "is_source": False,
        "is_sink": False,
        "earliest_time": 0.0,
        "latest_time": 0.0,
        "signal_places": [],
        "is_environment_aware": False,
        "module_id": "",
        "compartment": "cytoplasm",
        "kinetic_metadata": {},
        "metadata": {"added_by": "add_energy_pool.py"},
        "properties": {"rate_function": rate_function},
    }


def _arc_template(aid: str, name: str, source_id: str, target_id: str,
                  arc_type: str = "normal", weight: float = 1.0) -> dict:
    color = {
        "normal":      [0.0, 0.0, 0.0],
        "test":        [0.0, 0.0, 1.0],
        "signal_flow": [0.7, 0.7, 0.7],
        "inhibitor":   [1.0, 0.0, 0.0],
    }.get(arc_type, [0.0, 0.0, 0.0])
    return {
        "id": aid,
        "name": name,
        "arc_type": arc_type,
        "source_id": source_id,
        "target_id": target_id,
        "weight": float(weight),
        "threshold": 0.0,
        "color": color,
        "width": 1.5,
        "control_points": [],
    }


def main() -> int:
    if not SRC.exists():
        print(f"[add_energy_pool] source missing: {SRC}", file=sys.stderr)
        return 1

    model = json.loads(SRC.read_text())

    # ── 1. Allocate fresh IDs ────────────────────────────────────────
    p_next = _next_id(model["places"], "P")
    t_next = _next_id(model["transitions"], "T")
    a_next = _next_id(model["arcs"], "A")
    pid_NADPH    = f"P{p_next}"
    pid_NADPplus = f"P{p_next + 1}"
    tid_regen    = f"T{t_next}"

    # Position: park near the existing Glutathione_Reductase for visual
    # cohesion. We don't know exact GUI coords here — just pick something
    # reasonable; the GUI auto-relayout can clean up later.
    gr = next(t for t in model["transitions"]
              if t["name"] == "Glutathione_Reductase")
    base_x, base_y = float(gr.get("x", 600.0)), float(gr.get("y", 400.0))

    # ── 2. Add NADPH and NADP_plus places ────────────────────────────
    model["places"].append(_place_template(
        pid_NADPH, "NADPH",
        x=base_x - 90.0, y=base_y - 70.0,
        initial_marking=100.0,
    ))
    model["places"].append(_place_template(
        pid_NADPplus, "NADP_plus",
        x=base_x + 90.0, y=base_y - 70.0,
        initial_marking=10.0,
    ))

    # ── 3. Add NADPH_Regeneration transition (NADP_plus → NADPH) ─────
    regen_rate = (
        "1.0 * NADP_plus / (5 + NADP_plus) "
        "* (1 - 0.5 * Abeta_Oligomer / (50 + Abeta_Oligomer)) "
        "* Temperature_factor"
    )
    model["transitions"].append(_trans_template(
        tid_regen, "NADPH_Regeneration",
        x=base_x, y=base_y - 110.0,
        rate_function=regen_rate,
    ))

    # ── 4. Wire NADPH_Regeneration arcs ──────────────────────────────
    # NADP_plus → NADPH_Regeneration  (substrate, normal)
    model["arcs"].append(_arc_template(
        f"A{a_next}", f"A{a_next}",
        source_id=pid_NADPplus, target_id=tid_regen, arc_type="normal",
    ))
    a_next += 1
    # NADPH_Regeneration → NADPH  (product, normal)
    model["arcs"].append(_arc_template(
        f"A{a_next}", f"A{a_next}",
        source_id=tid_regen, target_id=pid_NADPH, arc_type="normal",
    ))
    a_next += 1

    # ── 5. Couple Glutathione_Reductase to NADPH ─────────────────────
    # NADPH → Glutathione_Reductase  (consumed, normal)
    model["arcs"].append(_arc_template(
        f"A{a_next}", f"A{a_next}",
        source_id=pid_NADPH, target_id=gr["id"], arc_type="normal",
    ))
    a_next += 1
    # Glutathione_Reductase → NADP_plus  (oxidized, normal)
    model["arcs"].append(_arc_template(
        f"A{a_next}", f"A{a_next}",
        source_id=gr["id"], target_id=pid_NADPplus, arc_type="normal",
    ))
    a_next += 1

    # Modify Glutathione_Reductase rate to gate on NADPH availability.
    # Old: 0.06 * GSSG
    # New: 0.06 * GSSG * NADPH / (50 + NADPH)   (MM-saturating in NADPH)
    old_rate = gr.get("properties", {}).get("rate_function") \
               or gr.get("rate_function") or "<unset>"
    new_rate = "0.06 * GSSG * NADPH / (50 + NADPH)"
    gr.setdefault("properties", {})["rate_function"] = new_rate
    # Strip stale top-level rate_function shadow per loader rules.
    gr.pop("rate_function", None)

    # ── 6. Save and roundtrip ────────────────────────────────────────
    DST.write_text(json.dumps(model, indent=2))
    rebuilt = json.loads(DST.read_text())

    # Roundtrip assertions per shy_loader_scopes
    by_pname = {p["name"]: p for p in rebuilt["places"]}
    by_tname = {t["name"]: t for t in rebuilt["transitions"]}

    assert "NADPH" in by_pname and by_pname["NADPH"]["is_energy_place"] is True
    assert by_pname["NADPH"]["initial_marking"] == 100.0
    assert "NADP_plus" in by_pname and by_pname["NADP_plus"]["is_energy_place"] is True
    assert by_pname["NADP_plus"]["initial_marking"] == 10.0

    nr = by_tname["NADPH_Regeneration"]
    assert nr["transition_type"] == "continuous"
    assert nr["properties"]["rate_function"] == regen_rate

    gr_new = by_tname["Glutathione_Reductase"]
    assert gr_new["properties"]["rate_function"] == new_rate, \
        f"rate_function did not land in properties: {gr_new['properties'].get('rate_function')!r}"

    # Verify all 4 new arcs are present at top-level with arc_type set
    new_arcs = [a for a in rebuilt["arcs"]
                if a["source_id"] in (pid_NADPH, pid_NADPplus, tid_regen, gr["id"])
                and a["target_id"] in (pid_NADPH, pid_NADPplus, tid_regen, gr["id"])]
    # Filter strictly to the 4 we added by checking they involve at least one
    # of the new objects (NADPH/NADP_plus/regen) — gr↔X count both.
    energy_objs = {pid_NADPH, pid_NADPplus, tid_regen}
    new_arcs = [a for a in rebuilt["arcs"]
                if a["source_id"] in energy_objs or a["target_id"] in energy_objs]
    assert len(new_arcs) == 4, f"expected 4 new arcs, got {len(new_arcs)}"
    for a in new_arcs:
        assert a["arc_type"] == "normal"
        assert "weight" in a and a["weight"] == 1.0

    print(f"[add_energy_pool] Wrote {DST}")
    print(f"  + Place {pid_NADPH:5} NADPH       M0=100 (is_energy_place=True)")
    print(f"  + Place {pid_NADPplus:5} NADP_plus   M0= 10 (is_energy_place=True)")
    print(f"  + Transition {tid_regen:5} NADPH_Regeneration")
    print(f"  + 4 arcs (NADP_plus→regen, regen→NADPH, NADPH→Reductase, Reductase→NADP_plus)")
    print(f"  ~ Glutathione_Reductase rate:")
    print(f"      OLD: {old_rate}")
    print(f"      NEW: {new_rate}")
    print(f"\n[add_energy_pool] Roundtrip OK — open in GUI to inspect / re-run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
