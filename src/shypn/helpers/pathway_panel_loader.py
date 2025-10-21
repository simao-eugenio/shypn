#!/usr/bin/env python3
"""Pathway Panel Loader/Controller.

This module is responsible for loading and managing the Pathway Operations panel.
The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container

The panel contains a notebook with multiple tabs:
  - Import: KEGG pathway import interface
  - Browse: Browse available pathways (future)
  - History: Recently imported pathways (future)
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in pathway_panel loader:', e, file=sys.stderr)
    sys.exit(1)


class PathwayPanelLoader:
    """Loader and controller for the Pathway Operations panel (attachable window)."""
    
    def __init__(self, ui_path=None, model_canvas=None, workspace_settings=None):
        """Initialize the pathway panel loader.
        
        Args:
            ui_path: Optional path to pathway_panel.ui. If None, uses default location.
            model_canvas: Optional ModelCanvasManager for loading imported pathways
            workspace_settings: Optional WorkspaceSettings for remembering user preferences
        """
        if ui_path is None:
            # Default: ui/panels/pathway_panel.ui
            # This loader file is in: src/shypn/helpers/pathway_panel_loader.py
            # UI file is in: ui/panels/pathway_panel.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'panels', 'pathway_panel.ui')
        
        self.ui_path = ui_path
        self.model_canvas = model_canvas
        self.workspace_settings = workspace_settings
        self.builder = None
        self.window = None
        self.content = None
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self._attach_in_progress = False  # WAYLAND FIX: Prevent concurrent attach operations
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
        
        # Import tab controllers (will be instantiated after loading UI)
        self.kegg_import_controller = None
        self.sbml_import_controller = None
    
    def load(self):
        """Load the panel UI and return the window.
        
        Returns:
            Gtk.Window: The pathway panel window.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If window or content not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Pathway panel UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('pathway_panel_window')
        self.content = self.builder.get_object('pathway_panel_content')
        
        if self.window is None:
            raise ValueError("Object 'pathway_panel_window' not found in pathway_panel.ui")
        if self.content is None:
            raise ValueError("Object 'pathway_panel_content' not found in pathway_panel.ui")
        
        # Get float button and connect callback
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
        else:
            self.float_button = None
        
        # Connect delete-event to prevent window destruction
        # When X button is clicked, just hide the window instead of destroying it
        self.window.connect('delete-event', self._on_delete_event)
        
        # Initialize tab controllers
        self._setup_import_tab()
        self._setup_sbml_tab()
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        return self.window
    
    def _setup_import_tab(self):
        """Set up the Import tab controllers.
        
        This method instantiates the KEGG import controller and wires it to the UI.
        """
        # Import the KEGG import controller (from helpers, not ui)
        try:
            from shypn.helpers.kegg_import_panel import KEGGImportPanel
            
            # Instantiate controller with builder and model_canvas
            self.kegg_import_controller = KEGGImportPanel(
                self.builder,
                self.model_canvas
            )
            
        except ImportError as e:
            print(f"Warning: Could not load KEGG import controller: {e}", file=sys.stderr)
            pass
    
    def _setup_sbml_tab(self):
        """Set up the SBML tab controllers.
        
        This method instantiates the SBML import controller and wires it to the UI.
        """
        # Import the SBML import controller (from helpers)
        try:
            from shypn.helpers.sbml_import_panel import SBMLImportPanel
            
            # Instantiate controller with builder and model_canvas
            # WAYLAND FIX: Pass None for parent_window initially, will be set when panel attaches
            self.sbml_import_controller = SBMLImportPanel(
                self.builder,
                self.model_canvas,
                self.workspace_settings,
                parent_window=None
            )
            
        except ImportError as e:
            print(f"Warning: Could not load SBML import controller: {e}", file=sys.stderr)
            pass
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas for loading imported pathways.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
        
        # Update import controllers if they exist
        if self.kegg_import_controller:
            self.kegg_import_controller.set_model_canvas(model_canvas)
        
        if self.sbml_import_controller:
            self.sbml_import_controller.set_model_canvas(model_canvas)
        
        # Wire SBML panel to model canvas so Swiss Palette can read layout parameters
        if model_canvas and self.sbml_import_controller:
            model_canvas.sbml_panel = self.sbml_import_controller
    
    def get_sbml_controller(self):
        """Get the SBML import controller instance.
        
        Returns:
            SBMLImportPanel instance or None
        """
        return self.sbml_import_controller
    
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
    
    def _on_delete_event(self, window, event):
        """Handle window close button (X) - hide instead of destroy.
        
        When user clicks X on floating window, we don't want to destroy
        the window (which causes segfault), just hide it and dock it back.
        
        Args:
            window: The window being closed
            event: The delete event
            
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
            self.attach_to(self.parent_container, self.parent_window)
        
        # Return True to prevent window destruction
        return True
    
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
            # WAYLAND FIX: Update SBML controller's parent window for FileChooser dialogs
            if self.sbml_import_controller:
                self.sbml_import_controller.set_parent_window(parent_window)
            # WAYLAND FIX: Update KEGG controller's parent window if needed
            if self.kegg_import_controller and hasattr(self.kegg_import_controller, 'set_parent_window'):
                self.kegg_import_controller.set_parent_window(parent_window)
        
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
                        self.window.add(self.content)
                    
                    self.is_attached = False
                    
                    # Hide the container after unattaching
                    if self.parent_container:
                        self.parent_container.set_visible(False)
                
                # WAYLAND FIX: Always set parent, use stored parent if not provided
                parent = parent_window if parent_window else self.parent_window
                if parent:
                    self.window.set_transient_for(parent)
                else:
                    # No parent available - try to set to None explicitly
                    self.window.set_transient_for(None)
                
                # Update float button state
                if self.float_button and not self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(True)
                    self._updating_button = False
                
                # Notify that panel is floating (to collapse paned)
                if self.on_float_callback:
                    self.on_float_callback()
                
                # WAYLAND FIX: Ensure content is visible before showing window
                self.content.set_visible(True)
                # GTK3: use show_all() instead of present()
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
        """Attach panel to container (embed content, hide window).
        
        WAYLAND SAFE: Uses idle callbacks to ensure widgets are properly realized
        before reparenting operations.
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        print(f"[ATTACH] PathwayPanel attach_to() called, is_attached={self.is_attached}", file=sys.stderr)
        
        if self.window is None:
            self.load()
        
        # WAYLAND FIX: Prevent rapid attach/detach race conditions
        if self.is_attached and self.parent_container == container:
            # Already attached to this container, just ensure visibility
            print(f"[ATTACH] PathwayPanel already attached, ensuring visibility", file=sys.stderr)
            # Check if content was removed by hide() - if so, re-add it
            if self.content.get_parent() != container:
                print(f"[ATTACH] PathwayPanel content was removed, re-adding to container", file=sys.stderr)
                container.add(self.content)
            # WAYLAND FIX: Don't call set_visible repeatedly - can cause protocol errors
            if not container.get_visible():
                container.set_visible(True)
            # Content should already be visible if we're in fast path
            return
        
        # WAYLAND FIX: Prevent concurrent attach operations
        if self._attach_in_progress:
            print(f"[ATTACH] PathwayPanel attach already in progress, ignoring", file=sys.stderr)
            return
        
        print(f"[ATTACH] PathwayPanel scheduling deferred attach", file=sys.stderr)
        
        # Set flag BEFORE scheduling idle to prevent concurrent attach attempts
        self._attach_in_progress = True
        
        # WAYLAND FIX: Set is_attached=True NOW to prevent duplicate attach_to() calls
        # The idle callback will complete the actual reparenting operation
        self.is_attached = True
        
        # Store parent window and container for float button callback
        if parent_window:
            self.parent_window = parent_window
            # WAYLAND FIX: Update SBML controller's parent window for FileChooser dialogs
            if self.sbml_import_controller:
                self.sbml_import_controller.set_parent_window(parent_window)
            # WAYLAND FIX: Update KEGG controller's parent window if needed
            if self.kegg_import_controller and hasattr(self.kegg_import_controller, 'set_parent_window'):
                self.kegg_import_controller.set_parent_window(parent_window)
        self.parent_container = container
        
        print(f"[ATTACH] PathwayPanel scheduling deferred attach", file=sys.stderr)
        
        def _do_attach():
            """Deferred attach operation for Wayland safety."""
            print(f"[ATTACH] PathwayPanel _do_attach() executing", file=sys.stderr)
            try:
                # Extract content from window first
                current_parent = self.content.get_parent()
                if current_parent == self.window:
                    self.window.remove(self.content)  # GTK3 uses remove()
                elif current_parent and current_parent != container:
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
                
                print(f"[ATTACH] PathwayPanel attached successfully, content visible", file=sys.stderr)
                
                # Update float button state
                if self.float_button and self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(False)
                    self._updating_button = False
                
                # NOTE: is_attached was already set to True before scheduling idle
                
                # WAYLAND FIX: Clear attach operation flag
                self._attach_in_progress = False
                
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
        print(f"[HIDE] PathwayPanel hide() called, is_attached={self.is_attached}", file=sys.stderr)
        
        def _do_hide():
            """Deferred hide operation for Wayland safety."""
            print(f"[HIDE] PathwayPanel _do_hide() executing", file=sys.stderr)
            try:
                if self.is_attached:
                    # WAYLAND FIX: Just remove content from container, DON'T call set_visible(False)
                    # Setting visibility can cause unrealize/realize cycles on embedded widgets (SBML panel!)
                    if self.content and self.parent_container:
                        current_parent = self.content.get_parent()
                        if current_parent == self.parent_container:
                            print(f"[HIDE] PathwayPanel removing content from container", file=sys.stderr)
                            self.parent_container.remove(self.content)
                        # CRITICAL: Don't call self.content.set_visible(False) - causes Wayland issues
                        # Content stays realized and ready for fast re-attach
                        # Don't hide container - other panels might use it
                    # NOTE: Keep is_attached=True so next attach_to() can use fast path
                    print(f"[HIDE] PathwayPanel hidden (attached mode)", file=sys.stderr)
                elif self.window:
                    # When floating, hide the window
                    self.window.hide()
                    print(f"[HIDE] PathwayPanel hidden (floating mode)", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Error during panel hide: {e}", file=sys.stderr)
            return False  # Don't repeat
        
        # WAYLAND FIX: Use idle callback to defer hide operation
        GLib.idle_add(_do_hide)


def create_pathway_panel(ui_path=None, model_canvas=None, workspace_settings=None):
    """Convenience function to create and load the pathway panel loader.
    
    Args:
        ui_path: Optional path to pathway_panel.ui.
        model_canvas: Optional ModelCanvasManager for loading imported pathways.
        workspace_settings: Optional WorkspaceSettings for remembering user preferences.
        
    Returns:
        PathwayPanelLoader: The loaded pathway panel loader instance.
        
    Example:
        loader = create_pathway_panel(model_canvas=canvas_manager, workspace_settings=settings)
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to container
    """
    loader = PathwayPanelLoader(ui_path, model_canvas, workspace_settings)
    loader.load()
    return loader
