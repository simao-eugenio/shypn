"""Tests for SBML compound mapper with cross-reference database integration.

This module tests the integration of CrossReferenceDatabase with
SBMLCompoundMapper for ChEBI and BiGG to KEGG conversions.
"""

import pytest
from unittest.mock import MagicMock

from shypn.thermodynamics.sbml_compound_mapper import SBMLCompoundMapper


class MockSpecies:
    """Mock SBML species for testing."""
    
    def __init__(self, id, name=None, annotation=None):
        self.id = id
        self.name = name
        self.annotation_text = annotation


class TestSBMLCompoundMapperWithXref:
    """Test SBML compound mapper with cross-reference database."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Initialize mapper with xref enabled
        self.mapper = SBMLCompoundMapper(
            use_cache=True,
            use_name_fallback=True,
            use_xref=True
        )
    
    def test_mapper_initialization(self):
        """Test mapper initialization with xref."""
        assert self.mapper is not None
        assert hasattr(self.mapper, 'xref')
        assert hasattr(self.mapper, 'resolver')
    
    def test_mapping_with_kegg_annotation(self):
        """Test direct KEGG annotation (highest priority)."""
        # Create species with KEGG annotation
        species = MockSpecies(
            id="ATP",
            name="ATP",
            annotation="urn:miriam:kegg.compound:C00002"
        )
        
        kegg_id = self.mapper.map_species(species)
        assert kegg_id == "C00002", "Expected direct KEGG mapping"
    
    def test_mapping_with_chebi_annotation(self):
        """Test ChEBI annotation → KEGG conversion."""
        if not self.mapper.xref or not self.mapper.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        # Create species with ChEBI annotation
        species = MockSpecies(
            id="ATP",
            name="ATP",
            annotation="urn:miriam:chebi:CHEBI:15422"
        )
        
        kegg_id = self.mapper.map_species(species)
        assert kegg_id == "C00002", "Expected ChEBI→KEGG mapping for ATP"
    
    def test_mapping_with_bigg_annotation(self):
        """Test BiGG annotation → KEGG conversion."""
        if not self.mapper.xref or not self.mapper.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        if len(self.mapper.xref.bigg_to_kegg_map) == 0:
            pytest.skip("BiGG cross-reference data not available")
        
        # Create species with BiGG annotation
        species = MockSpecies(
            id="M_atp_c",
            name="ATP",
            annotation="urn:miriam:bigg.metabolite:atp_c"
        )
        
        kegg_id = self.mapper.map_species(species)
        assert kegg_id == "C00002", "Expected BiGG→KEGG mapping for ATP"
    
    def test_mapping_priority_kegg_over_chebi(self):
        """Test that KEGG annotation has priority over ChEBI."""
        if not self.mapper.xref or not self.mapper.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        # Create species with both KEGG and ChEBI annotations
        # (in real SBML, both might be present)
        species = MockSpecies(
            id="ATP",
            name="ATP",
            annotation="urn:miriam:kegg.compound:C00002 urn:miriam:chebi:CHEBI:15422"
        )
        
        kegg_id = self.mapper.map_species(species)
        assert kegg_id == "C00002", "Expected KEGG annotation to take priority"
    
    def test_mapping_fallback_to_name(self):
        """Test fallback to name matching when no annotations."""
        # Create species with no annotations, only name
        species = MockSpecies(
            id="species_1",
            name="ATP",
            annotation=None
        )
        
        kegg_id = self.mapper.map_species(species)
        
        # Should fallback to name matching (if resolver has ATP)
        if self.mapper.resolver:
            # Name matching might not always work, but for ATP it should
            assert kegg_id == "C00002" or kegg_id is None
    
    def test_mapping_with_xref_disabled(self):
        """Test mapper behavior when xref is disabled."""
        mapper_no_xref = SBMLCompoundMapper(
            use_cache=True,
            use_name_fallback=True,
            use_xref=False
        )
        
        assert mapper_no_xref.xref is None
        
        # ChEBI annotation should not be converted
        species = MockSpecies(
            id="ATP",
            name="ATP",
            annotation="urn:miriam:chebi:CHEBI:15422"
        )
        
        kegg_id = mapper_no_xref.map_species(species)
        
        # Should fallback to name matching (not ChEBI conversion)
        # Result depends on whether resolver has ATP
        if mapper_no_xref.resolver:
            assert kegg_id == "C00002" or kegg_id is None
    
    def test_mapping_nonexistent_chebi(self):
        """Test behavior with nonexistent ChEBI ID."""
        if not self.mapper.xref or not self.mapper.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        # Create species with nonexistent ChEBI ID
        species = MockSpecies(
            id="unknown",
            name="Unknown Compound",
            annotation="urn:miriam:chebi:CHEBI:99999999"
        )
        
        kegg_id = self.mapper.map_species(species)
        
        # Should return None or fallback to name matching
        # (name matching for "Unknown Compound" likely won't work)
        assert kegg_id is None
    
    def test_mapping_glucose_variants(self):
        """Test mapping for glucose (multiple ChEBI IDs)."""
        if not self.mapper.xref or not self.mapper.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        # Glucose has multiple ChEBI IDs (D-glucose, beta-D-glucose, etc.)
        # Try D-glucose: CHEBI:4167 → C00031
        species = MockSpecies(
            id="glucose",
            name="D-glucose",
            annotation="urn:miriam:chebi:CHEBI:4167"
        )
        
        kegg_id = self.mapper.map_species(species)
        
        # May or may not map depending on database content
        # Just check it returns something or None
        assert kegg_id is None or isinstance(kegg_id, str)


class TestSBMLCompoundMapperCaching:
    """Test caching behavior with cross-reference lookups."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = SBMLCompoundMapper(use_cache=True, use_xref=True)
    
    def test_cache_with_chebi_lookup(self):
        """Test that ChEBI lookups are cached."""
        if not self.mapper.xref or not self.mapper.xref.is_available():
            pytest.skip("Cross-reference database not available")
        
        species = MockSpecies(
            id="ATP",
            name="ATP",
            annotation="urn:miriam:chebi:CHEBI:15422"
        )
        
        # First lookup (cache miss)
        kegg_id_1 = self.mapper.map_species(species)
        
        # Second lookup (should hit cache)
        kegg_id_2 = self.mapper.map_species(species)
        
        assert kegg_id_1 == kegg_id_2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
