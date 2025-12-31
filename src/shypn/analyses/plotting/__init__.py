"""Publication-quality plotting package.

Provides matplotlib-based plots with time range control and export options.
"""
from .base_plot import BasePlot
from .timeseries_plot import TimeSeriesPlot
from .histogram_plot import HistogramPlot
from .scatter_plot import ScatterPlot
from .phase_plot import PhasePlot

__all__ = [
    'BasePlot',
    'TimeSeriesPlot',
    'HistogramPlot',
    'ScatterPlot',
    'PhasePlot',
]
