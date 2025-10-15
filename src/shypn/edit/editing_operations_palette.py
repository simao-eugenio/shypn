#!/usr/bin/env python3
"""Editing Operations Palette - Manages edit operations UI and state."""

from gi.repository import Gdk


class EditingOperationsPalette:
    """Manages the editing operations palette state and behavior.
    
    This class handles:
    - Revealer state (open/close)
    - Button state updates (enabled/disabled)
    - Keyboard shortcut handling
    - Delegation to EditOperations for actual operations
    
    This is separate from the loader to follow OOP principles:
    - Loader: Loads UI and connects signals
    - Palette: Manages state and behavior
    - Operations: Executes the actual operations
    """
    
    def __init__(self):
        """Initialize the editing operations palette."""
        self.edit_operations = None
        
        # Button references (set by loader)
        self.btn_lasso = None
        self.btn_undo = None
        self.btn_redo = None
        self.btn_duplicate = None
        self.btn_align = None
        self.btn_cut = None
        self.btn_copy = None
        self.btn_paste = None
    
    def set_edit_operations(self, edit_operations):
        """Set the edit operations manager.
        
        Args:
            edit_operations: EditOperations instance
        """
        self.edit_operations = edit_operations
    
    # Selection Tools
    def on_lasso_clicked(self):
        """Handle [L] Lasso clicked."""
        if self.edit_operations:
            self.edit_operations.activate_lasso_mode()
    
    # History Operations
    def on_undo_clicked(self):
        """Handle [U] Undo clicked."""
        if self.edit_operations:
            self.edit_operations.undo()
    
    def on_redo_clicked(self):
        """Handle [R] Redo clicked."""
        if self.edit_operations:
            self.edit_operations.redo()
    
    # Object Operations
    def on_duplicate_clicked(self):
        """Handle [D] Duplicate clicked."""
        if self.edit_operations:
            self.edit_operations.duplicate_selection()
    
    def on_align_clicked(self):
        """Handle [A] Align clicked."""
        if self.edit_operations:
            self.edit_operations.show_align_dialog()
    
    # Clipboard Operations
    def on_cut_clicked(self):
        """Handle [X] Cut clicked."""
        if self.edit_operations:
            self.edit_operations.cut()
    
    def on_copy_clicked(self):
        """Handle [C] Copy clicked."""
        if self.edit_operations:
            self.edit_operations.copy()
    
    def on_paste_clicked(self):
        """Handle [V] Paste clicked."""
        if self.edit_operations:
            self.edit_operations.paste()
    
    def update_button_states(self, undo_available=False, redo_available=False, has_selection=False):
        """Update enabled/disabled state of buttons.
        
        Args:
            undo_available: bool - Can undo
            redo_available: bool - Can redo
            has_selection: bool - Objects are selected
        """
        if self.btn_undo:
            self.btn_undo.set_sensitive(undo_available)
        if self.btn_redo:
            self.btn_redo.set_sensitive(redo_available)
        
        # Selection-dependent operations
        if self.btn_duplicate:
            self.btn_duplicate.set_sensitive(has_selection)
        if self.btn_align:
            self.btn_align.set_sensitive(has_selection)
        if self.btn_cut:
            self.btn_cut.set_sensitive(has_selection)
        if self.btn_copy:
            self.btn_copy.set_sensitive(has_selection)
    
    def handle_key_press(self, event):
        """Handle keyboard shortcuts.
        
        Args:
            event: GdkEventKey
            
        Returns:
            bool: True if handled, False otherwise
        """
        key = event.keyval
        
        # Don't intercept Ctrl+key combinations - let main handler deal with them
        is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if is_ctrl:
            return False
        
        # Selection tools
        if key == Gdk.KEY_l or key == Gdk.KEY_L:
            self.on_lasso_clicked()
            return True
        
        # History
        if key == Gdk.KEY_u or key == Gdk.KEY_U:
            self.on_undo_clicked()
            return True
        
        if key == Gdk.KEY_r or key == Gdk.KEY_R:
            self.on_redo_clicked()
            return True
        
        # Object operations
        if key == Gdk.KEY_d or key == Gdk.KEY_D:
            self.on_duplicate_clicked()
            return True
        
        if key == Gdk.KEY_a or key == Gdk.KEY_A:
            self.on_align_clicked()
            return True
        
        # Clipboard (without Ctrl modifier - these are legacy single-key shortcuts)
        if key == Gdk.KEY_x or key == Gdk.KEY_X:
            self.on_cut_clicked()
            return True
        
        if key == Gdk.KEY_c or key == Gdk.KEY_C:
            self.on_copy_clicked()
            return True
        
        if key == Gdk.KEY_v or key == Gdk.KEY_V:
            self.on_paste_clicked()
            return True
        
        return False
