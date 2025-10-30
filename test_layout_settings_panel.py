#!/usr/bin/env python3
"""
Quick test for layout settings panel - verify all parameters are editable
and properly connected.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.helpers.layout_settings_loader import LayoutSettingsLoader


class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Layout Settings Panel Test")
        
        self.set_default_size(400, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        
        # Create layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.add(vbox)
        
        # Title
        title = Gtk.Label()
        title.set_markup('<span size="large" weight="bold">Layout Settings Panel Test</span>')
        vbox.pack_start(title, False, False, 0)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            '<span size="small">Edit the values below and watch the console output.</span>'
        )
        vbox.pack_start(instructions, False, False, 0)
        
        # Create layout settings loader
        self.loader = LayoutSettingsLoader()
        
        if self.loader.settings_revealer:
            vbox.pack_start(self.loader.settings_revealer, False, False, 0)
            
            # Connect signal
            self.loader.connect('settings-changed', self._on_settings_changed)
            
            # Status label
            self.status_label = Gtk.Label()
            self.status_label.set_markup('<span size="small" style="italic">Ready</span>')
            vbox.pack_start(self.status_label, False, False, 10)
            
            # Current values display
            self.values_label = Gtk.Label()
            self._update_values_display()
            vbox.pack_start(self.values_label, True, True, 0)
            
            print("✅ Layout settings panel loaded successfully")
            print()
            print("TESTING:")
            print("  1. Try editing each entry")
            print("  2. Verify values are clamped to valid ranges")
            print("  3. Check that settings-changed signal fires")
            print()
            self._show_current_values()
        else:
            error_label = Gtk.Label()
            error_label.set_markup('<span color="red">Failed to load settings panel!</span>')
            vbox.pack_start(error_label, True, True, 0)
            print("❌ Failed to load layout settings panel")
    
    def _on_settings_changed(self, loader):
        """Handle settings change."""
        self.status_label.set_markup(
            '<span size="small" style="italic" color="green">Settings changed!</span>'
        )
        self._update_values_display()
        self._show_current_values()
        
        # Reset status after 1 second
        GLib.timeout_add(1000, self._reset_status)
    
    def _reset_status(self):
        """Reset status label."""
        self.status_label.set_markup('<span size="small" style="italic">Ready</span>')
        return False  # Don't repeat
    
    def _update_values_display(self):
        """Update values display label."""
        settings = self.loader.get_settings()
        text = '<span size="small" font="monospace">\n'
        text += '<b>Current Values:</b>\n\n'
        text += '<b>Hierarchical:</b>\n'
        text += f'  layer_spacing: {settings["layer_spacing"]} px\n'
        text += f'  node_spacing:  {settings["node_spacing"]} px\n\n'
        text += '<b>Force-Directed:</b>\n'
        text += f'  iterations:    {settings["iterations"]}\n'
        text += f'  k_multiplier:  {settings["k_multiplier"]}\n'
        text += f'  scale:         {settings["scale"]} px\n'
        text += '</span>'
        self.values_label.set_markup(text)
    
    def _show_current_values(self):
        """Print current values to console."""
        settings = self.loader.get_settings()
        print("-" * 50)
        print("HIERARCHICAL:")
        print(f"  layer_spacing: {settings['layer_spacing']} px")
        print(f"  node_spacing:  {settings['node_spacing']} px")
        print()
        print("FORCE-DIRECTED:")
        print(f"  iterations:    {settings['iterations']}")
        print(f"  k_multiplier:  {settings['k_multiplier']}")
        print(f"  scale:         {settings['scale']} px")
        print("-" * 50)
        print()


if __name__ == '__main__':
    print("=" * 60)
    print("LAYOUT SETTINGS PANEL TEST")
    print("=" * 60)
    print()
    
    window = TestWindow()
    window.show_all()
    
    Gtk.main()
