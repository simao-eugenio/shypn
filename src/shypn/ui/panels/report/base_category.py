#!/usr/bin/env python3
"""Base class for report categories.

All report categories inherit from BaseReportCategory and implement
the _build_content() method to populate their specific views.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.category_frame import CategoryFrame


class BaseReportCategory:
    """Base class for report category controllers.
    
    Each category is responsible for:
    1. Building its content view (TreeView, labels, plots, etc.)
    2. Populating data from project/model
    3. Refreshing when data changes
    4. Exporting its section to various formats
    
    Subclasses must implement:
    - _build_content(): Create and return the content widget
    - refresh(): Update data display
    """
    
    def __init__(self, title, project=None, model_canvas=None, expanded=False):
        """Initialize base category.
        
        Args:
            title: Category title displayed in expander
            project: Project instance (optional)
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
        """
        self.title = title
        self.project = project
        self.model_canvas = model_canvas
        self.expanded = expanded
        
        # Create category frame
        self.category_frame = CategoryFrame(
            title=self.title,
            expanded=self.expanded
        )
        
        # Build content (implemented by subclasses)
        content_widget = self._build_content()
        if content_widget:
            content_widget.show_all()  # Ensure all widgets are visible
            self.category_frame.set_content(content_widget)
    
    def _build_content(self):
        """Build and return the content widget.
        
        Must be implemented by subclasses.
        
        Returns:
            Gtk.Widget: The content to display in this category
        """
        raise NotImplementedError("Subclasses must implement _build_content()")
    
    def refresh(self):
        """Refresh the category content.
        
        Should be implemented by subclasses to update their data display.
        Called when project or model changes.
        """
        pass
    
    def set_project(self, project):
        """Set project and refresh.
        
        Args:
            project: Project instance
        """
        self.project = project
        self.refresh()
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas and refresh.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        self.refresh()
    
    def get_widget(self):
        """Get the category frame widget.
        
        Returns:
            CategoryFrame: The category widget to add to parent container
        """
        return self.category_frame
    
    def export_to_text(self):
        """Export category content as plain text.
        
        Returns:
            str: Text representation of this category
        """
        return f"# {self.title}\n\n(Export not implemented)\n"
    
    def export_to_html(self):
        """Export category content as HTML.
        
        Returns:
            str: HTML representation of this category
        """
        return f"<h2>{self.title}</h2>\n<p>(Export not implemented)</p>\n"
    
    def _create_label(self, text, bold=False, xalign=0):
        """Helper to create a label.
        
        Args:
            text: Label text
            bold: Whether to make text bold
            xalign: Horizontal alignment (0=left, 0.5=center, 1=right)
        
        Returns:
            Gtk.Label: Configured label
        """
        label = Gtk.Label()
        if bold:
            label.set_markup(f"<b>{text}</b>")
        else:
            label.set_text(text)
        label.set_xalign(xalign)
        return label
    
    def _create_scrolled_textview(self, text=""):
        """Helper to create a scrolled text view.
        
        Args:
            text: Initial text content
        
        Returns:
            tuple: (ScrolledWindow, TextView, TextBuffer)
        """
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        textview.set_left_margin(6)
        textview.set_right_margin(6)
        
        buffer = textview.get_buffer()
        buffer.set_text(text)
        
        scrolled.add(textview)
        
        return scrolled, textview, buffer
