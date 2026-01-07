"""
Simulation Settings Module

Provides SimulationSettings class to encapsulate all timing and execution
configuration for simulation. Follows OOP principles with validation,
defaults, and clear separation of concerns.
"""
from typing import Optional
from shypn.utils.time_utils import TimeUnits, TimeConverter, TimeValidator


class SimulationSettings:
    """Encapsulates simulation configuration settings.
    
    This class manages all timing and execution parameters for a simulation,
    including time units, duration, time step calculation, and time scale.
    
    Attributes:
        time_units: TimeUnits enum for model time interpretation
        duration: Simulation duration in time_units (None = run indefinitely)
        dt_auto: Whether to auto-calculate time step
        dt_manual: Manual time step override (used if dt_auto=False)
        time_scale: Real-world time scale factor (future use)
    
    Example:
        settings = SimulationSettings()
        settings.set_duration(60.0, TimeUnits.SECONDS)
        dt = settings.get_effective_dt()  # Auto: 60/1000 = 0.06
    """
    
    # Default values
    DEFAULT_TIME_UNITS = TimeUnits.SECONDS
    DEFAULT_DURATION = None  # Run indefinitely
    DEFAULT_DT_AUTO = True
    DEFAULT_DT_MANUAL = 0.1
    DEFAULT_TIME_SCALE = 1.0
    DEFAULT_STEPS_TARGET = 10000  # Target number of steps for auto dt
    
    # τ-Leaping defaults - ALWAYS ENABLED (it's the stochastic engine, not an option)
    # τ-leaping is 10-100× faster than exact SSA and enables continuous+stochastic concurrency
    DEFAULT_TAU_EPSILON = 0.03  # 3% leap condition tolerance (controls accuracy)
    DEFAULT_CRITICAL_THRESHOLD = 0.01  # Propensity threshold for critical reactions (lowered for biochemical models)
    DEFAULT_MAX_TAU = 0.1  # Maximum leap size (seconds) - allows reasonable simulation speed
    DEFAULT_MIN_TAU = 1e-6  # Minimum leap size (seconds)
    DEFAULT_USE_PARALLEL_STOCHASTIC = True  # Parallel sampling for weakly independent transitions (2-4× faster)
    # Note: max_workers is auto-determined from os.cpu_count(), not a user setting
    # Note: use_tau_leaping removed - τ-leaping is always the stochastic simulation method
    
    # Precision tolerance for time comparisons (prevents floating-point errors)
    # Using 1e-9 (1 nanosecond) to safely handle accumulated rounding errors
    # while still maintaining high precision for scientific simulations
    TIME_EPSILON = 1e-9
    
    def __init__(self):
        """Initialize with default settings."""
        self._time_units = self.DEFAULT_TIME_UNITS
        self._duration = self.DEFAULT_DURATION
        self._dt_auto = self.DEFAULT_DT_AUTO
        self._dt_manual = self.DEFAULT_DT_MANUAL
        self._time_scale = self.DEFAULT_TIME_SCALE
        
        # τ-Leaping settings (τ-leaping is always used for stochastic simulation)
        self._tau_epsilon = self.DEFAULT_TAU_EPSILON
        self._critical_threshold = self.DEFAULT_CRITICAL_THRESHOLD
        self._max_tau = self.DEFAULT_MAX_TAU
        self._min_tau = self.DEFAULT_MIN_TAU
        self._use_parallel_stochastic = self.DEFAULT_USE_PARALLEL_STOCHASTIC
        
        # Batch mode settings (for experiment replication)
        self._batch_mode_enabled = False
        self._batch_replicates = 100
        self._batch_output_folder = None
        self._recorded_objects = set()  # Set of place/transition IDs to record
        
        # Initial condition randomness (biological variability)
        self._ic_noise_enabled = False  # Enable random perturbations to initial conditions
        self._ic_noise_percent = 20.0  # Percentage of noise (±20% = uniform in [0.8, 1.2] range)
        self._ic_noise_places = set()  # Specific places to randomize (empty = all non-catalyst places)
        
        # Token accounting (conservation validation)
        self._token_accounting_enabled = False  # Enable token conservation tracking
    
    # ========== Properties with Validation ==========
    
    @property
    def token_accounting_enabled(self) -> bool:
        """Get token accounting enabled status."""
        return self._token_accounting_enabled
    
    @token_accounting_enabled.setter
    def token_accounting_enabled(self, value: bool):
        """Set token accounting enabled with validation.
        
        Args:
            value: Whether to enable token accounting
        
        Raises:
            TypeError: If value is not bool
        """
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool, got {type(value)}")
        self._token_accounting_enabled = value
    
    @property
    def time_units(self) -> TimeUnits:
        """Get time units for model."""
        return self._time_units
    
    @time_units.setter
    def time_units(self, value: TimeUnits):
        """Set time units with validation.
        
        Args:
            value: TimeUnits enum value
        
        Raises:
            TypeError: If value is not TimeUnits enum
        """
        if not isinstance(value, TimeUnits):
            raise TypeError(f"Expected TimeUnits, got {type(value)}")
        self._time_units = value
    
    @property
    def duration(self) -> Optional[float]:
        """Get simulation duration in time_units."""
        return self._duration
    
    @duration.setter
    def duration(self, value: Optional[float]):
        """Set simulation duration with validation.
        
        Args:
            value: Duration in time_units, or None for indefinite
        
        Raises:
            ValueError: If duration is negative or zero
        """
        if value is not None:
            if value <= 0:
                raise ValueError("Duration must be positive or None")
            
            # Validate using TimeValidator
            is_valid, error = TimeValidator.validate_duration(value, self._time_units)
            if not is_valid:
                raise ValueError(f"Invalid duration: {error}")
        
        self._duration = value
    
    @property
    def dt_auto(self) -> bool:
        """Get whether time step is auto-calculated."""
        return self._dt_auto
    
    @dt_auto.setter
    def dt_auto(self, value: bool):
        """Set auto time step mode."""
        self._dt_auto = bool(value)
    
    @property
    def dt_manual(self) -> float:
        """Get manual time step value."""
        return self._dt_manual
    
    @dt_manual.setter
    def dt_manual(self, value: float):
        """Set manual time step with validation.
        
        Args:
            value: Time step in seconds
        
        Raises:
            ValueError: If time step is invalid
        """
        is_valid, error = TimeValidator.validate_time_step(value)
        if not is_valid:
            raise ValueError(f"Invalid time step: {error}")
        self._dt_manual = value
    
    @property
    def time_scale(self) -> float:
        """Get time scale factor (real-world to simulation)."""
        return self._time_scale
    
    @time_scale.setter
    def time_scale(self, value: float):
        """Set time scale with validation.
        
        Args:
            value: Scale factor (must be positive)
        
        Raises:
            ValueError: If scale is not positive
        """
        if value <= 0:
            raise ValueError("Time scale must be positive")
        self._time_scale = value
    
    # ========== τ-Leaping Properties ==========
    
    @property
    def use_tau_leaping(self) -> bool:
        """DEPRECATED: τ-leaping is always enabled (it's the stochastic engine).
        
        This property exists for backward compatibility but always returns True.
        To control parallelism, use use_parallel_stochastic instead.
        """
        return True  # Always enabled
    
    @use_tau_leaping.setter
    def use_tau_leaping(self, value: bool):
        """DEPRECATED: τ-leaping cannot be disabled (it's the stochastic engine).
        
        Setting this has no effect. τ-leaping is always used for stochastic simulation
        because it's 10-100× faster than exact SSA and enables continuous+stochastic concurrency.
        """
        pass  # Ignored - τ-leaping is always enabled
    
    @property
    def tau_epsilon(self) -> float:
        """Get τ-leaping epsilon (leap condition tolerance)."""
        return self._tau_epsilon
    
    @tau_epsilon.setter
    def tau_epsilon(self, value: float):
        """Set epsilon with validation.
        
        Args:
            value: Epsilon (0 < ε < 1, typically 0.01-0.05)
        
        Raises:
            ValueError: If epsilon is invalid
        """
        if not 0 < value < 1:
            raise ValueError("Epsilon must be in (0, 1)")
        self._tau_epsilon = value
    
    @property
    def critical_threshold(self) -> float:
        """Get critical reaction threshold."""
        return self._critical_threshold
    
    @critical_threshold.setter
    def critical_threshold(self, value: float):
        """Set critical threshold with validation.
        
        Args:
            value: Threshold (positive)
        
        Raises:
            ValueError: If threshold is not positive
        """
        if value <= 0:
            raise ValueError("Critical threshold must be positive")
        self._critical_threshold = value
    
    @property
    def max_tau(self) -> float:
        """Get maximum leap size."""
        return self._max_tau
    
    @max_tau.setter
    def max_tau(self, value: float):
        """Set maximum tau with validation.
        
        Args:
            value: Max tau (positive)
        
        Raises:
            ValueError: If max_tau is not positive
        """
        if value <= 0:
            raise ValueError("Max tau must be positive")
        self._max_tau = value
    
    @property
    def min_tau(self) -> float:
        """Get minimum leap size."""
        return self._min_tau
    
    @min_tau.setter
    def min_tau(self, value: float):
        """Set minimum tau with validation.
        
        Args:
            value: Min tau (positive, < max_tau)
        
        Raises:
            ValueError: If min_tau is invalid
        """
        if value <= 0:
            raise ValueError("Min tau must be positive")
        if hasattr(self, '_max_tau') and value >= self._max_tau:
            raise ValueError("Min tau must be less than max tau")
        self._min_tau = value
    
    @property
    def use_parallel_stochastic(self) -> bool:
        """Get whether parallel stochastic execution is enabled.
        
        When enabled, weakly independent transitions (convergent and regulatory
        coupling) are sampled concurrently, reflecting the biological reality
        of spatially distributed molecular collisions. Thread count is
        automatically determined based on system capabilities.
        """
        return self._use_parallel_stochastic
    
    @use_parallel_stochastic.setter
    def use_parallel_stochastic(self, value: bool):
        """Set parallel stochastic mode.
        
        Args:
            value: True to enable parallel sampling of weakly independent transitions
        """
        self._use_parallel_stochastic = bool(value)

    
    # ========== Duration Management ==========
    
    def set_duration(self, duration: float, units: TimeUnits):
        """Set duration with explicit units.
        
        Args:
            duration: Duration value
            units: Time units for duration
        """
        self.time_units = units
        self.duration = duration
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get duration in seconds.
        
        Returns:
            float or None: Duration in seconds, or None if not set
        """
        if self._duration is None:
            return None
        return TimeConverter.to_seconds(self._duration, self._time_units)
    
    def clear_duration(self):
        """Clear duration (run indefinitely)."""
        self._duration = None
    
    # ========== Time Step Calculation ==========
    
    def get_effective_dt(self) -> float:
        """Calculate effective time step.
        
        If auto mode: dt = duration / target_steps (default 1000 steps)
        If manual mode: dt = dt_manual
        If auto but no duration: fallback to dt_manual
        
        Returns:
            float: Time step in seconds
        """
        if self._dt_auto:
            duration_seconds = self.get_duration_seconds()
            
            if duration_seconds is not None and duration_seconds > 0:
                # Auto: duration / target steps
                dt = duration_seconds / self.DEFAULT_STEPS_TARGET
                
                # Validate
                is_valid, _ = TimeValidator.validate_time_step(dt)
                if is_valid:
                    return dt
            
            # Fallback to manual if auto calculation fails
            return self._dt_manual
        else:
            # Manual mode
            return self._dt_manual
    
    def estimate_step_count(self) -> Optional[int]:
        """Estimate total number of simulation steps.
        
        Returns:
            int or None: Estimated steps, or None if no duration set
        """
        duration_seconds = self.get_duration_seconds()
        if duration_seconds is None:
            return None
        
        dt = self.get_effective_dt()
        step_count = int(duration_seconds / dt) + 1
        return step_count
    
    def get_step_count_warning(self) -> Optional[str]:
        """Get warning message if step count is problematic.
        
        Returns:
            str or None: Warning message, or None if okay
        """
        step_count = self.estimate_step_count()
        if step_count is None:
            return None
        
        duration_seconds = self.get_duration_seconds()
        dt = self.get_effective_dt()
        
        _, warning = TimeValidator.estimate_step_count(duration_seconds, dt)
        return warning if warning else None
    
    # ========== Progress Tracking ==========
    
    def calculate_progress(self, current_time_seconds: float) -> float:
        """Calculate simulation progress as fraction.
        
        Uses min(progress, 1.0) clamping to ensure progress never exceeds 100%,
        even if simulation overshoots duration due to time step granularity.
        
        Args:
            current_time_seconds: Current simulation time in seconds
        
        Returns:
            float: Progress fraction [0.0, 1.0], or 0.0 if no duration
        
        Example:
            duration = 60.0
            time = 30.0  → 0.5 (50%)
            time = 60.0  → 1.0 (100%)
            time = 60.1  → 1.0 (clamped, overshoot)
        """
        duration_seconds = self.get_duration_seconds()
        
        if duration_seconds is None or duration_seconds <= 0:
            return 0.0  # Unknown duration
        
        progress = current_time_seconds / duration_seconds
        return min(progress, 1.0)  # Clamp to prevent overshoot display
    
    def is_complete(self, current_time_seconds: float) -> bool:
        """Check if simulation is complete based on duration.
        
        Uses epsilon tolerance to handle floating-point precision issues.
        A simulation is considered complete if current_time >= duration - epsilon.
        
        This prevents two common issues:
        1. Simulation overshooting duration due to time step granularity
        2. Simulation never reaching exact duration due to rounding errors
        
        Args:
            current_time_seconds: Current simulation time in seconds
        
        Returns:
            bool: True if time >= duration (within epsilon), False otherwise
        
        Example:
            duration = 60.0, epsilon = 1e-9
            time = 59.999999999  → True (close enough)
            time = 60.0          → True (exact match)
            time = 60.000000001  → True (slightly over)
            time = 59.9          → False (not close enough)
        """
        duration_seconds = self.get_duration_seconds()
        
        if duration_seconds is None:
            return False  # No duration = never complete
        
        # Use epsilon tolerance: complete if within epsilon of duration
        # This handles both undershooting (59.99999999) and overshooting (60.00000001)
        return current_time_seconds >= (duration_seconds - self.TIME_EPSILON)
    
    # ========== Serialization ==========
    
    def to_dict(self) -> dict:
        """Serialize settings to dictionary.
        
        Returns:
            dict: Settings as dictionary for saving
        """
        return {
            'time_units': self._time_units.full_name,
            'duration': self._duration,
            'dt_auto': self._dt_auto,
            'dt_manual': self._dt_manual,
            'time_scale': self._time_scale,
            # τ-Leaping settings
            'use_tau_leaping': True,  # Always enabled (kept for compatibility)
            'tau_epsilon': self._tau_epsilon,
            'critical_threshold': self._critical_threshold,
            'max_tau': self._max_tau,
            'min_tau': self._min_tau,
            'use_parallel_stochastic': self._use_parallel_stochastic
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SimulationSettings':
        """Deserialize settings from dictionary.
        
        Args:
            data: Dictionary with settings
        
        Returns:
            SimulationSettings: New instance with loaded settings
        """
        settings = cls()
        
        if 'time_units' in data:
            settings.time_units = TimeUnits.from_string(data['time_units'])
        
        if 'duration' in data:
            settings.duration = data['duration']
        
        if 'dt_auto' in data:
            settings.dt_auto = data['dt_auto']
        
        if 'dt_manual' in data:
            settings.dt_manual = data['dt_manual']
        
        if 'time_scale' in data:
            settings.time_scale = data['time_scale']
        
        # τ-Leaping settings (with defaults for backward compatibility)
        if 'use_tau_leaping' in data:
            pass  # Ignored - τ-leaping is always enabled
        
        if 'tau_epsilon' in data:
            settings.tau_epsilon = data['tau_epsilon']
        
        if 'critical_threshold' in data:
            settings.critical_threshold = data['critical_threshold']
        
        if 'max_tau' in data:
            settings.max_tau = data['max_tau']
        
        if 'min_tau' in data:
            settings.min_tau = data['min_tau']
        
        if 'use_parallel_stochastic' in data:
            settings.use_parallel_stochastic = data['use_parallel_stochastic']
        
        return settings
    
    # ========== String Representation ==========
    
    def __repr__(self) -> str:
        """Get string representation for debugging."""
        duration_str = f"{self._duration} {self._time_units.full_name}" if self._duration else "None"
        dt_str = "auto" if self._dt_auto else f"manual ({self._dt_manual})"
        tau_str = "τ-leaping (always)"  # τ-leaping is always the stochastic engine
        parallel_str = "+parallel" if self._use_parallel_stochastic else ""
        
        return (f"SimulationSettings(duration={duration_str}, "
                f"dt={dt_str}, scale={self._time_scale}, "
                f"stochastic={tau_str}{parallel_str})")
    
    def __str__(self) -> str:
        """Get user-friendly string representation."""
        lines = []
        
        # Duration
        if self._duration is not None:
            lines.append(f"Duration: {self._duration} {self._time_units.full_name}")
        else:
            lines.append("Duration: Not set (run indefinitely)")
        
        # Time step
        dt = self.get_effective_dt()
        if self._dt_auto:
            lines.append(f"Time step: Auto ({dt:.6f} s)")
        else:
            lines.append(f"Time step: Manual ({dt:.6f} s)")
        
        # Estimated steps
        step_count = self.estimate_step_count()
        if step_count is not None:
            lines.append(f"Estimated steps: {step_count:,}")
            
            warning = self.get_step_count_warning()
            if warning:
                lines.append(f"Warning: {warning}")
        
        # Time scale
        lines.append(f"Time scale: {self._time_scale}")
        
        # Stochastic simulation mode (τ-leaping is always used)
        lines.append("\n✓ Stochastic Mode: τ-leaping (always enabled, 10-100× faster than exact SSA)")
        lines.append(f"  Accuracy: ε={self._tau_epsilon:.4f} (leap condition tolerance)")
        lines.append(f"  Critical threshold: {self._critical_threshold}")
        lines.append(f"  Tau range: [{self._min_tau}, {self._max_tau}]")
        if self._use_parallel_stochastic:
            lines.append(f"  Parallel execution: Enabled (weak independence scheduling)")
        else:
            lines.append(f"  Parallel execution: Disabled (sequential τ-leaping)")
        
        return "\n".join(lines)


class SimulationSettingsBuilder:
    """Builder pattern for creating SimulationSettings.
    
    Provides fluent API for constructing settings objects.
    
    Example:
        settings = (SimulationSettingsBuilder()
                   .with_duration(60, TimeUnits.SECONDS)
                   .with_auto_dt()
                   .build())
    """
    
    def __init__(self):
        """Initialize builder."""
        self._settings = SimulationSettings()
    
    def with_duration(self, duration: float, units: TimeUnits) -> 'SimulationSettingsBuilder':
        """Set duration.
        
        Args:
            duration: Duration value
            units: Time units
        
        Returns:
            SimulationSettingsBuilder: Self for chaining
        """
        self._settings.set_duration(duration, units)
        return self
    
    def with_auto_dt(self) -> 'SimulationSettingsBuilder':
        """Enable auto time step calculation.
        
        Returns:
            SimulationSettingsBuilder: Self for chaining
        """
        self._settings.dt_auto = True
        return self
    
    def with_manual_dt(self, dt: float) -> 'SimulationSettingsBuilder':
        """Set manual time step.
        
        Args:
            dt: Time step in seconds
        
        Returns:
            SimulationSettingsBuilder: Self for chaining
        """
        self._settings.dt_auto = False
        self._settings.dt_manual = dt
        return self
    
    def with_time_scale(self, scale: float) -> 'SimulationSettingsBuilder':
        """Set time scale.
        
        Args:
            scale: Time scale factor
        
        Returns:
            SimulationSettingsBuilder: Self for chaining
        """
        self._settings.time_scale = scale
        return self
    
    def with_tau_leaping(
        self,
        epsilon: float = 0.03,
        critical_threshold: float = 10.0,
        max_tau: float = 1.0,
        min_tau: float = 1e-6,
        use_parallel: bool = False
    ) -> 'SimulationSettingsBuilder':
        """Enable τ-leaping approximate stochastic simulation.
        
        Args:
            epsilon: Leap condition tolerance (smaller = more accurate, typically 0.01-0.05)
            critical_threshold: Propensity below this uses exact SSA
            max_tau: Maximum leap size
            min_tau: Minimum leap size
            use_parallel: Enable parallel sampling for weakly independent transitions.
                         Thread count auto-determined from system capabilities.
        
        Returns:
            SimulationSettingsBuilder: Self for chaining
        """
        self._settings.use_tau_leaping = True
        self._settings.tau_epsilon = epsilon
        self._settings.critical_threshold = critical_threshold
        self._settings.max_tau = max_tau
        self._settings.min_tau = min_tau
        self._settings.use_parallel_stochastic = use_parallel
        return self
    
    def with_exact_ssa(self) -> 'SimulationSettingsBuilder':
        """Disable τ-leaping (use exact SSA).
        
        Returns:
            SimulationSettingsBuilder: Self for chaining
        """
        self._settings.use_tau_leaping = False
        return self
    
    def build(self) -> SimulationSettings:
        """Build and return settings object.
        
        Returns:
            SimulationSettings: Configured settings
        """
        return self._settings

# ==================== Batch Mode Extension ====================

# Add batch mode properties to SimulationSettings
def _add_batch_mode_properties():
    """Add batch mode properties to SimulationSettings class.
    
    This function extends the SimulationSettings class with batch mode
    functionality without modifying the core settings file structure.
    """
    
    # Batch mode enabled property
    @property
    def batch_mode_enabled(self) -> bool:
        """Get whether batch mode is enabled."""
        return getattr(self, '_batch_mode_enabled', False)
    
    @batch_mode_enabled.setter
    def batch_mode_enabled(self, value: bool):
        """Set batch mode enabled state."""
        self._batch_mode_enabled = bool(value)
    
    # Batch replicates property
    @property
    def batch_replicates(self) -> int:
        """Get number of batch replicates."""
        return getattr(self, '_batch_replicates', 100)
    
    @batch_replicates.setter
    def batch_replicates(self, value: int):
        """Set number of batch replicates with validation.
        
        Args:
            value: Number of replicates (must be >= 1)
        
        Raises:
            ValueError: If replicates < 1
        """
        if value < 1:
            raise ValueError("Batch replicates must be at least 1")
        self._batch_replicates = int(value)
    
    # Batch output folder property
    @property
    def batch_output_folder(self) -> Optional[str]:
        """Get batch output folder path."""
        return getattr(self, '_batch_output_folder', None)
    
    @batch_output_folder.setter
    def batch_output_folder(self, value: Optional[str]):
        """Set batch output folder path."""
        self._batch_output_folder = value
    
    # Recorded objects property
    @property
    def recorded_objects(self) -> set:
        """Get set of object IDs marked for recording."""
        if not hasattr(self, '_recorded_objects'):
            self._recorded_objects = set()
        return self._recorded_objects
    
    # Batch mode methods
    def add_recorded_object(self, object_id: str):
        """Mark an object (place/transition) for recording.
        
        Args:
            object_id: ID of place or transition to record
        """
        if not hasattr(self, '_recorded_objects'):
            self._recorded_objects = set()
        self._recorded_objects.add(object_id)
    
    def remove_recorded_object(self, object_id: str):
        """Unmark an object from recording.
        
        Args:
            object_id: ID of place or transition to stop recording
        """
        if hasattr(self, '_recorded_objects'):
            self._recorded_objects.discard(object_id)
    
    def clear_recorded_objects(self):
        """Clear all recorded objects."""
        if hasattr(self, '_recorded_objects'):
            self._recorded_objects.clear()
    
    def is_object_recorded(self, object_id: str) -> bool:
        """Check if an object is marked for recording.
        
        Args:
            object_id: ID of place or transition
        
        Returns:
            bool: True if object is marked for recording
        """
        if not hasattr(self, '_recorded_objects'):
            return False
        return object_id in self._recorded_objects
    
    # Initial condition noise properties
    @property
    def ic_noise_enabled(self) -> bool:
        """Get whether initial condition noise is enabled.
        
        When enabled, initial markings are perturbed by random noise
        for each replicate in batch mode. This simulates biological
        cell-to-cell variability in initial molecular concentrations.
        """
        return getattr(self, '_ic_noise_enabled', False)
    
    @ic_noise_enabled.setter
    def ic_noise_enabled(self, value: bool):
        """Set initial condition noise enabled state."""
        self._ic_noise_enabled = bool(value)
    
    @property
    def ic_noise_percent(self) -> float:
        """Get initial condition noise percentage.
        
        Noise is applied as uniform distribution: value * uniform(1-p/100, 1+p/100)
        Example: 20% means each IC is multiplied by uniform(0.8, 1.2)
        """
        return getattr(self, '_ic_noise_percent', 20.0)
    
    @ic_noise_percent.setter
    def ic_noise_percent(self, value: float):
        """Set noise percentage with validation.
        
        Args:
            value: Noise percentage (0-100)
        
        Raises:
            ValueError: If percentage is out of range
        """
        if not 0 <= value <= 100:
            raise ValueError("Noise percentage must be between 0 and 100")
        self._ic_noise_percent = float(value)
    
    @property
    def ic_noise_places(self) -> set:
        """Get set of place IDs to apply noise to.
        
        If empty, noise is applied to all non-catalyst places.
        """
        if not hasattr(self, '_ic_noise_places'):
            self._ic_noise_places = set()
        return self._ic_noise_places
    
    def add_ic_noise_place(self, place_id: str):
        """Mark a place for initial condition randomization.
        
        Args:
            place_id: ID of place to randomize
        """
        if not hasattr(self, '_ic_noise_places'):
            self._ic_noise_places = set()
        self._ic_noise_places.add(place_id)
    
    def remove_ic_noise_place(self, place_id: str):
        """Remove a place from randomization.
        
        Args:
            place_id: ID of place to stop randomizing
        """
        if hasattr(self, '_ic_noise_places'):
            self._ic_noise_places.discard(place_id)
    
    def clear_ic_noise_places(self):
        """Clear all places from randomization list."""
        if hasattr(self, '_ic_noise_places'):
            self._ic_noise_places.clear()
    
    # Add methods to SimulationSettings class
    SimulationSettings.batch_mode_enabled = batch_mode_enabled
    SimulationSettings.batch_replicates = batch_replicates
    SimulationSettings.batch_output_folder = batch_output_folder
    SimulationSettings.recorded_objects = recorded_objects
    SimulationSettings.add_recorded_object = add_recorded_object
    SimulationSettings.remove_recorded_object = remove_recorded_object
    SimulationSettings.clear_recorded_objects = clear_recorded_objects
    SimulationSettings.is_object_recorded = is_object_recorded
    SimulationSettings.ic_noise_enabled = ic_noise_enabled
    SimulationSettings.ic_noise_percent = ic_noise_percent
    SimulationSettings.ic_noise_places = ic_noise_places
    SimulationSettings.add_ic_noise_place = add_ic_noise_place
    SimulationSettings.remove_ic_noise_place = remove_ic_noise_place
    SimulationSettings.clear_ic_noise_places = clear_ic_noise_places


# Initialize batch mode properties
_add_batch_mode_properties()
