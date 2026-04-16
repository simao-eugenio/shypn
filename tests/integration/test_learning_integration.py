"""
Integration Tests for Intelligent Heuristics Learning

Tests end-to-end workflow:
1. User enriches pathways with SABIO-RK/BRENDA data
2. User rates parameters
3. Learning engine extracts patterns
4. Heuristic engine uses learned patterns
5. Confidence improves over time

Author: Shypn Development Team  
Date: November 2025
"""

import pytest
import tempfile
import os

from shypn.crossfetch.learning.heuristic_learner import HeuristicLearner
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine
from shypn.crossfetch.tracking.parameter_tracker import ParameterTracker


@pytest.fixture
def temp_db():
    """Create temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_integration.db')
        yield HeuristicDatabase(db_path)


@pytest.fixture
def tracker(temp_db):
    """Create parameter tracker."""
    return ParameterTracker(temp_db)


@pytest.fixture
def learner(temp_db):
    """Create heuristic learner."""
    return HeuristicLearner(db=temp_db, min_sample_size=3)


@pytest.fixture
def engine(temp_db):
    """Create inference engine."""
    # Create engine with same DB path
    return HeuristicInferenceEngine(db_path=temp_db.db_path)


def test_end_to_end_learning_workflow(temp_db, tracker, learner, engine):
    """Test complete workflow from enrichment to learned patterns."""
    
    # Step 1: Simulate user enriching pathways with SABIO-RK data
    # User applies hexokinase parameters from SABIO-RK
    enrichment_ids = []
    
    for i in range(10):
        params = {
            'vmax': 50.0 + i * 2.0,
            'km': 0.05 + i * 0.005,
            'kcat': 500.0
        }
        
        param_id = tracker.track_application(
            transition_id=f'trans_hk_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='2.7.1.1',
            organism='Homo sapiens',
            pathway_id='glycolysis',
            confidence_score=0.85
        )
        enrichment_ids.append(param_id)
    
    # Step 2: User rates parameters as good
    for param_id in enrichment_ids[:7]:  # Rate 7 out of 10 as good
        tracker.update_rating(param_id, rating=1, comment="Works well")
    
    # Step 3: Learning engine extracts patterns
    summary = learner.learn_from_history()
    
    assert summary['ec_specific_patterns'] > 0
    assert summary['total_samples_processed'] >= 10
    
    # Step 4: Verify learned pattern matches expected values
    vmax_pattern = learner.get_learned_parameter('vmax', ec_number='2.7.1.1', organism='Homo sapiens')
    km_pattern = learner.get_learned_parameter('km', ec_number='2.7.1.1', organism='Homo sapiens')
    
    assert vmax_pattern is not None
    assert km_pattern is not None
    
    # Should learn mean values close to data
    assert vmax_pattern['param_mean'] == pytest.approx(59.0, abs=5.0)  # Middle of 50-68 range
    assert km_pattern['param_mean'] == pytest.approx(0.0725, abs=0.01)  # Middle of 0.05-0.095
    
    # Confidence should be high (specific EC + organism + good sample size)
    assert vmax_pattern['confidence_score'] >= 0.65
    
    # Step 5: Heuristic engine uses learned pattern
    # Create mock transition
    class MockTransition:
        id = 'test_trans'
        label = 'hexokinase'
        ec_number = '2.7.1.1'
        
    transition = MockTransition()
    
    # Get learned kinetics
    learned = engine._get_learned_kinetics('2.7.1.1', 'Homo sapiens')
    
    assert learned is not None
    vmax, km, kcat, confidence = learned
    assert vmax == pytest.approx(vmax_pattern['param_mean'], rel=0.01)
    assert km == pytest.approx(km_pattern['param_mean'], rel=0.01)
    assert confidence >= 0.65


def test_pattern_confidence_improves_with_samples(temp_db, tracker, learner):
    """Test that confidence increases as more enrichments are added."""
    
    # Phase 1: Small sample (N=3)
    for i in range(3):
        params = {'vmax': 100.0 + i * 5.0, 'km': 0.1, 'kcat': 1000.0}
        tracker.track_application(
            transition_id=f'trans_phase1_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='1.2.3.4',
            organism='Test organism',
            pathway_id='test_pathway'
        )
    
    learner.learn_from_history()
    pattern_small = learner.get_learned_parameter('vmax', ec_number='1.2.3.4')
    
    assert pattern_small is not None
    confidence_small = pattern_small['confidence_score']
    sample_size_small = pattern_small['sample_size']
    
    # Phase 2: Add more samples (N=10 total)
    for i in range(7):
        params = {'vmax': 100.0 + (i + 3) * 5.0, 'km': 0.1, 'kcat': 1000.0}
        tracker.track_application(
            transition_id=f'trans_phase2_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='1.2.3.4',
            organism='Test organism',
            pathway_id='test_pathway'
        )
    
    learner.learn_from_history()
    pattern_large = learner.get_learned_parameter('vmax', ec_number='1.2.3.4')
    
    assert pattern_large is not None
    confidence_large = pattern_large['confidence_score']
    sample_size_large = pattern_large['sample_size']
    
    # Confidence should increase with more samples
    assert sample_size_large > sample_size_small
    assert confidence_large > confidence_small  # More samples → more confidence


def test_blending_learned_with_defaults(temp_db, tracker, learner, engine):
    """Test blending of learned patterns with hardcoded defaults."""
    
    # Create medium-confidence pattern (conf ~0.55)
    # Use small sample with some variance
    for i in range(5):
        params = {
            'vmax': 80.0 + i * 8.0,  # Some variance
            'km': 0.06 + i * 0.01,
            'kcat': 800.0
        }
        tracker.track_application(
            transition_id=f'trans_blend_{i}',
            parameters=params,
            source='BRENDA',
            ec_number='2.7.1.5',
            organism='Homo sapiens',
            pathway_id='blend_test'
        )
    
    learner.learn_from_history()
    
    # Get blended kinetics
    vmax, km, kcat = engine._get_default_kinetics('2.7.1.5', 'kinase', 'Homo sapiens')
    
    # Should be blend of learned (~92 for Vmax at i=4) and default (50 for kinases)
    # Exact blend depends on confidence, but should be between learned and default
    assert vmax > 50.0  # Higher than pure default
    assert vmax < 100.0  # Lower than pure learned mean


def test_fallback_to_defaults_without_learned_data(engine):
    """Test engine falls back to hardcoded defaults when no learned data."""
    
    # Query for EC with no learned patterns
    vmax, km, kcat = engine._get_default_kinetics('9.9.9.9', 'unknown_enzyme', 'Unknown organism')
    
    # Should return generic defaults
    assert vmax == 100.0  # Generic default
    assert km == 0.1
    assert kcat == 10.0


def test_cross_organism_learning(temp_db, tracker, learner):
    """Test learning patterns across different organisms."""
    
    # Add human enrichments
    for i in range(6):
        params = {'vmax': 50.0 + i * 3.0, 'km': 0.05, 'kcat': 500.0}
        tracker.track_application(
            transition_id=f'trans_human_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='2.7.1.1',
            organism='Homo sapiens',
            pathway_id='glycolysis_human'
        )
    
    # Add yeast enrichments (different kinetics)
    for i in range(6):
        params = {'vmax': 70.0 + i * 3.0, 'km': 0.08, 'kcat': 700.0}
        tracker.track_application(
            transition_id=f'trans_yeast_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='2.7.1.1',
            organism='Saccharomyces cerevisiae',
            pathway_id='glycolysis_yeast'
        )
    
    learner.learn_from_history()
    
    # Should learn different patterns for each organism
    human_pattern = learner.get_learned_parameter('vmax', ec_number='2.7.1.1', organism='Homo sapiens')
    yeast_pattern = learner.get_learned_parameter('vmax', ec_number='2.7.1.1', organism='Saccharomyces cerevisiae')
    
    assert human_pattern is not None
    assert yeast_pattern is not None
    
    # Patterns should differ
    assert abs(human_pattern['param_mean'] - yeast_pattern['param_mean']) > 10.0  # Significant difference


def test_undone_enrichments_excluded(temp_db, tracker, learner):
    """Test that undone enrichments are excluded from learning."""
    
    # Add enrichments
    ids_to_undo = []
    for i in range(8):
        params = {'vmax': 100.0 + i * 5.0, 'km': 0.1, 'kcat': 1000.0}
        param_id = tracker.track_application(
            transition_id=f'trans_undo_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='3.4.5.6',
            organism='Test organism',
            pathway_id='undo_test'
        )
        if i < 3:
            ids_to_undo.append(param_id)
    
    # Undo first 3
    for param_id in ids_to_undo:
        tracker.undo_application(param_id)
    
    # Learn patterns
    learner.learn_from_history()
    
    pattern = learner.get_learned_parameter('vmax', ec_number='3.4.5.6')
    
    assert pattern is not None
    # Sample size should be 5 (8 - 3 undone)
    assert pattern['sample_size'] == 5


def test_poor_ratings_excluded(temp_db, tracker, learner):
    """Test that poorly-rated enrichments are excluded."""
    
    # Add enrichments with mixed ratings
    for i in range(10):
        params = {'vmax': 150.0 + i * 10.0, 'km': 0.15, 'kcat': 1500.0}
        param_id = tracker.track_application(
            transition_id=f'trans_rating_{i}',
            parameters=params,
            source='SABIO-RK',
            ec_number='4.5.6.7',
            organism='Test organism',
            pathway_id='rating_test'
        )
        
        # Rate: 3 poor (-1), 4 neutral (0), 3 unrated (None)
        if i < 3:
            tracker.update_rating(param_id, rating=-1, comment="Bad")
        elif i < 7:
            tracker.update_rating(param_id, rating=0, comment="OK")
    
    learner.learn_from_history()
    
    pattern = learner.get_learned_parameter('vmax', ec_number='4.5.6.7')
    
    assert pattern is not None
    # Should exclude 3 poor ratings: 7 samples (4 neutral + 3 unrated)
    assert pattern['sample_size'] == 7
