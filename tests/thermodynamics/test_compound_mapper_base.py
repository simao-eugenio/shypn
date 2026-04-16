"""
Tests for Compound Mapper Base Class

Tests abstract base class functionality:
- Batch mapping with caching
- URN parsing (KEGG, ChEBI, BiGG)
- Cache management and statistics
"""

import pytest
from shypn.thermodynamics.compound_mapper_base import CompoundMapperBase


class MockCompoundMapper(CompoundMapperBase):
    """Mock mapper for testing base class."""
    
    def __init__(self, use_cache=True):
        super().__init__(use_cache=use_cache)
        # Mock species database
        self.mock_mappings = {
            'ATP': 'C00002',
            'ADP': 'C00008',
            'Glucose': 'C00031',
            'H2O': 'C00001',
        }
    
    def map_species(self, species):
        """Mock mapping using name lookup."""
        name = self._get_species_id(species)
        return self.mock_mappings.get(name)
    
    def _get_species_id(self, species):
        """Extract species ID (assumes string or object with 'id' attribute)."""
        if isinstance(species, str):
            return species
        return getattr(species, 'id', str(species))


class TestCompoundMapperBase:
    """Test suite for CompoundMapperBase."""
    
    def test_batch_mapping_with_cache(self):
        """Test batch mapping uses cache correctly."""
        mapper = MockCompoundMapper(use_cache=True)
        
        # Create mock species list
        species_list = ['ATP', 'ADP', 'Glucose', 'Unknown']
        
        # First mapping
        results = mapper.map_species_list(species_list)
        
        assert results['ATP'] == 'C00002'
        assert results['ADP'] == 'C00008'
        assert results['Glucose'] == 'C00031'
        assert results['Unknown'] is None
        
        # Check cache populated
        assert len(mapper._cache) == 4
        assert mapper._cache['ATP'] == 'C00002'
    
    def test_batch_mapping_without_cache(self):
        """Test batch mapping without caching."""
        mapper = MockCompoundMapper(use_cache=False)
        
        species_list = ['ATP', 'ADP']
        results = mapper.map_species_list(species_list)
        
        assert results['ATP'] == 'C00002'
        assert results['ADP'] == 'C00008'
        
        # Cache should be empty
        assert len(mapper._cache) == 0
    
    def test_kegg_urn_extraction(self):
        """Test KEGG compound ID extraction from URNs."""
        mapper = MockCompoundMapper()
        
        # Standard MIRIAM URN
        assert mapper._extract_kegg_from_urn(
            'urn:miriam:kegg.compound:C00002'
        ) == 'C00002'
        
        # Alternate format
        assert mapper._extract_kegg_from_urn(
            'urn:miriam:kegg:C00031'
        ) == 'C00031'
        
        # Short format
        assert mapper._extract_kegg_from_urn(
            'kegg.compound:C00008'
        ) == 'C00008'
        
        # Minimal format
        assert mapper._extract_kegg_from_urn(
            'kegg:C00001'
        ) == 'C00001'
        
        # Reaction (R prefix)
        assert mapper._extract_kegg_from_urn(
            'urn:miriam:kegg.compound:R00001'
        ) == 'R00001'
        
        # Case insensitive
        assert mapper._extract_kegg_from_urn(
            'URN:MIRIAM:KEGG.COMPOUND:c00002'
        ) == 'C00002'
    
    def test_kegg_urn_invalid(self):
        """Test KEGG URN extraction with invalid inputs."""
        mapper = MockCompoundMapper()
        
        # Invalid format
        assert mapper._extract_kegg_from_urn('invalid') is None
        
        # Wrong database
        assert mapper._extract_kegg_from_urn('urn:miriam:chebi:CHEBI:15422') is None
        
        # Malformed ID
        assert mapper._extract_kegg_from_urn('kegg:12345') is None
        
        # Empty
        assert mapper._extract_kegg_from_urn('') is None
        assert mapper._extract_kegg_from_urn(None) is None
    
    def test_chebi_urn_extraction(self):
        """Test ChEBI ID extraction from URNs."""
        mapper = MockCompoundMapper()
        
        # Standard MIRIAM URN
        assert mapper._extract_chebi_from_urn(
            'urn:miriam:chebi:CHEBI:15422'
        ) == 'CHEBI:15422'
        
        # URL-encoded format
        assert mapper._extract_chebi_from_urn(
            'urn:miriam:obo.chebi:CHEBI%3A15422'
        ) == 'CHEBI:15422'
        
        # Short format
        assert mapper._extract_chebi_from_urn(
            'chebi:CHEBI:30616'
        ) == 'CHEBI:30616'
        
        # Minimal format
        assert mapper._extract_chebi_from_urn(
            'CHEBI:16761'
        ) == 'CHEBI:16761'
    
    def test_bigg_urn_extraction(self):
        """Test BiGG metabolite ID extraction from URNs."""
        mapper = MockCompoundMapper()
        
        # identifiers.org URL
        assert mapper._extract_bigg_from_urn(
            'http://identifiers.org/bigg.metabolite/atp'
        ) == 'atp'
        
        # Short format
        assert mapper._extract_bigg_from_urn(
            'bigg.metabolite:glc__D'
        ) == 'glc__d'
        
        # Case insensitive
        assert mapper._extract_bigg_from_urn(
            'http://identifiers.org/bigg.metabolite/ATP'
        ) == 'atp'
    
    def test_cache_management(self):
        """Test cache clearing and statistics."""
        mapper = MockCompoundMapper(use_cache=True)
        
        # Populate cache
        mapper.map_species_list(['ATP', 'ADP', 'Unknown'])
        
        # Check stats
        stats = mapper.get_cache_stats()
        assert stats['cache_size'] == 3
        assert stats['mapped_count'] == 2  # ATP, ADP
        assert stats['unmapped_count'] == 1  # Unknown
        
        # Clear cache
        mapper.clear_cache()
        assert len(mapper._cache) == 0
        
        stats = mapper.get_cache_stats()
        assert stats['cache_size'] == 0
    
    def test_cache_reuse(self):
        """Test that cache is reused for repeated lookups."""
        mapper = MockCompoundMapper(use_cache=True)
        
        # First lookup
        result1 = mapper.map_species_list(['ATP'])
        
        # Modify mock database (cache should prevent update)
        mapper.mock_mappings['ATP'] = 'C99999'
        
        # Second lookup (should use cached value)
        result2 = mapper.map_species_list(['ATP'])
        
        # Should get original cached value, not updated one
        assert result1['ATP'] == 'C00002'
        assert result2['ATP'] == 'C00002'
        
        # Clear cache and try again
        mapper.clear_cache()
        result3 = mapper.map_species_list(['ATP'])
        
        # Now should get updated value
        assert result3['ATP'] == 'C99999'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
