"""Snapshot-list sweep strategy.

Loads a pre-built list of :class:`ExperimentSnapshot` objects from a JSON
file exported by the GUI (``ExperimentManager.export_to_json``).  This
enables a **design-in-GUI, run-on-server** workflow.

JSON example::

    {
      "mode": "snapshots",
      "replicates": 200,
      "duration": 2000.0,
      "snapshots_file": "exported_snapshots.json"
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from shypn.cli.sweep_config import (
    SimulationParams,
    SweepConfig,
    _build_sim_params,
)
from shypn.ui.panels.viability.experiment_manager import ExperimentSnapshot


class SnapshotsSweep(SweepConfig):
    """Run conditions defined by pre-exported experiment snapshots."""

    def __init__(
        self,
        sim_params: SimulationParams,
        snapshots_path: Path,
    ) -> None:
        super().__init__(sim_params)
        self.snapshots_path = snapshots_path
        self._cached: Optional[List[ExperimentSnapshot]] = None

    # ── private helpers ──────────────────────────────────────────────

    def _load_snapshots(self) -> List[ExperimentSnapshot]:
        if self._cached is not None:
            return self._cached
        with open(self.snapshots_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        snaps = [
            ExperimentSnapshot.from_dict(s)
            for s in data.get('snapshots', [])
        ]
        if not snaps:
            raise ValueError(
                f"No snapshots found in {self.snapshots_path}"
            )
        self._cached = snaps
        return snaps

    # ── SweepConfig interface ────────────────────────────────────────

    def generate_snapshots(
        self,
        baseline: ExperimentSnapshot,
    ) -> List[ExperimentSnapshot]:
        return self._load_snapshots()

    def describe(self) -> str:
        return (
            f"Snapshots sweep: {self.condition_count()} conditions "
            f"from {self.snapshots_path.name}"
        )

    def condition_count(self) -> int:
        return len(self._load_snapshots())

    # ── serialisation ────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['mode'] = 'snapshots'
        d['snapshots_file'] = str(self.snapshots_path)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SnapshotsSweep':
        sim = _build_sim_params(data)
        path = Path(data['snapshots_file'])
        return cls(sim_params=sim, snapshots_path=path)
