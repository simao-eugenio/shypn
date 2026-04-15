"""Test simulation settings serialization with τ-leaping parameters."""
import pytest
from shypn.engine.simulation.settings import SimulationSettings, SimulationSettingsBuilder
from shypn.utils.time_utils import TimeUnits


class TestSettingsSerialization:
    """Test serialization/deserialization of settings."""
    
    def test_basic_serialization(self):
        """Test basic settings serialization."""
        settings = SimulationSettings()
        settings.set_duration(60.0, TimeUnits.SECONDS)
        settings.dt_auto = True
        
        # Serialize
        data = settings.to_dict()
        
        # Verify basic fields
        assert data['time_units'] == 'seconds'
        assert data['duration'] == 60.0
        assert data['dt_auto'] is True
        
        # Deserialize
        restored = SimulationSettings.from_dict(data)
        assert restored.duration == 60.0
        assert restored.time_units == TimeUnits.SECONDS
        assert restored.dt_auto is True
    
    def test_tau_leaping_serialization(self):
        """Test τ-leaping settings serialization."""
        settings = (SimulationSettingsBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .with_tau_leaping(
                       epsilon=0.05,
                       critical_threshold=15.0,
                       max_tau=2.0,
                       min_tau=1e-5,
                       use_parallel=True
                   )
                   .build())
        
        # Serialize
        data = settings.to_dict()
        
        # Verify τ-leaping fields
        assert data['use_tau_leaping'] is True
        assert data['tau_epsilon'] == 0.05
        assert data['critical_threshold'] == 15.0
        assert data['max_tau'] == 2.0
        assert data['min_tau'] == 1e-5
        assert data['use_parallel_stochastic'] is True
        
        # Deserialize
        restored = SimulationSettings.from_dict(data)
        assert restored.use_tau_leaping is True
        assert restored.tau_epsilon == 0.05
        assert restored.critical_threshold == 15.0
        assert restored.max_tau == 2.0
        assert restored.min_tau == 1e-5
        assert restored.use_parallel_stochastic is True
    
    def test_backward_compatibility(self):
        """Test that old saved settings without τ-leaping fields load correctly."""
        # Old format without τ-leaping fields
        old_data = {
            'time_units': 'seconds',
            'duration': 60.0,
            'dt_auto': True,
            'dt_manual': 0.1,
            'time_scale': 1.0
        }
        
        # Should load with default τ-leaping values
        settings = SimulationSettings.from_dict(old_data)
        
        assert settings.use_tau_leaping is False  # Default
        assert settings.tau_epsilon == 0.03  # Default
        assert settings.critical_threshold == 10.0  # Default
        assert settings.use_parallel_stochastic is False  # Default
    
    def test_string_representation(self):
        """Test string representation includes τ-leaping info."""
        settings = (SimulationSettingsBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .with_tau_leaping(epsilon=0.03, use_parallel=True)
                   .build())
        
        str_repr = str(settings)
        
        # Should include τ-leaping information
        assert 'τ-Leaping' in str_repr
        assert 'Epsilon' in str_repr
        assert '0.03' in str_repr
        assert 'Parallel execution: Enabled' in str_repr
    
    def test_repr_includes_stochastic_mode(self):
        """Test __repr__ includes stochastic mode."""
        # Exact SSA
        settings1 = SimulationSettings()
        repr1 = repr(settings1)
        assert 'exact SSA' in repr1
        
        # τ-leaping
        settings2 = (SimulationSettingsBuilder()
                    .with_tau_leaping()
                    .build())
        repr2 = repr(settings2)
        assert 'τ-leaping' in repr2
        
        # τ-leaping + parallel
        settings3 = (SimulationSettingsBuilder()
                    .with_tau_leaping(use_parallel=True)
                    .build())
        repr3 = repr(settings3)
        assert 'τ-leaping+parallel' in repr3
    
    def test_buffered_settings_clones_tau_leaping(self):
        """Test that BufferedSettings properly clones τ-leaping settings."""
        from shypn.engine.simulation.buffered import BufferedSimulationSettings
        
        settings = (SimulationSettingsBuilder()
                   .with_tau_leaping(epsilon=0.04, use_parallel=True)
                   .build())
        
        buffered = BufferedSimulationSettings(settings)
        
        # Modify buffer
        buffered.buffer.tau_epsilon = 0.05
        buffered.buffer.use_parallel_stochastic = False
        
        # Original should be unchanged (not committed yet)
        assert settings.tau_epsilon == 0.04
        assert settings.use_parallel_stochastic is True
        
        # Commit changes
        buffered.mark_dirty()
        buffered.commit()
        
        # Now original should be updated
        assert settings.tau_epsilon == 0.05
        assert settings.use_parallel_stochastic is False
    
    def test_builder_exact_ssa(self):
        """Test builder can disable τ-leaping."""
        settings = (SimulationSettingsBuilder()
                   .with_tau_leaping()  # Enable
                   .with_exact_ssa()    # Disable
                   .build())
        
        assert settings.use_tau_leaping is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
