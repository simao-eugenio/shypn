"""Load-time arc-type audit per AGENT_RULES.md §8.

Emits non-blocking warnings for two silent-failure patterns:

  C13 — continuous transition with **only** signal_flow input arcs.
        PreemptionCheck risk: the transition will silently freeze whenever
        any upstream signal_flow producer of any of its input signal places
        is itself disabled. Common cause: basal turnover/degradation
        wired with signal_flow when it should be normal.

  C14 — basal sink-style transition (single input, no output, name matches
        *_degradation/_turnover/_clearance/_metabolism/_efflux/_desensit*)
        whose sole input is a signal_flow arc. Almost always a Rule M2 bug.

These are warnings, not errors. The model still loads and runs.
"""
from __future__ import annotations

import logging
import re
from typing import Any, List, Tuple

LOGGER = logging.getLogger(__name__)

_BASAL_NAME_RE = re.compile(
    r"degradation|turnover|clearance|metabolism|efflux|desensit",
    re.IGNORECASE,
)


def audit_arc_types(model: Any) -> List[Tuple[str, str, str]]:
    """Scan ``model`` for arc-type misuse patterns and emit warnings.

    Returns:
        List of ``(code, transition_id, message)`` triples for callers that
        want to surface findings in a UI panel. Warnings are also logged.
    """
    findings: List[Tuple[str, str, str]] = []

    transitions = list(getattr(model, "transitions", []) or [])
    arcs_attr = getattr(model, "arcs", None)
    if arcs_attr is None:
        return findings
    arcs = list(arcs_attr.values()) if isinstance(arcs_attr, dict) else list(arcs_attr)

    inputs_by_t: dict = {}
    outputs_by_t: dict = {}
    for a in arcs:
        tgt = getattr(a, "target_id", None)
        src = getattr(a, "source_id", None)
        if tgt and isinstance(tgt, str) and tgt.startswith("T"):
            inputs_by_t.setdefault(tgt, []).append(a)
        if src and isinstance(src, str) and src.startswith("T"):
            outputs_by_t.setdefault(src, []).append(a)

    for t in transitions:
        tid = getattr(t, "id", None)
        tname = getattr(t, "name", "?")
        ttype = getattr(t, "transition_type", "?")
        if not tid:
            continue

        ins = inputs_by_t.get(tid, [])
        outs = outputs_by_t.get(tid, [])

        # Filter to consuming inputs (skip test arcs; they are non-consuming).
        consuming_in = [
            a for a in ins
            if getattr(a, "arc_type", "normal") not in ("test", "inhibitor")
        ]
        sf_in = [a for a in consuming_in if getattr(a, "arc_type", "normal") == "signal_flow"]
        normal_in = [a for a in consuming_in if getattr(a, "arc_type", "normal") == "normal"]

        # C13: continuous transition with only signal_flow consuming inputs.
        if (
            ttype == "continuous"
            and consuming_in
            and len(sf_in) == len(consuming_in)
            and not normal_in
        ):
            msg = (
                f"C13 [{tid} {tname}] continuous transition has only "
                f"signal_flow consuming inputs ({len(sf_in)}). PreemptionCheck "
                "may silently disable this transition. If it is a basal "
                "turnover/degradation, change input arcs to 'normal' "
                "(see AGENT_RULES.md §8 Rule M2)."
            )
            LOGGER.warning(msg)
            findings.append(("C13", tid, msg))

        # C14: basal sink shape with signal_flow input.
        if (
            _BASAL_NAME_RE.search(tname or "")
            and len(consuming_in) == 1
            and not outs
            and getattr(consuming_in[0], "arc_type", "normal") == "signal_flow"
        ):
            msg = (
                f"C14 [{tid} {tname}] basal sink (single signal_flow input, "
                "no output). signal_flow input opts this sink into "
                "PreemptionCheck — typically not intended for basal turnover. "
                "Change input arc to 'normal' (see AGENT_RULES.md §8 Rule M2)."
            )
            LOGGER.warning(msg)
            findings.append(("C14", tid, msg))

    return findings
