"""Environment Panel — signal spatial places viewer + event scheduler.

Provides per-document read-only view of signal spatial places and an
editable schedule of model-level environment events that drive signal
place perturbations during simulation.
"""
from .environment_panel import EnvironmentPanel

__all__ = ['EnvironmentPanel']
