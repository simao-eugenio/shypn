"""
Metadata Manager Factory

Factory for creating appropriate metadata manager instances based on file type
or user preference.

Supports:
- JSON (default)
- XML (for SBML compatibility)
- SQLite (for large projects)
- Auto-detection based on file extension

Author: Shypn Development Team
Date: October 2025
"""

from typing import Optional, Type, Dict, Any
from pathlib import Path
from enum import Enum
import logging

from .base_metadata_manager import BaseMetadataManager
from .json_metadata_manager import JSONMetadataManager


class MetadataFormat(Enum):
    """Supported metadata formats."""
    JSON = "json"
    XML = "xml"
    SQLITE = "sqlite"
    AUTO = "auto"


class MetadataManagerFactory:
    """Factory for creating metadata managers.
    
    This factory provides a central place to create metadata managers
    with appropriate configuration based on format, file type, or user preference.
    
    Features:
    - Auto-detection of format from file extension
    - Support for multiple metadata formats
    - Configuration management
    - Manager class registration
    """
    
    # Registry of manager classes by format
    _managers: Dict[MetadataFormat, Type[BaseMetadataManager]] = {
        MetadataFormat.JSON: JSONMetadataManager,
        # XML and SQLite managers can be added here when implemented
        # MetadataFormat.XML: XMLMetadataManager,
        # MetadataFormat.SQLITE: SQLiteMetadataManager,
    }
    
    # Default format
    _default_format = MetadataFormat.JSON
    
    # Format preferences by file extension
    _extension_preferences = {
        ".shy": MetadataFormat.JSON,      # Primary Shypn file extension
        ".shypn": MetadataFormat.JSON,    # Legacy support
        ".sbml": MetadataFormat.XML,
        ".xml": MetadataFormat.XML,
        # Add more as needed
    }
    
    def __init__(self):
        """Initialize factory."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @classmethod
    def create(cls,
              pathway_file: Path,
              format: Optional[MetadataFormat] = None,
              **kwargs) -> BaseMetadataManager:
        """Create metadata manager for pathway file.
        
        Args:
            pathway_file: Path to pathway file
            format: Optional format (auto-detected if not specified)
            **kwargs: Additional arguments for manager constructor
            
        Returns:
            Metadata manager instance
            
        Raises:
            ValueError: If format not supported
        """
        pathway_file = Path(pathway_file)
        
        # Determine format
        if format is None or format == MetadataFormat.AUTO:
            format = cls._detect_format(pathway_file)
        
        # Get manager class
        manager_class = cls._managers.get(format)
        
        if manager_class is None:
            raise ValueError(f"Unsupported metadata format: {format}")
        
        # Create manager instance
        return manager_class(pathway_file, **kwargs)
    
    @classmethod
    def _detect_format(cls, pathway_file: Path) -> MetadataFormat:
        """Auto-detect format from file extension.
        
        Args:
            pathway_file: Path to pathway file
            
        Returns:
            Detected format (defaults to JSON)
        """
        extension = pathway_file.suffix.lower()
        return cls._extension_preferences.get(extension, cls._default_format)
    
    @classmethod
    def register_manager(cls,
                        format: MetadataFormat,
                        manager_class: Type[BaseMetadataManager]):
        """Register a new metadata manager class.
        
        Args:
            format: Metadata format
            manager_class: Manager class to register
        """
        if not issubclass(manager_class, BaseMetadataManager):
            raise ValueError(f"{manager_class} must inherit from BaseMetadataManager")
        
        cls._managers[format] = manager_class
    
    @classmethod
    def set_default_format(cls, format: MetadataFormat):
        """Set default metadata format.
        
        Args:
            format: Default format
        """
        cls._default_format = format
    
    @classmethod
    def get_default_format(cls) -> MetadataFormat:
        """Get current default format.
        
        Returns:
            Default format
        """
        return cls._default_format
    
    @classmethod
    def set_extension_preference(cls, extension: str, format: MetadataFormat):
        """Set format preference for file extension.
        
        Args:
            extension: File extension (e.g., '.shypn')
            format: Preferred format
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        cls._extension_preferences[extension] = format
    
    @classmethod
    def get_supported_formats(cls) -> list[MetadataFormat]:
        """Get list of supported formats.
        
        Returns:
            List of supported formats
        """
        return list(cls._managers.keys())
    
    @classmethod
    def is_format_supported(cls, format: MetadataFormat) -> bool:
        """Check if format is supported.
        
        Args:
            format: Format to check
            
        Returns:
            True if supported
        """
        return format in cls._managers


# Convenience functions

def create_metadata_manager(pathway_file: Path,
                           format: Optional[MetadataFormat] = None,
                           **kwargs) -> BaseMetadataManager:
    """Create metadata manager (convenience function).
    
    Args:
        pathway_file: Path to pathway file
        format: Optional format (auto-detected if not specified)
        **kwargs: Additional arguments for manager constructor
        
    Returns:
        Metadata manager instance
    """
    factory = MetadataManagerFactory()
    return factory.create(pathway_file, format, **kwargs)


def create_json_manager(pathway_file: Path, **kwargs) -> JSONMetadataManager:
    """Create JSON metadata manager (convenience function).
    
    Args:
        pathway_file: Path to pathway file
        **kwargs: Additional arguments for manager constructor
        
    Returns:
        JSON metadata manager instance
    """
    return JSONMetadataManager(pathway_file, **kwargs)


# Example usage
if __name__ == "__main__":
    # Auto-detect format from file extension
    manager = MetadataManagerFactory.create(Path("project/models/glycolysis.shypn"))
    
    # Explicit format
    manager = MetadataManagerFactory.create(
        Path("project/models/glycolysis.shypn"),
        format=MetadataFormat.JSON
    )
    
    # Check supported formats
    formats = MetadataManagerFactory.get_supported_formats()
