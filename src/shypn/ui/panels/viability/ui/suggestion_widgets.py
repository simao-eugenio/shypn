"""Widgets for displaying and interacting with fix suggestions."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from typing import Callable, Optional, List
from shypn.ui.panels.viability.investigation import Suggestion


class SuggestionWidget(Gtk.Box):
    """Widget for displaying a single suggestion with action buttons.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ 💡 Suggestion Action                            [Apply] │
    │    Expected impact: ...                      [Preview]  │
    │    Category: structural                                 │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, suggestion: Suggestion, 
                 on_apply: Optional[Callable[[Suggestion], None]] = None,
                 on_preview: Optional[Callable[[Suggestion], None]] = None):
        """Initialize suggestion widget.
        
        Args:
            suggestion: The suggestion to display
            on_apply: Callback when Apply button clicked
            on_preview: Callback when Preview button clicked
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        self.suggestion = suggestion
        self.on_apply = on_apply
        self.on_preview = on_preview
        
        # Add CSS classes for styling
        self.get_style_context().add_class('suggestion-widget')
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        # Main row: action text + buttons
        main_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Action label with emoji
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        emoji_label = Gtk.Label(label="💡")
        action_label = Gtk.Label(label=self.suggestion.action)
        action_label.set_line_wrap(True)
        action_label.set_max_width_chars(60)
        action_label.set_xalign(0)
        action_box.pack_start(emoji_label, False, False, 0)
        action_box.pack_start(action_label, True, True, 0)
        
        main_row.pack_start(action_box, True, True, 0)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        # Preview button (if callback provided)
        if self.on_preview:
            preview_btn = Gtk.Button(label="Preview")
            preview_btn.connect('clicked', self._on_preview_clicked)
            preview_btn.get_style_context().add_class('suggested-action')
            button_box.pack_start(preview_btn, False, False, 0)
        
        # Apply button (if callback provided)
        if self.on_apply:
            apply_btn = Gtk.Button(label="Apply")
            apply_btn.connect('clicked', self._on_apply_clicked)
            apply_btn.get_style_context().add_class('suggested-action')
            button_box.pack_start(apply_btn, False, False, 0)
        
        main_row.pack_end(button_box, False, False, 0)
        self.pack_start(main_row, False, False, 0)
        
        # Impact label (indented)
        if self.suggestion.impact:
            impact_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            impact_box.set_margin_start(20)
            impact_label = Gtk.Label(label=f"→ {self.suggestion.impact}")
            impact_label.set_line_wrap(True)
            impact_label.set_max_width_chars(60)
            impact_label.set_xalign(0)
            impact_label.get_style_context().add_class('dim-label')
            impact_box.pack_start(impact_label, True, True, 0)
            self.pack_start(impact_box, False, False, 0)
        
        # Category badge (small, indented)
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        category_box.set_margin_start(20)
        category_label = Gtk.Label(label=f"Category: {self.suggestion.category}")
        category_label.set_xalign(0)
        category_label.get_style_context().add_class('dim-label')
        category_box.pack_start(category_label, False, False, 0)
        self.pack_start(category_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(4)
        self.pack_start(separator, False, False, 0)
    
    def _on_apply_clicked(self, button):
        """Handle Apply button click."""
        if self.on_apply:
            self.on_apply(self.suggestion)
    
    def _on_preview_clicked(self, button):
        """Handle Preview button click."""
        if self.on_preview:
            self.on_preview(self.suggestion)


class SuggestionList(Gtk.Box):
    """Scrollable list of suggestions grouped by category.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Suggestions (12)                        [Apply All]     │
    ├─────────────────────────────────────────────────────────┤
    │ ▼ Structural (5)                                        │
    │   💡 Balance arc weights...                    [Apply]  │
    │   💡 Review source transition...               [Apply]  │
    │                                                          │
    │ ▼ Kinetic (4)                                           │
    │   💡 Query BRENDA for rate...                  [Apply]  │
    │   💡 Investigate enablement...                 [Apply]  │
    │                                                          │
    │ ▼ Biological (3)                                        │
    │   💡 Map compound to KEGG...                   [Apply]  │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, suggestions: List[Suggestion] = None,
                 on_apply: Optional[Callable[[Suggestion], None]] = None,
                 on_preview: Optional[Callable[[Suggestion], None]] = None,
                 on_apply_all: Optional[Callable[[List[Suggestion]], None]] = None):
        """Initialize suggestion list.
        
        Args:
            suggestions: List of suggestions to display
            on_apply: Callback when individual Apply clicked
            on_preview: Callback when Preview clicked
            on_apply_all: Callback when Apply All clicked
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.suggestions = suggestions or []
        self.on_apply = on_apply
        self.on_preview = on_preview
        self.on_apply_all = on_apply_all
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        # Header with count and Apply All button
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(8)
        header.set_margin_end(8)
        header.set_margin_top(8)
        header.set_margin_bottom(8)
        
        title_label = Gtk.Label(label=f"Suggestions ({len(self.suggestions)})")
        title_label.set_xalign(0)
        title_label.get_style_context().add_class('title')
        header.pack_start(title_label, True, True, 0)
        
        if self.on_apply_all and self.suggestions:
            apply_all_btn = Gtk.Button(label="Apply All")
            apply_all_btn.connect('clicked', self._on_apply_all_clicked)
            apply_all_btn.get_style_context().add_class('suggested-action')
            header.pack_end(apply_all_btn, False, False, 0)
        
        self.pack_start(header, False, False, 0)
        
        # Scrolled window for suggestions
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # Container for grouped suggestions
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Group suggestions by category
        from collections import defaultdict
        grouped = defaultdict(list)
        for suggestion in self.suggestions:
            grouped[suggestion.category].append(suggestion)
        
        # Create expandable section for each category
        for category, category_suggestions in sorted(grouped.items()):
            expander = self._create_category_expander(category, category_suggestions)
            container.pack_start(expander, False, False, 0)
        
        scrolled.add(container)
        self.pack_start(scrolled, True, True, 0)
    
    def _create_category_expander(self, category: str, suggestions: List[Suggestion]) -> Gtk.Expander:
        """Create expander for a category of suggestions."""
        expander = Gtk.Expander()
        expander.set_label(f"{category.capitalize()} ({len(suggestions)})")
        expander.set_expanded(True)
        expander.set_margin_start(8)
        expander.set_margin_end(8)
        expander.set_margin_top(4)
        expander.set_margin_bottom(4)
        
        # Container for suggestions in this category
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_start(12)
        
        for suggestion in suggestions:
            widget = SuggestionWidget(
                suggestion,
                on_apply=self.on_apply,
                on_preview=self.on_preview
            )
            box.pack_start(widget, False, False, 0)
        
        expander.add(box)
        return expander
    
    def _on_apply_all_clicked(self, button):
        """Handle Apply All button click."""
        if self.on_apply_all:
            self.on_apply_all(self.suggestions)
    
    def update_suggestions(self, suggestions: List[Suggestion]):
        """Update the displayed suggestions.
        
        Args:
            suggestions: New list of suggestions
        """
        self.suggestions = suggestions
        
        # Clear and rebuild
        for child in self.get_children():
            self.remove(child)
        
        self._build_ui()
        self.show_all()


class SuggestionAppliedBanner(Gtk.InfoBar):
    """Banner shown after suggestion is applied.
    
    Shows success message with undo option.
    """
    
    def __init__(self, suggestion: Suggestion, 
                 on_undo: Optional[Callable[[Suggestion], None]] = None):
        """Initialize banner.
        
        Args:
            suggestion: The applied suggestion
            on_undo: Callback when Undo clicked
        """
        super().__init__()
        
        self.suggestion = suggestion
        self.on_undo = on_undo
        
        self.set_message_type(Gtk.MessageType.INFO)
        self.set_show_close_button(True)
        
        # Content area
        content = self.get_content_area()
        label = Gtk.Label(label=f"✓ Applied: {suggestion.action}")
        label.set_line_wrap(True)
        label.set_max_width_chars(60)
        label.set_xalign(0)
        content.pack_start(label, True, True, 0)
        
        # Undo button
        if on_undo:
            self.add_button("Undo", Gtk.ResponseType.CANCEL)
            self.connect('response', self._on_response)
        
        self.show_all()
    
    def _on_response(self, info_bar, response_id):
        """Handle button response."""
        if response_id == Gtk.ResponseType.CANCEL and self.on_undo:
            self.on_undo(self.suggestion)
        
        # Close banner
        self.hide()
