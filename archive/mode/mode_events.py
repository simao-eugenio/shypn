"""Mode and tool change events.

This module defines events related to application mode and tool changes:
- Mode changes (Edit ↔ Simulate)
- Tool selection changes
"""

from .base_event import BaseEvent


class ModeChangedEvent(BaseEvent):
    """Event fired when application mode changes.
    
    The application can be in different modes:
    - 'edit': Normal editing mode
    - 'simulate': Simulation mode
    
    Attributes:
        old_mode: Previous mode
        new_mode: New mode
    """
    
    def __init__(self, old_mode: str, new_mode: str):
        """Initialize event.
        
        Args:
            old_mode: Previous mode ('edit' or 'simulate')
            new_mode: New mode ('edit' or 'simulate')
        """
        super().__init__()
        self.old_mode = old_mode
        self.new_mode = new_mode
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'old_mode': self.old_mode,
            'new_mode': self.new_mode,
        })
        return data
    
    def __repr__(self):
        return f"ModeChangedEvent(from={self.old_mode}, to={self.new_mode})"


class ToolChangedEvent(BaseEvent):
    """Event fired when the active tool changes.
    
    Tools include:
    - 'select': Selection tool
    - 'place': Place creation tool
    - 'transition': Transition creation tool
    - 'arc': Arc creation tool
    - 'token': Token manipulation tool
    
    Attributes:
        old_tool: Previous tool (optional)
        new_tool: New tool
    """
    
    def __init__(self, new_tool: str, old_tool: str = None):
        """Initialize event.
        
        Args:
            new_tool: New tool name
            old_tool: Previous tool name (optional)
        """
        super().__init__()
        self.new_tool = new_tool
        self.old_tool = old_tool
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'old_tool': self.old_tool,
            'new_tool': self.new_tool,
        })
        return data
    
    def __repr__(self):
        return f"ToolChangedEvent(tool={self.new_tool})"
