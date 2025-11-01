#!/usr/bin/env python3
"""
Test Ctrl+Click Multi-Selection with Drag and Delete
====================================================

This test demonstrates the new multi-selection behavior:

1. Ctrl+Click on unselected object → Add to selection
2. Ctrl+Click on selected object → Remove from selection  
3. Regular Click+Drag on selected objects → Drag all selected
4. Delete key → Delete all selected objects

Usage:
    python3 test_ctrl_multi_select.py

Expected Behavior:
------------------
✅ Click object → Select (deselect others)
✅ Ctrl+Click another object → Add to selection (multi-select)
✅ Ctrl+Click selected object → Remove from selection
✅ Click+Drag selected object → Drag all selected objects together
✅ Press Delete → Delete all selected objects
✅ Rectangle selection with Ctrl → Add objects to existing selection
✅ Rectangle selection without Ctrl → Replace selection

Interactive Test:
-----------------
1. Create 3-4 places by clicking the Place tool then clicking canvas
2. Click on first place → Should select it (blue highlight)
3. Ctrl+Click second place → Both should be selected
4. Ctrl+Click third place → All three selected
5. Ctrl+Click second place again → Should deselect it (only 1st and 3rd remain)
6. Click+Drag first place → All selected places should move together
7. Press Delete key → All selected places should be deleted

Code Changes:
-------------
File: src/shypn/helpers/model_canvas_loader.py
Location: _on_button_press() method, ~line 1380

Added logic to detect Ctrl+Click on already-selected object and deselect it
instead of starting a drag operation.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.edit.manager import Manager
from shypn.helpers.model_canvas_loader import ModelCanvasLoader


class MultiSelectTestWindow(Gtk.Window):
    """Test window for Ctrl+Click multi-selection."""
    
    def __init__(self):
        super().__init__(title="Ctrl+Click Multi-Selection Test")
        self.set_default_size(800, 600)
        self.connect('destroy', Gtk.main_quit)
        
        # Create main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        
        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup(
            "<b>Multi-Selection Test</b>\n\n"
            "• <b>Click</b> object → Select (deselect others)\n"
            "• <b>Ctrl+Click</b> unselected → Add to selection\n"
            "• <b>Ctrl+Click</b> selected → Remove from selection\n"
            "• <b>Click+Drag</b> selected → Move all selected\n"
            "• <b>Delete</b> key → Delete all selected\n"
            "• <b>Rectangle</b> selection (drag on empty) with Ctrl → Add to selection"
        )
        info_label.set_justify(Gtk.Justification.LEFT)
        vbox.pack_start(info_label, False, False, 10)
        
        # Toolbar with tools
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        vbox.pack_start(toolbar, False, False, 0)
        
        # Place tool button
        place_btn = Gtk.Button(label="🔵 Place Tool")
        place_btn.connect('clicked', self.on_place_tool_clicked)
        toolbar.pack_start(place_btn, False, False, 0)
        
        # Transition tool button
        transition_btn = Gtk.Button(label="⬜ Transition Tool")
        transition_btn.connect('clicked', self.on_transition_tool_clicked)
        toolbar.pack_start(transition_btn, False, False, 0)
        
        # Select tool button (default)
        select_btn = Gtk.Button(label="👆 Select Tool")
        select_btn.connect('clicked', self.on_select_tool_clicked)
        toolbar.pack_start(select_btn, False, False, 0)
        
        # Clear button
        clear_btn = Gtk.Button(label="🗑️ Clear All")
        clear_btn.connect('clicked', self.on_clear_clicked)
        toolbar.pack_start(clear_btn, False, False, 0)
        
        # Selection info label
        self.selection_label = Gtk.Label(label="Selection: None")
        toolbar.pack_end(self.selection_label, False, False, 10)
        
        # Drawing area (canvas)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_can_focus(True)
        self.drawing_area.set_size_request(800, 500)
        
        # Add event mask for mouse and keyboard
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.SCROLL_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )
        
        vbox.pack_start(self.drawing_area, True, True, 0)
        
        # Initialize manager and loader
        self.manager = Manager()
        self.loader = ModelCanvasLoader()
        self.loader.load(self.drawing_area, self.manager)
        
        # Connect selection changed signal to update label
        self.drawing_area.connect('draw', self.on_draw_update_selection)
        
    def on_draw_update_selection(self, widget, cr):
        """Update selection label after each draw."""
        selected = self.manager.selection_manager.get_selected_objects(self.manager)
        if selected:
            obj_types = [type(obj).__name__ for obj in selected]
            self.selection_label.set_text(f"Selected: {len(selected)} objects ({', '.join(obj_types)})")
        else:
            self.selection_label.set_text("Selection: None")
        return False
    
    def on_place_tool_clicked(self, button):
        """Activate place tool."""
        self.manager.set_tool('place', active=True)
        print("✓ Place tool activated - Click canvas to create places")
    
    def on_transition_tool_clicked(self, button):
        """Activate transition tool."""
        self.manager.set_tool('transition', active=True)
        print("✓ Transition tool activated - Click canvas to create transitions")
    
    def on_select_tool_clicked(self, button):
        """Activate select tool."""
        self.manager.set_tool('select', active=True)
        print("✓ Select tool activated")
    
    def on_clear_clicked(self, button):
        """Clear all objects."""
        self.manager.model.places.clear()
        self.manager.model.transitions.clear()
        self.manager.model.arcs.clear()
        self.manager.clear_all_selections()
        self.drawing_area.queue_draw()
        print("✓ Cleared all objects")


def main():
    """Run the multi-selection test."""
    print("=" * 70)
    print("CTRL+CLICK MULTI-SELECTION TEST")
    print("=" * 70)
    print()
    print("Starting test window...")
    print()
    print("Test Procedure:")
    print("1. Click 'Place Tool' and create 3-4 places on canvas")
    print("2. Click 'Select Tool' to activate selection mode")
    print("3. Click first place → Should select it (blue)")
    print("4. Ctrl+Click second place → Both selected")
    print("5. Ctrl+Click third place → All three selected")
    print("6. Ctrl+Click second place → Should DESELECT it")
    print("7. Click+Drag first place → All selected should move")
    print("8. Press Delete → All selected should be deleted")
    print()
    
    window = MultiSelectTestWindow()
    window.show_all()
    
    print("✓ Window opened. Try the multi-selection features!")
    print()
    
    Gtk.main()


if __name__ == '__main__':
    main()
