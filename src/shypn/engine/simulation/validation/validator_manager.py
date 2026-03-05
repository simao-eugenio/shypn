#!/usr/bin/env python3
"""Validator manager to orchestrate multiple thermodynamic validators.

Manages lifecycle of all validators during simulation:
- Reset before simulation
- Update at recording intervals
- Validate at end or checkpoints
- Aggregate results for reporting
"""

from typing import List, Dict, Any, Optional
from .base_validator import BaseValidator, ValidationResult, ValidationStatus


class ValidatorManager:
    """Manages multiple validators during simulation.
    
    Centralizes validator lifecycle management and provides
    unified interface for simulation controllers.
    
    Usage:
        manager = ValidatorManager()
        manager.add_validator(MassConservationValidator(...))
        manager.add_validator(EnergyDissipationValidator(...))
        
        manager.reset()  # Before simulation
        
        # During simulation
        for step in simulation:
            manager.update(time, places, transitions)
        
        # After simulation
        results = manager.validate_all()
        summary = manager.get_summary()
    """
    
    def __init__(self) -> None:
        """Initialize validator manager."""
        self._validators: List[BaseValidator] = []
        self._enabled = True
    
    def add_validator(self, validator: BaseValidator) -> None:
        """Add a validator to the manager.
        
        Args:
            validator: Validator instance to add
        """
        self._validators.append(validator)
    
    def remove_validator(self, validator_name: str) -> bool:
        """Remove a validator by name.
        
        Args:
            validator_name: Name of validator to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, validator in enumerate(self._validators):
            if validator.name == validator_name:
                self._validators.pop(i)
                return True
        return False
    
    def get_validator(self, validator_name: str) -> Optional[BaseValidator]:
        """Get a validator by name.
        
        Args:
            validator_name: Name of validator to retrieve
            
        Returns:
            Validator instance or None if not found
        """
        for validator in self._validators:
            if validator.name == validator_name:
                return validator
        return None
    
    def reset(self) -> None:
        """Reset all validators for new simulation."""
        for validator in self._validators:
            validator.reset()
    
    def update(self, time: float, places: Dict[str, Any], transitions: Dict[str, Any]) -> None:
        """Update all validators with current simulation state.
        
        Args:
            time: Current simulation time
            places: Dict of place_id -> Place object
            transitions: Dict of transition_id -> Transition object
        """
        if not self._enabled:
            return
        
        for validator in self._validators:
            try:
                validator.update(time, places, transitions)
            except Exception as e:
                # Log error but continue with other validators
                print(f"Warning: Validator {validator.name} update failed: {e}")
    
    def validate_all(self) -> List[ValidationResult]:
        """Run validation on all validators.
        
        Returns:
            List of ValidationResult objects, one per validator
        """
        results = []
        
        for validator in self._validators:
            try:
                result = validator.validate()
                results.append(result)
            except Exception as e:
                # Create error result for failed validator
                results.append(ValidationResult(
                    validator_name=validator.name,
                    status=ValidationStatus.FAIL,
                    message=f"Validation failed with error: {str(e)}",
                    details={'error': str(e)}
                ))
        
        return results
    
    def get_all_results(self) -> Dict[str, List[ValidationResult]]:
        """Get all validation results from all validators.
        
        Returns:
            Dict mapping validator_name -> list of results
        """
        results_by_validator = {}
        
        for validator in self._validators:
            results_by_validator[validator.name] = validator.get_results()
        
        return results_by_validator
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all validator results.
        
        Returns:
            Dict with overall status and per-validator summaries
        """
        validator_summaries = []
        overall_status = ValidationStatus.PASS
        
        for validator in self._validators:
            summary = validator.get_summary()
            validator_summaries.append(summary)
            
            # Determine overall status (worst case)
            worst_status = summary.get('worst_status', 'PASS')
            if worst_status == 'FAIL':
                overall_status = ValidationStatus.FAIL
            elif worst_status == 'WARNING' and overall_status != ValidationStatus.FAIL:
                overall_status = ValidationStatus.WARNING
        
        return {
            'overall_status': overall_status.value,
            'num_validators': len(self._validators),
            'validator_summaries': validator_summaries
        }
    
    def is_passing(self) -> bool:
        """Check if all validators are passing.
        
        Returns:
            True if all validators passed their latest check
        """
        return all(validator.is_passing() for validator in self._validators)
    
    def enable(self) -> None:
        """Enable all validators."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable all validators."""
        self._enabled = False
    
    def __len__(self) -> int:
        """Get number of validators."""
        return len(self._validators)
    
    def __iter__(self) -> Any:
        """Iterate over validators."""
        return iter(self._validators)
