#!/usr/bin/env python3
"""Topology Analyses category for Report Panel.

Displays network structure and connectivity analysis results.
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseReportCategory


class TopologyAnalysesCategory(BaseReportCategory):
    """Topology Analyses report category.
    
    Displays:
    - Topology analysis results (degree, components, cycles)
    - Locality analysis results (regions)
    - Source-Sink analysis results (flows)
    - Structural invariants (T-inv, P-inv)
    - Sub-expanders for detailed metrics
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize topology analyses category."""
        # Set topology_panel BEFORE calling super().__init__
        # because super() calls _build_content() which calls refresh()
        self.topology_panel = None
        
        super().__init__(
            title="TOPOLOGY ANALYSES",
            project=project,
            model_canvas=model_canvas,
            expanded=True  # Expand by default so users see content
        )
    
    def _build_content(self):
        """Build topology analyses content: Summary first, then sub-expanders."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === SUMMARY SECTION (Always visible when category is open) ===
        summary_frame = Gtk.Frame()
        summary_frame.set_label("Analysis Summary")
        summary_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_start(12)
        summary_box.set_margin_end(12)
        summary_box.set_margin_top(6)
        summary_box.set_margin_bottom(6)
        
        self.overall_summary_label = Gtk.Label()
        self.overall_summary_label.set_xalign(0)
        self.overall_summary_label.set_line_wrap(True)
        self.overall_summary_label.set_markup(
            "<b>Topology Analyses:</b> No analyses performed yet\n"
            "Expand sections below to see details when available."
        )
        summary_box.pack_start(self.overall_summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # === SUB-EXPANDERS (Collapsed by default) ===
        
        # Sub-expander: Topology Analysis
        self.topology_expander = Gtk.Expander(label="Topology Analysis")
        self.topology_expander.set_expanded(False)
        topology_content = self._create_topology_content()
        self.topology_expander.add(topology_content)
        box.pack_start(self.topology_expander, False, False, 0)
        
        # Sub-expander: Locality Analysis
        self.locality_expander = Gtk.Expander(label="Locality Analysis")
        self.locality_expander.set_expanded(False)
        locality_content = self._create_locality_content()
        self.locality_expander.add(locality_content)
        box.pack_start(self.locality_expander, False, False, 0)
        
        # Sub-expander: Source-Sink Analysis
        self.sourcesink_expander = Gtk.Expander(label="Source-Sink Analysis")
        self.sourcesink_expander.set_expanded(False)
        sourcesink_content = self._create_sourcesink_content()
        self.sourcesink_expander.add(sourcesink_content)
        box.pack_start(self.sourcesink_expander, False, False, 0)
        
        # Sub-expander: Structural Invariants
        self.invariants_expander = Gtk.Expander(label="Structural Invariants")
        self.invariants_expander.set_expanded(False)
        invariants_content = self._create_invariants_content()
        self.invariants_expander.add(invariants_content)
        box.pack_start(self.invariants_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def _create_topology_content(self):
        """Create topology analysis content."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Summary
        self.topology_summary_label = Gtk.Label()
        self.topology_summary_label.set_xalign(0)
        self.topology_summary_label.set_line_wrap(True)
        self.topology_summary_label.set_text("No topology analysis performed")
        box.pack_start(self.topology_summary_label, False, False, 0)
        
        # Detailed metrics expander
        details_expander = Gtk.Expander(label="Detailed Metrics")
        details_expander.set_expanded(False)
        scrolled, self.topology_textview, self.topology_buffer = self._create_scrolled_textview(
            "No detailed data available"
        )
        details_expander.add(scrolled)
        box.pack_start(details_expander, False, False, 6)
        
        return box
    
    def _create_locality_content(self):
        """Create locality analysis content."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Summary
        self.locality_summary_label = Gtk.Label()
        self.locality_summary_label.set_xalign(0)
        self.locality_summary_label.set_line_wrap(True)
        self.locality_summary_label.set_text("No locality analysis performed")
        box.pack_start(self.locality_summary_label, False, False, 0)
        
        # Region details expander
        details_expander = Gtk.Expander(label="Region Details")
        details_expander.set_expanded(False)
        scrolled, self.locality_textview, self.locality_buffer = self._create_scrolled_textview(
            "No region data available"
        )
        details_expander.add(scrolled)
        box.pack_start(details_expander, False, False, 6)
        
        return box
    
    def _create_sourcesink_content(self):
        """Create source-sink analysis content."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Summary
        self.sourcesink_summary_label = Gtk.Label()
        self.sourcesink_summary_label.set_xalign(0)
        self.sourcesink_summary_label.set_line_wrap(True)
        self.sourcesink_summary_label.set_text("No source-sink analysis performed")
        box.pack_start(self.sourcesink_summary_label, False, False, 0)
        
        # Flow details expander
        details_expander = Gtk.Expander(label="Flow Details")
        details_expander.set_expanded(False)
        scrolled, self.sourcesink_textview, self.sourcesink_buffer = self._create_scrolled_textview(
            "No flow data available"
        )
        details_expander.add(scrolled)
        box.pack_start(details_expander, False, False, 6)
        
        return box
    
    def _create_invariants_content(self):
        """Create structural invariants content."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Summary
        self.invariants_summary_label = Gtk.Label()
        self.invariants_summary_label.set_xalign(0)
        self.invariants_summary_label.set_line_wrap(True)
        self.invariants_summary_label.set_text("No invariant analysis performed")
        box.pack_start(self.invariants_summary_label, False, False, 0)
        
        # Invariant vectors expander
        details_expander = Gtk.Expander(label="Invariant Vectors")
        details_expander.set_expanded(False)
        scrolled, self.invariants_textview, self.invariants_buffer = self._create_scrolled_textview(
            "No invariant data available"
        )
        details_expander.add(scrolled)
        box.pack_start(details_expander, False, False, 6)
        
        return box
    
    def set_topology_panel(self, topology_panel):
        """Set topology panel reference for fetching analysis data.
        
        Args:
            topology_panel: TopologyPanel instance
        """
        self.topology_panel = topology_panel
        # Refresh to show new data
        self.refresh()
    
    def refresh(self):
        """Refresh topology analyses data from Topology Panel."""
        # If topology panel is available, fetch real summary data
        if self.topology_panel:
            try:
                summary = self.topology_panel.generate_summary_for_report_panel()
                self._update_with_summary(summary)
                return
            except Exception as e:
                print(f"Warning: Could not fetch topology summary: {e}", file=sys.__stderr__)
                # Fall through to placeholder display
        
        # Otherwise show placeholder (topology panel not yet connected)
        self._show_placeholder_summary()
    
    def _update_with_summary(self, summary):
        """Update UI with real topology summary data.
        
        Args:
            summary: Dict from TopologyPanel.generate_summary_for_report_panel()
        """
        # Update OVERALL SUMMARY at the top
        status = summary.get('status', 'unknown')
        summary_lines = summary.get('summary_lines', [])
        statistics = summary.get('statistics', {})
        warnings = summary.get('warnings', [])
        
        # Build summary text with status indicator
        status_emoji = {
            'complete': '✓',
            'partial': '⚠️',
            'error': '❌',
            'not_analyzed': 'ℹ️'
        }.get(status, '○')
        
        summary_text = [f"<b>{status_emoji} Topology Analyses Status:</b>\n"]
        
        # Add summary lines
        for line in summary_lines:
            summary_text.append(f"  {line}")
        
        # Add warnings if any
        if warnings:
            summary_text.append("\n<b>Warnings:</b>")
            for warning in warnings:
                summary_text.append(f"  {warning}")
        
        self.overall_summary_label.set_markup("\n".join(summary_text))
        
        # Update individual sub-sections with detailed data
        self._update_structural_section(statistics)
        self._update_graph_section(statistics)
        self._update_behavioral_section(statistics)
    
    def _update_structural_section(self, statistics):
        """Update structural analysis section with real data."""
        p_inv_count = statistics.get('p_invariants', 0)
        t_inv_count = statistics.get('t_invariants', 0)
        p_inv_coverage = statistics.get('p_invariant_coverage', 0)
        t_inv_coverage = statistics.get('t_invariant_coverage', 0)
        
        if p_inv_count > 0 or t_inv_count > 0:
            summary_text = f"Structural Analysis: ✓ Completed\n"
            summary_text += f"  • {p_inv_count} P-invariants ({p_inv_coverage:.0%} coverage)\n"
            summary_text += f"  • {t_inv_count} T-invariants ({t_inv_coverage:.0%} coverage)"
            self.topology_summary_label.set_text(summary_text)
            
            # Detailed metrics
            details = f"P-Invariants: {p_inv_count}\n"
            details += f"Coverage: {p_inv_coverage:.1%}\n\n"
            details += f"T-Invariants: {t_inv_count}\n"
            details += f"Coverage: {t_inv_coverage:.1%}"
            self.topology_buffer.set_text(details)
        else:
            self.topology_summary_label.set_text("Structural Analysis: Not computed")
            self.topology_buffer.set_text("No structural invariants computed yet")
    
    def _update_graph_section(self, statistics):
        """Update graph/network analysis section with real data."""
        cycles = statistics.get('cycles', 0)
        hubs = statistics.get('hubs', 0)
        paths = statistics.get('paths', 0)
        
        if cycles > 0 or hubs > 0:
            summary_text = f"Graph Analysis: ✓ Completed\n"
            summary_text += f"  • {cycles} cycles detected\n"
            summary_text += f"  • {hubs} hub nodes\n"
            summary_text += f"  • {paths} critical paths"
            self.locality_summary_label.set_text(summary_text)
            
            # Detailed metrics
            details = f"Cycles: {cycles}\n"
            details += f"Hub nodes: {hubs}\n"
            details += f"Critical paths: {paths}"
            self.locality_buffer.set_text(details)
        else:
            self.locality_summary_label.set_text("Graph Analysis: Not computed")
            self.locality_buffer.set_text("No graph analysis performed yet")
    
    def _update_behavioral_section(self, statistics):
        """Update behavioral analysis section with real data."""
        is_live = statistics.get('is_live')
        is_bounded = statistics.get('is_bounded')
        is_deadlock_free = statistics.get('is_deadlock_free')
        
        if is_live is not None or is_bounded is not None:
            summary_text = "Behavioral Analysis: ✓ Completed\n"
            
            properties = []
            if is_live is True:
                properties.append("✓ Live")
            elif is_live is False:
                properties.append("✗ Not live")
            
            if is_bounded is True:
                properties.append("✓ Bounded")
            elif is_bounded is False:
                properties.append("✗ Unbounded")
            
            if is_deadlock_free is True:
                properties.append("✓ Deadlock-free")
            elif is_deadlock_free is False:
                properties.append("✗ Has deadlocks")
            
            if properties:
                summary_text += "  • " + ", ".join(properties)
            
            self.sourcesink_summary_label.set_text(summary_text)
            self.invariants_summary_label.set_text(summary_text)
            
            # Detailed metrics
            details = ""
            if is_live is not None:
                details += f"Liveness: {'Yes' if is_live else 'No'}\n"
            if is_bounded is not None:
                details += f"Boundedness: {'Yes' if is_bounded else 'No'}\n"
            if is_deadlock_free is not None:
                details += f"Deadlock-free: {'Yes' if is_deadlock_free else 'No'}"
            
            self.sourcesink_buffer.set_text(details)
            self.invariants_buffer.set_text(details)
        else:
            self.sourcesink_summary_label.set_text("Behavioral Analysis: Not computed")
            self.invariants_summary_label.set_text("Behavioral Analysis: Not computed")
            self.sourcesink_buffer.set_text("No behavioral analysis performed yet")
            self.invariants_buffer.set_text("No behavioral analysis performed yet")
    
    def _show_placeholder_summary(self):
        """Show placeholder text when topology panel not connected."""
    def _show_placeholder_summary(self):
        """Show placeholder text when topology panel not connected."""
        # TODO: Integrate with actual analysis results from Analyses Panel
        # For now, show placeholder summaries
        
        # Update OVERALL SUMMARY (visible at top when category opens)
        analyses_performed = 0
        summary_lines = ["<b>Topology Analyses Status:</b>"]
        
        # Check each analysis (placeholder - will be real data later)
        topology_done = False  # TODO: Check if topology analysis exists
        locality_done = False  # TODO: Check if locality analysis exists
        sourcesink_done = False  # TODO: Check if source-sink analysis exists
        invariants_done = False  # TODO: Check if invariants computed
        
        if topology_done:
            analyses_performed += 1
            summary_lines.append("  ✓ Topology Analysis")
        else:
            summary_lines.append("  ○ Topology Analysis (not computed)")
        
        if locality_done:
            analyses_performed += 1
            summary_lines.append("  ✓ Locality Analysis")
        else:
            summary_lines.append("  ○ Locality Analysis (not computed)")
        
        if sourcesink_done:
            analyses_performed += 1
            summary_lines.append("  ✓ Source-Sink Analysis")
        else:
            summary_lines.append("  ○ Source-Sink Analysis (not computed)")
        
        if invariants_done:
            analyses_performed += 1
            summary_lines.append("  ✓ Structural Invariants")
        else:
            summary_lines.append("  ○ Structural Invariants (not computed)")
        
        summary_lines.insert(1, f"\n<b>Completed:</b> {analyses_performed} of 4 analyses\n")
        
        self.overall_summary_label.set_markup("\n".join(summary_lines))
        
        # Update individual sub-section summaries
        self.topology_summary_label.set_text(
            "Topology Analysis: (Not yet computed)\n"
            "Will show: Degree distribution, connected components, cycles, hubs"
        )
        
        self.locality_summary_label.set_text(
            "Locality Analysis: (Not yet computed)\n"
            "Will show: Metabolite clustering, region identification"
        )
        
        self.sourcesink_summary_label.set_text(
            "Source-Sink Analysis: (Not yet computed)\n"
            "Will show: Source nodes, sink nodes, flow patterns"
        )
        
        self.invariants_summary_label.set_text(
            "Structural Invariants: (Not yet computed)\n"
            "Will show: T-invariants, P-invariants"
        )
        
        # Detailed data (placeholder)
        self.topology_buffer.set_text(
            "Detailed topology metrics will appear here when analysis is performed:\n"
            "- Node degree distribution\n"
            "- Connected components list\n"
            "- Detected cycles\n"
            "- Hub nodes identification"
        )
        
        self.locality_buffer.set_text(
            "Detailed locality data will appear here when analysis is performed:\n"
            "- Region membership\n"
            "- Region sizes\n"
            "- Inter-region connections"
        )
        
        self.sourcesink_buffer.set_text(
            "Detailed flow data will appear here when analysis is performed:\n"
            "- Source nodes list\n"
            "- Sink nodes list\n"
            "- Flow paths"
        )
        
        self.invariants_buffer.set_text(
            "Detailed invariant vectors will appear here when analysis is performed:\n"
            "- T-invariant vectors\n"
            "- P-invariant vectors"
        )
    
    def export_to_text(self):
        """Export as plain text."""
        text = [
            "# TOPOLOGY ANALYSES",
            ""
        ]
        
        # Include each analysis if its expander is expanded
        if self.topology_expander.get_expanded():
            text.append("## Topology Analysis")
            text.append(self.topology_summary_label.get_text())
            text.append("")
            text.append(self.topology_buffer.get_text(
                self.topology_buffer.get_start_iter(),
                self.topology_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        if self.locality_expander.get_expanded():
            text.append("## Locality Analysis")
            text.append(self.locality_summary_label.get_text())
            text.append("")
            text.append(self.locality_buffer.get_text(
                self.locality_buffer.get_start_iter(),
                self.locality_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        if self.sourcesink_expander.get_expanded():
            text.append("## Source-Sink Analysis")
            text.append(self.sourcesink_summary_label.get_text())
            text.append("")
            text.append(self.sourcesink_buffer.get_text(
                self.sourcesink_buffer.get_start_iter(),
                self.sourcesink_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        if self.invariants_expander.get_expanded():
            text.append("## Structural Invariants")
            text.append(self.invariants_summary_label.get_text())
            text.append("")
            text.append(self.invariants_buffer.get_text(
                self.invariants_buffer.get_start_iter(),
                self.invariants_buffer.get_end_iter(),
                False
            ))
            text.append("")
        
        return "\n".join(text)
