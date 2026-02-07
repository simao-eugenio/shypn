"""
Conservation laws and mass balance metadata section.

Tracks conserved quantities (drug, energy, etc.) and validates
mass balance throughout the simulation.
"""

from typing import Dict, Any, Optional, List

from .base import MetadataSection


class ConservationLaws(MetadataSection):
    """Metadata about conservation laws and mass balance."""
    
    def __init__(self):
        super().__init__("Conservation Laws")
        self._conservation_sets: Dict[str, List[str]] = {}
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect conservation law information from context.
        
        Expected context keys:
            - model: Loaded model dictionary
            - conservation_sets: Dict mapping conserved quantity name to place IDs
            - initial_state: Dict of place_id -> initial concentration
            - final_state: Dict of place_id -> final concentration (if available)
        """
        model = context.get('model')
        conservation_sets = context.get('conservation_sets', {})
        initial_state = context.get('initial_state', {})
        final_state = context.get('final_state')
        
        if not model:
            raise ValueError("Context must contain 'model'")
        
        # Store conservation sets
        self._conservation_sets = conservation_sets
        
        # Calculate initial totals
        for quantity_name, place_ids in conservation_sets.items():
            initial_total = sum(
                initial_state.get(pid, 0) for pid in place_ids
            )
            
            place_names = [self._get_place_name(model, pid) for pid in place_ids]
            comment = f"{'+'.join(place_names)}"
            
            self.add_field(
                f"{quantity_name}_Total",
                initial_total,
                comment
            )
        
        # Calculate final totals and conservation errors (if final state available)
        if final_state:
            for quantity_name, place_ids in conservation_sets.items():
                final_total = sum(
                    final_state.get(pid, 0) for pid in place_ids
                )
                
                initial_total = self.get_field(f"{quantity_name}_Total", 0)
                
                if initial_total > 0:
                    error_pct = abs(final_total - initial_total) / initial_total * 100
                else:
                    error_pct = 0 if final_total == 0 else 100
                
                self.add_field(
                    f"{quantity_name}_Total_Final",
                    round(final_total, 2)
                )
                
                self.add_field(
                    f"{quantity_name}_Conservation_Error",
                    f"{error_pct:.2f}%"
                )
                
                # Overall status
                status = "PASS" if error_pct < 1.0 else "FAIL"
                self.add_field(
                    f"{quantity_name}_Balance_Status",
                    status
                )
        
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate conservation laws."""
        # Check that at least one conservation set is defined
        if not self._conservation_sets:
            return False, "No conservation sets defined"
        
        # Check for negative totals
        for key, value in self._fields.items():
            if key.endswith('_Total') and isinstance(value, (int, float)):
                if value < 0:
                    return False, f"Negative total for {key}: {value}"
        
        return True, None
    
    @staticmethod
    def _get_place_name(model: Dict[str, Any], place_id: str) -> str:
        """Get the name of a place from the model."""
        for place in model.get('places', []):
            if place.get('id') == place_id:
                name = place.get('name', place_id)
                # Simplify name for display
                return name.replace('_pool', '').replace('_', '')
        return place_id


class ValidationFlags(MetadataSection):
    """Metadata containing validation flags and quality control checks."""
    
    def __init__(self):
        super().__init__("Validation Flags")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect validation flags from context.
        
        Expected context keys:
            - trajectory_data: Simulation trajectory
            - warnings: List of warning messages
            - errors: List of error messages
            - execution_status: 'SUCCESS', 'FAILED', 'WARNING'
        """
        trajectory = context.get('trajectory_data')
        warnings = context.get('warnings', [])
        errors = context.get('errors', [])
        status = context.get('execution_status', 'SUCCESS')
        
        # Check for common issues in trajectory
        if trajectory is not None and len(trajectory) > 0:
            # Check for specific known places first (ATP, Pi)
            self._check_depletion(trajectory, 'P7', 'ATP', 'Energy_Depletion_Warning')
            
            # Also check any place with 'ATP' or 'atp' in the name
            atp_checked = False
            for place_id in trajectory.keys():
                if 'ATP' in place_id.upper() or 'ENERGY' in place_id.upper():
                    if not atp_checked:
                        self._check_depletion(trajectory, place_id, place_id, 'Resource_Depletion_Warning', threshold=1.0)
                        atp_checked = True
                        break
            
            self._check_depletion(trajectory, 'P9', 'Pi', 'Pi_Depletion_Warning')
            self._check_negative_concentrations(trajectory)
            self._check_numerical_instability(trajectory)
        else:
            # No trajectory data available
            self.add_field('Energy_Depletion_Warning', 'UNCHECKED', 'No trajectory data')
            self.add_field('Pi_Depletion_Warning', 'UNCHECKED', 'No trajectory data')
            self.add_field('Negative_Concentration_Warning', 'UNCHECKED', 'No trajectory data')
            self.add_field('Numerical_Instability_Warning', 'UNCHECKED', 'No trajectory data')
        
        # Overall execution status
        if errors:
            status = 'FAILED'
        elif warnings:
            status = 'WARNING' if status == 'SUCCESS' else status
        
        self.add_field('Execution_Status', status)
        
        # Add warning/error counts
        if warnings:
            self.add_field('Warning_Count', len(warnings))
        if errors:
            self.add_field('Error_Count', len(errors))
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate validation flags."""
        status = self.get_field('Execution_Status')
        if status == 'FAILED':
            return False, "Execution failed"
        
        return True, None
    
    def _check_depletion(
        self,
        trajectory: Dict[str, Any],
        place_id: str,
        name: str,
        field_name: str,
        threshold: float = 0.1
    ) -> None:
        """Check if a place depletes below threshold."""
        if place_id in trajectory:
            values = trajectory[place_id]
            if values and len(values) > 0:
                # Handle numpy arrays or lists
                try:
                    min_value = min(values)
                    
                    if min_value < threshold:
                        self.add_field(field_name, 'YES', f'Minimum: {min_value:.2f}')
                    else:
                        self.add_field(field_name, 'NO', f'Minimum: {min_value:.2f}')
                except (ValueError, TypeError) as e:
                    self.add_field(field_name, 'UNCHECKED', f'Invalid data: {e}')
            else:
                self.add_field(field_name, 'UNCHECKED', 'Empty trajectory')
        else:
            self.add_field(field_name, 'UNCHECKED', f'{place_id} not in model')
    
    def _check_negative_concentrations(self, trajectory: Dict[str, Any]) -> None:
        """Check for negative concentrations."""
        has_negative = False
        negative_places = []
        
        for place_id, values in trajectory.items():
            if values and len(values) > 0:
                try:
                    if any(v < 0 for v in values):
                        has_negative = True
                        negative_places.append(place_id)
                except (TypeError, ValueError):
                    pass  # Skip invalid data
        
        if has_negative:
            comment = f'Found in: {", ".join(negative_places[:3])}'
            if len(negative_places) > 3:
                comment += f' +{len(negative_places) - 3} more'
            self.add_field('Negative_Concentration_Warning', 'YES', comment)
        else:
            self.add_field('Negative_Concentration_Warning', 'NO', 'All values ≥ 0')
    
    def _check_numerical_instability(self, trajectory: Dict[str, Any]) -> None:
        """Check for numerical instability (NaN, Inf)."""
        import math
        
        has_instability = False
        unstable_places = []
        
        for place_id, values in trajectory.items():
            if values and len(values) > 0:
                try:
                    if any(math.isnan(v) or math.isinf(v) for v in values):
                        has_instability = True
                        unstable_places.append(place_id)
                except (TypeError, ValueError):
                    pass  # Skip invalid data
        
        if has_instability:
            comment = f'Found in: {", ".join(unstable_places[:3])}'
            if len(unstable_places) > 3:
                comment += f' +{len(unstable_places) - 3} more'
            self.add_field('Numerical_Instability_Warning', 'YES', comment)
        else:
            self.add_field('Numerical_Instability_Warning', 'NO', 'All values finite')
