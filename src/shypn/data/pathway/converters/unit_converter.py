"""
Unit Converter

Converts parameters to consistent base units using SBML unit definitions.
"""

from typing import Dict
import logging

from ..pathway_data import UnitDefinition


class UnitConverter:
    """
    Converts parameters to consistent base units.
    
    Responsibilities:
    - Apply unit definitions to parameters
    - Normalize all values to SI base units
    - Detect and warn on unit inconsistencies
    
    Usage:
        converter = UnitConverter(unit_definitions)
        si_value = converter.convert_parameter(value=5.0, units='mM')
    """
    
    def __init__(self, unit_definitions: Dict[str, UnitDefinition]):
        """
        Initialize converter with unit definitions.
        
        Args:
            unit_definitions: Dict mapping unit IDs to UnitDefinition objects
        """
        self.unit_defs = unit_definitions
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def convert_parameter(self, value: float, units: str) -> float:
        """
        Convert parameter to SI base units.
        
        Args:
            value: Parameter value
            units: Unit ID or unit kind string
            
        Returns:
            Converted value in SI units
        """
        if not units:
            return value
        
        # Check custom unit definitions first
        if units in self.unit_defs:
            unit_def = self.unit_defs[units]
            converted = value * unit_def.si_conversion_factor
            self.logger.debug(f"Converted {value} {units} → {converted} SI")
            return converted
        
        # Try predefined units
        factor = self._get_predefined_conversion(units)
        if factor != 1.0:
            converted = value * factor
            self.logger.debug(f"Converted {value} {units} → {converted} (factor={factor})")
            return converted
        
        # Unknown unit
        self.logger.warning(f"Unknown unit '{units}', no conversion applied")
        return value
    
    def _get_predefined_conversion(self, units: str) -> float:
        """
        Get conversion factor for common units.
        
        Args:
            units: Unit string
            
        Returns:
            Multiplicative conversion factor to SI base
        """
        conversions = {
            # Concentration
            'mM': 1e-3,      # millimolar → molar
            'µM': 1e-6,      # micromolar → molar
            'uM': 1e-6,      # micromolar (alternative)
            'nM': 1e-9,      # nanomolar → molar
            'pM': 1e-12,     # picomolar → molar
            
            # Volume
            'mL': 1e-3,      # milliliter → liter
            'µL': 1e-6,      # microliter → liter
            'uL': 1e-6,      # microliter (alternative)
            'nL': 1e-9,      # nanoliter → liter
            
            # Time
            'ms': 1e-3,      # millisecond → second
            'min': 60.0,     # minute → second
            'h': 3600.0,     # hour → second
            
            # Mass
            'mg': 1e-3,      # milligram → gram
            'µg': 1e-6,      # microgram → gram
            'ug': 1e-6,      # microgram (alternative)
            
            # Amount (substance)
            'mmol': 1e-3,    # millimole → mole
            'µmol': 1e-6,    # micromole → mole
            'umol': 1e-6,    # micromole (alternative)
            'nmol': 1e-9,    # nanomole → mole
            'pmol': 1e-12,   # picomole → mole
        }
        
        return conversions.get(units, 1.0)
    
    def get_available_units(self) -> Dict[str, float]:
        """
        Get all available units and their conversion factors.
        
        Returns:
            Dict mapping unit strings to SI conversion factors
        """
        available = {}
        
        # Add custom units
        for unit_id, unit_def in self.unit_defs.items():
            available[unit_id] = unit_def.si_conversion_factor
        
        # Add predefined units
        predefined = {
            'mM': 1e-3, 'µM': 1e-6, 'uM': 1e-6, 'nM': 1e-9, 'pM': 1e-12,
            'mL': 1e-3, 'µL': 1e-6, 'uL': 1e-6, 'nL': 1e-9,
            'ms': 1e-3, 'min': 60.0, 'h': 3600.0,
            'mg': 1e-3, 'µg': 1e-6, 'ug': 1e-6,
            'mmol': 1e-3, 'µmol': 1e-6, 'umol': 1e-6, 'nmol': 1e-9, 'pmol': 1e-12,
        }
        available.update(predefined)
        
        return available
