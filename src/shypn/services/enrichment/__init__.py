"""Model enrichment services.

This package provides enrichers that fetch additional information from
external sources and add it to DocumentModel objects.

Available enrichers:
- KEGGStoichiometryEnricher: Add complete reaction stoichiometry to KEGG models
"""

from .base import BaseEnricher, EnrichmentResult
from .stoichiometry import (
    KEGGStoichiometryEnricher,
    ReactionStoichiometry,
    CompoundStoich
)

__all__ = [
    'BaseEnricher',
    'EnrichmentResult',
    'KEGGStoichiometryEnricher',
    'ReactionStoichiometry',
    'CompoundStoich',
]
