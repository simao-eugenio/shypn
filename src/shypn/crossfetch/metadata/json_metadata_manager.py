"""
JSON Metadata Manager

Concrete implementation of metadata manager using JSON format.
Stores enrichment information in .meta.json files alongside pathway files.

Author: Shypn Development Team
Date: October 2025
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base_metadata_manager import BaseMetadataManager


class JSONMetadataManager(BaseMetadataManager):
    """JSON-based metadata manager.
    
    Stores metadata in JSON format for easy reading and version control.
    Format: pathway_file.shypn -> metadata/pathway_file.shypn.meta.json
    
    Features:
    - Human-readable JSON format
    - Pretty-printed for version control
    - Automatic backup on updates
    - Atomic writes (write to temp, then rename)
    """
    
    def __init__(self, pathway_file: Path, pretty_print: bool = True, indent: int = 2):
        """Initialize JSON metadata manager.
        
        Args:
            pathway_file: Path to pathway file
            pretty_print: Pretty-print JSON (default: True)
            indent: JSON indentation spaces (default: 2)
        """
        super().__init__(pathway_file)
        self.pretty_print = pretty_print
        self.indent = indent if pretty_print else None
    
    def create(self, initial_data: Optional[Dict[str, Any]] = None) -> bool:
        """Create new metadata file.
        
        Args:
            initial_data: Optional initial metadata (merged with defaults)
            
        Returns:
            True if created successfully
        """
        try:
            # Get default structure
            metadata = self._get_default_metadata()
            
            # Merge with initial data if provided
            if initial_data:
                metadata.update(initial_data)
            
            # Write to file
            self._write_json(metadata)
            
            self.logger.info(f"Created metadata file: {self.metadata_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to create metadata file: {e}")
            return False
    
    def read(self) -> Optional[Dict[str, Any]]:
        """Read metadata from JSON file.
        
        Returns:
            Metadata dictionary or None if not found/error
        """
        try:
            if not self.metadata_file.exists():
                self.logger.debug(f"Metadata file not found: {self.metadata_file}")
                return None
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return metadata
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in metadata file: {e}")
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to read metadata file: {e}")
            return None
    
    def update(self, data: Dict[str, Any]) -> bool:
        """Update metadata file (merge with existing data).
        
        Args:
            data: Metadata to update/merge
            
        Returns:
            True if updated successfully
        """
        try:
            # Read existing metadata
            existing = self.read()
            
            # If no existing metadata, create new
            if existing is None:
                return self.create(data)
            
            # Merge data (deep merge for nested dicts)
            merged = self._merge_metadata(existing, data)
            
            # Backup existing file
            self._backup_metadata()
            
            # Write updated metadata
            self._write_json(merged)
            
            self.logger.debug(f"Updated metadata file: {self.metadata_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to update metadata file: {e}")
            return False
    
    def delete(self) -> bool:
        """Delete metadata file.
        
        Returns:
            True if deleted successfully
        """
        try:
            if not self.metadata_file.exists():
                self.logger.debug(f"Metadata file does not exist: {self.metadata_file}")
                return True
            
            # Backup before delete
            self._backup_metadata()
            
            # Delete file
            self.metadata_file.unlink()
            
            self.logger.info(f"Deleted metadata file: {self.metadata_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete metadata file: {e}")
            return False
    
    def _write_json(self, data: Dict[str, Any]):
        """Write JSON data to file (atomic write).
        
        Args:
            data: Data to write
        """
        # Atomic write: write to temp file, then rename
        temp_file = self.metadata_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=self.indent, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.metadata_file)
        
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _merge_metadata(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge metadata dictionaries.
        
        Args:
            existing: Existing metadata
            new: New metadata to merge
            
        Returns:
            Merged metadata
        """
        merged = existing.copy()
        
        for key, value in new.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                merged[key] = self._merge_metadata(merged[key], value)
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                # Extend lists
                merged[key].extend(value)
            else:
                # Overwrite value
                merged[key] = value
        
        return merged
    
    def _backup_metadata(self):
        """Create backup of metadata file.
        
        Backups are stored with .bak extension.
        Only keeps latest backup.
        """
        if not self.metadata_file.exists():
            return
        
        backup_file = self.metadata_file.with_suffix('.meta.json.bak')
        
        try:
            # Read existing
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Write backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(data)
            
            self.logger.debug(f"Created backup: {backup_file}")
        
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
    
    def restore_from_backup(self) -> bool:
        """Restore metadata from backup file.
        
        Returns:
            True if restored successfully
        """
        backup_file = self.metadata_file.with_suffix('.meta.json.bak')
        
        if not backup_file.exists():
            self.logger.warning("No backup file found")
            return False
        
        try:
            # Read backup
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Write to metadata file
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                f.write(data)
            
            self.logger.info(f"Restored metadata from backup: {backup_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def export_to_dict(self) -> Optional[Dict[str, Any]]:
        """Export metadata as dictionary (alias for read).
        
        Returns:
            Metadata dictionary or None
        """
        return self.read()
    
    def import_from_dict(self, data: Dict[str, Any]) -> bool:
        """Import metadata from dictionary (overwrites existing).
        
        Args:
            data: Complete metadata dictionary
            
        Returns:
            True if imported successfully
        """
        try:
            # Backup existing
            if self.exists():
                self._backup_metadata()
            
            # Write new metadata
            self._write_json(data)
            
            self.logger.info(f"Imported metadata from dictionary")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to import metadata: {e}")
            return False
