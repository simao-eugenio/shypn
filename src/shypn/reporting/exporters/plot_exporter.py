#!/usr/bin/env python3
"""Plot exporter for generating publication-quality figures.

Generates matplotlib plots and exports to SVG/PNG without GUI interaction.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class PlotExporter:
    """Export simulation data as plots (SVG/PNG/PDF).
    
    Generates publication-ready plots with proper formatting,
    labels, legends, and styling.
    """
    
    def __init__(self, simulation_data: dict, metadata: Optional[dict] = None, model=None):
        """Initialize plot exporter.
        
        Args:
            simulation_data: Dict with 'time_points', 'place_data', 'transition_data'
            metadata: Optional metadata dict
            model: Model object for accessing entity details
        """
        self.simulation_data = simulation_data
        self.metadata = metadata or {}
        self.model = model or simulation_data.get('model')
        self.time_points = simulation_data.get('time_points', [])
        self.place_data = simulation_data.get('place_data', {})
        self.transition_data = simulation_data.get('transition_data', {})
        
        # Color palette (same as AnalysisPlotPanel)
        self.colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', 
                      '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b']
    
    def export_concentration_curves(self, filepath: str, 
                                   place_ids: Optional[List[str]] = None,
                                   format: str = 'svg',
                                   dpi: int = 300,
                                   figsize: Tuple[float, float] = (10, 6)) -> bool:
        """Export place concentration curves.
        
        Args:
            filepath: Output file path
            place_ids: List of place IDs to plot (None = all)
            format: Output format ('svg', 'png', 'pdf')
            dpi: Resolution for raster formats
            figsize: Figure size in inches (width, height)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig, ax = self._setup_figure(figsize, dpi)
            
            # Determine which places to plot
            if place_ids is None:
                place_ids = sorted(self.place_data.keys())
            
            # Plot each place
            for i, place_id in enumerate(place_ids):
                if place_id not in self.place_data:
                    continue
                
                # Extract values from (time, tokens) tuples
                raw_data = self.place_data[place_id]
                values = [tokens for _, tokens in raw_data] if raw_data else []
                place_name = self._get_place_name(place_id)
                unit = self._get_place_unit(place_id)
                color = self.colors[i % len(self.colors)]
                
                # Direct 1:1 conversion: 1 token = 1 mM
                # No conversion needed - models use mM directly
                converted_values = values
                
                # Plot
                ax.plot(self.time_points, converted_values, 
                       color=color, linewidth=2, label=f"{place_name} ({unit})")
            
            # Formatting
            ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Concentration', fontsize=12, fontweight='bold')
            ax.set_title('Species Concentration over Time', fontsize=14, fontweight='bold')
            ax.legend(loc='best', framealpha=0.9)
            ax.grid(True, alpha=0.3)
            
            # Save
            fig.tight_layout()
            fig.savefig(filepath, format=format, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            
            return True
        except Exception as e:
            logger.error("Error exporting concentration curves: %s", e)
            return False
    
    def export_firing_rate_curves(self, filepath: str,
                                  transition_ids: Optional[List[str]] = None,
                                  format: str = 'svg',
                                  dpi: int = 300,
                                  figsize: Tuple[float, float] = (10, 6)) -> bool:
        """Export transition firing rate curves.
        
        Args:
            filepath: Output file path
            transition_ids: List of transition IDs to plot (None = all)
            format: Output format ('svg', 'png', 'pdf')
            dpi: Resolution for raster formats
            figsize: Figure size in inches (width, height)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig, ax = self._setup_figure(figsize, dpi)
            
            # Determine which transitions to plot
            if transition_ids is None:
                transition_ids = sorted(self.transition_data.keys())
            
            # Calculate firing rates (derivative of cumulative firings)
            for i, trans_id in enumerate(transition_ids):
                if trans_id not in self.transition_data:
                    continue
                
                # Extract values from (time, count) tuples
                raw_data = self.transition_data[trans_id]
                values = [count for _, count in raw_data] if raw_data else []
                trans_name = self._get_transition_name(trans_id)
                color = self.colors[i % len(self.colors)]
                
                # Calculate rate as diff(firings) / diff(time)
                if len(values) > 1 and len(self.time_points) > 1:
                    rates = []
                    rate_times = []
                    for j in range(1, len(values)):
                        dt = self.time_points[j] - self.time_points[j-1]
                        if dt > 0:
                            rate = (values[j] - values[j-1]) / dt
                            rates.append(rate)
                            rate_times.append(self.time_points[j])
                    
                    # Plot
                    if rates:
                        ax.plot(rate_times, rates, 
                               color=color, linewidth=2, label=trans_name)
            
            # Formatting
            ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Firing Rate (firings/s)', fontsize=12, fontweight='bold')
            ax.set_title('Reaction Firing Rates over Time', fontsize=14, fontweight='bold')
            ax.legend(loc='best', framealpha=0.9)
            ax.grid(True, alpha=0.3)
            
            # Save
            fig.tight_layout()
            fig.savefig(filepath, format=format, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            
            return True
        except Exception as e:
            logger.error("Error exporting firing rate curves: %s", e)
            return False
    
    def export_combined_plot(self, filepath: str, 
                           format: str = 'svg',
                           dpi: int = 300,
                           figsize: Tuple[float, float] = (12, 8)) -> bool:
        """Export combined multi-panel plot.
        
        Creates a figure with two subplots:
        - Top: Concentration curves
        - Bottom: Firing rate curves
        
        Args:
            filepath: Output file path
            format: Output format ('svg', 'png', 'pdf')
            dpi: Resolution for raster formats
            figsize: Figure size in inches (width, height)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=dpi)
            
            # Top panel: Concentrations
            for i, place_id in enumerate(sorted(self.place_data.keys())):
                # Extract values from (time, tokens) tuples
                raw_data = self.place_data[place_id]
                values = [tokens for _, tokens in raw_data] if raw_data else []
                place_name = self._get_place_name(place_id)
                unit = self._get_place_unit(place_id)
                color = self.colors[i % len(self.colors)]
                
                # Direct 1:1 conversion: 1 token = 1 mM
                # No conversion needed - models use mM directly
                converted_values = values
                
                ax1.plot(self.time_points, converted_values, 
                        color=color, linewidth=2, label=f"{place_name} ({unit})")
            
            ax1.set_ylabel('Concentration', fontsize=11, fontweight='bold')
            ax1.set_title('Species Concentration over Time', fontsize=12, fontweight='bold')
            ax1.legend(loc='best', framealpha=0.9, fontsize=9)
            ax1.grid(True, alpha=0.3)
            
            # Bottom panel: Firing rates
            for i, trans_id in enumerate(sorted(self.transition_data.keys())):
                # Extract values from (time, count) tuples
                raw_data = self.transition_data[trans_id]
                values = [count for _, count in raw_data] if raw_data else []
                trans_name = self._get_transition_name(trans_id)
                color = self.colors[i % len(self.colors)]
                
                # Calculate rates
                if len(values) > 1 and len(self.time_points) > 1:
                    rates = []
                    rate_times = []
                    for j in range(1, len(values)):
                        dt = self.time_points[j] - self.time_points[j-1]
                        if dt > 0:
                            rate = (values[j] - values[j-1]) / dt
                            rates.append(rate)
                            rate_times.append(self.time_points[j])
                    
                    if rates:
                        ax2.plot(rate_times, rates, 
                                color=color, linewidth=2, label=trans_name)
            
            ax2.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Firing Rate (firings/s)', fontsize=11, fontweight='bold')
            ax2.set_title('Reaction Firing Rates over Time', fontsize=12, fontweight='bold')
            ax2.legend(loc='best', framealpha=0.9, fontsize=9)
            ax2.grid(True, alpha=0.3)
            
            # Save
            fig.tight_layout()
            fig.savefig(filepath, format=format, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            
            return True
        except Exception as e:
            logger.error("Error exporting combined plot: %s", e)
            return False
    
    def _setup_figure(self, figsize: Tuple[float, float], dpi: int) -> Tuple[Figure, plt.Axes]:
        """Setup matplotlib figure with publication settings."""
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['lines.linewidth'] = 2
        
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        return fig, ax
    
    def _get_place_name(self, place_id: str) -> str:
        """Get place name from model."""
        if self.model and hasattr(self.model, 'places'):
            for place in self.model.places:
                if place.id == place_id:
                    return getattr(place, 'name', place_id)
        return place_id
    
    def _get_place_unit(self, place_id: str) -> str:
        """Get place unit from model."""
        if self.model and hasattr(self.model, 'places'):
            for place in self.model.places:
                if place.id == place_id:
                    return getattr(place, 'unit', 'mM')
        return 'mM'
    
    def _get_place_obj(self, place_id: str):
        """Get place object from model."""
        if self.model and hasattr(self.model, 'places'):
            for place in self.model.places:
                if place.id == place_id:
                    return place
        return None
    
    def _get_transition_name(self, trans_id: str) -> str:
        """Get transition name from model."""
        if self.model and hasattr(self.model, 'transitions'):
            for trans in self.model.transitions:
                if trans.id == trans_id:
                    return getattr(trans, 'name', trans_id)
        return trans_id
