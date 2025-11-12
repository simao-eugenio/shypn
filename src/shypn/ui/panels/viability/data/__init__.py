"""Data layer for viability analysis.

This module provides on-demand data pulling from KB and simulation,
with optional caching for efficiency. No reactive observers.
"""
from .data_puller import DataPuller
from .data_cache import DataCache

__all__ = ['DataPuller', 'DataCache']
