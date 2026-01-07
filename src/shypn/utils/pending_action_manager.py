#!/usr/bin/env python3
"""Pending Action Manager - Queue actions that require a project.

When users try to use functionality that requires an open project,
but no project is open, the action is queued. When a project is opened,
all pending actions are automatically executed with a notification.

Author: Simão Eugénio
Date: 2026-01-05
"""
from typing import Callable, List, Tuple, Optional
import logging


class PendingActionManager:
    """Manages actions that are pending until a project is opened.
    
    Singleton pattern ensures all components use the same queue.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.pending_actions: List[Tuple[str, Callable, tuple, dict]] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.on_actions_executed: Optional[Callable[[int], None]] = None
    
    def add_pending_action(self, description: str, callback: Callable, *args, **kwargs):
        """Add an action to the pending queue.
        
        Args:
            description: Human-readable description of the action
            callback: Function to call when project is opened
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback
        """
        self.pending_actions.append((description, callback, args, kwargs))
        self.logger.info(f"Queued pending action: {description}")
    
    def has_pending_actions(self) -> bool:
        """Check if there are any pending actions."""
        return len(self.pending_actions) > 0
    
    def get_pending_count(self) -> int:
        """Get number of pending actions."""
        return len(self.pending_actions)
    
    def get_pending_descriptions(self) -> List[str]:
        """Get descriptions of all pending actions."""
        return [desc for desc, _, _, _ in self.pending_actions]
    
    def execute_pending_actions(self):
        """Execute all pending actions now that a project is available.
        
        Returns:
            int: Number of actions executed successfully
        """
        if not self.pending_actions:
            return 0
        
        executed_count = 0
        failed_actions = []
        
        # Execute each pending action
        for description, callback, args, kwargs in self.pending_actions:
            try:
                self.logger.info(f"Executing pending action: {description}")
                callback(*args, **kwargs)
                executed_count += 1
            except Exception as e:
                self.logger.error(f"Failed to execute pending action '{description}': {e}")
                failed_actions.append((description, str(e)))
        
        # Clear the queue
        self.pending_actions.clear()
        
        # Notify about execution
        if self.on_actions_executed and executed_count > 0:
            try:
                self.on_actions_executed(executed_count)
            except Exception as e:
                self.logger.error(f"Error in on_actions_executed callback: {e}")
        
        # Log failures
        if failed_actions:
            self.logger.warning(f"Failed to execute {len(failed_actions)} pending actions")
            for desc, error in failed_actions:
                self.logger.warning(f"  - {desc}: {error}")
        
        return executed_count
    
    def clear_pending_actions(self):
        """Clear all pending actions without executing them."""
        count = len(self.pending_actions)
        self.pending_actions.clear()
        if count > 0:
            self.logger.info(f"Cleared {count} pending actions")


# Singleton accessor
_pending_action_manager = None


def get_pending_action_manager() -> PendingActionManager:
    """Get the global pending action manager instance."""
    global _pending_action_manager
    if _pending_action_manager is None:
        _pending_action_manager = PendingActionManager()
    return _pending_action_manager


__all__ = ['PendingActionManager', 'get_pending_action_manager']
