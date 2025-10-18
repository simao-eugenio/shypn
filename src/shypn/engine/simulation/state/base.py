"""
Base Classes for Simulation State System

Defines core abstractions for state detection and behavior queries.
Following OOP principles with clear separation of concerns.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class SimulationState(Enum):
    """Enumeration of possible simulation states.
    
    These states replace the old 'edit'/'simulate' mode strings with
    clear, semantic state names based on simulation lifecycle.
    """
    
    IDLE = "idle"
    """No simulation active, ready for full editing (time = 0)"""
    
    RUNNING = "running"
    """Simulation actively executing"""
    
    STARTED = "started"
    """Simulation has been started but is currently paused (time > 0)"""
    
    COMPLETED = "completed"
    """Simulation finished (reached duration limit)"""
    
    def __str__(self) -> str:
        """Get human-readable state name."""
        return self.value
    
    @property
    def is_editing_allowed(self) -> bool:
        """Check if structure editing is allowed in this state."""
        return self == SimulationState.IDLE
    
    @property
    def is_simulation_active(self) -> bool:
        """Check if simulation is active (started or running)."""
        return self in (SimulationState.RUNNING, SimulationState.STARTED)
    
    @property
    def allows_token_manipulation(self) -> bool:
        """Check if token manipulation is allowed in this state."""
        return True  # Always allowed for interactive simulation


class StateQuery(ABC):
    """Abstract base class for state-based behavior queries.
    
    Subclasses implement specific queries (e.g., can_edit_structure)
    by examining simulation state and returning decisions with reasons.
    
    This pattern provides:
    - Clear separation of concerns (one query = one decision)
    - Reusable query logic
    - User-friendly restriction messages
    - Easy testing
    
    Example:
        query = StructureEditQuery(state_detector)
        allowed, reason = query.check()
        if not allowed:
            show_message(reason)
    """
    
    def __init__(self, state_detector: 'SimulationStateDetector'):
        """Initialize query with state detector.
        
        Args:
            state_detector: SimulationStateDetector instance to query
        """
        self.state_detector = state_detector
    
    @abstractmethod
    def check(self) -> tuple[bool, Optional[str]]:
        """Check if action is allowed.
        
        Returns:
            tuple: (allowed: bool, reason: Optional[str])
                - allowed: True if action permitted, False otherwise
                - reason: User-friendly message explaining restriction (None if allowed)
        """
        pass
    
    def __bool__(self) -> bool:
        """Allow query to be used in boolean context.
        
        Example:
            if StructureEditQuery(detector):
                # Editing allowed
        """
        allowed, _ = self.check()
        return allowed


class StateChangeObserver(ABC):
    """Observer interface for state change notifications.
    
    Classes interested in state changes should implement this interface
    and register with the state detector.
    """
    
    @abstractmethod
    def on_state_changed(self, old_state: SimulationState, new_state: SimulationState):
        """Called when simulation state changes.
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        pass


class StateProvider(ABC):
    """Abstract interface for objects that provide simulation state.
    
    The SimulationController should implement this interface to provide
    state information to the detector.
    """
    
    @property
    @abstractmethod
    def time(self) -> float:
        """Get current simulation time in seconds."""
        pass
    
    @property
    @abstractmethod
    def running(self) -> bool:
        """Check if simulation is currently running."""
        pass
    
    @property
    @abstractmethod
    def duration(self) -> Optional[float]:
        """Get simulation duration limit, or None if indefinite."""
        pass
