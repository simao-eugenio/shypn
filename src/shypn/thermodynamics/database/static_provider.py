"""Static data provider for core metabolites.

Provides thermodynamic data for essential biochemical compounds
from curated literature values. No internet connection required.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from ..base import CompoundDataProviderBase
from ..models import CompoundThermodynamics

logger = logging.getLogger(__name__)


class StaticDataProvider(CompoundDataProviderBase):
    """Provide thermodynamic data from local JSON database.
    
    This provider contains curated ΔG°_f values for ~100 core metabolites
    from authoritative sources (Alberty 2003, NIST).
    
    Use cases:
    - Offline operation
    - Fallback when web services unavailable
    - Testing with known values
    
    Example:
        >>> provider = StaticDataProvider()
        >>> atp = provider.get_compound("C00002")  # ATP
        >>> print(f"ΔG°_f = {atp.delta_g_formation} kJ/mol")
    """
    
    def __init__(self, data_file: Optional[Path] = None):
        """Initialize static provider.
        
        Args:
            data_file: Path to JSON file with compound data.
                      If None, uses default core_metabolites.json
        """
        if data_file is None:
            data_file = Path(__file__).parent.parent / "data" / "core_metabolites.json"
        
        self.data_file = Path(data_file)
        self._compounds = {}
        
        self._load_data()
    
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Retrieve compound data from static database.
        
        Note: pH/temperature/ionic_strength are used to select appropriate
        data set, but corrections are not applied dynamically. Data should
        match requested conditions.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            ph: pH value (used to select data set)
            temperature: Temperature in Kelvin
            ionic_strength: Ionic strength in M
            
        Returns:
            CompoundThermodynamics if available, None otherwise
        """
        compound_data = self._compounds.get(compound_id)
        
        if compound_data is None:
            return None
        
        # Check if conditions match (within tolerance)
        stored_ph = compound_data.get("conditions", {}).get("pH", 7.0)
        stored_temp = compound_data.get("conditions", {}).get("temperature", 298.15)
        
        if abs(stored_ph - ph) > 0.5 or abs(stored_temp - temperature) > 10:
            logger.warning(
                f"Condition mismatch for {compound_id}: "
                f"requested pH={ph}, T={temperature}, "
                f"stored pH={stored_ph}, T={stored_temp}"
            )
        
        return CompoundThermodynamics(
            compound_id=compound_data["compound_id"],
            name=compound_data["name"],
            delta_g_formation=compound_data["delta_g_formation"],
            source=compound_data.get("source", "static"),
            uncertainty=compound_data.get("uncertainty", 0.0),
            conditions=compound_data.get("conditions", {
                'pH': ph,
                'temperature': temperature,
                'ionic_strength': ionic_strength
            })
        )
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound data is available.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            
        Returns:
            True if compound exists in static database
        """
        return compound_id in self._compounds
    
    def _load_data(self):
        """Load compound data from JSON file."""
        if not self.data_file.exists():
            logger.warning(f"Static data file not found: {self.data_file}")
            logger.info("StaticDataProvider will work with empty database")
            return
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            self._compounds = data.get("compounds", {})
            
            logger.info(f"Loaded {len(self._compounds)} compounds from static database")
            
        except Exception as e:
            logger.error(f"Failed to load static data: {e}")
    
    def get_available_compounds(self) -> list[str]:
        """Get list of all available compound IDs.
        
        Returns:
            List of KEGG C-numbers or ChEBI IDs
        """
        return list(self._compounds.keys())
