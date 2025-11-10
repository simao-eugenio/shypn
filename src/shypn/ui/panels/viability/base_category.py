#!/usr/bin/env python3
"""Base Category for Viability Panel.

Provides common infrastructure for all viability categories
(Structural, Biological, Kinetic, Diagnosis).

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, List, Dict, Any

from shypn.ui.category_frame import CategoryFrame


class BaseViabilityCategory:
    """Base class for viability analysis categories.
    
    Provides:
    - Expandable category frame (like topology categories)
    - Knowledge base access
    - Locality filtering support
    - Issue display infrastructure
    - Apply/Preview/Undo buttons
    
    Subclasses implement:
    - _build_content(): Create category-specific UI
    - _scan_issues(): Run category-specific analysis
    - _refresh(): Update UI with current data
    """
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize base category.
        
        Args:
            model_canvas: ModelCanvas instance for accessing model and KB
            expanded: Whether category starts expanded
        """
        self.model_canvas = model_canvas
        self.parent_panel = None  # Will be set by parent ViabilityPanel
        
        # Issue tracking
        self.current_issues = []
        self.selected_locality_id = None  # None = full model
        
        # Undo stack
        self.change_history = []
        
        # UI Components
        self.category_frame = None
        self.content_box = None
        self.issues_listbox = None
        self.scan_button = None
        self.undo_button = None
        
        # Build UI using CategoryFrame
        self._build_frame(expanded)
    
    def _build_frame(self, expanded):
        """Build category frame using CategoryFrame widget.
        
        Args:
            expanded: Whether to start expanded
        """
        # Use CategoryFrame for consistent styling with other panels
        self.category_frame = CategoryFrame(
            title=self.get_category_name(),
            expanded=expanded
        )
        
        # Main content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)
        
        # Build category-specific content
        self._build_content()
        
        # Set content in CategoryFrame
        self.category_frame.set_content(self.content_box)
    
    def get_widget(self):
        """Get the main widget for this category.
        
        Returns:
            CategoryFrame: The category frame
        """
        return self.category_frame
    
    def get_category_name(self):
        """Get category display name.
        
        Subclasses must override.
        
        Returns:
            str: Category name with emoji
        """
        raise NotImplementedError("Subclass must implement get_category_name()")
    
    def get_knowledge_base(self):
        """Get the knowledge base for the current model.
        
        Returns:
            ModelKnowledgeBase: The knowledge base, or None
        """
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            kb = self.model_canvas.get_current_knowledge_base()
            if kb:
                return kb
        return None
    
    def _build_content(self):
        """Build category-specific content.
        
        Subclasses must override to create their UI.
        """
        raise NotImplementedError("Subclass must implement _build_content()")
    
    def _on_expansion_changed(self, expander, param):
        """Handle expander state change.
        
        Args:
            expander: Gtk.Expander that changed
            param: Parameter spec (not used)
        """
        if expander.get_expanded():
            # Category was expanded - refresh data
            GLib.idle_add(self._refresh)
    
    def _refresh(self):
        """Refresh category content.
        
        Subclasses should override to update their UI.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        return False
    
    def _scan_issues(self):
        """Scan for issues in this category.
        
        Subclasses must override to implement category-specific scanning.
        
        Returns:
            List[Issue]: Detected issues
        """
        raise NotImplementedError("Subclass must implement _scan_issues()")
    
    def _create_action_buttons(self):
        """Create common action buttons (Scan, Undo, etc.).
        
        Returns:
            Gtk.Box: Button box
        """
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.START)
        
        # Scan button
        self.scan_button = Gtk.Button(label="SCAN FOR ISSUES")
        self.scan_button.connect('clicked', self._on_scan_clicked)
        button_box.pack_start(self.scan_button, False, False, 0)
        
        # Undo button
        self.undo_button = Gtk.Button(label="UNDO LAST")
        self.undo_button.set_sensitive(False)  # Initially disabled
        self.undo_button.connect('clicked', self._on_undo_clicked)
        button_box.pack_start(self.undo_button, False, False, 0)
        
        # Clear button
        clear_button = Gtk.Button(label="CLEAR ALL")
        clear_button.connect('clicked', self._on_clear_clicked)
        button_box.pack_start(clear_button, False, False, 0)
        
        return button_box
    
    def _on_scan_clicked(self, button):
        """Handle scan button click.
        
        Args:
            button: Button that was clicked
        """
        # Clear previous issues
        self.current_issues = []
        
        # Scan for new issues
        issues = self._scan_issues()
        
        if issues:
            self.current_issues = issues
            self._display_issues(issues)
            print(f"[{self.get_category_name()}] Found {len(issues)} issues")
        else:
            self._show_no_issues_message()
            print(f"[{self.get_category_name()}] No issues found")
    
    def _on_undo_clicked(self, button):
        """Handle undo button click.
        
        Args:
            button: Button that was clicked
        """
        if self.change_history:
            change = self.change_history.pop()
            self._apply_undo(change)
            
            # Disable undo button if history is empty
            if not self.change_history:
                self.undo_button.set_sensitive(False)
            
            print(f"[{self.get_category_name()}] Undid change: {change}")
    
    def _on_clear_clicked(self, button):
        """Handle clear button click.
        
        Args:
            button: Button that was clicked
        """
        self.current_issues = []
        if self.issues_listbox:
            # Clear all rows
            for child in self.issues_listbox.get_children():
                self.issues_listbox.remove(child)
    
    def _display_issues(self, issues):
        """Display issues in the UI.
        
        Args:
            issues: List of Issue objects
        """
        # To be implemented by subclasses or use default ListBox display
        pass
    
    def _show_no_issues_message(self):
        """Show message when no issues are found."""
        if self.issues_listbox:
            # Clear existing content
            for child in self.issues_listbox.get_children():
                self.issues_listbox.remove(child)
            
            # Add "no issues" message
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="NO ISSUES DETECTED")
            label.set_margin_start(12)
            label.set_margin_end(12)
            label.set_margin_top(12)
            label.set_margin_bottom(12)
            row.add(label)
            self.issues_listbox.add(row)
            self.issues_listbox.show_all()
    
    def _apply_undo(self, change):
        """Apply an undo operation.
        
        Args:
            change: Change object to undo
        """
        # To be implemented by subclasses
        print(f"[{self.get_category_name()}] Undo not implemented yet")
    
    def _record_change(self, change):
        """Record a change to the undo history.
        
        Args:
            change: Change object to record
        """
        self.change_history.append(change)
        self.undo_button.set_sensitive(True)
    
    def set_locality(self, locality_id):
        """Set the locality filter for this category.
        
        Args:
            locality_id: Locality ID, or None for full model
        """
        self.selected_locality_id = locality_id
        # Refresh if category is expanded
        if self.category_frame and self.category_frame.is_expanded():
            GLib.idle_add(self._refresh)
