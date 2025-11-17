#!/usr/bin/env python3
"""Unit tests for cache managers.

Tests for BaseCacheManager, SabioRKCacheManager, and BRENDACacheManager.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.shypn.crossfetch.database.heuristic_db import HeuristicDatabase
from src.shypn.crossfetch.cache.sabio_rk_cache_manager import SabioRKCacheManager
from src.shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_heuristic.db')
        db = HeuristicDatabase(db_path)
        yield db


class TestSabioRKCacheManager:
    """Tests for SABIO-RK cache manager."""
    
    def test_initialization(self, temp_db):
        """Test cache manager initialization."""
        cache = SabioRKCacheManager(temp_db)
        assert cache.source_name == 'SABIO-RK'
        assert cache.db == temp_db
    
    def test_build_query_key(self, temp_db):
        """Test query key generation."""
        cache = SabioRKCacheManager(temp_db)
        
        # With organism
        key1 = cache.build_query_key('2.7.1.1', 'Homo sapiens')
        assert key1 == 'sabio_rk|2.7.1.1|Homo sapiens'
        
        # Without organism
        key2 = cache.build_query_key('2.7.1.1', None)
        assert key2 == 'sabio_rk|2.7.1.1|all'
    
    def test_cache_miss(self, temp_db):
        """Test cache miss returns None."""
        cache = SabioRKCacheManager(temp_db)
        query_key = cache.build_query_key('2.7.1.1', 'Homo sapiens')
        
        result = cache.get_cached_result(query_key)
        assert result is None
        assert cache._cache_misses == 0  # get_cached_result doesn't increment misses
    
    def test_store_and_retrieve(self, temp_db):
        """Test storing and retrieving results."""
        cache = SabioRKCacheManager(temp_db)
        query_key = cache.build_query_key('2.7.1.1', 'Homo sapiens')
        
        # Store result
        result_data = {
            'parameters': [
                {'Km': 0.1, 'Vmax': 226.0, 'organism': 'Homo sapiens'}
            ],
            'statistics': {'median_km': 0.1, 'median_vmax': 226.0}
        }
        
        success = cache.store_result(query_key, result_data)
        assert success is True
        
        # Retrieve result
        cached = cache.get_cached_result(query_key)
        assert cached is not None
        assert cached['result_count'] == 1
        assert len(cached['parameters']) == 1
        assert cached['parameters'][0]['Km'] == 0.1
    
    def test_cache_statistics(self, temp_db):
        """Test cache hit/miss statistics."""
        cache = SabioRKCacheManager(temp_db)
        
        # Initial stats
        stats = cache.get_statistics()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        
        # Simulate cache miss and hit
        query_key = cache.build_query_key('2.7.1.1', 'Homo sapiens')
        
        # First query - cache miss
        def mock_query():
            return {'parameters': [{'Km': 0.1}]}
        
        result = cache.query_with_cache(mock_query, query_key)
        assert result is not None
        assert cache._cache_misses == 1
        
        # Second query - cache hit
        cached = cache.get_cached_result(query_key)
        assert cached is not None
        # Note: get_cached_result doesn't increment stats
    
    def test_invalidate_cache(self, temp_db):
        """Test cache invalidation."""
        cache = SabioRKCacheManager(temp_db)
        query_key = cache.build_query_key('2.7.1.1', 'Homo sapiens')
        
        # Store result
        cache.store_result(query_key, {'parameters': [{'Km': 0.1}]})
        
        # Verify stored
        assert cache.get_cached_result(query_key) is not None
        
        # Invalidate
        cache.invalidate_cache(query_key)
        
        # Verify deleted
        assert cache.get_cached_result(query_key) is None
    
    def test_cache_summary(self, temp_db):
        """Test cache summary statistics."""
        cache = SabioRKCacheManager(temp_db)
        
        # Store multiple results
        for i in range(3):
            key = cache.build_query_key(f'2.7.1.{i}', 'Homo sapiens')
            cache.store_result(key, {'parameters': [{'Km': 0.1 * i}]})
        
        summary = cache.get_cache_summary()
        assert summary['total_cached_queries'] == 3
        assert summary['unique_ec_numbers'] == 3


class TestBRENDACacheManager:
    """Tests for BRENDA cache manager."""
    
    def test_initialization(self, temp_db):
        """Test cache manager initialization."""
        cache = BRENDACacheManager(temp_db)
        assert cache.source_name == 'BRENDA'
        assert cache.db == temp_db
    
    def test_build_query_key(self, temp_db):
        """Test query key generation."""
        cache = BRENDACacheManager(temp_db)
        
        # Full parameters
        key1 = cache.build_query_key('2.7.1.1', 'Km', 'Homo sapiens', 'glucose')
        assert key1 == 'brenda|2.7.1.1|Km|Homo sapiens|glucose'
        
        # Minimal parameters
        key2 = cache.build_query_key('2.7.1.1', 'Km')
        assert key2 == 'brenda|2.7.1.1|Km|all|all'
    
    def test_store_raw_data(self, temp_db):
        """Test storing raw BRENDA data."""
        cache = BRENDACacheManager(temp_db)
        
        raw_data = [
            {
                'ec_number': '2.7.1.1',
                'parameter_type': 'Km',
                'value': 0.1,
                'unit': 'mM',
                'substrate': 'glucose',
                'organism': 'Homo sapiens',
                'literature': 'PMID:12345',
                'commentary': 'Test data',
                'quality': 0.9
            }
        ]
        
        inserted = cache.store_raw_data_batch(raw_data)
        assert inserted == 1
    
    def test_query_raw_data(self, temp_db):
        """Test querying cached raw data."""
        cache = BRENDACacheManager(temp_db)
        
        # Store data
        raw_data = [
            {
                'ec_number': '2.7.1.1',
                'parameter_type': 'Km',
                'value': 0.1,
                'unit': 'mM',
                'substrate': 'glucose',
                'organism': 'Homo sapiens',
                'literature': 'PMID:12345',
                'commentary': '',
                'quality': 0.9
            }
        ]
        cache.store_raw_data_batch(raw_data)
        
        # Query
        results = cache.query_raw_data('2.7.1.1', 'Km', 'Homo sapiens')
        assert len(results) == 1
        assert results[0]['value'] == 0.1
    
    def test_cache_summary(self, temp_db):
        """Test cache summary statistics."""
        cache = BRENDACacheManager(temp_db)
        
        # Store data
        raw_data = [
            {
                'ec_number': '2.7.1.1',
                'parameter_type': 'Km',
                'value': 0.1,
                'unit': 'mM',
                'substrate': 'glucose',
                'organism': 'Homo sapiens',
                'literature': 'PMID:12345',
                'commentary': '',
                'quality': 0.9
            }
        ]
        cache.store_raw_data_batch(raw_data)
        
        summary = cache.get_cache_summary()
        assert summary['total_records'] >= 1
        assert summary['unique_ec_numbers'] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
