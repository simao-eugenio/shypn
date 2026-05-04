"""Reads ``SimulationParams`` out of the GTK ``ParameterSweepBuilder`` widgets.

Centralising this here means there is exactly one place that knows the
widget names — eliminating the drift class of bug that caused the dt
manual entry to be silently dropped on the remote dispatch path.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional, TypeVar

from .types import SimulationParams

T = TypeVar('T')

_log = logging.getLogger(__name__)


def _read(
    obj: Any,
    attr: str,
    parse: Callable[[str], T],
    *,
    validate: Optional[Callable[[T], bool]] = None,
) -> Optional[T]:
    """Best-effort widget read. Returns ``None`` on any failure.

    Tries ``obj.<attr>.get_text()``, parses, optionally validates. Caller
    decides whether to keep or fall back to the default.
    """
    if not hasattr(obj, attr):
        return None
    try:
        text = getattr(obj, attr).get_text().strip()
    except Exception:
        return None
    if not text:
        return None
    try:
        value = parse(text)
    except (ValueError, TypeError):
        return None
    if validate is not None and not validate(value):
        return None
    return value


def _combo_id(obj: Any, attr: str) -> Optional[str]:
    if not hasattr(obj, attr):
        return None
    try:
        return getattr(obj, attr).get_active_id()
    except Exception:
        return None


class WidgetParamCollector:
    """Collects ``SimulationParams`` from a ``ParameterSweepBuilder`` instance.

    Stateless utility; held as a class so subclasses can override
    individual reads if a future variant uses different widgets.
    """

    @classmethod
    def collect(cls, sweep_builder: Any, *, use_parallel: bool = True) -> SimulationParams:
        """Build a fully-typed ``SimulationParams`` from the live widgets.

        Missing or invalid widget values fall back to dataclass defaults.
        """
        if sweep_builder is None:
            return SimulationParams(use_parallel=use_parallel)

        sp = SimulationParams(use_parallel=use_parallel)

        # Sweep shape
        v_int = _read(sweep_builder, 'replicates_entry', int, validate=lambda v: v > 0)
        if v_int is not None:
            sp.replicates = v_int

        v_flt = _read(sweep_builder, 'duration_entry', float, validate=lambda v: v > 0)
        if v_flt is not None:
            sp.duration = v_flt

        term = _combo_id(sweep_builder, 'termination_combo')
        if term:
            sp.termination = term

        v_int = _read(sweep_builder, 'sweep_seed_entry', int)
        if v_int is not None:
            sp.seed_base = v_int

        tier = _combo_id(sweep_builder, 'output_tier_combo')
        if tier:
            sp.output_tier = tier

        # Solver
        v_flt = _read(sweep_builder, 'sweep_tau_epsilon_entry', float,
                      validate=lambda v: 0 < v <= 1)
        if v_flt is not None:
            sp.tau_epsilon = v_flt

        v_flt = _read(sweep_builder, 'sweep_max_tau_entry', float,
                      validate=lambda v: 0 < v <= 100)
        if v_flt is not None:
            sp.max_tau = v_flt

        # Manual dt — only when the Manual radio is active. Auto leaves
        # ``time_step=None`` so the engine falls back to dt_auto (capped
        # at SimulationSettings.DEFAULT_DT_AUTO_CAP = 1.0 s).
        if (hasattr(sweep_builder, 'sweep_dt_manual_radio')
                and hasattr(sweep_builder, 'sweep_dt_manual_entry')):
            try:
                manual_active = sweep_builder.sweep_dt_manual_radio.get_active()
            except Exception:
                manual_active = False
            if manual_active:
                v_flt = _read(sweep_builder, 'sweep_dt_manual_entry', float,
                              validate=lambda v: v > 0)
                if v_flt is not None:
                    sp.time_step = v_flt

        # Local-only compressor knobs
        v_flt = _read(sweep_builder, 'sweep_compressor_epsilon_entry', float,
                      validate=lambda v: 0 < v < 1)
        if v_flt is not None:
            sp.compressor_epsilon = v_flt

        v_flt = _read(sweep_builder, 'sweep_compressor_min_gap_entry', float,
                      validate=lambda v: v >= 0)
        if v_flt is not None:
            sp.compressor_min_gap = v_flt

        v_flt = _read(sweep_builder, 'sweep_compressor_max_gap_entry', float,
                      validate=lambda v: v > 0)
        if v_flt is not None:
            sp.compressor_max_gap = v_flt

        return sp
