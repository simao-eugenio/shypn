"""Canvas Architecture Package.

This package contains the core canvas architecture components that separate
concerns between data management, viewport state, and document lifecycle.

Components:
- canvas_state: ViewportState and DocumentState for managing view and document metadata
- document_model: DocumentModel for Petri net object storage and queries
- document_canvas: DocumentCanvas as the main controller coordinating everything

Architecture:
    UI Layer (Loaders)
         ↓
    Canvas Layer (DocumentCanvas) ← Main coordinator
         ↓
    Data Layer (DocumentModel + CanvasState)
         ↓
    Domain Layer (netobjs: Place, Transition, Arc)

Usage:
    from shypn.data.canvas import DocumentCanvas, DocumentModel, ViewportState
    
    # Create a new canvas
    canvas = DocumentCanvas(width=800, height=600)
    canvas.create_new_document("Untitled")
    
    # Add objects
    place = canvas.add_place(x=100, y=100)
    
    # Viewport control
    canvas.zoom_in(center_x=400, center_y=300)
    canvas.pan(dx=50, dy=50)
"""

from .canvas_state import ViewportState, DocumentState
from .document_model import DocumentModel
from .document_canvas import DocumentCanvas

__all__ = [
    'ViewportState',
    'DocumentState',
    'DocumentModel',
    'DocumentCanvas',
]
