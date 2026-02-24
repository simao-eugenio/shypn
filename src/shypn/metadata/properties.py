"""
Dose-response and inferred properties metadata section.

Captures metrics computed during sweep analysis like homeostasis,
Hill coefficients, and other emergent properties.
"""

from typing import Dict, Any, Optional

from .base import MetadataSection, EditableField


class DoseResponseMetrics(MetadataSection):
    """Metadata about inferred dose-response characteristics."""
    
    # Editable threshold for homeostasis detection
    EDITABLE_FIELDS = {
        'Homeostasis_CV_Threshold': EditableField(
            float,
            default=1.0,
            min_value=0.01,
            max_value=10.0,
            description='CV threshold (%) for homeostasis detection'
        )
    }
    
    def __init__(self):
        super().__init__("Inferred Properties")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect inferred properties from context.
        
        Expected context keys:
            - homeostasis_detected: bool
            - homeostasis_metric: str (e.g., 'P2_AUC')
            - homeostasis_cv: float
            - sensitivity_metric: str (e.g., 'P2_initial_slope')
            - sensitivity_cv: float
            - hill_coefficient: float (if fitted)
            - k50: float (if fitted)
            - response_variable: str
            - fit_r_squared: float
        """
        # Homeostasis detection
        homeostasis = context.get('homeostasis_detected', False)
        self.add_field('Homeostasis_Detected', homeostasis)
        
        if homeostasis:
            metric = context.get('homeostasis_metric', 'unknown')
            self.add_field('Homeostasis_Metric', metric)
            
            cv = context.get('homeostasis_cv')
            if cv is not None:
                self.add_field('Homeostasis_CV', f"{cv:.2f}%")
        
        # ATP/parameter sensitivity
        sensitivity_metric = context.get('sensitivity_metric')
        if sensitivity_metric:
            self.add_field('ATP_Sensitivity_Metric', sensitivity_metric)
            
            sensitivity_cv = context.get('sensitivity_cv')
            if sensitivity_cv is not None:
                self.add_field('ATP_Sensitivity_CV', f"{sensitivity_cv:.2f}%")
        
        # Hill equation parameters (if fitted)
        hill_coeff = context.get('hill_coefficient')
        if hill_coeff is not None:
            self.add_field('Hill_Coefficient', round(hill_coeff, 3))
        
        k50 = context.get('k50')
        if k50 is not None:
            units = context.get('sweep_units', 'µM')
            self.add_field('K50_ATP', f"{k50:.1f} {units}")
        
        response_var = context.get('response_variable')
        if response_var:
            self.add_field('Response_Variable', response_var)
        
        r_squared = context.get('fit_r_squared')
        if r_squared is not None:
            self.add_field('Fit_R_Squared', round(r_squared, 4))
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate dose-response metrics."""
        # Optional section - no strict requirements
        return True, None


class ParametrizationState(MetadataSection):
    """Metadata about model parametrization state."""
    
    def __init__(self):
        super().__init__("Parametrization State")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect critical parametrization information.
        
        Expected context keys:
            - model: Loaded model dictionary
            - critical_places: List of place IDs to document
            - phase: Phase identifier (e.g., 'Phase_0', 'Phase_1')
            - stoichiometry_arcs: List of arc IDs to verify
        """
        model = context.get('model')
        if not model:
            raise ValueError("Context must contain 'model'")
        
        # Document critical place initial conditions
        critical_places = context.get('critical_places', [])
        property_overrides = context.get('property_overrides', {})
        
        self.add_field('', '# Critical pool initial conditions', '')
        
        for place in model.get('places', []):
            place_id = place.get('id')
            
            if place_id in critical_places or not critical_places:
                name = place.get('name', place_id)
                # Use override value if present (actual swept value), else model baseline.
                # Sweep overrides use 'place_id.initial_marking' as key; fall back to bare
                # 'place_id' key, then to the model's stored baseline.
                marking = property_overrides.get(
                    f'{place_id}.initial_marking',
                    property_overrides.get(place_id, place.get('initial_marking', 0))
                )
                units = 'µM'  # Could be context-specific
                
                self.add_field(
                    f"{place_id}_{name}",
                    f"{marking} {units}"
                )
        
        # Document Phase information
        phase = context.get('phase')
        if phase:
            self.add_field('Current_Phase', phase)
        
        # Verify stoichiometry arcs
        stoich_arcs = context.get('stoichiometry_arcs', [])
        if stoich_arcs:
            self.add_field('', '# ATP hydrolysis arcs', '')
            
            for arc in model.get('arcs', []):
                arc_id = arc.get('id')
                
                if arc_id in stoich_arcs:
                    source = arc.get('source_id')
                    target = arc.get('target_id')
                    weight = arc.get('weight', 1.0)
                    
                    # Get transition name
                    trans_name = self._get_transition_name(model, source)
                    target_name = self._get_place_name(model, target)
                    
                    self.add_field(
                        f"Arc_{arc_id}_{source}_{target_name}",
                        weight,
                        f"{trans_name} → {target_name}"
                    )
            
            status = 'VERIFIED' if all(
                self._verify_arc(model, arc_id) for arc_id in stoich_arcs
            ) else 'INCOMPLETE'
            
            self.add_field('Stoichiometry_Status', status)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parametrization state."""
        stoich_status = self.get_field('Stoichiometry_Status')
        
        if stoich_status == 'INCOMPLETE':
            return False, "Stoichiometry verification incomplete"
        
        return True, None
    
    @staticmethod
    def _get_transition_name(model: Dict[str, Any], trans_id: str) -> str:
        """Get transition name."""
        for trans in model.get('transitions', []):
            if trans.get('id') == trans_id:
                return trans.get('name', trans_id)
        return trans_id
    
    @staticmethod
    def _get_place_name(model: Dict[str, Any], place_id: str) -> str:
        """Get place name."""
        for place in model.get('places', []):
            if place.get('id') == place_id:
                return place.get('name', place_id)
        return place_id
    
    @staticmethod
    def _verify_arc(model: Dict[str, Any], arc_id: str) -> bool:
        """Verify arc exists in model."""
        for arc in model.get('arcs', []):
            if arc.get('id') == arc_id:
                return True
        return False
