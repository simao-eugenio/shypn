"""
Unit tests for ReactomeFetcher

Tests cover:
- Basic fetcher functionality  
- Data extraction methods
- Quality metrics calculation
- Error handling
- Edge cases
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.crossfetch.fetchers.reactome_fetcher import ReactomeFetcher
from shypn.crossfetch.models import FetchResult, FetchStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fetcher():
    """Create a ReactomeFetcher instance."""
    return ReactomeFetcher()


# ============================================================================
# Basic Functionality Tests
# ============================================================================

class TestBasicFunctionality:
    """Test basic fetcher functionality."""
    
    def test_fetcher_initialization(self, fetcher):
        """Test that fetcher initializes correctly."""
        assert fetcher is not None
        assert fetcher.source_name == "Reactome"
        assert fetcher.reliability_score == 0.95
        assert fetcher.is_available()
    
    def test_supported_data_types(self, fetcher):
        """Test that fetcher reports correct supported data types."""
        supported = fetcher.supported_data_types
        assert "pathways" in supported
        assert "interactions" in supported
        assert "annotations" in supported
        assert "reactions" in supported
        assert "participants" in supported
    
    def test_fetch_pathways_success(self, fetcher):
        """Test successful pathway fetch."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        assert isinstance(result, FetchResult)
        assert result.source_name == "Reactome"
        assert result.success
        assert result.status == FetchStatus.SUCCESS
    
    def test_fetch_interactions_success(self, fetcher):
        """Test successful interactions fetch."""
        result = fetcher.fetch("R-HSA-109581", "interactions")
        assert result.success
        assert result.enrichment_data is not None
    
    def test_fetch_reactions_success(self, fetcher):
        """Test successful reactions fetch."""
        result = fetcher.fetch("R-HSA-70171", "reactions")
        assert result.success
        assert result.enrichment_data is not None
    
    def test_fetch_annotations_success(self, fetcher):
        """Test successful annotations fetch."""
        result = fetcher.fetch("R-HSA-109581", "annotations")
        assert result.success
        assert result.enrichment_data is not None
    
    def test_fetch_participants_success(self, fetcher):
        """Test successful participants fetch."""
        result = fetcher.fetch("R-HSA-70171", "participants")
        assert result.success
        assert result.enrichment_data is not None


# ============================================================================
# Quality Metrics Tests
# ============================================================================

class TestQualityMetrics:
    """Test quality metrics calculation."""
    
    def test_quality_metrics_present(self, fetcher):
        """Test that quality metrics are calculated."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        assert result.quality_metrics is not None
    
    def test_quality_metrics_values_valid(self, fetcher):
        """Test that quality metric values are valid."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        metrics = result.quality_metrics
        
        assert 0.0 <= metrics.completeness_score <= 1.0
        assert 0.0 <= metrics.reliability_score <= 1.0
        assert 0.0 <= metrics.consistency_score <= 1.0
        assert 0.0 <= metrics.validation_score <= 1.0
    
    def test_reliability_score_matches_fetcher(self, fetcher):
        """Test that reliability score matches fetcher's reliability."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        assert result.quality_metrics.reliability_score == fetcher.reliability_score


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling."""
    
    def test_unsupported_data_type(self, fetcher):
        """Test handling of unsupported data type."""
        result = fetcher.fetch("R-HSA-70171", "unsupported_type")
        assert not result.success
        assert result.status == FetchStatus.FAILED
        assert "unsupported" in result.error_message.lower()
    
    def test_invalid_pathway_id(self, fetcher):
        """Test handling of invalid pathway ID."""
        result = fetcher.fetch("", "pathways")
        assert not result.success
    
    def test_error_message_informative(self, fetcher):
        """Test that error messages are informative."""
        result = fetcher.fetch("invalid-id", "unknown_type")
        assert not result.success
        assert result.error_message is not None
        assert len(result.error_message) > 0


# ============================================================================
# Source Attribution Tests
# ============================================================================

class TestSourceAttribution:
    """Test source attribution information."""
    
    def test_source_attribution_present(self, fetcher):
        """Test that source attribution is included."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        assert result.source_attribution is not None
    
    def test_source_name_correct(self, fetcher):
        """Test that source name is correct."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        assert result.source_attribution.source_name == "Reactome"
    
    def test_reliability_score_correct(self, fetcher):
        """Test that reliability score in attribution is correct."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        assert result.source_attribution.reliability_score == 0.95


# ============================================================================
# Pathway ID Parsing Tests
# ============================================================================

class TestPathwayIdParsing:
    """Test pathway ID parsing and validation."""
    
    def test_parse_standard_id(self, fetcher):
        """Test parsing standard Reactome pathway ID."""
        pathway_id = "R-HSA-109581"
        parsed = fetcher.parse_pathway_id(pathway_id)
        assert parsed == "R-HSA-109581"
    
    def test_parse_id_with_version(self, fetcher):
        """Test parsing pathway ID with version number."""
        pathway_id = "R-HSA-109581.1"
        parsed = fetcher.parse_pathway_id(pathway_id)
        assert "R-HSA-109581" in parsed
    
    def test_parse_id_other_organism(self, fetcher):
        """Test parsing pathway ID for other organisms."""
        pathway_id = "R-MMU-109581"  # Mouse
        parsed = fetcher.parse_pathway_id(pathway_id)
        assert parsed == "R-MMU-109581"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test integration with other components."""
    
    def test_fetch_result_serializable(self, fetcher):
        """Test that fetch result can be serialized."""
        result = fetcher.fetch("R-HSA-70171", "pathways")
        
        # Convert to dict (simulating serialization)
        result_dict = {
            "success": result.success,
            "status": result.status.value,
            "enrichment_data": result.enrichment_data,
            "error_message": result.error_message,
            "source_name": result.source_name
        }
        
        assert result_dict["success"] == result.success
        assert result_dict["source_name"] == "Reactome"
    
    def test_quality_scorer_compatibility(self, fetcher):
        """Test compatibility with QualityScorer."""
        from shypn.crossfetch.core import QualityScorer
        
        result = fetcher.fetch("R-HSA-70171", "pathways")
        scorer = QualityScorer()
        
        # Should be able to score the result
        score = scorer.score_result(result)
        assert 0.0 <= score <= 1.0
    
    def test_enrichment_pipeline_compatibility(self, fetcher):
        """Test compatibility with EnrichmentPipeline."""
        from shypn.crossfetch.core import EnrichmentPipeline
        
        pipeline = EnrichmentPipeline()
        
        # Fetcher should be registered
        sources = pipeline.get_available_sources()
        assert "Reactome" in sources


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""
    
    def test_multiple_fetches_consistent(self, fetcher):
        """Test that multiple fetches produce consistent results."""
        result1 = fetcher.fetch("R-HSA-70171", "pathways")
        result2 = fetcher.fetch("R-HSA-70171", "pathways")
        
        # Results should be structurally similar
        assert result1.success == result2.success
        assert result1.status == result2.status
    
    def test_fetch_completes_quickly(self, fetcher):
        """Test that fetch completes in reasonable time."""
        import time
        
        start = time.time()
        result = fetcher.fetch("R-HSA-70171", "pathways")
        elapsed = time.time() - start
        
        # Should complete within 1 second (stubbed API calls)
        assert elapsed < 1.0
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
