"""THERMODYNAMICS category for Pathway Operations Panel.

Thin loader that assembles thermodynamic settings, compound mapping,
and validation sections into a unified category.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import logging

from ..base_pathway_category import BasePathwayCategory
from .settings_section import SettingsSection
from .mapping_section import MappingSection
from .validation_section import ValidationSection


logger = logging.getLogger(__name__)


class ThermodynamicsCategory(BasePathwayCategory):
    """THERMODYNAMICS category for Pathway Operations Panel.
    
    Provides universal access to thermodynamic validation features:
    - Settings configuration (pH, temperature, presets)
    - Compound mapping editor (place → compound ID)
    - Validation trigger and results
    
    This category is available for ALL model types (not just SBML).
    """
    
    def __init__(self, expanded=False, model_canvas=None, parent_window=None):
        """Initialize THERMODYNAMICS category.
        
        Args:
            expanded: Whether category starts expanded
            model_canvas: ModelCanvasManager instance (optional)
            parent_window: Parent window for dialogs (Wayland fix)
        """
        # Initialize attributes BEFORE calling super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_canvas = model_canvas
        self.parent_window = parent_window
        
        # Create sections (self-contained UI components)
        self.settings_section = SettingsSection(model_canvas)
        self.mapping_section = MappingSection(model_canvas)
        self.validation_section = ValidationSection(model_canvas)
        
        # Current document
        self.document = None
        
        # Call parent constructor (calls _build_content)
        super().__init__(category_name="THERMODYNAMICS", expanded=expanded)
    
    def _build_content(self):
        """Build and return the content widget.
        
        Returns:
            Gtk.Box: Container with all sections
        """
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Add sections
        vbox.pack_start(self.settings_section.get_widget(), False, False, 0)
        vbox.pack_start(self.mapping_section.get_widget(), True, True, 0)
        vbox.pack_start(self.validation_section.get_widget(), False, False, 0)
        
        return vbox
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas and update all sections.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
        
        if model_canvas and hasattr(model_canvas, 'document'):
            self.document = model_canvas.document
            
            # Update all sections
            self.settings_section.set_model_canvas(model_canvas)
            self.mapping_section.set_model_canvas(model_canvas)
            self.validation_section.set_model_canvas(model_canvas)
            
            self.logger.info("THERMODYNAMICS category updated with new model canvas")
    
    def set_document(self, document):
        """Set document and update all sections.
        
        Args:
            document: DocumentModel instance
        """
        self.document = document
        
        # Update all sections
        self.settings_section.set_document(document)
        self.mapping_section.set_document(document)
        self.validation_section.set_document(document)
        
        self.logger.info("THERMODYNAMICS category updated with new document")
    
    def refresh(self):
        """Refresh all sections from document."""
        self.settings_section.refresh_data()
        self.mapping_section.refresh_data()
        self.validation_section.refresh_data()
    
    def save_settings(self):
        """Save all section settings to document."""
        if self.document:
            self.settings_section.save_to_document()
            self.mapping_section.save_to_document()
            self.validation_section.save_to_document()
            self.logger.info("Thermodynamic settings saved to document")
