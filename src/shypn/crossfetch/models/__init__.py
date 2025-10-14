"""
Cross-Fetch Data Models

Data structures for the cross-fetch enrichment system.

Author: Shypn Development Team
Date: October 2025
"""

from .fetch_result import (
    FetchResult,
    FetchStatus,
    QualityMetrics,
    SourceAttribution
)

from .enrichment_request import (
    EnrichmentRequest,
    DataType,
    EnrichmentPriority
)

__all__ = [
    # Fetch result models
    "FetchResult",
    "FetchStatus",
    "QualityMetrics",
    "SourceAttribution",
    
    # Enrichment request models
    "EnrichmentRequest",
    "DataType",
    "EnrichmentPriority",
]
