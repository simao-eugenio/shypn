import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class ModePaletteLoader(GObject.GObject):
    __gsignals__ = {
        'mode-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'edit-palettes-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),  # True=show, False=hide
    }

    def __init__(self):
        super().__init__()
        builder = Gtk.Builder()
        builder.add_from_file('ui/palettes/mode/mode_palette.ui')
        self.container = builder.get_object('mode_palette_container')
        self.edit_button = builder.get_object('edit_mode_button')
        self.sim_button = builder.get_object('sim_mode_button')
        self.edit_button.connect('clicked', self.on_edit_clicked)
        self.sim_button.connect('clicked', self.on_sim_clicked)
        self.current_mode = 'edit'  # Start in edit mode
        self.edit_palettes_visible = False  # Palettes start hidden
        
        # Apply CSS for active mode button highlighting
        self._apply_css()
        
        self.update_button_states()  # Set initial button states
        print(f"[ModePalette] Initialized in {self.current_mode} mode")
    
    def _apply_css(self):
        """Apply CSS styling for mode buttons."""
        css = b"""
        .mode-button.active-mode {
            background: linear-gradient(to bottom, #3498db, #2980b9);
            border: 2px solid #2471a3;
            font-weight: bold;
            color: white;
            box-shadow: inset 0 1px 3px rgba(255, 255, 255, 0.3),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .mode-button:not(.active-mode) {
            opacity: 0.7;
        }
        
        .mode-button:not(.active-mode):hover {
            opacity: 1.0;
        }
        """
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.edit_button.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

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
        return self.container
