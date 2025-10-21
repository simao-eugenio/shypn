"""MasterPalette loader: loads `ui/palettes/master_palette.ui` and populates
buttons in top-to-bottom order. This keeps UI definition (XML) decoupled from
behavior (Python).

CSS theming uses Material Design inspired palette for better visibility:
    - Background: #263238 (dark blue-grey)
    - Hover: #4CAF50 (material green)
    - Active: #FF9800 (material orange)
    - Text: #FFFFFF (white)
"""

import sys
from gi.repository import Gtk, Gdk
from pathlib import Path
from .palette_button import PaletteButton


UI_PATH = Path(__file__).parents[3] / 'ui' / 'palettes' / 'master_palette.ui'


# Material Design inspired CSS for master palette - high contrast, bold colors
PALETTE_CSS = """
/* Master Palette Container */
#master_palette_container {
    background-color: #263238;
    border-right: 2px solid #37474F;
    padding: 4px;
}

/* Palette Buttons - Base State */
.palette-button {
    background-color: #37474F;
    border: 2px solid #455A64;
    border-radius: 6px;
    color: #FFFFFF;
    transition: all 150ms ease;
    margin: 3px;
    min-width: 50px;
    min-height: 50px;
}

.palette-button:hover {
    background-color: #4CAF50;
    border-color: #66BB6A;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.palette-button:active,
.palette-button:checked {
    background-color: #388E3C;
}

/* Active State (toggled on) - Bold orange to stand out */
.palette-button-active {
    background-color: #FF9800;
    border-color: #FFB74D;
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4),
                inset 0 0 0 2px #FFA726;
}

.palette-button-active:hover {
    background-color: #FB8C00;
    border-color: #FFA726;
}

/* Disabled State */
.palette-button:disabled {
    opacity: 0.35;
    background-color: #37474F;
    border-color: #455A64;
    color: #78909C;
}
"""


class MasterPalette:
    """MasterPalette provides a GTK container with category buttons.

    Buttons are defined programmatically but layout is loaded from an XML UI
    file. This keeps the UI structure editable by designers while code owns
    behavior wiring.
    
    Usage:
        palette = MasterPalette()
        palette.connect('files', lambda active: print(f'Files: {active}'))
        palette.connect('analyses', on_analyses_toggle)
        palette.set_sensitive('topology', False)  # Disable until implemented
        
        # Add to main window
        container.pack_start(palette.get_widget(), False, False, 0)
    """

    BUTTON_ORDER = [
        ('files', 'folder-symbolic', 'File Operations'),
        ('pathways', 'network-workgroup-symbolic', 'Pathway Import'),
        ('analyses', 'utilities-system-monitor-symbolic', 'Dynamic Analyses'),
        ('topology', 'applications-science-symbolic', 'Topology Analysis'),
    ]

    def __init__(self, builder: Gtk.Builder = None):
        self.builder = builder or Gtk.Builder()
        self.container = None
        self.buttons = {}
        self._callbacks = {}
        self._css_applied = False
        self._updating = False  # Guard flag to prevent callback loops

        self._load_ui()
        self._create_buttons()
        # Note: CSS will be applied later when widget is realized (Wayland safe)

    def _load_ui(self):
        """Load the master_palette.ui file into a Builder and extract container."""
        try:
            self.builder.add_from_file(str(UI_PATH))
            self.container = self.builder.get_object('master_palette_container')
        except Exception as e:
            # Fallback to creating container programmatically
            self.container = None

        if not self.container:
            # Create fallback container
            self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.container.set_name('master_palette_container')
            self.container.set_size_request(54, -1)
            self.container.set_spacing(0)
            self.container.set_hexpand(False)
            self.container.set_vexpand(True)
            self.container.set_visible(True)

    def _apply_css(self):
        """Apply Nord-themed CSS to palette widgets.
        
        WAYLAND SAFE: Only applies CSS if not already applied and screen is available.
        This should be called after widget is realized to avoid Wayland surface issues.
        """
        if self._css_applied:
            return  # Already applied
        
        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_data(PALETTE_CSS.encode())
            
            # WAYLAND FIX: Get screen safely, return if not available
            screen = Gdk.Screen.get_default()
            if not screen:
                print("Warning: No default screen available for palette CSS", file=sys.stderr)
                return
            
            # Add CSS provider to screen
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self._css_applied = True
        except Exception as e:
            # CSS load failed, continue without styling
            print(f"Warning: Could not load palette CSS: {e}", file=sys.stderr)

    def _create_buttons(self):
        """Pack buttons from top using pack_start; spacer at end."""
        for name, icon, tooltip in self.BUTTON_ORDER:
            pb = PaletteButton(name, icon, tooltip)
            self.buttons[name] = pb
            self.container.pack_start(pb.widget, False, False, 0)

        # Disable topology button by default (not implemented yet)
        if 'topology' in self.buttons:
            self.buttons['topology'].set_sensitive(False)

        # Add expanding spacer to push buttons to top
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self.container.pack_end(spacer, True, True, 0)

    def get_widget(self) -> Gtk.Widget:
        """Get the root GTK widget for this palette."""
        return self.container

    def connect(self, category: str, callback):
        """Register callback for a category toggled event.

        Args:
            category: Button name ('files', 'pathways', 'analyses', 'topology')
            callback: Callable with signature callback(active: bool)
        
        Raises:
            KeyError: If category doesn't exist
        """
        if category not in self.buttons:
            raise KeyError(f"Unknown category: {category}")
        self._callbacks[category] = callback
        
        # Wrap callback to implement exclusive button behavior
        def exclusive_callback(active):
            # Prevent recursive callback loops
            if self._updating:
                return
            
            try:
                self._updating = True
                
                if active:
                    # When button is activated, deactivate all other buttons
                    for btn_name, btn in self.buttons.items():
                        if btn_name != category and btn.get_active():
                            btn.set_active(False)
                
                # Call original callback only if not in update loop
                callback(active)
            finally:
                self._updating = False
        
        self.buttons[category].connect_toggled(exclusive_callback)

    def set_active(self, category: str, active: bool):
        """Set button active state programmatically (e.g., when panel floats/docks)."""
        if category not in self.buttons:
            return
        
        # Use guard flag to prevent triggering callbacks during programmatic changes
        try:
            self._updating = True
            self.buttons[category].set_active(active)
        finally:
            self._updating = False

    def set_sensitive(self, category: str, sensitive: bool):
        """Enable/disable a button (e.g., disable Topology until implemented)."""
        if category not in self.buttons:
            return
        self.buttons[category].set_sensitive(sensitive)
    
    def _on_realize(self, widget):
        """Called when palette widget is realized (Wayland safe).
        
        This ensures CSS is applied only after the widget has a GDK window/surface,
        preventing Wayland crashes from premature CSS application.
        """
        if not self._css_applied:
            self._apply_css()
    
    def get_widget(self):
        """Get the master palette container widget.
        
        Connects realize signal to ensure CSS is applied at the right time.
        This is critical for Wayland compatibility.
        
        Returns:
            Gtk.Box: The master palette container.
        """
        if self.container and not self._css_applied:
            # Connect to realize signal for Wayland-safe CSS application
            self.container.connect('realize', self._on_realize)
        return self.container


__all__ = ['MasterPalette']
