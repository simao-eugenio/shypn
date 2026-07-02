"""Sweep configuration base class and shared types.

Defines the abstract interface that all sweep modes (single, factorial,
snapshots) must implement.  Subclasses live in their own modules to keep
each strategy focused and independently testable.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from shypn.ui.panels.viability.experiment_manager import ExperimentSnapshot


# ── Shared value objects ──────────────────────────────────────────────────

@dataclass(frozen=True)
class SimulationParams:
    """Immutable simulation engine parameters shared across all conditions."""

    replicates: int = 200
    duration: float = 2000.0
    termination: str = "deadlock"
    seed_base: int = 42
    tau_epsilon: float = 0.03
    max_tau: float = 0.1
    time_step: Optional[float] = None

    def __post_init__(self) -> None:
        if self.replicates < 1:
            raise ValueError(f"replicates must be >= 1, got {self.replicates}")
        if self.duration <= 0:
            raise ValueError(f"duration must be > 0, got {self.duration}")
        if not (0 < self.tau_epsilon <= 1):
            raise ValueError(f"tau_epsilon must be in (0, 1], got {self.tau_epsilon}")


# Allowed sweep target types.
#   places       — place property (e.g. "P5.initial_marking")
#   transitions  — transition property (e.g. "T12.rate")
#   arcs         — arc property (e.g. "A34.weight")
#   events       — environment-event field (e.g. "evt_loading_dose.delay").
#                  See sweep_runner._apply_snapshot for the supported field
#                  set; canonical ‘sweep an event payload value’ uses the
#                  Pattern A bridge: sweep a ▢ parameter place that the
#                  event RHS reads (e.g. LOADING_DOSE.initial_marking).
PARAMETER_SWEEP_TYPES = ('places', 'transitions', 'arcs', 'events')


@dataclass(frozen=True)
class ParameterSpec:
    """One swept parameter axis: type, property path, and values."""

    param_type: str          # see PARAMETER_SWEEP_TYPES
    path: str                # e.g. 'P_EPO.initial_marking' or 'evt_loading_dose.delay'
    values: List[float]

    def __post_init__(self) -> None:
        if self.param_type not in PARAMETER_SWEEP_TYPES:
            raise ValueError(
                f"param_type must be one of {PARAMETER_SWEEP_TYPES}, "
                f"got '{self.param_type}'"
            )
        if not self.values:
            raise ValueError("values list must not be empty")


# ── Output granularity ───────────────────────────────────────────────────

# Output tier hierarchy — controls per-condition disk footprint.
# Each tier is the previous tier plus more artefacts. Same ladder is honoured
# by both the CLI/remote sweep path (sweep_runner + SweepOutputManager) and
# the local viability sweep path (_auto_save_experiment).
#
#   G0 — summary.csv only (run-level, one row per condition)
#   G1 — + replicates.csv (per-replicate endpoint scalars: *_final, *_firings)
#   G2 — + statistics.json with endpoint-only stats (no per-step arrays)
#   G3 — + statistics.json with full per-step time-series stats   ← current default
#   G4 — + per-replicate trajectory CSVs (every dt, all places) under
#        replicates_trajectories/run_NNN.csv. Honours trajectory_places
#        (subset filter) and trajectory_thin_seconds (decimation step) when
#        set on OutputOptions.
#   G5 — + covariance.json with mean / covariance / correlation matrices over
#        per-replicate final-state place values, plus n_replicates.
#
# Backwards compatibility: missing output_tier in config → G3.
OUTPUT_TIERS = ('G0', 'G1', 'G2', 'G3', 'G4', 'G5')
DEFAULT_OUTPUT_TIER = 'G3'

# Numeric level per tier — use this instead of lexicographic comparison
# (`'G10' < 'G2'` lexicographically, which would silently misroute writes
# if the ladder ever grows past 9). Single source of truth.
_TIER_LEVEL: Dict[str, int] = {t: i for i, t in enumerate(OUTPUT_TIERS)}


@dataclass(frozen=True)
class OutputOptions:
    """Run-level output granularity controls.

    Decoupled from :class:`SimulationParams` because granularity is a
    storage / analysis concern, not an engine concern. The Viability
    Panel binds to this; engines stay oblivious.
    """

    tier: str = DEFAULT_OUTPUT_TIER
    # G4 trajectory shaping (optional — None means "all places, no thinning"):
    trajectory_places: Optional[List[str]] = None   # subset of place IDs/names
    trajectory_thin_seconds: Optional[float] = None  # min Δt between samples

    def __post_init__(self) -> None:
        if self.tier not in OUTPUT_TIERS:
            raise ValueError(
                f"output_tier must be one of {OUTPUT_TIERS}, got '{self.tier}'"
            )
        if self.trajectory_thin_seconds is not None \
                and self.trajectory_thin_seconds < 0:
            raise ValueError(
                f"trajectory_thin_seconds must be >= 0, "
                f"got {self.trajectory_thin_seconds}"
            )

    # Convenience predicates the worker uses to gate writes.
    @property
    def _level(self) -> int:
        return _TIER_LEVEL.get(self.tier, _TIER_LEVEL[DEFAULT_OUTPUT_TIER])

    @property
    def write_replicates_csv(self) -> bool:
        return self._level >= _TIER_LEVEL['G1']

    @property
    def write_statistics_json(self) -> bool:
        return self._level >= _TIER_LEVEL['G2']

    @property
    def statistics_endpoint_only(self) -> bool:
        return self.tier == 'G2'

    @property
    def write_per_replicate_trajectories(self) -> bool:
        """G4+ — one CSV per replicate under replicates_trajectories/."""
        return self._level >= _TIER_LEVEL['G4']

    @property
    def write_covariance(self) -> bool:
        """G5+ — covariance.json over per-replicate final-state values."""
        return self._level >= _TIER_LEVEL['G5']

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {'tier': self.tier}
        if self.trajectory_places is not None:
            d['trajectory_places'] = list(self.trajectory_places)
        if self.trajectory_thin_seconds is not None:
            d['trajectory_thin_seconds'] = self.trajectory_thin_seconds
        return d

    @staticmethod
    def from_dict(data: Optional[Dict[str, Any]]) -> 'OutputOptions':
        if not data:
            return OutputOptions()
        return OutputOptions(
            tier=data.get('tier', DEFAULT_OUTPUT_TIER),
            trajectory_places=data.get('trajectory_places'),
            trajectory_thin_seconds=data.get('trajectory_thin_seconds'),
        )


# ── Abstract base ─────────────────────────────────────────────────────────

class SweepConfig(ABC):
    """Abstract base for all sweep configuration strategies.

    Subclasses must implement :meth:`generate_snapshots` which produces
    the concrete list of :class:`ExperimentSnapshot` objects — one per
    condition to simulate.

    The class also owns the shared :class:`SimulationParams` and handles
    JSON (de)serialisation dispatch.
    """

    def __init__(self, sim_params: SimulationParams,
                 output: Optional[OutputOptions] = None) -> None:
        self.sim_params = sim_params
        self.output = output if output is not None else OutputOptions()
        # Top-level environment events captured from the model at dispatch
        # time.  Each entry is a dict produced by Event.to_dict().  Applied
        # to every condition (per-snapshot override is not yet implemented).
        self.events: List[Dict[str, Any]] = []
        # Top-level **fixed** property overrides — applied to every
        # snapshot before the swept axis layers on. Use this for sweep-wide
        # constants (e.g. DISEASE_SEVERITY=0.5, TEMPERATURE=310.15) that
        # the user wants to differ from the model defaults but should NOT
        # vary across conditions. Keys are full property paths
        # ("P38.initial_marking"); values are floats.
        # Precedence at apply-time:
        #   model defaults < fixed_overrides < per-snapshot overrides
        #     < swept axis  < events fired during the run
        self.fixed_overrides: Dict[str, float] = {}
        # Opt-in observable reduction config (UI-only). The engine
        # never reads this; the Results Browser uses it to compute
        # endpoint / first-crossing scalars per condition.
        self.primary_observables: Optional[Dict[str, Any]] = None

    # ── abstract contract ─────────────────────────────────────────────

    @abstractmethod
    def generate_snapshots(
        self,
        baseline: ExperimentSnapshot,
    ) -> List[ExperimentSnapshot]:
        """Return one snapshot per experimental condition.

        Args:
            baseline: The baseline snapshot (initial model state).

        Returns:
            Ordered list of snapshots.  Each snapshot carries the
            ``property_overrides`` that distinguish it from the baseline.
        """

    @abstractmethod
    def describe(self) -> str:
        """Human-readable one-line summary (used by ``--dry-run``)."""

    @abstractmethod
    def condition_count(self) -> int:
        """Total number of conditions that will be generated."""

    # ── JSON (de)serialisation dispatch ───────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-safe dictionary.

        Subclasses should call ``super().to_dict()`` and add their keys.
        """
        d: Dict[str, Any] = {
            'replicates': self.sim_params.replicates,
            'duration': self.sim_params.duration,
            'termination': self.sim_params.termination,
            'seed_base': self.sim_params.seed_base,
            'tau_epsilon': self.sim_params.tau_epsilon,
            'max_tau': self.sim_params.max_tau,
            'time_step': self.sim_params.time_step,
        }
        if self.events:
            d['events'] = list(self.events)
        if self.fixed_overrides:
            d['fixed_overrides'] = dict(self.fixed_overrides)
        # Output granularity (only emitted if non-default to keep configs tidy)
        if self.output.tier != DEFAULT_OUTPUT_TIER \
                or self.output.trajectory_places is not None \
                or self.output.trajectory_thin_seconds is not None:
            d['output'] = self.output.to_dict()
        # Pass-through opt-in observable reduction config (UI-only;
        # the engine never reads it). Lives on the instance as
        # ``primary_observables`` when present.
        po = getattr(self, 'primary_observables', None)
        if po:
            d['primary_observables'] = po
        return d

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SweepConfig':
        """Dispatch to the correct subclass based on ``mode`` key.

        Raises:
            ValueError: If ``mode`` is missing, unrecognised, or any
                top-level key is not a recognised configuration field
                (silent-drop guardrail — see Layer A of the 2026-04-30
                sweep-pipeline audit).
        """
        from shypn.cli.sweep_single import SingleParameterSweep
        from shypn.cli.sweep_factorial import FactorialSweep
        from shypn.cli.sweep_snapshots import SnapshotsSweep

        mode = data.get('mode')
        if mode is None:
            raise ValueError("sweep config must contain a 'mode' key")

        dispatch = {
            'single': SingleParameterSweep,
            'factorial': FactorialSweep,
            'snapshots': SnapshotsSweep,
        }
        cls = dispatch.get(mode)
        if cls is None:
            raise ValueError(
                f"Unknown sweep mode '{mode}'. "
                f"Supported: {', '.join(dispatch)}"
            )

        # ── Layer A guardrail: reject unknown top-level keys ────────────
        # Computed as the union of the universal top-level keys and the
        # subclass's mode-specific keys. Any leftover key is almost always
        # a typo or a deprecated/unmigrated payload — failing loudly is
        # far safer than silently dropping it (Q1 sweep, run_20260430_135106:
        # 30 reps × 7 conditions × 4 h GPU time wasted because top-level
        # `property_overrides` was silently ignored by this very loader).
        known = set(_UNIVERSAL_TOP_LEVEL_KEYS) | set(
            getattr(cls, 'KNOWN_KEYS', ())
        )
        unknown = set(data.keys()) - known
        if unknown:
            raise ValueError(
                f"Unrecognised top-level keys in sweep config: "
                f"{sorted(unknown)}.\n"
                f"Recognised keys for mode='{mode}': {sorted(known)}.\n"
                f"Hint: per-condition overrides belong under 'snapshots' "
                f"(mode:snapshots) or are derived from 'parameter'/'parameters' "
                f"(mode:single/factorial); sweep-wide constants belong under "
                f"'fixed_overrides'."
            )

        result = cls.from_dict(data)  # type: ignore[attr-defined]
        # Preserve model_path from JSON so CLI can pick it up
        if 'model_path' in data:
            result._raw_model_path = data['model_path']
        # Pull top-level environment events (defined on the Environment
        # Panel of the dispatching client).  Stored as raw dicts; the
        # worker reconstructs Event objects via Event.from_dict().
        events = data.get('events') or []
        if events:
            result.events = list(events)
        # Sweep-wide fixed property overrides (Layer B). Validated as
        # {full_path: numeric_value}. Empty / missing → no overrides.
        fixed = data.get('fixed_overrides') or {}
        if fixed:
            if not isinstance(fixed, dict):
                raise ValueError(
                    f"'fixed_overrides' must be a JSON object "
                    f"({{path: value}}), got {type(fixed).__name__}"
                )
            normalised: Dict[str, float] = {}
            for k, v in fixed.items():
                try:
                    normalised[str(k)] = float(v)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"fixed_overrides[{k!r}] must be numeric, "
                        f"got {v!r} ({exc})"
                    )
            result.fixed_overrides = normalised
        # Hydrate output options if present
        if 'output' in data:
            result.output = OutputOptions.from_dict(data['output'])
        # Pass-through observable reduction config (UI-only; opaque to
        # the engine). Validated as a dict if present.
        po = data.get('primary_observables')
        if po is not None:
            if not isinstance(po, dict):
                raise ValueError(
                    f"'primary_observables' must be a JSON object, "
                    f"got {type(po).__name__}"
                )
            result.primary_observables = dict(po)
        return result

    @staticmethod
    def load(path: Path) -> 'SweepConfig':
        """Load a sweep configuration from a JSON file."""
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return SweepConfig.from_dict(data)


def _build_sim_params(data: Dict[str, Any]) -> SimulationParams:
    """Extract :class:`SimulationParams` from a raw JSON dict."""
    return SimulationParams(
        replicates=int(data.get('replicates', 200)),
        duration=float(data.get('duration', 2000.0)),
        termination=str(data.get('termination', 'deadlock')),
        seed_base=int(data.get('seed_base', 42)),
        tau_epsilon=float(data.get('tau_epsilon', 0.03)),
        max_tau=float(data.get('max_tau', 0.1)),
        time_step=float(data['time_step']) if data.get('time_step') is not None else None,
    )


# ── Top-level schema (Layer A: silent-drop guardrail) ──────────────────
#
# Universal keys accepted at the JSON root regardless of sweep mode.
# Subclasses (SingleParameterSweep, FactorialSweep, SnapshotsSweep) extend
# this set via a class-level ``KNOWN_KEYS`` attribute.  Anything else
# triggers a hard ValueError in :meth:`SweepConfig.from_dict` — see the
# 2026-04-30 sweep-pipeline audit (Layer A) for the rationale.
_UNIVERSAL_TOP_LEVEL_KEYS = frozenset({
    # SimulationParams fields
    'replicates', 'duration', 'termination', 'seed_base',
    'tau_epsilon', 'max_tau', 'time_step',
    # SweepConfig dispatch + plumbing
    'mode', 'model_path', 'events', 'output',
    'fixed_overrides',
    # Optional metadata emitted by ExperimentManager.export_to_json
    'exported_from', 'exported_date',
    # Optional escape hatch for documented superposition (see
    # /memories/repo/hpn_experiment_plan_rule.md and the project
    # instructions §"Sweep ↔ model superposition rule").
    'superposition_intent',
    # Opt-in primary-observable reduction config consumed by the
    # Results Browser (UI side). Persisted as-is into
    # run_<ts>/config.json so observables remain reproducible per run.
    'primary_observables',
})
