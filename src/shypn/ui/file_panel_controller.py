#!/usr/bin/env python3
"""File Panel Controller - Business logic for file operations.

Handles:
- File tree population and refresh
- File/folder operations (create, rename, delete)
- Context menu
- File opening/navigation
- Integration with canvas loader

Author: Simão Eugénio
Date: 2025-10-22
"""

import os
import sys
from pathlib import Path
from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango


class FilePanelController:
    """Controller for File Panel business logic.
    
    Separates UI management (loader) from business logic (controller).
    Follows MVC pattern for clean architecture.
    """
    
    def __init__(self, base_path, tree_view, tree_store, path_entry, name_renderer):
        """Initialize controller.
        
        Args:
            base_path: Base directory path
            tree_view: GtkTreeView widget
            tree_store: GtkTreeStore model
            path_entry: GtkEntry for path display
            name_renderer: GtkCellRendererText for file names
        """
        self.base_path = Path(base_path)
        self.current_path = self.base_path
        
        # Widgets
        self.tree_view = tree_view
        self.tree_store = tree_store
        self.path_entry = path_entry
        self.name_renderer = name_renderer
        
        # State
        self.current_file = None
        self.parent_window = None
        self.canvas_loader = None
        self.persistency = None
        
        # Build context menu
        self._build_context_menu()
        
    
    # ===============================
    # Public API
    # ===============================
    
    def set_parent_window(self, parent_window):
        """Set parent window for dialogs."""
        self.parent_window = parent_window
    
    def set_canvas_loader(self, canvas_loader):
        """Set canvas loader for file operations."""
        self.canvas_loader = canvas_loader
    
    def set_persistency_manager(self, persistency):
        """Set persistency manager."""
        self.persistency = persistency
    
    def refresh_tree(self):
        """Refresh the file tree."""
        self._populate_tree()
        self._update_path_entry()
    
    def navigate_to(self, path):
        """Navigate to a specific directory.
        
        Args:
            path: Path to navigate to
        """
        path = Path(path)
        if path.exists() and path.is_dir():
            self.current_path = path
            self.refresh_tree()
    
    # ===============================
    # Tree Population
    # ===============================
    
    def _populate_tree(self):
        """Populate tree with files from current directory."""
        self.tree_store.clear()
        
        if not self.current_path.exists():
            print(f"⚠ Path does not exist: {self.current_path}", file=sys.stderr)
            return
        
        try:
            # Add parent directory entry if not at base
            if self.current_path != self.base_path and self.current_path.parent:
                parent_iter = self.tree_store.append(None, [
                    "..",
                    str(self.current_path.parent),
                    True,
                    Pango.Weight.BOLD
                ])
            
            # List directory contents
            items = []
            try:
                items = list(self.current_path.iterdir())
            except PermissionError:
                print(f"⚠ Permission denied: {self.current_path}", file=sys.stderr)
                return
            
            # Sort: directories first, then files (alphabetically)
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            # Add items to tree
            for item in items:
                is_dir = item.is_dir()
                weight = Pango.Weight.BOLD if is_dir else Pango.Weight.NORMAL
                
                self.tree_store.append(None, [
                    item.name,
                    str(item),
                    is_dir,
                    weight
                ])
        
        except Exception as e:
            print(f"Error populating tree: {e}", file=sys.stderr)
    
    def _update_path_entry(self, selected_file: Optional[str] = None):
        """Update path entry with current directory or selected file."""
        if selected_file:
            self.path_entry.set_text(selected_file)
        else:
            self.path_entry.set_text(str(self.current_path))
    
    # ===============================
    # Signal Handlers
    # ===============================
    
    def on_row_activated(self, tree_view, path, column):
        """Handle double-click on tree row."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        
        name = model.get_value(iter, 0)
        full_path = model.get_value(iter, 1)
        is_dir = model.get_value(iter, 2)
        
        if is_dir:
            # Navigate to directory
            self.current_path = Path(full_path)
            self.refresh_tree()
        else:
            # Open file
            self._open_file(full_path)
    
    def on_selection_changed(self, selection):
        """Handle selection change in tree."""
        model, iter = selection.get_selected()
        if iter:
            name = model.get_value(iter, 0)
            full_path = model.get_value(iter, 1)
            is_dir = model.get_value(iter, 2)
            
            self.current_file = full_path if not is_dir else None
            self._update_path_entry(full_path)
    
    def on_tree_button_press(self, tree_view, event):
        """Handle button press on tree (for context menu)."""
        if event.button == 3:  # Right click
            # Get selection
            path_info = tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, column, cell_x, cell_y = path_info
                tree_view.set_cursor(path, column, False)
            
            # Show context menu
            self.context_menu.popup(None, None, None, None, event.button, event.time)
            return True
        return False
    
    def on_path_entry_activate(self, entry):
        """Handle Enter key in path entry."""
        path_text = entry.get_text()
        path = Path(path_text)
        
        if path.exists():
            if path.is_dir():
                self.navigate_to(path)
            elif path.is_file():
                self._open_file(str(path))
        else:
            print(f"⚠ Path does not exist: {path}", file=sys.stderr)
    
    # ===============================
    # Context Menu
    # ===============================
    
    def _build_context_menu(self):
        """Build context menu for file operations."""
        self.context_menu = Gtk.Menu()
        
        menu_items = [
            ("New File", self._on_context_new_file),
            ("New Folder", self._on_context_new_folder),
            ("---", None),
            ("Open", self._on_context_open),
            ("Rename", self._on_context_rename),
            ("Delete", self._on_context_delete),
            ("---", None),
            ("Refresh", self._on_context_refresh),
        ]
        
        for label, callback in menu_items:
            if label == "---":
                item = Gtk.SeparatorMenuItem()
            else:
                item = Gtk.MenuItem(label=label)
                if callback:
                    item.connect('activate', callback)
            
            self.context_menu.append(item)
        
        self.context_menu.show_all()
    
    def _on_context_new_file(self, menu_item):
        """Create new file."""
        dialog = Gtk.Dialog(
            title="New File",
            parent=self.parent_window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        
        content = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("File name")
        content.pack_start(entry, True, True, 10)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = entry.get_text()
            if filename:
                filepath = self.current_path / filename
                try:
                    filepath.touch()
                    self.refresh_tree()
                except Exception as e:
                    print(f"Error creating file: {e}", file=sys.stderr)
        
        dialog.destroy()
    
    def _on_context_new_folder(self, menu_item):
        """Create new folder."""
        dialog = Gtk.Dialog(
            title="New Folder",
            parent=self.parent_window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        
        content = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("Folder name")
        content.pack_start(entry, True, True, 10)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            foldername = entry.get_text()
            if foldername:
                folderpath = self.current_path / foldername
                try:
                    folderpath.mkdir(parents=True, exist_ok=True)
                    self.refresh_tree()
                except Exception as e:
                    print(f"Error creating folder: {e}", file=sys.stderr)
        
        dialog.destroy()
    
    def _on_context_open(self, menu_item):
        """Open selected file."""
        selection = self.tree_view.get_selection()
        model, iter = selection.get_selected()
        
        if iter:
            full_path = model.get_value(iter, 1)
            is_dir = model.get_value(iter, 2)
            
            if not is_dir:
                self._open_file(full_path)
    
    def _on_context_rename(self, menu_item):
        """Rename selected file/folder."""
        selection = self.tree_view.get_selection()
        model, iter = selection.get_selected()
        
        if iter:
            path = selection.get_selected_rows()[1][0]
            self.name_renderer.set_property('editable', True)
            self.tree_view.set_cursor(path, self.tree_view.get_column(0), True)
    
    def _on_context_delete(self, menu_item):
        """Delete selected file/folder."""
        selection = self.tree_view.get_selection()
        model, iter = selection.get_selected()
        
        if iter:
            name = model.get_value(iter, 0)
            full_path = model.get_value(iter, 1)
            
            # Confirmation dialog
            dialog = Gtk.MessageDialog(
                parent=self.parent_window,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                message_format=f"Delete '{name}'?"
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                try:
                    path = Path(full_path)
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    self.refresh_tree()
                except Exception as e:
                    print(f"Error deleting: {e}", file=sys.stderr)
    
    def _on_context_refresh(self, menu_item):
        """Refresh file tree."""
        self.refresh_tree()
    
    # ===============================
    # Inline Button Handlers (CategoryFrame buttons)
    # ===============================
    
    def on_new_file(self, button=None):
        """Handle New File button (inline button in Files category)."""
        self._on_context_new_file(None)
    
    def on_new_folder(self, button=None):
        """Handle New Folder button (inline button in Files category)."""
        self._on_context_new_folder(None)
    
    def on_refresh(self, button=None):
        """Handle Refresh button (inline button in Files category)."""
        self.refresh_tree()
    
    def on_collapse_all(self, button=None):
        """Handle Collapse All button (inline button in Files category)."""
        if self.tree_view:
            self.tree_view.collapse_all()
    
    # ===============================
    # File Operations
    # ===============================
    
    def _open_file(self, filepath):
        """Open file with canvas loader.
        
        Args:
            filepath: Path to file to open
        """
        
        if self.canvas_loader:
            try:
                self.canvas_loader.load_file(filepath)
            except Exception as e:
                print(f"Error opening file: {e}", file=sys.stderr)
        else:
            print(f"⚠ No canvas loader available to open file", file=sys.stderr)


__all__ = ['FilePanelController']
