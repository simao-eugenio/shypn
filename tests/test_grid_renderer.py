"""Tests for GridRenderer service.

Tests adaptive grid spacing and all three grid styles (line/dot/cross).
"""

import math
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.rendering.grid_renderer import (
    BASE_GRID_SPACING,
    GRID_MAJOR_EVERY,
    GRID_STYLE_LINE,
    GRID_STYLE_DOT,
    GRID_STYLE_CROSS,
    get_adaptive_grid_spacing,
    draw_grid,
)


# Mock Cairo context for testing
class MockCairoContext:
    """Mock Cairo context to capture drawing commands."""
    
    def __init__(self):
        self.operations = []
        self.current_color = None
        self.current_line_width = None
        
    def set_source_rgba(self, r, g, b, a):
        """Record color setting."""
        self.current_color = (r, g, b, a)
        
    def set_line_width(self, width):
        """Record line width setting."""
        self.current_line_width = width
        
    def move_to(self, x, y):
        """Record move operation."""
        self.operations.append(('move_to', x, y))
        
    def line_to(self, x, y):
        """Record line operation."""
        self.operations.append(('line_to', x, y))
        
    def stroke(self):
        """Record stroke operation."""
        self.operations.append(('stroke', self.current_color, self.current_line_width))
        
    def arc(self, x, y, radius, start_angle, end_angle):
        """Record arc (circle) operation."""
        self.operations.append(('arc', x, y, radius, start_angle, end_angle))
        
    def fill(self):
        """Record fill operation."""
        self.operations.append(('fill', self.current_color))
        
    def get_line_count(self):
        """Count number of lines drawn."""
        count = 0
        for i, op in enumerate(self.operations):
            if op[0] == 'stroke':
                count += 1
        return count
        
    def get_dot_count(self):
        """Count number of dots drawn."""
        count = 0
        for op in self.operations:
            if op[0] == 'fill':
                count += 1
        return count
        
    def get_cross_count(self):
        """Count number of crosses drawn."""
        # Each cross = 2 line pairs + 1 stroke
        count = 0
        i = 0
        while i < len(self.operations):
            if self.operations[i][0] == 'move_to':
                # Check if this is a cross (4 moves + 1 stroke)
                if (i + 4 < len(self.operations) and
                    self.operations[i+1][0] == 'line_to' and
                    self.operations[i+2][0] == 'move_to' and
                    self.operations[i+3][0] == 'line_to' and
                    self.operations[i+4][0] == 'stroke'):
                    count += 1
                    i += 5
                    continue
            i += 1
        return count
        
    def has_major_elements(self):
        """Check if major elements (darker color) were drawn."""
        for op in self.operations:
            if op[0] in ('stroke', 'fill'):
                color = op[1]
                # Major elements use darker gray (0.65)
                if color and color[0] == 0.65:
                    return True
        return False
        
    def has_minor_elements(self):
        """Check if minor elements (lighter color) were drawn."""
        for op in self.operations:
            if op[0] in ('stroke', 'fill'):
                color = op[1]
                # Minor elements use lighter gray (0.85)
                if color and color[0] == 0.85:
                    return True
        return False


class TestAdaptiveGridSpacing:
    """Test adaptive grid spacing calculation."""
    
    def test_normal_zoom(self):
        """At zoom=1.0, should return base spacing (1mm grid)."""
        spacing = get_adaptive_grid_spacing(1.0, 10.0)
        assert spacing == 10.0, f"Expected 10.0, got {spacing}"
        
    def test_high_zoom_very_fine(self):
        """At zoom>=5.0, should use very fine grid (base/5)."""
        spacing = get_adaptive_grid_spacing(5.0, 10.0)
        assert spacing == 2.0, f"Expected 2.0, got {spacing}"
        
        spacing = get_adaptive_grid_spacing(10.0, 10.0)
        assert spacing == 2.0, f"Expected 2.0, got {spacing}"
        
    def test_high_zoom_fine(self):
        """At zoom>=2.0, should use fine grid (base/2)."""
        spacing = get_adaptive_grid_spacing(2.0, 10.0)
        assert spacing == 5.0, f"Expected 5.0, got {spacing}"
        
        spacing = get_adaptive_grid_spacing(3.0, 10.0)
        assert spacing == 5.0, f"Expected 5.0, got {spacing}"
        
    def test_mid_zoom_normal(self):
        """At zoom>=0.5, should use normal grid (base)."""
        spacing = get_adaptive_grid_spacing(0.5, 10.0)
        assert spacing == 10.0, f"Expected 10.0, got {spacing}"
        
        spacing = get_adaptive_grid_spacing(1.5, 10.0)
        assert spacing == 10.0, f"Expected 10.0, got {spacing}"
        
    def test_low_zoom_coarse(self):
        """At zoom>=0.2, should use coarse grid (base*2)."""
        spacing = get_adaptive_grid_spacing(0.2, 10.0)
        assert spacing == 20.0, f"Expected 20.0, got {spacing}"
        
        spacing = get_adaptive_grid_spacing(0.4, 10.0)
        assert spacing == 20.0, f"Expected 20.0, got {spacing}"
        
    def test_very_low_zoom_very_coarse(self):
        """At zoom<0.2, should use very coarse grid (base*5)."""
        spacing = get_adaptive_grid_spacing(0.1, 10.0)
        assert spacing == 50.0, f"Expected 50.0, got {spacing}"
        
        spacing = get_adaptive_grid_spacing(0.01, 10.0)
        assert spacing == 50.0, f"Expected 50.0, got {spacing}"


class TestLineGrid:
    """Test line grid rendering."""
    
    def test_basic_line_grid(self):
        """Should draw vertical and horizontal lines."""
        cr = MockCairoContext()
        draw_grid(cr, GRID_STYLE_LINE, 10.0, 1.0, 0, 0, 30, 30)
        
        # Should have drawn lines
        assert cr.get_line_count() > 0, "No lines drawn"
        
        # Should have both move_to and line_to operations
        move_count = sum(1 for op in cr.operations if op[0] == 'move_to')
        line_count = sum(1 for op in cr.operations if op[0] == 'line_to')
        assert move_count > 0, "No move_to operations"
        assert line_count > 0, "No line_to operations"
        assert move_count == line_count, "move_to and line_to counts should match"
        
    def test_major_minor_distinction(self):
        """Should draw major lines darker/thicker than minor lines."""
        cr = MockCairoContext()
        # Draw enough to include both major and minor lines
        # At spacing=10, grid at 0,10,20,30,40,50 (indices 0,1,2,3,4,5)
        # Major lines at indices 0,5 (every 5th)
        draw_grid(cr, GRID_STYLE_LINE, 10.0, 1.0, 0, 0, 50, 50)
        
        assert cr.has_major_elements(), "No major lines drawn"
        assert cr.has_minor_elements(), "No minor lines drawn"
        
    def test_line_width_zoom_compensation(self):
        """Line width should be compensated for zoom."""
        cr = MockCairoContext()
        draw_grid(cr, GRID_STYLE_LINE, 10.0, 2.0, 0, 0, 30, 30)
        
        # Check that some line width was set
        widths = [op[2] for op in cr.operations if op[0] == 'stroke' and op[2] is not None]
        assert len(widths) > 0, "No line widths recorded"
        
        # At zoom=2.0, major width should be 1.0/2.0=0.5, minor 0.5/2.0=0.25
        assert any(abs(w - 0.5) < 0.01 for w in widths), "No major line width found"
        assert any(abs(w - 0.25) < 0.01 for w in widths), "No minor line width found"


class TestDotGrid:
    """Test dot grid rendering."""
    
    def test_basic_dot_grid(self):
        """Should draw dots at grid intersections."""
        cr = MockCairoContext()
        draw_grid(cr, GRID_STYLE_DOT, 10.0, 1.0, 0, 0, 30, 30)
        
        # Should have drawn dots (arc + fill operations)
        assert cr.get_dot_count() > 0, "No dots drawn"
        
        # Should have arc operations
        arc_count = sum(1 for op in cr.operations if op[0] == 'arc')
        assert arc_count > 0, "No arc operations"
        
    def test_dot_major_minor_distinction(self):
        """Major intersections should have larger/darker dots."""
        cr = MockCairoContext()
        # Draw enough to include both major and minor intersections
        draw_grid(cr, GRID_STYLE_DOT, 10.0, 1.0, 0, 0, 50, 50)
        
        assert cr.has_major_elements(), "No major dots drawn"
        assert cr.has_minor_elements(), "No minor dots drawn"
        
        # Check that major dots have larger radius
        arcs = [op for op in cr.operations if op[0] == 'arc']
        radii = [op[3] for op in arcs]
        
        # Major dots: 2.0/zoom=2.0, Minor dots: 1.5/zoom=1.5
        assert any(abs(r - 2.0) < 0.01 for r in radii), "No major dot radius found"
        assert any(abs(r - 1.5) < 0.01 for r in radii), "No minor dot radius found"
        
    def test_dot_count_correct(self):
        """Should draw correct number of dots for viewport."""
        cr = MockCairoContext()
        # Grid spacing=10, viewport 0-30 in both dimensions
        # Grid points at: 0, 10, 20, 30 (4 points each dimension)
        # Total: 4x4 = 16 intersections
        draw_grid(cr, GRID_STYLE_DOT, 10.0, 1.0, 0, 0, 30, 30)
        
        dot_count = cr.get_dot_count()
        assert dot_count == 16, f"Expected 16 dots, got {dot_count}"


class TestCrossGrid:
    """Test cross-hair grid rendering."""
    
    def test_basic_cross_grid(self):
        """Should draw crosses at grid intersections."""
        cr = MockCairoContext()
        draw_grid(cr, GRID_STYLE_CROSS, 10.0, 1.0, 0, 0, 30, 30)
        
        # Should have drawn crosses
        assert cr.get_cross_count() > 0, "No crosses drawn"
        
    def test_cross_major_minor_distinction(self):
        """Major intersections should have larger/darker crosses."""
        cr = MockCairoContext()
        # Draw enough to include both major and minor intersections
        draw_grid(cr, GRID_STYLE_CROSS, 10.0, 1.0, 0, 0, 50, 50)
        
        assert cr.has_major_elements(), "No major crosses drawn"
        assert cr.has_minor_elements(), "No minor crosses drawn"
        
    def test_cross_count_correct(self):
        """Should draw correct number of crosses for viewport."""
        cr = MockCairoContext()
        # Grid spacing=10, viewport 0-30 in both dimensions
        # Grid points at: 0, 10, 20, 30 (4 points each dimension)
        # Total: 4x4 = 16 intersections
        draw_grid(cr, GRID_STYLE_CROSS, 10.0, 1.0, 0, 0, 30, 30)
        
        cross_count = cr.get_cross_count()
        assert cross_count == 16, f"Expected 16 crosses, got {cross_count}"


class TestGridIntegration:
    """Integration tests for grid rendering."""
    
    def test_negative_coordinates(self):
        """Grid should work with negative coordinates."""
        cr = MockCairoContext()
        draw_grid(cr, GRID_STYLE_LINE, 10.0, 1.0, -20, -20, 20, 20)
        
        assert cr.get_line_count() > 0, "No lines drawn with negative coords"
        
    def test_non_aligned_viewport(self):
        """Grid should work when viewport is not aligned to grid."""
        cr = MockCairoContext()
        # Viewport at 5-35 (not aligned to 10-unit grid)
        draw_grid(cr, GRID_STYLE_DOT, 10.0, 1.0, 5, 5, 35, 35)
        
        # Should still draw dots (at 10, 20, 30)
        assert cr.get_dot_count() > 0, "No dots drawn with non-aligned viewport"
        
    def test_high_zoom_fine_grid(self):
        """Grid should adapt to high zoom levels."""
        cr = MockCairoContext()
        # At zoom=5.0, spacing adapts to base/5
        base_px = 10.0
        spacing = get_adaptive_grid_spacing(5.0, base_px)
        draw_grid(cr, GRID_STYLE_LINE, spacing, 5.0, 0, 0, 30, 30)
        
        # Should draw more lines due to finer spacing
        assert cr.get_line_count() > 0, "No lines drawn at high zoom"
        
    def test_low_zoom_coarse_grid(self):
        """Grid should adapt to low zoom levels."""
        cr = MockCairoContext()
        # At zoom=0.1, spacing adapts to base*5
        base_px = 10.0
        spacing = get_adaptive_grid_spacing(0.1, base_px)
        draw_grid(cr, GRID_STYLE_LINE, spacing, 0.1, 0, 0, 200, 200)
        
        # Should draw fewer lines due to coarser spacing
        assert cr.get_line_count() > 0, "No lines drawn at low zoom"


def run_all_tests():
    """Run all grid renderer tests."""
    test_classes = [
        TestAdaptiveGridSpacing(),
        TestLineGrid(),
        TestDotGrid(),
        TestCrossGrid(),
        TestGridIntegration(),
    ]
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\nRunning {class_name}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                method = getattr(test_class, method_name)
                method()
                print(f"  ✓ {method_name}")
            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                return False
            except Exception as e:
                print(f"  ✗ {method_name}: Unexpected error: {e}")
                return False
    
    print("\n" + "="*60)
    print("✅ All grid renderer tests passed!")
    print("="*60)
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
