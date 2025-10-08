#!/usr/bin/env python3
"""
Standalone test for New Project dialog
"""
import sys
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.project_models import ProjectManager
from shypn.helpers.project_dialog_manager import ProjectDialogManager

def on_project_created(project):
    print(f"✓ Project created callback: {project.name}")
    Gtk.main_quit()

def main():
    print("Creating main window...")
    window = Gtk.Window(title="Test Window")
    window.set_default_size(400, 300)
    window.connect("destroy", Gtk.main_quit)
    
    button = Gtk.Button(label="New Project")
    window.add(button)
    
    print("Initializing ProjectManager...")
    pm = ProjectManager()
    print(f"Projects root: {pm.projects_root}")
    
    print("Initializing ProjectDialogManager...")
    dialog_manager = ProjectDialogManager(parent_window=window)
    dialog_manager.on_project_created = on_project_created
    
    print(f"Projects root: {dialog_manager.project_manager.projects_root}")
    
    def on_button_clicked(btn):
        print("\n" + "="*50)
        print("Button clicked - showing dialog...")
        print("="*50)
        try:
            project = dialog_manager.show_new_project_dialog()
            if project:
                print(f"\n✓ SUCCESS: Project created!")
                print(f"  Name: {project.name}")
                print(f"  Path: {project.base_path}")
            else:
                print("\n✗ Dialog cancelled or failed")
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    button.connect("clicked", on_button_clicked)
    
    print("\nShowing window...")
    window.show_all()
    
    print("Starting GTK main loop...")
    print("Click the 'New Project' button to test\n")
    Gtk.main()

if __name__ == "__main__":
    main()
