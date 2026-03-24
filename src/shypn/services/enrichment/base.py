"""Base enricher class for model enrichment operations.

This module defines the abstract base class for all enrichers that modify
DocumentModel objects by adding missing information from external sources.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Callable, Dict, Any, List
import logging


if TYPE_CHECKING:
    from shypn.data.canvas.document_model import DocumentModel



logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Result of an enrichment operation.
    
    Attributes:
        success: Whether enrichment completed successfully
        message: Human-readable result message
        statistics: Dictionary of enrichment statistics
        errors: List of error messages encountered
        warnings: List of warning messages
        duration_seconds: Time taken for enrichment
        modified_elements: IDs of modified model elements
    """
    success: bool
    message: str
    statistics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    modified_elements: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_statistic(self, key: str, value: Any):
        """Add a statistic to the result."""
        self.statistics[key] = value
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        logger.error(f"Enrichment error: {message}")
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(f"Enrichment warning: {message}")
    
    def get_summary(self) -> str:
        """Get human-readable summary of enrichment.
        
        Returns:
            Multi-line string with enrichment summary
        """
        lines = [
            f"Enrichment {'succeeded' if self.success else 'failed'}: {self.message}",
            f"Duration: {self.duration_seconds:.2f} seconds",
            ""
        ]
        
        if self.statistics:
            lines.append("Statistics:")
            for key, value in self.statistics.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5
                lines.append(f"  ⚠️  {warning}")
            if len(self.warnings) > 5:
                lines.append(f"  ... and {len(self.warnings) - 5} more")
            lines.append("")
        
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5
                lines.append(f"  ❌ {error}")
            if len(self.errors) > 5:
                lines.append(f"  ... and {len(self.errors) - 5} more")
        
        return "\n".join(lines)


class BaseEnricher(ABC):
    """Abstract base class for model enrichers.
    
    Enrichers fetch additional information from external sources and add it
    to DocumentModel objects. Examples: name enrichment, stoichiometry enrichment,
    kinetic parameter enrichment, etc.
    
    Subclasses must implement:
    - enrich_document(): Main enrichment logic
    - validate_document(): Check if document can be enriched
    - get_enricher_name(): Return enricher identifier
    
    Attributes:
        progress_callback: Optional callback for progress reporting
                          Signature: callback(current: int, total: int, message: str)
        logger: Logger instance for this enricher
    """
    
    def __init__(self, progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """Initialize base enricher.
        
        Args:
            progress_callback: Optional callback for progress updates
                              Called with (current, total, message)
        """
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._cancelled = False
    
    @abstractmethod
    def enrich_document(self, document: 'DocumentModel') -> EnrichmentResult:
        """Enrich a document model with additional information.
        
        This is the main enrichment method that subclasses must implement.
        
        Args:
            document: DocumentModel to enrich (modified in place)
        
        Returns:
            EnrichmentResult with statistics and status
        """
        pass
    
    @abstractmethod
    def validate_document(self, document: 'DocumentModel') -> tuple[bool, List[str]]:
        """Validate if document can be enriched.
        
        Args:
            document: DocumentModel to validate
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        pass
    
    @abstractmethod
    def get_enricher_name(self) -> str:
        """Get human-readable name of this enricher.
        
        Returns:
            Enricher name (e.g., "KEGG Stoichiometry Enricher")
        """
        pass
    
    def cancel(self):
        """Request cancellation of ongoing enrichment.
        
        Enrichers should check self._cancelled periodically and
        stop processing gracefully if True.
        """
        self._cancelled = True
        self.logger.info(f"{self.get_enricher_name()} cancellation requested")
    
    def is_cancelled(self) -> bool:
        """Check if enrichment has been cancelled.
        
        Returns:
            True if cancel() was called
        """
        return self._cancelled
    
    def report_progress(self, current: int, total: int, message: str = ""):
        """Report progress to callback if registered.
        
        Args:
            current: Current item being processed (0-based)
            total: Total items to process
            message: Optional progress message
        """
        if self.progress_callback:
            try:
                self.progress_callback(current, total, message)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
    
    def _create_success_result(self, message: str, **statistics) -> EnrichmentResult:
        """Helper to create success result with statistics.
        
        Args:
            message: Success message
            **statistics: Key-value pairs for statistics
        
        Returns:
            EnrichmentResult with success=True
        """
        result = EnrichmentResult(success=True, message=message)
        for key, value in statistics.items():
            result.add_statistic(key, value)
        return result
    
    def _create_failure_result(self, message: str, errors: List[str] = None) -> EnrichmentResult:
        """Helper to create failure result with errors.
        
        Args:
            message: Failure message
            errors: List of error messages
        
        Returns:
            EnrichmentResult with success=False
        """
        result = EnrichmentResult(success=False, message=message)
        if errors:
            for error in errors:
                result.add_error(error)
        return result
