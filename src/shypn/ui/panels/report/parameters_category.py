#!/usr/bin/env python3
"""Dynamic Analyses category for Report Panel.

Displays kinetic parameters, enrichments, and simulation data.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseReportCategory


class DynamicAnalysesCategory(BaseReportCategory):
    """Dynamic Analyses report category.
    
    Displays:
    - Kinetic parameters summary (Km, Kcat, Ki, Vmax)
    - Applied enrichments (BRENDA, SABIO-RK)
    - Parameter sources and citations
    - Simulation results (future)
    - Sub-expanders for detailed data
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize dynamic analyses category."""
        super().__init__(
            title="DYNAMIC ANALYSES",
            project=project,
            model_canvas=model_canvas,
            expanded=False
        )
    
    def _build_content(self):
        """Build dynamic analyses content: Summary first, then sub-expanders."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === SUMMARY SECTION (Always visible when category is open) ===
        summary_frame = Gtk.Frame()
        summary_frame.set_label("Summary")
        summary_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_start(12)
        summary_box.set_margin_end(12)
        summary_box.set_margin_top(6)
        summary_box.set_margin_bottom(6)
        
        self.summary_label = Gtk.Label()
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        self.summary_label.set_text("No enrichments applied yet")
        summary_box.pack_start(self.summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # === SUB-EXPANDERS (Collapsed by default) ===
        
        # Sub-expander: Enrichments Details
        self.enrichments_expander = Gtk.Expander(label="Show Enrichment Details")
        self.enrichments_expander.set_expanded(False)
        scrolled_enrich, self.enrichments_textview, self.enrichments_buffer = self._create_scrolled_textview(
            "No enrichments applied"
        )
        self.enrichments_expander.add(scrolled_enrich)
        box.pack_start(self.enrichments_expander, False, False, 0)
        
        # Sub-expander: Parameter Sources & Citations
        self.citations_expander = Gtk.Expander(label="Show Parameter Sources & Citations")
        self.citations_expander.set_expanded(False)
        scrolled_cit, self.citations_textview, self.citations_buffer = self._create_scrolled_textview(
            "No data"
        )
        self.citations_expander.add(scrolled_cit)
        box.pack_start(self.citations_expander, False, False, 0)
        
        # Sub-expander: Simulation Results (future)
        self.simulation_expander = Gtk.Expander(label="Simulation Results")
        self.simulation_expander.set_expanded(False)
        sim_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sim_box.set_margin_start(12)
        sim_box.set_margin_top(6)
        sim_box.set_margin_bottom(6)
        self.simulation_label = Gtk.Label(label="(No simulations performed yet)")
        self.simulation_label.set_xalign(0)
        sim_box.pack_start(self.simulation_label, False, False, 0)
        self.simulation_expander.add(sim_box)
        box.pack_start(self.simulation_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def _create_summary_grid(self):
        """Create grid for parameter counts."""
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        
        # Labels
        self.total_label = Gtk.Label(label="0")
        self.km_label = Gtk.Label(label="0")
        self.kcat_label = Gtk.Label(label="0")
        self.ki_label = Gtk.Label(label="0")
        self.vmax_label = Gtk.Label(label="0")
        
        for label in [self.total_label, self.km_label, self.kcat_label, self.ki_label, self.vmax_label]:
            label.set_xalign(0)
        
        # Add to grid
        grid.attach(Gtk.Label(label="Total Parameters:"), 0, 0, 1, 1)
        grid.attach(self.total_label, 1, 0, 1, 1)
        
        grid.attach(Gtk.Label(label="Km (substrate affinity):"), 0, 1, 1, 1)
        grid.attach(self.km_label, 1, 1, 1, 1)
        
        grid.attach(Gtk.Label(label="Kcat (turnover number):"), 0, 2, 1, 1)
        grid.attach(self.kcat_label, 1, 2, 1, 1)
        
        grid.attach(Gtk.Label(label="Ki (inhibition constant):"), 0, 3, 1, 1)
        grid.attach(self.ki_label, 1, 3, 1, 1)
        
        grid.attach(Gtk.Label(label="Vmax (maximum velocity):"), 0, 4, 1, 1)
        grid.attach(self.vmax_label, 1, 4, 1, 1)
        
        return grid
    
    def refresh(self):
        """Refresh dynamic analyses data with summary + detailed info."""
        if not self.project or not hasattr(self.project, 'pathways'):
            self.summary_label.set_text("No project loaded")
            self.enrichments_buffer.set_text("No project loaded")
            self.citations_buffer.set_text("No project loaded")
            return
        
        pathways = self.project.pathways.list_pathways()
        
        # Count enrichments
        total_enrichments = sum(len(p.enrichments) for p in pathways)
        
        # Build summary
        if total_enrichments > 0:
            summary = f"Enrichments Applied: {total_enrichments}\n"
            summary += "Parameters: Km=0, Kcat=0, Ki=0, Vmax=0 (to be counted)\n"
            summary += f"Pathways enriched: {len([p for p in pathways if p.enrichments])}"
        else:
            summary = "No enrichments applied yet"
        
        self.summary_label.set_text(summary)
        
        # Build detailed enrichments list
        enrichments_text = self._build_enrichments_detail(pathways)
        self.enrichments_buffer.set_text(enrichments_text)
        
        # Build citations list
        citations_text = self._build_citations_detail(pathways)
        self.citations_buffer.set_text(citations_text)
    
    def _build_enrichments_detail(self, pathways):
        """Build detailed enrichments list."""
        lines = []
        enrichment_count = 0
        
        for pathway in pathways:
            if pathway.enrichments:
                lines.append(f"Pathway: {pathway.name}")
                for enrichment_id in pathway.enrichments:
                    enrichment_count += 1
                    lines.append(f"  {enrichment_count}. Enrichment ID: {enrichment_id}")
                    lines.append(f"      Source: BRENDA (placeholder)")
                    lines.append(f"      Transitions enriched: (to be counted)")
                    lines.append(f"      Parameters added: (to be listed)")
                lines.append("")
        
        if not lines:
            return "No enrichments applied yet"
        
        return "\n".join(lines)
    
    def _build_citations_detail(self, pathways):
        """Build citations and parameter sources list."""
        lines = ["Parameter Sources:", ""]
        
        has_data = False
        for pathway in pathways:
            if pathway.enrichments:
                has_data = True
                lines.append(f"From pathway: {pathway.name}")
                lines.append("  • BRENDA database")
                lines.append(f"  • Organism: {pathway.source_organism}")
                lines.append("  • Citations: (to be extracted from enrichment data)")
                lines.append("")
        
        if not has_data:
            return "No parameter sources available"
        
        return "\n".join(lines)
    
    def export_to_text(self):
        """Export as plain text."""
        if not self.project:
            return "# DYNAMIC ANALYSES\n\nNo project loaded\n"
        
        text = [
            "# DYNAMIC ANALYSES",
            "",
            "## Summary",
            self.summary_label.get_text(),
            ""
        ]
        
        # Include detailed enrichments if expander is expanded
        if self.enrichments_expander.get_expanded():
            text.append("## Enrichments Details")
            text.append(self.enrichments_buffer.get_text(
                self.enrichments_buffer.get_start_iter(),
                self.enrichments_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        # Include citations if expander is expanded
        if self.citations_expander.get_expanded():
            text.append("## Parameter Sources & Citations")
            text.append(self.citations_buffer.get_text(
                self.citations_buffer.get_start_iter(),
                self.citations_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        return "\n".join(text)
