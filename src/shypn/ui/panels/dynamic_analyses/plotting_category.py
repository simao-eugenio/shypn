#!/usr/bin/env python3
"""Plotting Category - Publication-quality matplotlib plots.

Provides notebook with 4 plot types:
- Time Series
- Histogram
- Scatter
- Phase

Author: Simão Eugénio
Date: 2025-12-30
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_dynamic_category import BaseDynamicCategory
from shypn.analyses.plotting import (
    TimeSeriesPlot,
    HistogramPlot,
    ScatterPlot,
    PhasePlot
)


class PlottingCategory(BaseDynamicCategory):
    """Category for publication-quality plotting with locality awareness.
    
    Features:
    - 4 plot types in notebook tabs (Time Series, Histogram, Scatter, Phase)
    - Time range control
    - Object selection from Transitions/Places
    - Full matplotlib toolbar (zoom, pan, save)
    - Export configuration
    - **Automatic locality detection**: When a transition is added, its entire
      locality (input places, output places, and catalyst places) is automatically
      included in all plots, showing the complete P→T→P reaction context
    
    Locality Support:
        When adding a transition via context menu or programmatically:
        - Detects the transition's locality (connected places)
        - Adds all input places (substrates)
        - Adds all output places (products)  
        - Adds all catalyst places (enzymes, cofactors)
        - Tracks locality for coordinated removal
        
    Example:
        # Add transition T1 with locality
        plotting_category.add_object(t1)
        # Automatically adds: P1 (input) → T1 → P2 (output) + E1 (catalyst)
        
        # Remove transition removes entire locality
        plotting_category.remove_object(t1)
        # Also removes: P1, P2, E1
    """
    
    def __init__(self, model=None, data_collector=None, expanded=False):
        """Initialize plotting category.
        
        Args:
            model: ModelCanvasManager instance (optional)
            data_collector: SimulationDataCollector instance (optional)
            expanded: Whether category starts expanded
        """
        # Store plot instances
        self.timeseries_plot = None
        self.histogram_plot = None
        self.scatter_plot = None
        self.phase_plot = None
        
        # Locality tracking
        self._locality_places = {}  # Maps transition_id -> {input_places, output_places, catalyst_places}
        
        super().__init__(
            title='PLOTTING',
            model=model,
            data_collector=data_collector,
            expanded=expanded
        )
    
    def _build_content(self):
        """Build plotting category content.
        
        Returns:
            Gtk.Box: Content widget with notebook of plot types
        """
        # Container for all content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create notebook with plot tabs
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        notebook.set_scrollable(True)
        
        # Create plot instances
        self.timeseries_plot = TimeSeriesPlot(
            data_collector=self.data_collector,
            model=self.model
        )
        
        self.histogram_plot = HistogramPlot(
            data_collector=self.data_collector,
            model=self.model
        )
        
        self.scatter_plot = ScatterPlot(
            data_collector=self.data_collector,
            model=self.model
        )
        
        self.phase_plot = PhasePlot(
            data_collector=self.data_collector,
            model=self.model
        )
        
        # Add tabs to notebook
        notebook.append_page(
            self.timeseries_plot,
            Gtk.Label(label="Time Series")
        )
        
        notebook.append_page(
            self.histogram_plot,
            Gtk.Label(label="Histogram")
        )
        
        notebook.append_page(
            self.scatter_plot,
            Gtk.Label(label="Scatter")
        )
        
        notebook.append_page(
            self.phase_plot,
            Gtk.Label(label="Phase")
        )
        
        content_box.pack_start(notebook, True, True, 0)
        
        # Store reference to notebook
        self.notebook = notebook
        
        # Store all plots in list for easy access
        self.plots = [
            self.timeseries_plot,
            self.histogram_plot,
            self.scatter_plot,
            self.phase_plot
        ]
        
        # Create dummy panel attribute for compatibility
        # (some code expects category.panel)
        self.panel = self
        
        return content_box
    
    def add_object(self, obj):
        """Add object to all plots.
        
        For transitions added directly (not through add_locality_places),
        automatically detects and adds locality places.
        
        Args:
            obj: Place or Transition to plot
        """
        from shypn.netobjs import Transition
        
        # Check if this is a transition being added for the first time
        # (not already tracked in locality)
        is_new_transition = (isinstance(obj, Transition) and 
                            obj.id not in self._locality_places)
        
        # If it's a new transition, detect and add its locality
        if is_new_transition and self.model:
            from shypn.diagnostic import LocalityDetector
            
            detector = LocalityDetector(self.model)
            locality = detector.get_locality_for_transition(obj)
            
            if locality.is_valid:
                # Add the transition itself
                for plot in self.plots:
                    plot.add_object(obj)
                
                # Add all locality places
                self.add_locality_places(obj, locality)
                return
        
        # For places or transitions without locality, just add the object
        for plot in self.plots:
            plot.add_object(obj)
    
    def remove_object(self, obj):
        """Remove object from all plots.
        
        For transitions, also removes associated locality places.
        
        Args:
            obj: Place or Transition to remove
        """
        from shypn.netobjs import Transition, Place
        from shypn.utils.color_schema_manager import ColorSchemaManager
        
        # Reset color to schema default when removing
        if isinstance(obj, Place):
            ColorSchemaManager.reset_place_color(obj)
        elif isinstance(obj, Transition):
            ColorSchemaManager.reset_transition_colors(obj)
        
        # If it's a transition with tracked locality, remove locality places first
        if isinstance(obj, Transition) and obj.id in self._locality_places:
            locality_data = self._locality_places[obj.id]
            
            # Remove all locality places
            for place in locality_data['input_places']:
                ColorSchemaManager.reset_place_color(place)
                for plot in self.plots:
                    plot.remove_object(place)
            
            for place in locality_data['output_places']:
                ColorSchemaManager.reset_place_color(place)
                for plot in self.plots:
                    plot.remove_object(place)
            
            for place in locality_data.get('catalyst_places', []):
                ColorSchemaManager.reset_place_color(place)
                for plot in self.plots:
                    plot.remove_object(place)
            
            # Remove locality tracking
            del self._locality_places[obj.id]
        
        # Remove the object itself
        for plot in self.plots:
            plot.remove_object(obj)
    
    def clear_objects(self):
        """Clear all objects from all plots."""
        # Reset all object colors to schema defaults before clearing
        from shypn.utils.color_schema_manager import ColorSchemaManager
        from shypn.netobjs import Place, Transition
        
        # Collect all objects from all plots
        all_objects = set()
        for plot in self.plots:
            if hasattr(plot, 'selected_objects'):
                all_objects.update(plot.selected_objects)
        
        # Reset colors for all objects
        for obj in all_objects:
            if isinstance(obj, Place):
                ColorSchemaManager.reset_place_color(obj)
            elif isinstance(obj, Transition):
                ColorSchemaManager.reset_transition_colors(obj)
        
        # Clear locality tracking
        self._locality_places.clear()
        
        for plot in self.plots:
            plot.clear_objects()
    
    def clear_plot(self):
        """Clear all plots (called when simulation is reset).
        
        This is the method called by the simulation Reset button.
        It clears the plot data but keeps the selected objects (like transitions/places panels).
        """
        # Note: We do NOT clear locality tracking or selected objects
        # This matches the behavior of transitions/places panels where
        # reset clears the data but keeps the selection intact
        
        # Clear all plots and show reset state
        for plot in self.plots:
            # Reset data tracking counters
            plot._last_data_count = 0
            plot._last_selected_count = 0
            plot.needs_update = False
            
            # Show reset state (blank canvas with axes, grid, legend)
            if hasattr(plot, '_show_reset_state'):
                plot._show_reset_state()
    
    def add_locality_places(self, transition, locality):
        """Add locality places for a transition to all plots.
        
        This stores the locality places and adds them to all plot instances,
        showing the complete P→T→P pattern in all visualization types.
        
        Called either by add_object() for automatic locality detection,
        or by context menu handler when transition is added with locality.
        
        Args:
            transition: Transition object
            locality: Locality object with input/output places
        """
        if not locality.is_valid:
            return
        
        # Check if already tracked (avoid duplicate additions)
        if transition.id in self._locality_places:
            return
        
        # Store locality information
        self._locality_places[transition.id] = {
            'input_places': list(locality.input_places),
            'output_places': list(locality.output_places),
            'catalyst_places': list(locality.catalyst_places),
            'transition': transition
        }
        
        # Add all locality places to all plots
        for place in locality.input_places:
            for plot in self.plots:
                plot.add_object(place)
        
        for place in locality.output_places:
            for plot in self.plots:
                plot.add_object(place)
        
        for place in locality.catalyst_places:
            for plot in self.plots:
                plot.add_object(place)
    
    def set_data_collector(self, data_collector):
        """Set data collector for all plots.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        self.data_collector = data_collector
        for plot in self.plots:
            plot.set_data_collector(data_collector)
    
    def set_model(self, model):
        """Set model for all plots.
        
        Args:
            model: ModelCanvasManager instance
        """
        self.model = model
        for plot in self.plots:
            plot.model = model
    
    def refresh(self):
        """Refresh all plots."""
        for plot in self.plots:
            plot.needs_update = True
    
    def get_locality_info(self, transition_id):
        """Get locality information for a tracked transition.
        
        Args:
            transition_id: ID of the transition
            
        Returns:
            dict with locality info or None if not tracked
        """
        return self._locality_places.get(transition_id)
    
    def set_transition(self, transition):
        """Add transition to plots (compatibility method).
        
        Args:
            transition: Transition to add
        """
        self.add_object(transition)
    
    def set_place(self, place):
        """Add place to plots (compatibility method).
        
        Args:
            place: Place to add
        """
        self.add_object(place)
    
    def register_with_model(self, model):
        """Register with model (compatibility method).
        
        Args:
            model: ModelCanvasManager instance
        """
        self.set_model(model)
