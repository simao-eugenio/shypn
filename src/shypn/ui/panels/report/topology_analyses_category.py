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
        """Build topology analyses content: Status + Key Findings + Brief Summaries."""
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
        
        # Structural Analysis
        self.structural_expander = Gtk.Expander(label="Structural Analysis")
        self.structural_expander.set_expanded(False)
        self.structural_summary_label = Gtk.Label()
        self.structural_summary_label.set_xalign(0)
        self.structural_summary_label.set_line_wrap(True)
        self.structural_summary_label.set_margin_start(12)
        self.structural_summary_label.set_margin_end(12)
        self.structural_summary_label.set_margin_top(6)
        self.structural_summary_label.set_margin_bottom(6)
        self.structural_summary_label.set_text("No structural analysis performed")
        self.structural_expander.add(self.structural_summary_label)
        box.pack_start(self.structural_expander, False, False, 0)
        
        # Graph & Network Analysis
        self.graph_expander = Gtk.Expander(label="Graph & Network Analysis")
        self.graph_expander.set_expanded(False)
        self.graph_summary_label = Gtk.Label()
        self.graph_summary_label.set_xalign(0)
        self.graph_summary_label.set_line_wrap(True)
        self.graph_summary_label.set_margin_start(12)
        self.graph_summary_label.set_margin_end(12)
        self.graph_summary_label.set_margin_top(6)
        self.graph_summary_label.set_margin_bottom(6)
        self.graph_summary_label.set_text("No graph analysis performed")
        self.graph_expander.add(self.graph_summary_label)
        box.pack_start(self.graph_expander, False, False, 0)
        
        # Behavioral Analysis
        self.behavioral_expander = Gtk.Expander(label="Behavioral Analysis")
        self.behavioral_expander.set_expanded(False)
        self.behavioral_summary_label = Gtk.Label()
        self.behavioral_summary_label.set_xalign(0)
        self.behavioral_summary_label.set_line_wrap(True)
        self.behavioral_summary_label.set_margin_start(12)
        self.behavioral_summary_label.set_margin_end(12)
        self.behavioral_summary_label.set_margin_top(6)
        self.behavioral_summary_label.set_margin_bottom(6)
        self.behavioral_summary_label.set_text("No behavioral analysis performed")
        self.behavioral_expander.add(self.behavioral_summary_label)
        box.pack_start(self.behavioral_expander, False, False, 0)
        
        # Biological Analysis
        self.biological_expander = Gtk.Expander(label="Biological Analysis")
        self.biological_expander.set_expanded(False)
        self.biological_summary_label = Gtk.Label()
        self.biological_summary_label.set_xalign(0)
        self.biological_summary_label.set_line_wrap(True)
        self.biological_summary_label.set_margin_start(12)
        self.biological_summary_label.set_margin_end(12)
        self.biological_summary_label.set_margin_top(6)
        self.biological_summary_label.set_margin_bottom(6)
        self.biological_summary_label.set_text("No biological analysis performed")
        self.biological_expander.add(self.biological_summary_label)
        box.pack_start(self.biological_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def set_topology_panel(self, topology_panel):
        """Set topology panel reference for fetching analysis data.
        
        Args:
            topology_panel: TopologyPanel instance
        """
        print(f"[TOPOLOGY_CATEGORY] set_topology_panel() called with {topology_panel}")
        self.topology_panel = topology_panel
        # Refresh to show new data
        self.refresh()
    
    def refresh(self):
        """Refresh topology analyses data from Topology Panel."""
        print(f"[TOPOLOGY_CATEGORY] refresh() called, topology_panel={self.topology_panel is not None}")
        
        # If topology panel is available, fetch real summary data
        if self.topology_panel:
            try:
                summary = self.topology_panel.generate_summary_for_report_panel()
                print(f"[TOPOLOGY_CATEGORY] Got summary: status={summary.get('status')}, stats_keys={list(summary.get('statistics', {}).keys())}")
                self._update_display(summary)
                return
            except Exception as e:
                print(f"[TOPOLOGY_CATEGORY] ERROR: Could not fetch topology summary: {e}", file=sys.__stderr__)
                import traceback
                traceback.print_exc()
                # Fall through to placeholder display
        else:
            print(f"[TOPOLOGY_CATEGORY] No topology_panel reference - showing placeholder")
        
        # Otherwise show placeholder (topology panel not yet connected)
        self._show_placeholder()
    
    def _update_display(self, summary):
        """Update UI with topology summary (brief preview for user).
        
        Args:
            summary: Dict from TopologyPanel.generate_summary_for_report_panel()
        """
        status = summary.get('status', 'unknown')
        stats = summary.get('statistics', {})
        warnings = summary.get('warnings', [])
        
        # === UPDATE STATUS BAR ===
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
        
        # === UPDATE SECTION SUMMARIES ===
        self._update_structural_preview(stats)
        self._update_graph_preview(stats)
        self._update_behavioral_preview(stats)
        self._update_biological_preview(stats)
    
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
        p_inv = stats.get('p_invariants', 0)
        if p_inv > 0:
            p_cov = stats.get('p_invariant_coverage', 0)
            findings.append(f"{p_inv} P-invariants ({p_cov:.0%} coverage)")
        
        t_inv = stats.get('t_invariants', 0)
        if t_inv > 0:
            t_cov = stats.get('t_invariant_coverage', 0)
            findings.append(f"{t_inv} T-invariants ({t_cov:.0%} coverage)")
        
        # Graph findings
        cycles = stats.get('cycles', 0)
        if cycles > 0:
            findings.append(f"{cycles} feedback cycle(s) detected")
        
        hubs = stats.get('hubs', 0)
        if hubs > 0:
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
    
    def _update_structural_preview(self, stats):
        """Update structural analysis preview (brief summary).
        
        Args:
            stats: statistics dict from summary
        """
        p_inv = stats.get('p_invariants', 0) or 0
        t_inv = stats.get('t_invariants', 0) or 0
        siphons = stats.get('siphons', 0) or 0
        traps = stats.get('traps', 0) or 0
        
        if p_inv > 0 or t_inv > 0 or siphons > 0 or traps > 0:
            lines = []
            
            if p_inv > 0:
                p_cov = stats.get('p_invariant_coverage', 0)
                lines.append(f"✓ {p_inv} P-invariants ({p_cov:.0%} coverage)")
            
            if t_inv > 0:
                t_cov = stats.get('t_invariant_coverage', 0)
                lines.append(f"✓ {t_inv} T-invariants ({t_cov:.0%} coverage)")
            
            if siphons > 0:
                lines.append(f"✓ {siphons} siphon(s)")
            
            if traps > 0:
                lines.append(f"✓ {traps} trap(s)")
            
            self.structural_summary_label.set_text("\n".join(lines))
        else:
            self.structural_summary_label.set_text("○ No structural analysis performed")
    
    def _update_graph_preview(self, stats):
        """Update graph & network analysis preview (brief summary).
        
        Args:
            stats: statistics dict from summary
        """
        cycles = stats.get('cycles', 0)
        hubs = stats.get('hubs', 0)
        paths = stats.get('paths', 0)
        
        if cycles > 0 or hubs > 0 or paths > 0:
            lines = []
            
            if cycles > 0:
                lines.append(f"✓ {cycles} feedback cycle(s)")
            
            if hubs > 0:
                lines.append(f"✓ {hubs} hub node(s)")
            
            if paths > 0:
                lines.append(f"✓ {paths} critical path(s)")
            
            self.graph_summary_label.set_text("\n".join(lines))
        else:
            self.graph_summary_label.set_text("○ No graph analysis performed")
    
    def _update_behavioral_preview(self, stats):
        """Update behavioral analysis preview (brief summary).
        
        Args:
            stats: statistics dict from summary
        """
        properties = []
        
        # Check each behavioral property
        is_bounded = stats.get('is_bounded')
        if is_bounded is True:
            properties.append("✓ Bounded")
        elif is_bounded is False:
            properties.append("✗ Unbounded")
        elif is_bounded == 'timeout':
            properties.append("⏱️ Boundedness (timeout)")
        
        is_live = stats.get('is_live')
        if is_live is True:
            properties.append("✓ Live")
        elif is_live is False:
            properties.append("✗ Not live")
        elif is_live == 'timeout':
            properties.append("⏱️ Liveness (timeout)")
        
        is_deadlock_free = stats.get('is_deadlock_free')
        if is_deadlock_free is True:
            properties.append("✓ Deadlock-free")
        elif is_deadlock_free is False:
            properties.append("✗ Has deadlocks")
        elif is_deadlock_free == 'timeout':
            properties.append("⏱️ Deadlocks (timeout)")
        
        is_fair = stats.get('is_fair')
        if is_fair is True:
            properties.append("✓ Fair")
        elif is_fair is False:
            properties.append("✗ Not fair")
        elif is_fair == 'timeout':
            properties.append("⏱️ Fairness (timeout)")
        
        is_reachable = stats.get('is_reachable')
        if is_reachable is True:
            properties.append("✓ Reachable")
        elif is_reachable is False:
            properties.append("✗ Not reachable")
        elif is_reachable == 'timeout':
            properties.append("⏱️ Reachability (timeout)")
        
        if properties:
            self.behavioral_summary_label.set_text("\n".join(properties))
        else:
            self.behavioral_summary_label.set_text("○ No behavioral analysis performed")
    
    def _update_biological_preview(self, stats):
        """Update biological analysis preview (brief summary).
        
        Args:
            stats: statistics dict from summary
        """
        dep_score = stats.get('dependency_score')
        reg_patterns = stats.get('regulatory_patterns', 0)
        
        if dep_score is not None or reg_patterns > 0:
            lines = []
            
            if dep_score is not None:
                # Interpret dependency score
                if dep_score < 0.3:
                    interp = "low coupling"
                elif dep_score < 0.6:
                    interp = "moderate coupling"
                else:
                    interp = "high coupling"
                lines.append(f"✓ Dependency score: {dep_score:.2f} ({interp})")
            
            if reg_patterns > 0:
                lines.append(f"✓ {reg_patterns} regulatory pattern(s)")
            
            self.biological_summary_label.set_text("\n".join(lines))
        else:
            self.biological_summary_label.set_text("○ No biological analysis performed")
    
    def _show_placeholder(self):
        """Show placeholder when topology panel not connected."""
        self.status_label.set_markup("<b>ℹ️ Status:</b> No analyses performed yet")
        self.findings_label.set_text("Perform analyses in Topology Panel to see results here")
        
        self.structural_summary_label.set_text(
            "○ P-Invariants, T-Invariants, Siphons, Traps\n"
            "(Not computed)"
        )
        
        self.graph_summary_label.set_text(
            "○ Cycles, Paths, Hubs\n"
            "(Not computed)"
        )
        
        self.behavioral_summary_label.set_text(
            "○ Boundedness, Liveness, Deadlocks, Fairness, Reachability\n"
            "(Not computed)"
        )
        
        self.biological_summary_label.set_text(
            "○ Dependency & Coupling, Regulatory Structure\n"
            "(Not computed)"
        )
    
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
        except Exception as e:
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
