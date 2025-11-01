#!/usr/bin/env python3
"""Layout Settings Loader - Manages layout parameter panel.

Provides parameter panel for layout algorithms (Auto, Hierarchical, Force-Directed).

Parameters:
- Hierarchical: layer_spacing (vertical), node_spacing (horizontal)
- Force-Directed: iterations, k_multiplier (spacing control), scale (canvas size)

This parameter panel integrates with the universal ParameterPanelManager
(Phase 3 architecture) and provides comprehensive control over all layout algorithms.
"""

import os
from gi.repository import Gtk, Gdk, GObject


class LayoutSettingsLoader(GObject.GObject):
    """Loader for layout settings parameter panel.
    
    Provides UI for configuring layout algorithm parameters:
    
    Hierarchical Layout:
    - layer_spacing: Vertical spacing between layers (50-500px, default 150)
    - node_spacing: Horizontal spacing between nodes (50-300px, default 100)
    
    Force-Directed Layout:
    - iterations: Number of physics simulation steps (50-1000, default 500)
    - k_multiplier: Spacing control multiplier (0.5-3.0, default 1.5)
      * 0.5-1.0: Compact layout
      * 1.5: Balanced (default)
      * 2.0-3.0: Spacious layout
    - scale: Canvas size in pixels (500-5000, default 2000)
    
    Signals:
        settings-changed(): Emitted when any setting is modified
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
        
        # Hierarchical settings (defaults match algorithm defaults)
        self.layer_spacing = 150  # pixels (vertical spacing between layers)
        self.node_spacing = 100   # pixels (horizontal spacing between nodes)
        
        # Force-directed settings (defaults match algorithm defaults)
        self.iterations = 500     # physics simulation steps
        self.k_multiplier = 1.5   # spacing control (0.5=compact, 3.0=spacious)
        self.scale = 2000.0       # canvas size in pixels
        
        # UI widgets
        self.settings_revealer = None
        self.layer_spacing_entry = None
        self.node_spacing_entry = None
        self.iterations_entry = None
        self.k_multiplier_entry = None
        self.scale_entry = None
        
        self._load_ui()
    
    def _load_ui(self):
        """Load the layout settings panel UI from file."""
        if not os.path.exists(self.ui_path):
            return
        
        try:
            builder = Gtk.Builder()
            builder.add_from_file(self.ui_path)
            
            # Get widgets
            self.settings_revealer = builder.get_object('layout_settings_revealer')
            self.layer_spacing_entry = builder.get_object('layer_spacing_entry')
            self.node_spacing_entry = builder.get_object('node_spacing_entry')
            self.iterations_entry = builder.get_object('iterations_entry')
            self.k_multiplier_entry = builder.get_object('k_multiplier_entry')
            self.scale_entry = builder.get_object('scale_entry')
            
            if not self.settings_revealer:
                return
            
            # Connect signals - auto-emit on value change (no apply button needed)
            if self.layer_spacing_entry:
                self.layer_spacing_entry.connect('changed', self._on_layer_spacing_changed)
                self.layer_spacing_entry.connect('activate', self._on_layer_spacing_changed)
                self.layer_spacing_entry.set_sensitive(True)
                self.layer_spacing_entry.set_can_focus(True)
            
            if self.node_spacing_entry:
                self.node_spacing_entry.connect('changed', self._on_node_spacing_changed)
                self.node_spacing_entry.connect('activate', self._on_node_spacing_changed)
                self.node_spacing_entry.set_sensitive(True)
                self.node_spacing_entry.set_can_focus(True)
            
            if self.iterations_entry:
                self.iterations_entry.connect('changed', self._on_iterations_changed)
                self.iterations_entry.connect('activate', self._on_iterations_changed)
                self.iterations_entry.set_sensitive(True)
                self.iterations_entry.set_can_focus(True)
            
            if self.k_multiplier_entry:
                self.k_multiplier_entry.connect('changed', self._on_k_multiplier_changed)
                self.k_multiplier_entry.connect('activate', self._on_k_multiplier_changed)
                self.k_multiplier_entry.set_sensitive(True)
                self.k_multiplier_entry.set_can_focus(True)
            
            if self.scale_entry:
                self.scale_entry.connect('changed', self._on_scale_changed)
                self.scale_entry.connect('activate', self._on_scale_changed)
                self.scale_entry.set_sensitive(True)
                self.scale_entry.set_can_focus(True)
            
            # Load CSS
            self._load_css()
            
            # Initially revealed (no internal animation, parameter panel manager handles it)
            self.settings_revealer.set_reveal_child(True)
            self.settings_revealer.set_visible(True)
            
        except Exception as e:
            import traceback
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
        except Exception:
            pass
    
    def _on_layer_spacing_changed(self, entry):
        """Handle layer spacing entry change - auto-emit signal."""
        try:
            value = int(entry.get_text())
            # Clamp to valid range (50-500px)
            value = max(50, min(500, value))
            self.layer_spacing = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def _on_node_spacing_changed(self, entry):
        """Handle node spacing entry change - auto-emit signal."""
        try:
            value = int(entry.get_text())
            # Clamp to valid range (50-300px)
            value = max(50, min(300, value))
            self.node_spacing = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def _on_iterations_changed(self, entry):
        """Handle iterations entry change - auto-emit signal."""
        try:
            value = int(entry.get_text())
            # Clamp to valid range (50-1000)
            value = max(50, min(1000, value))
            self.iterations = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def _on_k_multiplier_changed(self, entry):
        """Handle k multiplier entry change - auto-emit signal."""
        try:
            value = float(entry.get_text())
            # Clamp to valid range (0.5-3.0)
            value = max(0.5, min(3.0, value))
            self.k_multiplier = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def _on_scale_changed(self, entry):
        """Handle scale entry change - auto-emit signal."""
        try:
            value = float(entry.get_text())
            # Clamp to valid range (500-5000)
            value = max(500.0, min(5000.0, value))
            self.scale = value
            self.emit('settings-changed')
        except ValueError:
            # Invalid input - ignore
            pass
    
    def get_settings(self):
        """Get current layout settings.
        
        Returns:
            dict: Current settings with keys:
                - Hierarchical: 'layer_spacing', 'node_spacing'
                - Force-Directed: 'iterations', 'k_multiplier', 'scale'
        """
        return {
            # Hierarchical parameters
            'layer_spacing': self.layer_spacing,
            'node_spacing': self.node_spacing,
            # Force-directed parameters
            'iterations': self.iterations,
            'k_multiplier': self.k_multiplier,
            'scale': self.scale
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
