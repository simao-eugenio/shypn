"""
Experiment-specific metadata section.

Captures information unique to each experiment in a batch/sweep,
such as experiment index, parameter values being tested, etc.
"""

from typing import Dict, Any, Optional

from .base import MetadataSection


class ExperimentMetadata(MetadataSection):
    """Metadata about the specific experiment instance."""
    
    def __init__(self):
        super().__init__("Experiment Details")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect experiment-specific information from context.
        
        Expected context keys:
            - experiment_index: Index of this experiment in batch
            - experiment_name: Name/identifier for this experiment
            - experiment_parameters: Dict of parameter values for this experiment
            - swept_parameter: Info about swept parameter (if applicable)
        """
        # Experiment identification
        exp_index = context.get('experiment_index')
        if exp_index is not None:
            self.add_field('Experiment_Index', exp_index)
        
        exp_name = context.get('experiment_name')
        if exp_name:
            self.add_field('Experiment_Name', exp_name)
        
        # Swept parameter information
        swept_param = context.get('swept_parameter')
        if swept_param:
            if isinstance(swept_param, dict):
                param_type = swept_param.get('type', 'unknown')
                param_id = swept_param.get('id', 'unknown')
                param_name = swept_param.get('name', param_id)
                param_value = swept_param.get('value', 'N/A')
                
                self.add_field('Swept_Parameter_Type', param_type.capitalize())
                self.add_field('Swept_Parameter_ID', param_id)
                self.add_field('Swept_Parameter_Name', param_name)
                self.add_field('Swept_Parameter_Value', f"{param_value:.4g}" if isinstance(param_value, (int, float)) else str(param_value))
        
        # Experiment-specific parameter values
        exp_params = context.get('experiment_parameters', {})
        
        # Places (initial markings)
        place_markings = exp_params.get('place_markings', {})
        if place_markings:
            self.add_field('', '# Place Initial Markings', '')
            for place_id, marking in sorted(place_markings.items())[:10]:  # Show first 10
                self.add_field(f'Place_{place_id}', f"{marking:.4g}" if isinstance(marking, (int, float)) else str(marking))
            
            if len(place_markings) > 10:
                self.add_field('...', f'({len(place_markings) - 10} more places)', '')
        
        # Transitions (rates)
        transition_rates = exp_params.get('transition_rates', {})
        if transition_rates:
            self.add_field('', '# Transition Rates', '')
            for trans_id, rate in sorted(transition_rates.items())[:10]:  # Show first 10
                self.add_field(f'Transition_{trans_id}', f"{rate:.4g}" if isinstance(rate, (int, float)) else str(rate))
            
            if len(transition_rates) > 10:
                self.add_field('...', f'({len(transition_rates) - 10} more transitions)', '')
        
        # Arc weights
        arc_weights = exp_params.get('arc_weights', {})
        if arc_weights and len(arc_weights) > 0:
            self.add_field('', '# Arc Weights', '')
            for arc_id, weight in sorted(arc_weights.items()):  # All arcs — needed for reproducibility
                self.add_field(f'Arc_{arc_id}', f"{weight:.4g}" if isinstance(weight, (int, float)) else str(weight))
        
        # Machine-readable sweep overrides (actual values set for this experiment)
        overrides = context.get('property_overrides', {})
        if overrides:
            self.add_field('', '# Sweep Overrides', '')
            for param_id, value in sorted(overrides.items()):
                self.add_field(
                    param_id,
                    f"{value:.6g} µM" if isinstance(value, (int, float)) else str(value)
                )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate experiment metadata."""
        # All fields are optional - this section may be empty if no experiment-specific info
        return True, None
