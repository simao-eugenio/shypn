#!/usr/bin/env python3
"""Models category for Report Panel.

Displays Petri net structure and biological entities.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseReportCategory


class ModelsCategory(BaseReportCategory):
    """Models report category.
    
    Displays:
    - Petri net components (places, transitions, arcs counts)
    - Biological entities summary (species, reactions)
    - Sub-expanders for detailed lists
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize models category."""
        super().__init__(
            title="MODELS",
            project=project,
            model_canvas=model_canvas,
            expanded=False
        )
    
    def _build_content(self):
        """Build models content: Summary first, then sub-expanders."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === SUMMARY SECTION (Always visible when category is open) ===
        summary_frame = Gtk.Frame()
        summary_frame.set_label("Petri Net Structure")
        summary_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_start(12)
        summary_box.set_margin_end(12)
        summary_box.set_margin_top(6)
        summary_box.set_margin_bottom(6)
        
        self.summary_label = Gtk.Label()
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        self.summary_label.set_text("No model loaded")
        summary_box.pack_start(self.summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # Show frame explicitly
        summary_frame.show_all()
        
        # === SUB-EXPANDERS (Collapsed by default) ===
        
        # Sub-expander: Species List
        # TODO: Future refinement - Create table with columns:
        #       - Place Name (from Petri Net)
        #       - Species Code (identifier)
        #       - Species Name (biological name)
        #       Need to determine what data is available from model/enrichments
        self.species_expander = Gtk.Expander(label="Show Species List")
        self.species_expander.set_expanded(False)
        scrolled_species, self.species_textview, self.species_buffer = self._create_scrolled_textview(
            "No data"
        )
        self.species_expander.add(scrolled_species)
        box.pack_start(self.species_expander, False, False, 0)
        
        # Sub-expander: Reactions List
        # TODO: Future refinement - Create table with columns:
        #       - Transition Name (from Petri Net)
        #       - Reaction Code (identifier - if available)
        #       - Reaction Name (biological name - if available)
        #       - Kinetic Law/Type (if available from enrichments)
        #       Need to determine what data is available from model/enrichments
        self.reactions_expander = Gtk.Expander(label="Show Reactions List")
        self.reactions_expander.set_expanded(False)
        scrolled_reactions, self.reactions_textview, self.reactions_buffer = self._create_scrolled_textview(
            "No data"
        )
        self.reactions_expander.add(scrolled_reactions)
        box.pack_start(self.reactions_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def _create_summary_grid(self):
        """No longer needed - summary is in frame."""
        pass
    
    def refresh(self):
        """Refresh models data with summary + detailed lists."""
        if not self.model_canvas or not hasattr(self.model_canvas, 'model'):
            self.summary_label.set_text("No model loaded")
            self.species_buffer.set_text("No model loaded")
            self.reactions_buffer.set_text("No model loaded")
            return
        
        model = self.model_canvas.model
        
        # Get counts
        places_count = len(model.places) if hasattr(model, 'places') else 0
        transitions_count = len(model.transitions) if hasattr(model, 'transitions') else 0
        arcs_count = len(model.arcs) if hasattr(model, 'arcs') else 0
        
        # Build summary text
        summary = f"Petri Net: {places_count} places, {transitions_count} transitions, {arcs_count} arcs\n"
        summary += f"Entities: {places_count} species, {transitions_count} reactions"
        self.summary_label.set_text(summary)
        
        # Build detailed lists (hidden in expanders)
        species_text = self._build_species_list(model)
        self.species_buffer.set_text(species_text)
        
        reactions_text = self._build_reactions_list(model)
        self.reactions_buffer.set_text(reactions_text)
    
    def _build_species_list(self, model):
        """Build species/places list."""
        if not hasattr(model, 'places') or not model.places:
            return "No species found"
        
        lines = [f"Total Species: {len(model.places)}", ""]
        
        for i, (place_id, place) in enumerate(model.places.items(), 1):
            if place and hasattr(place, 'label'):
                name = place.label
            elif place and hasattr(place, 'id'):
                name = place.id
            else:
                name = place_id  # Use dict key as fallback
            lines.append(f"{i}. {name}")
        
        return "\n".join(lines)
    
    def _build_reactions_list(self, model):
        """Build reactions/transitions list."""
        if not hasattr(model, 'transitions') or not model.transitions:
            return "No reactions found"
        
        lines = [f"Total Reactions: {len(model.transitions)}", ""]
        
        for i, (trans_id, transition) in enumerate(model.transitions.items(), 1):
            if transition and hasattr(transition, 'label'):
                name = transition.label
            elif transition and hasattr(transition, 'id'):
                name = transition.id
            else:
                name = trans_id  # Use dict key as fallback
            lines.append(f"{i}. {name}")
        
        return "\n".join(lines)
    
    def export_to_text(self):
        """Export as plain text."""
        if not self.model_canvas or not hasattr(self.model_canvas, 'model'):
            return "# MODELS\n\nNo model loaded\n"
        
        text = [
            "# MODELS",
            "",
            self.summary_label.get_text(),
            ""
        ]
        
        # Include detailed lists if expanders are expanded
        if self.species_expander.get_expanded():
            text.append("## Species List")
            text.append(self.species_buffer.get_text(
                self.species_buffer.get_start_iter(),
                self.species_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        if self.reactions_expander.get_expanded():
            text.append("## Reactions List")
            text.append(self.reactions_buffer.get_text(
                self.reactions_buffer.get_start_iter(),
                self.reactions_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        return "\n".join(text)
