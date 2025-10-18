"""
Simulation State Detector

Detects current simulation state and provides context-aware queries.
Replaces explicit mode checking with state-based decisions.
"""

from typing import Optional, List
from .base import SimulationState, StateProvider, StateChangeObserver


class SimulationStateDetector:
    """Detects and tracks simulation state for context-aware behavior.
    
    This class is the core of the mode elimination system. It examines
    the simulation controller's state (time, running status) and provides
    queries for determining what actions are allowed.
    
    Key Design Decisions:
    - State based on simulation time and running status
    - IDLE when time = 0 (full editing allowed)
    - STARTED when time > 0 but not running (paused)
    - RUNNING when actively executing
    - Structure editing only allowed in IDLE state
    - Token manipulation always allowed
    
    Example:
        detector = SimulationStateDetector(simulation_controller)
        
        if detector.can_edit_structure():
            create_place()
        else:
            show_message(detector.get_restriction_message('create place'))
    """
    
    def __init__(self, state_provider: StateProvider):
        """Initialize detector with state provider.
        
        Args:
            state_provider: Object providing simulation state (usually SimulationController)
        """
        self._provider = state_provider
        self._observers: List[StateChangeObserver] = []
        self._current_state = SimulationState.IDLE
    
    # ========== State Detection ==========
    
    @property
    def state(self) -> SimulationState:
        """Get current simulation state.
        
        State determination logic:
        - time = 0 → IDLE
        - time > 0 and running → RUNNING
        - time > 0 and not running → STARTED
        - time >= duration → COMPLETED (if duration set)
        
        Returns:
            SimulationState: Current state enum value
        """
        if self._provider.time == 0.0:
            return SimulationState.IDLE
        
        # Check if completed (reached duration limit)
        if self._provider.duration is not None:
            if self._provider.time >= self._provider.duration:
                return SimulationState.COMPLETED
        
        # Active simulation
        if self._provider.running:
            return SimulationState.RUNNING
        else:
            return SimulationState.STARTED
    
    def update_state(self) -> bool:
        """Update and check if state has changed.
        
        Call this after any operation that might change state
        (start, pause, reset, step).
        
        Returns:
            bool: True if state changed, False otherwise
        """
        old_state = self._current_state
        new_state = self.state
        
        if old_state != new_state:
            self._current_state = new_state
            self._notify_observers(old_state, new_state)
            return True
        
        return False
    
    # ========== State Queries ==========
    
    def is_idle(self) -> bool:
        """Check if simulation is idle (ready for editing).
        
        Returns:
            bool: True if in IDLE state (time = 0)
        """
        return self.state == SimulationState.IDLE
    
    def is_running(self) -> bool:
        """Check if simulation is actively running.
        
        Returns:
            bool: True if in RUNNING state
        """
        return self.state == SimulationState.RUNNING
    
    def has_started(self) -> bool:
        """Check if simulation has been started (time > 0).
        
        Returns:
            bool: True if time > 0 (STARTED, RUNNING, or COMPLETED)
        """
        return self._provider.time > 0.0
    
    def is_completed(self) -> bool:
        """Check if simulation has completed.
        
        Returns:
            bool: True if in COMPLETED state
        """
        return self.state == SimulationState.COMPLETED
    
    # ========== Action Permission Queries ==========
    
    def can_edit_structure(self) -> bool:
        """Check if structure editing is allowed.
        
        Structure editing includes:
        - Creating/deleting places and transitions
        - Creating/deleting arcs
        - Moving objects
        - Changing properties
        
        Returns:
            bool: True only if in IDLE state
        """
        return self.state.is_editing_allowed
    
    def can_manipulate_tokens(self) -> bool:
        """Check if token manipulation is allowed.
        
        Token manipulation includes:
        - Adding tokens to places
        - Removing tokens from places
        
        This is always allowed to support:
        - Setting initial marking (IDLE)
        - Interactive simulation (RUNNING/STARTED)
        
        Returns:
            bool: Always True
        """
        return self.state.allows_token_manipulation
    
    def can_move_objects(self) -> bool:
        """Check if objects can be moved.
        
        Returns:
            bool: True only if in IDLE state
        """
        return self.can_edit_structure()
    
    def can_show_transform_handles(self) -> bool:
        """Check if transform handles can be shown.
        
        Transform handles are shown for object transformation
        (resize, rotate) and should only be available when
        structure editing is allowed.
        
        Returns:
            bool: True only if in IDLE state
        """
        return self.can_edit_structure()
    
    # ========== Restriction Messages ==========
    
    def get_restriction_message(self, action: str) -> Optional[str]:
        """Get user-friendly message explaining why action is restricted.
        
        Args:
            action: Action name (e.g., 'create place', 'move object')
        
        Returns:
            str or None: Restriction message, or None if action allowed
        """
        if self.can_edit_structure():
            return None  # No restriction
        
        # Provide helpful message based on state
        if self.has_started():
            return f"Cannot {action} - reset simulation to edit structure"
        
        return f"Cannot {action} in current state"
    
    # ========== Observer Pattern ==========
    
    def add_observer(self, observer: StateChangeObserver):
        """Register an observer for state changes.
        
        Args:
            observer: Observer implementing StateChangeObserver interface
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: StateChangeObserver):
        """Unregister an observer.
        
        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, old_state: SimulationState, new_state: SimulationState):
        """Notify all observers of state change.
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        for observer in self._observers:
            try:
                observer.on_state_changed(old_state, new_state)
            except Exception as e:
                # Don't let observer errors break state updates
                print(f"[StateDetector] Observer error: {e}")
    
    # ========== String Representation ==========
    
    def __repr__(self) -> str:
        """Get debug representation."""
        return (f"SimulationStateDetector(state={self.state}, "
                f"time={self._provider.time:.2f}s, "
                f"running={self._provider.running})")
    
    def __str__(self) -> str:
        """Get user-friendly string representation."""
        state_str = str(self.state)
        time_str = f"{self._provider.time:.2f}s"
        
        if self.is_idle():
            return f"Ready for editing (time = 0)"
        elif self.is_running():
            return f"Running simulation (time = {time_str})"
        elif self.has_started():
            return f"Paused (time = {time_str})"
        else:
            return f"{state_str.title()} (time = {time_str})"
