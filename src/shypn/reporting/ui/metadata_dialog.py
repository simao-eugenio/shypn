#!/usr/bin/env python3
"""Metadata editing dialog for model documentation.

This dialog collects and composes metadata from existing system data
(model structure, file info, import history) and allows editing.
Designed for future refactoring to auto-populate from various sources.

Author: Simão Eugénio
Date: 2025-11-15
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, Callable

from ..metadata import ModelMetadata


class MetadataDialog(Gtk.Dialog):
    """Dialog for editing model metadata.
    
    Composes data from multiple sources throughout the system:
    - Model structure (places, transitions, arcs)
    - File information (path, import source)
    - Modification history from system logs
    - User profile data
    
    Future refactoring will auto-populate fields from:
    - model_canvas_manager (model structure)
    - file_explorer_panel (file path, import source)
    - modification tracking systems
    - user_profile (authorship)
    """
    
    def __init__(self, parent: Optional[Gtk.Window], metadata: Optional[ModelMetadata] = None):
        """Initialize metadata dialog.
        
        Args:
            parent: Parent window for modal behavior
            metadata: Existing metadata to edit, or None for new
        """
        super().__init__(
            title="Model Metadata",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        # Store metadata (copy to avoid modifying original until save)
        self.metadata = metadata.from_dict(metadata.to_dict()) if metadata else ModelMetadata()
        self._original_metadata = metadata
        
        # Dialog buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        # Set dialog size
        self.set_default_size(600, 500)
        
        # Build UI
        self._build_ui()
        
        # Populate from metadata
        self._populate_fields()
        
        self.show_all()
    
    def _build_ui(self):
        """Build dialog UI with tabbed notebook."""
        content = self.get_content_area()
        content.set_border_width(12)
        
        # Create notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        content.pack_start(self.notebook, True, True, 0)
        
        # Add tabs
        self._build_basic_tab()
        self._build_authorship_tab()
        self._build_biological_tab()
        self._build_provenance_tab()
        self._build_references_tab()
    
    def _build_basic_tab(self):
        """Build Basic Information tab.
        
        Future: Auto-populate from model object and file path.
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_border_width(12)
        
        # Model Name
        self.name_entry = self._add_entry_row(page, "Model Name:", "")
        
        # Model ID
        self.id_entry = self._add_entry_row(page, "Model ID:", "")
        
        # Version
        self.version_entry = self._add_entry_row(page, "Version:", "1.0")
        
        # Description (multiline)
        desc_label = Gtk.Label(label="Description:", xalign=0)
        page.pack_start(desc_label, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(100)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.description_buffer = Gtk.TextBuffer()
        description_view = Gtk.TextView(buffer=self.description_buffer)
        description_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll.add(description_view)
        page.pack_start(scroll, True, True, 0)
        
        # Keywords (comma-separated)
        self.keywords_entry = self._add_entry_row(page, "Keywords (comma-separated):", "")
        
        # Add tab
        label = Gtk.Label(label="Basic Information")
        self.notebook.append_page(page, label)
    
    def _build_authorship_tab(self):
        """Build Authorship tab.
        
        Future: Auto-populate from UserProfile.
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_border_width(12)
        
        # Primary Author
        self.author_entry = self._add_entry_row(page, "Primary Author:", "")
        
        # Contributors (multiline)
        contrib_label = Gtk.Label(label="Contributors (one per line):", xalign=0)
        page.pack_start(contrib_label, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(80)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.contributors_buffer = Gtk.TextBuffer()
        contributors_view = Gtk.TextView(buffer=self.contributors_buffer)
        contributors_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll.add(contributors_view)
        page.pack_start(scroll, True, True, 0)
        
        # Institution
        self.institution_entry = self._add_entry_row(page, "Institution:", "")
        
        # Department
        self.department_entry = self._add_entry_row(page, "Department:", "")
        
        # Contact Email
        self.email_entry = self._add_entry_row(page, "Contact Email:", "")
        
        # Add tab
        label = Gtk.Label(label="Authorship")
        self.notebook.append_page(page, label)
    
    def _build_biological_tab(self):
        """Build Biological Context tab.
        
        Future: Auto-populate from SBML/KEGG import data.
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_border_width(12)
        
        # Organism
        self.organism_entry = self._add_entry_row(page, "Organism:", "")
        
        # Biological System
        self.system_entry = self._add_entry_row(page, "Biological System:", "")
        
        # Pathway Name
        self.pathway_entry = self._add_entry_row(page, "Pathway Name:", "")
        
        # Cell Type
        self.celltype_entry = self._add_entry_row(page, "Cell Type:", "")
        
        # Add spacer
        page.pack_start(Gtk.Box(), True, True, 0)
        
        # Add tab
        label = Gtk.Label(label="Biological Context")
        self.notebook.append_page(page, label)
    
    def _build_provenance_tab(self):
        """Build Provenance tab.
        
        Future: Auto-populate from file history and import tracking.
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_border_width(12)
        
        # Import Source
        source_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        source_label = Gtk.Label(label="Import Source:", xalign=0)
        source_label.set_size_request(150, -1)
        source_box.pack_start(source_label, False, False, 0)
        
        self.source_combo = Gtk.ComboBoxText()
        self.source_combo.append_text("Manual")
        self.source_combo.append_text("SBML")
        self.source_combo.append_text("KEGG")
        self.source_combo.append_text("BioPAX")
        self.source_combo.append_text("Other")
        self.source_combo.set_active(0)
        source_box.pack_start(self.source_combo, True, True, 0)
        page.pack_start(source_box, False, False, 0)
        
        # Original Model ID
        self.original_id_entry = self._add_entry_row(page, "Original Model ID:", "")
        
        # Modification History (read-only display)
        history_label = Gtk.Label(label="Modification History:", xalign=0)
        page.pack_start(history_label, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(150)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.history_buffer = Gtk.TextBuffer()
        history_view = Gtk.TextView(buffer=self.history_buffer)
        history_view.set_wrap_mode(Gtk.WrapMode.WORD)
        history_view.set_editable(False)
        history_view.set_cursor_visible(False)
        scroll.add(history_view)
        page.pack_start(scroll, True, True, 0)
        
        # Add tab
        label = Gtk.Label(label="Provenance")
        self.notebook.append_page(page, label)
    
    def _build_references_tab(self):
        """Build References tab.
        
        Future: Link to bibliography manager if integrated.
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_border_width(12)
        
        # Publications (multiline)
        pub_label = Gtk.Label(label="Publications (DOI/PubMed, one per line):", xalign=0)
        page.pack_start(pub_label, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(80)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.publications_buffer = Gtk.TextBuffer()
        publications_view = Gtk.TextView(buffer=self.publications_buffer)
        publications_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll.add(publications_view)
        page.pack_start(scroll, True, True, 0)
        
        # Related Models (multiline)
        models_label = Gtk.Label(label="Related Models (one per line):", xalign=0)
        page.pack_start(models_label, False, False, 0)
        
        scroll2 = Gtk.ScrolledWindow()
        scroll2.set_min_content_height(80)
        scroll2.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.related_models_buffer = Gtk.TextBuffer()
        related_models_view = Gtk.TextView(buffer=self.related_models_buffer)
        related_models_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll2.add(related_models_view)
        page.pack_start(scroll2, True, True, 0)
        
        # External Resources (multiline)
        resources_label = Gtk.Label(label="External Resources (URLs, one per line):", xalign=0)
        page.pack_start(resources_label, False, False, 0)
        
        scroll3 = Gtk.ScrolledWindow()
        scroll3.set_min_content_height(80)
        scroll3.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.resources_buffer = Gtk.TextBuffer()
        resources_view = Gtk.TextView(buffer=self.resources_buffer)
        resources_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll3.add(resources_view)
        page.pack_start(scroll3, True, True, 0)
        
        # Add tab
        label = Gtk.Label(label="References")
        self.notebook.append_page(page, label)
    
    def _add_entry_row(self, parent: Gtk.Box, label_text: str, placeholder: str) -> Gtk.Entry:
        """Helper to add label + entry row.
        
        Args:
            parent: Parent container
            label_text: Label text
            placeholder: Entry placeholder
            
        Returns:
            Created entry widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        label = Gtk.Label(label=label_text, xalign=0)
        label.set_size_request(150, -1)
        box.pack_start(label, False, False, 0)
        
        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        box.pack_start(entry, True, True, 0)
        
        parent.pack_start(box, False, False, 0)
        return entry
    
    def _populate_fields(self):
        """Populate fields from metadata object.
        
        Future: This is where auto-population from system sources happens.
        """
        # Basic Information
        self.name_entry.set_text(self.metadata.model_name or "")
        self.id_entry.set_text(self.metadata.model_id or "")
        self.version_entry.set_text(self.metadata.version or "1.0")
        self.description_buffer.set_text(self.metadata.description or "")
        self.keywords_entry.set_text(", ".join(self.metadata.keywords))
        
        # Authorship
        self.author_entry.set_text(self.metadata.primary_author or "")
        self.contributors_buffer.set_text("\n".join(self.metadata.contributors))
        self.institution_entry.set_text(self.metadata.institution or "")
        self.department_entry.set_text(self.metadata.department or "")
        self.email_entry.set_text(self.metadata.contact_email or "")
        
        # Biological Context
        self.organism_entry.set_text(self.metadata.organism or "")
        self.system_entry.set_text(self.metadata.biological_system or "")
        self.pathway_entry.set_text(self.metadata.pathway_name or "")
        self.celltype_entry.set_text(self.metadata.cell_type or "")
        
        # Provenance
        source_idx = {
            "Manual": 0, "SBML": 1, "KEGG": 2, "BioPAX": 3
        }.get(self.metadata.import_source, 0)
        self.source_combo.set_active(source_idx)
        self.original_id_entry.set_text(self.metadata.original_model_id or "")
        
        # Modification History (read-only)
        history_text = []
        for mod in self.metadata.modification_history:
            timestamp = mod.get('timestamp', 'Unknown')
            action = mod.get('action', 'Unknown')
            desc = mod.get('description', '')
            user = mod.get('user', '')
            user_str = f" by {user}" if user else ""
            history_text.append(f"[{timestamp}] {action}{user_str}: {desc}")
        self.history_buffer.set_text("\n".join(history_text) if history_text else "No modifications recorded")
        
        # References
        self.publications_buffer.set_text("\n".join(self.metadata.publications))
        self.related_models_buffer.set_text("\n".join(self.metadata.related_models))
        self.resources_buffer.set_text("\n".join(self.metadata.external_resources))
    
    def _collect_fields(self) -> bool:
        """Collect field values back to metadata object.
        
        Returns:
            True if validation passed
        """
        # Basic Information
        self.metadata.model_name = self.name_entry.get_text().strip()
        self.metadata.model_id = self.id_entry.get_text().strip()
        self.metadata.version = self.version_entry.get_text().strip() or "1.0"
        
        start, end = self.description_buffer.get_bounds()
        self.metadata.description = self.description_buffer.get_text(start, end, True).strip()
        
        keywords_text = self.keywords_entry.get_text().strip()
        self.metadata.keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        
        # Authorship
        self.metadata.primary_author = self.author_entry.get_text().strip()
        
        start, end = self.contributors_buffer.get_bounds()
        contrib_text = self.contributors_buffer.get_text(start, end, True).strip()
        self.metadata.contributors = [c.strip() for c in contrib_text.split('\n') if c.strip()]
        
        self.metadata.institution = self.institution_entry.get_text().strip()
        self.metadata.department = self.department_entry.get_text().strip()
        self.metadata.contact_email = self.email_entry.get_text().strip()
        
        # Biological Context
        self.metadata.organism = self.organism_entry.get_text().strip()
        self.metadata.biological_system = self.system_entry.get_text().strip()
        self.metadata.pathway_name = self.pathway_entry.get_text().strip()
        self.metadata.cell_type = self.celltype_entry.get_text().strip()
        
        # Provenance
        source_text = self.source_combo.get_active_text()
        self.metadata.import_source = source_text if source_text != "Manual" else ""
        self.metadata.original_model_id = self.original_id_entry.get_text().strip()
        
        # References
        start, end = self.publications_buffer.get_bounds()
        pub_text = self.publications_buffer.get_text(start, end, True).strip()
        self.metadata.publications = [p.strip() for p in pub_text.split('\n') if p.strip()]
        
        start, end = self.related_models_buffer.get_bounds()
        models_text = self.related_models_buffer.get_text(start, end, True).strip()
        self.metadata.related_models = [m.strip() for m in models_text.split('\n') if m.strip()]
        
        start, end = self.resources_buffer.get_bounds()
        resources_text = self.resources_buffer.get_text(start, end, True).strip()
        self.metadata.external_resources = [r.strip() for r in resources_text.split('\n') if r.strip()]
        
        # Validate
        is_valid, errors = self.metadata.validate()
        if not is_valid:
            error_text = "\n".join(errors)
            self._show_error_dialog("Validation Error", error_text)
            return False
        
        return True
    
    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def get_metadata(self) -> Optional[ModelMetadata]:
        """Get edited metadata after dialog closes.
        
        Returns:
            Updated metadata if OK was clicked, None if cancelled
        """
        response = self.run()
        self.hide()
        
        if response == Gtk.ResponseType.OK:
            if self._collect_fields():
                # Add modification record for the edit
                self.metadata.add_modification("metadata_updated", "Metadata edited via dialog")
                return self.metadata
        
        return None
    
    # === FUTURE REFACTORING HOOKS ===
    # These methods are placeholders for future auto-population
    
    def compose_from_model(self, model):
        """Compose metadata from model object.
        
        Future: Extract model name, structure info, etc.
        
        Args:
            model: Model object with places, transitions, arcs
        """
        # TODO: Extract from model_canvas_manager
        pass
    
    def compose_from_file_info(self, filepath: str, import_source: str):
        """Compose metadata from file information.
        
        Future: Extract from file_explorer_panel data.
        
        Args:
            filepath: Path to model file
            import_source: Import source ("SBML", "KEGG", etc.)
        """
        # TODO: Extract from file_explorer_panel
        pass
    
    def compose_from_user_profile(self, profile):
        """Compose authorship from user profile.
        
        Future: Auto-fill from UserProfile.
        
        Args:
            profile: UserProfile instance
        """
        # TODO: Auto-populate authorship fields
        pass
