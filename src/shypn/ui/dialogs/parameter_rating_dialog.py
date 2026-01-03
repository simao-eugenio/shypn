#!/usr/bin/env python3
"""Parameter rating dialog for user feedback on enrichment quality.

Allows users to rate parameter applications from SABIO-RK, BRENDA, or Heuristic
sources. Ratings are stored in the Knowledge Base for future confidence scoring
and learning.

Author: Simão Eugénio
Date: 2025-11-16
"""
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Pango, Pango
from typing import Optional, Dict, Any


class ParameterRatingDialog(Gtk.Dialog):
    """Dialog for rating applied parameters.
    
    Presents parameter details and allows user to provide feedback via:
    - Thumbs up/down rating (-1, 0, 1)
    - Optional text comment
    
    Ratings are stored in KB via ParameterTracker.
    
    Attributes:
        parameter_info: Dict with parameter details
        rating: User's rating (-1, 0, 1)
        comment: Optional user comment
    """
    
    def __init__(self, 
                 parent: Optional[Gtk.Window],
                 parameter_info: Dict[str, Any]):
        """Initialize rating dialog.
        
        Args:
            parent: Parent window for modal behavior
            parameter_info: Dict containing:
                - transition_id: Transition identifier
                - parameters: Dict of applied parameters
                - source: 'SABIO-RK', 'BRENDA', or 'Heuristic'
                - ec_number: EC number (optional)
                - organism: Organism name (optional)
                - confidence_score: Confidence (0.0-1.0)
        """
        super().__init__(
            title="Rate Parameter Application",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        self.parameter_info = parameter_info
        self.rating = 0  # Default: neutral
        self.comment = ""
        
        # Dialog buttons
        self.add_button("Skip", Gtk.ResponseType.CANCEL)
        self.add_button("Submit", Gtk.ResponseType.OK)
        
        # Set dialog size
        self.set_default_size(500, 400)
        
        # Build UI
        self._build_ui()
        
        self.show_all()
    
    def _build_ui(self):
        """Build dialog UI."""
        content = self.get_content_area()
        content.set_border_width(12)
        
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.pack_start(vbox, True, True, 0)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<big><b>Rate Parameter Application</b></big>")
        title_label.set_halign(Gtk.Align.START)
        vbox.pack_start(title_label, False, False, 0)
        
        # Instruction
        instruction = Gtk.Label()
        instruction.set_markup(
            "<i>Help improve parameter suggestions by rating this application:</i>"
        )
        instruction.set_halign(Gtk.Align.START)
        instruction.set_line_wrap(True)
        vbox.pack_start(instruction, False, False, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 0)
        
        # Parameter details frame
        details_frame = Gtk.Frame(label="Parameter Details")
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        details_box.set_border_width(12)
        details_frame.add(details_box)
        vbox.pack_start(details_frame, False, False, 0)
        
        # Source
        source = self.parameter_info.get('source', 'Unknown')
        source_label = Gtk.Label()
        source_label.set_markup(f"<b>Source:</b> {source}")
        source_label.set_halign(Gtk.Align.START)
        details_box.pack_start(source_label, False, False, 0)
        
        # EC number and organism (if available)
        ec_number = self.parameter_info.get('ec_number')
        if ec_number:
            ec_label = Gtk.Label()
            ec_label.set_markup(f"<b>EC Number:</b> {ec_number}")
            ec_label.set_halign(Gtk.Align.START)
            details_box.pack_start(ec_label, False, False, 0)
        
        organism = self.parameter_info.get('organism')
        if organism:
            org_label = Gtk.Label()
            org_label.set_markup(f"<b>Organism:</b> {organism}")
            org_label.set_halign(Gtk.Align.START)
            details_box.pack_start(org_label, False, False, 0)
        
        # Parameters
        parameters = self.parameter_info.get('parameters', {})
        if parameters:
            params_label = Gtk.Label()
            params_label.set_markup("<b>Applied Parameters:</b>")
            params_label.set_halign(Gtk.Align.START)
            details_box.pack_start(params_label, False, False, 0)
            
            # Create scrollable text view for parameters
            params_scroll = Gtk.ScrolledWindow()
            params_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            params_scroll.set_min_content_height(80)
            
            params_textview = Gtk.TextView()
            params_textview.set_editable(False)
            params_textview.set_cursor_visible(False)
            params_textview.set_wrap_mode(Pango.WrapMode.WORD)
            params_textview.set_left_margin(8)
            params_textview.set_right_margin(8)
            params_textview.set_top_margin(4)
            params_textview.set_bottom_margin(4)
            
            # Format parameters
            params_text = []
            for key, value in parameters.items():
                if isinstance(value, float):
                    params_text.append(f"{key}: {value:.4g}")
                else:
                    params_text.append(f"{key}: {value}")
            
            params_textview.get_buffer().set_text("\n".join(params_text))
            params_scroll.add(params_textview)
            details_box.pack_start(params_scroll, True, True, 0)
        
        # Confidence score
        confidence = self.parameter_info.get('confidence_score', 0.0)
        confidence_label = Gtk.Label()
        confidence_label.set_markup(f"<b>Confidence:</b> {confidence:.0%}")
        confidence_label.set_halign(Gtk.Align.START)
        details_box.pack_start(confidence_label, False, False, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 0)
        
        # Rating section
        rating_frame = Gtk.Frame(label="Your Rating")
        rating_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        rating_box.set_border_width(12)
        rating_frame.add(rating_box)
        vbox.pack_start(rating_frame, False, False, 0)
        
        # Rating question
        rating_question = Gtk.Label()
        rating_question.set_markup(
            "<b>How well do these parameters work for this transition?</b>"
        )
        rating_question.set_halign(Gtk.Align.START)
        rating_box.pack_start(rating_question, False, False, 0)
        
        # Rating buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        button_box.set_halign(Gtk.Align.CENTER)
        rating_box.pack_start(button_box, False, False, 0)
        
        # Thumbs down button
        self.thumbs_down_btn = Gtk.Button(label="👎 Poor")
        self.thumbs_down_btn.set_size_request(120, 50)
        self.thumbs_down_btn.connect('clicked', self._on_thumbs_down)
        button_box.pack_start(self.thumbs_down_btn, False, False, 0)
        
        # Neutral button
        self.neutral_btn = Gtk.Button(label="🤷 Unsure")
        self.neutral_btn.set_size_request(120, 50)
        self.neutral_btn.connect('clicked', self._on_neutral)
        button_box.pack_start(self.neutral_btn, False, False, 0)
        
        # Thumbs up button
        self.thumbs_up_btn = Gtk.Button(label="👍 Good")
        self.thumbs_up_btn.set_size_request(120, 50)
        self.thumbs_up_btn.connect('clicked', self._on_thumbs_up)
        button_box.pack_start(self.thumbs_up_btn, False, False, 0)
        
        # Highlight neutral (default)
        self._update_button_styles()
        
        # Optional comment
        comment_label = Gtk.Label()
        comment_label.set_markup("<b>Optional comment:</b>")
        comment_label.set_halign(Gtk.Align.START)
        rating_box.pack_start(comment_label, False, False, 0)
        
        # Comment text view
        comment_scroll = Gtk.ScrolledWindow()
        comment_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        comment_scroll.set_min_content_height(60)
        
        self.comment_textview = Gtk.TextView()
        self.comment_textview.set_wrap_mode(Pango.WrapMode.WORD)
        self.comment_textview.set_left_margin(8)
        self.comment_textview.set_right_margin(8)
        self.comment_textview.set_top_margin(4)
        self.comment_textview.set_bottom_margin(4)
        
        comment_scroll.add(self.comment_textview)
        rating_box.pack_start(comment_scroll, True, True, 0)
    
    def _on_thumbs_down(self, button):
        """Handle thumbs down rating."""
        self.rating = -1
        self._update_button_styles()
    
    def _on_neutral(self, button):
        """Handle neutral rating."""
        self.rating = 0
        self._update_button_styles()
    
    def _on_thumbs_up(self, button):
        """Handle thumbs up rating."""
        self.rating = 1
        self._update_button_styles()
    
    def _update_button_styles(self):
        """Update button styles to show selected rating."""
        # Remove all style classes
        for btn in [self.thumbs_down_btn, self.neutral_btn, self.thumbs_up_btn]:
            context = btn.get_style_context()
            context.remove_class("suggested-action")
            context.remove_class("destructive-action")
        
        # Add style to selected button
        if self.rating == -1:
            self.thumbs_down_btn.get_style_context().add_class("destructive-action")
        elif self.rating == 0:
            self.neutral_btn.get_style_context().add_class("suggested-action")
        elif self.rating == 1:
            self.thumbs_up_btn.get_style_context().add_class("suggested-action")
    
    def get_rating(self) -> int:
        """Get user's rating.
        
        Returns:
            Rating (-1, 0, 1)
        """
        return self.rating
    
    def get_comment(self) -> str:
        """Get user's comment.
        
        Returns:
            Comment text
        """
        buffer = self.comment_textview.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True).strip()
    
    def run_and_get_feedback(self) -> Optional[Dict[str, Any]]:
        """Show dialog and return feedback.
        
        Returns:
            Dict with 'rating' and 'comment' if submitted, None if cancelled
        """
        response = self.run()
        self.hide()
        
        if response == Gtk.ResponseType.OK:
            return {
                'rating': self.get_rating(),
                'comment': self.get_comment()
            }
        
        return None
