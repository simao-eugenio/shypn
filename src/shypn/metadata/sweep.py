"""
Sweep configuration metadata section.

Captures parameter sweep settings and experimental design.
"""

from typing import Dict, Any, Optional

from .base import MetadataSection, EditableField


class SweepConfiguration(MetadataSection):
    """Metadata about the parameter sweep configuration."""
    
    # Define editable fields for UI
    EDITABLE_FIELDS = {
        'Sweep_Type': EditableField(
            str,
            default='Parameter_Dose_Response',
            choices=['Parameter_Dose_Response', 'Multi_Parameter', 'Time_Course', 'Stochastic_Ensemble'],
            description='Type of parameter sweep experiment'
        ),
        'N_Replicates': EditableField(
            int,
            default=3,
            min_value=1,
            max_value=1000,
            description='Number of stochastic replicates per condition'
        ),
        'Random_Seed': EditableField(
            int,
            default=42,
            min_value=0,
            description='Random seed for reproducibility'
        )
    }
    
    def __init__(self):
        super().__init__("Sweep Configuration")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect sweep configuration from context.
        
        Expected context keys:
            - sweep_type: Type of sweep
            - sweep_parameter: Parameter being swept (e.g., 'P7.initial_marking')
            - sweep_range: (min, max) tuple
            - sweep_step: Step size
            - sweep_units: Units (e.g., 'µM')
            - current_value: Current parameter value for this experiment
            - simulation_config: Dict with time_span, n_replicates, etc.
        """
        # Sweep design
        sweep_type = context.get('sweep_type', 'Parameter_Dose_Response')
        self.add_field('Sweep_Type', sweep_type)
        
        sweep_param = context.get('sweep_parameter')
        if sweep_param:
            self.add_field('Sweep_Parameter', sweep_param)
        
        sweep_range = context.get('sweep_range')
        if sweep_range:
            self.add_field('Sweep_Range', f"{sweep_range[0]}-{sweep_range[1]}")
        
        sweep_step = context.get('sweep_step')
        if sweep_step:
            self.add_field('Sweep_Step', sweep_step)
        
        sweep_units = context.get('sweep_units', 'µM')
        self.add_field('Sweep_Units', sweep_units)
        
        # Calculate total experiments
        if sweep_range and sweep_step:
            total = int((sweep_range[1] - sweep_range[0]) / sweep_step) + 1
            self.add_field('Total_Experiments', total)
        
        # Current experiment value
        current_value = context.get('current_value')
        if current_value is not None:
            param_name = sweep_param.split('.')[-1] if sweep_param else 'parameter'
            self.add_field('Current_Experiment', f"{param_name}={current_value}")
        
        # Simulation settings
        sim_config = context.get('simulation_config', {})
        
        time_span = sim_config.get('time_span', (0, 120))
        self.add_field('Time_Span', f"{time_span[0]}-{time_span[1]}")
        self.add_field('Time_Units', sim_config.get('time_units', 'seconds'))
        
        n_replicates = sim_config.get('n_replicates', 3)
        self.add_field('N_Replicates', n_replicates)
        
        random_seed = sim_config.get('random_seed', 42)
        self.add_field('Random_Seed', random_seed)
        
        solver = sim_config.get('solver', 'Gillespie_SSA')
        self.add_field('Solver', solver)
        
        timestep = sim_config.get('timestep', 'adaptive')
        self.add_field('Timestep', timestep)
        
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate sweep configuration."""
        required = ['Sweep_Type', 'Time_Span', 'N_Replicates']
        
        for field in required:
            if field not in self._fields:
                return False, f"Missing required field: {field}"
        
        # Validate ranges
        n_reps = self.get_field('N_Replicates')
        if n_reps and n_reps < 1:
            return False, "N_Replicates must be >= 1"
        
        return True, None
