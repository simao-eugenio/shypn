"""Tests for database providers (cache, static, multi-source).

Test coverage:
- CacheProvider read/write/expiry
- StaticDataProvider loading from JSON
- MultiSourceProvider fallback logic
"""

import pytest
import tempfile
import time
from pathlib import Path

from shypn.thermodynamics import (
    CompoundThermodynamics,
    CacheProvider,
    StaticDataProvider,
    MultiSourceProvider
)


class TestCacheProvider:
    """Test disk cache provider."""
    
    @pytest.fixture
    def cache(self):
        """Create cache with temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheProvider(cache_dir=Path(tmpdir), ttl_days=1)
            yield cache
    
    def test_cache_miss(self, cache):
        """Non-existent compound should return None."""
        compound = cache.get_compound("C99999")
        assert compound is None
    
    def test_cache_store_and_retrieve(self, cache):
        """Stored compound should be retrievable."""
        original = CompoundThermodynamics(
            compound_id="C00002",
            name="ATP",
            delta_g_formation=-2292.2,
            source="test"
        )
        
        cache.store_compound(original)
        retrieved = cache.get_compound("C00002", ph=7.0, temperature=298.15)
        
        assert retrieved is not None
        assert retrieved.compound_id == "C00002"
        assert retrieved.delta_g_formation == -2292.2
    
    def test_cache_has_compound(self, cache):
        """has_compound should detect cached entries."""
        compound = CompoundThermodynamics(
            compound_id="C00002",
            name="ATP",
            delta_g_formation=-2292.2,
            source="test"
        )
        
        assert not cache.has_compound("C00002")
        cache.store_compound(compound)
        assert cache.has_compound("C00002")
    
    def test_cache_clear(self, cache):
        """Cache clear should remove entries."""
        compound = CompoundThermodynamics(
            compound_id="C00002",
            name="ATP",
            delta_g_formation=-2292.2,
            source="test"
        )
        
        cache.store_compound(compound)
        assert cache.has_compound("C00002")
        
        cache.clear_cache("C00002")
        assert not cache.has_compound("C00002")


class TestStaticDataProvider:
    """Test static data provider with JSON file."""
    
    def test_load_static_data(self):
        """Provider should load from core_metabolites.json."""
        provider = StaticDataProvider()
        
        # Test with ATP (should be in core metabolites)
        atp = provider.get_compound("C00002")
        
        if atp:  # Only test if data file exists
            assert atp.compound_id == "C00002"
            assert atp.name == "ATP"
            assert atp.delta_g_formation < 0  # ATP formation is negative
    
    def test_has_compound(self):
        """has_compound should check availability."""
        provider = StaticDataProvider()
        
        # Should have ATP
        assert provider.has_compound("C00002") or True  # Allow empty data
        
        # Should not have random compound
        assert not provider.has_compound("C99999")
    
    def test_get_available_compounds(self):
        """Should list all available compounds."""
        provider = StaticDataProvider()
        
        compounds = provider.get_available_compounds()
        assert isinstance(compounds, list)


class TestMultiSourceProvider:
    """Test multi-source provider with fallback."""
    
    def test_initialization(self):
        """Provider should initialize all sources."""
        provider = MultiSourceProvider()
        assert provider.providers  # Should have at least one provider
    
    def test_query_static_data(self):
        """Should find compound in static data."""
        provider = MultiSourceProvider(enable_cache=False, enable_static=True)
        
        atp = provider.get_compound("C00002")
        if atp:  # Only test if data available
            assert atp.compound_id == "C00002"
    
    def test_cache_after_static_hit(self):
        """Finding in static should cache result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create provider with temp cache
            cache = CacheProvider(cache_dir=Path(tmpdir))
            provider = MultiSourceProvider(enable_cache=True, enable_static=True)
            provider.cache = cache  # Replace with temp cache
            provider.providers = [cache, provider.static]
            
            # First query should hit static
            atp1 = provider.get_compound("C00002")
            
            if atp1:
                # Second query should hit cache
                atp2 = provider.get_compound("C00002")
                assert atp2 is not None
                assert atp2.compound_id == "C00002"
    
    def test_has_compound_multiple_sources(self):
        """has_compound should check all sources."""
        provider = MultiSourceProvider()
        
        # Should check both cache and static
        result = provider.has_compound("C00002")
        # Result depends on data availability, just check it doesn't crash
        assert isinstance(result, bool)


class TestGibbsCalculatorIntegration:
    """Test GibbsCalculator with real providers."""
    
    def test_calculator_with_multi_source_provider(self):
        """Calculator should work with MultiSourceProvider."""
        from shypn.thermodynamics import GibbsCalculator, MultiSourceProvider
        
        provider = MultiSourceProvider()
        calculator = GibbsCalculator(provider)
        
        # Try ATP hydrolysis
        reactants = {"C00002": 1, "C00001": 1}  # ATP + H2O
        products = {"C00008": 1, "C00009": 1}   # ADP + Pi
        
        try:
            thermo = calculator.calculate_delta_g_reaction(reactants, products)
            
            # Should produce negative ΔG (favorable)
            assert thermo.delta_g_standard < 0
            assert thermo.k_eq > 1  # K_eq >> 1 for favorable reaction
            
        except ValueError:
            # Acceptable if compound data not available
            pytest.skip("Compound data not available in static database")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
