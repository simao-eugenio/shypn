"""Cross-reference database for compound ID mapping.

Maps between different biochemical database identifiers:
- KEGG Compound IDs (C00002)
- ChEBI IDs (CHEBI:15422)
- BiGG IDs (atp_c)
"""

from .base import CrossReferenceMapperBase
from .xref_database import CrossReferenceDatabase

__all__ = [
    'CrossReferenceMapperBase',
    'CrossReferenceDatabase',
]
