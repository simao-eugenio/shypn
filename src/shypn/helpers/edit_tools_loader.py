#!/usr/bin/env python3
"""Edit Tools Palette Loader - Place, Transition, Arc Tool Buttons.

This module provides a floating tools palette that contains tool selection
buttons for Petri net object creation:
- [P] Place Tool
- [T] Transition Tool  
- [A] Arc Tool

The buttons implement radio button behavior (only one can be active at a time).
When a tool is selected, a 'tool-changed' signal is emitted.
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject
except Exception as e:
    print('ERROR: GTK3 not available in edit_tools_loader:', e, file=sys.stderr)
    sys.exit(1)


class EditToolsLoader(GObject.GObject):
    """Manager for the edit tools palette with P, T, A buttons."""
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    # Tool constants
    TOOL_NONE = None
    TOOL_PLACE = 'place'
    TOOL_TRANSITION = 'transition'
    TOOL_ARC = 'arc'
    
    def __init__(self, ui_path=None):
        """Initialize the edit tools palette loader.
        
        Args:
            ui_path: Optional path to edit_tools_palette.ui. If None, uses default location.
        """
        super().__init__()
        
        if ui_path is None:
            # Default: ui/palettes/edit_tools_palette.ui
            # This loader file is in: src/shypn/helpers/edit_tools_loader.py
            # UI file is in: ui/palettes/edit_tools_palette.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'palettes', 'edit_tools_palette.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.edit_tools_revealer = None  # Revealer container
        self.edit_tools_container = None  # Tools box
        
        # Tool buttons
        self.place_tool_button = None
        self.transition_tool_button = None
        self.arc_tool_button = None
        
        # Current active tool
        self.current_tool = self.TOOL_NONE
        
        # Signal blocking flags (to prevent recursion during programmatic changes)
        self._updating_buttons = False
        
        # CSS provider for styling
        self.css_provider = None
    
    def load(self):
        """Load the edit tools palette UI and return the widget.
        
        Returns:
            Gtk.Revealer: The edit tools revealer widget.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If required objects not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Edit tools palette UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract widgets
        self.edit_tools_revealer = self.builder.get_object('edit_tools_revealer')
        self.edit_tools_container = self.builder.get_object('edit_tools_container')
        self.place_tool_button = self.builder.get_object('place_tool_button')
        self.transition_tool_button = self.builder.get_object('transition_tool_button')
        self.arc_tool_button = self.builder.get_object('arc_tool_button')
        
        if self.edit_tools_revealer is None:
            raise ValueError("Object 'edit_tools_revealer' not found in edit_tools_palette.ui")
        
        # Verify all buttons exist
        if not all([self.place_tool_button, self.transition_tool_button, self.arc_tool_button]):
            raise ValueError("One or more tool buttons not found in edit_tools_palette.ui")
        
        # Connect button signals
        self.place_tool_button.connect('toggled', self._on_place_toggled)
        self.transition_tool_button.connect('toggled', self._on_transition_toggled)
        self.arc_tool_button.connect('toggled', self._on_arc_toggled)
        
        # Apply custom CSS styling
        self._apply_styling()
        
        return self.edit_tools_revealer
    
    def _apply_styling(self):
        """Apply custom CSS styling to the edit tools palette."""
        css = """
        .edit-tools-palette {
            background: linear-gradient(to bottom, #f0f0f5, #e8e8ee);
            border: 1px solid #b0b0b8;
            border-radius: 8px;
            padding: 8px 12px 8px 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 2px 8px rgba(0,0,0,0.18);
        }
        
        .tool-button {
            background: #ffffff;
            border: 1px solid #c0c0c8;
            border-radius: 4px;
            font-size: 14px;
            font-weight: normal;
            color: #2a2a3a;
            min-width: 40px;
            min-height: 40px;
            padding: 0;
            margin: 0;
        }
        
        .tool-button:hover {
            background: #e8f0ff;
            border-color: #6090d0;
        }
        
        .tool-button:active,
        .tool-button:checked {
            background: #4a90e2;
            color: white;
            border: 2px solid #2a70c2;
            font-weight: bold;
            box-shadow: 0 0 8px rgba(74, 144, 226, 0.5);
        }
        """
        
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply to screen
        from gi.repository import Gdk
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    # ==================== Event Handlers ====================
    
    def _on_place_toggled(self, toggle_button):
        """Handle Place tool button toggle.
        
        Args:
            toggle_button: GtkToggleButton that was toggled.
        """
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            # Place tool selected - deactivate other tools
            self._updating_buttons = True
            self.transition_tool_button.set_active(False)
            self.arc_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_PLACE
            self.emit('tool-changed', self.TOOL_PLACE)
        else:
            # Place tool deselected - if no other tool is active, clear selection
            if not self.transition_tool_button.get_active() and not self.arc_tool_button.get_active():
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    def _on_transition_toggled(self, toggle_button):
        """Handle Transition tool button toggle.
        
        Args:
            toggle_button: GtkToggleButton that was toggled.
        """
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            # Transition tool selected - deactivate other tools
            self._updating_buttons = True
            self.place_tool_button.set_active(False)
            self.arc_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_TRANSITION
            self.emit('tool-changed', self.TOOL_TRANSITION)
        else:
            # Transition tool deselected
            if not self.place_tool_button.get_active() and not self.arc_tool_button.get_active():
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    def _on_arc_toggled(self, toggle_button):
        """Handle Arc tool button toggle.
        
        Args:
            toggle_button: GtkToggleButton that was toggled.
        """
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            # Arc tool selected - deactivate other tools
            self._updating_buttons = True
            self.place_tool_button.set_active(False)
            self.transition_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_ARC
            self.emit('tool-changed', self.TOOL_ARC)
        else:
            # Arc tool deselected
            if not self.place_tool_button.get_active() and not self.transition_tool_button.get_active():
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    # ==================== Public API ====================
    
    def show(self):
        """Show the tools palette with animation."""
        if self.edit_tools_revealer:
            self.edit_tools_revealer.set_reveal_child(True)
    
    def hide(self):
        """Hide the tools palette with animation."""
        if self.edit_tools_revealer:
            self.edit_tools_revealer.set_reveal_child(False)
    
    def is_visible(self):
        """Check if the tools palette is currently visible.
        
        Returns:
            bool: True if palette is revealed, False otherwise.
        """
        if self.edit_tools_revealer:
            return self.edit_tools_revealer.get_reveal_child()
        return False
    
    def get_widget(self):
        """Get the edit tools revealer widget.
        
        Returns:
            Gtk.Revealer: The edit tools revealer widget, or None if not loaded.
        """
        return self.edit_tools_revealer
    
    def get_current_tool(self):
        """Get the currently selected tool.
        
        Returns:
            str: Tool name ('place', 'transition', 'arc') or None if no tool selected.
        """
        return self.current_tool
    
    def set_tool(self, tool_name):
        """Programmatically set the active tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc') or None to clear.
        """
        self._updating_buttons = True
        
        # Deactivate all buttons first
        self.place_tool_button.set_active(False)
        self.transition_tool_button.set_active(False)
        self.arc_tool_button.set_active(False)
        
        # Activate the requested tool
        if tool_name == self.TOOL_PLACE:
            self.place_tool_button.set_active(True)
            self.current_tool = self.TOOL_PLACE
        elif tool_name == self.TOOL_TRANSITION:
            self.transition_tool_button.set_active(True)
            self.current_tool = self.TOOL_TRANSITION
        elif tool_name == self.TOOL_ARC:
            self.arc_tool_button.set_active(True)
            self.current_tool = self.TOOL_ARC
        else:
            self.current_tool = self.TOOL_NONE
        
        self._updating_buttons = False
        
        # Emit signal
        self.emit('tool-changed', tool_name or '')
    
    def clear_tool(self):
        """Clear the active tool selection."""
        self.set_tool(None)


def create_edit_tools_palette(ui_path=None):
    """Convenience function to create and load the edit tools palette.
    
    Args:
        ui_path: Optional path to edit_tools_palette.ui.
        
    Returns:
        EditToolsLoader: The loaded edit tools palette instance.
        
    Example:
        tools_palette = create_edit_tools_palette()
        widget = tools_palette.load()
        tools_palette.connect('tool-changed', on_tool_changed_callback)
        # Add widget as overlay to canvas
    """
    palette = EditToolsLoader(ui_path)
    palette.load()
    return palette
