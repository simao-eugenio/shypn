#!/usr/bin/env python3
"""Standalone test application for SwissKnifePalette.

Runs independently of main shypn application.
Tests animations, CSS, signals with placeholder tools.

Usage:
    python3 test_app.py --mode edit      # Test Edit mode
    python3 test_app.py --mode simulate  # Test Simulate mode
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import sys
import argparse
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add shypn to path for model imports
shypn_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, shypn_path)

from placeholder_palette import PlaceholderPalette


class MockPetriNetModel:
    """Minimal mock Petri Net model for testing simulation palette.
    
    This is a minimal stub to satisfy SimulateToolsPaletteLoader's requirements.
    It doesn't implement full simulation logic - just enough for the palette to load.
    """
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
        self.initial_marking = {}
        print("[MockModel] Created minimal Petri Net model for testing")


class SwissKnifeTestApp(Gtk.Window):
    """Standalone test application window."""
    
    def __init__(self, mode='edit'):
        super().__init__(title=f"SwissKnifePalette Test - {mode.upper()} Mode")
        
        self.mode = mode
        self.palette = None
        
        self.set_default_size(900, 700)
        self.set_border_width(10)
        
        # Create main layout
        self._create_layout()
        
        # Create palette
        self._create_palette()
        
        # Connect window signals
        self.connect('destroy', Gtk.main_quit)
        
        # Initial log message
        self.log("Test application ready. Click category buttons to test.")
    
    def _create_layout(self):
        """Create main window layout."""
        # Main vertical box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_vbox)
        
        # Header
        header = self._create_header()
        main_vbox.pack_start(header, False, False, 0)
        
        # Canvas area with overlay (for palette)
        self.canvas_overlay = self._create_canvas_area()
        main_vbox.pack_start(self.canvas_overlay, True, True, 0)
        
        # Console log area
        console_frame = self._create_console()
        main_vbox.pack_start(console_frame, False, False, 0)
    
    def _create_header(self):
        """Create header with mode info and controls."""
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Mode indicator
        self.mode_label = Gtk.Label()
        self.mode_label.set_markup(f"<b>Mode: {self.mode.upper()}</b>")
        hbox.pack_start(self.mode_label, False, False, 0)
        
        # Spacer
        hbox.pack_start(Gtk.Box(), True, True, 0)
        
        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup("<i>Click category buttons → Watch animations → Check console</i>")
        hbox.pack_start(info_label, False, False, 0)
        
        # Spacer
        hbox.pack_start(Gtk.Box(), True, True, 0)
        
        # Mode switch buttons
        edit_btn = Gtk.Button(label="Switch to EDIT")
        edit_btn.connect('clicked', self._on_switch_mode, 'edit')
        hbox.pack_start(edit_btn, False, False, 0)
        
        sim_btn = Gtk.Button(label="Switch to SIMULATE")
        sim_btn.connect('clicked', self._on_switch_mode, 'simulate')
        hbox.pack_start(sim_btn, False, False, 0)
        
        return hbox
    
    def _create_canvas_area(self):
        """Create simulated canvas area with overlay."""
        overlay = Gtk.Overlay()
        
        # Simulated drawing area
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_size_request(400, 400)
        drawing_area.connect('draw', self._on_draw_canvas)
        
        overlay.add(drawing_area)
        
        return overlay
    
    def _on_draw_canvas(self, widget, cr):
        """Draw simulated canvas (gray background with text)."""
        # Get widget size
        alloc = widget.get_allocation()
        width = alloc.width
        height = alloc.height
        
        # Fill with light gray
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        # Draw border
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.set_line_width(2)
        cr.rectangle(1, 1, width - 2, height - 2)
        cr.stroke()
        
        # Draw text
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(14)
        
        text = "Simulated Canvas (Petri Net would go here)"
        extents = cr.text_extents(text)
        x = (width - extents.width) / 2
        y = (height - extents.height) / 2
        
        cr.move_to(x, y)
        cr.show_text(text)
        
        return False
    
    def _create_console(self):
        """Create console log area."""
        frame = Gtk.Frame(label="Signal Console")
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(-1, 200)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.console_buffer = Gtk.TextBuffer()
        text_view = Gtk.TextView(buffer=self.console_buffer)
        text_view.set_editable(False)
        text_view.set_monospace(True)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Add tag for different message types
        tag_table = self.console_buffer.get_tag_table()
        
        signal_tag = Gtk.TextTag(name="signal")
        signal_tag.set_property("foreground", "#2980b9")
        signal_tag.set_property("weight", 700)
        tag_table.add(signal_tag)
        
        animation_tag = Gtk.TextTag(name="animation")
        animation_tag.set_property("foreground", "#27ae60")
        tag_table.add(animation_tag)
        
        tool_tag = Gtk.TextTag(name="tool")
        tool_tag.set_property("foreground", "#8e44ad")
        tag_table.add(tool_tag)
        
        error_tag = Gtk.TextTag(name="error")
        error_tag.set_property("foreground", "#c0392b")
        error_tag.set_property("weight", 700)
        tag_table.add(error_tag)
        
        scrolled.add(text_view)
        frame.add(scrolled)
        
        return frame
    
    def _create_palette(self):
        """Create PlaceholderPalette and attach to overlay."""
        self.log(f"Creating PlaceholderPalette(mode='{self.mode}')")
        
        try:
            # Create mock model for widget palettes (e.g., Simulate)
            mock_model = MockPetriNetModel()
            
            # Create palette with model
            self.palette = PlaceholderPalette(mode=self.mode, model=mock_model)
            
            # Connect signals
            self.palette.connect('category-selected', self._on_category_selected)
            self.palette.connect('tool-activated', self._on_tool_activated)
            self.palette.connect('sub-palette-shown', self._on_sub_palette_shown)
            self.palette.connect('sub-palette-hidden', self._on_sub_palette_hidden)
            
            # Connect mode change signal
            self.palette.connect('mode-change-requested', self._on_mode_change_requested)
            
            # Connect simulation palette signals
            self.palette.connect('simulation-step-executed', self._on_simulation_step)
            self.palette.connect('simulation-reset-executed', self._on_simulation_reset)
            self.palette.connect('simulation-settings-changed', self._on_simulation_settings_changed)
            
            # Attach to overlay
            palette_widget = self.palette.get_widget()
            self.canvas_overlay.add_overlay(palette_widget)
            
            # Position at bottom-center
            palette_widget.set_halign(Gtk.Align.CENTER)
            palette_widget.set_valign(Gtk.Align.END)
            palette_widget.set_margin_bottom(20)
            
            palette_widget.show_all()
            
            self.log("✓ PlaceholderPalette created and attached", "signal")
            
        except Exception as e:
            self.log(f"✗ Error creating palette: {e}", "error")
            import traceback
            traceback.print_exc()
    
    def _on_switch_mode(self, button, new_mode):
        """Handle mode switch button click."""
        if new_mode == self.mode:
            self.log(f"Already in {new_mode} mode")
            return
        
        self.log(f"\n{'='*60}")
        self.log(f"MODE SWITCH: {self.mode} → {new_mode}", "signal")
        self.log(f"{'='*60}")
        
        # Remove old palette
        if self.palette:
            old_widget = self.palette.get_widget()
            self.canvas_overlay.remove(old_widget)
            self.log(f"✓ Removed old palette ({self.mode})")
        
        # Update mode
        self.mode = new_mode
        self.mode_label.set_markup(f"<b>Mode: {new_mode.upper()}</b>")
        self.set_title(f"SwissKnifePalette Test - {new_mode.upper()} Mode")
        
        # Create new palette
        self._create_palette()
    
    def _on_category_selected(self, palette, category_id):
        """Log category button click."""
        self.log(f"[SIGNAL] category-selected: '{category_id}'", "signal")
    
    def _on_mode_change_requested(self, palette, requested_mode):
        """Handle mode change request from palette.
        
        Args:
            palette: PlaceholderPalette instance
            requested_mode: 'edit' or 'simulate'
        """
        self.log(f"[SIGNAL] mode-change-requested: '{requested_mode}'", "signal")
        
        # Check if mode needs to change
        if requested_mode != self.mode:
            self.log(f"[MODE CHANGE] Switching from {self.mode} to {requested_mode}", "signal")
            self._on_switch_mode(None, requested_mode)
        else:
            self.log(f"[MODE CHANGE] Already in {requested_mode} mode - showing sub-palette only", "signal")
    
    def _on_tool_activated(self, palette, tool_id):
        """Log tool activation."""
        self.log(f"[SIGNAL] tool-activated: '{tool_id}'", "tool")
    
    def _on_sub_palette_shown(self, palette, palette_id):
        """Log sub-palette reveal."""
        self.log(f"[SIGNAL] sub-palette-shown: '{palette_id}'", "signal")
    
    def _on_sub_palette_hidden(self, palette, palette_id):
        """Log sub-palette hide."""
        self.log(f"[SIGNAL] sub-palette-hidden: '{palette_id}'", "signal")
    
    def _on_simulation_step(self, palette, time):
        """Log simulation step."""
        self.log(f"[SIMULATION] Step executed at time: {time:.3f}s", "animation")
    
    def _on_simulation_reset(self, palette):
        """Log simulation reset."""
        self.log(f"[SIMULATION] Reset executed", "signal")
    
    def _on_simulation_settings_changed(self, palette):
        """Log simulation settings change."""
        self.log(f"[SIMULATION] Settings changed", "signal")
    
    def log(self, message, tag=None):
        """Log message to console.
        
        Args:
            message: Message text
            tag: Optional tag name ('signal', 'animation', 'tool', 'error')
        """
        end_iter = self.console_buffer.get_end_iter()
        
        if tag:
            self.console_buffer.insert_with_tags_by_name(end_iter, message + '\n', tag)
        else:
            self.console_buffer.insert(end_iter, message + '\n')
        
        # Auto-scroll to bottom
        mark = self.console_buffer.create_mark(None, self.console_buffer.get_end_iter(), False)
        GLib.idle_add(lambda: self._scroll_to_mark(mark))
    
    def _scroll_to_mark(self, mark):
        """Scroll text view to mark."""
        # Find the text view
        frame = None
        for child in self.get_children():
            if isinstance(child, Gtk.Box):
                for subchild in child.get_children():
                    if isinstance(subchild, Gtk.Frame):
                        frame = subchild
                        break
        
        if frame:
            scrolled = frame.get_child()
            if scrolled:
                text_view = scrolled.get_child()
                if text_view:
                    text_view.scroll_mark_onscreen(mark)
        
        return False  # Don't repeat


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='SwissKnifePalette Test Application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode edit      # Test Edit mode
  %(prog)s --mode simulate  # Test Simulate mode

Test Instructions:
  1. Click category buttons to reveal sub-palettes
  2. Watch animations (slide up/down, 200ms)
  3. Click tools to test signal emission
  4. Use mode switch buttons to change modes
  5. Check console for signal logs
  6. Verify CSS styling (hover effects, active states)
        """
    )
    parser.add_argument(
        '--mode',
        choices=['edit', 'simulate'],
        default='edit',
        help='Initial mode to test (default: edit)'
    )
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "="*60)
    print("SwissKnifePalette Test Application")
    print("="*60)
    print(f"Initial Mode: {args.mode.upper()}")
    print("\nInstructions:")
    print("  1. Click category buttons to reveal sub-palettes")
    print("  2. Watch animations (slide up/down, 200ms)")
    print("  3. Click tools to test signal emission")
    print("  4. Use mode switch buttons to change modes")
    print("  5. Check console for signal logs")
    print("  6. Verify CSS styling (hover effects, highlights)")
    print("="*60 + "\n")
    
    # Create and run app
    app = SwissKnifeTestApp(mode=args.mode)
    app.show_all()
    
    Gtk.main()


if __name__ == '__main__':
    main()
