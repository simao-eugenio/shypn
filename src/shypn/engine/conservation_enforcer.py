#!/usr/bin/env python3
"""Mass Conservation Enforcer for SHYPN Engine.

Provides runtime verification and correction of mass conservation violations
in Petri net simulations. Addresses numerical drift and mode switching artifacts.

Usage:
    enforcer = ConservationEnforcer(model)
    enforcer.add_conservation_group('energy', ['ATP_pool', 'ADP_pool', 'Pi_pool'], 15.0)
    
    # After each firing step
    violations = enforcer.verify_and_correct()
    if violations:
        logger.warning(f"Corrected {len(violations)} conservation violations")
"""

import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class ConservationGroup:
    """Defines a set of places whose total mass should be conserved.
    
    Example: ATP + ADP + Pi = constant (energy conservation)
    """
    name: str
    place_ids: List[str]
    expected_total: float
    tolerance: float = 1e-6  # Allowable numerical error
    auto_correct: bool = True  # Automatically fix violations


class ConservationEnforcer:
    """Enforces mass conservation during simulation.
    
    Tracks conservation groups and corrects violations by proportionally
    adjusting tokens to restore the expected total.
    
    Implementation details:
    - Phase 1: Detect violations (sum of tokens != expected total)
    - Phase 2: Calculate correction factor
    - Phase 3: Apply corrections proportionally to each place
    
    This prevents:
    - Floating-point drift in RK4 integration
    - Token loss during mode switching (adaptive behavior)
    - Rounding errors in stochastic burst firing
    """
    
    def __init__(self, model):
        """Initialize conservation enforcer.
        
        Args:
            model: Petri net model with places
        """
        self.model = model
        self.conservation_groups: Dict[str, ConservationGroup] = {}
        self.logger = logging.getLogger(__name__)
        
        # Statistics tracking
        self.total_corrections = 0
        self.max_violation = 0.0
        
    def add_conservation_group(
        self, 
        name: str, 
        place_ids: List[str], 
        expected_total: Optional[float] = None,
        tolerance: float = 1e-6,
        auto_correct: bool = True
    ):
        """Register a conservation group.
        
        Args:
            name: Human-readable group name (e.g., "energy_cycle", "carbon_balance")
            place_ids: List of place IDs that should conserve mass
            expected_total: Expected sum of tokens (if None, uses current sum)
            tolerance: Allowable numerical error before correction
            auto_correct: Whether to automatically fix violations
        """
        # Calculate initial total if not provided
        if expected_total is None:
            expected_total = self._calculate_total(place_ids)
        
        group = ConservationGroup(
            name=name,
            place_ids=place_ids,
            expected_total=expected_total,
            tolerance=tolerance,
            auto_correct=auto_correct
        )
        
        self.conservation_groups[name] = group
        self.logger.info(
            f"Added conservation group '{name}': {place_ids} (total={expected_total:.6f})"
        )
    
    def auto_detect_conservation_groups(self) -> List[ConservationGroup]:
        """Automatically detect potential conservation groups.
        
        Uses heuristics:
        1. Find strongly connected components in the Petri net
        2. Group places that form closed cycles
        3. Look for compound families (ATP/ADP/AMP, NAD/NADH, etc.)
        
        Returns:
            List of detected conservation groups (not yet registered)
        """
        # TODO: Implement SCC detection
        # TODO: Implement compound family matching
        groups = []
        self.logger.info("Auto-detection not yet implemented")
        return groups
    
    def verify_and_correct(self) -> List[Dict[str, any]]:
        """Check all conservation groups and apply corrections if needed.
        
        Returns:
            List of violations detected and corrected
        """
        violations = []
        
        for name, group in self.conservation_groups.items():
            actual_total = self._calculate_total(group.place_ids)
            error = abs(actual_total - group.expected_total)
            
            if error > group.tolerance:
                # Violation detected
                violation_info = {
                    'group': name,
                    'expected': group.expected_total,
                    'actual': actual_total,
                    'error': error,
                    'percent': (error / group.expected_total * 100) if group.expected_total > 0 else 0
                }
                
                self.logger.debug(
                    f"Conservation violation in '{name}': "
                    f"expected={group.expected_total:.6f}, "
                    f"actual={actual_total:.6f}, "
                    f"error={error:.6f} ({violation_info['percent']:.3f}%)"
                )
                
                # Apply correction if enabled
                if group.auto_correct:
                    self._correct_group(group, actual_total)
                    violation_info['corrected'] = True
                else:
                    violation_info['corrected'] = False
                
                violations.append(violation_info)
                self.total_corrections += 1
                self.max_violation = max(self.max_violation, error)
        
        return violations
    
    def _calculate_total(self, place_ids: List[str]) -> float:
        """Sum tokens across all places in the group.
        
        Args:
            place_ids: List of place IDs
            
        Returns:
            Total token count
        """
        total = 0.0
        
        # Handle both dict and list formats
        if hasattr(self.model, 'places'):
            places = self.model.places
            if isinstance(places, dict):
                for place_id in place_ids:
                    if place_id in places:
                        total += places[place_id].tokens
            else:
                # List format
                for place in places:
                    if place.id in place_ids:
                        total += place.tokens
        
        return total
    
    def _correct_group(self, group: ConservationGroup, actual_total: float):
        """Proportionally correct token counts to enforce conservation.
        
        Strategy:
        - Calculate correction factor: expected / actual
        - Multiply each place's tokens by this factor
        - Preserves relative proportions while fixing total
        
        Example:
            Expected: 15.0 mM
            Actual: 14.5 mM (loss of 0.5 mM)
            Factor: 15.0 / 14.5 = 1.0345
            ATP: 5.0 × 1.0345 = 5.172
            ADP: 4.5 × 1.0345 = 4.655
            Pi:  5.0 × 1.0345 = 5.172
            New total: 5.172 + 4.655 + 5.172 = 15.0 ✓
        
        Args:
            group: Conservation group to correct
            actual_total: Current (incorrect) total
        """
        if actual_total < 1e-12:
            # All places empty - can't correct proportionally
            # Distribute expected total equally
            per_place = group.expected_total / len(group.place_ids)
            self._set_tokens_by_ids(group.place_ids, per_place)
            return
        
        # Calculate correction factor
        correction_factor = group.expected_total / actual_total
        
        # Apply correction to each place
        places = self.model.places
        if isinstance(places, dict):
            for place_id in group.place_ids:
                if place_id in places:
                    place = places[place_id]
                    corrected_tokens = place.tokens * correction_factor
                    place.set_tokens(corrected_tokens)
        else:
            # List format
            for place in places:
                if place.id in group.place_ids:
                    corrected_tokens = place.tokens * correction_factor
                    place.set_tokens(corrected_tokens)
        
        self.logger.debug(
            f"Applied correction to '{group.name}': factor={correction_factor:.6f}"
        )
    
    def _set_tokens_by_ids(self, place_ids: List[str], value: float):
        """Set all places to same token value."""
        places = self.model.places
        if isinstance(places, dict):
            for place_id in place_ids:
                if place_id in places:
                    places[place_id].set_tokens(value)
        else:
            for place in places:
                if place.id in place_ids:
                    place.set_tokens(value)
    
    def get_statistics(self) -> Dict[str, any]:
        """Return conservation enforcement statistics.
        
        Returns:
            Dictionary with correction counts and max violation
        """
        return {
            'total_corrections': self.total_corrections,
            'max_violation_observed': self.max_violation,
            'num_groups': len(self.conservation_groups)
        }
    
    def reset_statistics(self):
        """Reset correction counters."""
        self.total_corrections = 0
        self.max_violation = 0.0
