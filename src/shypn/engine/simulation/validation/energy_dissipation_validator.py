#!/usr/bin/env python3
"""Energy dissipation validator for ATP/ADP/Pi pools.

Validates that energy pool dissipation matches expected biological range
(typically 25-35% dissipation representing metabolic efficiency).
"""

from typing import Any, Dict, Optional, Tuple
from .base_validator import BaseValidator, ValidationResult, ValidationStatus


class EnergyDissipationValidator(BaseValidator):
    """Validates energy pool dissipation matches biological expectations.
    
    Checks that total adenylate pool (ATP + ADP + Pi) dissipates by
    an appropriate amount, representing conversion of chemical energy
    to heat according to cellular thermodynamic efficiency.
    
    Typical biological range: 25-35% dissipation
    (i.e., ~70% energy retained in chemical bonds)
    
    Attributes:
        atp_place_id: Place ID for ATP pool
        adp_place_id: Place ID for ADP pool
        pi_place_id: Place ID for Pi pool
        expected_dissipation_range: (min%, max%) acceptable dissipation
    """
    
    def __init__(
        self,
        atp_place_id: str = 'P7',
        adp_place_id: str = 'P8',
        pi_place_id: str = 'P9',
        expected_dissipation_range: Tuple[float, float] = (25.0, 35.0),
        enabled: bool = True
    ):
        """Initialize energy dissipation validator.
        
        Args:
            atp_place_id: Place ID for ATP pool (default P7)
            adp_place_id: Place ID for ADP pool (default P8)
            pi_place_id: Place ID for Pi pool (default P9)
            expected_dissipation_range: (min%, max%) acceptable dissipation
            enabled: Enable/disable validator
        """
        super().__init__(name="EnergyDissipation", enabled=enabled)
        self.atp_place_id = atp_place_id
        self.adp_place_id = adp_place_id
        self.pi_place_id = pi_place_id
        self.expected_dissipation_range = expected_dissipation_range
        
        # Track initial and final energy pools
        self._initial_energy: Optional[float] = None
        self._final_energy: Optional[float] = None
        self._min_energy: Optional[float] = None
        self._max_energy: Optional[float] = None
        
        # Track individual pools for diagnostics
        self._initial_atp: Optional[float] = None
        self._initial_adp: Optional[float] = None
        self._initial_pi: Optional[float] = None
        self._final_atp: Optional[float] = None
        self._final_adp: Optional[float] = None
        self._final_pi: Optional[float] = None
    
    def reset(self) -> None:
        """Reset validator state for new simulation."""
        super().reset()
        self._initial_energy = None
        self._final_energy = None
        self._min_energy = None
        self._max_energy = None
        self._initial_atp = None
        self._initial_adp = None
        self._initial_pi = None
        self._final_atp = None
        self._final_adp = None
        self._final_pi = None
    
    def update(self, time: float, places: Dict[str, Any], transitions: Dict[str, Any]) -> None:
        """Update validator with current simulation state.
        
        Args:
            time: Current simulation time
            places: Dict of place_id -> Place object
            transitions: Dict of transition_id -> Transition object (unused)
        """
        if not self.enabled:
            return
        
        # Get current energy pool values
        atp = places[self.atp_place_id].tokens if self.atp_place_id in places else 0.0
        adp = places[self.adp_place_id].tokens if self.adp_place_id in places else 0.0
        pi = places[self.pi_place_id].tokens if self.pi_place_id in places else 0.0
        
        total_energy = atp + adp + pi
        
        # Initialize on first update
        if self._initial_energy is None:
            self._initial_energy = total_energy
            self._min_energy = total_energy
            self._max_energy = total_energy
            self._initial_atp = atp
            self._initial_adp = adp
            self._initial_pi = pi
        else:
            # Track min/max
            self._min_energy = min(self._min_energy, total_energy)
            self._max_energy = max(self._max_energy, total_energy)
        
        # Always update final values (last update wins)
        self._final_energy = total_energy
        self._final_atp = atp
        self._final_adp = adp
        self._final_pi = pi
    
    def validate(self) -> ValidationResult:
        """Perform energy dissipation validation.
        
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
        
        if self._initial_energy is None or self._final_energy is None:
            result = ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIPPED,
                message="Insufficient data - validator not updated"
            )
            self._results.append(result)
            return result
        
        # Calculate dissipation percentage
        if self._initial_energy > 0:
            dissipation_pct = (self._initial_energy - self._final_energy) / self._initial_energy * 100
        else:
            dissipation_pct = 0.0
        
        # Check against expected range
        min_expected, max_expected = self.expected_dissipation_range
        
        if dissipation_pct < 0:
            # Energy increased - violation of thermodynamics!
            status = ValidationStatus.FAIL
            message = f"Energy increased by {abs(dissipation_pct):.1f}% - violates thermodynamics!"
        elif dissipation_pct < min_expected:
            status = ValidationStatus.WARNING
            message = f"Energy dissipation {dissipation_pct:.1f}% below expected range " + \
                     f"({min_expected}-{max_expected}%) - unusually efficient"
        elif dissipation_pct > max_expected:
            status = ValidationStatus.WARNING
            message = f"Energy dissipation {dissipation_pct:.1f}% above expected range " + \
                     f"({min_expected}-{max_expected}%) - excessive loss"
        else:
            status = ValidationStatus.PASS
            message = f"Energy dissipation {dissipation_pct:.2f}% within expected range " + \
                     f"({min_expected}-{max_expected}%)"
        
        result = ValidationResult(
            validator_name=self.name,
            status=status,
            message=message,
            value=dissipation_pct,
            expected_range=self.expected_dissipation_range,
            details={
                'initial_energy': self._initial_energy,
                'final_energy': self._final_energy,
                'min_energy': self._min_energy,
                'max_energy': self._max_energy,
                'dissipation_percent': dissipation_pct,
                'initial_atp': self._initial_atp,
                'initial_adp': self._initial_adp,
                'initial_pi': self._initial_pi,
                'final_atp': self._final_atp,
                'final_adp': self._final_adp,
                'final_pi': self._final_pi
            }
        )
        
        self._results.append(result)
        return result
