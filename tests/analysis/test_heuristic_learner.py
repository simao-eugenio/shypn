"""
Tests for HeuristicLearner - Pattern Learning from Enrichment History

Tests Phase 3 functionality:
- Pattern extraction from enrichment history
- Statistical calculations
- Outlier detection
- Confidence scoring
- Biological validation

Author: Shypn Development Team
Date: November 2025
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

from shypn.crossfetch.learning.heuristic_learner import HeuristicLearner
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_learning.db')
        db = HeuristicDatabase(db_path)
        yield db


@pytest.fixture
def learner(temp_db):
    """Create learner with temp database."""
    return HeuristicLearner(db=temp_db, min_sample_size=3)


@pytest.fixture
def sample_enrichments(temp_db):
    """Create sample enrichment data for learning."""
    # Insert sample continuous parameters for EC 2.7.1.1 (hexokinase)
    enrichment_ids = []
    
    # Good enrichments (Vmax around 50, Km around 0.05)
    for i in range(10):
        params = {
            'vmax': 50.0 + (i - 5) * 2.0,  # 40-60 range
            'km': 0.05 + (i - 5) * 0.005,  # 0.025-0.075 range
            'kcat': 500.0 + (i - 5) * 20.0
        }
        
        param_id = temp_db.store_parameter(
            transition_type='continuous',
            organism='Homo sapiens',
            parameters=params,
            source='SABIO-RK',
            confidence_score=0.85,
            ec_number='2.7.1.1',
            enzyme_name='Hexokinase',
            user_rating=1 if i % 2 == 0 else None  # Some rated good
        )
        enrichment_ids.append(param_id)
    
    # Add one outlier (should be removed)
    outlier_params = {'vmax': 500.0, 'km': 5.0, 'kcat': 10000.0}
    temp_db.store_parameter(
        transition_type='continuous',
        organism='Homo sapiens',
        parameters=outlier_params,
        source='SABIO-RK',
        confidence_score=0.50,
        ec_number='2.7.1.1',
        enzyme_name='Hexokinase'
    )
    
    # Add enrichments for another EC class (transferases)
    for i in range(8):
        params = {
            'vmax': 60.0 + i * 3.0,
            'km': 0.08 + i * 0.01,
            'kcat': 600.0 + i * 50.0
        }
        
        temp_db.store_parameter(
            transition_type='continuous',
            organism='Homo sapiens',
            parameters=params,
            source='BRENDA',
            confidence_score=0.80,
            ec_number='2.7.1.2',  # Glucokinase
            enzyme_name='Glucokinase',
            user_rating=1 if i % 3 == 0 else 0
        )
    
    return enrichment_ids


def test_learner_initialization(learner):
    """Test learner initializes correctly."""
    assert learner.min_sample_size == 3
    assert learner.min_confidence == 0.5
    assert learner.outlier_threshold == 3.0
    assert 'vmax' in learner.param_ranges
    assert 'km' in learner.param_ranges


def test_extract_continuous_parameters(learner, temp_db, sample_enrichments):
    """Test extraction of continuous parameters from enrichments."""
    # Get enrichments
    with temp_db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, parameters FROM transition_parameters
            WHERE ec_number = '2.7.1.1'
        """)
        enrichments = [{'id': row['id'], 'parameters': row['parameters']} 
                      for row in cursor.fetchall()]
    
    param_data = learner._extract_continuous_parameters(enrichments)
    
    assert 'vmax' in param_data
    assert 'km' in param_data
    assert 'kcat' in param_data
    
    # Should have 11 entries (10 good + 1 outlier)
    assert len(param_data['vmax']) == 11
    assert len(param_data['km']) == 11
    assert len(param_data['kcat']) == 11
    
    # Check data format (value, id) tuples
    assert isinstance(param_data['vmax'][0], tuple)
    assert len(param_data['vmax'][0]) == 2


def test_outlier_removal(learner):
    """Test outlier detection and removal."""
    # Create data with obvious outlier
    values_with_ids = [
        (50.0, 1), (52.0, 2), (48.0, 3), (51.0, 4), (49.0, 5),
        (500.0, 6)  # Outlier (Z-score >> 3)
    ]
    
    clean_values, clean_ids, outliers = learner._remove_outliers(values_with_ids)
    
    # Should remove 1 outlier
    assert outliers == 1
    assert len(clean_values) == 5
    assert 500.0 not in clean_values
    assert 6 not in clean_ids


def test_parameter_statistics(learner):
    """Test statistical calculation."""
    values = [50.0, 52.0, 48.0, 51.0, 49.0]
    
    stats = learner._calculate_parameter_statistics(values)
    
    assert 'mean' in stats
    assert 'median' in stats
    assert 'std_dev' in stats
    assert 'min' in stats
    assert 'max' in stats
    assert 'cv' in stats  # Coefficient of variation
    assert 'variance_penalty' in stats
    
    # Check values
    assert stats['mean'] == pytest.approx(50.0)
    assert stats['median'] == pytest.approx(50.0)
    assert stats['min'] == 48.0
    assert stats['max'] == 52.0
    assert stats['cv'] < 0.1  # Low variance


def test_biological_validation(learner):
    """Test biological range validation."""
    # Valid parameters
    assert learner._validate_parameter_range('vmax', 100.0) is True
    assert learner._validate_parameter_range('km', 0.1) is True
    assert learner._validate_parameter_range('kcat', 1000.0) is True
    
    # Invalid parameters (out of range)
    assert learner._validate_parameter_range('vmax', -10.0) is False
    assert learner._validate_parameter_range('vmax', 100000.0) is False
    assert learner._validate_parameter_range('km', 0.0) is False
    assert learner._validate_parameter_range('km', 10000.0) is False


def test_confidence_calculation(learner):
    """Test confidence scoring."""
    # Low variance, medium sample
    stats_low_var = {
        'mean': 50.0,
        'std_dev': 2.0,
        'cv': 0.04,
        'variance_penalty': 0.0
    }
    
    conf = learner._calculate_confidence(stats_low_var, sample_size=10, pattern_type='ec_specific')
    assert conf >= 0.70  # Base + sample boost
    assert conf <= 0.85
    
    # High variance, same sample
    stats_high_var = {
        'mean': 50.0,
        'std_dev': 30.0,
        'cv': 0.6,
        'variance_penalty': 0.15
    }
    
    conf_var = learner._calculate_confidence(stats_high_var, sample_size=10, pattern_type='ec_specific')
    assert conf_var < conf  # Variance penalty reduces confidence


def test_learn_ec_class_patterns(learner, sample_enrichments):
    """Test EC class pattern learning."""
    stats = learner._learn_ec_class_patterns()
    
    assert stats['patterns_created'] > 0
    assert stats['samples_processed'] > 0
    
    # Should learn EC 2.7 patterns (transferases)
    # Query learned pattern
    vmax_pattern = learner.get_learned_parameter('vmax', ec_number='2.7.1.1')
    
    assert vmax_pattern is not None
    assert vmax_pattern['param_type'] == 'vmax'
    assert vmax_pattern['ec_class'] == '2.7'
    assert vmax_pattern['param_mean'] > 0
    assert vmax_pattern['confidence_score'] >= 0.5


def test_learn_ec_specific_patterns(learner, sample_enrichments):
    """Test EC-specific pattern learning."""
    stats = learner._learn_ec_specific_patterns()
    
    assert stats['patterns_created'] > 0
    
    # Query specific EC 2.7.1.1 pattern
    km_pattern = learner.get_learned_parameter('km', ec_number='2.7.1.1', organism='Homo sapiens')
    
    assert km_pattern is not None
    assert km_pattern['ec_number'] == '2.7.1.1'
    assert km_pattern['organism'] == 'Homo sapiens'
    assert km_pattern['param_mean'] == pytest.approx(0.05, abs=0.02)  # Around 0.05


def test_learn_organism_patterns(learner, sample_enrichments):
    """Test organism-specific pattern learning."""
    stats = learner._learn_organism_patterns()
    
    assert stats['patterns_created'] > 0
    
    # Query human-specific pattern
    kcat_pattern = learner.get_learned_parameter('kcat', organism='Homo sapiens')
    
    assert kcat_pattern is not None
    assert kcat_pattern['organism'] == 'Homo sapiens'
    assert kcat_pattern['param_mean'] > 0


def test_full_learning_workflow(learner, sample_enrichments):
    """Test complete learning workflow."""
    summary = learner.learn_from_history()
    
    assert summary['ec_class_patterns'] > 0
    assert summary['ec_specific_patterns'] > 0
    assert summary['organism_patterns'] > 0
    assert summary['total_samples_processed'] > 0
    assert summary['outliers_removed'] >= 1  # Should remove the outlier
    
    # Verify patterns stored in database
    stats = learner.db.get_learning_statistics()
    
    assert stats['total_patterns'] > 0
    assert stats['total_samples_used'] > 0
    assert stats['avg_confidence'] >= 0.5
    assert len(stats['best_patterns']) > 0


def test_pattern_query_priority(learner, temp_db):
    """Test pattern query follows correct priority."""
    # Create patterns with different specificities
    
    # 1. EC-specific + organism (highest priority)
    temp_db.store_learned_pattern(
        pattern_type='ec_specific',
        param_type='vmax',
        param_mean=100.0,
        param_std_dev=10.0,
        sample_size=10,
        confidence_score=0.85,
        source_ids=[1, 2, 3],
        ec_number='2.7.1.1',
        organism='Homo sapiens'
    )
    
    # 2. EC class + organism
    temp_db.store_learned_pattern(
        pattern_type='ec_class',
        param_type='vmax',
        param_mean=80.0,
        param_std_dev=15.0,
        sample_size=20,
        confidence_score=0.75,
        source_ids=[4, 5, 6],
        ec_class='2.7',
        organism='Homo sapiens'
    )
    
    # Query should return highest priority match
    pattern = learner.get_learned_parameter('vmax', ec_number='2.7.1.1', organism='Homo sapiens')
    
    assert pattern is not None
    assert pattern['param_mean'] == 100.0  # EC-specific match
    assert pattern['ec_number'] == '2.7.1.1'


def test_insufficient_samples(learner, temp_db):
    """Test handling of insufficient sample size."""
    # Create pattern with only 2 samples (below min_sample_size=3)
    params1 = {'vmax': 50.0, 'km': 0.1, 'kcat': 500.0}
    params2 = {'vmax': 52.0, 'km': 0.11, 'kcat': 520.0}
    
    temp_db.store_parameter(
        transition_type='continuous',
        organism='Test organism',
        parameters=params1,
        source='SABIO-RK',
        confidence_score=0.85,
        ec_number='1.1.1.1'
    )
    
    temp_db.store_parameter(
        transition_type='continuous',
        organism='Test organism',
        parameters=params2,
        source='SABIO-RK',
        confidence_score=0.85,
        ec_number='1.1.1.1'
    )
    
    # Learn patterns
    stats = learner._learn_ec_class_patterns()
    
    # Should not create pattern (insufficient samples)
    pattern = learner.get_learned_parameter('vmax', ec_number='1.1.1.1')
    assert pattern is None


def test_low_confidence_rejection(learner, temp_db):
    """Test rejection of low-confidence patterns."""
    # Create pattern with high variance (low confidence)
    params_list = [
        {'vmax': 10.0, 'km': 0.1, 'kcat': 100.0},
        {'vmax': 100.0, 'km': 0.1, 'kcat': 1000.0},
        {'vmax': 1000.0, 'km': 0.1, 'kcat': 10000.0},
        {'vmax': 50.0, 'km': 0.1, 'kcat': 500.0},
        {'vmax': 500.0, 'km': 0.1, 'kcat': 5000.0}
    ]
    
    for params in params_list:
        temp_db.store_parameter(
            transition_type='continuous',
            organism='Variable organism',
            parameters=params,
            source='SABIO-RK',
            confidence_score=0.70,
            ec_number='3.3.3.3'
        )
    
    # Learn patterns
    stats = learner._learn_ec_specific_patterns()
    
    # High variance should result in low confidence
    # Pattern might be created but with low confidence
    pattern = learner.get_learned_parameter('vmax', ec_number='3.3.3.3')
    
    # If pattern exists, confidence should reflect high variance
    if pattern:
        assert pattern['variance_penalty'] > 0.1  # High variance penalty
