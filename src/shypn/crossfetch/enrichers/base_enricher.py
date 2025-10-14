"""
Base Enricher Class

Abstract base class for all data enrichers.

Enrichers apply fetched data to pathway objects (places, transitions, arcs).
They validate data before application and support rollback.

Author: Shypn Development Team
Date: October 2025
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from ..models import FetchResult


@dataclass
class EnrichmentChange:
    """Record of a single enrichment change for rollback support."""
    
    object_id: str
    object_type: str  # "place", "transition", "arc"
    property_name: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    
    def rollback_dict(self) -> Dict[str, Any]:
        """Get dictionary for rollback operation."""
        return {
            "object_id": self.object_id,
            "property": self.property_name,
            "value": self.old_value
        }


@dataclass
class EnrichmentResult:
    """Result of an enrichment operation."""
    
    success: bool
    objects_modified: int
    changes: List[EnrichmentChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    enricher_name: str = ""
    source_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_change(self, change: EnrichmentChange) -> None:
        """Add a change record."""
        self.changes.append(change)
        self.objects_modified = len(set(c.object_id for c in self.changes))
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "objects_modified": self.objects_modified,
            "changes_count": len(self.changes),
            "errors": self.errors,
            "warnings": self.warnings,
            "enricher": self.enricher_name,
            "source": self.source_name,
            "timestamp": self.timestamp.isoformat()
        }


class EnricherBase(ABC):
    """
    Abstract base class for data enrichers.
    
    Enrichers take fetched data and apply it to pathway objects.
    They support validation, conflict resolution, and rollback.
    
    Subclasses must implement:
    - apply(): Apply enrichment data to pathway
    - validate(): Validate data before application
    - can_enrich(): Check if enricher can handle this data type
    """
    
    def __init__(self, enricher_name: str):
        """
        Initialize enricher.
        
        Args:
            enricher_name: Name of this enricher
        """
        self.enricher_name = enricher_name
        self._change_history: List[EnrichmentChange] = []
    
    @abstractmethod
    def apply(
        self,
        pathway: Any,
        fetch_result: FetchResult,
        **options
    ) -> EnrichmentResult:
        """
        Apply enrichment data to pathway.
        
        Args:
            pathway: Pathway object to enrich (or pathway document)
            fetch_result: Result from data fetcher
            **options: Enricher-specific options
            
        Returns:
            EnrichmentResult with details of changes made
        """
        pass
    
    @abstractmethod
    def validate(
        self,
        pathway: Any,
        fetch_result: FetchResult
    ) -> tuple[bool, List[str]]:
        """
        Validate that enrichment data can be applied.
        
        Args:
            pathway: Pathway object to validate against
            fetch_result: Result from data fetcher
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def can_enrich(self, data_type: str) -> bool:
        """
        Check if this enricher can handle the given data type.
        
        Args:
            data_type: Type of data (e.g., "concentrations", "kinetics")
            
        Returns:
            True if this enricher can handle this data type
        """
        pass
    
    def get_supported_data_types(self) -> Set[str]:
        """
        Get set of data types this enricher supports.
        
        Returns:
            Set of supported data type strings
        """
        return set()
    
    def rollback(
        self,
        pathway: Any,
        changes: Optional[List[EnrichmentChange]] = None
    ) -> EnrichmentResult:
        """
        Rollback enrichment changes.
        
        Args:
            pathway: Pathway object to rollback
            changes: Specific changes to rollback (None = all recent changes)
            
        Returns:
            EnrichmentResult with rollback details
        """
        if changes is None:
            changes = self._change_history.copy()
        
        result = EnrichmentResult(
            success=True,
            objects_modified=0,
            enricher_name=self.enricher_name,
            source_name="rollback"
        )
        
        # Rollback in reverse order
        for change in reversed(changes):
            try:
                self._apply_change(pathway, change.rollback_dict())
                result.add_change(change)
            except Exception as e:
                result.success = False
                result.add_error(f"Failed to rollback {change.object_id}: {e}")
        
        return result
    
    def _apply_change(self, pathway: Any, change_dict: Dict[str, Any]) -> None:
        """
        Apply a single change to pathway.
        
        Args:
            pathway: Pathway object
            change_dict: Dictionary describing the change
        """
        # Default implementation - subclasses should override
        pass
    
    def _record_change(
        self,
        object_id: str,
        object_type: str,
        property_name: str,
        old_value: Any,
        new_value: Any,
        source: str = ""
    ) -> EnrichmentChange:
        """
        Record a change for potential rollback.
        
        Args:
            object_id: ID of modified object
            object_type: Type of object ("place", "transition", "arc")
            property_name: Name of property changed
            old_value: Previous value
            new_value: New value
            source: Source of the enrichment data
            
        Returns:
            EnrichmentChange record
        """
        change = EnrichmentChange(
            object_id=object_id,
            object_type=object_type,
            property_name=property_name,
            old_value=old_value,
            new_value=new_value,
            source=source
        )
        self._change_history.append(change)
        return change
    
    def clear_history(self) -> None:
        """Clear change history."""
        self._change_history.clear()
    
    def get_history(self) -> List[EnrichmentChange]:
        """Get change history."""
        return self._change_history.copy()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.enricher_name})"
