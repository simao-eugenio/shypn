#!/usr/bin/env python3
"""Pathway Panel Loader - Simplified for CategoryFrame Architecture.

This module provides a simple loader for the Pathway Operations panel.
The panel now uses the CategoryFrame architecture (KEGG, SBML, BRENDA categories).

The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container
"""
import os
import sys
import logging

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in pathway_panel loader:', e, file=sys.stderr)
    sys.exit(1)

from shypn.ui.panels.pathway_operations_panel import PathwayOperationsPanel


class PathwayPanelLoader:
    """Simplified loader for the Pathway Operations panel.
    
    Uses CategoryFrame architecture - all logic is in PathwayOperationsPanel
    and its category subclasses (KEGG, SBML, BRENDA).
    """
    
    def __init__(self, ui_path=None, model_canvas=None, workspace_settings=None):
        """Initialize the pathway panel loader.
        
        Args:
            ui_path: Deprecated - CategoryFrame doesn't use .ui files
            model_canvas: Optional ModelCanvasManager for loading imported pathways
            workspace_settings: Optional WorkspaceSettings for remembering user preferences
        """
        self.model_canvas = model_canvas
        self.workspace_settings = workspace_settings
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # State management
        self.window = None
        self.content = None
        self.panel = None
        self.is_hanged = False
        self.parent_container = None
        self.parent_window = None
        self._updating_button = False
        self.on_float_callback = None
        self.on_attach_callback = None
        self.project = None
        
        # Legacy compatibility
        self.kegg_import_controller = None
        self.sbml_import_controller = None
        self.brenda_enrichment_controller = None
    
    def load(self):
        """Load the panel and create the window.
        
        Returns:
            Gtk.Window: The pathway panel window containing the panel.
        """
        # Create the panel (CategoryFrame architecture)
        self.panel = PathwayOperationsPanel(
            workspace_settings=self.workspace_settings,
            parent_window=self.parent_window,
            project=self.project,
            model_canvas=self.model_canvas
        )
        
        # Create a window to contain the panel
        self.window = Gtk.Window()
        self.window.set_title("Pathway Operations")
        self.window.set_default_size(400, 600)
        
        # Create content box (just contains the panel, header is now inside panel)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.pack_start(self.panel, True, True, 0)
        
        # Wire float button (now part of the panel)
        if hasattr(self.panel, 'float_button') and self.panel.float_button:
            self.panel.float_button.connect('toggled', self._on_float_toggled)
        
        # Add content to window
        self.window.add(self.content)
        
        # Connect delete-event to handle window close
        self.window.connect('delete-event', self._on_delete_event)
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        # Set up legacy compatibility references
        self._setup_legacy_compatibility()
        
        self.logger.info("Pathway Operations panel loaded with CategoryFrame architecture")
        
        return self.window
    
    def _setup_legacy_compatibility(self):
        """Set up legacy compatibility references for old code."""
        # Expose category controllers as legacy attributes
        if self.panel:
            self.kegg_import_controller = self.panel.kegg_category
            self.sbml_import_controller = self.panel.sbml_category
            self.brenda_enrichment_controller = self.panel.brenda_category

    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
        
        if self.panel:
            self.panel.set_model_canvas(model_canvas)
        
        self.logger.info("Model canvas updated")
    
    def set_project(self, project):
        """Set or update the current project.
        
        Args:
            project: Project instance
        """
        self.project = project
        
        if self.panel:
            self.panel.set_project(project)
        
        self.logger.info(f"Project set: {project.name if project else None}")
    
    def set_file_panel_loader(self, file_panel_loader):
        """Set file panel loader for file tree refresh.
        
        Args:
            file_panel_loader: FilePanelLoader instance
        """
        if self.panel:
            self.panel.set_file_panel_loader(file_panel_loader)
        
        self.logger.info("File panel loader set")
    
    def get_sbml_controller(self):
        """Get the SBML category instance.
        
        Returns:
            SBMLCategory instance or None
        """
        return self.sbml_import_controller
    
    def _on_float_toggled(self, button):
        """Handle float toggle button click."""
        if self._updating_button:
            return
        
        is_active = button.get_active()
        if is_active:
            self.detach()
        else:
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def _on_delete_event(self, window, event):
        """Handle window close button - hide instead of destroy."""
        self.hide()
        
        if self.panel and hasattr(self.panel, 'float_button') and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False
        
        if self.parent_container:
            self.attach_to(self.parent_container, self.parent_window)
        
        return True
    
    def detach(self):
        """Detach from container and show as floating window."""
        if not self.is_hanged:
            return
        
        if self.parent_container:
            self.parent_container.remove(self.content)
            self.parent_container.set_visible(False)
        
        self.window.add(self.content)
        
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        self.is_hanged = False
        
        if self.panel and hasattr(self.panel, 'float_button') and not self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(True)
            self._updating_button = False
        
        if self.on_float_callback:
            self.on_float_callback()
        
        self.window.show()
    
    def float(self, parent_window=None):
        """Float panel as a separate window."""
        if parent_window:
            self.parent_window = parent_window
            if self.panel:
                self.panel.parent_window = parent_window
        self.detach()
    
    def hang_on(self, container):
        """Attach panel to a container."""
        if self.is_hanged:
            if not self.content.get_visible():
                self.content.show()
            if not container.get_visible():
                container.set_visible(True)
            return
        
        self.window.hide()
        self.window.remove(self.content)
        
        container.pack_start(self.content, True, True, 0)
        self.content.show()
        container.set_visible(True)
        
        self.is_hanged = True
        self.parent_container = container
        
        if self.panel and hasattr(self.panel, 'float_button') and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False
        
        if self.on_attach_callback:
            self.on_attach_callback()
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container."""
        if parent_window:
            self.parent_window = parent_window
            if self.panel:
                self.panel.parent_window = parent_window
        
        self.hang_on(container)
    
    def unattach(self):
        """Unattach panel from container."""
        self.detach()
    
    def hide(self):
        """Hide the panel."""
        if self.is_hanged and self.parent_container:
            self.content.set_no_show_all(True)
            self.content.hide()
        else:
            self.window.hide()
    
    def show(self):
        """Show the panel."""
        if self.is_hanged and self.parent_container:
            self.content.set_no_show_all(False)
            self.content.show()
        else:
            self.window.show()
    
    def add_to_stack(self, stack, container, panel_name='pathways'):
        """Add panel to a GtkStack container."""
        if self.panel is None:
            self.panel = PathwayOperationsPanel(
                workspace_settings=self.workspace_settings,
                parent_window=self.parent_window,
                project=self.project,
                model_canvas=self.model_canvas
            )
            self._setup_legacy_compatibility()
        
        if self.panel.get_parent() != container:
            current_parent = self.panel.get_parent()
            if current_parent:
                current_parent.remove(self.panel)
            container.add(self.panel)
        
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
    
    def show_in_stack(self):
        """Show this panel in the GtkStack."""
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        if self.panel:
            self.panel.set_no_show_all(False)
            self.panel.show()
        
        if self.parent_container:
            self.parent_container.set_visible(True)
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack."""
        if self.panel:
            self.panel.set_no_show_all(True)
            self.panel.hide()
        
        if self.parent_container:
            self.parent_container.set_visible(False)
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up Pathway Panel loader")
        
        if self.panel:
            self.panel.cleanup()


def create_pathway_panel(ui_path=None, model_canvas=None, workspace_settings=None):
    """Convenience function to create and load the pathway panel.
    
    Args:
        ui_path: Deprecated - not used in CategoryFrame architecture
        model_canvas: Optional ModelCanvasManager
        workspace_settings: Optional WorkspaceSettings
        
    Returns:
        PathwayPanelLoader: The loaded pathway panel loader instance.
    """
    loader = PathwayPanelLoader(ui_path, model_canvas, workspace_settings)
    loader.load()
    return loader
