#!/usr/bin/env python3
"""CSV exporter for simulation time-series data.

Exports simulation data in CSV format with two layout options:
- Wide format: One column per species/reaction
- Long format: Tidy data with Entity/Type/Value columns
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional
import logging
import statistics

logger = logging.getLogger(__name__)


class CSVSimulationExporter:
    """Export simulation data to CSV format.
    
    Supports:
    - Wide format (one column per species)
    - Long/tidy format (entity-type-value)
    - Summary statistics only
    """
    
    def __init__(self, simulation_data: dict, metadata: Optional[dict] = None, accounting_data: Optional[dict] = None):
        """Initialize CSV exporter.
        
        Args:
            simulation_data: Dict with 'time_points', 'place_data', 'transition_data', 'model', 'validation_results'
            metadata: Optional metadata dict
            accounting_data: Optional token accounting report dict
        """
        self.simulation_data = simulation_data
        self.metadata = metadata or {}
        self.accounting_data = accounting_data
        self.time_points = simulation_data.get('time_points', [])
        self.place_data = simulation_data.get('place_data', {})
        self.transition_data = simulation_data.get('transition_data', {})
        self.model = simulation_data.get('model')
        self.validation_results = simulation_data.get('validation_results')
        # Lazy-built lookup caches — avoids repeated O(N) scans through model lists
        self._place_cache: Dict[str, Any] = {}
        self._transition_cache: Dict[str, Any] = {}
    
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
                    place_headers.append((place_id, header, unit))  # Store unit for conversion
                    headers.append(header)
                
                # Add transition columns
                transition_headers = []
                for trans_id in sorted(self.transition_data.keys()):
                    trans_name = self._get_transition_name(trans_id)
                    header = f"{trans_name} (firings)"
                    transition_headers.append((trans_id, header))
                    headers.append(header)
                
                # Add accounting columns if available
                if self.accounting_data:
                    headers.append('Accounting: Total Consumed')
                    headers.append('Accounting: Total Produced')
                    headers.append('Accounting: Net Change')
                
                writer.writerow(headers)
                
                # Write accounting summary row if available
                if self.accounting_data:
                    stats = self.accounting_data.get('statistics', {})
                    summary_row = ['# Token Accounting Summary']
                    summary_row.extend([''] * (len(place_headers) + len(transition_headers)))
                    summary_row.append(f"{stats.get('total_consumed', 0):.6f}")
                    summary_row.append(f"{stats.get('total_produced', 0):.6f}")
                    summary_row.append(f"{stats.get('net_change', 0):+.6f}")
                    writer.writerow(summary_row)
                    
                    status_row = ['# Conservation Status']
                    status_row.extend([''] * (len(place_headers) + len(transition_headers)))
                    status = 'PASS' if self.accounting_data.get('global_conservation') else 'FAIL'
                    leak = self.accounting_data.get('total_leak', 0)
                    status_row.append(f'{status} (leak: {leak:+.6f})')
                    status_row.extend([''] * 2)
                    writer.writerow(status_row)
                    
                    # Add firing count validation row
                    firing_status_row = ['# Firing Count Validation']
                    firing_status_row.extend([''] * (len(place_headers) + len(transition_headers)))
                    firing_valid = self.accounting_data.get('firing_counts_valid', True)
                    num_discrepancies = stats.get('num_firing_discrepancies', 0)
                    firing_status = 'PASS' if firing_valid else f'FAIL ({num_discrepancies} discrepancies)'
                    firing_status_row.append(firing_status)
                    firing_status_row.extend([''] * 2)
                    writer.writerow(firing_status_row)
                
                # Write thermodynamic validation results if available
                if self.validation_results:
                    validator_summaries = self.validation_results.get('validator_summaries', [])
                    overall_status = self.validation_results.get('overall_status', 'NO_DATA')
                    
                    # Overall status header
                    validation_header_row = ['# Thermodynamic Validation']
                    validation_header_row.extend([''] * (len(place_headers) + len(transition_headers)))
                    validation_header_row.append(f'Overall: {overall_status}')
                    validation_header_row.extend([''] * 2)
                    writer.writerow(validation_header_row)
                    
                    # Per-validator results
                    for summary in validator_summaries:
                        validator_name = summary.get('validator', 'Unknown')
                        worst_status = summary.get('worst_status', 'NO_DATA')
                        latest_result = summary.get('latest_result')
                        
                        validator_row = [f'#   {validator_name}']
                        validator_row.extend([''] * (len(place_headers) + len(transition_headers)))
                        
                        if latest_result:
                            message = latest_result.get('message', 'No message')
                            validator_row.append(f'{worst_status}: {message}')
                        else:
                            validator_row.append(f'{worst_status}')
                        
                        validator_row.extend([''] * 2)
                        writer.writerow(validator_row)
                
                # Write data rows
                for i, time in enumerate(self.time_points):
                    row = [f"{time:.6f}"]
                    
                    # Add place values (apply scale_factor so exported values are in model units)
                    for place_id, _, unit in place_headers:
                        if i < len(self.place_data[place_id]):
                            _, value = self.place_data[place_id][i]  # Extract value from (time, tokens) tuple
                            scale = self._get_place_scale_factor(place_id)
                            row.append(f"{value / scale:.6f}")
                        else:
                            row.append('')
                    
                    # Add transition values
                    for trans_id, _ in transition_headers:
                        if i < len(self.transition_data[trans_id]):
                            _, value = self.transition_data[trans_id][i]  # Extract value from (time, count) tuple
                            row.append(str(value))
                        else:
                            row.append('')
                    
                    writer.writerow(row)
            
            return True
        except Exception as e:
            logger.error("Error exporting CSV (wide): %s", e)
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
                    
                    scale = self._get_place_scale_factor(place_id)
                    for i, time in enumerate(self.time_points):
                        if i < len(values):
                            _, value = values[i]  # Extract value from (time, tokens) tuple
                            writer.writerow([
                                f"{time:.6f}",
                                place_name,
                                'Place',
                                f"{value / scale:.6f}",
                                unit or ''
                            ])
                
                # Write transition data
                for trans_id, values in self.transition_data.items():
                    trans_name = self._get_transition_name(trans_id)
                    
                    for i, time in enumerate(self.time_points):
                        if i < len(values):
                            entry = values[i]
                            count = entry[1] if isinstance(entry, tuple) else entry
                            writer.writerow([
                                f"{time:.6f}",
                                trans_name,
                                'Transition',
                                str(count),
                                'firings'
                            ])
            
            return True
        except Exception as e:
            logger.error("Error exporting CSV (long): %s", e)
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
                    
                    # Extract tokens from (time, tokens) tuples and apply scale_factor
                    token_values = [v[1] if isinstance(v, tuple) else v for v in values]
                    scale = self._get_place_scale_factor(place_id)
                    converted_values = [v / scale for v in token_values]
                    
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
                    
                    # Extract counts from (time, count) tuples
                    count_values = [v[1] if isinstance(v, tuple) else v for v in values]
                    stats = self._calculate_statistics(count_values)
                    
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
            logger.error("Error exporting CSV (summary): %s", e)
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
        """Get place object from model (cached)."""
        if not self._place_cache and self.model and hasattr(self.model, 'places'):
            self._place_cache = {p.id: p for p in self.model.places}
        return self._place_cache.get(place_id)

    def _get_place_scale_factor(self, place_id: str) -> float:
        """Return scale_factor for a place (1.0 if not set or zero)."""
        place = self._get_place_obj(place_id)
        if place:
            sf = getattr(place, 'scale_factor', None)
            if sf:
                return float(sf)
        return 1.0

    def _get_transition_name(self, trans_id: str) -> str:
        """Get transition name from model."""
        if self.model:
            trans = self._get_transition_obj(trans_id)
            if trans:
                return getattr(trans, 'name', trans_id)
        return trans_id

    def _get_transition_obj(self, trans_id: str):
        """Get transition object from model (cached)."""
        if not self._transition_cache and self.model and hasattr(self.model, 'transitions'):
            self._transition_cache = {t.id: t for t in self.model.transitions}
        return self._transition_cache.get(trans_id)
