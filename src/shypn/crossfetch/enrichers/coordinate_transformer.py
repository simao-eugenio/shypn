"""
Coordinate System Transformer

Transforms coordinates between different coordinate systems.
Handles conversion from screen/image coordinates (top-left origin) to 
Cartesian coordinates (bottom-left origin, first quadrant).

Author: Shypn Development Team
Date: October 2025
"""

import logging
from typing import Dict, List, Optional, Tuple


class CoordinateTransformer:
    """Transforms coordinates between different coordinate systems.
    
    Key Systems:
    - Screen/Image: Origin (0,0) at top-left, Y increases downward
    - Cartesian: Origin (0,0) at bottom-left, Y increases upward (first quadrant)
    
    KEGG KGML uses screen coordinates, but Shypn uses Cartesian coordinates.
    """
    
    def __init__(self):
        """Initialize coordinate transformer."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def screen_to_cartesian(
        self,
        coords: Dict[str, float],
        canvas_height: float
    ) -> Dict[str, float]:
        """Convert screen coordinates to Cartesian coordinates.
        
        Screen system: (0,0) at top-left, Y down
        Cartesian system: (0,0) at bottom-left, Y up (first quadrant)
        
        Transformation:
            x_cartesian = x_screen
            y_cartesian = canvas_height - y_screen
        
        Args:
            coords: Dictionary with 'x', 'y' keys (and optionally 'width', 'height')
            canvas_height: Total height of the canvas/viewport
        
        Returns:
            Transformed coordinates in Cartesian system
        """
        x = coords.get('x', 0.0)
        y = coords.get('y', 0.0)
        
        # Transform Y coordinate
        y_cartesian = canvas_height - y
        
        # If height is provided, adjust for element height
        # In screen coords: y is top edge
        # In Cartesian coords: y should be bottom edge
        if 'height' in coords:
            y_cartesian -= coords['height']
        
        result = {
            'x': x,
            'y': y_cartesian
        }
        
        # Preserve other dimensions
        if 'width' in coords:
            result['width'] = coords['width']
        if 'height' in coords:
            result['height'] = coords['height']
        
        return result
    
    def cartesian_to_screen(
        self,
        coords: Dict[str, float],
        canvas_height: float
    ) -> Dict[str, float]:
        """Convert Cartesian coordinates to screen coordinates.
        
        Inverse of screen_to_cartesian.
        
        Args:
            coords: Dictionary with 'x', 'y' keys in Cartesian system
            canvas_height: Total height of the canvas/viewport
        
        Returns:
            Transformed coordinates in screen system
        """
        x = coords.get('x', 0.0)
        y = coords.get('y', 0.0)
        
        # If height is provided, adjust for element height
        if 'height' in coords:
            y += coords['height']
        
        # Transform Y coordinate
        y_screen = canvas_height - y
        
        result = {
            'x': x,
            'y': y_screen
        }
        
        # Preserve other dimensions
        if 'width' in coords:
            result['width'] = coords['width']
        if 'height' in coords:
            result['height'] = coords['height']
        
        return result
    
    def transform_species_coordinates(
        self,
        species_data: List[Dict],
        canvas_height: float
    ) -> List[Dict]:
        """Transform species coordinate data from screen to Cartesian.
        
        Args:
            species_data: List of species dicts with coordinate info
            canvas_height: Canvas height for transformation
        
        Returns:
            List of species dicts with transformed coordinates
        """
        transformed = []
        
        for species in species_data:
            transformed_species = species.copy()
            
            # Extract coordinate info
            coords = {
                'x': species.get('x', 0),
                'y': species.get('y', 0),
                'width': species.get('width', 50),
                'height': species.get('height', 20)
            }
            
            # Transform to Cartesian
            cartesian_coords = self.screen_to_cartesian(coords, canvas_height)
            
            # Update species data
            transformed_species.update(cartesian_coords)
            transformed.append(transformed_species)
        
        self.logger.debug(
            f"Transformed {len(transformed)} species coordinates "
            f"(canvas_height={canvas_height})"
        )
        
        return transformed
    
    def transform_reaction_coordinates(
        self,
        reaction_data: List[Dict],
        canvas_height: float
    ) -> List[Dict]:
        """Transform reaction coordinate data from screen to Cartesian.
        
        Args:
            reaction_data: List of reaction dicts with coordinate info
            canvas_height: Canvas height for transformation
        
        Returns:
            List of reaction dicts with transformed coordinates
        """
        transformed = []
        
        for reaction in reaction_data:
            transformed_reaction = reaction.copy()
            
            # Extract coordinate info
            coords = {
                'x': reaction.get('x', 0),
                'y': reaction.get('y', 0),
                'width': reaction.get('width', 30),
                'height': reaction.get('height', 30)
            }
            
            # Transform to Cartesian
            cartesian_coords = self.screen_to_cartesian(coords, canvas_height)
            
            # Update reaction data
            transformed_reaction.update(cartesian_coords)
            transformed.append(transformed_reaction)
        
        self.logger.debug(
            f"Transformed {len(transformed)} reaction coordinates "
            f"(canvas_height={canvas_height})"
        )
        
        return transformed
    
    def calculate_canvas_height(
        self,
        data: List[Dict]
    ) -> float:
        """Calculate canvas height from coordinate data.
        
        Finds the maximum Y coordinate + height to determine canvas bounds.
        
        Args:
            data: List of elements with 'y' and optionally 'height' keys
        
        Returns:
            Maximum canvas height needed
        """
        max_y = 0.0
        
        for item in data:
            y = item.get('y', 0)
            height = item.get('height', 0)
            max_y = max(max_y, y + height)
        
        # Add padding
        padding = 50.0
        canvas_height = max_y + padding
        
        self.logger.debug(f"Calculated canvas height: {canvas_height}")
        
        return canvas_height
