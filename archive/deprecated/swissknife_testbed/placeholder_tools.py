#!/usr/bin/env python3
"""Placeholder tools for testing SwissKnifePalette.

These are simple buttons that emit signals but don't perform real actions.
Used for testing animations, layout, signal flow, and CSS styling.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class PlaceholderTool(GObject.GObject):
    """Generic placeholder tool for testing.
    
    Just a button that emits a signal when clicked.
    No real functionality - purely for testing architecture.
    
    Signals:
        activated: Emitted when tool button is clicked
    """
    
    __gsignals__ = {
        'activated': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self, tool_id: str, label: str, tooltip: str):
        """Initialize placeholder tool.
        
        Args:
            tool_id: Unique tool identifier (e.g., 'place', 'select')
            label: Button label text (e.g., 'P', 'S')
            tooltip: Tooltip text
        """
        super().__init__()
        self.tool_id = tool_id
        self.label = label
        self.tooltip_text = tooltip
        self.button = None
        
        self._create_button()
    
    def _create_button(self):
        """Create simple button."""
        self.button = Gtk.Button(label=self.label)
        self.button.set_size_request(50, 40)
        self.button.set_tooltip_text(self.tooltip_text)
        self.button.get_style_context().add_class('tool-button')
        self.button.get_style_context().add_class('placeholder-tool')
        self.button.connect('clicked', self._on_clicked)
    
    def _on_clicked(self, button):
        """Handle button click - emit signal."""
        print(f"[PlaceholderTool] {self.tool_id} clicked")
        self.emit('activated', self.tool_id)
    
    def get_button(self):
        """Get button widget."""
        return self.button


# ============================================================================
# Pre-defined Placeholder Tools for Edit Mode
# ============================================================================

def create_edit_mode_tools():
    """Create all placeholder tools for Edit mode.
    
    Returns:
        dict: Tool ID → PlaceholderTool instance
    """
    return {
        # Create Tools
        'place': PlaceholderTool('place', 'P', 'Place Tool (Placeholder)\n\nClick to test signal'),
        'transition': PlaceholderTool('transition', 'T', 'Transition Tool (Placeholder)\n\nClick to test signal'),
        'arc': PlaceholderTool('arc', 'A', 'Arc Tool (Placeholder)\n\nClick to test signal'),
        
        # Edit Operations
        'select': PlaceholderTool('select', 'S', 'Select Tool (Placeholder)\n\nClick to test signal'),
        'lasso': PlaceholderTool('lasso', 'L', 'Lasso Tool (Placeholder)\n\nClick to test signal'),
        'undo': PlaceholderTool('undo', 'U', 'Undo (Placeholder)\n\nClick to test signal'),
        'redo': PlaceholderTool('redo', 'R', 'Redo (Placeholder)\n\nClick to test signal'),
        
        # Simulation Control (Row 0: Buttons)
        'sim_run': PlaceholderTool('sim_run', 'R', 'Run Button [R]\n\nStart executing the Petri net'),
        'sim_step': PlaceholderTool('sim_step', 'P', 'Step Button [P]\n\nExecute one simulation step'),
        'sim_stop': PlaceholderTool('sim_stop', 'S', 'Stop Button [S]\n\nPause execution'),
        'sim_reset': PlaceholderTool('sim_reset', 'T', 'Reset Button [T]\n\nReset to initial marking'),
        'sim_settings': PlaceholderTool('sim_settings', '⚙', 'Settings Button [⚙]\n\nConfigure duration, time step, and policies'),
        
        # Simulation Controls (Row 1: Duration controls - placeholder representation)
        'sim_duration_label': PlaceholderTool('sim_duration_label', '[Duration:]', 'Duration Label\n\n(Label widget in real palette)'),
        'sim_duration_entry': PlaceholderTool('sim_duration_entry', '[60]', 'Duration Entry\n\n(Entry widget in real palette)'),
        'sim_units_combo': PlaceholderTool('sim_units_combo', '[seconds▼]', 'Time Units Combo\n\n(ComboBoxText in real palette)'),
        
        # Simulation Feedback (Row 2 & 3: Progress/Time display - placeholder representation)
        'sim_progress_bar': PlaceholderTool('sim_progress_bar', '[Progress]', 'Progress Bar\n\n(ProgressBar widget in real palette)'),
        'sim_time_display': PlaceholderTool('sim_time_display', '[Time: 0.0/60.0s]', 'Time Display\n\n(Label widget in real palette)'),
        
        # Layout Tools
        'layout_auto': PlaceholderTool('layout_auto', 'Auto', 'Auto Layout (Placeholder)\n\nClick to test signal'),
        'layout_hierarchical': PlaceholderTool('layout_hierarchical', 'Hier', 'Hierarchical Layout (Placeholder)\n\nClick to test signal'),
        'layout_force': PlaceholderTool('layout_force', 'Force', 'Force-Directed Layout (Placeholder)\n\nClick to test signal'),
        
        # Transform Tools
        'transform_parallel': PlaceholderTool('transform_parallel', 'Para', 'Parallel Arc (Placeholder)\n\nClick to test signal'),
        'transform_inhibitor': PlaceholderTool('transform_inhibitor', 'Inhib', 'Inhibitor Arc (Placeholder)\n\nClick to test signal'),
        'transform_read': PlaceholderTool('transform_read', 'Read', 'Read Arc (Placeholder)\n\nClick to test signal'),
        'transform_reset': PlaceholderTool('transform_reset', 'Reset', 'Reset Arc (Placeholder)\n\nClick to test signal'),
        
        # View Tools
        'view_zoom_in': PlaceholderTool('view_zoom_in', 'Z+', 'Zoom In (Placeholder)\n\nClick to test signal'),
        'view_zoom_out': PlaceholderTool('view_zoom_out', 'Z-', 'Zoom Out (Placeholder)\n\nClick to test signal'),
        'view_fit': PlaceholderTool('view_fit', 'Fit', 'Fit to Window (Placeholder)\n\nClick to test signal'),
        'view_center': PlaceholderTool('view_center', 'Ctr', 'Center View (Placeholder)\n\nClick to test signal'),
    }


# ============================================================================
# Pre-defined Placeholder Tools for Simulate Mode
# ============================================================================

def create_simulate_mode_tools():
    """Create all placeholder tools for Simulate mode.
    
    Returns:
        dict: Tool ID → PlaceholderTool instance
    """
    return {
        # Simulation Control
        'sim_step': PlaceholderTool('sim_step', 'Step', 'Simulation Step (Placeholder)\n\nClick to test signal'),
        'sim_play': PlaceholderTool('sim_play', 'Play', 'Play Simulation (Placeholder)\n\nClick to test signal'),
        'sim_pause': PlaceholderTool('sim_pause', 'Pause', 'Pause Simulation (Placeholder)\n\nClick to test signal'),
        'sim_reset': PlaceholderTool('sim_reset', 'Reset', 'Reset Simulation (Placeholder)\n\nClick to test signal'),
        'sim_speed': PlaceholderTool('sim_speed', 'Speed', 'Speed Control (Placeholder)\n\nClick to test signal'),
        
        # Visualization
        'viz_tokens': PlaceholderTool('viz_tokens', 'Tokens', 'Show Tokens (Placeholder)\n\nClick to test signal'),
        'viz_marking': PlaceholderTool('viz_marking', 'Mark', 'Show Marking (Placeholder)\n\nClick to test signal'),
        'viz_chart': PlaceholderTool('viz_chart', 'Chart', 'Show Chart (Placeholder)\n\nClick to test signal'),
        'viz_metrics': PlaceholderTool('viz_metrics', 'Metrics', 'Show Metrics (Placeholder)\n\nClick to test signal'),
        
        # Analysis
        'analyze_export': PlaceholderTool('analyze_export', 'Export', 'Export Data (Placeholder)\n\nClick to test signal'),
        'analyze_stats': PlaceholderTool('analyze_stats', 'Stats', 'Statistics (Placeholder)\n\nClick to test signal'),
    }


# ============================================================================
# Tool Categories Configuration
# ============================================================================

EDIT_MODE_CATEGORIES = {
    'edit': {
        'label': 'Edit',
        'tooltip': 'Create Tools\n\nPlace, Transition, Arc, Select, Lasso',
        'tools': ['place', 'transition', 'arc', 'select', 'lasso']
    },
    'simulate': {
        'label': 'Simulate',
        'tooltip': 'Simulation Tools\n\nReal simulation palette with all controls',
        'widget_palette': True,  # Flag to indicate this uses a widget palette instead of tool buttons
        'tools': []  # Empty - will be replaced by SimulateToolsPaletteLoader widget
    },
    'layout': {
        'label': 'Layout',
        'tooltip': 'Layout Tools\n\nAuto, Hierarchical, Force-Directed',
        'tools': ['layout_auto', 'layout_hierarchical', 'layout_force']
    }
}

SIMULATE_MODE_CATEGORIES = {
    'control': {
        'label': 'Control',
        'tooltip': 'Simulation Control\n\nStep, Play, Reset',
        'tools': ['sim_step', 'sim_play', 'sim_pause', 'sim_reset', 'sim_speed']
    },
    'visualize': {
        'label': 'Visualize',
        'tooltip': 'Visualization\n\nTokens, Charts, Metrics',
        'tools': ['viz_tokens', 'viz_marking', 'viz_chart', 'viz_metrics']
    },
    'analyze': {
        'label': 'Analyze',
        'tooltip': 'Analysis\n\nExport, Statistics',
        'tools': ['analyze_export', 'analyze_stats']
    }
}


def get_categories_for_mode(mode: str):
    """Get category configuration for specified mode.
    
    Args:
        mode: 'edit' or 'simulate'
        
    Returns:
        dict: Category configuration
    """
    if mode == 'edit':
        return EDIT_MODE_CATEGORIES
    elif mode == 'simulate':
        return SIMULATE_MODE_CATEGORIES
    else:
        raise ValueError(f"Unknown mode: {mode}")


def create_tools_for_mode(mode: str):
    """Create all placeholder tools for specified mode.
    
    Args:
        mode: 'edit' or 'simulate'
        
    Returns:
        dict: Tool ID → PlaceholderTool instance
    """
    if mode == 'edit':
        return create_edit_mode_tools()
    elif mode == 'simulate':
        return create_simulate_mode_tools()
    else:
        raise ValueError(f"Unknown mode: {mode}")
