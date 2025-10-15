"""Grid rendering service for canvas.

Pure functions for drawing adaptive grid patterns with major/minor line distinction.
Supports three grid styles: line, dot, and cross-hair.

Stateless design - all state passed as parameters.
DPI-aware physical spacing (1mm base at 100% zoom).
"""

import math

# Grid constants
BASE_GRID_SPACING = 1.0  # 1mm physical spacing (DPI-aware)
GRID_MAJOR_EVERY = 5     # Every 5th line is a major line
GRID_STYLE_LINE = 'line'   # Standard grid lines
GRID_STYLE_DOT = 'dot'     # Dots at intersections
GRID_STYLE_CROSS = 'cross' # Small crosses at intersections


def get_adaptive_grid_spacing(zoom, base_spacing_px):
    """Calculate adaptive grid spacing based on zoom level.
    
    Grid spacing adapts to maintain readability:
    - At high zoom (zoomed in): smaller subdivisions for precision
    - At low zoom (zoomed out): larger spacing to avoid clutter
    
    Target behavior at zoom=1.0: 
    - Grid spacing = 1mm (minor cell)
    - Major cell = 5mm (every 5th line with GRID_MAJOR_EVERY=5)
    
    Args:
        zoom: Current zoom level (1.0 = 100%).
        base_spacing_px: Base grid spacing in pixels (1mm converted to pixels).
        
    Returns:
        float: Adapted grid spacing in world coordinates.
        
    Examples:
        >>> # At zoom=1.0 with 1mm base
        >>> get_adaptive_grid_spacing(1.0, 10.0)  # 10px = 1mm at some DPI
        10.0  # Normal grid (1mm, major = 5mm)
        
        >>> # At zoom=5.0 (zoomed in)
        >>> get_adaptive_grid_spacing(5.0, 10.0)
        2.0   # Fine grid (0.2mm, major = 1mm)
        
        >>> # At zoom=0.1 (zoomed out)
        >>> get_adaptive_grid_spacing(0.1, 10.0)
        50.0  # Very coarse grid (5mm, major = 25mm)
    """
    if zoom >= 5.0:
        return base_spacing_px / 5   # Very fine grid (0.2mm, major = 1mm)
    elif zoom >= 2.0:
        return base_spacing_px / 2   # Fine grid (0.5mm, major = 2.5mm)
    elif zoom >= 0.5:
        return base_spacing_px       # Normal grid (1mm, major = 5mm) ← TARGET at zoom=1.0
    elif zoom >= 0.2:
        return base_spacing_px * 2   # Coarse grid (2mm, major = 10mm)
    else:
        return base_spacing_px * 5   # Very coarse grid (5mm, major = 25mm)


def draw_grid(cr, grid_style, grid_spacing, zoom, min_x, min_y, max_x, max_y):
    """Draw grid pattern on Cairo context.
    
    Draws in world space (inside Cairo transform) so grid scales with zoom.
    Line widths are compensated to maintain constant pixel size.
    Uses major/minor distinction (every 5th line is major).
    
    Args:
        cr: Cairo context with zoom transform already applied.
        grid_style: One of GRID_STYLE_LINE, GRID_STYLE_DOT, GRID_STYLE_CROSS.
        grid_spacing: Grid spacing in world coordinates (from get_adaptive_grid_spacing).
        zoom: Current zoom level (for line width compensation).
        min_x, min_y: Top-left corner of visible area (world coords).
        max_x, max_y: Bottom-right corner of visible area (world coords).
        
    Notes:
        - Line widths are divided by zoom to maintain constant pixel size
        - Major lines/dots/crosses are drawn every GRID_MAJOR_EVERY (5) cells
        - Major elements are darker (0.65 gray) and thicker
        - Minor elements are lighter (0.85 gray) and thinner
        
    Examples:
        >>> # Line grid
        >>> draw_grid(cr, GRID_STYLE_LINE, 10.0, 1.0, 0, 0, 100, 100)
        
        >>> # Dot grid with high zoom
        >>> draw_grid(cr, GRID_STYLE_DOT, 5.0, 2.0, -50, -50, 50, 50)
    """
    # Calculate grid positions in world coordinates
    start_x = math.floor(min_x / grid_spacing) * grid_spacing
    start_y = math.floor(min_y / grid_spacing) * grid_spacing
    
    # Calculate starting indices (for major/minor line determination)
    start_index_x = int(math.floor(min_x / grid_spacing))
    start_index_y = int(math.floor(min_y / grid_spacing))
    
    if grid_style == GRID_STYLE_LINE:
        _draw_line_grid(cr, grid_spacing, zoom, start_x, start_y, 
                       min_x, min_y, max_x, max_y,
                       start_index_x, start_index_y)
    elif grid_style == GRID_STYLE_DOT:
        _draw_dot_grid(cr, grid_spacing, zoom, start_x, start_y,
                      max_x, max_y, start_index_x, start_index_y)
    elif grid_style == GRID_STYLE_CROSS:
        _draw_cross_grid(cr, grid_spacing, zoom, start_x, start_y,
                        max_x, max_y, start_index_x, start_index_y)


def _draw_line_grid(cr, grid_spacing, zoom, start_x, start_y,
                    min_x, min_y, max_x, max_y,
                    start_index_x, start_index_y):
    """Draw standard line grid with major/minor distinction.
    
    Args:
        cr: Cairo context.
        grid_spacing: Grid spacing in world coordinates.
        zoom: Current zoom level.
        start_x, start_y: Starting grid positions (world coords).
        min_x, min_y: Viewport top-left (world coords).
        max_x, max_y: Viewport bottom-right (world coords).
        start_index_x, start_index_y: Starting grid indices.
    """
    # Draw vertical grid lines
    x = start_x
    index_x = start_index_x
    while x <= max_x:
        # Determine if this is a major line
        is_major = (index_x % GRID_MAJOR_EVERY) == 0
        
        if is_major:
            # Major line: darker color, thicker width
            cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
            cr.set_line_width(1.0 / zoom)
        else:
            # Minor line: lighter color, thinner width
            cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
            cr.set_line_width(0.5 / zoom)
        
        cr.move_to(x, min_y)
        cr.line_to(x, max_y)
        cr.stroke()
        
        x += grid_spacing
        index_x += 1
    
    # Draw horizontal grid lines
    y = start_y
    index_y = start_index_y
    while y <= max_y:
        # Determine if this is a major line
        is_major = (index_y % GRID_MAJOR_EVERY) == 0
        
        if is_major:
            # Major line: darker color, thicker width
            cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
            cr.set_line_width(1.0 / zoom)
        else:
            # Minor line: lighter color, thinner width
            cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
            cr.set_line_width(0.5 / zoom)
        
        cr.move_to(min_x, y)
        cr.line_to(max_x, y)
        cr.stroke()
        
        y += grid_spacing
        index_y += 1


def _draw_dot_grid(cr, grid_spacing, zoom, start_x, start_y,
                   max_x, max_y, start_index_x, start_index_y):
    """Draw dot grid with major/minor distinction.
    
    Major intersections (every 5th line) get larger/darker dots.
    
    Args:
        cr: Cairo context.
        grid_spacing: Grid spacing in world coordinates.
        zoom: Current zoom level.
        start_x, start_y: Starting grid positions (world coords).
        max_x, max_y: Viewport bottom-right (world coords).
        start_index_x, start_index_y: Starting grid indices.
    """
    y = start_y
    index_y = start_index_y
    while y <= max_y:
        x = start_x
        index_x = start_index_x
        while x <= max_x:
            # Check if this is a major intersection
            is_major_x = (index_x % GRID_MAJOR_EVERY) == 0
            is_major_y = (index_y % GRID_MAJOR_EVERY) == 0
            is_major = is_major_x and is_major_y
            
            if is_major:
                # Major intersection: larger, darker dot
                cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)
                dot_radius = 2.0 / zoom
            else:
                # Minor intersection: smaller, lighter dot
                cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)
                dot_radius = 1.5 / zoom
            
            cr.arc(x, y, dot_radius, 0, 2 * math.pi)
            cr.fill()
            
            x += grid_spacing
            index_x += 1
        y += grid_spacing
        index_y += 1


def _draw_cross_grid(cr, grid_spacing, zoom, start_x, start_y,
                     max_x, max_y, start_index_x, start_index_y):
    """Draw cross-hair grid with major/minor distinction.
    
    Major intersections (every 5th line) get larger/darker crosses.
    
    Args:
        cr: Cairo context.
        grid_spacing: Grid spacing in world coordinates.
        zoom: Current zoom level.
        start_x, start_y: Starting grid positions (world coords).
        max_x, max_y: Viewport bottom-right (world coords).
        start_index_x, start_index_y: Starting grid indices.
    """
    y = start_y
    index_y = start_index_y
    while y <= max_y:
        x = start_x
        index_x = start_index_x
        while x <= max_x:
            # Check if this is a major intersection
            is_major_x = (index_x % GRID_MAJOR_EVERY) == 0
            is_major_y = (index_y % GRID_MAJOR_EVERY) == 0
            is_major = is_major_x and is_major_y
            
            if is_major:
                # Major intersection: larger, darker cross
                cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)
                cross_size = 4.0 / zoom
                cr.set_line_width(1.0 / zoom)
            else:
                # Minor intersection: smaller, lighter cross
                cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)
                cross_size = 3.0 / zoom
                cr.set_line_width(0.5 / zoom)
            
            # Horizontal line of cross
            cr.move_to(x - cross_size, y)
            cr.line_to(x + cross_size, y)
            # Vertical line of cross
            cr.move_to(x, y - cross_size)
            cr.line_to(x, y + cross_size)
            cr.stroke()
            
            x += grid_spacing
            index_x += 1
        y += grid_spacing
        index_y += 1
