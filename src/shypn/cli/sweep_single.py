"""Single-parameter sweep strategy.

Varies one parameter across a list of values, producing one
:class:`ExperimentSnapshot` per value.

JSON example::

    {
      "mode": "single",
      "replicates": 200,
      "duration": 2000.0,
      "parameter": {
        "type": "places",
        "path": "P_EPO.initial_marking",
        "values": [0, 10, 50, 100, 500]
      }
    }
"""

from __future__ import annotations

from typing import Any, Dict, List

from shypn.cli.sweep_config import (
    ParameterSpec,
    SimulationParams,
    SweepConfig,
    _build_sim_params,
)
from shypn.ui.panels.viability.experiment_manager import ExperimentSnapshot
from shypn.ui.panels.viability.automation.property_path_parser import parse_property_path


class SingleParameterSweep(SweepConfig):
    """Sweep a single parameter across a list of values."""

    def __init__(
        self,
        sim_params: SimulationParams,
        parameter: ParameterSpec,
    ) -> None:
        super().__init__(sim_params)
        self.parameter = parameter

    # ── SweepConfig interface ────────────────────────────────────────

    def generate_snapshots(
        self,
        baseline: ExperimentSnapshot,
    ) -> List[ExperimentSnapshot]:
        obj_id, prop_name = parse_property_path(self.parameter.path)
        snapshots: List[ExperimentSnapshot] = []

        for value in self.parameter.values:
            name = f"{self.parameter.path}={value:.6g}"
            snap = ExperimentSnapshot(name)
            snap.place_markings = baseline.place_markings.copy()
            snap.arc_weights = baseline.arc_weights.copy()
            snap.transition_rates = baseline.transition_rates.copy()
            snap.property_overrides = getattr(baseline, 'property_overrides', {}).copy()
            snap.property_overrides[f"{obj_id}.{prop_name}"] = value
            snap.swept_parameter = {
                'type': self.parameter.param_type,
                'id': self.parameter.path,
                'name': self.parameter.path,
                'value': value,
            }
            snapshots.append(snap)

        return snapshots

    def describe(self) -> str:
        vals = self.parameter.values
        return (
            f"Single sweep: {self.parameter.path} "
            f"({len(vals)} values: {vals[0]:.6g}..{vals[-1]:.6g})"
        )

    def condition_count(self) -> int:
        return len(self.parameter.values)

    # ── serialisation ────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['mode'] = 'single'
        d['parameter'] = {
            'type': self.parameter.param_type,
            'path': self.parameter.path,
            'values': self.parameter.values,
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SingleParameterSweep':
        sim = _build_sim_params(data)
        p = data['parameter']
        spec = ParameterSpec(
            param_type=p['type'],
            path=p['path'],
            values=[float(v) for v in p['values']],
        )
        return cls(sim_params=sim, parameter=spec)
