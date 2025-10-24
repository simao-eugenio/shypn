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
        self.is_hanged = False  # Simple state flag (skeleton pattern)
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
        
                # Connect delete-event to prevent window destruction
        self.window.connect('delete-event', self._on_delete_event)
        
        # WAYLAND FIX: Don't realize window early - let GTK do it naturally
        # Realizing too early can cause protocol errors on Wayland
        # self.window.realize()
        # if self.window.get_window():
        #     try:
        #         from gi.repository import Gdk
        #         self.window.get_window().set_events(
        #             self.window.get_window().get_events() | 
        #             Gdk.EventMask.STRUCTURE_MASK |
        #             Gdk.EventMask.PROPERTY_CHANGE_MASK
        #         )
        #     except Exception as e:
        #         print(f"[LEFT_PANEL] Could not set window event mask: {e}", file=sys.stderr)
        
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
        
        print(f"[LEFT_PANEL] Float button toggled: active={button.get_active()}, is_hanged={self.is_hanged}")
            
        is_active = button.get_active()
        if is_active:
            # Button is now active -> detach the panel (float)
            print(f"[LEFT_PANEL] Calling detach()")
            self.detach()
        else:
            # Button is now inactive -> attach the panel back
            print(f"[LEFT_PANEL] Calling hang_on()")
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def _on_delete_event(self, window, event):
        """Handle window close button (X) - hide instead of destroy.
        
        Returns:
            bool: True to prevent default destroy behavior
        """
        # Hide the window
        self.hide()
        
        # Update float button to inactive state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Dock back if we have a container
        if self.parent_container:
            self.hang_on(self.parent_container)
        
        # Return True to prevent window destruction
        return True
    
    def detach(self):
        """Detach from container and restore as independent window (skeleton pattern)."""
        
        print(f"[LEFT_PANEL] detach() called: is_hanged={self.is_hanged}, window exists={self.window is not None}")
        
        if not self.is_hanged:
            print(f"[LEFT_PANEL] Already detached, returning")
            return
        
        # Create window if it doesn't exist (happens when panel was loaded via add_to_stack)
        if self.window is None:
            print(f"[LEFT_PANEL] Creating window on-demand")
            self.window = Gtk.Window()
            self.window.set_title('Files')
            self.window.set_default_size(300, 600)
            # Connect delete-event to prevent destruction
            self.window.connect('delete-event', self._on_delete_event)
        
        # Remove from container
        if self.parent_container:
            print(f"[LEFT_PANEL] Removing content from container")
            self.parent_container.remove(self.content)
            # Hide the container after unattaching
            self.parent_container.set_visible(False)
        
        # Return content to independent window
        print(f"[LEFT_PANEL] Adding content to window")
        self.window.add(self.content)
        
        # Set transient for main window if available
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state
        if self.float_button and not self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating
        if self.on_float_callback:
            self.on_float_callback()
        
        # Show window
        print(f"[LEFT_PANEL] Showing window")
        self.window.show_all()
        print(f"[LEFT_PANEL] Detach complete")
        
    
    def float(self, parent_window=None):
        """Float panel as a separate window (alias for detach for backward compatibility).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        if parent_window:
            self.parent_window = parent_window
        self.detach()
    
    def hang_on(self, container):
        """Hang this panel on a container (attach - skeleton pattern).
        
        Args:
            container: Gtk.Box or other container to embed content into.
        """
        
        if self.is_hanged:
            if not self.content.get_visible():
                self.content.show_all()
            # Make sure container is visible when re-showing
            if not container.get_visible():
                container.set_visible(True)
            return
        
        # Hide independent window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Hang content on container
        container.pack_start(self.content, True, True, 0)
        self.content.show_all()
        
        # Make container visible (it was hidden when detached)
        container.set_visible(True)
        
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Notify that panel is attached
        if self.on_attach_callback:
            self.on_attach_callback()
        
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (alias for hang_on for backward compatibility).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        if parent_window:
            self.parent_window = parent_window
            # Update parent window references for dialogs
            if self.project_controller:
                self.project_controller.set_parent_window(parent_window)
            if self.file_explorer and hasattr(self.file_explorer, 'persistency') and self.file_explorer.persistency:
                self.file_explorer.persistency.parent_window = parent_window
            if self.file_explorer:
                self.file_explorer.set_parent_window(parent_window)
        
        self.hang_on(container)
        
    
    def unattach(self):
        """Unattach panel from container (alias for detach for backward compatibility)."""
        self.detach()
    
    def hide(self):
        """Hide the panel (keep hanged but invisible - skeleton pattern)."""
        
        if self.is_hanged and self.parent_container:
            # Hide content while keeping it hanged
            self.content.set_no_show_all(True)  # Prevent show_all from revealing it
            self.content.hide()
        else:
            # Hide floating window
            self.window.hide()
    
    def show(self):
        """Show the panel (reveal if hanged, show window if floating - skeleton pattern)."""
        
        if self.is_hanged and self.parent_container:
            # Re-enable show_all and show content (reveal)
            self.content.set_no_show_all(False)
            self.content.show_all()
        else:
            # Show floating window
            self.window.show_all()
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='files'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        WAYLAND FIX: Don't create window in stack mode - load content directly.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('files')
        """
        
        # WAYLAND FIX: Load content directly without creating window
        if self.builder is None:
            # Validate UI file exists
            if not os.path.exists(self.ui_path):
                raise FileNotFoundError(f"Left panel UI file not found: {self.ui_path}")
            
            # Initialize flag for preventing recursive toggles
            if not hasattr(self, '_updating_button'):
                self._updating_button = False
            
            # Load the UI
            self.builder = Gtk.Builder.new_from_file(self.ui_path)
            
            # Extract ONLY the content (not the window)
            self.content = self.builder.get_object('left_panel_content')
            
            if self.content is None:
                raise ValueError("Object 'left_panel_content' not found in left_panel.ui")
            
            # Initialize controllers (skip window-related stuff)
            self._init_controllers()
            
            # Get float button and connect signal
            # NOTE: Float button works but will cause Error 71 if window is maximized
            self.float_button = self.builder.get_object('float_button')
            print(f"[LEFT_PANEL] Float button found: {self.float_button is not None}")
            if self.float_button:
                # Connect signal handler
                handler_id = self.float_button.connect('toggled', self._on_float_toggled)
                print(f"[LEFT_PANEL] Float button signal connected with handler_id={handler_id}")
                # Ensure button starts inactive in stack mode
                if self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(False)
                    self._updating_button = False
                print(f"[LEFT_PANEL] Float button initial state: active={self.float_button.get_active()}")
            else:
                print(f"[LEFT_PANEL] WARNING: Float button not found in UI file!")
        
        # Add content directly to stack container
        if self.content.get_parent() != container:
            current_parent = self.content.get_parent()
            if current_parent:
                current_parent.remove(self.content)
            container.add(self.content)
        
        # Mark as hanged in stack mode
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control).
        
        Called by Master Palette when user activates the Files button.
        Makes the stack visible and sets this panel as the active child.
        """
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # WAYLAND FIX: Use show() instead of show_all()
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show()  # Show just the container (not show_all!)
        
        # Make container visible too
        if self.parent_container:
            self.parent_container.set_visible(True)
        
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control).
        
        Called by Master Palette when user deactivates the Files button.
        Hides the content but keeps it in the stack for fast re-activation.
        """
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)

        
    
    def float_from_stack(self):
        """Float panel from GtkStack to separate window (Phase 5: float support).
        
        Called when user clicks the float button while panel is in stack.
        Extracts content from stack and shows it in a floating window.
        """
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Extract content from container
        if self.parent_container and self.content:
            current_parent = self.content.get_parent()
            if current_parent == self.parent_container:
                self.parent_container.remove(self.content)
        
        # Add content back to window
        if self.window and self.content:
            self.window.add(self.content)
            self.window.show_all()
        
        # Mark as not hanged (now floating)
        self.is_hanged = False
        
    
    def attach_back_to_stack(self):
        """Re-attach panel from floating window back to GtkStack (Phase 5: float support).
        
        Called when user clicks the float button again while panel is floating.
        Returns content from window back to stack container.
        """
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Hide floating window
        if self.window:
            self.window.hide()
        
        # Extract content from window
        if self.window and self.content:
            current_parent = self.content.get_parent()
            if current_parent == self.window:
                self.window.remove(self.content)
        
        # Add content back to stack container
        if self.parent_container and self.content:
            if self.content.get_parent() != self.parent_container:
                self.parent_container.add(self.content)
        
        # Mark as hanged
        self.is_hanged = True
        
        # Show in stack
        self.show_in_stack()
        


def create_left_panel(ui_path=None, base_path=None, load_window=True):
    """Convenience function to create and load the left panel loader.
    
    Args:
        ui_path: Optional path to left_panel.ui.
        base_path: Optional base path for file explorer (default: models directory).
        load_window: If True, creates window immediately. If False, defers to add_to_stack().
        
    Returns:
        LeftPanelLoader: The left panel loader instance.
        
    Example:
        loader = create_left_panel(base_path="/home/user/projects/models")
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to extreme left
    """
    loader = LeftPanelLoader(ui_path, base_path)
    if load_window:
        loader.load()
    return loader

