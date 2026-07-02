"""Simulation viability and structural checking.

- ViabilityChecker: dynamic check (per-step transition firing conditions).
- arc_type_auditor.audit_arc_types: load-time structural audit (arc-type
  misuse patterns C13/C14 per AGENT_RULES.md §8).
- timescale_auditor.audit_timescales: load-time / init-time integration
  step adequacy audit (TMD-1, codes C20/C21/C22).
"""

from .viability_checker import ViabilityChecker
from .arc_type_auditor import audit_arc_types
from .timescale_auditor import (
    audit_timescales,
    TimescaleProfile,
    TransitionTimescale,
)

__all__ = [
    'ViabilityChecker',
    'audit_arc_types',
    'audit_timescales',
    'TimescaleProfile',
    'TransitionTimescale',
]
