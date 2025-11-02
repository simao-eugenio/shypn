#!/usr/bin/env python3
"""Report Panel - Main container for scientific reports.

Displays comprehensive project reports organized by the 4 main panels.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .model_structure_category import ModelsCategory
from .provenance_category import ProvenanceCategory
from .parameters_category import DynamicAnalysesCategory
from .topology_analyses_category import TopologyAnalysesCategory


class ReportPanel(Gtk.Box):
    """Main report panel with scientific categories.
    
    Organizes report into categories aligned with SHYpn panels:
    - Models (from Model Canvas Panel)
    - Pathway Operations → Dynamic Analyses (from Pathway Operations Panel)
    - Topology Analyses (from Analyses Panel)
    - Provenance & Lineage (from all panels)
    
    Each category is collapsible and can export its content.
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize report panel.
        
        Args:
            project: Project instance
            model_canvas: ModelCanvas instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.project = project
        self.model_canvas = model_canvas
        self.topology_panel = None  # Will be set via set_topology_panel()
        self.dynamic_analyses_panel = None  # Will be set via set_dynamic_analyses_panel()
        self.pathway_operations_panel = None  # Will be set via set_pathway_operations_panel()
        
        # Category controllers
        self.categories = []
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build report panel UI."""
        # Panel title header (matches other panels: EXPLORER, PATHWAY OPERATIONS, etc.)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        header_label = Gtk.Label()
        header_label.set_markup("<b>REPORT</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button on the far right (icon only, matching other panels)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("⬈")
        self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)  # Flat button
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Scrolled window for all categories
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Container for categories
        categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create categories
        self._create_categories(categories_box)
        
        # Export buttons at bottom
        export_box = self._create_export_buttons()
        
        scrolled.add(categories_box)
        
        self.pack_start(scrolled, True, True, 0)
        self.pack_start(export_box, False, False, 0)
        
        # Setup exclusive expansion
        self._setup_exclusive_expansion()
        
        # Show all widgets (this ensures categories are visible even if collapsed)
        self.show_all()
    
    def _create_categories(self, container):
        """Create all report categories aligned with panels.
        
        Args:
            container: Container to add categories to
        """
        # MODELS (from Model Canvas Panel)
        models = ModelsCategory(
            project=self.project,
            model_canvas=self.model_canvas
        )
        self.categories.append(models)
        widget = models.get_widget()
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        
        # DYNAMIC ANALYSES (from Pathway Operations Panel - enrichments)
        dynamic = DynamicAnalysesCategory(
            project=self.project,
            model_canvas=self.model_canvas
        )
        self.categories.append(dynamic)
        widget = dynamic.get_widget()
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        
        # TOPOLOGY ANALYSES (from Analyses Panel)
        topology = TopologyAnalysesCategory(
            project=self.project,
            model_canvas=self.model_canvas
        )
        self.categories.append(topology)
        widget = topology.get_widget()
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        
        # PROVENANCE & LINEAGE (from all panels)
        provenance = ProvenanceCategory(
            project=self.project,
            model_canvas=self.model_canvas
        )
        self.categories.append(provenance)
        widget = provenance.get_widget()
        widget.show_all()
        container.pack_start(widget, False, False, 0)
    
    def _create_export_buttons(self):
        """Create export buttons bar.
        
        Returns:
            Gtk.Box: Box with export buttons
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Export PDF button
        pdf_btn = Gtk.Button(label="📤 Export PDF")
        pdf_btn.set_tooltip_text("Export full report as PDF")
        pdf_btn.connect('clicked', self._on_export_pdf)
        box.pack_start(pdf_btn, True, True, 0)
        
        # Export HTML button
        html_btn = Gtk.Button(label="📤 Export HTML")
        html_btn.set_tooltip_text("Export full report as HTML")
        html_btn.connect('clicked', self._on_export_html)
        box.pack_start(html_btn, True, True, 0)
        
        # Copy button
        copy_btn = Gtk.Button(label="📋 Copy Text")
        copy_btn.set_tooltip_text("Copy report as plain text")
        copy_btn.connect('clicked', self._on_copy_text)
        box.pack_start(copy_btn, True, True, 0)
        
        return box
    
    def _setup_exclusive_expansion(self):
        """Setup exclusive expansion - only one category at a time."""
        for category in self.categories:
            frame = category.get_widget()
            frame._title_event_box.connect('button-press-event',
                lambda w, e, cat=category: self._on_category_clicked(cat))
    
    def _on_category_clicked(self, clicked_category):
        """Handle category click - exclusive expansion.
        
        Args:
            clicked_category: The category that was clicked
        """
        frame = clicked_category.get_widget()
        
        # If clicked category is collapsed, expand it and collapse others
        if not frame.expanded:
            for category in self.categories:
                other_frame = category.get_widget()
                if category == clicked_category:
                    other_frame.set_expanded(True)
                else:
                    other_frame.set_expanded(False)
        
        return True
    
    def set_project(self, project):
        """Set project and refresh all categories.
        
        Args:
            project: Project instance
        """
        self.project = project
        for category in self.categories:
            category.set_project(project)
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas and refresh all categories.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        for category in self.categories:
            category.set_model_canvas(model_canvas)
    
    def set_topology_panel(self, topology_panel):
        """Set topology panel reference for fetching analysis data.
        
        Args:
            topology_panel: TopologyPanel instance
        """
        self.topology_panel = topology_panel
        
        # Update topology analyses category with the panel reference
        for category in self.categories:
            if isinstance(category, TopologyAnalysesCategory):
                category.set_topology_panel(topology_panel)
                break
        
        # Set callback so topology panel can notify us when analyses update
        if hasattr(topology_panel, 'set_report_refresh_callback'):
            topology_panel.set_report_refresh_callback(self._on_topology_updated)
    
    def _on_topology_updated(self):
        """Called by topology panel when analyses are updated."""
        # Refresh the topology analyses category
        for category in self.categories:
            if isinstance(category, TopologyAnalysesCategory):
                category.refresh()
                break
    
    def set_dynamic_analyses_panel(self, dynamic_analyses_panel):
        """Set dynamic analyses panel reference for fetching real-time data.
        
        Args:
            dynamic_analyses_panel: DynamicAnalysesPanel instance
        """
        self.dynamic_analyses_panel = dynamic_analyses_panel
        
        # Update dynamic analyses category with the panel reference
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.set_dynamic_analyses_panel(dynamic_analyses_panel)
                break
        
        # Set callback so dynamic analyses panel can notify us when data updates
        if hasattr(dynamic_analyses_panel, 'set_report_refresh_callback'):
            dynamic_analyses_panel.set_report_refresh_callback(self._on_dynamic_analyses_updated)
    
    def _on_dynamic_analyses_updated(self):
        """Called by dynamic analyses panel when monitoring data is updated."""
        # Refresh the dynamic analyses category
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.refresh()
                break
    
    def set_pathway_operations_panel(self, pathway_operations_panel):
        """Set pathway operations panel reference for fetching pathway data.
        
        Args:
            pathway_operations_panel: PathwayOperationsPanel instance
        """
        self.pathway_operations_panel = pathway_operations_panel
        
        # Update dynamic analyses category with the panel reference
        # (it displays pathway enrichments and KEGG/SBML import data)
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.set_pathway_operations_panel(pathway_operations_panel)
                break
        
        # Set callback so pathway operations panel can notify us when pathways are imported
        if hasattr(pathway_operations_panel, 'set_report_refresh_callback'):
            pathway_operations_panel.set_report_refresh_callback(self._on_pathway_imported)
    
    def _on_pathway_imported(self):
        """Called by pathway operations panel when new pathway is imported."""
        # Refresh the dynamic analyses category (shows pathway enrichments)
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.refresh()
                break
    
    def refresh_all(self):
        """Refresh all categories."""
        for category in self.categories:
            category.refresh()
    
    def _on_export_pdf(self, button):
        """Handle export to PDF."""
        # TODO: Implement PDF export
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="PDF Export"
        )
        dialog.format_secondary_text("PDF export not yet implemented")
        dialog.run()
        dialog.destroy()
    
    def _on_export_html(self, button):
        """Handle export to HTML."""
        # Build HTML from all categories
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>SHYpn Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>SHYpn Project Report</h1>"
        ]
        
        if self.project:
            html_parts.append(f"<p><strong>Project:</strong> {self.project.name}</p>")
        
        # Export each category
        for category in self.categories:
            html_parts.append(category.export_to_html())
        
        html_parts.extend(["</body>", "</html>"])
        
        html_content = "\n".join(html_parts)
        
        # Save dialog
        dialog = Gtk.FileChooserDialog(
            title="Export Report as HTML",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name("report.html")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Export Successful"
                )
                info_dialog.format_secondary_text(f"Report saved to:\n{filepath}")
                info_dialog.run()
                info_dialog.destroy()
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Export Failed"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _on_copy_text(self, button):
        """Handle copy as plain text."""
        # Build text from all categories
        text_parts = ["SHYpn Project Report", "=" * 50, ""]
        
        if self.project:
            text_parts.append(f"Project: {self.project.name}")
            text_parts.append("")
        
        for category in self.categories:
            text_parts.append(category.export_to_text())
        
        text_content = "\n".join(text_parts)
        
        # Copy to clipboard
        clipboard = Gtk.Clipboard.get(Gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text_content, -1)
        
        # Show confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Copied to Clipboard"
        )
        dialog.format_secondary_text("Report text copied to clipboard")
        dialog.run()
        dialog.destroy()
