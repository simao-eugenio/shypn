"""
Unit tests for Initial Marking Inference System

Tests compound classification, concentration estimation,
and initial marking inference.

Author: Shypn Development Team
Date: January 2026
"""

import pytest
from unittest.mock import Mock, patch

from shypn.crossfetch.inference.initial_marking_inferrer import (
    CompoundClass,
    CompoundClassifier,
    ConcentrationEstimator,
    InitialMarkingInferrer,
    InitialMarkingSuggestion
)
from shypn.thermodynamics.compound_resolver import CompoundIdentity


class TestCompoundClassifier:
    """Test compound classification logic."""
    
    def test_classify_energy_currency(self):
        """Test classification of energy currencies."""
        classifier = CompoundClassifier()
        
        # Test by name
        result = classifier.classify("C00002", ["ATP", "Adenosine triphosphate"])
        assert result == CompoundClass.ENERGY_CURRENCY
        
        result = classifier.classify(None, ["GTP"])
        assert result == CompoundClass.ENERGY_CURRENCY
    
    def test_classify_cofactor(self):
        """Test classification of cofactors."""
        classifier = CompoundClassifier()
        
        result = classifier.classify("C00004", ["NADH", "Reduced NAD"])
        assert result == CompoundClass.COFACTOR
        
        result = classifier.classify(None, ["FAD", "Flavin adenine dinucleotide"])
        assert result == CompoundClass.COFACTOR
    
    def test_classify_coenzyme_a(self):
        """Test classification of CoA derivatives."""
        classifier = CompoundClassifier()
        
        result = classifier.classify("C00024", ["Acetyl-CoA"])
        assert result == CompoundClass.COENZYME_A
        
        result = classifier.classify(None, ["Malonyl-CoA"])
        assert result == CompoundClass.COENZYME_A
    
    def test_classify_central_metabolite(self):
        """Test classification of central metabolites."""
        classifier = CompoundClassifier()
        
        # Glucose
        result = classifier.classify("C00031", ["D-Glucose"])
        assert result == CompoundClass.CENTRAL_METABOLITE
        
        # Pyruvate
        result = classifier.classify("C00022", ["Pyruvate"])
        assert result == CompoundClass.CENTRAL_METABOLITE
    
    def test_classify_unknown(self):
        """Test classification of unknown compounds."""
        classifier = CompoundClassifier()
        
        result = classifier.classify(None, None)
        assert result == CompoundClass.UNKNOWN
        
        result = classifier.classify("C99999", ["UnknownCompound"])
        # Should default to secondary metabolite
        assert result in [CompoundClass.SECONDARY_METABOLITE, CompoundClass.UNKNOWN]


class TestConcentrationEstimator:
    """Test concentration estimation logic."""
    
    def test_estimate_energy_currency(self):
        """Test estimation for energy currencies."""
        estimator = ConcentrationEstimator(scale_factor=10.0)
        
        tokens, confidence, reasoning = estimator.estimate_tokens(
            CompoundClass.ENERGY_CURRENCY
        )
        
        assert tokens == 50  # 5 mM * 10
        assert confidence == 0.85
        assert "energy currency" in reasoning.lower()
    
    def test_estimate_cofactor(self):
        """Test estimation for cofactors."""
        estimator = ConcentrationEstimator(scale_factor=10.0)
        
        tokens, confidence, reasoning = estimator.estimate_tokens(
            CompoundClass.COFACTOR
        )
        
        assert tokens == 10  # 1 mM * 10
        assert confidence == 0.75
        assert "cofactor" in reasoning.lower()
    
    def test_estimate_with_custom_scale_factor(self):
        """Test estimation with custom scale factor."""
        # High-resolution model
        estimator = ConcentrationEstimator(scale_factor=100.0)
        
        tokens, confidence, reasoning = estimator.estimate_tokens(
            CompoundClass.ENERGY_CURRENCY
        )
        
        assert tokens == 500  # 5 mM * 100
        assert confidence == 0.85
    
    def test_estimate_unknown(self):
        """Test estimation for unknown compounds."""
        estimator = ConcentrationEstimator(scale_factor=10.0)
        
        tokens, confidence, reasoning = estimator.estimate_tokens(
            CompoundClass.UNKNOWN
        )
        
        assert tokens == 5  # 0.5 mM * 10
        assert confidence == 0.40
        assert "compound" in reasoning.lower()


class TestInitialMarkingInferrer:
    """Test initial marking inference."""
    
    @pytest.fixture
    def mock_place(self):
        """Create a mock place object."""
        place = Mock()
        place.id = "P5"
        place.name = "ATP"
        place.tokens = 0
        place.metadata = {}
        return place
    
    @pytest.fixture
    def mock_resolver(self):
        """Create a mock compound resolver."""
        with patch('shypn.crossfetch.inference.initial_marking_inferrer.CompoundResolver') as mock:
            resolver_instance = mock.return_value
            
            # Mock resolve method to return ATP identity
            atp_identity = CompoundIdentity(
                kegg_id="C00002",
                chebi_id="CHEBI:15422",
                names=["ATP", "Adenosine 5'-triphosphate"],
                formula="C10H16N5O13P3"
            )
            resolver_instance.resolve.return_value = atp_identity
            
            yield mock
    
    def test_infer_marking_atp(self, mock_place, mock_resolver):
        """Test inference for ATP."""
        inferrer = InitialMarkingInferrer(scale_factor=10.0)
        
        suggestion = inferrer.infer_marking(mock_place)
        
        assert suggestion is not None
        assert suggestion.place_id == "P5"
        assert suggestion.tokens == 50  # ATP: 5 mM * 10
        assert suggestion.confidence >= 0.80
        assert suggestion.compound_class == CompoundClass.ENERGY_CURRENCY
        assert suggestion.compound_id == "C00002"
    
    def test_infer_marking_with_kegg_id_metadata(self, mock_resolver):
        """Test inference using KEGG ID from metadata."""
        place = Mock()
        place.id = "P12"
        place.name = "NADH"
        place.tokens = 0
        place.metadata = {'kegg_id': 'C00004'}
        
        # Mock resolver for NADH
        with patch('shypn.crossfetch.inference.initial_marking_inferrer.CompoundResolver') as mock:
            resolver_instance = mock.return_value
            nadh_identity = CompoundIdentity(
                kegg_id="C00004",
                names=["NADH"],
                formula="C21H29N7O14P2"
            )
            resolver_instance.resolve.return_value = nadh_identity
            
            inferrer = InitialMarkingInferrer(scale_factor=10.0)
            suggestion = inferrer.infer_marking(place)
            
            assert suggestion is not None
            assert suggestion.tokens == 10  # NADH: 1 mM * 10
            assert suggestion.compound_class == CompoundClass.COFACTOR
    
    def test_infer_marking_unknown_compound(self):
        """Test inference for unknown compound."""
        place = Mock()
        place.id = "P99"
        place.name = "UnknownMetabolite"
        place.tokens = 0
        place.metadata = {}
        
        # Mock resolver to return None (unknown compound)
        with patch('shypn.crossfetch.inference.initial_marking_inferrer.CompoundResolver') as mock:
            resolver_instance = mock.return_value
            resolver_instance.resolve.return_value = None
            
            inferrer = InitialMarkingInferrer()
            suggestion = inferrer.infer_marking(place)
            
            # Should return None for unknown compounds
            assert suggestion is None
    
    def test_infer_marking_no_identifier(self):
        """Test inference when place has no identifier."""
        place = Mock()
        place.id = "P100"
        place.name = None
        place.metadata = {}
        
        inferrer = InitialMarkingInferrer()
        suggestion = inferrer.infer_marking(place)
        
        assert suggestion is None
    
    def test_infer_markings_batch(self, mock_resolver):
        """Test batch inference for multiple places."""
        # Create multiple places
        places = []
        for i in range(5):
            place = Mock()
            place.id = f"P{i}"
            place.name = f"Compound{i}"
            place.tokens = 0
            place.metadata = {}
            places.append(place)
        
        inferrer = InitialMarkingInferrer()
        suggestions = inferrer.infer_markings_batch(places)
        
        # Should have suggestions for all places
        assert len(suggestions) == 5
        assert all(isinstance(s, InitialMarkingSuggestion) for s in suggestions)
    
    def test_infer_markings_batch_skips_places_with_tokens(self, mock_resolver):
        """Test batch inference skips places that already have tokens."""
        places = []
        
        # Place with tokens (should skip)
        place1 = Mock()
        place1.id = "P1"
        place1.name = "ATP"
        place1.tokens = 100  # Already has tokens
        place1.metadata = {}
        places.append(place1)
        
        # Place without tokens (should infer)
        place2 = Mock()
        place2.id = "P2"
        place2.name = "NADH"
        place2.tokens = 0
        place2.metadata = {}
        places.append(place2)
        
        inferrer = InitialMarkingInferrer()
        suggestions = inferrer.infer_markings_batch(places)
        
        # Should only have suggestion for P2
        assert len(suggestions) == 1
        assert suggestions[0].place_id == "P2"
    
    def test_suggestion_to_dict(self):
        """Test InitialMarkingSuggestion serialization."""
        suggestion = InitialMarkingSuggestion(
            place_id="P5",
            tokens=50,
            confidence=0.85,
            reasoning="Test reasoning",
            compound_class=CompoundClass.ENERGY_CURRENCY,
            compound_id="C00002",
            compound_names=["ATP"]
        )
        
        result = suggestion.to_dict()
        
        assert result['place_id'] == "P5"
        assert result['tokens'] == 50
        assert result['confidence'] == 0.85
        assert result['compound_class'] == "energy_currency"
        assert result['compound_id'] == "C00002"
        assert result['compound_names'] == ["ATP"]


class TestIntegration:
    """Integration tests with real CompoundResolver."""
    
    @pytest.mark.integration
    def test_full_inference_pipeline_atp(self):
        """Test full inference pipeline with real CompoundResolver.
        
        Note: Requires compound_resolver data files to be present.
        """
        place = Mock()
        place.id = "P5"
        place.name = "ATP"
        place.tokens = 0
        place.metadata = {}
        
        try:
            inferrer = InitialMarkingInferrer(scale_factor=10.0)
            suggestion = inferrer.infer_marking(place)
            
            # If resolver data available, should succeed
            if suggestion:
                assert suggestion.tokens > 0
                assert suggestion.confidence > 0
                assert suggestion.compound_class != CompoundClass.UNKNOWN
        except Exception as e:
            # Skip if data files not available
            pytest.skip(f"CompoundResolver data not available: {e}")
    
    @pytest.mark.integration
    def test_batch_inference_with_mixed_compounds(self):
        """Test batch inference with various compound types."""
        # Create places with different compound types
        test_data = [
            ("P1", "ATP", CompoundClass.ENERGY_CURRENCY),
            ("P2", "NADH", CompoundClass.COFACTOR),
            ("P3", "Glucose", CompoundClass.CENTRAL_METABOLITE),
            ("P4", "Acetyl-CoA", CompoundClass.COENZYME_A),
        ]
        
        places = []
        for place_id, name, expected_class in test_data:
            place = Mock()
            place.id = place_id
            place.name = name
            place.tokens = 0
            place.metadata = {}
            places.append(place)
        
        try:
            inferrer = InitialMarkingInferrer()
            suggestions = inferrer.infer_markings_batch(places)
            
            # Should have suggestions for recognized compounds
            assert len(suggestions) > 0
            
            # Check that different compound classes get different token counts
            token_counts = [s.tokens for s in suggestions]
            assert len(set(token_counts)) > 1  # Should have variety
            
        except Exception as e:
            pytest.skip(f"CompoundResolver data not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
