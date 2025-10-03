#!/usr/bin/env python3
"""Minimal test to verify right-click gesture is working."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gio
except Exception as e:
    print(f'ERROR: GTK4 not available: {e}', file=sys.stderr)
    sys.exit(1)


class TestWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Right-Click Test")
        self.set_default_size(400, 300)
        
        # Create a simple tree view
        self.store = Gtk.ListStore(str)
        self.store.append(["Item 1"])
        self.store.append(["Item 2"])
        self.store.append(["Item 3"])
        
        self.tree_view = Gtk.TreeView(model=self.store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        self.tree_view.append_column(column)
        
        # Add right-click gesture
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)  # Right mouse button
        gesture.connect("pressed", self.on_right_click)
        self.tree_view.add_controller(gesture)
        
        # Create simple context menu
        self.setup_menu()
        
        # Add to window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.tree_view)
        self.set_child(scrolled)
        
        print("✓ Test window created")
        print("✓ Right-click gesture added")
        print("✓ Context menu prepared")
        print("\n👉 Try right-clicking on the tree view!\n")
    
    def setup_menu(self):
        """Setup a simple context menu."""
        # Create action
        action = Gio.SimpleAction.new("test", None)
        action.connect("activate", lambda a, p: print("✓ Menu item activated!"))
        
        # Create action group
        action_group = Gio.SimpleActionGroup()
        action_group.add_action(action)
        self.tree_view.insert_action_group("test", action_group)
        
        # Create menu model
        menu = Gio.Menu()
        menu.append("Test Item", "test.test")
        
        # Create popover
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(menu)
        self.popover.set_parent(self.tree_view)
        self.popover.set_has_arrow(False)
    
    def on_right_click(self, gesture, n_press, x, y):
        """Handle right-click."""
        print(f"\n🖱️  RIGHT-CLICK DETECTED at ({x:.1f}, {y:.1f})")
        print(f"  → n_press: {n_press}")
        print(f"  → Gesture: {gesture}")
        print(f"  → Popover: {self.popover}")
        
        # Show menu
        rect = Gtk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        
        self.popover.set_pointing_to(rect)
        print(f"  → Calling popup()...")
        self.popover.popup()
        print(f"  → popup() called!\n")


def on_activate(app):
    window = TestWindow(app)
    window.present()


def main():
    app = Gtk.Application(application_id='com.test.rightclick')
    app.connect('activate', on_activate)
    print("Starting right-click test app...")
    app.run(None)


if __name__ == '__main__':
    main()
