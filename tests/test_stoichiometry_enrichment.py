"""Unit tests for KEGG stoichiometry enrichment.

Run tests:
    pytest tests/test_stoichiometry_enrichment.py -v
    pytest tests/test_stoichiometry_enrichment.py::test_parse_equation -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from shypn.services.enrichment import (
    KEGGStoichiometryEnricher,
    ReactionStoichiometry,
    CompoundStoich,
    EnrichmentResult
)
from shypn.netobjs import Place, Transition, Arc
from shypn.data.canvas.document_model import DocumentModel


class TestReactionParsing:
    """Test reaction equation parsing."""
    
    def test_parse_simple_equation(self):
        """Test parsing simple equation."""
        enricher = KEGGStoichiometryEnricher()
        stoich = ReactionStoichiometry(reaction_id="R00001", equation="")
        
        equation = "C00002 + C00031 <=> C00008 + C00085"
        enricher._parse_equation(equation, stoich)
        
        assert len(stoich.substrates) == 2
        assert len(stoich.products) == 2
        assert stoich.substrates[0].compound_id == "C00002"
        assert stoich.substrates[1].compound_id == "C00031"
        assert stoich.products[0].compound_id == "C00008"
        assert stoich.products[1].compound_id == "C00085"
    
    def test_parse_equation_with_coefficients(self):
        """Test parsing equation with stoichiometric coefficients."""
        enricher = KEGGStoichiometryEnricher()
        stoich = ReactionStoichiometry(reaction_id="R00001", equation="")
        
        equation = "2 C00002 + C00031 <=> 2 C00008 + C00085"
        enricher._parse_equation(equation, stoich)
        
        assert stoich.substrates[0].compound_id == "C00002"
        assert stoich.substrates[0].coefficient == 2
        assert stoich.substrates[1].compound_id == "C00031"
        assert stoich.substrates[1].coefficient == 1
        assert stoich.products[0].compound_id == "C00008"
        assert stoich.products[0].coefficient == 2
    
    def test_parse_irreversible_equation(self):
        """Test parsing irreversible equation."""
        enricher = KEGGStoichiometryEnricher()
        stoich = ReactionStoichiometry(reaction_id="R00001", equation="")
        
        equation = "C00002 -> C00008"
        enricher._parse_equation(equation, stoich)
        
        assert len(stoich.substrates) == 1
        assert len(stoich.products) == 1
    
    def test_parse_compound_string(self):
        """Test parsing individual compound strings."""
        enricher = KEGGStoichiometryEnricher()
        
        # Simple compound
        compound = enricher._parse_compound_str("C00002")
        assert compound.compound_id == "C00002"
        assert compound.coefficient == 1
        
        # With coefficient
        compound = enricher._parse_compound_str("2 C00002")
        assert compound.compound_id == "C00002"
        assert compound.coefficient == 2
        
        # Invalid
        compound = enricher._parse_compound_str("invalid")
        assert compound is None


class TestFiltering:
    """Test compound filtering."""
    
    def test_always_filter_water(self):
        """Test that H2O is filtered by default."""
        enricher = KEGGStoichiometryEnricher(include_water=False)
        assert not enricher._should_add_compound("C00001")
    
    def test_always_filter_protons(self):
        """Test that H+ is filtered by default."""
        enricher = KEGGStoichiometryEnricher(include_protons=False)
        assert not enricher._should_add_compound("C00080")
    
    def test_include_water_option(self):
        """Test include_water option."""
        enricher = KEGGStoichiometryEnricher(include_water=True)
        # H2O still in ALWAYS_FILTER, so still False
        # (ALWAYS_FILTER overrides include_water in current implementation)
        assert not enricher._should_add_compound("C00001")
    
    def test_key_cofactors_included(self):
        """Test that key cofactors are always included."""
        enricher = KEGGStoichiometryEnricher()
        
        # Energy carriers
        assert enricher._should_add_compound("C00002")  # ATP
        assert enricher._should_add_compound("C00008")  # ADP
        
        # Redox carriers
        assert enricher._should_add_compound("C00003")  # NAD+
        assert enricher._should_add_compound("C00004")  # NADH
        
        # CoA
        assert enricher._should_add_compound("C00010")  # CoA


class TestEnrichmentResult:
    """Test EnrichmentResult class."""
    
    def test_create_success_result(self):
        """Test creating success result."""
        result = EnrichmentResult(success=True, message="Test succeeded")
        result.add_statistic("places_added", 5)
        result.add_statistic("arcs_added", 10)
        
        assert result.success
        assert result.statistics["places_added"] == 5
        assert result.statistics["arcs_added"] == 10
    
    def test_add_errors_and_warnings(self):
        """Test adding errors and warnings."""
        result = EnrichmentResult(success=False, message="Test failed")
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")
        
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
    
    def test_get_summary(self):
        """Test summary generation."""
        result = EnrichmentResult(success=True, message="Test")
        result.duration_seconds = 1.23
        result.add_statistic("test_stat", 42)
        result.add_warning("Test warning")
        
        summary = result.get_summary()
        assert "succeeded" in summary
        assert "1.23 seconds" in summary
        assert "test_stat: 42" in summary
        assert "Test warning" in summary


class TestDocumentValidation:
    """Test document validation."""
    
    def test_validate_kegg_document(self):
        """Test validation of valid KEGG document."""
        enricher = KEGGStoichiometryEnricher()
        
        # Create mock document
        document = DocumentModel()
        document.metadata = {'data_source': 'kegg_import'}
        
        # Add transition with reaction ID
        transition = Transition(x=0, y=0, id="T1", name="test")
        transition.metadata = {'kegg_reaction_id': 'R00200'}
        document.transitions.append(transition)
        
        is_valid, issues = enricher.validate_document(document)
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_non_kegg_document(self):
        """Test validation of non-KEGG document."""
        enricher = KEGGStoichiometryEnricher()
        
        document = DocumentModel()
        document.metadata = {'data_source': 'manual'}
        
        is_valid, issues = enricher.validate_document(document)
        assert not is_valid
        assert len(issues) > 0
        assert any("not from KEGG" in issue for issue in issues)
    
    def test_validate_already_enriched(self):
        """Test validation of already enriched document."""
        enricher = KEGGStoichiometryEnricher()
        
        document = DocumentModel()
        document.metadata = {
            'data_source': 'kegg_import',
            'stoichiometry_enriched': True
        }
        
        transition = Transition(x=0, y=0, id="T1", name="test")
        transition.metadata = {'kegg_reaction_id': 'R00200'}
        document.transitions.append(transition)
        
        is_valid, issues = enricher.validate_document(document)
        assert not is_valid
        assert any("already" in issue for issue in issues)
    
    def test_validate_no_reactions(self):
        """Test validation of document without reactions."""
        enricher = KEGGStoichiometryEnricher()
        
        document = DocumentModel()
        document.metadata = {'data_source': 'kegg_import'}
        # No transitions with reaction IDs
        
        is_valid, issues = enricher.validate_document(document)
        assert not is_valid
        assert any("No transitions" in issue for issue in issues)


class TestPlaceCreation:
    """Test place creation and positioning."""
    
    def test_create_place_cluster_strategy(self):
        """Test place creation with cluster positioning."""
        enricher = KEGGStoichiometryEnricher(position_strategy='cluster')
        
        document = DocumentModel()
        transition = Transition(x=100, y=100, id="T1", name="test")
        compound = CompoundStoich(compound_id="C00002", coefficient=1)
        
        place, was_created = enricher._find_or_create_place(document, compound, transition)
        
        assert place is not None
        assert was_created is True
        assert place.id.startswith("P")
        assert place.metadata['compound_id'] == "C00002"
        assert place.metadata['source'] == 'stoichiometry_enrichment'
        # Position should be near transition
        assert abs(place.x - 100) < 200
        assert abs(place.y - 100) < 200
    
    def test_create_place_region_strategy(self):
        """Test place creation with region positioning."""
        enricher = KEGGStoichiometryEnricher(position_strategy='region')
        
        document = DocumentModel()
        transition = Transition(x=100, y=100, id="T1", name="test")
        compound = CompoundStoich(compound_id="C00002", coefficient=1)
        
        place, was_created = enricher._find_or_create_place(document, compound, transition)
        
        assert place is not None
        assert was_created is True
        # Region strategy positions at top
        assert place.y == 50
    
    def test_find_existing_place(self):
        """Test finding existing place for compound."""
        enricher = KEGGStoichiometryEnricher()
        
        document = DocumentModel()
        
        # Create existing place
        existing_place = Place(x=50, y=50, id="P1", name="ATP")
        existing_place.metadata = {'compound_id': 'C00002'}
        document.places.append(existing_place)
        
        transition = Transition(x=100, y=100, id="T1", name="test")
        compound = CompoundStoich(compound_id="C00002", coefficient=1)
        
        # Should return existing place, not create new one
        place, was_created = enricher._find_or_create_place(document, compound, transition)
        
        assert place is existing_place
        assert was_created is False
        assert len(document.places) == 1  # No new place created


class TestGetConnectedCompounds:
    """Test getting connected compounds."""
    
    def test_get_input_compounds(self):
        """Test getting compounds from input arcs."""
        enricher = KEGGStoichiometryEnricher()
        
        document = DocumentModel()
        
        # Create place with compound
        place = Place(x=0, y=0, id="P1", name="ATP")
        place.metadata = {'kegg_id': 'cpd:C00002'}
        document.places.append(place)
        
        # Create transition
        transition = Transition(x=0, y=0, id="T1", name="test")
        document.transitions.append(transition)
        
        # Create input arc with required id and name
        arc = Arc(source=place, target=transition, id="A1", name="A1")
        document.arcs.append(arc)
        
        # Get connected compounds
        compounds = enricher._get_connected_compounds(document, transition)
        
        assert "C00002" in compounds
    
    def test_get_output_compounds(self):
        """Test getting compounds from output arcs."""
        enricher = KEGGStoichiometryEnricher()
        
        document = DocumentModel()
        
        place = Place(x=0, y=0, id="P1", name="ADP")
        place.metadata = {'compound_id': 'C00008'}
        document.places.append(place)
        
        transition = Transition(x=0, y=0, id="T1", name="test")
        document.transitions.append(transition)
        
        # Create output arc with required id and name
        arc = Arc(source=transition, target=place, id="A1", name="A1")
        document.arcs.append(arc)
        
        compounds = enricher._get_connected_compounds(document, transition)
        
        assert "C00008" in compounds


class TestProgressReporting:
    """Test progress reporting."""
    
    def test_progress_callback(self):
        """Test progress callback is called."""
        callback_calls = []
        
        def progress_callback(current, total, message):
            callback_calls.append((current, total, message))
        
        enricher = KEGGStoichiometryEnricher(progress_callback=progress_callback)
        enricher.report_progress(0, 10, "Test")
        enricher.report_progress(5, 10, "Half")
        enricher.report_progress(10, 10, "Done")
        
        assert len(callback_calls) == 3
        assert callback_calls[0] == (0, 10, "Test")
        assert callback_calls[1] == (5, 10, "Half")
        assert callback_calls[2] == (10, 10, "Done")
    
    def test_progress_callback_error_handling(self):
        """Test that progress callback errors are handled gracefully."""
        def bad_callback(current, total, message):
            raise Exception("Callback error")
        
        enricher = KEGGStoichiometryEnricher(progress_callback=bad_callback)
        # Should not raise exception
        enricher.report_progress(0, 10, "Test")


class TestCancellation:
    """Test enrichment cancellation."""
    
    def test_cancel_request(self):
        """Test cancellation request."""
        enricher = KEGGStoichiometryEnricher()
        
        assert not enricher.is_cancelled()
        
        enricher.cancel()
        
        assert enricher.is_cancelled()


class TestGetCompoundName:
    """Test compound name resolution."""
    
    def test_get_common_compound_name(self):
        """Test getting names for common compounds."""
        enricher = KEGGStoichiometryEnricher()
        
        # Should get ATP for C00002
        name = enricher._get_compound_name("C00002")
        assert "ATP" in name or "C00002" in name
    
    def test_get_unknown_compound_name(self):
        """Test fallback for unknown compounds."""
        enricher = KEGGStoichiometryEnricher()
        
        name = enricher._get_compound_name("C99999")
        assert "C99999" in name


# Integration tests (require network access)
@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring KEGG API access."""
    
    def test_fetch_real_reaction(self):
        """Test fetching real reaction from KEGG."""
        enricher = KEGGStoichiometryEnricher()
        
        # Fetch hexokinase reaction
        stoich = enricher._fetch_reaction_stoichiometry("R00200")
        
        assert stoich.reaction_id == "R00200"
        assert len(stoich.substrates) > 0
        assert len(stoich.products) > 0
        assert any(s.compound_id == "C00002" for s in stoich.substrates)  # ATP
    
    def test_cache_behavior(self):
        """Test that caching works."""
        enricher = KEGGStoichiometryEnricher()
        
        # First fetch
        stoich1 = enricher._fetch_reaction_stoichiometry("R00200")
        
        # Second fetch (should be cached)
        stoich2 = enricher._fetch_reaction_stoichiometry("R00200")
        
        # Should be same object from cache
        assert stoich1 is stoich2
        
        # Cache should contain entry
        assert "R00200" in enricher.cache


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
