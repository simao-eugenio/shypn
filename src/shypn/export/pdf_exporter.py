"""PDF exporter using Cairo PDFSurface.

Exports Petri Net models as vector PDF documents with high quality output.
Uses the same rendering code as the canvas display for visual consistency.

Author: Simão Eugénio
Date: December 30, 2025
"""

import cairo
from typing import Dict
from .base_exporter import BaseExporter, ExportError


class PDFExporter(BaseExporter):
    """Export Petri Net models to PDF format using Cairo.
    
    Features:
    - Vector graphics (infinitely scalable)
    - Same rendering as canvas display
    - White background
    - Centered content with padding
    - Production-quality output
    
    Implementation:
    - Uses cairo.PDFSurface for native PDF generation
    - Renders at zoom=1.0 for consistent sizing
    - Calculates optimal dimensions from content bounds
    - No external dependencies (Cairo already present)
    
    Usage:
        exporter = PDFExporter(parent_window=window)
        success = exporter.export(manager, filepath="model.pdf")
        
    Or with dialog:
        filepath = exporter.show_file_dialog(default_filename="mymodel")
        if filepath:
            success = exporter.export(manager, filepath)
    """
    
    def get_file_extension(self) -> str:
        """Get PDF file extension."""
        return '.pdf'
    
    def get_format_name(self) -> str:
        """Get format name."""
        return 'PDF'
    
    def _render_to_file(self, manager, filepath: str, bounds: Dict[str, float], 
                       padding: float) -> None:
        """Render model to PDF file using Cairo PDFSurface.
        
        Rendering pipeline:
        1. Create PDFSurface with calculated dimensions
        2. Set white background
        3. Translate to center content with padding
        4. Render all objects at zoom=1.0
        5. Finalize PDF surface
        
        Args:
            manager: ModelCanvasManager with model data
            filepath: Output PDF file path
            bounds: Bounding box dict with 'min_x', 'min_y', 'max_x', 'max_y'
            padding: Padding around content in world units
            
        Raises:
            ExportError: If rendering fails
        """
        try:
            # Calculate PDF dimensions (in points, 1 point = 1/72 inch)
            width, height = self.get_content_dimensions(bounds, padding)
            
            # Create Cairo PDF surface
            surface = cairo.PDFSurface(filepath, width, height)
            cr = cairo.Context(surface)
            
            # Set white background
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            
            # Translate to center content with padding
            # This moves the origin so that the content bounding box
            # starts at (padding, padding) instead of (min_x, min_y)
            cr.translate(
                -bounds['min_x'] + padding,
                -bounds['min_y'] + padding
            )
            
            # Render all objects at 1:1 scale (zoom=1.0 for PDF)
            # Objects render in world coordinates, no scaling needed
            all_objects = manager.get_all_objects()
            for obj in all_objects:
                obj.render(cr, zoom=1.0)
            
            # Finalize PDF (write to disk)
            surface.finish()
            
        except cairo.Error as e:
            raise ExportError(f"Cairo rendering error: {e}") from e
        except IOError as e:
            raise ExportError(f"File write error: {e}") from e
        except Exception as e:
            raise ExportError(f"Unexpected error during PDF export: {e}") from e
    
    def export_with_options(self, manager, filepath: str, 
                          include_grid: bool = False,
                          scale: float = 1.0) -> bool:
        """Export with additional options (future enhancement).
        
        Args:
            manager: ModelCanvasManager with model data
            filepath: Output PDF file path
            include_grid: Whether to render grid (default False)
            scale: Scale factor for output (default 1.0)
            
        Returns:
            True if export successful
            
        Raises:
            ExportError: If export fails
        """
        # TODO: Implement grid rendering
        # TODO: Implement scale transformation
        # For now, just call basic export
        return self.export(manager, filepath)
