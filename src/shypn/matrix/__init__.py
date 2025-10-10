"""Petri Net Incidence Matrix Module.

This module provides formal Petri net semantics using incidence matrices.
The matrix representation serves as the source of truth for the Petri net structure.

Architecture:
    IncidenceMatrix (base class) - Abstract interface for matrix operations
        ├── SparseIncidenceMatrix - Memory-efficient sparse matrix implementation
        └── DenseIncidenceMatrix - Dense matrix implementation for small nets
    MatrixManager - Integration layer for simulation system

Usage:
    from shypn.matrix import MatrixManager
    
    # Create manager (auto-builds matrix)
    manager = MatrixManager(document)
    
    # Query matrix
    if manager.is_enabled(transition_id, marking):
        new_marking = manager.fire(transition_id, marking)
    
    # Or use directly
    from shypn.matrix import SparseIncidenceMatrix
    matrix = SparseIncidenceMatrix(document)
    matrix.build()
"""

from .base import IncidenceMatrix
from .sparse import SparseIncidenceMatrix
from .dense import DenseIncidenceMatrix
from .manager import MatrixManager

__all__ = [
    'IncidenceMatrix',
    'SparseIncidenceMatrix', 
    'DenseIncidenceMatrix',
    'MatrixManager',
]
