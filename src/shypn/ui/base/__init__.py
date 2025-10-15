"""Base UI classes for all panels, dialogs, and widgets.

This module provides abstract base classes that enforce clean separation
between UI code and business logic.

Key Principles:
- UI classes only handle GTK widgets and events
- Business logic is delegated to injected controllers
- Dependencies are provided via constructor injection
- All base classes enforce consistent patterns
"""

from .base_panel import BasePanel

__all__ = ['BasePanel']
