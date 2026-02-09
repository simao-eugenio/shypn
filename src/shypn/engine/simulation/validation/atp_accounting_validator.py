#!/usr/bin/env python3
"""ATP accounting validator for energy-dependent processes.

Validates that ATP production exceeds or matches consumption across
all energy-dependent transitions, ensuring bioenergetic feasibility.

Implements manuscript equation (5):
ATP_consumed = 2×N_PEPT1 + 1×N_ABC + 0.5×N_facilitated + 4×N_proteasomal + 1×N_lysosomal
"""

from typing import Dict, Set
from .base_validator import BaseValidator, ValidationResult, ValidationStatus


class ATPAccountingValidator(BaseValidator):
    """Validates ATP budget: production >= consumption.
    
    Tallies ATP consumption from energy-dependent transitions and
    compares to ATP synthesis. Violations indicate bioenergetically
    impossible transport/degradation rates.
    
    Attributes:
        transition_costs: Dict mapping transition_id -> ATP cost per firing
        atp_synthesis_id: Transition ID for ATP synthesis
        allow_deficit_percent: Allow small deficit (e.g., 5% transient imbalance)
    """
    
    def __init__(
        self,
        transition_costs: Dict[str, float],
        atp_synthesis_id: str = 'T11',
        allow_deficit_percent: float = 5.0,
        enabled: bool = True
    ):
        """Initialize ATP accounting validator.
        
        Args:
            transition_costs: Dict of transition_id -> ATP cost per firing
                             e.g., {'T1': 2.0, 'T2': 1.0, 'T3': 0.5, 'T8': 4.0}
            atp_synthesis_id: Transition ID for ATP synthesis (default T11)
            allow_deficit_percent: Allow small deficit % (default 5%)
            enabled: Enable/disable validator
        """
        super().__init__(name="ATPAccounting", enabled=enabled)
        self.transition_costs = transition_costs
        self.atp_synthesis_id = atp_synthesis_id
        self.allow_deficit_percent = allow_deficit_percent
        
        # Track cumulative ATP production and consumption
        self._atp_produced: float = 0.0
        self._atp_consumed: float = 0.0
        
        # Track per-transition consumption for diagnostics
        self._consumption_by_transition: Dict[str, float] = {}
    
    def reset(self):
        """Reset validator state for new simulation."""
        super().reset()
        self._atp_produced = 0.0
        self._atp_consumed = 0.0
        self._consumption_by_transition = {}
    
    def update(self, time: float, places: Dict, transitions: Dict):
        """Update validator with current simulation state.
        
        Args:
            time: Current simulation time
            places: Dict of place_id -> Place object (unused)
            transitions: Dict of transition_id -> Transition object
        """
        if not self.enabled:
            return
        
        # Calculate ATP produced (cumulative firing count of ATP synthesis)
        if self.atp_synthesis_id in transitions:
            synthesis_transition = transitions[self.atp_synthesis_id]
            self._atp_produced = getattr(synthesis_transition, 'firing_count', 0.0)
        
        # Calculate ATP consumed (sum of cost × firing_count for each transition)
        total_consumed = 0.0
        consumption_breakdown = {}
        
        for trans_id, atp_cost in self.transition_costs.items():
            if trans_id in transitions:
                transition = transitions[trans_id]
                firing_count = getattr(transition, 'firing_count', 0.0)
                consumed = atp_cost * firing_count
                total_consumed += consumed
                consumption_breakdown[trans_id] = consumed
        
        self._atp_consumed = total_consumed
        self._consumption_by_transition = consumption_breakdown
    
    def validate(self) -> ValidationResult:
        """Perform ATP accounting validation.
        
        Returns:
            ValidationResult with PASS/WARNING/FAIL status
        """
        if not self.enabled:
            result = ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIPPED,
                message="Validator disabled"
            )
            self._results.append(result)
            return result
        
        # Check if we have data
        if self._atp_produced == 0 and self._atp_consumed == 0:
            result = ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIPPED,
                message="No ATP production or consumption detected"
            )
            self._results.append(result)
            return result
        
        # Calculate deficit/surplus
        deficit = self._atp_consumed - self._atp_produced
        
        if self._atp_consumed > 0:
            deficit_pct = (deficit / self._atp_consumed) * 100
        else:
            deficit_pct = 0.0
        
        # Determine status
        if deficit > 0:
            if deficit_pct <= self.allow_deficit_percent:
                status = ValidationStatus.WARNING
                message = f"ATP deficit {deficit:.1f} ({deficit_pct:.2f}%) within tolerance " + \
                         f"(<{self.allow_deficit_percent}%) - acceptable transient imbalance"
            else:
                status = ValidationStatus.FAIL
                message = f"ATP deficit {deficit:.1f} ({deficit_pct:.1f}%) exceeds tolerance " + \
                         f"({self.allow_deficit_percent}%) - bioenergetically impossible"
        else:
            status = ValidationStatus.PASS
            surplus = -deficit
            message = f"ATP surplus {surplus:.1f} - production ({self._atp_produced:.1f}) " + \
                     f"exceeds consumption ({self._atp_consumed:.1f})"
        
        result = ValidationResult(
            validator_name=self.name,
            status=status,
            message=message,
            value=deficit_pct,
            expected_range=(float('-inf'), self.allow_deficit_percent),
            details={
                'atp_produced': self._atp_produced,
                'atp_consumed': self._atp_consumed,
                'deficit': deficit,
                'deficit_percent': deficit_pct,
                'consumption_breakdown': self._consumption_by_transition.copy()
            }
        )
        
        self._results.append(result)
        return result
