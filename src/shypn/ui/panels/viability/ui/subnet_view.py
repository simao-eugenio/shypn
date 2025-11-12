"""View for displaying subnet investigation results with multi-level analysis."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from typing import Optional, Callable
from shypn.ui.panels.viability.investigation import (
    SubnetInvestigation, LocalityInvestigation, Suggestion, 
    BoundaryAnalysis, ConservationAnalysis
)
from shypn.ui.panels.viability.ui.issue_widgets import IssueList, IssueSummary
from shypn.ui.panels.viability.ui.suggestion_widgets import SuggestionList
from shypn.ui.panels.viability.ui.investigation_view import LocalityOverviewCard


class SubnetView(Gtk.Box):
    """View for displaying subnet investigation with multi-level analysis.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Subnet Investigation: 4 Localities                      │
    │ ─────────────────────────────────────────────────────────│
    │ [Level 1: Localities] [Level 2: Dependencies]           │
    │ [Level 3: Boundaries] [Level 4: Conservation]           │
    │ ┌─────────────────────────────────────────────────────┐ │
    │ │ (Content based on active level)                     │ │
    │ │                                                      │ │
    │ └─────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, investigation: Optional[SubnetInvestigation] = None,
                 on_apply: Optional[Callable[[Suggestion], None]] = None,
                 on_preview: Optional[Callable[[Suggestion], None]] = None,
                 on_expand_locality: Optional[Callable[[LocalityInvestigation], None]] = None):
        """Initialize subnet view.
        
        Args:
            investigation: The subnet investigation to display
            on_apply: Callback when suggestion is applied
            on_preview: Callback when suggestion preview requested
            on_expand_locality: Callback when locality should be expanded
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.investigation = investigation
        self.on_apply = on_apply
        self.on_preview = on_preview
        self.on_expand_locality = on_expand_locality
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        if not self.investigation:
            # Empty state
            self._show_empty_state()
            return
        
        # Header
        header = self._create_header()
        self.pack_start(header, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep, False, False, 0)
        
        # Stack for multi-level views
        stack = self._create_stack()
        
        # Stack switcher (level selector)
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)
        switcher.set_halign(Gtk.Align.CENTER)
        switcher.set_margin_top(8)
        switcher.set_margin_bottom(8)
        self.pack_start(switcher, False, False, 0)
        
        # Stack content
        self.pack_start(stack, True, True, 0)
    
    def _show_empty_state(self):
        """Show empty state when no investigation."""
        label = Gtk.Label(label="No subnet investigation selected")
        label.set_margin_top(50)
        label.set_margin_bottom(50)
        label.get_style_context().add_class('dim-label')
        self.pack_start(label, True, True, 0)
    
    def _create_header(self) -> Gtk.Box:
        """Create header with subnet info."""
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.set_margin_top(12)
        header.set_margin_bottom(8)
        
        # Title
        locality_count = len(self.investigation.locality_investigations)
        title_text = f"Subnet Investigation: {locality_count} Localities"
        
        title_label = Gtk.Label(label=title_text)
        title_label.set_xalign(0)
        title_label.get_style_context().add_class('title')
        header.pack_start(title_label, False, False, 0)
        
        # Overall status
        all_issues = self._get_all_issues()
        if all_issues:
            status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            status_label = Gtk.Label(label="Overall Status:")
            status_label.set_xalign(0)
            status_box.pack_start(status_label, False, False, 0)
            
            summary = IssueSummary(all_issues)
            status_box.pack_start(summary, True, True, 0)
            
            header.pack_start(status_box, False, False, 0)
        
        return header
    
    def _get_all_issues(self):
        """Get all issues from all levels."""
        all_issues = []
        
        # Level 1: Locality issues
        for locality_inv in self.investigation.locality_investigations:
            all_issues.extend(locality_inv.issues)
        
        # Level 2: Dependency issues
        all_issues.extend(self.investigation.dependency_issues)
        
        # Level 3: Boundary issues
        all_issues.extend(self.investigation.boundary_issues)
        
        # Level 4: Conservation issues
        all_issues.extend(self.investigation.conservation_issues)
        
        return all_issues
    
    def _create_stack(self) -> Gtk.Stack:
        """Create stack with views for each analysis level."""
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(200)
        
        # Level 1: Localities
        localities_view = self._create_localities_view()
        stack.add_titled(localities_view, "localities", "Level 1: Localities")
        
        # Level 2: Dependencies
        dependencies_view = self._create_dependencies_view()
        stack.add_titled(dependencies_view, "dependencies", "Level 2: Dependencies")
        
        # Level 3: Boundaries
        boundaries_view = self._create_boundaries_view()
        stack.add_titled(boundaries_view, "boundaries", "Level 3: Boundaries")
        
        # Level 4: Conservation
        conservation_view = self._create_conservation_view()
        stack.add_titled(conservation_view, "conservation", "Level 4: Conservation")
        
        return stack
    
    def _create_localities_view(self) -> Gtk.ScrolledWindow:
        """Create view for Level 1: Individual localities."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Description
        desc = Gtk.Label(
            label="Individual transition analysis: structural, biological, and kinetic issues."
        )
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        desc.get_style_context().add_class('dim-label')
        box.pack_start(desc, False, False, 0)
        
        # Locality cards
        for locality_inv in self.investigation.locality_investigations:
            card = LocalityOverviewCard(
                locality_inv,
                on_expand=self.on_expand_locality
            )
            box.pack_start(card, False, False, 0)
        
        scrolled.add(box)
        return scrolled
    
    def _create_dependencies_view(self) -> Gtk.Box:
        """Create view for Level 2: Dependencies."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Description
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        desc_box.set_margin_start(12)
        desc_box.set_margin_end(12)
        desc_box.set_margin_top(12)
        desc_box.set_margin_bottom(12)
        
        desc = Gtk.Label(
            label="Inter-locality flow analysis: imbalances, bottlenecks, and cascading issues."
        )
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        desc.get_style_context().add_class('dim-label')
        desc_box.pack_start(desc, False, False, 0)
        
        container.pack_start(desc_box, False, False, 0)
        
        # Notebook for Issues/Suggestions
        notebook = Gtk.Notebook()
        
        # Issues tab
        issues_label = Gtk.Label(label="Issues")
        issues_view = IssueList(self.investigation.dependency_issues)
        notebook.append_page(issues_view, issues_label)
        
        # Suggestions tab
        suggestions_label = Gtk.Label(label="Suggestions")
        suggestions_view = SuggestionList(
            self.investigation.dependency_suggestions,
            on_apply=self.on_apply,
            on_preview=self.on_preview
        )
        notebook.append_page(suggestions_view, suggestions_label)
        
        container.pack_start(notebook, True, True, 0)
        return container
    
    def _create_boundaries_view(self) -> Gtk.Box:
        """Create view for Level 3: Boundaries."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Description and summary
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        top_box.set_margin_start(12)
        top_box.set_margin_end(12)
        top_box.set_margin_top(12)
        top_box.set_margin_bottom(12)
        
        desc = Gtk.Label(
            label="Subnet boundary analysis: accumulation, depletion, and flow balance."
        )
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        desc.get_style_context().add_class('dim-label')
        top_box.pack_start(desc, False, False, 0)
        
        # Boundary summary (if available)
        if self.investigation.boundary_analysis:
            summary_frame = self._create_boundary_summary()
            top_box.pack_start(summary_frame, False, False, 0)
        
        container.pack_start(top_box, False, False, 0)
        
        # Notebook for Issues/Suggestions
        notebook = Gtk.Notebook()
        
        # Issues tab
        issues_label = Gtk.Label(label="Issues")
        issues_view = IssueList(self.investigation.boundary_issues)
        notebook.append_page(issues_view, issues_label)
        
        # Suggestions tab
        suggestions_label = Gtk.Label(label="Suggestions")
        suggestions_view = SuggestionList(
            self.investigation.boundary_suggestions,
            on_apply=self.on_apply,
            on_preview=self.on_preview
        )
        notebook.append_page(suggestions_view, suggestions_label)
        
        container.pack_start(notebook, True, True, 0)
        return container
    
    def _create_boundary_summary(self) -> Gtk.Frame:
        """Create boundary analysis summary card."""
        frame = Gtk.Frame()
        frame.set_label("Boundary Overview")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(12)
        grid.set_margin_start(8)
        grid.set_margin_end(8)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        
        analysis = self.investigation.boundary_analysis
        
        # Inputs
        inputs_label = Gtk.Label(label="Inputs:")
        inputs_label.set_xalign(0)
        inputs_label.get_style_context().add_class('dim-label')
        grid.attach(inputs_label, 0, 0, 1, 1)
        
        inputs_text = ', '.join(analysis.inputs[:5]) if analysis.inputs else '(none)'
        if len(analysis.inputs) > 5:
            inputs_text += f' ... and {len(analysis.inputs) - 5} more'
        inputs_value = Gtk.Label(label=inputs_text)
        inputs_value.set_xalign(0)
        inputs_value.set_line_wrap(True)
        grid.attach(inputs_value, 1, 0, 1, 1)
        
        # Outputs
        outputs_label = Gtk.Label(label="Outputs:")
        outputs_label.set_xalign(0)
        outputs_label.get_style_context().add_class('dim-label')
        grid.attach(outputs_label, 0, 1, 1, 1)
        
        outputs_text = ', '.join(analysis.outputs[:5]) if analysis.outputs else '(none)'
        if len(analysis.outputs) > 5:
            outputs_text += f' ... and {len(analysis.outputs) - 5} more'
        outputs_value = Gtk.Label(label=outputs_text)
        outputs_value.set_xalign(0)
        outputs_value.set_line_wrap(True)
        grid.attach(outputs_value, 1, 1, 1, 1)
        
        frame.add(grid)
        return frame
    
    def _create_conservation_view(self) -> Gtk.Box:
        """Create view for Level 4: Conservation."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Description and summary
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        top_box.set_margin_start(12)
        top_box.set_margin_end(12)
        top_box.set_margin_top(12)
        top_box.set_margin_bottom(12)
        
        desc = Gtk.Label(
            label="Conservation law validation: P-invariants, mass balance, and material leaks."
        )
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        desc.get_style_context().add_class('dim-label')
        top_box.pack_start(desc, False, False, 0)
        
        # Conservation summary (if available)
        if self.investigation.conservation_analysis:
            summary_frame = self._create_conservation_summary()
            top_box.pack_start(summary_frame, False, False, 0)
        
        container.pack_start(top_box, False, False, 0)
        
        # Notebook for Issues/Suggestions
        notebook = Gtk.Notebook()
        
        # Issues tab
        issues_label = Gtk.Label(label="Issues")
        issues_view = IssueList(self.investigation.conservation_issues)
        notebook.append_page(issues_view, issues_label)
        
        # Suggestions tab
        suggestions_label = Gtk.Label(label="Suggestions")
        suggestions_view = SuggestionList(
            self.investigation.conservation_suggestions,
            on_apply=self.on_apply,
            on_preview=self.on_preview
        )
        notebook.append_page(suggestions_view, suggestions_label)
        
        container.pack_start(notebook, True, True, 0)
        return container
    
    def _create_conservation_summary(self) -> Gtk.Frame:
        """Create conservation analysis summary card."""
        frame = Gtk.Frame()
        frame.set_label("Conservation Overview")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(12)
        grid.set_margin_start(8)
        grid.set_margin_end(8)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        
        analysis = self.investigation.conservation_analysis
        
        # P-invariants
        inv_label = Gtk.Label(label="P-Invariants:")
        inv_label.set_xalign(0)
        inv_label.get_style_context().add_class('dim-label')
        grid.attach(inv_label, 0, 0, 1, 1)
        
        inv_count = len(analysis.invariants_violated)
        inv_status = f"{inv_count} violated" if inv_count > 0 else "All preserved"
        inv_value = Gtk.Label(label=inv_status)
        inv_value.set_xalign(0)
        if inv_count > 0:
            inv_value.get_style_context().add_class('error')
        grid.attach(inv_value, 1, 0, 1, 1)
        
        # Mass balance
        mass_label = Gtk.Label(label="Mass Balance:")
        mass_label.set_xalign(0)
        mass_label.get_style_context().add_class('dim-label')
        grid.attach(mass_label, 0, 1, 1, 1)
        
        mass_count = len(analysis.mass_balance_issues)
        mass_status = f"{mass_count} issues" if mass_count > 0 else "Balanced"
        mass_value = Gtk.Label(label=mass_status)
        mass_value.set_xalign(0)
        if mass_count > 0:
            mass_value.get_style_context().add_class('warning')
        grid.attach(mass_value, 1, 1, 1, 1)
        
        frame.add(grid)
        return frame
    
    def update_investigation(self, investigation: SubnetInvestigation):
        """Update the displayed investigation.
        
        Args:
            investigation: New investigation to display
        """
        self.investigation = investigation
        
        # Clear and rebuild
        for child in self.get_children():
            self.remove(child)
        
        self._build_ui()
        self.show_all()
    
    def refresh(self):
        """Refresh the display with current investigation data."""
        if self.investigation:
            self.update_investigation(self.investigation)
