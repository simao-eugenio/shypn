# Utility Modules

This folder contains specific code routines and specialized utilities used throughout the project.

## Current Modules

### `arc_transform.py`
**Arc Geometry Transformations**

Utilities for arc coordinate transformations and geometry calculations:

- **Coordinate Conversions**: Transform between screen and world coordinates
- **Bézier Curve Calculations**: Control point computation for curved arcs
- **Arc Path Generation**: Generate smooth arc paths for rendering
- **Intersection Detection**: Calculate intersections between arcs and objects
- **Distance Calculations**: Compute distances from points to arc paths
- **Angle Calculations**: Determine arrow angles and arc orientations

**Use Cases:**
- Rendering curved arcs with Cairo
- Hit testing for arc selection
- Computing arc connection points to places/transitions
- Calculating control points for Bézier curves
- Arc path smoothing and interpolation

**Import Pattern:**
```python
from shypn.utils.arc_transform import (
    transform_arc_coordinates,
    calculate_bezier_control_points,
    arc_point_distance
)
```

## Future Utilities

Additional utility modules may be added for:
- Mathematical operations
- String formatting and parsing
- File path utilities
- Configuration management
- Logging helpers