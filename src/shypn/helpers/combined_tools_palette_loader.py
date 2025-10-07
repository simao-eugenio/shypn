#!/usr/bin/env python3
"""Combined Tools Palette Loader - Unified palette for all edit tools and operations.

This module provides a single unified palette that combines:
- Edit tools: [S][P][T][A] (Select, Place, Transition, Arc)
- Operations: [U][R][L][D][A][X][C][V] (Undo, Redo, Lasso, Duplicate, Align, Cut, Copy, Paste)

All tools are in one horizontal revealer, controlled by the [E] button.
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject
except Exception as e:
    print('ERROR: GTK3 not available in combined_tools_palette_loader:', e, file=sys.stderr)
    sys.exit(1)


class CombinedToolsPaletteLoader(GObject.GObject):
    """Manager for the combined tools palette with all edit tools and operations."""
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    # Tool constants (for edit tools)
    TOOL_NONE = None
    TOOL_SELECT = 'select'
    TOOL_PLACE = 'place'
    TOOL_TRANSITION = 'transition'
    TOOL_ARC = 'arc'
    
    def __init__(self, ui_path=None):
        """Initialize the combined tools palette loader.
        
        Args:
            ui_path: Optional path to combined_tools_palette.ui. If None, uses default location.
        """
        super().__init__()
        
        if ui_path is None:
            # Default: ui/palettes/combined_tools_palette.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'palettes', 'combined_tools_palette.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.combined_tools_revealer = None
        self.combined_tools_container = None
        
        # Edit tool buttons (toggle buttons)
        self.select_tool_button = None
        self.place_tool_button = None
        self.transition_tool_button = None
        self.arc_tool_button = None
        
        # Operation buttons (regular buttons)
        self.btn_undo = None
        self.btn_redo = None
        self.btn_lasso = None
        self.btn_duplicate = None
        self.btn_align = None
        self.btn_cut = None
        self.btn_copy = None
        self.btn_paste = None
        
        # Current active tool
        self.current_tool = self.TOOL_NONE
        
        # Signal blocking flags
        self._updating_buttons = False
        
        # CSS provider for styling
        self.css_provider = None
        
        # Edit operations instance (will be set externally)
        self.edit_operations = None
    
    def load(self):
        """Load the combined tools palette UI and return the widget.
        
        Returns:
            Gtk.Revealer: The combined tools revealer widget.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If required objects not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Combined tools palette UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract widgets
        self.combined_tools_revealer = self.builder.get_object('combined_tools_revealer')
        self.combined_tools_container = self.builder.get_object('combined_tools_container')
        
        # Edit tool buttons
        self.select_tool_button = self.builder.get_object('select_tool_button')
        self.place_tool_button = self.builder.get_object('place_tool_button')
        self.transition_tool_button = self.builder.get_object('transition_tool_button')
        self.arc_tool_button = self.builder.get_object('arc_tool_button')
        
        # Operation buttons
        self.btn_undo = self.builder.get_object('btn_undo')
        self.btn_redo = self.builder.get_object('btn_redo')
        self.btn_lasso = self.builder.get_object('btn_lasso')
        self.btn_duplicate = self.builder.get_object('btn_duplicate')
        self.btn_align = self.builder.get_object('btn_align')
        self.btn_cut = self.builder.get_object('btn_cut')
        self.btn_copy = self.builder.get_object('btn_copy')
        self.btn_paste = self.builder.get_object('btn_paste')
        
        if self.combined_tools_revealer is None:
            raise ValueError("Object 'combined_tools_revealer' not found in combined_tools_palette.ui")
        
        # Verify all buttons exist
        if not all([self.select_tool_button, self.place_tool_button, 
                   self.transition_tool_button, self.arc_tool_button]):
            raise ValueError("One or more tool buttons not found in combined_tools_palette.ui")
        
        if not all([self.btn_undo, self.btn_redo, self.btn_lasso, self.btn_duplicate,
                   self.btn_align, self.btn_cut, self.btn_copy, self.btn_paste]):
            raise ValueError("One or more operation buttons not found in combined_tools_palette.ui")
        
        # Connect signals
        self._connect_tool_signals()
        self._connect_operation_signals()
        
        # Apply custom CSS styling
        self._apply_styling()
        
        return self.combined_tools_revealer
    
    def _connect_tool_signals(self):
        """Connect edit tool button signals."""
        self.select_tool_button.connect('toggled', self._on_select_toggled)
        self.place_tool_button.connect('toggled', self._on_place_toggled)
        self.transition_tool_button.connect('toggled', self._on_transition_toggled)
        self.arc_tool_button.connect('toggled', self._on_arc_toggled)
    
    def _connect_operation_signals(self):
        """Connect operation button signals."""
        if self.btn_undo:
            self.btn_undo.connect('clicked', lambda btn: self._on_undo_clicked())
        if self.btn_redo:
            self.btn_redo.connect('clicked', lambda btn: self._on_redo_clicked())
        if self.btn_lasso:
            self.btn_lasso.connect('clicked', lambda btn: self._on_lasso_clicked())
        if self.btn_duplicate:
            self.btn_duplicate.connect('clicked', lambda btn: self._on_duplicate_clicked())
        if self.btn_align:
            self.btn_align.connect('clicked', lambda btn: self._on_align_clicked())
        if self.btn_cut:
            self.btn_cut.connect('clicked', lambda btn: self._on_cut_clicked())
        if self.btn_copy:
            self.btn_copy.connect('clicked', lambda btn: self._on_copy_clicked())
        if self.btn_paste:
            self.btn_paste.connect('clicked', lambda btn: self._on_paste_clicked())
    
    def _apply_styling(self):
        """Apply custom CSS styling to the combined tools palette."""
        css = """
        .combined-tools-palette {
            background: linear-gradient(to bottom, #f0f0f5, #e8e8ee);
            border: 1px solid #b0b0b8;
            border-radius: 8px;
            padding: 8px 12px;
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
    
    # ==================== Tool Button Event Handlers ====================
    
    def _on_select_toggled(self, toggle_button):
        """Handle Select tool button toggle."""
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            self._updating_buttons = True
            self.place_tool_button.set_active(False)
            self.transition_tool_button.set_active(False)
            self.arc_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_SELECT
            self.emit('tool-changed', self.TOOL_SELECT)
        else:
            if not any([self.place_tool_button.get_active(), 
                       self.transition_tool_button.get_active(),
                       self.arc_tool_button.get_active()]):
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    def _on_place_toggled(self, toggle_button):
        """Handle Place tool button toggle."""
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            self._updating_buttons = True
            self.select_tool_button.set_active(False)
            self.transition_tool_button.set_active(False)
            self.arc_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_PLACE
            self.emit('tool-changed', self.TOOL_PLACE)
        else:
            if not any([self.select_tool_button.get_active(),
                       self.transition_tool_button.get_active(), 
                       self.arc_tool_button.get_active()]):
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    def _on_transition_toggled(self, toggle_button):
        """Handle Transition tool button toggle."""
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            self._updating_buttons = True
            self.select_tool_button.set_active(False)
            self.place_tool_button.set_active(False)
            self.arc_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_TRANSITION
            self.emit('tool-changed', self.TOOL_TRANSITION)
        else:
            if not any([self.select_tool_button.get_active(),
                       self.place_tool_button.get_active(),
                       self.arc_tool_button.get_active()]):
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    def _on_arc_toggled(self, toggle_button):
        """Handle Arc tool button toggle."""
        if self._updating_buttons:
            return
        
        is_active = toggle_button.get_active()
        
        if is_active:
            self._updating_buttons = True
            self.select_tool_button.set_active(False)
            self.place_tool_button.set_active(False)
            self.transition_tool_button.set_active(False)
            self._updating_buttons = False
            
            self.current_tool = self.TOOL_ARC
            self.emit('tool-changed', self.TOOL_ARC)
        else:
            if not any([self.select_tool_button.get_active(),
                       self.place_tool_button.get_active(),
                       self.transition_tool_button.get_active()]):
                self.current_tool = self.TOOL_NONE
                self.emit('tool-changed', '')
    
    # ==================== Operation Button Event Handlers ====================
    
    def _on_undo_clicked(self):
        """Handle Undo button click."""
        if self.edit_operations:
            self.edit_operations.undo()
        print("[CombinedTools] Undo clicked")
    
    def _on_redo_clicked(self):
        """Handle Redo button click."""
        if self.edit_operations:
            self.edit_operations.redo()
        print("[CombinedTools] Redo clicked")
    
    def _on_lasso_clicked(self):
        """Handle Lasso button click."""
        print("[CombinedTools] Lasso clicked - TODO: Implement lasso selection")
    
    def _on_duplicate_clicked(self):
        """Handle Duplicate button click."""
        if self.edit_operations:
            self.edit_operations.duplicate_selection()
        print("[CombinedTools] Duplicate clicked")
    
    def _on_align_clicked(self):
        """Handle Align button click."""
        if self.edit_operations:
            self.edit_operations.align_selected()
        print("[CombinedTools] Align clicked")
    
    def _on_cut_clicked(self):
        """Handle Cut button click."""
        if self.edit_operations:
            self.edit_operations.cut()
        print("[CombinedTools] Cut clicked")
    
    def _on_copy_clicked(self):
        """Handle Copy button click."""
        if self.edit_operations:
            self.edit_operations.copy()
        print("[CombinedTools] Copy clicked")
    
    def _on_paste_clicked(self):
        """Handle Paste button click."""
        if self.edit_operations:
            self.edit_operations.paste()
        print("[CombinedTools] Paste clicked")
    
    # ==================== Public API ====================
    
    def show(self):
        """Show the combined tools palette by revealing it."""
        if self.combined_tools_revealer:
            self.combined_tools_revealer.set_reveal_child(True)
    
    def hide(self):
        """Hide the combined tools palette by unrevealing it."""
        if self.combined_tools_revealer:
            self.combined_tools_revealer.set_reveal_child(False)
    
    def is_visible(self):
        """Check if the palette is currently visible.
        
        Returns:
            bool: True if palette is revealed, False otherwise.
        """
        if self.combined_tools_revealer:
            return self.combined_tools_revealer.get_reveal_child()
        return False
    
    def get_widget(self):
        """Get the combined tools revealer widget.
        
        Returns:
            Gtk.Revealer: The combined tools revealer widget, or None if not loaded.
        """
        return self.combined_tools_revealer
    
    def get_current_tool(self):
        """Get the currently selected tool.
        
        Returns:
            str: Tool name ('select', 'place', 'transition', 'arc') or None if no tool selected.
        """
        return self.current_tool
    
    def set_tool(self, tool_name):
        """Programmatically set the active tool.
        
        Args:
            tool_name: Tool to activate ('select', 'place', 'transition', 'arc') or None to clear.
        """
        self._updating_buttons = True
        
        # Deactivate all buttons first
        self.select_tool_button.set_active(False)
        self.place_tool_button.set_active(False)
        self.transition_tool_button.set_active(False)
        self.arc_tool_button.set_active(False)
        
        # Activate the requested tool
        if tool_name == self.TOOL_SELECT:
            self.select_tool_button.set_active(True)
            self.current_tool = self.TOOL_SELECT
        elif tool_name == self.TOOL_PLACE:
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
    
    def set_edit_operations(self, edit_operations):
        """Set the EditOperations instance for operation buttons.
        
        Args:
            edit_operations: EditOperations instance.
        """
        self.edit_operations = edit_operations
    
    def update_button_states(self):
        """Update button states (e.g., enable/disable based on context)."""
        # TODO: Implement based on undo/redo stack state
        pass


def create_combined_tools_palette(ui_path=None):
    """Convenience function to create and load the combined tools palette.
    
    Args:
        ui_path: Optional path to combined_tools_palette.ui.
        
    Returns:
        CombinedToolsPaletteLoader: The loaded combined tools palette instance.
        
    Example:
        combined_palette = create_combined_tools_palette()
        widget = combined_palette.load()
        combined_palette.connect('tool-changed', on_tool_changed_callback)
        combined_palette.set_edit_operations(edit_ops_instance)
        # Add widget as overlay to canvas
    """
    palette = CombinedToolsPaletteLoader(ui_path)
    palette.load()
    return palette
