#!/usr/bin/env python3
"""Utility to configure thermodynamic validators for drug discovery models.

Provides pre-configured validators matching manuscript validation criteria:
- Mass conservation: Drug species (P1+P2+P3+P4+P6 = 100 µM)
- Energy conservation: ATP+ADP+Pi (total conserved)
- Energy dissipation: 25-35% dissipation
- ATP accounting: Production >= Consumption per manuscript equation (5)
"""

from shypn.engine.simulation.validation import (
    ValidatorManager,
    MassConservationValidator,
    EnergyDissipationValidator,
    ATPAccountingValidator
)


def configure_drug_discovery_validators() -> ValidatorManager:
    """Configure validators for drug discovery models.
    
    Matches manuscript validation criteria:
    - Drug mass: P1+P2+P3+P4+P6 = 100 µM (±1%)
    - Energy total: ATP+ADP+Pi conserved (±1%)
    - Energy dissipation: 25-35% over 500s
    - ATP budget: Consumption <= Production (5% deficit tolerance)
    
    Returns:
        ValidatorManager with all validators configured
    """
    manager = ValidatorManager()
    
    # 1. Mass Conservation: Drug species
    drug_places = {'P1', 'P2', 'P3', 'P4', 'P6'}  # All drug forms
    
    # 2. Mass Conservation: Energy cycle
    energy_places = {'P7', 'P8', 'P9'}  # ATP, ADP, Pi
    
    mass_validator = MassConservationValidator(
        place_groups={
            'drug': drug_places,
            'energy': energy_places
        },
        expected_totals={
            'drug': 100.0,   # 100 µM total drug dose
            'energy': 15000.0  # 15 mM total adenylate pool (ATP+ADP+Pi)
        },
        tolerance_percent=1.0,  # ±1% acceptable deviation
        enabled=True
    )
    manager.add_validator(mass_validator)
    
    # 3. Energy Dissipation: 25-35% expected
    energy_dissipation_validator = EnergyDissipationValidator(
        atp_place_id='P7',
        adp_place_id='P8',
        pi_place_id='P9',
        expected_dissipation_range=(25.0, 35.0),  # Biological efficiency range
        enabled=True
    )
    manager.add_validator(energy_dissipation_validator)
    
    # 4. ATP Accounting: Manuscript equation (5)
    # ATP_consumed = 2×N_PEPT1 + 1×N_ABC + 0.5×N_facilitated + 4×N_proteasomal + 1×N_lysosomal
    atp_costs = {
        'T1': 2.0,  # PEPT1 active transport
        'T2': 1.0,  # ABC efflux pump
        'T3': 0.5,  # Facilitated diffusion
        'T8': 4.0,  # Proteasomal degradation
        'T9': 1.0,  # Lysosomal degradation
    }
    
    atp_validator = ATPAccountingValidator(
        transition_costs=atp_costs,
        atp_synthesis_id='T11',  # ATP synthesis transition
        allow_deficit_percent=5.0,  # 5% transient deficit acceptable
        enabled=True
    )
    manager.add_validator(atp_validator)
    
    return manager


def configure_minimal_validators() -> ValidatorManager:
    """Configure minimal validation for quick checks.
    
    Only validates critical conservation laws:
    - Drug mass conservation
    - Energy pool conservation
    
    Returns:
        ValidatorManager with basic validators
    """
    manager = ValidatorManager()
    
    mass_validator = MassConservationValidator(
        place_groups={
            'drug': {'P1', 'P2', 'P3', 'P4', 'P6'},
            'energy': {'P7', 'P8', 'P9'}
        },
        tolerance_percent=1.0,
        enabled=True
    )
    manager.add_validator(mass_validator)
    
    return manager


def configure_energy_only_validators() -> ValidatorManager:
    """Configure energy-focused validation.
    
    Only validates ATP/ADP/Pi pools:
    - Energy conservation
    - Energy dissipation
    - ATP accounting
    
    Returns:
        ValidatorManager with energy validators
    """
    manager = ValidatorManager()
    
    # Energy conservation
    mass_validator = MassConservationValidator(
        place_groups={'energy': {'P7', 'P8', 'P9'}},
        expected_totals={'energy': 15000.0},
        tolerance_percent=1.0,
        enabled=True
    )
    manager.add_validator(mass_validator)
    
    # Energy dissipation
    energy_dissipation_validator = EnergyDissipationValidator(
        expected_dissipation_range=(25.0, 35.0),
        enabled=True
    )
    manager.add_validator(energy_dissipation_validator)
    
    # ATP accounting
    atp_costs = {
        'T1': 2.0,  # PEPT1
        'T2': 1.0,  # ABC
        'T3': 0.5,  # Facilitated
        'T8': 4.0,  # Proteasomal
        'T9': 1.0,  # Lysosomal
    }
    
    atp_validator = ATPAccountingValidator(
        transition_costs=atp_costs,
        atp_synthesis_id='T11',
        allow_deficit_percent=5.0,
        enabled=True
    )
    manager.add_validator(atp_validator)
    
    return manager


# Example usage
if __name__ == '__main__':
    print("=== Drug Discovery Validator Configuration ===\n")
    
    manager = configure_drug_discovery_validators()
    
    print(f"Configured {len(manager)} validators:")
    for validator in manager:
        print(f"  - {validator.name}: {'enabled' if validator.enabled else 'disabled'}")
    
    print("\n✅ Validators ready for integration into simulation controller")
    print("   Add to controller: controller.validator_manager = configure_drug_discovery_validators()")
