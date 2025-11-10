#!/usr/bin/env python3
"""Viability Panel - Main panel UI.

Displays model viability issues and (future) fix suggestions.
Follows the same architecture as Topology and Report panels.

Author: Simão Eugénio
Date: November 9, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from .diagnosis_view import DiagnosisView


class ViabilityPanel(Gtk.Box):
    """Viability Panel - Intelligent Model Repair Assistant.
    
    Phase 1: Displays model issues (structural, semantic, behavioral)
    Future: Suggests and applies fixes
    
    Architecture:
    - Follows Topology/Report panel patterns
    - Minimal logic here (business logic in src/shypn/viability/)
    - Wayland-safe operations
    """
    
    def __init__(self, model=None, model_canvas=None):
        """Initialize viability panel.
        
        Args:
            model: ShypnModel instance (optional, can be set later)
            model_canvas: ModelCanvas instance for accessing current model
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.model = model
        self.model_canvas = model_canvas
        self.topology_panel = None  # Will be set via set_topology_panel()
        
        # Build UI
        self._build_header()
        self._build_content()
    
    def _build_header(self):
        """Build panel header (matches REPORT, TOPOLOGY, etc.)."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        # Title label (left)
        header_label = Gtk.Label()
        header_label.set_markup("<b>VIABILITY</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button (right)
        self.float_button = Gtk.ToggleButton()
        float_icon = Gtk.Image.new_from_icon_name('window-new', Gtk.IconSize.BUTTON)
        self.float_button.set_image(float_icon)
        self.float_button.set_tooltip_text('Float panel in separate window')
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
    
    def _build_content(self):
        """Build main content area."""
        # Scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        
        # === DIAGNOSIS SECTION ===
        diagnosis_expander = Gtk.Expander(label="🔍 Diagnosis")
        diagnosis_expander.set_expanded(True)
        
        diagnosis_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        diagnosis_box.set_margin_start(12)
        diagnosis_box.set_margin_end(12)
        diagnosis_box.set_margin_top(6)
        diagnosis_box.set_margin_bottom(6)
        
        # Scan button
        scan_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.scan_button = Gtk.Button(label="🔄 Scan for Issues")
        self.scan_button.connect('clicked', self._on_scan_clicked)
        scan_button_box.pack_start(self.scan_button, False, False, 0)
        diagnosis_box.pack_start(scan_button_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_markup("<i>Click 'Scan' to analyze model</i>")
        diagnosis_box.pack_start(self.status_label, False, False, 0)
        
        # Diagnosis view (tree of issues)
        self.diagnosis_view = DiagnosisView()
        diagnosis_box.pack_start(self.diagnosis_view, True, True, 0)
        
        diagnosis_expander.add(diagnosis_box)
        content_box.pack_start(diagnosis_expander, True, True, 0)
        
        # === SUGGESTIONS SECTION (Future - Phase 2) ===
        suggestions_expander = Gtk.Expander(label="💡 Suggested Fixes")
        suggestions_expander.set_expanded(False)
        suggestions_expander.set_sensitive(False)  # Disabled for Phase 1
        
        suggestions_placeholder = Gtk.Label()
        suggestions_placeholder.set_text("Fix suggestions will appear here (Phase 2)")
        suggestions_placeholder.set_margin_start(12)
        suggestions_placeholder.set_margin_end(12)
        suggestions_placeholder.set_margin_top(6)
        suggestions_placeholder.set_margin_bottom(6)
        suggestions_expander.add(suggestions_placeholder)
        
        content_box.pack_start(suggestions_expander, False, False, 0)
        
        # === OPTIONS SECTION (Future - Phase 5) ===
        options_expander = Gtk.Expander(label="⚙️ Options")
        options_expander.set_expanded(False)
        options_expander.set_sensitive(False)  # Disabled for Phase 1
        
        options_placeholder = Gtk.Label()
        options_placeholder.set_text("Repair options will appear here (Phase 5)")
        options_placeholder.set_margin_start(12)
        options_placeholder.set_margin_end(12)
        options_placeholder.set_margin_top(6)
        options_placeholder.set_margin_bottom(6)
        options_expander.add(options_placeholder)
        
        content_box.pack_start(options_expander, False, False, 0)
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
    
    def set_topology_panel(self, topology_panel):
        """Set topology panel reference for reading analysis results.
        
        Args:
            topology_panel: TopologyPanel instance
        """
        self.topology_panel = topology_panel
        print(f"[VIABILITY] Connected to Topology Panel")
    
    def _on_scan_clicked(self, button):
        """Handle scan button click - analyze model for issues."""
        if not self.topology_panel:
            self.status_label.set_markup("<b>⚠️ Warning:</b> Topology Panel not connected")
            return
        
        # Get topology analysis results
        try:
            summary = self.topology_panel.generate_summary_for_report_panel()
            issues = self._parse_topology_summary(summary)
            
            # Display issues
            self.diagnosis_view.display_issues(issues)
            
            # Update status
            critical_count = sum(1 for i in issues if i['severity'] == 'critical')
            warning_count = sum(1 for i in issues if i['severity'] == 'warning')
            
            if critical_count > 0:
                status_icon = '🔴'
                status_text = f"<b>{status_icon} Found {critical_count} critical issue(s), {warning_count} warning(s)</b>"
            elif warning_count > 0:
                status_icon = '🟡'
                status_text = f"<b>{status_icon} Found {warning_count} warning(s)</b>"
            else:
                status_icon = '✓'
                status_text = f"<b>{status_icon} Model is viable - no issues detected</b>"
            
            self.status_label.set_markup(status_text)
            
        except Exception as e:
            self.status_label.set_markup(f"<b>❌ Error:</b> {str(e)}")
            print(f"[VIABILITY ERROR] Failed to scan: {e}")
            import traceback
            traceback.print_exc()
    
    def _parse_topology_summary(self, summary):
        """Parse topology summary into list of issues.
        
        Args:
            summary: Dict from TopologyPanel.generate_summary_for_report_panel()
        
        Returns:
            List of issue dicts with keys: severity, type, description, id
        """
        issues = []
        status = summary.get('status', 'unknown')
        stats = summary.get('statistics', {})
        warnings = summary.get('warnings', [])
        
        # Status-based issues
        if status == 'not_analyzed':
            issues.append({
                'severity': 'info',
                'type': 'not_analyzed',
                'description': 'No topology analysis performed yet',
                'id': 'status'
            })
            return issues
        
        # Check for dead transitions
        # (This is a simplified parser - Phase 2 will have full engine)
        
        # Behavioral issues
        is_live = stats.get('is_live')
        if is_live is False:
            issues.append({
                'severity': 'critical',
                'type': 'not_live',
                'description': 'Model is not live - some transitions may never fire',
                'id': 'liveness'
            })
        
        has_deadlock = stats.get('has_deadlock')
        if has_deadlock is True:
            issues.append({
                'severity': 'critical',
                'type': 'deadlock',
                'description': 'Model can reach deadlock state',
                'id': 'deadlock'
            })
        
        is_bounded = stats.get('is_bounded')
        if is_bounded is False:
            issues.append({
                'severity': 'warning',
                'type': 'unbounded',
                'description': 'Model is unbounded - some places may grow indefinitely',
                'id': 'boundedness'
            })
        
        # Structural issues
        siphons = stats.get('siphons', {})
        if isinstance(siphons, dict):
            blocked = siphons.get('blocked', [])
            if blocked:
                issues.append({
                    'severity': 'warning',
                    'type': 'blocked_siphon',
                    'description': f'Blocked siphons detected: {len(blocked)}',
                    'id': 'siphons'
                })
        
        # Add warnings from summary
        for warning in warnings:
            issues.append({
                'severity': 'warning',
                'type': 'topology_warning',
                'description': warning,
                'id': f'warn_{len(issues)}'
            })
        
        # If no issues found and analysis was complete
        if not issues and status == 'complete':
            issues.append({
                'severity': 'info',
                'type': 'viable',
                'description': '✓ Model appears viable - all basic checks passed',
                'id': 'viable'
            })
        
        return issues
    
    def refresh(self):
        """Refresh panel (can be called when model changes)."""
        # Clear current display
        self.diagnosis_view.clear()
        self.status_label.set_markup("<i>Click 'Scan' to analyze model</i>")
