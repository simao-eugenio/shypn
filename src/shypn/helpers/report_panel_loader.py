#!/usr/bin/env python3
"""Report Panel Loader - Manages float/detach functionality.

This loader wraps the Report panel to provide float/detach capabilities,
matching the pattern used in other panels (Topology, Dynamic Analyses, etc.).
"""
import sys
import logging

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print('ERROR: GTK3 not available in report_panel loader:', e, file=sys.stderr)
    sys.exit(1)

from shypn.ui.panels.report import ReportPanel


class ReportPanelLoader:
    """Loader for Report panel with float/detach support."""
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize the report panel loader.
        
        Args:
            project: Optional Project instance
            model_canvas: Optional ModelCanvasManager
        """
        self.project = project
        self.model_canvas = model_canvas
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # State management
        self.window = Gtk.Window()
        self.panel = None
        self.is_hanged = True
        self.parent_container = None
        self.parent_window = None
        self._updating_button = False
        self.on_float_callback = None
        self.on_attach_callback = None
        
        # Stack management
        self._stack = None
        self._stack_panel_name = 'report'
    
    def load(self):
        """Load the panel.
        
        Returns:
            Gtk.Window: The report panel window (used for floating).
        """
        # Create the panel
        self.panel = ReportPanel(
            project=self.project,
            model_canvas=self.model_canvas
        )
        
        # Set up window for floating
        self.window.set_title("Report")
        self.window.set_default_size(500, 700)
        
        # Wire float button
        if hasattr(self.panel, 'float_button') and self.panel.float_button:
            self.panel.float_button.connect('toggled', self._on_float_toggled)
        
        # Connect delete-event to handle window close
        self.window.connect('delete-event', self._on_delete_event)
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        self.logger.info("Report panel loaded")
        
        return self.window
    
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
        self.window.hide()
        
        if self.panel.float_button and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False
        
        if self.parent_container:
            self.hang_on(self.parent_container)
        
        return True
    
    def detach(self):
        """Detach from container and show as floating window."""
        if not self.is_hanged:
            return
        
        if self.parent_container:
            self.parent_container.remove(self.panel)
            self.parent_container.set_visible(False)
        
        self.window.add(self.panel)
        
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        self.is_hanged = False
        
        if self.panel.float_button and not self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(True)
            self._updating_button = False
        
        if self.on_float_callback:
            self.on_float_callback()
        
        self.window.show()
        self.logger.info("Report panel detached")
    
    def hang_on(self, container):
        """Attach panel to a container."""
        if self.is_hanged:
            if not self.panel.get_visible():
                self.panel.show()
            if not container.get_visible():
                container.set_visible(True)
            return
        
        self.window.hide()
        self.window.remove(self.panel)
        
        container.pack_start(self.panel, True, True, 0)
        self.panel.show()
        container.set_visible(True)
        
        self.is_hanged = True
        self.parent_container = container
        
        if self.panel.float_button and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False
        
        if self.on_attach_callback:
            self.on_attach_callback()
        
        self.logger.info("Report panel attached")
    
    def add_to_stack(self, stack, container, panel_name='report'):
        """Add panel to a GtkStack container (Master Palette architecture).
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: Container box for the panel content
            panel_name: Name for the stack child (default: 'report')
        """
        if self.panel is None:
            self.load()
        
        # Remove from current parent if any
        current_parent = self.panel.get_parent()
        if current_parent:
            current_parent.remove(self.panel)
        
        # Add to container
        container.add(self.panel)
        
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        self.logger.info(f"Report panel added to stack as '{panel_name}'")
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Master Palette control)."""
        if not self._stack:
            return
        
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        if self.panel:
            self.panel.set_no_show_all(False)
            self.panel.show()
        
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        self.logger.info("Report panel shown in stack")
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Master Palette control)."""
        if self.panel:
            self.panel.set_no_show_all(True)
            self.panel.hide()
        
        if self.parent_container:
            self.parent_container.set_visible(False)
        
        self.logger.info("Report panel hidden in stack")
    
    def set_project(self, project):
        """Set or update the current project.
        
        Args:
            project: Project instance
        """
        self.project = project
        
        if self.panel and hasattr(self.panel, 'set_project'):
            self.panel.set_project(project)
        
        self.logger.info(f"Project set: {project.name if project else None}")
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
        
        if self.panel and hasattr(self.panel, 'set_model_canvas'):
            self.panel.set_model_canvas(model_canvas)
        
        self.logger.info("Model canvas updated")
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up Report Panel loader")
        
        if self.panel and hasattr(self.panel, 'cleanup'):
            self.panel.cleanup()


def create_report_panel(project=None, model_canvas=None):
    """Convenience function to create and load the report panel.
    
    Args:
        project: Optional Project instance
        model_canvas: Optional ModelCanvasManager
        
    Returns:
        ReportPanelLoader: The loaded report panel loader instance.
    """
    loader = ReportPanelLoader(project, model_canvas)
    loader.load()
    return loader
