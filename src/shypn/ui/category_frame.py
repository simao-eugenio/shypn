#!/usr/bin/env python3
"""Category Frame - Bordered expandable category widget.

Base class for tab-like bordered categories used in panels.
Provides expand/collapse functionality with optional inline buttons.

Author: Simão Eugénio
Date: 2025-10-22
"""

import sys
from typing import Optional, Callable, List, Tuple

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available in category_frame: {e}', file=sys.stderr)
    sys.exit(1)


class CategoryFrame(Gtk.Frame):
    """Bordered expandable category with tab-like appearance.
    
    Features:
    - Bordered frame for visual separation
    - Expand/collapse arrow
    - Optional inline action buttons in title bar
    - CSS-friendly widget structure
    - Wayland-safe implementation
    
    Example:
        category = CategoryFrame(
            title="Files",
            buttons=[
                ("＋", on_new_file),
                ("📁", on_new_folder),
                ("↻", on_refresh)
            ]
        )
        category.set_content(tree_view_widget)
        category.set_expanded(True)
    """
    
    def __init__(self, 
                 title: str,
                 buttons: Optional[List[Tuple[str, Callable]]] = None,
                 expanded: bool = False,
                 placeholder: bool = False,
                 on_collapse: Optional[Callable] = None):
        """Initialize category frame.
        
        Args:
            title: Category title text
            buttons: Optional list of (label, callback) tuples for inline buttons
            expanded: Initial expand state
            placeholder: If True, shows "TODO" message instead of content
            on_collapse: Optional callback function to call when collapsing
        """
        super().__init__()
        
        self.title = title
        self.expanded = expanded
        self.placeholder = placeholder
        self._buttons = buttons or []
        self._content_widget = None
        self._on_collapse_callback = on_collapse
        
        # Style
        self.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.set_margin_start(5)
        self.set_margin_end(5)
        self.set_margin_top(3)
        self.set_margin_bottom(3)
        
        # Main container
        self._main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        super().add(self._main_box)
        
        # Build UI
        self._build_title_bar()
        self._build_content_area()
        
        # Set initial state
        self._update_visibility()
    
    def _build_title_bar(self):
        """Build title bar with expand arrow and inline buttons."""
        # Title bar container (clickable)
        self._title_event_box = Gtk.EventBox()
        self._title_event_box.connect('button-press-event', self._on_title_clicked)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        title_box.set_margin_top(5)
        title_box.set_margin_bottom(5)
        title_box.set_margin_start(8)
        title_box.set_margin_end(8)
        self._title_event_box.add(title_box)
        
        # Expand/collapse arrow
        self._arrow_label = Gtk.Label()
        self._update_arrow()
        title_box.pack_start(self._arrow_label, False, False, 0)
        
        # Title label
        title_label = Gtk.Label(label=self.title)
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, True, True, 0)
        
        # Inline action buttons
        if self._buttons:
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            
            for label, callback in self._buttons:
                btn = Gtk.Button(label=label)
                btn.set_relief(Gtk.ReliefStyle.NONE)
                btn.connect('clicked', lambda b, cb=callback: cb())
                button_box.pack_start(btn, False, False, 0)
            
            title_box.pack_end(button_box, False, False, 0)
        
        self._main_box.pack_start(self._title_event_box, False, False, 0)
        
        # Separator line
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._main_box.pack_start(separator, False, False, 0)
    
    def _build_content_area(self):
        """Build content area container."""
        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._content_box.set_margin_top(5)
        self._content_box.set_margin_bottom(5)
        self._content_box.set_margin_start(5)
        self._content_box.set_margin_end(5)
        
        if self.placeholder:
            # Placeholder content
            placeholder_label = Gtk.Label()
            placeholder_label.set_markup("<i>TODO: Feature not yet implemented</i>")
            placeholder_label.set_margin_top(10)
            placeholder_label.set_margin_bottom(10)
            self._content_box.pack_start(placeholder_label, False, False, 0)
        
        # Pack content box to expand when category is expanded
        # Content widgets inside should request their minimum size
        self._main_box.pack_start(self._content_box, True, True, 0)
    
    def _update_arrow(self):
        """Update arrow direction based on expanded state."""
        arrow = "▼" if self.expanded else "▶"
        self._arrow_label.set_text(arrow)
    
    def _update_visibility(self):
        """Update content visibility based on expanded state."""
        self._content_box.set_visible(self.expanded)
        # CRITICAL: Prevent show_all() from overriding collapsed state
        # When collapsed, mark content box to be skipped by show_all()
        self._content_box.set_no_show_all(not self.expanded)
    
    def _on_title_clicked(self, widget, event):
        """Handle title bar click to toggle expand/collapse."""
        if event.button == 1:  # Left click
            self.toggle()
        return True
    
    def toggle(self):
        """Toggle expand/collapse state."""
        self.set_expanded(not self.expanded)
    
    def set_expanded(self, expanded: bool):
        """Set expand state.
        
        Args:
            expanded: True to expand, False to collapse
        """
        # Call collapse callback when collapsing (not when expanding)
        if not expanded and self.expanded and self._on_collapse_callback:
            print(f"[CATEGORY] Calling collapse callback for {self.title}", file=sys.stderr)
            self._on_collapse_callback()
        
        self.expanded = expanded
        self._update_arrow()
        self._update_visibility()
        
        # CRITICAL: Adjust expansion behavior
        # When expanded, allow content to fill space
        # When collapsed, take minimal space
        parent = self.get_parent()
        if parent and isinstance(parent, Gtk.Box):
            # Re-pack with appropriate expand/fill settings
            expand = self.expanded and not self.placeholder
            parent.child_set_property(self, 'expand', expand)
            parent.child_set_property(self, 'fill', expand)
    
    def set_content(self, widget: Gtk.Widget):
        """Set content widget.
        
        Args:
            widget: Widget to display in content area
        """
        # Remove existing content if any
        if self._content_widget:
            self._content_box.remove(self._content_widget)
        
        # Add new content
        self._content_widget = widget
        self._content_box.pack_start(widget, True, True, 0)
        
        # Show all if expanded
        if self.expanded:
            widget.show_all()
    
    def get_content(self) -> Optional[Gtk.Widget]:
        """Get current content widget.
        
        Returns:
            Current content widget or None
        """
        return self._content_widget
    
    def add(self, widget: Gtk.Widget):
        """Override add() to set content (GTK compatibility).
        
        Args:
            widget: Widget to add as content
        """
        self.set_content(widget)
