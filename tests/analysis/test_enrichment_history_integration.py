#!/usr/bin/env python3
"""Integration test for Phase 2 enrichment history features.

Tests the complete workflow:
1. Track parameter applications
2. Rate applications
3. Filter history
4. Undo applications
"""

import pytest
import tempfile
import os

from src.shypn.crossfetch.database.heuristic_db import HeuristicDatabase
from src.shypn.crossfetch.tracking.parameter_tracker import ParameterTracker


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_heuristic.db')
        db = HeuristicDatabase(db_path)
        yield db


class TestEnrichmentHistoryIntegration:
    """Integration tests for Phase 2 user feedback features."""
    
    def test_complete_workflow(self, temp_db):
        """Test complete enrichment history workflow."""
        tracker = ParameterTracker(temp_db)
        
        # Step 1: Track SABIO-RK application
        param_id_sabio = tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 226.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous',
            ec_number='2.7.1.1',
            organism='Homo sapiens',
            pathway_id='hsa00010',
            pathway_name='Glycolysis'
        )
        
        assert param_id_sabio > 0
        
        # Step 2: Track BRENDA application
        param_id_brenda = tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 150.0, 'km': 0.2},
            source='BRENDA',
            transition_type='continuous',
            ec_number='2.7.1.2',
            organism='Homo sapiens',
            pathway_id='hsa00010',
            pathway_name='Glycolysis'
        )
        
        assert param_id_brenda > 0
        
        # Step 3: Rate the applications
        success = tracker.update_rating(param_id_sabio, rating=1, comment="Good match")
        assert success
        
        success = tracker.update_rating(param_id_brenda, rating=-1, comment="Poor fit")
        assert success
        
        # Step 4: Filter history by source
        sabio_history = tracker.get_filtered_history(source='SABIO-RK')
        assert len(sabio_history) == 1
        assert sabio_history[0]['source'] == 'SABIO-RK'
        assert sabio_history[0]['user_rating'] == 1
        
        brenda_history = tracker.get_filtered_history(source='BRENDA')
        assert len(brenda_history) == 1
        assert brenda_history[0]['source'] == 'BRENDA'
        assert brenda_history[0]['user_rating'] == -1
        
        # Step 5: Filter by rating
        good_rated = tracker.get_filtered_history(rating=1)
        assert len(good_rated) == 1
        assert good_rated[0]['parameter_id'] == param_id_sabio
        
        poor_rated = tracker.get_filtered_history(rating=-1)
        assert len(poor_rated) == 1
        assert poor_rated[0]['parameter_id'] == param_id_brenda
        
        # Step 6: Filter by pathway
        pathway_history = tracker.get_filtered_history(pathway_id='hsa00010')
        assert len(pathway_history) == 2
        
        # Step 7: Undo poor-rated application
        result = tracker.undo_application(param_id_brenda)
        assert result['success']
        assert result['transition_id'] == 'T2'
        
        # Step 8: Verify undone is excluded by default
        active_history = tracker.get_filtered_history(include_undone=False)
        assert len(active_history) == 1
        assert active_history[0]['parameter_id'] == param_id_sabio
        
        # Step 9: Include undone
        all_history = tracker.get_filtered_history(include_undone=True)
        assert len(all_history) == 2
        
        # Step 10: Verify confidence was updated based on ratings
        sabio_record = tracker.get_transition_history('T1')[0]
        # SABIO-RK (0.85) + good rating (+0.10) + 1 use (+0.01) = 0.96
        assert sabio_record['confidence_score'] > 0.85
        
        print("✓ Complete workflow test passed")
    
    def test_multiple_applications_same_transition(self, temp_db):
        """Test tracking multiple applications to same transition with undo."""
        tracker = ParameterTracker(temp_db)
        
        # First application
        param_id1 = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 100.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous'
        )
        
        # Second application (override)
        param_id2 = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 200.0, 'km': 0.2},
            source='BRENDA',
            transition_type='continuous'
        )
        
        # Third application
        param_id3 = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 150.0, 'km': 0.15},
            source='Heuristic',
            transition_type='continuous'
        )
        
        # Undo third application
        result = tracker.undo_application(param_id3)
        assert result['success']
        
        # Should return second application parameters
        prev = result['previous_parameters']
        assert prev is not None
        assert prev['vmax'] == 200.0
        assert prev['km'] == 0.2
        
        print("✓ Multiple applications with undo test passed")
    
    def test_confidence_calculation_factors(self, temp_db):
        """Test confidence calculation with all factors."""
        tracker = ParameterTracker(temp_db)
        
        # Track application
        param_id = tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0},
            source='BRENDA',
            transition_type='continuous'
        )
        
        # Initial confidence should be BRENDA baseline (0.80)
        history = tracker.get_transition_history('T1')
        assert history[0]['confidence_score'] == 0.80
        
        # Rate it good multiple times (increments usage_count)
        for i in range(5):
            tracker.update_rating(param_id, rating=1, comment=f"Test {i}")
        
        # Final confidence should be:
        # BRENDA (0.80) + good rating (+0.10) + 6 uses (+0.06) = 0.96
        history = tracker.get_transition_history('T1')
        final_conf = history[0]['confidence_score']
        assert final_conf == pytest.approx(0.96, abs=0.01)
        
        print("✓ Confidence calculation test passed")
    
    def test_get_summary_statistics(self, temp_db):
        """Test summary statistics across multiple sources."""
        tracker = ParameterTracker(temp_db)
        
        # Track from multiple sources
        tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0},
            source='SABIO-RK',
            transition_type='continuous',
            pathway_id='hsa00010'
        )
        
        tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 200.0},
            source='SABIO-RK',
            transition_type='continuous',
            pathway_id='hsa00010'
        )
        
        tracker.track_application(
            transition_id='T3',
            parameters={'vmax': 150.0},
            source='BRENDA',
            transition_type='continuous',
            pathway_id='hsa00020'
        )
        
        # Get summary
        summary = tracker.get_summary()
        
        assert summary['total_enrichments'] == 3
        assert summary['unique_transitions_enriched'] == 3
        assert summary['unique_pathways_enriched'] == 2
        assert 'SABIO-RK' in summary['by_source']
        assert 'BRENDA' in summary['by_source']
        # by_source structure is just source -> count (int)
        assert summary['by_source']['SABIO-RK'] == 2
        assert summary['by_source']['BRENDA'] == 1
        
        print("✓ Summary statistics test passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
