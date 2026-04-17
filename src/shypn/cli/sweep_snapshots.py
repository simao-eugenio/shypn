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
    """Run conditions defined by pre-exported experiment snapshots.

    Supports two modes:
    - **file-based**: ``snapshots_file`` points to an external JSON file.
    - **inline**: ``snapshots`` list is embedded directly in the config.
    """

    def __init__(
        self,
        sim_params: SimulationParams,
        snapshots_path: Optional[Path] = None,
        inline_snapshots: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(sim_params)
        self.snapshots_path = snapshots_path
        self._inline_snapshots = inline_snapshots
        self._cached: Optional[List[ExperimentSnapshot]] = None

    # ── private helpers ──────────────────────────────────────────────

    def _load_snapshots(self) -> List[ExperimentSnapshot]:
        if self._cached is not None:
            return self._cached

        if self._inline_snapshots is not None:
            raw = self._inline_snapshots
        elif self.snapshots_path is not None:
            with open(self.snapshots_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            raw = data.get('snapshots', [])
        else:
            raw = []

        snaps = [ExperimentSnapshot.from_dict(s) for s in raw]
        if not snaps:
            src = self.snapshots_path or 'inline config'
            raise ValueError(f"No snapshots found in {src}")
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
        if self.snapshots_path is not None:
            d['snapshots_file'] = str(self.snapshots_path)
        if self._inline_snapshots is not None:
            d['snapshots'] = self._inline_snapshots
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SnapshotsSweep':
        sim = _build_sim_params(data)
        path = Path(data['snapshots_file']) if 'snapshots_file' in data else None
        inline = data.get('snapshots')  # list of snapshot dicts, or None
        if path is None and inline is None:
            raise ValueError(
                "snapshots sweep config must contain either "
                "'snapshots_file' or 'snapshots'"
            )
        return cls(sim_params=sim, snapshots_path=path,
                   inline_snapshots=inline)
