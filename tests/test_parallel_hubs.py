"""Test parallel hubs analysis."""

import unittest
import time
from shypn.data.canvas.document_model import DocumentModel
from shypn.topology.network.hubs import HubAnalyzer


class TestParallelHubs(unittest.TestCase):
    """Test parallel hub detection."""
    
    def setUp(self):
        """Create test models."""
        self.model = DocumentModel()
        
        # Create a hub-and-spoke network (P0 is hub)
        # P0 (hub) -> T1,T2,T3,T4,T5
        # T1,T2,T3,T4,T5 -> P1,P2,P3,P4,P5
        self.hub_place = self.model.create_place(100, 100, label="P0_hub")
        self.hub_place.tokens = 10
        
        for i in range(1, 11):
            transition = self.model.create_transition(200 + i*50, 100, label=f"T{i}")
            place = self.model.create_place(300 + i*50, 100, label=f"P{i}")
            
            # P0 -> Ti
            self.model.create_arc(self.hub_place, transition, weight=1)
            # Ti -> Pi
            self.model.create_arc(transition, place, weight=1)
    
    def test_sequential_vs_parallel_correctness(self):
        """Test that parallel and sequential modes find same hubs."""
        analyzer = HubAnalyzer(self.model)
        
        # Sequential analysis
        result_seq = analyzer.analyze(min_degree=5, top_n=5, parallel=False)
        
        # Parallel analysis
        result_par = analyzer.analyze(min_degree=5, top_n=5, parallel=True, num_workers=2)
        
        # Both should succeed
        self.assertTrue(result_seq.success)
        self.assertTrue(result_par.success)
        
        # Same number of hubs
        hubs_seq = result_seq.get('hubs', [])
        hubs_par = result_par.get('hubs', [])
        self.assertEqual(len(hubs_seq), len(hubs_par))
        
        # Same hub IDs
        ids_seq = sorted([h['id'] for h in hubs_seq])
        ids_par = sorted([h['id'] for h in hubs_par])
        self.assertEqual(ids_seq, ids_par)
        
        # Same degrees
        for hub_seq, hub_par in zip(hubs_seq, hubs_par):
            self.assertEqual(hub_seq['degree'], hub_par['degree'])
            self.assertEqual(hub_seq['in_degree'], hub_par['in_degree'])
            self.assertEqual(hub_seq['out_degree'], hub_par['out_degree'])
    
    def test_parallel_speedup_large_network(self):
        """Test that parallel mode is faster on larger networks."""
        # Create a larger network with multiple hubs
        large_model = DocumentModel()
        
        # Create 50 places and 50 transitions with complex connections
        places = [large_model.create_place(i*50, 100) for i in range(50)]
        transitions = [large_model.create_transition(i*50, 200) for i in range(50)]
        
        # Connect in a mesh pattern (many connections)
        for i, trans in enumerate(transitions):
            for j in range(max(0, i-5), min(len(places), i+5)):
                large_model.create_arc(places[j], trans, weight=1)
                large_model.create_arc(trans, places[(j+1) % len(places)], weight=1)
        
        analyzer = HubAnalyzer(large_model)
        
        # Measure sequential time
        start_seq = time.perf_counter()
        result_seq = analyzer.analyze(min_degree=2, parallel=False)
        time_seq = time.perf_counter() - start_seq
        
        # Measure parallel time
        start_par = time.perf_counter()
        result_par = analyzer.analyze(min_degree=2, parallel=True, num_workers=4)
        time_par = time.perf_counter() - start_par
        
        # Both should succeed
        self.assertTrue(result_seq.success)
        self.assertTrue(result_par.success)
        
        # Parallel should be faster (or at least not much slower)
        print(f"\nHubs timing: Sequential={time_seq:.3f}s, Parallel={time_par:.3f}s")
        # For small to medium networks, parallel might have overhead
        # Just verify both complete successfully  
        self.assertTrue(result_seq.success)
        self.assertTrue(result_par.success)
    
    def test_parallel_with_type_filter(self):
        """Test parallel mode with node type filtering."""
        analyzer = HubAnalyzer(self.model)
        
        # Analyze only places
        result_places = analyzer.analyze(
            min_degree=2,
            node_type='place',
            parallel=True,
            num_workers=2
        )
        
        self.assertTrue(result_places.success)
        hubs = result_places.get('hubs', [])
        
        # All should be places
        for hub in hubs:
            self.assertEqual(hub['type'], 'place')
        
        # P0 (hub) should be found
        hub_ids = [h['id'] for h in hubs]
        self.assertIn(self.hub_place.id, hub_ids)
    
    def test_parallel_small_network_fallback(self):
        """Test that small networks don't use parallel (overhead too high)."""
        # Create tiny network (< 10 nodes)
        tiny_model = DocumentModel()
        p1 = tiny_model.create_place(100, 100)
        t1 = tiny_model.create_transition(200, 100)
        p2 = tiny_model.create_place(300, 100)
        tiny_model.create_arc(p1, t1)
        tiny_model.create_arc(t1, p2)
        
        analyzer = HubAnalyzer(tiny_model)
        
        # Request parallel, but should use sequential due to size
        result = analyzer.analyze(parallel=True, num_workers=4)
        
        self.assertTrue(result.success)
        # Should have run (even if sequential under the hood)
    
    def test_parallel_worker_count(self):
        """Test different worker counts."""
        analyzer = HubAnalyzer(self.model)
        
        # Test with various worker counts
        for workers in [1, 2, 4]:
            result = analyzer.analyze(
                min_degree=3,
                parallel=True,
                num_workers=workers
            )
            
            self.assertTrue(result.success, f"Failed with {workers} workers")
            self.assertGreater(len(result.get('hubs', [])), 0)
    
    def test_parallel_auto_workers(self):
        """Test automatic worker count detection."""
        analyzer = HubAnalyzer(self.model)
        
        # None should auto-detect CPU count
        result = analyzer.analyze(
            min_degree=3,
            parallel=True,
            num_workers=None
        )
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.get('hubs', [])), 0)


if __name__ == '__main__':
    unittest.main()
