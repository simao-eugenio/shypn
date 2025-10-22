#!/usr/bin/env python3
"""Simple test script to show window skeleton with left vertical container."""

import sys
import os

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


def main():
    """Main function to create and show the window."""
    
    # Get path to UI file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(script_dir, 'simple_window.ui')
    
    if not os.path.exists(ui_path):
        print(f"ERROR: UI file not found: {ui_path}", file=sys.stderr)
        return 1
    
    print(f"[INFO] Loading UI from: {ui_path}", file=sys.stderr)
    
    # Create GTK Application
    app = Gtk.Application(application_id='dev.shypn.simple_window')
    
    def on_activate(application):
        """Activate callback - build and show the window."""
        
        # Load main window UI file
        builder = Gtk.Builder()
        try:
            builder.add_from_file(ui_path)
        except Exception as e:
            print(f"ERROR: Failed to load UI: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Get main window
        window = builder.get_object('main_window')
        if window is None:
            print("ERROR: main_window not found in UI file", file=sys.stderr)
            sys.exit(1)
        
        # Load File Explorer window
        file_explorer_ui_path = os.path.join(script_dir, 'file_explorer_window.ui')
        file_explorer_builder = Gtk.Builder()
        try:
            file_explorer_builder.add_from_file(file_explorer_ui_path)
            print("[INFO] File Explorer UI loaded", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to load File Explorer UI: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Get File Explorer window and its content (notebook)
        file_explorer_window = file_explorer_builder.get_object('file_explorer_window')
        file_explorer_notebook = file_explorer_builder.get_object('file_explorer_notebook')
        
        if not file_explorer_window or not file_explorer_notebook:
            print("ERROR: File Explorer window or notebook not found", file=sys.stderr)
            sys.exit(1)
        
        # Get dock area where File Explorer will be docked
        dock_area = builder.get_object('dock_area')
        if not dock_area:
            print("ERROR: Dock area not found", file=sys.stderr)
            sys.exit(1)
        
        # Extract notebook from window and dock it to dock_area
        file_explorer_window.remove(file_explorer_notebook)
        dock_area.pack_start(file_explorer_notebook, True, True, 0)
        # Destroy the window (we only needed it to load the UI structure)
        file_explorer_window.destroy()
        print("[INFO] File Explorer notebook docked to dock_area", file=sys.stderr)
        
        # Set notebook to not expand and allow it to be hidden
        file_explorer_notebook.set_hexpand(False)
        file_explorer_notebook.set_vexpand(True)
        
        # Initially set dock area to collapsed (0 width) and hide its content
        dock_area.set_size_request(0, -1)
        file_explorer_notebook.set_visible(False)
        print("[INFO] Dock area initially collapsed (0px width, notebook hidden)", file=sys.stderr)
        
        # Get status bar and set initial message
        status_bar = builder.get_object('status_bar')
        if status_bar:
            context_id = status_bar.get_context_id("main")
            status_bar.push(context_id, "Ready - Window skeleton loaded")
        
        # Get toggle button and connect handler
        toggle_button = builder.get_object('test_toggle_button')
        if toggle_button:
            def on_toggle(button):
                """Handle toggle button state change - reveal/hide docked File Explorer."""
                is_active = button.get_active()
                state = "REVEALED" if is_active else "HIDDEN"
                print(f"[TOGGLE] File Explorer {state} (dock_area width: {'300px' if is_active else '0px'})", file=sys.stderr)
                
                # Reveal or hide the docked File Explorer
                if is_active:
                    # Reveal: show notebook and expand dock area
                    file_explorer_notebook.set_visible(True)
                    dock_area.set_size_request(300, -1)
                else:
                    # Hide: collapse dock area and hide notebook
                    dock_area.set_size_request(0, -1)
                    file_explorer_notebook.set_visible(False)
                
                if status_bar:
                    status_bar.pop(context_id)
                    if is_active:
                        status_bar.push(context_id, "File Explorer revealed (300px)")
                    else:
                        status_bar.push(context_id, "File Explorer hidden (0px)")
            
            toggle_button.connect('toggled', on_toggle)
            print("[INFO] Toggle button connected to File Explorer window", file=sys.stderr)
        
        # Set up the application
        window.set_application(application)
        
        # Show the window
        print("[INFO] Showing window...", file=sys.stderr)
        window.show_all()
        print("[INFO] Window shown successfully", file=sys.stderr)
        
        # IMPORTANT: Hide the File Explorer AFTER show_all()
        # show_all() reveals everything, so we need to explicitly hide what should start hidden
        dock_area.set_size_request(0, -1)
        file_explorer_notebook.set_visible(False)
        print("[INFO] File Explorer hidden after show_all()", file=sys.stderr)
    
    # Connect activate signal
    app.connect('activate', on_activate)
    
    # Run the application
    try:
        return app.run(sys.argv)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code if exit_code is not None else 0)
    except KeyboardInterrupt:
        sys.exit(0)
