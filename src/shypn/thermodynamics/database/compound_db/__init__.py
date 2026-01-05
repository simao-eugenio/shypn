"""Compound cross-reference database module.

Provides compound ID mapping between biochemical databases using SQLite backend.

Architecture:
- CompoundDatabaseBase: Abstract interface
- SQLiteCompoundDatabase: SQLite implementation
- Migrator: JSON to SQLite migration tools
"""

from .base import CompoundDatabaseBase, CompoundIdentity
from .sqlite_db import SQLiteCompoundDatabase

__all__ = [
    'CompoundDatabaseBase',
    'CompoundIdentity',
    'SQLiteCompoundDatabase',
]
