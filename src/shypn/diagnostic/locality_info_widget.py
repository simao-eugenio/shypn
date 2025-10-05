#!/usr/bin/env python3
"""Locality Info Widget - GTK widget for displaying locality information.

This widget displays locality structure and analysis in the transition
properties dialog diagnostics tab.

Example:
    # In transition_prop_dialog_loader
    widget = LocalityInfoWidget(model)
    widget.set_transition(transition)
    container.pack_start(widget, True, True, 0)
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from .locality_detector import Locality, LocalityDetector
from .locality_analyzer import LocalityAnalyzer


class LocalityInfoWidget(Gtk.Box):
    """GTK widget displaying locality information.
    
    This widget shows:
    - Locality summary (inputs → transition → outputs)
    - List of input places with token counts
    - List of output places with token counts
    - Token flow diagram
    - Analysis metrics (token balance, firing potential, etc.)
    
    The widget is designed to be embedded in the transition properties
    dialog's diagnostics tab, using the existing locality_info_container.
    
    Attributes:
        model: PetriNetModel instance
        detector: LocalityDetector for detecting localities
        analyzer: LocalityAnalyzer for analyzing localities
        locality: Current Locality object (or None)
        summary_label: GTK Label showing locality summary
        textview: GTK TextView showing detailed information
    
    Usage:
        # Create widget
        widget = LocalityInfoWidget(model)
        
        # Set transition to display
        widget.set_transition(transition)
        
        # Add to container
        container.pack_start(widget, True, True, 0)
        widget.show_all()
    """
    
    def __init__(self, model):
        """Initialize widget.
        
        Args:
            model: PetriNetModel instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        self.model = model
        self.detector = LocalityDetector(model)
        self.analyzer = LocalityAnalyzer(model)
        self.locality = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build widget UI.
        
        Creates:
        - Summary label (bold, at top)
        - Separator
        - Scrolled window with TextView for detailed information
        """
        # Summary label
        self.summary_label = Gtk.Label()
        self.summary_label.set_markup("<b>Locality Structure</b>")
        self.summary_label.set_xalign(0)
        self.summary_label.set_margin_start(5)
        self.summary_label.set_margin_end(5)
        self.pack_start(self.summary_label, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 5)
        
        # Scrolled window for details
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        
        # TextView for detailed info
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_left_margin(10)
        self.textview.set_right_margin(10)
        self.textview.set_top_margin(5)
        self.textview.set_bottom_margin(5)
        
        # Monospace font for better alignment
        font_desc = Pango.FontDescription("Monospace 10")
        self.textview.override_font(font_desc)
        
        scrolled.add(self.textview)
        self.pack_start(scrolled, True, True, 0)
        
        self.show_all()
    
    def set_transition(self, transition):
        """Set transition and update display.
        
        This is the main entry point for updating the widget.
        Call this method whenever the transition changes.
        
        Args:
            transition: Transition object to display locality for
        
        Example:
            widget.set_transition(transition)
            # Widget now shows locality info for this transition
        """
        if transition is None:
            self.locality = None
            self._show_no_transition()
            return
        
        self.locality = self.detector.get_locality_for_transition(transition)
        self._update_display()
    
    def _update_display(self):
        """Update widget display with locality info.
        
        Called internally after set_transition().
        Determines which content to show based on locality validity.
        """
        if self.locality is None:
            self._show_no_transition()
            return
        
        if not self.locality.is_valid:
            self._show_invalid_locality()
            return
        
        self._show_valid_locality()
    
    def _show_valid_locality(self):
        """Show valid locality information.
        
        Displays:
        - Summary in header
        - Token flow diagram
        - Analysis metrics
        """
        # Update summary
        self.summary_label.set_markup(
            f"<b>Locality: {self.locality.get_summary()}</b>"
        )
        
        # Get analysis
        analysis = self.analyzer.analyze_locality(self.locality)
        flow_desc = self.analyzer.get_token_flow_description(self.locality)
        
        # Build detailed text
        text_lines = []
        text_lines.extend(flow_desc)
        text_lines.append("")
        text_lines.append("═" * 60)
        text_lines.append("Analysis:")
        text_lines.append(f"  Total Places:     {analysis['place_count']}")
        text_lines.append(f"  Input Places:     {analysis['input_count']}")
        text_lines.append(f"  Output Places:    {analysis['output_count']}")
        text_lines.append(f"  Total Arcs:       {analysis['arc_count']}")
        text_lines.append("")
        text_lines.append(f"  Input Tokens:     {analysis['input_tokens']}")
        text_lines.append(f"  Output Tokens:    {analysis['output_tokens']}")
        text_lines.append(f"  Token Balance:    {analysis['token_balance']:+d}")
        text_lines.append(f"  Total Arc Weight: {analysis['total_weight']}")
        text_lines.append("")
        
        # Firing status with icon
        can_fire = analysis['can_fire']
        fire_icon = "✓" if can_fire else "✗"
        fire_status = "Yes (sufficient tokens)" if can_fire else "No (insufficient tokens)"
        text_lines.append(f"  Can Fire:         {fire_icon} {fire_status}")
        
        # Set text
        buffer = self.textview.get_buffer()
        buffer.set_text("\n".join(text_lines))
    
    def _show_no_transition(self):
        """Show message when no transition set.
        
        Displays placeholder message indicating no transition is selected.
        """
        self.summary_label.set_markup("<i>No transition selected</i>")
        buffer = self.textview.get_buffer()
        buffer.set_text("Select a transition to view its locality information.")
    
    def _show_invalid_locality(self):
        """Show message for invalid locality.
        
        Displays information about why the locality is invalid
        (missing inputs or outputs).
        """
        self.summary_label.set_markup("<i>Invalid Locality</i>")
        buffer = self.textview.get_buffer()
        
        text = []
        text.append(f"Transition: {self.locality.transition.name}")
        text.append("")
        text.append("⚠ This transition does not form a valid locality.")
        text.append("")
        text.append("A valid locality requires:")
        text.append("  • At least 1 input place (provides tokens TO transition)")
        text.append("  • At least 1 output place (receives tokens FROM transition)")
        text.append("")
        text.append("Current state:")
        text.append(f"  • Input places:  {len(self.locality.input_places)}")
        text.append(f"  • Output places: {len(self.locality.output_places)}")
        text.append("")
        
        if len(self.locality.input_places) == 0:
            text.append("  ✗ No input places found")
        else:
            text.append(f"  ✓ {len(self.locality.input_places)} input place(s)")
            for place in self.locality.input_places:
                text.append(f"      - {place.name}")
        
        text.append("")
        
        if len(self.locality.output_places) == 0:
            text.append("  ✗ No output places found")
        else:
            text.append(f"  ✓ {len(self.locality.output_places)} output place(s)")
            for place in self.locality.output_places:
                text.append(f"      - {place.name}")
        
        buffer.set_text("\n".join(text))
