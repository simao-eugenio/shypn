"""
SBML Metadata Category

Displays extracted SBML information in a tree view:
- Parameters (global and local)
- Compartments
- Events
- Annotations
- Unit definitions

Allows users to click on items to highlight corresponding elements in the canvas.
"""

from gi.repository import Gtk, Pango
import logging


class SBMLMetadataCategory:
    """SBML metadata tree view for Report panel."""
    
    def __init__(self, parent_panel):
        """Initialize SBML metadata category.
        
        Args:
            parent_panel: Parent ReportPanel instance
        """
        self.parent_panel = parent_panel
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Tree store columns: [icon, name, value, type, object_id, full_info]
        self.store = Gtk.TreeStore(str, str, str, str, str, str)
        self.tree_view = None
        self.container = None
    
    def create_widgets(self) -> Gtk.Widget:
        """Create the SBML metadata tree view.
        
        Returns:
            Container widget with tree view
        """
        # Main container
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.container.set_margin_top(12)
        self.container.set_margin_bottom(12)
        self.container.set_margin_start(12)
        self.container.set_margin_end(12)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<b>SBML Metadata Inspector</b>")
        header.set_halign(Gtk.Align.START)
        self.container.pack_start(header, False, False, 0)
        
        # Description
        desc = Gtk.Label()
        desc.set_markup(
            "<small>Click items to highlight in canvas. "
            "Shows parameters, compartments, events, and annotations.</small>"
        )
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.container.pack_start(desc, False, False, 0)
        
        # Scrolled window for tree
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Tree view
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.tree_view.set_enable_tree_lines(True)
        
        # Columns
        # Icon column
        icon_renderer = Gtk.CellRendererText()
        icon_col = Gtk.TreeViewColumn("", icon_renderer, text=0)
        icon_col.set_fixed_width(30)
        self.tree_view.append_column(icon_col)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_renderer.set_property("weight", Pango.Weight.BOLD)
        name_col = Gtk.TreeViewColumn("Name", name_renderer, text=1)
        name_col.set_resizable(True)
        name_col.set_expand(True)
        self.tree_view.append_column(name_col)
        
        # Value column
        value_renderer = Gtk.CellRendererText()
        value_renderer.set_property("family", "monospace")
        value_col = Gtk.TreeViewColumn("Value", value_renderer, text=2)
        value_col.set_resizable(True)
        value_col.set_expand(True)
        self.tree_view.append_column(value_col)
        
        # Connect signals
        self.tree_view.connect("row-activated", self._on_row_activated)
        
        scrolled.add(self.tree_view)
        self.container.pack_start(scrolled, True, True, 0)
        
        # Refresh button
        refresh_btn = Gtk.Button(label="🔄 Refresh Metadata")
        refresh_btn.connect("clicked", lambda w: self.refresh())
        self.container.pack_start(refresh_btn, False, False, 0)
        
        return self.container
    
    def refresh(self):
        """Refresh the SBML metadata tree from current document."""
        self.store.clear()
        
        document = self._get_document()
        if not document:
            # Show "No document" message
            iter_none = self.store.append(None, ["ℹ️", "No document loaded", "", "", "", ""])
            return
        
        # Check if document has SBML metadata
        if not hasattr(document, 'metadata') or not document.metadata:
            iter_none = self.store.append(None, ["ℹ️", "No SBML metadata", "", "", "", ""])
            return
        
        metadata = document.metadata
        
        # Parameters section
        params_root = self.store.append(None, [
            "📊", "Parameters", f"{self._count_parameters(document)} items", 
            "section", "", "Global and local kinetic parameters"
        ])
        self._add_parameters(params_root, document)
        
        # Compartments section
        comps_root = self.store.append(None, [
            "🔷", "Compartments", f"{self._count_compartments(document)} items",
            "section", "", "Cellular compartments with volumes"
        ])
        self._add_compartments(comps_root, document)
        
        # Events section
        events_count = metadata.get('sbml_events_count', 0)
        events_root = self.store.append(None, [
            "⚡", "Events", f"{events_count} items",
            "section", "", "Time/state-triggered perturbations"
        ])
        if events_count > 0:
            self._add_events(events_root, document)
        else:
            self.store.append(events_root, ["", "No events", "", "", "", ""])
        
        # Annotations section
        annot_root = self.store.append(None, [
            "🏷️", "Annotations", "Database IDs",
            "section", "", "ChEBI, KEGG, UniProt cross-references"
        ])
        self._add_annotations(annot_root, document)
        
        # Units section
        units_root = self.store.append(None, [
            "📏", "Unit Definitions", f"{len(metadata.get('unit_definitions', {}))} items",
            "section", "", "Custom units and conversions"
        ])
        self._add_units(units_root, document)
        
        # Expand top-level categories
        self.tree_view.expand_all()
    
    def _get_document(self):
        """Get current DocumentModel."""
        if not hasattr(self.parent_panel, 'main_window'):
            return None
        return getattr(self.parent_panel.main_window, 'document', None)
    
    def _count_parameters(self, document) -> int:
        """Count parameter places in document."""
        count = 0
        for place in document.places:
            if hasattr(place, 'metadata') and place.metadata.get('is_parameter_place'):
                count += 1
        return count
    
    def _count_compartments(self, document) -> int:
        """Count compartment places in document."""
        count = 0
        for place in document.places:
            if hasattr(place, 'is_signal_place') and place.is_signal_place:
                if hasattr(place, 'metadata') and 'compartment_id' in place.metadata:
                    count += 1
        return count
    
    def _add_parameters(self, parent_iter, document):
        """Add parameter entries to tree."""
        for place in document.places:
            if not hasattr(place, 'metadata') or not place.metadata.get('is_parameter_place'):
                continue
            
            param_type = place.metadata.get('parameter_type', 'unknown')
            param_value = place.metadata.get('parameter_value', place.tokens)
            reaction_id = place.metadata.get('used_in_reaction', '')
            
            icon = "🔵" if param_type == "local" else "🌐"
            info = f"{param_type.capitalize()} parameter, used in {reaction_id}"
            
            self.store.append(parent_iter, [
                icon, place.name, str(param_value), "parameter", 
                place.id, info
            ])
    
    def _add_compartments(self, parent_iter, document):
        """Add compartment entries to tree."""
        for place in document.places:
            if not hasattr(place, 'is_signal_place') or not place.is_signal_place:
                continue
            if not hasattr(place, 'metadata') or 'compartment_id' not in place.metadata:
                continue
            
            comp_size = place.metadata.get('compartment_size', place.tokens)
            
            self.store.append(parent_iter, [
                "🔷", place.name, f"{comp_size} L", "compartment",
                place.id, f"Volume: {comp_size} liters"
            ])
    
    def _add_events(self, parent_iter, document):
        """Add event entries to tree."""
        # Events are stored in metadata but not yet visualized
        events = document.metadata.get('sbml_events', [])
        for event in events:
            trigger = event.get('trigger', 'unknown')
            assignments = event.get('assignments', {})
            
            event_iter = self.store.append(parent_iter, [
                "⚡", event.get('id', 'unknown'), trigger, "event",
                event.get('id', ''), f"Trigger: {trigger}"
            ])
            
            # Add assignments as children
            for var, expr in assignments.items():
                self.store.append(event_iter, [
                    "➜", var, expr, "assignment", "", f"Sets {var} = {expr}"
                ])
    
    def _add_annotations(self, parent_iter, document):
        """Add annotation entries to tree."""
        # Group by species/transitions
        species_annot = self.store.append(parent_iter, [
            "🔵", "Species Annotations", "", "section", "", ""
        ])
        transition_annot = self.store.append(parent_iter, [
            "🔶", "Reaction Annotations", "", "section", "", ""
        ])
        
        # Add species annotations
        for place in document.places:
            if hasattr(place, 'metadata') and 'annotation' in place.metadata:
                annot = place.metadata['annotation']
                if annot:
                    place_iter = self.store.append(species_annot, [
                        "🔵", place.label or place.name, "", "species", place.id, ""
                    ])
                    for db, db_id in annot.items():
                        self.store.append(place_iter, [
                            "🏷️", db.upper(), db_id, "database_id", "", f"{db}:{db_id}"
                        ])
        
        # Add transition annotations
        for transition in document.transitions:
            if hasattr(transition, 'metadata') and 'annotation' in transition.metadata:
                annot = transition.metadata['annotation']
                if annot:
                    trans_iter = self.store.append(transition_annot, [
                        "🔶", transition.label or transition.name, "", "transition", transition.id, ""
                    ])
                    for db, db_id in annot.items():
                        self.store.append(trans_iter, [
                            "🏷️", db.upper(), db_id, "database_id", "", f"{db}:{db_id}"
                        ])
    
    def _add_units(self, parent_iter, document):
        """Add unit definition entries to tree."""
        units = document.metadata.get('unit_definitions', {})
        if not units:
            self.store.append(parent_iter, ["", "No custom units", "", "", "", ""])
            return
        
        for unit_id, unit_info in units.items():
            factor = unit_info.get('si_conversion_factor', 1.0)
            self.store.append(parent_iter, [
                "📏", unit_id, f"× {factor}", "unit", "", 
                f"SI conversion: × {factor}"
            ])
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle row activation (double-click or Enter).
        
        Highlights the corresponding element in the canvas.
        """
        model = tree_view.get_model()
        iter_node = model.get_iter(path)
        
        obj_type = model.get_value(iter_node, 3)  # type column
        obj_id = model.get_value(iter_node, 4)    # object_id column
        
        if not obj_id:
            return  # Section header or no object
        
        # Get document and find object
        document = self._get_document()
        if not document:
            return
        
        # Find and select the object
        obj = None
        if obj_type in ["parameter", "compartment", "species"]:
            obj = document.get_place_by_id(obj_id)
        elif obj_type == "transition":
            obj = document.get_transition_by_id(obj_id)
        
        if obj and hasattr(self.parent_panel, 'main_window'):
            # Select and center on object
            main_window = self.parent_panel.main_window
            if hasattr(main_window, 'canvas_manager'):
                main_window.canvas_manager.select_object(obj)
                main_window.canvas_manager.center_on_object(obj)
                self.logger.info(f"Selected {obj_type}: {obj.name}")
