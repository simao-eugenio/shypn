"""Mapping section for place → compound ID mappings.

Provides UI for viewing, editing, and managing compound mappings.
Uses TreeView with confidence badges.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import logging

from .base_section import ThermodynamicsSectionBase
from shypn.thermodynamics.mappers import CompoundMapperService


logger = logging.getLogger(__name__)


class MappingSection(ThermodynamicsSectionBase):
    """Compound mapping editor section.
    
    Provides:
    - Auto-map button (runs mapping service)
    - TreeView showing place → compound mappings with confidence
    - Edit/remove buttons
    - Unmapped places list
    - Statistics display
    """
    
    def __init__(self, model_canvas=None):
        """Initialize mapping section.
        
        Args:
            model_canvas: ModelCanvasManager instance (optional)
        """
        super().__init__(model_canvas)
        
        # Mapper service
        self.mapper_service = CompoundMapperService()
        
        # Widgets (created in build_widget)
        self.tree_view = None
        self.list_store = None
        self.stats_label = None
        self.auto_map_button = None
        
        # Current mappings and confidences
        self.current_mappings = {}
        self.current_confidences = {}
    
    def build_widget(self) -> Gtk.Widget:
        """Build mapping section widget.
        
        Returns:
            Gtk.Frame: Mapping editor frame
        """
        frame = Gtk.Frame()
        frame.set_label("Compound Mappings")
        frame.set_margin_top(6)
        frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        # Toolbar with auto-map and refresh buttons
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.auto_map_button = Gtk.Button(label="Auto-Map Compounds")
        self.auto_map_button.connect("clicked", self._on_auto_map_clicked)
        toolbar.pack_start(self.auto_map_button, False, False, 0)
        
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda btn: self.refresh_data())
        toolbar.pack_start(refresh_button, False, False, 0)
        
        vbox.pack_start(toolbar, False, False, 0)
        
        # Statistics label
        self.stats_label = Gtk.Label(label="No mappings")
        self.stats_label.set_halign(Gtk.Align.START)
        self.stats_label.get_style_context().add_class("dim-label")
        vbox.pack_start(self.stats_label, False, False, 0)
        
        # TreeView in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_vexpand(True)
        
        # Create list store: place_id, place_label, compound_id, confidence, confidence_badge
        self.list_store = Gtk.ListStore(str, str, str, float, str)
        
        self.tree_view = Gtk.TreeView(model=self.list_store)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(1)  # Search by place label
        
        # Place column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Place", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        self.tree_view.append_column(column)
        
        # Compound ID column (editable)
        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect("edited", self._on_compound_edited)
        column = Gtk.TreeViewColumn("Compound ID", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        self.tree_view.append_column(column)
        
        # Confidence badge column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Confidence", renderer, text=4)
        column.set_sort_column_id(3)
        self.tree_view.append_column(column)
        
        scrolled.add(self.tree_view)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        edit_button = Gtk.Button(label="Edit Selected")
        edit_button.connect("clicked", self._on_edit_clicked)
        button_box.pack_start(edit_button, False, False, 0)
        
        remove_button = Gtk.Button(label="Remove Selected")
        remove_button.connect("clicked", self._on_remove_clicked)
        button_box.pack_start(remove_button, False, False, 0)
        
        clear_button = Gtk.Button(label="Clear All")
        clear_button.connect("clicked", self._on_clear_clicked)
        button_box.pack_end(clear_button, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        frame.add(vbox)
        return frame
    
    def refresh_data(self):
        """Refresh mappings from document."""
        if not self.document:
            self.list_store.clear()
            self.stats_label.set_text("No document loaded")
            return
        
        # Get current mappings from document
        mappings = self.document.compound_mappings if hasattr(self.document, 'compound_mappings') else {}
        
        # Re-run mapper to get confidence scores
        try:
            self.current_mappings, self.current_confidences = self.mapper_service.map_all_places(self.document)
        except Exception as e:
            logger.error(f"Failed to run mapper: {e}")
            self.current_mappings = mappings
            self.current_confidences = {pid: 0.0 for pid in mappings}
        
        # Update tree view
        self.list_store.clear()
        
        if not self.document.places:
            self.stats_label.set_text("No places in model")
            return
        
        # Add rows for each place
        for place in self.document.places:
            place_id = place.id
            place_label = place.label if hasattr(place, 'label') else place.name
            compound_id = mappings.get(place_id, "")
            confidence = self.current_confidences.get(place_id, 0.0)
            confidence_badge = self._get_confidence_badge(confidence)
            
            self.list_store.append([place_id, place_label, compound_id, confidence, confidence_badge])
        
        # Update statistics
        self._update_statistics()
    
    def save_to_document(self):
        """Save mappings to document."""
        if not self.document:
            return
        
        # Mappings are already in document.compound_mappings (updated on edit)
        # Just log for confirmation
        count = len(self.document.compound_mappings) if hasattr(self.document, 'compound_mappings') else 0
        logger.info(f"Compound mappings saved: {count} mappings")
    
    def _on_auto_map_clicked(self, button):
        """Handle auto-map button click."""
        if not self.document:
            self._show_error("No document loaded")
            return
        
        button.set_sensitive(False)
        self.auto_map_button.set_label("Mapping...")
        
        def run_mapping():
            try:
                mappings, confidences = self.mapper_service.map_all_places(self.document)
                
                # Update on main thread
                GLib.idle_add(self._on_mapping_complete, mappings, confidences)
            except Exception as e:
                GLib.idle_add(self._on_mapping_error, str(e))
        
        import threading
        thread = threading.Thread(target=run_mapping)
        thread.daemon = True
        thread.start()
    
    def _on_mapping_complete(self, mappings, confidences):
        """Handle mapping completion (on main thread)."""
        self.current_mappings = mappings
        self.current_confidences = confidences
        
        # Update document
        if self.document and hasattr(self.document, 'compound_mappings'):
            self.document.compound_mappings.update(mappings)
        
        # Refresh display
        self.refresh_data()
        
        # Re-enable button
        self.auto_map_button.set_sensitive(True)
        self.auto_map_button.set_label("Auto-Map Compounds")
        
        summary = self.mapper_service.get_mapping_summary(mappings, confidences)
        self._show_info(f"Mapped {summary['total_mapped']} places (avg confidence: {summary['average_confidence']:.0%})")
        
        return False  # Remove from idle
    
    def _on_mapping_error(self, error_msg):
        """Handle mapping error (on main thread)."""
        self._show_error(f"Mapping failed: {error_msg}")
        self.auto_map_button.set_sensitive(True)
        self.auto_map_button.set_label("Auto-Map Compounds")
        return False  # Remove from idle
    
    def _on_compound_edited(self, renderer, path, new_text):
        """Handle compound ID edit in tree view."""
        if not self.document:
            return
        
        # Get place ID from row
        iterator = self.list_store.get_iter(path)
        place_id = self.list_store.get_value(iterator, 0)
        
        # Validate compound ID
        new_text = new_text.strip()
        if new_text:
            try:
                self.mapper_service.update_mapping(self.document, place_id, new_text, confidence=1.0)
                
                # Update tree view
                self.list_store.set_value(iterator, 2, new_text)
                self.list_store.set_value(iterator, 3, 1.0)
                self.list_store.set_value(iterator, 4, "🟢 Manual")
                
                self._update_statistics()
                logger.info(f"Updated mapping: {place_id} → {new_text}")
            except ValueError as e:
                self._show_error(str(e))
        else:
            # Remove mapping
            self.mapper_service.remove_mapping(self.document, place_id)
            self.list_store.set_value(iterator, 2, "")
            self.list_store.set_value(iterator, 3, 0.0)
            self.list_store.set_value(iterator, 4, "")
            self._update_statistics()
    
    def _on_edit_clicked(self, button):
        """Handle edit button click."""
        selection = self.tree_view.get_selection()
        model, iterator = selection.get_selected()
        
        if iterator:
            # Get current values
            place_id = model.get_value(iterator, 0)
            place_label = model.get_value(iterator, 1)
            current_compound = model.get_value(iterator, 2)
            
            # Show edit dialog
            dialog = Gtk.Dialog(
                title="Edit Compound Mapping",
                parent=None,
                flags=0
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
            
            content = dialog.get_content_area()
            content.set_spacing(6)
            content.set_margin_start(12)
            content.set_margin_end(12)
            content.set_margin_top(12)
            content.set_margin_bottom(12)
            
            content.pack_start(Gtk.Label(label=f"Place: {place_label}"), False, False, 0)
            
            entry = Gtk.Entry()
            entry.set_text(current_compound)
            entry.set_activates_default(True)
            content.pack_start(entry, False, False, 0)
            
            dialog.set_default_response(Gtk.ResponseType.OK)
            dialog.show_all()
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                new_compound = entry.get_text().strip()
                if new_compound:
                    try:
                        self.mapper_service.update_mapping(self.document, place_id, new_compound, confidence=1.0)
                        model.set_value(iterator, 2, new_compound)
                        model.set_value(iterator, 3, 1.0)
                        model.set_value(iterator, 4, "🟢 Manual")
                        self._update_statistics()
                    except ValueError as e:
                        self._show_error(str(e))
            
            dialog.destroy()
    
    def _on_remove_clicked(self, button):
        """Handle remove button click."""
        selection = self.tree_view.get_selection()
        model, iterator = selection.get_selected()
        
        if iterator:
            place_id = model.get_value(iterator, 0)
            self.mapper_service.remove_mapping(self.document, place_id)
            model.set_value(iterator, 2, "")
            model.set_value(iterator, 3, 0.0)
            model.set_value(iterator, 4, "")
            self._update_statistics()
    
    def _on_clear_clicked(self, button):
        """Handle clear all button click."""
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear all compound mappings?"
        )
        dialog.format_secondary_text(
            "This will remove all place → compound ID mappings. This action cannot be undone."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            if self.document and hasattr(self.document, 'compound_mappings'):
                self.document.compound_mappings.clear()
                self.refresh_data()
                self._show_info("All mappings cleared")
    
    def _get_confidence_badge(self, confidence: float) -> str:
        """Get confidence badge emoji.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Badge string with emoji
        """
        if confidence == 0.0:
            return ""
        elif confidence >= 0.95:
            return "🟢 High"
        elif confidence >= 0.6:
            return "🟡 Medium"
        else:
            return "🟠 Low"
    
    def _update_statistics(self):
        """Update statistics label."""
        if not self.document or not hasattr(self.document, 'places'):
            self.stats_label.set_text("No document loaded")
            return
        
        total_places = len(self.document.places)
        mappings = self.document.compound_mappings if hasattr(self.document, 'compound_mappings') else {}
        mapped_count = len(mappings)
        unmapped_count = total_places - mapped_count
        
        if total_places == 0:
            self.stats_label.set_text("No places in model")
        else:
            percent = (mapped_count / total_places) * 100 if total_places > 0 else 0
            self.stats_label.set_text(
                f"{mapped_count}/{total_places} places mapped ({percent:.0f}%) • "
                f"{unmapped_count} unmapped"
            )
