"""Compound mapper service - Facade for orchestrating multiple mapping strategies.

This service coordinates multiple compound mapping strategies and
merges their results with confidence-based prioritization.
"""

from typing import Dict, List, Tuple, Optional
import logging
from .base_mapper import CompoundMapperBase
from .label_matcher import LabelBasedMapper
from .sbml_annotator import SBMLAnnotationMapper


logger = logging.getLogger(__name__)


class CompoundMapperService:
    """Orchestrates multiple mapping strategies.
    
    This facade coordinates:
    1. SBMLAnnotationMapper (highest priority - confidence 1.0)
    2. LabelBasedMapper (fallback - confidence 0.6-0.95)
    
    The service merges results, preferring higher-confidence mappings.
    
    Usage Example:
        >>> service = CompoundMapperService()
        >>> mappings, confidences = service.map_all_places(document)
        >>> 
        >>> # Get only high-confidence mappings
        >>> high_conf = {
        ...     pid: cid for pid, cid in mappings.items()
        ...     if confidences[pid] > 0.8
        ... }
    """
    
    def __init__(self, custom_mappers: Optional[List[CompoundMapperBase]] = None):
        """Initialize compound mapper service.
        
        Args:
            custom_mappers: Optional list of additional mappers to use.
                          If None, uses default set (SBML + Label).
        """
        if custom_mappers is not None:
            self.mappers = custom_mappers
        else:
            # Default strategy: SBML annotations (high confidence) + label matching (fallback)
            self.mappers = [
                SBMLAnnotationMapper(),
                LabelBasedMapper(),
            ]
        
        logger.info(f"CompoundMapperService initialized with {len(self.mappers)} mappers")
    
    def map_all_places(self, document) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Map all places in document to compound IDs.
        
        This method:
        1. Runs all mappers
        2. Merges results, preferring higher confidence
        3. Returns mappings and confidence scores
        
        Args:
            document: DocumentModel with places and metadata
            
        Returns:
            Tuple of (mappings dict, confidences dict)
            - mappings: {place_id: compound_id}
            - confidences: {place_id: confidence_score}
            
        Example:
            >>> mappings, confidences = service.map_all_places(document)
            >>> len(mappings)
            15
            >>> confidences["P001"]
            0.95
        """
        if not hasattr(document, 'places'):
            logger.warning("Document has no places attribute")
            return {}, {}
        
        places = document.places
        if not places:
            logger.info("No places to map")
            return {}, {}
        
        # Collect results from all mappers
        all_mappings: Dict[str, List[Tuple[str, float]]] = {}  # place_id → [(compound_id, confidence), ...]
        
        for mapper in self.mappers:
            try:
                # Run mapper
                if isinstance(mapper, SBMLAnnotationMapper):
                    # SBML mapper needs document for metadata
                    mapper_results = mapper.map_places(places, document=document)
                else:
                    mapper_results = mapper.map_places(places)
                
                # Collect results with confidence scores
                for place_id, compound_id in mapper_results.items():
                    confidence = mapper.get_confidence(place_id)
                    
                    if place_id not in all_mappings:
                        all_mappings[place_id] = []
                    
                    all_mappings[place_id].append((compound_id, confidence))
                    
            except Exception as e:
                logger.error(f"Mapper {mapper.__class__.__name__} failed: {e}")
                continue
        
        # Merge results - prefer highest confidence
        final_mappings = {}
        final_confidences = {}
        
        for place_id, candidates in all_mappings.items():
            if not candidates:
                continue
            
            # Sort by confidence (descending) and pick best
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_compound_id, best_confidence = candidates[0]
            
            final_mappings[place_id] = best_compound_id
            final_confidences[place_id] = best_confidence
        
        logger.info(f"Mapped {len(final_mappings)} places to compound IDs")
        
        # Update document.compound_mappings
        if hasattr(document, 'compound_mappings'):
            document.compound_mappings.update(final_mappings)
            logger.debug(f"Updated document.compound_mappings with {len(final_mappings)} entries")
        
        return final_mappings, final_confidences
    
    def get_mapping_summary(
        self, 
        mappings: Dict[str, str], 
        confidences: Dict[str, float]
    ) -> Dict[str, any]:
        """Generate summary statistics for mappings.
        
        Args:
            mappings: Place → compound mappings
            confidences: Place → confidence scores
            
        Returns:
            Dictionary with summary statistics
            
        Example:
            >>> summary = service.get_mapping_summary(mappings, confidences)
            >>> print(summary['total_mapped'])
            15
            >>> print(summary['high_confidence'])
            12
        """
        if not mappings:
            return {
                'total_mapped': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'average_confidence': 0.0,
            }
        
        high_conf = sum(1 for c in confidences.values() if c >= 0.9)
        medium_conf = sum(1 for c in confidences.values() if 0.5 <= c < 0.9)
        low_conf = sum(1 for c in confidences.values() if c < 0.5)
        avg_conf = sum(confidences.values()) / len(confidences) if confidences else 0.0
        
        return {
            'total_mapped': len(mappings),
            'high_confidence': high_conf,
            'medium_confidence': medium_conf,
            'low_confidence': low_conf,
            'average_confidence': avg_conf,
        }
    
    def update_mapping(
        self, 
        document, 
        place_id: str, 
        compound_id: str,
        confidence: float = 1.0
    ) -> None:
        """Manually update a compound mapping.
        
        This allows users to override automatic mappings.
        
        Args:
            document: DocumentModel to update
            place_id: Place identifier
            compound_id: Compound identifier (KEGG or ChEBI)
            confidence: Confidence score (default 1.0 for manual)
            
        Raises:
            ValueError: If compound_id format is invalid
        """
        # Validate compound ID format
        mapper = LabelBasedMapper()  # Use for validation
        if not mapper.validate_compound_id(compound_id):
            raise ValueError(
                f"Invalid compound ID format: {compound_id}. "
                f"Expected KEGG (C#####) or ChEBI (CHEBI:#####)"
            )
        
        # Update document mappings
        if not hasattr(document, 'compound_mappings'):
            document.compound_mappings = {}
        
        document.compound_mappings[place_id] = compound_id
        
        # Mark document as modified so changes are saved
        if hasattr(document, 'mark_modified'):
            document.mark_modified()
        
        logger.info(f"Manual mapping updated: {place_id} → {compound_id}")
    
    def remove_mapping(self, document, place_id: str) -> None:
        """Remove a compound mapping.
        
        Args:
            document: DocumentModel to update
            place_id: Place identifier to remove
        """
        if hasattr(document, 'compound_mappings') and place_id in document.compound_mappings:
            del document.compound_mappings[place_id]
            
            # Mark document as modified so changes are saved
            if hasattr(document, 'mark_modified'):
                document.mark_modified()
            
            logger.info(f"Removed mapping for {place_id}")
    
    def get_unmapped_places(self, document) -> List:
        """Get list of places without compound mappings.
        
        Args:
            document: DocumentModel
            
        Returns:
            List of Place objects without mappings
        """
        if not hasattr(document, 'places'):
            return []
        
        mappings = document.compound_mappings if hasattr(document, 'compound_mappings') else {}
        
        unmapped = [
            place for place in document.places
            if place.id not in mappings
        ]
        
        return unmapped
