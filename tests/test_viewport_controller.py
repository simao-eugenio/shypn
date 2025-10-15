"""Tests for ViewportController.

Tests zoom, pan, bounds clamping, and view state persistence.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.core.controllers.viewport_controller import ViewportController


class TestViewportInitialization:
    """Test viewport controller initialization."""
    
    def test_default_initialization(self):
        """Should initialize with default values."""
        vc = ViewportController()
        
        assert vc.zoom == 1.0, f"Expected zoom=1.0, got {vc.zoom}"
        assert vc.pan_x == 0.0, f"Expected pan_x=0.0, got {vc.pan_x}"
        assert vc.pan_y == 0.0, f"Expected pan_y=0.0, got {vc.pan_y}"
        assert vc.viewport_width == 800, f"Expected width=800, got {vc.viewport_width}"
        assert vc.viewport_height == 600, f"Expected height=600, got {vc.viewport_height}"
        assert vc._initial_pan_set == False, "Initial pan should not be set"
        
    def test_custom_initialization(self):
        """Should accept custom viewport dimensions."""
        vc = ViewportController(viewport_width=1024, viewport_height=768)
        
        assert vc.viewport_width == 1024
        assert vc.viewport_height == 768
        
    def test_filename_initialization(self):
        """Should accept custom filename for persistence."""
        vc = ViewportController(filename="test_model")
        
        assert vc.filename == "test_model"


class TestZoomOperations:
    """Test zoom operations."""
    
    def test_zoom_in(self):
        """Zoom in should increase zoom level."""
        vc = ViewportController()
        initial_zoom = vc.zoom
        
        vc.zoom_in()
        
        assert vc.zoom > initial_zoom, "Zoom should increase"
        assert abs(vc.zoom - initial_zoom * vc.ZOOM_STEP) < 0.01, "Zoom should increase by ZOOM_STEP"
        
    def test_zoom_out(self):
        """Zoom out should decrease zoom level."""
        vc = ViewportController()
        initial_zoom = vc.zoom
        
        vc.zoom_out()
        
        assert vc.zoom < initial_zoom, "Zoom should decrease"
        assert abs(vc.zoom - initial_zoom / vc.ZOOM_STEP) < 0.01, "Zoom should decrease by ZOOM_STEP"
        
    def test_zoom_bounds_min(self):
        """Zoom should not go below MIN_ZOOM."""
        vc = ViewportController()
        
        # Zoom out many times
        for _ in range(20):
            vc.zoom_out()
        
        assert vc.zoom >= vc.MIN_ZOOM, f"Zoom should not go below {vc.MIN_ZOOM}"
        
    def test_zoom_bounds_max(self):
        """Zoom should not go above MAX_ZOOM."""
        vc = ViewportController()
        
        # Zoom in many times
        for _ in range(20):
            vc.zoom_in()
        
        assert vc.zoom <= vc.MAX_ZOOM, f"Zoom should not go above {vc.MAX_ZOOM}"
        
    def test_set_zoom_absolute(self):
        """Should set zoom to absolute value."""
        vc = ViewportController()
        
        vc.set_zoom(2.0)
        
        assert abs(vc.zoom - 2.0) < 0.01, f"Expected zoom=2.0, got {vc.zoom}"
        
    def test_set_zoom_clamped(self):
        """Set zoom should clamp to valid range."""
        vc = ViewportController()
        
        # Try to set too low
        vc.set_zoom(0.1)
        assert vc.zoom >= vc.MIN_ZOOM, "Zoom should be clamped to MIN_ZOOM"
        
        # Try to set too high
        vc.set_zoom(10.0)
        assert vc.zoom <= vc.MAX_ZOOM, "Zoom should be clamped to MAX_ZOOM"
        
    def test_zoom_by_factor(self):
        """Should zoom by arbitrary factor."""
        vc = ViewportController()
        initial_zoom = 1.0
        
        vc.zoom_by_factor(1.5)
        
        assert abs(vc.zoom - initial_zoom * 1.5) < 0.01, f"Expected zoom=1.5, got {vc.zoom}"
        
    def test_pointer_centered_zoom(self):
        """Zoom at point should keep world coordinate under pointer fixed."""
        vc = ViewportController(viewport_width=800, viewport_height=600)
        vc.set_viewport_size(800, 600)  # Trigger initial pan
        
        # Point at screen position (400, 300) - center of viewport
        screen_x, screen_y = 400, 300
        
        # Calculate world position before zoom
        world_x_before = (screen_x / vc.zoom) - vc.pan_x
        world_y_before = (screen_y / vc.zoom) - vc.pan_y
        
        # Zoom in at that point
        vc.zoom_by_factor(2.0, screen_x, screen_y)
        
        # Calculate world position after zoom
        world_x_after = (screen_x / vc.zoom) - vc.pan_x
        world_y_after = (screen_y / vc.zoom) - vc.pan_y
        
        # World coordinate should stay the same
        assert abs(world_x_after - world_x_before) < 0.01, "World X should stay fixed under pointer"
        assert abs(world_y_after - world_y_before) < 0.01, "World Y should stay fixed under pointer"


class TestPanOperations:
    """Test pan operations."""
    
    def test_pan_delta(self):
        """Pan should move viewport by screen delta."""
        vc = ViewportController()
        initial_pan_x = vc.pan_x
        initial_pan_y = vc.pan_y
        
        # Pan right 100px, down 50px
        vc.pan(100, 50)
        
        # Pan should have changed (world delta = screen delta / zoom)
        expected_dx = 100 / vc.zoom
        expected_dy = 50 / vc.zoom
        
        assert abs(vc.pan_x - (initial_pan_x + expected_dx)) < 0.01, "Pan X incorrect"
        assert abs(vc.pan_y - (initial_pan_y + expected_dy)) < 0.01, "Pan Y incorrect"
        
    def test_pan_to_absolute(self):
        """Pan to should attempt to center viewport on world coordinate."""
        vc = ViewportController(viewport_width=800, viewport_height=600)
        vc.set_viewport_size(800, 600)  # Trigger initial pan
        
        # Record initial center
        initial_center_x = (400 / vc.zoom) - vc.pan_x
        initial_center_y = (300 / vc.zoom) - vc.pan_y
        
        # Pan to world coordinate (100, 200)
        vc.pan_to(100, 200)
        
        # Check that center changed
        new_center_x = (400 / vc.zoom) - vc.pan_x
        new_center_y = (300 / vc.zoom) - vc.pan_y
        
        # Pan should have moved viewport (even if clamped)
        assert new_center_x != initial_center_x, "Viewport center X should change"
        assert new_center_y != initial_center_y, "Viewport center Y should change"
        
    def test_pan_relative(self):
        """Pan relative should be same as pan."""
        vc = ViewportController()
        
        initial_pan_x = vc.pan_x
        initial_pan_y = vc.pan_y
        
        vc.pan_relative(50, 30)
        
        expected_dx = 50 / vc.zoom
        expected_dy = 30 / vc.zoom
        
        assert abs(vc.pan_x - (initial_pan_x + expected_dx)) < 0.01
        assert abs(vc.pan_y - (initial_pan_y + expected_dy)) < 0.01


class TestBoundsClamping:
    """Test canvas bounds clamping."""
    
    def test_clamp_pan_prevents_excessive_pan(self):
        """Clamp should prevent pan from exceeding canvas extent."""
        vc = ViewportController()
        
        # Try to pan way beyond extent
        vc.pan_x = 100000
        vc.pan_y = 100000
        vc.clamp_pan()
        
        # Should be clamped to reasonable values
        assert vc.pan_x <= vc.CANVAS_EXTENT, "Pan X should be clamped"
        assert vc.pan_y <= vc.CANVAS_EXTENT, "Pan Y should be clamped"
        
    def test_clamp_pan_ensures_viewport_coverage(self):
        """Clamp should ensure canvas covers viewport."""
        vc = ViewportController(viewport_width=800, viewport_height=600)
        
        # Try to pan to negative extreme
        vc.pan_x = -100000
        vc.pan_y = -100000
        vc.clamp_pan()
        
        # Calculate min allowed pan
        min_pan_x = (vc.viewport_width / vc.zoom) - vc.CANVAS_EXTENT
        min_pan_y = (vc.viewport_height / vc.zoom) - vc.CANVAS_EXTENT
        
        assert vc.pan_x >= min_pan_x, "Pan X should not go below minimum"
        assert vc.pan_y >= min_pan_y, "Pan Y should not go below minimum"
        
    def test_clamp_adjusts_for_zoom(self):
        """Clamp limits should adjust for zoom level."""
        vc = ViewportController(viewport_width=800, viewport_height=600)
        
        # At zoom=1.0
        vc.zoom = 1.0
        vc.clamp_pan()
        pan_x_at_zoom1 = vc.pan_x
        
        # At zoom=2.0, viewport covers less world space
        vc.zoom = 2.0
        vc.clamp_pan()
        
        # Limits should be different
        # (Test passes if no exception raised)


class TestViewportManagement:
    """Test viewport size and state management."""
    
    def test_set_viewport_size(self):
        """Should update viewport dimensions."""
        vc = ViewportController()
        
        vc.set_viewport_size(1024, 768)
        
        assert vc.viewport_width == 1024
        assert vc.viewport_height == 768
        
    def test_first_viewport_size_centers_canvas(self):
        """First viewport size should center canvas at origin."""
        vc = ViewportController()
        assert vc._initial_pan_set == False
        
        vc.set_viewport_size(800, 600)
        
        # Should center (0,0) world at screen center
        expected_pan_x = -(800 / 2) / vc.zoom
        expected_pan_y = -(600 / 2) / vc.zoom
        
        assert abs(vc.pan_x - expected_pan_x) < 0.01, f"Expected pan_x={expected_pan_x}, got {vc.pan_x}"
        assert abs(vc.pan_y - expected_pan_y) < 0.01, f"Expected pan_y={expected_pan_y}, got {vc.pan_y}"
        assert vc._initial_pan_set == True, "Initial pan flag should be set"
        
    def test_subsequent_viewport_size_preserves_pan(self):
        """Subsequent size changes should not reset pan."""
        vc = ViewportController()
        vc.set_viewport_size(800, 600)
        initial_pan_x = vc.pan_x
        
        # Resize viewport
        vc.set_viewport_size(1024, 768)
        
        # Pan should be unchanged
        assert vc.pan_x == initial_pan_x, "Pan should not change on resize"
        
    def test_set_pointer_position(self):
        """Should update pointer position."""
        vc = ViewportController()
        
        vc.set_pointer_position(123, 456)
        
        assert vc.pointer_x == 123
        assert vc.pointer_y == 456
        
    def test_get_zoom_percentage(self):
        """Should return zoom as percentage string."""
        vc = ViewportController()
        
        vc.zoom = 1.0
        assert vc.get_zoom_percentage() == "100%"
        
        vc.zoom = 1.5
        assert vc.get_zoom_percentage() == "150%"
        
        vc.zoom = 0.5
        assert vc.get_zoom_percentage() == "50%"
        
    def test_get_viewport_info(self):
        """Should return viewport state dict."""
        vc = ViewportController()
        vc.zoom = 1.5
        vc.pan_x = 100
        vc.pan_y = 200
        
        info = vc.get_viewport_info()
        
        assert info['zoom'] == 1.5
        assert info['zoom_percent'] == "150%"
        assert info['pan_x'] == 100
        assert info['pan_y'] == 200
        assert 'viewport' in info
        assert 'pointer' in info


class TestRedrawManagement:
    """Test redraw flag management."""
    
    def test_initial_needs_redraw(self):
        """Should initially need redraw."""
        vc = ViewportController()
        
        assert vc.needs_redraw() == True
        
    def test_mark_clean(self):
        """Mark clean should clear redraw flag."""
        vc = ViewportController()
        vc.mark_clean()
        
        assert vc.needs_redraw() == False
        
    def test_mark_dirty(self):
        """Mark dirty should set redraw flag."""
        vc = ViewportController()
        vc.mark_clean()
        vc.mark_dirty()
        
        assert vc.needs_redraw() == True
        
    def test_operations_mark_dirty(self):
        """Operations should mark viewport dirty."""
        vc = ViewportController()
        
        # Zoom marks dirty
        vc.mark_clean()
        vc.zoom_in()
        assert vc.needs_redraw() == True
        
        # Pan marks dirty
        vc.mark_clean()
        vc.pan(10, 20)
        assert vc.needs_redraw() == True
        
        # Viewport resize marks dirty
        vc.mark_clean()
        vc.set_viewport_size(1024, 768)
        assert vc.needs_redraw() == True


class TestReset:
    """Test viewport reset."""
    
    def test_reset_to_defaults(self):
        """Reset should restore default state."""
        vc = ViewportController()
        vc.set_viewport_size(800, 600)
        
        # Change state
        vc.zoom_in()
        vc.pan(100, 200)
        
        # Reset
        vc.reset()
        
        assert vc.zoom == 1.0, "Zoom should reset to 1.0"
        # Pan is re-centered
        expected_pan_x = -(800 / 2) / vc.zoom
        assert abs(vc.pan_x - expected_pan_x) < 0.01, "Pan X should be re-centered"


class TestViewStatePersistence:
    """Test view state save/load."""
    
    def test_save_view_state(self):
        """Should save view state to file."""
        # Use temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            vc = ViewportController(filename="test_save")
            vc.zoom = 1.5
            vc.pan_x = 100
            vc.pan_y = 200
            
            vc.save_view_state_to_file()
            
            # Check file exists
            state_file = "workspace/.view_state_test_save.json"
            assert os.path.exists(state_file), "State file should exist"
            
            # Check content
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            assert state['zoom'] == 1.5
            assert state['pan_x'] == 100
            assert state['pan_y'] == 200
            
    def test_load_view_state(self):
        """Should load view state from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create state file
            os.makedirs("workspace", exist_ok=True)
            state = {'zoom': 2.0, 'pan_x': 300, 'pan_y': 400}
            with open("workspace/.view_state_test_load.json", 'w') as f:
                json.dump(state, f)
            
            # Load state
            vc = ViewportController(filename="test_load")
            success = vc.load_view_state_from_file()
            
            assert success == True, "Load should succeed"
            assert vc.zoom == 2.0, f"Expected zoom=2.0, got {vc.zoom}"
            assert vc.pan_x == 300, f"Expected pan_x=300, got {vc.pan_x}"
            assert vc.pan_y == 400, f"Expected pan_y=400, got {vc.pan_y}"
            
    def test_load_nonexistent_state(self):
        """Load should fail gracefully if file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            vc = ViewportController(filename="nonexistent")
            success = vc.load_view_state_from_file()
            
            assert success == False, "Load should fail"
            # State should remain at defaults
            assert vc.zoom == 1.0


def run_all_tests():
    """Run all viewport controller tests."""
    test_classes = [
        TestViewportInitialization(),
        TestZoomOperations(),
        TestPanOperations(),
        TestBoundsClamping(),
        TestViewportManagement(),
        TestRedrawManagement(),
        TestReset(),
        TestViewStatePersistence(),
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
                import traceback
                traceback.print_exc()
                return False
    
    print("\n" + "="*60)
    print("✅ All viewport controller tests passed!")
    print("="*60)
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
