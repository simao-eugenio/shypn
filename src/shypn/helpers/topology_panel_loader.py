"""Minimal Topology Panel Loader - Normalized Architecture.

Ultra-minimal loader that instantiates the normalized TopologyPanel class.
All business logic is in the topology panel package.

This is a compatibility wrapper to work with existing shypn.py infrastructure.
Eventually can be reduced further or eliminated.

Author: Simão Eugénio
Date: 2025-10-29
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.topology import TopologyPanel


class TopologyPanelLoader:
    """Minimal loader for normalized Topology Panel.
    
    Responsibilities:
    - Instantiate TopologyPanel class
    - Provide compatibility with existing shypn.py infrastructure
    - Wire model_canvas_loader reference
    
    All panel logic is in the TopologyPanel class and its categories.
    """
    
    def __init__(self, model):
        """Initialize topology panel loader.
        
        Args:
            model: The ShypnModel instance (can be None)
        """
        self.model = model
        self.model_canvas_loader = None  # Set externally
        
        # Create the topology panel
        self.panel = TopologyPanel(
            model=self.model,
            model_canvas=None  # Will be set via set_model_canvas_loader
        )
        
        # Compatibility: old code checks for controller attribute
        # Controller is the loader itself (has on_tab_switched, on_file_opened, etc.)
        self.controller = self
        
        # Expose the panel widget for adding to containers
        self.widget = self.panel
    
    def set_model_canvas_loader(self, model_canvas_loader):
        """Set model canvas loader for accessing current model.
        
        Args:
            model_canvas_loader: ModelCanvasLoader instance
        """
        self.model_canvas_loader = model_canvas_loader
        
        # Pass to panel
        self.panel.set_model_canvas(model_canvas_loader)
    
    def on_tab_switched(self, drawing_area):
        """Handle tab switch event.
        
        Args:
            drawing_area: The newly active drawing area
        """
        # Refresh all categories to update for new tab
        self.panel.refresh()
        
        # Auto-run SAFE analyzers only (P-Invariants, T-Invariants, etc.)
        # Dangerous analyzers (Siphons, Traps, Reachability) require manual expansion
        if drawing_area and self.model_canvas_loader:
            manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
            if manager and not (hasattr(manager, 'is_empty') and manager.is_empty()):
                self.panel.auto_run_all_analyzers()
    
    def on_file_opened(self, drawing_area):
        """Handle file open event.
        
        Args:
            drawing_area: The drawing area with newly opened file
        """
        # Refresh all categories
        self.panel.refresh()
        
        # Auto-run SAFE analyzers only (P-Invariants, T-Invariants, etc.)
        # Dangerous analyzers (Siphons, Traps, Reachability) require manual expansion
        if drawing_area and self.model_canvas_loader:
            manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
            if manager and not (hasattr(manager, 'is_empty') and manager.is_empty()):
                self.panel.auto_run_all_analyzers()
    
    def on_pathway_imported(self, drawing_area):
        """Handle pathway import event.
        
        Args:
            drawing_area: The drawing area with imported pathway
        """
        # Refresh all categories
        self.panel.refresh()
    
    def refresh(self):
        """Refresh the panel."""
        self.panel.refresh()
    
    def add_to_stack(self, stack, container, panel_name='topology'):
        """Add panel content to a GtkStack container.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('topology')
        """
        # Add panel widget directly to container
        if self.widget.get_parent() != container:
            current_parent = self.widget.get_parent()
            if current_parent:
                current_parent.remove(self.widget)
            container.pack_start(self.widget, True, True, 0)
        
        # Show all widgets
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


__all__ = ['TopologyPanelLoader']
