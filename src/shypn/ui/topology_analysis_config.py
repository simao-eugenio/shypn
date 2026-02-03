"""Configuration manager for topology analysis settings.

Provides centralized configuration for analysis options, particularly
parallel execution settings. Follows OOP principles with minimal overhead.
"""

from typing import Any, Dict, Optional


class TopologyAnalysisConfig:
    """Configuration for topology analysis execution.
    
    Centralized settings management for analysis options including
    parallel execution modes, worker counts, and performance tuning.
    
    Example:
        >>> config = TopologyAnalysisConfig.get_instance()
        >>> config.set_parallel_mode('reachability', 'maximal')
        >>> config.set_num_workers('reachability', 8)
    """
    
    _instance = None
    
    def __init__(self):
        """Initialize configuration with defaults."""
        if TopologyAnalysisConfig._instance is not None:
            raise RuntimeError("Use TopologyAnalysisConfig.get_instance()")
        
        # Per-analyzer settings
        self._analyzer_configs: Dict[str, Dict[str, Any]] = {
            # Reachability defaults to maximal parallel mode
            'reachability': {
                'parallel_mode': 'maximal',
                'num_workers': None  # Auto-detect
            },
            # Hubs can use simple parallel mode
            'hubs': {
                'parallel_mode': False,
                'num_workers': None
            },
            # Invariants use NumPy threading
            'p_invariants': {
                'parallel_mode': False,  # NumPy threading is transparent
                'num_threads': None  # Auto-detect
            },
            't_invariants': {
                'parallel_mode': False,
                'num_threads': None
            },
            # Siphons can use partition-based parallel
            'siphons': {
                'parallel_mode': False,
                'num_workers': None
            }
        }
        
        # Default settings for other analyzers
        self._defaults = {
            'parallel_mode': False,      # False, True/'basic', 'maximal'
            'num_workers': None,         # None = auto-detect
            'max_states': 10000,
            'max_depth': 100,
            'compute_graph': True,
            'find_deadlocks': True
        }
    
    @classmethod
    def get_instance(cls) -> 'TopologyAnalysisConfig':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)."""
        cls._instance = None
    
    def get_config(self, analyzer_name: str) -> Dict[str, Any]:
        """Get configuration for specific analyzer.
        
        Args:
            analyzer_name: Name of analyzer (e.g., 'reachability')
            
        Returns:
            Dict with configuration settings
        """
        if analyzer_name not in self._analyzer_configs:
            # Return defaults
            return self._defaults.copy()
        
        # Merge with defaults
        config = self._defaults.copy()
        config.update(self._analyzer_configs[analyzer_name])
        return config
    
    def set_parallel_mode(self, analyzer_name: str, mode: Any):
        """Set parallel execution mode.
        
        Args:
            analyzer_name: Name of analyzer
            mode: False (sequential), True/'basic' (Phase 1), 'maximal' (Phase 2)
        """
        if analyzer_name not in self._analyzer_configs:
            self._analyzer_configs[analyzer_name] = {}
        self._analyzer_configs[analyzer_name]['parallel_mode'] = mode
    
    def set_num_workers(self, analyzer_name: str, num_workers: Optional[int]):
        """Set number of worker processes.
        
        Args:
            analyzer_name: Name of analyzer
            num_workers: Number of workers (None = auto-detect)
        """
        if analyzer_name not in self._analyzer_configs:
            self._analyzer_configs[analyzer_name] = {}
        self._analyzer_configs[analyzer_name]['num_workers'] = num_workers
    
    def set_max_states(self, analyzer_name: str, max_states: int):
        """Set maximum states to explore.
        
        Args:
            analyzer_name: Name of analyzer
            max_states: Maximum states limit
        """
        if analyzer_name not in self._analyzer_configs:
            self._analyzer_configs[analyzer_name] = {}
        self._analyzer_configs[analyzer_name]['max_states'] = max_states
    
    def get_parallel_mode(self, analyzer_name: str) -> Any:
        """Get parallel mode for analyzer."""
        return self.get_config(analyzer_name)['parallel_mode']
    
    def get_num_workers(self, analyzer_name: str) -> Optional[int]:
        """Get number of workers for analyzer."""
        return self.get_config(analyzer_name)['num_workers']
    
    def is_parallel_enabled(self, analyzer_name: str) -> bool:
        """Check if parallel mode is enabled."""
        mode = self.get_parallel_mode(analyzer_name)
        return mode in (True, 'basic', 'maximal')
    
    def reset_to_defaults(self, analyzer_name: Optional[str] = None):
        """Reset configuration to defaults.
        
        Args:
            analyzer_name: Specific analyzer to reset (None = reset all)
        """
        if analyzer_name is None:
            self._analyzer_configs.clear()
        elif analyzer_name in self._analyzer_configs:
            del self._analyzer_configs[analyzer_name]


class AnalyzerFactory:
    """Factory for creating topology analyzers with configuration.
    
    Minimal factory that instantiates the appropriate analyzer based on
    configuration. Keeps loader code thin by centralizing logic here.
    
    Example:
        >>> factory = AnalyzerFactory(config)
        >>> analyzer = factory.create_analyzer('reachability', model)
    """
    
    def __init__(self, config: Optional[TopologyAnalysisConfig] = None):
        """Initialize factory.
        
        Args:
            config: Configuration instance (uses singleton if None)
        """
        self.config = config or TopologyAnalysisConfig.get_instance()
    
    def create_analyzer(self, analyzer_name: str, model: Any) -> Any:
        """Create analyzer instance with appropriate configuration.
        
        Args:
            analyzer_name: Name of analyzer
            model: Model instance
            
        Returns:
            Configured analyzer instance
        """
        # Import here to avoid circular dependencies
        from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
        # ParallelReachabilityAnalyzer is internal to reachability module
        from shypn.topology.behavioral.boundedness import BoundednessAnalyzer
        from shypn.topology.behavioral.liveness import LivenessAnalyzer
        from shypn.topology.behavioral.deadlocks import DeadlockAnalyzer
        from shypn.topology.behavioral.fairness import FairnessAnalyzer
        from shypn.topology.structural.siphons import SiphonAnalyzer
        from shypn.topology.structural.traps import TrapAnalyzer
        from shypn.topology.structural.p_invariants import PInvariantAnalyzer
        from shypn.topology.structural.t_invariants import TInvariantAnalyzer
        from shypn.topology.graph.cycles import CycleAnalyzer
        from shypn.topology.graph.paths import PathAnalyzer
        # HubAnalyzer: Network hub analysis (if exists)
        
        # Get configuration for this analyzer
        config = self.config.get_config(analyzer_name)
        
        # All analyzers use same instantiation pattern
        # Parallel mode is controlled via analyze() kwargs, not constructor
        if analyzer_name == 'reachability':
            return ReachabilityAnalyzer(model)
        
        # Standard analyzers (map name to class)
        analyzer_classes = {
            'boundedness': BoundednessAnalyzer,
            'liveness': LivenessAnalyzer,
            'deadlocks': DeadlockAnalyzer,
            'fairness': FairnessAnalyzer,
            'siphons': SiphonAnalyzer,
            'traps': TrapAnalyzer,
            'p_invariants': PInvariantAnalyzer,
            't_invariants': TInvariantAnalyzer,
            'cycles': CycleAnalyzer,
            'paths': PathAnalyzer,
            # 'hubs': HubAnalyzer,  # Commented out - module may not exist
        }
        
        analyzer_class = analyzer_classes.get(analyzer_name)
        if analyzer_class:
            return analyzer_class(model)
        
        raise ValueError(f"Unknown analyzer: {analyzer_name}")
    
    def get_analysis_kwargs(self, analyzer_name: str) -> Dict[str, Any]:
        """Get keyword arguments for analyze() call.
        
        Args:
            analyzer_name: Name of analyzer
            
        Returns:
            Dict of kwargs to pass to analyze()
        """
        config = self.config.get_config(analyzer_name)
        
        if analyzer_name == 'reachability':
            kwargs = {
                'max_states': config['max_states'],
                'max_depth': config['max_depth'],
                'compute_graph': config['compute_graph'],
                'find_deadlocks': config['find_deadlocks'],
                'parallel': config['parallel_mode']
            }
            # Add num_workers if parallel mode is enabled
            if config['parallel_mode'] in (True, 'basic', 'maximal'):
                kwargs['num_workers'] = config['num_workers']
            return kwargs
        
        # Boundedness also supports parallel (uses reachability internally)
        if analyzer_name in ['boundedness', 'liveness', 'deadlocks']:
            kwargs = {
                'parallel': config['parallel_mode']
            }
            # Add num_workers if parallel mode is enabled
            if config['parallel_mode'] in (True, 'basic', 'maximal'):
                kwargs['num_workers'] = config['num_workers']
            return kwargs
        
        # Hubs - simple parallel node processing
        if analyzer_name == 'hubs':
            kwargs = {}
            if config['parallel_mode']:
                kwargs['parallel'] = True
                kwargs['num_workers'] = config['num_workers']
            return kwargs
        
        # Invariants - NumPy threading
        if analyzer_name in ['p_invariants', 't_invariants']:
            kwargs = {}
            num_threads = config.get('num_threads')
            if num_threads is not None:
                kwargs['num_threads'] = num_threads
            return kwargs
        
        # Siphons - partition-based parallel
        if analyzer_name == 'siphons':
            kwargs = {}
            if config['parallel_mode']:
                kwargs['parallel'] = True
                kwargs['num_workers'] = config['num_workers']
            return kwargs
        
        # Other analyzers don't need special kwargs
        return {}
