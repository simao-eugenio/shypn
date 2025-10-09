# Post-Processing Enhancement Plan for KEGG Pathway Import

**Document Version**: 1.0  
**Date**: October 9, 2025  
**Status**: Implementation Plan  
**Purpose**: Design a post-processing pipeline to enhance Petri net mappings after KEGG pathway import

---

## 🎯 Executive Summary

This document outlines a **post-processing enhancement pipeline** that improves Petri net quality after initial KEGG pathway import. The approach leverages visual information (graphics data and optionally pathway images) to optimize layout, enhance arc routing, validate data, and enrich metadata.

**Key Benefits**:
- ✅ Non-invasive: Works as post-processing, preserving existing import pipeline
- ✅ Modular: Pluggable enhancement modules that can be enabled/disabled
- ✅ Incremental: Can be implemented phase-by-phase
- ✅ Backward compatible: Defaults to current behavior if disabled

---

## 📊 Current Import Pipeline Analysis

### Existing Flow

```
KGML XML
   ↓
[kgml_parser.py] → KEGGPathway (data model)
   ↓
[pathway_converter.py] → StandardConversionStrategy
   ↓
[CompoundMapper] → Places (with coordinates from graphics)
[ReactionMapper] → Transitions (positioned between compounds)
[ArcBuilder] → Arcs (with stoichiometry weights)
   ↓
DocumentModel (places, transitions, arcs)
   ↓
[APPLICATION] → Canvas rendering
```

### Current Architecture Strengths

1. **Strategy Pattern**: `ConversionStrategy` base class allows different mapping strategies
2. **Modular Mappers**: Separate `CompoundMapper`, `ReactionMapper`, `ArcBuilder`
3. **Options Object**: `ConversionOptions` for configuration
4. **Clean Separation**: Parsing → Conversion → Model

### Extension Points Identified

1. **Post-conversion hook**: After `StandardConversionStrategy.convert()` returns `DocumentModel`
2. **ConversionOptions**: Can add enhancement flags
3. **PathwayConverter**: Wrapper class where enhancement pipeline can be inserted
4. **DocumentModel**: Mutable object that can be modified in-place

---

## 🏗️ Proposed Post-Processing Architecture

### High-Level Flow

```
KGML XML
   ↓
[EXISTING PIPELINE]
   ↓
DocumentModel (initial)
   ↓
[POST-PROCESSING PIPELINE] ← NEW
   ↓
   ├─ [LayoutOptimizer] → Adjust positions to reduce overlap
   ├─ [ArcRouter] → Add control points for curved arcs
   ├─ [MetadataEnhancer] → Add visual/functional metadata
   └─ [VisualValidator] → Cross-check with pathway image (optional)
   ↓
DocumentModel (enhanced)
   ↓
[APPLICATION]
```

### Design Principles

1. **Pipeline Pattern**: Chain of processors, each enhancing the model
2. **Immutability Option**: Processors can modify in-place or return new model
3. **Configurability**: Each processor can be enabled/disabled via options
4. **Independence**: Processors don't depend on each other (can run in any order)
5. **Idempotency**: Running twice should be safe (detect already processed)

---

## 📐 Module Designs

### 1. PostProcessorBase (Abstract)

```python
from abc import ABC, abstractmethod
from typing import Optional
from shypn.data.canvas.document_model import DocumentModel
from shypn.importer.kegg.models import KEGGPathway

class PostProcessorBase(ABC):
    """Abstract base class for post-processors."""
    
    def __init__(self, enabled: bool = True):
        """Initialize processor.
        
        Args:
            enabled: Whether this processor is active
        """
        self.enabled = enabled
    
    @abstractmethod
    def process(self, document: DocumentModel, 
                pathway: KEGGPathway,
                options: 'EnhancementOptions') -> DocumentModel:
        """Process document model.
        
        Args:
            document: Petri net model to enhance
            pathway: Original KEGG pathway data
            options: Enhancement options
            
        Returns:
            Enhanced DocumentModel (may be modified in-place)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get processor name for logging."""
        pass
```

---

### 2. LayoutOptimizer

**Purpose**: Reduce element overlap by analyzing density and adjusting positions.

#### Algorithm Design

```python
class LayoutOptimizer(PostProcessorBase):
    """Optimize layout to reduce overlap and improve clarity."""
    
    def __init__(self, enabled: bool = True, 
                 min_spacing: float = 60.0,
                 overlap_threshold: float = 0.7):
        """Initialize optimizer.
        
        Args:
            enabled: Enable this processor
            min_spacing: Minimum distance between elements
            overlap_threshold: Overlap ratio to trigger adjustment
        """
        super().__init__(enabled)
        self.min_spacing = min_spacing
        self.overlap_threshold = overlap_threshold
    
    def process(self, document, pathway, options):
        """Optimize element positions."""
        if not self.enabled:
            return document
        
        # Step 1: Build spatial index
        spatial_index = self._build_spatial_index(document)
        
        # Step 2: Detect overlaps
        overlaps = self._detect_overlaps(document, spatial_index)
        
        # Step 3: Resolve overlaps iteratively
        self._resolve_overlaps(document, overlaps, max_iterations=10)
        
        # Step 4: Validate constraints
        self._enforce_connectivity(document)
        
        return document
    
    def _build_spatial_index(self, document):
        """Build R-tree spatial index for fast overlap detection."""
        from rtree import index
        
        idx = index.Index()
        
        # Index all places
        for i, place in enumerate(document.places):
            bbox = self._get_bounding_box(place)
            idx.insert(i, bbox, obj=('place', place))
        
        # Index all transitions
        for i, transition in enumerate(document.transitions):
            bbox = self._get_bounding_box(transition)
            idx.insert(len(document.places) + i, bbox, obj=('transition', transition))
        
        return idx
    
    def _get_bounding_box(self, element):
        """Get bounding box for element (x, y, width, height)."""
        # Place: circle with radius 20
        # Transition: rectangle 40x30
        if hasattr(element, 'marking'):  # Place
            r = 20
            return (element.x - r, element.y - r, element.x + r, element.y + r)
        else:  # Transition
            w, h = 40, 30
            return (element.x - w/2, element.y - h/2, element.x + w/2, element.y + h/2)
    
    def _detect_overlaps(self, document, spatial_index):
        """Detect all overlapping element pairs."""
        overlaps = []
        
        all_elements = [(p, 'place') for p in document.places] + \
                       [(t, 'transition') for t in document.transitions]
        
        for elem, elem_type in all_elements:
            bbox = self._get_bounding_box(elem)
            
            # Find nearby elements
            candidates = list(spatial_index.intersection(bbox, objects=True))
            
            for candidate in candidates:
                other_elem = candidate.object[1]
                if other_elem is elem:
                    continue
                
                # Calculate overlap
                overlap_ratio = self._calculate_overlap(elem, other_elem)
                
                if overlap_ratio > self.overlap_threshold:
                    overlaps.append((elem, other_elem, overlap_ratio))
        
        return overlaps
    
    def _calculate_overlap(self, elem1, elem2):
        """Calculate overlap ratio (0 = no overlap, 1 = full overlap)."""
        bbox1 = self._get_bounding_box(elem1)
        bbox2 = self._get_bounding_box(elem2)
        
        # Calculate intersection area
        x_overlap = max(0, min(bbox1[2], bbox2[2]) - max(bbox1[0], bbox2[0]))
        y_overlap = max(0, min(bbox1[3], bbox2[3]) - max(bbox1[1], bbox2[1]))
        intersection = x_overlap * y_overlap
        
        # Calculate union area
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _resolve_overlaps(self, document, overlaps, max_iterations):
        """Resolve overlaps by adjusting positions."""
        for iteration in range(max_iterations):
            if not overlaps:
                break
            
            # Sort by overlap ratio (resolve worst first)
            overlaps.sort(key=lambda x: x[2], reverse=True)
            
            moved = False
            for elem1, elem2, overlap_ratio in overlaps:
                # Calculate repulsion vector
                dx = elem2.x - elem1.x
                dy = elem2.y - elem1.y
                distance = (dx**2 + dy**2)**0.5
                
                if distance < 0.01:  # Elements at same position
                    dx, dy = 1, 0  # Move horizontally
                    distance = 1
                
                # Normalize and scale by overlap
                force = overlap_ratio * self.min_spacing
                shift_x = (dx / distance) * force
                shift_y = (dy / distance) * force
                
                # Move elements apart
                elem1.x -= shift_x / 2
                elem1.y -= shift_y / 2
                elem2.x += shift_x / 2
                elem2.y += shift_y / 2
                
                moved = True
            
            # Re-detect overlaps
            spatial_index = self._build_spatial_index(document)
            overlaps = self._detect_overlaps(document, spatial_index)
            
            if not moved:
                break
    
    def _enforce_connectivity(self, document):
        """Ensure arcs still connect properly after moves."""
        # Arc endpoints are stored as references, so they auto-update
        # Just validate that no arc is too stretched
        for arc in document.arcs:
            source = arc.source
            target = arc.target
            distance = ((target.x - source.x)**2 + (target.y - source.y)**2)**0.5
            
            # If arc too long, flag for review (or implement constraint-based layout)
            if distance > 500:  # Threshold
                print(f"Warning: Arc {arc.id} is very long ({distance:.0f} pixels)")
    
    def get_name(self):
        return "LayoutOptimizer"
```

#### Key Algorithms

1. **Spatial Indexing**: R-tree for O(log n) overlap queries
2. **Force-Directed Resolution**: Repulsion forces push overlapping elements apart
3. **Iterative Refinement**: Multiple passes until convergence
4. **Constraint Preservation**: Ensure arcs remain valid

---

### 3. ArcRouter

**Purpose**: Enhance arc visualization with curved paths and intelligent routing.

#### Algorithm Design

```python
class ArcRouter(PostProcessorBase):
    """Add control points to arcs for better routing."""
    
    def __init__(self, enabled: bool = True,
                 curve_style: str = 'auto'):
        """Initialize router.
        
        Args:
            enabled: Enable this processor
            curve_style: 'straight', 'curved', 'orthogonal', 'auto'
        """
        super().__init__(enabled)
        self.curve_style = curve_style
    
    def process(self, document, pathway, options):
        """Add control points to arcs."""
        if not self.enabled:
            return document
        
        # Group arcs by source-target pairs (detect parallel arcs)
        arc_groups = self._group_parallel_arcs(document.arcs)
        
        # Route each group
        for group in arc_groups:
            self._route_arc_group(group, document)
        
        return document
    
    def _group_parallel_arcs(self, arcs):
        """Group arcs that connect same source-target pair."""
        from collections import defaultdict
        
        groups = defaultdict(list)
        for arc in arcs:
            # Key: (source_id, target_id)
            key = (arc.source.id, arc.target.id)
            groups[key].append(arc)
        
        return list(groups.values())
    
    def _route_arc_group(self, arcs, document):
        """Route a group of parallel arcs."""
        if len(arcs) == 1:
            # Single arc: simple curve
            self._route_single_arc(arcs[0], document)
        else:
            # Multiple arcs: offset to avoid overlap
            self._route_parallel_arcs(arcs, document)
    
    def _route_single_arc(self, arc, document):
        """Add control point(s) for a single arc."""
        source = arc.source
        target = arc.target
        
        # Calculate arc direction
        dx = target.x - source.x
        dy = target.y - source.y
        distance = (dx**2 + dy**2)**0.5
        
        if distance < 0.01:
            return  # Self-loop (handle separately)
        
        # Check for obstacles between source and target
        obstacles = self._find_obstacles(source, target, document)
        
        if not obstacles:
            # No obstacles: gentle curve
            if self.curve_style in ['curved', 'auto']:
                # Add single control point offset perpendicular to arc
                mid_x = (source.x + target.x) / 2
                mid_y = (source.y + target.y) / 2
                
                # Perpendicular offset (20% of distance)
                offset = distance * 0.2
                perp_x = -dy / distance * offset
                perp_y = dx / distance * offset
                
                arc.control_points = [(mid_x + perp_x, mid_y + perp_y)]
        else:
            # Obstacles: route around them
            path = self._find_path_avoiding_obstacles(source, target, obstacles)
            arc.control_points = path
    
    def _find_obstacles(self, source, target, document):
        """Find elements between source and target."""
        obstacles = []
        
        # Line from source to target
        x1, y1 = source.x, source.y
        x2, y2 = target.x, target.y
        
        # Check all places and transitions
        for place in document.places:
            if place is source or place is target:
                continue
            if self._line_intersects_circle(x1, y1, x2, y2, place.x, place.y, 20):
                obstacles.append(place)
        
        for transition in document.transitions:
            if transition is source or transition is target:
                continue
            if self._line_intersects_rect(x1, y1, x2, y2, 
                                          transition.x - 20, transition.y - 15,
                                          transition.x + 20, transition.y + 15):
                obstacles.append(transition)
        
        return obstacles
    
    def _line_intersects_circle(self, x1, y1, x2, y2, cx, cy, r):
        """Check if line segment intersects circle."""
        # Vector from p1 to p2
        dx = x2 - x1
        dy = y2 - y1
        
        # Vector from p1 to circle center
        fx = cx - x1
        fy = cy - y1
        
        # Project circle center onto line
        t = (fx * dx + fy * dy) / (dx * dx + dy * dy) if (dx * dx + dy * dy) > 0 else 0
        t = max(0, min(1, t))  # Clamp to segment
        
        # Closest point on segment to circle
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from circle center to closest point
        dist = ((cx - closest_x)**2 + (cy - closest_y)**2)**0.5
        
        return dist < r
    
    def _line_intersects_rect(self, x1, y1, x2, y2, rx1, ry1, rx2, ry2):
        """Check if line segment intersects rectangle."""
        # Liang-Barsky algorithm or simple bounding box check
        # Simplified: check if either endpoint inside rect
        def point_in_rect(px, py):
            return rx1 <= px <= rx2 and ry1 <= py <= ry2
        
        if point_in_rect(x1, y1) or point_in_rect(x2, y2):
            return True
        
        # Check line-rect edge intersections (simplified)
        return False  # Placeholder
    
    def _find_path_avoiding_obstacles(self, source, target, obstacles):
        """Find path around obstacles using A* or simple waypoints."""
        # Simplified: offset perpendicular by enough to clear obstacles
        dx = target.x - source.x
        dy = target.y - source.y
        distance = (dx**2 + dy**2)**0.5
        
        # Offset perpendicular
        offset = 80  # Fixed offset
        perp_x = -dy / distance * offset
        perp_y = dx / distance * offset
        
        # Two control points for S-curve
        cp1_x = source.x + dx * 0.33 + perp_x
        cp1_y = source.y + dy * 0.33 + perp_y
        
        cp2_x = source.x + dx * 0.67 + perp_x
        cp2_y = source.y + dy * 0.67 + perp_y
        
        return [(cp1_x, cp1_y), (cp2_x, cp2_y)]
    
    def _route_parallel_arcs(self, arcs, document):
        """Route multiple arcs between same endpoints with offsets."""
        n = len(arcs)
        
        for i, arc in enumerate(arcs):
            # Offset index: ..., -1, 0, 1, ...
            offset_idx = i - n // 2
            
            source = arc.source
            target = arc.target
            
            dx = target.x - source.x
            dy = target.y - source.y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < 0.01:
                continue
            
            # Perpendicular offset scaled by index
            offset = offset_idx * 30  # 30 pixels per arc
            perp_x = -dy / distance * offset
            perp_y = dx / distance * offset
            
            # Control point at midpoint with offset
            mid_x = (source.x + target.x) / 2
            mid_y = (source.y + target.y) / 2
            
            arc.control_points = [(mid_x + perp_x, mid_y + perp_y)]
    
    def get_name(self):
        return "ArcRouter"
```

#### Key Algorithms

1. **Parallel Arc Detection**: Group arcs by source-target pairs
2. **Obstacle Avoidance**: Line-circle/rect intersection tests
3. **Path Planning**: Simple waypoint generation (can upgrade to A*)
4. **Offset Calculation**: Perpendicular vectors for parallel arcs

---

### 4. MetadataEnhancer

**Purpose**: Add functional and visual metadata from KEGG graphics.

```python
class MetadataEnhancer(PostProcessorBase):
    """Enhance elements with metadata from KEGG graphics."""
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def process(self, document, pathway, options):
        """Add metadata to elements."""
        if not self.enabled:
            return document
        
        # Map document elements back to KEGG entries
        entry_map = self._build_entry_map(pathway)
        
        # Enhance places
        for place in document.places:
            self._enhance_place(place, entry_map)
        
        # Enhance transitions
        for transition in document.transitions:
            self._enhance_transition(transition, entry_map)
        
        return document
    
    def _build_entry_map(self, pathway):
        """Build mapping from element IDs to KEGG entries."""
        return pathway.entries  # Already a dict
    
    def _enhance_place(self, place, entry_map):
        """Add metadata to place from KEGG compound."""
        # Extract KEGG ID from place metadata
        if not hasattr(place, 'metadata') or not place.metadata:
            return
        
        kegg_id = place.metadata.get('kegg_id')
        if not kegg_id or kegg_id not in entry_map:
            return
        
        entry = entry_map[kegg_id]
        graphics = entry.graphics
        
        # Add visual properties
        place.metadata.update({
            'graphics': {
                'bgcolor': graphics.bgcolor,
                'fgcolor': graphics.fgcolor,
                'shape': graphics.type,
                'width': graphics.width,
                'height': graphics.height,
            },
            'functional_class': self._classify_compound(entry),
            'kegg_name': entry.name,
            'display_name': graphics.name,
        })
        
        # Optionally set visual properties for rendering
        if hasattr(place, 'color'):
            place.color = graphics.bgcolor
            place.border_color = graphics.fgcolor
    
    def _classify_compound(self, entry):
        """Classify compound by type/role."""
        name = entry.name.lower()
        
        # Common cofactors
        cofactors = ['atp', 'adp', 'nad', 'nadh', 'nadp', 'nadph', 
                     'fad', 'fadh2', 'coa', 'h2o', 'pi']
        for cofactor in cofactors:
            if cofactor in name:
                return 'cofactor'
        
        # Currency metabolites
        currency = ['h+', 'proton', 'h2o', 'water', 'co2']
        for curr in currency:
            if curr in name:
                return 'currency'
        
        return 'metabolite'
    
    def _enhance_transition(self, transition, entry_map):
        """Add metadata to transition from KEGG reaction."""
        # Similar to place enhancement
        if not hasattr(transition, 'metadata') or not transition.metadata:
            return
        
        kegg_id = transition.metadata.get('kegg_id')
        if not kegg_id or kegg_id not in entry_map:
            return
        
        entry = entry_map[kegg_id]
        graphics = entry.graphics
        
        transition.metadata.update({
            'graphics': {
                'bgcolor': graphics.bgcolor,
                'fgcolor': graphics.fgcolor,
                'type': graphics.type,
            },
            'enzyme_class': self._extract_enzyme_class(entry),
        })
    
    def _extract_enzyme_class(self, entry):
        """Extract EC number from entry name."""
        import re
        name = entry.name
        # Look for EC number pattern (e.g., ec:1.1.1.1)
        match = re.search(r'ec:([\d\.]+)', name)
        if match:
            return match.group(1)
        return None
    
    def get_name(self):
        return "MetadataEnhancer"
```

---

### 5. VisualValidator

**Purpose**: Cross-check KGML data with pathway image (optional, advanced).

```python
class VisualValidator(PostProcessorBase):
    """Validate conversion against pathway image."""
    
    def __init__(self, enabled: bool = False,
                 image_url: Optional[str] = None):
        """Initialize validator.
        
        Args:
            enabled: Enable validation (requires image processing libs)
            image_url: URL to pathway PNG image
        """
        super().__init__(enabled)
        self.image_url = image_url
    
    def process(self, document, pathway, options):
        """Validate document against image."""
        if not self.enabled or not self.image_url:
            return document
        
        try:
            # Download and analyze image
            image = self._download_image(self.image_url)
            visual_data = self._analyze_image(image)
            
            # Cross-check with document
            report = self._validate_against_visual(document, visual_data, options)
            
            # Attach report to document metadata
            if not hasattr(document, 'metadata'):
                document.metadata = {}
            document.metadata['validation_report'] = report
            
        except Exception as e:
            print(f"Visual validation failed: {e}")
        
        return document
    
    def _download_image(self, url):
        """Download pathway image."""
        import requests
        from PIL import Image
        from io import BytesIO
        
        response = requests.get(url)
        return Image.open(BytesIO(response.content))
    
    def _analyze_image(self, image):
        """Analyze image for elements."""
        import numpy as np
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Detect nodes (simplified - full implementation would use CV)
        # For now, return empty data
        return {
            'detected_nodes': [],
            'detected_edges': [],
            'image_size': image.size
        }
    
    def _validate_against_visual(self, document, visual_data, options):
        """Compare document with visual analysis."""
        report = {
            'total_places': len(document.places),
            'total_transitions': len(document.transitions),
            'detected_nodes': len(visual_data['detected_nodes']),
            'warnings': []
        }
        
        # Check if counts match
        expected = len(document.places) + len(document.transitions)
        detected = len(visual_data['detected_nodes'])
        
        if abs(expected - detected) > 5:
            report['warnings'].append(
                f"Element count mismatch: {expected} in model, {detected} detected in image"
            )
        
        return report
    
    def get_name(self):
        return "VisualValidator"
```

---

## 🔧 Enhancement Pipeline Integration

### New EnhancementOptions Class

```python
@dataclass
class EnhancementOptions:
    """Options for post-processing enhancements.
    
    Attributes:
        enable_layout_optimization: Optimize layout to reduce overlap
        enable_arc_routing: Add control points for curved arcs
        enable_metadata_enhancement: Add visual/functional metadata
        enable_visual_validation: Validate against pathway image
        image_url: URL to pathway image (for validation)
        layout_min_spacing: Minimum spacing between elements
        arc_curve_style: Arc routing style ('straight', 'curved', 'auto')
    """
    enable_layout_optimization: bool = True
    enable_arc_routing: bool = True
    enable_metadata_enhancement: bool = True
    enable_visual_validation: bool = False
    
    image_url: Optional[str] = None
    layout_min_spacing: float = 60.0
    arc_curve_style: str = 'auto'
```

### Enhanced PathwayConverter

```python
class EnhancedPathwayConverter:
    """Pathway converter with post-processing enhancements."""
    
    def __init__(self, strategy: ConversionStrategy = None,
                 post_processors: List[PostProcessorBase] = None):
        """Initialize converter.
        
        Args:
            strategy: Conversion strategy (default: StandardConversionStrategy)
            post_processors: List of post-processors (default: all enabled)
        """
        # Initialize base converter
        if strategy is None:
            from .compound_mapper import StandardCompoundMapper
            from .reaction_mapper import StandardReactionMapper
            from .arc_builder import StandardArcBuilder
            
            strategy = StandardConversionStrategy(
                compound_mapper=StandardCompoundMapper(),
                reaction_mapper=StandardReactionMapper(),
                arc_builder=StandardArcBuilder()
            )
        
        self.strategy = strategy
        
        # Initialize post-processors
        if post_processors is None:
            post_processors = [
                MetadataEnhancer(enabled=True),
                LayoutOptimizer(enabled=True),
                ArcRouter(enabled=True),
                VisualValidator(enabled=False),  # Optional
            ]
        
        self.post_processors = post_processors
    
    def convert(self, pathway: KEGGPathway,
                options: ConversionOptions = None,
                enhancement_options: EnhancementOptions = None) -> DocumentModel:
        """Convert KEGG pathway to enhanced Petri net model.
        
        Args:
            pathway: Parsed KEGG pathway
            options: Conversion options
            enhancement_options: Enhancement options
            
        Returns:
            Enhanced DocumentModel
        """
        # Phase 1: Standard conversion
        if options is None:
            options = ConversionOptions()
        
        document = self.strategy.convert(pathway, options)
        
        # Phase 2: Post-processing enhancements
        if enhancement_options is None:
            enhancement_options = EnhancementOptions()
        
        for processor in self.post_processors:
            # Configure processor based on options
            self._configure_processor(processor, enhancement_options)
            
            # Apply processor
            if processor.enabled:
                print(f"Applying {processor.get_name()}...")
                document = processor.process(document, pathway, enhancement_options)
        
        return document
    
    def _configure_processor(self, processor, options):
        """Configure processor based on enhancement options."""
        if isinstance(processor, LayoutOptimizer):
            processor.enabled = options.enable_layout_optimization
            processor.min_spacing = options.layout_min_spacing
        
        elif isinstance(processor, ArcRouter):
            processor.enabled = options.enable_arc_routing
            processor.curve_style = options.arc_curve_style
        
        elif isinstance(processor, MetadataEnhancer):
            processor.enabled = options.enable_metadata_enhancement
        
        elif isinstance(processor, VisualValidator):
            processor.enabled = options.enable_visual_validation
            processor.image_url = options.image_url
```

### Convenience Function

```python
def convert_pathway_enhanced(pathway: KEGGPathway,
                            coordinate_scale: float = 2.5,
                            include_cofactors: bool = True,
                            enable_enhancements: bool = True,
                            image_url: Optional[str] = None) -> DocumentModel:
    """Convert pathway with optional enhancements.
    
    Args:
        pathway: Parsed KEGG pathway
        coordinate_scale: Coordinate scaling factor
        include_cofactors: Include common cofactors
        enable_enhancements: Enable post-processing (layout, routing, etc.)
        image_url: URL to pathway image (for validation)
        
    Returns:
        DocumentModel (enhanced if enabled)
        
    Example:
        >>> from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced
        >>> kgml = fetch_pathway("hsa00010")
        >>> pathway = parse_kgml(kgml)
        >>> document = convert_pathway_enhanced(
        ...     pathway,
        ...     enable_enhancements=True,
        ...     image_url="https://www.kegg.jp/kegg/pathway/hsa/hsa00010.png"
        ... )
    """
    # Conversion options
    conv_options = ConversionOptions(
        coordinate_scale=coordinate_scale,
        include_cofactors=include_cofactors
    )
    
    # Enhancement options
    enh_options = EnhancementOptions(
        enable_layout_optimization=enable_enhancements,
        enable_arc_routing=enable_enhancements,
        enable_metadata_enhancement=enable_enhancements,
        enable_visual_validation=(image_url is not None),
        image_url=image_url
    )
    
    # Convert
    converter = EnhancedPathwayConverter()
    return converter.convert(pathway, conv_options, enh_options)
```

---

## 📁 File Structure

Proposed new module structure:

```
src/shypn/importer/kegg/
├── __init__.py
├── models.py
├── kgml_parser.py
├── converter_base.py
├── pathway_converter.py
├── compound_mapper.py
├── reaction_mapper.py
├── arc_builder.py
└── enhancement/                    # NEW MODULE
    ├── __init__.py
    ├── processor_base.py          # PostProcessorBase
    ├── layout_optimizer.py        # LayoutOptimizer
    ├── arc_router.py              # ArcRouter
    ├── metadata_enhancer.py       # MetadataEnhancer
    ├── visual_validator.py        # VisualValidator (optional)
    └── utils.py                   # Shared utilities
```

---

## 📊 Implementation Phases

### Phase 1: Infrastructure (Week 1)

**Goal**: Set up post-processing framework

**Tasks**:
1. Create `enhancement/` module structure
2. Implement `PostProcessorBase` abstract class
3. Create `EnhancementOptions` dataclass
4. Modify `PathwayConverter` to support post-processing pipeline
5. Add unit tests for framework

**Deliverables**:
- ✅ Pipeline infrastructure
- ✅ No-op post-processor (pass-through)
- ✅ Integration tests

---

### Phase 2: Metadata Enhancement (Week 2)

**Goal**: Add visual and functional metadata

**Tasks**:
1. Implement `MetadataEnhancer` class
2. Extract graphics properties (colors, shapes)
3. Classify compounds (cofactors, metabolites)
4. Extract enzyme classifications
5. Add tests with real KEGG data

**Deliverables**:
- ✅ `MetadataEnhancer` implementation
- ✅ Enhanced metadata in DocumentModel
- ✅ Documentation of metadata schema

---

### Phase 3: Layout Optimization (Week 3-4)

**Goal**: Reduce element overlap

**Tasks**:
1. Implement spatial indexing (R-tree)
2. Implement overlap detection
3. Implement force-directed layout adjustment
4. Add constraint preservation (arc validity)
5. Test with crowded pathways
6. Performance optimization

**Deliverables**:
- ✅ `LayoutOptimizer` implementation
- ✅ Benchmarks on large pathways
- ✅ Before/after visualizations

**Dependencies**:
- `rtree` library for spatial indexing
- May need `scipy` for optimization

---

### Phase 4: Arc Routing (Week 5)

**Goal**: Improve arc visualization

**Tasks**:
1. Implement parallel arc detection
2. Implement simple curve generation
3. Implement obstacle detection
4. Implement path planning (waypoints)
5. Test with complex networks
6. Add orthogonal routing option

**Deliverables**:
- ✅ `ArcRouter` implementation
- ✅ Support for Bezier curves in renderer
- ✅ Multiple routing styles

---

### Phase 5: Visual Validation (Week 6-7) - OPTIONAL

**Goal**: Cross-check with images

**Tasks**:
1. Implement image download
2. Implement basic CV analysis (node detection)
3. Implement validation reporting
4. Document limitations
5. Make entirely optional

**Deliverables**:
- ✅ `VisualValidator` implementation
- ✅ Validation reports
- ⚠️ Clearly marked as experimental

**Dependencies**:
- `Pillow` (PIL)
- `opencv-python` (optional)
- `scikit-image` (optional)

---

## 🧪 Testing Strategy

### Unit Tests

Each processor should have:
- Input/output tests (correct data flow)
- Algorithm tests (core logic)
- Edge case tests (empty models, single elements)
- Configuration tests (enable/disable)

### Integration Tests

- End-to-end pipeline tests
- Processor ordering tests
- Performance benchmarks
- Real pathway tests (hsa00010, etc.)

### Visual Tests

- Before/after screenshots
- Manual inspection of results
- User acceptance testing

---

## 📈 Success Metrics

### Quantitative

1. **Layout Quality**:
   - Overlap reduction: Target >80% reduction
   - Average spacing: >60 pixels
   - Layout time: <2 seconds for typical pathway

2. **Arc Quality**:
   - Parallel arc separation: >30 pixels
   - Obstacle avoidance: >90% success rate
   - Rendering performance: No degradation

3. **Validation Accuracy** (optional):
   - Element count match: ±5%
   - Position accuracy: ±20 pixels

### Qualitative

1. Visual clarity improvement
2. User satisfaction (surveys)
3. Reduction in manual layout adjustments

---

## 🚀 Usage Examples

### Example 1: Basic Enhanced Conversion

```python
from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced

# Fetch and parse
kgml = fetch_pathway("hsa00010")
pathway = parse_kgml(kgml)

# Convert with enhancements
document = convert_pathway_enhanced(
    pathway,
    enable_enhancements=True
)

# Document now has:
# - Optimized layout (no overlaps)
# - Curved arcs
# - Rich metadata

print(f"Created {len(document.places)} places, {len(document.transitions)} transitions")
```

### Example 2: Custom Configuration

```python
from shypn.importer.kegg import EnhancedPathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions
from shypn.importer.kegg.enhancement import EnhancementOptions

# Custom options
conv_opts = ConversionOptions(
    coordinate_scale=3.0,
    include_cofactors=False
)

enh_opts = EnhancementOptions(
    enable_layout_optimization=True,
    enable_arc_routing=True,
    enable_metadata_enhancement=True,
    layout_min_spacing=80.0,
    arc_curve_style='curved'
)

# Convert
converter = EnhancedPathwayConverter()
document = converter.convert(pathway, conv_opts, enh_opts)
```

### Example 3: Selective Enhancement

```python
from shypn.importer.kegg.enhancement import (
    EnhancementOptions,
    LayoutOptimizer,
    MetadataEnhancer
)

# Only layout and metadata, no arc routing
enh_opts = EnhancementOptions(
    enable_layout_optimization=True,
    enable_arc_routing=False,  # DISABLED
    enable_metadata_enhancement=True
)

document = convert_pathway_enhanced(pathway, enable_enhancements=enh_opts)
```

### Example 4: With Visual Validation

```python
# With image validation
document = convert_pathway_enhanced(
    pathway,
    enable_enhancements=True,
    image_url="https://www.kegg.jp/kegg/pathway/hsa/hsa00010.png"
)

# Check validation report
if 'metadata' in document.__dict__ and 'validation_report' in document.metadata:
    report = document.metadata['validation_report']
    print(f"Validation: {report['total_places']} places, {report['detected_nodes']} detected")
    for warning in report['warnings']:
        print(f"Warning: {warning}")
```

---

## 🔄 Backward Compatibility

### Ensuring No Breaking Changes

1. **Default Behavior**: New `EnhancedPathwayConverter` is opt-in
2. **Old API Still Works**: `convert_pathway()` unchanged
3. **Gradual Migration**: Users can enable enhancements selectively
4. **Performance**: Enhancements can be disabled for speed

### Migration Path

```python
# Old way (still works)
from shypn.importer.kegg import convert_pathway
document = convert_pathway(pathway)

# New way (opt-in)
from shypn.importer.kegg import convert_pathway_enhanced
document = convert_pathway_enhanced(pathway, enable_enhancements=True)

# Or explicit
from shypn.importer.kegg import EnhancedPathwayConverter
converter = EnhancedPathwayConverter()
document = converter.convert(pathway)
```

---

## 📚 Dependencies

### Required (Phase 1-4)

- `rtree`: Spatial indexing for layout optimization
  ```bash
  pip install rtree
  ```

### Optional (Phase 5)

- `Pillow`: Image loading
- `opencv-python`: Computer vision (optional)
- `scikit-image`: Advanced image processing (optional)

```bash
pip install Pillow opencv-python scikit-image
```

---

## 🎯 Conclusion

This post-processing enhancement pipeline will significantly improve the quality of Petri nets generated from KEGG pathways:

✅ **Non-invasive**: Works as add-on to existing pipeline  
✅ **Modular**: Each enhancement can be enabled/disabled  
✅ **Extensible**: Easy to add new processors  
✅ **Performant**: Can be disabled for speed-critical applications  
✅ **Production-ready**: Phased implementation with testing at each stage

**Next Steps**:
1. Review and approve this plan
2. Begin Phase 1 implementation (infrastructure)
3. Iterate with user feedback

---

**Document Author**: ShypN Development Team  
**Last Updated**: October 9, 2025  
**Status**: Ready for Implementation
