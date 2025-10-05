"""Place Marking Analysis Panel.

This module provides the PlaceRatePanel class for plotting place token
counts (marking evolution) in real-time during simulation.

This is a SEPARATE MODULE - not implemented in loaders!
Loaders only instantiate this panel and attach it to the UI.
"""
from typing import List, Tuple, Any

from shypn.analyses.plot_panel import AnalysisPlotPanel


class PlaceRatePanel(AnalysisPlotPanel):
    """Panel for plotting place token counts over time (marking evolution).
    
    This panel displays the number of tokens in selected places over simulation time,
    showing how the marking evolves as transitions fire. This is more intuitive than
    showing rates, as it directly visualizes the state of the Petri net.
    
    Plot interpretation:
        pass
    - Y-axis shows actual token count in each place
    - Horizontal lines = steady state (no token change)
    - Increasing lines = tokens being added to place
    - Decreasing lines = tokens being consumed from place
    - For continuous transitions: smooth curves (continuous flow)
    - For discrete transitions: step functions (instantaneous changes)
    
    Attributes:
        (inherited from AnalysisPlotPanel)
    
    Example:
        # Create panel (in right_panel_loader or similar)
        place_panel = PlaceRatePanel(data_collector)
        
        # Add places for analysis
        place_panel.add_object(place1)
        place_panel.add_object(place2)
        
        # Panel automatically updates during simulation
    """
    
    def __init__(self, data_collector):
        """Initialize the place marking analysis panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        super().__init__('place', data_collector)
        
    
    def _get_rate_data(self, place_id: Any) -> List[Tuple[float, float]]:
        """Get token count data for a place (marking evolution).
        
        Returns the raw token count over time, showing how the marking
        evolves as transitions fire. This is more intuitive than rates.
        
        Args:
            place_id: ID of the place
            
        Returns:
            List of (time, token_count) tuples
        """
        DEBUG_PLOT_DATA = False  # Disable verbose logging
        
        # Get raw token count data from collector
        raw_data = self.data_collector.get_place_data(place_id)
        
        if DEBUG_PLOT_DATA:
            if len(raw_data) > 0:
        
                pass
        # Return raw data directly - no rate calculation needed!
        # raw_data is already List[Tuple[float, float]] where:
        #   - First element: time (float)
        #   - Second element: token count (float, can be fractional for continuous)
        return raw_data
    
    def _get_ylabel(self) -> str:
        """Get Y-axis label for token count plot.
        
        Returns:
            str: Y-axis label
        """
        return 'Token Count'
    
    def _get_title(self) -> str:
        """Get plot title for token count plot.
        
        Returns:
            str: Plot title
        """
        return 'Place Marking Evolution'
    
    def wire_search_ui(self, entry, search_btn, result_label, model):
        """Wire search UI controls to place search functionality.
        
        This method connects the search entry, buttons, and result label from
        the right panel UI to the SearchHandler for finding places to add to analysis.
        
        Args:
            entry: GtkEntry for search input
            search_btn: GtkButton for triggering search
            result_label: GtkLabel for displaying search results
            model: ModelCanvasManager instance to search
        """
        self.search_entry = entry
        self.search_result_label = result_label
        self.search_model = model
        self.search_results = []  # Store current search results
        
        # Connect search button
        def on_search_clicked(button):
            query = self.search_entry.get_text().strip()
            if not query:
                self.search_result_label.set_text("⚠ Enter search text")
                return
            
            # Check if model is available
            if not self.search_model:
                self.search_result_label.set_text("⚠ No model loaded. Open or create a Petri net first.")
                return
            
            # Import SearchHandler
            from shypn.analyses import SearchHandler
            
            # Perform search
            results = SearchHandler.search_places(self.search_model, query)
            self.search_results = results
            
            # Display results
            if results:
                summary = SearchHandler.format_result_summary(results, 'place')
                self.search_result_label.set_text(summary)
                
                # If exactly one result, add it automatically
                if len(results) == 1:
                    self.add_object(results[0])
                    self.search_result_label.set_text(f"✓ Added {results[0].name} to analysis")
            else:
                self.search_result_label.set_text(f"✗ No places found for '{query}'")

        
        search_btn.connect('clicked', on_search_clicked)
        
        # Allow Enter key in search entry
        def on_entry_activate(entry):
            on_search_clicked(search_btn)
        
        entry.connect('activate', on_entry_activate)
        
