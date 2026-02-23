"""BiGG import options panel.

Provides checkboxes for import configuration options.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import logging


class BiGGOptionsPanel(Gtk.Box):
    """Widget for BiGG import options.
    
    Provides configuration options for BiGG model import.
    Wayland-safe with proper lifecycle management.
    """
    
    def __init__(self):
        """Initialize options panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self._signal_handlers = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Build widget structure."""
        # Header
        header = Gtk.Label()
        header.set_markup("<b>Import Options</b>")
        header.set_xalign(0)
        self.pack_start(header, False, False, 0)
        
        # Options box
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        options_box.set_margin_start(12)
        
        # Energy signal classification
        self.classify_energy_check = Gtk.CheckButton(
            label="Classify energy signals (ATP, NAD, CoA)"
        )
        self.classify_energy_check.set_active(True)
        self.classify_energy_check.set_tooltip_text(
            "Automatically detect and classify energy metabolites as signal places"
        )
        options_box.pack_start(self.classify_energy_check, False, False, 0)
        
        # Gene import
        self.import_genes_check = Gtk.CheckButton(
            label="Import gene associations"
        )
        self.import_genes_check.set_active(True)
        self.import_genes_check.set_tooltip_text(
            "Import gene-protein-reaction (GPR) associations from model"
        )
        options_box.pack_start(self.import_genes_check, False, False, 0)
        
        # Use cache
        self.use_cache_check = Gtk.CheckButton(
            label="Use cached SBML files"
        )
        self.use_cache_check.set_active(True)
        self.use_cache_check.set_tooltip_text(
            "Use locally cached SBML files to avoid re-downloading"
        )
        options_box.pack_start(self.use_cache_check, False, False, 0)
        
        self.pack_start(options_box, False, False, 0)
    
    def get_classify_energy(self) -> bool:
        """Get energy signal classification option.
        
        Returns:
            True if energy signals should be classified
        """
        return self.classify_energy_check.get_active()
    
    def get_import_genes(self) -> bool:
        """Get gene import option.
        
        Returns:
            True if genes should be imported
        """
        return self.import_genes_check.get_active()
    
    def get_use_cache(self) -> bool:
        """Get cache usage option.
        
        Returns:
            True if cache should be used
        """
        return self.use_cache_check.get_active()
    
    def set_classify_energy(self, value: bool):
        """Set energy signal classification option."""
        self.classify_energy_check.set_active(value)
    
    def set_import_genes(self, value: bool):
        """Set gene import option."""
        self.import_genes_check.set_active(value)
    
    def set_use_cache(self, value: bool):
        """Set cache usage option."""
        self.use_cache_check.set_active(value)
    
    def cleanup(self):
        """Clean up resources (Wayland-safe)."""
        for handler_id, widget in self._signal_handlers:
            try:
                if widget and not widget.is_destroyed():
                    widget.disconnect(handler_id)
            except (AttributeError, TypeError) as e:
                # Widget already destroyed or invalid
                import logging
                logging.getLogger(__name__).debug(f"Signal disconnect failed: {e}")
                pass
        self._signal_handlers.clear()
        self.logger.debug("BiGGOptionsPanel cleaned up")
    
    def do_destroy(self):
        """Override destroy to ensure cleanup."""
        self.cleanup()
        Gtk.Box.do_destroy(self)
