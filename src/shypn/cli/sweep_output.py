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
    ) -> Path:
        """Save one condition's replicates + statistics.

        Args:
            name: Human-readable condition label (sanitised for filesystem).
            results: Per-replicate dicts from ``ReplicateRunner``.
            statistics: Aggregated statistics from ``compute_statistics()``.
            model: DocumentModel (for place/transition name lookup).

        Returns:
            Path to the condition directory.
        """
        safe_name = _sanitise(name)
        cond_dir = self.run_dir / f"condition_{safe_name}"
        cond_dir.mkdir(parents=True, exist_ok=True)
        self._condition_dirs.append(cond_dir)

        self._write_replicates_csv(cond_dir, results, model)
        self._write_statistics_json(cond_dir, statistics)
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
