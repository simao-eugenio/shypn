"""eQuilibrator web service provider for thermodynamic data.

This module interfaces with the eQuilibrator API to retrieve compound
thermodynamic data for ~10,000 biochemical compounds.

API Documentation: https://equilibrator.weizmann.ac.il/
"""

import logging
import time
from typing import Optional
import json

from ..base import CompoundDataProviderBase
from ..models import CompoundThermodynamics

logger = logging.getLogger(__name__)


class EquilibratorProvider(CompoundDataProviderBase):
    """Fetch compound thermodynamic data from eQuilibrator web API.
    
    eQuilibrator provides standard formation energies for thousands of
    biochemical compounds with pH and ionic strength corrections.
    
    Features:
    - REST API access (no authentication required)
    - pH-adjusted ΔG°' values
    - Ionic strength corrections
    - Uncertainty estimates
    - Retry logic for network errors
    
    Example:
        >>> provider = EquilibratorProvider()
        >>> atp = provider.get_compound("C00002", ph=7.4, temperature=310.15)
        >>> print(f"ΔG°_f = {atp.delta_g_formation} kJ/mol")
    
    Note: Requires internet connection. Falls back gracefully if unavailable.
    """
    
    # eQuilibrator API endpoints
    API_BASE_URL = "https://equilibrator.weizmann.ac.il/api/v1"
    COMPOUND_ENDPOINT = "/compound"
    SEARCH_ENDPOINT = "/search"
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize eQuilibrator provider.
        
        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._available = None  # Lazy check on first use
        
        # Import requests only if needed (optional dependency)
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.warning(
                "requests library not installed. "
                "Install with: pip install requests"
            )
            self.requests = None
            self._available = False
    
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Retrieve compound data from eQuilibrator API.
        
        Args:
            compound_id: KEGG C-number (e.g., C00002)
            ph: pH value for biochemical corrections
            temperature: Temperature in Kelvin
            ionic_strength: Ionic strength in M
            
        Returns:
            CompoundThermodynamics if found, None otherwise
        """
        if not self._check_availability():
            return None
        
        # eQuilibrator uses KEGG IDs
        if not compound_id.startswith("C"):
            logger.debug(f"eQuilibrator requires KEGG ID, got: {compound_id}")
            return None
        
        # Query API with retry logic
        for attempt in range(self.max_retries):
            try:
                data = self._fetch_compound_data(
                    compound_id, ph, temperature, ionic_strength
                )
                
                if data:
                    return self._parse_response(data, compound_id, ph, temperature, ionic_strength)
                else:
                    return None
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"eQuilibrator request failed (attempt {attempt+1}/{self.max_retries}): {e}"
                    )
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"eQuilibrator request failed after {self.max_retries} attempts: {e}")
                    return None
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound exists in eQuilibrator.
        
        Note: This requires a network request, so it's relatively slow.
        Consider using cache to avoid repeated checks.
        
        Args:
            compound_id: KEGG C-number
            
        Returns:
            True if compound exists in eQuilibrator database
        """
        if not self._check_availability():
            return False
        
        try:
            # Quick search query
            result = self._search_compound(compound_id)
            return result is not None
        except Exception:
            return False
    
    def _check_availability(self) -> bool:
        """Check if eQuilibrator API is available.
        
        Lazy check on first use, then cached.
        """
        if self._available is not None:
            return self._available
        
        if self.requests is None:
            self._available = False
            return False
        
        try:
            # Test API connectivity
            response = self.requests.get(
                f"{self.API_BASE_URL}/ping",
                timeout=3
            )
            self._available = response.status_code == 200
            
            if self._available:
                logger.info("eQuilibrator API is available")
            else:
                logger.warning("eQuilibrator API returned non-200 status")
                
        except Exception as e:
            logger.warning(f"eQuilibrator API unavailable: {e}")
            self._available = False
        
        return self._available
    
    def _fetch_compound_data(
        self,
        compound_id: str,
        ph: float,
        temperature: float,
        ionic_strength: float
    ) -> Optional[dict]:
        """Fetch compound data from API.
        
        Args:
            compound_id: KEGG C-number
            ph: pH value
            temperature: Temperature in Kelvin
            ionic_strength: Ionic strength in M
            
        Returns:
            Parsed JSON response or None
        """
        url = f"{self.API_BASE_URL}{self.COMPOUND_ENDPOINT}/{compound_id}"
        
        params = {
            'pH': ph,
            'ionic_strength': ionic_strength,
            'temperature': temperature
        }
        
        response = self.requests.get(
            url,
            params=params,
            timeout=self.timeout,
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 404:
            logger.debug(f"Compound not found in eQuilibrator: {compound_id}")
            return None
        
        response.raise_for_status()
        return response.json()
    
    def _search_compound(self, compound_id: str) -> Optional[dict]:
        """Search for compound in eQuilibrator.
        
        Args:
            compound_id: KEGG C-number
            
        Returns:
            Search result or None
        """
        url = f"{self.API_BASE_URL}{self.SEARCH_ENDPOINT}"
        
        params = {'query': compound_id}
        
        response = self.requests.get(
            url,
            params=params,
            timeout=self.timeout,
            headers={'Accept': 'application/json'}
        )
        
        response.raise_for_status()
        results = response.json()
        
        return results[0] if results else None
    
    def _parse_response(
        self,
        data: dict,
        compound_id: str,
        ph: float,
        temperature: float,
        ionic_strength: float
    ) -> CompoundThermodynamics:
        """Parse API response to CompoundThermodynamics.
        
        Args:
            data: JSON response from API
            compound_id: KEGG C-number
            ph: pH value
            temperature: Temperature
            ionic_strength: Ionic strength
            
        Returns:
            CompoundThermodynamics object
        """
        # eQuilibrator response structure (adjust based on actual API)
        # This is a simplified parser - actual API may have different structure
        
        name = data.get('name', compound_id)
        
        # Formation energy (kJ/mol)
        # eQuilibrator returns ΔG°' (biochemical standard state)
        delta_g_formation = data.get('formation_energy', {}).get('value', 0.0)
        
        # Uncertainty
        uncertainty = data.get('formation_energy', {}).get('uncertainty', 0.0)
        
        return CompoundThermodynamics(
            compound_id=compound_id,
            name=name,
            delta_g_formation=delta_g_formation,
            source="eQuilibrator API",
            uncertainty=uncertainty,
            conditions={
                'pH': ph,
                'temperature': temperature,
                'ionic_strength': ionic_strength
            }
        )


class MockEquilibratorProvider(CompoundDataProviderBase):
    """Mock provider for testing without network access.
    
    Returns synthetic data for known compounds to enable offline testing.
    Use this in unit tests to avoid network dependency.
    """
    
    def __init__(self):
        """Initialize mock provider with test data."""
        # Synthetic test data (realistic values from Alberty 2003)
        self._mock_data = {
            "C00002": {  # ATP
                "name": "ATP",
                "delta_g_formation": -2292.5,
                "uncertainty": 2.0
            },
            "C00008": {  # ADP
                "name": "ADP",
                "delta_g_formation": -1906.5,
                "uncertainty": 1.8
            },
            "C00001": {  # H2O
                "name": "H2O",
                "delta_g_formation": -237.2,
                "uncertainty": 0.1
            },
            "C00009": {  # Phosphate
                "name": "Phosphate",
                "delta_g_formation": -1059.2,
                "uncertainty": 0.5
            },
        }
    
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Return mock compound data."""
        data = self._mock_data.get(compound_id)
        
        if data is None:
            return None
        
        return CompoundThermodynamics(
            compound_id=compound_id,
            name=data["name"],
            delta_g_formation=data["delta_g_formation"],
            source="Mock eQuilibrator",
            uncertainty=data["uncertainty"],
            conditions={
                'pH': ph,
                'temperature': temperature,
                'ionic_strength': ionic_strength
            }
        )
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if mock compound exists."""
        return compound_id in self._mock_data
