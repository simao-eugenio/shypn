#!/usr/bin/env python3
"""
Test different methods of showing GTK4 PopoverMenu.
This will help us find what works on your system.
"""

import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib

class TestApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.test.popover')
        
    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("PopoverMenu Test")
        window.set_default_size(400, 300)
        
        # Create a label that we'll right-click on
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        label = Gtk.Label(label="Right-click anywhere in this window!")
        label.set_vexpand(True)
        box.append(label)
        
        window.set_child(box)
        
        # Create simple menu model
        menu = Gio.Menu()
        menu.append("Test Item 1", "app.test1")
        menu.append("Test Item 2", "app.test2")
        menu.append("Test Item 3", "app.test3")
        
        # Create actions
        action1 = Gio.SimpleAction.new("test1", None)
        action1.connect("activate", lambda a, p: print("✓ Item 1 clicked!"))
        self.add_action(action1)
        
        action2 = Gio.SimpleAction.new("test2", None)
        action2.connect("activate", lambda a, p: print("✓ Item 2 clicked!"))
        self.add_action(action2)
        
        action3 = Gio.SimpleAction.new("test3", None)
        action3.connect("activate", lambda a, p: print("✓ Item 3 clicked!"))
        self.add_action(action3)
        
        # Create PopoverMenu
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        popover.set_parent(window)
        popover.set_has_arrow(False)
        popover.set_autohide(True)
        
        # Add right-click gesture
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)  # Right button
        gesture.connect("pressed", lambda g, n, x, y: self.show_menu(popover, x, y))
        window.add_controller(gesture)
        
        self.popover = popover
        window.present()
        
        print("\n" + "="*60)
        print("PopoverMenu Test Application")
        print("="*60)
        print("\nRight-click anywhere to test different show methods")
        print("\nMethods that will be tried:")
        print("  1. popup()")
        print("  2. present()")
        print("  3. set_visible(True)")
        print("  4. popup() without pointing_to")
        print("\n" + "="*60 + "\n")
    
    def show_menu(self, popover, x, y):
        print(f"\n🖱️  Right-click at ({x:.0f}, {y:.0f})")
        
        # Method 1: popup() with rectangle
        print("  Testing Method 1: popup() with rectangle...")
        rect = Gtk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)
        try:
            popover.popup()
            print("    ✓ popup() called successfully")
            return
        except Exception as e:
            print(f"    ✗ popup() failed: {e}")
        
        # Method 2: present()
        print("  Testing Method 2: present()...")
        try:
            popover.present()
            print("    ✓ present() called successfully")
            return
        except Exception as e:
            print(f"    ✗ present() failed: {e}")
        
        # Method 3: set_visible
        print("  Testing Method 3: set_visible(True)...")
        try:
            popover.set_visible(True)
            print("    ✓ set_visible() called successfully")
            return
        except Exception as e:
            print(f"    ✗ set_visible() failed: {e}")
        
        # Method 4: popup without rectangle
        print("  Testing Method 4: popup() without rectangle...")
        try:
            popover.popup()
            print("    ✓ popup() (no rect) called successfully")
        except Exception as e:
            print(f"    ✗ popup() (no rect) failed: {e}")

if __name__ == '__main__':
    app = TestApp()
    app.run(None)
