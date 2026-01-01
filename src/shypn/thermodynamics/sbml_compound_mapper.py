"""
SBML Compound Mapper

Maps SBML species to KEGG compound IDs using MIRIAM annotations.
Falls back to name-based matching when annotations unavailable.

Supported Annotation Systems:
- KEGG Compound (direct mapping)
- ChEBI (cross-reference lookup)
- BiGG (cross-reference lookup)
- Name matching (fallback via CompoundResolver)

Design:
- Prioritizes KEGG annotations (direct mapping)
- Uses ChEBI/BiGG as secondary sources
- Falls back to name matching for unannotated species
- Caches all mappings for performance
"""

from typing import Optional, Dict, List
import logging

from shypn.thermodynamics.compound_mapper_base import CompoundMapperBase
from shypn.thermodynamics.compound_resolver import CompoundResolver


class SBMLCompoundMapper(CompoundMapperBase):
    """
    Maps SBML species to KEGG compound IDs.
    
    Extracts identifiers from SBML annotations using MIRIAM URNs.
    Falls back to name-based matching via CompoundResolver.
    """
    
    def __init__(
        self,
        use_cache: bool = True,
        use_name_fallback: bool = True
    ):
        """
        Initialize SBML compound mapper.
        
        Args:
            use_cache: Enable mapping cache
            use_name_fallback: Use name matching when annotations missing
        """
        super().__init__(use_cache=use_cache)
        self.use_name_fallback = use_name_fallback
        
        # Initialize compound resolver for name matching
        if use_name_fallback:
            self.resolver = CompoundResolver()
        else:
            self.resolver = None
    
    def map_species(self, species) -> Optional[str]:
        """
        Map SBML species to KEGG compound ID.
        
        Extraction order:
        1. KEGG compound annotation (direct)
        2. ChEBI annotation (cross-reference - not implemented yet)
        3. BiGG annotation (cross-reference - not implemented yet)
        4. Name matching via CompoundResolver (fallback)
        
        Args:
            species: SBML species object (from pathway_data.species)
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
        """
        species_id = self._get_species_id(species)
        
        # 1. Try KEGG annotation first (highest priority)
        kegg_id = self._extract_kegg_annotation(species)
        if kegg_id:
            self.logger.debug(f"Mapped {species_id} → {kegg_id} (KEGG annotation)")
            return kegg_id
        
        # 2. Try ChEBI annotation (requires cross-reference database)
        chebi_id = self._extract_chebi_annotation(species)
        if chebi_id:
            # TODO: Convert ChEBI to KEGG using cross-reference database
            # For now, log and continue to fallback
            self.logger.debug(
                f"Found ChEBI ID {chebi_id} for {species_id} "
                f"(ChEBI→KEGG conversion not yet implemented)"
            )
        
        # 3. Try BiGG annotation (requires cross-reference database)
        bigg_id = self._extract_bigg_annotation(species)
        if bigg_id:
            # TODO: Convert BiGG to KEGG using cross-reference database
            # For now, log and continue to fallback
            self.logger.debug(
                f"Found BiGG ID {bigg_id} for {species_id} "
                f"(BiGG→KEGG conversion not yet implemented)"
            )
        
        # 4. Fallback to name matching
        if self.use_name_fallback and self.resolver:
            species_name = self._get_species_name(species)
            if species_name:
                resolved_id = self.resolver.resolve(species_name)
                if resolved_id:
                    self.logger.debug(
                        f"Mapped {species_id} → {resolved_id} "
                        f"(name match: '{species_name}')"
                    )
                    return resolved_id
        
        # No mapping found
        self.logger.debug(f"Could not map {species_id} (no annotations or name match)")
        return None
    
    def _get_species_id(self, species) -> str:
        """
        Extract species identifier for caching.
        
        Args:
            species: SBML species object
            
        Returns:
            Species ID string
        """
        return getattr(species, 'id', str(species))
    
    def _get_species_name(self, species) -> Optional[str]:
        """
        Extract species name for name matching.
        
        Args:
            species: SBML species object
            
        Returns:
            Species name or None
        """
        return getattr(species, 'name', None)
    
    def _extract_kegg_annotation(self, species) -> Optional[str]:
        """
        Extract KEGG compound ID from species annotations.
        
        Searches for KEGG MIRIAM URNs in species annotation field.
        
        Args:
            species: SBML species object
            
        Returns:
            KEGG compound ID or None
        """
        # Get annotation from species
        annotation = self._get_annotation(species)
        if not annotation:
            return None
        
        # Try to extract KEGG ID from URN
        kegg_id = self._extract_kegg_from_urn(annotation)
        return kegg_id
    
    def _extract_chebi_annotation(self, species) -> Optional[str]:
        """
        Extract ChEBI ID from species annotations.
        
        Args:
            species: SBML species object
            
        Returns:
            ChEBI ID or None
        """
        annotation = self._get_annotation(species)
        if not annotation:
            return None
        
        return self._extract_chebi_from_urn(annotation)
    
    def _extract_bigg_annotation(self, species) -> Optional[str]:
        """
        Extract BiGG ID from species annotations.
        
        Args:
            species: SBML species object
            
        Returns:
            BiGG metabolite ID or None
        """
        annotation = self._get_annotation(species)
        if not annotation:
            return None
        
        return self._extract_bigg_from_urn(annotation)
    
    def _get_annotation(self, species) -> Optional[str]:
        """
        Get annotation string from SBML species.
        
        SBML species may have annotations in different fields:
        - annotation: Raw SBML annotation XML
        - annotation_text: Parsed annotation string
        - cv_terms: Controlled vocabulary terms
        
        This method extracts annotation in a format-agnostic way.
        
        Args:
            species: SBML species object
            
        Returns:
            Annotation string or None
        """
        # Try common annotation fields
        annotation_fields = [
            'annotation_text',  # Pre-parsed annotation
            'annotation',       # Raw XML annotation
            'cv_terms',         # Controlled vocabulary terms
        ]
        
        for field in annotation_fields:
            if hasattr(species, field):
                annotation = getattr(species, field)
                if annotation:
                    # Convert to string if needed
                    if not isinstance(annotation, str):
                        annotation = str(annotation)
                    return annotation
        
        # No annotation found
        return None
    
    def map_pathway_species(
        self,
        pathway_data
    ) -> Dict[str, Optional[str]]:
        """
        Map all species in a PathwayData object.
        
        Convenience method for batch mapping.
        
        Args:
            pathway_data: PathwayData object with species list
            
        Returns:
            Dict mapping species_id → KEGG compound ID
        """
        if not hasattr(pathway_data, 'species'):
            self.logger.warning("PathwayData has no species attribute")
            return {}
        
        return self.map_species_list(pathway_data.species)
