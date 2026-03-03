"""Writer that serialises a :class:`~.result.CompressionResult` to CSV."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .result import CompressionResult, _extract_value


class CompressedTrajectoryWriter:
    """Writes a single :class:`~.result.CompressionResult` to a self-describing CSV.

    The output format is:

    1. A block of ``# key: value`` comment lines that encode all provenance
       and compression metadata (readable without a separate sidecar file).
    2. A ``# col_schema`` line describing every column by index, ID, name,
       and type so that analysis scripts can parse it without loading the model.
    3. A standard header row (column names) followed by data rows.

    All comment lines use ``#`` as the first character so that
    ``pandas.read_csv(path, comment='#')`` works directly.

    Example output header::

        # experiment: EPO_external=0.449_GCSF_external=0.1
        # replicate_id: 7   seed: 49
        # status: completed
        # t_start: 0.0   t_end: 3600.0   t_units: s
        # n_points_original: 7200   n_points_kept: 147   compression_ratio: 49.0
        # compressor: DeltaFilterCompressor   epsilon: 0.02   max_gap_s: 300.0   min_gap_s: 0.0
        # generated: 2026-03-01T17:42:00Z
        # col_schema: 0:time(s) | 1:P19:ATP:place | 2:P17:GATA1_Protein_nuc:place | ...
        time,P17,P19,...
        0.0,0.001,30.0,...
    """

    # ── public API ────────────────────────────────────────────────────────────

    @classmethod
    def write(
        cls,
        path: Path,
        result: CompressionResult,
        *,
        experiment_name: str = "",
        status: str = "completed",
        id_to_name: Optional[Dict[str, str]] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Serialise *result* to *path*.

        Args:
            path:            Destination file path (parent dirs must exist).
            result:          Compressed replicate data to write.
            experiment_name: Human-readable experiment label for the header.
            status:          Replicate status string (``"completed"`` /
                             ``"deadlocked"`` / ``"error"``).
            id_to_name:      Optional ``{id: human_name}`` lookup; when
                             provided, column headers use human names.
            extra_meta:      Optional additional ``{key: value}`` pairs
                             appended to the comment block.
        """
        id_to_name = id_to_name or {}

        place_ids = result.sorted_place_ids()
        trans_ids = result.sorted_transition_ids()
        all_ids: List[str] = place_ids + trans_ids

        col_schema = cls._build_col_schema(all_ids, id_to_name, place_ids)
        t_start = result.time_points[0] if result.time_points else 0.0
        t_end = result.time_points[-1] if result.time_points else 0.0

        with path.open("w", newline="", encoding="utf-8") as fh:
            # ── comment header ────────────────────────────────────────────
            fh.write(f"# experiment: {experiment_name}\n")
            fh.write(
                f"# replicate_id: {result.replicate_id}   "
                f"seed: {result.seed if result.seed is not None else 'N/A'}\n"
            )
            fh.write(f"# status: {status}\n")
            fh.write(f"# t_start: {t_start}   t_end: {t_end}   t_units: s\n")
            fh.write(
                f"# n_points_original: {result.n_original}   "
                f"n_points_kept: {result.n_kept}   "
                f"compression_ratio: {result.compression_ratio:.2f}\n"
            )
            fh.write(
                f"# compressor: DeltaFilterCompressor   "
                f"epsilon: {result.epsilon}   "
                f"max_gap_s: {result.max_gap}   "
                f"min_gap_s: {result.min_gap}\n"
            )
            if extra_meta:
                for k, v in extra_meta.items():
                    fh.write(f"# {k}: {v}\n")
            fh.write(
                f"# generated: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            )
            fh.write(f"# col_schema: {col_schema}\n")

            # ── tabular data ──────────────────────────────────────────────
            writer = csv.writer(fh)
            header_row = ["time"] + [
                id_to_name.get(oid, oid) for oid in all_ids
            ]
            writer.writerow(header_row)

            flat_place = cls._to_flat_map(result.place_data)
            flat_trans = cls._to_flat_map(result.transition_data)

            for i, t in enumerate(result.time_points):
                row: List[Any] = [t]
                for pid in place_ids:
                    vals = flat_place.get(pid, [])
                    row.append(vals[i] if i < len(vals) else "")
                for tid in trans_ids:
                    vals = flat_trans.get(tid, [])
                    row.append(vals[i] if i < len(vals) else "")
                writer.writerow(row)

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_col_schema(
        all_ids: List[str],
        id_to_name: Dict[str, str],
        place_ids: List[str],
    ) -> str:
        """Return a compact ``0:time(s) | 1:P17:GATA1:place | …`` string."""
        parts = ["0:time(s)"]
        for col_idx, oid in enumerate(all_ids, start=1):
            name = id_to_name.get(oid, oid)
            kind = "place" if oid in place_ids else "transition"
            parts.append(f"{col_idx}:{oid}:{name}:{kind}")
        return " | ".join(parts)

    @staticmethod
    def _to_flat_map(channel_data: Any) -> Dict[str, List[float]]:
        """Convert channel data (tuples or flat) to ``{id: [float, …]}``."""
        out: Dict[str, List[float]] = {}
        for k, series in channel_data.items():
            out[k] = [_extract_value(item) for item in series]
        return out
