#!/usr/bin/env python3
"""Enrichment Document Data Model.

This module defines the EnrichmentDocument class which represents enrichment
data from external sources (BRENDA, Reactome, etc.) applied to a pathway.

Classes:
    EnrichmentDocument: Represents enrichment data with metadata and metrics
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class EnrichmentDocument:
    """Represents enrichment data from an external source.
    
    An EnrichmentDocument tracks enrichment data (e.g., BRENDA kinetic parameters)
    applied to a pathway, including what was added, quality metrics, and provenance.
    
    Attributes:
        id: Unique identifier (UUID)
        type: Enrichment type ("kinetics", "structural", "functional")
        source: Source name ("brenda", "reactome", "sabio-rk", etc.)
        source_query: Query parameters used to fetch enrichment
        data_file: Relative path to enrichment data JSON file
        applied_date: ISO timestamp when enrichment was applied
        transitions_enriched: List of transition IDs that were enriched
        parameters_added: Dict of parameter types and counts
        confidence: Quality confidence ("high", "medium", "low")
        citations: List of citation IDs (e.g., PubMed IDs)
        notes: User notes about this enrichment
    """
    
    def __init__(self,
                 id: str = None,
                 type: str = "kinetics",
                 source: str = "brenda"):
        """Initialize an EnrichmentDocument.
        
        Args:
            id: UUID string, generated if None
            type: Enrichment type
            source: Source database/API name
        """
        self.id = id or str(uuid.uuid4())
        self.type = type
        self.source = source
        
        # Query parameters
        self.source_query = {}
        
        # File path (relative to project pathways/ directory)
        self.data_file = ""
        
        # Timestamp
        self.applied_date = datetime.now().isoformat()
        
        # Enrichment results
        self.transitions_enriched = []
        self.parameters_added = {}
        
        # Quality metrics
        self.confidence = "medium"
        self.citations = []
        
        # User notes
        self.notes = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON
        """
        return {
            'id': self.id,
            'type': self.type,
            'source': self.source,
            'source_query': self.source_query,
            'data_file': self.data_file,
            'applied_date': self.applied_date,
            'transitions_enriched': self.transitions_enriched,
            'parameters_added': self.parameters_added,
            'confidence': self.confidence,
            'citations': self.citations,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnrichmentDocument':
        """Create EnrichmentDocument from dictionary.
        
        Args:
            data: Dictionary from JSON deserialization
            
        Returns:
            Reconstructed EnrichmentDocument instance
        """
        doc = cls(
            id=data.get('id'),
            type=data.get('type', 'kinetics'),
            source=data.get('source', 'brenda')
        )
        
        # Restore query parameters
        doc.source_query = data.get('source_query', {})
        
        # Restore file path
        doc.data_file = data.get('data_file', '')
        
        # Restore timestamp
        doc.applied_date = data.get('applied_date', doc.applied_date)
        
        # Restore results
        doc.transitions_enriched = data.get('transitions_enriched', [])
        doc.parameters_added = data.get('parameters_added', {})
        
        # Restore quality metrics
        doc.confidence = data.get('confidence', 'medium')
        doc.citations = data.get('citations', [])
        
        # Restore notes
        doc.notes = data.get('notes', '')
        
        return doc
    
    def add_transition(self, transition_id: str):
        """Add a transition ID to the enriched list.
        
        Args:
            transition_id: ID of transition that was enriched
        """
        if transition_id not in self.transitions_enriched:
            self.transitions_enriched.append(transition_id)
    
    def add_parameter(self, param_type: str, count: int = 1):
        """Add or increment a parameter count.
        
        Args:
            param_type: Parameter type (e.g., "km_values", "kcat_values")
            count: Number to add (default: 1)
        """
        if param_type in self.parameters_added:
            self.parameters_added[param_type] += count
        else:
            self.parameters_added[param_type] = count
    
    def add_citation(self, citation_id: str):
        """Add a citation ID.
        
        Args:
            citation_id: Citation identifier (e.g., "PMID:12345678")
        """
        if citation_id not in self.citations:
            self.citations.append(citation_id)
    
    def get_total_parameters(self) -> int:
        """Get total number of parameters added.
        
        Returns:
            Sum of all parameter counts
        """
        return sum(self.parameters_added.values())
    
    def get_transition_count(self) -> int:
        """Get number of transitions enriched.
        
        Returns:
            Number of unique transitions
        """
        return len(self.transitions_enriched)
    
    def get_citation_count(self) -> int:
        """Get number of citations.
        
        Returns:
            Number of unique citations
        """
        return len(self.citations)
    
    def set_confidence(self, confidence: str):
        """Set the confidence level.
        
        Args:
            confidence: "high", "medium", or "low"
        """
        if confidence in ["high", "medium", "low"]:
            self.confidence = confidence
        else:
            raise ValueError(f"Invalid confidence level: {confidence}")
    
    def is_high_confidence(self) -> bool:
        """Check if this enrichment has high confidence.
        
        Returns:
            True if confidence is "high"
        """
        return self.confidence == "high"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"EnrichmentDocument(id={self.id[:8]}, source={self.source}, "
                f"type={self.type}, transitions={len(self.transitions_enriched)}, "
                f"confidence={self.confidence})")
