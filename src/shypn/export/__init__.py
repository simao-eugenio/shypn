"""Export subsystem for SHYpn.

Provides export functionality for Petri Net models to various formats:
- PDF (vector graphics using Cairo)
- PNG (raster images)
- SVG (scalable vector graphics)

Architecture:
- BaseExporter: Abstract base class with common functionality
- PDFExporter: Cairo PDF export implementation
- PNGExporter: Cairo PNG export implementation (future)
- SVGExporter: Cairo SVG export implementation (future)

Author: Simão Eugénio
Date: December 30, 2025
"""

from .base_exporter import BaseExporter, ExportError
from .pdf_exporter import PDFExporter

__all__ = [
    'BaseExporter',
    'ExportError',
    'PDFExporter',
]
