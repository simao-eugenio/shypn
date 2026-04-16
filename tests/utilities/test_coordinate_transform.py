"""Tests for coordinate transformation utilities.

Tests pure functions with no side effects - easy to test!
"""

import pytest
from shypn.core.services.coordinate_transform import (
    screen_to_world,
    world_to_screen,
    mm_to_pixels,
    pixels_to_mm,
    validate_zoom,
)


class TestScreenToWorld:
    """Test screen_to_world coordinate transformation."""
    
    def test_identity_transform(self):
        """Test with zoom=1.0 and pan=0,0 (identity)."""
        world_x, world_y = screen_to_world(100, 200, zoom=1.0, pan_x=0, pan_y=0)
        assert world_x == 100.0
        assert world_y == 200.0
    
    def test_zoom_scales_inverse(self):
        """Test that zoom scales inversely (screen/zoom)."""
        # At 2x zoom, 100 pixels = 50 world units
        world_x, world_y = screen_to_world(100, 200, zoom=2.0, pan_x=0, pan_y=0)
        assert world_x == 50.0
        assert world_y == 100.0
    
    def test_pan_subtracts_offset(self):
        """Test that pan offset is subtracted."""
        # Pan shifts the world coordinate system
        world_x, world_y = screen_to_world(100, 200, zoom=1.0, pan_x=10, pan_y=20)
        assert world_x == 90.0
        assert world_y == 180.0
    
    def test_zoom_and_pan_combined(self):
        """Test zoom and pan together."""
        world_x, world_y = screen_to_world(200, 300, zoom=2.0, pan_x=50, pan_y=100)
        # (200 / 2.0) - 50 = 50
        # (300 / 2.0) - 100 = 50
        assert world_x == 50.0
        assert world_y == 50.0
    
    def test_negative_coordinates(self):
        """Test with negative screen coordinates."""
        world_x, world_y = screen_to_world(-100, -200, zoom=1.0, pan_x=0, pan_y=0)
        assert world_x == -100.0
        assert world_y == -200.0
    
    def test_fractional_zoom(self):
        """Test with fractional zoom (zoomed out)."""
        # At 0.5x zoom, 100 pixels = 200 world units
        world_x, world_y = screen_to_world(100, 200, zoom=0.5, pan_x=0, pan_y=0)
        assert world_x == 200.0
        assert world_y == 400.0


class TestWorldToScreen:
    """Test world_to_screen coordinate transformation."""
    
    def test_identity_transform(self):
        """Test with zoom=1.0 and pan=0,0 (identity)."""
        screen_x, screen_y = world_to_screen(100, 200, zoom=1.0, pan_x=0, pan_y=0)
        assert screen_x == 100.0
        assert screen_y == 200.0
    
    def test_zoom_scales_direct(self):
        """Test that zoom scales directly ((world+pan)*zoom)."""
        # At 2x zoom, 50 world units = 100 pixels
        screen_x, screen_y = world_to_screen(50, 100, zoom=2.0, pan_x=0, pan_y=0)
        assert screen_x == 100.0
        assert screen_y == 200.0
    
    def test_pan_adds_offset(self):
        """Test that pan offset is added."""
        screen_x, screen_y = world_to_screen(100, 200, zoom=1.0, pan_x=10, pan_y=20)
        assert screen_x == 110.0
        assert screen_y == 220.0
    
    def test_zoom_and_pan_combined(self):
        """Test zoom and pan together."""
        screen_x, screen_y = world_to_screen(50, 50, zoom=2.0, pan_x=50, pan_y=100)
        # (50 + 50) * 2.0 = 200
        # (50 + 100) * 2.0 = 300
        assert screen_x == 200.0
        assert screen_y == 300.0
    
    def test_inverse_of_screen_to_world(self):
        """Test that world_to_screen is inverse of screen_to_world."""
        # Round trip should return original values
        screen_x_orig, screen_y_orig = 123.45, 678.90
        zoom, pan_x, pan_y = 1.5, 10.0, 20.0
        
        # Screen → World → Screen
        world_x, world_y = screen_to_world(screen_x_orig, screen_y_orig, zoom, pan_x, pan_y)
        screen_x, screen_y = world_to_screen(world_x, world_y, zoom, pan_x, pan_y)
        
        assert abs(screen_x - screen_x_orig) < 1e-10
        assert abs(screen_y - screen_y_orig) < 1e-10


class TestMMToPixels:
    """Test mm_to_pixels DPI conversion."""
    
    def test_standard_dpi_96(self):
        """Test with standard 96 DPI."""
        # 25.4 mm = 1 inch = 96 pixels at 96 DPI
        pixels = mm_to_pixels(25.4, screen_dpi=96.0)
        assert abs(pixels - 96.0) < 1e-10
    
    def test_high_dpi_120(self):
        """Test with high DPI display."""
        # 25.4 mm = 1 inch = 120 pixels at 120 DPI
        pixels = mm_to_pixels(25.4, screen_dpi=120.0)
        assert abs(pixels - 120.0) < 1e-10
    
    def test_1mm_at_96dpi(self):
        """Test 1mm at standard DPI."""
        # 1 mm ≈ 3.78 pixels at 96 DPI
        pixels = mm_to_pixels(1.0, screen_dpi=96.0)
        expected = 96.0 / 25.4
        assert abs(pixels - expected) < 1e-10
    
    def test_default_dpi(self):
        """Test that default DPI is 96.0."""
        pixels_default = mm_to_pixels(10.0)
        pixels_explicit = mm_to_pixels(10.0, screen_dpi=96.0)
        assert pixels_default == pixels_explicit
    
    def test_zero_mm(self):
        """Test with zero millimeters."""
        pixels = mm_to_pixels(0.0, screen_dpi=96.0)
        assert pixels == 0.0
    
    def test_negative_mm(self):
        """Test with negative millimeters."""
        pixels = mm_to_pixels(-10.0, screen_dpi=96.0)
        assert pixels < 0


class TestPixelsToMM:
    """Test pixels_to_mm DPI conversion."""
    
    def test_standard_dpi_96(self):
        """Test with standard 96 DPI."""
        # 96 pixels = 1 inch = 25.4 mm at 96 DPI
        mm = pixels_to_mm(96.0, screen_dpi=96.0)
        assert abs(mm - 25.4) < 1e-10
    
    def test_inverse_of_mm_to_pixels(self):
        """Test that pixels_to_mm is inverse of mm_to_pixels."""
        mm_orig = 12.7  # Half inch
        screen_dpi = 120.0
        
        # MM → Pixels → MM
        pixels = mm_to_pixels(mm_orig, screen_dpi=screen_dpi)
        mm = pixels_to_mm(pixels, screen_dpi=screen_dpi)
        
        assert abs(mm - mm_orig) < 1e-10
    
    def test_zero_pixels(self):
        """Test with zero pixels."""
        mm = pixels_to_mm(0.0, screen_dpi=96.0)
        assert mm == 0.0


class TestValidateZoom:
    """Test validate_zoom clamping."""
    
    def test_within_range(self):
        """Test zoom within valid range."""
        zoom = validate_zoom(1.5, min_zoom=0.3, max_zoom=3.0)
        assert zoom == 1.5
    
    def test_clamp_to_min(self):
        """Test clamping to minimum."""
        zoom = validate_zoom(0.1, min_zoom=0.3, max_zoom=3.0)
        assert zoom == 0.3
    
    def test_clamp_to_max(self):
        """Test clamping to maximum."""
        zoom = validate_zoom(5.0, min_zoom=0.3, max_zoom=3.0)
        assert zoom == 3.0
    
    def test_exactly_min(self):
        """Test zoom exactly at minimum."""
        zoom = validate_zoom(0.3, min_zoom=0.3, max_zoom=3.0)
        assert zoom == 0.3
    
    def test_exactly_max(self):
        """Test zoom exactly at maximum."""
        zoom = validate_zoom(3.0, min_zoom=0.3, max_zoom=3.0)
        assert zoom == 3.0
    
    def test_default_limits(self):
        """Test with default limits."""
        zoom = validate_zoom(1.0)
        assert zoom == 1.0


class TestRoundTripTransforms:
    """Test round-trip transformations for consistency."""
    
    def test_screen_world_screen_roundtrip(self):
        """Test screen → world → screen returns original."""
        test_cases = [
            (100, 200, 1.0, 0, 0),
            (50, 75, 2.0, 10, 20),
            (200, 300, 0.5, -50, -100),
            (-100, -200, 1.5, 25, 75),
        ]
        
        for screen_x, screen_y, zoom, pan_x, pan_y in test_cases:
            world_x, world_y = screen_to_world(screen_x, screen_y, zoom, pan_x, pan_y)
            result_x, result_y = world_to_screen(world_x, world_y, zoom, pan_x, pan_y)
            
            assert abs(result_x - screen_x) < 1e-10, f"Failed for {test_cases}"
            assert abs(result_y - screen_y) < 1e-10, f"Failed for {test_cases}"
    
    def test_mm_pixels_mm_roundtrip(self):
        """Test mm → pixels → mm returns original."""
        test_cases = [
            (10.0, 96.0),
            (25.4, 120.0),
            (1.0, 144.0),
            (100.0, 72.0),
        ]
        
        for mm, dpi in test_cases:
            pixels = mm_to_pixels(mm, screen_dpi=dpi)
            result_mm = pixels_to_mm(pixels, screen_dpi=dpi)
            
            assert abs(result_mm - mm) < 1e-10, f"Failed for mm={mm}, dpi={dpi}"


if __name__ == "__main__":
    # Run tests manually
    import sys
    
    print("Running coordinate transform tests...")
    
    # Test screen_to_world
    test = TestScreenToWorld()
    test.test_identity_transform()
    test.test_zoom_scales_inverse()
    test.test_pan_subtracts_offset()
    print("✓ screen_to_world tests passed")
    
    # Test world_to_screen
    test = TestWorldToScreen()
    test.test_identity_transform()
    test.test_inverse_of_screen_to_world()
    print("✓ world_to_screen tests passed")
    
    # Test DPI conversions
    test = TestMMToPixels()
    test.test_standard_dpi_96()
    test.test_1mm_at_96dpi()
    print("✓ mm_to_pixels tests passed")
    
    test = TestPixelsToMM()
    test.test_inverse_of_mm_to_pixels()
    print("✓ pixels_to_mm tests passed")
    
    # Test validation
    test = TestValidateZoom()
    test.test_clamp_to_min()
    test.test_clamp_to_max()
    print("✓ validate_zoom tests passed")
    
    # Test round trips
    test = TestRoundTripTransforms()
    test.test_screen_world_screen_roundtrip()
    test.test_mm_pixels_mm_roundtrip()
    print("✓ round-trip tests passed")
    
    print("\n✅ All coordinate transform tests passed!")
