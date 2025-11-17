#!/usr/bin/env python3
"""Unit tests for parameter tracker.

Tests for ParameterTracker provenance tracking functionality.
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


class TestParameterTracker:
    """Tests for parameter tracker."""
    
    def test_initialization(self, temp_db):
        """Test tracker initialization."""
        tracker = ParameterTracker(temp_db)
        assert tracker.db == temp_db
    
    def test_track_application(self, temp_db):
        """Test tracking parameter application."""
        tracker = ParameterTracker(temp_db)
        
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous',
            ec_number='2.7.1.1',
            organism='Homo sapiens',
            confidence_score=0.9
        )
        
        assert param_id > 0
    
    def test_get_transition_history(self, temp_db):
        """Test retrieving transition enrichment history."""
        tracker = ParameterTracker(temp_db)
        
        # Track application
        tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens',
            confidence_score=0.9
        )
        
        # Get history
        history = tracker.get_transition_history('T42')
        assert len(history) == 1
        assert history[0]['transition_id'] == 'T42'
    
    def test_get_pathway_history(self, temp_db):
        """Test retrieving pathway enrichment history."""
        tracker = ParameterTracker(temp_db)
        
        # Track applications for pathway
        tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0, 'km': 0.5},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens',
            pathway_id='hsa00010',
            confidence_score=0.8
        )
        
        tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 200.0, 'km': 1.0},
            source='BRENDA',
            transition_type='continuous',
            organism='Homo sapiens',
            pathway_id='hsa00010',
            confidence_score=0.7
        )
        
        # Get pathway history
        history = tracker.get_pathway_history('hsa00010')
        assert len(history) == 2
    
    def test_get_source_statistics(self, temp_db):
        """Test source statistics aggregation."""
        tracker = ParameterTracker(temp_db)
        
        # Track from different sources
        tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens',
            confidence_score=0.9
        )
        
        tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 200.0},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens',
            confidence_score=0.8
        )
        
        stats = tracker.get_source_statistics('SABIO-RK')
        assert stats['total_applications'] == 2
        assert stats['avg_confidence'] > 0.8
    
    def test_get_summary(self, temp_db):
        """Test overall tracking summary."""
        tracker = ParameterTracker(temp_db)
        
        # Track applications
        tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens',
            pathway_id='hsa00010',
            confidence_score=0.9
        )
        
        tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 200.0},
            source='BRENDA',
            transition_type='continuous',
            organism='Homo sapiens',
            pathway_id='hsa00020',
            confidence_score=0.8
        )
        
        summary = tracker.get_summary()
        assert summary['total_enrichments'] == 2
        assert summary['unique_transitions_enriched'] == 2
        assert summary['unique_pathways_enriched'] == 2
        assert 'SABIO-RK' in summary['by_source']
        assert 'BRENDA' in summary['by_source']
    
    def test_multiple_applications_same_transition(self, temp_db):
        """Test tracking multiple applications to same transition."""
        tracker = ParameterTracker(temp_db)
        
        # First application
        param_id1 = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 100.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens',
            confidence_score=0.7
        )
        
        # Second application (override)
        param_id2 = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 200.0, 'km': 0.2},
            source='BRENDA',
            transition_type='continuous',
            organism='Homo sapiens',
            confidence_score=0.9
        )
        
        assert param_id1 != param_id2
        
        # History should show both
        history = tracker.get_transition_history('T42')
        assert len(history) >= 2
    
    # ========================================================================
    # Phase 2: User Feedback & History Management Tests
    # ========================================================================
    
    def test_confidence_calculation_baseline(self, temp_db):
        """Test confidence score calculation with default values."""
        tracker = ParameterTracker(temp_db)
        
        # SABIO-RK baseline
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=0,
            user_rating=None
        )
        assert conf == 0.85
        
        # BRENDA baseline
        conf = tracker._calculate_confidence(
            source='BRENDA',
            usage_count=0,
            user_rating=None
        )
        assert conf == 0.80
        
        # Heuristic baseline
        conf = tracker._calculate_confidence(
            source='Heuristic',
            usage_count=0,
            user_rating=None
        )
        assert conf == 0.70
    
    def test_confidence_calculation_usage_boost(self, temp_db):
        """Test usage count boosts confidence."""
        tracker = ParameterTracker(temp_db)
        
        # 5 uses = +5% boost
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=5,
            user_rating=None
        )
        assert conf == 0.90  # 0.85 + 0.05
        
        # Max boost capped at 10%
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=20,
            user_rating=None
        )
        assert conf == 0.95  # 0.85 + 0.10 (capped)
    
    def test_confidence_calculation_user_rating(self, temp_db):
        """Test user rating influences confidence."""
        tracker = ParameterTracker(temp_db)
        
        # Good rating (+10%)
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=0,
            user_rating=1
        )
        assert conf == 0.95  # 0.85 + 0.10
        
        # Poor rating (-15%)
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=0,
            user_rating=-1
        )
        assert conf == 0.70  # 0.85 - 0.15
        
        # Neutral rating (no change)
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=0,
            user_rating=0
        )
        assert conf == 0.85
    
    def test_confidence_calculation_combined_factors(self, temp_db):
        """Test confidence with multiple factors."""
        tracker = ParameterTracker(temp_db)
        
        # SABIO-RK (0.85) + 3 uses (+3%) + good rating (+10%)
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=3,
            user_rating=1
        )
        assert conf == 0.98  # 0.85 + 0.03 + 0.10
        
        # Can't exceed 1.0
        conf = tracker._calculate_confidence(
            source='SABIO-RK',
            usage_count=10,
            user_rating=1
        )
        assert conf == 1.0  # Capped at 1.0
    
    def test_update_rating(self, temp_db):
        """Test updating user rating for parameter."""
        tracker = ParameterTracker(temp_db)
        
        # Track application
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous',
            organism='Homo sapiens'
        )
        
        # Update rating
        success = tracker.update_rating(
            parameter_id=param_id,
            rating=1,
            comment="Great parameters, matches experimental data!"
        )
        assert success
        
        # Verify confidence updated
        history = tracker.get_transition_history('T42')
        assert len(history) > 0
        record = history[0]
        assert record['user_rating'] == 1
        assert record['confidence_score'] > 0.85  # Should increase
    
    def test_update_rating_recalculates_confidence(self, temp_db):
        """Test that rating updates trigger confidence recalculation."""
        tracker = ParameterTracker(temp_db)
        
        # Initial application
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0},
            source='BRENDA',
            transition_type='continuous'
        )
        
        # Get initial confidence (should be 0.80 for BRENDA)
        history = tracker.get_transition_history('T42')
        initial_conf = history[0]['confidence_score']
        assert initial_conf == 0.80
        
        # Poor rating
        tracker.update_rating(param_id, rating=-1, comment="Doesn't work")
        
        # Confidence should decrease
        # Note: update_rating increments usage_count, so:
        # 0.80 (BRENDA) + 0.02 (2 uses) - 0.15 (poor) = 0.67
        history = tracker.get_transition_history('T42')
        new_conf = history[0]['confidence_score']
        assert new_conf < initial_conf
        assert new_conf == 0.67  # Adjusted for usage_count increment
    
    def test_get_filtered_history_by_source(self, temp_db):
        """Test filtering history by source."""
        tracker = ParameterTracker(temp_db)
        
        # Track from different sources
        tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0},
            source='SABIO-RK',
            transition_type='continuous'
        )
        
        tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 200.0},
            source='BRENDA',
            transition_type='continuous'
        )
        
        # Filter by source
        sabio_history = tracker.get_filtered_history(source='SABIO-RK')
        assert len(sabio_history) == 1
        assert sabio_history[0]['source'] == 'SABIO-RK'
        
        brenda_history = tracker.get_filtered_history(source='BRENDA')
        assert len(brenda_history) == 1
        assert brenda_history[0]['source'] == 'BRENDA'
    
    def test_get_filtered_history_by_rating(self, temp_db):
        """Test filtering history by user rating."""
        tracker = ParameterTracker(temp_db)
        
        # Track and rate applications
        param_id1 = tracker.track_application(
            transition_id='T1',
            parameters={'vmax': 100.0},
            source='SABIO-RK',
            transition_type='continuous'
        )
        tracker.update_rating(param_id1, rating=1, comment="Good")
        
        param_id2 = tracker.track_application(
            transition_id='T2',
            parameters={'vmax': 200.0},
            source='SABIO-RK',
            transition_type='continuous'
        )
        tracker.update_rating(param_id2, rating=-1, comment="Bad")
        
        # Filter by rating
        good_history = tracker.get_filtered_history(rating=1)
        assert len(good_history) == 1
        assert good_history[0]['user_rating'] == 1
        
        poor_history = tracker.get_filtered_history(rating=-1)
        assert len(poor_history) == 1
        assert poor_history[0]['user_rating'] == -1
    
    def test_get_filtered_history_exclude_undone(self, temp_db):
        """Test filtering excludes undone applications by default."""
        tracker = ParameterTracker(temp_db)
        
        # Track application
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0},
            source='SABIO-RK',
            transition_type='continuous'
        )
        
        # Initially visible
        history = tracker.get_filtered_history()
        assert len(history) == 1
        
        # Undo it
        tracker.undo_application(param_id)
        
        # Now excluded by default
        history = tracker.get_filtered_history(include_undone=False)
        assert len(history) == 0
        
        # Can include undone explicitly
        history = tracker.get_filtered_history(include_undone=True)
        assert len(history) == 1
        assert history[0]['undone'] == 1
    
    def test_undo_application(self, temp_db):
        """Test undoing parameter application."""
        tracker = ParameterTracker(temp_db)
        
        # Track application
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0, 'km': 0.1},
            source='SABIO-RK',
            transition_type='continuous'
        )
        
        # Undo it
        result = tracker.undo_application(param_id)
        
        assert result['success']
        assert result['transition_id'] == 'T42'
        assert 'message' in result
        
        # Verify marked as undone
        history = tracker.get_filtered_history(include_undone=True)
        assert len(history) > 0
        assert history[0]['undone'] == 1
    
    def test_undo_returns_previous_parameters(self, temp_db):
        """Test undo returns previous parameter values."""
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
        
        # Undo second application
        result = tracker.undo_application(param_id2)
        
        assert result['success']
        assert result['previous_parameters'] is not None
        assert result['previous_parameters']['vmax'] == 100.0
        assert result['previous_parameters']['km'] == 0.1
    
    def test_undo_already_undone(self, temp_db):
        """Test undoing already undone application fails gracefully."""
        tracker = ParameterTracker(temp_db)
        
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0},
            source='SABIO-RK',
            transition_type='continuous'
        )
        
        # Undo once
        result1 = tracker.undo_application(param_id)
        assert result1['success']
        
        # Try undo again
        result2 = tracker.undo_application(param_id)
        assert not result2['success']
        assert 'already undone' in result2['message'].lower()
    
    def test_auto_confidence_calculation(self, temp_db):
        """Test automatic confidence calculation when not provided."""
        tracker = ParameterTracker(temp_db)
        
        # Track without explicit confidence
        param_id = tracker.track_application(
            transition_id='T42',
            parameters={'vmax': 226.0},
            source='SABIO-RK',
            transition_type='continuous'
        )
        
        # Should auto-calculate based on source
        history = tracker.get_transition_history('T42')
        assert len(history) > 0
        assert history[0]['confidence_score'] == 0.85  # SABIO-RK baseline


if __name__ == '__main__':
    pytest.main([__file__, '-v'])