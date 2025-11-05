#!/usr/bin/env python3
"""
Test KEGG import with auto-load functionality.

This test verifies that:
1. KEGG import with catalysts enabled works
2. Model is automatically loaded into canvas after import
3. Pan and zoom functions work immediately after import
4. Test arcs (catalysts) are visible and rendered correctly
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.ui.panels.pathway_operations.kegg_category import KEGGCategory
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.project.project import Project


class TestWindow(Gtk.Window):
    """Test window for KEGG import with auto-load."""
    
    def __init__(self):
        super().__init__(title="Test KEGG Import Auto-Load")
        self.set_default_size(1200, 800)
        self.connect('destroy', Gtk.main_quit)
        
        # Create main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.add(main_box)
        
        # Left panel: KEGG category
        left_paned = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left_paned.set_size_request(400, -1)
        main_box.pack_start(left_paned, False, True, 0)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Test Auto-Load After KEGG Import</b>\n\n"
            "1. Enable 'Show catalysts' checkbox\n"
            "2. Import hsa00010 (Glycolysis)\n"
            "3. Verify model loads automatically\n"
            "4. Test pan (drag) and zoom (wheel)\n\n"
            "<b>Expected:</b>\n"
            "• Model visible immediately after import\n"
            "• 63 enzyme places with test arcs\n"
            "• Pan/zoom work without File → Open\n"
            "• Test arcs: dashed lines + hollow diamonds"
        )
        instructions.set_line_wrap(True)
        instructions.set_xalign(0)
        left_paned.pack_start(instructions, False, True, 6)
        
        # Create temporary project
        self.project = self._create_temp_project()
        
        # Create model canvas manager
        self.canvas_manager = ModelCanvasManager()
        
        # Create KEGG category panel
        self.kegg_category = KEGGCategory(
            project=self.project,
            model_canvas=self.canvas_manager,
            file_panel_loader=None  # Not needed for test
        )
        
        # Add KEGG panel to left side
        kegg_scroll = Gtk.ScrolledWindow()
        kegg_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        kegg_scroll.add(self.kegg_category)
        left_paned.pack_start(kegg_scroll, True, True, 0)
        
        # Right panel: Canvas
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.pack_start(right_box, True, True, 0)
        
        # Canvas toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        right_box.pack_start(toolbar, False, True, 0)
        
        # Zoom controls
        zoom_in_btn = Gtk.Button(label="Zoom In (+)")
        zoom_in_btn.connect('clicked', lambda b: self._zoom_in())
        toolbar.pack_start(zoom_in_btn, False, True, 0)
        
        zoom_out_btn = Gtk.Button(label="Zoom Out (-)")
        zoom_out_btn.connect('clicked', lambda b: self._zoom_out())
        toolbar.pack_start(zoom_out_btn, False, True, 0)
        
        fit_btn = Gtk.Button(label="Fit to Page")
        fit_btn.connect('clicked', lambda b: self._fit_to_page())
        toolbar.pack_start(fit_btn, False, True, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="Ready to import")
        self.status_label.set_xalign(0)
        toolbar.pack_start(self.status_label, True, True, 6)
        
        # Canvas drawing area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_vexpand(True)
        self.drawing_area.connect('draw', self._on_draw)
        self.drawing_area.connect('scroll-event', self._on_scroll)
        self.drawing_area.set_events(
            Gdk.EventMask.SCROLL_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        
        # Pan state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.drawing_area.connect('button-press-event', self._on_button_press)
        self.drawing_area.connect('button-release-event', self._on_button_release)
        self.drawing_area.connect('motion-notify-event', self._on_motion)
        
        canvas_frame = Gtk.Frame()
        canvas_frame.add(self.drawing_area)
        right_box.pack_start(canvas_frame, True, True, 0)
        
        # Connect canvas manager to drawing area
        self.canvas_manager.drawing_area = self.drawing_area
        
        # Monitor canvas changes
        def on_canvas_change(manager, change_type, obj):
            count = (len(manager.places) + len(manager.transitions) + len(manager.arcs))
            self.status_label.set_text(
                f"Canvas: {len(manager.places)} places, "
                f"{len(manager.transitions)} transitions, "
                f"{len(manager.arcs)} arcs (Zoom: {manager.get_zoom():.1%})"
            )
            self.drawing_area.queue_draw()
        
        self.canvas_manager.add_observer(on_canvas_change)
        
        self.show_all()
    
    def _create_temp_project(self):
        """Create temporary project for testing."""
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='shypn_test_')
        print(f"Created temp project: {temp_dir}")
        
        # Create project structure
        project = Project(temp_dir)
        project.create_new_project()
        return project
    
    def _zoom_in(self):
        """Zoom in canvas."""
        self.canvas_manager.zoom_in()
        self.drawing_area.queue_draw()
        self._update_status()
    
    def _zoom_out(self):
        """Zoom out canvas."""
        self.canvas_manager.zoom_out()
        self.drawing_area.queue_draw()
        self._update_status()
    
    def _fit_to_page(self):
        """Fit canvas to page."""
        self.canvas_manager.fit_to_page()
        self.drawing_area.queue_draw()
        self._update_status()
    
    def _update_status(self):
        """Update status label."""
        self.status_label.set_text(
            f"Canvas: {len(self.canvas_manager.places)} places, "
            f"{len(self.canvas_manager.transitions)} transitions, "
            f"{len(self.canvas_manager.arcs)} arcs "
            f"(Zoom: {self.canvas_manager.get_zoom():.1%})"
        )
    
    def _on_draw(self, widget, cr):
        """Handle canvas draw event."""
        # White background
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        
        # Render model
        zoom = self.canvas_manager.get_zoom()
        pan_x, pan_y = self.canvas_manager.get_pan()
        
        # Apply transformations
        cr.translate(pan_x, pan_y)
        cr.scale(zoom, zoom)
        
        # Render all objects
        for place in self.canvas_manager.places:
            if hasattr(place, 'render'):
                place.render(cr, zoom=zoom)
        
        for transition in self.canvas_manager.transitions:
            if hasattr(transition, 'render'):
                transition.render(cr, zoom=zoom)
        
        for arc in self.canvas_manager.arcs:
            if hasattr(arc, 'render'):
                arc.render(cr, zoom=zoom)
        
        return False
    
    def _on_scroll(self, widget, event):
        """Handle scroll event for zoom."""
        if event.direction == Gdk.ScrollDirection.UP:
            self.canvas_manager.zoom_in()
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.canvas_manager.zoom_out()
        
        self.drawing_area.queue_draw()
        self._update_status()
        return True
    
    def _on_button_press(self, widget, event):
        """Handle button press for panning."""
        if event.button == 1:  # Left button
            self.panning = True
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            return True
        return False
    
    def _on_button_release(self, widget, event):
        """Handle button release."""
        if event.button == 1:
            self.panning = False
            return True
        return False
    
    def _on_motion(self, widget, event):
        """Handle motion for panning."""
        if self.panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            # Update pan
            pan_x, pan_y = self.canvas_manager.get_pan()
            self.canvas_manager.set_pan(pan_x + dx, pan_y + dy)
            
            # Update start position
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            
            self.drawing_area.queue_draw()
            return True
        return False


def main():
    """Run test."""
    print("="*70)
    print("KEGG Import Auto-Load Test")
    print("="*70)
    print("\nTest Objectives:")
    print("1. Import KEGG pathway with catalysts enabled")
    print("2. Verify model loads automatically into canvas")
    print("3. Verify pan and zoom work immediately")
    print("4. Verify test arcs (catalysts) are visible\n")
    print("Instructions:")
    print("• Enable 'Show catalysts (Biological Petri Net)' checkbox")
    print("• Import hsa00010 (Glycolysis pathway)")
    print("• Model should appear automatically after import")
    print("• Test pan (drag) and zoom (mouse wheel)")
    print("• Verify dashed test arcs with hollow diamond endpoints")
    print("="*70)
    
    win = TestWindow()
    Gtk.main()


if __name__ == '__main__':
    main()
