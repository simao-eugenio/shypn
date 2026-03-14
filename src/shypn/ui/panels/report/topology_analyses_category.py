#!/usr/bin/env python3
"""Topology Analyses category for Report Panel.

Displays network structure and connectivity analysis results.
Refactored to use table-based layout for better data presentation and organization.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from .base_category import BaseReportCategory


class TopologyAnalysesCategory(BaseReportCategory):
    """Topology Analyses report category.
    
    Displays summary of topology analysis results for Report Panel.
    Provides structured data for export functions (PDF/Excel/SVG).
    
    Shows:
    - Status indicator (✓/⚠️/❌/ℹ️)
    - Key findings (3-5 bullet points)
    - Brief summaries of 4 analysis categories:
      * Structural Analysis (P/T-Invariants, Siphons, Traps)
      * Graph & Network Analysis (Cycles, Paths, Hubs)
      * Behavioral Analysis (Boundedness, Liveness, Deadlocks, etc.)
      * Biological Analysis (Dependency, Regulatory patterns)
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize topology analyses category."""
        # Set topology_panel BEFORE calling super().__init__
        # because super() calls _build_content() which calls refresh()
        self.topology_panel = None
        
        super().__init__(
            title="TOPOLOGICAL ANALYSES",
            project=project,
            model_canvas=model_canvas,
            expanded=True  # Expand by default so users see content
        )
    
    def _build_content(self):
        """Build topology analyses content with table-based layout."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === STATUS BAR ===
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_markup("<b>ℹ️ Status:</b> No analyses performed yet")
        box.pack_start(self.status_label, False, False, 0)
        
        # === KEY FINDINGS ===
        findings_frame = Gtk.Frame()
        findings_frame.set_label("Key Findings")
        findings_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        findings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        findings_box.set_margin_start(12)
        findings_box.set_margin_end(12)
        findings_box.set_margin_top(6)
        findings_box.set_margin_bottom(6)
        
        self.findings_label = Gtk.Label()
        self.findings_label.set_xalign(0)
        self.findings_label.set_line_wrap(True)
        self.findings_label.set_text("No findings yet - perform analyses in Topology Panel")
        findings_box.pack_start(self.findings_label, False, False, 0)
        
        findings_frame.add(findings_box)
        box.pack_start(findings_frame, False, False, 0)
        
        # === ANALYSIS CATEGORIES (Brief Summaries) ===
        
        # === STRUCTURAL ANALYSIS TABLE ===
        self.structural_expander = Gtk.Expander(label="Structural Analysis")
        self.structural_expander.set_expanded(False)
        
        # Create TreeView for structural analysis
        self.structural_store = Gtk.ListStore(str, int, str, str)  # Type, Count, Coverage, Status
        self.structural_tree = Gtk.TreeView(model=self.structural_store)
        self.structural_tree.set_enable_search(True)
        self.structural_tree.set_search_column(0)
        
        # Configure columns
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Analysis Type", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(120)
        self.structural_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)  # Right-align numbers
        column = Gtk.TreeViewColumn("Count", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_min_width(60)
        self.structural_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)  # Right-align
        column = Gtk.TreeViewColumn("Coverage", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_min_width(80)
        self.structural_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)  # Center-align status
        column = Gtk.TreeViewColumn("Status", renderer, text=3)
        column.set_sort_column_id(3)
        column.set_min_width(60)
        self.structural_tree.append_column(column)
        
        structural_scroll = Gtk.ScrolledWindow()
        structural_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        structural_scroll.set_min_content_height(120)
        structural_scroll.set_max_content_height(250)
        structural_scroll.add(self.structural_tree)
        self.structural_expander.add(structural_scroll)
        box.pack_start(self.structural_expander, False, False, 0)
        
        # === GRAPH & NETWORK ANALYSIS TABLE ===
        self.graph_expander = Gtk.Expander(label="Graph & Network Analysis")
        self.graph_expander.set_expanded(False)
        
        # Create TreeView for graph analysis
        self.graph_store = Gtk.ListStore(str, int, str, str)  # Feature, Count, Details, Status
        self.graph_tree = Gtk.TreeView(model=self.graph_store)
        self.graph_tree.set_enable_search(True)
        self.graph_tree.set_search_column(0)
        
        # Configure columns
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Feature", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(120)
        self.graph_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)
        column = Gtk.TreeViewColumn("Count", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_min_width(60)
        self.graph_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Details", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_expand(True)
        self.graph_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)
        column = Gtk.TreeViewColumn("Status", renderer, text=3)
        column.set_sort_column_id(3)
        column.set_min_width(60)
        self.graph_tree.append_column(column)
        
        graph_scroll = Gtk.ScrolledWindow()
        graph_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        graph_scroll.set_min_content_height(120)
        graph_scroll.set_max_content_height(250)
        graph_scroll.add(self.graph_tree)
        self.graph_expander.add(graph_scroll)
        box.pack_start(self.graph_expander, False, False, 0)
        
        # === BEHAVIORAL ANALYSIS TABLE ===
        self.behavioral_expander = Gtk.Expander(label="Behavioral Analysis")
        self.behavioral_expander.set_expanded(False)
        
        # Create TreeView for behavioral analysis
        self.behavioral_store = Gtk.ListStore(str, str, str, str)  # Property, Result, Status, Details
        self.behavioral_tree = Gtk.TreeView(model=self.behavioral_store)
        self.behavioral_tree.set_enable_search(True)
        self.behavioral_tree.set_search_column(0)
        
        # Configure columns
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Property", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(120)
        self.behavioral_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Result", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_min_width(100)
        self.behavioral_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)
        column = Gtk.TreeViewColumn("Status", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_min_width(60)
        self.behavioral_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("wrap-mode", Pango.WrapMode.WORD)
        renderer.set_property("wrap-width", 250)
        column = Gtk.TreeViewColumn("Details", renderer, text=3)
        column.set_sort_column_id(3)
        column.set_resizable(True)
        column.set_expand(True)
        self.behavioral_tree.append_column(column)
        
        behavioral_scroll = Gtk.ScrolledWindow()
        behavioral_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        behavioral_scroll.set_min_content_height(150)
        behavioral_scroll.set_max_content_height(300)
        behavioral_scroll.add(self.behavioral_tree)
        self.behavioral_expander.add(behavioral_scroll)
        box.pack_start(self.behavioral_expander, False, False, 0)
        
        # === BIOLOGICAL ANALYSIS TABLE ===
        self.biological_expander = Gtk.Expander(label="Biological Analysis")
        self.biological_expander.set_expanded(False)
        
        # Create TreeView for biological analysis
        self.biological_store = Gtk.ListStore(str, str, str, str)  # Analysis, Result, Status, Interpretation
        self.biological_tree = Gtk.TreeView(model=self.biological_store)
        self.biological_tree.set_enable_search(True)
        self.biological_tree.set_search_column(0)
        
        # Configure columns
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Analysis", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(130)
        self.biological_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Result", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_min_width(100)
        self.biological_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)
        column = Gtk.TreeViewColumn("Status", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_min_width(60)
        self.biological_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_property("wrap-mode", Pango.WrapMode.WORD)
        renderer.set_property("wrap-width", 250)
        column = Gtk.TreeViewColumn("Interpretation", renderer, text=3)
        column.set_sort_column_id(3)
        column.set_resizable(True)
        column.set_expand(True)
        self.biological_tree.append_column(column)
        
        biological_scroll = Gtk.ScrolledWindow()
        biological_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        biological_scroll.set_min_content_height(150)
        biological_scroll.set_max_content_height(300)
        biological_scroll.add(self.biological_tree)
        self.biological_expander.add(biological_scroll)
        box.pack_start(self.biological_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
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
                
                # Check if we got valid data
                if summary and 'status' in summary:
                    self._update_display(summary)
                else:
                    # Got response but no valid data structure
                    self.status_label.set_markup("<b>⚠️ Status:</b> Invalid topology data structure")
                    self.findings_label.set_text("Topology panel returned incomplete data")
                    self._show_placeholder()
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                # Show error state with details
                self.status_label.set_markup("<b>❌ Status:</b> Failed to retrieve topology data")
                self.findings_label.set_text(f"Error: {str(e)}\n\nPlease check the Topology Panel connection")
                self._show_placeholder()
                return
        
        # Otherwise show placeholder (topology panel not yet connected)
        self.status_label.set_markup("<b>ℹ️ Status:</b> Topology panel not connected")
        self.findings_label.set_text("Waiting for topology panel connection...\nAnalyses will appear after connection is established")
        self._show_placeholder()
    
    def _update_display(self, summary):
        """Update UI with topology summary (brief preview for user).
        
        Args:
            summary: Dict from TopologyPanel.generate_summary_for_report_panel()
        """
        status = summary.get('status', 'unknown')
        stats = summary.get('statistics', {})
        warnings = summary.get('warnings', [])
        
        status_icons = {
            'complete': '✓',
            'partial': '⚠️',
            'error': '❌',
            'not_analyzed': 'ℹ️'
        }
        icon = status_icons.get(status, '○')
        
        status_text = {
            'complete': 'All analyses complete',
            'partial': 'Partial results (some timeouts)',
            'error': 'Analysis errors occurred',
            'not_analyzed': 'No analysis performed'
        }
        
        status_msg = status_text.get(status, 'Unknown status')
        
        if warnings:
            status_msg += f" - {len(warnings)} warning(s)"
        
        self.status_label.set_markup(f"<b>{icon} Status:</b> {status_msg}")
        
        # === UPDATE KEY FINDINGS ===
        findings = self._extract_key_findings(summary)
        if findings:
            findings_text = "• " + "\n• ".join(findings)
            self.findings_label.set_text(findings_text)
        else:
            self.findings_label.set_text("No significant findings")
        
        # === UPDATE SECTION TABLES ===
        self._update_structural_table(stats)
        self._update_graph_table(stats)
        self._update_behavioral_table(stats)
        self._update_biological_table(stats)
    
    def _extract_key_findings(self, summary):
        """Extract 3-5 key findings for bullet list.
        
        Args:
            summary: Dict from TopologyPanel.generate_summary_for_report_panel()
            
        Returns:
            List of 3-5 key finding strings
        """
        findings = []
        stats = summary.get('statistics', {})
        
        # Structural findings
        p_inv = stats.get('p_invariants', 0) or 0
        if p_inv > 0:
            p_cov = stats.get('p_invariant_coverage', 0)
            findings.append(f"{p_inv} P-invariants ({p_cov:.0%} coverage)")
        
        t_inv = stats.get('t_invariants', 0) or 0
        if t_inv > 0:
            t_cov = stats.get('t_invariant_coverage', 0)
            findings.append(f"{t_inv} T-invariants ({t_cov:.0%} coverage)")
        
        # Graph findings
        cycles = stats.get('cycles', 0) or 0
        if isinstance(cycles, (int, float)) and cycles > 0:
            findings.append(f"{cycles} feedback cycle(s) detected")
        
        hubs = stats.get('hubs', 0) or 0
        if isinstance(hubs, (int, float)) and hubs > 0:
            findings.append(f"{hubs} hub node(s) identified")
        
        # Behavioral findings
        if stats.get('is_bounded') is True:
            findings.append("System is bounded")
        
        if stats.get('is_deadlock_free') is False:
            findings.append("Deadlock states exist")
        elif stats.get('is_deadlock_free') is True:
            findings.append("No deadlocks detected")
        
        # Biological findings
        dep_score = stats.get('dependency_score')
        if dep_score is not None:
            findings.append(f"Dependency score: {dep_score:.2f}")
        
        # Return max 5 findings
        return findings[:5]
    
    def _update_structural_table(self, stats):
        """Populate structural analysis table.
        
        Args:
            stats: statistics dict from summary
        """
        self.structural_store.clear()
        
        # P-Invariants
        p_inv = stats.get('p_invariants')
        p_cov = stats.get('p_invariant_coverage')
        if p_inv is not None and p_inv > 0:
            coverage_str = f"{p_cov:.0%}" if p_cov is not None else "N/A"
            self.structural_store.append(["P-Invariants", p_inv, coverage_str, "✓"])
        elif p_inv == 0:
            self.structural_store.append(["P-Invariants", 0, "0%", "○"])
        else:
            self.structural_store.append(["P-Invariants", 0, "N/A", "○"])
        
        # T-Invariants
        t_inv = stats.get('t_invariants')
        t_cov = stats.get('t_invariant_coverage')
        if t_inv is not None and t_inv > 0:
            coverage_str = f"{t_cov:.0%}" if t_cov is not None else "N/A"
            self.structural_store.append(["T-Invariants", t_inv, coverage_str, "✓"])
        elif t_inv == 0:
            self.structural_store.append(["T-Invariants", 0, "0%", "○"])
        else:
            self.structural_store.append(["T-Invariants", 0, "N/A", "○"])
        
        # Siphons (can be 'blocked')
        siphons = stats.get('siphons')
        if siphons == 'blocked':
            self.structural_store.append(["Siphons", 0, "Blocked", "⏱️"])
        elif siphons is not None and siphons > 0:
            self.structural_store.append(["Siphons", siphons, "N/A", "✓"])
        elif siphons == 0:
            self.structural_store.append(["Siphons", 0, "N/A", "○"])
        else:
            self.structural_store.append(["Siphons", 0, "N/A", "○"])
        
        # Traps (can be 'blocked')
        traps = stats.get('traps')
        if traps == 'blocked':
            self.structural_store.append(["Traps", 0, "Blocked", "⏱️"])
        elif traps is not None and traps > 0:
            self.structural_store.append(["Traps", traps, "N/A", "✓"])
        elif traps == 0:
            self.structural_store.append(["Traps", 0, "N/A", "○"])
        else:
            self.structural_store.append(["Traps", 0, "N/A", "○"])
    
    def _update_graph_table(self, stats):
        """Populate graph & network analysis table.
        
        Args:
            stats: statistics dict from summary
        """
        self.graph_store.clear()
        
        # Feedback Cycles
        cycles = stats.get('cycles')
        if cycles is not None and cycles > 0:
            self.graph_store.append(["Feedback Cycles", int(cycles), "Detected", "✓"])
        elif cycles == 0:
            self.graph_store.append(["Feedback Cycles", 0, "None found", "○"])
        else:
            self.graph_store.append(["Feedback Cycles", 0, "Not computed", "○"])
        
        # Hub Nodes
        hubs = stats.get('hubs')
        if hubs is not None and hubs > 0:
            self.graph_store.append(["Hub Nodes", int(hubs), "High connectivity", "✓"])
        elif hubs == 0:
            self.graph_store.append(["Hub Nodes", 0, "No hubs found", "○"])
        else:
            self.graph_store.append(["Hub Nodes", 0, "Not computed", "○"])
    
    def _update_behavioral_table(self, stats):
        """Populate behavioral analysis table.
        
        Args:
            stats: statistics dict from summary
        """
        self.behavioral_store.clear()
        
        # Boundedness
        is_bounded = stats.get('is_bounded')
        if is_bounded is True:
            self.behavioral_store.append(["Boundedness", "Bounded", "✓", "System tokens limited"])
        elif is_bounded is False:
            self.behavioral_store.append(["Boundedness", "Unbounded", "✗", "Tokens can grow infinitely"])
        else:
            self.behavioral_store.append(["Boundedness", "Not computed", "○", "Analysis not performed"])
        
        # Liveness
        is_live = stats.get('is_live')
        if is_live is True:
            self.behavioral_store.append(["Liveness", "Live", "✓", "All transitions can eventually fire"])
        elif is_live is False:
            self.behavioral_store.append(["Liveness", "Not Live", "✗", "Some transitions cannot fire"])
        else:
            self.behavioral_store.append(["Liveness", "Not computed", "○", "Analysis not performed"])
        
        # Deadlock-Free (use has_deadlock from stats)
        has_deadlock = stats.get('has_deadlock')
        is_deadlock_free = stats.get('is_deadlock_free')
        if is_deadlock_free is True or has_deadlock is False:
            self.behavioral_store.append(["Deadlock-Free", "Yes", "✓", "No deadlock states"])
        elif is_deadlock_free is False or has_deadlock is True:
            self.behavioral_store.append(["Deadlock-Free", "No", "✗", "Deadlock states exist"])
        else:
            self.behavioral_store.append(["Deadlock-Free", "Not computed", "○", "Analysis not performed"])
        
        # Reachability (use reachable_states from stats)
        reachable_states = stats.get('reachable_states')
        if reachable_states is not None and reachable_states > 0:
            self.behavioral_store.append(["Reachability", f"{reachable_states} states", "✓", "State space explored"])
        elif reachable_states == 0:
            self.behavioral_store.append(["Reachability", "0 states", "⚠️", "Empty state space"])
        elif stats.get('siphons') == 'blocked' or stats.get('traps') == 'blocked':
            self.behavioral_store.append(["Reachability", "Blocked", "⏱️", "Model too large"])
        else:
            self.behavioral_store.append(["Reachability", "Not computed", "○", "Analysis not performed"])
    
    def _update_biological_table(self, stats):
        """Populate biological analysis table.
        
        Args:
            stats: statistics dict from summary
        """
        self.biological_store.clear()
        
        # Mass Balance
        mass_balance = stats.get('mass_balance')
        if mass_balance is True:
            self.biological_store.append(["Mass Balance", "Passed", "✓", "All reactions balanced"])
        elif mass_balance is False:
            self.biological_store.append(["Mass Balance", "Failed", "✗", "Some reactions unbalanced"])
        else:
            self.biological_store.append(["Mass Balance", "Not computed", "○", "Analysis not performed"])
        
        # Stoichiometry
        stoichiometry = stats.get('stoichiometry')
        if stoichiometry is True:
            self.biological_store.append(["Stoichiometry", "Valid", "✓", "Stoichiometry is valid"])
        elif stoichiometry is False:
            self.biological_store.append(["Stoichiometry", "Invalid", "✗", "Stoichiometry issues detected"])
        else:
            self.biological_store.append(["Stoichiometry", "Not computed", "○", "Analysis not performed"])
        
        # Flux Balance Analysis
        flux_balance = stats.get('flux_balance')
        if flux_balance is True:
            self.biological_store.append(["Flux Balance", "Feasible", "✓", "FBA solution exists"])
        elif flux_balance is False:
            self.biological_store.append(["Flux Balance", "Infeasible", "✗", "No FBA solution"])
        else:
            self.biological_store.append(["Flux Balance", "Not computed", "○", "Analysis not performed"])
        
        # Dependency Score
        dep_score = stats.get('dependency_score')
        if dep_score is not None:
            if dep_score < 0.3:
                interp = "Low coupling"
            elif dep_score < 0.6:
                interp = "Moderate coupling"
            else:
                interp = "High coupling"
            self.biological_store.append(["Dependency Score", f"{dep_score:.2f}", "✓", interp])
        else:
            self.biological_store.append(["Dependency Score", "N/A", "○", "Not computed"])
        
        # Regulatory Patterns
        reg_patterns = stats.get('regulatory_patterns', 0) or 0
        if reg_patterns > 0:
            self.biological_store.append(["Regulatory Patterns", f"{reg_patterns} found", "✓", "Patterns identified"])
        else:
            self.biological_store.append(["Regulatory Patterns", "None", "○", "No patterns detected"])
        
        # Thermodynamics
        thermo_warnings = stats.get('thermodynamics_warnings', 0)
        if thermo_warnings is not None:
            if thermo_warnings == 0:
                self.biological_store.append(["Thermodynamics", "No warnings", "✓", "All checks passed"])
            else:
                self.biological_store.append(["Thermodynamics", f"{thermo_warnings} warnings", "⚠️", "See Thermodynamic Validation"])
        else:
            self.biological_store.append(["Thermodynamics", "Not computed", "○", "Analysis not performed"])
    
    def get_structured_data(self):
        """Get structured topology analysis data for document generation.
        
        Returns:
            dict: Topology data with keys:
                - title: 'Topological Analyses'
                - has_data: Boolean
                - status: str ('complete', 'partial', 'error', 'not_analyzed')
                - statistics: dict with all topology metrics
                - key_findings: list of finding strings
                - sections: dict with structural, graph, behavioral, biological summaries
        """
        if not self.topology_panel:
            return {
                'title': 'Topological Analyses',
                'has_data': False,
                'status': 'not_analyzed',
                'summary': 'Topology panel not connected'
            }
        
        try:
            summary = self.topology_panel.generate_summary_for_report_panel()
            
            return {
                'title': 'Topological Analyses',
                'has_data': True,
                'status': summary.get('status', 'unknown'),
                'statistics': summary.get('statistics', {}),
                'key_findings': self._extract_key_findings(summary),
                'warnings': summary.get('warnings', []),
                'sections': {
                    'structural': self._get_structural_data(summary.get('statistics', {})),
                    'graph': self._get_graph_data(summary.get('statistics', {})),
                    'behavioral': self._get_behavioral_data(summary.get('statistics', {})),
                    'biological': self._get_biological_data(summary.get('statistics', {}))
                }
            }
        except (AttributeError, KeyError, ValueError, TypeError, RuntimeError) as e:
            return {
                'title': 'Topological Analyses',
                'has_data': False,
                'status': 'error',
                'summary': f'Error fetching topology data: {str(e)}'
            }
    
    def _get_structural_data(self, stats):
        """Extract structural analysis data."""
        return {
            'p_invariants': stats.get('p_invariants', 0),
            'p_invariant_coverage': stats.get('p_invariant_coverage', 0),
            't_invariants': stats.get('t_invariants', 0),
            't_invariant_coverage': stats.get('t_invariant_coverage', 0),
            'siphons': stats.get('siphons', 0),
            'traps': stats.get('traps', 0)
        }
    
    def _get_graph_data(self, stats):
        """Extract graph analysis data."""
        return {
            'cycles': stats.get('cycles', 0),
            'hubs': stats.get('hubs', 0),
            'paths': stats.get('paths', 0)
        }
    
    def _get_behavioral_data(self, stats):
        """Extract behavioral analysis data."""
        return {
            'is_bounded': stats.get('is_bounded'),
            'is_live': stats.get('is_live'),
            'is_deadlock_free': stats.get('is_deadlock_free'),
            'is_reversible': stats.get('is_reversible')
        }
    
    def _get_biological_data(self, stats):
        """Extract biological analysis data."""
        return {
            'dependency_score': stats.get('dependency_score'),
            'regulatory_patterns': stats.get('regulatory_patterns', [])
        }
    
    def _show_placeholder(self):
        """Show placeholder when topology panel not connected."""
        self.status_label.set_markup("<b>ℹ️ Status:</b> No analyses performed yet")
        self.findings_label.set_text("Perform analyses in Topology Panel to see results here")
        
        # Clear all tables and show placeholder rows
        self.structural_store.clear()
        self.structural_store.append(["P-Invariants", 0, "N/A", "○"])
        self.structural_store.append(["T-Invariants", 0, "N/A", "○"])
        self.structural_store.append(["Siphons", 0, "N/A", "○"])
        self.structural_store.append(["Traps", 0, "N/A", "○"])
        
        self.graph_store.clear()
        self.graph_store.append(["Feedback Cycles", 0, "Not computed", "○"])
        self.graph_store.append(["Hub Nodes", 0, "Not computed", "○"])
        self.graph_store.append(["Critical Paths", 0, "Not computed", "○"])
        
        self.behavioral_store.clear()
        self.behavioral_store.append(["Boundedness", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Liveness", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Deadlock-Free", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Fairness", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Reachability", "Not computed", "○", "Analysis not performed"])
        
        self.biological_store.clear()
        self.biological_store.append(["Mass Balance", "Not computed", "○", "Analysis not performed"])
        self.biological_store.append(["Stoichiometry", "Not computed", "○", "Analysis not performed"])
        self.biological_store.append(["Flux Balance", "Not computed", "○", "Analysis not performed"])
        self.biological_store.append(["Dependency Score", "N/A", "○", "Not computed"])
        self.biological_store.append(["Regulatory Patterns", "None", "○", "No patterns detected"])
        self.biological_store.append(["Thermodynamics", "Not computed", "○", "Analysis not performed"])
    
        self.behavioral_store.clear()
        self.behavioral_store.append(["Boundedness", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Liveness", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Deadlock-Free", "Not computed", "○", "Analysis not performed"])
        self.behavioral_store.append(["Reachability", "Not computed", "○", "Analysis not performed"])
        
        self.biological_store.clear()
        self.biological_store.append(["Mass Balance", "Not computed", "○", "Analysis not performed"])
        self.biological_store.append(["Stoichiometry", "Not computed", "○", "Analysis not performed"])
        self.biological_store.append(["Flux Balance", "Not computed", "○", "Analysis not performed"])
        self.biological_store.append(["Dependency Score", "N/A", "○", "Not computed"])
        self.biological_store.append(["Regulatory Patterns", "None", "○", "No patterns detected"])
        self.biological_store.append(["Thermodynamics", "Not computed", "○", "Analysis not performed"])
    
    def get_export_data(self):
        """Provide structured data for export functions (PDF/Excel/SVG).
        
        Called by Report Panel's export buttons at bottom.
        
        Returns:
            Dict with structured data ready for document generation:
            {
                'category': 'Topological Analysis',
                'status': 'complete'/'partial'/'error'/'not_analyzed',
                'key_findings': ['finding 1', 'finding 2', ...],
                'sections': {
                    'structural': {'title': ..., 'data': {...}},
                    'graph_network': {'title': ..., 'data': {...}},
                    'behavioral': {'title': ..., 'data': {...}},
                    'biological': {'title': ..., 'data': {...}}
                },
                'metadata': {...}
            }
        """
        if not self.topology_panel:
            return {
                'category': 'Topological Analysis',
                'status': 'not_analyzed',
                'key_findings': ['No analysis performed yet'],
                'sections': {},
                'metadata': {}
            }
        
        try:
            summary = self.topology_panel.generate_summary_for_report_panel()
        except (AttributeError, KeyError, ValueError, TypeError, RuntimeError) as e:
            return {
                'category': 'Topological Analysis',
                'status': 'error',
                'key_findings': [f'Error retrieving data: {str(e)}'],
                'sections': {},
                'metadata': {}
            }
        
        stats = summary.get('statistics', {})
        
        # Organize data into structured sections
        export_data = {
            'category': 'Topological Analysis',
            'status': summary.get('status', 'unknown'),
            'key_findings': self._extract_key_findings(summary),
            'sections': {
                'structural': {
                    'title': 'Structural Analysis',
                    'data': {
                        'p_invariants': stats.get('p_invariants', 0),
                        'p_invariant_coverage': stats.get('p_invariant_coverage', 0),
                        't_invariants': stats.get('t_invariants', 0),
                        't_invariant_coverage': stats.get('t_invariant_coverage', 0),
                        'siphons': stats.get('siphons', 0),
                        'traps': stats.get('traps', 0),
                    }
                },
                'graph_network': {
                    'title': 'Graph & Network Analysis',
                    'data': {
                        'cycles': stats.get('cycles', 0),
                        'hubs': stats.get('hubs', 0),
                        'paths': stats.get('paths', 0),
                    }
                },
                'behavioral': {
                    'title': 'Behavioral Analysis',
                    'data': {
                        'is_bounded': stats.get('is_bounded'),
                        'is_live': stats.get('is_live'),
                        'is_deadlock_free': stats.get('is_deadlock_free'),
                        'is_fair': stats.get('is_fair'),
                        'is_reachable': stats.get('is_reachable'),
                    }
                },
                'biological': {
                    'title': 'Biological Analysis',
                    'data': {
                        'dependency_score': stats.get('dependency_score'),
                        'regulatory_patterns': stats.get('regulatory_patterns', 0),
                    }
                }
            },
            'metadata': {
                'warnings': summary.get('warnings', []),
                'summary_lines': summary.get('summary_lines', []),
            }
        }
        
        return export_data
    def export_to_text(self):
        """Export as plain text for simple text export.
        
        For full document export (PDF/Excel/SVG), use get_export_data() instead.
        """
        if not self.topology_panel:
            return "# TOPOLOGICAL ANALYSES\n\nNo analyses performed yet."
        
        try:
            export_data = self.get_export_data()
        except Exception as e:
            return f"# TOPOLOGICAL ANALYSES\n\nError: {str(e)}"
        
        lines = ["# TOPOLOGICAL ANALYSES\n"]
        
        # Status
        status = export_data.get('status', 'unknown')
        lines.append(f"Status: {status}\n")
        
        # Key Findings
        findings = export_data.get('key_findings', [])
        if findings:
            lines.append("## Key Findings")
            for finding in findings:
                lines.append(f"  • {finding}")
            lines.append("")
        
        # Sections
        sections = export_data.get('sections', {})
        
        if sections.get('structural'):
            lines.append("## Structural Analysis")
            data = sections['structural']['data']
            lines.append(f"  P-Invariants: {data.get('p_invariants', 0)} ({data.get('p_invariant_coverage', 0):.0%} coverage)")
            lines.append(f"  T-Invariants: {data.get('t_invariants', 0)} ({data.get('t_invariant_coverage', 0):.0%} coverage)")
            lines.append(f"  Siphons: {data.get('siphons', 0)}")
            lines.append(f"  Traps: {data.get('traps', 0)}")
            lines.append("")
        
        if sections.get('graph_network'):
            lines.append("## Graph & Network Analysis")
            data = sections['graph_network']['data']
            lines.append(f"  Cycles: {data.get('cycles', 0)}")
            lines.append(f"  Hubs: {data.get('hubs', 0)}")
            lines.append(f"  Paths: {data.get('paths', 0)}")
            lines.append("")
        
        if sections.get('behavioral'):
            lines.append("## Behavioral Analysis")
            data = sections['behavioral']['data']
            for prop, value in data.items():
                prop_name = prop.replace('is_', '').replace('_', ' ').title()
                if value is True:
                    lines.append(f"  {prop_name}: Yes")
                elif value is False:
                    lines.append(f"  {prop_name}: No")
                elif value == 'timeout':
                    lines.append(f"  {prop_name}: Timeout")
            lines.append("")
        
        if sections.get('biological'):
            lines.append("## Biological Analysis")
            data = sections['biological']['data']
            if data.get('dependency_score') is not None:
                lines.append(f"  Dependency Score: {data['dependency_score']:.2f}")
            if data.get('regulatory_patterns', 0) > 0:
                lines.append(f"  Regulatory Patterns: {data['regulatory_patterns']}")
            lines.append("")
        
        return "\n".join(lines)
