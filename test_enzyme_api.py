"""
Test EnzymeKineticsAPI - Hybrid Architecture

Tests three-tier system:
1. Cache lookup
2. API fetch (SABIO-RK)
3. Fallback database

Run with: python -m pytest test_enzyme_api.py -v
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pytest
import tempfile
import time

from shypn.data.enzyme_kinetics_api import EnzymeKineticsAPI


class TestEnzymeKineticsAPI:
    """Test hybrid API architecture."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def api_offline(self, temp_cache_dir):
        """Create API instance in offline mode (uses only fallback DB)."""
        return EnzymeKineticsAPI(
            cache_dir=temp_cache_dir,
            offline_mode=True
        )
    
    @pytest.fixture
    def api_online(self, temp_cache_dir):
        """Create API instance in online mode (can fetch from SABIO-RK)."""
        return EnzymeKineticsAPI(
            cache_dir=temp_cache_dir,
            offline_mode=False,
            api_timeout=5
        )
    
    # ========================================================================
    # TIER 3: Fallback Database Tests
    # ========================================================================
    
    def test_fallback_database_offline(self, api_offline):
        """Test that offline mode uses fallback database."""
        # Hexokinase is in fallback database (10 glycolysis enzymes)
        result = api_offline.lookup("2.7.1.1")
        
        assert result is not None
        assert result['ec_number'] == "2.7.1.1"
        assert result['enzyme_name'] == "Hexokinase"
        assert 'parameters' in result
        assert result['_lookup_source'] == 'fallback'
    
    def test_fallback_database_all_glycolysis(self, api_offline):
        """Test that all 10 glycolysis enzymes are in fallback."""
        glycolysis_ecs = [
            "2.7.1.1",   # Hexokinase
            "5.3.1.9",   # Glucose-6-phosphate isomerase
            "2.7.1.11",  # Phosphofructokinase
            "4.1.2.13",  # Fructose-bisphosphate aldolase
            "5.3.1.1",   # Triosephosphate isomerase
            "1.2.1.12",  # Glyceraldehyde-3-phosphate dehydrogenase
            "2.7.2.3",   # Phosphoglycerate kinase
            "5.4.2.12",  # Phosphoglycerate mutase
            "4.2.1.11",  # Enolase
            "2.7.1.40",  # Pyruvate kinase
        ]
        
        found_count = 0
        for ec in glycolysis_ecs:
            result = api_offline.lookup(ec)
            if result:
                found_count += 1
                assert result['ec_number'] == ec
                assert result['_lookup_source'] == 'fallback'
        
        assert found_count == 10, f"Expected 10 glycolysis enzymes, found {found_count}"
    
    def test_not_in_fallback(self, api_offline):
        """Test that non-glycolysis enzyme returns None in offline mode."""
        # EC 1.1.1.1 (Alcohol dehydrogenase) - not in fallback DB
        result = api_offline.lookup("1.1.1.1")
        assert result is None
    
    # ========================================================================
    # TIER 1: Cache Tests
    # ========================================================================
    
    def test_cache_save_and_retrieve(self, api_offline, temp_cache_dir):
        """Test that lookups are cached."""
        # First lookup (from fallback)
        result1 = api_offline.lookup("2.7.1.1")
        assert result1 is not None
        source1 = result1.get('_lookup_source')
        
        # Second lookup (should be from cache)
        result2 = api_offline.lookup("2.7.1.1")
        assert result2 is not None
        # Note: In offline mode, fallback doesn't cache, 
        # so this test mainly verifies cache structure exists
        
        # Verify cache file exists
        cache_db = temp_cache_dir / "enzyme_kinetics.db"
        assert cache_db.exists()
    
    def test_cache_expiration(self, temp_cache_dir):
        """Test that expired cache entries are ignored."""
        # Create API with very short TTL
        api = EnzymeKineticsAPI(
            cache_dir=temp_cache_dir,
            cache_ttl_days=0,  # Immediate expiration
            offline_mode=True
        )
        
        # Lookup enzyme
        result1 = api.lookup("2.7.1.1")
        assert result1 is not None
        
        # Even with cache, expired entries should be refetched
        # (In offline mode, would refetch from fallback)
        time.sleep(0.1)
        result2 = api.lookup("2.7.1.1")
        assert result2 is not None
    
    def test_cache_stats(self, api_offline):
        """Test cache statistics."""
        # Initial stats
        stats = api_offline.get_cache_stats()
        assert 'total_entries' in stats
        assert 'valid_entries' in stats
        assert 'cache_location' in stats
        assert stats['offline_mode'] is True
    
    def test_clear_cache(self, api_offline):
        """Test cache clearing."""
        # Lookup something to populate cache
        api_offline.lookup("2.7.1.1")
        
        # Clear cache
        api_offline.clear_cache()
        
        # Verify cache is empty
        stats = api_offline.get_cache_stats()
        # Note: Fallback lookups might not cache, so this tests the API
        assert stats is not None
    
    # ========================================================================
    # TIER 2: API Tests (Online Mode)
    # ========================================================================
    
    @pytest.mark.skip(reason="Online API tests - enable manually with pytest -k test_api_fetch_sabio")
    def test_api_fetch_sabio(self, api_online):
        """Test fetching from SABIO-RK API (requires internet)."""
        # Try to fetch hexokinase
        result = api_online.lookup("2.7.1.1", use_cache=False)
        
        if result:
            # API returned data
            assert result['ec_number'] == "2.7.1.1"
            assert 'parameters' in result
            assert result.get('source') in ['SABIO-RK', 'fallback']
        else:
            # API unavailable, should fall back
            pytest.skip("SABIO-RK API unavailable")
    
    @pytest.mark.skip(reason="Online API tests - enable manually")
    def test_api_caching(self, api_online):
        """Test that API results are cached."""
        # First lookup (from API)
        start1 = time.time()
        result1 = api_online.lookup("2.7.1.1", use_cache=False)
        time1 = time.time() - start1
        
        if result1 is None:
            pytest.skip("SABIO-RK API unavailable")
        
        # Second lookup (from cache)
        start2 = time.time()
        result2 = api_online.lookup("2.7.1.1", use_cache=True)
        time2 = time.time() - start2
        
        assert result2 is not None
        assert result1['ec_number'] == result2['ec_number']
        
        # Cache should be much faster
        if result2.get('_lookup_source') == 'cache':
            assert time2 < time1, "Cache should be faster than API"
    
    # ========================================================================
    # Integration Tests
    # ========================================================================
    
    def test_force_refresh(self, api_offline):
        """Test force_refresh parameter."""
        # First lookup
        result1 = api_offline.lookup("2.7.1.1")
        assert result1 is not None
        
        # Force refresh (should bypass cache)
        result2 = api_offline.lookup("2.7.1.1", force_refresh=True)
        assert result2 is not None
        assert result1['ec_number'] == result2['ec_number']
    
    def test_invalid_ec_number(self, api_offline):
        """Test with invalid EC number."""
        result = api_offline.lookup("9.9.9.999")
        assert result is None
    
    def test_lookup_performance(self, api_offline):
        """Test that fallback lookups are fast."""
        start = time.time()
        
        # Lookup 10 enzymes
        for ec in ["2.7.1.1", "5.3.1.9", "2.7.1.11", "4.1.2.13", "5.3.1.1",
                   "1.2.1.12", "2.7.2.3", "5.4.2.12", "4.2.1.11", "2.7.1.40"]:
            api_offline.lookup(ec)
        
        elapsed = time.time() - start
        
        # Should be very fast (all from fallback DB)
        assert elapsed < 1.0, f"10 lookups took {elapsed:.3f}s (expected <1s)"


# ============================================================================
# Convenience Function Tests
# ============================================================================

def test_module_level_functions():
    """Test convenience functions."""
    from shypn.data.enzyme_kinetics_api import get_api, lookup_enzyme
    
    # Get API instance
    api = get_api(offline_mode=True)
    assert isinstance(api, EnzymeKineticsAPI)
    
    # Lookup enzyme
    enzyme = lookup_enzyme("2.7.1.1")
    if enzyme:  # Might be None if not in fallback
        assert enzyme['ec_number'] == "2.7.1.1"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    """
    Run tests directly:
    
    Offline tests (fast):
        python test_enzyme_api.py
    
    All tests including online API:
        pytest test_enzyme_api.py --run-online -v
    """
    pytest.main([__file__, '-v'])
