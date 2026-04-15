"""
Test Suite for Phase 3: UI Integration

Tests configuration layer, factory pattern, and controller integration.

Author: shypn
Date: 2025-01-XX
"""

import pytest
from unittest.mock import Mock, MagicMock

from shypn.ui.topology_analysis_config import TopologyAnalysisConfig, AnalyzerFactory
from shypn.topology.behavioral.reachability import ReachabilityAnalyzer


class TestTopologyAnalysisConfig:
    """Test TopologyAnalysisConfig singleton."""
    
    def test_singleton_pattern(self):
        """Verify singleton returns same instance."""
        config1 = TopologyAnalysisConfig.get_instance()
        config2 = TopologyAnalysisConfig.get_instance()
        assert config1 is config2
    
    def test_default_parallel_modes(self):
        """Verify default parallel mode configuration."""
        config = TopologyAnalysisConfig.get_instance()
        
        # Reachability defaults to maximal
        assert config.get_parallel_mode('reachability') == 'maximal'
        
        # Other analyzers default to sequential
        assert config.get_parallel_mode('boundedness') == False
        assert config.get_parallel_mode('liveness') == False
    
    def test_set_parallel_mode(self):
        """Test setting parallel mode for analyzer."""
        config = TopologyAnalysisConfig.get_instance()
        
        config.set_parallel_mode('reachability', 'basic')
        assert config.get_parallel_mode('reachability') == 'basic'
        
        config.set_parallel_mode('reachability', False)
        assert config.get_parallel_mode('reachability') == False
    
    def test_default_num_workers(self):
        """Verify default worker count is None (auto)."""
        config = TopologyAnalysisConfig.get_instance()
        assert config.get_num_workers('reachability') is None
    
    def test_set_num_workers(self):
        """Test setting worker count."""
        config = TopologyAnalysisConfig.get_instance()
        
        config.set_num_workers('reachability', 8)
        assert config.get_num_workers('reachability') == 8
        
        config.set_num_workers('reachability', None)
        assert config.get_num_workers('reachability') is None


class TestAnalyzerFactory:
    """Test AnalyzerFactory class."""
    
    def test_create_reachability_analyzer(self):
        """Test factory creates ReachabilityAnalyzer."""
        config = TopologyAnalysisConfig.get_instance()
        factory = AnalyzerFactory(config)
        
        mock_model = Mock()
        analyzer = factory.create_analyzer('reachability', mock_model)
        
        assert isinstance(analyzer, ReachabilityAnalyzer)
        assert analyzer.model is mock_model
    
    def test_get_analysis_kwargs_reachability(self):
        """Test factory returns correct kwargs for reachability."""
        config = TopologyAnalysisConfig.get_instance()
        config.set_parallel_mode('reachability', 'maximal')
        config.set_num_workers('reachability', 4)
        
        factory = AnalyzerFactory(config)
        kwargs = factory.get_analysis_kwargs('reachability')
        
        assert 'parallel' in kwargs
        assert kwargs['parallel'] == 'maximal'
        assert 'num_workers' in kwargs
        assert kwargs['num_workers'] == 4
    
    def test_get_analysis_kwargs_non_parallel_analyzer(self):
        """Test factory returns empty kwargs for non-parallel analyzers."""
        config = TopologyAnalysisConfig.get_instance()
        factory = AnalyzerFactory(config)
        
        # P-Invariants doesn't support parallelism
        kwargs = factory.get_analysis_kwargs('p_invariants')
        assert kwargs == {}
    
    def test_factory_respects_configuration_changes(self):
        """Test factory uses updated configuration."""
        config = TopologyAnalysisConfig.get_instance()
        factory = AnalyzerFactory(config)
        
        # Initial mode
        config.set_parallel_mode('reachability', 'basic')
        kwargs1 = factory.get_analysis_kwargs('reachability')
        assert kwargs1['parallel'] == 'basic'
        
        # Change mode
        config.set_parallel_mode('reachability', 'maximal')
        kwargs2 = factory.get_analysis_kwargs('reachability')
        assert kwargs2['parallel'] == 'maximal'
    
    def test_create_analyzer_unknown_name(self):
        """Test factory handles unknown analyzer gracefully."""
        config = TopologyAnalysisConfig.get_instance()
        factory = AnalyzerFactory(config)
        
        mock_model = Mock()
        with pytest.raises((KeyError, ValueError)):
            factory.create_analyzer('unknown_analyzer', mock_model)


class TestControllerIntegration:
    """Test controller integration with factory."""
    
    def test_controller_uses_factory(self):
        """Verify controller can use factory to create analyzers."""
        config = TopologyAnalysisConfig.get_instance()
        config.set_parallel_mode('reachability', 'maximal')
        
        factory = AnalyzerFactory(config)
        
        mock_model = Mock()
        # Simulate controller creating analyzer
        analyzer = factory.create_analyzer('reachability', mock_model)
        kwargs = factory.get_analysis_kwargs('reachability')
        
        # Verify analyzer is created with correct config
        assert isinstance(analyzer, ReachabilityAnalyzer)
        assert kwargs['parallel'] == 'maximal'
    
    def test_controller_factory_pattern_benefits(self):
        """Test that factory pattern reduces controller complexity."""
        config = TopologyAnalysisConfig.get_instance()
        factory = AnalyzerFactory(config)
        
        mock_model = Mock()
        
        # Before factory: Controller needed conditional logic
        # if analyzer_name == 'reachability':
        #     if use_parallel:
        #         analyzer = ReachabilityAnalyzer(model)
        #         result = analyzer.analyze(parallel=True, num_workers=8)
        #     else:
        #         analyzer = ReachabilityAnalyzer(model)
        #         result = analyzer.analyze()
        
        # After factory: Controller just delegates
        analyzer = factory.create_analyzer('reachability', mock_model)
        kwargs = factory.get_analysis_kwargs('reachability')
        
        # This is all the controller needs to do
        assert len(kwargs) > 0  # Factory provides the config


class TestPhase3Integration:
    """Integration tests for complete Phase 3 system."""
    
    def test_end_to_end_configuration(self):
        """Test complete configuration flow."""
        # 1. User opens configuration dialog
        config = TopologyAnalysisConfig.get_instance()
        
        # 2. User selects maximal mode with 8 workers
        config.set_parallel_mode('reachability', 'maximal')
        config.set_num_workers('reachability', 8)
        
        # 3. Controller creates analyzer via factory
        factory = AnalyzerFactory(config)
        mock_model = Mock()
        analyzer = factory.create_analyzer('reachability', mock_model)
        kwargs = factory.get_analysis_kwargs('reachability')
        
        # 4. Verify correct configuration
        assert isinstance(analyzer, ReachabilityAnalyzer)
        assert kwargs['parallel'] == 'maximal'
        assert kwargs['num_workers'] == 8
    
    def test_multiple_analyzers_different_configs(self):
        """Test different analyzers can have different configs."""
        config = TopologyAnalysisConfig.get_instance()
        
        # Reachability: maximal with 8 workers
        config.set_parallel_mode('reachability', 'maximal')
        config.set_num_workers('reachability', 8)
        
        # Boundedness: basic with 4 workers
        config.set_parallel_mode('boundedness', 'basic')
        config.set_num_workers('boundedness', 4)
        
        # Liveness: sequential
        config.set_parallel_mode('liveness', False)
        
        factory = AnalyzerFactory(config)
        
        # Verify each analyzer has correct config
        reach_kwargs = factory.get_analysis_kwargs('reachability')
        assert reach_kwargs['parallel'] == 'maximal'
        assert reach_kwargs['num_workers'] == 8
        
        bound_kwargs = factory.get_analysis_kwargs('boundedness')
        assert bound_kwargs['parallel'] == 'basic'
        assert bound_kwargs['num_workers'] == 4
        
        live_kwargs = factory.get_analysis_kwargs('liveness')
        assert live_kwargs['parallel'] == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
