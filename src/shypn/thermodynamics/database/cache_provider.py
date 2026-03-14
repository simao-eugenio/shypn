"""Local cache provider for thermodynamic data.

Implements disk-based caching to avoid repeated database queries.
Uses JSON files for portability and human-readability.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..base import CompoundDataProviderBase
from ..models import CompoundThermodynamics

logger = logging.getLogger(__name__)


class CacheProvider(CompoundDataProviderBase):
    """Disk-based cache for compound thermodynamic data.
    
    This provider stores compound data in JSON files for fast offline access.
    Acts as a first-level cache before querying remote databases.
    
    Features:
    - JSON storage for human-readable data
    - Expiry mechanism (configurable TTL)
    - Automatic cache cleanup
    - Thread-safe operations
    
    Example:
        >>> cache = CacheProvider(cache_dir=Path("~/.shypn/thermo"))
        >>> compound = cache.get_compound("C00002", ph=7.0, temperature=298.15)
        >>> if compound:
        ...     print(f"ΔG°_f = {compound.delta_g_formation}")
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_days: int = 30
    ):
        """Initialize cache provider.
        
        Args:
            cache_dir: Directory for cache files. If None, uses default.
            ttl_days: Time-to-live in days. 0 = never expire.
        """
        if cache_dir is None:
            # Default: ~/.shypn/thermodynamics/cache
            from platformdirs import user_cache_dir
            cache_dir = Path(user_cache_dir("shypn")) / "thermodynamics" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Cache initialized: {self.cache_dir}")
    
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Retrieve compound data from cache.
        
        Args:
            compound_id: KEGG or ChEBI identifier
            ph: pH value
            temperature: Temperature in Kelvin
            ionic_strength: Ionic strength in M
            
        Returns:
            CompoundThermodynamics if cached and not expired, None otherwise
        """
        cache_file = self._get_cache_file(compound_id, ph, temperature, ionic_strength)
        
        if not cache_file.exists():
            logger.debug(f"Cache miss: {compound_id}")
            return None
        
        # Check expiry
        if self._is_expired(cache_file):
            logger.debug(f"Cache expired: {compound_id}")
            cache_file.unlink()  # Delete expired entry
            return None
        
        # Load from cache
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            compound = CompoundThermodynamics(
                compound_id=data["compound_id"],
                name=data["name"],
                delta_g_formation=data["delta_g_formation"],
                source=data.get("source", "cache"),
                uncertainty=data.get("uncertainty", 0.0),
                conditions=data.get("conditions", {
                    'pH': ph,
                    'temperature': temperature,
                    'ionic_strength': ionic_strength
                })
            )
            
            logger.debug(f"Cache hit: {compound_id}")
            return compound
            
        except Exception as e:
            logger.error(f"Cache read error for {compound_id}: {e}")
            return None
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound is in cache (any conditions).
        
        Args:
            compound_id: KEGG or ChEBI identifier
            
        Returns:
            True if any cache entry exists for compound
        """
        # Check if any cache file starts with compound_id
        pattern = f"{compound_id}_*.json"
        matches = list(self.cache_dir.glob(pattern))
        return len(matches) > 0
    
    def store_compound(self, compound: CompoundThermodynamics):
        """Store compound data in cache.
        
        Args:
            compound: CompoundThermodynamics to cache
        """
        cache_file = self._get_cache_file(
            compound.compound_id,
            compound.ph,
            compound.temperature,
            compound.ionic_strength
        )
        
        try:
            data = {
                "compound_id": compound.compound_id,
                "name": compound.name,
                "delta_g_formation": compound.delta_g_formation,
                "source": compound.source,
                "uncertainty": compound.uncertainty,
                "conditions": compound.conditions,
                "cached_at": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Cached: {compound.compound_id}")
            
        except Exception as e:
            logger.error(f"Cache write error for {compound.compound_id}: {e}")
    
    def clear_cache(self, compound_id: Optional[str] = None):
        """Clear cache entries.
        
        Args:
            compound_id: If provided, clear only this compound.
                        If None, clear entire cache.
        """
        if compound_id:
            pattern = f"{compound_id}_*.json"
            files = list(self.cache_dir.glob(pattern))
        else:
            files = list(self.cache_dir.glob("*.json"))
        
        for cache_file in files:
            cache_file.unlink()
        
        logger.info(f"Cleared {len(files)} cache entries")
    
    def cleanup_expired(self):
        """Remove all expired cache entries."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            if self._is_expired(cache_file):
                cache_file.unlink()
                count += 1
        
        logger.info(f"Cleaned up {count} expired cache entries")
    
    def _get_cache_file(
        self,
        compound_id: str,
        ph: float,
        temperature: float,
        ionic_strength: float
    ) -> Path:
        """Generate cache file path based on compound and conditions.
        
        Format: {compound_id}_{ph}_{temp}_{ionic}.json
        """
        # Round to avoid floating point issues
        ph_str = f"{ph:.1f}"
        temp_str = f"{temperature:.1f}"
        ionic_str = f"{ionic_strength:.2f}"
        
        filename = f"{compound_id}_{ph_str}_{temp_str}_{ionic_str}.json"
        return self.cache_dir / filename
    
    def _is_expired(self, cache_file: Path) -> bool:
        """Check if cache file has expired based on TTL.
        
        Args:
            cache_file: Path to cache file
            
        Returns:
            True if expired, False otherwise
        """
        if self.ttl_days == 0:
            return False  # Never expire
        
        try:
            # Check file modification time
            mtime = cache_file.stat().st_mtime
            age_days = (time.time() - mtime) / (24 * 3600)
            return age_days > self.ttl_days
            
        except Exception:
            return True  # Consider it expired if we can't read
