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


# ── Abstract base ─────────────────────────────────────────────────────────

class SweepConfig(ABC):
    """Abstract base for all sweep configuration strategies.

    Subclasses must implement :meth:`generate_snapshots` which produces
    the concrete list of :class:`ExperimentSnapshot` objects — one per
    condition to simulate.

    The class also owns the shared :class:`SimulationParams` and handles
    JSON (de)serialisation dispatch.
    """

    def __init__(self, sim_params: SimulationParams) -> None:
        self.sim_params = sim_params

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
        return {
            'replicates': self.sim_params.replicates,
            'duration': self.sim_params.duration,
            'termination': self.sim_params.termination,
            'seed_base': self.sim_params.seed_base,
            'tau_epsilon': self.sim_params.tau_epsilon,
            'max_tau': self.sim_params.max_tau,
            'time_step': self.sim_params.time_step,
        }

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
