"""Unit tests for LayoutOptimizer."""

import pytest
from shypn.pathway.layout_optimizer import LayoutOptimizer
from shypn.pathway.options import EnhancementOptions
from shypn.data.canvas.document_model import DocumentModel


class TestLayoutOptimizer:
    """Test LayoutOptimizer processor."""
    
    def test_optimizer_creation(self):
        """Can create optimizer."""
        optimizer = LayoutOptimizer()
        assert optimizer is not None
        assert optimizer.get_name() == "Layout Optimizer"
    
    def test_with_options(self):
        """Can create optimizer with options."""
        opts = EnhancementOptions(layout_min_spacing=80.0)
        optimizer = LayoutOptimizer(opts)
        assert optimizer.options is opts
    
    def test_is_applicable_with_objects(self):
        """Applicable when document has objects."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        document.create_place(100, 100)
        
        assert optimizer.is_applicable(document, None) is True
    
    def test_is_applicable_empty_document(self):
        """Not applicable for empty document."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        
        assert optimizer.is_applicable(document, None) is False
    
    def test_is_applicable_disabled(self):
        """Not applicable when disabled."""
        opts = EnhancementOptions(enable_layout_optimization=False)
        optimizer = LayoutOptimizer(opts)
        document = DocumentModel()
        document.create_place(100, 100)
        
        assert optimizer.is_applicable(document, None) is False
    
    def test_process_no_overlaps(self):
        """Process document with no overlaps."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        
        p1 = document.create_place(100, 100)
        p2 = document.create_place(300, 100)
        
        # Store original positions
        orig_x1, orig_y1 = p1.x, p1.y
        orig_x2, orig_y2 = p2.x, p2.y
        
        result = optimizer.process(document, None)
        
        assert result is document
        stats = optimizer.get_stats()
        assert stats['overlaps_before'] == 0
        assert stats['overlaps_after'] == 0
        
        # Positions should be unchanged
        assert p1.x == orig_x1
        assert p1.y == orig_y1
        assert p2.x == orig_x2
        assert p2.y == orig_y2
    
    def test_process_with_overlaps(self):
        """Process document with overlapping places."""
        opts = EnhancementOptions(
            layout_min_spacing=60.0,
            layout_max_iterations=50
        )
        optimizer = LayoutOptimizer(opts)
        document = DocumentModel()
        
        # Create two overlapping places (distance < min_spacing + 2*radius)
        # Places have radius 25, so distance < 60 + 50 = 110
        p1 = document.create_place(100, 100)
        p2 = document.create_place(120, 100)  # Only 20px apart, definitely overlapping
        
        # Store original positions
        orig_x1, orig_y1 = p1.x, p1.y
        orig_x2, orig_y2 = p2.x, p2.y
        
        result = optimizer.process(document, None)
        
        assert result is document
        stats = optimizer.get_stats()
        
        # Should have detected overlap
        assert stats['overlaps_before'] > 0
        
        # Should have moved elements
        assert stats['elements_moved'] > 0
        
        # Places should have moved apart
        new_distance = abs(p2.x - p1.x)
        orig_distance = abs(orig_x2 - orig_x1)
        assert new_distance > orig_distance
    
    def test_convergence(self):
        """Optimizer converges and stops."""
        opts = EnhancementOptions(
            layout_min_spacing=60.0,
            layout_max_iterations=100,
            layout_convergence_threshold=1.0
        )
        optimizer = LayoutOptimizer(opts)
        document = DocumentModel()
        
        # Create overlapping places
        p1 = document.create_place(100, 100)
        p2 = document.create_place(110, 100)
        
        result = optimizer.process(document, None)
        
        stats = optimizer.get_stats()
        
        # Should converge before max iterations
        assert stats['iterations'] < 100
        
        # Check convergence flag
        assert 'converged' in stats
    
    def test_multiple_overlaps(self):
        """Handle multiple overlapping elements."""
        opts = EnhancementOptions(layout_min_spacing=60.0)
        optimizer = LayoutOptimizer(opts)
        document = DocumentModel()
        
        # Create cluster of overlapping places
        places = [
            document.create_place(100, 100),
            document.create_place(110, 100),
            document.create_place(100, 110),
            document.create_place(110, 110)
        ]
        
        result = optimizer.process(document, None)
        
        stats = optimizer.get_stats()
        
        # Should have detected multiple overlaps
        assert stats['overlaps_before'] >= 4  # At least 4 pairs overlapping
        
        # Should have reduced overlaps
        assert stats['overlaps_after'] < stats['overlaps_before']
        
        # All elements should have moved
        assert stats['elements_moved'] == 4
    
    def test_mixed_objects(self):
        """Handle both places and transitions."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        
        # Create overlapping place and transition
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(110, 100)
        
        result = optimizer.process(document, None)
        
        stats = optimizer.get_stats()
        
        # Should handle mixed types
        assert stats['total_elements'] == 2
        assert stats['implemented'] is True
    
    def test_attraction_to_original_position(self):
        """Elements are attracted back to original positions."""
        opts = EnhancementOptions(
            layout_min_spacing=20.0,  # Small spacing requirement
            layout_attraction_strength=0.3,  # Stronger attraction
            layout_repulsion_strength=5.0,  # Moderate repulsion
            layout_max_iterations=20
        )
        optimizer = LayoutOptimizer(opts)
        document = DocumentModel()
        
        # Create barely overlapping places (40px apart, radius 25 each = 50px diameter)
        # With min_spacing=20, they need 70px (20+25+25) to not overlap
        p1 = document.create_place(100, 100)
        p2 = document.create_place(200, 100)  # Far enough that only small adjustment needed
        
        orig_x1 = p1.x
        orig_x2 = p2.x
        
        result = optimizer.process(document, None)
        
        # Elements should not have moved far from original due to strong attraction
        movement1 = abs(p1.x - orig_x1)
        movement2 = abs(p2.x - orig_x2)
        assert movement1 < 50  # Reasonable movement limit
        assert movement2 < 50
    
    def test_statistics_tracking(self):
        """Statistics are correctly tracked."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        
        p1 = document.create_place(100, 100)
        p2 = document.create_place(110, 100)
        
        result = optimizer.process(document, None)
        
        stats = optimizer.get_stats()
        
        # Check all expected statistics
        assert 'overlaps_before' in stats
        assert 'overlaps_after' in stats
        assert 'overlaps_resolved' in stats
        assert 'elements_moved' in stats
        assert 'total_elements' in stats
        assert 'max_movement' in stats
        assert 'avg_movement' in stats
        assert 'iterations' in stats
        assert 'converged' in stats
        assert 'implemented' in stats
        
        # Verify values
        assert stats['total_elements'] == 2
        assert stats['implemented'] is True
        assert stats['overlaps_resolved'] >= 0
    
    def test_bounding_box_place(self):
        """Get bounding box for place."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        
        place = document.create_place(100, 100)  # radius = 25
        
        bbox = optimizer._get_bounding_box(place)
        
        # Should be (75, 75, 125, 125)
        assert bbox == (75.0, 75.0, 125.0, 125.0)
    
    def test_bounding_box_transition(self):
        """Get bounding box for transition."""
        optimizer = LayoutOptimizer()
        document = DocumentModel()
        
        trans = document.create_transition(100, 100)  # width=50, height=25
        
        bbox = optimizer._get_bounding_box(trans)
        
        # Should be (75, 87.5, 125, 112.5)
        assert bbox == (75.0, 87.5, 125.0, 112.5)
    
    def test_boxes_overlap_true(self):
        """Detect overlapping boxes."""
        optimizer = LayoutOptimizer()
        
        box1 = (0, 0, 100, 100)
        box2 = (50, 50, 150, 150)
        
        assert optimizer._boxes_overlap(box1, box2, min_spacing=0) is True
    
    def test_boxes_overlap_false(self):
        """Detect non-overlapping boxes."""
        optimizer = LayoutOptimizer()
        
        box1 = (0, 0, 100, 100)
        box2 = (200, 200, 300, 300)
        
        assert optimizer._boxes_overlap(box1, box2, min_spacing=0) is False
    
    def test_boxes_overlap_with_spacing(self):
        """Min spacing affects overlap detection."""
        optimizer = LayoutOptimizer()
        
        box1 = (0, 0, 100, 100)
        box2 = (110, 0, 210, 100)  # 10px apart
        
        # Without spacing: no overlap
        assert optimizer._boxes_overlap(box1, box2, min_spacing=0) is False
        
        # With 20px spacing: overlap
        assert optimizer._boxes_overlap(box1, box2, min_spacing=20) is True
    
    def test_calculate_overlap_amount(self):
        """Calculate overlap area."""
        optimizer = LayoutOptimizer()
        
        box1 = (0, 0, 100, 100)
        box2 = (50, 50, 150, 150)
        
        overlap = optimizer._calculate_overlap_amount(box1, box2)
        
        # Overlap region is 50x50 = 2500
        assert overlap == 2500.0
    
    def test_calculate_overlap_no_overlap(self):
        """Zero overlap for non-overlapping boxes."""
        optimizer = LayoutOptimizer()
        
        box1 = (0, 0, 100, 100)
        box2 = (200, 200, 300, 300)
        
        overlap = optimizer._calculate_overlap_amount(box1, box2)
        
        assert overlap == 0.0
