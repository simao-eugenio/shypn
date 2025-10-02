#!/usr/bin/env python3
"""Right Panel Loader/Controller.

This module is responsible for loading and managing the right Dynamic Analyses panel.
The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container (extreme right)
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK4 not available in right_panel loader:', e, file=sys.stderr)
    sys.exit(1)


class RightPanelLoader:
    """Loader and controller for the right Dynamic Analyses panel (attachable window)."""
    
    def __init__(self, ui_path=None):
        """Initialize the right panel loader.
        
        Args:
            ui_path: Optional path to right_panel.ui. If None, uses default location.
        """
        if ui_path is None:
            # Default: ui/panels/right_panel.ui
            # This loader file is in: src/shypn/helpers/right_panel_loader.py
            # UI file is in: ui/panels/right_panel.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'panels', 'right_panel.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.window = None
        self.content = None
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
    
    def load(self):
        """Load the panel UI and return the window.
        
        Returns:
            Gtk.Window: The right panel window.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If window or content not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Right panel UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('right_panel_window')
        self.content = self.builder.get_object('right_panel_content')
        
        if self.window is None:
            raise ValueError("Object 'right_panel_window' not found in right_panel.ui")
        if self.content is None:
            raise ValueError("Object 'right_panel_content' not found in right_panel.ui")
        
        # Get float button and connect callback
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
        else:
            self.float_button = None
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        print(f"✓ Right panel window loaded from: {os.path.basename(self.ui_path)}")
        return self.window
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        print(f"→ Right panel float button toggled: active={is_active}, is_attached={self.is_attached}")
        if is_active:
            # Button is now active -> float the panel
            self.float(self.parent_window)
        else:
            # Button is now inactive -> dock the panel back
            if self.parent_container:
                self.attach_to(self.parent_container, self.parent_window)
    
    def float(self, parent_window=None):
        """Float panel as a separate window (detach if currently attached).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        # Recreate window if it was destroyed during attach
        if self.window is None:
            # Reload the UI to recreate the window
            self.builder = Gtk.Builder.new_from_file(self.ui_path)
            self.window = self.builder.get_object('right_panel_window')
            # Get float button and reconnect callback
            float_button = self.builder.get_object('float_button')
            if float_button:
                float_button.connect('toggled', self._on_float_toggled)
                self.float_button = float_button
            # Content reference is still valid, just needs to be reparented
        
        # If currently attached, unattach first
        if self.is_attached:
            self.unattach()
        
        # Set as transient for parent if provided
        if parent_window:
            self.window.set_transient_for(parent_window)
        
        # Update float button state
        if self.float_button and not self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating (to collapse paned)
        if self.on_float_callback:
            self.on_float_callback()
        
        self.window.present()
        print("✓ Right panel: floating")
    
    def detach(self, parent_window=None):
        """Detach panel to show as a floating window.
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        # Detach is now an alias for float
        self.float(parent_window)
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (embed content in extreme right, hide window).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        print(f"  → attach_to called: container={container}, parent_container={self.parent_container}")
        if self.window is None:
            self.load()
        
        # Store parent window and container for float button callback
        if parent_window:
            self.parent_window = parent_window
        self.parent_container = container
        
        # Extract content from window first
        if self.content.get_parent() == self.window:
            self.window.set_child(None)
        
        # Destroy the window to prevent phantom windows (especially on WSL/X11)
        # We'll recreate it when floating again
        if self.window:
            self.window.destroy()
            self.window = None
        
        # Only append if not already in container
        if self.content.get_parent() != container:
            container.append(self.content)
        
        # Make container visible when panel is attached
        container.set_visible(True)
        
        # Make sure content is visible
        self.content.set_visible(True)
        
        # Update float button state
        print(f"  → Updating button: current={self.float_button.get_active() if self.float_button else 'none'}")
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        self.is_attached = True
        
        # Notify that panel is attached (to expand paned)
        if self.on_attach_callback:
            self.on_attach_callback()
        
        print("✓ Right panel: attached (extreme right)")
    
    def unattach(self):
        """Unattach panel from container (return content to window)."""
        if not self.is_attached:
            return
        
        # Remove from container
        if self.parent_container and self.content.get_parent() == self.parent_container:
            self.parent_container.remove(self.content)
        
        # Return content to window
        self.window.set_child(self.content)
        
        self.is_attached = False
        # Don't clear parent_container - we need it to dock back
        print("✓ Right panel: unattached")
    
    def hide(self):
        """Hide panel (works for both attached and detached states)."""
        if self.is_attached:
            # When attached, hide both content and container
            self.content.set_visible(False)
            if self.parent_container:
                self.parent_container.set_visible(False)
        elif self.window:
            self.window.set_visible(False)
        print("✓ Right panel: hidden")


def create_right_panel(ui_path=None):
    """Convenience function to create and load the right panel loader.
    
    Args:
        ui_path: Optional path to right_panel.ui.
        
    Returns:
        RightPanelLoader: The loaded right panel loader instance.
        
    Example:
        loader = create_right_panel()
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to extreme right
    """
    loader = RightPanelLoader(ui_path)
    loader.load()
    return loader
