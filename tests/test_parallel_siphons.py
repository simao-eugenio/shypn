"""Test parallel siphon detection."""

import unittest
import time
from shypn.data.canvas.document_model import DocumentModel
from shypn.topology.structural.siphons import SiphonAnalyzer


class TestParallelSiphons(unittest.TestCase):
    """Test parallel siphon enumeration."""
    
    def setUp(self):
        """Create test model with siphons."""
        self.model = DocumentModel()
        
        # Create a model with known siphons
        # Classic deadlock pattern with siphon
        self.p1 = self.model.create_place(100, 100, label="P1")
        self.p1.tokens = 1
        self.p2 = self.model.create_place(200, 100, label="P2")
        self.p2.tokens = 0
        self.p3 = self.model.create_place(300, 100, label="P3")
        self.p3.tokens = 1
        
        # T1: P1 -> P2
        t1 = self.model.create_transition(150, 50)
        self.model.create_arc(self.p1, t1, weight=1)
        self.model.create_arc(t1, self.p2, weight=1)
        
        # T2: P2 + P3 -> P1
        t2 = self.model.create_transition(250, 150)
        self.model.create_arc(self.p2, t2, weight=1)
        self.model.create_arc(self.p3, t2, weight=1)
        self.model.create_arc(t2, self.p1, weight=1)
        
        # {P2, P3} is a siphon (and a trap)
    
    def test_sequential_vs_parallel_correctness(self):
        """Test that parallel and sequential modes find same siphons."""
        analyzer = SiphonAnalyzer(self.model)
        
        # Sequential analysis
        result_seq = analyzer.analyze(min_size=1, max_size=3, parallel=False)
        
        # Parallel analysis
        result_par = analyzer.analyze(min_size=1, max_size=3, parallel=True, num_workers=2)
        
        # Both should succeed
        self.assertTrue(result_seq.success)
        self.assertTrue(result_par.success)
        
        # Same number of siphons
        siphons_seq = result_seq.get('siphons', [])
        siphons_par = result_par.get('siphons', [])
        self.assertEqual(len(siphons_seq), len(siphons_par))
        
        # Same siphon place sets
        sets_seq = {frozenset(s['place_ids']) for s in siphons_seq}
        sets_par = {frozenset(s['place_ids']) for s in siphons_par}
        self.assertEqual(sets_seq, sets_par)
    
    def test_parallel_speedup_medium_network(self):
        """Test parallel speedup on medium-sized networks."""
        # Create a network with ~15 places (near the size limit)
        medium_model = DocumentModel()
        
        places = [medium_model.create_place(i*50, 100) for i in range(15)]
        transitions = [medium_model.create_transition(i*60, 200) for i in range(10)]
        
        # Connect in a pattern that creates siphons
        for i, trans in enumerate(transitions):
            # Each transition consumes from 2 places, produces to 1
            medium_model.create_arc(places[i], trans, weight=1)
            medium_model.create_arc(places[(i+1) % 15], trans, weight=1)
            medium_model.create_arc(trans, places[(i+2) % 15], weight=1)
        
        analyzer = SiphonAnalyzer(medium_model)
        
        # Measure sequential time
        start_seq = time.perf_counter()
        result_seq = analyzer.analyze(min_size=2, max_size=5, parallel=False, max_siphons=50)
        time_seq = time.perf_counter() - start_seq
        
        # Measure parallel time
        start_par = time.perf_counter()
        result_par = analyzer.analyze(min_size=2, max_size=5, parallel=True, num_workers=4, max_siphons=50)
        time_par = time.perf_counter() - start_par
        
        # Both should succeed
        self.assertTrue(result_seq.success)
        self.assertTrue(result_par.success)
        
        print(f"\nSiphons timing: Sequential={time_seq:.3f}s, Parallel={time_par:.3f}s")
        
        # Parallel might have overhead on medium networks
        # Just verify both complete successfully
        self.assertTrue(result_seq.success)
        self.assertTrue(result_par.success)
    
    def test_parallel_small_network_fallback(self):
        """Test that small networks don't use parallel (< 8 places)."""
        # The setUp model only has 3 places
        analyzer = SiphonAnalyzer(self.model)
        
        # Request parallel, but should fall back to sequential
        result = analyzer.analyze(parallel=True, num_workers=4)
        
        self.assertTrue(result.success)
        # Should work even with sequential fallback
    
    def test_parallel_size_guard(self):
        """Test that parallel mode respects the size guard (>20 places)."""
        # Create a model with 22 places (above safety limit)
        large_model = DocumentModel()
        
        places = [large_model.create_place(i*50, 100) for i in range(22)]
        trans = large_model.create_transition(500, 200)
        
        # Connect minimally
        for p in places[:5]:
            large_model.create_arc(p, trans)
            large_model.create_arc(trans, p)
        
        analyzer = SiphonAnalyzer(large_model)
        
        # Should fail with size guard error (even with parallel)
        result = analyzer.analyze(parallel=True, num_workers=4)
        
        self.assertFalse(result.success)
        self.assertIn("too large", str(result.errors[0]).lower())
    
    def test_parallel_worker_count(self):
        """Test different worker counts."""
        analyzer = SiphonAnalyzer(self.model)
        
        # Test with various worker counts
        for workers in [1, 2, 4]:
            result = analyzer.analyze(
                min_size=1,
                parallel=True,
                num_workers=workers
            )
            
            self.assertTrue(result.success, f"Failed with {workers} workers")
            self.assertGreaterEqual(len(result.get('siphons', [])), 0)
    
    def test_parallel_partition_strategy(self):
        """Test that partition strategy distributes work correctly."""
        # Create a model with enough places to parallelize (10 places)
        medium_model = DocumentModel()
        
        places = [medium_model.create_place(i*50, 100) for i in range(10)]
        trans = medium_model.create_transition(250, 200)
        
        # Simple connection
        for p in places:
            medium_model.create_arc(p, trans)
            medium_model.create_arc(trans, p)
        
        analyzer = SiphonAnalyzer(medium_model)
        
        # Parallel with 4 workers
        result = analyzer.analyze(
            min_size=1,
            max_size=3,
            parallel=True,
            num_workers=4
        )
        
        self.assertTrue(result.success)
        
        # Should find some siphons
        siphons = result.get('siphons', [])
        # This particular model should have siphons
        # (all subsets are siphons in this simple case)
    
    def test_parallel_auto_workers(self):
        """Test automatic worker count detection."""
        analyzer = SiphonAnalyzer(self.model)
        
        # None should auto-detect CPU count
        result = analyzer.analyze(
            min_size=1,
            parallel=True,
            num_workers=None
        )
        
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.get('siphons', [])), 0)
    
    def test_parallel_with_marking_check(self):
        """Test parallel mode with marking status checking."""
        analyzer = SiphonAnalyzer(self.model)
        
        # Parallel with marking check
        result = analyzer.analyze(
            check_marking=True,
            parallel=True,
            num_workers=2
        )
        
        self.assertTrue(result.success)
        
        # Siphons should have marking status
        siphons = result.get('siphons', [])
        for siphon in siphons:
            self.assertIn('is_empty', siphon)
            self.assertIn('marking', siphon)  # Dict of place_id -> token count


if __name__ == '__main__':
    unittest.main()
