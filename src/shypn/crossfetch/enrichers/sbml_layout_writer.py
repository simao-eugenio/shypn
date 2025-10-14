"""
SBML Layout Extension Writer

Writes coordinate data to SBML Layout extension structures.
Handles creation of layout elements conforming to SBML Layout package specification.

Author: Shypn Development Team
Date: October 2025
"""

import logging
from typing import Dict, Optional


class SBMLLayoutWriter:
    """Writes coordinate data to SBML Layout extension.
    
    Creates proper SBML Layout package structures including:
    - Layout definition
    - Compartment glyphs
    - Species glyphs with bounding boxes
    - Reaction glyphs with curves
    """
    
    def __init__(self):
        """Initialize layout writer."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def write_layout(
        self,
        model,
        species_coords: Dict[str, Dict],
        reaction_coords: Optional[Dict[str, Dict]] = None,
        layout_id: str = "kegg_layout_1",
        layout_name: str = "KEGG Coordinates"
    ) -> bool:
        """Write coordinate data to SBML Layout extension.
        
        Args:
            model: SBML Model object (from libsbml)
            species_coords: Mapping of {sbml_species_id: {'x': float, 'y': float, ...}}
            reaction_coords: Optional mapping of reaction coordinates
            layout_id: ID for the layout element
            layout_name: Human-readable name for the layout
        
        Returns:
            True if layout written successfully, False otherwise
        """
        try:
            import libsbml
            
            # Enable Layout plugin
            document = model.getSBMLDocument()
            document.enablePackage(
                libsbml.LayoutExtension.getXmlnsL3V1V1(),
                'layout',
                True
            )
            
            # Get layout plugin for model
            mplugin = model.getPlugin('layout')
            if not mplugin:
                self.logger.error("Failed to get Layout plugin for model")
                return False
            
            # Create new layout
            layout = mplugin.createLayout()
            layout.setId(layout_id)
            layout.setName(layout_name)
            
            # Calculate canvas dimensions
            canvas_dims = self._calculate_canvas_dimensions(
                species_coords,
                reaction_coords
            )
            layout.setDimensions(
                libsbml.Dimensions(
                    libsbml.LayoutPkgNamespaces(),
                    canvas_dims['width'],
                    canvas_dims['height']
                )
            )
            
            # Add species glyphs
            species_count = self._add_species_glyphs(
                layout,
                model,
                species_coords
            )
            
            # Add reaction glyphs (if coordinates provided)
            reaction_count = 0
            if reaction_coords:
                reaction_count = self._add_reaction_glyphs(
                    layout,
                    model,
                    reaction_coords
                )
            
            self.logger.info(
                f"Successfully wrote layout with {species_count} species glyphs "
                f"and {reaction_count} reaction glyphs"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write layout: {e}", exc_info=True)
            return False
    
    def _calculate_canvas_dimensions(
        self,
        species_coords: Dict,
        reaction_coords: Optional[Dict]
    ) -> Dict[str, float]:
        """Calculate canvas dimensions from coordinate data.
        
        Args:
            species_coords: Species coordinate mappings
            reaction_coords: Optional reaction coordinate mappings
        
        Returns:
            Dictionary with 'width' and 'height' keys
        """
        max_x = max_y = 0.0
        
        # Check species coordinates
        for coords in species_coords.values():
            x = coords.get('x', 0) + coords.get('width', 50)
            y = coords.get('y', 0) + coords.get('height', 20)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        
        # Check reaction coordinates if present
        if reaction_coords:
            for coords in reaction_coords.values():
                x = coords.get('x', 0) + coords.get('width', 30)
                y = coords.get('y', 0) + coords.get('height', 30)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        # Add padding
        padding = 50.0
        return {
            'width': max_x + padding,
            'height': max_y + padding
        }
    
    def _add_species_glyphs(
        self,
        layout,
        model,
        species_coords: Dict[str, Dict]
    ) -> int:
        """Add species glyphs to layout.
        
        Args:
            layout: SBML Layout object
            model: SBML Model object
            species_coords: Species coordinate mappings
        
        Returns:
            Number of glyphs added
        """
        import libsbml
        
        count = 0
        for sbml_id, coords in species_coords.items():
            species = model.getSpecies(sbml_id)
            if not species:
                self.logger.warning(f"Species {sbml_id} not found in model")
                continue
            
            # Create species glyph
            glyph = layout.createSpeciesGlyph()
            glyph.setId(f"SpeciesGlyph_{sbml_id}")
            glyph.setSpeciesId(sbml_id)
            
            # Set bounding box
            x = coords.get('x', 0)
            y = coords.get('y', 0)
            width = coords.get('width', 50)
            height = coords.get('height', 20)
            
            bbox = libsbml.BoundingBox(
                libsbml.LayoutPkgNamespaces(),
                f"bb_{sbml_id}",
                x, y, 0.0,  # z = 0 for 2D
                width, height, 0.0
            )
            glyph.setBoundingBox(bbox)
            
            count += 1
        
        return count
    
    def _add_reaction_glyphs(
        self,
        layout,
        model,
        reaction_coords: Dict[str, Dict]
    ) -> int:
        """Add reaction glyphs to layout.
        
        Args:
            layout: SBML Layout object
            model: SBML Model object
            reaction_coords: Reaction coordinate mappings
        
        Returns:
            Number of glyphs added
        """
        import libsbml
        
        count = 0
        for sbml_id, coords in reaction_coords.items():
            reaction = model.getReaction(sbml_id)
            if not reaction:
                self.logger.warning(f"Reaction {sbml_id} not found in model")
                continue
            
            # Create reaction glyph
            glyph = layout.createReactionGlyph()
            glyph.setId(f"ReactionGlyph_{sbml_id}")
            glyph.setReactionId(sbml_id)
            
            # Set bounding box (center point)
            x = coords.get('x', 0)
            y = coords.get('y', 0)
            width = coords.get('width', 30)
            height = coords.get('height', 30)
            
            bbox = libsbml.BoundingBox(
                libsbml.LayoutPkgNamespaces(),
                f"bb_rxn_{sbml_id}",
                x, y, 0.0,
                width, height, 0.0
            )
            glyph.setBoundingBox(bbox)
            
            # TODO: Add species reference glyphs for substrates/products
            # This requires mapping reaction participants to species glyphs
            
            count += 1
        
        return count
