#!/usr/bin/env python3
"""Diagnostics Category - Real-time runtime diagnostics for transitions.

This category wraps the DiagnosticsPanel to display transition-specific
runtime metrics including locality, firing events, and throughput.

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_dynamic_category import BaseDynamicCategory
from shypn.analyses.diagnostics_panel import DiagnosticsPanel


class DiagnosticsCategory(BaseDynamicCategory):
    """Category for real-time transition diagnostics.
    
    Displays runtime execution metrics for selected transitions:
    - Locality structure and analysis
    - Recent firing events
    - Throughput calculations
    - Dynamic enablement state
    - Token flow visualization
    
    Unlike the static transition properties dialog, this updates in real-time
    during simulation.
    
    Features:
    - Real-time runtime diagnostics
    - Locality detection and analysis
    - Automatic updates during simulation
    - Context menu integration for transition selection
    """
    
    def __init__(self, model=None, data_collector=None, expanded=False):
        """Initialize diagnostics category.
        
        Args:
            model: ModelCanvasManager instance (optional)
            data_collector: SimulationDataCollector instance (optional)
            expanded: Whether category starts expanded
        """
        super().__init__(
            title='DIAGNOSTICS',
            model=model,
            data_collector=data_collector,
            expanded=expanded
        )
    
    def _build_content(self):
        """Build diagnostics category content.
        
        Returns:
            Gtk.Box: Content widget with diagnostics display
        """
        # Container for all content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.set_margin_top(6)
        content_box.set_margin_bottom(6)
        content_box.set_margin_start(6)
        content_box.set_margin_end(6)
        
        # Create diagnostics panel
        self.panel = DiagnosticsPanel(
            model=self.model,
            data_collector=self.data_collector
        )
        
        # Create container for diagnostics panel
        diagnostics_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create selection label
        selection_label = Gtk.Label()
        selection_label.set_markup('<b>Selected Transition:</b> None')
        selection_label.set_halign(Gtk.Align.START)
        selection_label.set_margin_bottom(6)
        
        # Create scrolled window for diagnostics text
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # Create text view for diagnostics output
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        textview.set_left_margin(6)
        textview.set_right_margin(6)
        textview.set_top_margin(6)
        textview.set_bottom_margin(6)
        
        # Use monospace font for better formatting
        try:
            import pango
            font_desc = pango.FontDescription('Monospace 9')
            textview.modify_font(font_desc)
        except:
            pass
        
        scrolled.add(textview)
        
        # Create placeholder label (shown when no transition selected)
        placeholder_label = Gtk.Label()
        placeholder_label.set_markup(
            '<span foreground="#888888">Right-click a transition and select\n'
            '"Show Diagnostics" to view runtime metrics</span>'
        )
        placeholder_label.set_halign(Gtk.Align.CENTER)
        placeholder_label.set_valign(Gtk.Align.CENTER)
        
        # Add widgets to container
        diagnostics_container.pack_start(selection_label, False, False, 0)
        diagnostics_container.pack_start(scrolled, True, True, 0)
        diagnostics_container.pack_start(placeholder_label, True, True, 0)
        
        # Setup panel with container
        self.panel.setup(
            container=diagnostics_container,
            selection_label=selection_label,
            placeholder_label=placeholder_label
        )
        
        # Store widgets for later access
        self.selection_label = selection_label
        self.textview = textview
        self.placeholder_label = placeholder_label
        
        # Add diagnostics container to content box
        content_box.pack_start(diagnostics_container, True, True, 0)
        
        content_box.show_all()
        return content_box
    
    def _perform_search(self):
        """Perform search (not applicable for diagnostics).
        
        Diagnostics panel doesn't have search functionality - transitions
        are selected via context menu.
        """
        # Not applicable for diagnostics
        pass
    
    def set_model(self, model):
        """Set model and update panel.
        
        Args:
            model: ModelCanvasManager instance
        """
        super().set_model(model)
        
        # Update panel's model and recreate analyzers
        if self.panel:
            self.panel.model = model
            if model:
                from shypn.diagnostic import (
                    LocalityDetector,
                    LocalityAnalyzer,
                    LocalityRuntimeAnalyzer
                )
                self.panel.detector = LocalityDetector(model)
                self.panel.analyzer = LocalityAnalyzer(model)
                if self.data_collector:
                    self.panel.runtime_analyzer = LocalityRuntimeAnalyzer(model, self.data_collector)
    
    def set_data_collector(self, data_collector):
        """Set data collector and update panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        super().set_data_collector(data_collector)
        
        # Update panel's data collector (direct attribute assignment)
        if self.panel:
            self.panel.data_collector = data_collector
            if self.model and data_collector:
                from shypn.diagnostic import LocalityRuntimeAnalyzer
                self.panel.runtime_analyzer = LocalityRuntimeAnalyzer(self.model, data_collector)
    
    def refresh(self):
        """Refresh diagnostics display."""
        if self.panel and self.panel.current_transition:
            # Re-display current transition to refresh metrics
            self.panel.set_transition(self.panel.current_transition)
    
    def set_transition(self, transition):
        """Set transition to display diagnostics for.
        
        Args:
            transition: Transition object to analyze
        """
        if self.panel:
            self.panel.set_transition(transition)
    
    def clear_transition(self):
        """Clear currently displayed transition."""
        if self.panel:
            self.panel.clear_display()
