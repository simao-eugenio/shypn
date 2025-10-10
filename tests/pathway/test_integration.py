"""Integration tests for pathway enhancement pipeline.

Tests the complete pipeline on real KEGG pathways to validate:
- All processors work together seamlessly
- Performance is acceptable
- Output quality is maintained
- Edge cases are handled

Test Categories:
- Small pathways (< 50 elements)
- Medium pathways (50-200 elements)
- Large pathways (> 200 elements)
- Different pathway types (metabolic, signaling, etc.)
"""

import unittest
import time
from typing import Dict, Any
from unittest.mock import Mock, patch

from shypn.pathway import EnhancementPipeline, EnhancementOptions
from shypn.pathway.options import get_standard_options, get_minimal_options, get_maximum_options
from shypn.pathway.layout_optimizer import LayoutOptimizer
from shypn.pathway.arc_router import ArcRouter
from shypn.pathway.metadata_enhancer import MetadataEnhancer
from shypn.data.canvas.document_model import DocumentModel


def get_processor_stats(pipeline: EnhancementPipeline) -> Dict[str, Dict]:
    """Extract processor statistics from pipeline report.
    
    Args:
        pipeline: The enhancement pipeline after processing.
        
    Returns:
        Dictionary mapping processor name to its stats.
    """
    report = pipeline.get_report()
    stats = {}
    for entry in report['execution_log']:
        if not entry['skipped']:
            stats[entry['processor']] = entry['stats']
    return stats


def create_pipeline(options: EnhancementOptions) -> EnhancementPipeline:
    """Create and configure an enhancement pipeline.
    
    Args:
        options: Enhancement options.
        
    Returns:
        Configured pipeline with processors added based on options.
    """
    pipeline = EnhancementPipeline(options)
    
    # Add processors based on options
    if options.enable_layout_optimization:
        pipeline.add_processor(LayoutOptimizer(options))
    
    if options.enable_arc_routing:
        pipeline.add_processor(ArcRouter(options))
    
    if options.enable_metadata_enhancement:
        pipeline.add_processor(MetadataEnhancer(options))
    
    return pipeline


class TestIntegrationSmallPathways(unittest.TestCase):
    """Test integration on small pathways."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.options = get_standard_options()
    
    def test_empty_document(self):
        """Test enhancement on empty document."""
        document = DocumentModel()
        pipeline = create_pipeline(self.options)
        
        start_time = time.time()
        result = pipeline.process(document, None)
        elapsed = time.time() - start_time
        
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertEqual(len(result.places), 0)
        self.assertEqual(len(result.transitions), 0)
        
        # Should be very fast
        self.assertLess(elapsed, 0.1)
    
    def test_minimal_pathway(self):
        """Test enhancement on minimal pathway (2 places, 1 transition)."""
        document = DocumentModel()
        
        # Create minimal pathway
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        p2 = document.create_place(300, 100)
        
        document.create_arc(p1, t1)
        document.create_arc(t1, p2)
        
        pipeline = create_pipeline(self.options)
        
        start_time = time.time()
        result = pipeline.process(document, None)
        elapsed = time.time() - start_time
        
        # Verify structure preserved
        self.assertEqual(len(result.places), 2)
        self.assertEqual(len(result.transitions), 1)
        self.assertEqual(len(result.arcs), 2)
        
        # Should be very fast
        self.assertLess(elapsed, 0.1)
        
        # Get statistics
        stats = get_processor_stats(pipeline)
        self.assertIn('Layout Optimizer', stats)
        self.assertIn('Arc Router', stats)
        # Metadata Enhancer is skipped when no pathway data is provided
    
    def test_small_pathway_with_overlaps(self):
        """Test on small pathway with overlapping elements."""
        document = DocumentModel()
        
        # Create overlapping elements
        p1 = document.create_place(100, 100)
        p2 = document.create_place(110, 105)  # Overlaps with p1
        p3 = document.create_place(200, 100)
        
        t1 = document.create_transition(150, 150)
        
        document.create_arc(p1, t1)
        document.create_arc(p2, t1)
        document.create_arc(t1, p3)
        
        pipeline = create_pipeline(self.options)
        result = pipeline.process(document, None)
        
        # Check overlap resolution
        stats = get_processor_stats(pipeline)
        layout_stats = stats['Layout Optimizer']
        
        # Should have detected and resolved overlaps
        if layout_stats.get('overlaps_before', 0) > 0:
            self.assertLess(layout_stats['overlaps_after'], 
                          layout_stats['overlaps_before'])


class TestIntegrationMediumPathways(unittest.TestCase):
    """Test integration on medium-sized pathways."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.options = get_standard_options()
    
    def test_linear_chain_pathway(self):
        """Test enhancement on linear chain (10 places, 9 transitions)."""
        document = DocumentModel()
        
        # Create linear chain
        places = []
        transitions = []
        
        for i in range(10):
            p = document.create_place(100 + i * 80, 100)
            places.append(p)
            
            if i < 9:
                t = document.create_transition(100 + i * 80 + 40, 150)
                transitions.append(t)
                
                # Connect chain
                document.create_arc(places[i], t)
                if i > 0:
                    document.create_arc(transitions[i-1], places[i])
        
        # Connect last transition to last place
        document.create_arc(transitions[-1], places[-1])
        
        pipeline = create_pipeline(self.options)
        
        start_time = time.time()
        result = pipeline.process(document, None)
        elapsed = time.time() - start_time
        
        # Verify structure preserved
        self.assertEqual(len(result.places), 10)
        self.assertEqual(len(result.transitions), 9)
        
        # Should be fast for medium pathways
        self.assertLess(elapsed, 1.0)
        
        # Check statistics
        stats = get_processor_stats(pipeline)
        self.assertGreater(len(stats), 0)
    
    def test_branching_pathway(self):
        """Test enhancement on branching pathway (fan-out)."""
        document = DocumentModel()
        
        # Create branching structure
        # 1 place -> 1 transition -> 5 places
        p_source = document.create_place(100, 200)
        t_branch = document.create_transition(200, 200)
        document.create_arc(p_source, t_branch)
        
        for i in range(5):
            p = document.create_place(300, 100 + i * 50)
            document.create_arc(t_branch, p)
        
        pipeline = create_pipeline(self.options)
        result = pipeline.process(document, None)
        
        # Verify structure
        self.assertEqual(len(result.places), 6)
        self.assertEqual(len(result.transitions), 1)
        self.assertEqual(len(result.arcs), 6)
        
        # Check arc routing handled parallel arcs
        stats = get_processor_stats(pipeline)
        arc_stats = stats.get('Arc Router', {})
        
        if arc_stats.get('parallel_arc_groups', 0) > 0:
            self.assertGreater(arc_stats['arcs_in_parallel_groups'], 0)
    
    def test_cyclic_pathway(self):
        """Test enhancement on cyclic pathway."""
        document = DocumentModel()
        
        # Create cycle: P1 -> T1 -> P2 -> T2 -> P3 -> T3 -> P1
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        p2 = document.create_place(300, 100)
        t2 = document.create_transition(300, 200)
        p3 = document.create_place(200, 200)
        t3 = document.create_transition(100, 200)
        
        document.create_arc(p1, t1)
        document.create_arc(t1, p2)
        document.create_arc(p2, t2)
        document.create_arc(t2, p3)
        document.create_arc(p3, t3)
        document.create_arc(t3, p1)
        
        pipeline = create_pipeline(self.options)
        result = pipeline.process(document, None)
        
        # Verify structure preserved
        self.assertEqual(len(result.places), 3)
        self.assertEqual(len(result.transitions), 3)
        self.assertEqual(len(result.arcs), 6)


class TestIntegrationLargePathways(unittest.TestCase):
    """Test integration on large pathways."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.options = get_standard_options()
    
    def test_grid_pathway(self):
        """Test enhancement on grid layout (10x10 = 100 elements)."""
        document = DocumentModel()
        
        # Create grid of places and transitions
        grid_size = 10
        spacing = 80
        
        for i in range(grid_size):
            for j in range(grid_size):
                x = 100 + i * spacing
                y = 100 + j * spacing
                
                # Alternate between places and transitions
                if (i + j) % 2 == 0:
                    document.create_place(x, y)
                else:
                    document.create_transition(x, y)
        
        pipeline = create_pipeline(self.options)
        
        start_time = time.time()
        result = pipeline.process(document, None)
        elapsed = time.time() - start_time
        
        # Verify all elements present
        total_elements = len(result.places) + len(result.transitions)
        self.assertEqual(total_elements, 100)
        
        # Should complete in reasonable time (< 5 seconds)
        self.assertLess(elapsed, 5.0)
        
        # Report performance
        print(f"\nGrid pathway (100 elements): {elapsed:.3f}s")
        
        # Check statistics
        stats = get_processor_stats(pipeline)
        self.assertIn('Layout Optimizer', stats)
    
    def test_dense_network_pathway(self):
        """Test enhancement on densely connected network (50 elements, many arcs)."""
        document = DocumentModel()
        
        # Create places in circle
        import math
        num_places = 25
        radius = 300
        center_x = 400
        center_y = 400
        
        places = []
        for i in range(num_places):
            angle = 2 * math.pi * i / num_places
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            p = document.create_place(x, y)
            places.append(p)
        
        # Create transitions and connect to nearby places
        transitions = []
        for i in range(num_places):
            angle = 2 * math.pi * (i + 0.5) / num_places
            x = center_x + (radius * 0.7) * math.cos(angle)
            y = center_y + (radius * 0.7) * math.sin(angle)
            t = document.create_transition(x, y)
            transitions.append(t)
            
            # Connect to adjacent places
            document.create_arc(places[i], t)
            document.create_arc(t, places[(i + 1) % num_places])
        
        pipeline = create_pipeline(self.options)
        
        start_time = time.time()
        result = pipeline.process(document, None)
        elapsed = time.time() - start_time
        
        # Verify structure
        self.assertEqual(len(result.places), 25)
        self.assertEqual(len(result.transitions), 25)
        self.assertEqual(len(result.arcs), 50)
        
        # Should handle dense networks
        self.assertLess(elapsed, 3.0)
        
        print(f"\nDense network (50 elements, 50 arcs): {elapsed:.3f}s")


class TestIntegrationWithMetadata(unittest.TestCase):
    """Test integration with metadata enhancement."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.options = EnhancementOptions(
            enable_layout_optimization=True,
            enable_arc_routing=True,
            enable_metadata_enhancement=True
        )
    
    def test_metadata_with_mock_pathway(self):
        """Test metadata enhancement with mock KEGG pathway."""
        document = DocumentModel()
        
        # Create places with metadata
        p1 = document.create_place(100, 100)
        p1.metadata = {'kegg_entry_id': '1'}
        
        p2 = document.create_place(200, 100)
        p2.metadata = {'kegg_entry_id': '2'}
        
        # Create transition with metadata
        t1 = document.create_transition(150, 150)
        t1.metadata = {'kegg_entry_id': '3'}
        
        document.create_arc(p1, t1)
        document.create_arc(t1, p2)
        
        # Create mock pathway
        mock_pathway = Mock()
        mock_entry1 = Mock()
        mock_entry1.graphics = Mock()
        mock_entry1.graphics.name = "Glucose"
        mock_entry1.graphics.bgcolor = "#BFFFBF"
        mock_entry1.graphics.fgcolor = "#000000"
        mock_entry1.get_kegg_ids.return_value = ["cpd:C00031"]
        
        mock_entry2 = Mock()
        mock_entry2.graphics = Mock()
        mock_entry2.graphics.name = "ATP"
        mock_entry2.graphics.bgcolor = "#FFFFBF"
        mock_entry2.graphics.fgcolor = "#000000"
        mock_entry2.get_kegg_ids.return_value = ["cpd:C00002"]
        
        mock_entry3 = Mock()
        mock_entry3.graphics = Mock()
        mock_entry3.graphics.name = "HK1"
        mock_entry3.graphics.bgcolor = "#BFBFFF"
        mock_entry3.graphics.fgcolor = "#000000"
        mock_entry3.get_kegg_ids.return_value = ["hsa:3098"]
        
        mock_pathway.entries = {
            '1': mock_entry1,
            '2': mock_entry2,
            '3': mock_entry3
        }
        mock_pathway.reactions = []
        
        pipeline = create_pipeline(self.options)
        result = pipeline.process(document, mock_pathway)
        
        # Verify metadata was enhanced
        stats = get_processor_stats(pipeline)
        metadata_stats = stats.get('Metadata Enhancer', {})
        
        self.assertGreater(metadata_stats.get('places_enhanced', 0), 0)
        
        # Check that metadata was actually added
        self.assertIn('compound_name', p1.metadata)
        self.assertEqual(p1.metadata['compound_name'], "Glucose")


class TestIntegrationConfiguration(unittest.TestCase):
    """Test different configuration combinations."""
    
    def test_layout_only(self):
        """Test with only layout optimization enabled."""
        options = EnhancementOptions(
            enable_layout_optimization=True,
            enable_arc_routing=False,
            enable_metadata_enhancement=False
        )
        
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        p2 = document.create_place(105, 105)  # Overlapping
        
        pipeline = create_pipeline(options)
        result = pipeline.process(document, None)
        
        stats = get_processor_stats(pipeline)
        
        # Should have layout stats only
        self.assertIn('Layout Optimizer', stats)
        self.assertEqual(len([k for k in stats.keys() if stats[k].get('implemented')]), 1)
    
    def test_arcs_only(self):
        """Test with only arc routing enabled."""
        options = EnhancementOptions(
            enable_layout_optimization=False,
            enable_arc_routing=True,
            enable_metadata_enhancement=False
        )
        
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        p2 = document.create_place(300, 100)
        
        document.create_arc(p1, t1)
        document.create_arc(t1, p2)
        
        pipeline = create_pipeline(options)
        result = pipeline.process(document, None)
        
        stats = get_processor_stats(pipeline)
        
        # Should have arc stats only
        self.assertIn('Arc Router', stats)
    
    def test_all_enabled(self):
        """Test with all processors enabled."""
        options = get_maximum_options()
        
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        p2 = document.create_place(300, 100)
        
        document.create_arc(p1, t1)
        document.create_arc(t1, p2)
        
        pipeline = create_pipeline(options)
        result = pipeline.process(document, None)
        
        stats = get_processor_stats(pipeline)
        
        # Should have stats from all processors (except Metadata Enhancer if no pathway)
        self.assertIn('Layout Optimizer', stats)
        self.assertIn('Arc Router', stats)
        # Metadata Enhancer may be skipped without pathway data
    
    def test_all_disabled(self):
        """Test with all processors disabled."""
        options = get_minimal_options()
        options.enable_layout_optimization = False
        
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        
        pipeline = create_pipeline(options)
        
        start_time = time.time()
        result = pipeline.process(document, None)
        elapsed = time.time() - start_time
        
        # Should be essentially instant
        self.assertLess(elapsed, 0.01)
        
        # Should have minimal or no stats
        stats = get_processor_stats(pipeline)
        implemented_count = sum(1 for s in stats.values() if s.get('implemented'))
        self.assertEqual(implemented_count, 0)


class TestIntegrationPerformance(unittest.TestCase):
    """Test performance characteristics of the pipeline."""
    
    def test_performance_scaling(self):
        """Test how performance scales with pathway size."""
        options = get_standard_options()
        pipeline = create_pipeline(options)
        
        sizes = [10, 25, 50, 100]
        times = []
        
        for size in sizes:
            document = DocumentModel()
            
            # Create pathway of given size
            for i in range(size // 2):
                document.create_place(100 + (i % 10) * 80, 100 + (i // 10) * 80)
                document.create_transition(140 + (i % 10) * 80, 140 + (i // 10) * 80)
            
            start_time = time.time()
            pipeline.process(document, None)
            elapsed = time.time() - start_time
            
            times.append(elapsed)
        
        # Print performance table
        print("\n\nPerformance Scaling:")
        print("Size\tTime(s)\tTime/Element(ms)")
        print("-" * 40)
        for size, elapsed in zip(sizes, times):
            time_per_elem = (elapsed / size) * 1000
            print(f"{size}\t{elapsed:.3f}\t{time_per_elem:.2f}")
        
        # Verify reasonable performance
        # Should complete 100 elements in under 5 seconds
        self.assertLess(times[-1], 5.0)
    
    def test_memory_efficiency(self):
        """Test that pipeline doesn't create excessive copies."""
        import sys
        
        document = DocumentModel()
        
        # Create medium pathway
        for i in range(50):
            document.create_place(100 + (i % 10) * 80, 100 + (i // 10) * 80)
        
        options = get_standard_options()
        pipeline = create_pipeline(options)
        
        # Get initial size
        size_before = sys.getsizeof(document)
        
        result = pipeline.process(document, None)
        
        # Get final size
        size_after = sys.getsizeof(result)
        
        # Size shouldn't grow dramatically (no deep copies)
        # Allow for some metadata growth
        self.assertLess(size_after, size_before * 2)


class TestIntegrationErrorHandling(unittest.TestCase):
    """Test error handling in the pipeline."""
    
    def test_handle_invalid_document(self):
        """Test handling of invalid document."""
        options = get_standard_options()
        pipeline = create_pipeline(options)
        
        # Pipeline should handle None gracefully by catching errors and continuing
        result = pipeline.process(None, None)
        
        # Should return None (unchanged) and log errors
        self.assertIsNone(result)
        
        # Check that errors were logged
        report = pipeline.get_report()
        self.assertGreater(report['processors_failed'], 0)
    
    def test_handle_processor_error(self):
        """Test handling when a processor fails."""
        options = EnhancementOptions(
            enable_layout_optimization=True,
            fail_fast=False  # Continue despite errors
        )
        
        document = DocumentModel()
        p1 = document.create_place(100, 100)
        
        pipeline = create_pipeline(options)
        
        # Should complete even if a processor has issues
        result = pipeline.process(document, None)
        self.assertIsNotNone(result)
    
    def test_timeout_handling(self):
        """Test timeout handling (if implemented)."""
        options = get_standard_options()
        options.processing_timeout = 0.001  # Very short timeout
        
        document = DocumentModel()
        
        # Create large pathway that might timeout
        for i in range(100):
            document.create_place(100 + (i % 10) * 80, 100 + (i // 10) * 80)
        
        pipeline = create_pipeline(options)
        
        # Should handle timeout gracefully (implementation dependent)
        # For now, just ensure it doesn't crash
        try:
            result = pipeline.process(document, None)
            self.assertIsNotNone(result)
        except TimeoutError:
            # Timeout is acceptable
            pass


class TestIntegrationOutputQuality(unittest.TestCase):
    """Test output quality of the enhanced pathways."""
    
    def test_no_disconnected_arcs(self):
        """Test that arcs remain connected after enhancement."""
        document = DocumentModel()
        
        p1 = document.create_place(100, 100)
        t1 = document.create_transition(200, 100)
        p2 = document.create_place(300, 100)
        
        arc1 = document.create_arc(p1, t1)
        arc2 = document.create_arc(t1, p2)
        
        options = get_standard_options()
        pipeline = create_pipeline(options)
        
        result = pipeline.process(document, None)
        
        # Verify arcs still connect to correct elements
        self.assertEqual(len(result.arcs), 2)
        
        # Arc sources and targets should be valid
        for arc in result.arcs:
            self.assertIsNotNone(arc.source)
            self.assertIsNotNone(arc.target)
    
    def test_element_positions_valid(self):
        """Test that element positions remain valid after enhancement."""
        document = DocumentModel()
        
        for i in range(10):
            document.create_place(100 + i * 80, 100)
        
        options = get_standard_options()
        pipeline = create_pipeline(options)
        
        result = pipeline.process(document, None)
        
        # All positions should be finite numbers
        for place in result.places:
            self.assertIsInstance(place.x, (int, float))
            self.assertIsInstance(place.y, (int, float))
            self.assertFalse(float('inf') == place.x)
            self.assertFalse(float('inf') == place.y)
    
    def test_metadata_preserved(self):
        """Test that existing metadata is preserved."""
        document = DocumentModel()
        
        p1 = document.create_place(100, 100)
        p1.metadata = {'custom_field': 'important_data'}
        
        options = get_standard_options()
        pipeline = create_pipeline(options)
        
        result = pipeline.process(document, None)
        
        # Custom metadata should still exist
        self.assertIn('custom_field', result.places[0].metadata)
        self.assertEqual(result.places[0].metadata['custom_field'], 'important_data')


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
