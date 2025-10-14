"""
Fetch Result Data Model

Represents the result of a data fetch operation from an external source.

Author: Shypn Development Team
Date: October 2025
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class FetchStatus(Enum):
    """Status of a fetch operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"


@dataclass
class SourceAttribution:
    """Attribution information for fetched data."""
    source_name: str
    source_url: Optional[str] = None
    database_version: Optional[str] = None
    fetch_timestamp: datetime = field(default_factory=datetime.now)
    license: Optional[str] = None
    citation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_name": self.source_name,
            "source_url": self.source_url,
            "database_version": self.database_version,
            "fetch_timestamp": self.fetch_timestamp.isoformat(),
            "license": self.license,
            "citation": self.citation
        }


@dataclass
class QualityMetrics:
    """Quality metrics for fetched data."""
    completeness: float  # 0.0-1.0: fraction of requested fields filled
    source_reliability: float  # 0.0-1.0: known reliability of source
    consistency: float  # 0.0-1.0: internal consistency check
    validation_status: float  # 0.0-1.0: passed validation checks
    
    def overall_score(self) -> float:
        """Calculate overall quality score.
        
        Formula: 0.25*completeness + 0.30*reliability + 0.20*consistency + 0.25*validation
        """
        return (
            0.25 * self.completeness +
            0.30 * self.source_reliability +
            0.20 * self.consistency +
            0.25 * self.validation_status
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "completeness": self.completeness,
            "source_reliability": self.source_reliability,
            "consistency": self.consistency,
            "validation_status": self.validation_status,
            "overall_score": self.overall_score()
        }


@dataclass
class FetchResult:
    """Result of a data fetch operation.
    
    Represents data fetched from an external source with quality metrics
    and attribution information.
    """
    
    # Core data
    data: Dict[str, Any]
    data_type: str  # coordinates, concentrations, kinetics, etc.
    
    # Status
    status: FetchStatus
    
    # Quality and attribution
    quality_metrics: QualityMetrics
    attribution: SourceAttribution
    
    # Metadata
    fields_filled: List[str] = field(default_factory=list)
    fields_missing: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Query info
    query_params: Dict[str, Any] = field(default_factory=dict)
    fetch_duration_ms: Optional[float] = None
    
    def is_successful(self) -> bool:
        """Check if fetch was successful."""
        return self.status == FetchStatus.SUCCESS
    
    def is_usable(self) -> bool:
        """Check if result is usable (success or partial)."""
        return self.status in (FetchStatus.SUCCESS, FetchStatus.PARTIAL)
    
    def get_quality_score(self) -> float:
        """Get overall quality score."""
        return self.quality_metrics.overall_score()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "data": self.data,
            "data_type": self.data_type,
            "status": self.status.value,
            "quality_metrics": self.quality_metrics.to_dict(),
            "attribution": self.attribution.to_dict(),
            "fields_filled": self.fields_filled,
            "fields_missing": self.fields_missing,
            "errors": self.errors,
            "warnings": self.warnings,
            "query_params": self.query_params,
            "fetch_duration_ms": self.fetch_duration_ms
        }
    
    @classmethod
    def create_failed(cls,
                     data_type: str,
                     source_name: str,
                     error: str,
                     status: FetchStatus = FetchStatus.FAILED) -> 'FetchResult':
        """Create a failed fetch result.
        
        Args:
            data_type: Type of data being fetched
            source_name: Name of the source
            error: Error message
            status: Fetch status (default: FAILED)
            
        Returns:
            Failed FetchResult instance
        """
        return cls(
            data={},
            data_type=data_type,
            status=status,
            quality_metrics=QualityMetrics(
                completeness=0.0,
                source_reliability=0.0,
                consistency=0.0,
                validation_status=0.0
            ),
            attribution=SourceAttribution(source_name=source_name),
            errors=[error]
        )
    
    @classmethod
    def create_success(cls,
                      data: Dict[str, Any],
                      data_type: str,
                      source_name: str,
                      fields_filled: List[str],
                      source_reliability: float = 0.85) -> 'FetchResult':
        """Create a successful fetch result.
        
        Args:
            data: Fetched data
            data_type: Type of data
            source_name: Name of the source
            fields_filled: List of fields successfully filled
            source_reliability: Reliability score of source (0.0-1.0)
            
        Returns:
            Successful FetchResult instance
        """
        completeness = 1.0 if fields_filled else 0.0
        
        return cls(
            data=data,
            data_type=data_type,
            status=FetchStatus.SUCCESS,
            quality_metrics=QualityMetrics(
                completeness=completeness,
                source_reliability=source_reliability,
                consistency=1.0,  # Assume consistent for now
                validation_status=1.0  # Assume validated for now
            ),
            attribution=SourceAttribution(source_name=source_name),
            fields_filled=fields_filled
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FetchResult(data_type={self.data_type}, "
            f"source={self.attribution.source_name}, "
            f"status={self.status.value}, "
            f"quality={self.get_quality_score():.2f})"
        )
