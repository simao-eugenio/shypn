#!/usr/bin/env python3
"""Test production SwissKnifePalette with real tool implementations.

Tests the production-ready SwissKnifePalette and ToolRegistry to verify:
- Tools are created correctly
- Tool signals work properly
- Tool buttons respond to clicks
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import sys
import os

# Add shypn to path
shypn_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, shypn_path)

from shypn.ui.swissknife_palette import SwissKnifePalette
from shypn.ui.swissknife_tool_registry import ToolRegistry


class MockPetriNetModel:
    """Minimal mock model for testing."""
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
        self.initial_marking = {}


class ProductionToolsTestApp(Gtk.Window):
    """Test window for production SwissKnifePalette."""
    
    def __init__(self):
        super().__init__(title="SwissKnifePalette Production Test")
        
        # Window setup
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        
        # Create mock model
        self.model = MockPetriNetModel()
        
        # Create tool registry
        self.tool_registry = ToolRegistry()
        
        # Create production SwissKnifePalette
        self.palette = SwissKnifePalette(
            mode='edit',
            model=self.model,
            tool_registry=self.tool_registry
        )
        
        # Connect signals
        self._connect_signals()
        
        # Create overlay for positioning
        overlay = Gtk.Overlay()
        
        # Background (canvas simulation)
        background = Gtk.DrawingArea()
        background.set_size_request(800, 600)
        background.connect('draw', self._on_draw_background)
        overlay.add(background)
        
        # Add palette as overlay
        palette_widget = self.palette.get_widget()
        palette_widget.set_halign(Gtk.Align.CENTER)
        palette_widget.set_valign(Gtk.Align.END)
        palette_widget.set_margin_bottom(20)
        overlay.add_overlay(palette_widget)
        
        # Add to window
        self.add(overlay)
        self.show_all()
        
        print("\n" + "="*60)
        print("PRODUCTION SWISSKNIFE PALETTE TEST")
        print("="*60)
        print("Testing tool implementations:")
        print("- Edit category: P, T, A, S, L tools")
        print("- Simulate category: Widget palette")
        print("- Layout category: Auto, Hier, Force tools")
        print("\nClick tools to test signal emission.")
        print("="*60 + "\n")
    
    def _connect_signals(self):
        """Connect palette signals."""
        self.palette.connect('category-selected', self._on_category_selected)
        self.palette.connect('tool-activated', self._on_tool_activated)
        self.palette.connect('mode-change-requested', self._on_mode_change_requested)
        self.palette.connect('sub-palette-shown', self._on_sub_palette_shown)
        self.palette.connect('sub-palette-hidden', self._on_sub_palette_hidden)
    
    def _on_draw_background(self, widget, cr):
        """Draw simple background."""
        # Light gray background
        cr.set_source_rgb(0.95, 0.95, 0.95)
        cr.paint()
        
        # Title text
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.select_font_face("Sans", 0, 1)
        cr.set_font_size(24)
        cr.move_to(20, 40)
        cr.show_text("Production SwissKnifePalette Test")
        
        cr.set_font_size(14)
        cr.move_to(20, 70)
        cr.show_text("Click category buttons to reveal tools, then click tools to test signals")
        
        return False
    
    def _on_category_selected(self, palette, category):
        """Handle category selection."""
        print(f"[SIGNAL] category-selected: {category}")
    
    def _on_tool_activated(self, palette, tool_id):
        """Handle tool activation."""
        print(f"[SIGNAL] tool-activated: {tool_id}")
        print(f"  → This would call: canvas_manager.set_tool('{tool_id}')")
    
    def _on_mode_change_requested(self, palette, mode):
        """Handle mode change request."""
        print(f"[SIGNAL] mode-change-requested: {mode}")
        print(f"  → This would switch application to {mode} mode")
    
    def _on_sub_palette_shown(self, palette, category):
        """Handle sub-palette shown."""
        print(f"[SIGNAL] sub-palette-shown: {category}")
    
    def _on_sub_palette_hidden(self, palette, category):
        """Handle sub-palette hidden."""
        print(f"[SIGNAL] sub-palette-hidden: {category}")


def main():
    """Run test application."""
    app = ProductionToolsTestApp()
    Gtk.main()


if __name__ == '__main__':
    main()
