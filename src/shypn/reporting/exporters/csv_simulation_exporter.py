#!/usr/bin/env python3
"""CSV exporter for simulation time-series data.

Exports simulation data in CSV format with two layout options:
- Wide format: One column per species/reaction
- Long format: Tidy data with Entity/Type/Value columns
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional
import statistics


class CSVSimulationExporter:
    """Export simulation data to CSV format.
    
    Supports:
    - Wide format (one column per species)
    - Long/tidy format (entity-type-value)
    - Summary statistics only
    """
    
    def __init__(self, simulation_data: dict, metadata: Optional[dict] = None):
        """Initialize CSV exporter.
        
        Args:
            simulation_data: Dict with 'time_points', 'place_data', 'transition_data', 'model'
            metadata: Optional metadata dict
        """
        self.simulation_data = simulation_data
        self.metadata = metadata or {}
        self.time_points = simulation_data.get('time_points', [])
        self.place_data = simulation_data.get('place_data', {})
        self.transition_data = simulation_data.get('transition_data', {})
        self.model = simulation_data.get('model')
    
    def export_timeseries_wide(self, filepath: str) -> bool:
        """Export time series in wide format (one column per species).
        
        Format:
            Time (s), Species1 (unit), Species2 (unit), ..., Reaction1 (firings), ...
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Build header row
                headers = ['Time (s)']
                
                # Add place columns with units
                place_headers = []
                for place_id in sorted(self.place_data.keys()):
                    place_name = self._get_place_name(place_id)
                    unit = self._get_place_unit(place_id)
                    header = f"{place_name} ({unit})" if unit else place_name
                    place_headers.append((place_id, header))
                    headers.append(header)
                
                # Add transition columns
                transition_headers = []
                for trans_id in sorted(self.transition_data.keys()):
                    trans_name = self._get_transition_name(trans_id)
                    header = f"{trans_name} (firings)"
                    transition_headers.append((trans_id, header))
                    headers.append(header)
                
                writer.writerow(headers)
                
                # Write data rows
                for i, time in enumerate(self.time_points):
                    row = [f"{time:.6f}"]
                    
                    # Add place values
                    for place_id, _ in place_headers:
                        value = self.place_data[place_id][i] if i < len(self.place_data[place_id]) else ''
                        # Convert tokens to concentration if scale factor exists
                        if self.model:
                            place = self._get_place_obj(place_id)
                            if place and hasattr(place, 'scale_factor') and place.scale_factor:
                                value = value / place.scale_factor
                        row.append(f"{value:.6f}" if value != '' else '')
                    
                    # Add transition values
                    for trans_id, _ in transition_headers:
                        value = self.transition_data[trans_id][i] if i < len(self.transition_data[trans_id]) else ''
                        row.append(str(value))
                    
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error exporting CSV (wide): {e}")
            return False
    
    def export_timeseries_long(self, filepath: str) -> bool:
        """Export time series in long/tidy format.
        
        Format:
            Time, Entity, Type, Value, Unit
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['Time', 'Entity', 'Type', 'Value', 'Unit'])
                
                # Write place data
                for place_id, values in self.place_data.items():
                    place_name = self._get_place_name(place_id)
                    unit = self._get_place_unit(place_id)
                    
                    for i, time in enumerate(self.time_points):
                        if i < len(values):
                            value = values[i]
                            # Convert tokens to concentration if scale factor exists
                            if self.model:
                                place = self._get_place_obj(place_id)
                                if place and hasattr(place, 'scale_factor') and place.scale_factor:
                                    value = value / place.scale_factor
                            
                            writer.writerow([
                                f"{time:.6f}",
                                place_name,
                                'Place',
                                f"{value:.6f}",
                                unit or ''
                            ])
                
                # Write transition data
                for trans_id, values in self.transition_data.items():
                    trans_name = self._get_transition_name(trans_id)
                    
                    for i, time in enumerate(self.time_points):
                        if i < len(values):
                            writer.writerow([
                                f"{time:.6f}",
                                trans_name,
                                'Transition',
                                str(values[i]),
                                'firings'
                            ])
            
            return True
        except Exception as e:
            print(f"Error exporting CSV (long): {e}")
            return False
    
    def export_summary_statistics(self, filepath: str) -> bool:
        """Export summary statistics only.
        
        Format:
            Entity, Type, Initial, Final, Min, Max, Mean, StdDev, Unit
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['Entity', 'Type', 'Initial', 'Final', 'Min', 'Max', 'Mean', 'StdDev', 'Unit'])
                
                # Calculate statistics for places
                for place_id, values in self.place_data.items():
                    if not values:
                        continue
                    
                    place_name = self._get_place_name(place_id)
                    unit = self._get_place_unit(place_id)
                    
                    # Convert to concentrations if needed
                    converted_values = values
                    if self.model:
                        place = self._get_place_obj(place_id)
                        if place and hasattr(place, 'scale_factor') and place.scale_factor:
                            converted_values = [v / place.scale_factor for v in values]
                    
                    stats = self._calculate_statistics(converted_values)
                    
                    writer.writerow([
                        place_name,
                        'Place',
                        f"{stats['initial']:.6f}",
                        f"{stats['final']:.6f}",
                        f"{stats['min']:.6f}",
                        f"{stats['max']:.6f}",
                        f"{stats['mean']:.6f}",
                        f"{stats['stddev']:.6f}",
                        unit or ''
                    ])
                
                # Calculate statistics for transitions
                for trans_id, values in self.transition_data.items():
                    if not values:
                        continue
                    
                    trans_name = self._get_transition_name(trans_id)
                    stats = self._calculate_statistics(values)
                    
                    writer.writerow([
                        trans_name,
                        'Transition',
                        str(stats['initial']),
                        str(stats['final']),
                        str(stats['min']),
                        str(stats['max']),
                        f"{stats['mean']:.2f}",
                        f"{stats['stddev']:.2f}",
                        'firings'
                    ])
            
            return True
        except Exception as e:
            print(f"Error exporting CSV (summary): {e}")
            return False
    
    def _calculate_statistics(self, series: List[float]) -> dict:
        """Calculate statistics for a time series.
        
        Args:
            series: List of values
            
        Returns:
            Dict with initial, final, min, max, mean, stddev
        """
        if not series:
            return {
                'initial': 0, 'final': 0, 'min': 0, 'max': 0,
                'mean': 0, 'stddev': 0
            }
        
        return {
            'initial': series[0],
            'final': series[-1],
            'min': min(series),
            'max': max(series),
            'mean': statistics.mean(series),
            'stddev': statistics.stdev(series) if len(series) > 1 else 0
        }
    
    def _get_place_name(self, place_id: str) -> str:
        """Get place name from model."""
        if self.model:
            place = self._get_place_obj(place_id)
            if place:
                return getattr(place, 'name', place_id)
        return place_id
    
    def _get_place_unit(self, place_id: str) -> str:
        """Get place unit from model."""
        if self.model:
            place = self._get_place_obj(place_id)
            if place:
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
        if self.model:
            trans = self._get_transition_obj(trans_id)
            if trans:
                return getattr(trans, 'name', trans_id)
        return trans_id
    
    def _get_transition_obj(self, trans_id: str):
        """Get transition object from model."""
        if self.model and hasattr(self.model, 'transitions'):
            for trans in self.model.transitions:
                if trans.id == trans_id:
                    return trans
        return None
