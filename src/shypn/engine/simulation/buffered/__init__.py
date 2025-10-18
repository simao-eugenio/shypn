"""
Buffered Parameter Management Module

Provides atomic, transaction-safe parameter updates during simulation.
Prevents race conditions from rapid UI changes.
"""

from .base import BufferStrategy, ValidationError
from .buffered_settings import BufferedSimulationSettings
from .transaction import SettingsTransaction

__all__ = [
    'BufferStrategy',
    'ValidationError',
    'BufferedSimulationSettings',
    'SettingsTransaction'
]
