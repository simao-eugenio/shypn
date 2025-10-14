"""
Coordinate Enricher

Enriches SBML with layout coordinates from KEGG pathway maps.
Adds SBML Layout extension with species and reaction positions.
Uses Cartesian coordinate system (first quadrant, origin at bottom-left).

Author: Shypn Development Team
Date: October 2025
"""

import logging
from typing import Dict, List, Optional

from .base_enricher import EnricherBase, EnrichmentResult, EnrichmentChange
from .sbml_id_mapper import SBMLIDMapper
from .sbml_layout_writer import SBMLLayoutWriter
from .coordinate_transformer import CoordinateTransformer


class CoordinateEnricher(EnricherBase):
    """Enriches SBML with coordinate data from KEGG pathways.
    
    Takes coordinate data from KEGG KGML and writes it to the
    SBML Layout extension, enabling visual representation of
    the pathway using the original KEGG layout.
    
    Key Features:
    - Converts KEGG screen coordinates to Cartesian (first quadrant)
    - Maps KEGG IDs to SBML species/reaction IDs
    - Writes SBML Layout extension conforming to specification
    """
    
    def __init__(self):
        """Initialize coordinate enricher with helper components."""
        super().__init__("CoordinateEnricher")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize helper components
        self.id_mapper = SBMLIDMapper()
        self.layout_writer = SBMLLayoutWriter()
        self.transformer = CoordinateTransformer()
    
    def can_enrich(self, data_type: str) -> bool:
        """Check if this enricher can handle the given data type.
        
        Args:
            data_type: Type of data to enrich
        
        Returns:
            True if data_type is 'coordinates' or 'layout'
        """
        return data_type.lower() in ['coordinates', 'layout', 'kgml']
    
    def apply(
        self,
        pathway,
        fetch_result,
        **options
    ) -> EnrichmentResult:
        """Apply coordinate enrichment to pathway.
        
        Args:
            pathway: Pathway object containing SBML model
            fetch_result: FetchResult from KEGGFetcher with coordinate data
            **options: Additional options (e.g., coordinate_system='cartesian')
        
        Returns:
            EnrichmentResult with changes and statistics
        """
        changes = []
        
        try:
            import libsbml
            
            # Extract coordinate data from fetch result
            coord_data = fetch_result.data
            if not coord_data:
                return EnrichmentResult(
                    success=False,
                    changes=[],
                    message="No coordinate data in fetch result"
                )
            
            species_data = coord_data.get('species', [])
            reaction_data = coord_data.get('reactions', [])
            
            if not species_data and not reaction_data:
                return EnrichmentResult(
                    success=False,
                    changes=[],
                    message="No species or reaction coordinates found"
                )
            
            # Get SBML model from pathway
            model = self._get_model_from_pathway(pathway)
            if not model:
                return EnrichmentResult(
                    success=False,
                    changes=[],
                    message="Failed to get SBML model from pathway"
                )
            
            # Transform coordinates from screen to Cartesian system
            canvas_height = self.transformer.calculate_canvas_height(
                species_data + reaction_data
            )
            
            cartesian_species = self.transformer.transform_species_coordinates(
                species_data,
                canvas_height
            )
            
            cartesian_reactions = self.transformer.transform_reaction_coordinates(
                reaction_data,
                canvas_height
            )
            
            # Map external IDs to SBML IDs
            species_mapping = self.id_mapper.map_species_ids(
                model,
                cartesian_species
            )
            
            reaction_mapping = self.id_mapper.map_reaction_ids(
                model,
                cartesian_reactions
            )
            
            # Write layout extension
            success = self.layout_writer.write_layout(
                model,
                species_mapping,
                reaction_mapping,
                layout_id="kegg_layout_1",
                layout_name="KEGG Pathway Coordinates"
            )
            
            if not success:
                return EnrichmentResult(
                    success=False,
                    changes=[],
                    message="Failed to write SBML Layout extension"
                )
            
            # Record changes
            changes.append(
                EnrichmentChange(
                    element_type='layout',
                    element_id='kegg_layout_1',
                    change_type='add',
                    description=f"Added SBML Layout with {len(species_mapping)} species "
                               f"and {len(reaction_mapping)} reaction glyphs"
                )
            )
            
            self.logger.info(
                f"Successfully enriched pathway with coordinates: "
                f"{len(species_mapping)} species, {len(reaction_mapping)} reactions"
            )
            
            return EnrichmentResult(
                success=True,
                changes=changes,
                message=f"Added layout with {len(species_mapping) + len(reaction_mapping)} glyphs",
                statistics={
                    'species_glyphs': len(species_mapping),
                    'reaction_glyphs': len(reaction_mapping),
                    'canvas_height': canvas_height
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to apply coordinate enrichment: {e}", exc_info=True)
            return EnrichmentResult(
                success=False,
                changes=changes,
                message=f"Error during enrichment: {str(e)}"
            )
    
    def validate(
        self,
        pathway,
        fetch_result
    ) -> tuple[bool, List[str]]:
        """Validate that coordinate data is suitable for enrichment.
        
        Args:
            pathway: Pathway object to enrich
            fetch_result: FetchResult containing coordinate data
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check fetch result
        if not fetch_result or not fetch_result.success:
            return False, ["Fetch result is invalid or unsuccessful"]
        
        # Check data structure
        coord_data = fetch_result.data
        if not isinstance(coord_data, dict):
            return False, ["Coordinate data is not a dictionary"]
        
        species_data = coord_data.get('species', [])
        reaction_data = coord_data.get('reactions', [])
        
        if not species_data and not reaction_data:
            return False, ["No species or reaction coordinate data found"]
        
        # Validate species data
        for i, species in enumerate(species_data):
            if 'x' not in species or 'y' not in species:
                warnings.append(f"Species at index {i} missing x/y coordinates")
        
        # Validate reaction data
        for i, reaction in enumerate(reaction_data):
            if 'x' not in reaction or 'y' not in reaction:
                warnings.append(f"Reaction at index {i} missing x/y coordinates")
        
        # Check pathway has SBML model
        try:
            model = self._get_model_from_pathway(pathway)
            if not model:
                return False, ["Pathway does not contain valid SBML model"]
        except Exception as e:
            return False, [f"Failed to access pathway model: {str(e)}"]
        
        is_valid = len(warnings) < len(species_data + reaction_data) * 0.5
        
        return is_valid, warnings
    
    def _get_model_from_pathway(self, pathway):
        """Extract SBML model from pathway object.
        
        Args:
            pathway: Pathway object (may have different structures)
        
        Returns:
            libsbml.Model object or None
        """
        import libsbml
        
        # Case 1: Pathway has direct model attribute
        if hasattr(pathway, 'model') and pathway.model:
            return pathway.model
        
        # Case 2: Pathway has sbml_document
        if hasattr(pathway, 'sbml_document'):
            return pathway.sbml_document.getModel()
        
        # Case 3: Pathway has sbml_string
        if hasattr(pathway, 'sbml_string'):
            document = libsbml.readSBMLFromString(pathway.sbml_string)
            return document.getModel() if document else None
        
        # Case 4: Pathway IS the model
        if isinstance(pathway, libsbml.Model):
            return pathway
        
        self.logger.error("Failed to extract SBML model from pathway object")
        return None
