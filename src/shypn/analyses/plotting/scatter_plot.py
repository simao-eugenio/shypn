#!/usr/bin/env python3
"""Scatter plot - correlation between two objects.

Author: Simão Eugénio
Date: 2025-12-30
"""
from .base_plot import BasePlot


class ScatterPlot(BasePlot):
    """Scatter plot showing correlation between two objects.
    
    Features:
    - X vs Y correlation
    - Requires exactly 2 objects
    - Color by time (optional)
    """
    
    def _create_plot(self, data):
        """Create scatter plot.
        
        Args:
            data: Filtered time and object data
        """
        obj_data = data['data']
        
        num_objects = len(self.selected_objects)
        
        if num_objects < 2:
            # Show instruction message
            self.axes.text(
                0.5, 0.5,
                'Scatter plot requires at least 2 objects\n\nSelect places or transitions to compare',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='gray'
            )
            self.axes.set_xticks([])
            self.axes.set_yticks([])
            return
        
        # If more than 2 objects, use first 2 that have data
        available_objects = [obj for obj in self.selected_objects if obj.id in obj_data]
        
        if len(available_objects) < 2:
            # Show waiting message
            self.axes.text(
                0.5, 0.5,
                f'Waiting for data from at least 2 objects\n\nSelected: {num_objects}, With data: {len(available_objects)}',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='gray'
            )
            self.axes.set_xticks([])
            self.axes.set_yticks([])
            return
        
        # Use first two objects with data
        obj1 = available_objects[0]
        obj2 = available_objects[1]
        
        x_values = obj_data[obj1.id]['values']
        y_values = obj_data[obj2.id]['values']
        
        if not x_values or not y_values:
            return
        
        # Ensure same length
        min_len = min(len(x_values), len(y_values))
        x_values = x_values[:min_len]
        y_values = y_values[:min_len]
        
        # Create scatter plot
        scatter = self.axes.scatter(
            x_values,
            y_values,
            alpha=0.6,
            s=30,
            c=range(len(x_values)),
            cmap='viridis',
            edgecolors='black',
            linewidth=0.5
        )
        
        # Add colorbar for time (only if scatter was successful)
        if scatter:
            try:
                cbar = self.figure.colorbar(scatter, ax=self.axes)
                cbar.set_label('Time index', rotation=270, labelpad=15)
            except (ValueError, RuntimeError, AttributeError) as e:
                # Colorbar creation can fail with certain data configurations
                import logging
                logging.getLogger(__name__).debug(f"Colorbar creation failed: {e}")
                pass  # Colorbar creation failed, skip it
        
        # Configure axes
        self.axes.set_xlabel(obj1.name, fontsize=12)
        self.axes.set_ylabel(obj2.name, fontsize=12)
        self.axes.set_title(self._get_plot_title(), fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3)
        
        # Tight layout
        try:
            self.figure.tight_layout()
        except (ValueError, RuntimeError) as e:
            # tight_layout can fail with colorbar
            import logging
            logging.getLogger(__name__).debug(f"Tight layout failed: {e}")
            pass  # tight_layout can fail with colorbar, skip if it does
    
    def _get_plot_title(self) -> str:
        """Get plot title.
        
        Returns:
            str: Plot title
        """
        if len(self.selected_objects) == 2:
            return f'{self.selected_objects[0].name} vs {self.selected_objects[1].name}'
        return 'Scatter Plot'
