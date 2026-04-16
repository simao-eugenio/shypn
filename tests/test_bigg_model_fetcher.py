"""Unit tests for BiGG model fetcher service."""

import unittest
from unittest.mock import Mock, patch
import json

from shypn.importer.bigg.bigg_model_fetcher import BiGGModelFetcher, BiGGModelInfo


class TestBiGGModelFetcher(unittest.TestCase):
    """Test cases for BiGGModelFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = BiGGModelFetcher()
    
    def test_initialization(self):
        """Test fetcher initialization."""
        self.assertIsNotNone(self.fetcher)
        self.assertEqual(self.fetcher.base_url, "http://bigg.ucsd.edu")
        self.assertIsNone(self.fetcher._model_cache)
    
    @patch('urllib.request.urlopen')
    def test_validate_success(self, mock_urlopen):
        """Test successful API validation."""
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'api_version': 'v2',
            'last_updated': '2019-10-31'
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = self.fetcher.validate()
        
        self.assertTrue(result)
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlopen')
    def test_fetch_models_success(self, mock_urlopen):
        """Test successful model fetching."""
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'results': [
                {
                    'bigg_id': 'e_coli_core',
                    'organism': 'Escherichia coli',
                    'reaction_count': 95,
                    'metabolite_count': 72,
                    'gene_count': 137
                },
                {
                    'bigg_id': 'iML1515',
                    'organism': 'Escherichia coli K-12 MG1655',
                    'reaction_count': 2712,
                    'metabolite_count': 1877,
                    'gene_count': 1516
                }
            ]
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        models = self.fetcher.fetch_models()
        
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0].id, 'e_coli_core')
        self.assertEqual(models[0].reaction_count, 95)
        self.assertEqual(models[1].id, 'iML1515')
    
    def test_fetch_models_uses_cache(self):
        """Test that fetch_models uses cache."""
        # Set up cache
        cached_models = [
            BiGGModelInfo(
                id='test_model',
                name='Test',
                organism='Test organism',
                reaction_count=10,
                metabolite_count=5,
                gene_count=3
            )
        ]
        self.fetcher._model_cache = cached_models
        
        # Fetch without force_refresh should return cache
        models = self.fetcher.fetch_models(force_refresh=False)
        
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].id, 'test_model')
    
    def test_filter_by_organism(self):
        """Test organism filtering."""
        # Set up test data
        self.fetcher._model_cache = [
            BiGGModelInfo(
                id='e_coli_core',
                name='E. coli',
                organism='Escherichia coli',
                reaction_count=95,
                metabolite_count=72,
                gene_count=137
            ),
            BiGGModelInfo(
                id='yeast_model',
                name='Yeast',
                organism='Saccharomyces cerevisiae',
                reaction_count=100,
                metabolite_count=80,
                gene_count=150
            )
        ]
        
        # Filter for E. coli
        results = self.fetcher.filter_by_organism('Escherichia')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'e_coli_core')
    
    def test_search_models(self):
        """Test model search."""
        # Set up test data
        self.fetcher._model_cache = [
            BiGGModelInfo(
                id='e_coli_core',
                name='E. coli core',
                organism='Escherichia coli',
                reaction_count=95,
                metabolite_count=72,
                gene_count=137
            ),
            BiGGModelInfo(
                id='iML1515',
                name='E. coli comprehensive',
                organism='Escherichia coli K-12',
                reaction_count=2712,
                metabolite_count=1877,
                gene_count=1516
            ),
            BiGGModelInfo(
                id='yeast_model',
                name='Yeast',
                organism='Saccharomyces cerevisiae',
                reaction_count=100,
                metabolite_count=80,
                gene_count=150
            )
        ]
        
        # Search for 'core'
        results = self.fetcher.search_models('core')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'e_coli_core')
        
        # Search for 'coli' (should match organism)
        results = self.fetcher.search_models('coli')
        
        self.assertEqual(len(results), 2)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        self.fetcher._model_cache = [Mock()]
        
        self.fetcher.clear_cache()
        
        self.assertIsNone(self.fetcher._model_cache)


if __name__ == '__main__':
    unittest.main()
