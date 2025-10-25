#!/usr/bin/env python3
"""Project Pathway Manager.

This module provides pathway management functionality for Projects,
keeping the Project class clean by separating pathway operations.

Classes:
    ProjectPathwayManager: Manages pathways within a project
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from .pathway_document import PathwayDocument
from .enrichment_document import EnrichmentDocument


class ProjectPathwayManager:
    """Manages pathways within a project.
    
    This class handles all pathway-related operations for a Project,
    including adding, removing, finding, and file operations.
    
    Attributes:
        project: Reference to parent Project instance
        pathways: Dict mapping pathway_id -> PathwayDocument
    """
    
    def __init__(self, project):
        """Initialize the pathway manager.
        
        Args:
            project: Parent Project instance
        """
        self.project = project
        self.pathways: Dict[str, PathwayDocument] = {}
    
    def add_pathway(self, pathway_doc: PathwayDocument) -> None:
        """Register a pathway in the project.
        
        Args:
            pathway_doc: PathwayDocument to add
        """
        self.pathways[pathway_doc.id] = pathway_doc
        self.project.update_modified_date()
    
    def remove_pathway(self, pathway_id: str) -> bool:
        """Remove a pathway and its associated files.
        
        Args:
            pathway_id: UUID of pathway to remove
            
        Returns:
            True if removed, False if not found
        """
        if pathway_id not in self.pathways:
            return False
        
        pathway_doc = self.pathways[pathway_id]
        
        # Delete associated files
        pathways_dir = self.project.get_pathways_dir()
        
        # Delete raw file
        if pathway_doc.raw_file:
            raw_path = pathways_dir / pathway_doc.raw_file
            if raw_path.exists():
                raw_path.unlink()
        
        # Delete metadata file
        if pathway_doc.metadata_file:
            meta_path = pathways_dir / pathway_doc.metadata_file
            if meta_path.exists():
                meta_path.unlink()
        
        # Delete enrichment files
        for enrichment in pathway_doc.enrichments:
            if enrichment.data_file:
                enrich_path = pathways_dir / enrichment.data_file
                if enrich_path.exists():
                    enrich_path.unlink()
        
        # Remove from dict
        del self.pathways[pathway_id]
        self.project.update_modified_date()
        return True
    
    def get_pathway(self, pathway_id: str) -> Optional[PathwayDocument]:
        """Get a pathway by ID.
        
        Args:
            pathway_id: UUID of pathway
            
        Returns:
            PathwayDocument if found, None otherwise
        """
        return self.pathways.get(pathway_id)
    
    def find_pathway_by_model_id(self, model_id: str) -> Optional[PathwayDocument]:
        """Find the pathway that was converted to a specific model.
        
        Args:
            model_id: UUID of ModelDocument
            
        Returns:
            PathwayDocument if found, None otherwise
        """
        for pathway_doc in self.pathways.values():
            if pathway_doc.model_id == model_id:
                return pathway_doc
        return None
    
    def find_pathways_by_source(self, source_type: str) -> List[PathwayDocument]:
        """Find all pathways from a specific source.
        
        Args:
            source_type: "kegg" or "sbml"
            
        Returns:
            List of PathwayDocument instances
        """
        return [p for p in self.pathways.values() if p.source_type == source_type]
    
    def list_pathways(self) -> List[PathwayDocument]:
        """Get all pathways in the project.
        
        Returns:
            List of all PathwayDocument instances
        """
        return list(self.pathways.values())
    
    def get_pathway_count(self) -> int:
        """Get the total number of pathways.
        
        Returns:
            Number of pathways
        """
        return len(self.pathways)
    
    def get_converted_pathway_count(self) -> int:
        """Get the number of pathways that have been converted to models.
        
        Returns:
            Number of pathways with model_id set
        """
        return sum(1 for p in self.pathways.values() if p.is_converted())
    
    def save_pathway_file(self, filename: str, content: str) -> Path:
        """Save a pathway file to the pathways/ directory.
        
        Args:
            filename: Name of file to save
            content: File content (text)
            
        Returns:
            Path to saved file
        """
        pathways_dir = self.project.get_pathways_dir()
        pathways_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = pathways_dir / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def save_pathway_metadata(self, filename: str, metadata: Dict[str, Any]) -> Path:
        """Save pathway metadata as JSON.
        
        Args:
            filename: Name of metadata file (should end in .json)
            metadata: Metadata dictionary
            
        Returns:
            Path to saved file
        """
        pathways_dir = self.project.get_pathways_dir()
        pathways_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = pathways_dir / filename
        file_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        return file_path
    
    def save_enrichment_file(self, filename: str, data: Dict[str, Any]) -> Path:
        """Save enrichment data to the pathways/ directory.
        
        Args:
            filename: Name of enrichment file
            data: Enrichment data dictionary
            
        Returns:
            Path to saved file
        """
        pathways_dir = self.project.get_pathways_dir()
        pathways_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = pathways_dir / filename
        file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        return file_path
    
    def load_pathway_file(self, filename: str) -> Optional[str]:
        """Load a pathway file from the pathways/ directory.
        
        Args:
            filename: Name of file to load
            
        Returns:
            File content as string, or None if not found
        """
        pathways_dir = self.project.get_pathways_dir()
        file_path = pathways_dir / filename
        
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pathways to dictionary for serialization.
        
        Returns:
            Dictionary mapping pathway_id -> pathway_data
        """
        return {
            pathway_id: pathway_doc.to_dict()
            for pathway_id, pathway_doc in self.pathways.items()
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load pathways from dictionary.
        
        Args:
            data: Dictionary mapping pathway_id -> pathway_data
        """
        self.pathways.clear()
        
        for pathway_id, pathway_data in data.items():
            pathway_doc = PathwayDocument.from_dict(pathway_data)
            self.pathways[pathway_id] = pathway_doc
    
    def migrate_from_list(self, old_pathways: List[str]) -> None:
        """Migrate from old flat list format to new PathwayDocument format.
        
        Args:
            old_pathways: List of pathway file paths (old format)
        """
        for i, filepath in enumerate(old_pathways):
            # Create PathwayDocument from file path
            pathway_doc = PathwayDocument(
                name=Path(filepath).stem,
                source_type='unknown',
                source_id=Path(filepath).stem
            )
            pathway_doc.raw_file = filepath
            pathway_doc.tags = ['migrated']
            pathway_doc.notes = 'Migrated from v1 project format'
            
            self.pathways[pathway_doc.id] = pathway_doc
    
    def __len__(self) -> int:
        """Get number of pathways."""
        return len(self.pathways)
    
    def __contains__(self, pathway_id: str) -> bool:
        """Check if pathway exists."""
        return pathway_id in self.pathways
    
    def __iter__(self):
        """Iterate over pathway IDs."""
        return iter(self.pathways)
