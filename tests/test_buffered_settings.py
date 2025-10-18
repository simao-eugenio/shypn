"""
Unit Tests for Buffered Simulation Settings

Tests atomic parameter updates and transaction safety.
"""

import unittest
from unittest.mock import Mock
from shypn.engine.simulation.settings import SimulationSettings
from shypn.engine.simulation.buffered import (
    BufferedSimulationSettings,
    SettingsTransaction,
    ValidationError
)
from shypn.utils.time_utils import TimeUnits


class TestBufferedSimulationSettings(unittest.TestCase):
    """Test BufferedSimulationSettings."""
    
    def setUp(self):
        """Create fresh settings for each test."""
        self.live_settings = SimulationSettings()
        self.buffered = BufferedSimulationSettings(self.live_settings)
    
    def test_buffer_isolation(self):
        """Test that buffer changes don't affect live settings."""
        # Change buffer
        self.buffered.buffer.time_scale = 10.0
        self.buffered.mark_dirty()
        
        # Live unchanged
        self.assertEqual(self.live_settings.time_scale, 1.0)
        self.assertTrue(self.buffered.is_dirty)
        
        # Commit
        success = self.buffered.commit()
        
        # Now live updated
        self.assertTrue(success)
        self.assertEqual(self.live_settings.time_scale, 10.0)
        self.assertFalse(self.buffered.is_dirty)
    
    def test_rollback_discards_changes(self):
        """Test that rollback discards buffer changes."""
        # Change buffer
        self.buffered.buffer.time_scale = 100.0
        self.buffered.mark_dirty()
        
        # Rollback
        self.buffered.rollback()
        
        # Live unchanged, dirty flag cleared
        self.assertEqual(self.live_settings.time_scale, 1.0)
        self.assertFalse(self.buffered.is_dirty)
    
    def test_validation_prevents_invalid_commit(self):
        """Test that invalid buffer cannot be committed."""
        # Set invalid value (negative time_scale)
        try:
            self.buffered.buffer.time_scale = -5.0
            self.buffered.mark_dirty()
            
            # Try to commit
            success = self.buffered.commit()
            
            # Should fail validation
            self.assertFalse(success)
            # Live settings unchanged
            self.assertEqual(self.live_settings.time_scale, 1.0)
        except ValueError:
            # Some validations raise immediately in setter
            self.assertEqual(self.live_settings.time_scale, 1.0)
    
    def test_atomic_commit_multiple_properties(self):
        """Test that multi-property changes are atomic."""
        # Change multiple properties
        self.buffered.buffer.duration = 100.0
        self.buffered.buffer.time_units = TimeUnits.MINUTES
        self.buffered.buffer.time_scale = 60.0
        self.buffered.mark_dirty()
        
        # Commit atomically
        success = self.buffered.commit()
        
        self.assertTrue(success)
        self.assertEqual(self.live_settings.duration, 100.0)
        self.assertEqual(self.live_settings.time_units, TimeUnits.MINUTES)
        self.assertEqual(self.live_settings.time_scale, 60.0)
    
    def test_no_commit_when_not_dirty(self):
        """Test that commit does nothing when no changes."""
        initial_time_scale = self.live_settings.time_scale
        
        # Commit without changes
        success = self.buffered.commit()
        
        self.assertTrue(success)
        self.assertEqual(self.live_settings.time_scale, initial_time_scale)
    
    def test_buffer_created_on_demand(self):
        """Test that buffer is created lazily."""
        # Initially no buffer
        self.assertIsNone(self.buffered._buffer)
        
        # Access creates buffer
        buffer = self.buffered.buffer
        self.assertIsNotNone(buffer)
        self.assertIsInstance(buffer, SimulationSettings)
    
    def test_commit_clears_buffer(self):
        """Test that successful commit clears buffer."""
        # Change and commit
        self.buffered.buffer.time_scale = 5.0
        self.buffered.mark_dirty()
        self.buffered.commit()
        
        # Buffer cleared
        self.assertIsNone(self.buffered._buffer)
        self.assertFalse(self.buffered.is_dirty)
    
    def test_excessive_step_count_validation(self):
        """Test that excessive step counts are caught."""
        # Try to create a scenario with too many steps
        self.buffered.buffer.duration = 10000.0  # 10000 seconds
        self.buffered.buffer.dt_manual = 0.001   # 1ms steps
        self.buffered.buffer.dt_auto = False
        self.buffered.mark_dirty()
        
        # Should fail validation (10M steps > 1M limit)
        success = self.buffered.commit()
        self.assertFalse(success)
        
        # Live settings unchanged
        self.assertIsNone(self.live_settings.duration)


class TestSettingsTransaction(unittest.TestCase):
    """Test SettingsTransaction context manager."""
    
    def setUp(self):
        """Create fresh settings for each test."""
        self.live_settings = SimulationSettings()
        self.buffered = BufferedSimulationSettings(self.live_settings)
    
    def test_auto_commit_on_success(self):
        """Test that transaction auto-commits on successful exit."""
        txn = None
        with SettingsTransaction(self.buffered) as txn_context:
            txn = txn_context
            txn.settings.time_scale = 10.0
            self.buffered.mark_dirty()
        
        # Automatically committed
        self.assertEqual(self.live_settings.time_scale, 10.0)
        # Note: txn flags are checked in __exit__, so we check the result
        self.assertFalse(self.buffered.is_dirty)  # Successfully committed
    
    def test_auto_rollback_on_exception(self):
        """Test that transaction auto-rolls-back on exception."""
        txn = None
        try:
            with SettingsTransaction(self.buffered) as txn_context:
                txn = txn_context
                txn.settings.time_scale = 10.0
                self.buffered.mark_dirty()
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Automatically rolled back
        self.assertEqual(self.live_settings.time_scale, 1.0)
        # Check that changes were discarded
        self.assertFalse(self.buffered.is_dirty)
    
    def test_manual_commit(self):
        """Test explicit commit in transaction."""
        with SettingsTransaction(self.buffered, auto_commit=False) as txn:
            txn.settings.time_scale = 15.0
            self.buffered.mark_dirty()
            
            # Explicit commit
            success = txn.commit()
            self.assertTrue(success)
        
        self.assertEqual(self.live_settings.time_scale, 15.0)
        self.assertTrue(txn.is_committed)
    
    def test_manual_rollback(self):
        """Test explicit rollback in transaction."""
        with SettingsTransaction(self.buffered, auto_commit=False) as txn:
            txn.settings.time_scale = 20.0
            self.buffered.mark_dirty()
            
            # Explicit rollback
            txn.rollback()
        
        self.assertEqual(self.live_settings.time_scale, 1.0)
        self.assertTrue(txn.is_rolled_back)
    
    def test_cannot_commit_after_rollback(self):
        """Test that commit after rollback raises error."""
        with self.assertRaises(RuntimeError):
            with SettingsTransaction(self.buffered, auto_commit=False) as txn:
                txn.settings.time_scale = 25.0
                self.buffered.mark_dirty()
                txn.rollback()
                txn.commit()  # Should raise
    
    def test_cannot_rollback_after_commit(self):
        """Test that rollback after commit raises error."""
        with self.assertRaises(RuntimeError):
            with SettingsTransaction(self.buffered, auto_commit=False) as txn:
                txn.settings.time_scale = 30.0
                self.buffered.mark_dirty()
                txn.commit()
                txn.rollback()  # Should raise


class TestParameterRaceConditionPrevention(unittest.TestCase):
    """Test that rapid parameter changes don't corrupt simulation."""
    
    def setUp(self):
        """Create fresh settings for each test."""
        self.live_settings = SimulationSettings()
        self.buffered = BufferedSimulationSettings(self.live_settings)
    
    def test_rapid_changes_buffered(self):
        """Test that rapid UI changes stay in buffer until commit."""
        # Simulate rapid slider drag (100 changes in quick succession)
        for i in range(1, 101):  # Start from 1 to avoid 0 (invalid for time_scale)
            self.buffered.buffer.time_scale = i / 10.0
            self.buffered.mark_dirty()
        
        # Live settings still unchanged
        self.assertEqual(self.live_settings.time_scale, 1.0)
        
        # Only final value committed
        success = self.buffered.commit()
        self.assertTrue(success)
        self.assertEqual(self.live_settings.time_scale, 10.0)
    
    def test_commit_failure_leaves_live_unchanged(self):
        """Test that failed commit doesn't partially apply changes."""
        initial_duration = self.live_settings.duration
        initial_time_scale = self.live_settings.time_scale
        
        # Make valid and invalid changes
        self.buffered.buffer.duration = 100.0
        # Create scenario that will fail validation
        self.buffered.buffer.dt_manual = 0.000001  # Too small
        self.buffered.buffer.dt_auto = False
        self.buffered.mark_dirty()
        
        # Try to commit (should fail)
        success = self.buffered.commit()
        
        # Entire commit failed - live settings completely unchanged
        self.assertFalse(success)
        self.assertEqual(self.live_settings.duration, initial_duration)
        self.assertEqual(self.live_settings.time_scale, initial_time_scale)


if __name__ == '__main__':
    unittest.main()
