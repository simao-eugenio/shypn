#!/usr/bin/env python3
"""Biological Inference Category.

Provides biochemical semantic inference using:
- KEGG compound metadata
- KEGG reaction metadata
- Stoichiometry from reactions
- Conservation laws (P-invariants)

Suggests:
- Arc weights (stoichiometry)
- Compound mappings
- Conservation law compliance
- Basal concentrations

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseViabilityCategory


class BiologicalCategory(BaseViabilityCategory):
    """Biological inference category.
    
    Uses KEGG metadata to suggest semantic fixes.
    """
    
    def get_category_name(self):
        """Get category display name.
        
        Returns:
            str: Category name
        """
        return "Biological Inference"
    
    def _build_content(self):
        """Build biological category content."""
        # Status section
        status_frame = Gtk.Frame(label="📊 Current Knowledge")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(12)
        status_box.set_margin_bottom(12)
        
        self.status_label = Gtk.Label(label="Click 'Scan Semantics' to analyze")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)
        
        status_frame.add(status_box)
        self.content_box.pack_start(status_frame, False, False, 0)
        
        # Action buttons
        button_box = self._create_action_buttons()
        # Customize scan button label
        self.scan_button.set_label("Scan Semantics")
        self.content_box.pack_start(button_box, False, False, 0)
        
        # Issues list
        issues_frame = Gtk.Frame(label="Issues Detected")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        self.issues_listbox = Gtk.ListBox()
        self.issues_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.issues_listbox)
        
        issues_frame.add(scrolled)
        self.content_box.pack_start(issues_frame, True, True, 0)
    
    def _scan_issues(self):
        """Scan for biological/semantic issues.
        
        Returns:
            List[Issue]: Detected biological issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            print("[Biological] No knowledge base available")
            return []
        
        issues = []
        
        # Update status
        self.status_label.set_markup(
            f"<b>KB Status:</b>\n"
            f"  • Compounds: {len(kb.compounds)}\n"
            f"  • Reactions: {len(kb.reactions)}\n"
            f"  • Pathway: {kb.pathway_info.name if kb.pathway_info else 'None'}"
        )
        
        # Scan for unmapped compounds
        unmapped_count = sum(1 for p in kb.places.values() if p.compound_id is None)
        if unmapped_count > 0:
            issues.append({
                'severity': 'warning',
                'title': f'{unmapped_count} places without compound mapping',
                'description': 'Places not linked to KEGG compounds',
                'element_id': 'unmapped_compounds',
                'suggestions': []
            })
        
        # Scan for stoichiometry mismatches (simplified)
        for arc_id, arc in kb.arcs.items():
            if arc.stoichiometry and arc.current_weight != arc.stoichiometry:
                issues.append({
                    'severity': 'warning',
                    'title': f'Stoichiometry mismatch in arc {arc_id}',
                    'description': f'Current: {arc.current_weight}, Expected: {arc.stoichiometry}',
                    'element_id': arc_id,
                    'suggestions': []
                })
        
        return issues
    
    def _display_issues(self, issues):
        """Display biological issues in the UI.
        
        Args:
            issues: List of issue dictionaries
        """
        # Clear existing issues
        for child in self.issues_listbox.get_children():
            self.issues_listbox.remove(child)
        
        if not issues:
            self._show_no_issues_message()
            return
        
        # Add each issue as a row
        for issue in issues:
            row = self._create_issue_row(issue)
            self.issues_listbox.add(row)
        
        self.issues_listbox.show_all()
    
    def _create_issue_row(self, issue):
        """Create a row widget for an issue.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            Gtk.ListBoxRow: Row widget
        """
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        
        # Main box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Title with severity icon
        severity_icons = {
            'critical': '🔴',
            'warning': '⚠️',
            'suggestion': '💡'
        }
        icon = severity_icons.get(issue['severity'], '•')
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{icon} {issue['title']}</b>")
        title_label.set_halign(Gtk.Align.START)
        box.pack_start(title_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label=issue['description'])
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_line_wrap(True)
        box.pack_start(desc_label, False, False, 0)
        
        row.add(box)
        return row
    
    def _refresh(self):
        """Refresh biological category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.expander.get_expanded():
            self._on_scan_clicked(None)
        return False
