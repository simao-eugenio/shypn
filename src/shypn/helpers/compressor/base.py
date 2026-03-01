"""Abstract base class for all trajectory compressors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .result import ChannelData, CompressionResult


class BaseTrajectoryCompressor(ABC):
    """Contract that every trajectory compressor must satisfy.

    Subclasses implement :meth:`compress` for a single replicate.
    The concrete :meth:`compress_batch` loop is provided here so that
    all subclasses inherit it automatically.

    Typical subclass pattern::

        @dataclass
        class MyCompressor(BaseTrajectoryCompressor):
            threshold: float = 0.05

            def compress(self, time_points, place_data, transition_data,
                         replicate_id=0, seed=None) -> CompressionResult:
                ...
    """

    # ── abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    def compress(
        self,
        time_points: List[float],
        place_data: ChannelData,
        transition_data: ChannelData,
        replicate_id: int = 0,
        seed: Optional[int] = None,
    ) -> CompressionResult:
        """Compress a single replicate trajectory.

        Args:
            time_points:      Common time grid (length *N*).
            place_data:       Per-place series, keyed by place ID.  Each series
                              is either a flat ``List[float]`` or a list of
                              ``(time, value)`` tuples (DataCollector format).
            transition_data:  Per-transition series, same format.
            replicate_id:     Zero-based index of this replicate in the batch.
            seed:             Random seed used for this replicate.

        Returns:
            A :class:`~.result.CompressionResult` with the kept subset.
        """

    # ── concrete helpers ──────────────────────────────────────────────────────

    def compress_batch(
        self,
        results: List[Dict[str, Any]],
    ) -> List[CompressionResult]:
        """Compress all successful replicates in a batch result list.

        Replicates that contain an *'error'* key are silently skipped so
        that partial batches (e.g. from cancelled sweeps) are handled
        gracefully.

        Args:
            results: Raw list returned by
                     :meth:`~shypn.engine.simulation.replicate_runner.ReplicateRunner.run_replicates`.

        Returns:
            One :class:`~.result.CompressionResult` per successful replicate,
            in the same order.
        """
        compressed: List[CompressionResult] = []
        for raw in results:
            if "error" in raw:
                continue
            cr = self.compress(
                time_points=raw.get("time_points", []),
                place_data=raw.get("place_data", {}),
                transition_data=raw.get("transition_data", {}),
                replicate_id=raw.get("replicate_id", 0),
                seed=raw.get("seed"),
            )
            compressed.append(cr)
        return compressed
