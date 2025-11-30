#!/usr/bin/env python3
"""JSON exporter for complete simulation data.

Exports simulation data with full metadata, parameters, and time series
in a structured JSON format suitable for archival and sharing.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import statistics


class JSONSimulationExporter:
    """Export simulation data to JSON format.
    
    Includes:
    - Complete metadata
    - Simulation parameters
    - Time-series data for all entities
    - Summary statistics
    """
    
    def __init__(self, simulation_data: dict, metadata: Optional[dict] = None, model=None):
        """Initialize JSON exporter.
        
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
    
    def export(self, filepath: str, 
               include_metadata: bool = True,
               include_timeseries: bool = True,
               include_statistics: bool = True) -> bool:
        """Export complete simulation data to JSON.
        
        Args:
            filepath: Output file path
            include_metadata: Include metadata section
            include_timeseries: Include time-series data
            include_statistics: Include summary statistics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output = {}
            
            if include_metadata:
                output['metadata'] = self._build_metadata_section()
            
            if include_timeseries:
                output['time_points'] = [float(t) for t in self.time_points]
                output['places'] = self._build_places_section()
                output['transitions'] = self._build_transitions_section()
            
            if include_statistics:
                output['statistics'] = self._calculate_statistics()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting JSON: {e}")
            return False
    
    def _build_metadata_section(self) -> dict:
        """Build metadata section."""
        model_name = "Unknown"
        if self.model:
            model_name = getattr(self.model, 'name', 
                               getattr(self.model, 'id', 'Untitled'))
        elif self.metadata:
            model_name = self.metadata.get('model_name', 'Unknown')
        
        # Get simulation parameters from stored metadata
        stored_metadata = self.simulation_data.get('metadata', {})
        
        return {
            'model_name': model_name,
            'timestamp': stored_metadata.get('timestamp', datetime.now().isoformat()),
            'shypn_version': '2.0',
            'simulation_parameters': {
                'time_step': stored_metadata.get('time_step'),
                'target_duration': stored_metadata.get('target_duration'),
                'actual_duration': stored_metadata.get('duration', 
                                 self.time_points[-1] if self.time_points else 0),
                'time_scale': stored_metadata.get('time_scale', 1.0),
                'num_time_points': len(self.time_points),
                'method': 'Gillespie SSA'
            }
        }
    
    def _build_places_section(self) -> dict:
        """Build places data section with units and names."""
        places = {}
        
        for place_id, values in self.place_data.items():
            place_name = place_id
            unit = 'mM'
            initial_tokens = values[0] if values else 0
            final_tokens = values[-1] if values else 0
            
            # Get place details from model
            if self.model and hasattr(self.model, 'places'):
                for place in self.model.places:
                    if place.id == place_id:
                        place_name = getattr(place, 'name', place_id)
                        unit = getattr(place, 'unit', 'mM')
                        
                        # Convert tokens to concentration if scale factor exists
                        if hasattr(place, 'scale_factor') and place.scale_factor:
                            initial = initial_tokens / place.scale_factor
                            final = final_tokens / place.scale_factor
                            converted_series = [v / place.scale_factor for v in values]
                        else:
                            initial = initial_tokens
                            final = final_tokens
                            converted_series = values
                        
                        places[place_id] = {
                            'name': place_name,
                            'unit': unit,
                            'initial': round(initial, 6),
                            'final': round(final, 6),
                            'time_series': [round(v, 6) for v in converted_series]
                        }
                        break
            else:
                # No model available, use raw values
                places[place_id] = {
                    'name': place_name,
                    'unit': unit,
                    'initial': initial_tokens,
                    'final': final_tokens,
                    'time_series': values
                }
        
        return places
    
    def _build_transitions_section(self) -> dict:
        """Build transitions data section with rates."""
        transitions = {}
        
        for trans_id, values in self.transition_data.items():
            trans_name = trans_id
            rate = None
            total_firings = values[-1] if values else 0
            
            # Get transition details from model
            if self.model and hasattr(self.model, 'transitions'):
                for trans in self.model.transitions:
                    if trans.id == trans_id:
                        trans_name = getattr(trans, 'name', trans_id)
                        rate = getattr(trans, 'rate', None)
                        break
            
            transitions[trans_id] = {
                'name': trans_name,
                'rate': rate,
                'total_firings': int(total_firings),
                'time_series': [int(v) for v in values]
            }
        
        return transitions
    
    def _calculate_statistics(self) -> dict:
        """Calculate overall simulation statistics."""
        total_firings = 0
        for values in self.transition_data.values():
            if values:
                total_firings += values[-1]
        
        sim_time = self.time_points[-1] if self.time_points else 0
        
        # Check for steady state (simple heuristic: last 10% has low variance)
        steady_state_reached = False
        if self.time_points:
            # Check if any place shows stable concentrations
            for place_id, values in self.place_data.items():
                if len(values) > 10:
                    last_10_percent = values[-len(values)//10:]
                    if len(last_10_percent) > 1:
                        stddev = statistics.stdev(last_10_percent)
                        mean = statistics.mean(last_10_percent)
                        if mean > 0 and (stddev / mean) < 0.01:  # <1% coefficient of variation
                            steady_state_reached = True
                            break
        
        return {
            'total_firings': int(total_firings),
            'simulation_time': float(sim_time),
            'num_time_points': len(self.time_points),
            'num_places': len(self.place_data),
            'num_transitions': len(self.transition_data),
            'steady_state_reached': steady_state_reached,
            'avg_firing_rate': float(total_firings / sim_time) if sim_time > 0 else 0
        }
