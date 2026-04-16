"""
Tests for SimulationConfigBuilder

Comprehensive test suite for the Phase 3.1 simulation configuration builder,
covering time settings, stochastic simulation parameters, batch mode,
initial condition randomization, and validation.
"""

import pytest
from shypn.builders.simulation_config_builder import SimulationConfigBuilder
from shypn.engine.simulation.settings import SimulationSettings
from shypn.utils.time_utils import TimeUnits


class TestBasicTimeConfiguration:
    """Tests for basic time configuration methods."""
    
    def test_default_settings(self):
        """Test builder creates settings with sensible defaults."""
        builder = SimulationConfigBuilder()
        settings = builder.build()
        
        assert settings is not None
        assert isinstance(settings, SimulationSettings)
        assert settings.time_units == TimeUnits.SECONDS
        assert settings.duration is None  # Run indefinitely by default
        assert settings.dt_auto is True
        assert settings.dt_manual == 0.1
        assert settings.time_scale == 1.0
    
    def test_with_duration_seconds(self):
        """Test setting duration in seconds."""
        settings = (SimulationConfigBuilder()
                   .with_duration(60.0, TimeUnits.SECONDS)
                   .build())
        
        assert settings.duration == 60.0
        assert settings.time_units == TimeUnits.SECONDS
    
    def test_with_duration_minutes(self):
        """Test setting duration in minutes."""
        settings = (SimulationConfigBuilder()
                   .with_duration(5.0, TimeUnits.MINUTES)
                   .build())
        
        assert settings.duration == 5.0
        assert settings.time_units == TimeUnits.MINUTES
    
    def test_with_duration_milliseconds(self):
        """Test setting duration in milliseconds."""
        settings = (SimulationConfigBuilder()
                   .with_duration(1000.0, TimeUnits.MILLISECONDS)
                   .build())
        
        assert settings.duration == 1000.0
        assert settings.time_units == TimeUnits.MILLISECONDS
    
    def test_without_duration(self):
        """Test clearing duration for indefinite simulation."""
        settings = (SimulationConfigBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .without_duration()
                   .build())
        
        assert settings.duration is None
    
    def test_with_auto_dt(self):
        """Test enabling automatic time step."""
        settings = (SimulationConfigBuilder()
                   .with_auto_dt()
                   .build())
        
        assert settings.dt_auto is True
    
    def test_with_manual_dt(self):
        """Test setting manual time step."""
        settings = (SimulationConfigBuilder()
                   .with_manual_dt(0.01)
                   .build())
        
        assert settings.dt_auto is False
        assert settings.dt_manual == 0.01
    
    def test_with_time_scale(self):
        """Test setting time scale."""
        settings = (SimulationConfigBuilder()
                   .with_time_scale(2.0)
                   .build())
        
        assert settings.time_scale == 2.0
    
    def test_with_time_units(self):
        """Test changing time units without duration."""
        settings = (SimulationConfigBuilder()
                   .with_time_units(TimeUnits.MILLISECONDS)
                   .build())
        
        assert settings.time_units == TimeUnits.MILLISECONDS


class TestTauLeapingConfiguration:
    """Tests for τ-leaping configuration methods."""
    
    def test_default_tau_leaping(self):
        """Test default τ-leaping parameters."""
        settings = SimulationConfigBuilder().build()
        
        # τ-leaping always enabled
        assert settings.use_tau_leaping is True
        assert settings.tau_epsilon == 0.03
        assert settings.critical_threshold == 0.01
        assert settings.max_tau == 0.1
        assert settings.min_tau == 1e-6
        assert settings.use_parallel_stochastic is True
    
    def test_with_tau_leaping_epsilon(self):
        """Test setting τ-leaping epsilon only."""
        settings = (SimulationConfigBuilder()
                   .with_tau_leaping(epsilon=0.01)
                   .build())
        
        assert settings.tau_epsilon == 0.01
    
    def test_with_tau_leaping_all_params(self):
        """Test setting all τ-leaping parameters."""
        settings = (SimulationConfigBuilder()
                   .with_tau_leaping(
                       epsilon=0.05,
                       critical_threshold=0.02,
                       max_tau=0.2,
                       min_tau=1e-5
                   )
                   .build())
        
        assert settings.tau_epsilon == 0.05
        assert settings.critical_threshold == 0.02
        assert settings.max_tau == 0.2
        assert settings.min_tau == 1e-5
    
    def test_with_parallel_stochastic_enabled(self):
        """Test enabling parallel stochastic execution."""
        settings = (SimulationConfigBuilder()
                   .with_parallel_stochastic(True)
                   .build())
        
        assert settings.use_parallel_stochastic is True
    
    def test_with_parallel_stochastic_disabled(self):
        """Test disabling parallel stochastic execution."""
        settings = (SimulationConfigBuilder()
                   .with_parallel_stochastic(False)
                   .build())
        
        assert settings.use_parallel_stochastic is False


class TestBatchModeConfiguration:
    """Tests for batch mode configuration methods."""
    
    def test_batch_mode_disabled_by_default(self):
        """Test batch mode is disabled by default."""
        settings = SimulationConfigBuilder().build()
        
        assert settings.batch_mode_enabled is False
        assert settings.batch_replicates == 100
        assert settings.batch_output_folder is None
        assert len(settings.recorded_objects) == 0
    
    def test_with_batch_mode(self):
        """Test enabling batch mode with replicates."""
        settings = (SimulationConfigBuilder()
                   .with_batch_mode(replicates=200)
                   .build())
        
        assert settings.batch_mode_enabled is True
        assert settings.batch_replicates == 200
    
    def test_with_batch_mode_and_output_folder(self):
        """Test batch mode with output folder."""
        settings = (SimulationConfigBuilder()
                   .with_batch_mode(replicates=150, output_folder="results")
                   .build())
        
        assert settings.batch_mode_enabled is True
        assert settings.batch_replicates == 150
        assert settings.batch_output_folder == "results"
    
    def test_with_replicates(self):
        """Test setting replicates directly."""
        settings = (SimulationConfigBuilder()
                   .with_replicates(500)
                   .build())
        
        assert settings.batch_mode_enabled is True
        assert settings.batch_replicates == 500
    
    def test_with_output_folder(self):
        """Test setting output folder."""
        settings = (SimulationConfigBuilder()
                   .with_batch_mode(replicates=100)
                   .with_output_folder("output/batch1")
                   .build())
        
        assert settings.batch_output_folder == "output/batch1"
    
    def test_with_recorded_objects_single(self):
        """Test recording single object."""
        settings = (SimulationConfigBuilder()
                   .with_recorded_objects("P1")
                   .build())
        
        assert "P1" in settings.recorded_objects
    
    def test_with_recorded_objects_multiple(self):
        """Test recording multiple objects."""
        settings = (SimulationConfigBuilder()
                   .with_recorded_objects("P1", "P2", "T1", "T2")
                   .build())
        
        assert "P1" in settings.recorded_objects
        assert "P2" in settings.recorded_objects
        assert "T1" in settings.recorded_objects
        assert "T2" in settings.recorded_objects
        assert len(settings.recorded_objects) == 4
    
    def test_with_recorded_objects_chaining(self):
        """Test chaining recorded objects calls."""
        settings = (SimulationConfigBuilder()
                   .with_recorded_objects("P1", "P2")
                   .with_recorded_objects("T1")
                   .build())
        
        assert "P1" in settings.recorded_objects
        assert "P2" in settings.recorded_objects
        assert "T1" in settings.recorded_objects
    
    def test_clear_recorded_objects(self):
        """Test clearing recorded objects."""
        settings = (SimulationConfigBuilder()
                   .with_recorded_objects("P1", "P2")
                   .clear_recorded_objects()
                   .build())
        
        assert len(settings.recorded_objects) == 0


class TestInitialConditionNoise:
    """Tests for initial condition noise configuration."""
    
    def test_ic_noise_disabled_by_default(self):
        """Test IC noise is disabled by default."""
        settings = SimulationConfigBuilder().build()
        
        assert settings.ic_noise_enabled is False
        assert settings.ic_noise_percent == 20.0  # Default value
        assert len(settings.ic_noise_places) == 0
    
    def test_with_ic_noise_default_percent(self):
        """Test enabling IC noise with default percentage."""
        settings = (SimulationConfigBuilder()
                   .with_ic_noise()
                   .build())
        
        assert settings.ic_noise_enabled is True
        assert settings.ic_noise_percent == 20.0
    
    def test_with_ic_noise_custom_percent(self):
        """Test enabling IC noise with custom percentage."""
        settings = (SimulationConfigBuilder()
                   .with_ic_noise(percent=15.0)
                   .build())
        
        assert settings.ic_noise_enabled is True
        assert settings.ic_noise_percent == 15.0
    
    def test_with_ic_noise_specific_places(self):
        """Test IC noise on specific places."""
        settings = (SimulationConfigBuilder()
                   .with_ic_noise(percent=10.0, places={"P1", "P2"})
                   .build())
        
        assert settings.ic_noise_enabled is True
        assert settings.ic_noise_percent == 10.0
        assert "P1" in settings.ic_noise_places
        assert "P2" in settings.ic_noise_places
    
    def test_with_ic_noise_percent_method(self):
        """Test setting IC noise percentage via dedicated method."""
        settings = (SimulationConfigBuilder()
                   .with_ic_noise_percent(25.0)
                   .build())
        
        assert settings.ic_noise_enabled is True
        assert settings.ic_noise_percent == 25.0
    
    def test_with_ic_noise_places(self):
        """Test specifying IC noise places."""
        settings = (SimulationConfigBuilder()
                   .with_ic_noise()
                   .with_ic_noise_places("P1", "P2", "P3")
                   .build())
        
        assert "P1" in settings.ic_noise_places
        assert "P2" in settings.ic_noise_places
        assert "P3" in settings.ic_noise_places
    
    def test_without_ic_noise(self):
        """Test disabling IC noise after enabling."""
        settings = (SimulationConfigBuilder()
                   .with_ic_noise(percent=20.0)
                   .without_ic_noise()
                   .build())
        
        assert settings.ic_noise_enabled is False


class TestTokenAccounting:
    """Tests for token accounting configuration."""
    
    def test_token_accounting_disabled_by_default(self):
        """Test token accounting is disabled by default."""
        settings = SimulationConfigBuilder().build()
        
        assert settings.token_accounting_enabled is False
    
    def test_with_token_accounting_enabled(self):
        """Test enabling token accounting."""
        settings = (SimulationConfigBuilder()
                   .with_token_accounting(True)
                   .build())
        
        assert settings.token_accounting_enabled is True
    
    def test_with_token_accounting_disabled(self):
        """Test explicitly disabling token accounting."""
        settings = (SimulationConfigBuilder()
                   .with_token_accounting(False)
                   .build())
        
        assert settings.token_accounting_enabled is False
    
    def test_with_token_accounting_default_enabled(self):
        """Test token accounting defaults to enabled when called without args."""
        settings = (SimulationConfigBuilder()
                   .with_token_accounting()
                   .build())
        
        assert settings.token_accounting_enabled is True


class TestValidationErrors:
    """Tests for validation errors and edge cases."""
    
    def test_invalid_duration_negative(self):
        """Test negative duration raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Duration must be positive"):
            builder.with_duration(-10.0)
    
    def test_invalid_duration_zero(self):
        """Test zero duration raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Duration must be positive"):
            builder.with_duration(0.0)
    
    def test_invalid_manual_dt_negative(self):
        """Test negative manual dt raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Invalid time step"):
            builder.with_manual_dt(-0.01)
    
    def test_invalid_manual_dt_zero(self):
        """Test zero manual dt raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Invalid time step"):
            builder.with_manual_dt(0.0)
    
    def test_invalid_time_scale_negative(self):
        """Test negative time scale raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Time scale must be positive"):
            builder.with_time_scale(-1.0)
    
    def test_invalid_time_scale_zero(self):
        """Test zero time scale raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Time scale must be positive"):
            builder.with_time_scale(0.0)
    
    def test_invalid_epsilon_too_small(self):
        """Test epsilon <= 0 raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Epsilon must be in"):
            builder.with_tau_leaping(epsilon=0.0)
    
    def test_invalid_epsilon_too_large(self):
        """Test epsilon >= 1 raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Epsilon must be in"):
            builder.with_tau_leaping(epsilon=1.0)
    
    def test_invalid_min_tau_negative(self):
        """Test negative min_tau raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Min tau must be positive"):
            builder.with_tau_leaping(min_tau=-1e-6)
    
    def test_invalid_max_tau_negative(self):
        """Test negative max_tau raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Max tau must be positive"):
            builder.with_tau_leaping(max_tau=-0.1)
    
    def test_invalid_min_max_tau_order(self):
        """Test min_tau >= max_tau raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Min tau.*must be less than max tau"):
            builder.with_tau_leaping(min_tau=0.2, max_tau=0.1)
    
    def test_invalid_batch_replicates_zero(self):
        """Test zero batch replicates raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Batch replicates must be at least 1"):
            builder.with_batch_mode(replicates=0)
    
    def test_invalid_batch_replicates_negative(self):
        """Test negative batch replicates raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Batch replicates must be at least 1"):
            builder.with_replicates(-10)
    
    def test_invalid_ic_noise_percent_negative(self):
        """Test negative IC noise percent raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Noise percentage must be between 0 and 100"):
            builder.with_ic_noise(percent=-5.0)
    
    def test_invalid_ic_noise_percent_over_100(self):
        """Test IC noise percent > 100 raises error."""
        builder = SimulationConfigBuilder()
        
        with pytest.raises(ValueError, match="Noise percentage must be between 0 and 100"):
            builder.with_ic_noise_percent(150.0)


class TestComplexScenarios:
    """Tests for complex, realistic simulation configurations."""
    
    def test_basic_stochastic_simulation(self):
        """Test typical stochastic simulation configuration."""
        settings = (SimulationConfigBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .with_auto_dt()
                   .with_tau_leaping(epsilon=0.03)
                   .with_parallel_stochastic(True)
                   .build())
        
        assert settings.duration == 100.0
        assert settings.dt_auto is True
        assert settings.tau_epsilon == 0.03
        assert settings.use_parallel_stochastic is True
    
    def test_batch_experiment_configuration(self):
        """Test batch mode experiment with replicates."""
        settings = (SimulationConfigBuilder()
                   .with_duration(60.0, TimeUnits.SECONDS)
                   .with_batch_mode(replicates=500, output_folder="results/experiment1")
                   .with_recorded_objects("P1", "P2", "P3", "T1")
                   .build())
        
        assert settings.batch_mode_enabled is True
        assert settings.batch_replicates == 500
        assert settings.batch_output_folder == "results/experiment1"
        assert len(settings.recorded_objects) == 4
    
    def test_biological_variability_simulation(self):
        """Test simulation with IC noise for biological variability."""
        settings = (SimulationConfigBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .with_batch_mode(replicates=100)
                   .with_ic_noise(percent=20.0)
                   .with_ic_noise_places("P1", "P2", "P3")
                   .build())
        
        assert settings.batch_mode_enabled is True
        assert settings.ic_noise_enabled is True
        assert settings.ic_noise_percent == 20.0
        assert len(settings.ic_noise_places) == 3
    
    def test_high_accuracy_simulation(self):
        """Test high-accuracy stochastic simulation."""
        settings = (SimulationConfigBuilder()
                   .with_duration(50.0, TimeUnits.SECONDS)
                   .with_manual_dt(0.001)  # 1 ms time step
                   .with_tau_leaping(epsilon=0.01, max_tau=0.05)  # High accuracy
                   .with_token_accounting(True)
                   .build())
        
        assert settings.dt_auto is False
        assert settings.dt_manual == 0.001
        assert settings.tau_epsilon == 0.01
        assert settings.max_tau == 0.05
        assert settings.token_accounting_enabled is True
    
    def test_indefinite_simulation(self):
        """Test indefinite simulation (no duration)."""
        settings = (SimulationConfigBuilder()
                   .without_duration()
                   .with_manual_dt(0.1)
                   .build())
        
        assert settings.duration is None
        assert settings.dt_manual == 0.1
    
    def test_millisecond_precision_simulation(self):
        """Test simulation with millisecond precision."""
        settings = (SimulationConfigBuilder()
                   .with_duration(5000.0, TimeUnits.MILLISECONDS)
                   .with_manual_dt(1.0)  # 1 second
                   .with_time_scale(0.1)  # 10× slower
                   .build())
        
        assert settings.duration == 5000.0
        assert settings.time_units == TimeUnits.MILLISECONDS
        assert settings.time_scale == 0.1
    
    def test_comprehensive_configuration(self):
        """Test comprehensive configuration with all features."""
        settings = (SimulationConfigBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .with_auto_dt()
                   .with_time_scale(1.0)
                   .with_tau_leaping(epsilon=0.03, critical_threshold=0.01, max_tau=0.1)
                   .with_parallel_stochastic(True)
                   .with_batch_mode(replicates=200, output_folder="results")
                   .with_recorded_objects("P1", "P2", "T1")
                   .with_ic_noise(percent=15.0)
                   .with_ic_noise_places("P1", "P2")
                   .with_token_accounting(True)
                   .build())
        
        # Time configuration
        assert settings.duration == 100.0
        assert settings.time_units == TimeUnits.SECONDS
        assert settings.dt_auto is True
        assert settings.time_scale == 1.0
        
        # τ-Leaping
        assert settings.tau_epsilon == 0.03
        assert settings.critical_threshold == 0.01
        assert settings.max_tau == 0.1
        assert settings.use_parallel_stochastic is True
        
        # Batch mode
        assert settings.batch_mode_enabled is True
        assert settings.batch_replicates == 200
        assert settings.batch_output_folder == "results"
        assert len(settings.recorded_objects) == 3
        
        # IC noise
        assert settings.ic_noise_enabled is True
        assert settings.ic_noise_percent == 15.0
        assert len(settings.ic_noise_places) == 2
        
        # Token accounting
        assert settings.token_accounting_enabled is True


class TestMethodChaining:
    """Tests for fluent API method chaining."""
    
    def test_all_methods_return_builder(self):
        """Test all configuration methods return builder for chaining."""
        builder = SimulationConfigBuilder()
        
        # Test each method returns self
        assert builder.with_duration(60.0) is builder
        assert builder.with_time_units(TimeUnits.SECONDS) is builder
        assert builder.with_auto_dt() is builder
        assert builder.with_manual_dt(0.01) is builder
        assert builder.with_time_scale(1.0) is builder
        assert builder.without_duration() is builder
        
        assert builder.with_tau_leaping(epsilon=0.03) is builder
        assert builder.with_parallel_stochastic(True) is builder
        
        assert builder.with_batch_mode(replicates=100) is builder
        assert builder.with_replicates(200) is builder
        assert builder.with_output_folder("results") is builder
        assert builder.with_recorded_objects("P1") is builder
        assert builder.clear_recorded_objects() is builder
        
        assert builder.with_ic_noise(percent=20.0) is builder
        assert builder.with_ic_noise_percent(15.0) is builder
        assert builder.with_ic_noise_places("P1") is builder
        assert builder.without_ic_noise() is builder
        
        assert builder.with_token_accounting(True) is builder
    
    def test_long_method_chain(self):
        """Test long method chain works correctly."""
        settings = (SimulationConfigBuilder()
                   .with_duration(100.0, TimeUnits.SECONDS)
                   .with_auto_dt()
                   .with_tau_leaping(epsilon=0.03)
                   .with_parallel_stochastic(True)
                   .with_batch_mode(replicates=150)
                   .with_recorded_objects("P1", "P2")
                   .with_ic_noise(percent=20.0)
                   .with_token_accounting(True)
                   .build())
        
        assert settings.duration == 100.0
        assert settings.batch_replicates == 150
        assert settings.ic_noise_percent == 20.0
        assert settings.token_accounting_enabled is True


class TestBuilderReuse:
    """Tests for builder reusability."""
    
    def test_builder_can_build_multiple_times(self):
        """Test builder can be used to create multiple settings objects."""
        builder = (SimulationConfigBuilder()
                  .with_duration(60.0, TimeUnits.SECONDS)
                  .with_batch_mode(replicates=100))
        
        settings1 = builder.build()
        settings2 = builder.build()
        
        # Both should be valid
        assert settings1.duration == 60.0
        assert settings2.duration == 60.0
        
        # But different objects
        assert settings1 is not settings2
    
    def test_builder_state_preserved_between_builds(self):
        """Test builder preserves state between builds."""
        builder = SimulationConfigBuilder().with_duration(50.0)
        
        settings1 = builder.build()
        assert settings1.duration == 50.0
        
        # Modify builder
        builder.with_duration(100.0)
        
        settings2 = builder.build()
        assert settings2.duration == 100.0


class TestBuilderRepr:
    """Tests for builder string representation."""
    
    def test_repr_basic(self):
        """Test builder repr."""
        builder = SimulationConfigBuilder()
        repr_str = repr(builder)
        
        assert "SimulationConfigBuilder" in repr_str
        assert "duration=None" in repr_str
    
    def test_repr_with_duration(self):
        """Test repr with duration."""
        builder = (SimulationConfigBuilder()
                  .with_duration(60.0, TimeUnits.SECONDS))
        repr_str = repr(builder)
        
        assert "duration=60.0" in repr_str
        assert "seconds" in repr_str.lower()
    
    def test_repr_with_batch(self):
        """Test repr with batch mode."""
        builder = (SimulationConfigBuilder()
                  .with_batch_mode(replicates=200))
        repr_str = repr(builder)
        
        assert "batch=200" in repr_str
    
    def test_repr_with_ic_noise(self):
        """Test repr with IC noise."""
        builder = (SimulationConfigBuilder()
                  .with_ic_noise(percent=20.0))
        repr_str = repr(builder)
        
        assert "IC_noise=20.0%" in repr_str
