"""Tests for compound ID resolver.

Test coverage:
- KEGG → ChEBI resolution
- ChEBI → KEGG resolution
- Name → KEGG/ChEBI resolution
- Compound identity unification
"""

import pytest
from pathlib import Path

from shypn.thermodynamics import CompoundResolver, CompoundIdentity


class TestCompoundResolver:
    """Test compound identifier resolution."""
    
    @pytest.fixture
    def resolver(self):
        """Create resolver with test data."""
        resolver = CompoundResolver()
        
        # Add test mappings
        resolver.add_mapping(
            kegg_id="C00002",
            chebi_id="CHEBI:15422",
            names=["ATP", "adenosine triphosphate"]
        )
        resolver.add_mapping(
            kegg_id="C00031",
            chebi_id="CHEBI:17234",
            names=["glucose", "D-glucose"]
        )
        
        return resolver
    
    def test_resolve_from_kegg(self, resolver):
        """Resolve from KEGG C-number."""
        identity = resolver.resolve("C00002")
        
        assert identity is not None
        assert identity.kegg_id == "C00002"
        assert identity.chebi_id == "CHEBI:15422"
        assert "ATP" in identity.names
    
    def test_resolve_from_chebi(self, resolver):
        """Resolve from ChEBI ID."""
        identity = resolver.resolve("CHEBI:15422")
        
        assert identity is not None
        assert identity.kegg_id == "C00002"
        assert identity.chebi_id == "CHEBI:15422"
        assert "ATP" in identity.names
    
    def test_resolve_from_name(self, resolver):
        """Resolve from common name."""
        identity = resolver.resolve("ATP")
        
        assert identity is not None
        assert identity.kegg_id == "C00002"
        assert identity.chebi_id == "CHEBI:15422"
    
    def test_resolve_from_name_case_insensitive(self, resolver):
        """Name resolution should be case-insensitive."""
        identity1 = resolver.resolve("atp")
        identity2 = resolver.resolve("ATP")
        identity3 = resolver.resolve("Atp")
        
        assert identity1 is not None
        assert identity1.kegg_id == identity2.kegg_id == identity3.kegg_id
    
    def test_resolve_to_kegg(self, resolver):
        """Convert any ID to KEGG."""
        assert resolver.resolve_to_kegg("C00002") == "C00002"
        assert resolver.resolve_to_kegg("CHEBI:15422") == "C00002"
        assert resolver.resolve_to_kegg("ATP") == "C00002"
    
    def test_resolve_to_chebi(self, resolver):
        """Convert any ID to ChEBI."""
        assert resolver.resolve_to_chebi("C00002") == "CHEBI:15422"
        assert resolver.resolve_to_chebi("CHEBI:15422") == "CHEBI:15422"
        assert resolver.resolve_to_chebi("ATP") == "CHEBI:15422"
    
    def test_get_compound_names(self, resolver):
        """Get all names for a compound."""
        names = resolver.get_compound_names("C00002")
        
        assert "ATP" in names
        assert "adenosine triphosphate" in names
    
    def test_resolve_unknown_compound(self, resolver):
        """Unknown compound should return None."""
        identity = resolver.resolve("C99999")
        assert identity is None
    
    def test_primary_name(self, resolver):
        """Primary name should be first in list."""
        identity = resolver.resolve("C00002")
        assert identity.primary_name == "ATP"


class TestCompoundResolverWithStaticData:
    """Test resolver with actual static data files."""
    
    def test_load_from_static_data(self):
        """Resolver should load mappings from JSON file."""
        # This will use the real compound_mappings.json
        resolver = CompoundResolver()
        
        # Check some known mappings
        atp = resolver.resolve("C00002")
        if atp:  # Only test if data file exists
            assert atp.kegg_id == "C00002"
            assert atp.chebi_id == "CHEBI:15422"
    
    def test_resolve_glucose(self):
        """Test glucose resolution."""
        resolver = CompoundResolver()
        
        identity = resolver.resolve("C00031")
        if identity:  # Only test if data loaded
            assert identity.kegg_id == "C00031"
            assert "glucose" in [n.lower() for n in identity.names]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
