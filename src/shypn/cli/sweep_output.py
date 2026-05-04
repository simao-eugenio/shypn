"""Sweep output manager — structured results persistence.

Handles folder creation, per-condition CSV export, statistics JSON,
and the run-level summary.  Reuses :class:`BatchResultsSaver` internals
where possible without coupling to the GTK UI layer.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np


class SweepOutputManager:
    """Write structured sweep results to disk.

    Output layout::

        <output>/
          run_<timestamp>/
            config.json
            condition_<name>/
              replicates.csv
              statistics.json
            ...
            summary.csv
    """

    def __init__(self, output_dir: Path) -> None:
        ts = datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')
        self.run_dir = output_dir / f"run_{ts}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._condition_dirs: List[Path] = []

    # ── public API ───────────────────────────────────────────────────

    def save_config(self, config_dict: Dict[str, Any], model_path: str) -> Path:
        """Persist the sweep configuration for reproducibility."""
        payload = {
            'sweep_config': config_dict,
            'model_path': str(model_path),
            'timestamp': datetime.now(tz=timezone.utc).isoformat(),
        }
        path = self.run_dir / 'config.json'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2)
        return path

    def save_condition(
        self,
        name: str,
        results: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        model: Any,
        output_options: Optional[Any] = None,
    ) -> Path:
        """Save one condition's replicates + statistics.

        Args:
            name: Human-readable condition label (sanitised for filesystem).
            results: Per-replicate dicts from ``ReplicateRunner``.
            statistics: Aggregated statistics from ``compute_statistics()``.
            model: DocumentModel (for place/transition name lookup).
            output_options: Optional :class:`OutputOptions` controlling tier
                gating. Defaults to G3 (all of G0..G3) when omitted, which
                matches the historical behaviour.

        Returns:
            Path to the condition directory.
        """
        # Local import keeps the public API circular-import safe.
        from shypn.cli.sweep_config import OutputOptions

        opts = output_options if output_options is not None else OutputOptions()

        safe_name = _sanitise(name)
        cond_dir = self.run_dir / f"condition_{safe_name}"
        cond_dir.mkdir(parents=True, exist_ok=True)
        self._condition_dirs.append(cond_dir)

        if opts.write_replicates_csv:
            self._write_replicates_csv(cond_dir, results, model)
        if opts.write_statistics_json:
            self._write_statistics_json(cond_dir, statistics)
        if opts.write_per_replicate_trajectories:
            self._write_per_replicate_trajectories(
                cond_dir, results, model,
                trajectory_places=opts.trajectory_places,
                trajectory_thin_seconds=opts.trajectory_thin_seconds,
            )
        if opts.write_covariance:
            self._write_covariance(cond_dir, results, model)
        return cond_dir

    def write_summary(
        self,
        rows: List[Dict[str, Any]],
    ) -> Path:
        """Write the one-row-per-condition summary CSV."""
        path = self.run_dir / 'summary.csv'
        if not rows:
            return path
        fieldnames = list(rows[0].keys())
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    # ── internal helpers ─────────────────────────────────────────────

    @staticmethod
    def _write_replicates_csv(
        cond_dir: Path,
        results: List[Dict[str, Any]],
        model: Any,
    ) -> None:
        """Columnar CSV: Time, Place1, Place2, ..., Trans1, ... per replicate."""
        successful = [r for r in results if 'error' not in r]
        if not successful:
            return

        # Build ID → name map
        id_to_name: Dict[str, str] = {}
        for p in getattr(model, 'places', []):
            id_to_name[p.id] = getattr(p, 'name', p.id) or p.id
        for t in getattr(model, 'transitions', []):
            id_to_name[t.id] = getattr(t, 'name', t.id) or t.id

        place_ids = list(successful[0].get('place_data', {}).keys())
        trans_ids = list(successful[0].get('total_firings', successful[0].get('transition_data', {})).keys())

        path = cond_dir / 'replicates.csv'
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            # header
            header = ['replicate_id', 'seed', 'stopped_reason', 'final_time']
            for pid in place_ids:
                header.append(f"{id_to_name.get(pid, pid)}_final")
            for tid in trans_ids:
                header.append(f"{id_to_name.get(tid, tid)}_firings")
            writer.writerow(header)

            for r in successful:
                # Derive final_time from time_points if not stored directly
                final_time = r.get('final_time', '')
                if not final_time:
                    tp = r.get('time_points', [])
                    if tp:
                        final_time = f"{float(tp[-1]):.6g}"
                row: List[Any] = [
                    r.get('replicate_id', ''),
                    r.get('seed', ''),
                    r.get('stopped_reason', ''),
                    final_time,
                ]
                for pid in place_ids:
                    series = r.get('place_data', {}).get(pid)
                    if series is not None and len(series) > 0:
                        val = series[-1] if not isinstance(series[-1], tuple) else series[-1][1]
                        row.append(f"{float(val):.6g}")
                    else:
                        row.append('')
                for tid in trans_ids:
                    # Prefer total_firings (always populated) over
                    # transition_data time-series (empty when numpy fast-path
                    # is active with skip_rate_eval=True).
                    firings = r.get('total_firings', {}).get(tid)
                    if firings is not None:
                        row.append(f"{int(firings)}")
                    else:
                        series = r.get('transition_data', {}).get(tid)
                        if series is not None and len(series) > 0:
                            val = series[-1] if not isinstance(series[-1], tuple) else series[-1][1]
                            row.append(f"{float(val):.6g}")
                        else:
                            row.append('')
                writer.writerow(row)

    @staticmethod
    def _write_statistics_json(
        cond_dir: Path,
        statistics: Dict[str, Any],
    ) -> None:
        """Serialise statistics, converting numpy arrays to lists."""
        def _convert(obj: Any) -> Any:
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            if isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            return obj

        path = cond_dir / 'statistics.json'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(_convert(statistics), fh, indent=2)

    # ── G4 — per-replicate trajectory CSVs ───────────────────────────

    @staticmethod
    def _write_per_replicate_trajectories(
        cond_dir: Path,
        results: List[Dict[str, Any]],
        model: Any,
        trajectory_places: Optional[List[str]] = None,
        trajectory_thin_seconds: Optional[float] = None,
    ) -> None:
        """G4 writer: one CSV per replicate under ``replicates_trajectories/``.

        Each file is self-describing — a comment header records the source
        condition, the replicate id/seed, and the place column ordering, so
        downstream analysis needs no sidecar metadata.

        Args:
            cond_dir: Per-condition directory.
            results: Per-replicate dicts from ``ReplicateRunner``.
            model: DocumentModel (for place name resolution).
            trajectory_places: Optional subset of place IDs *or* names. When
                provided, only matching columns are written. Unknown labels
                are silently skipped — the header comment records which
                columns were actually emitted.
            trajectory_thin_seconds: Optional minimum Δt between recorded
                samples. ``0`` or ``None`` keeps every sample. ``> 0``
                decimates to the first sample whose ``time >= last_kept + Δ``.
        """
        successful = [r for r in results if 'error' not in r]
        if not successful:
            return

        # Build ID → name map and the inverse, so callers can pass either.
        id_to_name: Dict[str, str] = {}
        name_to_id: Dict[str, str] = {}
        for p in getattr(model, 'places', []):
            nm = getattr(p, 'name', p.id) or p.id
            id_to_name[p.id] = nm
            name_to_id[nm] = p.id

        # Resolve the column set: full places (sorted) by default, or the
        # caller-supplied subset (preserving order, deduped).
        all_place_ids = list(successful[0].get('place_data', {}).keys())
        if trajectory_places:
            requested: List[str] = []
            seen: Set[str] = set()
            for tok in trajectory_places:
                pid = tok if tok in id_to_name else name_to_id.get(tok)
                if pid and pid in id_to_name and pid not in seen:
                    requested.append(pid)
                    seen.add(pid)
            place_ids = [pid for pid in requested if pid in all_place_ids]
        else:
            place_ids = all_place_ids

        if not place_ids:
            return  # nothing to write

        thin_dt = float(trajectory_thin_seconds) if trajectory_thin_seconds else 0.0

        traj_dir = cond_dir / 'replicates_trajectories'
        traj_dir.mkdir(exist_ok=True)

        col_names = [id_to_name.get(pid, pid) for pid in place_ids]

        for r in successful:
            rid = r.get('replicate_id', 0)
            seed = r.get('seed', '')
            stopped = r.get('stopped_reason', '')
            time_points = r.get('time_points') or []
            place_data = r.get('place_data', {})

            # Build per-row data — each place's series is a flat list of
            # values aligned with time_points. Some engines store tuples
            # (t, v); flatten transparently.
            def _flat(series: Any) -> List[float]:
                if not series:
                    return []
                if isinstance(series[0], tuple):
                    return [float(v) for (_, v) in series]
                return [float(v) for v in series]

            cols = {pid: _flat(place_data.get(pid, [])) for pid in place_ids}
            n_samples = min([len(time_points)] + [len(c) for c in cols.values()] or [0])

            csv_path = traj_dir / f'run_{int(rid) + 1:03d}.csv'
            with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
                fh.write(f"# condition_dir: {cond_dir.name}\n")
                fh.write(f"# replicate_id: {rid}\n")
                fh.write(f"# seed: {seed}\n")
                fh.write(f"# stopped_reason: {stopped}\n")
                fh.write(f"# n_samples_raw: {n_samples}\n")
                if thin_dt > 0:
                    fh.write(f"# thin_dt_seconds: {thin_dt}\n")
                fh.write(f"# columns: time,{','.join(col_names)}\n")

                writer = csv.writer(fh)
                writer.writerow(['time'] + col_names)

                last_kept = -float('inf')
                for i in range(n_samples):
                    t = float(time_points[i])
                    if thin_dt > 0 and t < last_kept + thin_dt and i != n_samples - 1:
                        continue
                    last_kept = t
                    row = [f"{t:.6g}"]
                    for pid in place_ids:
                        row.append(f"{cols[pid][i]:.6g}")
                    writer.writerow(row)

    # ── G5 — covariance / correlation over per-replicate finals ──────

    @staticmethod
    def _write_covariance(
        cond_dir: Path,
        results: List[Dict[str, Any]],
        model: Any,
    ) -> None:
        """G5 writer: ``covariance.json`` with mean / cov / corr matrices.

        Computes statistics over the *final-state* place values across the
        successful replicates of a single condition. Output schema::

            {
              "n_replicates": <int>,
              "place_ids":    [...],
              "place_names":  [...],
              "mean":         [...],            # length P
              "covariance":   [[...], ...],     # P×P, ddof=1
              "correlation":  [[...], ...]      # P×P, NaN-safe
            }

        Skipped silently when fewer than 2 replicates succeed (covariance
        is undefined). Constant columns produce NaN rows in the
        correlation matrix; mean / covariance remain valid.
        """
        successful = [r for r in results if 'error' not in r]
        if len(successful) < 2:
            return

        id_to_name: Dict[str, str] = {}
        for p in getattr(model, 'places', []):
            id_to_name[p.id] = getattr(p, 'name', p.id) or p.id

        place_ids = list(successful[0].get('place_data', {}).keys())
        if not place_ids:
            return

        # Build [N replicates × P places] final-value matrix.
        finals = np.full((len(successful), len(place_ids)), np.nan, dtype=float)
        for ri, r in enumerate(successful):
            pdata = r.get('place_data', {})
            for ci, pid in enumerate(place_ids):
                series = pdata.get(pid)
                if not series:
                    continue
                last = series[-1]
                finals[ri, ci] = float(last[1] if isinstance(last, tuple) else last)

        # Drop replicates with any NaN (incomplete runs); numpy.cov can't
        # handle them and silently filling 0 would bias the matrix.
        valid_mask = ~np.isnan(finals).any(axis=1)
        finals_clean = finals[valid_mask]
        if finals_clean.shape[0] < 2:
            return

        mean = finals_clean.mean(axis=0)
        cov = np.cov(finals_clean, rowvar=False, ddof=1)
        # Ensure 2-D shape even when P == 1 (np.cov returns scalar then).
        cov = np.atleast_2d(cov)

        # Correlation: divide by outer-product of stds; NaN where std == 0.
        std = np.sqrt(np.diag(cov))
        with np.errstate(divide='ignore', invalid='ignore'):
            denom = np.outer(std, std)
            corr = np.where(denom > 0, cov / denom, np.nan)

        payload = {
            'n_replicates': int(finals_clean.shape[0]),
            'n_replicates_dropped': int((~valid_mask).sum()),
            'place_ids': list(place_ids),
            'place_names': [id_to_name.get(pid, pid) for pid in place_ids],
            'mean': [float(v) for v in mean],
            'covariance': [[float(v) for v in row] for row in cov],
            'correlation': [
                [None if np.isnan(v) else float(v) for v in row]
                for row in corr
            ],
        }

        path = cond_dir / 'covariance.json'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2)


def _sanitise(name: str) -> str:
    """Filesystem-safe condition name."""
    return (
        name.replace(' ', '_')
            .replace('/', '_')
            .replace('\\', '_')
            .replace(':', '_')
            .replace(',', '_')
            .replace(';', '_')
            .replace('=', '_eq_')
    )[:120]
