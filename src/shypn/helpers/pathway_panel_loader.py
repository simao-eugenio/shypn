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
        self.is_hanged = False  # Simple state flag (skeleton pattern)
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
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
        
        # WAYLAND FIX: Realize window and set event mask for multi-monitor support
        self.window.realize()
        if self.window.get_window():
            try:
                from gi.repository import Gdk
                self.window.get_window().set_events(
                    self.window.get_window().get_events() | 
                    Gdk.EventMask.STRUCTURE_MASK |
                    Gdk.EventMask.PROPERTY_CHANGE_MASK
                )
            except Exception as e:
                print(f"[PATHWAY_PANEL] Could not set window event mask: {e}", file=sys.stderr)
        
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
            # Button is now active → detach the panel (float)
            self.detach()
        else:
            # Button is now inactive → attach the panel back
            if self.parent_container:
                self.hang_on(self.parent_container)
    
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
    
    def detach(self):
        """Detach from container and restore as independent window (skeleton pattern)."""
        print(f"[PATHWAY_PANEL] Detaching from container...")
        
        if not self.is_hanged:
            print(f"[PATHWAY_PANEL] Already detached")
            return
        
        # Remove from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            # Hide the container after unattaching
            self.parent_container.set_visible(False)
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Return content to independent window
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
        self.window.show_all()
        
        print(f"[PATHWAY_PANEL] Detached successfully")
    
    def float(self, parent_window=None):
        """Float panel as a separate window (alias for detach for backward compatibility).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        if parent_window:
            self.parent_window = parent_window
            # Update SBML controller's parent window for FileChooser dialogs
            if self.sbml_import_controller:
                self.sbml_import_controller.set_parent_window(parent_window)
            # Update KEGG controller's parent window if needed
            if self.kegg_import_controller and hasattr(self.kegg_import_controller, 'set_parent_window'):
                self.kegg_import_controller.set_parent_window(parent_window)
        self.detach()
    
    def hang_on(self, container):
        """Hang this panel on a container (attach - skeleton pattern).
        
        Args:
            container: Gtk.Box or other container to embed content into.
        """
        print(f"[PATHWAY_PANEL] Hanging on container...")
        
        if self.is_hanged:
            print(f"[PATHWAY_PANEL] Already hanged, just showing")
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
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            if hasattr(self, '_stack_panel_name'):
                self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Notify that panel is attached
        if self.on_attach_callback:
            self.on_attach_callback()
        
        print(f"[PATHWAY_PANEL] Hanged successfully")
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (alias for hang_on for backward compatibility).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        if parent_window:
            self.parent_window = parent_window
            # Update SBML controller's parent window for FileChooser dialogs
            if self.sbml_import_controller:
                self.sbml_import_controller.set_parent_window(parent_window)
            # Update KEGG controller's parent window if needed
            if self.kegg_import_controller and hasattr(self.kegg_import_controller, 'set_parent_window'):
                self.kegg_import_controller.set_parent_window(parent_window)
        
        self.hang_on(container)
    
    def unattach(self):
        """Unattach panel from container (alias for detach for backward compatibility)."""
        self.detach()
    
    def hide(self):
        """Hide the panel (keep hanged but invisible - skeleton pattern)."""
        print(f"[PATHWAY_PANEL] Hiding panel...")
        
        if self.is_hanged and self.parent_container:
            # Hide content while keeping it hanged
            self.content.set_no_show_all(True)  # Prevent show_all from revealing it
            self.content.hide()
            print(f"[PATHWAY_PANEL] Hidden (still hanged)")
        else:
            # Hide floating window
            self.window.hide()
            print(f"[PATHWAY_PANEL] Window hidden")
    
    def show(self):
        """Show the panel (reveal if hanged, show window if floating - skeleton pattern)."""
        print(f"[PATHWAY_PANEL] Showing panel...")
        
        if self.is_hanged and self.parent_container:
            # Re-enable show_all and show content (reveal)
            self.content.set_no_show_all(False)
            self.content.show_all()
            print(f"[PATHWAY_PANEL] Revealed (hanged)")
        else:
            # Show floating window
            self.window.show_all()
            print(f"[PATHWAY_PANEL] Window shown")
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='pathways'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('pathways')
        """
        
        if self.window is None:
            self.load()
        
        # Extract content from window
        current_parent = self.content.get_parent()
        if current_parent == self.window:
            self.window.remove(self.content)
        elif current_parent and current_parent != container:
            current_parent.remove(self.content)
        
        # Add content to stack container
        if self.content.get_parent() != container:
            container.add(self.content)
        
        # Mark as hanged in stack mode
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        # Hide window (not needed in stack mode)
        if self.window:
            self.window.hide()
        
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # WAYLAND FIX: Use show() instead of show_all() to avoid protocol errors
        # The content widgets were already made visible during load() or initialization
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show()  # Show just the container, not all children recursively
        
        # Make container visible too
        if self.parent_container:
            self.parent_container.set_visible(True)
        
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)

        


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
