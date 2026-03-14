#!/usr/bin/env python3
"""Enrichment History Category - Phase 2 KB Integration.

Displays parameter enrichment history with filtering, rating, and undo capabilities.
Shows all parameter applications tracked in the KB, allowing users to:
1. View history of all enrichments (SABIO-RK, BRENDA, Heuristic)
2. Filter by source, pathway, date range, rating
3. Rate parameter applications
4. Undo unwanted enrichments
5. View enrichment details (confidence, metadata, etc.)

Author: Simão Eugénio
Date: 2025-11-16
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Pango

from .base_pathway_category import BasePathwayCategory
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
from shypn.crossfetch.tracking.parameter_tracker import ParameterTracker

# Rating dialog for manual rating
try:
    from shypn.ui.dialogs.parameter_rating_dialog import ParameterRatingDialog
    RATING_DIALOG_AVAILABLE = True
except ImportError:
    RATING_DIALOG_AVAILABLE = False


class EnrichmentHistoryCategory(BasePathwayCategory):
    """Enrichment History category for Pathway Operations panel.
    
    Displays searchable/filterable history of all parameter enrichments
    with rating and undo capabilities.
    
    UI Layout:
    ┌─────────────────────────────────────┐
    │ Filters: [Source▾] [Rating▾] [Date]│
    ├─────────────────────────────────────┤
    │ TreeView: History List              │
    │  - Transition | Source | Rating     │
    │  - Date | Confidence | Params       │
    ├─────────────────────────────────────┤
    │ Detail Panel:                       │
    │  Parameters: Km, Vmax, etc.        │
    │  Metadata: Organism, EC, etc.      │
    ├─────────────────────────────────────┤
    │ [Rate] [Undo] [Refresh]            │
    └─────────────────────────────────────┘
    """
    
    def __init__(self, model_canvas_loader=None, expanded=False):
        """Initialize Enrichment History category.
        
        Args:
            model_canvas_loader: Model canvas loader for transition access
            expanded: Whether category starts expanded
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize KB components
        try:
            self.db = HeuristicDatabase()
            self.tracker = ParameterTracker(self.db)
            self.kb_available = True
        except Exception as e:
            self.logger.error(f"KB initialization failed: {e}")
            self.db = None
            self.tracker = None
            self.kb_available = False
        
        # Initialize UI components (before super().__init__)
        self.history_store = None
        self.history_tree = None
        self.detail_text = None
        self.filter_source_combo = None
        self.filter_rating_combo = None
        self.filter_date_combo = None
        self.undo_button = None
        self.rate_button = None
        
        # Current selection
        self.selected_param_id = None
        self.selected_record = None
        
        super().__init__(
            category_name="ENRICHMENT HISTORY",
            expanded=expanded
        )
        
        if model_canvas_loader:
            self.set_model_canvas(model_canvas_loader)
        
        # Load initial history
        if self.kb_available:
            self._refresh_history()
    
    def _build_content(self):
        """Build the enrichment history view."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.set_margin_top(6)
        main_box.set_margin_bottom(6)
        main_box.set_margin_start(6)
        main_box.set_margin_end(6)
        
        if not self.kb_available:
            # Show error if KB not available
            error_label = Gtk.Label()
            error_label.set_markup(
                '<span foreground="red">⚠ Knowledge Base not available</span>'
            )
            main_box.pack_start(error_label, False, False, 0)
            return main_box
        
        # Filters section
        filters_box = self._build_filters()
        main_box.pack_start(filters_box, False, False, 0)
        
        # History TreeView (scrollable)
        history_scroll = self._build_history_tree()
        main_box.pack_start(history_scroll, True, True, 0)
        
        # Detail panel
        detail_frame = self._build_detail_panel()
        main_box.pack_start(detail_frame, False, False, 0)
        
        # Action buttons
        action_box = self._build_action_buttons()
        main_box.pack_start(action_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Show all widgets (required for content to be visible)
        main_box.show_all()
        
        return main_box
    
    def _build_filters(self):
        """Build filter controls."""
        filters_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Source filter
        filters_box.pack_start(Gtk.Label(label="Source:"), False, False, 0)
        self.filter_source_combo = Gtk.ComboBoxText()
        self.filter_source_combo.append_text("All Sources")
        self.filter_source_combo.append_text("SABIO-RK")
        self.filter_source_combo.append_text("BRENDA")
        self.filter_source_combo.append_text("Heuristic")
        self.filter_source_combo.set_active(0)
        self.filter_source_combo.connect("changed", self._on_filter_changed)
        filters_box.pack_start(self.filter_source_combo, False, False, 0)
        
        # Rating filter
        filters_box.pack_start(Gtk.Label(label="Rating:"), False, False, 0)
        self.filter_rating_combo = Gtk.ComboBoxText()
        self.filter_rating_combo.append_text("All Ratings")
        self.filter_rating_combo.append_text("👍 Good (1)")
        self.filter_rating_combo.append_text("😐 Neutral (0)")
        self.filter_rating_combo.append_text("👎 Poor (-1)")
        self.filter_rating_combo.append_text("⭐ Unrated")
        self.filter_rating_combo.set_active(0)
        self.filter_rating_combo.connect("changed", self._on_filter_changed)
        filters_box.pack_start(self.filter_rating_combo, False, False, 0)
        
        # Date filter
        filters_box.pack_start(Gtk.Label(label="Date:"), False, False, 0)
        self.filter_date_combo = Gtk.ComboBoxText()
        self.filter_date_combo.append_text("All Time")
        self.filter_date_combo.append_text("Last 24 hours")
        self.filter_date_combo.append_text("Last 7 days")
        self.filter_date_combo.append_text("Last 30 days")
        self.filter_date_combo.set_active(0)
        self.filter_date_combo.connect("changed", self._on_filter_changed)
        filters_box.pack_start(self.filter_date_combo, False, False, 0)
        
        return filters_box
    
    def _build_history_tree(self):
        """Build history TreeView."""
        # Create list store: param_id, transition_id, source, rating, date, confidence, params_str
        self.history_store = Gtk.ListStore(
            int,     # 0: param_id (hidden)
            str,     # 1: transition_id
            str,     # 2: source
            str,     # 3: rating (emoji)
            str,     # 4: date
            str,     # 5: confidence
            str      # 6: parameters summary
        )
        
        self.history_tree = Gtk.TreeView(model=self.history_store)
        self.history_tree.set_headers_visible(True)
        self.history_tree.get_selection().connect("changed", self._on_selection_changed)
        
        # Columns
        columns = [
            ("Transition", 1, 100),
            ("Source", 2, 80),
            ("Rating", 3, 60),
            ("Date", 4, 100),
            ("Confidence", 5, 80),
            ("Parameters", 6, 150)
        ]
        
        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            if title == "Parameters":
                column.set_expand(True)
            self.history_tree.append_column(column)
        
        # Scrollable container
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(200)
        scroll.add(self.history_tree)
        
        return scroll
    
    def _build_detail_panel(self):
        """Build detail panel showing selected enrichment details."""
        frame = Gtk.Frame(label="Details")
        frame.set_margin_top(6)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(120)
        
        self.detail_text = Gtk.TextView()
        self.detail_text.set_editable(False)
        self.detail_text.set_wrap_mode(Pango.WrapMode.WORD)
        self.detail_text.set_left_margin(6)
        self.detail_text.set_right_margin(6)
        self.detail_text.get_buffer().set_text("Select an enrichment to view details")
        
        scroll.add(self.detail_text)
        frame.add(scroll)
        
        return frame
    
    def _build_action_buttons(self):
        """Build action buttons."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_top(6)
        
        # Rate button
        self.rate_button = Gtk.Button(label="Rate")
        self.rate_button.set_sensitive(False)
        self.rate_button.connect("clicked", self._on_rate_clicked)
        button_box.pack_start(self.rate_button, False, False, 0)
        
        # Undo button
        self.undo_button = Gtk.Button(label="Undo")
        self.undo_button.set_sensitive(False)
        self.undo_button.connect("clicked", self._on_undo_clicked)
        button_box.pack_start(self.undo_button, False, False, 0)
        
        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda _: self._refresh_history())
        button_box.pack_start(refresh_button, False, False, 0)
        
        return button_box
    
    def _refresh_history(self):
        """Refresh history from database with current filters."""
        if not self.kb_available or not self.history_store:
            return
        
        self._show_progress("Loading history...")
        
        # Get filter values
        source_idx = self.filter_source_combo.get_active()
        rating_idx = self.filter_rating_combo.get_active()
        date_idx = self.filter_date_combo.get_active()
        
        # Map to filter parameters
        source = None
        if source_idx == 1:
            source = "SABIO-RK"
        elif source_idx == 2:
            source = "BRENDA"
        elif source_idx == 3:
            source = "Heuristic"
        
        rating = None
        if rating_idx == 1:
            rating = 1  # Good
        elif rating_idx == 2:
            rating = 0  # Neutral
        elif rating_idx == 3:
            rating = -1  # Poor
        # Note: "Unrated" (idx 4) would need special handling
        
        date_range = None
        if date_idx > 0:
            now = datetime.now()
            if date_idx == 1:  # Last 24 hours
                start = now - timedelta(days=1)
            elif date_idx == 2:  # Last 7 days
                start = now - timedelta(days=7)
            elif date_idx == 3:  # Last 30 days
                start = now - timedelta(days=30)
            date_range = (start.isoformat(), now.isoformat())
        
        # Query history
        try:
            history = self.tracker.get_filtered_history(
                source=source,
                rating=rating,
                date_range=date_range,
                include_undone=False,
                limit=500
            )
            
            # Populate tree
            self.history_store.clear()
            for record in history:
                param_id = record['parameter_id']
                transition_id = record.get('transition_id', 'N/A')
                src = record['source']
                
                # Format rating
                user_rating = record.get('user_rating')
                if user_rating == 1:
                    rating_str = "👍"
                elif user_rating == 0:
                    rating_str = "😐"
                elif user_rating == -1:
                    rating_str = "👎"
                else:
                    rating_str = "—"
                
                # Format date
                date_str = record.get('applied_date', record.get('import_date', 'N/A'))
                if date_str and len(date_str) > 10:
                    date_str = date_str[:10]  # Just YYYY-MM-DD
                
                # Format confidence
                conf = record.get('confidence_score', 0.0)
                conf_str = f"{conf:.2f}"
                
                # Format parameters
                params = record.get('parameters', {})
                if isinstance(params, dict):
                    params_list = [f"{k}={v}" for k, v in params.items() if v is not None]
                    params_str = ", ".join(params_list[:3])  # Show first 3
                    if len(params_list) > 3:
                        params_str += "..."
                else:
                    params_str = str(params)[:50]
                
                self.history_store.append([
                    param_id,
                    transition_id,
                    src,
                    rating_str,
                    date_str,
                    conf_str,
                    params_str
                ])
            
            count = len(history)
            self._show_success(f"Loaded {count} enrichment(s)")
            
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
            self._show_error(f"Failed to load history: {e}")
    
    def _on_filter_changed(self, widget):
        """Handle filter change."""
        self._refresh_history()
    
    def _on_selection_changed(self, selection):
        """Handle history selection change."""
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            self.selected_param_id = None
            self.selected_record = None
            self.rate_button.set_sensitive(False)
            self.undo_button.set_sensitive(False)
            self.detail_text.get_buffer().set_text("Select an enrichment to view details")
            return
        
        # Get selected param_id
        self.selected_param_id = model[tree_iter][0]
        
        # Load full record details
        try:
            history = self.tracker.get_filtered_history(limit=1)
            # Find record with matching param_id
            self.selected_record = None
            for record in history:
                if record['parameter_id'] == self.selected_param_id:
                    self.selected_record = record
                    break
            
            if not self.selected_record:
                # Try querying by transition
                transition_id = model[tree_iter][1]
                history = self.tracker.get_transition_history(transition_id, limit=50)
                for record in history:
                    if record['parameter_id'] == self.selected_param_id:
                        self.selected_record = record
                        break
            
            if self.selected_record:
                self._show_details(self.selected_record)
                self.rate_button.set_sensitive(True)
                self.undo_button.set_sensitive(True)
            else:
                self.detail_text.get_buffer().set_text("Could not load details")
                self.rate_button.set_sensitive(False)
                self.undo_button.set_sensitive(False)
                
        except Exception as e:
            self.logger.error(f"Failed to load details: {e}")
            self.detail_text.get_buffer().set_text(f"Error loading details: {e}")
            self.rate_button.set_sensitive(False)
            self.undo_button.set_sensitive(False)
    
    def _show_details(self, record: Dict[str, Any]):
        """Show enrichment details in detail panel."""
        lines = []
        lines.append(f"Transition: {record.get('transition_id', 'N/A')}")
        lines.append(f"Pathway: {record.get('pathway_name', 'N/A')} ({record.get('pathway_id', 'N/A')})")
        lines.append(f"Source: {record['source']}")
        lines.append(f"Confidence: {record.get('confidence_score', 0.0):.2f}")
        
        # Rating
        user_rating = record.get('user_rating')
        if user_rating == 1:
            lines.append("Rating: 👍 Good")
        elif user_rating == 0:
            lines.append("Rating: 😐 Neutral")
        elif user_rating == -1:
            lines.append("Rating: 👎 Poor")
        else:
            lines.append("Rating: Not rated")
        
        # Notes
        notes = record.get('notes')
        if notes:
            lines.append(f"Notes: {notes}")
        
        lines.append("")
        lines.append("Parameters:")
        params = record.get('parameters', {})
        if isinstance(params, dict):
            for key, value in params.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")
        else:
            lines.append(f"  {params}")
        
        lines.append("")
        lines.append("Metadata:")
        lines.append(f"  Organism: {record.get('organism', 'N/A')}")
        lines.append(f"  EC Number: {record.get('ec_number', 'N/A')}")
        lines.append(f"  Applied: {record.get('applied_date', record.get('import_date', 'N/A'))}")
        lines.append(f"  Usage Count: {record.get('usage_count', 0)}")
        
        self.detail_text.get_buffer().set_text("\n".join(lines))
    
    def _on_rate_clicked(self, button):
        """Handle rate button click."""
        if not self.selected_param_id or not RATING_DIALOG_AVAILABLE:
            return
        
        try:
            record = self.selected_record
            if not record:
                return
            
            # Create rating dialog
            dialog = ParameterRatingDialog(
                parent=None,
                transition_name=record.get('transition_id', 'Unknown'),
                parameters=list(record.get('parameters', {}).keys()),
                source=record['source']
            )
            
            # Show dialog
            feedback = dialog.run_and_get_feedback()
            
            if feedback:
                rating = feedback['rating']
                comment = feedback.get('comment', '')
                
                # Update rating
                success = self.tracker.update_rating(
                    parameter_id=self.selected_param_id,
                    rating=rating,
                    comment=comment
                )
                
                if success:
                    self._show_success("Rating updated")
                    self._refresh_history()
                else:
                    self._show_error("Failed to update rating")
            
        except Exception as e:
            self.logger.error(f"Rating failed: {e}")
            self._show_error(f"Rating failed: {e}")
    
    def _on_undo_clicked(self, button):
        """Handle undo button click."""
        if not self.selected_param_id:
            return
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Undo Parameter Application?"
        )
        dialog.format_secondary_text(
            "This will mark the enrichment as undone. "
            "The transition will need to be manually reverted in the canvas."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Perform undo
        try:
            result = self.tracker.undo_application(self.selected_param_id)
            
            if result['success']:
                self._show_success(result['message'])
                
                # Show previous parameters if available
                if result.get('previous_parameters'):
                    prev = result['previous_parameters']
                    msg = "Previous parameters:\n" + "".join(
                        f"  {key}: {value}\n" for key, value in prev.items()
                    )
                    
                    info_dialog = Gtk.MessageDialog(
                        transient_for=None,
                        flags=0,
                        message_type=Gtk.MessageType.INFO,
                        buttons=Gtk.ButtonsType.OK,
                        text="Undo Complete"
                    )
                    info_dialog.format_secondary_text(msg)
                    info_dialog.run()
                    info_dialog.destroy()
                
                self._refresh_history()
            else:
                self._show_error(result['message'])
                
        except Exception as e:
            self.logger.error(f"Undo failed: {e}")
            self._show_error(f"Undo failed: {e}")    
    def on_tab_switched(self):
        """Called when the user switches to a different model tab.
        
        Updates the enrichment history to reflect the currently active model:
        - Refreshes history list for the new model
        - Updates button states
        - Clears any selection from previous model
        """
        self.logger.debug("Tab switched, refreshing enrichment history")
        
        # Clear current selection
        self.selected_param_id = None
        self.selected_record = None
        self.undo_button.set_sensitive(False)
        self.rate_button.set_sensitive(False)
        self.detail_text.get_buffer().set_text("No selection")
        
        # Get current document
        document = None
        if self.model_canvas:
            try:
                if hasattr(self.model_canvas, 'get_current_model'):
                    canvas_manager = self.model_canvas.get_current_model()
                else:
                    canvas_manager = self.model_canvas
                
                if canvas_manager and hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
            except Exception as e:
                self.logger.warning(f"Could not get document on tab switch: {e}")
        
        # Refresh history for new model
        if document and self.kb_available:
            self._refresh_history()
        else:
            # No document or KB not available - clear history
            self.history_store.clear()
            if not self.kb_available:
                self.status_label.set_markup('<span size="small">Knowledge base not available</span>')
            else:
                self.status_label.set_markup('<span size="small">No model loaded</span>')