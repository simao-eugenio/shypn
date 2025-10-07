#!/usr/bin/env python3
"""Operations Palette - Select, Lasso, Undo, Redo buttons."""

import sys
from shypn.edit.base_edit_palette import BaseEditPalette

try:
    from gi.repository import Gtk
except ImportError as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


class OperationsPalette(BaseEditPalette):
    """Palette for selection and editing operations.
    
    This palette contains buttons for selection modes and
    edit history operations (undo/redo).
    
    Buttons:
        [S] Select - Rectangle selection mode
        [L] Lasso - Freeform lasso selection
        [U] Undo - Undo last operation
        [R] Redo - Redo undone operation
    """
    
    def __init__(self):
        """Initialize operations palette."""
        super().__init__()
        self.select_active = False
    
    def setup_buttons(self, button_widgets):
        """Setup button references from UI.
        
        Args:
            button_widgets: Dict with keys: 'select', 'lasso', 'undo', 'redo'
        """
        self.buttons = button_widgets
    
    def connect_signals(self):
        """Connect button signals."""
        if 'select' in self.buttons:
            self.buttons['select'].connect('toggled', self._on_select_toggled)
        
        if 'lasso' in self.buttons:
            self.buttons['lasso'].connect('clicked', self._on_lasso_clicked)
        
        if 'undo' in self.buttons:
            self.buttons['undo'].connect('clicked', self._on_undo_clicked)
        
        if 'redo' in self.buttons:
            self.buttons['redo'].connect('clicked', self._on_redo_clicked)
    
    def _on_select_toggled(self, button):
        """Handle select button toggle.
        
        Args:
            button: GtkToggleButton for select mode
        """
        is_active = button.get_active()
        self.select_active = is_active
        
        if is_active:
            if self.edit_operations:
                self.edit_operations.activate_select_mode()
                if self.edit_operations.canvas_manager:
                    self.edit_operations.canvas_manager.clear_tool()
            
            self.emit_tool_changed('select')
            print("[OperationsPalette] Select mode activated")
        else:
            self.emit_tool_changed('')
            print("[OperationsPalette] Select mode deactivated")
    
    def _on_lasso_clicked(self, button):
        """Handle lasso button click.
        
        Args:
            button: GtkButton for lasso selection
        """
        if self.edit_operations:
            self.edit_operations.activate_lasso_mode()
            print("[OperationsPalette] Lasso mode activated")
        else:
            print("[OperationsPalette] ERROR: edit_operations not set", file=sys.stderr)
    
    def _on_undo_clicked(self, button):
        """Handle undo button click.
        
        Args:
            button: GtkButton for undo
        """
        if self.edit_operations:
            self.edit_operations.undo()
            print("[OperationsPalette] Undo triggered")
        else:
            print("[OperationsPalette] ERROR: edit_operations not set", file=sys.stderr)
    
    def _on_redo_clicked(self, button):
        """Handle redo button click.
        
        Args:
            button: GtkButton for redo
        """
        if self.edit_operations:
            self.edit_operations.redo()
            print("[OperationsPalette] Redo triggered")
        else:
            print("[OperationsPalette] ERROR: edit_operations not set", file=sys.stderr)
    
    def set_edit_operations(self, edit_operations):
        """Set edit operations and register state callback.
        
        Args:
            edit_operations: EditOperations instance
        """
        super().set_edit_operations(edit_operations)
        
        # Register for state change notifications
        if edit_operations:
            edit_operations.set_state_change_callback(self._on_state_changed)
            self._update_button_states()
    
    def _on_state_changed(self, undo_available, redo_available, has_selection):
        """Handle state changes from EditOperations.
        
        Args:
            undo_available: bool - Can undo
            redo_available: bool - Can redo  
            has_selection: bool - Objects selected
        """
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button sensitivity based on operation availability."""
        if not self.edit_operations:
            return
        
        # Update undo/redo button states
        undo_avail = self.edit_operations.can_undo()
        redo_avail = self.edit_operations.can_redo()
        
        if 'undo' in self.buttons:
            self.buttons['undo'].set_sensitive(undo_avail)
        
        if 'redo' in self.buttons:
            self.buttons['redo'].set_sensitive(redo_avail)
    
    def apply_styling(self):
        """Apply light gray background with shadow styling to operations palette.
        
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
        print("[OperationsPalette] Light gray background with bottom shadow applied")
