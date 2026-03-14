#!/usr/bin/env python3
"""Pathway Panel Loader - Per-Document Instance Architecture.

This module provides a per-document panel loader for the Pathway Operations panel.
Each document gets its own PathwayOperationsPanel instance, ensuring complete
state isolation between documents.

Architecture:
  - Inherits from PerDocumentPanelLoader base class
  - Creates PathwayOperationsPanel with 8 categories (KEGG, SBML, BiGG, BRENDA, etc.)
  - Each panel instance tied to one document (ModelCanvasManager)
  - State preserved per document (form fields, selections, expanded categories)

Author: SHYPN Development Team
Date: 2026-01-06
"""
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK3 not available in pathway_panel_loader: {e}', file=sys.stderr)
    sys.exit(1)

from shypn.ui.panels.pathway_operations_panel import PathwayOperationsPanel
from .base_panel_loader import PerDocumentPanelLoader
from shypn.events import EventBus


class PathwayPanelLoader(PerDocumentPanelLoader):
    """Per-document loader for Pathway Operations panel.
    
    Creates a PathwayOperationsPanel instance tied to a specific document.
    Each document maintains its own pathway operations state:
    - KEGG import: pathway ID, organism, form fields
    - SBML import: file path, BioModels ID
    - BiGG import: model search query, selected model
    - BRENDA: EC numbers list, enrichment history
    - SABIO-RK: query state
    - Heuristic Parameters: configuration
    - Enrichment History: parameter enrichments
    - THERMODYNAMICS: compound mappings, validation settings
    
    Attributes:
        workspace_settings: Optional workspace settings for preferences
        project: Optional project reference
        
    Inherited Attributes:
        model: ModelCanvasManager for this document
        parent_window: Parent window for dialogs (Wayland-safe)
        panel: PathwayOperationsPanel instance
        widget: Root widget for packing into containers
    """
    
    def __init__(self, model, parent_window=None, workspace_settings=None, project=None, canvas_loader=None, document_id=None, drawing_area=None):
        """Initialize pathway panel loader for a document.
        
        Args:
            model: ModelCanvasManager for this document
            parent_window: Optional parent window for dialogs (Wayland-safe)
            workspace_settings: Optional workspace settings
            project: Optional project reference
            canvas_loader: Optional ModelCanvasLoader for creating new tabs
            document_id: Optional document ID for EventBus scoping
            drawing_area: Optional drawing area reference
        """
        self.workspace_settings = workspace_settings
        self.project = project
        self.canvas_loader = canvas_loader
        self.document_id = document_id
        self.drawing_area = drawing_area
        
        # Initialize base class (calls _create_panel)
        super().__init__(model, parent_window)
        
        # Set up legacy compatibility references for backward compatibility
        self._setup_legacy_compatibility()
    
    # =========================================================================
    # Abstract Method Implementations (required by PerDocumentPanelLoader)
    # =========================================================================
    
    def _create_panel(self) -> Gtk.Widget:
        """Create PathwayOperationsPanel instance for this document.
        
        Creates a panel with 8 categories:
        1. KEGG - Import from KEGG database
        2. SBML - Import from SBML files/BioModels
        3. BiGG - Import from BiGG database
        4. BRENDA - Enrich with BRENDA kinetic parameters
        5. SABIO-RK - Enrich with SABIO-RK parameters
        6. Heuristic Parameters - Type-aware parameter inference
        7. Enrichment History - View/rate/undo enrichments
        8. THERMODYNAMICS - Universal thermodynamic validation
        
        Returns:
            PathwayOperationsPanel: The created panel widget
        """
        self.logger.debug(f"Creating PathwayOperationsPanel for document (model id={id(self.model)})")
        
        panel = PathwayOperationsPanel(
            workspace_settings=self.workspace_settings,
            parent_window=self.parent_window,
            project=self.project,
            model_canvas=self.canvas_loader if self.canvas_loader else self.model  # Pass canvas_loader for auto-load imports
        )
        
        return panel
    
    def get_panel_name(self) -> str:
        """Get human-readable panel name.
        
        Returns:
            str: "Pathway Operations"
        """
        return "Pathway Operations"
    
    # =========================================================================
    # Template Method Overrides (optional customization)
    # =========================================================================
    
    def refresh(self) -> None:
        """Refresh panel to reflect current model state.
        
        Updates all 8 categories to ensure they display data for the current model.
        """
        if self.panel:
            self.logger.debug(f"Refreshing {self.get_panel_name()}")
            
            # Note: DO NOT call set_model_canvas(self.model) here!
            # The panel already has the canvas_loader reference from initialization,
            # and calling set_model_canvas(self.model) would replace it with the
            # manager, breaking auto-load for subsequent imports.
            # The categories automatically get the current manager via _get_canvas_manager().
    
    # =========================================================================
    # Legacy Compatibility Methods
    # =========================================================================
    
    def _setup_legacy_compatibility(self) -> None:
        """Set up legacy compatibility references.
        
        Maintains backward compatibility with code that expects specific
        controller references (kegg_import_controller, etc.).
        """
        if self.panel:
            # KEGG category controller
            if hasattr(self.panel, 'kegg_category'):
                self.kegg_import_controller = getattr(
                    self.panel.kegg_category, 'controller', None
                )
            
            # SBML category controller
            if hasattr(self.panel, 'sbml_category'):
                self.sbml_import_controller = getattr(
                    self.panel.sbml_category, 'controller', None
                )
            
            # BRENDA category controller
            if hasattr(self.panel, 'brenda_category'):
                self.brenda_enrichment_controller = getattr(
                    self.panel.brenda_category, 'controller', None
                )
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas reference (legacy compatibility).
        
        This method exists for backward compatibility. The base class
        provides set_model() which should be used instead.
        
        Args:
            model_canvas: ModelCanvasManager or ModelCanvasLoader instance
        """
        # If it's a loader, extract the current manager
        if hasattr(model_canvas, 'get_current_manager'):
            manager = model_canvas.get_current_manager()
            if manager:
                self.set_model(manager)
        else:
            # Direct manager reference
            self.set_model(model_canvas)
        
        # Also update panel's reference
        if self.panel and hasattr(self.panel, 'set_model_canvas'):
            self.panel.set_model_canvas(model_canvas)
    
    def on_tab_switched(self, drawing_area):
        """Handle tab switch event (legacy compatibility).
        
        With per-document instances, tab switching is handled by the
        model_canvas_loader swapping panel instances. This method is
        kept for backward compatibility but does nothing.
        
        Args:
            drawing_area: The newly active DrawingArea
        """
        # No-op: Tab switching handled by instance swapping
        pass
    
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
    
    def add_to_stack(self, stack, container, name):
        """Add panel to GTK stack (legacy compatibility).
        
        With per-document instances, panels are added to containers
        dynamically during tab switching. This method is kept for
        backward compatibility but does nothing.
        
        Args:
            stack: GTK stack
            container: Container widget
            name: Stack page name
        """
        # No-op: Panel packing handled by tab switch logic
        pass


def create_pathway_panel(model_canvas=None, workspace_settings=None, 
                        parent_window=None, project=None):
    """Legacy factory function for creating pathway panel loaders.
    
    This function is kept for backward compatibility with existing code.
    New code should use PanelLoaderFactory.create_pathway_panel() instead.
    
    Args:
        model_canvas: ModelCanvasManager for the document
        workspace_settings: Optional workspace settings
        parent_window: Optional parent window for dialogs
        project: Optional project reference
        
    Returns:
        PathwayPanelLoader: The created panel loader
        
    Note:
        This creates a loader for a single document. With per-document
        instances, you should create one loader per document via the
        factory pattern in base_panel_loader.py.
    """
    return PathwayPanelLoader(
        model=model_canvas,
        parent_window=parent_window,
        workspace_settings=workspace_settings,
        project=project
    )


__all__ = ['PathwayPanelLoader', 'create_pathway_panel']
