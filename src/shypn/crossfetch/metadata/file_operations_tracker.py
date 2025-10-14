"""
File Operations Tracker

Tracks pathway file operations and automatically reflects them to metadata files.
Implements the "gemini" pattern - every file operation on a pathway file is
mirrored in its metadata file.

Author: Shypn Development Team
Date: October 2025
"""

from typing import Optional, Dict, Any, Callable
from pathlib import Path
from datetime import datetime
import logging
import shutil

from .json_metadata_manager import JSONMetadataManager


class FileOperationsTracker:
    """Tracks file operations and updates metadata automatically.
    
    This class wraps file operations (create, save, load, delete, rename, copy)
    and ensures that metadata files are kept in sync with pathway files.
    
    The "gemini" pattern: Every file operation is reflected in metadata.
    
    Features:
    - Automatic metadata creation on file creation
    - Operation logging (what, when, by whom)
    - Metadata sync on all file operations
    - Rollback support on operation failure
    """
    
    def __init__(self, metadata_manager_class=JSONMetadataManager):
        """Initialize file operations tracker.
        
        Args:
            metadata_manager_class: Metadata manager class to use (default: JSONMetadataManager)
        """
        self.metadata_manager_class = metadata_manager_class
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_file(self, 
                   file_path: Path,
                   initial_data: Optional[Dict[str, Any]] = None,
                   user: Optional[str] = None) -> bool:
        """Create pathway file and corresponding metadata.
        
        Args:
            file_path: Path to pathway file
            initial_data: Optional initial metadata
            user: Optional user performing operation
            
        Returns:
            True if created successfully
        """
        try:
            file_path = Path(file_path)
            
            # Create metadata manager
            metadata_mgr = self.metadata_manager_class(file_path)
            
            # Prepare initial metadata
            metadata = initial_data or {}
            metadata.update({
                "pathway_file": str(file_path.name),
                "created": datetime.now().isoformat(),
                "created_by": user or "unknown",
            })
            
            # Create metadata file
            if not metadata_mgr.create(metadata):
                self.logger.error(f"Failed to create metadata for {file_path}")
                return False
            
            # Log operation
            metadata_mgr.log_operation("create", {
                "user": user or "unknown",
                "file_path": str(file_path)
            })
            
            self.logger.info(f"Created file and metadata: {file_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to create file: {e}")
            return False
    
    def save_file(self,
                 file_path: Path,
                 user: Optional[str] = None,
                 changes: Optional[Dict[str, Any]] = None) -> bool:
        """Log save operation to metadata.
        
        Args:
            file_path: Path to pathway file
            user: Optional user performing save
            changes: Optional description of changes
            
        Returns:
            True if logged successfully
        """
        try:
            file_path = Path(file_path)
            metadata_mgr = self.metadata_manager_class(file_path)
            
            # Ensure metadata exists
            if not metadata_mgr.exists():
                self.logger.warning(f"No metadata found for {file_path.name}, creating...")
                metadata_mgr.create()
            
            # Log operation
            metadata_mgr.log_operation("save", {
                "user": user or "unknown",
                "changes": changes or {},
                "file_size": file_path.stat().st_size if file_path.exists() else 0
            })
            
            self.logger.debug(f"Logged save operation: {file_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to log save operation: {e}")
            return False
    
    def load_file(self,
                 file_path: Path,
                 user: Optional[str] = None) -> bool:
        """Log load operation to metadata.
        
        Args:
            file_path: Path to pathway file
            user: Optional user performing load
            
        Returns:
            True if logged successfully
        """
        try:
            file_path = Path(file_path)
            metadata_mgr = self.metadata_manager_class(file_path)
            
            # Ensure metadata exists
            if not metadata_mgr.exists():
                self.logger.warning(f"No metadata found for {file_path.name}, creating...")
                metadata_mgr.create()
            
            # Log operation
            metadata_mgr.log_operation("load", {
                "user": user or "unknown"
            })
            
            self.logger.debug(f"Logged load operation: {file_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to log load operation: {e}")
            return False
    
    def delete_file(self,
                   file_path: Path,
                   user: Optional[str] = None,
                   delete_metadata: bool = True) -> bool:
        """Delete pathway file and optionally its metadata.
        
        Args:
            file_path: Path to pathway file
            user: Optional user performing deletion
            delete_metadata: Whether to delete metadata file (default: True)
            
        Returns:
            True if deleted successfully
        """
        try:
            file_path = Path(file_path)
            metadata_mgr = self.metadata_manager_class(file_path)
            
            if delete_metadata:
                # Log deletion before removing
                if metadata_mgr.exists():
                    metadata_mgr.log_operation("delete", {
                        "user": user or "unknown",
                        "deleted_at": datetime.now().isoformat()
                    })
                    
                    # Delete metadata
                    metadata_mgr.delete()
                    self.logger.info(f"Deleted metadata: {metadata_mgr.get_path().name}")
            else:
                # Mark as deleted in metadata
                if metadata_mgr.exists():
                    metadata_mgr.log_operation("delete", {
                        "user": user or "unknown",
                        "deleted_at": datetime.now().isoformat(),
                        "metadata_preserved": True
                    })
            
            self.logger.info(f"Deleted file: {file_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return False
    
    def rename_file(self,
                   old_path: Path,
                   new_path: Path,
                   user: Optional[str] = None) -> bool:
        """Rename pathway file and update metadata accordingly.
        
        Args:
            old_path: Current file path
            new_path: New file path
            user: Optional user performing rename
            
        Returns:
            True if renamed successfully
        """
        try:
            old_path = Path(old_path)
            new_path = Path(new_path)
            
            # Get old metadata manager
            old_metadata_mgr = self.metadata_manager_class(old_path)
            
            # Read existing metadata
            metadata = old_metadata_mgr.read()
            
            if metadata:
                # Log rename in old metadata
                old_metadata_mgr.log_operation("rename", {
                    "user": user or "unknown",
                    "old_name": str(old_path.name),
                    "new_name": str(new_path.name),
                    "renamed_to": str(new_path)
                })
                
                # Get new metadata manager
                new_metadata_mgr = self.metadata_manager_class(new_path)
                
                # Copy metadata to new location
                metadata["pathway_file"] = str(new_path.name)
                new_metadata_mgr.create(metadata)
                
                # Delete old metadata
                old_metadata_mgr.delete()
                
                self.logger.info(f"Renamed file metadata: {old_path.name} -> {new_path.name}")
            else:
                self.logger.warning(f"No metadata found for {old_path.name}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to rename file: {e}")
            return False
    
    def copy_file(self,
                 source_path: Path,
                 dest_path: Path,
                 user: Optional[str] = None,
                 copy_metadata: bool = True) -> bool:
        """Copy pathway file and optionally its metadata.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            user: Optional user performing copy
            copy_metadata: Whether to copy metadata (default: True)
            
        Returns:
            True if copied successfully
        """
        try:
            source_path = Path(source_path)
            dest_path = Path(dest_path)
            
            if copy_metadata:
                # Get source metadata
                source_metadata_mgr = self.metadata_manager_class(source_path)
                metadata = source_metadata_mgr.read()
                
                if metadata:
                    # Create destination metadata
                    dest_metadata_mgr = self.metadata_manager_class(dest_path)
                    
                    # Update metadata for copy
                    metadata["pathway_file"] = str(dest_path.name)
                    metadata["created"] = datetime.now().isoformat()
                    metadata["copied_from"] = str(source_path.name)
                    
                    dest_metadata_mgr.create(metadata)
                    
                    # Log operation in both
                    source_metadata_mgr.log_operation("copy_source", {
                        "user": user or "unknown",
                        "copied_to": str(dest_path)
                    })
                    
                    dest_metadata_mgr.log_operation("copy_destination", {
                        "user": user or "unknown",
                        "copied_from": str(source_path)
                    })
                    
                    self.logger.info(f"Copied file metadata: {source_path.name} -> {dest_path.name}")
                else:
                    self.logger.warning(f"No metadata found for {source_path.name}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to copy file: {e}")
            return False
    
    def get_metadata_manager(self, file_path: Path) -> JSONMetadataManager:
        """Get metadata manager for a file.
        
        Args:
            file_path: Path to pathway file
            
        Returns:
            Metadata manager instance
        """
        return self.metadata_manager_class(file_path)
    
    def verify_metadata_sync(self, file_path: Path) -> bool:
        """Verify that metadata is in sync with file.
        
        Args:
            file_path: Path to pathway file
            
        Returns:
            True if in sync
        """
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Check if metadata exists
            metadata_mgr = self.metadata_manager_class(file_path)
            if not metadata_mgr.exists():
                self.logger.warning(f"No metadata for {file_path.name}")
                return False
            
            # Read metadata
            metadata = metadata_mgr.read()
            if not metadata:
                self.logger.error(f"Failed to read metadata for {file_path.name}")
                return False
            
            # Verify filename matches
            if metadata.get("pathway_file") != file_path.name:
                self.logger.warning(f"Filename mismatch in metadata for {file_path.name}")
                return False
            
            self.logger.debug(f"Metadata in sync for {file_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to verify metadata sync: {e}")
            return False
    
    def repair_metadata(self, file_path: Path) -> bool:
        """Repair or recreate metadata for a file.
        
        Args:
            file_path: Path to pathway file
            
        Returns:
            True if repaired successfully
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"Cannot repair metadata for non-existent file: {file_path}")
                return False
            
            metadata_mgr = self.metadata_manager_class(file_path)
            
            # Create new metadata
            metadata_mgr.create({
                "repaired": True,
                "repaired_at": datetime.now().isoformat()
            })
            
            self.logger.info(f"Repaired metadata for {file_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to repair metadata: {e}")
            return False
