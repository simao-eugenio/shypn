"""
KEGG Fetcher

Fetches pathway data from KEGG (Kyoto Encyclopedia of Genes and Genomes) database.

Author: Shypn Development Team
Date: October 2025
"""

import time
from typing import Dict, Any, List, Optional
import logging

from .base_fetcher import BaseFetcher
from ..models import FetchResult, FetchStatus


class KEGGFetcher(BaseFetcher):
    """Fetcher for KEGG database.
    
    KEGG provides:
    - Pathway coordinates (layout positions)
    - Pathway diagrams
    - Gene/protein annotations
    - Reaction information
    
    Reliability: 0.85 (high quality, comprehensive coverage)
    """
    
    # Source reliability for KEGG
    KEGG_RELIABILITY = 0.85
    
    # Base URLs
    KEGG_API_BASE = "https://rest.kegg.jp"
    KEGG_PATHWAY_BASE = "https://www.genome.jp/kegg-bin/show_pathway"
    
    def __init__(self):
        """Initialize KEGG fetcher."""
        super().__init__(
            source_name="KEGG",
            source_reliability=self.KEGG_RELIABILITY
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def fetch(self,
             pathway_id: str,
             data_type: str,
             **kwargs) -> FetchResult:
        """Fetch data from KEGG.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., "hsa00010")
            data_type: Type of data (coordinates, annotations, etc.)
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with fetched data
        """
        start_time = time.time()
        
        try:
            # Route to appropriate fetch method
            if data_type == "coordinates":
                result = self._fetch_coordinates(pathway_id, **kwargs)
            elif data_type == "annotations":
                result = self._fetch_annotations(pathway_id, **kwargs)
            elif data_type == "reactions":
                result = self._fetch_reactions(pathway_id, **kwargs)
            else:
                return self._create_failed_result(
                    data_type=data_type,
                    error=f"Data type '{data_type}' not supported by KEGG fetcher",
                    status=FetchStatus.NOT_FOUND
                )
            
            # Add fetch duration
            duration_ms = (time.time() - start_time) * 1000
            result.fetch_duration_ms = duration_ms
            
            return result
        
        except Exception as e:
            self.logger.error(f"KEGG fetch failed: {e}")
            return self._create_failed_result(
                data_type=data_type,
                error=str(e)
            )
    
    def _fetch_coordinates(self, pathway_id: str, **kwargs) -> FetchResult:
        """Fetch coordinate data from KEGG KGML.
        
        Fetches KGML XML from KEGG and extracts layout coordinates
        for species and reactions.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., 'hsa00010')
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with coordinate data:
            {
                'pathway_id': 'hsa00010',
                'species': [
                    {
                        'kegg_id': 'cpd:C00031',
                        'name': 'Glucose',
                        'x': 150.0,
                        'y': 100.0,
                        'width': 46.0,
                        'height': 17.0
                    },
                    ...
                ],
                'reactions': [
                    {
                        'kegg_id': 'rn:R00299',
                        'name': 'Hexokinase',
                        'x': 200.0,
                        'y': 150.0
                    },
                    ...
                ]
            }
        """
        try:
            import requests
            
            # Fetch KGML XML from KEGG API
            kgml_url = f"{self.KEGG_API_BASE}/get/{pathway_id}/kgml"
            self.logger.info(f"Fetching KGML from: {kgml_url}")
            
            response = requests.get(kgml_url, timeout=30)
            response.raise_for_status()
            
            # Parse KGML using existing parser
            try:
                from shypn.importer.kegg.kgml_parser import KGMLParser
            except ImportError as e:
                self.logger.warning(f"KGML parser not available: {e}")
                return self._create_failure_result(
                    error="KGML parser not available",
                    data_type="coordinates"
                )
            
            parser = KGMLParser()
            pathway_data = parser.parse_string(response.text)
            
            # Extract coordinates from entries
            species_coords = []
            reaction_coords = []
            
            for entry_id, entry in pathway_data.entries.items():
                graphics = entry.graphics
                
                # Extract compound coordinates
                if entry.type == 'compound':
                    kegg_ids = entry.get_kegg_ids()
                    for kegg_id in kegg_ids:
                        species_coords.append({
                            'kegg_id': kegg_id,
                            'name': graphics.name,
                            'x': graphics.x,
                            'y': graphics.y,
                            'width': graphics.width,
                            'height': graphics.height
                        })
                
                # Extract reaction coordinates (from enzyme entries or reaction attribute)
                elif entry.type in ('enzyme', 'ortholog'):
                    if entry.reaction:
                        reaction_coords.append({
                            'kegg_id': entry.reaction,
                            'name': graphics.name,
                            'x': graphics.x,
                            'y': graphics.y
                        })
            
            # Build result data
            data = {
                'pathway_id': pathway_id,
                'species': species_coords,
                'reactions': reaction_coords
            }
            
            fields_filled = ['pathway_id', 'species', 'reactions']
            
            self.logger.info(
                f"✓ Fetched {len(species_coords)} species coords, "
                f"{len(reaction_coords)} reaction coords from KEGG"
            )
            
            return self._create_success_result(
                data=data,
                data_type="coordinates",
                fields_filled=fields_filled,
                source_url=kgml_url
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching KGML: {e}")
            return self._create_failure_result(
                error=f"Network error: {str(e)}",
                data_type="coordinates"
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch KEGG coordinates: {e}")
            return self._create_failure_result(
                error=str(e),
                data_type="coordinates"
            )
    
    def _fetch_annotations(self, pathway_id: str, **kwargs) -> FetchResult:
        """Fetch annotation data from KEGG.
        
        Args:
            pathway_id: KEGG pathway ID
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with annotation data
        """
        # TODO: Implement actual KEGG API call
        
        self.logger.info(f"Fetching annotations for pathway: {pathway_id}")
        
        data = {
            "pathway_id": pathway_id,
            "pathway_name": "",
            "organism": "",
            "genes": [],
            "compounds": []
        }
        
        fields_filled = ["pathway_id"]
        
        return self._create_success_result(
            data=data,
            data_type="annotations",
            fields_filled=fields_filled,
            source_url=f"{self.KEGG_API_BASE}/get/{pathway_id}"
        )
    
    def _fetch_reactions(self, pathway_id: str, **kwargs) -> FetchResult:
        """Fetch reaction data from KEGG.
        
        Args:
            pathway_id: KEGG pathway ID
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with reaction data
        """
        # TODO: Implement actual KEGG API call
        
        self.logger.info(f"Fetching reactions for pathway: {pathway_id}")
        
        data = {
            "pathway_id": pathway_id,
            "reactions": []
        }
        
        fields_filled = ["pathway_id"]
        
        return self._create_success_result(
            data=data,
            data_type="reactions",
            fields_filled=fields_filled,
            source_url=f"{self.KEGG_API_BASE}/link/reaction/{pathway_id}"
        )
    
    def is_available(self) -> bool:
        """Check if KEGG API is available.
        
        Returns:
            True if available (for now, always True)
        """
        # TODO: Implement actual availability check
        # Could ping KEGG API or check network connectivity
        return True
    
    def get_supported_data_types(self) -> List[str]:
        """Get supported data types for KEGG.
        
        Returns:
            List of supported data types
        """
        return [
            "coordinates",
            "annotations",
            "reactions",
            "pathways"
        ]
    
    @staticmethod
    def parse_pathway_id(pathway_id: str) -> Dict[str, str]:
        """Parse KEGG pathway ID into components.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., "hsa00010")
            
        Returns:
            Dictionary with organism and pathway number
            
        Example:
            >>> KEGGFetcher.parse_pathway_id("hsa00010")
            {'organism': 'hsa', 'pathway_number': '00010'}
        """
        if len(pathway_id) >= 3:
            return {
                "organism": pathway_id[:3],
                "pathway_number": pathway_id[3:]
            }
        return {"organism": "", "pathway_number": pathway_id}
    
    def __repr__(self) -> str:
        """String representation."""
        return f"KEGGFetcher(reliability={self.KEGG_RELIABILITY})"
