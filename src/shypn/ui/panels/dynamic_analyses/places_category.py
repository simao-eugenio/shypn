#!/usr/bin/env python3
"""Places Category - Real-time place marking evolution analysis.

This category wraps the PlaceRatePanel to display place token counts
(marking evolution) with search functionality.

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_dynamic_category import BaseDynamicCategory
from shypn.analyses.place_rate_panel import PlaceRatePanel


class PlacesCategory(BaseDynamicCategory):
    """Category for place marking evolution analysis with search.
    
    Displays place token counts over time, showing how the marking
    evolves as transitions fire. Includes search functionality to
    find and select places for plotting.
    
    Features:
    - Real-time token count visualization
    - Search by place name
    - Smooth curves for continuous transitions
    - Step functions for discrete transitions
    """
    
    def __init__(self, model=None, data_collector=None, expanded=False):
        """Initialize places category.
        
        Args:
            model: ModelCanvasManager instance (optional)
            data_collector: SimulationDataCollector instance (optional)
            expanded: Whether category starts expanded
        """
        super().__init__(
            title='PLACES',
            model=model,
            data_collector=data_collector,
            expanded=expanded
        )
    
    def _build_content(self):
        """Build places category content.
        
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
        
        # Create place rate panel
        self.panel = PlaceRatePanel(data_collector=self.data_collector)
        
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
        """Perform search in place panel.
        
        The actual search is handled by the panel's wire_search_ui,
        which connects the search controls to the panel's search logic.
        """
        # Search is handled by PlaceRatePanel via wire_search_ui
        # This method is required by base class but implementation is in panel
        pass
    
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
        """Refresh place plots."""
        if self.panel:
            self.panel.refresh()
    
    def add_place(self, place):
        """Add place to plot.
        
        Args:
            place: Place object to plot
        """
        if self.panel:
            self.panel.add_object(place)
    
    def remove_place(self, place):
        """Remove place from plot.
        
        Args:
            place: Place object to remove
        """
        if self.panel:
            self.panel.remove_object(place)
    
    def clear_places(self):
        """Clear all places from plot."""
        if self.panel:
            self.panel.clear_objects()
