#!/usr/bin/env python3
"""Left Panel Loader/Controller.

This module is responsible for loading and managing the left File Operations panel.
The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container (extreme left)

The panel integrates three sub-controllers (following OOP principles):
  - FileExplorerPanel: File browser tree view
  - ProjectActionsController: Project management actions
  - Built-in: File operations toolbar
  
Architecture:
  LeftPanelLoader: Minimal loader, UI state management, dock/float behavior
  └── Delegates to:
      ├── FileExplorerPanel: File browsing logic
      └── ProjectActionsController: Project actions logic
"""
import os
import sys
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in left_panel loader:', e, file=sys.stderr)
    sys.exit(1)

# Import sub-controllers (OOP: composition over inheritance)
from shypn.helpers.file_explorer_panel import FileExplorerPanel
from shypn.helpers.project_actions_controller import ProjectActionsController


class LeftPanelLoader:
    """Loader and controller for the left File Operations panel (attachable window)."""
    
    def __init__(self, ui_path=None, base_path=None):
        """Initialize the left panel loader.
        
        Args:
            ui_path: Optional path to left_panel.ui. If None, uses default location.
            base_path: Optional base path for file explorer. If None, uses examples directory.
        """
        if ui_path is None:
            # Default: ui/panels/left_panel.ui
            # This loader file is in: src/shypn/helpers/left_panel_loader.py
            # UI file is in: ui/panels/left_panel.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'panels', 'left_panel.ui')
            
            # If base_path not provided, start at workspace/ to show examples/, projects/, cache/
            # This prevents users from accessing application code (src/, tests/, ui/)
            if base_path is None:
                base_path = os.path.join(repo_root, 'workspace')
                # Ensure base_path exists
                if not os.path.exists(base_path):
                    try:
                        os.makedirs(base_path)
                    except Exception as e:
                        # Fallback to repo root if workspace creation fails
                        base_path = repo_root
        
        self.ui_path = ui_path
        self.base_path = base_path
        self.repo_root = repo_root if ui_path is None else os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.builder = None
        self.window = None
        self.content = None
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
        self.on_quit_callback = None  # Callback when quit button is clicked
        
        # Sub-controllers (following OOP: composition pattern)
        self.file_explorer = None  # FileExplorerPanel controller
        self.project_controller = None  # ProjectActionsController
    
    def load(self):
        """Load the panel UI and return the window.
        
        Returns:
            Gtk.Window: The left panel window.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If window or content not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Left panel UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('left_panel_window')
        self.content = self.builder.get_object('left_panel_content')
        
        if self.window is None:
            raise ValueError("Object 'left_panel_window' not found in left_panel.ui")
        if self.content is None:
            raise ValueError("Object 'left_panel_content' not found in left_panel.ui")
        
        # Get float button and connect callback
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
        else:
            self.float_button = None
        
        # Initialize the file explorer controller
        # This connects the FileExplorer API to the UI widgets defined in XML
        # Set root_boundary to workspace/ so users can only access examples/, projects/, cache/
        # This prevents accidental corruption of application code (src/, tests/, ui/)
        try:
            workspace_boundary = os.path.join(self.repo_root, 'workspace')
            self.file_explorer = FileExplorerPanel(
                self.builder, 
                base_path=self.base_path,  # Start in workspace/
                root_boundary=workspace_boundary  # Cannot navigate above workspace/
            )
        except Exception as e:
            pass  # Continue anyway - panel will work without file explorer
        
        # Initialize project actions controller (handles all project management)
        # CRITICAL: Don't set parent_window here - it will be set when panel attaches/floats
        # This prevents dialogs from using the (hidden) panel window as parent
        try:
            self.project_controller = ProjectActionsController(self.builder, parent_window=None)
            # Set integration callbacks (minimal - just update file explorer navigation)
            self.project_controller.on_project_created = self._on_project_created
            self.project_controller.on_project_opened = self._on_project_opened
            self.project_controller.on_project_closed = self._on_project_closed
        except Exception as e:
            self.project_controller = None
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        return self.window
    
    # ===============================
    # Project Integration Callbacks (Minimal - just navigation)
    # ===============================
    
    def _on_project_created(self, project):
        """Handle project creation - update file explorer to project location.
        
        Args:
            project: The newly created Project instance
        """
        if self.file_explorer and project:
            # Navigate file explorer to new project directory
            self.file_explorer.navigate_to(project.base_path)
    
    def _on_project_opened(self, project):
        """Handle project open - update file explorer to project location.
        
        Args:
            project: The opened Project instance
        """
        if self.file_explorer and project:
            # Navigate file explorer to opened project directory
            self.file_explorer.navigate_to(project.base_path)
    
    def _on_project_closed(self):
        """Handle project closed event.

        When a project is closed, navigate back to workspace root.
        """
        if self.file_explorer:
            # Navigate to workspace root (safe user directory)
            workspace_root = os.path.join(self.repo_root, 'workspace')
            self.file_explorer.navigate_to(workspace_root)
    
    # ===============================
    # Float/Attach (Dock) Behavior
    # ===============================
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        if is_active:
            # Button is now active -> float the panel
            self.float(self.parent_window)
        else:
            # Button is now inactive -> dock the panel back
            if self.parent_container:
                self.attach_to(self.parent_container, self.parent_window)
    
    def float(self, parent_window=None):
        """Float panel as a separate window (detach if currently attached).
        
        WAYLAND SAFE: Uses idle callbacks for reparenting and window operations.
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        # If window doesn't exist, load the UI
        if self.window is None:
            self.load()
        
        # Store parent window reference
        if parent_window:
            self.parent_window = parent_window
        
        def _do_float():
            """Deferred float operation for Wayland safety."""
            try:
                # If currently attached, unattach first (moves content back to window)
                if self.is_attached:
                    # Remove from container
                    if self.parent_container and self.content.get_parent() == self.parent_container:
                        self.parent_container.remove(self.content)
                    
                    # Return content to window
                    if self.content.get_parent() != self.window:
                        self.window.add(self.content)  # GTK3 uses add()
                    
                    self.is_attached = False
                    
                    # Hide the container after unattaching
                    if self.parent_container:
                        self.parent_container.set_visible(False)
                
                # WAYLAND FIX: Set floating window as transient for main window
                # Use stored parent if not provided
                parent = parent_window if parent_window else self.parent_window
                if parent:
                    self.window.set_transient_for(parent)
                
                # CRITICAL: Dialogs should use MAIN WINDOW as parent, not floating panel window
                # This ensures dialogs attach to the main window (which is always visible)
                # rather than the floating panel window
                if parent and self.project_controller:
                    self.project_controller.set_parent_window(parent)
                if parent and self.file_explorer and hasattr(self.file_explorer, 'persistency') and self.file_explorer.persistency:
                    self.file_explorer.persistency.parent_window = parent
                
                # Update float button state
                if self.float_button and not self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(True)
                    self._updating_button = False
                
                # Notify that panel is floating (to collapse paned)
                if self.on_float_callback:
                    self.on_float_callback()
                
                # GTK3: use show_all() instead of present()
                # WAYLAND FIX: Ensure content is visible before showing window
                self.content.set_visible(True)
                self.window.show_all()
            except Exception as e:
                print(f"Warning: Error during panel float: {e}", file=sys.stderr)
            
            return False  # Don't repeat
        
        # WAYLAND FIX: Use idle callback to defer float operation
        GLib.idle_add(_do_float)
    
    def detach(self, parent_window=None):
        """Detach panel to show as a floating window.
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        # Detach is now an alias for float
        self.float(parent_window)
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (embed content in extreme left, hide window).
        
        WAYLAND SAFE: Uses idle callbacks to ensure widgets are properly realized
        before reparenting operations.
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        print(f"[ATTACH] LeftPanel attach_to() called, is_attached={self.is_attached}", file=sys.stderr)
        
        if self.window is None:
            self.load()
        
        # WAYLAND FIX: Prevent rapid attach/detach race conditions
        if self.is_attached and self.parent_container == container:
            # Already attached to this container, just ensure visibility
            print(f"[ATTACH] LeftPanel already attached, ensuring visibility", file=sys.stderr)
            # Check if content was removed by hide() - if so, re-add it
            if self.content.get_parent() != container:
                print(f"[ATTACH] LeftPanel content was removed, re-adding to container", file=sys.stderr)
                container.add(self.content)
            container.set_visible(True)
            self.content.set_visible(True)
            self.content.show_all()  # Ensure all children are visible
            return
        
        print(f"[ATTACH] LeftPanel scheduling deferred attach", file=sys.stderr)
        
        # Store parent window and container for float button callback
        if parent_window:
            self.parent_window = parent_window
            # CRITICAL: Update project controller's parent window so dialogs attach to main window
            if self.project_controller:
                self.project_controller.set_parent_window(parent_window)
            # WAYLAND FIX: Also update file explorer persistency parent window
            if self.file_explorer and hasattr(self.file_explorer, 'persistency') and self.file_explorer.persistency:
                self.file_explorer.persistency.parent_window = parent_window
        self.parent_container = container
        
        def _do_attach():
            """Deferred attach operation for Wayland safety."""
            print(f"[ATTACH] LeftPanel _do_attach() executing", file=sys.stderr)
            try:
                # Extract content from window first
                current_parent = self.content.get_parent()
                if current_parent == self.window:
                    self.window.remove(self.content)  # GTK3 uses remove()
                elif current_parent and current_parent != container:
                    # Content is in another container, remove it first
                    current_parent.remove(self.content)
                
                # WAYLAND FIX: Hide window BEFORE reparenting to avoid surface issues
                if self.window:
                    self.window.hide()
                
                # Only append if not already in container
                if self.content.get_parent() != container:
                    container.add(self.content)  # GTK3 uses add() instead of append()
                
                # Make container visible when panel is attached
                container.set_visible(True)
                
                # Make sure content is visible
                self.content.set_visible(True)
                
                print(f"[ATTACH] LeftPanel attached successfully, content visible", file=sys.stderr)
                
                # Update float button state
                if self.float_button and self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(False)
                    self._updating_button = False
                
                self.is_attached = True
                
                # Notify that panel is attached (to expand paned)
                if self.on_attach_callback:
                    self.on_attach_callback()
            except Exception as e:
                print(f"Warning: Error during panel attach: {e}", file=sys.stderr)
            
            return False  # Don't repeat
        
        # WAYLAND FIX: Use idle callback to defer reparenting
        GLib.idle_add(_do_attach)
        
    
    def unattach(self):
        """Unattach panel from container (return content to window)."""
        if not self.is_attached:
            return
        
        # Remove from container
        if self.parent_container and self.content.get_parent() == self.parent_container:
            self.parent_container.remove(self.content)
        
        # Return content to window
        self.window.add(self.content)  # GTK3 uses add() instead of set_child()
        
        self.is_attached = False
        # Don't clear parent_container - we need it to dock back
    
    def hide(self):
        """Hide panel (works for both attached and detached states).
        
        WAYLAND SAFE: Uses idle callbacks to avoid surface issues.
        """
        print(f"[HIDE] LeftPanel hide() called, is_attached={self.is_attached}", file=sys.stderr)
        
        def _do_hide():
            """Deferred hide operation for Wayland safety."""
            print(f"[HIDE] LeftPanel _do_hide() executing", file=sys.stderr)
            try:
                if self.is_attached:
                    # When attached, remove content from container and hide it
                    if self.content and self.parent_container:
                        current_parent = self.content.get_parent()
                        if current_parent == self.parent_container:
                            print(f"[HIDE] LeftPanel removing content from container", file=sys.stderr)
                            self.parent_container.remove(self.content)
                        self.content.set_visible(False)
                    # Don't hide the container - other panels might use it
                    print(f"[HIDE] LeftPanel hidden (attached mode)", file=sys.stderr)
                elif self.window:
                    # When floating, hide the window
                    self.window.hide()
                    print(f"[HIDE] LeftPanel hidden (floating mode)", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Error during panel hide: {e}", file=sys.stderr)
            return False  # Don't repeat
        
        # WAYLAND FIX: Use idle callback to defer hide operation
        GLib.idle_add(_do_hide)


def create_left_panel(ui_path=None, base_path=None):
    """Convenience function to create and load the left panel loader.
    
    Args:
        ui_path: Optional path to left_panel.ui.
        base_path: Optional base path for file explorer (default: models directory).
        
    Returns:
        LeftPanelLoader: The loaded left panel loader instance.
        
    Example:
        loader = create_left_panel(base_path="/home/user/projects/models")
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to extreme left
    """
    loader = LeftPanelLoader(ui_path, base_path)
    loader.load()
    return loader
