#!/usr/bin/env python3
"""Thermodynamic Validation category for Report Panel.

Displays thermodynamic consistency validation results for reversible reactions.
Shows violations, warnings, and statistics from automated validation during SBML import.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseReportCategory


class ThermodynamicValidationCategory(BaseReportCategory):
    """Thermodynamic Validation report category.
    
    Displays validation results for reversible reactions:
    - Status indicator (✓/⚠️/❌/ℹ️)
    - Summary statistics (total, valid, warnings, violations)
    - Detailed lists of violations and warnings
    - Missing data notifications
    
    Data source: SimulationController.thermodynamic_results
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize thermodynamic validation category."""
        self.controller = None  # Set before super() since refresh() is called during init
        
        super().__init__(
            title="THERMODYNAMIC VALIDATION",
            project=project,
            model_canvas=model_canvas,
            expanded=True  # Expand by default to show important validation info
        )
    
    def _build_content(self):
        """Build thermodynamic validation content."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === STATUS BAR ===
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_markup("<b>ℹ️ Status:</b> No validation performed yet")
        box.pack_start(self.status_label, False, False, 0)
        
        # === SUMMARY STATISTICS ===
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
        self.summary_label.set_text("No reversible reactions found")
        summary_box.pack_start(self.summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # === VIOLATIONS (Expandable) ===
        self.violations_expander = Gtk.Expander(label="❌ Violations")
        self.violations_expander.set_expanded(True)  # Show violations by default
        
        violations_scroll = Gtk.ScrolledWindow()
        violations_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        violations_scroll.set_max_content_height(200)
        violations_scroll.set_propagate_natural_height(True)
        
        self.violations_label = Gtk.Label()
        self.violations_label.set_xalign(0)
        self.violations_label.set_yalign(0)
        self.violations_label.set_line_wrap(True)
        self.violations_label.set_selectable(True)
        self.violations_label.set_margin_start(12)
        self.violations_label.set_margin_end(12)
        self.violations_label.set_margin_top(6)
        self.violations_label.set_margin_bottom(6)
        self.violations_label.set_text("No violations")
        
        violations_scroll.add(self.violations_label)
        self.violations_expander.add(violations_scroll)
        box.pack_start(self.violations_expander, False, False, 0)
        
        # === WARNINGS (Expandable) ===
        self.warnings_expander = Gtk.Expander(label="⚠️  Warnings")
        self.warnings_expander.set_expanded(False)
        
        warnings_scroll = Gtk.ScrolledWindow()
        warnings_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        warnings_scroll.set_max_content_height(200)
        warnings_scroll.set_propagate_natural_height(True)
        
        self.warnings_label = Gtk.Label()
        self.warnings_label.set_xalign(0)
        self.warnings_label.set_yalign(0)
        self.warnings_label.set_line_wrap(True)
        self.warnings_label.set_selectable(True)
        self.warnings_label.set_margin_start(12)
        self.warnings_label.set_margin_end(12)
        self.warnings_label.set_margin_top(6)
        self.warnings_label.set_margin_bottom(6)
        self.warnings_label.set_text("No warnings")
        
        warnings_scroll.add(self.warnings_label)
        self.warnings_expander.add(warnings_scroll)
        box.pack_start(self.warnings_expander, False, False, 0)
        
        # === VALID TRANSITIONS (Expandable, collapsed by default) ===
        self.valid_expander = Gtk.Expander(label="✓ Valid Transitions")
        self.valid_expander.set_expanded(False)
        
        valid_scroll = Gtk.ScrolledWindow()
        valid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        valid_scroll.set_max_content_height(200)
        valid_scroll.set_propagate_natural_height(True)
        
        self.valid_label = Gtk.Label()
        self.valid_label.set_xalign(0)
        self.valid_label.set_yalign(0)
        self.valid_label.set_line_wrap(True)
        self.valid_label.set_selectable(True)
        self.valid_label.set_margin_start(12)
        self.valid_label.set_margin_end(12)
        self.valid_label.set_margin_top(6)
        self.valid_label.set_margin_bottom(6)
        self.valid_label.set_text("No valid transitions")
        
        valid_scroll.add(self.valid_label)
        self.valid_expander.add(valid_scroll)
        box.pack_start(self.valid_expander, False, False, 0)
        
        # === INSUFFICIENT DATA (Expandable, collapsed by default) ===
        self.insufficient_expander = Gtk.Expander(label="ℹ️  Insufficient Data")
        self.insufficient_expander.set_expanded(False)
        
        insufficient_scroll = Gtk.ScrolledWindow()
        insufficient_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        insufficient_scroll.set_max_content_height(200)
        insufficient_scroll.set_propagate_natural_height(True)
        
        self.insufficient_label = Gtk.Label()
        self.insufficient_label.set_xalign(0)
        self.insufficient_label.set_yalign(0)
        self.insufficient_label.set_line_wrap(True)
        self.insufficient_label.set_selectable(True)
        self.insufficient_label.set_margin_start(12)
        self.insufficient_label.set_margin_end(12)
        self.insufficient_label.set_margin_top(6)
        self.insufficient_label.set_margin_bottom(6)
        self.insufficient_label.set_text("No transitions with missing data")
        
        insufficient_scroll.add(self.insufficient_label)
        self.insufficient_expander.add(insufficient_scroll)
        box.pack_start(self.insufficient_expander, False, False, 0)
        
        # Initial refresh
        self.refresh()
        
        return box
    
    def refresh(self):
        """Refresh thermodynamic validation data from controller."""
        if not self.controller:
            self._show_no_controller()
            return
        
        # Get validation results from controller
        results = self.controller.thermodynamic_results
        
        if results is None:
            # No validation performed yet
            self._show_no_validation()
            return
        
        # Update content from results
        self._update_status(results)
        self._update_summary(results)
        self._update_violations(results.get('violations', []))
        self._update_warnings(results.get('warnings', []))
        self._update_valid(results.get('valid', []))
        self._update_insufficient(results.get('insufficient_data', []))
    
    def _show_no_controller(self):
        """Show placeholder when no controller available."""
        self.status_label.set_markup("<b>ℹ️ Status:</b> No simulation controller available")
        self.summary_label.set_text("Controller not initialized")
        self.violations_label.set_text("No data")
        self.warnings_label.set_text("No data")
        self.valid_label.set_text("No data")
        self.insufficient_label.set_text("No data")
    
    def _show_no_validation(self):
        """Show placeholder when validation not yet performed."""
        self.status_label.set_markup("<b>ℹ️ Status:</b> No validation performed yet")
        self.summary_label.set_text(
            "Thermodynamic validation runs automatically during SBML import.\n"
            "Import an SBML file with reversible reactions to see results."
        )
        self.violations_label.set_text("No validation performed")
        self.warnings_label.set_text("No validation performed")
        self.valid_label.set_text("No validation performed")
        self.insufficient_label.set_text("No validation performed")
    
    def _update_status(self, results):
        """Update status bar based on results."""
        summary = results.get('summary', {})
        total = summary.get('total', 0)
        violations = summary.get('violations', 0)
        warnings = summary.get('warnings', 0)
        valid = summary.get('valid', 0)
        
        if total == 0:
            status = "<b>ℹ️ Status:</b> No reversible reactions found"
        elif violations > 0:
            status = f"<b>❌ Status:</b> {violations} violation(s) detected"
        elif warnings > 0:
            status = f"<b>⚠️  Status:</b> {warnings} warning(s) - review recommended"
        elif valid == total:
            status = f"<b>✓ Status:</b> All {total} reversible reaction(s) valid"
        else:
            status = f"<b>ℹ️ Status:</b> {total} reversible reaction(s) checked"
        
        self.status_label.set_markup(status)
    
    def _update_summary(self, results):
        """Update summary statistics."""
        summary = results.get('summary', {})
        
        lines = [
            f"Total reversible reactions: {summary.get('total', 0)}",
            f"  ✓ Valid: {summary.get('valid', 0)}",
            f"  ⚠️  Warnings: {summary.get('warnings', 0)}",
            f"  ❌ Violations: {summary.get('violations', 0)}",
            f"  ℹ️  Insufficient data: {summary.get('insufficient_data', 0)}",
        ]
        
        self.summary_label.set_text('\n'.join(lines))
    
    def _update_violations(self, violations):
        """Update violations list."""
        if not violations:
            self.violations_label.set_text("No violations detected")
            self.violations_expander.set_label("❌ Violations (0)")
            return
        
        self.violations_expander.set_label(f"❌ Violations ({len(violations)})")
        
        lines = []
        for v in violations:
            transition = v.get('transition', 'Unknown')
            k_ratio = v.get('k_ratio', 'N/A')
            k_eq = v.get('k_eq', 'N/A')
            deviation = v.get('deviation', 'N/A')
            message = v.get('message', '')
            
            lines.append(f"• {transition}")
            lines.append(f"  k_f/k_r = {k_ratio:.2e}, K_eq = {k_eq:.2e}")
            lines.append(f"  Deviation: {deviation:.2f}")
            if message:
                lines.append(f"  {message}")
            lines.append("")  # Blank line between entries
        
        self.violations_label.set_text('\n'.join(lines))
    
    def _update_warnings(self, warnings):
        """Update warnings list."""
        if not warnings:
            self.warnings_label.set_text("No warnings")
            self.warnings_expander.set_label("⚠️  Warnings (0)")
            return
        
        self.warnings_expander.set_label(f"⚠️  Warnings ({len(warnings)})")
        
        lines = []
        for w in warnings:
            transition = w.get('transition', 'Unknown')
            k_ratio = w.get('k_ratio', 'N/A')
            k_eq = w.get('k_eq', 'N/A')
            deviation = w.get('deviation', 'N/A')
            message = w.get('message', '')
            
            lines.append(f"• {transition}")
            lines.append(f"  k_f/k_r = {k_ratio:.2e}, K_eq = {k_eq:.2e}")
            lines.append(f"  Deviation: {deviation:.2f}")
            if message:
                lines.append(f"  {message}")
            lines.append("")
        
        self.warnings_label.set_text('\n'.join(lines))
    
    def _update_valid(self, valid):
        """Update valid transitions list."""
        if not valid:
            self.valid_label.set_text("No valid transitions")
            self.valid_expander.set_label("✓ Valid Transitions (0)")
            return
        
        self.valid_expander.set_label(f"✓ Valid Transitions ({len(valid)})")
        
        lines = []
        for v in valid:
            transition = v.get('transition', 'Unknown')
            k_ratio = v.get('k_ratio', 'N/A')
            k_eq = v.get('k_eq', 'N/A')
            deviation = v.get('deviation', 'N/A')
            
            lines.append(f"• {transition}")
            if k_ratio != 'N/A' and k_eq != 'N/A':
                lines.append(f"  k_f/k_r = {k_ratio:.2e}, K_eq = {k_eq:.2e}, deviation = {deviation:.2f}")
            lines.append("")
        
        self.valid_label.set_text('\n'.join(lines))
    
    def _update_insufficient(self, insufficient):
        """Update insufficient data list."""
        if not insufficient:
            self.insufficient_label.set_text("No transitions with missing data")
            self.insufficient_expander.set_label("ℹ️  Insufficient Data (0)")
            return
        
        self.insufficient_expander.set_label(f"ℹ️  Insufficient Data ({len(insufficient)})")
        
        lines = []
        for item in insufficient:
            transition = item.get('transition', 'Unknown')
            status = item.get('status', 'unknown')
            message = item.get('message', 'No details')
            
            lines.append(f"• {transition}")
            lines.append(f"  Status: {status}")
            lines.append(f"  {message}")
            lines.append("")
        
        self.insufficient_label.set_text('\n'.join(lines))
    
    def set_controller(self, controller):
        """Set simulation controller reference.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
        self.refresh()
    
    def get_widget(self):
        """Get the widget for this category.
        
        Returns:
            CategoryFrame widget
        """
        return self.category_frame
