#!/usr/bin/env python3
"""Provenance & Lineage category for Report Panel.

Displays data sources and transformation history.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseReportCategory


class ProvenanceCategory(BaseReportCategory):
    """Provenance & Lineage report category.
    
    Displays:
    - Source pathways (KEGG, SBML)
    - Transformation pipeline
    - Change history
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize provenance category."""
        super().__init__(
            title="PROVENANCE & LINEAGE",
            project=project,
            model_canvas=model_canvas,
            expanded=False
        )
    
    def _build_content(self):
        """Build provenance content: Summary first, then sub-expanders."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === SUMMARY SECTION (Always visible when category is open) ===
        summary_frame = Gtk.Frame()
        summary_frame.set_label("Data Sources Summary")
        summary_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_start(12)
        summary_box.set_margin_end(12)
        summary_box.set_margin_top(6)
        summary_box.set_margin_bottom(6)
        
        self.summary_label = Gtk.Label()
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        self.summary_label.set_text("No project loaded")
        summary_box.pack_start(self.summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # === SUB-EXPANDERS (Collapsed by default) ===
        
        # Sub-expander: Source Pathways
        self.pathways_expander = Gtk.Expander(label="Show Source Pathways")
        self.pathways_expander.set_expanded(False)
        pathways_treeview, pathways_store = self._create_pathways_treeview()
        self.pathways_treeview = pathways_treeview
        self.pathways_store = pathways_store
        self.pathways_expander.add(pathways_treeview)
        box.pack_start(self.pathways_expander, False, False, 0)
        
        # Sub-expander: Transformation Pipeline
        self.pipeline_expander = Gtk.Expander(label="Show Transformation Pipeline")
        self.pipeline_expander.set_expanded(False)
        scrolled, self.pipeline_textview, self.pipeline_buffer = self._create_scrolled_textview(
            "No transformations recorded"
        )
        self.pipeline_expander.add(scrolled)
        box.pack_start(self.pipeline_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def _create_pathways_treeview(self):
        """Create TreeView for source pathways."""
        # Create store: Name | Source | Source_ID | Organism | Date
        store = Gtk.ListStore(str, str, str, str, str)
        
        treeview = Gtk.TreeView(model=store)
        treeview.set_headers_visible(True)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        
        # Columns
        columns = [
            ("Name", 0, 200),
            ("Source", 1, 80),
            ("Source ID", 2, 120),
            ("Organism", 3, 120),
            ("Import Date", 4, 150)
        ]
        
        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            treeview.append_column(column)
        
        # Add scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        scrolled.add(treeview)
        
        return scrolled, store
    
    def refresh(self):
        """Refresh provenance data with summary."""
        self.pathways_store.clear()
        
        if not self.project or not hasattr(self.project, 'pathways'):
            self.summary_label.set_text("No project loaded")
            self.pipeline_buffer.set_text("No project loaded")
            return
        
        # Get pathways
        pathways = self.project.pathways.list_pathways()
        
        # Build summary
        kegg_count = len([p for p in pathways if p.source_type == 'kegg'])
        sbml_count = len([p for p in pathways if p.source_type == 'sbml'])
        converted_count = len([p for p in pathways if p.model_id])
        enriched_count = len([p for p in pathways if p.enrichments])
        
        summary = f"Total Pathways: {len(pathways)}\n"
        summary += f"  KEGG: {kegg_count}, SBML: {sbml_count}\n"
        summary += f"Converted to Models: {converted_count}\n"
        summary += f"Enriched: {enriched_count}"
        
        self.summary_label.set_text(summary)
        
        # Populate pathways table
        for pathway in pathways:
            self.pathways_store.append([
                pathway.name or "Untitled",
                pathway.source_type.upper() if pathway.source_type else "Unknown",
                pathway.source_id or "N/A",
                pathway.source_organism or "N/A",
                str(pathway.imported_date) if pathway.imported_date else "N/A"
            ])
        
        # Build transformation pipeline text
        pipeline_text = self._build_pipeline_text(pathways)
        self.pipeline_buffer.set_text(pipeline_text)
    
    def _build_pipeline_text(self, pathways):
        """Build transformation pipeline description."""
        if not pathways:
            return "No pathways imported"
        
        lines = []
        
        for i, pathway in enumerate(pathways, 1):
            lines.append(f"{i}. {pathway.source_type.upper()} Import")
            lines.append(f"   Source: {pathway.source_id}")
            lines.append(f"   File: {pathway.raw_file}")
            lines.append(f"   Date: {pathway.imported_date}")
            
            if pathway.model_id:
                lines.append(f"   → Converted to model: {pathway.model_id}")
            else:
                lines.append(f"   → Not yet converted")
            
            if pathway.enrichments:
                lines.append(f"   → Enrichments applied: {len(pathway.enrichments)}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def export_to_text(self):
        """Export as plain text."""
        if not self.project or not hasattr(self.project, 'pathways'):
            return "# PROVENANCE & LINEAGE\n\nNo project loaded\n"
        
        pathways = self.project.pathways.list_pathways()
        
        text = [
            "# PROVENANCE & LINEAGE",
            "",
            "## Source Pathways",
            ""
        ]
        
        for pathway in pathways:
            text.append(f"### {pathway.name or 'Untitled'}")
            text.append(f"- Source: {pathway.source_type.upper()}")
            text.append(f"- ID: {pathway.source_id}")
            text.append(f"- Organism: {pathway.source_organism}")
            text.append(f"- Imported: {pathway.imported_date}")
            text.append(f"- File: {pathway.raw_file}")
            text.append("")
        
        text.append("## Transformation Pipeline")
        text.append("")
        text.append(self._build_pipeline_text(pathways))
        text.append("")
        
        return "\n".join(text)
