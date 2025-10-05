"""Simulation Analysis Package.

This package provides real-time analysis and visualization capabilities for Petri net simulations,
including rate-based plotting of place token dynamics and transition firing rates.

Modules:
    data_collector: Collects raw simulation data for analysis
    rate_calculator: Calculates rates (token flow, firing frequency) from raw data
    plot_panel: Base class for matplotlib-based plotting panels
    place_rate_panel: Place token rate plotting
    transition_rate_panel: Transition firing rate plotting
    search_handler: Search for places and transitions to add to plots
    context_menu_handler: Add "Add to Analysis" items to canvas context menus
"""

__all__ = [
    'SimulationDataCollector',
    'RateCalculator',
    'AnalysisPlotPanel',
    'PlaceRatePanel',
    'TransitionRatePanel',
    'SearchHandler',
    'ContextMenuHandler',
]

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'SimulationDataCollector':
        from .data_collector import SimulationDataCollector
        return SimulationDataCollector
    elif name == 'RateCalculator':
        from .rate_calculator import RateCalculator
        return RateCalculator
    elif name == 'AnalysisPlotPanel':
        from .plot_panel import AnalysisPlotPanel
        return AnalysisPlotPanel
    elif name == 'PlaceRatePanel':
        from .place_rate_panel import PlaceRatePanel
        return PlaceRatePanel
    elif name == 'TransitionRatePanel':
        from .transition_rate_panel import TransitionRatePanel
        return TransitionRatePanel
    elif name == 'SearchHandler':
        from .search_handler import SearchHandler
        return SearchHandler
    elif name == 'ContextMenuHandler':
        from .context_menu_handler import ContextMenuHandler
        return ContextMenuHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
