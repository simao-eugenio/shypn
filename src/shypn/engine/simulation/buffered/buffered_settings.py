"""
Buffered Simulation Settings

Provides transaction-safe wrapper for SimulationSettings with:
- Write buffering
- Atomic commits
- Validation before apply
- Rollback support
"""

import threading
from typing import Optional, Dict, Any, List
from shypn.engine.simulation.settings import SimulationSettings
from shypn.utils.time_utils import TimeUnits, TimeValidator
from .base import ValidationError, ChangeListener


class BufferedSimulationSettings:
    """Transaction-safe wrapper for SimulationSettings.
    
    This class prevents race conditions when users rapidly change
    parameters during simulation. Changes are buffered and only
    applied atomically on explicit commit.
    
    Key Features:
    - Write buffering: UI changes write to buffer, not live settings
    - Explicit commit: Changes applied only when commit() called
    - Validation before commit: All validation before any change
    - Atomic updates: All properties updated together or not at all
    - Thread-safe: Lock protects concurrent access
    - Rollback support: Can undo uncommitted changes
    
    Usage Pattern:
        # Create buffered wrapper
        buffered = BufferedSimulationSettings(controller.settings)
        
        # UI changes write to buffer (not live)
        buffered.buffer.time_scale = 10.0
        buffered.buffer.duration = 60.0
        buffered.mark_dirty()
        
        # Commit atomically (validated, all-or-nothing)
        if buffered.commit():
        else:
    
    Thread Safety:
        All public methods are thread-safe. The commit operation
        is atomic - either all changes apply or none do.
    """
    
    def __init__(self, live_settings: SimulationSettings):
        """Initialize buffered settings.
        
        Args:
            live_settings: The actual SimulationSettings used by simulation engine
        """
        self._live = live_settings
        self._buffer: Optional[SimulationSettings] = None
        self._lock = threading.Lock()
        self._dirty = False
        self._listeners: List[ChangeListener] = []
        
        # Track changes for notification
        self._pending_changes: Dict[str, tuple[Any, Any]] = {}
    
    # ========== Properties ==========
    
    @property
    def live(self) -> SimulationSettings:
        """Get live settings (currently used by simulation).
        
        WARNING: Direct modifications to live settings bypass buffering!
        UI code should use .buffer property instead.
        
        Returns:
            SimulationSettings: Live settings object
        """
        return self._live
    
    @property
    def buffer(self) -> SimulationSettings:
        """Get buffer for editing (changes not yet committed).
        
        This is what UI code should modify. Changes accumulate in
        the buffer until commit() is called.
        
        Returns:
            SimulationSettings: Buffered copy of settings
        """
        if self._buffer is None:
            self._buffer = self._clone_settings(self._live)
        return self._buffer
    
    @property
    def is_dirty(self) -> bool:
        """Check if buffer has uncommitted changes.
        
        Returns:
            bool: True if changes pending, False otherwise
        """
        return self._dirty
    
    # ========== State Management ==========
    
    def mark_dirty(self):
        """Mark buffer as having uncommitted changes.
        
        UI code should call this after modifying buffer properties.
        """
        self._dirty = True
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes.
        
        Alias for is_dirty property.
        
        Returns:
            bool: True if changes pending
        """
        return self._dirty
    
    # ========== Commit/Rollback ==========
    
    def commit(self) -> bool:
        """Atomically commit buffered changes to live settings.
        
        Process:
        1. Acquire lock (thread-safe)
        2. Validate ALL buffered values
        3. If validation passes, apply ALL changes atomically
        4. If validation fails, rollback (no changes applied)
        5. Notify listeners
        6. Release lock
        
        Returns:
            bool: True if committed successfully, False if validation failed
        """
        if not self._dirty:
            return True  # No changes to commit
        
        with self._lock:
            try:
                # Step 1: Validate ALL buffered values
                self._validate_buffer()
                
                # Step 2: Track what's changing
                self._track_changes()
                
                # Step 3: Apply atomically (all or nothing)
                self._apply_buffer_to_live()
                
                # Step 4: Notify listeners of successful commit
                self._notify_commit()
                
                # Step 5: Clear buffer
                self._buffer = None
                self._dirty = False
                self._pending_changes.clear()
                
                return True
                
            except (ValueError, ValidationError) as e:
                # Validation failed - rollback
                return False
    
    def rollback(self):
        """Discard uncommitted changes, restore buffer to live values.
        
        This resets the buffer to match current live settings,
        effectively undoing all pending changes.
        """
        with self._lock:
            # Track changes for notification
            if self._dirty:
                self._track_changes()
                self._notify_rollback()
            
            # Clear buffer and dirty flag
            self._buffer = None
            self._dirty = False
            self._pending_changes.clear()
    
    # ========== Internal Methods ==========
    
    def _clone_settings(self, settings: SimulationSettings) -> SimulationSettings:
        """Create a deep copy of settings.
        
        Args:
            settings: Settings to clone
        
        Returns:
            SimulationSettings: Independent copy
        """
        clone = SimulationSettings()
        clone.time_units = settings.time_units
        clone.duration = settings.duration
        clone.dt_auto = settings.dt_auto
        clone.dt_manual = settings.dt_manual
        clone.time_scale = settings.time_scale
        return clone
    
    def _validate_buffer(self):
        """Validate all buffered values.
        
        Performs two types of validation:
        1. Property validation: Each property's setter validation
        2. Cross-validation: Constraints involving multiple properties
        
        Raises:
            ValueError: If any buffered value is invalid
            ValidationError: If cross-constraints violated
        """
        # Property validation happens automatically via setters
        # Access all properties to trigger validation
        _ = self._buffer.time_units
        _ = self._buffer.duration
        _ = self._buffer.dt_auto
        _ = self._buffer.dt_manual
        _ = self._buffer.time_scale
        
        # Cross-validation: Check step count
        if self._buffer.duration is not None:
            dt = self._buffer.get_effective_dt()
            duration_seconds = self._buffer.get_duration_seconds()
            
            if duration_seconds is not None:
                step_count = int(duration_seconds / dt)
                
                # Prevent excessive step counts
                if step_count > 1_000_000:
                    raise ValidationError(
                        f"Duration {self._buffer.duration} {self._buffer.time_units.full_name} "
                        f"with dt={dt}s would require {step_count:,} steps. "
                        f"Maximum allowed: 1,000,000 steps. "
                        f"Increase time step or reduce duration."
                    )
                
                # Warning for very small step counts
                if step_count < 10:
                    pass  # Could log warning if needed
    
    def _track_changes(self):
        """Track what properties have changed for notification."""
        if self._buffer is None:
            return
        
        self._pending_changes.clear()
        
        # Compare buffer to live settings
        if self._buffer.time_units != self._live.time_units:
            self._pending_changes['time_units'] = (
                self._live.time_units,
                self._buffer.time_units
            )
        
        if self._buffer.duration != self._live.duration:
            self._pending_changes['duration'] = (
                self._live.duration,
                self._buffer.duration
            )
        
        if self._buffer.dt_auto != self._live.dt_auto:
            self._pending_changes['dt_auto'] = (
                self._live.dt_auto,
                self._buffer.dt_auto
            )
        
        if self._buffer.dt_manual != self._live.dt_manual:
            self._pending_changes['dt_manual'] = (
                self._live.dt_manual,
                self._buffer.dt_manual
            )
        
        if self._buffer.time_scale != self._live.time_scale:
            self._pending_changes['time_scale'] = (
                self._live.time_scale,
                self._buffer.time_scale
            )
    
    def _apply_buffer_to_live(self):
        """Apply buffered values to live settings atomically.
        
        This is the critical section where changes are actually applied.
        All validation has already passed at this point.
        """
        # All validation passed - safe to apply
        self._live.time_units = self._buffer.time_units
        self._live.duration = self._buffer.duration
        self._live.dt_auto = self._buffer.dt_auto
        self._live.dt_manual = self._buffer.dt_manual
        self._live.time_scale = self._buffer.time_scale
    
    # ========== Observer Pattern ==========
    
    def add_listener(self, listener: ChangeListener):
        """Register a listener for parameter changes.
        
        Args:
            listener: Listener implementing ChangeListener interface
        """
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: ChangeListener):
        """Unregister a listener.
        
        Args:
            listener: Listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_commit(self):
        """Notify listeners that changes were committed."""
        for listener in self._listeners:
            try:
                listener.on_changes_committed(self._pending_changes.copy())
            except Exception:
                pass
    
    def _notify_rollback(self):
        """Notify listeners that changes were rolled back."""
        for listener in self._listeners:
            try:
                listener.on_changes_rolled_back(self._pending_changes.copy())
            except Exception:
                pass
    
    # ========== String Representation ==========
    
    def __repr__(self) -> str:
        """Get debug representation."""
        status = "dirty" if self._dirty else "clean"
        changes = len(self._pending_changes)
        return f"BufferedSimulationSettings(status={status}, pending_changes={changes})"
    
    def __str__(self) -> str:
        """Get user-friendly string representation."""
        if not self._dirty:
            return "No pending changes"
        
        if self._buffer:
            changes = []
            if self._buffer.time_units != self._live.time_units:
                changes.append(f"time_units: {self._live.time_units} → {self._buffer.time_units}")
            if self._buffer.duration != self._live.duration:
                changes.append(f"duration: {self._live.duration} → {self._buffer.duration}")
            if self._buffer.time_scale != self._live.time_scale:
                changes.append(f"time_scale: {self._live.time_scale} → {self._buffer.time_scale}")
            
            return f"Pending changes: {', '.join(changes)}"
        
        return "Buffer dirty but no specific changes tracked"
