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
    
    def __init__(self, project=None, model_canvas_loader=None):
        """Initialize the report panel loader.
        
        Args:
            project: Optional Project instance
            model_canvas_loader: Optional ModelCanvasLoader (for accessing get_current_model())
        """
        self.project = project
        self.model_canvas_loader = model_canvas_loader
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
        # Create the panel with the model_canvas_loader reference
        self.panel = ReportPanel(
            project=self.project,
            model_canvas=self.model_canvas_loader  # Pass loader, not manager
        )
        
        # Compatibility: expose panel as content/widget for container operations
        self.content = self.panel
        self.widget = self.panel
        
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
        
        # Make sure panel widgets are ready to be shown (but don't show the window)
        # This ensures the panel content is visible when added to a container
        self.panel.show_all()
        
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
        """Detach from container and show as floating window (Wayland-safe)."""
        if not self.is_hanged:
            return
        
        # Remove from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            # Hide the container after unattaching (matches other panel behavior)
            self.parent_container.set_visible(False)
        
        # Hide the stack if this was the active panel (matches other panel behavior)
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
            # Also set no-show-all to prevent it from reappearing
            self._stack.set_no_show_all(True)
        
        # Add content to window
        self.window.add(self.content)
        
        # Set transient for main window if available (CRITICAL for Wayland)
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state
        if self.panel.float_button and not self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating
        if self.on_float_callback:
            self.on_float_callback()
        
        # Show window (use show_all for Wayland compatibility)
        self.window.show_all()
        self.logger.info("Report panel detached")
    
    def float(self, parent_window=None):
        """Float panel as a separate window (alias for detach for backward compatibility).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        if parent_window:
            self.parent_window = parent_window
        self.detach()
    
    def hang_on(self, container):
        """Attach panel to a container (Wayland-safe)."""
        if self.is_hanged:
            # Already attached, just make sure it's visible
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
        
        # Attach content to container
        container.pack_start(self.content, True, True, 0)
        self.content.show_all()
        
        # Make container visible (matches other panel behavior)
        container.set_visible(True)
        
        # Show the stack if available (Report panel is in a stack)
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_no_show_all(False)
            self._stack.set_visible(True)
            self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Update state
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if self.panel.float_button and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False
        
        # Notify that panel is attached
        if self.on_attach_callback:
            self.on_attach_callback()
        
        self.logger.info("Report panel attached")
    
    def add_to_stack(self, stack, container, panel_name='report'):
        """Add panel to a GtkStack container (Master Palette architecture).
        
        Per-document architecture: Unlike other panels, Report panel instances
        are swapped in/out of the container during tab switching.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: Container box for the panel content (GtkBox, supports multiple children)
            panel_name: Name for the stack child (default: 'report')
        """
        if self.panel is None:
            self.load()
        
        # Remove from current parent if any
        current_parent = self.content.get_parent()
        if current_parent:
            current_parent.remove(self.content)
        
        # Add to container (use pack_start for GtkBox, not add)
        container.pack_start(self.content, True, True, 0)
        
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
        
        if self.content:
            self.content.set_no_show_all(False)
            self.content.show_all()  # Use show_all to show nested widgets
        
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        self.logger.info("Report panel shown in stack")
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Master Palette control)."""
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
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
    
    def set_model_canvas(self, model_manager):
        """Set or update the model canvas manager (the actual model with places/transitions).
        
        This is called when the active model changes (e.g., tab switching).
        
        Args:
            model_manager: ModelCanvasManager instance (has places, transitions, arcs)
        """
        if self.panel and hasattr(self.panel, 'set_model_canvas'):
            self.panel.set_model_canvas(model_manager)
        
        self.logger.info("Model manager updated for Report Panel")
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up Report Panel loader")
        
        if self.panel and hasattr(self.panel, 'cleanup'):
            self.panel.cleanup()


def create_report_panel(project=None, model_canvas_loader=None):
    """Convenience function to create and load the report panel.
    
    Args:
        project: Optional Project instance
        model_canvas_loader: Optional ModelCanvasLoader
        
    Returns:
        ReportPanelLoader: The loaded report panel loader instance.
    """
    loader = ReportPanelLoader(project, model_canvas_loader)
    loader.load()
    return loader
