"""Tests for ArcRouter processor.

Tests cover:
- Arc router creation and configuration
- Applicability checks
- Parallel arc detection and grouping
- Control point calculation for parallel arcs
- Obstacle detection along arc paths
- Obstacle avoidance routing
- Edge cases and error handling
"""

import unittest
import math
from shypn.pathway.arc_router import ArcRouter
from shypn.pathway.options import EnhancementOptions
from shypn.data.canvas.document_model import DocumentModel


class TestArcRouterCreation(unittest.TestCase):
    """Test arc router creation and configuration."""
    
    def test_create_with_default_options(self):
        """Test creating arc router with default options."""
        router = ArcRouter()
        self.assertIsNotNone(router)
        self.assertEqual(router.get_name(), "Arc Router")
    
    def test_create_with_custom_options(self):
        """Test creating arc router with custom options."""
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_curve_style='curved',
            arc_parallel_offset=40.0,
            arc_obstacle_clearance=25.0
        )
        router = ArcRouter(options)
        self.assertIsNotNone(router)
        self.assertEqual(router.options.arc_parallel_offset, 40.0)
        self.assertEqual(router.options.arc_obstacle_clearance, 25.0)


class TestArcRouterApplicability(unittest.TestCase):
    """Test arc router applicability checks."""
    
    def test_applicable_with_arcs(self):
        """Test router is applicable when document has arcs."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        document.create_arc(p1, t1)
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        
        self.assertTrue(router.is_applicable(document))
    
    def test_not_applicable_without_arcs(self):
        """Test router is not applicable when document has no arcs."""
        document = DocumentModel()
        document.create_place(100, 100)
        document.create_transition(200, 100)
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        
        self.assertFalse(router.is_applicable(document))
    
    def test_not_applicable_when_disabled(self):
        """Test router is not applicable when disabled in options."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        document.create_arc(p1, t1)
        
        options = EnhancementOptions(enable_arc_routing=False)
        router = ArcRouter(options)
        
        self.assertFalse(router.is_applicable(document))


class TestParallelArcDetection(unittest.TestCase):
    """Test parallel arc detection and grouping."""
    
    def test_no_parallel_arcs(self):
        """Test with no parallel arcs (all unique source/target pairs)."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        p2 = document.create_place(300, 100)
        t1 = document.create_transition(200, 200)
        
        document.create_arc(p1, t1)
        document.create_arc(t1, p2)
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        document = router.process(document)
        
        self.assertEqual(router.stats['parallel_arc_groups'], 0)
        self.assertEqual(router.stats['arcs_in_parallel_groups'], 0)
    
    def test_two_parallel_arcs(self):
        """Test with two parallel arcs (same source/target)."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(p1, t1)
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_parallel_offset=30.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Should have 1 parallel group with 2 arcs
        self.assertEqual(router.stats['parallel_arc_groups'], 1)
        self.assertEqual(router.stats['arcs_in_parallel_groups'], 2)
        
        # Both arcs should be curved
        self.assertTrue(arc1.is_curved)
        self.assertTrue(arc2.is_curved)
        
        # Offsets should be symmetric
        self.assertAlmostEqual(arc1.control_offset_x, -arc2.control_offset_x, places=5)
        self.assertAlmostEqual(arc1.control_offset_y, -arc2.control_offset_y, places=5)
    
    def test_three_parallel_arcs(self):
        """Test with three parallel arcs."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(p1, t1)
        arc3 = document.create_arc(p1, t1)
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_parallel_offset=30.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # All should be curved
        self.assertTrue(arc1.is_curved)
        self.assertTrue(arc2.is_curved)
        self.assertTrue(arc3.is_curved)
        
        # Middle arc should have near-zero offset (centered)
        self.assertLess(abs(arc2.control_offset_x**2 + arc2.control_offset_y**2), 1e-6)
        
        # First and third should be symmetric
        self.assertAlmostEqual(arc1.control_offset_x, -arc3.control_offset_x, places=5)
        self.assertAlmostEqual(arc1.control_offset_y, -arc3.control_offset_y, places=5)
    
    def test_bidirectional_arcs_not_parallel(self):
        """Test that bidirectional arcs (A→B and B→A) are not considered parallel."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(t1, p1)
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        document = router.process(document)
        
        # Should not be grouped as parallel (different source/target pairs)
        self.assertEqual(router.stats['parallel_arc_groups'], 0)


class TestControlPointCalculation(unittest.TestCase):
    """Test control point calculation for curved arcs."""
    
    def test_perpendicular_offset_horizontal_arc(self):
        """Test perpendicular offset for horizontal arc."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(p1, t1)
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_parallel_offset=30.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # For horizontal arc (left to right), perpendicular is vertical
        # Arc 1 should have negative Y offset (upward)
        # Arc 2 should have positive Y offset (downward)
        self.assertLess(arc1.control_offset_y, 0)
        self.assertGreater(arc2.control_offset_y, 0)
        
        # X offsets should be near zero for horizontal arc
        self.assertLess(abs(arc1.control_offset_x), 1.0)
        self.assertLess(abs(arc2.control_offset_x), 1.0)
    
    def test_perpendicular_offset_vertical_arc(self):
        """Test perpendicular offset for vertical arc."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(100, 300)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(p1, t1)
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_parallel_offset=30.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # For vertical arc (top to bottom), perpendicular is horizontal
        # Arc 1 should have positive X offset (rightward, based on CCW perpendicular)
        # Arc 2 should have negative X offset (leftward)
        self.assertGreater(arc1.control_offset_x, 0)
        self.assertLess(arc2.control_offset_x, 0)
        
        # Y offsets should be near zero for vertical arc
        self.assertLess(abs(arc1.control_offset_y), 1.0)
        self.assertLess(abs(arc2.control_offset_y), 1.0)
    
    def test_offset_magnitude(self):
        """Test that offset magnitude is proportional to arc_parallel_offset."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(p1, t1)
        
        offset_amount = 50.0
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_parallel_offset=offset_amount
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Offset magnitude should be approximately offset_amount/2 for 2 arcs
        magnitude1 = math.sqrt(arc1.control_offset_x**2 + arc1.control_offset_y**2)
        magnitude2 = math.sqrt(arc2.control_offset_x**2 + arc2.control_offset_y**2)
        
        expected = offset_amount / 2
        self.assertAlmostEqual(magnitude1, expected, places=1)
        self.assertAlmostEqual(magnitude2, expected, places=1)


class TestObstacleDetection(unittest.TestCase):
    """Test obstacle detection along arc paths."""
    
    def test_no_obstacles(self):
        """Test arc with no obstacles along path."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        arc = document.create_arc(p1, t1)
        
        # Add obstacle far away
        document.create_place(200, 300)
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_obstacle_clearance=20.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Arc should not be curved (no obstacles)
        self.assertFalse(arc.is_curved)
    
    def test_obstacle_on_path(self):
        """Test arc with obstacle directly on path."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        arc = document.create_arc(p1, t1)
        
        # Add obstacle directly on arc path (midpoint)
        obstacle = document.create_place(200, 100)
        obstacle.radius = 15.0
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_obstacle_clearance=20.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Arc should be curved to avoid obstacle
        self.assertTrue(arc.is_curved)
        self.assertEqual(router.stats['arcs_routed_around_obstacles'], 1)
    
    def test_obstacle_near_path(self):
        """Test arc with obstacle near (but not on) path."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        arc = document.create_arc(p1, t1)
        
        # Add obstacle close to arc path
        obstacle = document.create_place(200, 125)  # 25 pixels away
        obstacle.radius = 15.0
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_obstacle_clearance=20.0  # 15 + 20 = 35 > 25, so detected
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Arc should be curved to avoid obstacle
        self.assertTrue(arc.is_curved)
    
    def test_source_and_target_not_obstacles(self):
        """Test that source and target are not detected as obstacles."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        arc = document.create_arc(p1, t1)
        
        # No other elements
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        document = router.process(document)
        
        # Arc should not be curved (source/target don't count as obstacles)
        self.assertFalse(arc.is_curved)


class TestObstacleAvoidanceRouting(unittest.TestCase):
    """Test obstacle avoidance routing."""
    
    def test_route_around_obstacle_above(self):
        """Test routing around obstacle above arc path."""
        document = DocumentModel()
        p1 = document.create_place(100, 200)
        t1 = document.create_transition(300, 200)
        arc = document.create_arc(p1, t1)
        
        # Obstacle above arc path
        obstacle = document.create_place(200, 180)  # 20 pixels above
        obstacle.radius = 15.0
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_obstacle_clearance=20.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Arc should curve downward (away from obstacle)
        self.assertTrue(arc.is_curved)
        self.assertGreater(arc.control_offset_y, 0)  # Positive Y = downward
    
    def test_route_around_obstacle_below(self):
        """Test routing around obstacle below arc path."""
        document = DocumentModel()
        p1 = document.create_place(100, 200)
        t1 = document.create_transition(300, 200)
        arc = document.create_arc(p1, t1)
        
        # Obstacle below arc path
        obstacle = document.create_place(200, 220)  # 20 pixels below
        obstacle.radius = 15.0
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_obstacle_clearance=20.0
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Arc should curve upward (away from obstacle)
        self.assertTrue(arc.is_curved)
        self.assertLess(arc.control_offset_y, 0)  # Negative Y = upward
    
    def test_clearance_affects_offset(self):
        """Test that obstacle clearance affects offset magnitude."""
        document = DocumentModel()
        p1 = document.create_place(100, 200)
        t1 = document.create_transition(300, 200)
        arc = document.create_arc(p1, t1)
        
        # Obstacle on arc path
        obstacle = document.create_place(200, 200)
        obstacle.radius = 15.0
        
        clearance = 30.0  # Large clearance
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_obstacle_clearance=clearance
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # Offset should be at least radius + clearance
        offset_magnitude = math.sqrt(
            arc.control_offset_x**2 + arc.control_offset_y**2)
        
        min_expected = obstacle.radius + clearance
        self.assertGreaterEqual(offset_magnitude, min_expected * 0.9)  # Allow 10% tolerance


class TestStraightCurveStyle(unittest.TestCase):
    """Test straight curve style (no curves applied)."""
    
    def test_straight_style_no_curves(self):
        """Test that straight style keeps all arcs straight."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        
        # Create parallel arcs
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(p1, t1)
        
        options = EnhancementOptions(
            enable_arc_routing=True,
            arc_curve_style='straight'  # Force straight
        )
        router = ArcRouter(options)
        document = router.process(document)
        
        # No arcs should be curved
        self.assertFalse(arc1.is_curved)
        self.assertFalse(arc2.is_curved)
        self.assertEqual(router.stats['arcs_with_curves'], 0)


class TestStatistics(unittest.TestCase):
    """Test statistics collection."""
    
    def test_statistics_structure(self):
        """Test that all expected statistics are present."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(300, 100)
        document.create_arc(p1, t1)
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        document = router.process(document)
        
        # Check all expected stats keys
        self.assertIn('total_arcs', router.stats)
        self.assertIn('parallel_arc_groups', router.stats)
        self.assertIn('arcs_in_parallel_groups', router.stats)
        self.assertIn('arcs_with_curves', router.stats)
        self.assertIn('arcs_routed_around_obstacles', router.stats)
        self.assertIn('avg_parallel_group_size', router.stats)
        self.assertIn('implemented', router.stats)
        
        # Check implemented flag
        self.assertTrue(router.stats['implemented'])
    
    def test_statistics_accuracy(self):
        """Test statistics accuracy with known scenario."""
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        p2 = document.create_place(300, 100)
        t1 = document.create_transition(500, 100)
        
        # Create 2 parallel arcs
        document.create_arc(p1, t1)
        document.create_arc(p1, t1)
        
        # Create 1 normal arc
        document.create_arc(p2, t1)
        
        options = EnhancementOptions(enable_arc_routing=True)
        router = ArcRouter(options)
        document = router.process(document)
        
        # Verify statistics
        self.assertEqual(router.stats['total_arcs'], 3)
        self.assertEqual(router.stats['parallel_arc_groups'], 1)
        self.assertEqual(router.stats['arcs_in_parallel_groups'], 2)
        self.assertEqual(router.stats['arcs_with_curves'], 2)  # Only parallel ones
        self.assertAlmostEqual(router.stats['avg_parallel_group_size'], 2.0)


if __name__ == '__main__':
    unittest.main()
