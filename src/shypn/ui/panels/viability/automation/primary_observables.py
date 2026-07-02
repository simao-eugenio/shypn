"""Primary-observable reduction for the Results Browser.

Reads an optional ``primary_observables`` block from a sweep
``config.json`` and reduces a per-condition results directory
(``statistics.json`` + ``replicates.csv``) to scalar observables that
the GUI can render as columns and export to CSV.

Sweep-config schema (all fields optional)::

    "primary_observables": {
      "endpoint_place":   "Outer_coat",        # place name or id
      "endpoint_label":   "Outer coat (final)",
      "first_crossing": {
        "place":     "Mature_spore",
        "threshold": 1.0,
        "time_unit": "min",                    # or "s"
        "label":     "t1 Mature spore (min)"
      }
    }

If the block is absent the helpers return ``{}`` and the browser
columns stay blank — so this is fully opt-in per project.
"""
from __future__ import annotations

import csv
import json
import math
import statistics as _stats
from pathlib import Path
from typing import Optional


def load_place_name_to_id(run_dir: Path) -> dict:
    """Build a ``{place_name: place_id}`` map from ``model_snapshot.shy``.

    Returns an empty dict if the snapshot is missing or malformed —
    the caller will then fall back to treating observable specs as
    raw place ids.
    """
    snap = run_dir / 'model_snapshot.shy'
    if not snap.is_file():
        return {}
    try:
        m = json.loads(snap.read_text())
    except Exception:
        return {}
    out: dict = {}
    for p in m.get('places', []):
        nm = p.get('name')
        pid = p.get('id')
        if nm and pid:
            out[nm] = pid
    return out


def load_run_config(run_dir: Path) -> dict:
    """Read ``run_dir/config.json`` if present, else ``{}``.

    Handles two layouts:

    * **Wrapped** (current writer ``SweepOutputManager.save_config``)::

          {"sweep_config": {...full sweep config...},
           "model_path": "...", "timestamp": "..."}

    * **Flat** (legacy / hand-written): the sweep-config keys live at
      the top level of the file.

    The returned dict is the inner sweep-config (with the
    ``primary_observables`` block at the top level) so callers can
    just do ``cfg.get('primary_observables')`` regardless of layout.
    """
    cfg_path = run_dir / 'config.json'
    if not cfg_path.is_file():
        return {}
    try:
        raw = json.loads(cfg_path.read_text())
    except Exception:
        return {}
    if isinstance(raw, dict) and 'sweep_config' in raw \
            and isinstance(raw['sweep_config'], dict):
        return raw['sweep_config']
    return raw


def load_project_observables_fallback(run_dir: Path) -> dict:
    """Fallback when the run's snapshotted config has no observables.

    Walks up from ``run_dir`` to find the project root
    (``<project>/experiments/results/run_<ts>``) and reads the
    project's live ``sweep_config*.json``. Returns the
    ``primary_observables`` block of the first matching file, or
    ``{}`` if none exists.

    This lets us retroactively render observables for runs that
    finished before the block existed in the source config.
    """
    # run_dir = .../<project>/experiments/results/run_<ts>
    try:
        project_root = run_dir.parent.parent.parent
    except Exception:
        return {}
    if not project_root.is_dir():
        return {}
    for cfg_file in sorted(project_root.glob('sweep_config*.json')):
        try:
            data = json.loads(cfg_file.read_text())
        except Exception:
            continue
        po = data.get('primary_observables')
        if po:
            return po
    return {}


def _resolve_pid(spec: str, name_to_id: dict) -> Optional[str]:
    """Accept either a place id (``P23``) or a place name (``Outer_coat``)."""
    if spec in name_to_id.values():
        return spec
    return name_to_id.get(spec)


def _first_crossing(times, values, threshold) -> float:
    for t, v in zip(times, values):
        try:
            if float(v) >= threshold:
                return float(t)
        except (TypeError, ValueError):
            continue
    return math.nan


def compute_observables(
    cond_dir: Path,
    obs_cfg: dict,
    name_to_id: dict,
) -> dict:
    """Compute primary observables for one condition.

    Returns a dict of the shape::

        {
          'endpoint':       {'species', 'mean', 'std', 'n', 'label'},
          'first_crossing': {'species', 'threshold', 'time_s',
                             'time_display', 'time_unit', 'label'},
        }

    Either key may be absent if the corresponding config block is
    missing or the underlying data cannot be located. Returns ``{}``
    when no observables are configured at all.
    """
    if not obs_cfg:
        return {}
    stats_path = cond_dir / 'statistics.json'
    if not stats_path.is_file():
        return {}
    try:
        stats = json.loads(stats_path.read_text())
    except Exception:
        return {}

    times = stats.get('time_points', []) or []
    species = stats.get('species_statistics', {}) or {}

    out: dict = {}

    # ── endpoint (final value of mean trajectory; std from replicates.csv) ──
    ep_spec = obs_cfg.get('endpoint_place')
    if ep_spec:
        pid = _resolve_pid(ep_spec, name_to_id)
        if pid and pid in species:
            mean_traj = species[pid].get('mean') or []
            std_traj = species[pid].get('std') or []

            mean_v: Optional[float] = None
            std_v: Optional[float] = None
            n = stats.get('n_replicates', 0)

            rep_csv = cond_dir / 'replicates.csv'
            col = f'{ep_spec}_final'
            if rep_csv.is_file():
                vals: list[float] = []
                try:
                    with rep_csv.open() as f:
                        for row in csv.DictReader(f):
                            v = row.get(col)
                            if v not in (None, ''):
                                try:
                                    vals.append(float(v))
                                except ValueError:
                                    pass
                except Exception:
                    vals = []
                if vals:
                    mean_v = _stats.mean(vals)
                    std_v = _stats.stdev(vals) if len(vals) > 1 else 0.0
                    n = len(vals)

            if mean_v is None and mean_traj:
                try:
                    mean_v = float(mean_traj[-1])
                    std_v = float(std_traj[-1]) if std_traj else 0.0
                except (TypeError, ValueError):
                    mean_v = None

            if mean_v is not None:
                out['endpoint'] = {
                    'species': ep_spec,
                    'mean': mean_v,
                    'std': std_v if std_v is not None else 0.0,
                    'n': n,
                    'label': obs_cfg.get('endpoint_label', f'{ep_spec} (final)'),
                }

    # ── first_crossing (earliest time mean trajectory >= threshold) ──
    fc = obs_cfg.get('first_crossing')
    if isinstance(fc, dict):
        spec = fc.get('place')
        thr = float(fc.get('threshold', 1.0))
        unit = fc.get('time_unit', 's')
        pid = _resolve_pid(spec, name_to_id) if spec else None
        if pid and pid in species and times:
            mean_traj = species[pid].get('mean') or []
            t = _first_crossing(times, mean_traj, thr)
            if unit == 'min' and not math.isnan(t):
                t_disp = t / 60.0
            else:
                t_disp = t
            out['first_crossing'] = {
                'species': spec,
                'threshold': thr,
                'time_s': t,
                'time_display': t_disp,
                'time_unit': unit,
                'label': fc.get('label', f't1 {spec} ({unit})'),
            }

    return out


def format_endpoint(ep: Optional[dict]) -> str:
    """Format endpoint observable as ``mean ± std (n=…)``; '' if absent."""
    if not ep:
        return ''
    mean = ep['mean']
    std = ep.get('std', 0.0)
    n = ep.get('n', 0)
    return f"{mean:.2f} ± {std:.2f} (n={n})"


def format_first_crossing(fc: Optional[dict]) -> str:
    """Format first-crossing observable as ``X.YZ unit`` or 'never'."""
    if not fc:
        return ''
    t = fc.get('time_display', math.nan)
    if isinstance(t, float) and math.isnan(t):
        return 'never'
    unit = fc.get('time_unit', 's')
    return f"{t:.2f} {unit}"
