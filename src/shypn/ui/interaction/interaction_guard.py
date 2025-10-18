"""Interaction guard - controls what actions are allowed based on simulation state.

This replaces mode-based checks (if mode == 'edit') with state-based queries
(if state_detector.can_edit_structure()).
"""

from typing import Optional, Tuple
from shypn.engine.simulation.state import SimulationStateDetector


class InteractionGuard:
    """Guards user interactions based on simulation state.
    
    Provides a clean API for checking if actions are allowed, replacing
    mode string checks with state detector queries.
    
    Example:
        guard = InteractionGuard(controller.state_detector)
        
        if guard.can_activate_tool('place'):
            manager.set_tool('place')
        else:
            show_message(guard.get_block_reason('place'))
    """
    
    def __init__(self, state_detector: SimulationStateDetector):
        """Initialize interaction guard.
        
        Args:
            state_detector: State detector to query for permissions
        """
        self._detector = state_detector
    
    def can_activate_tool(self, tool_name: str) -> bool:
        """Check if a tool can be activated.
        
        Args:
            tool_name: Tool identifier ('place', 'transition', 'arc', 'select', etc.)
            
        Returns:
            True if tool can be activated, False otherwise
        """
        # Structural editing tools require structure editing permission
        if tool_name in ('place', 'transition', 'arc'):
            return self._detector.can_edit_structure()
        
        # Selection and manipulation tools are always allowed
        if tool_name in ('select', 'lasso'):
            return True
        
        # Token manipulation tools are always allowed
        if tool_name in ('add_token', 'remove_token'):
            return self._detector.can_manipulate_tokens()
        
        # Unknown tools - default to structure editing rules
        return self._detector.can_edit_structure()
    
    def can_delete_object(self, obj) -> bool:
        """Check if an object can be deleted.
        
        Args:
            obj: Object to check (Place, Transition, or Arc)
            
        Returns:
            True if object can be deleted, False otherwise
        """
        # Object deletion is a structural change
        return self._detector.can_edit_structure()
    
    def can_move_object(self, obj) -> bool:
        """Check if an object can be moved.
        
        Args:
            obj: Object to check
            
        Returns:
            True if object can be moved, False otherwise
        """
        # Moving objects is allowed (doesn't change structure)
        # This enables animation/visualization during simulation
        return True
    
    def can_edit_properties(self, obj) -> bool:
        """Check if object properties can be edited.
        
        Args:
            obj: Object to check
            
        Returns:
            True if properties can be edited, False otherwise
        """
        # Property editing depends on object type
        # For now, be conservative: only allow when structure can be edited
        # TODO: Refine this - some properties might be editable during simulation
        return self._detector.can_edit_structure()
    
    def can_show_transform_handles(self) -> bool:
        """Check if transformation handles should be shown.
        
        Returns:
            True if handles should be visible, False otherwise
        """
        return self._detector.can_show_transform_handles()
    
    def get_block_reason(self, action: str) -> Optional[str]:
        """Get human-readable reason why an action is blocked.
        
        Args:
            action: Action identifier ('place', 'delete', etc.)
            
        Returns:
            Reason string if blocked, None if allowed
        """
        if action in ('place', 'transition', 'arc', 'delete'):
            if not self._detector.can_edit_structure():
                # Convert action identifier to user-friendly verb
                action_verbs = {
                    'place': 'create place',
                    'transition': 'create transition',
                    'arc': 'create arc',
                    'delete': 'delete object'
                }
                verb = action_verbs.get(action, action)
                return self._detector.get_restriction_message(verb)
        
        # Action is allowed or unknown
        return None
    
    def check_tool_activation(self, tool_name: str) -> Tuple[bool, Optional[str]]:
        """Check if tool can be activated with reason.
        
        Args:
            tool_name: Tool identifier
            
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        if self.can_activate_tool(tool_name):
            return (True, None)
        else:
            reason = self.get_block_reason(tool_name)
            return (False, reason)
