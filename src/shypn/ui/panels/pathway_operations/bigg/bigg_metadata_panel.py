"""BiGG metadata display panel.

Shows detailed information about selected BiGG model.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Pango
from typing import Optional, Dict
import logging

from shypn.importer.bigg.bigg_model_fetcher import BiGGModelInfo


class BiGGMetadataPanel(Gtk.Box):
    """Widget for displaying BiGG model metadata.
    
    Shows model details including publication, genome info, and statistics.
    Wayland-safe with proper lifecycle management.
    """
    
    def __init__(self):
        """Initialize metadata panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self._current_model: Optional[BiGGModelInfo] = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build widget structure."""
        # Header
        header = Gtk.Label()
        header.set_markup("<b>Model Information</b>")
        header.set_xalign(0)
        self.pack_start(header, False, False, 0)
        
        # Scrolled window for metadata
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        # Text view for metadata
        self.text_buffer = Gtk.TextBuffer()
        self.text_view = Gtk.TextView(buffer=self.text_buffer)
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Pango.WrapMode.WORD)
        self.text_view.set_left_margin(6)
        self.text_view.set_right_margin(6)
        
        scrolled.add(self.text_view)
        self.pack_start(scrolled, True, True, 0)
        
        # Set default message
        self._show_no_selection()
    
    def _show_no_selection(self):
        """Show message when no model selected."""
        self.text_buffer.set_text("Select a model to view details")
    
    def update_model(self, model: Optional[BiGGModelInfo]):
        """Update displayed model information.
        
        Args:
            model: BiGGModelInfo to display, or None to clear
        """
        self._current_model = model
        
        if not model:
            self._show_no_selection()
            return
        
        # Format metadata
        lines = [
            f"Model ID: {model.id}",
            f"Organism: {model.organism}",
            "",
            "Statistics:",
            f"  • Reactions: {model.reaction_count}",
            f"  • Metabolites: {model.metabolite_count}",
            f"  • Genes: {model.gene_count}",
        ]
        
        if model.compartment_count > 0:
            lines.append(f"  • Compartments: {model.compartment_count}")
        
        if model.publication_doi:
            lines.extend([
                "",
                f"Publication: {model.publication_doi}",
            ])
        
        self.text_buffer.set_text("\n".join(lines))
        self.logger.debug(f"Updated metadata for model '{model.id}'")
    
    def update_detailed_metadata(self, details: Dict):
        """Update with detailed metadata from API.
        
        Args:
            details: Detailed model information from get_model_details()
        """
        if not self._current_model:
            return
        
        lines = [
            f"Model ID: {self._current_model.id}",
            f"Organism: {self._current_model.organism}",
            "",
            "Statistics:",
            f"  • Reactions: {self._current_model.reaction_count}",
            f"  • Metabolites: {self._current_model.metabolite_count}",
            f"  • Genes: {self._current_model.gene_count}",
        ]
        
        # Add compartments if available
        if 'compartments' in details:
            compartments = details['compartments']
            lines.append(f"  • Compartments: {len(compartments)}")
        
        # Add genome info if available
        if 'genome_name' in details:
            lines.extend([
                "",
                "Genome:",
                f"  {details['genome_name']}",
            ])
        
        # Add reference if available
        if 'reference_type' in details and 'reference_id' in details:
            lines.extend([
                "",
                f"Reference: {details['reference_type']} {details['reference_id']}",
            ])
        
        self.text_buffer.set_text("\n".join(lines))
    
    def clear(self):
        """Clear displayed metadata."""
        self._current_model = None
        self._show_no_selection()
    
    def cleanup(self):
        """Clean up resources (Wayland-safe)."""
        self.logger.debug("BiGGMetadataPanel cleaned up")
    
    def do_destroy(self):
        """Override destroy to ensure cleanup."""
        self.cleanup()
        Gtk.Box.do_destroy(self)
