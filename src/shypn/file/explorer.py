#!/usr/bin/env python3
"""File Explorer API for SHYpn.

This module provides the core file system navigation and management functionality.
It's a pure business logic layer with no GTK dependencies, making it testable
and reusable across different UI implementations.

Example:
    explorer = FileExplorer(base_path="/home/user/projects")
    
    # Navigate
    explorer.navigate_to("/home/user/documents")
    
    # Get current directory contents
    entries = explorer.get_current_entries()
    # entries contains list of file/directory dictionaries
    
    # History navigation
    explorer.go_back()
    explorer.go_forward()
    explorer.go_up()
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable


class FileExplorer:
    """Core file system explorer API.
    
    Provides directory navigation, file listing, and history management
    without any GTK dependencies. This is pure business logic.
    
    Attributes:
        current_path: Current directory path (str)
        history_back: List of previous paths for back navigation
        history_forward: List of forward paths for forward navigation
        show_hidden: Whether to show hidden files (default: False)
        sort_by: Sort criteria ('name', 'size', 'modified')
        sort_ascending: Sort direction (default: True)
    """
    
    def __init__(self, base_path: Optional[str] = None, show_hidden: bool = False):
        """Initialize the file explorer.
        
        Args:
            base_path: Starting directory (default: home directory)
            show_hidden: Whether to show hidden files (default: False)
        """
        self.current_path = base_path or str(Path.home())
        self.home_path = self.current_path  # Store home path for go_home()
        self.root_boundary = self.home_path  # Don't navigate above this directory
        self.history_back: List[str] = []
        self.history_forward: List[str] = []
        self.show_hidden = show_hidden
        self.sort_by = 'name'
        self.sort_ascending = True
        
        # Callbacks for observers (UI layer)
        self.on_path_changed: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Validate initial path
        if not os.path.isdir(self.current_path):
            self.current_path = str(Path.home())
            self.home_path = self.current_path
            self.root_boundary = self.current_path
    
    def _is_within_boundary(self, path: str) -> bool:
        """Check if path is within the root boundary (models directory).
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path is within or equal to root_boundary
        """
        # Normalize paths for comparison
        path = os.path.normpath(os.path.abspath(path))
        boundary = os.path.normpath(os.path.abspath(self.root_boundary))
        
        # Check if path is within boundary
        return path == boundary or path.startswith(boundary + os.sep)
    
    def navigate_to(self, path: str) -> bool:
        """Navigate to a specific directory.
        
        Args:
            path: Target directory path
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        if not os.path.isdir(path):
            if self.on_error:
                self.on_error(f"Not a directory: {path}")
            return False
        
        # Check if path is within boundary (models directory and subdirectories)
        if not self._is_within_boundary(path):
            if self.on_error:
                self.on_error(f"Cannot navigate outside models directory")
            return False
        
        # Update history
        if self.current_path != path:
            self.history_back.append(self.current_path)
            self.history_forward.clear()
        
        self.current_path = path
        
        # Notify observers
        if self.on_path_changed:
            self.on_path_changed(self.current_path)
        
        return True
    
    def go_back(self) -> bool:
        """Navigate to previous directory in history.
        
        Returns:
            bool: True if navigation successful, False if no history
        """
        if not self.history_back:
            return False
        
        # Move current to forward history
        self.history_forward.append(self.current_path)
        
        # Pop from back history
        self.current_path = self.history_back.pop()
        
        # Notify observers
        if self.on_path_changed:
            self.on_path_changed(self.current_path)
        
        return True
    
    def go_forward(self) -> bool:
        """Navigate to next directory in history.
        
        Returns:
            bool: True if navigation successful, False if no forward history
        """
        if not self.history_forward:
            return False
        
        # Move current to back history
        self.history_back.append(self.current_path)
        
        # Pop from forward history
        self.current_path = self.history_forward.pop()
        
        # Notify observers
        if self.on_path_changed:
            self.on_path_changed(self.current_path)
        
        return True
    
    def go_up(self) -> bool:
        """Navigate to parent directory.
        
        Only allows navigation up to the root boundary (models directory).
        
        Returns:
            bool: True if navigation successful, False if at boundary or root
        """
        parent = os.path.dirname(self.current_path)
        
        # Check if we can go up (not at root)
        if parent == self.current_path:
            return False
        
        # Check if parent is within boundary
        if not self._is_within_boundary(parent):
            return False
        
        # Check if we're already at the boundary
        if os.path.normpath(self.current_path) == os.path.normpath(self.root_boundary):
            return False
        
        return self.navigate_to(parent)
    
    def go_home(self) -> bool:
        """Navigate to home directory (models directory).
        
        Returns:
            bool: True (always succeeds)
        """
        return self.navigate_to(self.home_path)
    
    def refresh(self) -> None:
        """Refresh current directory (trigger path changed callback)."""
        if self.on_path_changed:
            self.on_path_changed(self.current_path)
    
    def get_current_entries(self) -> List[Dict[str, any]]:
        """Get entries (files and directories) in current path.
        
        Returns:
            List of dictionaries with file/directory information:
            - name: Display name (str)
            - path: Full path (str)
            - is_directory: Whether it's a directory (bool)
            - size: File size in bytes (int, 0 for directories)
            - size_formatted: Human-readable size (str)
            - modified: Modification timestamp (float)
            - modified_formatted: Human-readable date/time (str)
            - icon_name: Suggested icon name (str)
        """
        entries = []
        
        try:
            items = os.listdir(self.current_path)
            
            for item in items:
                # Skip hidden files if configured
                if not self.show_hidden and item.startswith('.'):
                    continue
                
                full_path = os.path.join(self.current_path, item)
                
                try:
                    stat = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    
                    entry = {
                        'name': item,
                        'path': full_path,
                        'is_directory': is_dir,
                        'size': 0 if is_dir else stat.st_size,
                        'size_formatted': '' if is_dir else self._format_size(stat.st_size),
                        'modified': stat.st_mtime,
                        'modified_formatted': self._format_time(stat.st_mtime),
                        'icon_name': self._get_icon_name(item, is_dir)
                    }
                    
                    entries.append(entry)
                    
                except (PermissionError, OSError):
                    # Skip files we can't read
                    continue
            
            # Sort entries
            entries = self._sort_entries(entries)
            
        except PermissionError:
            if self.on_error:
                self.on_error(f"Permission denied: {self.current_path}")
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error reading directory: {str(e)}")
        
        return entries
    
    def _sort_entries(self, entries: List[Dict]) -> List[Dict]:
        """Sort entries based on current sort settings.
        
        Directories always come first, then files sorted by criteria.
        
        Args:
            entries: List of entry dictionaries
            
        Returns:
            Sorted list of entries
        """
        # Separate directories and files
        dirs = [e for e in entries if e['is_directory']]
        files = [e for e in entries if not e['is_directory']]
        
        # Sort each group
        def get_sort_key(entry):
            if self.sort_by == 'name':
                return entry['name'].lower()
            elif self.sort_by == 'size':
                return entry['size']
            elif self.sort_by == 'modified':
                return entry['modified']
            return entry['name'].lower()
        
        dirs.sort(key=get_sort_key, reverse=not self.sort_ascending)
        files.sort(key=get_sort_key, reverse=not self.sort_ascending)
        
        return dirs + files
    
    def _format_size(self, size: int) -> str:
        """Format file size for display.
        
        Args:
            size: Size in bytes
            
        Returns:
            Human-readable size string (e.g., "1.2 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{size:.0f} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format modification time for display.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Formatted date/time string
        """
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError):
            return ""
    
    def _get_icon_name(self, filename: str, is_directory: bool) -> str:
        """Get appropriate icon name for file or directory.
        
        Args:
            filename: Name of file or directory
            is_directory: Whether item is a directory
            
        Returns:
            GTK icon name (symbolic)
        """
        if is_directory:
            return "folder-symbolic"
        
        # Get file extension
        ext = os.path.splitext(filename)[1].lower()
        
        # Map extensions to icon names
        icon_map = {
            # SHYpn Petri net files (use application icon)
            '.shy': 'application-x-executable-symbolic',
            
            # Other Petri net files
            '.pn': 'application-x-executable-symbolic',
            '.pnml': 'application-x-executable-symbolic',
            
            # Text files
            '.txt': 'text-x-generic-symbolic',
            '.md': 'text-x-generic-symbolic',
            '.rst': 'text-x-generic-symbolic',
            
            # Code files
            '.py': 'text-x-python-symbolic',
            '.js': 'text-x-script-symbolic',
            '.ts': 'text-x-script-symbolic',
            '.c': 'text-x-csrc-symbolic',
            '.cpp': 'text-x-c++src-symbolic',
            '.h': 'text-x-chdr-symbolic',
            '.java': 'text-x-java-symbolic',
            
            # Data files
            '.json': 'text-x-generic-symbolic',
            '.xml': 'text-x-generic-symbolic',
            '.yaml': 'text-x-generic-symbolic',
            '.yml': 'text-x-generic-symbolic',
            '.csv': 'x-office-spreadsheet-symbolic',
            
            # Documents
            '.pdf': 'x-office-document-symbolic',
            '.doc': 'x-office-document-symbolic',
            '.docx': 'x-office-document-symbolic',
            '.odt': 'x-office-document-symbolic',
            
            # Images
            '.png': 'image-x-generic-symbolic',
            '.jpg': 'image-x-generic-symbolic',
            '.jpeg': 'image-x-generic-symbolic',
            '.gif': 'image-x-generic-symbolic',
            '.svg': 'image-x-generic-symbolic',
            '.bmp': 'image-x-generic-symbolic',
            
            # Archives
            '.zip': 'package-x-generic-symbolic',
            '.tar': 'package-x-generic-symbolic',
            '.gz': 'package-x-generic-symbolic',
            '.bz2': 'package-x-generic-symbolic',
            '.xz': 'package-x-generic-symbolic',
            '.7z': 'package-x-generic-symbolic',
        }
        
        return icon_map.get(ext, 'text-x-generic-symbolic')
    
    def can_go_back(self) -> bool:
        """Check if back navigation is available.
        
        Returns:
            bool: True if can go back
        """
        return len(self.history_back) > 0
    
    def can_go_forward(self) -> bool:
        """Check if forward navigation is available.
        
        Returns:
            bool: True if can go forward
        """
        return len(self.history_forward) > 0
    
    def can_go_up(self) -> bool:
        """Check if up navigation is available (not at root or boundary).
        
        Returns:
            bool: True if can go up within boundary
        """
        # Check if already at boundary
        if os.path.normpath(self.current_path) == os.path.normpath(self.root_boundary):
            return False
        
        parent = os.path.dirname(self.current_path)
        
        # Check if at filesystem root
        if parent == self.current_path:
            return False
        
        # Check if parent is within boundary
        return self._is_within_boundary(parent)
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about current directory.
        
        Returns:
            Dictionary with counts:
            - total: Total items
            - directories: Number of directories
            - files: Number of files
        """
        entries = self.get_current_entries()
        dirs = sum(1 for e in entries if e['is_directory'])
        files = len(entries) - dirs
        
        return {
            'total': len(entries),
            'directories': dirs,
            'files': files
        }
    
    def set_sort(self, sort_by: str, ascending: bool = True) -> None:
        """Set sort criteria.
        
        Args:
            sort_by: Sort field ('name', 'size', 'modified')
            ascending: Sort direction (default: True)
        """
        if sort_by in ['name', 'size', 'modified']:
            self.sort_by = sort_by
            self.sort_ascending = ascending
            # Refresh to apply new sort
            self.refresh()
    
    def set_show_hidden(self, show_hidden: bool) -> None:
        """Set whether to show hidden files.
        
        Args:
            show_hidden: True to show hidden files
        """
        if self.show_hidden != show_hidden:
            self.show_hidden = show_hidden
            # Refresh to apply change
            self.refresh()
    
    def get_breadcrumbs(self) -> List[Dict[str, str]]:
        """Get breadcrumb path components for navigation.
        
        Returns:
            List of dictionaries with:
            - name: Directory name
            - path: Full path to this directory
        """
        breadcrumbs = []
        path = self.current_path
        
        while True:
            parent = os.path.dirname(path)
            name = os.path.basename(path) or path  # Use full path for root
            
            breadcrumbs.insert(0, {'name': name, 'path': path})
            
            # Stop at root
            if parent == path:
                break
            
            path = parent
        
        return breadcrumbs
    
    # File Operations
    
    def create_folder(self, name: str) -> bool:
        """Create a new folder in the current directory.
        
        Args:
            name: Name of the new folder
            
        Returns:
            bool: True if creation successful, False otherwise
        """
        if not name or name.strip() == '':
            if self.on_error:
                self.on_error("Folder name cannot be empty")
            return False
        
        # Sanitize name (remove path separators)
        name = name.strip().replace('/', '').replace('\\', '')
        
        if name in ['.', '..']:
            if self.on_error:
                self.on_error("Invalid folder name")
            return False
        
        new_path = os.path.join(self.current_path, name)
        
        if os.path.exists(new_path):
            if self.on_error:
                self.on_error(f"'{name}' already exists")
            return False
        
        try:
            os.makedirs(new_path)
            # Refresh to show new folder
            self.refresh()
            return True
        except PermissionError:
            if self.on_error:
                self.on_error(f"Permission denied: cannot create '{name}'")
            return False
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error creating folder: {str(e)}")
            return False
    
    def rename_item(self, old_path: str, new_name: str) -> bool:
        """Rename a file or folder.
        
        Args:
            old_path: Full path to the item to rename
            new_name: New name (not full path, just the name)
            
        Returns:
            bool: True if rename successful, False otherwise
        """
        if not new_name or new_name.strip() == '':
            if self.on_error:
                self.on_error("Name cannot be empty")
            return False
        
        # Sanitize name
        new_name = new_name.strip().replace('/', '').replace('\\', '')
        
        if new_name in ['.', '..']:
            if self.on_error:
                self.on_error("Invalid name")
            return False
        
        if not os.path.exists(old_path):
            if self.on_error:
                self.on_error("Item does not exist")
            return False
        
        # Build new path (same directory, new name)
        directory = os.path.dirname(old_path)
        new_path = os.path.join(directory, new_name)
        
        if os.path.exists(new_path):
            if self.on_error:
                self.on_error(f"'{new_name}' already exists")
            return False
        
        try:
            os.rename(old_path, new_path)
            # Refresh to show renamed item
            self.refresh()
            return True
        except PermissionError:
            if self.on_error:
                self.on_error(f"Permission denied: cannot rename")
            return False
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error renaming: {str(e)}")
            return False
    
    def delete_item(self, path: str) -> bool:
        """Delete a file or folder.
        
        For directories, only deletes if empty (safety measure).
        
        Args:
            path: Full path to the item to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not os.path.exists(path):
            if self.on_error:
                self.on_error("Item does not exist")
            return False
        
        try:
            if os.path.isdir(path):
                # Check if directory is empty
                if os.listdir(path):
                    if self.on_error:
                        self.on_error("Cannot delete non-empty folder")
                    return False
                os.rmdir(path)
            else:
                os.remove(path)
            
            # Refresh to update view
            self.refresh()
            return True
        except PermissionError:
            if self.on_error:
                self.on_error("Permission denied: cannot delete")
            return False
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error deleting: {str(e)}")
            return False
    
    def get_file_info(self, path: str) -> Optional[Dict[str, any]]:
        """Get detailed information about a file or folder.
        
        Args:
            path: Full path to the item
            
        Returns:
            Dictionary with detailed information or None if error:
            - name: Item name
            - path: Full path
            - is_directory: Whether it's a directory
            - size: Size in bytes
            - size_formatted: Human-readable size
            - modified: Modification timestamp
            - modified_formatted: Formatted date/time
            - created: Creation timestamp (if available)
            - created_formatted: Formatted date/time
            - permissions: File permissions (octal string)
            - readable: Whether user can read
            - writable: Whether user can write
            - executable: Whether user can execute
        """
        if not os.path.exists(path):
            if self.on_error:
                self.on_error("Item does not exist")
            return None
        
        try:
            stat = os.stat(path)
            is_dir = os.path.isdir(path)
            
            info = {
                'name': os.path.basename(path),
                'path': path,
                'is_directory': is_dir,
                'size': 0 if is_dir else stat.st_size,
                'size_formatted': '' if is_dir else self._format_size(stat.st_size),
                'modified': stat.st_mtime,
                'modified_formatted': self._format_time(stat.st_mtime),
                'permissions': oct(stat.st_mode)[-3:],
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK),
                'executable': os.access(path, os.X_OK),
            }
            
            # Add creation time if available (not on all systems)
            if hasattr(stat, 'st_birthtime'):
                info['created'] = stat.st_birthtime
                info['created_formatted'] = self._format_time(stat.st_birthtime)
            
            # For directories, add item count
            if is_dir:
                try:
                    items = os.listdir(path)
                    info['item_count'] = len(items)
                except (PermissionError, OSError):
                    info['item_count'] = 0
            
            return info
            
        except (PermissionError, OSError) as e:
            if self.on_error:
                self.on_error(f"Error getting file info: {str(e)}")
            return None
