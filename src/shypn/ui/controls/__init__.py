"""
Debounced UI controls for smooth user interactions.

This module provides GTK widgets with built-in debouncing to prevent
rapid event firing during continuous user input (e.g., slider dragging,
text entry). Debouncing ensures that callback handlers are called only
after the user has finished making changes, reducing unnecessary updates
and improving performance.

Classes:
    DebouncedSpinButton: SpinButton with debounced value changes
    DebouncedEntry: Entry with debounced text changes
"""

from .base import DebounceStrategy, DebouncedWidget
from .debounced_spin_button import DebouncedSpinButton
from .debounced_entry import DebouncedEntry

__all__ = [
    'DebounceStrategy',
    'DebouncedWidget',
    'DebouncedSpinButton',
    'DebouncedEntry',
]
