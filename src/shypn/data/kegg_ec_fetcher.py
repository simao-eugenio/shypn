"""
KEGG EC Number Fetcher

Fetches EC numbers from KEGG REST API for reactions.
Part of Phase 2C - KEGG EC enrichment for kinetics enhancement.

API Documentation:
    https://rest.kegg.jp/
    
Example:
    >>> fetcher = KEGGECFetcher()
    >>> ec_numbers = fetcher.fetch_ec_numbers("R00710")
    >>> print(ec_numbers)
    ['2.7.1.1']  # hexokinase
"""

import logging
import requests
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class KEGGECFetcher:
    """
    Fetches EC numbers from KEGG REST API.
    
    The KEGG REST API provides reliable, fast access to enzyme data.
    This fetcher queries the reaction endpoint and extracts EC numbers.
    
    API Endpoint:
        GET https://rest.kegg.jp/get/{reaction_id}
        
    Response Format (text):
        ENTRY       R00710              Reaction
        NAME        ...
        ENZYME      2.7.1.1
        
    Attributes:
        base_url: KEGG REST API base URL
        timeout: Request timeout in seconds
        cache: In-memory cache for fetched EC numbers
    """
    
    def __init__(self, timeout: int = 5):
        """
        Initialize KEGG EC fetcher.
        
        Args:
            timeout: HTTP request timeout in seconds (default: 5)
        """
        self.base_url = "https://rest.kegg.jp"
        self.timeout = timeout
        self.cache: Dict[str, List[str]] = {}
        
    def fetch_ec_numbers(self, reaction_id: str) -> List[str]:
        """
        Fetch EC numbers for a KEGG reaction ID.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00710")
            
        Returns:
            List of EC numbers (e.g., ["2.7.1.1"])
            Empty list if no EC numbers found or request fails
            
        Example:
            >>> fetcher = KEGGECFetcher()
            >>> fetcher.fetch_ec_numbers("R00710")
            ['2.7.1.1']
            
            >>> fetcher.fetch_ec_numbers("R01015")
            ['2.7.1.11']
        """
        # Check cache first
        if reaction_id in self.cache:
            logger.debug(f"Cache hit for {reaction_id}: {self.cache[reaction_id]}")
            return self.cache[reaction_id]
        
        # Normalize reaction ID (remove "rn:" prefix if present)
        if reaction_id.startswith("rn:"):
            reaction_id = reaction_id[3:]
        
        # Fetch from KEGG API
        try:
            url = f"{self.base_url}/get/{reaction_id}"
            logger.debug(f"Fetching EC numbers from KEGG: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            ec_numbers = self._parse_kegg_response(response.text)
            
            # Cache result
            self.cache[reaction_id] = ec_numbers
            
            if ec_numbers:
                logger.info(f"Found EC numbers for {reaction_id}: {ec_numbers}")
            else:
                logger.debug(f"No EC numbers found for {reaction_id}")
            
            return ec_numbers
            
        except requests.exceptions.Timeout:
            logger.warning(f"KEGG API timeout for {reaction_id}")
            return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"KEGG API error for {reaction_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching EC for {reaction_id}: {e}")
            return []
    
    def _parse_kegg_response(self, response_text: str) -> List[str]:
        """
        Parse KEGG response text to extract EC numbers.
        
        KEGG response format:
            ENTRY       R00710              Reaction
            NAME        ...
            ENZYME      2.7.1.1
            
        Multiple EC numbers on same line:
            ENZYME      2.7.1.1 2.7.1.2
            
        Multiple ENZYME lines:
            ENZYME      2.7.1.1
            ENZYME      2.7.1.2
            
        Args:
            response_text: Raw KEGG API response
            
        Returns:
            List of EC numbers
        """
        ec_numbers = []
        
        for line in response_text.split('\n'):
            line = line.strip()
            
            # Look for ENZYME field
            if line.startswith('ENZYME'):
                # Remove "ENZYME" prefix and split by whitespace
                parts = line.split()[1:]  # Skip "ENZYME" keyword
                
                # Each part should be an EC number (format: X.Y.Z.W)
                for ec in parts:
                    ec = ec.strip()
                    if self._is_valid_ec_number(ec):
                        ec_numbers.append(ec)
        
        return ec_numbers
    
    def _is_valid_ec_number(self, ec: str) -> bool:
        """
        Validate EC number format.
        
        Valid formats:
            - 2.7.1.1 (complete)
            - 2.7.1.- (incomplete, but valid)
            - 2.7.-.- (incomplete, but valid)
            - 2.-.-.- (incomplete, but valid)
            
        Args:
            ec: EC number string
            
        Returns:
            True if valid EC number format
        """
        if not ec:
            return False
        
        parts = ec.split('.')
        if len(parts) != 4:
            return False
        
        # Each part should be a number or '-'
        for part in parts:
            if part != '-' and not part.isdigit():
                return False
        
        # First part should be a number (1-7 are current EC classes)
        if parts[0] == '-' or not parts[0].isdigit():
            return False
        
        return True
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self.cache.clear()
        logger.debug("KEGG EC cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats:
                - size: Number of cached entries
        """
        return {
            "size": len(self.cache)
        }


def fetch_ec_for_reaction(reaction_id: str, timeout: int = 5) -> List[str]:
    """
    Convenience function to fetch EC numbers for a KEGG reaction.
    
    This is a simple wrapper around KEGGECFetcher for one-off queries.
    For batch queries, use KEGGECFetcher directly to benefit from caching.
    
    Args:
        reaction_id: KEGG reaction ID (e.g., "R00710")
        timeout: Request timeout in seconds
        
    Returns:
        List of EC numbers
        
    Example:
        >>> from shypn.data.kegg_ec_fetcher import fetch_ec_for_reaction
        >>> fetch_ec_for_reaction("R00710")
        ['2.7.1.1']
    """
    fetcher = KEGGECFetcher(timeout=timeout)
    return fetcher.fetch_ec_numbers(reaction_id)


# Singleton instance for module-level usage
_default_fetcher: Optional[KEGGECFetcher] = None


def get_default_fetcher() -> KEGGECFetcher:
    """
    Get the default KEGGECFetcher singleton instance.
    
    This provides a shared cache across the application.
    
    Returns:
        Shared KEGGECFetcher instance
    """
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = KEGGECFetcher()
    return _default_fetcher


def reset_default_fetcher():
    """Reset the default fetcher singleton (mainly for testing)."""
    global _default_fetcher
    _default_fetcher = None
