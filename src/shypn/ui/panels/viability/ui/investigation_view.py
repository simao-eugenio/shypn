"""View for displaying single locality investigation results."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from typing import Optional, Callable
from shypn.ui.panels.viability.investigation import LocalityInvestigation, Suggestion
from shypn.ui.panels.viability.ui.issue_widgets import IssueList, IssueSummary
from shypn.ui.panels.viability.ui.suggestion_widgets import SuggestionList


class InvestigationView(Gtk.Box):
    """View for displaying single locality investigation results.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Investigation: T1 (Glycolysis Step 1)                   │
    │ ─────────────────────────────────────────────────────────│
    │ Locality Overview                                        │
    │   Inputs: P1 (Glucose), P2 (ATP)                        │
    │   Outputs: P3 (G6P), P4 (ADP)                           │
    │   Status: 🔴 3 errors, 🟡 2 warnings                    │
    │ ─────────────────────────────────────────────────────────│
    │ [Issues Tab] [Suggestions Tab]                           │
    │ ┌─────────────────────────────────────────────────────┐ │
    │ │ (Issue or Suggestion content based on active tab)   │ │
    │ │                                                      │ │
    │ └─────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, investigation: Optional[LocalityInvestigation] = None,
                 on_apply: Optional[Callable[[Suggestion], None]] = None,
                 on_preview: Optional[Callable[[Suggestion], None]] = None):
        """Initialize investigation view.
        
        Args:
            investigation: The investigation to display
            on_apply: Callback when suggestion is applied
            on_preview: Callback when suggestion preview requested
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.investigation = investigation
        self.on_apply = on_apply
        self.on_preview = on_preview
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        if not self.investigation:
            # Empty state
            self._show_empty_state()
            return
        
        # Header with transition info
        header = self._create_header()
        self.pack_start(header, False, False, 0)
        
        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep1, False, False, 0)
        
        # Locality overview
        overview = self._create_overview()
        self.pack_start(overview, False, False, 0)
        
        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep2, False, False, 0)
        
        # Notebook for Issues/Suggestions tabs
        notebook = self._create_notebook()
        self.pack_start(notebook, True, True, 0)
    
    def _show_empty_state(self):
        """Show empty state when no investigation."""
        label = Gtk.Label(label="No investigation selected")
        label.set_margin_top(50)
        label.set_margin_bottom(50)
        label.get_style_context().add_class('dim-label')
        self.pack_start(label, True, True, 0)
    
    def _create_header(self) -> Gtk.Box:
        """Create header with transition info."""
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.set_margin_top(12)
        header.set_margin_bottom(8)
        
        # Transition ID and label
        transition = self.investigation.locality.transition
        title_text = f"Investigation: {transition.id}"
        if hasattr(transition, 'label') and transition.label:
            title_text += f" ({transition.label})"
        
        title_label = Gtk.Label(label=title_text)
        title_label.set_xalign(0)
        title_label.get_style_context().add_class('title')
        header.pack_start(title_label, False, False, 0)
        
        return header
    
    def _create_overview(self) -> Gtk.Box:
        """Create locality overview section."""
        overview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        overview.set_margin_start(12)
        overview.set_margin_end(12)
        overview.set_margin_top(8)
        overview.set_margin_bottom(8)
        
        # Section title
        title = Gtk.Label(label="Locality Overview")
        title.set_xalign(0)
        title.get_style_context().add_class('heading')
        overview.pack_start(title, False, False, 0)
        
        # Inputs
        locality = self.investigation.locality
        inputs_text = self._format_places_list(locality.input_places, "Inputs")
        inputs_label = Gtk.Label(label=inputs_text)
        inputs_label.set_xalign(0)
        inputs_label.set_line_wrap(True)
        inputs_label.set_max_width_chars(70)
        overview.pack_start(inputs_label, False, False, 0)
        
        # Outputs
        outputs_text = self._format_places_list(locality.output_places, "Outputs")
        outputs_label = Gtk.Label(label=outputs_text)
        outputs_label.set_xalign(0)
        outputs_label.set_line_wrap(True)
        outputs_label.set_max_width_chars(70)
        overview.pack_start(outputs_label, False, False, 0)
        
        # Status summary
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_label = Gtk.Label(label="Status:")
        status_label.set_xalign(0)
        status_box.pack_start(status_label, False, False, 0)
        
        summary = IssueSummary(self.investigation.issues)
        status_box.pack_start(summary, True, True, 0)
        
        overview.pack_start(status_box, False, False, 0)
        
        return overview
    
    def _format_places_list(self, places: list, label: str) -> str:
        """Format list of places for display."""
        if not places:
            return f"{label}: (none)"
        
        place_strs = []
        for place in places[:5]:  # Limit to first 5
            place_str = place.id
            if hasattr(place, 'label') and place.label:
                place_str += f" ({place.label})"
            place_strs.append(place_str)
        
        result = f"{label}: {', '.join(place_strs)}"
        if len(places) > 5:
            result += f" ... and {len(places) - 5} more"
        
        return result
    
    def _create_notebook(self) -> Gtk.Notebook:
        """Create notebook with Issues and Suggestions tabs."""
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        
        # Issues tab
        issues_label = Gtk.Label(label="Issues")
        issues_view = IssueList(self.investigation.issues)
        notebook.append_page(issues_view, issues_label)
        
        # Suggestions tab
        suggestions_label = Gtk.Label(label="Suggestions")
        suggestions_view = SuggestionList(
            self.investigation.suggestions,
            on_apply=self.on_apply,
            on_preview=self.on_preview
        )
        notebook.append_page(suggestions_view, suggestions_label)
        
        return notebook
    
    def update_investigation(self, investigation: LocalityInvestigation):
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


class LocalityOverviewCard(Gtk.Frame):
    """Compact card showing locality overview.
    
    Used in subnet view to show multiple localities.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ T1: Glycolysis Step 1                                   │
    │ → 2 inputs, 2 outputs                                   │
    │ Status: 🔴 3 errors, 🟡 2 warnings          [Expand →]  │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, investigation: LocalityInvestigation,
                 on_expand: Optional[Callable[[LocalityInvestigation], None]] = None):
        """Initialize overview card.
        
        Args:
            investigation: The investigation to summarize
            on_expand: Callback when Expand clicked
        """
        super().__init__()
        
        self.investigation = investigation
        self.on_expand = on_expand
        
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        # Transition name
        transition = self.investigation.locality.transition
        title_text = transition.id
        if hasattr(transition, 'label') and transition.label:
            title_text += f": {transition.label}"
        
        title_label = Gtk.Label(label=title_text)
        title_label.set_xalign(0)
        title_label.get_style_context().add_class('heading')
        box.pack_start(title_label, False, False, 0)
        
        # I/O counts
        locality = self.investigation.locality
        io_text = f"→ {len(locality.input_places)} inputs, {len(locality.output_places)} outputs"
        io_label = Gtk.Label(label=io_text)
        io_label.set_xalign(0)
        io_label.get_style_context().add_class('dim-label')
        box.pack_start(io_label, False, False, 0)
        
        # Status and expand button
        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        status_label = Gtk.Label(label="Status:")
        status_label.set_xalign(0)
        status_row.pack_start(status_label, False, False, 0)
        
        summary = IssueSummary(self.investigation.issues)
        status_row.pack_start(summary, True, True, 0)
        
        if self.on_expand:
            expand_btn = Gtk.Button(label="Expand →")
            expand_btn.connect('clicked', self._on_expand_clicked)
            expand_btn.get_style_context().add_class('flat')
            status_row.pack_end(expand_btn, False, False, 0)
        
        box.pack_start(status_row, False, False, 0)
        
        self.add(box)
    
    def _on_expand_clicked(self, button):
        """Handle Expand button click."""
        if self.on_expand:
            self.on_expand(self.investigation)
