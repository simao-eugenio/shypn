"""KEGG API client for fetching pathway data.

This module provides functions to access the KEGG REST API
and retrieve KGML (KEGG Markup Language) data for pathways.

API Documentation: https://www.kegg.jp/kegg/rest/keggapi.html

⚠️ ACADEMIC USE ONLY:
The KEGG API is provided for academic use only. Users must comply
with KEGG's usage policies and cite KEGG appropriately in publications.
"""

import urllib.request
import urllib.error
from typing import Optional, List, Tuple
import time


class KEGGAPIClient:
    """Client for accessing KEGG REST API."""
    
    BASE_URL = "https://rest.kegg.jp"
    
    def __init__(self, timeout: int = 30):
        """Initialize KEGG API client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self._last_request_time = 0.0
        self._min_request_interval = 0.5  # Minimum 0.5s between requests (be nice to API)
    
    def _rate_limit(self):
        """Enforce rate limiting to be respectful to KEGG API."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request with error handling.
        
        Args:
            url: Full URL to request
            
        Returns:
            Response text or None on error
        """
        self._rate_limit()
        
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print(f"[KEGGAPIClient] HTTP Error {e.code}: {e.reason} for {url}")
            return None
        except urllib.error.URLError as e:
            print(f"[KEGGAPIClient] URL Error: {e.reason} for {url}")
            return None
        except Exception as e:
            print(f"[KEGGAPIClient] Unexpected error: {e} for {url}")
            return None
    
    def fetch_kgml(self, pathway_id: str) -> Optional[str]:
        """Fetch KGML (XML) data for a pathway.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., "hsa00010", "map00020")
            
        Returns:
            KGML XML string or None on error
            
        Example:
            >>> client = KEGGAPIClient()
            >>> kgml = client.fetch_kgml("hsa00010")
            >>> if kgml:
            ...     print("Fetched glycolysis pathway")
        """
        url = f"{self.BASE_URL}/get/{pathway_id}/kgml"
        print(f"[KEGGAPIClient] Fetching KGML for {pathway_id}")
        
        kgml = self._make_request(url)
        
        if kgml:
            print(f"[KEGGAPIClient] Successfully fetched KGML ({len(kgml)} bytes)")
        else:
            print(f"[KEGGAPIClient] Failed to fetch KGML for {pathway_id}")
        
        return kgml
    
    def fetch_pathway_info(self, pathway_id: str) -> Optional[str]:
        """Fetch pathway information in flat-file format.
        
        Args:
            pathway_id: KEGG pathway ID
            
        Returns:
            Pathway info text or None on error
        """
        url = f"{self.BASE_URL}/get/{pathway_id}"
        print(f"[KEGGAPIClient] Fetching info for {pathway_id}")
        return self._make_request(url)
    
    def list_pathways(self, organism: Optional[str] = None) -> List[Tuple[str, str]]:
        """List available pathways.
        
        Args:
            organism: Optional organism code (e.g., "hsa" for human).
                     If None, lists reference pathways.
            
        Returns:
            List of (pathway_id, title) tuples
            
        Example:
            >>> client = KEGGAPIClient()
            >>> pathways = client.list_pathways("hsa")
            >>> for pid, title in pathways[:5]:
            ...     print(f"{pid}: {title}")
        """
        if organism:
            url = f"{self.BASE_URL}/list/pathway/{organism}"
        else:
            url = f"{self.BASE_URL}/list/pathway"
        
        print(f"[KEGGAPIClient] Listing pathways" + (f" for {organism}" if organism else ""))
        
        response = self._make_request(url)
        if not response:
            return []
        
        pathways = []
        for line in response.strip().split('\n'):
            if '\t' in line:
                pathway_id, title = line.split('\t', 1)
                # Remove "path:" prefix if present
                pathway_id = pathway_id.replace('path:', '')
                pathways.append((pathway_id, title))
        
        print(f"[KEGGAPIClient] Found {len(pathways)} pathways")
        return pathways
    
    def list_organisms(self) -> List[Tuple[str, str, str]]:
        """List available organisms in KEGG.
        
        Returns:
            List of (code, name, lineage) tuples
            
        Example:
            >>> client = KEGGAPIClient()
            >>> organisms = client.list_organisms()
            >>> # Find human
            >>> human = [o for o in organisms if o[0] == 'hsa'][0]
            >>> print(human)  # ('hsa', 'Homo sapiens (human)', 'Eukaryotes;Animals;...')
        """
        url = f"{self.BASE_URL}/list/organism"
        print(f"[KEGGAPIClient] Listing organisms")
        
        response = self._make_request(url)
        if not response:
            return []
        
        organisms = []
        for line in response.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) >= 3:
                # Format: T<number> <code> <name> <lineage>
                code = parts[1]
                name = parts[2]
                lineage = parts[3] if len(parts) > 3 else ""
                organisms.append((code, name, lineage))
        
        print(f"[KEGGAPIClient] Found {len(organisms)} organisms")
        return organisms
    
    def get_pathway_image_url(self, pathway_id: str) -> str:
        """Get URL for pathway map image.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., "hsa00010")
            
        Returns:
            URL to PNG image
            
        Example:
            >>> client = KEGGAPIClient()
            >>> url = client.get_pathway_image_url("hsa00010")
            >>> print(url)  # https://www.kegg.jp/kegg/pathway/hsa/hsa00010.png
        """
        # Extract organism prefix (e.g., "hsa" from "hsa00010")
        if len(pathway_id) >= 3 and not pathway_id.startswith('map'):
            org = pathway_id[:3]
            return f"https://www.kegg.jp/kegg/pathway/{org}/{pathway_id}.png"
        else:
            # Reference pathway
            return f"https://www.kegg.jp/kegg/pathway/map/{pathway_id}.png"


# Convenience function for quick access
def fetch_pathway(pathway_id: str) -> Optional[str]:
    """Quick function to fetch KGML for a pathway.
    
    Args:
        pathway_id: KEGG pathway ID
        
    Returns:
        KGML XML string or None
        
    Example:
        >>> from shypn.import.kegg.api_client import fetch_pathway
        >>> kgml = fetch_pathway("hsa00010")
    """
    client = KEGGAPIClient()
    return client.fetch_kgml(pathway_id)
