"""
Simulation Configuration Builder

Provides fluent API for building SimulationSettings objects with comprehensive
configuration of time parameters, stochastic simulation settings, batch mode,
initial condition randomization, and validation.

This builder follows the Phase 3.1 builder pattern established by PlaceBuilder,
ArcBuilder, TransitionBuilder, and PetriNetBuilder, providing type safety,
validation, and clear API for simulation configuration.

Example:
    Basic simulation with auto time step:
    >>> config = (SimulationConfigBuilder()
    ...     .with_duration(60.0, TimeUnits.SECONDS)
    ...     .with_auto_dt()
    ...     .build())
    
    Batch mode with replication:
    >>> config = (SimulationConfigBuilder()
    ...     .with_duration(100.0, TimeUnits.SECONDS)
    ...     .with_batch_mode(replicates=200, output_folder="results")
    ...     .with_recorded_objects("P1", "P2", "T1")
    ...     .build())
    
    Stochastic simulation with τ-leaping configuration:
    >>> config = (SimulationConfigBuilder()
    ...     .with_duration(100.0, TimeUnits.SECONDS)
    ...     .with_tau_leaping(epsilon=0.03, critical_threshold=0.01)
    ...     .with_parallel_stochastic(enabled=True)
    ...     .build())
    
    Initial condition randomization for biological variability:
    >>> config = (SimulationConfigBuilder()
    ...     .with_duration(50.0, TimeUnits.SECONDS)
    ...     .with_ic_noise(percent=20.0)  # ±20% uniform noise
    ...     .with_ic_noise_places("P1", "P2")
    ...     .build())
"""

from typing import Optional, Set
from shypn.engine.simulation.settings import SimulationSettings
from shypn.utils.time_utils import TimeUnits, TimeValidator


class SimulationConfigBuilder:
    """Fluent API builder for SimulationSettings.
    
    Provides comprehensive configuration of simulation parameters including:
    - Time settings (duration, time units, time step, time scale)
    - Stochastic simulation (τ-leaping parameters)
    - Batch mode (experiment replication)
    - Initial condition randomization (biological variability)
    - Token accounting (conservation validation)
    
    All settings have sensible defaults and are validated before building.
    
    Attributes:
        _duration: Simulation duration value
        _time_units: Time units for duration
        _dt_auto: Whether to auto-calculate time step
        _dt_manual: Manual time step override
        _time_scale: Real-world time scale factor
        _tau_epsilon: τ-leaping epsilon (leap condition tolerance)
        _critical_threshold: Critical reaction threshold
        _max_tau: Maximum leap size
        _min_tau: Minimum leap size
        _use_parallel_stochastic: Enable parallel stochastic execution
        _batch_mode_enabled: Enable batch mode
        _batch_replicates: Number of batch replicates
        _batch_output_folder: Output folder for batch results
        _recorded_objects: Set of object IDs to record
        _ic_noise_enabled: Enable IC randomization
        _ic_noise_percent: Noise percentage
        _ic_noise_places: Places to apply noise to
        _token_accounting_enabled: Enable token conservation tracking
    """
    
    def __init__(self):
        """Initialize builder with default settings."""
        # Time configuration
        self._duration: Optional[float] = None
        self._time_units: TimeUnits = SimulationSettings.DEFAULT_TIME_UNITS
        self._dt_auto: bool = SimulationSettings.DEFAULT_DT_AUTO
        self._dt_manual: float = SimulationSettings.DEFAULT_DT_MANUAL
        self._time_scale: float = SimulationSettings.DEFAULT_TIME_SCALE
        
        # τ-Leaping configuration (always enabled for stochastic simulation)
        self._tau_epsilon: float = SimulationSettings.DEFAULT_TAU_EPSILON
        self._critical_threshold: float = SimulationSettings.DEFAULT_CRITICAL_THRESHOLD
        self._max_tau: float = SimulationSettings.DEFAULT_MAX_TAU
        self._min_tau: float = SimulationSettings.DEFAULT_MIN_TAU
        self._use_parallel_stochastic: bool = SimulationSettings.DEFAULT_USE_PARALLEL_STOCHASTIC
        
        # Batch mode configuration
        self._batch_mode_enabled: bool = False
        self._batch_replicates: int = 100
        self._batch_output_folder: Optional[str] = None
        self._recorded_objects: Set[str] = set()
        
        # Initial condition noise configuration
        self._ic_noise_enabled: bool = False
        self._ic_noise_percent: float = 20.0
        self._ic_noise_places: Set[str] = set()
        
        # Token accounting
        self._token_accounting_enabled: bool = False
    
    # ===== Time Configuration Methods =====
    
    def with_duration(self, duration: float, units: TimeUnits = TimeUnits.SECONDS) -> 'SimulationConfigBuilder':
        """Set simulation duration with explicit time units.
        
        Args:
            duration: Duration value (must be positive)
            units: Time units (default: SECONDS)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If duration is not positive
        
        Example:
            >>> builder.with_duration(60.0, TimeUnits.SECONDS)
            >>> builder.with_duration(1.0, TimeUnits.MINUTES)
        """
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        self._duration = duration
        self._time_units = units
        return self
    
    def with_time_units(self, units: TimeUnits) -> 'SimulationConfigBuilder':
        """Set time units without changing duration.
        
        Args:
            units: Time units enum
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_time_units(TimeUnits.MILLISECONDS)
        """
        self._time_units = units
        return self
    
    def with_auto_dt(self) -> 'SimulationConfigBuilder':
        """Enable automatic time step calculation.
        
        When enabled, dt = duration / target_steps (typically 10000 steps).
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_auto_dt()
        """
        self._dt_auto = True
        return self
    
    def with_manual_dt(self, dt: float) -> 'SimulationConfigBuilder':
        """Set manual time step and disable auto calculation.
        
        Args:
            dt: Time step in seconds (must be positive)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If dt is not positive or too small/large
        
        Example:
            >>> builder.with_manual_dt(0.01)  # 10 ms
        """
        is_valid, error = TimeValidator.validate_time_step(dt)
        if not is_valid:
            raise ValueError(f"Invalid time step: {error}")
        
        self._dt_manual = dt
        self._dt_auto = False
        return self
    
    def with_time_scale(self, scale: float) -> 'SimulationConfigBuilder':
        """Set real-world time scale factor.
        
        Args:
            scale: Time scale factor (must be positive)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If scale is not positive
        
        Example:
            >>> builder.with_time_scale(1.0)  # Real-time
            >>> builder.with_time_scale(2.0)  # 2× faster
        """
        if scale <= 0:
            raise ValueError("Time scale must be positive")
        
        self._time_scale = scale
        return self
    
    def without_duration(self) -> 'SimulationConfigBuilder':
        """Clear duration to run simulation indefinitely.
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.without_duration()  # Run until manually stopped
        """
        self._duration = None
        return self
    
    # ===== Stochastic Simulation Configuration =====
    
    def with_tau_leaping(
        self,
        epsilon: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        max_tau: Optional[float] = None,
        min_tau: Optional[float] = None
    ) -> 'SimulationConfigBuilder':
        """Configure τ-leaping parameters for stochastic simulation.
        
        τ-leaping is always enabled for stochastic simulation (10-100× faster
        than exact SSA). This method allows fine-tuning the accuracy/speed tradeoff.
        
        Args:
            epsilon: Leap condition tolerance (0 < ε < 1, typically 0.01-0.05)
                    Lower = more accurate, slower. Default: 0.03 (3%)
            critical_threshold: Propensity threshold for critical reactions
                               Default: 0.01
            max_tau: Maximum leap size in seconds (default: 0.1)
            min_tau: Minimum leap size in seconds (default: 1e-6)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If parameters are invalid
        
        Example:
            >>> # High accuracy (slower)
            >>> builder.with_tau_leaping(epsilon=0.01)
            >>> # Fast simulation (less accurate)
            >>> builder.with_tau_leaping(epsilon=0.05)
        """
        if epsilon is not None:
            if not 0 < epsilon < 1:
                raise ValueError("Epsilon must be in (0, 1)")
            self._tau_epsilon = epsilon
        
        if critical_threshold is not None:
            if critical_threshold <= 0:
                raise ValueError("Critical threshold must be positive")
            self._critical_threshold = critical_threshold
        
        if max_tau is not None:
            if max_tau <= 0:
                raise ValueError("Max tau must be positive")
            self._max_tau = max_tau
        
        if min_tau is not None:
            if min_tau <= 0:
                raise ValueError("Min tau must be positive")
            self._min_tau = min_tau
        
        # Validate min < max if both set
        if self._min_tau >= self._max_tau:
            raise ValueError(f"Min tau ({self._min_tau}) must be less than max tau ({self._max_tau})")
        
        return self
    
    def with_parallel_stochastic(self, enabled: bool = True) -> 'SimulationConfigBuilder':
        """Enable or disable parallel stochastic execution.
        
        When enabled, weakly independent transitions (convergent and regulatory
        coupling) are sampled concurrently, reflecting the biological reality
        of spatially distributed molecular collisions. Provides 2-4× speedup
        on multi-core systems.
        
        Args:
            enabled: True to enable parallel execution (default: True)
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_parallel_stochastic(True)  # Parallel (faster)
            >>> builder.with_parallel_stochastic(False)  # Sequential
        """
        self._use_parallel_stochastic = enabled
        return self
    
    # ===== Batch Mode Configuration =====
    
    def with_batch_mode(
        self,
        replicates: int = 100,
        output_folder: Optional[str] = None
    ) -> 'SimulationConfigBuilder':
        """Enable batch mode for experiment replication.
        
        Batch mode runs multiple replicate simulations with different random
        seeds, enabling statistical analysis of stochastic systems.
        
        Args:
            replicates: Number of replicate simulations (must be >= 1)
            output_folder: Output folder for results (default: None)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If replicates < 1
        
        Example:
            >>> builder.with_batch_mode(replicates=200, output_folder="results")
        """
        if replicates < 1:
            raise ValueError("Batch replicates must be at least 1")
        
        self._batch_mode_enabled = True
        self._batch_replicates = replicates
        self._batch_output_folder = output_folder
        return self
    
    def with_replicates(self, replicates: int) -> 'SimulationConfigBuilder':
        """Set number of batch replicates (enables batch mode).
        
        Args:
            replicates: Number of replicate simulations (must be >= 1)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If replicates < 1
        
        Example:
            >>> builder.with_replicates(500)
        """
        if replicates < 1:
            raise ValueError("Batch replicates must be at least 1")
        
        self._batch_mode_enabled = True
        self._batch_replicates = replicates
        return self
    
    def with_output_folder(self, folder: str) -> 'SimulationConfigBuilder':
        """Set batch output folder.
        
        Args:
            folder: Output folder path
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_output_folder("results/experiment1")
        """
        self._batch_output_folder = folder
        return self
    
    def with_recorded_objects(self, *object_ids: str) -> 'SimulationConfigBuilder':
        """Mark objects (places/transitions) for recording in batch mode.
        
        Args:
            *object_ids: Variable number of place/transition IDs to record
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_recorded_objects("P1", "P2", "T1")
        """
        self._recorded_objects.update(object_ids)
        return self
    
    def clear_recorded_objects(self) -> 'SimulationConfigBuilder':
        """Clear all recorded objects.
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.clear_recorded_objects()
        """
        self._recorded_objects.clear()
        return self
    
    # ===== Initial Condition Noise Configuration =====
    
    def with_ic_noise(
        self,
        percent: float = 20.0,
        places: Optional[Set[str]] = None
    ) -> 'SimulationConfigBuilder':
        """Enable initial condition randomization for biological variability.
        
        Applies uniform noise to initial markings for each replicate in batch mode.
        This simulates cell-to-cell variability in initial molecular concentrations.
        
        Noise formula: M₀ = M₀_nominal × uniform(1 - p/100, 1 + p/100)
        Example: 20% means M₀ ∈ [0.8×M₀_nominal, 1.2×M₀_nominal]
        
        Args:
            percent: Noise percentage (0-100, default: 20.0 = ±20%)
            places: Set of place IDs to apply noise to (None = all non-catalyst places)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If percent is out of range [0, 100]
        
        Example:
            >>> builder.with_ic_noise(percent=20.0)  # ±20% uniform noise
            >>> builder.with_ic_noise(percent=10.0, places={"P1", "P2"})
        """
        if not 0 <= percent <= 100:
            raise ValueError("Noise percentage must be between 0 and 100")
        
        self._ic_noise_enabled = True
        self._ic_noise_percent = percent
        
        if places is not None:
            self._ic_noise_places = places.copy()
        
        return self
    
    def with_ic_noise_percent(self, percent: float) -> 'SimulationConfigBuilder':
        """Set IC noise percentage (enables IC noise).
        
        Args:
            percent: Noise percentage (0-100)
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If percent is out of range [0, 100]
        
        Example:
            >>> builder.with_ic_noise_percent(15.0)  # ±15% noise
        """
        if not 0 <= percent <= 100:
            raise ValueError("Noise percentage must be between 0 and 100")
        
        self._ic_noise_enabled = True
        self._ic_noise_percent = percent
        return self
    
    def with_ic_noise_places(self, *place_ids: str) -> 'SimulationConfigBuilder':
        """Specify places to apply IC noise to.
        
        Args:
            *place_ids: Variable number of place IDs
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_ic_noise_places("P1", "P2", "P3")
        """
        self._ic_noise_places.update(place_ids)
        return self
    
    def without_ic_noise(self) -> 'SimulationConfigBuilder':
        """Disable initial condition noise.
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.without_ic_noise()
        """
        self._ic_noise_enabled = False
        return self
    
    # ===== Token Accounting Configuration =====
    
    def with_token_accounting(self, enabled: bool = True) -> 'SimulationConfigBuilder':
        """Enable or disable token accounting (conservation validation).
        
        When enabled, the simulation tracks token conservation for debugging
        and validation of places marked as catalyst or conserved.
        
        Args:
            enabled: True to enable token accounting (default: True)
        
        Returns:
            self for method chaining
        
        Example:
            >>> builder.with_token_accounting()  # Enable
            >>> builder.with_token_accounting(False)  # Disable
        """
        self._token_accounting_enabled = enabled
        return self
    
    # ===== Build Method =====
    
    def build(self) -> SimulationSettings:
        """Build and validate SimulationSettings object.
        
        Performs comprehensive validation of all settings before creating
        the final configuration object.
        
        Returns:
            SimulationSettings: Validated simulation configuration
        
        Raises:
            ValueError: If configuration is invalid
        
        Example:
            >>> settings = builder.build()
        """
        # Validate configuration
        self._validate()
        
        # Create settings object
        settings = SimulationSettings()
        
        # Apply time configuration
        settings.time_units = self._time_units
        if self._duration is not None:
            settings.duration = self._duration
        settings.dt_auto = self._dt_auto
        settings.dt_manual = self._dt_manual
        settings.time_scale = self._time_scale
        
        # Apply τ-leaping configuration
        settings.tau_epsilon = self._tau_epsilon
        settings.critical_threshold = self._critical_threshold
        settings.max_tau = self._max_tau
        settings.min_tau = self._min_tau
        settings.use_parallel_stochastic = self._use_parallel_stochastic
        
        # Apply batch mode configuration
        settings.batch_mode_enabled = self._batch_mode_enabled
        settings.batch_replicates = self._batch_replicates
        settings.batch_output_folder = self._batch_output_folder
        for obj_id in self._recorded_objects:
            settings.add_recorded_object(obj_id)
        
        # Apply IC noise configuration
        settings.ic_noise_enabled = self._ic_noise_enabled
        settings.ic_noise_percent = self._ic_noise_percent
        for place_id in self._ic_noise_places:
            settings.add_ic_noise_place(place_id)
        
        # Apply token accounting
        settings.token_accounting_enabled = self._token_accounting_enabled
        
        return settings
    
    def _validate(self):
        """Validate builder configuration before building.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate time configuration
        if self._duration is not None and self._duration <= 0:
            raise ValueError("Duration must be positive")
        
        if self._time_scale <= 0:
            raise ValueError("Time scale must be positive")
        
        if not self._dt_auto:
            is_valid, error = TimeValidator.validate_time_step(self._dt_manual)
            if not is_valid:
                raise ValueError(f"Invalid manual time step: {error}")
        
        # Validate τ-leaping configuration
        if not 0 < self._tau_epsilon < 1:
            raise ValueError("Epsilon must be in (0, 1)")
        
        if self._critical_threshold <= 0:
            raise ValueError("Critical threshold must be positive")
        
        if self._max_tau <= 0:
            raise ValueError("Max tau must be positive")
        
        if self._min_tau <= 0:
            raise ValueError("Min tau must be positive")
        
        if self._min_tau >= self._max_tau:
            raise ValueError(f"Min tau ({self._min_tau}) must be less than max tau ({self._max_tau})")
        
        # Validate batch mode configuration
        if self._batch_mode_enabled:
            if self._batch_replicates < 1:
                raise ValueError("Batch replicates must be at least 1")
        
        # Validate IC noise configuration
        if self._ic_noise_enabled:
            if not 0 <= self._ic_noise_percent <= 100:
                raise ValueError("Noise percentage must be between 0 and 100")
        
        # Validate batch + IC noise combination
        if self._ic_noise_enabled and not self._batch_mode_enabled:
            # IC noise is typically used with batch mode, but not required
            # Issue a warning through validation but don't fail
            pass
    
    def __repr__(self) -> str:
        """Get string representation for debugging."""
        duration_str = f"{self._duration} {self._time_units.full_name}" if self._duration else "None"
        dt_str = "auto" if self._dt_auto else f"manual ({self._dt_manual})"
        batch_str = f", batch={self._batch_replicates}" if self._batch_mode_enabled else ""
        noise_str = f", IC_noise={self._ic_noise_percent}%" if self._ic_noise_enabled else ""
        
        return (f"SimulationConfigBuilder(duration={duration_str}, "
                f"dt={dt_str}{batch_str}{noise_str})")
