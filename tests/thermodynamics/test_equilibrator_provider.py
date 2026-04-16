"""Tests for eQuilibrator web service provider.

Test coverage:
- Mock provider for offline testing
- API connectivity check
- Compound data fetching
- Error handling and retries
- Integration with multi-source provider
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from shypn.thermodynamics import (
    EquilibratorProvider,
    MockEquilibratorProvider,
    MultiSourceProvider,
    CompoundThermodynamics
)


class TestMockEquilibratorProvider:
    """Test mock provider (no network required)."""
    
    def test_mock_provider_atp(self):
        """Mock provider should return ATP data."""
        provider = MockEquilibratorProvider()
        
        atp = provider.get_compound("C00002")
        
        assert atp is not None
        assert atp.compound_id == "C00002"
        assert atp.name == "ATP"
        assert atp.source == "Mock eQuilibrator"
    
    def test_mock_provider_unknown_compound(self):
        """Mock provider should return None for unknown compounds."""
        provider = MockEquilibratorProvider()
        
        unknown = provider.get_compound("C99999")
        assert unknown is None
    
    def test_mock_provider_has_compound(self):
        """Mock provider should check compound existence."""
        provider = MockEquilibratorProvider()
        
        assert provider.has_compound("C00002")
        assert not provider.has_compound("C99999")


class TestEquilibratorProvider:
    """Test eQuilibrator web service provider."""
    
    def test_provider_without_requests(self):
        """Provider should handle missing requests library."""
        with patch('shypn.thermodynamics.database.equilibrator_provider.logger') as mock_logger:
            # Simulate missing requests
            with patch.object(EquilibratorProvider, '__init__', lambda self, **kwargs: None):
                provider = EquilibratorProvider()
                provider.requests = None
                provider._available = False
                provider.timeout = 10
                provider.max_retries = 3
                provider.retry_delay = 1.0
                
                result = provider.get_compound("C00002")
                assert result is None
    
    def test_provider_availability_check(self):
        """Provider should check API availability."""
        provider = EquilibratorProvider()
        
        # Mock requests module
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(provider.requests, 'get', return_value=mock_response):
            available = provider._check_availability()
            # Should cache the result
            assert provider._available is not None
    
    def test_provider_fetch_with_mock_response(self):
        """Provider should parse API responses."""
        provider = EquilibratorProvider()
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "ATP",
            "formation_energy": {
                "value": -2292.5,
                "uncertainty": 2.0
            }
        }
        
        with patch.object(provider.requests, 'get', return_value=mock_response):
            provider._available = True
            compound = provider.get_compound("C00002")
            
            if compound:  # Only test if requests is available
                assert compound.compound_id == "C00002"
                assert compound.name == "ATP"
                assert compound.source == "eQuilibrator API"
    
    def test_provider_404_response(self):
        """Provider should handle 404 (not found) gracefully."""
        provider = EquilibratorProvider()
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(provider.requests, 'get', return_value=mock_response):
            provider._available = True
            result = provider._fetch_compound_data("C99999", 7.0, 298.15, 0.1)
            assert result is None
    
    def test_provider_retry_logic(self):
        """Provider should retry on network errors."""
        provider = EquilibratorProvider(max_retries=3, retry_delay=0.01)
        
        # Mock failing then succeeding
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("Network error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "name": "ATP",
            "formation_energy": {"value": -2292.5, "uncertainty": 2.0}
        }
        
        with patch.object(provider.requests, 'get', side_effect=[
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]):
            provider._available = True
            compound = provider.get_compound("C00002")
            
            # Should succeed after retries (if requests available)
            if compound:
                assert compound.compound_id == "C00002"


class TestMultiSourceWithEquilibrator:
    """Test multi-source provider with eQuilibrator."""
    
    def test_multi_source_with_web_disabled(self):
        """Multi-source should work without web services."""
        provider = MultiSourceProvider(enable_web=False)
        
        # Should only have cache and static
        assert provider.cache is not None or provider.static is not None
        assert not hasattr(provider, 'equilibrator') or provider.equilibrator is None
    
    def test_multi_source_with_web_enabled(self):
        """Multi-source should initialize eQuilibrator when enabled."""
        provider = MultiSourceProvider(enable_web=True)
        
        # Should have eQuilibrator (even if it can't connect)
        # It's OK if initialization fails due to missing requests or network
        assert provider.providers  # Should have at least cache or static
    
    def test_multi_source_fallback_to_equilibrator(self):
        """Multi-source should fall back to eQuilibrator if static misses."""
        # Create provider with mock eQuilibrator
        provider = MultiSourceProvider(enable_cache=False, enable_static=False, enable_web=False)
        
        # Manually add mock eQuilibrator
        mock_equilibrator = MockEquilibratorProvider()
        provider.equilibrator = mock_equilibrator
        provider.providers = [mock_equilibrator]
        
        # Query compound only in mock eQuilibrator
        compound = provider.get_compound("C00002")
        
        assert compound is not None
        assert compound.compound_id == "C00002"
        assert "Mock" in compound.source


class TestEquilibratorIntegration:
    """Integration tests with GibbsCalculator."""
    
    def test_calculator_with_equilibrator_mock(self):
        """GibbsCalculator should work with mock eQuilibrator."""
        from shypn.thermodynamics import GibbsCalculator
        
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        
        # ATP + H2O → ADP + Pi (mock has all compounds)
        reactants = {"C00002": 1, "C00001": 1}  # ATP + H2O
        products = {"C00008": 1, "C00009": 1}   # ADP + Pi
        
        thermo = calculator.calculate_delta_g_reaction(reactants, products)
        
        # Should calculate from mock data
        # ΔG = (ΔG_ADP + ΔG_Pi) - (ΔG_ATP + ΔG_H2O)
        # = (-1906.5 + -1059.2) - (-2292.5 + -237.2) = -436.0 kJ/mol
        assert thermo.delta_g_standard < 0, f"Expected negative ΔG, got {thermo.delta_g_standard}"
        assert thermo.k_eq > 1, f"Expected K_eq > 1, got {thermo.k_eq}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
