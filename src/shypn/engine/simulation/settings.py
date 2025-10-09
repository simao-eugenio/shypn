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
    DEFAULT_STEPS_TARGET = 1000  # Target number of steps for auto dt
    
    def __init__(self):
        """Initialize with default settings."""
        self._time_units = self.DEFAULT_TIME_UNITS
        self._duration = self.DEFAULT_DURATION
        self._dt_auto = self.DEFAULT_DT_AUTO
        self._dt_manual = self.DEFAULT_DT_MANUAL
        self._time_scale = self.DEFAULT_TIME_SCALE
    
    # ========== Properties with Validation ==========
    
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
        
        Args:
            current_time_seconds: Current simulation time in seconds
        
        Returns:
            float: Progress fraction [0.0, 1.0], or 0.0 if no duration
        """
        duration_seconds = self.get_duration_seconds()
        
        if duration_seconds is None or duration_seconds <= 0:
            return 0.0  # Unknown duration
        
        progress = current_time_seconds / duration_seconds
        return min(progress, 1.0)  # Clamp to 1.0
    
    def is_complete(self, current_time_seconds: float) -> bool:
        """Check if simulation is complete based on duration.
        
        Args:
            current_time_seconds: Current simulation time in seconds
        
        Returns:
            bool: True if time >= duration, False otherwise
        """
        duration_seconds = self.get_duration_seconds()
        
        if duration_seconds is None:
            return False  # No duration = never complete
        
        return current_time_seconds >= duration_seconds
    
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
            'time_scale': self._time_scale
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
        
        return settings
    
    # ========== String Representation ==========
    
    def __repr__(self) -> str:
        """Get string representation for debugging."""
        duration_str = f"{self._duration} {self._time_units.full_name}" if self._duration else "None"
        dt_str = "auto" if self._dt_auto else f"manual ({self._dt_manual})"
        
        return (f"SimulationSettings(duration={duration_str}, "
                f"dt={dt_str}, scale={self._time_scale})")
    
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
    
    def build(self) -> SimulationSettings:
        """Build and return settings object.
        
        Returns:
            SimulationSettings: Configured settings
        """
        return self._settings
