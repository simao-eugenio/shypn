#!/usr/bin/env python3
"""Base validator for thermodynamic and conservation validation.

Provides abstract interface for all simulation validators.
Each validator checks a specific conservation law or thermodynamic criterion.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Validation result status."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"  # Insufficient data


@dataclass
class ValidationResult:
    """Result from a validation check.
    
    Attributes:
        validator_name: Name of validator that produced this result
        status: PASS/WARNING/FAIL/SKIPPED
        message: Human-readable description
        value: Measured value (e.g., conservation error %)
        expected_range: Tuple of (min, max) acceptable values
        details: Additional diagnostic information
        timestamp: Simulation time when checked
    """
    validator_name: str
    status: ValidationStatus
    message: str
    value: Optional[float] = None
    expected_range: Optional[tuple] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'validator': self.validator_name,
            'status': self.status.value,
            'message': self.message,
            'value': self.value,
            'expected_range': self.expected_range,
            'details': self.details or {},
            'timestamp': self.timestamp
        }


class BaseValidator(ABC):
    """Abstract base class for thermodynamic/conservation validators.
    
    All validators follow the same pattern:
    1. Initialize with configuration (tolerance, expected values, etc.)
    2. Accumulate data during simulation
    3. Validate at checkpoints or end
    4. Return ValidationResult with status and details
    
    Subclasses implement specific validation logic:
    - MassConservationValidator: Checks token balance
    - EnergyDissipationValidator: Validates ATP+ADP+Pi dissipation
    - ATPAccountingValidator: Verifies ATP production >= consumption
    """
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize base validator.
        
        Args:
            name: Validator name for logging/reporting
            enabled: If False, validator returns SKIPPED
        """
        self.name = name
        self.enabled = enabled
        self._results: List[ValidationResult] = []
    
    @abstractmethod
    def reset(self):
        """Reset validator state for new simulation."""
        self._results = []
    
    @abstractmethod
    def update(self, time: float, places: Dict, transitions: Dict):
        """Update validator with current simulation state.
        
        Called at each recording interval during simulation.
        
        Args:
            time: Current simulation time
            places: Dict of place_id -> Place object
            transitions: Dict of transition_id -> Transition object
        """
        pass
    
    @abstractmethod
    def validate(self) -> ValidationResult:
        """Perform validation and return result.
        
        Called at end of simulation or at checkpoints.
        
        Returns:
            ValidationResult with status and details
        """
        pass
    
    def get_results(self) -> List[ValidationResult]:
        """Get all validation results collected so far."""
        return self._results.copy()
    
    def get_latest_result(self) -> Optional[ValidationResult]:
        """Get most recent validation result."""
        return self._results[-1] if self._results else None
    
    def is_passing(self) -> bool:
        """Check if latest validation passed."""
        latest = self.get_latest_result()
        return latest.status == ValidationStatus.PASS if latest else True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results.
        
        Returns:
            Dict with pass/fail counts, worst status, etc.
        """
        if not self._results:
            return {
                'validator': self.name,
                'num_checks': 0,
                'status': 'NO_DATA'
            }
        
        status_counts = {
            'PASS': sum(1 for r in self._results if r.status == ValidationStatus.PASS),
            'WARNING': sum(1 for r in self._results if r.status == ValidationStatus.WARNING),
            'FAIL': sum(1 for r in self._results if r.status == ValidationStatus.FAIL),
            'SKIPPED': sum(1 for r in self._results if r.status == ValidationStatus.SKIPPED)
        }
        
        # Determine worst status
        if status_counts['FAIL'] > 0:
            worst_status = 'FAIL'
        elif status_counts['WARNING'] > 0:
            worst_status = 'WARNING'
        elif status_counts['PASS'] > 0:
            worst_status = 'PASS'
        else:
            worst_status = 'SKIPPED'
        
        return {
            'validator': self.name,
            'num_checks': len(self._results),
            'worst_status': worst_status,
            'status_counts': status_counts,
            'latest_result': self._results[-1].to_dict() if self._results else None
        }
