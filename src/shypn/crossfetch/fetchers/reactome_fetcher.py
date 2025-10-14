"""
Reactome Database Fetcher

Fetches pathway and interaction data from Reactome (https://reactome.org/).

Reactome is a high-quality source with reliability 0.95:
- Expert-curated pathway database
- Focus on human and model organism pathways
- Detailed protein-protein interactions
- Hierarchical pathway organization
- Cross-referenced to many databases

Supported data types:
- pathways: Pathway information and hierarchy
- interactions: Protein-protein interactions and complexes
- annotations: Species and reaction annotations
- reactions: Biochemical reactions and catalysis
- participants: Pathway participants (proteins, metabolites)

API Documentation: https://reactome.org/ContentService/
"""

from typing import Dict, Any, List, Optional
import time

# Import will be needed when requests is available
# import requests
# import json

from .base_fetcher import BaseFetcher
from ..models import FetchResult, FetchStatus


class ReactomeFetcher(BaseFetcher):
    """
    Fetcher for Reactome Pathway Database.
    
    Reactome provides expert-curated pathway data with detailed
    protein interactions and regulatory relationships.
    
    Reliability: 0.95 (expert-curated, peer-reviewed)
    
    Features:
    - Hierarchical pathway organization
    - Detailed protein-protein interactions
    - Complex formation data
    - Regulatory relationships
    - Cross-references to UniProt, ChEBI, etc.
    
    Example:
        >>> fetcher = ReactomeFetcher()
        >>> result = fetcher.fetch("R-HSA-70171", "interactions")
        >>> if result.is_successful():
        ...     print(f"Found {len(result.data['interactions'])} interactions")
    """
    
    # Reactome configuration
    REACTOME_RELIABILITY = 0.95  # Expert-curated
    REACTOME_API_BASE = "https://reactome.org/ContentService"
    REACTOME_DATA_API = f"{REACTOME_API_BASE}/data"
    REACTOME_QUERY_API = f"{REACTOME_API_BASE}/query"
    REACTOME_INTERACTORS_API = f"{REACTOME_API_BASE}/interactors"
    
    # Supported organisms (examples)
    SUPPORTED_ORGANISMS = {
        "HSA": "Homo sapiens",
        "MMU": "Mus musculus",
        "RNO": "Rattus norvegicus",
        "DME": "Drosophila melanogaster",
        "CEL": "Caenorhabditis elegans",
        "SCE": "Saccharomyces cerevisiae",
    }
    
    # Rate limiting
    MIN_REQUEST_INTERVAL = 0.3  # 300ms between requests
    
    def __init__(self):
        """Initialize Reactome fetcher."""
        super().__init__(
            source_name="Reactome",
            source_reliability=self.REACTOME_RELIABILITY
        )
        self._last_request_time = 0
        
    def fetch(
        self,
        pathway_id: str,
        data_type: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch data from Reactome Database.
        
        Args:
            pathway_id: Reactome pathway ID (e.g., "R-HSA-70171") or pathway name
            data_type: Type of data to fetch
            **kwargs: Additional parameters
                - organism: Organism code (e.g., "HSA" for human)
                - include_disease: Include disease pathways (default: False)
                - interactor_score: Minimum interaction score (0.0-1.0)
        
        Returns:
            FetchResult with requested data
            
        Note:
            Reactome IDs typically start with "R-" followed by organism code.
            Example: R-HSA-70171 (Glycolysis, Homo sapiens)
        """
        start_time = time.time()
        
        try:
            # Rate limiting
            self._rate_limit()
            
            # Route to appropriate fetch method
            if data_type == "pathways":
                result = self._fetch_pathway_info(pathway_id, **kwargs)
            elif data_type == "interactions":
                result = self._fetch_interactions(pathway_id, **kwargs)
            elif data_type == "annotations":
                result = self._fetch_annotations(pathway_id, **kwargs)
            elif data_type == "reactions":
                result = self._fetch_reactions(pathway_id, **kwargs)
            elif data_type == "participants":
                result = self._fetch_participants(pathway_id, **kwargs)
            else:
                return self._create_failed_result(
                    data_type=data_type,
                    error=f"Unsupported data type: {data_type}",
                    status=FetchStatus.FAILED
                )
            
            # Add fetch duration
            result.fetch_duration_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            return self._create_failed_result(
                data_type=data_type,
                error=f"Reactome fetch error: {str(e)}",
                status=FetchStatus.FAILED
            )
    
    def is_available(self) -> bool:
        """
        Check if Reactome API is available.
        
        Returns:
            True if API is accessible, False otherwise
        """
        # TODO: Implement actual availability check
        # For now, assume available
        return True
    
    def get_supported_data_types(self) -> List[str]:
        """
        Get list of supported data types.
        
        Returns:
            List of supported data type names
        """
        return [
            "pathways",
            "interactions",
            "annotations",
            "reactions",
            "participants"
        ]
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - time_since_last)
        
        self._last_request_time = time.time()
    
    def _fetch_pathway_info(
        self,
        pathway_id: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch pathway information from Reactome.
        
        Args:
            pathway_id: Reactome pathway ID
            **kwargs: include_disease flag
            
        Returns:
            FetchResult with pathway information
            
        Data format:
            {
                "pathway_id": str,
                "stable_id": str,
                "display_name": str,
                "species": str,
                "diagram_available": bool,
                "summation": str,
                "references": List[Dict],
                "cross_references": {
                    "uniprot": List[str],
                    "chebi": List[str],
                    "ensembl": List[str]
                },
                "hierarchy": {
                    "parent_pathways": List[str],
                    "child_pathways": List[str]
                },
                "disease_pathway": bool,
                "inferred": bool
            }
        """
        # TODO: Implement actual Reactome API call
        # Steps:
        # 1. Query Reactome Content Service for pathway details
        # 2. Get pathway hierarchy (parents, children)
        # 3. Extract summation and references
        # 4. Get cross-references
        # 5. Check for diagram availability
        
        # Stubbed implementation
        data = {
            "pathway_id": pathway_id,
            "stable_id": pathway_id,
            "display_name": f"Pathway {pathway_id}",
            "species": "Unknown",
            "diagram_available": False,
            "summation": "",
            "references": [],
            "cross_references": {},
            "hierarchy": {
                "parent_pathways": [],
                "child_pathways": []
            },
            "disease_pathway": False,
            "inferred": False
        }
        
        fields_filled = ["pathway_id", "stable_id", "display_name"]
        
        return self._create_success_result(
            data_type="pathways",
            data=data,
            fields_filled=fields_filled
        )
    
    def _fetch_interactions(
        self,
        pathway_id: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch protein-protein interactions from Reactome.
        
        Args:
            pathway_id: Reactome pathway ID
            **kwargs: interactor_score minimum score
            
        Returns:
            FetchResult with interaction data
            
        Data format:
            {
                "pathway_id": str,
                "interactions": [
                    {
                        "interaction_type": str,  # binding, catalysis, regulation
                        "participant_a": {
                            "id": str,
                            "name": str,
                            "type": str,  # protein, complex, small_molecule
                            "uniprot_id": str
                        },
                        "participant_b": {
                            "id": str,
                            "name": str,
                            "type": str,
                            "uniprot_id": str
                        },
                        "interaction_score": float,
                        "evidence": List[str],
                        "references": List[str]
                    }
                ],
                "complexes": [
                    {
                        "complex_id": str,
                        "name": str,
                        "components": List[str],
                        "stoichiometry": Dict[str, int]
                    }
                ],
                "total_interactions": int
            }
        """
        # TODO: Implement actual Reactome API call
        # Steps:
        # 1. Query Reactome for pathway participants
        # 2. Get protein-protein interactions
        # 3. Get complex formations
        # 4. Filter by interactor_score if provided
        # 5. Get evidence codes
        
        # Stubbed implementation
        data = {
            "pathway_id": pathway_id,
            "interactions": [],
            "complexes": [],
            "total_interactions": 0
        }
        
        fields_filled = ["pathway_id", "total_interactions"]
        
        return self._create_success_result(
            data_type="interactions",
            data=data,
            fields_filled=fields_filled
        )
    
    def _fetch_annotations(
        self,
        pathway_id: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch annotations from Reactome.
        
        Args:
            pathway_id: Reactome pathway ID
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with annotation data
            
        Data format:
            {
                "pathway_id": str,
                "protein_annotations": {
                    "protein_id": {
                        "name": str,
                        "gene_name": str,
                        "uniprot_id": str,
                        "ensembl_id": str,
                        "description": str,
                        "go_terms": List[str],
                        "modifications": List[Dict]
                    }
                },
                "molecule_annotations": {
                    "molecule_id": {
                        "name": str,
                        "chebi_id": str,
                        "formula": str,
                        "type": str  # small_molecule, polymer, etc.
                    }
                },
                "reaction_annotations": {
                    "reaction_id": {
                        "name": str,
                        "ec_number": str,
                        "go_terms": List[str],
                        "reversible": bool
                    }
                }
            }
        """
        # TODO: Implement actual Reactome API call
        # Steps:
        # 1. Query for pathway participants
        # 2. Get protein annotations (UniProt, Ensembl)
        # 3. Get small molecule annotations (ChEBI)
        # 4. Get reaction annotations (EC numbers, GO terms)
        
        # Stubbed implementation
        data = {
            "pathway_id": pathway_id,
            "protein_annotations": {},
            "molecule_annotations": {},
            "reaction_annotations": {}
        }
        
        fields_filled = ["pathway_id"]
        
        return self._create_success_result(
            data_type="annotations",
            data=data,
            fields_filled=fields_filled
        )
    
    def _fetch_reactions(
        self,
        pathway_id: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch biochemical reactions from Reactome.
        
        Args:
            pathway_id: Reactome pathway ID
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with reaction data
            
        Data format:
            {
                "pathway_id": str,
                "reactions": {
                    "reaction_id": {
                        "name": str,
                        "type": str,  # biochemical_reaction, polymerisation, etc.
                        "inputs": [
                            {
                                "id": str,
                                "name": str,
                                "stoichiometry": int,
                                "compartment": str
                            }
                        ],
                        "outputs": [
                            {
                                "id": str,
                                "name": str,
                                "stoichiometry": int,
                                "compartment": str
                            }
                        ],
                        "catalysts": List[str],
                        "regulators": [
                            {
                                "id": str,
                                "type": str,  # positive, negative
                                "mechanism": str
                            }
                        ],
                        "reversible": bool,
                        "ec_number": str,
                        "go_biological_process": str
                    }
                },
                "compartments": List[str]
            }
        """
        # TODO: Implement actual Reactome API call
        # Steps:
        # 1. Query for pathway reactions
        # 2. Get reaction participants (inputs, outputs)
        # 3. Get catalysts and regulators
        # 4. Get compartment information
        # 5. Get EC numbers and GO terms
        
        # Stubbed implementation
        data = {
            "pathway_id": pathway_id,
            "reactions": {},
            "compartments": []
        }
        
        fields_filled = ["pathway_id"]
        
        return self._create_success_result(
            data_type="reactions",
            data=data,
            fields_filled=fields_filled
        )
    
    def _fetch_participants(
        self,
        pathway_id: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch pathway participants (proteins, metabolites) from Reactome.
        
        Args:
            pathway_id: Reactome pathway ID
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with participant data
            
        Data format:
            {
                "pathway_id": str,
                "proteins": [
                    {
                        "id": str,
                        "name": str,
                        "uniprot_id": str,
                        "gene_name": str,
                        "compartment": str
                    }
                ],
                "complexes": [
                    {
                        "id": str,
                        "name": str,
                        "components": List[str],
                        "compartment": str
                    }
                ],
                "small_molecules": [
                    {
                        "id": str,
                        "name": str,
                        "chebi_id": str,
                        "formula": str,
                        "compartment": str
                    }
                ],
                "total_participants": int
            }
        """
        # TODO: Implement actual Reactome API call
        # Steps:
        # 1. Query for all pathway participants
        # 2. Separate by type (protein, complex, small molecule)
        # 3. Get cross-references (UniProt, ChEBI)
        # 4. Get compartment information
        
        # Stubbed implementation
        data = {
            "pathway_id": pathway_id,
            "proteins": [],
            "complexes": [],
            "small_molecules": [],
            "total_participants": 0
        }
        
        fields_filled = ["pathway_id", "total_participants"]
        
        return self._create_success_result(
            data_type="participants",
            data=data,
            fields_filled=fields_filled
        )
    
    def search_pathways(
        self,
        query: str,
        organism: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Reactome for pathways matching query.
        
        Args:
            query: Search query (pathway name, protein, etc.)
            organism: Filter by organism code (e.g., "HSA")
            limit: Maximum number of results
            
        Returns:
            List of matching pathway metadata
            
        Example:
            >>> fetcher = ReactomeFetcher()
            >>> pathways = fetcher.search_pathways("glycolysis", organism="HSA")
            >>> for pathway in pathways:
            ...     print(f"{pathway['id']}: {pathway['name']}")
        """
        # TODO: Implement Reactome search API
        # https://reactome.org/ContentService/search/query?query=glycolysis&species=HSA
        
        return []
    
    def get_pathway_hierarchy(self, pathway_id: str) -> Dict[str, Any]:
        """
        Get pathway hierarchy (parents and children).
        
        Args:
            pathway_id: Reactome pathway ID
            
        Returns:
            Dictionary with parent and child pathways
            
        Example:
            >>> fetcher = ReactomeFetcher()
            >>> hierarchy = fetcher.get_pathway_hierarchy("R-HSA-70171")
            >>> print(hierarchy['parent_pathways'])
        """
        # TODO: Implement hierarchy retrieval
        # https://reactome.org/ContentService/data/pathway/{id}/containedEvents
        
        return {
            "pathway_id": pathway_id,
            "parent_pathways": [],
            "child_pathways": [],
            "siblings": []
        }
    
    def get_pathway_url(self, pathway_id: str) -> str:
        """
        Get Reactome pathway browser URL.
        
        Args:
            pathway_id: Reactome pathway ID
            
        Returns:
            URL to pathway page
        """
        return f"https://reactome.org/PathwayBrowser/#/{pathway_id}"
    
    def get_pathway_diagram_url(self, pathway_id: str) -> str:
        """
        Get URL for pathway diagram.
        
        Args:
            pathway_id: Reactome pathway ID
            
        Returns:
            URL to pathway diagram
        """
        return f"https://reactome.org/ContentService/exporter/diagram/{pathway_id}.png"
    
    def parse_pathway_id(self, pathway_id: str) -> Optional[Dict[str, str]]:
        """
        Parse Reactome pathway ID to extract organism and numeric ID.
        
        Args:
            pathway_id: Reactome ID (e.g., "R-HSA-70171")
            
        Returns:
            Dictionary with organism and id, or None if invalid
            
        Example:
            >>> fetcher = ReactomeFetcher()
            >>> parsed = fetcher.parse_pathway_id("R-HSA-70171")
            >>> print(parsed)
            {'organism': 'HSA', 'numeric_id': '70171', 'species': 'Homo sapiens'}
        """
        if not pathway_id.startswith("R-"):
            return None
        
        parts = pathway_id.split("-")
        if len(parts) < 3:
            return None
        
        organism_code = parts[1]
        numeric_id = "-".join(parts[2:])
        
        return {
            "organism": organism_code,
            "numeric_id": numeric_id,
            "species": self.SUPPORTED_ORGANISMS.get(organism_code, "Unknown")
        }
