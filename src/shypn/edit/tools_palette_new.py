#!/usr/bin/env python3
"""Tools Palette - Edit mode tool selection (Place, Transition, Arc).

Provides buttons for creating Petri Net elements:
- Place (P): Create place nodes
- Transition (T): Create transition nodes
- Arc (A): Create arcs between nodes

Architecture:
    Pure Python/OOP - no UI file dependency
    Extends BasePalette for common functionality
"""

from shypn.edit.base_palette import BasePalette
from gi.repository import GObject, Gtk


class ToolsPalette(BasePalette):
    """Palette for Petri Net creation tools.
    
    Provides toggle buttons for Place, Transition, and Arc tools.
    Only one tool can be active at a time (radio button behavior).
    
    Signals:
        tool-selected(str): Emitted when a tool is activated/deactivated
                           Tool name or empty string for none
    """
    
    __gsignals__ = {
        'tool-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self):
        """Initialize tools palette."""
        # Call parent with palette ID and horizontal orientation
        super().__init__(palette_id='tools', orientation=Gtk.Orientation.HORIZONTAL)
        
        self.current_tool = None
        self._updating = False
    
    def _create_content(self):
        """Create palette-specific content (Place, Transition, Arc buttons).
        
        Implementation of BasePalette abstract method.
        """
        # Create Place button
        self.buttons['place'] = self._create_tool_button(
            'P', 
            'Place Tool (Ctrl+P)\n\nCreate circular place nodes'
        )
        
        # Create Transition button
        self.buttons['transition'] = self._create_tool_button(
            'T',
            'Transition Tool (Ctrl+T)\n\nCreate rectangular transition nodes'
        )
        
        # Create Arc button
        self.buttons['arc'] = self._create_tool_button(
            'A',
            'Arc Tool (Ctrl+A)\n\nCreate arcs between places and transitions'
        )
        
        # Add buttons to content box
        for button in self.buttons.values():
            self.content_box.pack_start(button, False, False, 0)
        
        print(f"[ToolsPalette] Created {len(self.buttons)} tool buttons")
    
    def _create_tool_button(self, label: str, tooltip: str) -> Gtk.ToggleButton:
        """Create a styled tool toggle button.
        
        Args:
            label: Button label text
            tooltip: Tooltip text
            
        Returns:
            GtkToggleButton: Configured button
        """
        button = Gtk.ToggleButton(label=label)
        button.set_tooltip_text(tooltip)
        button.set_size_request(40, 40)
        button.get_style_context().add_class('tool-button')
        button.set_visible(True)  # Ensure button is visible
        button.show()  # Explicitly show button
        return button
    
    def _connect_signals(self):
        """Connect button toggle signals.
        
        Implementation of BasePalette abstract method.
        """
        for tool_name, button in self.buttons.items():
            button.connect('toggled', self._on_tool_toggled, tool_name)
    
    def _on_tool_toggled(self, button: Gtk.ToggleButton, tool_name: str):
        """Handle tool button toggle.
        
        Args:
            button: The button that was toggled
            tool_name: Name of the tool ('place', 'transition', 'arc')
        """
        if self._updating:
            return
        
        is_active = button.get_active()
        
        if is_active:
            # Deactivate other tool buttons (radio behavior)
            self._updating = True
            for name, btn in self.buttons.items():
                if name != tool_name:
                    btn.set_active(False)
            self._updating = False
            
            # Set as current tool
            self.current_tool = tool_name
            self.emit('tool-selected', tool_name)
            print(f"[ToolsPalette] Tool activated: {tool_name}")
        else:
            # Tool deactivated - return to no tool
            if self.current_tool == tool_name:
                self.current_tool = None
                self.emit('tool-selected', '')
                print(f"[ToolsPalette] Tool deactivated: {tool_name}")
    
    def _get_css(self) -> bytes:
        """Get tools palette CSS styling with dramatic floating effect.
        
        Implementation of BasePalette abstract method.
        
        Returns:
            bytes: CSS data for tools palette with floating shadows
        """
        return b"""
        /* ============================================
           Tools Palette - Floating Effect (Zoom Palette Style)
           Strong shadows and gradients like zoom palette
           ============================================ */
        
        .palette-tools {
            /* Strong white gradient background */
            background: linear-gradient(to bottom, #f5f5f5 0%, #d8d8d8 100%);
            border: 2px solid #999999;
            border-radius: 8px;
            padding: 3px;
            /* STRONG shadow like zoom palette */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        
        .palette-tools:hover {
            /* Enhanced on hover */
            border-color: #3584e4;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.45),
                        0 3px 6px rgba(0, 0, 0, 0.35),
                        0 0 12px rgba(53, 132, 228, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }
        
        .palette-tools .tool-button {
            /* White gradient like zoom buttons */
            background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
            border: 2px solid #999999;
            border-radius: 5px;
            color: #2e3436;
            font-weight: bold;
            font-size: 18px;
            min-width: 36px;
            min-height: 36px;
            padding: 0;
            margin: 0;
            transition: all 200ms ease;
        }
        
        .palette-tools .tool-button:hover {
            /* Light blue tint on hover like zoom */
            background: linear-gradient(to bottom, #e8f0ff 0%, #d5e5ff 100%);
            border-color: #3584e4;
            color: #1c71d8;
            box-shadow: 0 0 8px rgba(53, 132, 228, 0.5);
        }
        
        .palette-tools .tool-button:active {
            background: linear-gradient(to bottom, #d0e0ff 0%, #c0d5ff 100%);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .palette-tools .tool-button:checked {
            /* Strong blue gradient when active */
            background: linear-gradient(to bottom, #3584e4 0%, #1c71d8 100%);
            color: white;
            border-color: #1a5fb4;
            box-shadow: 0 0 12px rgba(53, 132, 228, 0.6),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        
        .palette-tools .tool-button:checked:hover {
            background: linear-gradient(to bottom, #4590f4 0%, #2c82e8 100%);
            box-shadow: 0 0 16px rgba(53, 132, 228, 0.7),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }
        """
    
    # ==================== Public API ====================
    
    def get_current_tool(self) -> str:
        """Get currently active tool.
        
        Returns:
            str: Tool name ('place', 'transition', 'arc') or None
        """
        return self.current_tool
    
    def set_tool(self, tool_name: str):
        """Programmatically activate a tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc') or None/empty
        """
        self._updating = True
        
        # Deactivate all tools
        for button in self.buttons.values():
            button.set_active(False)
        
        # Activate requested tool
        if tool_name and tool_name in self.buttons:
            self.buttons[tool_name].set_active(True)
            self.current_tool = tool_name
        else:
            self.current_tool = None
        
        self._updating = False
    
    def clear_tool(self):
        """Clear active tool (deactivate all)."""
        self.set_tool(None)


# Register GObject type
GObject.type_register(ToolsPalette)
