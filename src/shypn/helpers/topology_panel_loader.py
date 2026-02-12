"""Topology Panel Loader - Per-Document Architecture.

Per-document loader that instantiates the normalized TopologyPanel class.
Each model/document gets its own TopologyPanelLoader instance with complete
state isolation for topology analysis (invariants, siphons, traps, etc.).

Inherits from PerDocumentPanelLoader base class for consistent behavior
with Pathway and Analyses panels.

Author: Simão Eugénio, SHYPN Development Team
Date: 2026-01-06
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
from shypn.ui.panels.topology import TopologyPanel
from shypn.events import EventBus


class TopologyPanelLoader(PerDocumentPanelLoader):
    """Per-document loader for Topology Panel.
    
    Provides:
    - Per-document topology analysis panel
    - Per-document analysis caches (P-Invariants, T-Invariants, Siphons, Traps, etc.)
    - Full state isolation between documents
    - Auto-run safe analyzers on tab switch/file open
    
    Architecture:
    - Inherits float/attach behavior from PerDocumentPanelLoader
    - Implements _create_panel() to instantiate TopologyPanel
    - Stores model_canvas_loader reference for current model access
    
    All panel logic is in the TopologyPanel class and its categories.
    """
    
    def __init__(self, model, parent_window=None, document_id=None, drawing_area=None):
        """Initialize per-document topology panel loader.
        
        Args:
            model: ModelCanvasManager instance (can be None)
            parent_window: Optional parent window for dialogs
            document_id: Optional document ID for EventBus scoping
            drawing_area: Optional drawing area reference
        """
        self.document_id = document_id
        self.drawing_area = drawing_area
        self.model_canvas_loader = None  # Set after creation
        
        # Initialize base class (creates panel via _create_panel)
        super().__init__(model, parent_window)
        
        # Compatibility: old code checks for controller attribute
        # Controller is the loader itself (has on_tab_switched, on_file_opened)
        self.controller = self
        # Compatibility: old code checks for controller attribute
        # Controller is the loader itself (has on_tab_switched, on_file_opened)
        self.controller = self
    
    def _create_panel(self) -> Gtk.Widget:
        """Factory method: Create TopologyPanel instance.
        
        Returns:
            TopologyPanel widget instance
        """
        panel = TopologyPanel(
            model=self.model,
            model_canvas=None  # Will be set via set_model_canvas_loader
        )
        return panel
    
    def get_panel_name(self) -> str:
        """Get panel display name.
        
        Returns:
            str: Panel name for UI display
        """
        return "Topology"
    
    def initialize(self):
        """Initialize panel (called after construction).
        
        Sets window title and wires float button callback.
        """
        super().initialize()
    
    def refresh(self):
        """Refresh panel with current model state.
        
        Refreshes all topology categories (P-Invariants, T-Invariants, etc.)
        """
        super().refresh()
        if self.panel:
            self.panel.refresh()
    
    # === Model Canvas Loader Integration ===
    
    def set_model_canvas_loader(self, model_canvas_loader):
        """Set model canvas loader for accessing current model.
        
        Args:
            model_canvas_loader: ModelCanvasLoader instance
        """
        self.model_canvas_loader = model_canvas_loader
        
        # Pass to panel
        if self.panel:
            self.panel.set_model_canvas(model_canvas_loader)
    
    # === Event Handlers (Compatibility API) ===
    
    def on_tab_switched(self, drawing_area):
        """Handle tab switch event.
        
        Args:
            drawing_area: The newly active drawing area
        """
        # Refresh all categories to update for new tab
        if self.panel:
            self.panel.refresh()
        
        # Auto-run SAFE analyzers only (P-Invariants, T-Invariants, etc.)
        # Dangerous analyzers (Siphons, Traps, Reachability) require manual expansion
        if drawing_area and self.model_canvas_loader:
            manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
            if manager and not (hasattr(manager, 'is_empty') and manager.is_empty()):
                if self.panel:
                    self.panel.auto_run_all_analyzers()
    
    def on_file_opened(self, drawing_area):
        """Handle file open event.
        
        Args:
            drawing_area: The drawing area with newly opened file
        """
        # Refresh all categories
        if self.panel:
            self.panel.refresh()
        
        # Auto-run SAFE analyzers only
        if drawing_area and self.model_canvas_loader:
            manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
            if manager and not (hasattr(manager, 'is_empty') and manager.is_empty()):
                if self.panel:
                    self.panel.auto_run_all_analyzers()
    
    def on_pathway_imported(self, drawing_area):
        """Handle pathway import event.
        
        Args:
            drawing_area: The drawing area with imported pathway
        """
        # Refresh all categories
        if self.panel:
            self.panel.refresh()
    
    def on_tab_closed(self, drawing_area):
        """Handle tab close event - clear analyzer results.
        
        Args:
            drawing_area: The drawing area being closed
        """
        # Clear all analyzer results for this drawing area
        if self.panel and hasattr(self.panel, 'clear_all_results'):
            self.panel.clear_all_results(drawing_area)
    
    def cleanup(self):
        """Cleanup resources when panel is destroyed.
        
        Called when the associated tab is closed.
        """
        # Unsubscribe from EventBus
        EventBus.unsubscribe('document.focused', self._on_document_focused)
        
        # Clear all results
        if self.panel and hasattr(self.panel, 'clear_all_results'):
            self.panel.clear_all_results()
        
        # Call parent cleanup
        super().cleanup()
    
    def initialize(self):
        """Initialize panel and subscribe to tab switching events."""
        super().initialize()
        # Subscribe to document.focused events for automatic tab switching
        EventBus.subscribe('document.focused', self._on_document_focused)
    
    def _on_document_focused(self, data):
        """Handle document.focused events for automatic panel swapping.
        
        Args:
            data: Event data containing drawing_area, canvas_manager, overlay_manager
        """
        event_document_id = data.get('_document_id')
        
        # Don't handle swapping if panel is floated
        if not self.is_hanged:
            return
        
        # Don't handle if no parent container
        if not self.parent_container:
            return
        
        # Check if this event is for our document
        is_our_document = (event_document_id == self.document_id)
        
        if is_our_document:
            # This is our document - show and refresh
            # Ensure we're in the container
            current_parent = self.widget.get_parent()
            if current_parent != self.parent_container:
                # Not in container, need to pack
                if current_parent:
                    current_parent.remove(self.widget)
                self.parent_container.pack_start(self.widget, True, True, 0)
            
            # Update panel with new document's model
            canvas_manager = data.get('canvas_manager')
            if canvas_manager:
                self.refresh()
            
            # Trigger auto-running safe analyzers
            drawing_area = data.get('drawing_area')
            if drawing_area and hasattr(self, 'on_tab_switched'):
                self.on_tab_switched(drawing_area)
            
            # Show our widget
            self.widget.show()
        else:
            # This is NOT our document - hide
            self.widget.hide()


# === Factory Function ===

def create_topology_panel(model, parent_window=None):
    """Factory function for creating topology panel loaders.
    
    Args:
        model: ModelCanvasManager instance
        parent_window: Optional parent window for dialogs
    
    Returns:
        TopologyPanelLoader: New panel loader instance
    """
    loader = TopologyPanelLoader(model, parent_window)
    loader.initialize()
    return loader


__all__ = ['TopologyPanelLoader', 'create_topology_panel']
