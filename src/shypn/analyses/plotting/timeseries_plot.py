#!/usr/bin/env python3
"""Time series plot - traces over time.

Author: Simão Eugénio  
Date: 2025-12-30
"""
from .base_plot import BasePlot


class TimeSeriesPlot(BasePlot):
    """Time series plot showing values over time.
    
    Features:
    - Multiple traces (one per object)
    - Color-coded by object
    - Time range filtering
    - Publication-quality export
    """
    
    def _create_plot(self, data):
        """Create time series plot with dual y-axes when needed.
        
        Args:
            data: Filtered time and object data (per-object time points)
        """
        obj_data = data['data']
        
        if not obj_data:
            return
        
        # Color palette (same as plot_panel.py)
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', 
                 '#9b59b6', '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b']
        
        from shypn.netobjs import Place, Transition
        
        # Separate transitions and places (mirroring Transitions category behavior)
        transitions = []
        places = []
        
        for obj in self.selected_objects:
            obj_id = obj.id
            if obj_id in obj_data:
                if isinstance(obj, Transition):
                    transitions.append((obj, obj_data[obj_id]))
                else:
                    places.append((obj, obj_data[obj_id]))
        
        # Create secondary Y-axis for places if we have both transitions and places
        # This mirrors the Transitions category's rate/tokens dual-axis approach
        ax_places = None
        if transitions and places:
            ax_places = self.axes.twinx()
            ax_places.set_ylabel('Tokens (places)', color='gray', fontsize=10)
            ax_places.tick_params(axis='y', labelcolor='gray')
        
        # Plot transitions on primary axis
        for i, (obj, obj_info) in enumerate(transitions):
            time_points = obj_info['time']
            values = obj_info['values']
            color = colors[i % len(colors)]
            
            # Create label with transition type
            transition_type = getattr(obj, 'transition_type', 'continuous')
            type_abbrev = {'immediate': 'IMM', 'timed': 'TIM', 'stochastic': 'STO', 
                          'continuous': 'CON'}.get(transition_type, transition_type[:3].upper())
            label = f'{obj.name} [{type_abbrev}]'
            
            self.axes.plot(
                time_points,
                values,
                label=label,
                color=color,
                linewidth=2,
                alpha=0.9,
                linestyle='-',
                marker=None
            )
        
        # Plot places on secondary axis if available, otherwise primary
        target_ax = ax_places if ax_places else self.axes
        place_start_idx = len(transitions)
        
        for i, (obj, obj_info) in enumerate(places):
            time_points = obj_info['time']
            values = obj_info['values']
            color = colors[(place_start_idx + i) % len(colors)]
            label = obj.name
            
            target_ax.plot(
                time_points,
                values,
                label=label,
                color=color,
                linewidth=2,
                alpha=0.9,
                linestyle='-',
                marker=None
            )
        
        # Configure primary axes (matching plot_panel.py style)
        self.axes.set_xlabel('Time (s)', fontsize=11)
        self.axes.set_ylabel('Rate (transitions)' if transitions else 'Value', fontsize=11)
        self.axes.set_title(self._get_plot_title(), fontsize=12, fontweight='bold')
        self.axes.grid(True, alpha=0.3)
        
        # Add 10% padding to primary y-axis
        ylim = self.axes.get_ylim()
        y_range = ylim[1] - ylim[0]
        if y_range > 0:
            self.axes.set_ylim(ylim[0] - y_range * 0.1, ylim[1] + y_range * 0.1)
        
        # Add 10% padding to secondary y-axis if it exists
        if ax_places:
            ylim2 = ax_places.get_ylim()
            y_range2 = ylim2[1] - ylim2[0]
            if y_range2 > 0:
                ax_places.set_ylim(ylim2[0] - y_range2 * 0.1, ylim2[1] + y_range2 * 0.1)
            
            # Combine legends from both axes
            lines1, labels1 = self.axes.get_legend_handles_labels()
            lines2, labels2 = ax_places.get_legend_handles_labels()
            if lines1 or lines2:
                self.axes.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=9, framealpha=0.9)
        else:
            self.axes.legend(loc='best', fontsize=9, framealpha=0.9)
        
        # Tight layout
        try:
            self.figure.tight_layout()
        except:
            pass
    
    def _get_plot_title(self) -> str:
        """Get plot title.
        
        Returns:
            str: Plot title
        """
        return 'Time Series'
