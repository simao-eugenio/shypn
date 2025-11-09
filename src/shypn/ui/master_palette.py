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


class PanelManager:
    """Manages panel switching for Master Palette.
    
    SIMPLIFIED ARCHITECTURE:
    - Panels are windows parented to Master Palette
    - Show/hide panels by calling panel_loader.show() / hide()
    - Panels positioned next to palette
    - No widget reparenting = No Error 71!
    
    This keeps panel control logic centralized instead of scattered in main app.
    """
    
    def __init__(self, palette_widget):
        """Initialize panel manager.
        
        Args:
            palette_widget: The Master Palette container widget (for positioning panels)
        """
        self.panels = {}  # {category: panel_loader}
        self.active_panel = None
        self.palette_widget = palette_widget
    
    def register_panel(self, category, panel_loader):
        """Register a panel with the manager.
        
        Args:
            category: Panel category name ('files', 'analyses', etc.)
            panel_loader: Panel loader instance with show()/hide() methods
        """
        self.panels[category] = panel_loader
    
    def show_panel(self, category):
        """Show a specific panel (hide others).
        
        Args:
            category: Panel category to show
        """
        if category not in self.panels:
            return
        
        panel_loader = self.panels[category]
        
        # Hide all other panels
        for cat, loader in self.panels.items():
            if cat != category:
                loader.hide()
        
        # Show the requested panel
        panel_loader.show()
        
        self.active_panel = category
    
    def hide_all(self):
        """Hide all panels."""
        for loader in self.panels.values():
            loader.hide()
        self.active_panel = None


UI_PATH = Path(__file__).parents[3] / 'ui' / 'palettes' / 'master_palette.ui'


# Material Design inspired CSS for master palette - high contrast, bold colors
# Width: 48px = 40px button + 6px margin + 2px padding
PALETTE_CSS = """
/* Master Palette Container - 48px total width */
#master_palette_container {
    background-color: #263238;
    border-right: 2px solid #37474F;
    padding: 2px;
}

/* Palette Buttons - Base State (squared 40x40px buttons) */
.palette-button {
    background-color: #37474F;
    border: 2px solid #455A64;
    border-radius: 4px;
    color: #FFFFFF;
    transition: all 200ms cubic-bezier(0.4, 0.0, 0.2, 1);
    margin: 3px;
    min-width: 40px;
    min-height: 40px;
    padding: 0;
}

/* Hover State - Bright highlight */
.palette-button:hover {
    background-color: #4CAF50;
    border-color: #66BB6A;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(76, 175, 80, 0.5);
}

/* Pressed State */
.palette-button:active {
    background-color: #388E3C;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Active/Checked State (toggled on) - Bold orange */
.palette-button:checked,
.palette-button-active {
    background-color: #FF9800;
    border-color: #FFB74D;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5),
                inset 0 0 0 2px #FFA726,
                0 0 0 1px rgba(255, 152, 0, 0.6);
}

/* Active Hover State */
.palette-button:checked:hover,
.palette-button-active:hover {
    background-color: #FB8C00;
    border-color: #FFA726;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.5),
                inset 0 0 0 2px #FFB74D,
                0 0 0 1px rgba(251, 140, 0, 0.7);
}

/* Disabled State */
.palette-button:disabled {
    opacity: 0.35;
    background-color: #37474F;
    border-color: #455A64;
    color: #78909C;
    box-shadow: none;
}

/* Icon styling */
.palette-button image {
    min-width: 32px;
    min-height: 32px;
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
        ('report', 'document-properties-symbolic', 'Report Generation'),
    ]

    def __init__(self, builder: Gtk.Builder = None):
        self.builder = builder or Gtk.Builder()
        self.container = None
        self.buttons = {}
        self._callbacks = {}
        self._css_applied = False
        self._in_handler = {}  # Per-button guard flags to prevent re-entrance: {category: bool}
        self.panel_manager = None  # Will be set by setup_panel_manager()
        self.parent_window = None  # Parent window for panels

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
            # Width calculation: 40px button + 6px margin (3px each) + 2px padding (1px each) = 48px
            self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.container.set_name('master_palette_container')
            self.container.set_size_request(48, -1)
            self.container.set_spacing(0)
            self.container.set_hexpand(False)
            self.container.set_vexpand(True)
            self.container.set_visible(True)

    def _apply_css(self):
        """Apply Material Design CSS to palette widgets.
        
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
        # Add top margin for better aesthetics
        top_spacer = Gtk.Box()
        top_spacer.set_size_request(-1, 10)
        self.container.pack_start(top_spacer, False, False, 0)
        
        for i, (name, icon, tooltip) in enumerate(self.BUTTON_ORDER):
            pb = PaletteButton(name, icon, tooltip)
            self.buttons[name] = pb
            self.container.pack_start(pb.widget, False, False, 0)
            
            # Add spacing between buttons (8px between each button)
            if i < len(self.BUTTON_ORDER) - 1:
                separator = Gtk.Box()
                separator.set_size_request(-1, 8)
                self.container.pack_start(separator, False, False, 0)

        # All buttons are now implemented and enabled by default
        
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
        
        # Initialize per-button handler lock
        self._in_handler[category] = False
        
        # Wrapper with per-button re-entrance protection
        def protected_callback(active):
            if self._in_handler.get(category, False):
                # Already in this button's handler - don't trigger nested calls
                return
            
            self._in_handler[category] = True
            try:
                callback(active)
            except Exception as e:
                import traceback
                traceback.print_exc()
            finally:
                self._in_handler[category] = False
        
        self.buttons[category].connect_toggled(protected_callback)

    def set_active(self, category: str, active: bool):
        """Set button active state programmatically (e.g., for initial activation).
        
        This method allows deactivation handlers to run (for proper panel hiding),
        but prevents re-activating the same button to avoid recursion.
        """
        if category not in self.buttons:
            return
        
        button = self.buttons[category]
        if button.get_active() == active:
            return  # Already in desired state, nothing to do
        
        # Only block if we're activating AND already in this button's handler
        # This prevents infinite recursion while allowing deactivation handlers to run
        should_block = active and self._in_handler.get(category, False)
        
        if should_block:
            # Block handler to prevent recursion when re-activating same button
            was_in_handler = self._in_handler[category]
            self._in_handler[category] = True
            try:
                button.set_active(active)
            finally:
                self._in_handler[category] = was_in_handler
        else:
            # Allow handler to run (especially for deactivation)
            button.set_active(active)

    def is_active(self, category: str) -> bool:
        """Check if a button is currently active.
        
        Args:
            category: Button category name ('files', 'pathways', etc.)
        
        Returns:
            True if button is active, False otherwise
        """
        if category not in self.buttons:
            return False
        return self.buttons[category].get_active()

    def set_sensitive(self, category: str, sensitive: bool):
        """Enable/disable a button (e.g., disable Topology until implemented)."""
        if category not in self.buttons:
            return
        self.buttons[category].set_sensitive(sensitive)
    
    def setup_panel_manager(self):
        """Setup integrated panel management.
        
        This method configures the palette to automatically manage panels using
        the PanelManager. Call this instead of manually connecting callbacks.
        
        Example:
            palette.setup_panel_manager()
            palette.register_panel('files', left_panel_loader)
            palette.register_panel('analyses', right_panel_loader)
        """
        self.panel_manager = PanelManager(self.container)
    
    def register_panel(self, category, panel_loader):
        """Register a panel with integrated management.
        
        Must call setup_panel_manager() first!
        
        Args:
            category: Panel category ('files', 'analyses', 'pathways', 'topology')
            panel_loader: Panel loader with show()/hide() methods
        """
        if not self.panel_manager:
            raise RuntimeError("Call setup_panel_manager() before register_panel()")
        
        # Set palette widget as parent for panel positioning
        panel_loader.set_palette_parent(self.container)
        
        self.panel_manager.register_panel(category, panel_loader)
        
        # Auto-connect toggle handler
        def toggle_handler(is_active):
            if is_active:
                # Deactivate other buttons
                for cat in self.buttons:
                    if cat != category:
                        self.set_active(cat, False)
                # Show this panel
                self.panel_manager.show_panel(category)
            else:
                # Hide all panels
                self.panel_manager.hide_all()
        
        self.connect(category, toggle_handler)
    
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
