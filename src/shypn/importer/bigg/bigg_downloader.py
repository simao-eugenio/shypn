"""BiGG SBML download and caching service.

Handles downloading gzipped SBML files from BiGG database,
decompression, and local caching.
"""

import urllib.request
import gzip
from pathlib import Path
from typing import Optional

from .base_bigg_service import BaseBiGGService


class BiGGDownloader(BaseBiGGService):
    """Service for downloading and caching BiGG SBML files.
    
    Handles gzip decompression and local caching to avoid
    repeated downloads. Uses XDG cache directory by default.
    
    Attributes:
        cache_dir: Directory for caching downloaded SBML files
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize downloader service.
        
        Args:
            cache_dir: Directory for caching files (default: ~/.cache/shypn/bigg)
        """
        super().__init__()
        self.cache_dir = cache_dir or Path.home() / ".cache" / "shypn" / "bigg"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"BiGG cache directory: {self.cache_dir}")
    
    def validate(self) -> bool:
        """Check if cache directory is writable.
        
        Returns:
            True if cache directory exists and is writable
        """
        if not self.cache_dir.exists():
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                return True
            except (OSError, IOError, PermissionError) as e:
                self.logger.error(f"Cannot create cache directory: {e}")
                return False
        
        return self.cache_dir.is_dir() and os.access(self.cache_dir, os.W_OK)
    
    def download_sbml(self, model_id: str, use_cache: bool = True) -> str:
        """Download SBML file for model.
        
        Downloads gzipped SBML file from BiGG, decompresses it,
        and saves to cache directory.
        
        Args:
            model_id: BiGG model identifier (e.g., 'e_coli_core')
            use_cache: If True, use cached file if available
            
        Returns:
            Path to SBML file (cached)
            
        Raises:
            BiGGServiceError: If download or decompression fails
        """
        cache_file = self.cache_dir / f"{model_id}.xml"
        
        # Check cache first
        if use_cache and cache_file.exists():
            self.logger.info(f"Using cached SBML for '{model_id}'")
            return str(cache_file)
        
        # Download from BiGG
        try:
            url = f"{self.base_url}/static/models/{model_id}.xml.gz"
            self.logger.info(f"Downloading SBML from {url}")
            
            with urllib.request.urlopen(url, timeout=60) as response:
                compressed = response.read()
            
            self.logger.debug(f"Downloaded {len(compressed)} bytes (compressed)")
            
            # Decompress
            sbml_xml = gzip.decompress(compressed).decode('utf-8')
            self.logger.info(f"Decompressed to {len(sbml_xml)} bytes")
            
            # Cache for future use
            try:
                cache_file.write_text(sbml_xml, encoding='utf-8')
                self.logger.debug(f"Cached SBML for '{model_id}'")
            except (OSError, IOError, PermissionError) as e:
                self.logger.warning(f"Failed to cache SBML: {e}")
                # Still continue, just won't be cached
            
            return str(cache_file)
            
        except Exception as e:
            self._handle_http_error(e, f"download SBML for '{model_id}'")
            return ""
    
    def is_cached(self, model_id: str) -> bool:
        """Check if model is cached.
        
        Args:
            model_id: BiGG model identifier
            
        Returns:
            True if model is cached locally
        """
        cache_file = self.cache_dir / f"{model_id}.xml"
        return cache_file.exists()
    
    def get_cache_path(self, model_id: str) -> Path:
        """Get cache file path for model.
        
        Args:
            model_id: BiGG model identifier
            
        Returns:
            Path to cache file (may not exist)
        """
        return self.cache_dir / f"{model_id}.xml"
    
    def clear_cache(self, model_id: Optional[str] = None):
        """Remove cached SBML files.
        
        Args:
            model_id: If provided, remove only this model's cache.
                     If None, remove all cached files.
        """
        if model_id:
            cache_file = self.cache_dir / f"{model_id}.xml"
            if cache_file.exists():
                cache_file.unlink()
                self.logger.info(f"Removed cache for '{model_id}'")
        else:
            count = 0
            for cache_file in self.cache_dir.glob("*.xml"):
                cache_file.unlink()
                count += 1
            self.logger.info(f"Cleared {count} cached SBML files")
    
    def get_cache_size(self) -> int:
        """Get total size of cached files in bytes.
        
        Returns:
            Total size of all cached SBML files
        """
        total_size = 0
        for cache_file in self.cache_dir.glob("*.xml"):
            total_size += cache_file.stat().st_size
        return total_size


# Import os for access check
import os
