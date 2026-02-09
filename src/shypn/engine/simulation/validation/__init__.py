#!/usr/bin/env python3
"""Thermodynamic and conservation validation for Petri net simulations.

This package provides validators for checking:
- Mass conservation (token balance)
- Energy dissipation (ATP+ADP+Pi thermodynamic efficiency)
- ATP accounting (production vs consumption)

Usage:
    from shypn.engine.simulation.validation import (
        ValidatorManager,
        MassConservationValidator,
        EnergyDissipationValidator,
        ATPAccountingValidator
    )
    
    manager = ValidatorManager()
    manager.add_validator(MassConservationValidator(
        place_groups={'drug': {'P1', 'P2', 'P3'}},
        tolerance_percent=1.0
    ))
    manager.add_validator(EnergyDissipationValidator(
        expected_dissipation_range=(25.0, 35.0)
    ))
    
    # During simulation
    manager.update(time, places, transitions)
    
    # After simulation
    results = manager.validate_all()
"""

from .base_validator import BaseValidator, ValidationResult, ValidationStatus
from .mass_conservation_validator import MassConservationValidator
from .energy_dissipation_validator import EnergyDissipationValidator
from .atp_accounting_validator import ATPAccountingValidator
from .validator_manager import ValidatorManager

__all__ = [
    'BaseValidator',
    'ValidationResult',
    'ValidationStatus',
    'MassConservationValidator',
    'EnergyDissipationValidator',
    'ATPAccountingValidator',
    'ValidatorManager'
]
