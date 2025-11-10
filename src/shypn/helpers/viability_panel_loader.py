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
            self.panel.model_canvas = model_canvas_loader
    
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
        """Add panel to GtkStack for Master Palette control.
        
        Args:
            stack: GtkStack to add panel to
            container: Container widget for the panel
            panel_name: Name for stack child (default: 'viability')
        """
        self.parent_container = container
        self.parent_window = stack.get_toplevel()
        
        # Add to stack
        stack.add_named(self.panel, panel_name)
        
        print(f"[VIABILITY_LOADER] Added to stack as '{panel_name}'")
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Master Palette control)."""
        def _do_show():
            if self.parent_container:
                # Panel is already in stack, just make sure it's attached
                if not self.is_hanged:
                    self.hang_on(self.parent_container)
            self.panel.show_all()
        
        GLib.idle_add(_do_show)
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Master Palette control)."""
        def _do_hide():
            # Don't actually remove, just let stack handle visibility
            pass
        
        GLib.idle_add(_do_hide)
    
    def hang_on(self, container):
        """Attach panel to container (Wayland-safe).
        
        Args:
            container: GtkContainer to attach panel to
        """
        def _do_hang():
            if self.is_hanged:
                return
            
            self.parent_container = container
            
            # Remove from window if floating
            if self.window.get_child() == self.panel:
                self.window.remove(self.panel)
            
            # Add to container (already in stack, just ensure visibility)
            self.panel.show_all()
            
            # Hide floating window
            self.window.hide()
            
            self.is_hanged = True
            
            # Update float button state
            self._updating_button = True
            if hasattr(self.panel, 'float_button'):
                self.panel.float_button.set_active(False)
            self._updating_button = False
        
        GLib.idle_add(_do_hang)
    
    def detach(self):
        """Detach panel to floating window (Wayland-safe)."""
        def _do_detach():
            if not self.is_hanged:
                return
            
            # Panel stays in stack, but window shows copy
            # Actually, for proper float we need to temporarily remove from stack
            # But since we're using stack, just hide and show in window
            
            # Add to window
            if self.window.get_child() != self.panel:
                # Can't move widget between containers directly in GTK3
                # Need to keep in stack for now, just show window as overlay
                pass
            
            # Show window
            if self.parent_window:
                self.window.set_transient_for(self.parent_window)
            self.window.show_all()
            
            self.is_hanged = False
            
            # Update button state
            self._updating_button = True
            if hasattr(self.panel, 'float_button'):
                self.panel.float_button.set_active(True)
            self._updating_button = False
        
        GLib.idle_add(_do_detach)
    
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
        # Re-attach instead of closing
        if self.parent_container:
            self.hang_on(self.parent_container)
        return True  # Prevent window destruction


__all__ = ['ViabilityPanelLoader']
