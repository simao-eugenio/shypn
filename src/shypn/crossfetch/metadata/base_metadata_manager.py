"""
Base Metadata Manager

Abstract base class for managing metadata files that track cross-fetch enrichment
information alongside pathway files.

Architecture:
- Each pathway file (.shypn) has a corresponding metadata file (.shypn.meta.json)
- Metadata files are automatically created/updated/deleted with pathway files
- All file operations are reflected in metadata (gemini reflection)
- Metadata tracks: sources, quality scores, enrichment history, timestamps

Author: Shypn Development Team
Date: October 2025
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import logging


class BaseMetadataManager(ABC):
    """Abstract base class for metadata file management.
    
    This class defines the interface for managing metadata files that track
    enrichment information alongside pathway files. Each pathway file has a
    corresponding metadata file that logs all cross-fetch operations.
    
    Attributes:
        pathway_file: Path to the pathway file
        metadata_file: Path to the metadata file (auto-generated)
        logger: Logger instance
    """
    
    METADATA_EXTENSION = ".meta.json"
    
    def __init__(self, pathway_file: Path):
        """Initialize metadata manager for a pathway file.
        
        Args:
            pathway_file: Path to the pathway file (e.g., "model.shypn")
        """
        self.pathway_file = Path(pathway_file)
        self.metadata_file = self._get_metadata_path(self.pathway_file)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure metadata directory exists
        self._ensure_metadata_directory()
    
    def _get_metadata_path(self, pathway_file: Path) -> Path:
        """Get metadata file path for a pathway file.
        
        The metadata file is stored in a 'metadata' subdirectory within
        the project structure.
        
        Args:
            pathway_file: Path to pathway file
            
        Returns:
            Path to metadata file
            
        Example:
            pathway: /project/models/glycolysis.shypn
            metadata: /project/metadata/glycolysis.shypn.meta.json
        """
        project_root = self._find_project_root(pathway_file)
        metadata_dir = project_root / "metadata"
        
        # Create metadata filename
        relative_path = pathway_file.relative_to(project_root)
        metadata_name = str(relative_path).replace("/", "_") + self.METADATA_EXTENSION
        
        return metadata_dir / metadata_name
    
    def _find_project_root(self, file_path: Path) -> Path:
        """Find project root directory.
        
        Looks for project markers (.shypn_project, .git, etc.)
        
        Args:
            file_path: File within project
            
        Returns:
            Path to project root
        """
        current = file_path.parent if file_path.is_file() else file_path
        
        # Look for project markers
        while current != current.parent:
            if (current / ".shypn_project").exists():
                return current
            if (current / ".git").exists():
                return current
            current = current.parent
        
        # Fallback to file's parent directory
        return file_path.parent if file_path.is_file() else file_path
    
    def _ensure_metadata_directory(self):
        """Ensure metadata directory exists."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    # ===== Abstract Methods (must be implemented by subclasses) =====
    
    @abstractmethod
    def create(self, initial_data: Optional[Dict[str, Any]] = None) -> bool:
        """Create new metadata file.
        
        Args:
            initial_data: Optional initial metadata
            
        Returns:
            True if created successfully
        """
        pass
    
    @abstractmethod
    def read(self) -> Optional[Dict[str, Any]]:
        """Read metadata from file.
        
        Returns:
            Metadata dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def update(self, data: Dict[str, Any]) -> bool:
        """Update metadata file.
        
        Args:
            data: Metadata to update/merge
            
        Returns:
            True if updated successfully
        """
        pass
    
    @abstractmethod
    def delete(self) -> bool:
        """Delete metadata file.
        
        Returns:
            True if deleted successfully
        """
        pass
    
    # ===== Concrete Methods (shared implementation) =====
    
    def exists(self) -> bool:
        """Check if metadata file exists.
        
        Returns:
            True if metadata file exists
        """
        return self.metadata_file.exists()
    
    def get_path(self) -> Path:
        """Get metadata file path.
        
        Returns:
            Path to metadata file
        """
        return self.metadata_file
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Log file operation to metadata.
        
        This is called automatically when pathway file operations occur.
        
        Args:
            operation: Operation type ("create", "save", "load", "delete", "rename")
            details: Optional operation details
        """
        metadata = self.read() or self._get_default_metadata()
        
        # Add to operation history
        if "operations" not in metadata:
            metadata["operations"] = []
        
        metadata["operations"].append({
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
        
        # Update last modified
        metadata["last_modified"] = datetime.now().isoformat()
        
        self.update(metadata)
        self.logger.info(f"Logged operation: {operation} for {self.pathway_file.name}")
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata structure.
        
        Returns:
            Default metadata dictionary
        """
        return {
            "pathway_file": str(self.pathway_file.name),
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "version": "1.0",
            "enrichments": [],
            "operations": [],
            "statistics": {
                "total_enrichments": 0,
                "sources_used": [],
                "quality_scores": {}
            }
        }
    
    def add_enrichment_record(self, 
                            data_type: str,
                            source: str,
                            quality_score: float,
                            fields_enriched: List[str],
                            details: Optional[Dict[str, Any]] = None):
        """Add enrichment record to metadata.
        
        Args:
            data_type: Type of data enriched ("coordinates", "concentrations", etc.)
            source: Data source ("KEGG", "BioModels", etc.)
            quality_score: Quality score (0.0-1.0)
            fields_enriched: List of fields that were enriched
            details: Optional additional details
        """
        metadata = self.read() or self._get_default_metadata()
        
        enrichment_record = {
            "data_type": data_type,
            "source": source,
            "quality_score": quality_score,
            "fields_enriched": fields_enriched,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        metadata["enrichments"].append(enrichment_record)
        
        # Update statistics
        metadata["statistics"]["total_enrichments"] += 1
        if source not in metadata["statistics"]["sources_used"]:
            metadata["statistics"]["sources_used"].append(source)
        metadata["statistics"]["quality_scores"][data_type] = quality_score
        
        self.update(metadata)
        self.logger.info(f"Added enrichment: {data_type} from {source} (quality={quality_score:.2f})")
    
    def get_enrichment_history(self, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get enrichment history.
        
        Args:
            data_type: Optional filter by data type
            
        Returns:
            List of enrichment records
        """
        metadata = self.read()
        if not metadata:
            return []
        
        enrichments = metadata.get("enrichments", [])
        
        if data_type:
            enrichments = [e for e in enrichments if e.get("data_type") == data_type]
        
        return enrichments
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enrichment statistics.
        
        Returns:
            Statistics dictionary
        """
        metadata = self.read()
        if not metadata:
            return {}
        
        return metadata.get("statistics", {})
    
    def get_sources_used(self) -> List[str]:
        """Get list of sources used for enrichment.
        
        Returns:
            List of source names
        """
        stats = self.get_statistics()
        return stats.get("sources_used", [])
    
    def get_quality_report(self) -> Dict[str, float]:
        """Get quality scores for each data type.
        
        Returns:
            Dictionary {data_type: quality_score}
        """
        stats = self.get_statistics()
        return stats.get("quality_scores", {})
    
    def get_path(self) -> Path:
        """Get the metadata file path.
        
        Returns:
            Path to metadata file
        """
        return self.metadata_file
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(pathway={self.pathway_file.name}, metadata={self.metadata_file.name})"
