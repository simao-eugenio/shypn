"""
Metadata Management Package

Automatic metadata tracking for pathway files implementing the "gemini" pattern.
Every file operation on a pathway file is reflected in its metadata file.

Features:
- Automatic metadata creation/update/deletion
- Operation logging (create, save, load, delete, rename, copy)
- Enrichment tracking (source, quality, timestamp)
- Multiple formats (JSON, XML, SQLite)
- Factory pattern for flexible instantiation

Public API:
-----------

Metadata Managers:
    BaseMetadataManager: Abstract base class
    JSONMetadataManager: JSON implementation (default)

Factory:
    MetadataManagerFactory: Creates appropriate manager
    create_metadata_manager(): Convenience function
    create_json_manager(): Create JSON manager

Tracker:
    FileOperationsTracker: Tracks file operations

Enums:
    MetadataFormat: Supported formats (JSON, XML, SQLITE, AUTO)

Usage Example:
--------------
    from shypn.crossfetch.metadata import (
        create_metadata_manager,
        FileOperationsTracker
    )
    
    # Create metadata manager
    manager = create_metadata_manager(Path("glycolysis.shypn"))
    
    # Track file operations
    tracker = FileOperationsTracker()
    tracker.create_file(Path("glycolysis.shypn"))
    tracker.save_file(Path("glycolysis.shypn"), user="simao")
    
    # Add enrichment record
    manager.add_enrichment_record(
        data_type="coordinates",
        source="KEGG",
        quality_score=0.85,
        fields_enriched=["species[0].x", "species[0].y"]
    )
    
    # Get enrichment history
    history = manager.get_enrichment_history()
    
    # Get statistics
    stats = manager.get_statistics()

Author: Shypn Development Team
Date: October 2025
"""

from .base_metadata_manager import BaseMetadataManager
from .json_metadata_manager import JSONMetadataManager
from .metadata_manager_factory import (
    MetadataManagerFactory,
    MetadataFormat,
    create_metadata_manager,
    create_json_manager
)
from .file_operations_tracker import FileOperationsTracker


__all__ = [
    # Base classes
    "BaseMetadataManager",
    "JSONMetadataManager",
    
    # Factory
    "MetadataManagerFactory",
    "MetadataFormat",
    "create_metadata_manager",
    "create_json_manager",
    
    # Tracker
    "FileOperationsTracker",
]


__version__ = "1.0.0"
__author__ = "Shypn Development Team"
