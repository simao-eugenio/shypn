"""Test NumPy threading configuration for invariant analysis."""

import unittest
import time
import os
from shypn.data.canvas.document_model import DocumentModel
from shypn.topology.structural.p_invariants import PInvariantAnalyzer
from shypn.topology.structural.t_invariants import TInvariantAnalyzer


class TestParallelInvariants(unittest.TestCase):
    """Test NumPy threading for invariant analysis."""
    
    def setUp(self):
        """Create test model with invariants."""
        self.model = DocumentModel()
        
        # Create a model with known P-invariant
        # Classic producer-consumer pattern: P1 + P2 = constant
        self.p1 = self.model.create_place(100, 100, label="P1")
        self.p1.tokens = 5
        self.p2 = self.model.create_place(300, 100, label="P2")
        self.p2.tokens = 5
        
        # T1: P1 -> P2
        t1 = self.model.create_transition(200, 50)
        self.model.create_arc(self.p1, t1, weight=1)
        self.model.create_arc(t1, self.p2, weight=1)
        
        # T2: P2 -> P1
        t2 = self.model.create_transition(200, 150)
        self.model.create_arc(self.p2, t2, weight=1)
        self.model.create_arc(t2, self.p1, weight=1)
        
        # P-invariant should be [1, 1] (P1 + P2 = 10)
    
    def test_thread_configuration(self):
        """Test that thread configuration doesn't break analysis."""
        analyzer = PInvariantAnalyzer(self.model)
        
        # Test with different thread counts
        for num_threads in [1, 2, 4]:
            result = analyzer.analyze(num_threads=num_threads)
            
            self.assertTrue(result.success, f"Failed with {num_threads} threads")
            invariants = result.get('p_invariants', [])
            self.assertGreater(len(invariants), 0, "Should find at least one invariant")
    
    def test_auto_threading(self):
        """Test automatic thread detection (None)."""
        analyzer = PInvariantAnalyzer(self.model)
        
        # None should use default NumPy threading
        result = analyzer.analyze(num_threads=None)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.get('p_invariants', [])), 0)
    
    def test_thread_settings_restored(self):
        """Test that thread settings are restored after analysis."""
        # Set custom environment before test
        os.environ['OMP_NUM_THREADS'] = '99'
        
        analyzer = PInvariantAnalyzer(self.model)
        
        # Run with different thread count
        result = analyzer.analyze(num_threads=2)
        
        self.assertTrue(result.success)
        
        # Environment should be restored
        self.assertEqual(os.environ.get('OMP_NUM_THREADS'), '99')
        
        # Clean up
        del os.environ['OMP_NUM_THREADS']
    
    def test_threading_correctness(self):
        """Test that threading doesn't change results."""
        analyzer = PInvariantAnalyzer(self.model)
        
        # Analyze with different thread counts
        result_1 = analyzer.analyze(num_threads=1)
        result_4 = analyzer.analyze(num_threads=4)
        
        self.assertTrue(result_1.success)
        self.assertTrue(result_4.success)
        
        # Should find same invariants
        inv_1 = result_1.get('p_invariants', [])
        inv_4 = result_4.get('p_invariants', [])
        
        self.assertEqual(len(inv_1), len(inv_4))
        
        # Check that invariants match (order may differ)
        vectors_1 = {tuple(inv['vector']) for inv in inv_1}
        vectors_4 = {tuple(inv['vector']) for inv in inv_4}
        self.assertEqual(vectors_1, vectors_4)
    
    def test_large_matrix_threading(self):
        """Test threading benefit on larger matrices."""
        # Create a larger model with more places
        large_model = DocumentModel()
        
        # Create 20 places in circular conservation pattern
        places = [large_model.create_place(i*50, 100) for i in range(20)]
        for p in places:
            p.tokens = 1
        
        # Create transitions in a cycle
        for i in range(20):
            trans = large_model.create_transition(i*50, 200)
            large_model.create_arc(places[i], trans, weight=1)
            large_model.create_arc(trans, places[(i+1) % 20], weight=1)
        
        analyzer = PInvariantAnalyzer(large_model)
        
        # Measure with 1 thread
        start_1 = time.perf_counter()
        result_1 = analyzer.analyze(num_threads=1, max_invariants=50)
        time_1 = time.perf_counter() - start_1
        
        # Measure with 4 threads
        start_4 = time.perf_counter()
        result_4 = analyzer.analyze(num_threads=4, max_invariants=50)
        time_4 = time.perf_counter() - start_4
        
        self.assertTrue(result_1.success)
        self.assertTrue(result_4.success)
        
        print(f"\nP-Invariants timing: 1 thread={time_1:.3f}s, 4 threads={time_4:.3f}s")
        
        # Threading may or may not help depending on BLAS library
        # Just verify both work
    
    def test_t_invariants_threading(self):
        """Test that T-invariant analyzer also supports threading."""
        analyzer = TInvariantAnalyzer(self.model)
        
        # Should work with threading parameter
        result = analyzer.analyze(num_threads=2)
        
        self.assertTrue(result.success)
        # This model has T-invariants [1,0], [0,1] or [1,1]


if __name__ == '__main__':
    unittest.main()
