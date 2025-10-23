#!/usr/bin/env python3
"""Layout Settings Loader - Manages layout parameter panel.

Provides parameter panel for layout algorithms (Auto, Hierarchical, Force-Directed).
Parameters include node spacing, iterations, and algorithm-specific settings.

This is a simple parameter panel that integrates with the universal
ParameterPanelManager (Phase 3 architecture).
"""

import os
from gi.repository import Gtk, Gdk, GObject


class LayoutSettingsLoader(GObject.GObject):
    """Loader for layout settings parameter panel.
    
    Provides UI for configuring layout algorithm parameters:
    - Node spacing (distance between nodes)
    - Iterations (for force-directed algorithm)
    - Other algorithm-specific parameters
    
    Signals:
        settings-changed(): Emitted when settings are modified
    """
    
    __gsignals__ = {
        'settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, ui_dir=None):
        """Initialize layout settings loader.
        
        Args:
            ui_dir: Directory containing UI files. Defaults to project ui/palettes/layout/.
        """
        super().__init__()
        
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'palettes', 'layout')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'layout_settings_panel.ui')
        
        # Settings values (defaults)
        self.spacing = 100  # pixels
        self.iterations = 50  # for force-directed
        
        # UI widgets
        self.settings_revealer = None
        self.spacing_entry = None
        self.iterations_entry = None
        
        self._load_ui()
    
    def _load_ui(self):
        """Load the layout settings panel UI from file."""
        if not os.path.exists(self.ui_path):
            print(f'Warning: Layout settings UI file not found: {self.ui_path}')
            return
        
        try:
            builder = Gtk.Builder()
            builder.add_from_file(self.ui_path)
            
            # Get widgets
            self.settings_revealer = builder.get_object('layout_settings_revealer')
            self.spacing_entry = builder.get_object('spacing_entry')
            self.iterations_entry = builder.get_object('iterations_entry')
            
            if not self.settings_revealer:
                print('Warning: layout_settings_revealer not found in UI file')
                return
            
            # Connect signals - auto-emit on value change (no apply button needed)
            if self.spacing_entry:
                self.spacing_entry.connect('changed', self._on_spacing_changed)
                self.spacing_entry.connect('activate', self._on_spacing_changed)
            if self.iterations_entry:
                self.iterations_entry.connect('changed', self._on_iterations_changed)
                self.iterations_entry.connect('activate', self._on_iterations_changed)
            
            # Load CSS
            self._load_css()
            
            # Initially revealed (no internal animation, parameter panel manager handles it)
            self.settings_revealer.set_reveal_child(True)
            self.settings_revealer.set_visible(True)
            
        except Exception as e:
            import traceback
            print(f'Error loading layout settings UI: {e}')
            traceback.print_exc()
            self.settings_revealer = None
    
    def _load_css(self):
        """Load CSS styling for settings panel."""
        css_path = os.path.join(self.ui_dir, 'layout_settings_panel.css')
        
        if not os.path.exists(css_path):
            return
        
        try:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_path(css_path)
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen, css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f'Warning: Failed to load layout settings CSS: {e}')
    
    def _on_spacing_changed(self, entry):
        """Handle spacing entry change - auto-emit signal."""
        try:
            value = int(entry.get_text())
            # Clamp to valid range
            value = max(20, min(500, value))
            self.spacing = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def _on_iterations_changed(self, entry):
        """Handle iterations entry change - auto-emit signal."""
        try:
            value = int(entry.get_text())
            # Clamp to valid range
            value = max(10, min(200, value))
            self.iterations = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def get_settings(self):
        """Get current layout settings.
        
        Returns:
            dict: Current settings {'spacing': int, 'iterations': int}
        """
        return {
            'spacing': self.spacing,
            'iterations': self.iterations
        }
    
    def create_settings_panel(self):
        """Factory method to create settings panel widget.
        
        Called by ParameterPanelManager to get the settings panel.
        
        Returns:
            Gtk.Revealer: Settings panel revealer, or None if not available.
        """
        if self.settings_revealer:
            self.settings_revealer.set_visible(True)
            self.settings_revealer.set_reveal_child(True)
        return self.settings_revealer


__all__ = ['LayoutSettingsLoader']
