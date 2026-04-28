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


@dataclass(frozen=True)
class ParameterSpec:
    """One swept parameter axis: type, property path, and values."""

    param_type: str          # 'places', 'transitions', 'arcs'
    path: str                # e.g. 'P_EPO.initial_marking' or 'EPO_external.initial_marking'
    values: List[float]

    def __post_init__(self) -> None:
        if self.param_type not in ('places', 'transitions', 'arcs'):
            raise ValueError(
                f"param_type must be places|transitions|arcs, got '{self.param_type}'"
            )
        if not self.values:
            raise ValueError("values list must not be empty")


# ── Output granularity ───────────────────────────────────────────────────

# Output tier hierarchy — controls per-condition disk footprint.
# Each tier is the previous tier plus more artefacts.
#
#   G0 — summary.csv only (run-level, one row per condition)
#   G1 — + replicates.csv (per-replicate endpoint scalars: *_final, *_firings)
#   G2 — + statistics.json with endpoint-only stats (no per-step arrays)
#   G3 — + statistics.json with full per-step time-series stats   ← current default
#   G4 — RESERVED: + per-replicate trajectory CSVs (every dt, all places)
#   G5 — RESERVED: + covariance / cross-correlation matrices
#
# Backwards compatibility: missing output_tier in config → G3.
OUTPUT_TIERS = ('G0', 'G1', 'G2', 'G3', 'G4', 'G5')
DEFAULT_OUTPUT_TIER = 'G3'


@dataclass(frozen=True)
class OutputOptions:
    """Run-level output granularity controls.

    Decoupled from :class:`SimulationParams` because granularity is a
    storage / analysis concern, not an engine concern. The Viability
    Panel binds to this; engines stay oblivious.
    """

    tier: str = DEFAULT_OUTPUT_TIER
    # G2/G4 future use:
    trajectory_places: Optional[List[str]] = None   # subset to record (G4)
    trajectory_thin_seconds: Optional[float] = None  # downsample dt (G4)

    def __post_init__(self) -> None:
        if self.tier not in OUTPUT_TIERS:
            raise ValueError(
                f"output_tier must be one of {OUTPUT_TIERS}, got '{self.tier}'"
            )

    # Convenience predicates the worker uses to gate writes.
    @property
    def write_replicates_csv(self) -> bool:
        return self.tier >= 'G1'

    @property
    def write_statistics_json(self) -> bool:
        return self.tier >= 'G2'

    @property
    def statistics_endpoint_only(self) -> bool:
        return self.tier == 'G2'

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
        # Output granularity (only emitted if non-default to keep configs tidy)
        if self.output.tier != DEFAULT_OUTPUT_TIER \
                or self.output.trajectory_places is not None \
                or self.output.trajectory_thin_seconds is not None:
            d['output'] = self.output.to_dict()
        return d

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SweepConfig':
        """Dispatch to the correct subclass based on ``mode`` key.

        Raises:
            ValueError: If ``mode`` is missing or unrecognised.
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
        # Hydrate output options if present
        if 'output' in data:
            result.output = OutputOptions.from_dict(data['output'])
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
