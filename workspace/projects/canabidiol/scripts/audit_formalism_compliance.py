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
  C9  Disconnected remote sensing. A REGULAR ○ place referenced by name
      inside some Φ but with ZERO arcs of any type ($F$, $F_s$, $F_t$)
      is a parameter-place backdoor wearing the wrong glyph. Signal
      places (⬡ biological and ◇ spatial) are exempt: Ψ membership
      itself declares "informational state, designed to be read by many
      transitions." Fix a flagged ○ by adding the missing arc, by
      reclassifying as ◇ spatial signal (event-fed kinetic scalar
      shared by N rates), or by reclassifying as ▢ parameter.
  C10 Spatial signal places ◇ must NOT have F_s arcs. ◇ places are
      environmental scalars excluded from the biological cascade
      (PreemptionCheck and POSet); an F_s arc would smuggle them back
      into the hierarchy.
  C11 Every spatial signal place ◇ must be either referenced by some
      Φ or written by some event. An unused ◇ is an inert scalar —
      promote to ▢ or delete.
  C12 Events must not perform stateful algebra. Per "Pattern A
      discipline", an event assignment `target := expr` may only read
      parameter places ▢ and the target itself (additive update). Any
      reference to a non-target state place (○, ⬡, ◇) on the RHS means
      the event is acting as a hidden ODE integrator — that algebra
      belongs in a transition rate Φ.

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


def collect_rate_fields(t: dict, executable_only: bool = False) -> list[tuple[str, str]]:
    """Return [(field_name, expression_string), ...] for a transition.

    Schemas seen in the wild:
      * top-level ``rate_function`` / ``rate_expression`` / ``rate`` etc.
      * nested ``properties.rate_function`` / ``properties.rate_function_display``
        (canonical .shy file format produced by the GUI),
      * nested ``kinetics.{rate_function,expression,formula}`` (legacy).

    When ``executable_only`` is True, drop ``*_display`` fields — those are
    human-readable labels (LaTeX-ish, may contain ``Q10``, ``[X]``) that the
    engine never evaluates, so they should not raise C1 / C5 violations.
    """
    out = []
    for key in ("rate_function", "rate_expression", "rate", "kinetic_law",
                "propensity", "guard", "guard_function"):
        v = t.get(key)
        if isinstance(v, str) and v.strip():
            out.append((key, v))
    # Canonical .shy schema: the GUI persists rate functions under
    # ``properties.rate_function`` (numeric / executable) and
    # ``properties.rate_function_display`` (human-readable).
    props = t.get("properties")
    if isinstance(props, dict):
        keys = ("rate_function", "rate_expression") if executable_only else (
            "rate_function", "rate_function_display", "rate_expression")
        for key in keys:
            v = props.get(key)
            if isinstance(v, str) and v.strip():
                out.append((f"properties.{key}", v))
    # Legacy nested 'kinetics' container
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
        rates = collect_rate_fields(t, executable_only=True)
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
    #
    # In the legacy formalism this flag was set manually to opt a
    # transition into engine-side env-symbol injection (Temperature, pH,
    # Q10, …). In the current code (2026-04+) the flag is purely a
    # *derived* display attribute computed by the engine as
    # ``len(signal_places) > 0`` — see
    # ``builders/transition_builder.py:400`` and
    # ``analysis/quorum_sensing.py:258``. It never gates execution.
    #
    # The genuine backdoor pattern is ``is_environment_aware=True`` with
    # an EMPTY ``signal_places`` list — that combination cannot arise
    # from the engine's auto-derivation and indicates a stale
    # hand-edited flag from a pre-refactor model. With a non-empty
    # ``signal_places`` the flag is benign bookkeeping.
    # ------------------------------------------------------------------
    for t in transitions:
        if not t.get("is_environment_aware"):
            continue
        sp = t.get("signal_places") or []
        if sp:
            continue  # benign: flag matches engine-derived bookkeeping
        n += 1
        lines.append(
            f"  [C4] {t.get('name', t.get('id'))} has "
            "is_environment_aware=True but no signal_places "
            "(stale legacy backdoor flag — clear it)"
        )

    # ------------------------------------------------------------------
    # C5: hard-coded environment symbols in rate expressions
    # ------------------------------------------------------------------
    for t in transitions:
        rates = collect_rate_fields(t, executable_only=True)
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
        # Signal places (⬡ biological and ◇ spatial) are exempt from C9 by
        # design — Ψ membership declares "informational state, designed to
        # be read by many transitions" (formalism doc §5.5). For spatial
        # signal places ◇ this is the canonical event-fed kinetic-scalar
        # pattern; for biological signal places ⬡ the lack of F_s arcs is
        # unusual but legal.
        if p.get("is_signal_place"):
            if p["name"] in referenced_in_phi:
                continue  # legal remote sensing of a signal hub
            # signal place not referenced anywhere → flag via C11 below
            continue
        if p["name"] in referenced_in_phi:
            # C9: disconnected remote sensing of a REGULAR ○ place.
            # Per the formalism doc §5.5, the fix is one of:
            #   1. Add the missing F/F_s/F_t arc(s).
            #   2. Reclassify as ◇ spatial signal (is_signal_place=true,
            #      signal_type=SPATIAL) — for event-fed kinetic scalars
            #      shared by many rates.
            #   3. Reclassify as ▢ parameter — for values read by events
            #      only, not by Φ.
            n += 1
            lines.append(
                f"  [C9] regular ○ place '{p['name']}' is referenced inside"
                " some Φ but has ZERO arcs — disconnected remote sensing."
                " Fix: add F/F_s/F_t arc, or reclassify as ◇ spatial signal,"
                " or as ▢ parameter."
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
    # C10: spatial signal places (◇) must NOT have F_s arcs.
    # Per formalism doc §5.4 carrier 3, ◇ places are environmental
    # scalars excluded from the biological cascade; an F_s arc would
    # smuggle them back into PreemptionCheck and POSet layering.
    # ------------------------------------------------------------------
    spatial_ids = {
        p["id"] for p in places
        if p.get("is_signal_place")
        and (p.get("signal_type") or "").lower() == "spatial"
    }
    if spatial_ids:
        for a in arcs:
            if a.get("arc_type") != "signal_flow":
                continue
            sp_id = a.get("source_id")
            tg_id = a.get("target_id")
            if sp_id in spatial_ids or tg_id in spatial_ids:
                n += 1
                offender = sp_id if sp_id in spatial_ids else tg_id
                lines.append(
                    f"  [C10] signal_flow arc {sp_id} → {tg_id} touches"
                    f" spatial signal place '{offender}'. Spatial places"
                    " are excluded from the biological cascade and must"
                    " not have F_s arcs (formalism doc §5.4 carrier 3)."
                )

    # ------------------------------------------------------------------
    # C11: every spatial signal place ◇ must be either referenced by a Φ
    # or written by an event — otherwise it is an inert scalar that
    # should be promoted to ▢ or deleted.
    # ------------------------------------------------------------------
    if events:
        evt_text_all = json.dumps(events)
    else:
        evt_text_all = ""
    for p in places:
        if not p.get("is_signal_place"):
            continue
        if (p.get("signal_type") or "").lower() != "spatial":
            continue
        in_phi = p["name"] in referenced_in_phi
        in_evt = bool(evt_text_all) and name_in_expr(p["name"], evt_text_all)
        if not in_phi and not in_evt:
            n += 1
            lines.append(
                f"  [C11] spatial signal place ◇ '{p['name']}' is neither"
                " referenced in any Φ nor written by any event — it is"
                " inert. Either use it (read in Φ / write from event), or"
                " reclassify as ▢ parameter, or delete it."
            )

    # ------------------------------------------------------------------
    # C12: events must not perform stateful algebra. Event bodies are
    # discrete protocol interventions, not a back-channel for continuous
    # dynamics. Per formalism doc §"Pattern A discipline": the only
    # legal RHS in an event assignment `target := expr` is one whose
    # variable references are a subset of
    #     {target}  ∪  {parameter places ▢}
    # i.e. constants, parameters, and self-referential additive updates
    # like `Abeta_Monomer + Disease_Severity * 0.125`. Any reference to
    # another simulation-state place (○, ⬡, or ◇) on the RHS means the
    # event is doing the topology's job — that algebra belongs in Φ.
    # ------------------------------------------------------------------
    import ast as _ast
    state_place_names = {
        p["name"] for p in places if not p.get("is_parameter_place")
    }
    for ev in events or []:
        assigns = ev.get("assignments") or {}
        if not isinstance(assigns, dict):
            continue
        ev_label = ev.get("name", ev.get("id", "?"))
        for target, expr in assigns.items():
            if not isinstance(expr, str) or not expr.strip():
                continue
            # Strip any leading 'target :=' / 'target =' if the engine
            # stores the full statement form (defensive — current shy
            # files store RHS only).
            rhs = expr
            for sep in (":=", "="):
                if sep in rhs and rhs.split(sep, 1)[0].strip() == target:
                    rhs = rhs.split(sep, 1)[1]
                    break
            try:
                tree = _ast.parse(rhs, mode="eval")
            except SyntaxError:
                # Non-Python expression syntax — skip rather than false-flag.
                continue
            referenced = {
                node.id for node in _ast.walk(tree)
                if isinstance(node, _ast.Name)
            }
            illegal = (referenced & state_place_names) - {target}
            if illegal:
                n += 1
                lines.append(
                    f"  [C12] event '{ev_label}' assignment to '{target}'"
                    f" references state place(s) {sorted(illegal)} on the"
                    " RHS. Events may only read parameter places ▢ and the"
                    " target itself (additive updates). Move the algebra"
                    " into a transition rate Φ instead — values must"
                    " emerge from the topology, not from event arithmetic."
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
