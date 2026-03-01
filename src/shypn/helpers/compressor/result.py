"""CompressionResult dataclass — output contract for all compressors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

# ── type aliases ──────────────────────────────────────────────────────────────

#: A single channel series: either a flat list of values **or** a list of
#: ``(time, value)`` tuples, exactly as returned by *DataCollector*.
SeriesItem = Union[float, Tuple[float, float]]
ChannelData = Dict[str, List[SeriesItem]]


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_value(item: SeriesItem) -> float:
    """Return the numeric value from a *SeriesItem* (tuple or scalar)."""
    return float(item[1]) if isinstance(item, tuple) else float(item)  # type: ignore[index]


# ── dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class CompressionResult:
    """Compressed trajectory for a single simulation replicate.

    The *place_data* and *transition_data* fields preserve the original
    serialisation format (flat list **or** ``(time, value)`` tuples) so that
    downstream consumers do not need to change their parsing logic.

    Attributes:
        replicate_id: Zero-based replicate index within the batch.
        seed:         Random seed used for this replicate (``None`` if unknown).
        time_points:  Kept time values (subset of the original grid).
        place_data:   Compressed place series, same format as the source.
        transition_data: Compressed transition series, same format as the source.
        n_original:   Number of time-points before compression.
        n_kept:       Number of time-points after compression.
        epsilon:      Normalised-change threshold used by the compressor.
        max_gap:      Maximum heartbeat interval (seconds) used by the compressor.
    """

    replicate_id: int
    seed: Optional[int]
    time_points: List[float]
    place_data: ChannelData
    transition_data: ChannelData
    n_original: int
    n_kept: int
    epsilon: float
    max_gap: float

    # ── derived properties ────────────────────────────────────────────────────

    @property
    def compression_ratio(self) -> float:
        """Ratio of original to kept points (>= 1.0; 1.0 means no compression)."""
        return self.n_original / max(1, self.n_kept)

    @property
    def is_empty(self) -> bool:
        """``True`` when no time-points were recorded."""
        return self.n_kept == 0

    # ── convenience ───────────────────────────────────────────────────────────

    def final_values(self) -> Dict[str, float]:
        """Return a ``{place_id: value}`` mapping at the last kept time-point."""
        return {
            pid: _extract_value(series[-1])
            for pid, series in self.place_data.items()
            if series
        }

    def sorted_place_ids(self) -> List[str]:
        """Sorted list of place IDs present in this result."""
        return sorted(self.place_data.keys())

    def sorted_transition_ids(self) -> List[str]:
        """Sorted list of transition IDs present in this result."""
        return sorted(self.transition_data.keys())
