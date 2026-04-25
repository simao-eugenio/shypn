#!/usr/bin/env python3
"""
Audit canabidiol experiment protocols against their paired models.

Per doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md §6
("Sweep ↔ model superposition rule"):

  S1  Each `protocols/P*.md` paragraph 1 references an existing
      model file via the `Pairing` line.
  S2  The matching `sweep_config.P*.json` exists at the project root.
  S3  Every sweep parameter path of the form `<Place>.initial_marking`
      targets a place that exists in the paired model. The sweep is
      legal whether the place is a parameter place ▢, a signal place
      ⬡, or a regular biological place ○ — sweeping the initial
      marking of a topology element is a legitimate initial-condition
      perturbation of $M_0$ (see formalism doc §5.4 corollary).
  S4  Every place that the sweep mentions must actually exist in the
      model.
  S5  Every event the protocol's "Built-in events" table lists must
      exist in the paired model.
  S6  No sweep parameter has the same value in every level (would be a
      degenerate sweep).
  S7  The protocol's `Pairing` line and the sweep config's
      `model_path` agree.
  S8  Sweep target must not collide with a parameter mirror in the
      paired model. If `X` is being swept and the model contains BOTH
      a topology place `X` and a parameter mirror `X_param` (or vice
      versa), the override target is ambiguous. This is the §5.4
      mirroring smell surfacing at sweep time.

Exit code 0 if every protocol passes, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_DIR = ROOT / "protocols"
MODEL_DIR = ROOT / "models"


def load_json(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def find_pairing(md_text: str) -> str | None:
    """Return the URL inside `**Pairing.** Model: [`...`](URL)`, or
    the literal sentinel `__TBD__` if the protocol declares the model
    pending, or None if the line is missing entirely.
    """
    # TBD form: `**Pairing.** Model: TBD ...`
    if re.search(r"\*\*Pairing\.\*\*\s*Model:\s*TBD\b", md_text):
        return "__TBD__"
    # Markdown link form: `[display](url)`
    m = re.search(r"\*\*Pairing\.\*\*\s*Model:\s*\[[^\]]+\]\(([^)]+)\)",
                  md_text)
    return m.group(1) if m else None


def find_built_in_events(md_text: str) -> list[str]:
    """Return event ids listed in the Built-in events table of a protocol."""
    # Look for table rows starting with `evt_*` in backticks.
    return re.findall(r"\|\s*`(evt_[A-Za-z0-9_*\\]+)`", md_text)


def find_sweep_paths(cfg: dict) -> list[tuple[str, str, list]]:
    """Return (type, path, values) tuples from a sweep_config.json."""
    out = []
    for p in cfg.get("parameters", []):
        out.append((p.get("type", "?"), p.get("path", "?"), p.get("values", [])))
    return out


def model_param_places(model: dict) -> set[str]:
    return {p["name"] for p in model.get("places", []) if p.get("is_parameter_place")}


def model_place_names(model: dict) -> set[str]:
    return {p["name"] for p in model.get("places", [])}


def model_event_ids(model: dict) -> set[str]:
    out = set()
    for ev in model.get("events", []) or []:
        for k in ("id", "name"):
            v = ev.get(k)
            if v:
                out.add(v)
    return out


def sweep_config_for_protocol(pid: str) -> Path | None:
    """Find sweep_config.P<id>*.json variants."""
    candidates = sorted(ROOT.glob(f"sweep_config.{pid}*.json"))
    return candidates[0] if candidates else None


def audit_protocol(md_path: Path) -> tuple[int, list[str]]:
    md_text = md_path.read_text()
    lines: list[str] = [f"\n=== {md_path.name} ==="]
    n = 0

    # ------- S1: pairing line + model file exists --------------------
    paired_rel = find_pairing(md_text)
    if not paired_rel:
        n += 1
        lines.append("  [S1] no `Pairing` line found in protocol")
        return n, lines
    if paired_rel == "__TBD__":
        lines.append("  [S1 info] protocol declares Model: TBD — skipping")
        return n, lines

    paired_path = (md_path.parent / paired_rel).resolve()
    if not paired_path.exists():
        n += 1
        lines.append(f"  [S1] paired model not found: {paired_path}")
        return n, lines

    lines.append(f"  paired model: {paired_path.relative_to(ROOT)}")
    model = load_json(paired_path)
    param_places = model_param_places(model)
    all_places = model_place_names(model)
    all_events = model_event_ids(model)

    # ------- S2: matching sweep_config.P*.json -----------------------
    pid_match = re.match(r"P(\d+)", md_path.stem)
    if not pid_match:
        n += 1
        lines.append(f"  [S2] cannot parse protocol id from {md_path.name}")
        return n, lines
    pid = "P" + pid_match.group(1)
    cfg_path = sweep_config_for_protocol(pid)
    if not cfg_path:
        lines.append(f"  [S2 info] no sweep_config.{pid}*.json in project "
                     "root (protocol pending)")
        # Don't fail — README marks several protocols as pending.
    else:
        lines.append(f"  sweep config: {cfg_path.name}")
        try:
            cfg = load_json(cfg_path)
        except json.JSONDecodeError as exc:
            n += 1
            lines.append(f"  [S2] cannot parse {cfg_path.name}: {exc}")
            return n, lines

        # ------- S7: model_path agreement ----------------------------
        cfg_model = cfg.get("model_path", "")
        if cfg_model and not cfg_model.endswith(paired_path.name):
            n += 1
            lines.append(
                f"  [S7] sweep model_path mismatch: protocol -> "
                f"{paired_path.name}, sweep -> {cfg_model}"
            )

        # ------- S3 + S4 + S8: parameter paths target real places ----
        # Build a stem -> [names] map to detect mirror collisions.
        def _stem(name: str) -> str:
            s = name.lower()
            for suf in ("_param", "_parameter", "_p", "_value",
                        "_setpoint", "_target", "_init"):
                if s.endswith(suf):
                    return s[: -len(suf)]
            for pre in ("param_", "parameter_", "p_", "set_"):
                if s.startswith(pre):
                    return s[len(pre):]
            return s

        stem_index: dict[str, list[str]] = {}
        for pn in all_places:
            stem_index.setdefault(_stem(pn), []).append(pn)

        for ptype, ppath, pvals in find_sweep_paths(cfg):
            m = re.match(r"^([A-Za-z0-9_]+)\.initial_marking$", ppath)
            if not m:
                continue
            place = m.group(1)
            if place not in all_places:
                n += 1
                lines.append(
                    f"  [S4] sweep targets unknown place: {ppath}"
                )
                continue
            # S3: classification (informational — always legal to sweep
            # initial_marking of any topology element).
            kind = ("parameter ▢" if place in param_places
                    else "signal ⬡/regular ○")
            lines.append(
                f"  [S3 info] sweep '{place}.initial_marking'"
                f" targets a {kind} place"
            )
            # S8: collision with a mirror under the same stem
            siblings = [n2 for n2 in stem_index.get(_stem(place), [])
                        if n2 != place]
            if siblings:
                n += 1
                lines.append(
                    f"  [S8] sweep '{place}' collides with mirror(s)"
                    f" in model: {', '.join(siblings)} — collapse to"
                    " one carrier per §5.4 of the formalism doc"
                )
            # ------- S6: degenerate sweep --------------------------
            if isinstance(pvals, list) and len(pvals) > 1 and len(set(pvals)) == 1:
                n += 1
                lines.append(
                    f"  [S6] sweep over '{place}' has identical values "
                    f"({pvals}) — degenerate"
                )

    # ------- S5: built-in events listed by protocol exist ------------
    listed_events = find_built_in_events(md_text)
    # The protocols use shorthand `evt_install_*` to refer to families;
    # treat trailing `*` as a wildcard.
    missing = []
    matched = 0
    for ev in listed_events:
        if ev.endswith("*"):
            prefix = ev[:-1]
            family = [e for e in all_events if e.startswith(prefix)]
            if not family:
                missing.append(ev)
            else:
                matched += len(family)
        else:
            if ev not in all_events:
                missing.append(ev)
            else:
                matched += 1
    if missing:
        n += 1
        lines.append(
            f"  [S5] events listed in protocol but missing in model: "
            + ", ".join(missing)
        )
    else:
        lines.append(f"  [S5 info] {matched} model event(s) match "
                     f"{len(listed_events)} protocol entries")

    if n == 0:
        lines.append("  ✓ COMPLIANT")
    else:
        lines.append(f"  ✗ {n} violation(s)")
    return n, lines


def main() -> int:
    protocols = sorted(p for p in PROTOCOL_DIR.glob("P*.md")
                       if p.name != "README.md")
    if not protocols:
        print(f"No protocols found under {PROTOCOL_DIR}")
        return 2

    out = ["Canabidiol experiment-protocol compliance audit",
           "=" * 60,
           f"Protocols scanned: {len(protocols)}"]
    total = 0
    for p in protocols:
        n, ls = audit_protocol(p)
        total += n
        out.extend(ls)

    out.append("")
    out.append("=" * 60)
    if total == 0:
        out.append("OVERALL: ALL PROTOCOLS COMPLIANT ✓")
    else:
        out.append(f"OVERALL: {total} violation(s) across protocols")
    print("\n".join(out))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
