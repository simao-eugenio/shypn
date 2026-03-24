"""
Compartment Extractor

Extracts compartments (cellular locations) from SBML model.
"""

from typing import Dict

try:
    import libsbml
except ImportError:
    libsbml = None

from ..pathway_data import Compartment
from .base import BaseExtractor


class CompartmentExtractor(BaseExtractor[Dict[str, Compartment]]):
    """
    Extracts compartments (cellular locations) from SBML model.
    
    Returns enhanced Compartment objects with volume information
    for proper amount ↔ concentration conversion.
    """
    
    def extract(self) -> Dict[str, Compartment]:
        """
        Extract all compartments from SBML model.
        
        Returns:
            Dict mapping compartment IDs to Compartment objects
        """
        compartments = {}
        
        num_compartments = self.model.getNumCompartments()
        self.logger.info(f"Extracting {num_compartments} compartments...")
        
        for i in range(num_compartments):
            sbml_compartment = self.model.getCompartment(i)
            compartment = self._convert_compartment(sbml_compartment)
            if compartment:
                compartments[compartment.id] = compartment
                self.logger.debug(f"  - {compartment.id}: {compartment.name} (size={compartment.size})")
        
        return compartments
    
    def _convert_compartment(self, sbml_compartment) -> Compartment:
        """
        Convert SBML compartment to Compartment object.
        
        Args:
            sbml_compartment: libsbml Compartment object
            
        Returns:
            Compartment object with volume information
        """
        comp_id = sbml_compartment.getId()
        comp_name = sbml_compartment.getName() or comp_id
        
        # Get size (volume), default to 1.0 if not set
        comp_size = sbml_compartment.getSize() if sbml_compartment.isSetSize() else 1.0
        
        # Get spatial dimensions (3D by default)
        spatial_dims = sbml_compartment.getSpatialDimensions() if sbml_compartment.isSetSpatialDimensions() else 3
        
        # Get units
        units = None
        if sbml_compartment.isSetUnits():
            units = sbml_compartment.getUnits()
        
        # Check if constant
        constant = sbml_compartment.getConstant()
        
        return Compartment(
            id=comp_id,
            name=comp_name,
            size=comp_size,
            spatial_dimensions=int(spatial_dims),
            units=units,
            constant=constant
        )
    
    def extract_legacy(self) -> Dict[str, str]:
        """
        Extract compartments in legacy format (ID → name mapping).
        
        For backward compatibility with existing code.
        
        Returns:
            Dict mapping compartment IDs to names
        """
        compartments = {}
        
        num_compartments = self.model.getNumCompartments()
        
        for i in range(num_compartments):
            sbml_compartment = self.model.getCompartment(i)
            comp_id = sbml_compartment.getId()
            comp_name = sbml_compartment.getName() or comp_id
            compartments[comp_id] = comp_name
        
        return compartments
