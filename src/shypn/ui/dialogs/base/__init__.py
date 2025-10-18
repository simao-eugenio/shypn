"""Base classes for property dialogs.

This package provides abstract base classes and shared utilities
for all property dialog implementations.
"""

from .property_dialog_base import PropertyDialogBase
from .expression_validator import ExpressionValidator

__all__ = ['PropertyDialogBase', 'ExpressionValidator']
