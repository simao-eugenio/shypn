#!/usr/bin/env python3
"""
Settings Sub-Palette Testbed Application

Standalone GTK3 application for testing the settings sub-palette prototype
before integrating into production code.

Run:
    python -m shypn.dev.settings_sub_palette_testbed.test_app
"""

import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import cairo

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))

from shypn.dev.settings_sub_palette_testbed.mock_simulation import MockSimulationController
from shypn.dev.settings_sub_palette_testbed.settings_palette_loader import SettingsPaletteLoader


class SettingsSubPaletteTestApp(Gtk.Window):
    """Test application window for settings sub-palette prototype."""
    
    def __init__(self):
        super().__init__(title="Settings Sub-Palette Testbed")
        
        # Window setup
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        
        # Create mock simulation controller
        self.simulation = MockSimulationController()
        
        # Create main layout
        self._setup_ui()
        
        print("=" * 70)
        print("SETTINGS SUB-PALETTE TESTBED")
        print("=" * 70)
        print()
        print("Testing:")
        print("  1. Settings button [⚙] toggles sub-palette")
        print("  2. Speed preset buttons (0.1x, 1x, 10x, 60x)")
        print("  3. Custom speed spin button")
        print("  4. Time step controls (Auto/Manual)")
        print("  5. Conflict policy combo")
        print("  6. Apply/Reset buttons")
        print()
        print("Try:")
        print("  • Click [⚙] to expand/collapse settings")
        print("  • Click [R] to start simulation")
        print("  • Change speed while running")
        print("  • Watch time display update with speed indicator")
        print()
        print("=" * 70)
        print()
    
    def _setup_ui(self):
        """Setup the test application UI."""
        # Create overlay to mimic production canvas structure
        overlay = Gtk.Overlay()
        self.add(overlay)
        
        # Add a drawing area as fake canvas background
        drawing_area = Gtk.DrawingArea()
        drawing_area.connect('draw', self._on_draw_background)
        overlay.add(drawing_area)
        
        # Add status label at top
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        header.set_halign(Gtk.Align.CENTER)
        header.set_valign(Gtk.Align.START)
        header.set_margin_top(20)
        
        title_label = Gtk.Label()
        title_label.set_markup('<span size="x-large" weight="bold">Settings Sub-Palette Testbed</span>')
        header.pack_start(title_label, False, False, 0)
        
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup('<span size="small">Prototype for time scale controls</span>')
        header.pack_start(subtitle_label, False, False, 0)
        
        status_label = Gtk.Label()
        status_label.set_markup('<span size="small" style="italic">Click [⚙] to expand settings</span>')
        status_label.set_margin_top(10)
        header.pack_start(status_label, False, False, 0)
        self.status_label = status_label
        
        overlay.add_overlay(header)
        
        # Load settings palette
        ui_dir = current_dir
        self.palette_loader = SettingsPaletteLoader(self.simulation, ui_dir)
        
        # Connect signals for status updates
        self.palette_loader.connect('step-executed', self._on_step_executed)
        self.palette_loader.connect('reset-executed', self._on_reset_executed)
        self.palette_loader.connect('settings-changed', self._on_settings_changed)
        
        # Add palette to overlay
        palette_widget = self.palette_loader.get_widget()
        overlay.add_overlay(palette_widget)
        
        # Show info box in center
        self._add_info_box(overlay)
        
        self.show_all()
    
    def _add_info_box(self, overlay):
        """Add info box in center of canvas."""
        info_box = Gtk.Frame()
        info_box.set_halign(Gtk.Align.CENTER)
        info_box.set_valign(Gtk.Align.CENTER)
        info_box.set_shadow_type(Gtk.ShadowType.OUT)
        
        info_grid = Gtk.Grid()
        info_grid.set_row_spacing(8)
        info_grid.set_column_spacing(12)
        info_grid.set_margin_top(20)
        info_grid.set_margin_bottom(20)
        info_grid.set_margin_start(20)
        info_grid.set_margin_end(20)
        
        # Title
        title = Gtk.Label()
        title.set_markup('<span size="large" weight="bold">Testing Checklist</span>')
        info_grid.attach(title, 0, 0, 2, 1)
        
        # Checklist items
        checklist_items = [
            ("Phase 1", "Settings button toggles sub-palette"),
            ("Phase 2", "Speed presets behave like radio buttons"),
            ("Phase 3", "Custom spin unchecks presets"),
            ("Phase 4", "Time display shows speed (@ Nx)"),
            ("Phase 5", "Smooth slide-down/up animation"),
            ("Phase 6", "Settings persist when reopening"),
        ]
        
        row = 1
        for phase, description in checklist_items:
            phase_label = Gtk.Label()
            phase_label.set_markup(f'<span weight="bold">{phase}:</span>')
            phase_label.set_xalign(1)
            info_grid.attach(phase_label, 0, row, 1, 1)
            
            desc_label = Gtk.Label(description)
            desc_label.set_xalign(0)
            info_grid.attach(desc_label, 1, row, 1, 1)
            
            row += 1
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        info_grid.attach(separator, 0, row, 2, 1)
        row += 1
        
        # Current status
        self.test_status_label = Gtk.Label()
        self.test_status_label.set_markup('<span style="italic">Waiting for interaction...</span>')
        info_grid.attach(self.test_status_label, 0, row, 2, 1)
        
        info_box.add(info_grid)
        overlay.add_overlay(info_box)
    
    def _on_draw_background(self, widget, cr):
        """Draw fake canvas background."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # Draw gradient background
        pattern = cairo.LinearGradient(0, 0, 0, height)
        pattern.add_color_stop_rgb(0, 0.95, 0.95, 0.97)
        pattern.add_color_stop_rgb(1, 0.85, 0.85, 0.90)
        cr.set_source(pattern)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        # Draw grid pattern
        cr.set_source_rgba(0.8, 0.8, 0.85, 0.3)
        cr.set_line_width(1)
        
        # Vertical lines
        for x in range(0, width, 50):
            cr.move_to(x, 0)
            cr.line_to(x, height)
            cr.stroke()
        
        # Horizontal lines
        for y in range(0, height, 50):
            cr.move_to(0, y)
            cr.line_to(width, y)
            cr.stroke()
        
        return False
    
    def _on_step_executed(self, loader, time):
        """Handle simulation step executed."""
        self.test_status_label.set_markup(
            f'<span color="#27ae60">✓ Simulation running</span> '
            f'(t={time:.2f}s, speed={self.simulation.settings.time_scale:.1f}x)'
        )
    
    def _on_reset_executed(self, loader):
        """Handle simulation reset."""
        self.test_status_label.set_markup(
            '<span color="#f39c12">↻ Simulation reset to t=0.0s</span>'
        )
    
    def _on_settings_changed(self, loader):
        """Handle settings changed."""
        settings = self.simulation.settings
        self.test_status_label.set_markup(
            f'<span color="#3498db">⚙ Settings updated:</span> '
            f'dt={settings.get_effective_dt():.3f}s, '
            f'speed={settings.time_scale:.1f}x, '
            f'policy={settings.conflict_policy}'
        )


def main():
    """Run the testbed application."""
    app = SettingsSubPaletteTestApp()
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\n\n✓ Testbed closed by user")
    
    print("\n" + "=" * 70)
    print("TESTBED SESSION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review console output for any errors")
    print("  2. Verify all checklist items passed")
    print("  3. If validated, proceed with production integration")
    print()


if __name__ == '__main__':
    main()
