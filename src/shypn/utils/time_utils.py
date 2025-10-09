"""
Time Utilities Module

Provides OOP classes for time unit conversion, formatting, and display.
Follows clean architecture with separate concerns:
- TimeUnits: Enum for supported time units
- TimeConverter: Unit conversion logic
- TimeFormatter: Display formatting logic
"""
from enum import Enum
from typing import Dict, Tuple


class TimeUnits(Enum):
    """Enumeration of supported time units."""
    MILLISECONDS = ('milliseconds', 'ms', 0.001)
    SECONDS = ('seconds', 's', 1.0)
    MINUTES = ('minutes', 'min', 60.0)
    HOURS = ('hours', 'hr', 3600.0)
    DAYS = ('days', 'd', 86400.0)
    
    def __init__(self, full_name: str, abbreviation: str, seconds_multiplier: float):
        self.full_name = full_name
        self.abbreviation = abbreviation
        self.seconds_multiplier = seconds_multiplier
    
    @classmethod
    def from_string(cls, name: str) -> 'TimeUnits':
        """Get TimeUnits from full name or abbreviation.
        
        Args:
            name: Full name (e.g., 'seconds') or abbreviation (e.g., 's')
        
        Returns:
            TimeUnits: Matching enum value
        
        Raises:
            ValueError: If name not recognized
        """
        name_lower = name.lower()
        for unit in cls:
            if unit.full_name == name_lower or unit.abbreviation == name_lower:
                return unit
        raise ValueError(f"Unknown time unit: {name}")
    
    @classmethod
    def get_all_names(cls) -> list:
        """Get list of all full names.
        
        Returns:
            list: Full names of all time units
        """
        return [unit.full_name for unit in cls]
    
    @classmethod
    def get_all_abbreviations(cls) -> list:
        """Get list of all abbreviations.
        
        Returns:
            list: Abbreviations of all time units
        """
        return [unit.abbreviation for unit in cls]


class TimeConverter:
    """Handles time unit conversions.
    
    Provides methods to convert between different time units using
    seconds as the intermediate representation.
    
    Example:
        converter = TimeConverter()
        seconds = converter.to_seconds(60, TimeUnits.MINUTES)  # 3600.0
        minutes = converter.from_seconds(3600, TimeUnits.MINUTES)  # 60.0
    """
    
    @staticmethod
    def to_seconds(value: float, units: TimeUnits) -> float:
        """Convert time value to seconds.
        
        Args:
            value: Time value in source units
            units: Source time units
        
        Returns:
            float: Time in seconds
        
        Raises:
            TypeError: If units is not TimeUnits enum
        """
        if not isinstance(units, TimeUnits):
            raise TypeError(f"Expected TimeUnits, got {type(units)}")
        return value * units.seconds_multiplier
    
    @staticmethod
    def from_seconds(value_seconds: float, target_units: TimeUnits) -> float:
        """Convert seconds to target time units.
        
        Args:
            value_seconds: Time in seconds
            target_units: Target time units
        
        Returns:
            float: Time in target units
        
        Raises:
            TypeError: If target_units is not TimeUnits enum
        """
        if not isinstance(target_units, TimeUnits):
            raise TypeError(f"Expected TimeUnits, got {type(target_units)}")
        return value_seconds / target_units.seconds_multiplier
    
    @staticmethod
    def convert(value: float, from_units: TimeUnits, to_units: TimeUnits) -> float:
        """Convert time value between any two units.
        
        Args:
            value: Time value in source units
            from_units: Source time units
            to_units: Target time units
        
        Returns:
            float: Time in target units
        """
        seconds = TimeConverter.to_seconds(value, from_units)
        return TimeConverter.from_seconds(seconds, to_units)


class TimeFormatter:
    """Handles time display formatting.
    
    Provides methods to format time values for display, auto-select
    appropriate units, and generate user-friendly strings.
    
    Example:
        formatter = TimeFormatter()
        text = formatter.format(12.5, TimeUnits.SECONDS)  # "12.5 s"
        units = formatter.auto_select_units(0.005)  # TimeUnits.MILLISECONDS
    """
    
    # Precision rules based on magnitude
    PRECISION_RULES = [
        (1.0, 3),      # < 1: 3 decimals
        (10.0, 2),     # 1-10: 2 decimals
        (100.0, 1),    # 10-100: 1 decimal
        (float('inf'), 0)  # >= 100: no decimals
    ]
    
    @staticmethod
    def format(value: float, units: TimeUnits, include_unit: bool = True) -> str:
        """Format time value for display.
        
        Automatically adjusts precision based on magnitude.
        
        Args:
            value: Time value
            units: Time units
            include_unit: Whether to include unit abbreviation
        
        Returns:
            str: Formatted string (e.g., "12.5 s" or "12.5")
        """
        # Determine precision
        abs_value = abs(value)
        precision = 0
        for threshold, prec in TimeFormatter.PRECISION_RULES:
            if abs_value < threshold:
                precision = prec
                break
        
        # Format number
        if precision == 0:
            formatted = f"{value:.0f}"
        else:
            formatted = f"{value:.{precision}f}"
        
        # Add unit if requested
        if include_unit:
            formatted += f" {units.abbreviation}"
        
        return formatted
    
    @staticmethod
    def auto_select_units(duration_seconds: float) -> TimeUnits:
        """Auto-select appropriate display units based on duration.
        
        Rules:
        - < 1 second: milliseconds
        - 1-60 seconds: seconds
        - 60-3600 seconds: minutes
        - 3600-86400 seconds: hours
        - >= 86400 seconds: days
        
        Args:
            duration_seconds: Duration in seconds
        
        Returns:
            TimeUnits: Best units for display
        """
        abs_duration = abs(duration_seconds)
        
        if abs_duration < 1.0:
            return TimeUnits.MILLISECONDS
        elif abs_duration < 60.0:
            return TimeUnits.SECONDS
        elif abs_duration < 3600.0:
            return TimeUnits.MINUTES
        elif abs_duration < 86400.0:
            return TimeUnits.HOURS
        else:
            return TimeUnits.DAYS
    
    @staticmethod
    def format_with_auto_units(value_seconds: float) -> str:
        """Format time with automatically selected units.
        
        Args:
            value_seconds: Time in seconds
        
        Returns:
            str: Formatted string with auto-selected units
        """
        units = TimeFormatter.auto_select_units(value_seconds)
        value = TimeConverter.from_seconds(value_seconds, units)
        return TimeFormatter.format(value, units)
    
    @staticmethod
    def format_progress(current_seconds: float, duration_seconds: float, 
                       units: TimeUnits) -> Tuple[str, float]:
        """Format progress display (current/duration + percentage).
        
        Args:
            current_seconds: Current time in seconds
            duration_seconds: Total duration in seconds
            units: Display units
        
        Returns:
            Tuple[str, float]: (formatted_text, fraction)
                - formatted_text: "12.5 / 60.0 s"
                - fraction: 0.0 to 1.0
        """
        current = TimeConverter.from_seconds(current_seconds, units)
        duration = TimeConverter.from_seconds(duration_seconds, units)
        
        # Format values
        current_fmt = TimeFormatter.format(current, units, include_unit=False)
        duration_fmt = TimeFormatter.format(duration, units, include_unit=False)
        
        # Calculate fraction
        fraction = min(current_seconds / duration_seconds, 1.0) if duration_seconds > 0 else 0.0
        
        # Build text
        text = f"{current_fmt} / {duration_fmt} {units.abbreviation}"
        
        return text, fraction
    
    @staticmethod
    def format_progress_with_percentage(current_seconds: float, duration_seconds: float,
                                       units: TimeUnits) -> str:
        """Format progress with percentage.
        
        Args:
            current_seconds: Current time in seconds
            duration_seconds: Total duration in seconds
            units: Display units
        
        Returns:
            str: "60% (12.5 / 60.0 s)"
        """
        text, fraction = TimeFormatter.format_progress(current_seconds, duration_seconds, units)
        percent = int(fraction * 100)
        return f"{percent}% ({text})"


class TimeValidator:
    """Validates time-related inputs.
    
    Provides validation for duration values, time steps, and other
    time-related parameters to ensure they are positive and sensible.
    """
    
    # Sanity limits (in seconds)
    MIN_DURATION = 1e-9  # 1 nanosecond
    MAX_DURATION = 3.154e9  # ~100 years
    MIN_TIME_STEP = 1e-12  # 1 picosecond
    MAX_TIME_STEP = 86400.0  # 1 day
    
    @staticmethod
    def validate_duration(duration: float, units: TimeUnits) -> Tuple[bool, str]:
        """Validate duration value.
        
        Args:
            duration: Duration value
            units: Time units
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if duration <= 0:
            return False, "Duration must be positive"
        
        duration_seconds = TimeConverter.to_seconds(duration, units)
        
        if duration_seconds < TimeValidator.MIN_DURATION:
            return False, f"Duration too small (< {TimeValidator.MIN_DURATION} s)"
        
        if duration_seconds > TimeValidator.MAX_DURATION:
            return False, f"Duration too large (> {TimeValidator.MAX_DURATION} s = ~100 years)"
        
        return True, ""
    
    @staticmethod
    def validate_time_step(dt: float) -> Tuple[bool, str]:
        """Validate time step value.
        
        Args:
            dt: Time step in seconds
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if dt <= 0:
            return False, "Time step must be positive"
        
        if dt < TimeValidator.MIN_TIME_STEP:
            return False, f"Time step too small (< {TimeValidator.MIN_TIME_STEP} s)"
        
        if dt > TimeValidator.MAX_TIME_STEP:
            return False, f"Time step too large (> {TimeValidator.MAX_TIME_STEP} s = 1 day)"
        
        return True, ""
    
    @staticmethod
    def estimate_step_count(duration_seconds: float, dt_seconds: float) -> Tuple[int, str]:
        """Estimate number of simulation steps and provide warning if needed.
        
        Args:
            duration_seconds: Duration in seconds
            dt_seconds: Time step in seconds
        
        Returns:
            Tuple[int, str]: (step_count, warning_message)
        """
        step_count = int(duration_seconds / dt_seconds) + 1
        warning = ""
        
        if step_count < 10:
            warning = "Very few steps (<10). Results may be inaccurate. Use smaller time step."
        elif step_count > 1_000_000:
            warning = f"Very large step count ({step_count:,}). Simulation may be slow. Consider larger time step."
        
        return step_count, warning


# Convenience functions for backwards compatibility
def convert_to_seconds(value: float, units_str: str) -> float:
    """Convert time value to seconds (convenience function).
    
    Args:
        value: Time value
        units_str: Units name (e.g., 'seconds', 'minutes')
    
    Returns:
        float: Time in seconds
    """
    units = TimeUnits.from_string(units_str)
    return TimeConverter.to_seconds(value, units)


def format_time_display(time_seconds: float, units_str: str) -> str:
    """Format time for display (convenience function).
    
    Args:
        time_seconds: Time in seconds
        units_str: Display units name
    
    Returns:
        str: Formatted string (value only, no unit)
    """
    units = TimeUnits.from_string(units_str)
    value = TimeConverter.from_seconds(time_seconds, units)
    return TimeFormatter.format(value, units, include_unit=False)


def get_time_units_abbreviation(units_str: str) -> str:
    """Get abbreviation for time units (convenience function).
    
    Args:
        units_str: Units name (e.g., 'seconds')
    
    Returns:
        str: Abbreviation (e.g., 's')
    """
    units = TimeUnits.from_string(units_str)
    return units.abbreviation
