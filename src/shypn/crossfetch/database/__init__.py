"""Database module for caching inferred parameters.

This module provides SQLite-based caching for:
- Inferred kinetic parameters
- Pathway enrichments
- Heuristic cache (query results)
- Organism compatibility data
"""

from .heuristic_db import HeuristicDatabase

__all__ = ['HeuristicDatabase']
