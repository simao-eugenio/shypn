"""Generic panel loader for loading UI definitions.

This module provides a minimal, reusable loader for GTK panels that:
- Loads .ui files from /ui/ directory at repo root
- Creates panel instances with dependency injection
- Wires GTK signals to panel handler methods

The loader is completely generic and contains NO business logic.
All behavior is implemented in the panel classes themselves.
"""

import os
from pathlib import Path
from typing import Type, Any

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.base import BasePanel


class PanelLoader:
    """Generic panel loader - UI file loading only.
    
    This loader:
    1. Finds the UI root directory (/ui/ at repo root)
    2. Loads .ui files using GTK Builder
    3. Instantiates panel classes with dependency injection
    4. Wires signals via panel.connect_signals()
    
    Does NOT:
    - Contain any business logic
    - Know about specific panel types
    - Handle state management
    - Process events
    
    Attributes:
        ui_root: Path to UI root directory (/ui/ at repo root)
    
    Example:
        # Create loader (auto-finds /ui/)
        loader = PanelLoader()
        
        # Load left panel
        left_panel = loader.load_panel(
            ui_file="panels/left_panel.ui",
            panel_class=LeftPanel,
            state_manager=state_manager
        )
        
        # Load canvas panel with multiple dependencies
        canvas_panel = loader.load_panel(
            ui_file="canvas/model_canvas.ui",
            panel_class=CanvasPanel,
            state_manager=state_manager,
            canvas_controller=controller,
            renderer=renderer
        )
    """
    
    def __init__(self, ui_root: Path = None):
        """Initialize loader with UI root directory.
        
        Args:
            ui_root: Path to UI root directory. If None, auto-detects
                    by finding repo root (defaults to /ui/ at repo root).
        
        The auto-detection works by going up from this file's location:
        src/shypn/loaders/panel_loader.py -> repo_root/ui/
        """
        if ui_root is None:
            ui_root = self._find_ui_root()
        
        self.ui_root = Path(ui_root)
        
        # Validate UI root exists
        if not self.ui_root.exists():
            raise FileNotFoundError(
                f"UI root directory not found: {self.ui_root}\n"
                f"Expected /ui/ directory at repo root."
            )
    
    def _find_ui_root(self) -> Path:
        """Find UI root directory at repo root.
        
        Returns:
            Path to /ui/ directory at repo root.
        
        Raises:
            FileNotFoundError: If UI root cannot be found.
        """
        # Get this file's location: src/shypn/loaders/panel_loader.py
        current_file = Path(__file__).resolve()
        
        # Go up to repo root: loaders -> shypn -> src -> repo_root
        repo_root = current_file.parent.parent.parent.parent
        
        # UI root should be at repo_root/ui
        ui_root = repo_root / "ui"
        
        return ui_root
    
    def load_panel(self, ui_file: str, panel_class: Type[BasePanel],
                   **dependencies) -> BasePanel:
        """Load UI file and create panel instance with dependencies.
        
        This method:
        1. Resolves ui_file relative to UI root
        2. Loads .ui file using GTK Builder
        3. Creates panel instance with injected dependencies
        4. Calls panel.connect_signals() to wire GTK signals
        
        Args:
            ui_file: Relative path from UI root (e.g., "panels/left_panel.ui")
            panel_class: Panel class to instantiate (subclass of BasePanel)
            **dependencies: Dependencies to inject into panel constructor
        
        Returns:
            Panel instance with loaded UI and wired signals.
        
        Raises:
            FileNotFoundError: If .ui file doesn't exist
            TypeError: If panel_class is not a BasePanel subclass
        
        Example:
            panel = loader.load_panel(
                ui_file="panels/right_panel.ui",
                panel_class=RightPanel,
                state_manager=state_manager,
                property_controller=controller
            )
        """
        # Validate panel class
        if not issubclass(panel_class, BasePanel):
            raise TypeError(
                f"{panel_class.__name__} must be a subclass of BasePanel"
            )
        
        # Build full path to .ui file
        ui_path = self.ui_root / ui_file
        
        # Validate .ui file exists
        if not ui_path.exists():
            raise FileNotFoundError(
                f"UI file not found: {ui_path}\n"
                f"Looking for: {ui_file}\n"
                f"In UI root: {self.ui_root}"
            )
        
        # Load GTK builder from .ui file
        builder = Gtk.Builder()
        builder.add_from_file(str(ui_path))
        
        # Create panel instance with injected dependencies
        # Panel's __init__ receives builder + all dependencies
        panel = panel_class(builder=builder, **dependencies)
        
        # Wire GTK signals to panel handler methods
        panel.connect_signals()
        
        return panel
    
    def get_ui_path(self, ui_file: str) -> Path:
        """Get full path to a UI file.
        
        Useful for checking if UI files exist or for debugging.
        
        Args:
            ui_file: Relative path from UI root
        
        Returns:
            Full path to the UI file.
        
        Example:
            path = loader.get_ui_path("panels/left_panel.ui")
        """
        return self.ui_root / ui_file
    
    def ui_file_exists(self, ui_file: str) -> bool:
        """Check if a UI file exists.
        
        Args:
            ui_file: Relative path from UI root
        
        Returns:
            True if file exists, False otherwise.
        
        Example:
            if loader.ui_file_exists("panels/new_panel.ui"):
                panel = loader.load_panel("panels/new_panel.ui", NewPanel)
        """
        return self.get_ui_path(ui_file).exists()
