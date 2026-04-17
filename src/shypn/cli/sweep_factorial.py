"""Factorial (multi-parameter) sweep strategy.

Generates the Cartesian product of N parameter axes, producing one
:class:`ExperimentSnapshot` per combination.

JSON example::

    {
      "mode": "factorial",
      "replicates": 100,
      "duration": 2000.0,
      "parameters": [
        {"type": "places", "path": "P_EPO.initial_marking", "values": [0, 50, 500]},
        {"type": "places", "path": "P_GCSF.initial_marking", "values": [10, 50, 100]}
      ]
    }
"""

from __future__ import annotations

import itertools
from typing import Any, Dict, List, Tuple

from shypn.cli.sweep_config import (
    ParameterSpec,
    SimulationParams,
    SweepConfig,
    _build_sim_params,
)
from shypn.ui.panels.viability.experiment_manager import ExperimentSnapshot
from shypn.ui.panels.viability.automation.property_path_parser import parse_property_path


class FactorialSweep(SweepConfig):
    """Full factorial design across multiple parameter axes."""

    def __init__(
        self,
        sim_params: SimulationParams,
        parameters: List[ParameterSpec],
    ) -> None:
        super().__init__(sim_params)
        if len(parameters) < 2:
            raise ValueError("Factorial sweep requires at least 2 parameters")
        self.parameters = parameters

    # ── SweepConfig interface ────────────────────────────────────────

    def generate_snapshots(
        self,
        baseline: ExperimentSnapshot,
    ) -> List[ExperimentSnapshot]:
        parsed = [
            (spec, *parse_property_path(spec.path))
            for spec in self.parameters
        ]
        # Cartesian product of all value lists
        axes_values: List[List[float]] = [spec.values for spec in self.parameters]
        combinations: List[Tuple[float, ...]] = list(itertools.product(*axes_values))

        snapshots: List[ExperimentSnapshot] = []
        for combo in combinations:
            parts = [
                f"{spec.path}={v:.6g}"
                for spec, v in zip(self.parameters, combo)
            ]
            name = ", ".join(parts)
            snap = ExperimentSnapshot(name)
            snap.place_markings = baseline.place_markings.copy()
            snap.arc_weights = baseline.arc_weights.copy()
            snap.transition_rates = baseline.transition_rates.copy()
            snap.property_overrides = getattr(baseline, 'property_overrides', {}).copy()

            for (spec, obj_id, prop_name), value in zip(parsed, combo):
                snap.property_overrides[f"{obj_id}.{prop_name}"] = value

            snap.swept_parameter = {
                'type': 'factorial',
                'id': '; '.join(s.path for s in self.parameters),
                'name': name,
                'value': list(combo),
            }
            snapshots.append(snap)

        return snapshots

    def describe(self) -> str:
        dims = " × ".join(
            f"{s.path}({len(s.values)})" for s in self.parameters
        )
        return f"Factorial sweep: {dims} = {self.condition_count()} conditions"

    def condition_count(self) -> int:
        total = 1
        for spec in self.parameters:
            total *= len(spec.values)
        return total

    # ── serialisation ────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['mode'] = 'factorial'
        d['parameters'] = [
            {'type': s.param_type, 'path': s.path, 'values': s.values}
            for s in self.parameters
        ]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FactorialSweep':
        sim = _build_sim_params(data)
        specs = [
            ParameterSpec(
                param_type=p['type'],
                path=p['path'],
                values=[float(v) for v in p['values']],
            )
            for p in data['parameters']
        ]
        return cls(sim_params=sim, parameters=specs)
