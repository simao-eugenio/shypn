"""
Settings Transaction Context Manager

Provides convenient context manager for atomic settings updates.
"""

from typing import Optional
from .buffered_settings import BufferedSimulationSettings


class SettingsTransaction:
    """Context manager for atomic settings transactions.
    
    This provides a clean, Pythonic way to make multiple parameter
    changes atomically. If any exception occurs, changes are automatically
    rolled back.
    
    Usage:
        with SettingsTransaction(buffered_settings) as txn:
            txn.settings.time_scale = 10.0
            txn.settings.duration = 60.0
            txn.settings.time_units = TimeUnits.MINUTES
            # Automatically commits on success
            # Automatically rolls back on exception
    
    Alternative usage with explicit control:
        with SettingsTransaction(buffered_settings, auto_commit=False) as txn:
            txn.settings.time_scale = 10.0
            
            if some_condition:
                txn.commit()  # Explicit commit
            else:
                txn.rollback()  # Explicit rollback
    """
    
    def __init__(self, buffered_settings: BufferedSimulationSettings, auto_commit: bool = True):
        """Initialize transaction.
        
        Args:
            buffered_settings: BufferedSimulationSettings instance
            auto_commit: If True, automatically commits on successful exit
        """
        self.buffered = buffered_settings
        self.settings = buffered_settings.buffer
        self.auto_commit = auto_commit
        self._committed = False
        self._rolled_back = False
    
    def __enter__(self):
        """Enter transaction context.
        
        Returns:
            SettingsTransaction: Self for access to settings and methods
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context.
        
        Automatically commits if no exception and auto_commit=True,
        otherwise rolls back.
        
        Args:
            exc_type: Exception type (None if no exception)
            exc_val: Exception value
            exc_tb: Exception traceback
        
        Returns:
            bool: False to not suppress exceptions
        """
        if exc_type is None:
            # No exception
            if self.auto_commit and not self._committed and not self._rolled_back:
                # Try to commit
                success = self.buffered.commit()
                if not success:
                    # Commit validation failed - rollback
                    self.buffered.rollback()
        else:
            # Exception occurred - rollback if not already done
            if not self._rolled_back:
                self.buffered.rollback()
        
        return False  # Don't suppress exceptions
    
    def commit(self) -> bool:
        """Explicitly commit transaction.
        
        Returns:
            bool: True if committed successfully, False if validation failed
        """
        if self._committed:
            return True  # Already committed
        
        if self._rolled_back:
            raise RuntimeError("Cannot commit after rollback")
        
        success = self.buffered.commit()
        if success:
            self._committed = True
        return success
    
    def rollback(self):
        """Explicitly rollback transaction."""
        if self._committed:
            raise RuntimeError("Cannot rollback after commit")
        
        if not self._rolled_back:
            self.buffered.rollback()
            self._rolled_back = True
    
    @property
    def is_committed(self) -> bool:
        """Check if transaction has been committed.
        
        Returns:
            bool: True if committed
        """
        return self._committed
    
    @property
    def is_rolled_back(self) -> bool:
        """Check if transaction has been rolled back.
        
        Returns:
            bool: True if rolled back
        """
        return self._rolled_back


class SettingsTransactionBuilder:
    """Builder pattern for creating complex transactions.
    
    Provides fluent API for building transactions with validation
    and error handling.
    
    Usage:
        transaction = (SettingsTransactionBuilder(buffered_settings)
                      .set_time_scale(10.0)
                      .set_duration(60.0, TimeUnits.MINUTES)
                      .validate()
                      .execute())
        
        if transaction.is_committed:
            print("Success!")
    """
    
    def __init__(self, buffered_settings: BufferedSimulationSettings):
        """Initialize builder.
        
        Args:
            buffered_settings: BufferedSimulationSettings instance
        """
        self.buffered = buffered_settings
        self.settings = buffered_settings.buffer
        self._should_validate = True
        self._error_message: Optional[str] = None
    
    def set_time_scale(self, value: float) -> 'SettingsTransactionBuilder':
        """Set time scale.
        
        Args:
            value: Time scale factor
        
        Returns:
            SettingsTransactionBuilder: Self for chaining
        """
        try:
            self.settings.time_scale = value
            self.buffered.mark_dirty()
        except ValueError as e:
            self._error_message = str(e)
        return self
    
    def set_duration(self, duration: float, units) -> 'SettingsTransactionBuilder':
        """Set duration with units.
        
        Args:
            duration: Duration value
            units: TimeUnits enum value
        
        Returns:
            SettingsTransactionBuilder: Self for chaining
        """
        try:
            self.settings.set_duration(duration, units)
            self.buffered.mark_dirty()
        except ValueError as e:
            self._error_message = str(e)
        return self
    
    def set_dt_manual(self, value: float) -> 'SettingsTransactionBuilder':
        """Set manual time step.
        
        Args:
            value: Time step in seconds
        
        Returns:
            SettingsTransactionBuilder: Self for chaining
        """
        try:
            self.settings.dt_manual = value
            self.settings.dt_auto = False
            self.buffered.mark_dirty()
        except ValueError as e:
            self._error_message = str(e)
        return self
    
    def set_dt_auto(self, enabled: bool = True) -> 'SettingsTransactionBuilder':
        """Enable/disable auto time step.
        
        Args:
            enabled: True to enable auto dt
        
        Returns:
            SettingsTransactionBuilder: Self for chaining
        """
        self.settings.dt_auto = enabled
        self.buffered.mark_dirty()
        return self
    
    def validate(self) -> 'SettingsTransactionBuilder':
        """Mark that validation should occur before commit.
        
        Returns:
            SettingsTransactionBuilder: Self for chaining
        """
        self._should_validate = True
        return self
    
    def execute(self) -> SettingsTransaction:
        """Execute the transaction.
        
        Returns:
            SettingsTransaction: Transaction object (may be committed or rolled back)
        """
        if self._error_message:
            # Validation error occurred during building
            self.buffered.rollback()
            txn = SettingsTransaction(self.buffered, auto_commit=False)
            txn._rolled_back = True
            return txn
        
        # Try to commit
        if self._should_validate:
            success = self.buffered.commit()
            txn = SettingsTransaction(self.buffered, auto_commit=False)
            if success:
                txn._committed = True
            else:
                txn._rolled_back = True
            return txn
        else:
            # Return uncommitted transaction
            return SettingsTransaction(self.buffered, auto_commit=False)
