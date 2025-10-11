"""Layout optimization processor.

Reduces overlaps between Petri net elements using force-directed layout
refinement. Preserves the overall structure from the pathway image while
improving spacing.
"""

from typing import Optional, List, Tuple, Dict
import logging
import math

from shypn.pathway.base import PostProcessorBase, ProcessorError


logger = logging.getLogger(__name__)


class LayoutOptimizer(PostProcessorBase):
    """Optimize layout to reduce overlaps.
    
    Uses force-directed algorithm to push apart overlapping elements
    while maintaining attraction to original positions (from pathway image).
    
    Algorithm:
    1. Store original positions for each element
    2. Build spatial grid for efficient overlap detection
    3. For each iteration:
       a. Detect overlapping pairs using spatial grid
       b. Calculate repulsive forces between overlapping elements
       c. Calculate attractive forces to original positions
       d. Apply forces to update positions
       e. Check convergence (max movement < threshold)
    4. Stop when converged or max iterations reached
    
    Example:
        from shypn.pathway.layout_optimizer import LayoutOptimizer
        from shypn.pathway.options import EnhancementOptions
        
        options = EnhancementOptions(
            layout_min_spacing=80.0,
            layout_max_iterations=50
        )
        
        optimizer = LayoutOptimizer(options)
        enhanced_document = optimizer.process(document, pathway)
        
        stats = optimizer.get_stats()
        print(f"Overlaps before: {stats['overlaps_before']}")
        print(f"Overlaps after: {stats['overlaps_after']}")
        print(f"Iterations: {stats['iterations']}")
    """
    
    def __init__(self, options: Optional['EnhancementOptions'] = None):
        """Initialize layout optimizer.
        
        Args:
            options: Enhancement options with layout parameters.
        """
        super().__init__(options)
        self.logger = logging.getLogger(f"{__name__}.LayoutOptimizer")
    
    def get_name(self) -> str:
        """Return processor name."""
        return "Layout Optimizer"
    
    def is_applicable(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> bool:
        """Check if layout optimization is applicable.
        
        Requires:
            - Layout optimization enabled
            - Document has objects to optimize
        """
        # Check if enabled
        if self.options and not self.options.enable_layout_optimization:
            return False
        
        # Check if document has objects
        if not document.places and not document.transitions:
            return False
        
        return True
    
    def _get_bounding_box(self, obj) -> Tuple[float, float, float, float]:
        """Get bounding box for an object (min_x, min_y, max_x, max_y)."""
        if hasattr(obj, 'radius'):  # Place
            return (
                obj.x - obj.radius,
                obj.y - obj.radius,
                obj.x + obj.radius,
                obj.y + obj.radius
            )
        else:  # Transition
            half_width = obj.width / 2
            half_height = obj.height / 2
            return (
                obj.x - half_width,
                obj.y - half_height,
                obj.x + half_width,
                obj.y + half_height
            )
    
    def _boxes_overlap(self, box1: Tuple[float, float, float, float],
                       box2: Tuple[float, float, float, float],
                       min_spacing: float = 0.0) -> bool:
        """Check if two bounding boxes overlap (with optional minimum spacing)."""
        min_x1, min_y1, max_x1, max_y1 = box1
        min_x2, min_y2, max_x2, max_y2 = box2
        
        # Add spacing buffer
        min_x1 -= min_spacing
        min_y1 -= min_spacing
        max_x1 += min_spacing
        max_y1 += min_spacing
        
        # Check overlap
        return not (max_x1 < min_x2 or max_x2 < min_x1 or
                   max_y1 < min_y2 or max_y2 < min_y1)
    
    def _calculate_overlap_amount(self, box1: Tuple[float, float, float, float],
                                   box2: Tuple[float, float, float, float]) -> float:
        """Calculate overlap amount between two boxes (returns overlap area)."""
        min_x1, min_y1, max_x1, max_y1 = box1
        min_x2, min_y2, max_x2, max_y2 = box2
        
        # Calculate overlap dimensions
        overlap_x = max(0, min(max_x1, max_x2) - max(min_x1, min_x2))
        overlap_y = max(0, min(max_y1, max_y2) - max(min_y1, min_y2))
        
        return overlap_x * overlap_y
    
    def _detect_overlaps(self, objects: List, min_spacing: float) -> List[Tuple]:
        """Detect overlapping object pairs.
        
        Returns:
            List of (obj1, obj2, overlap_amount) tuples.
        """
        overlaps = []
        
        # Simple O(n²) check - could use spatial grid for large datasets
        for i, obj1 in enumerate(objects):
            box1 = self._get_bounding_box(obj1)
            for obj2 in objects[i+1:]:
                box2 = self._get_bounding_box(obj2)
                if self._boxes_overlap(box1, box2, min_spacing):
                    overlap_amount = self._calculate_overlap_amount(box1, box2)
                    overlaps.append((obj1, obj2, overlap_amount))
        
        return overlaps
    
    def _calculate_repulsive_force(self, obj1, obj2, overlap_amount: float,
                                    repulsion_strength: float) -> Tuple[float, float]:
        """Calculate repulsive force vector from obj2 to obj1.
        
        Returns:
            (force_x, force_y) tuple.
        """
        # Vector from obj2 to obj1
        dx = obj1.x - obj2.x
        dy = obj1.y - obj2.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 0.1:  # Avoid division by zero
            # If objects are at same position, push in random direction
            dx = 1.0
            dy = 0.0
            distance = 1.0
        
        # Normalize
        dx /= distance
        dy /= distance
        
        # Force magnitude proportional to square root of overlap (reduce sensitivity)
        # Using sqrt because overlap_amount is area (pixels²)
        force_magnitude = repulsion_strength * math.sqrt(overlap_amount)
        
        return (dx * force_magnitude, dy * force_magnitude)
    
    def _calculate_attractive_force(self, obj, original_x: float, original_y: float,
                                      attraction_strength: float) -> Tuple[float, float]:
        """Calculate attractive force pulling object back to original position.
        
        Returns:
            (force_x, force_y) tuple.
        """
        dx = original_x - obj.x
        dy = original_y - obj.y
        
        # Force proportional to distance from original position
        force_x = dx * attraction_strength
        force_y = dy * attraction_strength
        
        return (force_x, force_y)
    
    def process(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> 'DocumentModel':
        """Optimize layout to reduce overlaps.
        
        Args:
            document: Document to optimize.
            pathway: Pathway data for context.
        
        Returns:
            Document with optimized layout.
        """
        self.reset_stats()
        self.validate_inputs(document, pathway)
        
        # Get parameters from options
        min_spacing = self.options.layout_min_spacing if self.options else 60.0
        max_iterations = self.options.layout_max_iterations if self.options else 100
        repulsion_strength = self.options.layout_repulsion_strength if self.options else 10.0  # Reduced from 1000
        attraction_strength = self.options.layout_attraction_strength if self.options else 0.1
        convergence_threshold = self.options.layout_convergence_threshold if self.options else 1.0
        
        # Combine all objects
        all_objects = list(document.places) + list(document.transitions)
        
        if not all_objects:
            self.stats = {'overlaps_before': 0, 'overlaps_after': 0, 'iterations': 0}
            return document
        
        # Store original positions
        original_positions = {id(obj): (obj.x, obj.y) for obj in all_objects}
        
        # Detect initial overlaps
        initial_overlaps = self._detect_overlaps(all_objects, min_spacing)
        overlaps_before = len(initial_overlaps)
        
        # Iterative refinement
        iteration = 0
        converged = False
        
        for iteration in range(max_iterations):
            # Detect overlaps
            overlaps = self._detect_overlaps(all_objects, min_spacing)
            
            if not overlaps:
                converged = True
                break
            
            # Calculate forces for each object
            forces = {id(obj): [0.0, 0.0] for obj in all_objects}
            
            # Repulsive forces from overlaps
            for obj1, obj2, overlap_amount in overlaps:
                force_x, force_y = self._calculate_repulsive_force(
                    obj1, obj2, overlap_amount, repulsion_strength
                )
                forces[id(obj1)][0] += force_x
                forces[id(obj1)][1] += force_y
                forces[id(obj2)][0] -= force_x
                forces[id(obj2)][1] -= force_y
            
            # Attractive forces to original positions
            for obj in all_objects:
                orig_x, orig_y = original_positions[id(obj)]
                attr_x, attr_y = self._calculate_attractive_force(
                    obj, orig_x, orig_y, attraction_strength
                )
                forces[id(obj)][0] += attr_x
                forces[id(obj)][1] += attr_y
            
            # Apply forces and track maximum movement
            max_movement = 0.0
            for obj in all_objects:
                force_x, force_y = forces[id(obj)]
                obj.x += force_x
                obj.y += force_y
                
                movement = math.sqrt(force_x*force_x + force_y*force_y)
                max_movement = max(max_movement, movement)
            
            # Check convergence
            if max_movement < convergence_threshold:
                converged = True
                break
        
        # Final overlap count
        final_overlaps = self._detect_overlaps(all_objects, min_spacing)
        overlaps_after = len(final_overlaps)
        
        # Count moved elements
        elements_moved = 0
        total_movement = 0.0
        max_element_movement = 0.0
        
        for obj in all_objects:
            orig_x, orig_y = original_positions[id(obj)]
            dx = obj.x - orig_x
            dy = obj.y - orig_y
            movement = math.sqrt(dx*dx + dy*dy)
            
            if movement > 0.1:  # Threshold for "moved"
                elements_moved += 1
                total_movement += movement
                max_element_movement = max(max_element_movement, movement)
        
        # Store statistics
        self.stats = {
            'overlaps_before': overlaps_before,
            'overlaps_after': overlaps_after,
            'overlaps_resolved': overlaps_before - overlaps_after,
            'elements_moved': elements_moved,
            'total_elements': len(all_objects),
            'max_movement': max_element_movement,
            'avg_movement': total_movement / elements_moved if elements_moved > 0 else 0.0,
            'iterations': iteration + 1,
            'converged': converged,
            'implemented': True
        }
        
        return document
