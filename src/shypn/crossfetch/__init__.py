"""
Cross-Fetch Information Enrichment System

Multi-source pathway data enrichment with quality-based selection.

This package provides a comprehensive system for enriching pathway data
by fetching information from multiple reliable sources (KEGG, BioModels,
Reactome, etc.) and selecting the best quality data through automated
scoring and conflict resolution.

Features:
- Multi-source data fetching (KEGG, BioModels, Reactome, WikiPathways, etc.)
- Quality-based selection with configurable weights
- Automatic conflict resolution with voting strategies
- Complete enrichment provenance tracking
- Metadata management with automatic operation logging

Main Components:
- EnrichmentPipeline: Main orchestrator for enrichment workflow
- Fetchers: Source-specific data fetchers (KEGG, BioModels, etc.)
- QualityScorer: Evaluates and ranks fetch results
- MetadataManager: Tracks enrichment provenance

Usage Example:
--------------
    from pathlib import Path
    from shypn.crossfetch import EnrichmentPipeline, EnrichmentRequest
    
    # Create pipeline
    pipeline = EnrichmentPipeline()
    
    # Create enrichment request
    request = EnrichmentRequest.create_simple(
        pathway_id="hsa00010",
        data_types=["coordinates", "concentrations"]
    )
    
    # Enrich pathway
    results = pipeline.enrich(Path("glycolysis.shy"), request)
    
    # Check results
    for enrichment in results['enrichments']:

Author: Shypn Development Team
Date: October 2025
"""

# Core components
from .core import (
    EnrichmentPipeline,
    QualityScorer
)

# Data models
from .models import (
    FetchResult,
    FetchStatus,
    QualityMetrics,
    SourceAttribution,
    EnrichmentRequest,
    DataType,
    EnrichmentPriority
)

# Fetchers
from .fetchers import (
    BaseFetcher,
    KEGGFetcher,
    BioModelsFetcher,
    ReactomeFetcher
)

# Enrichers
from .enrichers import (
    EnricherBase,
    EnrichmentChange,
    EnrichmentResult,
    ConcentrationEnricher,
    InteractionEnricher,
    KineticsEnricher,
    AnnotationEnricher,
    InteractionType,
    KineticLawType,
    ConflictResolutionStrategy
)

# Metadata management
from .metadata import (
    BaseMetadataManager,
    JSONMetadataManager,
    MetadataManagerFactory,
    MetadataFormat,
    create_metadata_manager,
    create_json_manager,
    FileOperationsTracker
)


__all__ = [
    # Core
    "EnrichmentPipeline",
    "QualityScorer",
    
    # Models
    "FetchResult",
    "FetchStatus",
    "QualityMetrics",
    "SourceAttribution",
    "EnrichmentRequest",
    "DataType",
    "EnrichmentPriority",
    
    # Fetchers
    "BaseFetcher",
    "KEGGFetcher",
    "BioModelsFetcher",
    "ReactomeFetcher",
    
    # Enrichers
    "EnricherBase",
    "EnrichmentChange",
    "EnrichmentResult",
    "ConcentrationEnricher",
    "InteractionEnricher",
    "KineticsEnricher",
    "AnnotationEnricher",
    "InteractionType",
    "KineticLawType",
    "ConflictResolutionStrategy",
    
    # Metadata
    "BaseMetadataManager",
    "JSONMetadataManager",
    "MetadataManagerFactory",
    "MetadataFormat",
    "create_metadata_manager",
    "create_json_manager",
    "FileOperationsTracker",
]


__version__ = "1.0.0"
__author__ = "Shypn Development Team"
