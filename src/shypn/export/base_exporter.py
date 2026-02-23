"""Base exporter class for model export functionality.

Provides common functionality for all export formats:
- Bounding box calculation
- File dialog management (Wayland-safe)
- Error handling
- Export validation

Author: Simão Eugénio
Date: December 30, 2025
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from shypn.data.project_models import get_project_manager


class ExportError(Exception):
    """Exception raised for export-related errors."""
    pass


class BaseExporter(ABC):
    """Abstract base class for model exporters.
    
    Provides common functionality for exporting Petri Net models to various formats.
    Subclasses implement format-specific rendering logic.
    
    Architecture:
    - Minimal dependency on GTK (only for dialogs)
    - Format-agnostic bounding box calculation
    - Wayland-safe parent window handling
    - Consistent error handling
    
    Usage:
        exporter = PDFExporter(parent_window=window)
        success = exporter.export(manager, filepath="/path/to/output.pdf")
    """
    
    def __init__(self, parent_window: Optional[Gtk.Window] = None):
        """Initialize the exporter.
        
        Args:
            parent_window: Parent window for dialogs (Wayland-safe)
        """
        self.parent_window = parent_window
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this export format.
        
        Returns:
            File extension including dot (e.g., '.pdf', '.png', '.svg')
        """
        pass
    
    @abstractmethod
    def get_format_name(self) -> str:
        """Get the human-readable format name.
        
        Returns:
            Format name (e.g., 'PDF', 'PNG', 'SVG')
        """
        pass
    
    @abstractmethod
    def _render_to_file(self, manager, filepath: str, bounds: Dict[str, float], 
                       padding: float) -> None:
        """Render the model to a file (format-specific implementation).
        
        Args:
            manager: ModelCanvasManager with model data
            filepath: Output file path
            bounds: Bounding box dict with 'min_x', 'min_y', 'max_x', 'max_y'
            padding: Padding around content in world units
            
        Raises:
            ExportError: If rendering fails
        """
        pass
    
    def export(self, manager, filepath: str, padding_percent: float = 10.0) -> bool:
        """Export the model to a file.
        
        Args:
            manager: ModelCanvasManager with model data
            filepath: Output file path
            padding_percent: Padding as percentage of content size (default 10%)
            
        Returns:
            True if export successful, False otherwise
            
        Raises:
            ExportError: If export fails with details
        """
        try:
            # Validate input
            if not manager:
                raise ExportError("No model manager provided")
            
            if not filepath:
                raise ExportError("No output filepath provided")
            
            # Calculate bounding box
            bounds = self.calculate_bounds(manager)
            if bounds is None:
                raise ExportError("Cannot export empty model (no objects)")
            
            # Calculate padding
            content_width = bounds['max_x'] - bounds['min_x']
            content_height = bounds['max_y'] - bounds['min_y']
            padding = max(
                content_width * (padding_percent / 100.0),
                content_height * (padding_percent / 100.0),
                20.0  # Minimum 20 units padding
            )
            
            # Ensure correct file extension
            if not filepath.lower().endswith(self.get_file_extension()):
                filepath += self.get_file_extension()
            
            # Delegate to format-specific renderer
            self._render_to_file(manager, filepath, bounds, padding)
            
            return True
            
        except ExportError:
            raise
        except (AttributeError, ValueError, TypeError, OSError, IOError) as e:
            raise ExportError(f"Export failed: {e}") from e
    
    def calculate_bounds(self, manager) -> Optional[Dict[str, float]]:
        """Calculate bounding box of all objects in the model.
        
        Args:
            manager: ModelCanvasManager instance
            
        Returns:
            dict with 'min_x', 'min_y', 'max_x', 'max_y' or None if empty
        """
        all_objects = manager.get_all_objects()
        if not all_objects:
            return None
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for obj in all_objects:
            bbox = obj.get_bounding_box()
            if bbox:
                min_x = min(min_x, bbox['x'])
                min_y = min(min_y, bbox['y'])
                max_x = max(max_x, bbox['x'] + bbox['width'])
                max_y = max(max_y, bbox['y'] + bbox['height'])
        
        # Validate bounds
        if min_x == float('inf') or max_x == float('-inf'):
            return None
        
        return {
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def show_file_dialog(self, default_filename: str = "model") -> Optional[str]:
        """Show file chooser dialog for export (Wayland-safe).
        
        Args:
            default_filename: Default filename without extension (can include path)
            
        Returns:
            Selected filepath or None if cancelled
        """
        import os
        
        # Get the actual top-level window (Wayland-safe)
        parent = None
        if self.parent_window:
            parent = self.parent_window
            # Ensure we have the top-level window
            if hasattr(parent, 'get_toplevel'):
                toplevel = parent.get_toplevel()
                if isinstance(toplevel, Gtk.Window):
                    parent = toplevel
        
        dialog = Gtk.FileChooserDialog(
            title=f"Export as {self.get_format_name()}",
            transient_for=parent,  # Wayland-safe
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # File filter for this format
        filter_format = Gtk.FileFilter()
        filter_format.set_name(f"{self.get_format_name()} files (*{self.get_file_extension()})")
        filter_format.add_pattern(f"*{self.get_file_extension()}")
        dialog.add_filter(filter_format)
        
        # All files filter (fallback)
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        # Set initial directory to project base path if project is open
        project_manager = get_project_manager()
        if project_manager.current_project:
            project_exports_dir = os.path.join(project_manager.current_project.base_path, 'exports')
            if not os.path.exists(project_exports_dir):
                try:
                    os.makedirs(project_exports_dir, exist_ok=True)
                except (OSError, PermissionError) as e:
                    from shypn.utils.logging import get_logger
                    logger = get_logger(__name__)
                    logger.debug(f"Failed to create exports directory {project_exports_dir}: {e}")
            if os.path.isdir(project_exports_dir):
                dialog.set_current_folder(project_exports_dir)
            else:
                dialog.set_current_folder(project_manager.current_project.base_path)
        
        # Set default location and filename
        if default_filename and os.path.isabs(default_filename):
            # If absolute path, extract directory and filename
            directory = os.path.dirname(default_filename)
            filename = os.path.basename(default_filename)
            if directory and os.path.isdir(directory):
                dialog.set_current_folder(directory)
            # Remove extension if present to avoid double extension
            name_without_ext = os.path.splitext(filename)[0]
            dialog.set_current_name(f"{name_without_ext}{self.get_file_extension()}")
        else:
            # Just use as filename
            dialog.set_current_name(f"{default_filename}{self.get_file_extension()}")
        
        # Run dialog
        response = dialog.run()
        filepath = None
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            
            # Ensure correct extension
            if filepath and not filepath.lower().endswith(self.get_file_extension()):
                filepath += self.get_file_extension()
        
        dialog.destroy()
        return filepath
    
    def get_content_dimensions(self, bounds: Dict[str, float], padding: float) -> Tuple[float, float]:
        """Calculate final content dimensions with padding.
        
        Args:
            bounds: Bounding box dict
            padding: Padding in world units
            
        Returns:
            Tuple of (width, height) in world units
        """
        width = bounds['max_x'] - bounds['min_x'] + 2 * padding
        height = bounds['max_y'] - bounds['min_y'] + 2 * padding
        return (width, height)
