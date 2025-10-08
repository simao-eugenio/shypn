#!/usr/bin/env python3
"""Tools Palette - Place, Transition, Arc tool buttons."""

import sys
from shypn.edit.base_edit_palette import BaseEditPalette

try:
    from gi.repository import Gtk
except ImportError as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


class ToolsPalette(BaseEditPalette):
    """Palette for creation tools (Place, Transition, Arc).
    
    This palette contains toggle buttons for the three main
    Petri net creation tools. Only one tool can be active at a time.
    
    Buttons:
        [P] Place - Create places
        [T] Transition - Create transitions  
        [A] Arc - Create arcs between objects
    """
    
    def __init__(self):
        """Initialize tools palette."""
        super().__init__()
        self.current_tool = None
    
    def setup_buttons(self, button_widgets):
        """Setup button references from UI.
        
        Args:
            button_widgets: Dict with keys: 'place', 'transition', 'arc'
        """
        self.buttons = button_widgets
    
    def connect_signals(self):
        """Connect button toggle signals."""
        if 'place' in self.buttons:
            self.buttons['place'].connect(
                'toggled', 
                lambda b: self._on_tool_toggled('place', b)
            )
        
        if 'transition' in self.buttons:
            self.buttons['transition'].connect(
                'toggled',
                lambda b: self._on_tool_toggled('transition', b)
            )
        
        if 'arc' in self.buttons:
            self.buttons['arc'].connect(
                'toggled',
                lambda b: self._on_tool_toggled('arc', b)
            )
    
    def _on_tool_toggled(self, tool_name, button):
        """Handle tool button toggle.
        
        Args:
            tool_name: Tool name ('place', 'transition', 'arc')
            button: GtkToggleButton that was toggled
        """
        if self._updating:
            return
        
        is_active = button.get_active()
        
        if is_active:
            # Deactivate other tool buttons
            self._updating = True
            for name, btn in self.buttons.items():
                if name != tool_name and isinstance(btn, Gtk.ToggleButton):
                    btn.set_active(False)
            self._updating = False
            
            # Activate tool in canvas
            self.current_tool = tool_name
            if self.edit_operations and self.edit_operations.canvas_manager:
                self.edit_operations.canvas_manager.set_tool(tool_name)
            
            self.emit_tool_changed(tool_name)
        else:
            # Tool deactivated - return to pan mode
            self.current_tool = None
            if self.edit_operations and self.edit_operations.canvas_manager:
                self.edit_operations.canvas_manager.clear_tool()
            
            self.emit_tool_changed('')
    
    def apply_styling(self):
        """Apply light gray background with shadow styling to tools palette.
        
        Uses subtle styling with bottom shadow effect.
        """
        if self._css_applied:
            return
        
        css = """
        .gray-palette-frame {
            background-color: #E8E8E8;
            border: 1px solid #B0B0B0;
            border-bottom: 3px solid #808080;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .gray-palette-frame:backdrop {
            background-color: #E8E8E8;
            border: 1px solid #B0B0B0;
            border-bottom: 3px solid #808080;
        }
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8'))
        
        screen = self.revealer.get_screen()
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self._css_applied = True
    
    def get_current_tool(self):
        """Get currently active tool.
        
        Returns:
            str: Tool name or None
        """
        return self.current_tool
    
    def set_tool(self, tool_name):
        """Programmatically activate a tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc') or None
        """
        self._updating = True
        
        # Deactivate all tools
        for btn in self.buttons.values():
            if isinstance(btn, Gtk.ToggleButton):
                btn.set_active(False)
        
        # Activate requested tool
        if tool_name and tool_name in self.buttons:
            self.buttons[tool_name].set_active(True)
            self.current_tool = tool_name
        else:
            self.current_tool = None
        
        self._updating = False
