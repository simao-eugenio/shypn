"""Trajectory compression package.

Provides pluggable compressors that reduce per-replicate time-series data
before saving without any model-specific knowledge.

Typical usage::

    from shypn.helpers.compressor import DeltaFilterCompressor

    compressor = DeltaFilterCompressor(epsilon=0.02, max_gap=300.0)
    compressed = compressor.compress_batch(raw_results)   # List[CompressionResult]
"""

from .result import CompressionResult
from .base import BaseTrajectoryCompressor
from .delta_filter import DeltaFilterCompressor
from .csv_writer import CompressedTrajectoryWriter

__all__ = [
    "CompressionResult",
    "BaseTrajectoryCompressor",
    "DeltaFilterCompressor",
    "CompressedTrajectoryWriter",
]
