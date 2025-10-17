#!/usr/bin/env python3
"""Individual Floating Buttons Manager - True floating buttons without containers.

This module creates individual floating buttons that are positioned independently
using halign/valign properties. No container boxes - pure floating buttons.

Layout: [P][T][A] GAP             self._updating = False
            
            self.current_tool = tool_name
            self.emit('tool-changed', tool_name)
        else:
            # Tool was deactivated
            self.current_tool = None
            self.emit('tool-changed', '') [U][R]
"""
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk, GObject
except Exception as e:
    print('ERROR: GTK3 not available in floating_buttons_manager:', e, file=sys.stderr)
    sys.exit(1)


class FloatingButtonsManager(GObject.GObject):
    """Manager for individual floating buttons without containers."""
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    # Tool constants
    TOOL_PLACE = 'place'
    TOOL_TRANSITION = 'transition'
    TOOL_ARC = 'arc'
    TOOL_SELECT = 'select'
    
    def __init__(self):
        """Initialize the floating buttons manager."""
        super().__init__()
        
        # Button widgets
        self.buttons = {}
        
        # Current tool
        self.current_tool = None
        
        # Edit operations (set externally)
        self.edit_operations = None
        
        # Signal blocking
        self._updating = False
        
        # CSS provider
        self.css_provider = None
        
        # Visibility state
        self._visible = False
    
    def create_all_buttons(self):
        """Create all floating buttons with proper positioning."""
        buttons = {}
        
        # Button width = 44px
        # Spacing between buttons = 88px (2 full button widths)
        # Total per button step = 132px (44 + 88)
        # Gap between groups = 176px (4 button widths)
        
        # Tool buttons (toggle, mutually exclusive)
        # [P] Place button
        buttons['place'] = self._create_toggle_button(
            label='P',
            tooltip='Place Tool: Create places (Ctrl+P)',
            x_offset=-396,  # Start of first group
            callback=self._on_tool_clicked,
            tool='place'
        )
        
        # [T] Transition button
        buttons['transition'] = self._create_toggle_button(
            label='T',
            tooltip='Transition Tool: Create transitions (Ctrl+T)',
            x_offset=-264,  # 132px from [P] (88px spacing)
            callback=self._on_tool_clicked,
            tool='transition'
        )
        
        # [A] Arc button
        buttons['arc'] = self._create_toggle_button(
            label='A',
            tooltip='Arc Tool: Create arcs (Ctrl+A)',
            x_offset=-132,  # 132px from [T] (88px spacing)
            callback=self._on_tool_clicked,
            tool='arc'
        )
        
        # GAP (176px = 4 button widths)
        
        # [S] Select button
        buttons['select'] = self._create_toggle_button(
            label='S',
            tooltip='Select Tool: Select and manipulate objects (Ctrl+S)',
            x_offset=44,  # 176px gap from [A]
            callback=self._on_tool_clicked,
            tool='select'
        )
        
        # [L] Lasso button
        buttons['lasso'] = self._create_button(
            label='L',
            tooltip='Lasso Selection: Select multiple objects',
            x_offset=176,  # 132px from [S] (88px spacing)
            callback=self._on_lasso_clicked
        )
        
        # GAP (176px = 4 button widths)
        
        # [U] Undo button
        buttons['undo'] = self._create_button(
            label='U',
            tooltip='Undo: Undo last action (Ctrl+Z)',
            x_offset=352,  # 176px gap from [L]
            callback=self._on_undo_clicked
        )
        buttons['undo'].set_sensitive(False)  # Initially disabled
        
        # [R] Redo button
        buttons['redo'] = self._create_button(
            label='R',
            tooltip='Redo: Redo undone action (Ctrl+Shift+Z)',
            x_offset=484,  # 132px from [U] (88px spacing)
            callback=self._on_redo_clicked
        )
        buttons['redo'].set_sensitive(False)  # Initially disabled
        
        # Store buttons
        self.buttons = buttons
        
        # Apply CSS styling
        self._apply_styling()
    
    def _create_button(self, label, tooltip, x_offset, callback, sensitive=True):
        """Create a regular button (non-toggle).
        
        Args:
            label: Button label text
            tooltip: Tooltip text
            x_offset: Horizontal offset from center (negative = left, positive = right)
            callback: Click callback function
            sensitive: Whether button is initially sensitive
            
        Returns:
            Gtk.Button: Configured button widget
        """
        btn = Gtk.Button(label=label)
        btn.set_tooltip_text(tooltip)
        btn.set_size_request(40, 40)
        btn.set_sensitive(sensitive)
        
        # Position: bottom with horizontal offset from center
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_valign(Gtk.Align.END)
        btn.set_margin_bottom(78)
        
        # Apply horizontal positioning offset from center
        # Negative = left of center, Positive = right of center
        if x_offset < 0:
            # Left of center
            btn.set_margin_end(abs(x_offset))
        elif x_offset > 0:
            # Right of center
            btn.set_margin_start(x_offset)
        
        # Add style class
        btn.get_style_context().add_class('floating-button')
        
        # Connect signal
        if callback:
            btn.connect('clicked', callback)
        
        return btn
    
    def _create_toggle_button(self, label, tooltip, x_offset, callback, tool=None):
        """Create a toggle button (for tools).
        
        Args:
            label: Button label text
            tooltip: Tooltip text
            x_offset: Horizontal offset from center
            callback: Toggled callback function
            tool: Tool name to pass to callback (optional)
            
        Returns:
            Gtk.ToggleButton: Configured toggle button widget
        """
        btn = Gtk.ToggleButton(label=label)
        btn.set_tooltip_text(tooltip)
        btn.set_size_request(40, 40)
        
        # Position: bottom with horizontal offset from center
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_valign(Gtk.Align.END)
        btn.set_margin_bottom(78)
        
        # Apply horizontal positioning offset from center
        # Negative = left of center, Positive = right of center
        if x_offset < 0:
            # Left of center
            btn.set_margin_end(abs(x_offset))
        elif x_offset > 0:
            # Right of center
            btn.set_margin_start(x_offset)
        
        # Add style classes
        btn.get_style_context().add_class('floating-button')
        btn.get_style_context().add_class('tool-button')
        
        # Connect signal with tool name if provided
        if callback:
            if tool:
                btn.connect('toggled', lambda b: callback(tool, b))
            else:
                btn.connect('toggled', callback)
        
        return btn
    
    def _apply_styling(self):
        """Apply CSS styling to buttons."""
        css = """
        .floating-button {
            background: linear-gradient(to bottom, #34495e, #2c3e50);
            border: 2px solid #1c2833;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            min-width: 44px;
            min-height: 44px;
            padding: 4px;
            margin: 0 4px;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3),
                        0 1px 3px rgba(0, 0, 0, 0.2);
        }
        
        .floating-button:hover {
            background: linear-gradient(to bottom, #2c3e50, #1c2833);
            box-shadow: 0 4px 8px rgba(52, 73, 94, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .tool-button:checked {
            background: linear-gradient(to bottom, #2980b9, #21618c);
            border-color: #1b4f72;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .tool-button:checked:hover {
            background: linear-gradient(to bottom, #21618c, #1b4f72);
        }
        """
        
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply to screen
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    # ==================== Event Handlers ====================
    
    def _on_tool_clicked(self, tool_name, toggle_button):
        """Handle tool button toggle.
        
        Args:
            tool_name: Name of the tool ('place', 'transition', 'arc', 'select')
            toggle_button: The toggle button that was clicked
        """
        if self._updating:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            # Deactivate other tool buttons
            self._updating = True
            for name, btn in self.buttons.items():
                if name in ['place', 'transition', 'arc', 'select'] and name != tool_name:
                    if isinstance(btn, Gtk.ToggleButton):
                        btn.set_active(False)
            self._updating = False
            
            self.current_tool = tool_name
            
            # Activate tool in canvas manager
            if self.edit_operations and self.edit_operations.canvas_manager:
                if tool_name == 'select':
                    # Select tool clears any active creation tool
                    self.edit_operations.canvas_manager.clear_tool()
                    self.edit_operations.activate_select_mode()
                else:
                    # Place, Transition, Arc tools
                    self.edit_operations.canvas_manager.set_tool(tool_name)
            
            self.emit('tool-changed', tool_name)
        else:
            # Allow deselection - return to pan mode
            self.current_tool = None
            
            if self.edit_operations and self.edit_operations.canvas_manager:
                self.edit_operations.canvas_manager.clear_tool()
            
            self.emit('tool-changed', '')
    
    def _on_lasso_clicked(self, button):
        """Handle Lasso button click."""
        if self.edit_operations:
            self.edit_operations.activate_lasso_mode()
        else:
            pass  # No edit operations available
    
    def _on_undo_clicked(self, button):
        """Handle Undo button click."""
        if self.edit_operations:
            self.edit_operations.undo()
        else:
            pass  # No edit operations available
    
    def _on_redo_clicked(self, button):
        """Handle Redo button click."""
        if self.edit_operations:
            self.edit_operations.redo()
        else:
            pass  # No edit operations available
    
    # ==================== Public API ====================
    
    def get_buttons(self):
        """Get all button widgets for adding to overlay.
        
        Returns:
            dict: Dictionary of button name -> button widget
        """
        return self.buttons
    
    def show_all(self):
        """Show all buttons."""
        for btn in self.buttons.values():
            btn.show()
        self._visible = True
    
    def hide_all(self):
        """Hide all buttons."""
        for btn in self.buttons.values():
            btn.hide()
        self._visible = False
    
    def is_visible(self):
        """Check if buttons are visible.
        
        Returns:
            bool: True if visible
        """
        return self._visible
    
    def set_tool(self, tool_name):
        """Programmatically set active tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc', 'select') or None
        """
        self._updating = True
        
        # Deactivate all tools
        for name in ['place', 'transition', 'arc', 'select']:
            if name in self.buttons:
                btn = self.buttons[name]
                if isinstance(btn, Gtk.ToggleButton):
                    btn.set_active(False)
        
        # Activate requested tool
        if tool_name and tool_name in self.buttons:
            btn = self.buttons[tool_name]
            if isinstance(btn, Gtk.ToggleButton):
                btn.set_active(True)
            self.current_tool = tool_name
        else:
            self.current_tool = None
        
        self._updating = False
    
    def get_current_tool(self):
        """Get currently active tool.
        
        Returns:
            str: Current tool name or None
        """
        return self.current_tool
    
    def set_edit_operations(self, edit_operations):
        """Set edit operations instance.
        
        Args:
            edit_operations: EditOperations instance
        """
        self.edit_operations = edit_operations
        
        # Set state change callback to update button states
        if edit_operations:
            edit_operations.set_state_change_callback(self._on_state_changed)
            # Initial update
            self.update_button_states()
    
    def _on_state_changed(self, undo_available, redo_available, has_selection):
        """Handle state changes from EditOperations.
        
        Args:
            undo_available: bool - Whether undo is available
            redo_available: bool - Whether redo is available
            has_selection: bool - Whether objects are selected
        """
        # Update undo/redo button states
        if 'undo' in self.buttons:
            self.buttons['undo'].set_sensitive(undo_available)
        if 'redo' in self.buttons:
            self.buttons['redo'].set_sensitive(redo_available)
    
    def update_button_states(self):
        """Update button sensitivity based on context."""
        if not self.edit_operations:
            return
        
        # Update undo/redo states
        undo_avail = self.edit_operations.can_undo()
        redo_avail = self.edit_operations.can_redo()
        
        if 'undo' in self.buttons:
            self.buttons['undo'].set_sensitive(undo_avail)
        if 'redo' in self.buttons:
            self.buttons['redo'].set_sensitive(redo_avail)


def create_floating_buttons_manager():
    """Convenience function to create floating buttons manager.
    
    Returns:
        FloatingButtonsManager: Configured manager instance
        
    Example:
        manager = create_floating_buttons_manager()
        manager.create_all_buttons()
        
        # Add each button to overlay
        for btn in manager.get_buttons().values():
            overlay.add_overlay(btn)
        
        # Control visibility
        manager.show_all()  # or hide_all()
    """
    manager = FloatingButtonsManager()
    manager.create_all_buttons()
    return manager
