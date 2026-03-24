"""
Parameter Extractor

Extracts global parameters from SBML model.
"""

from typing import Dict

try:
    import libsbml
except ImportError:
    libsbml = None

from .base import BaseExtractor


class ParameterExtractor(BaseExtractor[Dict[str, float]]):
    """
    Extracts global parameters from SBML model.
    
    Parameters are kinetic constants (e.g., Km, Vmax) used in rate laws.
    """
    
    def extract(self) -> Dict[str, float]:
        """
        Extract all global parameters from SBML model.
        
        Returns:
            Dict mapping parameter IDs to values
        """
        parameters = {}
        
        num_parameters = self.model.getNumParameters()
        self.logger.info(f"Extracting {num_parameters} parameters...")
        
        for i in range(num_parameters):
            sbml_parameter = self.model.getParameter(i)
            param_id = sbml_parameter.getId()
            param_value = sbml_parameter.getValue()
            parameters[param_id] = param_value
            self.logger.debug(f"  - {param_id}: {param_value}")
        
        return parameters
