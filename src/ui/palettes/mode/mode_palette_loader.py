import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango
import os
from pathlib import Path

class ModePaletteLoader(GObject.GObject):
    __gsignals__ = {
        'mode-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'edit-palettes-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),  # True=show, False=hide
    }

    def __init__(self, ui_path=None):
        super().__init__()
        
        # Auto-detect UI path (like zoom palette)
        if ui_path is None:
            repo_root = Path(__file__).parent.parent.parent.parent.parent
            ui_path = os.path.join(repo_root, 'ui', 'palettes', 'mode', 'mode_palette.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.mode_palette_container = None  # Main container (outer box)
        self.mode_control = None  # Inner styled box (like zoom_control)
        self.edit_button = None
        self.sim_button = None
        
        self.current_mode = 'edit'  # Start in edit mode
        self.edit_palettes_visible = False  # Palettes start hidden
        
        # CSS provider for styling
        self.css_provider = None
        
        # Font metrics for dynamic sizing
        self.target_height = 28  # Will be calculated from font metrics
        
        print(f"[ModePalette] Initialized (will load UI from {self.ui_path})")
    
    def load(self):
        """Load the mode palette UI and return the widget.
        
        Returns:
            Gtk.Box: The mode palette container widget.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If required widgets not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Mode palette UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.ui_path)
        
        # Extract widgets
        self.mode_palette_container = self.builder.get_object('mode_palette_container')
        self.mode_control = self.builder.get_object('mode_control')
        self.edit_button = self.builder.get_object('edit_mode_button')
        self.sim_button = self.builder.get_object('sim_mode_button')
        
        if self.mode_palette_container is None:
            raise ValueError("Object 'mode_palette_container' not found in mode_palette.ui")
        
        if self.mode_control is None:
            raise ValueError("Object 'mode_control' not found in mode_palette.ui")
        
        if self.edit_button is None:
            raise ValueError("Object 'edit_mode_button' not found in mode_palette.ui")
        
        if self.sim_button is None:
            raise ValueError("Object 'sim_mode_button' not found in mode_palette.ui")
        
        # Calculate optimal size based on font metrics (like zoom palette)
        self._calculate_target_size()
        
        # Apply custom CSS styling (zoom-style)
        self._apply_css()
        
        # Connect button signals
        self.edit_button.connect('clicked', self.on_edit_clicked)
        self.sim_button.connect('clicked', self.on_sim_clicked)
        
        # Set initial button states
        self.update_button_states()
        
        print(f"[ModePalette] Loaded and initialized in {self.current_mode} mode")
        
        return self.mode_palette_container
    
    def _calculate_target_size(self):
        """Calculate target button size as 1.3× the height of 'W' character (from zoom palette)."""
        # Create a temporary label to measure font
        temp_label = Gtk.Label(label="W")
        
        # Get the Pango layout
        layout = temp_label.get_layout()
        if layout:
            # Get pixel extents of the 'W' character
            ink_rect, logical_rect = layout.get_pixel_extents()
            w_height = logical_rect.height
            
            # Calculate target as 1.3× W height
            self.target_height = int(w_height * 1.3)
            
            # Ensure minimum size for usability
            if self.target_height < 24:
                self.target_height = 24
            
            print(f"[ModePalette] Calculated target button size: {self.target_height}px")
        else:
            # Fallback if layout not available
            self.target_height = 28
            print(f"[ModePalette] Using fallback button size: {self.target_height}px")
    
    def _apply_css(self):
        """Apply custom CSS styling to match zoom palette."""
        css = f"""
        .mode-palette {{
            background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
            border: 2px solid #5568d3;
            border-radius: 8px;
            padding: 3px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }}
        
        .mode-button {{
            background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
            border: 2px solid #5568d3;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
            min-width: {self.target_height}px;
            min-height: {self.target_height}px;
            padding: 0;
            margin: 0;
            transition: all 200ms ease;
        }}
        
        .mode-button:hover {{
            background: linear-gradient(to bottom, #e8f0ff 0%, #d5e5ff 100%);
            border-color: #667eea;
            color: #5568d3;
            box-shadow: 0 0 8px rgba(102, 126, 234, 0.5);
        }}
        
        .mode-button:active {{
            background: linear-gradient(to bottom, #d0e0ff 0%, #c0d5ff 100%);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        /* Active mode highlighting */
        .mode-button.active-mode {{
            background: linear-gradient(to bottom, #3498db, #2980b9);
            border: 2px solid #2471a3;
            font-weight: bold;
            color: white;
            box-shadow: inset 0 1px 3px rgba(255, 255, 255, 0.3),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .mode-button:not(.active-mode) {{
            opacity: 0.9;
        }}
        
        .mode-button:not(.active-mode):hover {{
            opacity: 1.0;
        }}
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
    
    # ==================== Signal Handlers (PRESERVED) ====================

    def on_edit_clicked(self, button):
        """Switch to edit mode (mutually exclusive with sim mode)."""
        if self.current_mode == 'sim':
            # Switch from sim to edit mode
            self.current_mode = 'edit'
            self.edit_palettes_visible = False  # Start with palettes hidden
            self.emit('mode-changed', 'edit')
            self.update_button_states()
            print(f"[ModePalette] Switched to edit mode")
        else:
            print(f"[ModePalette] Already in edit mode - no action")

    def on_sim_clicked(self, button):
        """Switch to simulation mode (mutually exclusive with edit mode)."""
        if self.current_mode == 'edit':
            # Switch from edit to sim mode
            self.current_mode = 'sim'
            self.edit_palettes_visible = False  # Hide edit palettes when switching to sim
            self.emit('mode-changed', 'sim')
            self.update_button_states()
            print(f"[ModePalette] Switched to simulation mode")
        else:
            print(f"[ModePalette] Already in simulation mode - no action")

    def update_button_states(self):
        """Update button visual appearance - highlight active mode button."""
        # Use CSS classes to show which mode is active
        # Active button: bold/highlighted, Inactive button: normal
        
        edit_context = self.edit_button.get_style_context()
        sim_context = self.sim_button.get_style_context()
        
        if self.current_mode == 'edit':
            # Edit mode active: highlight Edit button, normal Sim button
            edit_context.add_class('active-mode')
            sim_context.remove_class('active-mode')
            print(f"[ModePalette] Button states: Edit=ACTIVE (highlighted), Sim=inactive")
        else:
            # Sim mode active: highlight Sim button, normal Edit button
            edit_context.remove_class('active-mode')
            sim_context.add_class('active-mode')
            print(f"[ModePalette] Button states: Edit=inactive, Sim=ACTIVE (highlighted)")

    def get_widget(self):
        """Get the mode palette container widget.
        
        Returns:
            Gtk.Box: The mode palette container widget, or None if not loaded.
        """
        return self.mode_palette_container


# ==================== Factory Function ====================

def create_mode_palette(ui_path=None):
    """Factory function to create and load the mode palette (like zoom palette).
    
    Args:
        ui_path: Optional path to mode_palette.ui.
        
    Returns:
        ModePaletteLoader: The loaded mode palette instance.
        
    Example:
        palette = create_mode_palette()
        widget = palette.load()
        # Add widget as overlay to canvas
    """
    palette = ModePaletteLoader(ui_path)
    palette.load()
    return palette

