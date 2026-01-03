"""BiGG model listing and search service.

Provides functionality to fetch, filter, and search BiGG model catalog.
"""

import urllib.request
import json
from typing import List, Optional, Dict
from dataclasses import dataclass

from .base_bigg_service import BaseBiGGService


@dataclass
class BiGGModelInfo:
    """Data class for BiGG model metadata.
    
    Attributes:
        id: BiGG model identifier (e.g., 'e_coli_core')
        name: Full model name
        organism: Organism name
        reaction_count: Number of reactions
        metabolite_count: Number of metabolites
        gene_count: Number of genes
        compartment_count: Number of compartments
        publication_doi: DOI of publication (if available)
    """
    id: str
    name: str
    organism: str
    reaction_count: int
    metabolite_count: int
    gene_count: int
    compartment_count: int = 0
    publication_doi: Optional[str] = None


class BiGGModelFetcher(BaseBiGGService):
    """Service for fetching and searching BiGG models.
    
    Handles model list retrieval, filtering by organism,
    and search functionality. Implements caching to minimize
    API requests.
    
    Attributes:
        _model_cache: Cached list of models to avoid repeated API calls
    """
    
    def __init__(self):
        """Initialize model fetcher service."""
        super().__init__()
        self._model_cache: Optional[List[BiGGModelInfo]] = None
    
    def validate(self) -> bool:
        """Check if BiGG API is accessible.
        
        Returns:
            True if API is accessible and responding
        """
        try:
            url = f"{self.base_url}/api/v2/database_version"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                api_version = data.get('api_version', 'unknown')
                self.logger.info(f"BiGG API accessible, version: {api_version}")
                return True
        except Exception as e:
            self.logger.error(f"BiGG API validation failed: {e}")
            return False
    
    def fetch_models(self, force_refresh: bool = False) -> List[BiGGModelInfo]:
        """Fetch list of all available models.
        
        Args:
            force_refresh: If True, bypass cache and fetch from API
            
        Returns:
            List of BiGGModelInfo objects
        """
        # Return cached models if available
        if self._model_cache and not force_refresh:
            self.logger.debug(f"Returning {len(self._model_cache)} cached models")
            return self._model_cache
        
        try:
            url = f"{self.base_url}/api/v2/models"
            self.logger.info(f"Fetching models from {url}")
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read())
            
            models = []
            for model_data in data.get('results', []):
                models.append(BiGGModelInfo(
                    id=model_data.get('bigg_id', ''),
                    name=model_data.get('organism', ''),
                    organism=model_data.get('organism', ''),
                    reaction_count=model_data.get('reaction_count', 0),
                    metabolite_count=model_data.get('metabolite_count', 0),
                    gene_count=model_data.get('gene_count', 0),
                    compartment_count=0  # Not provided in list endpoint
                ))
            
            self._model_cache = models
            self.logger.info(f"Fetched {len(models)} BiGG models")
            return models
            
        except Exception as e:
            self._handle_http_error(e, "fetch models")
            return []
    
    def filter_by_organism(self, organism_query: str) -> List[BiGGModelInfo]:
        """Filter models by organism name.
        
        Args:
            organism_query: Organism name or partial name (case-insensitive)
            
        Returns:
            List of models matching the organism query
        """
        models = self.fetch_models()
        query_lower = organism_query.lower()
        filtered = [m for m in models if query_lower in m.organism.lower()]
        self.logger.debug(f"Filtered to {len(filtered)} models for organism '{organism_query}'")
        return filtered
    
    def search_models(self, query: str) -> List[BiGGModelInfo]:
        """Search models by ID, name, or organism.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of models matching the search query
        """
        if not query:
            return self.fetch_models()
        
        models = self.fetch_models()
        query_lower = query.lower()
        results = [
            m for m in models
            if query_lower in m.id.lower() or query_lower in m.organism.lower()
        ]
        self.logger.debug(f"Search for '{query}' returned {len(results)} results")
        return results
    
    def get_model_details(self, model_id: str) -> Optional[Dict]:
        """Get detailed metadata for specific model.
        
        Args:
            model_id: BiGG model identifier
            
        Returns:
            Dictionary with detailed model information, or None if not found
        """
        try:
            url = f"{self.base_url}/api/v2/models/{model_id}"
            self.logger.info(f"Fetching details for model '{model_id}'")
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read())
            
            self.logger.debug(f"Retrieved details for {model_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to get details for model '{model_id}': {e}")
            return None
    
    def clear_cache(self):
        """Clear the model cache."""
        self._model_cache = None
        self.logger.debug("Model cache cleared")
