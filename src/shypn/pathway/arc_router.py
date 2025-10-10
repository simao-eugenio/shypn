"""Arc routing processor for curved arcs.

Adds control points to arcs for Bezier curves, handles parallel arcs,
and routes arcs around obstacles.

Implementation Strategy:
    1. Group parallel arcs (same source/target pair)
    2. Calculate perpendicular offset for parallel arcs
    3. Detect obstacles along arc path
    4. Generate control points for smooth curves
    5. Store control points in Arc objects
"""

from typing import Optional, List, Tuple, Dict, Set
import logging
import math

from shypn.pathway.base import PostProcessorBase


logger = logging.getLogger(__name__)


class ArcRouter(PostProcessorBase):
    """Route arcs with curved paths and handle parallel arcs.
    
    This processor enhances arc rendering by adding control points
    for Bezier curves, especially useful for parallel arcs and
    when avoiding obstacles.
    
    Algorithm:
        1. Group arcs by (source, target) pairs
        2. For parallel arcs, calculate perpendicular offsets
        3. For each arc, detect obstacles along straight path
        4. Generate control points for smooth routing
        5. Store control points in arc.is_curved and control_offset_x/y
    
    Example:
        from shypn.pathway.arc_router import ArcRouter
        from shypn.pathway.options import EnhancementOptions
        
        options = EnhancementOptions(
            arc_curve_style='curved',
            arc_parallel_offset=30.0
        )
        
        router = ArcRouter(options)
        enhanced_document = router.process(document)
        
        # Arcs now have curved paths
        for arc in document.arcs:
            if arc.is_curved:
                print(f"Arc {arc.id} is curved with offset ({arc.control_offset_x}, {arc.control_offset_y})")
    """
    
    def __init__(self, options: Optional['EnhancementOptions'] = None):
        """Initialize arc router.
        
        Args:
            options: Enhancement options with arc routing parameters.
        """
        super().__init__(options)
        self.logger = logging.getLogger(f"{__name__}.ArcRouter")
    
    def get_name(self) -> str:
        """Return processor name."""
        return "Arc Router"
    
    def is_applicable(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> bool:
        """Check if arc routing is applicable.
        
        Requires:
            - At least 1 arc
            - Arc routing enabled in options
        """
        # Check if enabled
        if self.options and not self.options.enable_arc_routing:
            return False
        
        # Check minimum arcs
        if len(document.arcs) < 1:
            self.logger.debug("Not applicable: no arcs to route")
            return False
        
        return True
    
    def _group_parallel_arcs(self, arcs: List) -> Dict[Tuple, List]:
        """Group arcs by (source_id, source_type, target_id, target_type) tuples.
        
        Parallel arcs are those with the same source and target objects.
        Bidirectional arcs (A→B and B→A) are considered distinct groups
        because they may have different types (Place→Transition vs Transition→Place).
        
        Args:
            arcs: List of Arc objects
            
        Returns:
            dict: Mapping from (source_id, source_type, target_id, target_type) to list of Arc objects
        """
        from shypn.netobjs.place import Place
        
        groups = {}
        for arc in arcs:
            # Use both ID and type to distinguish between Place and Transition
            source_type = 'place' if isinstance(arc.source, Place) else 'transition'
            target_type = 'place' if isinstance(arc.target, Place) else 'transition'
            key = (arc.source.id, source_type, arc.target.id, target_type)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(arc)
        return groups
    
    def _calculate_perpendicular_offset(self, arc, arc_index: int, total_parallel: int,
                                       offset_amount: float) -> Tuple[float, float]:
        """Calculate perpendicular offset for parallel arc.
        
        For N parallel arcs, distributes them symmetrically around the straight line:
        - N=1: No offset (0)
        - N=2: Offsets of -offset/2 and +offset/2
        - N=3: Offsets of -offset, 0, +offset
        - N=4: Offsets of -1.5*offset, -0.5*offset, +0.5*offset, +1.5*offset
        
        Args:
            arc: Arc object
            arc_index: Index of this arc in parallel group (0-based)
            total_parallel: Total number of parallel arcs
            offset_amount: Base offset distance (from options.arc_parallel_offset)
            
        Returns:
            tuple: (offset_x, offset_y) perpendicular offset from arc midpoint
        """
        if total_parallel == 1:
            return (0.0, 0.0)
        
        # Calculate multiplier for this arc's position
        # Center the distribution around 0
        if total_parallel % 2 == 0:
            # Even number: -1.5, -0.5, +0.5, +1.5 for N=4
            multiplier = (arc_index - (total_parallel - 1) / 2)
        else:
            # Odd number: -1, 0, +1 for N=3
            multiplier = (arc_index - total_parallel // 2)
        
        # Calculate arc direction (source → target)
        dx = arc.target.x - arc.source.x
        dy = arc.target.y - arc.source.y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1e-6:
            return (0.0, 0.0)  # Degenerate arc
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Perpendicular direction (90° counterclockwise rotation)
        # For rightward arc (1, 0), this gives upward (0, 1)
        # For downward arc (0, 1), this gives leftward (-1, 0)
        perp_x = -dy
        perp_y = dx
        
        # Calculate offset
        offset_distance = multiplier * offset_amount
        offset_x = perp_x * offset_distance
        offset_y = perp_y * offset_distance
        
        return (offset_x, offset_y)
    
    def _detect_obstacles(self, arc, elements: List) -> List:
        """Detect elements (places/transitions) near arc path.
        
        An element is considered an obstacle if it's close to the straight line
        segment between arc source and target, excluding the source and target themselves.
        
        Args:
            arc: Arc object
            elements: List of Place and Transition objects
            
        Returns:
            list: Elements that are obstacles (close to arc path)
        """
        obstacles = []
        
        src_x, src_y = arc.source.x, arc.source.y
        tgt_x, tgt_y = arc.target.x, arc.target.y
        
        clearance = self.options.arc_obstacle_clearance if self.options else 20.0
        
        for elem in elements:
            # Skip source and target
            if elem is arc.source or elem is arc.target:
                continue
            
            # Get element radius (for circular or rectangular bounding)
            if hasattr(elem, 'radius'):  # Place
                elem_radius = elem.radius
            elif hasattr(elem, 'width') and hasattr(elem, 'height'):  # Transition
                # Use half-diagonal as effective radius
                elem_radius = math.sqrt(elem.width**2 + elem.height**2) / 2
            else:
                elem_radius = 20.0  # Default
            
            # Calculate distance from element center to line segment
            dist = self._point_to_segment_distance(
                elem.x, elem.y, src_x, src_y, tgt_x, tgt_y)
            
            # Check if element is close enough to be an obstacle
            if dist < (elem_radius + clearance):
                obstacles.append(elem)
        
        return obstacles
    
    def _point_to_segment_distance(self, px: float, py: float,
                                   x1: float, y1: float,
                                   x2: float, y2: float) -> float:
        """Calculate distance from point to line segment.
        
        Args:
            px, py: Point coordinates
            x1, y1: Segment start
            x2, y2: Segment end
            
        Returns:
            float: Distance from point to closest point on segment
        """
        # Segment vector
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy
        
        if length_sq < 1e-6:
            # Degenerate segment → distance to point
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Parameter t: position of closest point on line (0=start, 1=end)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
        
        # Closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from point to closest point
        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    def _calculate_control_point_for_obstacles(self, arc, obstacles: List) -> Tuple[float, float]:
        """Calculate control point to route arc around obstacles.
        
        Strategy:
        1. Find the closest obstacle to the arc midpoint
        2. Calculate perpendicular offset to route around it
        3. Use clearance distance to determine offset amount
        
        Args:
            arc: Arc object
            obstacles: List of obstacle elements
            
        Returns:
            tuple: (offset_x, offset_y) from arc midpoint
        """
        if not obstacles:
            return (0.0, 0.0)
        
        src_x, src_y = arc.source.x, arc.source.y
        tgt_x, tgt_y = arc.target.x, arc.target.y
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        
        clearance = self.options.arc_obstacle_clearance if self.options else 20.0
        
        # Find closest obstacle to midpoint
        closest_obstacle = None
        closest_dist = float('inf')
        
        for obstacle in obstacles:
            dist = math.sqrt((obstacle.x - mid_x)**2 + (obstacle.y - mid_y)**2)
            if dist < closest_dist:
                closest_dist = dist
                closest_obstacle = obstacle
        
        if closest_obstacle is None:
            return (0.0, 0.0)
        
        # Calculate direction from arc line to obstacle
        # This determines which side to route the arc
        dx_arc = tgt_x - src_x
        dy_arc = tgt_y - src_y
        length_arc = math.sqrt(dx_arc * dx_arc + dy_arc * dy_arc)
        
        if length_arc < 1e-6:
            return (0.0, 0.0)
        
        # Normalize arc direction
        dx_arc /= length_arc
        dy_arc /= length_arc
        
        # Vector from midpoint to obstacle
        dx_obs = closest_obstacle.x - mid_x
        dy_obs = closest_obstacle.y - mid_y
        
        # Cross product determines which side obstacle is on
        # Positive = left side, Negative = right side
        cross = dx_arc * dy_obs - dy_arc * dx_obs
        
        # Perpendicular direction (away from obstacle)
        if cross > 0:
            # Obstacle on left → route right
            perp_x = dy_arc
            perp_y = -dx_arc
        else:
            # Obstacle on right → route left
            perp_x = -dy_arc
            perp_y = dx_arc
        
        # Calculate offset amount
        # Use obstacle radius + clearance as minimum offset
        if hasattr(closest_obstacle, 'radius'):
            obstacle_radius = closest_obstacle.radius
        elif hasattr(closest_obstacle, 'width') and hasattr(closest_obstacle, 'height'):
            obstacle_radius = math.sqrt(closest_obstacle.width**2 + closest_obstacle.height**2) / 2
        else:
            obstacle_radius = 20.0
        
        offset_amount = obstacle_radius + clearance
        
        # Return offset from midpoint
        return (perp_x * offset_amount, perp_y * offset_amount)
    
    def process(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> 'DocumentModel':
        """Route arcs with curved paths.
        
        Args:
            document: Document with arcs to route.
            pathway: Optional pathway data (unused currently).
        
        Returns:
            Enhanced document with curved arcs.
        """
        self.reset_stats()
        self.validate_inputs(document, pathway)
        
        self.logger.info("Starting arc routing...")
        
        # Get configuration
        curve_style = self.options.arc_curve_style if self.options else 'curved'
        parallel_offset = self.options.arc_parallel_offset if self.options else 30.0
        
        # Group parallel arcs
        parallel_groups = self._group_parallel_arcs(document.arcs)
        
        # Track statistics
        total_arcs = len(document.arcs)
        parallel_arc_count = sum(len(group) for group in parallel_groups.values() if len(group) > 1)
        arcs_with_curves = 0
        arcs_with_obstacles = 0
        
        # Collect all elements for obstacle detection
        all_elements = document.places + document.transitions
        
        # Process each group
        for group_key, arcs_in_group in parallel_groups.items():
            num_parallel = len(arcs_in_group)
            
            # Sort arcs by ID for consistent ordering
            arcs_in_group.sort(key=lambda a: a.id)
            
            for arc_index, arc in enumerate(arcs_in_group):
                # Reset arc curve state
                arc.is_curved = False
                arc.control_offset_x = 0.0
                arc.control_offset_y = 0.0
                
                # Check if we should apply curves
                if curve_style == 'straight':
                    continue  # Keep all arcs straight
                
                # Apply parallel arc offset if multiple arcs
                if num_parallel > 1:
                    offset_x, offset_y = self._calculate_perpendicular_offset(
                        arc, arc_index, num_parallel, parallel_offset)
                    
                    arc.is_curved = True
                    arc.control_offset_x = offset_x
                    arc.control_offset_y = offset_y
                    arcs_with_curves += 1
                    continue  # Parallel arc curve applied
                
                # Check for obstacles (only for non-parallel arcs)
                obstacles = self._detect_obstacles(arc, all_elements)
                
                if obstacles:
                    # Calculate control point to avoid obstacles
                    offset_x, offset_y = self._calculate_control_point_for_obstacles(
                        arc, obstacles)
                    
                    arc.is_curved = True
                    arc.control_offset_x = offset_x
                    arc.control_offset_y = offset_y
                    arcs_with_curves += 1
                    arcs_with_obstacles += 1
                    
                    self.logger.debug(
                        f"Arc {arc.id} routed around {len(obstacles)} obstacles "
                        f"with offset ({offset_x:.1f}, {offset_y:.1f})")
        
        # Store statistics
        self.stats = {
            'total_arcs': total_arcs,
            'parallel_arc_groups': sum(1 for group in parallel_groups.values() if len(group) > 1),
            'arcs_in_parallel_groups': parallel_arc_count,
            'arcs_with_curves': arcs_with_curves,
            'arcs_routed_around_obstacles': arcs_with_obstacles,
            'avg_parallel_group_size': (
                parallel_arc_count / max(1, sum(1 for group in parallel_groups.values() if len(group) > 1))
                if parallel_arc_count > 0 else 0.0
            ),
            'implemented': True
        }
        
        self.logger.info(
            f"Arc routing complete: {arcs_with_curves}/{total_arcs} arcs curved, "
            f"{parallel_arc_count} in parallel groups, "
            f"{arcs_with_obstacles} routed around obstacles")
        
        return document
