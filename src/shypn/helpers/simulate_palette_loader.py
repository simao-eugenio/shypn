"""Simulation Palette Loader.

Loads and manages the simulation palette UI (main [S] toggle button).
Works with SimulateToolsPaletteLoader for the tools revealer.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Try to import GTK
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject
except (ImportError, ValueError) as e:
    print('ERROR: GTK3 not available in simulate_palette_loader:', e, file=sys.stderr)
    raise


class SimulatePaletteLoader(GObject.GObject):
    """Loader for simulation palette UI.
    
    Manages the main [S] simulation toggle button.
    Links to SimulateToolsPaletteLoader for the tools revealer.
    """
    
    __gsignals__ = {}
    
    def __init__(self, ui_path: Optional[str] = None):
        """Initialize the simulation palette loader.
        
        Args:
            ui_path: Optional path to simulate_palette.ui. If None, uses default location.
        """
        super().__init__()
        
        if ui_path is None:
            # Default: ui/simulate/simulate_palette.ui
            # This loader file is in: src/shypn/helpers/simulate_palette_loader.py
            # UI file is in: ui/simulate/simulate_palette.ui
            repo_root = Path(__file__).parent.parent.parent.parent
            ui_path = os.path.join(repo_root, 'ui', 'simulate', 'simulate_palette.ui')
        
        self.ui_path = ui_path
        self.builder = Gtk.Builder()
        self.simulate_palette_container = None  # Main container
        self.simulate_toggle_button = None  # [S] button
        self.tools_palette_loader = None  # SimulateToolsPaletteLoader instance
        
        self._load_ui()
        self._connect_signals()
    
    def _load_ui(self) -> None:
        """Load the UI file and get widget references.
        
        Raises:
            FileNotFoundError: If UI file not found.
            ValueError: If simulate_palette_container not found in UI file.
        """
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(
                f"Simulation palette UI file not found: {self.ui_path}"
            )
        
        try:
            self.builder.add_from_file(self.ui_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load simulation palette UI: {e}")
        
        # Get widget references
        self.simulate_palette_container = self.builder.get_object('simulate_palette_container')
        self.simulate_toggle_button = self.builder.get_object('simulate_toggle_button')
        
        if self.simulate_palette_container is None:
            raise ValueError(
                f"'simulate_palette_container' not found in {self.ui_path}"
            )
        
        if self.simulate_toggle_button is None:
            raise ValueError(
                f"'simulate_toggle_button' not found in {self.ui_path}"
            )
    
    def _connect_signals(self) -> None:
        """Connect button signals."""
        if self.simulate_toggle_button:
            self.simulate_toggle_button.connect('toggled', self._on_simulate_toggle)
        
        # Apply custom CSS styling
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply custom CSS styling to the simulate palette."""
        css = """
        .simulate-button {
            background: linear-gradient(to bottom, #e74c3c, #c0392b);
            border: 2px solid #a93226;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            min-width: 36px;
            min-height: 36px;
            padding: 0;
            margin: 0;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3),
                        0 1px 3px rgba(0, 0, 0, 0.2);
        }
        
        .simulate-button:hover {
            background: linear-gradient(to bottom, #c0392b, #a93226);
            box-shadow: 0 4px 8px rgba(231, 76, 60, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .simulate-button:active,
        .simulate-button:checked {
            background: linear-gradient(to bottom, #a93226, #922b21);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .simulate-button:checked {
            border-color: #922b21;
        }
        """
        
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply to screen
        from gi.repository import Gdk
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _on_simulate_toggle(self, toggle_button: Gtk.ToggleButton) -> None:
        """Handle [S] button toggle - show/hide simulation tools.
        
        Args:
            toggle_button: The simulate toggle button that was clicked.
        """
        is_active = toggle_button.get_active()
        
        # Toggle the tools palette visibility
        if self.tools_palette_loader:
            if is_active:
                self.tools_palette_loader.show()
            else:
                self.tools_palette_loader.hide()
        
        # Emit signal for external listeners
        self.emit('tools-toggled', is_active)
    
    def set_tools_palette_loader(self, tools_palette_loader) -> None:
        """Link this palette to a SimulateToolsPaletteLoader instance.
        
        Args:
            tools_palette_loader: SimulateToolsPaletteLoader instance.
        """
        self.tools_palette_loader = tools_palette_loader
    
    def get_widget(self) -> Optional[Gtk.Widget]:
        """Get the main palette container widget.
        
        Returns:
            The simulate_palette_container widget, or None if not loaded.
        """
        return self.simulate_palette_container
    
    def get_toggle_button(self) -> Optional[Gtk.ToggleButton]:
        """Get the [S] toggle button.
        
        Returns:
            The simulate_toggle_button, or None if not loaded.
        """
        return self.simulate_toggle_button


class SimulateToolsPaletteLoader(GObject.GObject):
    """Loader for simulation tools palette UI.
    
    Manages the tools revealer with [R][S][T] buttons.
    """
    
    __gsignals__ = {}
    
    def __init__(self, ui_path: Optional[str] = None):
        """Initialize the simulation tools palette loader.
        
        Args:
            ui_path: Optional path to simulate_tools_palette.ui. If None, uses default location.
        """
        super().__init__()
        
        if ui_path is None:
            # Default: ui/simulate/simulate_tools_palette.ui
            repo_root = Path(__file__).parent.parent.parent.parent
            ui_path = os.path.join(repo_root, 'ui', 'simulate', 'simulate_tools_palette.ui')
        
        self.ui_path = ui_path
        self.builder = Gtk.Builder()
        self.simulate_tools_container = None  # Main container
        self.simulate_tools_revealer = None  # Revealer widget
        self.run_button = None
        self.stop_button = None
        self.reset_button = None
        
        self._load_ui()
        self._connect_signals()
    
    def _load_ui(self) -> None:
        """Load the UI file and get widget references.
        
        Raises:
            FileNotFoundError: If UI file not found.
            ValueError: If required widgets not found in UI file.
        """
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(
                f"Simulation tools palette UI file not found: {self.ui_path}"
            )
        
        try:
            self.builder.add_from_file(self.ui_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load simulation tools palette UI: {e}")
        
        # Get widget references
        self.simulate_tools_container = self.builder.get_object('simulate_tools_container')
        self.simulate_tools_revealer = self.builder.get_object('simulate_tools_revealer')
        self.run_button = self.builder.get_object('run_simulation_button')
        self.stop_button = self.builder.get_object('stop_simulation_button')
        self.reset_button = self.builder.get_object('reset_simulation_button')
        
        if self.simulate_tools_container is None:
            raise ValueError(
                f"'simulate_tools_container' not found in {self.ui_path}"
            )
        
        if self.simulate_tools_revealer is None:
            raise ValueError(
                f"'simulate_tools_revealer' not found in {self.ui_path}"
            )
    
    def _connect_signals(self) -> None:
        """Connect button signals.
        
        Note: Actual simulation logic will be connected by the controller.
        """
        # Buttons will be connected by SimulatePaletteController
        pass
    
    def show(self) -> None:
        """Show the tools palette with animation."""
        if self.simulate_tools_revealer:
            self.simulate_tools_revealer.set_reveal_child(True)
    
    def hide(self) -> None:
        """Hide the tools palette with animation."""
        if self.simulate_tools_revealer:
            self.simulate_tools_revealer.set_reveal_child(False)
    
    def set_revealed(self, revealed: bool) -> None:
        """Show or hide the tools revealer.
        
        Args:
            revealed: True to show, False to hide.
        """
        if revealed:
            self.show()
        else:
            self.hide()
    
    def get_widget(self) -> Optional[Gtk.Widget]:
        """Get the main tools palette container widget.
        
        Returns:
            The simulate_tools_container widget, or None if not loaded.
        """
        return self.simulate_tools_container
    
    def get_run_button(self) -> Optional[Gtk.Button]:
        """Get the Run [R] button."""
        return self.run_button
    
    def get_stop_button(self) -> Optional[Gtk.Button]:
        """Get the Stop [S] button."""
        return self.stop_button
    
    def get_reset_button(self) -> Optional[Gtk.Button]:
        """Get the Reset [T] button."""
        return self.reset_button


def create_simulate_palette(ui_path: Optional[str] = None) -> SimulatePaletteLoader:
    """Factory function to create a SimulatePaletteLoader instance.
    
    Args:
        ui_path: Optional path to simulate_palette.ui. If None, uses default location.
        
    Returns:
        SimulatePaletteLoader instance.
    """
    return SimulatePaletteLoader(ui_path=ui_path)


def create_simulate_tools_palette(ui_path: Optional[str] = None) -> SimulateToolsPaletteLoader:
    """Factory function to create a SimulateToolsPaletteLoader instance.
    
    Args:
        ui_path: Optional path to simulate_tools_palette.ui. If None, uses default location.
        
    Returns:
        SimulateToolsPaletteLoader instance.
    """
    return SimulateToolsPaletteLoader(ui_path=ui_path)
