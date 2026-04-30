"""Engine-side tests for the 2026-04-30 sweep-pipeline refactor.

Covers Layers A / B / B+ / D from the audit:

* Layer A — :class:`SweepConfig.from_dict` rejects unknown top-level keys
  with a descriptive ``ValueError`` instead of silently dropping them
  (the regression that wasted the Q1 sweep, run_20260430_135106).
* Layer B — Top-level ``fixed_overrides`` flow through
  ``generate_snapshots`` of every mode (single, factorial, snapshots)
  and end up in each snapshot's ``property_overrides`` *before* the
  swept axis layers on.
* Layer B+ — ``param_type='events'`` is accepted by :class:`ParameterSpec`
  and :func:`_apply_event_override` mutates a matching event's ``delay``
  while raising on unknown event ids / unsupported fields.
* Layer D — Override paths are returned by ``_apply_snapshot`` with the
  correct ``source`` tag (sweep / fixed_override / event) and the prior
  model value, ready for ``provenance.json``.
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

# Avoid GTK display lookups when DocumentModel is imported transitively.
os.environ.setdefault('DISPLAY', '')

# Make the repo's ``src/`` importable when tests run from the repo root.
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, 'src'))

from shypn.cli.sweep_config import (  # noqa: E402
    PARAMETER_SWEEP_TYPES,
    ParameterSpec,
    SimulationParams,
    SweepConfig,
)
from shypn.cli.sweep_factorial import FactorialSweep  # noqa: E402
from shypn.cli.sweep_runner import (  # noqa: E402
    SweepRunner,
    _apply_event_override,
    _is_event_path,
)
from shypn.cli.sweep_single import SingleParameterSweep  # noqa: E402
from shypn.cli.sweep_snapshots import SnapshotsSweep  # noqa: E402
from shypn.ui.panels.viability.experiment_manager import (  # noqa: E402
    ExperimentSnapshot,
)


# ── helpers ──────────────────────────────────────────────────────────


def _baseline_snapshot() -> ExperimentSnapshot:
    """A minimal baseline mirroring _capture_baseline()."""
    snap = ExperimentSnapshot('Baseline')
    snap.place_markings = {'P1': 1.0, 'P38': 0.0}
    snap.transition_rates = {'T1': 0.05}
    snap.arc_weights = {'A1': 1.0}
    return snap


class Place:  # noqa: N801 — name must match type-check in property_path_parser
    def __init__(self, pid: str, tokens: float = 0.0,
                 name: str = '') -> None:
        self.id = pid
        self.name = name or pid
        self.tokens = tokens
        self.initial_marking = tokens
        self.initial_tokens = tokens


class Transition:  # noqa: N801
    def __init__(self, tid: str, rate: float = 0.0) -> None:
        self.id = tid
        self.name = tid
        self.rate = rate


class Arc:  # noqa: N801
    def __init__(self, aid: str, weight: float = 1.0) -> None:
        self.id = aid
        self.name = aid
        self.weight = weight


class _FakeEvent:
    def __init__(self, eid: str, delay: float = 0.0,
                 priority: int = 0) -> None:
        self.id = eid
        self.delay = delay
        self.priority = priority


def _fake_model() -> Any:
    return SimpleNamespace(
        places=[Place('P1', 1.0), Place('P38', 0.0)],
        transitions=[Transition('T1', 0.05)],
        arcs=[Arc('A1', 1.0)],
        events=[_FakeEvent('evt_install_disease', delay=0.0)],
    )


# ── Layer A: silent-drop guardrail ───────────────────────────────────


class TestLayerA_UnknownKeysRejected:

    def test_unknown_top_level_key_raises(self):
        # The exact failure mode that wasted Q1: top-level
        # ``property_overrides`` is meaningless and must not be silently
        # accepted.
        cfg = {
            'mode': 'single',
            'replicates': 5,
            'duration': 100.0,
            'parameter': {
                'type': 'places',
                'path': 'P1.initial_marking',
                'values': [1.0, 2.0],
            },
            # Looks plausible — but the loader has never honoured it.
            'property_overrides': {'P38.initial_marking': 0.5},
        }
        with pytest.raises(ValueError, match=r'property_overrides'):
            SweepConfig.from_dict(cfg)

    def test_typo_in_known_key_raises(self):
        cfg = {
            'mode': 'single',
            'replicates': 5,
            'duration': 100.0,
            'paramter': {  # typo
                'type': 'places',
                'path': 'P1.initial_marking',
                'values': [1.0],
            },
        }
        with pytest.raises(ValueError, match=r'paramter'):
            SweepConfig.from_dict(cfg)

    def test_factorial_with_one_axis_rejected(self):
        cfg = {
            'mode': 'factorial',
            'replicates': 5,
            'duration': 100.0,
            'parameters': [
                {
                    'type': 'places',
                    'path': 'P1.initial_marking',
                    'values': [1.0, 2.0],
                },
            ],
        }
        with pytest.raises(ValueError, match=r'\u22652 parameters|>=2 parameters'):
            SweepConfig.from_dict(cfg)


# ── Layer B: fixed_overrides ────────────────────────────────────────


class TestLayerB_FixedOverrides:

    def test_single_merges_fixed_overrides_into_each_snapshot(self):
        cfg = SweepConfig.from_dict({
            'mode': 'single',
            'replicates': 5,
            'duration': 100.0,
            'fixed_overrides': {
                'P38.initial_marking': 0.5,
                'P28.initial_marking': 310.15,
            },
            'parameter': {
                'type': 'places',
                'path': 'P1.initial_marking',
                'values': [1.0, 2.0, 5.0],
            },
        })
        assert isinstance(cfg, SingleParameterSweep)
        assert cfg.fixed_overrides == {
            'P38.initial_marking': 0.5,
            'P28.initial_marking': 310.15,
        }
        snaps = cfg.generate_snapshots(_baseline_snapshot())
        assert len(snaps) == 3
        for snap in snaps:
            # Every condition carries the sweep-wide constants
            assert snap.property_overrides['P38.initial_marking'] == 0.5
            assert snap.property_overrides['P28.initial_marking'] == 310.15
        # Swept axis values still distinct per condition
        assert [s.property_overrides['P1.initial_marking'] for s in snaps] \
            == [1.0, 2.0, 5.0]

    def test_factorial_merges_fixed_overrides(self):
        cfg = SweepConfig.from_dict({
            'mode': 'factorial',
            'replicates': 5,
            'duration': 100.0,
            'fixed_overrides': {'P38.initial_marking': 0.5},
            'parameters': [
                {'type': 'places', 'path': 'P1.initial_marking',
                 'values': [1.0, 2.0]},
                {'type': 'transitions', 'path': 'T1.rate',
                 'values': [0.01, 0.05]},
            ],
        })
        assert isinstance(cfg, FactorialSweep)
        snaps = cfg.generate_snapshots(_baseline_snapshot())
        assert len(snaps) == 4
        for snap in snaps:
            assert snap.property_overrides['P38.initial_marking'] == 0.5

    def test_swept_axis_wins_over_fixed_override_on_collision(self):
        # If a user writes the same path in both, the swept axis is the
        # last write — that's the documented precedence.
        cfg = SweepConfig.from_dict({
            'mode': 'single',
            'replicates': 5,
            'duration': 100.0,
            'fixed_overrides': {'P1.initial_marking': 99.0},
            'parameter': {
                'type': 'places',
                'path': 'P1.initial_marking',
                'values': [1.0, 2.0],
            },
        })
        snaps = cfg.generate_snapshots(_baseline_snapshot())
        assert [s.property_overrides['P1.initial_marking'] for s in snaps] \
            == [1.0, 2.0]

    def test_fixed_overrides_must_be_numeric(self):
        cfg = {
            'mode': 'single',
            'replicates': 5,
            'duration': 100.0,
            'fixed_overrides': {'P38.initial_marking': 'hi'},
            'parameter': {
                'type': 'places',
                'path': 'P1.initial_marking',
                'values': [1.0],
            },
        }
        with pytest.raises(ValueError, match=r'must be numeric'):
            SweepConfig.from_dict(cfg)


# ── Layer B+: events sweep target type ───────────────────────────────


class TestLayerBPlus_EventsSweep:

    def test_events_param_type_accepted(self):
        spec = ParameterSpec(
            param_type='events',
            path='evt_install_disease.delay',
            values=[0.0, 60.0, 600.0],
        )
        assert spec.param_type == 'events'
        # Sanity: the universal type tuple lists it.
        assert 'events' in PARAMETER_SWEEP_TYPES

    def test_event_path_routed_correctly(self):
        assert _is_event_path('evt_loading_dose.delay')
        assert not _is_event_path('P1.initial_marking')
        assert not _is_event_path('T5.rate')

    def test_apply_event_override_mutates_delay(self):
        model = _fake_model()
        prior = _apply_event_override(
            model, 'evt_install_disease.delay', 60.0
        )
        assert prior == 0.0
        assert model.events[0].delay == 60.0

    def test_apply_event_override_unknown_event(self):
        model = _fake_model()
        with pytest.raises(ValueError, match=r"evt_unknown.* not found"):
            _apply_event_override(model, 'evt_unknown.delay', 1.0)

    def test_apply_event_override_unsupported_field(self):
        model = _fake_model()
        with pytest.raises(ValueError, match=r"is not sweepable"):
            _apply_event_override(
                model, 'evt_install_disease.assignments', 1.0
            )

    def test_single_sweep_with_events_axis_loads(self):
        cfg = SweepConfig.from_dict({
            'mode': 'single',
            'replicates': 5,
            'duration': 100.0,
            'parameter': {
                'type': 'events',
                'path': 'evt_install_disease.delay',
                'values': [0.0, 60.0, 600.0],
            },
        })
        snaps = cfg.generate_snapshots(_baseline_snapshot())
        assert len(snaps) == 3
        assert snaps[1].property_overrides['evt_install_disease.delay'] == 60.0


# ── Layer D: parameter_sources audit ─────────────────────────────────


class TestLayerD_ParameterSources:

    def test_apply_snapshot_returns_source_map(self):
        baseline = _baseline_snapshot()
        snap = ExperimentSnapshot('cond_A')
        snap.place_markings = dict(baseline.place_markings)
        snap.transition_rates = dict(baseline.transition_rates)
        snap.arc_weights = dict(baseline.arc_weights)
        snap.property_overrides = {
            'P1.initial_marking': 5.0,       # sweep axis
            'P38.initial_marking': 0.5,      # fixed override
            'evt_install_disease.delay': 60.0,  # event override
        }
        snap.swept_parameter = {
            'type': 'places',
            'id': 'P1.initial_marking',
            'name': 'P1.initial_marking',
            'value': 5.0,
        }
        model = _fake_model()
        sources = SweepRunner._apply_snapshot(model, snap, baseline)

        assert set(sources) == {
            'P1.initial_marking',
            'P38.initial_marking',
            'evt_install_disease.delay',
        }
        assert sources['P1.initial_marking']['source'] == 'sweep'
        assert sources['P1.initial_marking']['value'] == 5.0
        assert sources['P1.initial_marking']['prior'] == 1.0

        assert sources['P38.initial_marking']['source'] == 'fixed_override'
        assert sources['P38.initial_marking']['prior'] == 0.0

        assert sources['evt_install_disease.delay']['source'] == 'event'
        assert sources['evt_install_disease.delay']['value'] == 60.0
        assert sources['evt_install_disease.delay']['prior'] == 0.0

        # And the model state actually changed.
        assert model.places[0].tokens == 5.0
        assert model.places[1].tokens == 0.5
        assert model.events[0].delay == 60.0
