"""
Canvas Context - Container for canvas-scoped components.

Holds all components associated with a specific canvas instance:
- Drawing area widget
- Document model
- Simulation controller
- SwissKnife palette
- ID scope identifier
- Metadata (creation time, file path, etc.)
"""

import time
from dataclasses import dataclass, field
from typing import Optional
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


@dataclass
class CanvasContext:
    """Container for all components associated with a canvas instance.
    
    This class encapsulates all per-canvas state, ensuring clean separation
    between different document canvases in a multi-tab environment.
    
    Attributes:
        drawing_area: The GTK DrawingArea widget for this canvas
        document_model: The Petri net model (places, transitions, arcs)
        controller: Simulation controller for this canvas
        palette: SwissKnife palette instance for this canvas
        id_scope: Unique identifier for IDManager scope
        canvas_manager: ModelCanvasManager instance
        file_path: Path to loaded .shy file (None for new documents)
        is_modified: Whether document has unsaved changes
        creation_time: Unix timestamp of canvas creation
        last_save_time: Unix timestamp of last save (None if never saved)
    """
    
    # Core components (required)
    drawing_area: Gtk.DrawingArea
    document_model: 'DocumentModel'  # Forward reference
    controller: 'SimulationController'  # Forward reference
    palette: 'SwissKnifePalette'  # Forward reference
    id_scope: str
    canvas_manager: 'ModelCanvasManager'  # Forward reference
    
    # Metadata (optional with defaults)
    file_path: Optional[str] = None
    is_modified: bool = False
    creation_time: float = field(default_factory=time.time)
    last_save_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate context after initialization."""
        if not isinstance(self.drawing_area, Gtk.DrawingArea):
            raise TypeError(f"drawing_area must be Gtk.DrawingArea, got {type(self.drawing_area)}")
        
        if not self.id_scope:
            raise ValueError("id_scope cannot be empty")
        
        # Validate document_model has required attributes
        required_attrs = ['places', 'transitions', 'arcs']
        for attr in required_attrs:
            if not hasattr(self.document_model, attr):
                raise AttributeError(f"document_model missing required attribute: {attr}")
    
    @property
    def canvas_id(self) -> int:
        """Get unique canvas ID (memory address of drawing area)."""
        return id(self.drawing_area)
    
    @property
    def display_name(self) -> str:
        """Get display name for this canvas (for tab labels)."""
        if self.file_path:
            import os
            return os.path.basename(self.file_path)
        else:
            return "Untitled"
    
    @property
    def is_simulation_running(self) -> bool:
        """Check if simulation is currently running."""
        return hasattr(self.controller, '_running') and self.controller._running
    
    def mark_modified(self):
        """Mark document as modified (has unsaved changes)."""
        self.is_modified = True
    
    def mark_saved(self, file_path: str):
        """Mark document as saved.
        
        Args:
            file_path: Path where file was saved
        """
        self.file_path = file_path
        self.is_modified = False
        self.last_save_time = time.time()
    
    def get_object_counts(self) -> dict:
        """Get count of objects in this canvas.
        
        Returns:
            Dictionary with counts: {'places': N, 'transitions': M, 'arcs': K}
        """
        return {
            'places': len(self.document_model.places),
            'transitions': len(self.document_model.transitions),
            'arcs': len(self.document_model.arcs)
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        counts = self.get_object_counts()
        status = "modified" if self.is_modified else "saved"
        running = "running" if self.is_simulation_running else "idle"
        
        return (
            f"CanvasContext("
            f"name='{self.display_name}', "
            f"scope='{self.id_scope}', "
            f"objects={counts['places']}P/{counts['transitions']}T/{counts['arcs']}A, "
            f"status={status}, "
            f"simulation={running})"
        )
