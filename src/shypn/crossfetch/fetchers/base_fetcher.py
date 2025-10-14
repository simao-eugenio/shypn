"""
Base Fetcher Class

Abstract base class for all external data source fetchers.

Author: Shypn Development Team
Date: October 2025
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..models import FetchResult, FetchStatus, QualityMetrics, SourceAttribution


class BaseFetcher(ABC):
    """Abstract base class for data fetchers.
    
    Each fetcher is responsible for retrieving data from a specific external
    source (KEGG, BioModels, etc.) and converting it to a standardized format.
    """
    
    def __init__(self, source_name: str, source_reliability: float = 0.85):
        """Initialize fetcher.
        
        Args:
            source_name: Name of the data source
            source_reliability: Reliability score (0.0-1.0)
        """
        self.source_name = source_name
        self.source_reliability = source_reliability
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._fetch_count = 0
        self._error_count = 0
    
    @abstractmethod
    def fetch(self,
             pathway_id: str,
             data_type: str,
             **kwargs) -> FetchResult:
        """Fetch data from the source.
        
        Args:
            pathway_id: Pathway identifier
            data_type: Type of data to fetch (coordinates, concentrations, etc.)
            **kwargs: Additional parameters
            
        Returns:
            FetchResult with data and quality metrics
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the source is currently available.
        
        Returns:
            True if source can be accessed
        """
        pass
    
    @abstractmethod
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types.
        
        Returns:
            List of data type strings
        """
        pass
    
    def supports_data_type(self, data_type: str) -> bool:
        """Check if this fetcher supports a data type.
        
        Args:
            data_type: Data type to check
            
        Returns:
            True if supported
        """
        return data_type in self.get_supported_data_types()
    
    def _create_attribution(self,
                           source_url: Optional[str] = None,
                           **kwargs) -> SourceAttribution:
        """Create source attribution.
        
        Args:
            source_url: URL to the source
            **kwargs: Additional attribution fields
            
        Returns:
            SourceAttribution instance
        """
        return SourceAttribution(
            source_name=self.source_name,
            source_url=source_url,
            **kwargs
        )
    
    def _create_quality_metrics(self,
                               completeness: float,
                               consistency: float = 1.0,
                               validation_status: float = 1.0) -> QualityMetrics:
        """Create quality metrics.
        
        Args:
            completeness: Completeness score (0.0-1.0)
            consistency: Consistency score (0.0-1.0)
            validation_status: Validation score (0.0-1.0)
            
        Returns:
            QualityMetrics instance
        """
        return QualityMetrics(
            completeness=completeness,
            source_reliability=self.source_reliability,
            consistency=consistency,
            validation_status=validation_status
        )
    
    def _create_failed_result(self,
                            data_type: str,
                            error: str,
                            status: FetchStatus = FetchStatus.FAILED) -> FetchResult:
        """Create a failed fetch result.
        
        Args:
            data_type: Type of data
            error: Error message
            status: Fetch status
            
        Returns:
            Failed FetchResult
        """
        self._error_count += 1
        return FetchResult.create_failed(
            data_type=data_type,
            source_name=self.source_name,
            error=error,
            status=status
        )
    
    def _create_success_result(self,
                             data: Dict[str, Any],
                             data_type: str,
                             fields_filled: List[str],
                             fetch_duration_ms: Optional[float] = None,
                             **kwargs) -> FetchResult:
        """Create a successful fetch result.
        
        Args:
            data: Fetched data
            data_type: Type of data
            fields_filled: List of fields filled
            fetch_duration_ms: Fetch duration in milliseconds
            **kwargs: Additional parameters
            
        Returns:
            Successful FetchResult
        """
        self._fetch_count += 1
        
        completeness = len(fields_filled) / max(len(data), 1) if data else 0.0
        
        result = FetchResult(
            data=data,
            data_type=data_type,
            status=FetchStatus.SUCCESS,
            quality_metrics=self._create_quality_metrics(completeness),
            attribution=self._create_attribution(**kwargs),
            fields_filled=fields_filled,
            fetch_duration_ms=fetch_duration_ms
        )
        
        return result
    
    def get_statistics(self) -> Dict[str, int]:
        """Get fetcher statistics.
        
        Returns:
            Dictionary with fetch and error counts
        """
        return {
            "total_fetches": self._fetch_count,
            "total_errors": self._error_count,
            "success_rate": (
                (self._fetch_count - self._error_count) / self._fetch_count
                if self._fetch_count > 0 else 0.0
            )
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self._fetch_count = 0
        self._error_count = 0
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"source={self.source_name}, "
            f"reliability={self.source_reliability:.2f})"
        )
