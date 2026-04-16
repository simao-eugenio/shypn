"""Tests for cross-reference database.

This module tests the CrossReferenceDatabase class for mapping between
different biochemical database identifiers (KEGG, ChEBI, BiGG).
"""

import pytest
from pathlib import Path

from shypn.thermodynamics.database.xref import CrossReferenceDatabase


class TestCrossReferenceDatabase:
    """Test cross-reference database functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Initialize database (will gracefully fail if mapping files don't exist)
        self.xref = CrossReferenceDatabase()
    
    def test_initialization(self):
        """Test database initialization."""
        assert self.xref is not None
        assert hasattr(self.xref, 'kegg_to_chebi_map')
        assert hasattr(self.xref, 'chebi_to_kegg_map')
        assert hasattr(self.xref, 'bigg_to_kegg_map')
        assert hasattr(self.xref, 'alias_map')
    
    def test_chebi_to_kegg_atp_with_prefix(self):
        """Test ChEBI → KEGG conversion for ATP with CHEBI: prefix."""
        # ATP: CHEBI:15422 → C00002
        kegg_id = self.xref.chebi_to_kegg("CHEBI:15422")
        
        if self.xref.is_available():
            assert kegg_id == "C00002", "Expected ATP (CHEBI:15422) to map to C00002"
        else:
            pytest.skip("Cross-reference database not available")
    
    def test_chebi_to_kegg_atp_without_prefix(self):
        """Test ChEBI → KEGG conversion for ATP without prefix."""
        # Should work without CHEBI: prefix
        kegg_id = self.xref.chebi_to_kegg("15422")
        
        if self.xref.is_available():
            assert kegg_id == "C00002", "Expected ATP (15422) to map to C00002"
        else:
            pytest.skip("Cross-reference database not available")
    
    def test_kegg_to_chebi_atp(self):
        """Test KEGG → ChEBI conversion for ATP (may have multiple)."""
        chebi_ids = self.xref.kegg_to_chebi("C00002")
        
        if self.xref.is_available():
            assert isinstance(chebi_ids, list), "Expected list of ChEBI IDs"
            assert len(chebi_ids) > 0, "Expected at least one ChEBI ID for ATP"
            assert "CHEBI:15422" in chebi_ids, "Expected CHEBI:15422 in ATP ChEBI IDs"
        else:
            pytest.skip("Cross-reference database not available")
    
    def test_bigg_to_kegg_atp_with_compartment(self):
        """Test BiGG → KEGG conversion for ATP with compartment suffix."""
        # BiGG: atp_c (cytosolic ATP) → C00002
        kegg_id = self.xref.bigg_to_kegg("atp_c")
        
        if self.xref.is_available() and len(self.xref.bigg_to_kegg_map) > 0:
            assert kegg_id == "C00002", "Expected atp_c to map to C00002"
        else:
            pytest.skip("BiGG cross-reference data not available")
    
    def test_bigg_to_kegg_atp_without_compartment(self):
        """Test BiGG → KEGG conversion for ATP without compartment suffix."""
        # Should work without compartment suffix
        kegg_id = self.xref.bigg_to_kegg("atp")
        
        if self.xref.is_available() and len(self.xref.bigg_to_kegg_map) > 0:
            assert kegg_id == "C00002", "Expected atp to map to C00002"
        else:
            pytest.skip("BiGG cross-reference data not available")
    
    def test_resolve_alias_atp_uppercase(self):
        """Test compound name alias resolution (uppercase)."""
        kegg_id = self.xref.resolve_alias("ATP")
        
        if self.xref.is_available() and len(self.xref.alias_map) > 0:
            assert kegg_id == "C00002", "Expected 'ATP' to resolve to C00002"
        else:
            pytest.skip("Alias data not available")
    
    def test_resolve_alias_atp_lowercase(self):
        """Test compound name alias resolution (case-insensitive)."""
        kegg_id = self.xref.resolve_alias("atp")
        
        if self.xref.is_available() and len(self.xref.alias_map) > 0:
            assert kegg_id == "C00002", "Expected 'atp' to resolve to C00002"
        else:
            pytest.skip("Alias data not available")
    
    def test_resolve_alias_full_name(self):
        """Test compound name alias resolution with full name."""
        # Try common full names
        full_names = [
            "Adenosine 5'-triphosphate",
            "adenosine 5'-triphosphate",
        ]
        
        if not self.xref.is_available() or len(self.xref.alias_map) == 0:
            pytest.skip("Alias data not available")
        
        for name in full_names:
            kegg_id = self.xref.resolve_alias(name)
            if kegg_id:  # May not have all variations
                assert kegg_id == "C00002", f"Expected '{name}' to resolve to C00002"
                break
        else:
            pytest.skip("Full name aliases not available")
    
    def test_statistics(self):
        """Test database statistics."""
        stats = self.xref.get_statistics()
        
        assert isinstance(stats, dict), "Expected dict from get_statistics()"
        assert 'kegg_to_chebi' in stats
        assert 'chebi_to_kegg' in stats
        assert 'bigg_to_kegg' in stats
        assert 'aliases' in stats
        
        # All values should be non-negative integers
        for key, value in stats.items():
            assert isinstance(value, int), f"Expected int for {key}"
            assert value >= 0, f"Expected non-negative value for {key}"
    
    def test_is_available(self):
        """Test availability check."""
        is_available = self.xref.is_available()
        
        assert isinstance(is_available, bool)
        
        # If available, should have at least one mapping
        if is_available:
            stats = self.xref.get_statistics()
            total_mappings = sum(stats.values())
            assert total_mappings > 0, "Database claims to be available but has no mappings"
    
    def test_nonexistent_chebi_id(self):
        """Test behavior with nonexistent ChEBI ID."""
        kegg_id = self.xref.chebi_to_kegg("CHEBI:99999999")
        assert kegg_id is None, "Expected None for nonexistent ChEBI ID"
    
    def test_nonexistent_kegg_id(self):
        """Test behavior with nonexistent KEGG ID."""
        chebi_ids = self.xref.kegg_to_chebi("C99999")
        assert chebi_ids == [], "Expected empty list for nonexistent KEGG ID"
    
    def test_nonexistent_bigg_id(self):
        """Test behavior with nonexistent BiGG ID."""
        kegg_id = self.xref.bigg_to_kegg("nonexistent_compound_xyz")
        assert kegg_id is None, "Expected None for nonexistent BiGG ID"
    
    def test_nonexistent_alias(self):
        """Test behavior with nonexistent alias."""
        kegg_id = self.xref.resolve_alias("ThisCompoundDoesNotExist12345")
        assert kegg_id is None, "Expected None for nonexistent alias"


class TestCrossReferenceCaching:
    """Test LRU caching behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.xref = CrossReferenceDatabase()
    
    def test_cache_performance(self):
        """Test that repeated lookups are cached."""
        if not self.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        # First lookup (cache miss)
        kegg_id_1 = self.xref.chebi_to_kegg("CHEBI:15422")
        
        # Second lookup (should hit cache)
        kegg_id_2 = self.xref.chebi_to_kegg("CHEBI:15422")
        
        # Results should be identical
        assert kegg_id_1 == kegg_id_2
    
    def test_cache_with_different_formats(self):
        """Test that cache handles different ID formats correctly."""
        if not self.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        # Lookup with and without prefix should give same result
        kegg_id_with_prefix = self.xref.chebi_to_kegg("CHEBI:15422")
        kegg_id_without_prefix = self.xref.chebi_to_kegg("15422")
        
        assert kegg_id_with_prefix == kegg_id_without_prefix


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
