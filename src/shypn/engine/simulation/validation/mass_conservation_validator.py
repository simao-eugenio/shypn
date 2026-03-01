#!/usr/bin/env python3
"""Mass conservation validator for Petri net simulations.

Checks that total tokens across specified place groups remain constant,
within a tolerance threshold. Detects numerical drift and token leaks.
"""

from typing import Dict, List, Set, Optional
from .base_validator import BaseValidator, ValidationResult, ValidationStatus


class MassConservationValidator(BaseValidator):
    """Validates mass conservation for groups of places.
    
    Tracks total tokens across specified place groups and verifies
    that the sum remains constant throughout simulation.
    
    Example:
        Drug species: P1 + P2 + P3 + P4 + P6 = 100 µM (constant)
        Energy cycle: ATP + ADP + Pi = 15000 µM (constant)
    
    Attributes:
        place_groups: Dict of group_name -> set of place IDs
        expected_totals: Dict of group_name -> expected total tokens
        tolerance_percent: Acceptable deviation (e.g., 1.0 = ±1%)
    """
    
    def __init__(
        self,
        place_groups: Dict[str, Set[str]],
        expected_totals: Optional[Dict[str, float]] = None,
        tolerance_percent: float = 1.0,
        enabled: bool = True
    ):
        """Initialize mass conservation validator.
        
        Args:
            place_groups: Dict mapping group names to sets of place IDs
                         e.g., {'drug': {'P1', 'P2', 'P3'}, 'energy': {'P7', 'P8', 'P9'}}
            expected_totals: Dict of expected totals per group (if None, uses initial)
            tolerance_percent: Allowed deviation percentage (default 1%)
            enabled: Enable/disable validator
        """
        super().__init__(name="MassConservation", enabled=enabled)
        self.place_groups = place_groups
        self.expected_totals = expected_totals or {}
        self.tolerance_percent = tolerance_percent
        
        # Track initial totals (set on first update)
        self._initial_totals: Dict[str, float] = {}
        self._current_totals: Dict[str, float] = {}
        self._min_totals: Dict[str, float] = {}
        self._max_totals: Dict[str, float] = {}
        self._initialized = False
    
    def reset(self) -> None:
        """Reset validator state for new simulation."""
        super().reset()
        self._initial_totals = {}
        self._current_totals = {}
        self._min_totals = {}
        self._max_totals = {}
        self._initialized = False
    
    def update(self, time: float, places: Dict, transitions: Dict) -> None:
        """Update validator with current simulation state.
        
        Args:
            time: Current simulation time
            places: Dict of place_id -> Place object
            transitions: Dict of transition_id -> Transition object (unused)
        """
        if not self.enabled:
            return
        
        # Calculate current totals for each group
        for group_name, place_ids in self.place_groups.items():
            total = 0.0
            for place_id in place_ids:
                if place_id in places:
                    total += places[place_id].tokens
                else:
                    # Place not found - log warning but continue
                    pass
            
            self._current_totals[group_name] = total
            
            # Initialize on first update
            if not self._initialized:
                self._initial_totals[group_name] = total
                self._min_totals[group_name] = total
                self._max_totals[group_name] = total
                
                # Use expected total if provided, otherwise use initial
                if group_name not in self.expected_totals:
                    self.expected_totals[group_name] = total
            else:
                # Track min/max
                self._min_totals[group_name] = min(self._min_totals[group_name], total)
                self._max_totals[group_name] = max(self._max_totals[group_name], total)
        
        self._initialized = True
    
    def validate(self) -> ValidationResult:
        """Perform mass conservation validation.
        
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
        
        if not self._initialized:
            result = ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIPPED,
                message="No data collected - validator not updated"
            )
            self._results.append(result)
            return result
        
        # Check each group
        violations = []
        warnings = []
        max_deviation_pct = 0.0
        
        for group_name, expected_total in self.expected_totals.items():
            current = self._current_totals.get(group_name, 0.0)
            initial = self._initial_totals.get(group_name, expected_total)
            min_val = self._min_totals.get(group_name, current)
            max_val = self._max_totals.get(group_name, current)
            
            # Calculate deviation from expected
            if expected_total != 0:
                deviation_pct = abs(current - expected_total) / expected_total * 100
            else:
                deviation_pct = abs(current - expected_total)  # Absolute error if expected is 0
            
            max_deviation_pct = max(max_deviation_pct, deviation_pct)
            
            # Check against tolerance
            if deviation_pct > self.tolerance_percent:
                violations.append({
                    'group': group_name,
                    'expected': expected_total,
                    'current': current,
                    'initial': initial,
                    'min': min_val,
                    'max': max_val,
                    'deviation_pct': deviation_pct
                })
            elif deviation_pct > self.tolerance_percent * 0.5:  # Warning at 50% of tolerance
                warnings.append({
                    'group': group_name,
                    'expected': expected_total,
                    'current': current,
                    'deviation_pct': deviation_pct
                })
        
        # Determine status
        if violations:
            status = ValidationStatus.FAIL
            message = f"Mass conservation violated in {len(violations)} group(s): " + \
                     ", ".join(f"{v['group']} ({v['deviation_pct']:.2f}%)" for v in violations)
        elif warnings:
            status = ValidationStatus.WARNING
            message = f"Mass conservation warning in {len(warnings)} group(s): " + \
                     ", ".join(f"{w['group']} ({w['deviation_pct']:.2f}%)" for w in warnings)
        else:
            status = ValidationStatus.PASS
            message = f"Mass conserved within {self.tolerance_percent}% tolerance " + \
                     f"(max deviation: {max_deviation_pct:.4f}%)"
        
        result = ValidationResult(
            validator_name=self.name,
            status=status,
            message=message,
            value=max_deviation_pct,
            expected_range=(0.0, self.tolerance_percent),
            details={
                'violations': violations,
                'warnings': warnings,
                'group_totals': self._current_totals.copy(),
                'expected_totals': self.expected_totals.copy(),
                'initial_totals': self._initial_totals.copy(),
                'min_totals': self._min_totals.copy(),
                'max_totals': self._max_totals.copy()
            }
        )
        
        self._results.append(result)
        return result
