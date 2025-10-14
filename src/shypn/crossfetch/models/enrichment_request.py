"""
Enrichment Request Data Model

Represents a request to enrich pathway data from external sources.

Author: Shypn Development Team
Date: October 2025
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum


class DataType(Enum):
    """Types of data that can be enriched."""
    COORDINATES = "coordinates"
    CONCENTRATIONS = "concentrations"
    KINETICS = "kinetics"
    ANNOTATIONS = "annotations"
    STRUCTURES = "structures"
    INTERACTIONS = "interactions"
    PATHWAYS = "pathways"
    ALL = "all"


class EnrichmentPriority(Enum):
    """Priority level for enrichment requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EnrichmentRequest:
    """Request to enrich pathway data.
    
    Specifies what data to enrich, from which sources, and with what priorities.
    """
    
    # What to enrich
    pathway_id: str
    data_types: List[DataType]
    
    # Target objects
    species_ids: Optional[List[str]] = None
    reaction_ids: Optional[List[str]] = None
    
    # Source preferences
    preferred_sources: Optional[List[str]] = None
    excluded_sources: Optional[List[str]] = None
    
    # Quality requirements
    min_quality_score: float = 0.5
    require_validation: bool = False
    
    # Priority and limits
    priority: EnrichmentPriority = EnrichmentPriority.NORMAL
    max_sources_per_field: int = 3
    timeout_seconds: float = 30.0
    
    # Options
    allow_partial_results: bool = True
    cache_results: bool = True
    update_existing: bool = False
    
    # Additional parameters
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def get_data_types(self) -> Set[DataType]:
        """Get set of data types to enrich."""
        if DataType.ALL in self.data_types:
            return {
                DataType.COORDINATES,
                DataType.CONCENTRATIONS,
                DataType.KINETICS,
                DataType.ANNOTATIONS,
                DataType.STRUCTURES
            }
        return set(self.data_types)
    
    def should_enrich_type(self, data_type: DataType) -> bool:
        """Check if this data type should be enriched."""
        return data_type in self.get_data_types()
    
    def is_source_allowed(self, source_name: str) -> bool:
        """Check if source is allowed for this request."""
        if self.excluded_sources and source_name in self.excluded_sources:
            return False
        if self.preferred_sources and source_name not in self.preferred_sources:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pathway_id": self.pathway_id,
            "data_types": [dt.value for dt in self.data_types],
            "species_ids": self.species_ids,
            "reaction_ids": self.reaction_ids,
            "preferred_sources": self.preferred_sources,
            "excluded_sources": self.excluded_sources,
            "min_quality_score": self.min_quality_score,
            "require_validation": self.require_validation,
            "priority": self.priority.value,
            "max_sources_per_field": self.max_sources_per_field,
            "timeout_seconds": self.timeout_seconds,
            "allow_partial_results": self.allow_partial_results,
            "cache_results": self.cache_results,
            "update_existing": self.update_existing,
            "extra_params": self.extra_params
        }
    
    @classmethod
    def create_simple(cls,
                     pathway_id: str,
                     data_types: Optional[List[str]] = None) -> 'EnrichmentRequest':
        """Create a simple enrichment request with defaults.
        
        Args:
            pathway_id: Pathway identifier
            data_types: List of data type strings (default: all)
            
        Returns:
            EnrichmentRequest instance
        """
        if data_types is None:
            dt_list = [DataType.ALL]
        else:
            dt_list = [DataType(dt) for dt in data_types]
        
        return cls(
            pathway_id=pathway_id,
            data_types=dt_list
        )
    
    def __repr__(self) -> str:
        """String representation."""
        data_types_str = ", ".join(dt.value for dt in self.data_types)
        return (
            f"EnrichmentRequest(pathway={self.pathway_id}, "
            f"types=[{data_types_str}], "
            f"priority={self.priority.value})"
        )
