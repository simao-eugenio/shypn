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
    
    # ======= Shared helpers (used by network/behavioral/structural subclasses) =======

    def _build_graph(self):
        """Build directed graph from Petri net."""
        import networkx as nx
        graph = nx.DiGraph()
        for place in self.model.places:
            graph.add_node(str(place.id), type='place', obj=place,
                           name=getattr(place, 'name', f'P{place.id}'))
        for transition in self.model.transitions:
            graph.add_node(str(transition.id), type='transition', obj=transition,
                           name=getattr(transition, 'name', f'T{transition.id}'))
        for arc in self.model.arcs:
            # Prefer arc.source.id (real Arc and most mocks); fall back to arc.source_id
            if hasattr(arc, 'source') and hasattr(arc.source, 'id'):
                src, tgt = str(arc.source.id), str(arc.target.id)
            else:
                src, tgt = str(arc.source_id), str(arc.target_id)
            graph.add_edge(src, tgt, obj=arc, weight=getattr(arc, 'weight', 1))
        return graph

    def _filter_nodes_by_type(self, graph, node_type: str) -> list:
        """Filter graph nodes by type (place or transition)."""
        if node_type == 'place':
            return [n for n in graph.nodes() if n.startswith('p_')]
        elif node_type == 'transition':
            return [n for n in graph.nodes() if n.startswith('t_')]
        return list(graph.nodes())

    def _get_node_name(self, node_id: str) -> str:
        """Get human-readable name for a node."""
        for place in self.model.places:
            if str(place.id) == node_id:
                return getattr(place, 'name', node_id)
        for transition in self.model.transitions:
            if str(transition.id) == node_id:
                return getattr(transition, 'name', node_id)
        return node_id

    def _get_initial_marking(self) -> dict:
        """Get initial marking from the model."""
        marking = {}
        if hasattr(self.model.places, 'items'):
            for place_id, place in self.model.places.items():
                marking[place_id] = place.tokens
        else:
            for place in self.model.places:
                marking[place.id] = place.tokens
        return marking

    def _get_enabled_transitions(self, marking: dict) -> list:
        """Get list of enabled transitions for a marking."""
        enabled = []
        transitions = (self.model.transitions.keys() if
                       hasattr(self.model.transitions, 'keys')
                       else [t.id for t in self.model.transitions])
        arcs = (self.model.arcs.values() if hasattr(self.model.arcs, 'values')
                else self.model.arcs)
        for trans_id in transitions:
            can_fire = True
            for arc in arcs:
                arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
                arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
                if arc_target == trans_id:
                    if marking.get(arc_source, 0) < arc.weight:
                        can_fire = False
                        break
            if can_fire:
                enabled.append(trans_id)
        return enabled

    def _fire_transition(self, marking: dict, trans_id: str) -> dict:
        """Fire a transition and return the new marking."""
        new_marking = marking.copy()
        arcs = (self.model.arcs.values() if hasattr(self.model.arcs, 'values')
                else self.model.arcs)
        for arc in arcs:
            arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
            arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
            if arc_target == trans_id:
                new_marking[arc_source] = max(0, new_marking.get(arc_source, 0) - arc.weight)
        for arc in arcs:
            arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
            arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
            if arc_source == trans_id:
                new_marking[arc_target] = new_marking.get(arc_target, 0) + arc.weight
        return new_marking

    def _set_numpy_threads(self, num_threads: int) -> dict:
        """Configure NumPy/BLAS threading. Returns old settings dict."""
        import os
        old_settings = {}
        env_vars = ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                    'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']
        for var in env_vars:
            old_settings[var] = os.environ.get(var)
            os.environ[var] = str(num_threads)
        try:
            from threadpoolctl import threadpool_limits
            old_settings['threadpool_limits'] = threadpool_limits(limits=num_threads)
        except ImportError:
            old_settings['threadpool_limits'] = None
        return old_settings

    def _restore_numpy_threads(self, old_settings: dict):
        """Restore NumPy/BLAS threading settings."""
        import os
        env_vars = ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                    'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']
        for var in env_vars:
            old_val = old_settings.get(var)
            if old_val is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old_val
        if old_settings.get('threadpool_limits') is not None:
            old_settings['threadpool_limits'].__exit__(None, None, None)

    def _build_place_connectivity(self) -> tuple:
        """Build preset/postset maps for places.

        Returns:
            (place_presets, place_postsets) where:
            - place_presets[place_id]  = set of transition IDs that input to place
            - place_postsets[place_id] = set of transition IDs that output from place
        """
        place_presets = {str(p.id): set() for p in self.model.places}
        place_postsets = {str(p.id): set() for p in self.model.places}
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            if target_id in place_presets:
                place_presets[target_id].add(source_id)
            if source_id in place_postsets:
                place_postsets[source_id].add(target_id)
        return place_presets, place_postsets

    # ==================================================================================

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.model})"
