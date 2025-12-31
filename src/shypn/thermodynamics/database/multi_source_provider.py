"""Multi-source compound data provider with fallback.

Orchestrates multiple data sources with priority-based fallback:
1. Cache (fast, offline)
2. Static data (curated, offline)
3. Web services (comprehensive, requires internet)
"""

import logging
from typing import Optional, List

from ..base import CompoundDataProviderBase
from ..models import CompoundThermodynamics
from .cache_provider import CacheProvider
from .static_provider import StaticDataProvider

logger = logging.getLogger(__name__)


class MultiSourceProvider(CompoundDataProviderBase):
    """Unified provider with multiple data sources and fallback logic.
    
    Query order:
    1. Cache - Fast, returns immediately if available
    2. Static - Curated core metabolites (~100 compounds)
    3. Web services - Future: eQuilibrator, MetaCyc APIs
    
    Results are automatically cached for future queries.
    
    Example:
        >>> provider = MultiSourceProvider()
        >>> compound = provider.get_compound("C00002")  # ATP
        >>> # First query: cache miss → static hit → cache stored
        >>> compound2 = provider.get_compound("C00002")
        >>> # Second query: cache hit (fast!)
    """
    
    def __init__(
        self,
        enable_cache: bool = True,
        enable_static: bool = True,
        enable_web: bool = False  # Future implementation
    ):
        """Initialize multi-source provider.
        
        Args:
            enable_cache: Use disk cache
            enable_static: Use static data file
            enable_web: Use web services (not implemented yet)
        """
        self.providers: List[CompoundDataProviderBase] = []
        
        # Initialize providers in priority order
        if enable_cache:
            try:
                self.cache = CacheProvider()
                self.providers.append(self.cache)
                logger.info("Cache provider enabled")
            except Exception as e:
                logger.warning(f"Cache provider failed to initialize: {e}")
                self.cache = None
        else:
            self.cache = None
        
        if enable_static:
            try:
                self.static = StaticDataProvider()
                self.providers.append(self.static)
                logger.info("Static provider enabled")
            except Exception as e:
                logger.warning(f"Static provider failed to initialize: {e}")
                self.static = None
        else:
            self.static = None
        
        if enable_web:
            logger.warning("Web services not yet implemented")
        
        if not self.providers:
            logger.error("No data providers available!")
    
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Retrieve compound data from first available source.
        
        Queries sources in priority order. If found in lower-priority
        source, automatically caches for future queries.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            ph: pH value
            temperature: Temperature in Kelvin
            ionic_strength: Ionic strength in M
            
        Returns:
            CompoundThermodynamics if found in any source, None otherwise
        """
        for i, provider in enumerate(self.providers):
            try:
                compound = provider.get_compound(
                    compound_id, ph, temperature, ionic_strength
                )
                
                if compound is not None:
                    source_name = provider.__class__.__name__
                    logger.debug(f"Found {compound_id} in {source_name}")
                    
                    # Cache result if found in non-cache source
                    if i > 0 and self.cache is not None:
                        self.cache.store_compound(compound)
                        logger.debug(f"Cached {compound_id} from {source_name}")
                    
                    return compound
                    
            except Exception as e:
                provider_name = provider.__class__.__name__
                logger.error(f"{provider_name} failed for {compound_id}: {e}")
                continue
        
        logger.debug(f"Compound not found: {compound_id}")
        return None
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound is available in any source.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            
        Returns:
            True if compound exists in any provider
        """
        for provider in self.providers:
            try:
                if provider.has_compound(compound_id):
                    return True
            except Exception as e:
                logger.error(f"Provider check failed: {e}")
                continue
        
        return False
    
    def clear_cache(self):
        """Clear all cached data."""
        if self.cache is not None:
            self.cache.clear_cache()
            logger.info("Cache cleared")
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries."""
        if self.cache is not None:
            self.cache.cleanup_expired()
