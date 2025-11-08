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
import json
import concurrent.futures
from typing import List, Optional, Dict, Callable
from pathlib import Path
from datetime import datetime, timedelta

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
    
    def __init__(self, timeout: int = 5, use_persistent_cache: bool = True):
        """
        Initialize KEGG EC fetcher.
        
        Args:
            timeout: HTTP request timeout in seconds (default: 5)
            use_persistent_cache: Use persistent file cache (default: True)
        """
        self.base_url = "https://rest.kegg.jp"
        self.timeout = timeout
        self.cache: Dict[str, List[str]] = {}  # In-memory cache
        
        # Persistent cache (survives app restarts)
        self.persistent_cache: Optional[PersistentECCache] = None
        if use_persistent_cache:
            try:
                self.persistent_cache = PersistentECCache()
            except Exception as e:
                logger.warning(f"Failed to initialize persistent cache: {e}")
                self.persistent_cache = None
        
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
        # Check in-memory cache first (fastest)
        if reaction_id in self.cache:
            logger.debug(f"Memory cache hit for {reaction_id}: {self.cache[reaction_id]}")
            return self.cache[reaction_id]
        
        # Check persistent cache (fast, avoids API call)
        if self.persistent_cache:
            cached_ec = self.persistent_cache.get(reaction_id)
            if cached_ec is not None:
                # Store in memory cache for even faster subsequent access
                self.cache[reaction_id] = cached_ec
                logger.debug(f"Persistent cache hit for {reaction_id}: {cached_ec}")
                return cached_ec
        
        # Normalize reaction ID (remove "rn:" prefix if present)
        normalized_id = reaction_id
        if reaction_id.startswith("rn:"):
            normalized_id = reaction_id[3:]
        
        # Fetch from KEGG API
        try:
            url = f"{self.base_url}/get/{normalized_id}"
            logger.debug(f"Fetching EC numbers from KEGG: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            ec_numbers = self._parse_kegg_response(response.text)
            
            # Cache result in memory
            self.cache[reaction_id] = ec_numbers
            
            # Cache result persistently
            if self.persistent_cache:
                self.persistent_cache.set(reaction_id, ec_numbers)
                # Save immediately to ensure data persists
                self.persistent_cache.save()
            
            if ec_numbers:
                logger.info(f"Found EC numbers for {reaction_id}: {ec_numbers}")
            else:
                logger.debug(f"No EC numbers found for {reaction_id}")
            
            return ec_numbers
            
        except requests.exceptions.Timeout:
            logger.warning(f"KEGG API timeout for {reaction_id}")
            return []
        except requests.exceptions.HTTPError as e:
            # 400 Bad Request is expected for invalid reaction IDs (e.g., entry IDs)
            if e.response.status_code == 400:
                logger.debug(f"Invalid KEGG reaction ID: {reaction_id}")
            else:
                logger.warning(f"KEGG API HTTP error for {reaction_id}: {e}")
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
    
    def fetch_reaction_name(self, reaction_id: str) -> Optional[str]:
        """
        Fetch reaction name for a KEGG reaction ID.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00710")
            
        Returns:
            Reaction name (e.g., "ATP:D-hexose 6-phosphotransferase")
            None if not found or request fails
            
        Example:
            >>> fetcher = KEGGECFetcher()
            >>> fetcher.fetch_reaction_name("R00710")
            'ATP:D-hexose 6-phosphotransferase'
        """
        # Normalize reaction ID (remove "rn:" prefix if present)
        normalized_id = reaction_id
        if reaction_id.startswith("rn:"):
            normalized_id = reaction_id[3:]
        
        # Fetch from KEGG API
        try:
            url = f"{self.base_url}/get/{normalized_id}"
            logger.debug(f"Fetching reaction name from KEGG: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response for NAME field
            name = self._parse_kegg_name(response.text)
            
            if name:
                logger.info(f"Found reaction name for {reaction_id}: {name}")
            else:
                logger.debug(f"No reaction name found for {reaction_id}")
            
            return name
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"KEGG API error fetching name for {reaction_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching name for {reaction_id}: {e}")
            return None
    
    def _parse_kegg_name(self, response_text: str) -> Optional[str]:
        """
        Parse KEGG response text to extract reaction name.
        
        KEGG response format:
            ENTRY       R00710              Reaction
            NAME        ATP:D-hexose 6-phosphotransferase;
                        Hexokinase
            ENZYME      2.7.1.1
            
        Args:
            response_text: Raw KEGG API response
            
        Returns:
            Reaction name (first name if multiple, semicolon-separated)
        """
        name_lines = []
        in_name_section = False
        
        for line in response_text.split('\n'):
            stripped = line.strip()
            
            # Start of NAME section
            if stripped.startswith('NAME'):
                in_name_section = True
                # Get text after "NAME"
                name_text = stripped[4:].strip()
                if name_text:
                    name_lines.append(name_text)
            # Continuation of NAME section (indented lines)
            elif in_name_section and line.startswith('            '):
                name_lines.append(stripped)
            # End of NAME section (new field starting)
            elif in_name_section and not line.startswith('            '):
                break
        
        if not name_lines:
            return None
        
        # Join multiple lines and take first name (before semicolon)
        full_name = ' '.join(name_lines)
        # Remove trailing semicolons
        full_name = full_name.rstrip(';').strip()
        
        # If multiple names separated by semicolon, take the first one
        if ';' in full_name:
            return full_name.split(';')[0].strip()
        
        return full_name
    
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
    
    def fetch_ec_numbers_parallel(
        self, 
        reaction_ids: List[str], 
        max_workers: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, List[str]]:
        """
        Fetch EC numbers for multiple reactions in parallel.
        
        This method uses ThreadPoolExecutor to fetch EC numbers concurrently,
        significantly improving performance for pathways with many reactions.
        
        Args:
            reaction_ids: List of KEGG reaction IDs to fetch
            max_workers: Maximum number of parallel requests (default: 5)
                        Limited to 5 to be polite to KEGG API
            progress_callback: Optional callback function(completed, total)
                             Called after each fetch completes
        
        Returns:
            Dictionary mapping reaction_id → EC numbers list
            
        Example:
            >>> fetcher = KEGGECFetcher()
            >>> reaction_ids = ["R00710", "R00299", "R01015"]
            >>> results = fetcher.fetch_ec_numbers_parallel(reaction_ids)
            >>> print(results)
            {'R00710': ['2.7.1.1'], 'R00299': ['2.7.1.1', '2.7.1.2'], ...}
        """
        results = {}
        completed = 0
        total = len(reaction_ids)
        
        # Check which ones are already cached
        uncached_ids = []
        for rid in reaction_ids:
            if rid in self.cache:
                results[rid] = self.cache[rid]
                completed += 1
            else:
                uncached_ids.append(rid)
        
        # Report initial progress for cached items
        if progress_callback and completed > 0:
            progress_callback(completed, total)
        
        # Fetch uncached items in parallel
        if uncached_ids:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all fetches
                future_to_reaction = {
                    executor.submit(self.fetch_ec_numbers, rid): rid 
                    for rid in uncached_ids
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_reaction):
                    reaction_id = future_to_reaction[future]
                    try:
                        ec_numbers = future.result()
                        results[reaction_id] = ec_numbers
                        completed += 1
                        
                        # Report progress
                        if progress_callback:
                            progress_callback(completed, total)
                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch EC for {reaction_id}: {e}")
                        results[reaction_id] = []
                        completed += 1
                        
                        if progress_callback:
                            progress_callback(completed, total)
        
        logger.info(f"Parallel fetch completed: {len(results)} reactions, "
                   f"{len(uncached_ids)} fetched, {total - len(uncached_ids)} cached")
        
        return results


class PersistentECCache:
    """
    Persistent cache for KEGG EC numbers stored in JSON file.
    
    This cache survives application restarts, making subsequent imports
    much faster. Cache entries have a TTL (time-to-live) to ensure
    data freshness.
    
    Attributes:
        cache_file: Path to JSON cache file
        cache: In-memory cache dictionary
        ttl_days: Number of days before cache entry expires
    """
    
    def __init__(
        self, 
        cache_file: Optional[Path] = None,
        ttl_days: int = 90
    ):
        """
        Initialize persistent cache.
        
        Args:
            cache_file: Path to cache file (default: ~/.shypn/kegg_ec_cache.json)
            ttl_days: Cache entry time-to-live in days (default: 90)
                     EC numbers are stable, so long TTL is acceptable
        """
        if cache_file is None:
            # Default cache location
            cache_dir = Path.home() / ".shypn"
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / "kegg_ec_cache.json"
        
        self.cache_file = Path(cache_file)
        self.ttl_days = ttl_days
        self.cache: Dict[str, dict] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from JSON file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.debug(f"Loaded EC cache from {self.cache_file} "
                           f"({len(self.cache)} entries)")
            except Exception as e:
                logger.warning(f"Failed to load EC cache: {e}")
                self.cache = {}
        else:
            logger.debug(f"No existing EC cache at {self.cache_file}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to JSON file."""
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved EC cache to {self.cache_file} "
                        f"({len(self.cache)} entries)")
        except Exception as e:
            logger.warning(f"Failed to save EC cache: {e}")
    
    def _is_expired(self, entry: dict) -> bool:
        """
        Check if cache entry is expired.
        
        Args:
            entry: Cache entry dictionary with 'timestamp' field
            
        Returns:
            True if entry is older than ttl_days
        """
        try:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            age = datetime.now() - timestamp
            return age > timedelta(days=self.ttl_days)
        except (KeyError, ValueError) as e:
            logger.debug(f"Invalid cache entry timestamp: {e}")
            return True  # Treat invalid entries as expired
    
    def get(self, reaction_id: str) -> Optional[List[str]]:
        """
        Get EC numbers from cache.
        
        Args:
            reaction_id: KEGG reaction ID
            
        Returns:
            List of EC numbers if cached and not expired, None otherwise
        """
        entry = self.cache.get(reaction_id)
        
        if entry is None:
            return None
        
        if self._is_expired(entry):
            logger.debug(f"Cache entry expired for {reaction_id}")
            del self.cache[reaction_id]
            return None
        
        logger.debug(f"Cache hit for {reaction_id}: {entry['ec_numbers']}")
        return entry['ec_numbers']
    
    def set(self, reaction_id: str, ec_numbers: List[str]):
        """
        Store EC numbers in cache.
        
        Args:
            reaction_id: KEGG reaction ID
            ec_numbers: List of EC numbers to cache
        """
        self.cache[reaction_id] = {
            'ec_numbers': ec_numbers,
            'timestamp': datetime.now().isoformat()
        }
        logger.debug(f"Cached EC numbers for {reaction_id}: {ec_numbers}")
    
    def save(self):
        """Persist cache to disk."""
        self._save_cache()
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self._save_cache()
        logger.info("EC cache cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats:
                - total: Total entries
                - expired: Number of expired entries
                - valid: Number of valid entries
        """
        total = len(self.cache)
        expired = sum(1 for entry in self.cache.values() if self._is_expired(entry))
        valid = total - expired
        
        return {
            'total': total,
            'expired': expired,
            'valid': valid
        }
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        expired_keys = [
            rid for rid, entry in self.cache.items() 
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"Removed {len(expired_keys)} expired cache entries")


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


def fetch_ec_numbers_parallel(
    reaction_ids: List[str],
    max_workers: int = 5,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    timeout: int = 5
) -> Dict[str, List[str]]:
    """
    Convenience function to fetch EC numbers for multiple reactions in parallel.
    
    This uses the default fetcher singleton to benefit from caching across calls.
    
    Args:
        reaction_ids: List of KEGG reaction IDs
        max_workers: Maximum number of parallel requests (default: 5)
        progress_callback: Optional callback function(completed, total)
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary mapping reaction_id → EC numbers list
        
    Example:
        >>> from shypn.data.kegg_ec_fetcher import fetch_ec_numbers_parallel
        >>> ids = ["R00710", "R00299", "R01015"]
        >>> results = fetch_ec_numbers_parallel(ids)
        >>> print(results['R00710'])
        ['2.7.1.1']
    """
    fetcher = get_default_fetcher()
    return fetcher.fetch_ec_numbers_parallel(
        reaction_ids,
        max_workers=max_workers,
        progress_callback=progress_callback
    )


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
