#!/usr/bin/env python3
"""Pathway Document Data Model.

This module defines the PathwayDocument class which represents an external
pathway (KEGG/SBML) with full metadata, provenance, and enrichment tracking.

Classes:
    PathwayDocument: Represents an imported pathway with metadata and enrichments
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class PathwayDocument:
    """Represents an external pathway with metadata and enrichments.
    
    A PathwayDocument is the source data (KEGG/SBML file) that was imported,
    along with all associated enrichments (BRENDA, etc.) and the link to the
    converted model on the canvas.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Display name (e.g., "Glycolysis / Gluconeogenesis")
        source_type: Source type ("kegg", "sbml")
        source_id: Source identifier (e.g., "hsa00010" for KEGG, filename for SBML)
        source_organism: Organism name (e.g., "Homo sapiens")
        raw_file: Relative path to original file in pathways/ directory
        metadata_file: Relative path to metadata JSON file
        imported_date: ISO timestamp of import
        last_modified: ISO timestamp of last modification
        enrichments: List of EnrichmentDocument instances
        model_id: UUID of linked ModelDocument (if converted)
        tags: User-defined tags
        notes: User notes
    """
    
    def __init__(self, 
                 id: str = None,
                 name: str = "Untitled Pathway",
                 source_type: str = "kegg",
                 source_id: str = "",
                 source_organism: str = ""):
        """Initialize a PathwayDocument.
        
        Args:
            id: UUID string, generated if None
            name: Pathway display name
            source_type: "kegg" or "sbml"
            source_id: KEGG pathway ID or SBML filename
            source_organism: Organism name
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.source_type = source_type
        self.source_id = source_id
        self.source_organism = source_organism
        
        # File paths (relative to project pathways/ directory)
        self.raw_file = ""
        self.metadata_file = ""
        
        # Timestamps
        self.imported_date = datetime.now().isoformat()
        self.last_modified = self.imported_date
        
        # Enrichments (will contain EnrichmentDocument instances)
        self.enrichments = []
        
        # Link to converted model
        self.model_id = None
        
        # User annotations
        self.tags = []
        self.notes = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON
        """
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_organism': self.source_organism,
            'raw_file': self.raw_file,
            'metadata_file': self.metadata_file,
            'imported_date': self.imported_date,
            'last_modified': self.last_modified,
            'enrichments': [e.to_dict() for e in self.enrichments],
            'model_id': self.model_id,
            'tags': self.tags,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathwayDocument':
        """Create PathwayDocument from dictionary.
        
        Args:
            data: Dictionary from JSON deserialization
            
        Returns:
            Reconstructed PathwayDocument instance
        """
        # Import here to avoid circular dependency
        from .enrichment_document import EnrichmentDocument
        
        doc = cls(
            id=data.get('id'),
            name=data.get('name', 'Untitled Pathway'),
            source_type=data.get('source_type', 'kegg'),
            source_id=data.get('source_id', ''),
            source_organism=data.get('source_organism', '')
        )
        
        # Restore file paths
        doc.raw_file = data.get('raw_file', '')
        doc.metadata_file = data.get('metadata_file', '')
        
        # Restore timestamps
        doc.imported_date = data.get('imported_date', doc.imported_date)
        doc.last_modified = data.get('last_modified', doc.last_modified)
        
        # Restore enrichments
        enrichments_data = data.get('enrichments', [])
        doc.enrichments = [EnrichmentDocument.from_dict(e) for e in enrichments_data]
        
        # Restore link to model
        doc.model_id = data.get('model_id')
        
        # Restore annotations
        doc.tags = data.get('tags', [])
        doc.notes = data.get('notes', '')
        
        return doc
    
    def update_modified_date(self):
        """Update the last modified timestamp to now."""
        self.last_modified = datetime.now().isoformat()
    
    def add_enrichment(self, enrichment: 'EnrichmentDocument'):
        """Add an enrichment to this pathway.
        
        Args:
            enrichment: EnrichmentDocument instance to add
        """
        self.enrichments.append(enrichment)
        self.update_modified_date()
    
    def remove_enrichment(self, enrichment_id: str) -> bool:
        """Remove an enrichment by ID.
        
        Args:
            enrichment_id: UUID of enrichment to remove
            
        Returns:
            True if removed, False if not found
        """
        initial_len = len(self.enrichments)
        self.enrichments = [e for e in self.enrichments if e.id != enrichment_id]
        
        if len(self.enrichments) < initial_len:
            self.update_modified_date()
            return True
        return False
    
    def get_enrichment(self, enrichment_id: str) -> Optional['EnrichmentDocument']:
        """Get an enrichment by ID.
        
        Args:
            enrichment_id: UUID of enrichment
            
        Returns:
            EnrichmentDocument if found, None otherwise
        """
        for enrichment in self.enrichments:
            if enrichment.id == enrichment_id:
                return enrichment
        return None
    
    def link_to_model(self, model_id: str):
        """Link this pathway to a converted model.
        
        Args:
            model_id: UUID of the ModelDocument
        """
        self.model_id = model_id
        self.update_modified_date()
    
    def unlink_from_model(self):
        """Remove link to converted model."""
        self.model_id = None
        self.update_modified_date()
    
    def is_converted(self) -> bool:
        """Check if this pathway has been converted to a model.
        
        Returns:
            True if linked to a model, False otherwise
        """
        return self.model_id is not None
    
    def has_enrichments(self) -> bool:
        """Check if this pathway has any enrichments.
        
        Returns:
            True if has enrichments, False otherwise
        """
        return len(self.enrichments) > 0
    
    def get_enrichment_count(self) -> int:
        """Get the number of enrichments.
        
        Returns:
            Number of enrichments
        """
        return len(self.enrichments)
    
    def get_enrichments_by_source(self, source: str) -> List['EnrichmentDocument']:
        """Get all enrichments from a specific source.
        
        Args:
            source: Source name (e.g., "brenda", "reactome")
            
        Returns:
            List of EnrichmentDocument instances from that source
        """
        return [e for e in self.enrichments if e.source == source]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"PathwayDocument(id={self.id[:8]}, name={self.name}, "
                f"source={self.source_type}:{self.source_id}, "
                f"enrichments={len(self.enrichments)})")
