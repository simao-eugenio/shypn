#!/usr/bin/env python3
"""Editing Operations Palette Loader - Loads UI for editing operations palette."""

from shypn.edit.base_palette_loader import BasePaletteLoader
from shypn.edit.editing_operations_palette import EditingOperationsPalette


class EditingOperationsPaletteLoader(BasePaletteLoader):
    """Loader for the editing operations palette.
    
    Responsibilities:
    - Load editing_operations_palette.ui
    - Get widget references
    - Connect signals to palette handlers
    
    Does NOT contain business logic - that's in EditingOperationsPalette.
    """
    
    def __init__(self, parent_window=None):
        """Initialize the loader.
        
        Args:
            parent_window: Parent GTK window
        """
        super().__init__(parent_window)
        self.palette = EditingOperationsPalette()
    
    def get_ui_filename(self):
        """Return the UI filename to load.
        
        Returns:
            str: UI filename
        """
        return 'editing_operations_palette.ui'
    
    def get_widget_references(self):
        """Get references to widgets from the builder."""
        # Root widget - now it's the revealer
        self.root_widget = self.get_widget('editing_operations_revealer')
        
        # Button references
        self.palette.btn_lasso = self.get_widget('btn_lasso')
        self.palette.btn_undo = self.get_widget('btn_undo')
        self.palette.btn_redo = self.get_widget('btn_redo')
        self.palette.btn_duplicate = self.get_widget('btn_duplicate')
        self.palette.btn_align = self.get_widget('btn_align')
        self.palette.btn_cut = self.get_widget('btn_cut')
        self.palette.btn_copy = self.get_widget('btn_copy')
        self.palette.btn_paste = self.get_widget('btn_paste')
    
    def connect_signals(self):
        """Connect UI signals to palette handlers."""
        # Lasso selection
        if self.palette.btn_lasso:
            self.palette.btn_lasso.connect(
                'clicked',
                lambda btn: self.palette.on_lasso_clicked()
            )
        
        # History
        if self.palette.btn_undo:
            self.palette.btn_undo.connect(
                'clicked',
                lambda btn: self.palette.on_undo_clicked()
            )
        
        if self.palette.btn_redo:
            self.palette.btn_redo.connect(
                'clicked',
                lambda btn: self.palette.on_redo_clicked()
            )
        
        # Object operations
        if self.palette.btn_duplicate:
            self.palette.btn_duplicate.connect(
                'clicked',
                lambda btn: self.palette.on_duplicate_clicked()
            )
        
        if self.palette.btn_align:
            self.palette.btn_align.connect(
                'clicked',
                lambda btn: self.palette.on_align_clicked()
            )
        
        # Clipboard
        if self.palette.btn_cut:
            self.palette.btn_cut.connect(
                'clicked',
                lambda btn: self.palette.on_cut_clicked()
            )
        
        if self.palette.btn_copy:
            self.palette.btn_copy.connect(
                'clicked',
                lambda btn: self.palette.on_copy_clicked()
            )
        
        if self.palette.btn_paste:
            self.palette.btn_paste.connect(
                'clicked',
                lambda btn: self.palette.on_paste_clicked()
            )
    
    def get_palette(self):
        """Get the palette instance.
        
        Returns:
            EditingOperationsPalette: Palette instance
        """
        return self.palette
    
    def show(self):
        """Show the editing operations palette by revealing it."""
        if self.root_widget:
            self.root_widget.set_reveal_child(True)
    
    def hide(self):
        """Hide the editing operations palette by unrevealing it."""
        if self.root_widget:
            self.root_widget.set_reveal_child(False)
    
    def is_visible(self):
        """Check if the palette is currently visible.
        
        Returns:
            bool: True if palette is revealed, False otherwise.
        """
        if self.root_widget:
            return self.root_widget.get_reveal_child()
        return False
