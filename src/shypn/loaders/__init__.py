"""Minimal UI loaders for loading GTK UI definitions.

This module provides generic loaders that:
1. Load .ui files from /ui/ at repo root
2. Create Python class instances with injected dependencies
3. Wire GTK signals to handler methods

Loaders do NOT contain business logic - they are pure UI loading infrastructure.

Example:
    loader = PanelLoader()
    panel = loader.load_panel(
        ui_file="panels/left_panel.ui",  # From /ui/panels/left_panel.ui
        panel_class=LeftPanel,
        state_manager=state_manager,
        controller=controller
    )
"""

from .panel_loader import PanelLoader

__all__ = ['PanelLoader']
