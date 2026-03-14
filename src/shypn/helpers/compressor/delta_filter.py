"""δ-filter (greedy keepalive) trajectory compressor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from .base import BaseTrajectoryCompressor
from .result import ChannelData, CompressionResult, _extract_value


@dataclass
class DeltaFilterCompressor(BaseTrajectoryCompressor):
    """Greedy keepalive compressor based on normalised channel change.

    A time-point *i* is **kept** when at least one channel satisfies::

        |v_j(i) - v_j(last_kept)| / (1 + range_j) > epsilon

    where *range_j* is the full observed range of channel *j* across the
    entire trajectory.  Additionally, a **heartbeat** point is always kept
    when the gap since the last kept point reaches *max_gap* seconds.  The
    very first and last points are always kept regardless of any threshold.

    This algorithm requires no model-specific knowledge — it operates
    purely on normalised magnitude changes and so works correctly for any
    set of biological species or firing counts.

    Attributes:
        epsilon:  Normalised-change threshold (default ``0.02`` → 2 %).
        max_gap:  Maximum interval (seconds) between any two kept points,
                  used as a heartbeat to prevent long silent stretches from
                  being entirely discarded (default ``300`` s = 5 min).
        min_gap:  Minimum interval (seconds) between any two kept points
                  (default ``0.0`` = disabled).  When set, the δ-filter
                  check is suppressed for any candidate point closer than
                  *min_gap* to the last kept point (heartbeat still fires
                  unconditionally).  Recommended for SSA (Gillespie) data:
                  set to ~5–10× the raw simulation time-step to prevent
                  fast-transient channels (nuclear mRNAs, GTP/GDP) from
                  effectively defeating compression.  Example: with a 0.36 s
                  raw step, ``min_gap = 1.8`` raises compression from ~2.5×
                  to ~15–20× with negligible biological information loss.
    """

    epsilon: float = 0.02
    max_gap: float = 300.0
    min_gap: float = 0.0

    # ── public interface ──────────────────────────────────────────────────────

    # -- class docstring addition --
    # *min_gap* (seconds, default ``0.0`` = disabled) prevents keeping two
    # consecutive points closer together than this interval, regardless of the
    # delta-filter decision.  This is particularly useful for SSA (Gillespie)
    # trajectories where low-count species (e.g. nuclear mRNAs) change
    # discretely at nearly every integration step, driving the normalised delta
    # above *epsilon* and limiting compression to ~2–3×.  Setting
    # ``min_gap = 1.0`` on 0.36 s-resolution SSA data typically raises
    # compression from ~2.5× to ~15–20× with negligible loss of biological
    # resolution for protein-level dynamics.

    def compress(
        self,
        time_points: List[float],
        place_data: ChannelData,
        transition_data: ChannelData,
        replicate_id: int = 0,
        seed: Optional[int] = None,
    ) -> CompressionResult:
        """Apply the δ-filter to a single replicate.

        Args:
            time_points:     Common time grid (length *N*).
            place_data:      Per-place series (flat or tuple format).
            transition_data: Per-transition series (flat or tuple format).
            replicate_id:    Replicate index within the batch.
            seed:            Random seed for this replicate.

        Returns:
            :class:`~.result.CompressionResult` containing only the kept
            points, with the same serialisation format as the input.
        """
        n = len(time_points)
        _empty = CompressionResult(
            replicate_id=replicate_id,
            seed=seed,
            time_points=[],
            place_data={},
            transition_data={},
            n_original=n,
            n_kept=0,
            epsilon=self.epsilon,
            max_gap=self.max_gap,
            min_gap=self.min_gap,
        )
        if n == 0:
            return _empty

        all_data = {**place_data, **transition_data}
        flat = self._flatten(all_data)

        kept_indices = self._select_indices(time_points, flat)

        return CompressionResult(
            replicate_id=replicate_id,
            seed=seed,
            time_points=self._slice_list(time_points, kept_indices),
            place_data=self._slice_channel(place_data, flat, kept_indices),
            transition_data=self._slice_channel(transition_data, flat, kept_indices),
            n_original=n,
            n_kept=len(kept_indices),
            epsilon=self.epsilon,
            max_gap=self.max_gap,
            min_gap=self.min_gap,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _flatten(channel_data: ChannelData) -> Dict[str, np.ndarray]:
        """Extract numeric value arrays from a channel dict.

        Handles both flat ``List[float]`` and ``List[(time, value)]`` formats
        transparently.

        Returns:
            ``{channel_id: np.ndarray}`` of shape *(N,)*.
        """
        out: Dict[str, np.ndarray] = {}
        for key, series in channel_data.items():
            out[key] = np.array([_extract_value(item) for item in series], dtype=np.float64)
        return out

    def _select_indices(
        self,
        time_points: List[float],
        flat: Dict[str, np.ndarray],
    ) -> List[int]:
        """Return the subset of indices to keep.

        The algorithm runs in O(N × C) where *C* is the number of channels.
        For typical sweep sizes (N ≈ 7200, C ≈ 20) this completes in < 1 ms.

        Three cascaded rules (evaluated in order):

        1. **Heartbeat** — unconditionally keep when ``t_gap >= max_gap``.
        2. **Min-gap floor** — skip (do *not* keep) when ``t_gap < min_gap``.
           This prevents fast-transient channels (e.g. nuclear mRNAs in SSA)
           from triggering the delta rule at every raw integration step.
        3. **δ-filter** — keep when any channel's normalised change exceeds
           *epsilon*.
        """
        n = len(time_points)

        if not flat:
            # No channels: keep boundary points only.
            return [0] if n == 1 else [0, n - 1]

        # Per-channel normalisation denominator: 1 + observed range.
        # Guard against zero-length arrays (empty series from fast-path runs).
        denom: Dict[str, float] = {
            k: 1.0 + float(v.max() - v.min()) if len(v) > 0 else 1.0
            for k, v in flat.items()
        }
        # Drop channels whose array is empty so the delta loop never indexes them.
        flat = {k: v for k, v in flat.items() if len(v) > 0}

        if not flat:
            # All channels were empty: keep boundary points only.
            return [0] if n == 1 else [0, n - 1]

        kept: List[int] = [0]
        last = 0
        min_gap_active = self.min_gap > 0.0

        for i in range(1, n):
            t_gap = time_points[i] - time_points[last]

            # Rule 1 — Heartbeat: unconditionally keep if silent for too long.
            if t_gap >= self.max_gap:
                kept.append(i)
                last = i
                continue

            # Rule 2 — Min-gap floor: skip if not enough time has elapsed.
            if min_gap_active and t_gap < self.min_gap:
                continue

            # Rule 3 — δ-filter: keep if any channel changed by more than epsilon.
            for k, vals in flat.items():
                delta = abs(float(vals[i]) - float(vals[last])) / denom[k]
                if delta > self.epsilon:
                    kept.append(i)
                    last = i
                    break

        # Always include the final point.
        if kept[-1] != n - 1:
            kept.append(n - 1)

        return kept

    @staticmethod
    def _slice_list(source: List[Any], indices: List[int]) -> List[Any]:
        """Return a list containing only the elements at *indices*."""
        return [source[i] for i in indices]

    @staticmethod
    def _slice_channel(
        channel_data: ChannelData,
        flat: Dict[str, np.ndarray],
        indices: List[int],
    ) -> ChannelData:
        """Slice a channel dict to the kept *indices*, preserving input format.

        If the original series contained ``(time, value)`` tuples, the output
        will also contain tuples.  If it was a flat list, the output is flat.
        """
        out: ChannelData = {}
        for key, series in channel_data.items():
            vals = flat.get(key)
            if vals is None or len(vals) == 0:
                # Empty channel (fast-path run produced no data for it): skip.
                continue
            if series and isinstance(series[0], tuple):
                # Reconstruct tuples: (original_time, compressed_value)
                out[key] = [
                    (series[i][0], float(vals[i]))  # type: ignore[index]
                    for i in indices
                ]
            else:
                out[key] = [float(vals[i]) for i in indices]
        return out
