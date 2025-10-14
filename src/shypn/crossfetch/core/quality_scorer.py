"""
Quality Scorer

Evaluates and scores the quality of fetched data from multiple sources.

Author: Shypn Development Team
Date: October 2025
"""

from typing import List, Dict, Any
import logging

from ..models import FetchResult, QualityMetrics


class QualityScorer:
    """Scores and evaluates quality of fetched data.
    
    Implements the quality scoring formula:
    Score = 0.25 × Completeness + 0.30 × Source Reliability +
            0.20 × Consistency + 0.25 × Validation Status
    """
    
    # Scoring weights
    WEIGHT_COMPLETENESS = 0.25
    WEIGHT_RELIABILITY = 0.30
    WEIGHT_CONSISTENCY = 0.20
    WEIGHT_VALIDATION = 0.25
    
    def __init__(self):
        """Initialize quality scorer."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def score_result(self, result: FetchResult) -> float:
        """Calculate quality score for a fetch result.
        
        Args:
            result: FetchResult to score
            
        Returns:
            Quality score (0.0-1.0)
        """
        return result.quality_metrics.overall_score()
    
    def score_results(self, results: List[FetchResult]) -> List[float]:
        """Calculate quality scores for multiple results.
        
        Args:
            results: List of FetchResults
            
        Returns:
            List of quality scores
        """
        return [self.score_result(r) for r in results]
    
    def rank_results(self, results: List[FetchResult]) -> List[FetchResult]:
        """Rank results by quality score (highest first).
        
        Args:
            results: List of FetchResults
            
        Returns:
            Sorted list of FetchResults
        """
        return sorted(results, key=lambda r: self.score_result(r), reverse=True)
    
    def filter_by_min_quality(self,
                             results: List[FetchResult],
                             min_score: float = 0.5) -> List[FetchResult]:
        """Filter results by minimum quality score.
        
        Args:
            results: List of FetchResults
            min_score: Minimum acceptable quality score
            
        Returns:
            Filtered list of FetchResults
        """
        return [r for r in results if self.score_result(r) >= min_score]
    
    def get_best_result(self,
                       results: List[FetchResult],
                       min_score: float = 0.0) -> FetchResult | None:
        """Get the best quality result.
        
        Args:
            results: List of FetchResults
            min_score: Minimum acceptable quality score
            
        Returns:
            Best FetchResult or None if none meet criteria
        """
        usable_results = [r for r in results if r.is_usable()]
        if not usable_results:
            return None
        
        filtered = self.filter_by_min_quality(usable_results, min_score)
        if not filtered:
            return None
        
        ranked = self.rank_results(filtered)
        return ranked[0] if ranked else None
    
    def calculate_completeness(self,
                              requested_fields: List[str],
                              filled_fields: List[str]) -> float:
        """Calculate completeness score.
        
        Args:
            requested_fields: Fields that were requested
            filled_fields: Fields that were filled
            
        Returns:
            Completeness score (0.0-1.0)
        """
        if not requested_fields:
            return 1.0
        
        filled_set = set(filled_fields)
        requested_set = set(requested_fields)
        
        filled_count = len(filled_set & requested_set)
        return filled_count / len(requested_set)
    
    def calculate_consistency(self,
                            results: List[FetchResult],
                            field_name: str) -> float:
        """Calculate consistency across multiple results for a field.
        
        Args:
            results: List of FetchResults
            field_name: Field to check consistency for
            
        Returns:
            Consistency score (0.0-1.0)
        """
        if len(results) < 2:
            return 1.0
        
        values = []
        for result in results:
            if field_name in result.data:
                values.append(result.data[field_name])
        
        if not values:
            return 0.0
        
        # Check if all values are the same
        unique_values = set(str(v) for v in values)
        if len(unique_values) == 1:
            return 1.0
        
        # Calculate agreement ratio
        most_common_count = max(
            values.count(v) for v in values
        )
        return most_common_count / len(values)
    
    def evaluate_results(self,
                        results: List[FetchResult]) -> Dict[str, Any]:
        """Comprehensive evaluation of results.
        
        Args:
            results: List of FetchResults to evaluate
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not results:
            return {
                "total_results": 0,
                "usable_results": 0,
                "average_quality": 0.0,
                "best_quality": 0.0,
                "worst_quality": 0.0
            }
        
        scores = self.score_results(results)
        usable = [r for r in results if r.is_usable()]
        
        return {
            "total_results": len(results),
            "usable_results": len(usable),
            "average_quality": sum(scores) / len(scores) if scores else 0.0,
            "best_quality": max(scores) if scores else 0.0,
            "worst_quality": min(scores) if scores else 0.0,
            "sources": list(set(r.attribution.source_name for r in results))
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"QualityScorer("
            f"weights=[{self.WEIGHT_COMPLETENESS}, {self.WEIGHT_RELIABILITY}, "
            f"{self.WEIGHT_CONSISTENCY}, {self.WEIGHT_VALIDATION}])"
        )
