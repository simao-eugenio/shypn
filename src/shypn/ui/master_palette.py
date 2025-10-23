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

/* Palette Buttons - Base State (40x40px for 32x32px icons) */
.palette-button {
    background-color: #37474F;
    border: 2px solid #455A64;
    border-radius: 6px;
    color: #FFFFFF;
    transition: all 150ms ease;
    margin: 3px;
    min-width: 40px;
    min-height: 40px;
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
        self._in_handler = False  # Single guard flag to prevent re-entrance
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
        """Apply Nord-themed CSS to palette widgets.
        
        WAYLAND SAFE: Only applies CSS if not already applied and screen is available.
        This should be called after widget is realized to avoid Wayland surface issues.
        """
        # TESTING: Disable CSS completely to see if it causes Wayland Error 71
        print("[CSS] MasterPalette CSS application DISABLED for testing", file=sys.stderr)
        return
        
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
        
        # Wrapper with re-entrance protection
        def protected_callback(active):
            if self._in_handler:
                # Already in a handler - don't trigger nested calls
                return
            
            self._in_handler = True
            try:
                callback(active)
            except Exception as e:
                print(f"[ERROR] Master Palette callback failed for {category}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
            finally:
                self._in_handler = False
        
        self.buttons[category].connect_toggled(protected_callback)

    def set_active(self, category: str, active: bool):
        """Set button active state programmatically (e.g., for initial activation).
        
        This method blocks the callback to prevent re-entrance when called from within
        a toggle handler (e.g., when one button deactivates others).
        """
        if category not in self.buttons:
            return
        
        # Block handler during programmatic set to avoid recursion
        button = self.buttons[category]
        if button.get_active() == active:
            return  # Already in desired state, nothing to do
        
        # Use handler lock to prevent callback during programmatic change
        was_in_handler = self._in_handler
        self._in_handler = True
        try:
            button.set_active(active)
        finally:
            self._in_handler = was_in_handler

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
