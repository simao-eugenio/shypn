#!/usr/bin/env python3
"""Analyses Panel Loader - Per-Document Instance Architecture.

This module provides the AnalysesPanelLoader class for managing per-document
Dynamic Analyses panel instances. Each document gets its own independent panel
with preserved state for:
- Transition analyses (selected transitions, plot data, locality tracking)
- Place analyses (selected places, trajectories, marking evolution)
- Arc analyses (selected arcs, flow data)
- Reaction analyses (selected reactions)
- Plot configurations (colors, line styles, axes, zoom)

Architecture:
- Inherits from PerDocumentPanelLoader (OOP base class)
- Implements Template Method pattern
- Created per-document in model_canvas_loader._setup_edit_palettes()
- Stored in overlay_managers[drawing_area].analyses_panel_loader
- Tab switching swaps panel instances automatically

Author: GitHub Copilot with Simão Eugénio
Date: January 5, 2026
"""
import sys
import logging

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    logging.getLogger(__name__).error('GTK3 not available: %s', e)
    sys.exit(1)

from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
from shypn.ui.panels.dynamic_analyses import DynamicAnalysesPanel
from shypn.events import EventBus


class AnalysesPanelLoader(PerDocumentPanelLoader):
    """Per-document Dynamic Analyses panel loader.
    
    Each document gets its own panel instance with state preserved:
    - Transitions: Selected transitions, plot lines, locality data
    - Places: Selected places, trajectories, marking history
    - Plotting: Real-time plots, zoom level, axis configuration
    - Context: Selected objects for right-click analysis
    
    State Isolation:
    Every document maintains independent analysis state. Switching tabs
    automatically swaps panel instances, preserving:
    - Selected objects lists (transitions, places, arcs)
    - Plot data and visualization settings
    - Analysis history and cached results
    - UI state (expanded categories, scroll positions)
    
    Example Usage:
        # Created automatically per-document in model_canvas_loader
        analyses_loader = AnalysesPanelLoader(
            model=canvas_manager,
            parent_window=main_window,
            data_collector=data_collector
        )
        analyses_loader.initialize()  # Creates DynamicAnalysesPanel
        
        # Access panel
        panel = analyses_loader.panel  # DynamicAnalysesPanel instance
        
        # Refresh with new model
        analyses_loader.refresh()
    """
    
    def __init__(self, model, parent_window=None, data_collector=None, document_id=None, drawing_area=None):
        """Initialize analyses panel loader.
        
        Args:
            model: ModelCanvasManager instance for this document
            parent_window: Main application window (for dialogs, transient)
            data_collector: SimulationDataCollector for real-time plotting
            document_id: Optional document ID for EventBus scoping
            drawing_area: Optional drawing area reference
        """
        self.data_collector = data_collector
        self.document_id = document_id
        self.drawing_area = drawing_area
        super().__init__(model, parent_window)
    
    def _create_panel(self) -> Gtk.Widget:
        """Create DynamicAnalysesPanel instance (implements abstract method).
        
        Returns:
            DynamicAnalysesPanel: The analyses panel widget
        """
        panel = DynamicAnalysesPanel(
            model=self.model,
            data_collector=self.data_collector
        )
        
        # Store convenience accessors for backward compatibility
        self.place_panel = panel.places_category.panel
        self.transition_panel = panel.transitions_category.panel
        self.plotting_panel = panel.plotting_category.panel
        self.context_menu_handler = None  # Will be created by model_canvas_loader
        
        return panel
    
    def get_panel_name(self) -> str:
        """Return human-readable panel name (implements abstract method).
        
        Returns:
            str: "Dynamic Analyses"
        """
        return "Dynamic Analyses"
    
    def refresh(self):
        """Refresh panel with current model (override base class).
        
        Updates:
        - Model reference in panel
        - Transition panel model registration
        - Place panel model registration
        - Context menu handler model (if exists)
        """
        super().refresh()  # Updates self.panel model
        
        if self.panel:
            # Update model in sub-panels
            if hasattr(self.panel, 'set_model'):
                self.panel.set_model(self.model)
            
            # Register panels with model for object tracking
            if self.model:
                if hasattr(self.place_panel, 'register_with_model'):
                    self.place_panel.register_with_model(self.model)
                if hasattr(self.transition_panel, 'register_with_model'):
                    self.transition_panel.register_with_model(self.model)
            
            # Update context menu handler if it exists
            if hasattr(self, 'context_menu_handler') and self.context_menu_handler:
                if hasattr(self.context_menu_handler, 'set_model'):
                    self.context_menu_handler.set_model(self.model)
    
    def set_data_collector(self, data_collector):
        """Set or update the data collector for plotting panels.
        
        This allows updating the data collector after initialization,
        useful when simulation controller is created after panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        self.data_collector = data_collector
        
        # Update panel's data collector
        if self.panel and hasattr(self.panel, 'set_data_collector'):
            self.panel.set_data_collector(data_collector)
    
    def set_context_menu_handler(self, handler):
        """Set the context menu handler for right-click analysis.
        
        Args:
            handler: ContextMenuHandler instance
        """
        import logging
        logger = logging.getLogger(__name__)
        
        self.context_menu_handler = handler
        
        # Update panel's context menu handler
        if self.panel:
            self.panel.context_menu_handler = handler
            logger.debug(f"[ANALYSES_PANEL] Context menu handler set on panel: place_panel={handler.place_panel is not None}, transition_panel={handler.transition_panel is not None}")
        else:
            logger.warning(f"[ANALYSES_PANEL] Cannot set context menu handler: panel is None")
    
    # ========================================================================
    # Legacy Compatibility Layer
    # These methods maintain backward compatibility with existing code
    # ========================================================================
    
    def set_model(self, model):
        """Legacy method: Set model (delegates to refresh()).
        
        Args:
            model: ModelCanvasManager instance
        """
        self.model = model
        self.refresh()
    
    def recreate_context_menu_handler(self):
        """Legacy method: Recreate context menu handler.
        
        Note: This should be called from model_canvas_loader after
        the loader reference is available.
        """
        pass  # Context menu handler creation delegated to model_canvas_loader
    
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
            
            # Show our widget
            self.widget.show()
        else:
            # This is NOT our document - hide
            self.widget.hide()
    
    def cleanup(self):
        """Cleanup resources and unsubscribe from events."""
        # Unsubscribe from EventBus
        EventBus.unsubscribe('document.focused', self._on_document_focused)
        # Call parent cleanup
        super().cleanup()


def create_analyses_panel(model=None, parent_window=None, data_collector=None):
    """Factory function to create and initialize analyses panel loader.
    
    Backward-compatible factory function for creating AnalysesPanelLoader instances.
    
    Args:
        model: ModelCanvasManager instance
        parent_window: Main application window
        data_collector: SimulationDataCollector for plotting
    
    Returns:
        AnalysesPanelLoader: Initialized panel loader
    
    Example:
        loader = create_analyses_panel(
            model=canvas_manager,
            parent_window=main_window,
            data_collector=collector
        )
        panel = loader.panel  # DynamicAnalysesPanel instance
    """
    loader = AnalysesPanelLoader(model, parent_window, data_collector)
    loader.initialize()
    return loader


__all__ = ['AnalysesPanelLoader', 'create_analyses_panel']
