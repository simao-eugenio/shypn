"""
Enrichment Pipeline

Main orchestrator for the cross-fetch enrichment system.
Coordinates fetchers, scores quality, resolves conflicts, and enriches pathway data.

Author: Shypn Development Team
Date: October 2025
"""

from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from ..models import (
    EnrichmentRequest,
    FetchResult,
    DataType,
    FetchStatus
)
from ..fetchers import BaseFetcher, KEGGFetcher, BioModelsFetcher, ReactomeFetcher
from ..enrichers import (
    EnricherBase,
    ConcentrationEnricher,
    InteractionEnricher,
    KineticsEnricher,
    AnnotationEnricher
)
from .quality_scorer import QualityScorer
from ..metadata import create_metadata_manager, FileOperationsTracker


class EnrichmentPipeline:
    """Main pipeline for enriching pathway data from multiple sources.
    
    Workflow:
    1. Receive enrichment request
    2. Query relevant fetchers
    3. Collect results from multiple sources
    4. Score quality of each result
    5. Resolve conflicts using voting policies
    6. Apply enrichments to pathway
    7. Log enrichments in metadata
    """
    
    def __init__(self):
        """Initialize enrichment pipeline."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Components
        self.quality_scorer = QualityScorer()
        self.metadata_tracker = FileOperationsTracker()
        
        # Registry of fetchers
        self.fetchers: Dict[str, BaseFetcher] = {}
        
        # Registry of enrichers
        self.enrichers: Dict[str, EnricherBase] = {}
        
        # Statistics
        self.total_enrichments = 0
        self.successful_enrichments = 0
        self.failed_enrichments = 0
        
        # Initialize default fetchers and enrichers
        self._register_default_fetchers()
        self._register_default_enrichers()
    
    def _register_default_fetchers(self):
        """Register default fetchers."""
        self.register_fetcher(KEGGFetcher())
        self.register_fetcher(BioModelsFetcher())
        self.register_fetcher(ReactomeFetcher())
        # TODO: Add more fetchers as they are implemented
        # self.register_fetcher(WikiPathwaysFetcher())
        # self.register_fetcher(ChEBIFetcher())
    
    def _register_default_enrichers(self):
        """Register default enrichers."""
        self.register_enricher(ConcentrationEnricher(scale_factor=1000.0))
        self.register_enricher(InteractionEnricher(create_missing=True, min_confidence=0.7))
        self.register_enricher(KineticsEnricher(prefer_time_aware=True))
        self.register_enricher(AnnotationEnricher(
            conflict_strategy="highest_quality",
            merge_multi_valued=True,
            keep_provenance=True
        ))
    
    def register_fetcher(self, fetcher: BaseFetcher):
        """Register a data fetcher.
        
        Args:
            fetcher: BaseFetcher instance
        """
        self.fetchers[fetcher.source_name] = fetcher
        self.logger.info(f"Registered fetcher: {fetcher.source_name}")
    
    def register_enricher(self, enricher: EnricherBase):
        """Register a data enricher.
        
        Args:
            enricher: EnricherBase instance
        """
        self.enrichers[enricher.enricher_name] = enricher
        self.logger.info(f"Registered enricher: {enricher.enricher_name}")
    
    def unregister_fetcher(self, source_name: str):
        """Unregister a fetcher.
        
        Args:
            source_name: Name of source to unregister
        """
        if source_name in self.fetchers:
            del self.fetchers[source_name]
            self.logger.info(f"Unregistered fetcher: {source_name}")
    
    def unregister_enricher(self, enricher_name: str):
        """Unregister an enricher.
        
        Args:
            enricher_name: Name of enricher to unregister
        """
        if enricher_name in self.enrichers:
            del self.enrichers[enricher_name]
            self.logger.info(f"Unregistered enricher: {enricher_name}")
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources.
        
        Returns:
            List of source names
        """
        return [
            name for name, fetcher in self.fetchers.items()
            if fetcher.is_available()
        ]
    
    def fetch(self,
             pathway_id: str,
             preferred_sources: Optional[List[str]] = None,
             data_types: Optional[List[str]] = None) -> List[FetchResult]:
        """Fetch pathway data from external sources (for importing new pathways).
        
        This is the entry point for importing new pathways into Shypn.
        It fetches data from multiple sources, scores quality, and returns
        the best results for each data type.
        
        Use this when:
        - User wants to import a pathway from KEGG/BioModels/Reactome
        - Creating a new Shypn model from external data
        - Building a pathway from scratch
        
        Args:
            pathway_id: Pathway identifier (e.g., "hsa00010", "BIOMD0000000002")
            preferred_sources: List of source names to query (default: all available)
            data_types: List of data types to fetch (default: ["pathway", "concentrations", "kinetics"])
            
        Returns:
            List of FetchResult objects (one per data type, best quality source selected)
            
        Example:
            >>> pipeline = EnrichmentPipeline()
            >>> results = pipeline.fetch("hsa00010", preferred_sources=["KEGG"])
            >>> for result in results:
            ...     print(f"{result.data_type}: {len(result.data.get('species', []))} species")
        """
        self.logger.info(f"Fetching pathway data for: {pathway_id}")
        
        # Default to all available sources
        if preferred_sources is None:
            preferred_sources = self.get_available_sources()
        
        # Default to common data types
        if data_types is None:
            data_types = ["pathway", "concentrations", "kinetics", "interactions", "annotations"]
        
        # Create request object  
        request = EnrichmentRequest(
            pathway_id=pathway_id,
            preferred_sources=preferred_sources
        )
        
        # Fetch from all sources for all data types
        all_results = []
        for data_type_str in data_types:
            fetch_results = self._fetch_from_sources(request, data_type_str)
            
            # Filter successful results
            successful = [fr for fr in fetch_results if fr.is_usable()]
            
            if not successful:
                self.logger.warning(f"No successful fetches for data type: {data_type_str}")
                continue
            
            # Score quality of each result
            for result in successful:
                result.quality_score = self.quality_scorer.score(result)
            
            # Select best result for this data type
            best_result = max(successful, key=lambda r: r.quality_score)
            all_results.append(best_result)
            
            self.logger.info(
                f"Selected {best_result.source} for {data_type_str} "
                f"(quality: {best_result.quality_score:.2f})"
            )
        
        self.logger.info(f"Fetch complete: {len(all_results)} data types retrieved")
        return all_results
    
    def enrich(self,
              pathway_file: Path,
              request: EnrichmentRequest,
              pathway_object: Optional[Any] = None) -> Dict[str, Any]:
        """Enrich pathway data based on request.
        
        Args:
            pathway_file: Path to pathway file
            request: EnrichmentRequest specifying what to enrich
            pathway_object: Optional pathway object to enrich (if None, only metadata updated)
            
        Returns:
            Dictionary with enrichment results
        """
        self.logger.info(f"Starting enrichment for pathway: {request.pathway_id}")
        
        results = {
            "pathway_id": request.pathway_id,
            "pathway_file": str(pathway_file),
            "enrichments": [],
            "applied_enrichments": [],
            "errors": [],
            "statistics": {}
        }
        
        try:
            # Get metadata manager for this pathway
            metadata_mgr = create_metadata_manager(pathway_file)
            
            # Ensure metadata exists
            if not metadata_mgr.exists():
                metadata_mgr.create()
            
            # Process each requested data type
            for data_type in request.get_data_types():
                enrichment_result = self._enrich_data_type(
                    request,
                    data_type,
                    metadata_mgr,
                    pathway_object
                )
                results["enrichments"].append(enrichment_result)
                
                # If we have a pathway object and enrichment was successful, apply it
                if pathway_object and enrichment_result.get("fetch_result"):
                    applied_result = self._apply_enrichment(
                        pathway_object,
                        enrichment_result["fetch_result"],
                        data_type
                    )
                    results["applied_enrichments"].append(applied_result)
            
            # Update statistics
            results["statistics"] = self._get_statistics()
            
            self.logger.info(f"Enrichment complete for pathway: {request.pathway_id}")
            
        except Exception as e:
            error_msg = f"Enrichment failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)
            self.failed_enrichments += 1
        
        return results
    
    def _enrich_data_type(self,
                         request: EnrichmentRequest,
                         data_type: DataType,
                         metadata_mgr,
                         pathway_object: Optional[Any] = None) -> Dict[str, Any]:
        """Enrich a specific data type.
        
        Args:
            request: EnrichmentRequest
            data_type: DataType to enrich
            metadata_mgr: Metadata manager instance
            pathway_object: Optional pathway object to enrich
            
        Returns:
            Dictionary with enrichment result
        """
        self.logger.info(f"Enriching data type: {data_type.value}")
        
        result = {
            "data_type": data_type.value,
            "sources_queried": [],
            "sources_successful": [],
            "best_source": None,
            "quality_score": 0.0,
            "fields_enriched": [],
            "fetch_result": None,
            "errors": []
        }
        
        try:
            # Fetch from multiple sources
            fetch_results = self._fetch_from_sources(
                request,
                data_type.value
            )
            
            result["sources_queried"] = [
                fr.attribution.source_name for fr in fetch_results
            ]
            
            # Filter successful results
            successful = [fr for fr in fetch_results if fr.is_usable()]
            result["sources_successful"] = [
                fr.attribution.source_name for fr in successful
            ]
            
            if not successful:
                result["errors"].append("No successful fetches from any source")
                self.failed_enrichments += 1
                return result
            
            # Get best result based on quality
            best_result = self.quality_scorer.get_best_result(
                successful,
                min_score=request.min_quality_score
            )
            
            if not best_result:
                result["errors"].append(
                    f"No results met minimum quality threshold: {request.min_quality_score}"
                )
                self.failed_enrichments += 1
                return result
            
            # Store fetch result for later enrichment
            result["fetch_result"] = best_result
            
            # Record enrichment in metadata
            metadata_mgr.add_enrichment_record(
                data_type=data_type.value,
                source=best_result.attribution.source_name,
                quality_score=best_result.get_quality_score(),
                fields_enriched=best_result.fields_filled,
                details={
                    "source_url": best_result.attribution.source_url,
                    "fetch_duration_ms": best_result.fetch_duration_ms
                }
            )
            
            # Update result
            result["best_source"] = best_result.attribution.source_name
            result["quality_score"] = best_result.get_quality_score()
            result["fields_enriched"] = best_result.fields_filled
            
            self.successful_enrichments += 1
            self.total_enrichments += 1
            
        except Exception as e:
            error_msg = f"Error enriching {data_type.value}: {e}"
            self.logger.error(error_msg)
            result["errors"].append(error_msg)
            self.failed_enrichments += 1
        
        return result
    
    def _apply_enrichment(self,
                         pathway_object: Any,
                         fetch_result: FetchResult,
                         data_type: DataType) -> Dict[str, Any]:
        """Apply enrichment to pathway object using appropriate enricher.
        
        Args:
            pathway_object: Pathway object to enrich
            fetch_result: FetchResult containing data to apply
            data_type: Type of data being applied
            
        Returns:
            Dictionary with application result
        """
        result = {
            "data_type": data_type.value,
            "enricher_used": None,
            "success": False,
            "objects_modified": 0,
            "changes": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Find appropriate enricher
            enricher = self._select_enricher(data_type.value)
            
            if not enricher:
                result["errors"].append(f"No enricher available for data type: {data_type.value}")
                return result
            
            result["enricher_used"] = enricher.enricher_name
            
            # Apply enrichment
            enrichment_result = enricher.apply(pathway_object, fetch_result)
            
            # Extract results
            result["success"] = enrichment_result.success
            result["objects_modified"] = enrichment_result.objects_modified
            result["changes"] = [
                {
                    "object_id": change.object_id,
                    "object_type": change.object_type,
                    "property": change.property_name,
                    "old_value": change.old_value,
                    "new_value": change.new_value
                }
                for change in enrichment_result.changes
            ]
            result["errors"] = enrichment_result.errors
            result["warnings"] = enrichment_result.warnings
            
            self.logger.info(
                f"Applied {enricher.enricher_name}: "
                f"{enrichment_result.objects_modified} objects modified"
            )
            
        except Exception as e:
            error_msg = f"Error applying enrichment: {e}"
            self.logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    def _select_enricher(self, data_type: str) -> Optional[EnricherBase]:
        """Select appropriate enricher for data type.
        
        Args:
            data_type: Type of data to enrich
            
        Returns:
            EnricherBase instance or None
        """
        # Map data types to enrichers
        data_type_lower = data_type.lower()
        
        for enricher in self.enrichers.values():
            if enricher.can_enrich(data_type_lower):
                return enricher
        
        return None
    
    def _fetch_from_sources(self,
                           request: EnrichmentRequest,
                           data_type: str) -> List[FetchResult]:
        """Fetch data from multiple sources.
        
        Args:
            request: EnrichmentRequest
            data_type: Data type to fetch
            
        Returns:
            List of FetchResults from different sources
        """
        results = []
        
        for source_name, fetcher in self.fetchers.items():
            # Check if source is allowed
            if not request.is_source_allowed(source_name):
                continue
            
            # Check if fetcher supports this data type
            if not fetcher.supports_data_type(data_type):
                continue
            
            # Check if source is available
            if not fetcher.is_available():
                self.logger.warning(f"Source {source_name} is not available")
                continue
            
            # Fetch data
            try:
                fetch_result = fetcher.fetch(
                    pathway_id=request.pathway_id,
                    data_type=data_type
                )
                results.append(fetch_result)
            except Exception as e:
                self.logger.error(f"Fetch failed from {source_name}: {e}")
        
        return results
    
    def _get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_enrichments": self.total_enrichments,
            "successful_enrichments": self.successful_enrichments,
            "failed_enrichments": self.failed_enrichments,
            "success_rate": (
                self.successful_enrichments / self.total_enrichments
                if self.total_enrichments > 0 else 0.0
            ),
            "registered_sources": list(self.fetchers.keys()),
            "available_sources": self.get_available_sources()
        }
    
    def reset_statistics(self):
        """Reset pipeline statistics."""
        self.total_enrichments = 0
        self.successful_enrichments = 0
        self.failed_enrichments = 0
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EnrichmentPipeline("
            f"fetchers={len(self.fetchers)}, "
            f"enrichers={len(self.enrichers)}, "
            f"enrichments={self.total_enrichments})"
        )
