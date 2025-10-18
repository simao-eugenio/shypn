"""
Concrete State Query Implementations

Provides specific query classes for different action permissions.
Each query encapsulates the logic for one type of action.
"""

from typing import Optional
from .base import StateQuery


class StructureEditQuery(StateQuery):
    """Query for structure editing permission.
    
    Structure editing includes creating/deleting/moving places,
    transitions, and arcs.
    
    Example:
        query = StructureEditQuery(state_detector)
        allowed, reason = query.check()
        if not allowed:
            show_error_dialog(reason)
    """
    
    def check(self) -> tuple[bool, Optional[str]]:
        """Check if structure editing is allowed.
        
        Returns:
            tuple: (allowed, reason)
        """
        if self.state_detector.can_edit_structure():
            return (True, None)
        
        return (False, self.state_detector.get_restriction_message("edit structure"))


class TokenManipulationQuery(StateQuery):
    """Query for token manipulation permission.
    
    Token manipulation (add/remove tokens) is always allowed to support
    both initial marking setup and interactive simulation.
    """
    
    def check(self) -> tuple[bool, Optional[str]]:
        """Check if token manipulation is allowed.
        
        Returns:
            tuple: (True, None) - Always allowed
        """
        return (True, None)


class ObjectMovementQuery(StateQuery):
    """Query for object movement permission.
    
    Objects can only be moved when in IDLE state (no simulation started).
    """
    
    def check(self) -> tuple[bool, Optional[str]]:
        """Check if objects can be moved.
        
        Returns:
            tuple: (allowed, reason)
        """
        if self.state_detector.can_move_objects():
            return (True, None)
        
        return (False, self.state_detector.get_restriction_message("move objects"))


class TransformHandlesQuery(StateQuery):
    """Query for transform handle visibility.
    
    Transform handles (for resize/rotate) should only be shown when
    structure editing is allowed.
    """
    
    def check(self) -> tuple[bool, Optional[str]]:
        """Check if transform handles should be shown.
        
        Returns:
            tuple: (allowed, reason)
        """
        if self.state_detector.can_show_transform_handles():
            return (True, None)
        
        return (False, self.state_detector.get_restriction_message("show transform handles"))


class PropertyEditQuery(StateQuery):
    """Query for property editing permission.
    
    Properties (names, weights, delays) can only be edited in IDLE state.
    """
    
    def check(self) -> tuple[bool, Optional[str]]:
        """Check if properties can be edited.
        
        Returns:
            tuple: (allowed, reason)
        """
        if self.state_detector.can_edit_structure():
            return (True, None)
        
        return (False, self.state_detector.get_restriction_message("edit properties"))


class SimulationControlQuery(StateQuery):
    """Query for simulation control availability.
    
    Determines which simulation controls (Play/Pause/Reset) are available
    based on current state.
    """
    
    def check(self) -> tuple[bool, Optional[str]]:
        """Check simulation control availability.
        
        Returns:
            tuple: Always (True, None) - controls are always visible,
                   but specific buttons are enabled/disabled based on state
        """
        return (True, None)
    
    def can_play(self) -> bool:
        """Check if Play button should be enabled."""
        # Can play if idle or paused
        return self.state_detector.is_idle() or not self.state_detector.is_running()
    
    def can_pause(self) -> bool:
        """Check if Pause button should be enabled."""
        # Can pause only when running
        return self.state_detector.is_running()
    
    def can_reset(self) -> bool:
        """Check if Reset button should be enabled."""
        # Can reset anytime simulation has started
        return self.state_detector.has_started()
