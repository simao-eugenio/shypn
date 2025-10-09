"""
Test Suite for Simulation Timing System

Tests the time abstraction system including:
- TimeUnits enum
- TimeConverter class
- TimeFormatter class
- TimeValidator class
- SimulationSettings class
- SimulationController integration
"""
import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.utils.time_utils import (
    TimeUnits,
    TimeConverter,
    TimeFormatter,
    TimeValidator,
    convert_to_seconds,
    format_time_display
)
from shypn.engine.simulation.settings import (
    SimulationSettings,
    SimulationSettingsBuilder
)


class TestTimeUnits(unittest.TestCase):
    """Test TimeUnits enum."""
    
    def test_enum_values(self):
        """Test that all expected time units exist."""
        self.assertEqual(TimeUnits.MILLISECONDS.full_name, 'milliseconds')
        self.assertEqual(TimeUnits.SECONDS.full_name, 'seconds')
        self.assertEqual(TimeUnits.MINUTES.full_name, 'minutes')
        self.assertEqual(TimeUnits.HOURS.full_name, 'hours')
        self.assertEqual(TimeUnits.DAYS.full_name, 'days')
    
    def test_abbreviations(self):
        """Test time unit abbreviations."""
        self.assertEqual(TimeUnits.MILLISECONDS.abbreviation, 'ms')
        self.assertEqual(TimeUnits.SECONDS.abbreviation, 's')
        self.assertEqual(TimeUnits.MINUTES.abbreviation, 'min')
        self.assertEqual(TimeUnits.HOURS.abbreviation, 'hr')
        self.assertEqual(TimeUnits.DAYS.abbreviation, 'd')
    
    def test_multipliers(self):
        """Test seconds multipliers."""
        self.assertEqual(TimeUnits.MILLISECONDS.seconds_multiplier, 0.001)
        self.assertEqual(TimeUnits.SECONDS.seconds_multiplier, 1.0)
        self.assertEqual(TimeUnits.MINUTES.seconds_multiplier, 60.0)
        self.assertEqual(TimeUnits.HOURS.seconds_multiplier, 3600.0)
        self.assertEqual(TimeUnits.DAYS.seconds_multiplier, 86400.0)
    
    def test_from_string_full_name(self):
        """Test getting unit from full name."""
        self.assertEqual(TimeUnits.from_string('seconds'), TimeUnits.SECONDS)
        self.assertEqual(TimeUnits.from_string('minutes'), TimeUnits.MINUTES)
        self.assertEqual(TimeUnits.from_string('hours'), TimeUnits.HOURS)
    
    def test_from_string_abbreviation(self):
        """Test getting unit from abbreviation."""
        self.assertEqual(TimeUnits.from_string('ms'), TimeUnits.MILLISECONDS)
        self.assertEqual(TimeUnits.from_string('s'), TimeUnits.SECONDS)
        self.assertEqual(TimeUnits.from_string('min'), TimeUnits.MINUTES)
    
    def test_from_string_case_insensitive(self):
        """Test case-insensitive string matching."""
        self.assertEqual(TimeUnits.from_string('SECONDS'), TimeUnits.SECONDS)
        self.assertEqual(TimeUnits.from_string('Minutes'), TimeUnits.MINUTES)
        self.assertEqual(TimeUnits.from_string('MS'), TimeUnits.MILLISECONDS)
    
    def test_from_string_invalid(self):
        """Test error on invalid string."""
        with self.assertRaises(ValueError):
            TimeUnits.from_string('invalid')


class TestTimeConverter(unittest.TestCase):
    """Test TimeConverter class."""
    
    def test_to_seconds_milliseconds(self):
        """Test converting milliseconds to seconds."""
        result = TimeConverter.to_seconds(1000, TimeUnits.MILLISECONDS)
        self.assertEqual(result, 1.0)
    
    def test_to_seconds_seconds(self):
        """Test converting seconds to seconds (identity)."""
        result = TimeConverter.to_seconds(10, TimeUnits.SECONDS)
        self.assertEqual(result, 10.0)
    
    def test_to_seconds_minutes(self):
        """Test converting minutes to seconds."""
        result = TimeConverter.to_seconds(2, TimeUnits.MINUTES)
        self.assertEqual(result, 120.0)
    
    def test_to_seconds_hours(self):
        """Test converting hours to seconds."""
        result = TimeConverter.to_seconds(1, TimeUnits.HOURS)
        self.assertEqual(result, 3600.0)
    
    def test_to_seconds_days(self):
        """Test converting days to seconds."""
        result = TimeConverter.to_seconds(1, TimeUnits.DAYS)
        self.assertEqual(result, 86400.0)
    
    def test_from_seconds_milliseconds(self):
        """Test converting seconds to milliseconds."""
        result = TimeConverter.from_seconds(1.0, TimeUnits.MILLISECONDS)
        self.assertEqual(result, 1000.0)
    
    def test_from_seconds_minutes(self):
        """Test converting seconds to minutes."""
        result = TimeConverter.from_seconds(120.0, TimeUnits.MINUTES)
        self.assertEqual(result, 2.0)
    
    def test_from_seconds_hours(self):
        """Test converting seconds to hours."""
        result = TimeConverter.from_seconds(7200.0, TimeUnits.HOURS)
        self.assertEqual(result, 2.0)
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        # Test convert_to_seconds (takes string units)
        result = convert_to_seconds(10, 'minutes')
        self.assertEqual(result, 600.0)
        
        # Test format_time_display - 2 minutes is in [1, 10) range = 2 decimals
        result = format_time_display(120.0, 'minutes')
        self.assertEqual(result, '2.00')


class TestTimeFormatter(unittest.TestCase):
    """Test TimeFormatter class."""
    
    def test_format_seconds(self):
        """Test formatting seconds."""
        result = TimeFormatter.format(10.5, TimeUnits.SECONDS, include_unit=True)
        # 10.5 is in range [10, 100) so gets 1 decimal place
        self.assertEqual(result, '10.5 s')
    
    def test_format_without_unit(self):
        """Test formatting without unit label."""
        result = TimeFormatter.format(10.5, TimeUnits.SECONDS, include_unit=False)
        self.assertEqual(result, '10.5')
    
    def test_format_large_values(self):
        """Test formatting large values (no decimals)."""
        result = TimeFormatter.format(1000, TimeUnits.SECONDS, include_unit=True)
        self.assertEqual(result, '1000 s')
    
    def test_format_small_values(self):
        """Test formatting small values (3 decimals)."""
        result = TimeFormatter.format(0.123, TimeUnits.SECONDS, include_unit=True)
        self.assertEqual(result, '0.123 s')
    
    def test_auto_select_units_small(self):
        """Test auto-selecting units for small durations."""
        unit = TimeFormatter.auto_select_units(0.5)
        self.assertEqual(unit, TimeUnits.MILLISECONDS)
    
    def test_auto_select_units_medium(self):
        """Test auto-selecting units for medium durations."""
        unit = TimeFormatter.auto_select_units(120)  # 2 minutes
        self.assertEqual(unit, TimeUnits.MINUTES)
    
    def test_auto_select_units_large(self):
        """Test auto-selecting units for large durations."""
        unit = TimeFormatter.auto_select_units(7200)  # 2 hours
        self.assertEqual(unit, TimeUnits.HOURS)
    
    def test_format_progress(self):
        """Test formatting progress display."""
        text, fraction = TimeFormatter.format_progress(
            30,  # current_seconds (positional)
            60,  # duration_seconds (positional)
            TimeUnits.SECONDS  # units (positional)
        )
        self.assertIn('30', text)
        self.assertIn('60', text)
        self.assertEqual(fraction, 0.5)
    
    def test_format_progress_zero_duration(self):
        """Test progress formatting with zero duration."""
        text, fraction = TimeFormatter.format_progress(
            10,  # current_seconds
            0,   # duration_seconds (zero)
            TimeUnits.SECONDS
        )
        self.assertEqual(fraction, 0.0)


class TestTimeValidator(unittest.TestCase):
    """Test TimeValidator class."""
    
    def test_validate_valid_duration(self):
        """Test validating a valid duration."""
        is_valid, error = TimeValidator.validate_duration(60, TimeUnits.SECONDS)
        self.assertTrue(is_valid)
        # Error message may be empty string or None
        self.assertIn(error, [None, ''])
    
    def test_validate_negative_duration(self):
        """Test rejecting negative duration."""
        is_valid, error = TimeValidator.validate_duration(-10, TimeUnits.SECONDS)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_zero_duration(self):
        """Test rejecting zero duration."""
        is_valid, error = TimeValidator.validate_duration(0, TimeUnits.SECONDS)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_too_small_duration(self):
        """Test rejecting duration below minimum (1 nanosecond)."""
        is_valid, error = TimeValidator.validate_duration(0.0000001, TimeUnits.MILLISECONDS)
        self.assertFalse(is_valid)
        self.assertIn('too small', error.lower())
    
    def test_validate_too_large_duration(self):
        """Test rejecting duration above maximum (100 years)."""
        is_valid, error = TimeValidator.validate_duration(200, TimeUnits.DAYS)
        # This should be valid (200 days < 100 years)
        self.assertTrue(is_valid)
        
        # But 100000 days should be invalid
        is_valid, error = TimeValidator.validate_duration(100000, TimeUnits.DAYS)
        self.assertFalse(is_valid)
        self.assertIn('too large', error.lower())
    
    def test_estimate_step_count(self):
        """Test estimating step count."""
        count, warning = TimeValidator.estimate_step_count(60.0, 0.1)
        # Allow for off-by-one due to rounding (600 or 601 steps)
        self.assertIn(count, [600, 601])
        # Warning may be empty string or None
        self.assertIn(warning, [None, ''])
    
    def test_estimate_step_count_warning(self):
        """Test warning on very large step count."""
        count, warning = TimeValidator.estimate_step_count(100000.0, 0.001)
        self.assertGreater(count, 100000)
        self.assertIsNotNone(warning)


class TestSimulationSettings(unittest.TestCase):
    """Test SimulationSettings class."""
    
    def test_initialization_defaults(self):
        """Test default initialization."""
        settings = SimulationSettings()
        self.assertEqual(settings.time_units, TimeUnits.SECONDS)
        self.assertIsNone(settings.duration)
        self.assertTrue(settings.dt_auto)
        self.assertEqual(settings.dt_manual, 0.1)
        self.assertEqual(settings.time_scale, 1.0)
    
    def test_set_duration(self):
        """Test setting duration."""
        settings = SimulationSettings()
        settings.set_duration(60, TimeUnits.SECONDS)
        self.assertEqual(settings.duration, 60)
        self.assertEqual(settings.time_units, TimeUnits.SECONDS)
    
    def test_set_duration_validation(self):
        """Test duration validation."""
        settings = SimulationSettings()
        with self.assertRaises(ValueError):
            settings.set_duration(-10, TimeUnits.SECONDS)
    
    def test_get_duration_seconds(self):
        """Test getting duration in seconds."""
        settings = SimulationSettings()
        settings.set_duration(2, TimeUnits.MINUTES)
        self.assertEqual(settings.get_duration_seconds(), 120.0)
    
    def test_get_effective_dt_auto(self):
        """Test auto dt calculation."""
        settings = SimulationSettings()
        settings.set_duration(100, TimeUnits.SECONDS)
        settings.dt_auto = True
        dt = settings.get_effective_dt()
        self.assertEqual(dt, 0.1)  # 100 / 1000 = 0.1
    
    def test_get_effective_dt_manual(self):
        """Test manual dt."""
        settings = SimulationSettings()
        settings.dt_auto = False
        settings.dt_manual = 0.05
        dt = settings.get_effective_dt()
        self.assertEqual(dt, 0.05)
    
    def test_get_effective_dt_no_duration(self):
        """Test dt when no duration set."""
        settings = SimulationSettings()
        settings.dt_auto = True
        settings.duration = None
        dt = settings.get_effective_dt()
        self.assertEqual(dt, 0.1)  # Falls back to default
    
    def test_calculate_progress(self):
        """Test progress calculation."""
        settings = SimulationSettings()
        settings.set_duration(100, TimeUnits.SECONDS)
        
        progress = settings.calculate_progress(0)
        self.assertEqual(progress, 0.0)
        
        progress = settings.calculate_progress(50)
        self.assertEqual(progress, 0.5)
        
        progress = settings.calculate_progress(100)
        self.assertEqual(progress, 1.0)
    
    def test_calculate_progress_overflow(self):
        """Test progress clamped at 1.0."""
        settings = SimulationSettings()
        settings.set_duration(100, TimeUnits.SECONDS)
        progress = settings.calculate_progress(150)
        self.assertEqual(progress, 1.0)
    
    def test_is_complete(self):
        """Test completion check."""
        settings = SimulationSettings()
        settings.set_duration(100, TimeUnits.SECONDS)
        
        self.assertFalse(settings.is_complete(50))
        self.assertTrue(settings.is_complete(100))
        self.assertTrue(settings.is_complete(150))
    
    def test_estimate_step_count(self):
        """Test step count estimation."""
        settings = SimulationSettings()
        settings.set_duration(100, TimeUnits.SECONDS)
        settings.dt_auto = True
        
        count = settings.estimate_step_count()
        # Allow for off-by-one due to rounding (1000 or 1001 steps)
        self.assertIn(count, [1000, 1001])
    
    def test_to_dict(self):
        """Test serialization to dict."""
        settings = SimulationSettings()
        settings.set_duration(60, TimeUnits.SECONDS)
        settings.dt_manual = 0.05
        settings.time_scale = 2.0
        
        data = settings.to_dict()
        self.assertEqual(data['time_units'], 'seconds')
        self.assertEqual(data['duration'], 60)
        self.assertEqual(data['dt_manual'], 0.05)
        self.assertEqual(data['time_scale'], 2.0)
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            'time_units': 'minutes',
            'duration': 5,
            'dt_auto': False,
            'dt_manual': 0.02,
            'time_scale': 1.5
        }
        
        settings = SimulationSettings.from_dict(data)
        self.assertEqual(settings.time_units, TimeUnits.MINUTES)
        self.assertEqual(settings.duration, 5)
        self.assertFalse(settings.dt_auto)
        self.assertEqual(settings.dt_manual, 0.02)
        self.assertEqual(settings.time_scale, 1.5)


class TestSimulationSettingsBuilder(unittest.TestCase):
    """Test SimulationSettingsBuilder class."""
    
    def test_builder_pattern(self):
        """Test fluent builder API."""
        settings = (SimulationSettingsBuilder()
            .with_duration(60, TimeUnits.SECONDS)
            .with_auto_dt()
            .with_time_scale(2.0)
            .build())
        
        self.assertEqual(settings.duration, 60)
        self.assertEqual(settings.time_units, TimeUnits.SECONDS)
        self.assertTrue(settings.dt_auto)
        self.assertEqual(settings.time_scale, 2.0)
    
    def test_builder_manual_dt(self):
        """Test builder with manual dt."""
        settings = (SimulationSettingsBuilder()
            .with_duration(100, TimeUnits.MILLISECONDS)
            .with_manual_dt(0.001)
            .build())
        
        self.assertFalse(settings.dt_auto)
        self.assertEqual(settings.dt_manual, 0.001)


class TestSimulationControllerIntegration(unittest.TestCase):
    """Test SimulationController integration with settings.
    
    Note: These tests require a mock model since we don't have
    a full Petri net model in the test environment.
    """
    
    def test_settings_composition(self):
        """Test that controller has settings object."""
        # This would require mocking PetriNetModel
        # For now, just verify the module can be imported
        from shypn.engine.simulation import SimulationController
        self.assertTrue(hasattr(SimulationController, '__init__'))


def run_tests():
    """Run all tests and print results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
