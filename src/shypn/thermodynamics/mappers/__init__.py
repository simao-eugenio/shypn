"""Compound mapping strategies for thermodynamic validation.

This module provides multiple strategies for mapping Petri net places to
biochemical compound identifiers (KEGG, ChEBI). Each strategy is implemented
as a subclass of CompoundMapperBase, allowing flexible composition.

Available Strategies:
    - LabelBasedMapper: Extracts IDs from place labels using regex and fuzzy matching
    - SBMLAnnotationMapper: Uses SBML species annotations from document metadata
    
Usage Example:
    >>> from shypn.thermodynamics.mappers import CompoundMapperService
    >>> 
    >>> service = CompoundMapperService()
    >>> mappings, confidences = service.map_all_places(document)
    >>> 
    >>> for place_id, compound_id in mappings.items():
    ...     conf = confidences[place_id]
    ...     print(f"{place_id} → {compound_id} (confidence: {conf:.2f})")

See Also:
    - doc/THERMODYNAMICS_USER_GUIDE.md: End-user documentation
    - doc/thermodynamics_api.md: API reference
    - tests/thermodynamics/test_mappers.py: Unit tests

Author: SHYPN Development Team
Date: January 2026
License: See LICENSE file
"""

from .base_mapper import CompoundMapperBase
from .label_matcher import LabelBasedMapper
from .sbml_annotator import SBMLAnnotationMapper
from .compound_mapper_service import CompoundMapperService

__all__ = [
    'CompoundMapperBase',
    'LabelBasedMapper',
    'SBMLAnnotationMapper',
    'CompoundMapperService',
]
