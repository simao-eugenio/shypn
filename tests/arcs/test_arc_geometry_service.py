"""Tests for arc geometry service.

Tests stateless arc geometry calculations for parallel arc detection
and offset calculation.
"""

import pytest
from shypn.core.services.arc_geometry_service import (
    detect_parallel_arcs,
    calculate_arc_offset,
    count_parallel_arcs,
    has_parallel_arcs,
    get_arc_offset_for_rendering,
    separate_parallel_arcs_by_direction,
)


# Mock Arc class for testing
class MockArc:
    """Mock arc for testing."""
    
    def __init__(self, id, source, target):
        self.id = id
        self.source = source
        self.target = target
    
    def __repr__(self):
        return f"Arc({self.id}: {self.source}→{self.target})"


class TestDetectParallelArcs:
    """Test parallel arc detection."""
    
    def test_no_parallels(self):
        """Test arc with no parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'C', 'D')
        arc3 = MockArc(3, 'E', 'F')
        all_arcs = [arc1, arc2, arc3]
        
        parallels = detect_parallel_arcs(arc1, all_arcs)
        assert len(parallels) == 0
    
    def test_same_direction_parallel(self):
        """Test arcs in same direction (A→B, A→B)."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')  # Same direction
        arc3 = MockArc(3, 'C', 'D')
        all_arcs = [arc1, arc2, arc3]
        
        parallels = detect_parallel_arcs(arc1, all_arcs)
        assert len(parallels) == 1
        assert arc2 in parallels
        assert arc1 not in parallels  # Exclude self
    
    def test_opposite_direction_parallel(self):
        """Test arcs in opposite directions (A→B, B→A)."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'B', 'A')  # Opposite direction
        arc3 = MockArc(3, 'C', 'D')
        all_arcs = [arc1, arc2, arc3]
        
        parallels = detect_parallel_arcs(arc1, all_arcs)
        assert len(parallels) == 1
        assert arc2 in parallels
    
    def test_multiple_same_direction(self):
        """Test multiple arcs in same direction."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')
        arc3 = MockArc(3, 'A', 'B')
        all_arcs = [arc1, arc2, arc3]
        
        parallels = detect_parallel_arcs(arc1, all_arcs)
        assert len(parallels) == 2
        assert arc2 in parallels
        assert arc3 in parallels
    
    def test_mixed_directions(self):
        """Test mix of same and opposite direction parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')  # Same direction
        arc3 = MockArc(3, 'B', 'A')  # Opposite direction
        arc4 = MockArc(4, 'C', 'D')  # Different nodes
        all_arcs = [arc1, arc2, arc3, arc4]
        
        parallels = detect_parallel_arcs(arc1, all_arcs)
        assert len(parallels) == 2
        assert arc2 in parallels
        assert arc3 in parallels
        assert arc4 not in parallels
    
    def test_excludes_self(self):
        """Test that arc doesn't detect itself as parallel."""
        arc1 = MockArc(1, 'A', 'B')
        all_arcs = [arc1]
        
        parallels = detect_parallel_arcs(arc1, all_arcs)
        assert len(parallels) == 0


class TestCalculateArcOffset:
    """Test arc offset calculation."""
    
    def test_no_parallels_zero_offset(self):
        """Test that no parallels means zero offset."""
        arc1 = MockArc(1, 'A', 'B')
        parallels = []
        
        offset = calculate_arc_offset(arc1, parallels)
        assert offset == 0.0
    
    def test_two_arcs_opposite_direction(self):
        """Test two arcs in opposite directions (mirror symmetry)."""
        arc1 = MockArc(1, 'A', 'B')  # Lower ID
        arc2 = MockArc(2, 'B', 'A')  # Higher ID
        
        # Arc with lower ID gets positive offset
        offset1 = calculate_arc_offset(arc1, [arc2])
        assert offset1 == 50.0
        
        # Arc with higher ID gets negative offset (mirror)
        offset2 = calculate_arc_offset(arc2, [arc1])
        assert offset2 == -50.0
    
    def test_two_arcs_same_direction(self):
        """Test two arcs in same direction."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')
        
        # First arc (by ID) gets positive offset
        offset1 = calculate_arc_offset(arc1, [arc2])
        assert offset1 == 15.0
        
        # Second arc gets negative offset
        offset2 = calculate_arc_offset(arc2, [arc1])
        assert offset2 == -15.0
    
    def test_three_arcs_same_direction(self):
        """Test three arcs in same direction (distributed around center)."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')
        arc3 = MockArc(3, 'A', 'B')
        
        # all_arcs sorted by ID: [arc1, arc2, arc3]
        # index 0, 1, 2; total = 3
        # center = (3-1)/2 = 1.0
        # offset = (index - center) * 10
        # arc1: (0 - 1.0) * 10 = -10
        # arc2: (1 - 1.0) * 10 = 0
        # arc3: (2 - 1.0) * 10 = 10
        
        offset1 = calculate_arc_offset(arc1, [arc2, arc3])
        offset2 = calculate_arc_offset(arc2, [arc1, arc3])
        offset3 = calculate_arc_offset(arc3, [arc1, arc2])
        
        assert offset1 == -10.0
        assert offset2 == 0.0
        assert offset3 == 10.0
    
    def test_four_arcs_distribution(self):
        """Test four arcs distributed evenly."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')
        arc3 = MockArc(3, 'A', 'B')
        arc4 = MockArc(4, 'A', 'B')
        
        # For 4 arcs: center = 1.5
        # Offsets: -15, -5, +5, +15 (10px spacing)
        offset1 = calculate_arc_offset(arc1, [arc2, arc3, arc4])
        offset2 = calculate_arc_offset(arc2, [arc1, arc3, arc4])
        offset3 = calculate_arc_offset(arc3, [arc1, arc2, arc4])
        offset4 = calculate_arc_offset(arc4, [arc1, arc2, arc3])
        
        assert offset1 == -15.0  # (0 - 1.5) * 10
        assert offset2 == -5.0   # (1 - 1.5) * 10
        assert offset3 == 5.0    # (2 - 1.5) * 10
        assert offset4 == 15.0   # (3 - 1.5) * 10


class TestCountParallelArcs:
    """Test parallel arc counting."""
    
    def test_count_no_parallels(self):
        """Test counting with no parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'C', 'D')
        all_arcs = [arc1, arc2]
        
        count = count_parallel_arcs(arc1, all_arcs)
        assert count == 0
    
    def test_count_one_parallel(self):
        """Test counting with one parallel."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'B', 'A')
        all_arcs = [arc1, arc2]
        
        count = count_parallel_arcs(arc1, all_arcs)
        assert count == 1
    
    def test_count_multiple_parallels(self):
        """Test counting multiple parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')
        arc3 = MockArc(3, 'B', 'A')
        all_arcs = [arc1, arc2, arc3]
        
        count = count_parallel_arcs(arc1, all_arcs)
        assert count == 2


class TestHasParallelArcs:
    """Test boolean parallel arc check."""
    
    def test_has_no_parallels(self):
        """Test with no parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'C', 'D')
        all_arcs = [arc1, arc2]
        
        assert has_parallel_arcs(arc1, all_arcs) == False
    
    def test_has_parallels(self):
        """Test with parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'B', 'A')
        all_arcs = [arc1, arc2]
        
        assert has_parallel_arcs(arc1, all_arcs) == True


class TestGetArcOffsetForRendering:
    """Test combined detection and calculation."""
    
    def test_convenience_function(self):
        """Test that convenience function works correctly."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'B', 'A')
        all_arcs = [arc1, arc2]
        
        # Should combine detection + calculation
        offset = get_arc_offset_for_rendering(arc1, all_arcs)
        
        # Same as manual approach
        parallels = detect_parallel_arcs(arc1, all_arcs)
        expected = calculate_arc_offset(arc1, parallels)
        
        assert offset == expected
        assert offset == 50.0  # Lower ID gets positive


class TestSeparateParallelArcsByDirection:
    """Test separating parallels by direction."""
    
    def test_separate_same_and_opposite(self):
        """Test separating mixed directions."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')  # Same
        arc3 = MockArc(3, 'A', 'B')  # Same
        arc4 = MockArc(4, 'B', 'A')  # Opposite
        arc5 = MockArc(5, 'B', 'A')  # Opposite
        
        parallels = [arc2, arc3, arc4, arc5]
        same, opposite = separate_parallel_arcs_by_direction(arc1, parallels)
        
        assert len(same) == 2
        assert arc2 in same
        assert arc3 in same
        
        assert len(opposite) == 2
        assert arc4 in opposite
        assert arc5 in opposite
    
    def test_separate_only_same(self):
        """Test with only same-direction parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'A', 'B')
        arc3 = MockArc(3, 'A', 'B')
        
        parallels = [arc2, arc3]
        same, opposite = separate_parallel_arcs_by_direction(arc1, parallels)
        
        assert len(same) == 2
        assert len(opposite) == 0
    
    def test_separate_only_opposite(self):
        """Test with only opposite-direction parallels."""
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'B', 'A')
        arc3 = MockArc(3, 'B', 'A')
        
        parallels = [arc2, arc3]
        same, opposite = separate_parallel_arcs_by_direction(arc1, parallels)
        
        assert len(same) == 0
        assert len(opposite) == 2


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_simple_bidirectional(self):
        """Test simple A↔B bidirectional arcs."""
        arc_ab = MockArc(1, 'A', 'B')
        arc_ba = MockArc(2, 'B', 'A')
        all_arcs = [arc_ab, arc_ba]
        
        # Both should have parallels
        assert has_parallel_arcs(arc_ab, all_arcs)
        assert has_parallel_arcs(arc_ba, all_arcs)
        
        # Should have mirror offsets
        offset_ab = get_arc_offset_for_rendering(arc_ab, all_arcs)
        offset_ba = get_arc_offset_for_rendering(arc_ba, all_arcs)
        
        assert offset_ab == 50.0
        assert offset_ba == -50.0
    
    def test_complex_network(self):
        """Test complex network with multiple parallel sets."""
        # A↔B (2 arcs)
        arc1 = MockArc(1, 'A', 'B')
        arc2 = MockArc(2, 'B', 'A')
        
        # C→D (3 arcs same direction)
        arc3 = MockArc(3, 'C', 'D')
        arc4 = MockArc(4, 'C', 'D')
        arc5 = MockArc(5, 'C', 'D')
        
        # E→F (isolated)
        arc6 = MockArc(6, 'E', 'F')
        
        all_arcs = [arc1, arc2, arc3, arc4, arc5, arc6]
        
        # A↔B should have mirror offsets
        assert get_arc_offset_for_rendering(arc1, all_arcs) == 50.0
        assert get_arc_offset_for_rendering(arc2, all_arcs) == -50.0
        
        # C→D should be distributed
        offset3 = get_arc_offset_for_rendering(arc3, all_arcs)
        offset4 = get_arc_offset_for_rendering(arc4, all_arcs)
        offset5 = get_arc_offset_for_rendering(arc5, all_arcs)
        
        assert offset3 == -10.0
        assert offset4 == 0.0
        assert offset5 == 10.0
        
        # E→F should be straight
        assert get_arc_offset_for_rendering(arc6, all_arcs) == 0.0


if __name__ == "__main__":
    # Run tests manually
    print("Running arc geometry service tests...")
    
    # Test detection
    test = TestDetectParallelArcs()
    test.test_no_parallels()
    test.test_same_direction_parallel()
    test.test_opposite_direction_parallel()
    print("✓ detect_parallel_arcs tests passed")
    
    # Test offset calculation
    test = TestCalculateArcOffset()
    test.test_no_parallels_zero_offset()
    test.test_two_arcs_opposite_direction()
    test.test_two_arcs_same_direction()
    test.test_three_arcs_same_direction()
    test.test_four_arcs_distribution()
    print("✓ calculate_arc_offset tests passed")
    
    # Test convenience functions
    test = TestCountParallelArcs()
    test.test_count_no_parallels()
    test.test_count_multiple_parallels()
    print("✓ count_parallel_arcs tests passed")
    
    test = TestHasParallelArcs()
    test.test_has_no_parallels()
    test.test_has_parallels()
    print("✓ has_parallel_arcs tests passed")
    
    test = TestGetArcOffsetForRendering()
    test.test_convenience_function()
    print("✓ get_arc_offset_for_rendering tests passed")
    
    test = TestSeparateParallelArcsByDirection()
    test.test_separate_same_and_opposite()
    test.test_separate_only_same()
    test.test_separate_only_opposite()
    print("✓ separate_parallel_arcs_by_direction tests passed")
    
    # Test integration scenarios
    test = TestIntegrationScenarios()
    test.test_simple_bidirectional()
    test.test_complex_network()
    print("✓ integration scenario tests passed")
    
    print("\n✅ All arc geometry service tests passed!")
