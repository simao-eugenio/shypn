#!/usr/bin/env python3
"""Transitions Category - Real-time transition behavior analysis.

This category wraps the TransitionRatePanel to display transition firing
rates and cumulative counts with search functionality.

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_dynamic_category import BaseDynamicCategory
from shypn.analyses.transition_rate_panel import TransitionRatePanel


class TransitionsCategory(BaseDynamicCategory):
    """Category for transition behavior analysis with search.
    
    Displays transition firing rates (continuous) or cumulative counts (discrete)
    with the ability to search and select transitions for plotting.
    
    Features:
    - Real-time transition behavior plots
    - Search by transition name
    - Type-aware visualization (continuous vs discrete)
    - Locality place plotting support
    """
    
    def __init__(self, model=None, data_collector=None, expanded=False, place_panel=None):
        """Initialize transitions category.
        
        Args:
            model: ModelCanvasManager instance (optional)
            data_collector: SimulationDataCollector instance (optional)
            expanded: Whether category starts expanded
            place_panel: Optional PlaceRatePanel for locality plotting
        """
        self._place_panel = place_panel
        super().__init__(
            title='TRANSITIONS',
            model=model,
            data_collector=data_collector,
            expanded=expanded
        )
    
    def _build_content(self):
        """Build transitions category content.
        
        Returns:
            Gtk.Box: Content widget with search and plot
        """
        # Container for all content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.set_margin_top(6)
        content_box.set_margin_bottom(6)
        content_box.set_margin_start(6)
        content_box.set_margin_end(6)
        
        # Add search box at top
        search_box = self._create_search_box()
        content_box.pack_start(search_box, False, False, 0)
        
        # Create transition rate panel
        self.panel = TransitionRatePanel(
            data_collector=self.data_collector,
            place_panel=self._place_panel
        )
        
        # Wire search UI to panel
        if self.model:
            self.panel.wire_search_ui(
                entry=self.search_entry,
                search_btn=self.search_button,
                result_label=self.result_label,
                model=self.model
            )
        
        # Panel is a Gtk.Box, so it IS the widget
        # Store reference to panel container for size management
        self.canvas_container = self.panel
        
        # Add panel to content
        content_box.pack_start(self.panel, True, True, 0)
        
        content_box.show_all()
        return content_box
    
    def _perform_search(self):
        """Perform search in transition panel.
        
        The actual search is handled by the panel's wire_search_ui,
        which connects the search controls to the panel's search logic.
        """
        # Search is handled by TransitionRatePanel via wire_search_ui
        # This method is required by base class but implementation is in panel
        pass
    
    def set_place_panel(self, place_panel):
        """Set place panel reference for locality plotting.
        
        Args:
            place_panel: PlaceRatePanel instance
        """
        self._place_panel = place_panel
        if self.panel:
            self.panel.set_place_panel(place_panel)
    
    def set_model(self, model):
        """Set model and update panel.
        
        Args:
            model: ModelCanvasManager instance
        """
        super().set_model(model)
        
        # Re-wire search UI with new model
        if self.panel and model:
            self.panel.wire_search_ui(
                entry=self.search_entry,
                search_btn=self.search_button,
                result_label=self.result_label,
                model=model
            )
    
    def set_data_collector(self, data_collector):
        """Set data collector and update panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        super().set_data_collector(data_collector)
        
        # Update panel's data collector (direct attribute assignment)
        if self.panel:
            self.panel.data_collector = data_collector
    
    def refresh(self):
        """Refresh transition plots."""
        if self.panel:
            self.panel.refresh()
    
    def add_transition(self, transition):
        """Add transition to plot.
        
        Args:
            transition: Transition object to plot
        """
        if self.panel:
            self.panel.add_object(transition)
    
    def remove_transition(self, transition):
        """Remove transition from plot.
        
        Args:
            transition: Transition object to remove
        """
        if self.panel:
            self.panel.remove_object(transition)
    
    def clear_transitions(self):
        """Clear all transitions from plot."""
        if self.panel:
            self.panel.clear_objects()
