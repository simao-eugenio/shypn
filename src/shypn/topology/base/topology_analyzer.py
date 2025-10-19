"""Abstract base class for topology analyzers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time

from .analysis_result import AnalysisResult
from .exceptions import InvalidModelError


class TopologyAnalyzer(ABC):
    """Abstract base class for all topology analyzers.
    
    This class defines the common interface for topology analysis tools.
    All concrete analyzers must inherit from this class and implement
    the analyze() method.
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        class MyCycleAnalyzer(TopologyAnalyzer):
            def analyze(self, **kwargs) -> AnalysisResult:
                # Implementation
                return AnalysisResult(success=True, data={'cycles': cycles})
        
        analyzer = MyCycleAnalyzer(model)
        result = analyzer.analyze()
    """
    
    def __init__(self, model: Any):
        """Initialize analyzer.
        
        Args:
            model: PetriNetModel instance to analyze
            
        Raises:
            InvalidModelError: If model is None or invalid
        """
        if model is None:
            raise InvalidModelError("Model cannot be None")
        
        self.model = model
        self._cache: Dict[str, Any] = {}
        self._dirty: bool = True
        self._last_analysis_time: Optional[float] = None
    
    @abstractmethod
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform topology analysis.
        
        This method must be implemented by all concrete analyzers.
        
        Args:
            **kwargs: Analysis-specific parameters
            
        Returns:
            AnalysisResult: Analysis results with data, summary, warnings, errors
            
        Raises:
            TopologyAnalysisError: If analysis fails
        """
        pass
    
    def clear_cache(self) -> None:
        """Clear cached analysis results.
        
        Call this method when the model changes to invalidate
        cached results.
        """
        self._cache.clear()
        self._dirty = True
    
    def invalidate(self) -> None:
        """Mark cache as dirty without clearing.
        
        This is a lighter-weight alternative to clear_cache()
        that just marks the cache as needing refresh.
        """
        self._dirty = True
    
    def is_cached(self, key: str) -> bool:
        """Check if a result is cached.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if cached and not dirty
        """
        return key in self._cache and not self._dirty
    
    def get_cached(self, key: str, default: Any = None) -> Any:
        """Get cached result.
        
        Args:
            key: Cache key
            default: Default value if not cached
            
        Returns:
            Cached value or default
        """
        if self.is_cached(key):
            return self._cache.get(key, default)
        return default
    
    def set_cached(self, key: str, value: Any) -> None:
        """Store result in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value
        self._dirty = False
    
    def _start_timer(self) -> float:
        """Start timing analysis.
        
        Returns:
            Start time in seconds
        """
        return time.time()
    
    def _end_timer(self, start_time: float) -> float:
        """End timing and record duration.
        
        Args:
            start_time: Start time from _start_timer()
            
        Returns:
            Duration in seconds
        """
        duration = time.time() - start_time
        self._last_analysis_time = duration
        return duration
    
    def get_last_analysis_time(self) -> Optional[float]:
        """Get duration of last analysis.
        
        Returns:
            Duration in seconds, or None if no analysis yet
        """
        return self._last_analysis_time
    
    def _validate_model(self) -> None:
        """Validate that model is ready for analysis.
        
        Override this method to add custom validation.
        
        Raises:
            InvalidModelError: If model is invalid
        """
        if not hasattr(self.model, 'places'):
            raise InvalidModelError("Model missing 'places' attribute")
        
        if not hasattr(self.model, 'transitions'):
            raise InvalidModelError("Model missing 'transitions' attribute")
        
        if not hasattr(self.model, 'arcs'):
            raise InvalidModelError("Model missing 'arcs' attribute")
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.model})"
