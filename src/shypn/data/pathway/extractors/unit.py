"""
Unit Extractor

Extracts SBML unit definitions for parameter normalization.
"""

from typing import Dict, Optional

try:
    import libsbml
except ImportError:
    libsbml = None

from ..pathway_data import UnitDefinition
from .base import BaseExtractor


class UnitExtractor(BaseExtractor[Dict[str, UnitDefinition]]):
    """
    Extracts SBML unit definitions.
    
    Responsibilities:
    - Parse <unitDefinition> elements
    - Calculate SI conversion factors
    - Provide base for parameter normalization
    
    Note:
        Full unit conversion implementation in converters/unit_converter.py
    """
    
    def extract(self) -> Dict[str, UnitDefinition]:
        """
        Extract all unit definitions from SBML model.
        
        Returns:
            Dict mapping unit IDs to UnitDefinition objects
        """
        unit_defs = {}
        
        num_units = self.model.getNumUnitDefinitions()
        self.logger.info(f"Extracting {num_units} unit definitions...")
        
        for i in range(num_units):
            sbml_unit_def = self.model.getUnitDefinition(i)
            unit_def = self._convert_unit_definition(sbml_unit_def)
            if unit_def:
                unit_defs[unit_def.id] = unit_def
                self.logger.debug(f"  - {unit_def.id}: SI factor={unit_def.si_conversion_factor}")
        
        return unit_defs
    
    def _convert_unit_definition(self, sbml_unit_def) -> Optional[UnitDefinition]:
        """
        Convert SBML unit definition to UnitDefinition object.
        
        Args:
            sbml_unit_def: libsbml UnitDefinition object
            
        Returns:
            UnitDefinition object or None if extraction fails
        """
        try:
            unit_id = sbml_unit_def.getId()
            unit_name = sbml_unit_def.getName() or unit_id
            
            base_units = []
            conversion_factor = 1.0
            
            # Process each unit component
            for j in range(sbml_unit_def.getNumUnits()):
                unit = sbml_unit_def.getUnit(j)
                
                kind = libsbml.UnitKind_toString(unit.getKind())
                exponent = unit.getExponent()
                scale = unit.getScale()
                multiplier = unit.getMultiplier()
                
                base_units.append((kind, exponent, scale, multiplier))
                
                # Calculate conversion factor
                # Formula: multiplier × 10^(scale × exponent)
                unit_factor = multiplier * (10 ** scale) ** exponent
                conversion_factor *= unit_factor
            
            return UnitDefinition(
                id=unit_id,
                name=unit_name,
                base_units=base_units,
                si_conversion_factor=conversion_factor
            )
            
        except (AttributeError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to extract unit definition '{sbml_unit_def.getId()}': {e}")
            self.add_error(f"Unit extraction error: {e}")
            return None
