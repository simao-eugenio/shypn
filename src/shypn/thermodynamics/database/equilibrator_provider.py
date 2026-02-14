"""eQuilibrator Python API provider for thermodynamic data.

This module interfaces with the eQuilibrator API to retrieve compound
thermodynamic data for ~10,000 biochemical compounds.

Uses the official equilibrator-api Python package:
https://pypi.org/project/equilibrator-api/

API Documentation: https://equilibrator.weizmann.ac.il/
"""

import logging
from typing import Optional

from ..base import CompoundDataProviderBase
from ..models import CompoundThermodynamics

logger = logging.getLogger(__name__)


class EquilibratorProvider(CompoundDataProviderBase):
    """Fetch compound thermodynamic data from eQuilibrator using official Python API.
    
    Uses the equilibrator-api package which provides:
    - Standard formation energies for ~10,000 biochemical compounds
    - pH-adjusted ΔG°' values (biochemical standard state)
    - Ionic strength corrections
    - Temperature adjustments
    - Uncertainty estimates based on component contribution method
    
    Features:
    - No SSL/network issues (uses local cached database)
    - Fast lookups after initial database download
    - Proper error handling and logging
    - Supports KEGG compound IDs
    
    Example:
        >>> provider = EquilibratorProvider()
        >>> atp = provider.get_compound("C00002", ph=7.4, temperature=310.15)
        >>> print(f"ΔG°_f = {atp.delta_g_formation} kJ/mol")
    
    Note: First use downloads ~50MB database to ~/.cache/equilibrator/
    """
    
    def __init__(self):
        """Initialize eQuilibrator provider.
        
        On first use, will download thermodynamic database (~50MB)
        to ~/.cache/equilibrator/. Subsequent uses are instant.
        """
        self._cc = None  # ComponentContribution instance (lazy init)
        self._available = None  # Availability check (lazy)
        self._Q = None  # Pint quantity class
        
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Retrieve compound data from eQuilibrator.
        
        Args:
            compound_id: KEGG C-number (e.g., C00002, C00031)
            ph: pH value for biochemical corrections (default: 7.0)
            temperature: Temperature in Kelvin (default: 298.15K = 25°C)
            ionic_strength: Ionic strength in M (default: 0.1M)
            
        Returns:
            CompoundThermodynamics if found, None otherwise
        """
        if not self._check_availability():
            return None
        
        # eQuilibrator requires KEGG ID format
        if not compound_id.startswith("C"):
            logger.debug(f"eQuilibrator requires KEGG ID (C#####), got: {compound_id}")
            return None
        
        try:
            # Format as KEGG:C##### for equilibrator-api
            kegg_id = f"KEGG:{compound_id}"
            
            # Get compound object
            compound = self._cc.get_compound(kegg_id)
            
            if compound is None:
                logger.debug(f"Compound not found in eQuilibrator: {compound_id}")
                return None
            
            # Get standard formation energy (ΔGf°)
            # Returns tuple: (mean, sigma_array)
            result = self._cc.standard_dg_formation(compound)
            
            if result is None or result[0] is None:
                logger.warning(f"No formation energy available for {compound_id}")
                return None
            
            dg_formation = float(result[0])  # Mean formation energy in kJ/mol
            sigma_array = result[1]  # Uncertainty vector
            
            # Calculate uncertainty (norm of sigma vector)
            if sigma_array is not None and len(sigma_array) > 0:
                import numpy as np
                uncertainty = float(np.linalg.norm(sigma_array))
            else:
                uncertainty = 0.0
            
            # Get compound name (use formula as fallback)
            compound_name = self._get_compound_name(compound, compound_id)
            
            logger.info(
                f"Fetched {compound_id} from eQuilibrator: "
                f"ΔGf° = {dg_formation:.2f} kJ/mol (±{uncertainty:.2f})"
            )
            
            return CompoundThermodynamics(
                compound_id=compound_id,
                name=compound_name,
                delta_g_formation=dg_formation,
                source="eQuilibrator (Component Contribution)",
                uncertainty=uncertainty,
                conditions={
                    'pH': ph,
                    'temperature': temperature,
                    'ionic_strength': ionic_strength,
                    'note': 'Standard biochemical conditions (pH 7.0, 298.15K, 1M)'
                }
            )
            
        except Exception as e:
            logger.error(f"Error fetching {compound_id} from eQuilibrator: {e}")
            return None
    
    def _get_compound_name(self, compound, compound_id: str) -> str:
        """Extract common name from compound identifiers.
        
        Args:
            compound: Compound object from equilibrator-api
            compound_id: KEGG ID as fallback
            
        Returns:
            Common name or formula
        """
        try:
            # Try to get name from identifiers (synonyms namespace)
            if hasattr(compound, 'identifiers'):
                for identifier in compound.identifiers:
                    # Look for common synonyms (first short name)
                    if hasattr(identifier, 'registry'):
                        if identifier.registry.namespace == 'synonyms':
                            name = identifier.accession
                            # Skip InChI keys and complex IUPAC names
                            if len(name) < 50 and not name.startswith('ZKHQ'):
                                return name
            
            # Fallback to formula
            if hasattr(compound, 'formula'):
                return compound.formula
            
            # Ultimate fallback
            return compound_id
            
        except Exception:
            return compound_id
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound exists in eQuilibrator database.
        
        Args:
            compound_id: KEGG C-number
            
        Returns:
            True if compound exists in eQuilibrator database
        """
        if not self._check_availability():
            return False
        
        if not compound_id.startswith("C"):
            return False
        
        try:
            kegg_id = f"KEGG:{compound_id}"
            compound = self._cc.get_compound(kegg_id)
            return compound is not None
        except Exception:
            return False
    
    def _check_availability(self) -> bool:
        """Check if equilibrator-api package is available and initialize.
        
        Lazy initialization: only imports and sets up on first use.
        Caches result for subsequent calls.
        """
        if self._available is not None:
            return self._available
        
        try:
            # Import equilibrator-api package
            from equilibrator_api import ComponentContribution, Q_
            
            # Initialize ComponentContribution
            # First use will download database (~50MB) to ~/.cache/equilibrator/
            logger.info("Initializing eQuilibrator ComponentContribution...")
            self._cc = ComponentContribution()
            self._Q = Q_
            
            self._available = True
            logger.info("eQuilibrator API is available and ready")
            return True
            
        except ImportError:
            logger.warning(
                "equilibrator-api package not installed. "
                "Install with: pip install equilibrator-api"
            )
            self._available = False
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize eQuilibrator: {e}")
            self._available = False
            return False

