"""G4 — extend CBD maintenance dose protocol from 18 h to 7 days.

Issue: model has only evt_maint_1/2/3 → covers t = 6/12/18 h.
For 7-d sweeps (Q4+) the model runs 6 days untreated.

Patch: replace 3 maintenance events with 27 maintenance events, one
per DOSE_INTERVAL up to 7 d (= 28 dose periods including the loading
dose at t=0). Trigger expressions use ``t > N * DOSE_INTERVAL`` so the
edge-trigger fires reliably even with τ-leaping's variable time steps
(the trigger stays True forever after crossing → fires exactly once).

Usage:
    python workspace/projects/canabidiol/scripts/g4_extend_dose_protocol.py

Writes:
    workspace/projects/canabidiol/models/canabidiol-q1-testable.shy
        (in-place; .bak.preG4 saved before patching)
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path

MODEL = Path(__file__).resolve().parents[1] / 'models' / 'canabidiol-q1-testable.shy'
N_MAINT_DOSES = 27   # t = 6h, 12h, ..., 162h (load at t=0 + 27 maint = 28 events covering 168h)


def main() -> None:
    backup = MODEL.with_suffix('.shy.bak.preG4')
    shutil.copy2(MODEL, backup)
    print(f'Backup: {backup}')

    m = json.loads(MODEL.read_text())

    # Remove all existing maint events, keep evt_load and disease-install events
    before = len(m['events'])
    m['events'] = [e for e in m['events'] if not e['id'].startswith('evt_maint_')]
    removed = before - len(m['events'])
    print(f'Removed {removed} legacy maint events')

    # Generate N_MAINT_DOSES new maintenance events
    template = {
        'name': None,                          # set per event
        'trigger': None,                       # set per event
        'delay': 0.0,
        'use_values_from_trigger_time': True,
        'priority': 0,
        'assignments': {'CBD_plasma': 'CBD_plasma + MAINT_DOSE'},
        'metadata': {
            'group': 'maintenance_dose',
            'target': 'CBD_plasma',
            'purpose': 'G4: chronic 7-d dosing — one event per 6h interval',
        },
    }

    for n in range(1, N_MAINT_DOSES + 1):
        evt = dict(template)
        evt['id'] = f'evt_maint_{n:02d}'
        evt['name'] = f'evt_maint_{n:02d}'
        evt['trigger'] = f't > {n} * DOSE_INTERVAL'
        evt['metadata'] = dict(template['metadata'], dose_index=n,
                               nominal_time_hours=n * 6)
        m['events'].append(evt)

    print(f'Added {N_MAINT_DOSES} new maintenance events')

    MODEL.write_text(json.dumps(m, indent=2))

    # Roundtrip checks
    m2 = json.loads(MODEL.read_text())
    maint_evts = [e for e in m2['events'] if e['id'].startswith('evt_maint_')]
    assert len(maint_evts) == N_MAINT_DOSES, \
        f'expected {N_MAINT_DOSES}, got {len(maint_evts)}'
    for n, e in enumerate(maint_evts, 1):
        assert e['id'] == f'evt_maint_{n:02d}'
        assert e['trigger'] == f't > {n} * DOSE_INTERVAL'
        assert e['assignments'] == {'CBD_plasma': 'CBD_plasma + MAINT_DOSE'}
    # evt_load preserved
    load = next(e for e in m2['events'] if e['id'] == 'evt_load')
    assert load['assignments']['CBD_plasma'] == 'CBD_plasma + LOADING_DOSE'

    print('Roundtrip OK')
    print(f'Total events now: {len(m2["events"])}')
    print('First / last 3 maint events:')
    for e in maint_evts[:3] + ['…'] + maint_evts[-3:]:
        if isinstance(e, str):
            print(f'  {e}')
        else:
            print(f'  {e["id"]}  trigger={e["trigger"]}')


if __name__ == '__main__':
    main()
