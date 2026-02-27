"""
Buffered Simulation Settings

Provides transaction-safe wrapper for SimulationSettings with:
- Write buffering
- Atomic commits
- Validation before apply
- Rollback support
- Atomic disk persistence (settings survive interrupted sessions)
"""

import os
import json
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from shypn.engine.simulation.settings import SimulationSettings
from shypn.utils.time_utils import TimeUnits, TimeValidator
from .base import ValidationError, ChangeListener

logger = logging.getLogger(__name__)


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
            pass
        else:
            pass
    
    Thread Safety:
        All public methods are thread-safe. The commit operation
        is atomic - either all changes apply or none do.
    """
    
    def __init__(self, live_settings: SimulationSettings, model: Any=None):
        """Initialize buffered settings.
        
        Args:
            live_settings: The actual SimulationSettings used by simulation engine
            model: Optional DocumentModel (for persistence filepath)
        """
        self._live = live_settings
        self._buffer: Optional[SimulationSettings] = None
        self._lock = threading.Lock()
        self._dirty = False
        self._listeners: List[ChangeListener] = []
        
        # Track changes for notification
        self._pending_changes: Dict[str, tuple[Any, Any]] = {}
        
        # Model reference for persistence (weak coupling - only needs filepath)
        self._model = model
        
        # Load persisted settings if available
        self._load_from_disk()
    
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
    
    def mark_dirty(self) -> None:
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
                
                # Step 5: Persist to disk atomically
                self._save_to_disk()
                
                # Step 6: Clear buffer
                self._buffer = None
                self._dirty = False
                self._pending_changes.clear()
                
                return True
                
            except (ValueError, ValidationError) as e:
                # Validation failed - rollback
                return False
    
    def rollback(self) -> None:
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
        # τ-Leaping settings
        clone.use_tau_leaping = settings.use_tau_leaping
        clone.tau_epsilon = settings.tau_epsilon
        clone.critical_threshold = settings.critical_threshold
        clone.max_tau = settings.max_tau
        clone.min_tau = settings.min_tau
        clone.use_parallel_stochastic = settings.use_parallel_stochastic
        return clone
    
    def _validate_buffer(self) -> None:
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
        
        # τ-Leaping property validation
        _ = self._buffer.use_tau_leaping
        _ = self._buffer.tau_epsilon
        _ = self._buffer.critical_threshold
        _ = self._buffer.max_tau
        _ = self._buffer.min_tau
        _ = self._buffer.use_parallel_stochastic
        
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
    
    def _track_changes(self) -> None:
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
    
    def _apply_buffer_to_live(self) -> None:
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
        # τ-Leaping settings
        self._live.use_tau_leaping = self._buffer.use_tau_leaping
        self._live.tau_epsilon = self._buffer.tau_epsilon
        self._live.critical_threshold = self._buffer.critical_threshold
        self._live.max_tau = self._buffer.max_tau
        self._live.min_tau = self._buffer.min_tau
        self._live.use_parallel_stochastic = self._buffer.use_parallel_stochastic
    
    # ========== Observer Pattern ==========
    
    def add_listener(self, listener: ChangeListener) -> None:
        """Register a listener for parameter changes.
        
        Args:
            listener: Listener implementing ChangeListener interface
        """
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: ChangeListener) -> None:
        """Unregister a listener.
        
        Args:
            listener: Listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_commit(self) -> None:
        """Notify listeners that changes were committed."""
        for listener in self._listeners:
            try:
                listener.on_changes_committed(self._pending_changes.copy())
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Commit listener notification failed: {e}")
    
    def _notify_rollback(self) -> None:
        """Notify listeners that changes were rolled back."""
        for listener in self._listeners:
            try:
                listener.on_changes_rolled_back(self._pending_changes.copy())
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Rollback listener notification failed: {e}")
    
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
    
    # ========== Persistence ==========
    
    def _get_settings_filepath(self) -> Optional[str]:
        """Get the filepath for persisting settings.
        
        Settings are saved as .settings_{model_name}.json next to the model file,
        similar to how view state is saved. For unsaved models, uses ~/.config/shypn/
        
        Returns:
            str: Settings file path, or None if cannot determine
        """
        if not self._model:
            return None
        
        # Check if model has filepath attribute
        if not hasattr(self._model, 'filepath') or not self._model.filepath:
            # Unsaved model - use config directory
            config_dir = os.path.join(Path.home(), '.config', 'shypn')
            os.makedirs(config_dir, exist_ok=True)
            return os.path.join(config_dir, 'default_settings.json')
        
        # Model has filepath - save settings next to it
        model_dir = os.path.dirname(self._model.filepath)
        basename = os.path.basename(self._model.filepath)
        
        # Remove .shy extension if present
        if basename.endswith('.shy'):
            basename = basename[:-4]
        
        return os.path.join(model_dir, f".settings_{basename}.json")
    
    def _save_to_disk(self) -> None:
        """Atomically save settings to disk.
        
        Uses atomic write pattern (write to temp file, then rename) to ensure
        settings are never corrupted, even if process is interrupted.
        
        IMPORTANT: Excludes transient session parameters (playback speed) that
        should not persist across sessions. Only model-intrinsic parameters are saved.
        """
        filepath = self._get_settings_filepath()
        if not filepath:
            return  # No filepath available (model not saved yet)
        
        try:
            # Serialize settings to dict (includes all parameters)
            settings_dict = self._live.to_dict()
            
            # EXCLUDE transient session parameters that should not persist:
            # - time_scale: Playback speed is a UI control for current exploration,
            #   not a model property. Always defaults to 1.0x on load.
            transient_params = ['time_scale']
            for param in transient_params:
                settings_dict.pop(param, None)
            
            # Write to temp file first (atomic write pattern)
            temp_filepath = filepath + '.tmp'
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2)
            
            # Atomic rename (replaces old file atomically on POSIX systems)
            os.replace(temp_filepath, filepath)
            
            logger.debug(f"Settings persisted to {filepath} (transient params excluded)")
            
        except Exception as e:
            logger.warning(f"Failed to persist settings: {e}")
            # Clean up temp file if it exists
            try:
                temp_filepath = filepath + '.tmp'
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except OSError:
                pass  # Best-effort cleanup; ignore if temp file cannot be removed
    
    def _load_from_disk(self) -> None:
        """Load persisted settings from disk if available.
        
        Called during initialization to restore settings from previous session.
        Silently fails if file doesn't exist (uses defaults).
        
        IMPORTANT: Transient session parameters (playback speed) are NOT restored
        and remain at their defaults. This prevents confusion from forgotten high-speed
        settings from previous sessions.
        """
        filepath = self._get_settings_filepath()
        if not filepath or not os.path.exists(filepath):
            return  # No persisted settings
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
            
            # Ensure time_scale is NOT in the loaded dict (always use default 1.0x)
            # This prevents playback speed from persisting across sessions
            settings_dict.pop('time_scale', None)
            
            # Restore settings from dict (time_scale will use SimulationSettings default)
            loaded_settings = SimulationSettings.from_dict(settings_dict)
            
            # Copy loaded values to live settings (EXCEPT time_scale which stays at 1.0)
            self._live.time_units = loaded_settings.time_units
            self._live.duration = loaded_settings.duration
            self._live.dt_auto = loaded_settings.dt_auto
            self._live.dt_manual = loaded_settings.dt_manual
            # time_scale NOT restored - remains at default 1.0x
            self._live.tau_epsilon = loaded_settings.tau_epsilon
            self._live.critical_threshold = loaded_settings.critical_threshold
            self._live.max_tau = loaded_settings.max_tau
            self._live.min_tau = loaded_settings.min_tau
            self._live.use_parallel_stochastic = loaded_settings.use_parallel_stochastic
            
            logger.debug(f"Settings loaded from {filepath} (time_scale remains at default {self._live.time_scale}x)")
            
        except Exception as e:
            logger.warning(f"Failed to load persisted settings: {e}. Using defaults.")
