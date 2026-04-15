"""
Unit tests for KEGG EC Number Fetcher

Tests the KEGGECFetcher class that fetches EC numbers from KEGG REST API.
"""

import unittest
from unittest.mock import Mock, patch
import requests
from shypn.data.kegg_ec_fetcher import (
    KEGGECFetcher,
    fetch_ec_for_reaction,
    get_default_fetcher,
    reset_default_fetcher
)


class TestKEGGECFetcher(unittest.TestCase):
    """Test KEGGECFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = KEGGECFetcher(timeout=5)
    
    def test_parse_kegg_response_single_ec(self):
        """Test parsing KEGG response with single EC number."""
        response = """ENTRY       R00710              Reaction
NAME        ...
ENZYME      2.7.1.1
PATHWAY     ...
"""
        ec_numbers = self.fetcher._parse_kegg_response(response)
        self.assertEqual(ec_numbers, ["2.7.1.1"])
    
    def test_parse_kegg_response_multiple_ec_same_line(self):
        """Test parsing KEGG response with multiple EC numbers on same line."""
        response = """ENTRY       R00001              Reaction
ENZYME      1.1.1.1 1.1.1.2 1.1.1.3
"""
        ec_numbers = self.fetcher._parse_kegg_response(response)
        self.assertEqual(ec_numbers, ["1.1.1.1", "1.1.1.2", "1.1.1.3"])
    
    def test_parse_kegg_response_multiple_ec_lines(self):
        """Test parsing KEGG response with multiple ENZYME lines."""
        response = """ENTRY       R00001              Reaction
ENZYME      1.1.1.1
ENZYME      1.1.1.2
"""
        ec_numbers = self.fetcher._parse_kegg_response(response)
        self.assertEqual(ec_numbers, ["1.1.1.1", "1.1.1.2"])
    
    def test_parse_kegg_response_no_enzyme(self):
        """Test parsing KEGG response without ENZYME field."""
        response = """ENTRY       R00001              Reaction
NAME        ...
PATHWAY     ...
"""
        ec_numbers = self.fetcher._parse_kegg_response(response)
        self.assertEqual(ec_numbers, [])
    
    def test_parse_kegg_response_incomplete_ec(self):
        """Test parsing KEGG response with incomplete EC number."""
        response = """ENTRY       R00001              Reaction
ENZYME      2.7.1.-
"""
        ec_numbers = self.fetcher._parse_kegg_response(response)
        self.assertEqual(ec_numbers, ["2.7.1.-"])
    
    def test_is_valid_ec_number_complete(self):
        """Test EC number validation - complete EC."""
        self.assertTrue(self.fetcher._is_valid_ec_number("2.7.1.1"))
        self.assertTrue(self.fetcher._is_valid_ec_number("1.1.1.1"))
        self.assertTrue(self.fetcher._is_valid_ec_number("6.2.1.3"))
    
    def test_is_valid_ec_number_incomplete(self):
        """Test EC number validation - incomplete EC."""
        self.assertTrue(self.fetcher._is_valid_ec_number("2.7.1.-"))
        self.assertTrue(self.fetcher._is_valid_ec_number("2.7.-.-"))
        self.assertTrue(self.fetcher._is_valid_ec_number("2.-.-.-"))
    
    def test_is_valid_ec_number_invalid(self):
        """Test EC number validation - invalid formats."""
        self.assertFalse(self.fetcher._is_valid_ec_number(""))
        self.assertFalse(self.fetcher._is_valid_ec_number("2.7.1"))  # Too few parts
        self.assertFalse(self.fetcher._is_valid_ec_number("2.7.1.1.1"))  # Too many parts
        self.assertFalse(self.fetcher._is_valid_ec_number("-.7.1.1"))  # First part is -
        self.assertFalse(self.fetcher._is_valid_ec_number("a.b.c.d"))  # Letters
        self.assertFalse(self.fetcher._is_valid_ec_number("2.7.1.x"))  # Invalid char
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_numbers_success(self, mock_get):
        """Test successful EC number fetch from KEGG API."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """ENTRY       R00710              Reaction
NAME        hexokinase
ENZYME      2.7.1.1
"""
        mock_get.return_value = mock_response
        
        # Fetch EC numbers
        ec_numbers = self.fetcher.fetch_ec_numbers("R00710")
        
        # Verify
        self.assertEqual(ec_numbers, ["2.7.1.1"])
        mock_get.assert_called_once_with(
            "https://rest.kegg.jp/get/R00710",
            timeout=5
        )
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_numbers_cache(self, mock_get):
        """Test caching of EC numbers."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """ENTRY       R00710              Reaction
ENZYME      2.7.1.1
"""
        mock_get.return_value = mock_response
        
        # First fetch - should hit API
        ec1 = self.fetcher.fetch_ec_numbers("R00710")
        self.assertEqual(ec1, ["2.7.1.1"])
        self.assertEqual(mock_get.call_count, 1)
        
        # Second fetch - should use cache
        ec2 = self.fetcher.fetch_ec_numbers("R00710")
        self.assertEqual(ec2, ["2.7.1.1"])
        self.assertEqual(mock_get.call_count, 1)  # Still 1 - no new call
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_numbers_timeout(self, mock_get):
        """Test handling of API timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        ec_numbers = self.fetcher.fetch_ec_numbers("R00710")
        self.assertEqual(ec_numbers, [])
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_numbers_http_error(self, mock_get):
        """Test handling of HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        ec_numbers = self.fetcher.fetch_ec_numbers("R00710")
        self.assertEqual(ec_numbers, [])
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_numbers_no_enzyme_field(self, mock_get):
        """Test fetching when no ENZYME field in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """ENTRY       R00001              Reaction
NAME        ...
PATHWAY     ...
"""
        mock_get.return_value = mock_response
        
        ec_numbers = self.fetcher.fetch_ec_numbers("R00001")
        self.assertEqual(ec_numbers, [])
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_numbers_normalize_id(self, mock_get):
        """Test normalization of reaction ID (remove rn: prefix)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """ENTRY       R00710              Reaction
ENZYME      2.7.1.1
"""
        mock_get.return_value = mock_response
        
        # Fetch with "rn:" prefix
        ec_numbers = self.fetcher.fetch_ec_numbers("rn:R00710")
        
        # Should remove prefix and fetch correctly
        self.assertEqual(ec_numbers, ["2.7.1.1"])
        mock_get.assert_called_once_with(
            "https://rest.kegg.jp/get/R00710",  # No "rn:" prefix
            timeout=5
        )
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        # Add to cache
        self.fetcher.cache["R00710"] = ["2.7.1.1"]
        self.assertEqual(len(self.fetcher.cache), 1)
        
        # Clear cache
        self.fetcher.clear_cache()
        self.assertEqual(len(self.fetcher.cache), 0)
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Empty cache
        stats = self.fetcher.get_cache_stats()
        self.assertEqual(stats["size"], 0)
        
        # Add entries
        self.fetcher.cache["R00710"] = ["2.7.1.1"]
        self.fetcher.cache["R01015"] = ["2.7.1.11"]
        
        stats = self.fetcher.get_cache_stats()
        self.assertEqual(stats["size"], 2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""
    
    @patch('shypn.data.kegg_ec_fetcher.requests.get')
    def test_fetch_ec_for_reaction(self, mock_get):
        """Test convenience function."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """ENTRY       R00710              Reaction
ENZYME      2.7.1.1
"""
        mock_get.return_value = mock_response
        
        ec_numbers = fetch_ec_for_reaction("R00710")
        self.assertEqual(ec_numbers, ["2.7.1.1"])
    
    def test_get_default_fetcher_singleton(self):
        """Test that default fetcher is a singleton."""
        reset_default_fetcher()  # Start fresh
        
        fetcher1 = get_default_fetcher()
        fetcher2 = get_default_fetcher()
        
        self.assertIs(fetcher1, fetcher2)  # Same instance
    
    def test_reset_default_fetcher(self):
        """Test resetting default fetcher."""
        fetcher1 = get_default_fetcher()
        reset_default_fetcher()
        fetcher2 = get_default_fetcher()
        
        self.assertIsNot(fetcher1, fetcher2)  # Different instances


class TestRealKEGGAPI(unittest.TestCase):
    """
    Integration tests with real KEGG API.
    
    These tests make real HTTP requests to KEGG.
    Skip if network is unavailable or for faster testing.
    """
    
    @unittest.skip("Integration test - requires network")
    def test_fetch_hexokinase_real(self):
        """Test fetching hexokinase EC number from real KEGG API."""
        fetcher = KEGGECFetcher(timeout=10)
        ec_numbers = fetcher.fetch_ec_numbers("R00710")
        
        # R00710 should have EC 2.7.1.1 (hexokinase)
        self.assertIn("2.7.1.1", ec_numbers)
    
    @unittest.skip("Integration test - requires network")
    def test_fetch_phosphofructokinase_real(self):
        """Test fetching phosphofructokinase EC from real KEGG API."""
        fetcher = KEGGECFetcher(timeout=10)
        ec_numbers = fetcher.fetch_ec_numbers("R01015")
        
        # R01015 should have EC 2.7.1.11 (6-phosphofructokinase)
        self.assertIn("2.7.1.11", ec_numbers)


if __name__ == '__main__':
    unittest.main()
