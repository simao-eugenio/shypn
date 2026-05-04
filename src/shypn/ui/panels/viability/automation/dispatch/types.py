"""Typed value objects shared by the dispatch package.

Keeping these as plain dataclasses (no dependency on Gtk, BatchExecutor,
or RemoteSweepDispatcher) makes them trivially unit-testable and
serialisable.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional


class DispatchKind(str, enum.Enum):
    """Discriminator for which transport the controller uses."""
    LOCAL = 'local'
    REMOTE = 'remote'


@dataclass
class SimulationParams:
    """Engine + sweep-runtime parameters captured from the sweep builder.

    A single shape used by both local and remote dispatch paths so widget
    drift between them is impossible. ``time_step=None`` means *engine
    auto-dt* (capped at ``SimulationSettings.DEFAULT_DT_AUTO_CAP``).
    """

    # Sweep-shape
    replicates: int = 200
    duration: float = 2000.0
    termination: str = 'time_only'
    seed_base: int = 42
    output_tier: str = 'G3'

    # Solver
    use_tau_leaping: bool = True   # τ-leaping is the only stochastic engine
    tau_epsilon: float = 0.03
    max_tau: float = 0.1
    time_step: Optional[float] = None

    # Local-only data-compression knobs (ignored by remote)
    compressor_epsilon: float = 0.02
    compressor_min_gap: float = 5.0
    compressor_max_gap: float = 300.0

    # Local execution
    use_parallel: bool = True

    def to_dict(self) -> Dict[str, object]:
        """Plain dict for engine/manager APIs that take ``**kwargs``."""
        return {
            'replicates': self.replicates,
            'duration': self.duration,
            'termination': self.termination,
            'seed_base': self.seed_base,
            'tau_epsilon': self.tau_epsilon,
            'max_tau': self.max_tau,
            'time_step': self.time_step,
            'output_tier': self.output_tier,
        }


# (queue_row_index, experiment_name, snapshot_index)
ExperimentRef = Tuple[int, str, int]


@dataclass
class DispatchRequest:
    """All inputs required to start one sweep dispatch (local or remote).

    Built by the category panel; consumed by a ``SweepDispatchController``
    subclass via ``start(request)``.
    """
    experiments: List[ExperimentRef]
    sim_params: SimulationParams
    model_filepath: str
    project_folder: str
    events: List[Dict] = field(default_factory=list)
    fixed_overrides: Dict[str, float] = field(default_factory=dict)

    # Remote-only (ignored by local controller)
    ssh_password: Optional[str] = None
