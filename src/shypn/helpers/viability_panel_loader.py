"""Minimal Viability Panel Loader - Normalized Architecture.

Ultra-minimal loader that instantiates the normalized ViabilityPanel class.
All business logic is in the viability panel package.

This is a compatibility wrapper to work with existing shypn.py infrastructure.

Author: Simão Eugénio
Date: November 9, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.panels.viability import ViabilityPanel


class ViabilityPanelLoader:
    """Minimal loader for normalized Viability Panel.
    
    Responsibilities:
    - Instantiate ViabilityPanel class
    - Provide compatibility with existing shypn.py infrastructure
    - Wire model_canvas_loader reference
    - Handle float/attach mechanism (Wayland-safe)
    
    All panel logic is in the ViabilityPanel class.
    """
    
    def __init__(self, model):
        """Initialize viability panel loader.
        
        Args:
            model: The ShypnModel instance (can be None)
        """
        self.model = model
        self.model_canvas_loader = None  # Set externally
        self.parent_window = None
        self.parent_container = None
        self.is_hanged = True
        self._updating_button = False
        # Optional UI callbacks (wired by host app)
        self.on_float_callback = None
        self.on_attach_callback = None
        
        # Create floating window
        self.window = Gtk.Window()
        self.window.set_title('Viability')
        self.window.set_default_size(350, 700)
        self.window.connect('delete-event', self._on_delete_event)
        
        # Create the viability panel
        self.panel = ViabilityPanel(
            model=self.model,
            model_canvas=None  # Will be set via set_model_canvas_loader
        )
        
        # Wire float button
        if hasattr(self.panel, 'float_button'):
            self.panel.float_button.connect('toggled', self._on_float_toggled)
        
        # Compatibility: old code checks for controller attribute
        # Controller is the loader itself (has on_tab_switched, on_file_opened, etc.)
        self.controller = self
        
        # Expose the panel widget for adding to containers
        self.widget = self.panel
        self.content = self.panel
    
    def set_model_canvas_loader(self, model_canvas_loader):
        """Set model canvas loader reference.
        
        Args:
            model_canvas_loader: ModelCanvasLoader instance
        """
        self.model_canvas_loader = model_canvas_loader
        if self.panel:
            # Use the panel's method to update categories too
            if hasattr(self.panel, 'set_model_canvas'):
                self.panel.set_model_canvas(model_canvas_loader)
            else:
                # Fallback for backward compatibility
                self.panel.model_canvas = model_canvas_loader
        
        # Wire simulation complete callback to all controllers
        self._wire_simulation_callback()
    
    def _wire_simulation_callback(self):
        """Wire simulation complete callback to all existing controllers."""
        if not self.model_canvas_loader:
            return
        
        # Get all overlay managers and wire callbacks
        if hasattr(self.model_canvas_loader, 'overlay_managers'):
            for overlay_manager in self.model_canvas_loader.overlay_managers:
                controller = getattr(overlay_manager, 'controller', None)
                if controller and hasattr(controller, 'on_simulation_complete'):
                    # Add our callback alongside existing ones
                    existing_callback = controller.on_simulation_complete
                    
                    def combined_callback():
                        # Call existing callback first
                        if existing_callback and callable(existing_callback):
                            existing_callback()
                        # Then call viability panel
                        if self.panel and hasattr(self.panel, 'on_simulation_complete'):
                            self.panel.on_simulation_complete()
                    
                    controller.on_simulation_complete = combined_callback
    
    def on_tab_switched(self, drawing_area):
        """Called when user switches model tabs.
        
        Args:
            drawing_area: The newly active drawing area
        """
        # Refresh panel for new model
        if hasattr(self.panel, 'refresh'):
            self.panel.refresh()
    
    def on_file_opened(self, drawing_area):
        """Called when a new file is opened.
        
        Args:
            drawing_area: The drawing area for the new model
        """
        # Refresh panel for new model
        if hasattr(self.panel, 'refresh'):
            self.panel.refresh()
    
    def on_pathway_imported(self, drawing_area):
        """Called when a pathway is imported (KEGG/SBML).
        
        Args:
            drawing_area: The drawing area where pathway was imported
        """
        # Refresh panel for updated model
        if hasattr(self.panel, 'refresh'):
            self.panel.refresh()
    
    def refresh(self):
        """Refresh the panel."""
        if hasattr(self.panel, 'refresh'):
            self.panel.refresh()
    
    def add_to_stack(self, stack, container, panel_name='viability'):
        """Add panel content to a GtkStack container.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('viability')
        """
        # Always remove from current parent before adding to the target container
        current_parent = self.widget.get_parent()
        if current_parent and current_parent is not container:
            try:
                current_parent.remove(self.widget)
            except Exception:
                pass
        if self.widget.get_parent() != container:
            container.pack_start(self.widget, True, True, 0)
        
        # Show all widgets to ensure proper realization (match Topology/Analyses)
        self.widget.show_all()
        
        # Store references for compatibility
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Master Palette control)."""
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Show the container
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        # Show the widget and all children
        if self.widget:
            self.widget.set_no_show_all(False)
            self.widget.show_all()  # Ensure all children are shown
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Master Palette control)."""
        # Just hide container - don't use no_show_all as it breaks other panels
        if self.parent_container:
            self.parent_container.set_visible(False)
    
    def hang_on(self, container):
        """Hang this panel on a container (attach).
        
        Args:
            container: Gtk.Box or other container to embed content into.
        """
        if self.is_hanged:
            # Already attached, just ensure visibility
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
        
        # Make container visible (it was hidden when detached)
        container.set_visible(True)
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Update state
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if hasattr(self.panel, 'float_button') and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False
        
        # Notify host to expand/show docked area if needed
        if callable(self.on_attach_callback):
            self.on_attach_callback()
    
    def detach(self):
        """Detach from container and restore as independent window."""
        if not self.is_hanged:
            return
        
        print(f"[VIABILITY] Detaching - container visible: {self.parent_container.get_visible() if self.parent_container else 'N/A'}")
        print(f"[VIABILITY] Detaching - stack visible: {self._stack.get_visible() if hasattr(self, '_stack') and self._stack else 'N/A'}")
        
        # Remove content from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            # Hide the container after unattaching
            self.parent_container.set_visible(False)
            print(f"[VIABILITY] Container hidden: {not self.parent_container.get_visible()}")
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
            print(f"[VIABILITY] Stack hidden: {not self._stack.get_visible()}")
        
        # Add content to independent window
        self.window.add(self.content)
        
        # Set transient for main window if available
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Notify host to collapse/hide docked area (after UI changes)
        if callable(self.on_float_callback):
            print(f"[VIABILITY] Calling float callback")
            self.on_float_callback()
        
        # Update float button state
        if hasattr(self.panel, 'float_button') and not self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(True)
            self._updating_button = False
        
        # Show window
        self.window.show_all()
        print(f"[VIABILITY] Detach complete")
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        if self._updating_button:
            return
        
        is_active = button.get_active()
        if is_active:
            self.detach()
        else:
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def _on_delete_event(self, window, event):
        """Handle window close (X button clicked)."""
        # Hide the floating window and reattach to dock container if available
        try:
            self.window.hide()
        except Exception:
            pass

        if self.parent_container:
            self.hang_on(self.parent_container)

        # Update float button to inactive state after reattach
        if hasattr(self.panel, 'float_button') and self.panel.float_button.get_active():
            self._updating_button = True
            self.panel.float_button.set_active(False)
            self._updating_button = False

        # Return True to prevent window destruction (we keep the window instance)
        return True
    
    def hide(self):
        """Hide the panel (window or docked)."""
        if self.is_hanged:
            if self.parent_container:
                self.parent_container.set_visible(False)
        else:
            self.window.hide()
    
    def show(self):
        """Show the panel (window or docked)."""
        if self.is_hanged:
            if self.parent_container:
                self.parent_container.set_visible(True)
            self.content.show_all()
        else:
            self.window.show_all()
    
    def set_parent_window(self, parent_window):
        """Set parent window for modal dialog behavior.
        
        Args:
            parent_window: Parent GtkWindow
        """
        self.parent_window = parent_window
        if not self.is_hanged:
            self.window.set_transient_for(parent_window)


__all__ = ['ViabilityPanelLoader']
