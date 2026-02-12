"""Simulation execution strategies.

This package contains different execution strategies for running simulations:
- ContinuousExecutor: Continuous run mode with GLib timeout callbacks
- Future: StepExecutor, BatchExecutor, ParallelExecutor, etc.
"""

from .continuous_executor import ContinuousExecutor

__all__ = ['ContinuousExecutor']
