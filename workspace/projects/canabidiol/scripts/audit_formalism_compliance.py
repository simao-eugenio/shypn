#!/usr/bin/env python3
"""
Audit canabidiol .shy models against the HPN experiment-plan / object-net rule.

Checks (per doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md):

  C1  Parameter places do NOT appear by name in any object-net rate function.
  C2  No F / F_s / F_t arcs touch a parameter place.
  C3  No object-net transition lists a parameter place in its signal_places.
  C4  No transition has is_environment_aware=True.
  C5  No object-net rate function references hard-coded environment symbols
      (Q10, Temperature, pH, Age, DSev, LOADING_DOSE, MAINT_DOSE, etc.)
      unless those symbols are bound to a declared parameter place — in
      which case C1 already flags them.
  C6  Every parameter place is reachable ONLY via events (informational —
      we report, we don't fail).
  C7  Every place is either a topology element (has arcs OR is referenced
      by name in some rate function « remote sensing per Simao 2025)
      OR is flagged is_parameter_place=true. Truly orphan places (no
      arcs, not referenced anywhere, not flagged parameter) are reported.
  C8  No two places represent the same concept (no semantic mirroring).
      Detected when a parameter place's name is a suffix/prefix variant
      of a topology place's name (e.g. `Age` topology place and
      `Age_param` parameter place), or when both a parameter place and
      a topology place share the same conceptual stem.

Exit code 0 if every model is clean, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ENV_SYMBOLS = (
    "Q10", "Temperature", "pH", "Age", "DSev",
    "Disease_Severity", "LOADING_DOSE", "MAINT_DOSE",
)

ROOT = Path(__file__).resolve().parents[1]
MODELS = sorted((ROOT / "models").glob("cbd_ad_neuroprotection_*.shy"))


def load(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def name_in_expr(name: str, expr: str) -> bool:
    """Return True if `name` appears as a whole word in `expr`."""
    if not expr:
        return False
    return re.search(rf"\b{re.escape(name)}\b", expr) is not None


def collect_rate_fields(t: dict) -> list[tuple[str, str]]:
    """Return [(field_name, expression_string), ...] for a transition."""
    out = []
    for key in ("rate_function", "rate_expression", "rate", "kinetic_law",
                "propensity", "guard", "guard_function"):
        v = t.get(key)
        if isinstance(v, str) and v.strip():
            out.append((key, v))
    # Some files nest under "kinetics"
    kin = t.get("kinetics")
    if isinstance(kin, dict):
        for key in ("rate_function", "expression", "formula"):
            v = kin.get(key)
            if isinstance(v, str) and v.strip():
                out.append((f"kinetics.{key}", v))
    return out


def audit_model(path: Path) -> tuple[int, list[str]]:
    """Return (n_violations, lines)."""
    model = load(path)
    places = model.get("places", [])
    transitions = model.get("transitions", [])
    arcs = model.get("arcs", [])
    events = model.get("events", []) or model.get("event_schedule", [])

    by_id = {p["id"]: p for p in places}
    by_name = {p["name"]: p for p in places}

    param_places = [p for p in places if p.get("is_parameter_place")]
    param_names = {p["name"] for p in param_places}
    param_ids = {p["id"] for p in param_places}

    lines: list[str] = []
    n = 0

    lines.append(f"\n=== {path.name} ===")
    lines.append(f"  places={len(places)}  transitions={len(transitions)}  "
                 f"arcs={len(arcs)}  parameter_places={len(param_places)}")
    if param_places:
        lines.append("  parameter places: " + ", ".join(sorted(param_names)))

    # ------------------------------------------------------------------
    # C1: parameter-place name in any rate function
    # ------------------------------------------------------------------
    for t in transitions:
        rates = collect_rate_fields(t)
        for field, expr in rates:
            for pname in param_names:
                if name_in_expr(pname, expr):
                    n += 1
                    lines.append(
                        f"  [C1] {t.get('name', t.get('id'))}.{field} "
                        f"references parameter place '{pname}': {expr!r}"
                    )

    # ------------------------------------------------------------------
    # C2: arcs touching parameter places
    # ------------------------------------------------------------------
    for a in arcs:
        s, tgt = a.get("source_id"), a.get("target_id")
        if s in param_ids or tgt in param_ids:
            n += 1
            arc_type = a.get("arc_type", a.get("type", "?"))
            sname = by_id.get(s, {}).get("name", s)
            tname = by_id.get(tgt, {}).get("name", tgt)
            lines.append(
                f"  [C2] arc {a.get('id', '?')} (type={arc_type}) "
                f"connects parameter place: {sname} -> {tname}"
            )

    # ------------------------------------------------------------------
    # C3: parameter place inside a transition's signal_places
    # ------------------------------------------------------------------
    for t in transitions:
        sp = t.get("signal_places") or []
        # signal_places may be list of names or list of ids
        for entry in sp:
            if entry in param_names or entry in param_ids:
                n += 1
                lines.append(
                    f"  [C3] {t.get('name', t.get('id'))}.signal_places "
                    f"contains parameter place '{entry}'"
                )

    # ------------------------------------------------------------------
    # C4: is_environment_aware backdoor
    # ------------------------------------------------------------------
    for t in transitions:
        if t.get("is_environment_aware"):
            n += 1
            lines.append(
                f"  [C4] {t.get('name', t.get('id'))} has "
                "is_environment_aware=True (parameter-place backdoor)"
            )

    # ------------------------------------------------------------------
    # C5: hard-coded environment symbols in rate expressions
    # ------------------------------------------------------------------
    for t in transitions:
        rates = collect_rate_fields(t)
        for field, expr in rates:
            for sym in ENV_SYMBOLS:
                # If sym is also a declared parameter place, C1 already
                # flagged it; skip here to avoid duplicates.
                if sym in param_names:
                    continue
                if name_in_expr(sym, expr):
                    n += 1
                    lines.append(
                        f"  [C5] {t.get('name', t.get('id'))}.{field} "
                        f"references hard-coded env symbol '{sym}': {expr!r}"
                    )

    # ------------------------------------------------------------------
    # C7: orphan no-arc places not flagged as parameter AND not referenced
    # in any rate function (remote sensing per Simao 2025 is legal).
    # ------------------------------------------------------------------
    touched = set()
    for a in arcs:
        touched.add(a.get("source_id"))
        touched.add(a.get("target_id"))

    # Build the set of place names that appear inside any rate expression.
    referenced_in_phi: set[str] = set()
    all_place_names = {p["name"] for p in places}
    for t in transitions:
        rates = collect_rate_fields(t)
        for _field, expr in rates:
            for pname in all_place_names:
                if name_in_expr(pname, expr):
                    referenced_in_phi.add(pname)

    for p in places:
        if p["id"] in touched:
            continue
        if p.get("is_parameter_place"):
            continue
        if p["name"] in referenced_in_phi:
            # Legal remote-sensed regular/signal place: no arcs, but biology
            # rates depend on its marking via Phi.
            lines.append(
                f"  [C7 info] place '{p['name']}' has no arcs but is"
                " remote-sensed via Φ (legal per Simao 2025)"
            )
            continue
        n += 1
        lines.append(
            f"  [C7] place '{p['name']}' has no arcs, is not referenced"
            " in any rate function, and is not flagged is_parameter_place"
            " — promote it (▢) or wire it in"
        )

    # ------------------------------------------------------------------
    # C8: semantic mirroring — a parameter place whose name shares a
    # conceptual stem with a topology (signal/regulatory/biological) place.
    # ------------------------------------------------------------------
    def stem(name: str) -> str:
        # Lowercase, strip common suffix/prefix decorations.
        s = name.lower()
        for suf in ("_param", "_parameter", "_p", "_value", "_setpoint",
                    "_target", "_init"):
            if s.endswith(suf):
                s = s[: -len(suf)]
                break
        for pre in ("param_", "parameter_", "p_", "set_"):
            if s.startswith(pre):
                s = s[len(pre):]
                break
        return s

    topology_stems = {
        stem(p["name"]): p["name"]
        for p in places
        if not p.get("is_parameter_place")
    }
    for pp in param_places:
        s = stem(pp["name"])
        if s in topology_stems and topology_stems[s] != pp["name"]:
            n += 1
            lines.append(
                f"  [C8] parameter place '{pp['name']}' mirrors topology"
                f" place '{topology_stems[s]}' (shared stem '{s}') —"
                " collapse to one carrier per §5.4 of the formalism doc"
            )

    # ------------------------------------------------------------------
    # C6 (info): events that read parameter places
    # ------------------------------------------------------------------
    if events:
        readers = []
        for ev in events:
            ev_text = json.dumps(ev)
            for pname in param_names:
                if name_in_expr(pname, ev_text):
                    readers.append((ev.get("name", ev.get("id", "?")), pname))
        if readers:
            lines.append(f"  [C6 info] {len(readers)} event/parameter "
                         "couplings (legal):")
            for ename, pname in readers:
                lines.append(f"           {ename}  reads  {pname}")
        else:
            lines.append("  [C6 info] no events read parameter places")
    else:
        lines.append("  [C6 info] model has no events declared")

    if n == 0:
        lines.append("  ✓ COMPLIANT")
    else:
        lines.append(f"  ✗ {n} violation(s)")

    return n, lines


def main() -> int:
    if not MODELS:
        print(f"No models found under {ROOT/'models'}")
        return 2

    total = 0
    out: list[str] = ["HPN formalism / experiment-plan compliance audit",
                      "=" * 60,
                      f"Models scanned: {len(MODELS)}"]
    for m in MODELS:
        n, ls = audit_model(m)
        total += n
        out.extend(ls)

    out.append("")
    out.append("=" * 60)
    if total == 0:
        out.append("OVERALL: ALL MODELS COMPLIANT ✓")
    else:
        out.append(f"OVERALL: {total} violation(s) across "
                   f"{sum(1 for m in MODELS if audit_model(m)[0])} model(s)")
    print("\n".join(out))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
