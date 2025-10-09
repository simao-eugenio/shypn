#!/usr/bin/env python3
"""SwissKnife Tool Registry - Tool definitions and management.

This module provides tool management for the SwissKnifePalette.
Tools are simple button wrappers that emit activation signals.
"""

from gi.repository import Gtk, GObject
from typing import Dict, List, Optional


class SwissKnifeTool(GObject.Object):
    """Simple tool wrapper for SwissKnifePalette buttons.
    
    Each tool is a button that emits an 'activated' signal when clicked.
    The signal is then handled by the application to perform the actual operation.
    
    Signals:
        activated(str): Emitted when tool button is clicked, passes tool_id
    """
    
    __gsignals__ = {
        'activated': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self, tool_id: str, label: str, tooltip: str):
        """Initialize tool.
        
        Args:
            tool_id: Unique tool identifier (e.g., 'place', 'transition')
            label: Button label text
            tooltip: Tooltip text
        """
        super().__init__()
        
        self.tool_id = tool_id
        self.label = label
        self.tooltip = tooltip
        
        # Create button
        self._button = Gtk.Button(label=label)
        self._button.set_tooltip_text(tooltip)
        self._button.set_size_request(40, 40)
        self._button.get_style_context().add_class('swissknife-tool')
        
        # Connect click handler
        self._button.connect('clicked', self._on_clicked)
    
    def _on_clicked(self, button):
        """Handle button click - emit activated signal."""
        self.emit('activated', self.tool_id)
    
    def get_button(self):
        """Get the Gtk.Button widget.
        
        Returns:
            Gtk.Button: The tool button
        """
        return self._button



# Register GObject type
GObject.type_register(SwissKnifeTool)


class ToolRegistry:
    """Registry for SwissKnife palette tools and categories.
    
    Manages tool definitions and category configurations for the SwissKnifePalette.
    """
    
    # Tool definitions - ID: (label, tooltip)
    TOOL_DEFINITIONS = {
        # Edit category tools
        'place': ('P', 'Place Tool (Ctrl+P)\n\nCreate circular place nodes'),
        'transition': ('T', 'Transition Tool (Ctrl+T)\n\nCreate rectangular transition nodes'),
        'arc': ('A', 'Arc Tool (Ctrl+A)\n\nCreate arcs between places and transitions'),
        'select': ('S', 'Select Tool (Ctrl+S)\n\nSelect and manipulate elements'),
        'lasso': ('L', 'Lasso Tool (Ctrl+L)\n\nSelect multiple elements with lasso'),
        
        # Layout category tools
        'layout_auto': ('Auto', 'Auto Layout\n\nAutomatically arrange nodes'),
        'layout_hierarchical': ('Hier', 'Hierarchical Layout\n\nArrange nodes in hierarchy'),
        'layout_force': ('Force', 'Force-Directed Layout\n\nArrange nodes using force simulation'),
    }
    
    # Category configurations for Edit mode
    EDIT_MODE_CATEGORIES = {
        'edit': {
            'label': 'Edit',
            'tooltip': 'Edit Tools\n\nCreate and modify Petri net elements',
            'tools': ['place', 'transition', 'arc', 'select', 'lasso'],
            'widget_palette': False
        },
        'simulate': {
            'label': 'Simulate',
            'tooltip': 'Simulation Tools\n\nRun and control simulations',
            'tools': [],  # No regular tools - uses widget palette
            'widget_palette': True
        },
        'layout': {
            'label': 'Layout',
            'tooltip': 'Layout Tools\n\nArrange nodes automatically',
            'tools': ['layout_auto', 'layout_hierarchical', 'layout_force'],
            'widget_palette': False
        }
    }
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, SwissKnifeTool] = {}
        self._create_tools()
    
    def _create_tools(self):
        """Create all tool instances from definitions."""
        for tool_id, (label, tooltip) in self.TOOL_DEFINITIONS.items():
            tool = SwissKnifeTool(tool_id, label, tooltip)
            self._tools[tool_id] = tool
    
    def get_tool(self, tool_id: str) -> Optional[SwissKnifeTool]:
        """Get a tool by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            SwissKnifeTool or None if not found
        """
        return self._tools.get(tool_id)
    
    def get_all_tools(self) -> Dict[str, SwissKnifeTool]:
        """Get all registered tools.
        
        Returns:
            Dict mapping tool IDs to tool instances
        """
        return self._tools.copy()
    
    def get_categories(self, mode: str = 'edit') -> Dict:
        """Get category configurations for a mode.
        
        Args:
            mode: Mode name ('edit' or 'simulate')
            
        Returns:
            Dict of category configurations
        """
        if mode == 'edit':
            return self.EDIT_MODE_CATEGORIES.copy()
        else:
            # For now, only edit mode is implemented
            return {}

