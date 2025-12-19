"""
Concentration Calculator

Handles amount ↔ concentration conversion using compartment volumes.
"""

from typing import Dict
import logging

from ..pathway_data import Compartment


class ConcentrationCalculator:
    """
    Handles amount ↔ concentration conversion using compartment volumes.
    
    Responsibilities:
    - Convert amount (moles) to concentration (M)
    - Convert concentration to amount
    - Handle multi-compartment models correctly
    
    Formulas:
        concentration = amount / volume
        amount = concentration × volume
    
    Usage:
        calc = ConcentrationCalculator(compartments)
        conc = calc.amount_to_concentration(amount=1.0, compartment_id='cytosol')
    """
    
    def __init__(self, compartments: Dict[str, Compartment]):
        """
        Initialize calculator with compartment information.
        
        Args:
            compartments: Dict mapping compartment IDs to Compartment objects
        """
        self.compartments = compartments
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def amount_to_concentration(self, 
                                amount: float, 
                                compartment_id: str) -> float:
        """
        Convert amount (substance units) to concentration.
        
        Formula: concentration = amount / volume
        
        Args:
            amount: Amount in substance units (e.g., moles)
            compartment_id: Compartment ID
            
        Returns:
            Concentration (e.g., molar)
        """
        if compartment_id in self.compartments:
            volume = self.compartments[compartment_id].size
            if volume > 0:
                concentration = amount / volume
                self.logger.debug(
                    f"Converted {amount} mol ({compartment_id}) → "
                    f"{concentration} M (volume={volume} L)"
                )
                return concentration
            else:
                self.logger.warning(
                    f"Compartment '{compartment_id}' has zero volume, "
                    f"cannot convert amount to concentration"
                )
                return amount
        
        self.logger.warning(
            f"Unknown compartment '{compartment_id}', assuming volume=1.0 L"
        )
        return amount
    
    def concentration_to_amount(self,
                                concentration: float,
                                compartment_id: str) -> float:
        """
        Convert concentration to amount (substance units).
        
        Formula: amount = concentration × volume
        
        Args:
            concentration: Concentration (e.g., molar)
            compartment_id: Compartment ID
            
        Returns:
            Amount in substance units (e.g., moles)
        """
        if compartment_id in self.compartments:
            volume = self.compartments[compartment_id].size
            amount = concentration * volume
            self.logger.debug(
                f"Converted {concentration} M ({compartment_id}) → "
                f"{amount} mol (volume={volume} L)"
            )
            return amount
        
        self.logger.warning(
            f"Unknown compartment '{compartment_id}', assuming volume=1.0 L"
        )
        return concentration
    
    def get_compartment_volume(self, compartment_id: str) -> float:
        """
        Get volume of a compartment.
        
        Args:
            compartment_id: Compartment ID
            
        Returns:
            Volume in liters (default 1.0 if not found)
        """
        if compartment_id in self.compartments:
            return self.compartments[compartment_id].size
        
        self.logger.warning(
            f"Unknown compartment '{compartment_id}', returning default volume 1.0 L"
        )
        return 1.0
