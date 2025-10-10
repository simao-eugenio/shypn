"""Base class for pathway enhancement processors.

This module defines the abstract interface that all enhancement processors
must implement. Each processor takes a DocumentModel and optionally a
KEGGPathway, performs some enhancement, and returns the modified document.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)


class PostProcessorBase(ABC):
    """Abstract base class for post-processing enhancement modules.
    
    Each processor implements a specific enhancement:
    - LayoutOptimizer: Reduces overlaps, improves spacing
    - ArcRouter: Adds control points for curved arcs
    - MetadataEnhancer: Enriches with KEGG data
    - VisualValidator: Cross-checks with pathway images
    
    Processors are designed to be:
    - Independent: Don't depend on other processors
    - Idempotent: Can be run multiple times safely
    - Configurable: Honor options passed during initialization
    - Loggable: Report what they did for debugging
    """
    
    def __init__(self, options: Optional['EnhancementOptions'] = None):
        """Initialize the processor.
        
        Args:
            options: Configuration options for this processor.
                    If None, uses default options from subclass.
        """
        self.options = options
        self.stats = {}  # Statistics about what was done
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def process(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> 'DocumentModel':
        """Process the document and return enhanced version.
        
        This is the main method that subclasses must implement.
        
        Args:
            document: The Petri net document to enhance.
            pathway: Optional KEGG pathway data for context.
                    Contains semantic and graphics information.
        
        Returns:
            Enhanced DocumentModel (may be same object modified in-place
            or a new copy, depending on processor design).
        
        Raises:
            ProcessorError: If enhancement fails critically.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable name of this processor.
        
        Used for logging and reporting.
        
        Returns:
            String like "Layout Optimizer" or "Arc Router".
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the last processing run.
        
        Returns:
            Dictionary with metrics like:
            {
                'elements_processed': 42,
                'overlaps_resolved': 8,
                'processing_time_ms': 125,
                ...
            }
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """Clear statistics from previous run."""
        self.stats.clear()
    
    def is_applicable(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> bool:
        """Check if this processor can/should run on the given document.
        
        Some processors may have prerequisites:
        - LayoutOptimizer: Needs places with positions
        - ArcRouter: Needs arcs
        - VisualValidator: Needs image URL
        
        Args:
            document: Document to check.
            pathway: Optional pathway data.
        
        Returns:
            True if processor should run, False to skip.
        """
        # Default: always applicable
        return True
    
    def validate_inputs(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None):
        """Validate inputs before processing.
        
        Raises:
            ValueError: If inputs are invalid.
        """
        if document is None:
            raise ValueError(f"{self.get_name()}: document cannot be None")
        
        # Check document has required attributes
        if not hasattr(document, 'places'):
            raise ValueError(f"{self.get_name()}: document must have 'places' attribute")
        if not hasattr(document, 'transitions'):
            raise ValueError(f"{self.get_name()}: document must have 'transitions' attribute")
        if not hasattr(document, 'arcs'):
            raise ValueError(f"{self.get_name()}: document must have 'arcs' attribute")
    
    def __str__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}: {self.get_name()}>"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"{self.__class__.__name__}(options={self.options})"


class ProcessorError(Exception):
    """Exception raised when a processor encounters a critical error.
    
    Non-critical errors should be logged as warnings but not raise exceptions.
    Only raise this for truly unrecoverable errors.
    """
    
    def __init__(self, processor_name: str, message: str, cause: Optional[Exception] = None):
        """Initialize processor error.
        
        Args:
            processor_name: Name of the processor that failed.
            message: Description of the error.
            cause: Optional underlying exception.
        """
        self.processor_name = processor_name
        self.cause = cause
        super().__init__(f"{processor_name}: {message}")
