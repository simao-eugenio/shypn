#!/usr/bin/env python3
"""Histogram plot - value distributions.

Author: Simão Eugénio
Date: 2025-12-30
"""
import numpy as np
from .base_plot import BasePlot


class HistogramPlot(BasePlot):
    """Histogram plot showing value distributions.
    
    Features:
    - Distribution for each object
    - Configurable bin count
    - Color-coded by object
    """
    
    def __init__(self, data_collector=None, model=None):
        """Initialize histogram plot."""
        super().__init__(data_collector, model)
        self.bins = 30  # Default bin count
    
    def _create_plot(self, data):
        """Create histogram plot.
        
        Args:
            data: Filtered time and object data (per-object format)
        """
        obj_data = data['data']
        
        if not obj_data:
            return
        
        # Color palette
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12',
                 '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        
        from shypn.netobjs import Place, Transition
        
        # Plot each object
        for i, obj in enumerate(self.selected_objects):
            obj_id = obj.id
            if obj_id in obj_data:
                color = colors[i % len(colors)]
                obj_info = obj_data[obj_id]
                values = obj_info['values']
                
                if not values:
                    continue
                
                # Different hatching for places vs transitions
                is_place = isinstance(obj, Place)
                hatch = '//' if is_place else None  # Diagonal hatch for places
                
                # Plot histogram
                self.axes.hist(
                    values,
                    bins=self.bins,
                    label=obj.name,
                    color=color,
                    alpha=0.6 if not is_place else 0.5,  # Slightly more transparent for hatched places
                    edgecolor='black',
                    linewidth=0.5,
                    hatch=hatch
                )
        
        # Configure axes
        self.axes.set_xlabel('Value', fontsize=12)
        self.axes.set_ylabel('Frequency', fontsize=12)
        self.axes.set_title(self._get_plot_title(), fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3)
        if self.show_legend:
            self.axes.legend(loc='best', framealpha=0.9)
        
        # Tight layout
        self.figure.tight_layout()
    
    def _get_plot_title(self) -> str:
        """Get plot title.
        
        Returns:
            str: Plot title
        """
        return 'Value Distribution'
