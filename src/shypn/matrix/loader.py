"""Matrix Loader - Minimal factory for creating incidence matrices.

This module provides a simple interface for loading incidence matrices
from documents. The loader automatically selects the appropriate
implementation based on net size and density.

Usage:
    from shypn.matrix.loader import load_matrix
    
    # Auto-select implementation
    matrix = load_matrix(document)
    
    # Or explicitly specify
    matrix = load_matrix(document, implementation='sparse')
"""

from typing import Optional, Literal
from .base import IncidenceMatrix
from .sparse import SparseIncidenceMatrix
from .dense import DenseIncidenceMatrix


# Threshold for auto-selection (number of places × transitions)
AUTO_SELECT_THRESHOLD = 1000  # Use sparse if P×T > 1000


def load_matrix(
    document,
    implementation: Optional[Literal['sparse', 'dense', 'auto']] = 'auto',
    auto_build: bool = True
) -> IncidenceMatrix:
    """Load and build incidence matrix from document.
    
    Factory function that creates the appropriate matrix implementation
    based on the document and user preferences.
    
    Args:
        document: DocumentModel containing the Petri net
        implementation: Matrix implementation to use:
            - 'sparse': Use SparseIncidenceMatrix (dict-based)
            - 'dense': Use DenseIncidenceMatrix (NumPy array)
            - 'auto': Automatically select based on size (default)
        auto_build: If True, automatically call build() before returning
        
    Returns:
        Incidence matrix instance (built if auto_build=True)
        
    Raises:
        ValueError: If document is None or implementation invalid
        
    Example:
        >>> from shypn.matrix.loader import load_matrix
        >>> matrix = load_matrix(document)
        >>> print(matrix.get_statistics())
        {'built': True, 'places': 25, 'transitions': 34, 'total_arcs': 73}
    """
    if document is None:
        raise ValueError("Cannot load matrix: document is None")
    
    # Auto-select implementation
    if implementation == 'auto':
        num_places = len(document.places)
        num_transitions = len(document.transitions)
        matrix_size = num_places * num_transitions
        
        if matrix_size > AUTO_SELECT_THRESHOLD:
            implementation = 'sparse'
        else:
            implementation = 'dense'
    
    # Create matrix instance
    if implementation == 'sparse':
        matrix = SparseIncidenceMatrix(document)
    elif implementation == 'dense':
        matrix = DenseIncidenceMatrix(document)
    else:
        raise ValueError(
            f"Invalid implementation: {implementation}. "
            f"Use 'sparse', 'dense', or 'auto'."
        )
    
    # Build matrix if requested
    if auto_build:
        matrix.build()
    
    return matrix


def get_recommendation(document) -> str:
    """Get recommended matrix implementation for a document.
    
    Args:
        document: DocumentModel to analyze
        
    Returns:
        Recommended implementation ('sparse' or 'dense')
    """
    if document is None:
        return 'sparse'
    
    num_places = len(document.places)
    num_transitions = len(document.transitions)
    num_arcs = len(document.arcs)
    
    matrix_size = num_places * num_transitions
    
    # Density: fraction of possible arcs that exist
    # Possible arcs = 2 × P × T (bidirectional)
    max_arcs = 2 * num_places * num_transitions
    density = num_arcs / max_arcs if max_arcs > 0 else 0
    
    # Recommend sparse if:
    # - Matrix is large (P×T > threshold)
    # - OR density is low (< 20%)
    if matrix_size > AUTO_SELECT_THRESHOLD or density < 0.2:
        return 'sparse'
    else:
        return 'dense'
