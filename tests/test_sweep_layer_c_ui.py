"""UI-side wiring tests for Layer C of the 2026-04-30 sweep refactor.

Coverage:

* ``ExperimentManager.export_sweep_config`` round-trips a non-empty
  ``fixed_overrides`` block at the top level of the exported config and
  the engine's :class:`SweepConfig` accepts it without raising.
* ``ParameterSweepBuilder.detect_sweep_event_collisions`` flags the four
  collision codes (R1 / R3 / R3b / R4) at the right severity.

GTK is required only for the second group; we skip it if the user has
no display because constructing :class:`ParameterSweepBuilder` involves
real Gtk widgets.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, 'src'))

from shypn.cli.sweep_config import SweepConfig  # noqa: E402
from shypn.cli.sweep_single import SingleParameterSweep  # noqa: E402
from shypn.ui.panels.viability.experiment_manager import (  # noqa: E402
    ExperimentManager,
    ExperimentSnapshot,
)


# ── ExperimentManager.export_sweep_config(fixed_overrides=…) ────────


class TestExportFixedOverrides:

    def _seeded_manager(self) -> ExperimentManager:
        mgr = ExperimentManager()
        mgr.snapshots.clear()
        snap = ExperimentSnapshot('cond_A')
        snap.place_markings = {'P1': 1.0}
        snap.swept_parameter = {
            'type': 'places',
            'id': 'P1.initial_marking',
            'name': 'P1.initial_marking',
            'value': 1.0,
        }
        mgr.snapshots.append(snap)
        snap2 = ExperimentSnapshot('cond_B')
        snap2.place_markings = {'P1': 2.0}
        snap2.swept_parameter = {
            'type': 'places',
            'id': 'P1.initial_marking',
            'name': 'P1.initial_marking',
            'value': 2.0,
        }
        mgr.snapshots.append(snap2)
        return mgr

    def test_fixed_overrides_round_trip(self, tmp_path):
        mgr = self._seeded_manager()
        out = tmp_path / 'sweep_config.json'
        mgr.export_sweep_config(
            filepath=str(out),
            model_path='models/test.shy',
            replicates=3,
            duration=10.0,
            termination='deadlock',
            seed_base=1,
            tau_epsilon=0.03,
            max_tau=0.1,
            fixed_overrides={
                'P38.initial_marking': 0.5,
                'P28.initial_marking': 310.15,
            },
        )
        doc = json.loads(out.read_text())
        assert doc['fixed_overrides'] == {
            'P38.initial_marking': 0.5,
            'P28.initial_marking': 310.15,
        }

        # And the engine loader accepts it.
        cfg = SweepConfig.from_dict(doc)
        assert isinstance(cfg, SingleParameterSweep)
        assert cfg.fixed_overrides == {
            'P38.initial_marking': 0.5,
            'P28.initial_marking': 310.15,
        }

    def test_fixed_overrides_omitted_when_empty(self, tmp_path):
        mgr = self._seeded_manager()
        out = tmp_path / 'sweep_config.json'
        mgr.export_sweep_config(
            filepath=str(out),
            model_path='models/test.shy',
            replicates=1, duration=1.0, termination='deadlock',
            seed_base=0, tau_epsilon=0.03, max_tau=0.1,
            fixed_overrides={},
        )
        doc = json.loads(out.read_text())
        assert 'fixed_overrides' not in doc

    def test_export_rejects_non_numeric_fixed_override(self, tmp_path):
        mgr = self._seeded_manager()
        out = tmp_path / 'sweep_config.json'
        with pytest.raises(ValueError, match=r'numeric'):
            mgr.export_sweep_config(
                filepath=str(out),
                model_path='m.shy',
                replicates=1, duration=1.0, termination='deadlock',
                seed_base=0, tau_epsilon=0.03, max_tau=0.1,
                fixed_overrides={'P38.initial_marking': 'oops'},
            )


# ── ParameterSweepBuilder.detect_sweep_event_collisions ─────────────


_GTK_AVAILABLE = True
try:  # pragma: no cover — environment-dependent
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk  # noqa: F401
    if not os.environ.get('DISPLAY'):
        _GTK_AVAILABLE = False
except Exception:
    _GTK_AVAILABLE = False


@pytest.mark.skipif(
    not _GTK_AVAILABLE,
    reason='GTK display required for ParameterSweepBuilder construction',
)
class TestCollisionDetector:

    def _builder(self):
        from shypn.ui.panels.viability.automation.parameter_sweep_builder \
            import ParameterSweepBuilder
        return ParameterSweepBuilder()

    def _snap_targeting(self, path, value=1.0):
        snap = ExperimentSnapshot('c')
        snap.swept_parameter = {
            'type': 'places' if not path.startswith('evt_') else 'events',
            'id': path,
            'name': path,
            'value': value,
        }
        return snap

    def test_R1_sweep_writes_same_place_as_event(self):
        b = self._builder()
        snap = self._snap_targeting('Aβ_Monomer.initial_marking', 5.0)
        events = [{
            'id': 'evt_install_disease',
            'enabled': True,
            'assignments': {'Aβ_Monomer': 'Disease_Severity * 5.0'},
        }]
        issues = b.detect_sweep_event_collisions(
            snapshots=[snap], events=events, fixed_overrides={},
        )
        codes = [i['code'] for i in issues]
        assert 'R1' in codes
        r1 = next(i for i in issues if i['code'] == 'R1')
        assert r1['severity'] == 'error'

    def test_R1_fired_on_fixed_override_collision_too(self):
        b = self._builder()
        events = [{
            'id': 'evt_x',
            'enabled': True,
            'assignments': {'Aβ_Monomer': '5.0'},
        }]
        issues = b.detect_sweep_event_collisions(
            snapshots=[], events=events,
            fixed_overrides={'Aβ_Monomer.initial_marking': 1.0},
        )
        assert any(i['code'] == 'R1' for i in issues)

    def test_R3_warns_when_event_disabled(self):
        b = self._builder()
        snap = self._snap_targeting('evt_install_disease.delay', 60.0)
        events = [{
            'id': 'evt_install_disease',
            'enabled': False,
            'assignments': {'Aβ_Monomer': '5.0'},
        }]
        issues = b.detect_sweep_event_collisions(
            snapshots=[snap], events=events, fixed_overrides={},
        )
        # The disabled event still defines an assignment to Aβ_Monomer
        # but the sweep target is the event's own delay field — no R1.
        codes = [i['code'] for i in issues]
        assert 'R3' in codes
        assert all(c != 'R1' for c in codes)

    def test_R3b_errors_on_unknown_event_id(self):
        b = self._builder()
        snap = self._snap_targeting('evt_does_not_exist.delay', 1.0)
        issues = b.detect_sweep_event_collisions(
            snapshots=[snap], events=[], fixed_overrides={},
        )
        codes = [i['code'] for i in issues]
        assert 'R3b' in codes

    def test_R4_warns_on_two_events_writing_same_target(self):
        b = self._builder()
        events = [
            {'id': 'evt_a', 'enabled': True,
             'assignments': {'Aβ_Monomer': '5.0'}},
            {'id': 'evt_b', 'enabled': True,
             'assignments': {'Aβ_Monomer': '7.0'}},
        ]
        issues = b.detect_sweep_event_collisions(
            snapshots=[], events=events, fixed_overrides={},
        )
        assert any(i['code'] == 'R4' for i in issues)

    def test_clean_config_yields_no_issues(self):
        b = self._builder()
        snap = self._snap_targeting('Disease_Severity.initial_marking', 0.5)
        events = [{
            'id': 'evt_install_disease',
            'enabled': True,
            'assignments': {'Aβ_Monomer': 'Disease_Severity * 5.0'},
        }]
        # Sweep targets a ▢ parameter place; event reads it but writes
        # to Aβ_Monomer.  This is the canonical Pattern A bridge — must
        # not raise R1.
        issues = b.detect_sweep_event_collisions(
            snapshots=[snap], events=events, fixed_overrides={},
        )
        assert all(i['severity'] != 'error' for i in issues)
