#!/usr/bin/env python3
"""File Panel V2 - Refactored file panel with category-based layout.

Simplified architecture:
- Category-based layout (like Topology Panel)
- TreeView with context menu (critical feature)
- No complex toolbar - operations via context menu and inline buttons
- Placeholder categories for future project metadata
- Wayland-safe implementation

Author: Simão Eugénio
Date: 2025-10-22
"""

import os
import sys
from typing import Optional, Callable
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib, Gdk
except Exception as e:
    print(f'ERROR: GTK3 not available in file_panel_v2: {e}', file=sys.stderr)
    sys.exit(1)

from shypn.ui.category_frame import CategoryFrame


class FilePanelV2:
    """Refactored file panel with category-based layout.
    
    Features:
    - EXPLORER section with collapsible categories
    - Files category with TreeView (CRITICAL)
    - Context menu for file operations (CRITICAL)
    - Inline buttons: New File, New Folder, Refresh, Collapse All
    - Double-click to open files
    - Placeholder categories for future metadata
    
    Architecture:
    - Simple OOP design
    - Minimal signal handling
    - Direct GTK widgets (no heavy abstractions)
    - Wayland-safe patterns
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize file panel.
        
        Args:
            base_path: Base directory path for file browser
        """
        # Determine base path - default to workspace/projects
        if base_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            base_path = os.path.join(repo_root, 'workspace', 'projects')
            
            # Ensure projects directory exists
            if not os.path.exists(base_path):
                try:
                    os.makedirs(base_path, exist_ok=True)
                except Exception:
                    # Fallback to workspace if projects can't be created
                    base_path = os.path.join(repo_root, 'workspace')
        
        # State
        self.base_path = base_path
        self.current_path = self.base_path
        self.parent_window = None
        self.current_file = None  # Track selected file for display
        
        # Main container
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build panel UI structure."""
        # Section header: EXPLORER (generous 48px height)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        header_label = Gtk.Label()
        header_label.set_markup("<b>EXPLORER</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)
        
        self.container.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.container.pack_start(separator, False, False, 0)
        
        # Category 1: Files (CRITICAL - expanded by default)
        # Title will show current file path dynamically
        self.files_category = CategoryFrame(
            title="Files",
            buttons=[
                ("＋", self._on_new_file),
                ("📁", self._on_new_folder),
                ("↻", self._on_refresh),
                ("─", self._on_collapse_all)
            ],
            expanded=True
        )
        
        # Connect category expand to ensure only one is open at a time
        self.files_category._title_event_box.connect('button-press-event', 
            lambda w, e: self._on_category_clicked(self.files_category))
        
        # Create content box with path label FIRST (before building tree)
        files_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Current path entry (editable/selectable with more height)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_has_frame(True)
        self.path_entry.set_margin_start(5)
        self.path_entry.set_margin_end(5)
        self.path_entry.set_margin_top(5)
        self.path_entry.set_margin_bottom(5)
        self.path_entry.set_size_request(-1, 32)  # More height (32px)
        self.path_entry.set_placeholder_text("Path/filename")
        self.path_entry.connect('activate', self._on_path_entry_activate)
        files_content.pack_start(self.path_entry, False, False, 0)
        
        # Build TreeView (CRITICAL)
        self._build_tree_view()
        
        # Update path label after tree is built
        self._update_path_label()
        
        # Add tree view to content
        files_content.pack_start(self.tree_scroll, True, True, 0)
        
        self.files_category.set_content(files_content)
        
        # Pack Files category (initially expanded, so expand=True)
        self.container.pack_start(self.files_category, True, True, 0)
        
        # Category 2: Project Information (PLACEHOLDER)
        self.project_info_category = CategoryFrame(
            title="Project Information",
            expanded=False,
            placeholder=True
        )
        self.project_info_category._title_event_box.connect('button-press-event',
            lambda w, e: self._on_category_clicked(self.project_info_category))
        # Pack collapsed categories with expand=False
        self.container.pack_start(self.project_info_category, False, False, 0)
        
        # Category 3: Project Settings (PLACEHOLDER)
        self.project_settings_category = CategoryFrame(
            title="Project Settings",
            expanded=False,
            placeholder=True
        )
        self.project_settings_category._title_event_box.connect('button-press-event',
            lambda w, e: self._on_category_clicked(self.project_settings_category))
        # Pack collapsed categories with expand=False
        self.container.pack_start(self.project_settings_category, False, False, 0)
        
        # Keep track of all categories for exclusive expansion
        self.categories = [
            self.files_category,
            self.project_info_category,
            self.project_settings_category
        ]
    
    def _build_tree_view(self):
        """Build file browser TreeView (CRITICAL COMPONENT)."""
        # ScrolledWindow for TreeView with minimum height
        self.tree_scroll = Gtk.ScrolledWindow()
        self.tree_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # Set minimum height but allow vertical expansion
        self.tree_scroll.set_size_request(-1, 200)  # Minimum 200px height
        self.tree_scroll.set_vexpand(True)  # Allow vertical expansion
        self.tree_scroll.set_hexpand(True)  # Allow horizontal expansion
        
        # TreeStore: name, path, is_dir, weight (for bold folders)
        self.tree_store = Gtk.TreeStore(str, str, bool, int)
        
        # TreeView with indentation enabled
        self.tree_view = Gtk.TreeView(model=self.tree_store)
        self.tree_view.set_headers_visible(False)  # Hide headers for cleaner look
        self.tree_view.set_enable_tree_lines(True)  # Show tree lines
        self.tree_view.set_show_expanders(True)     # Show expanders
        
        # Column: Name only (no icon)
        name_column = Gtk.TreeViewColumn("Name")
        name_column.set_expand(True)
        
        # Name renderer (editable only when explicitly triggered, with weight for bold folders)
        self.name_renderer = Gtk.CellRendererText()
        self.name_renderer.set_property('editable', False)  # Disable auto-edit on click
        self.name_renderer.connect('edited', self._on_cell_edited)
        name_column.pack_start(self.name_renderer, True)
        name_column.add_attribute(self.name_renderer, 'text', 0)
        name_column.add_attribute(self.name_renderer, 'weight', 3)  # Bold for folders
        
        self.tree_view.append_column(name_column)
        
        # Signals
        self.tree_view.connect('row-activated', self._on_row_activated)  # Double-click
        self.tree_view.connect('button-press-event', self._on_tree_button_press)  # Context menu
        
        # Selection tracking to update path label
        selection = self.tree_view.get_selection()
        selection.connect('changed', self._on_selection_changed)
        
        self.tree_scroll.add(self.tree_view)
        
        # Build context menu (CRITICAL)
        self._build_context_menu()
        
        # Load initial content
        self._refresh_tree()
    
    def _build_context_menu(self):
        """Build context menu for file operations (CRITICAL COMPONENT)."""
        self.context_menu = Gtk.Menu()
        
        # Menu items
        menu_items = [
            ("New File", self._on_context_new_file),
            ("New Folder", self._on_context_new_folder),
            ("---", None),
            ("Open", self._on_context_open),
            ("Rename", self._on_context_rename),
            ("Delete", self._on_context_delete),
            ("---", None),
            ("Properties", self._on_context_properties),
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
    
    def _update_path_label(self, selected_file: Optional[str] = None):
        """Update path entry with current directory or selected file.
        
        Args:
            selected_file: Full path to selected file, or None for directory only
        """
        if selected_file and os.path.isfile(selected_file):
            # Show relative path from base
            try:
                rel_path = os.path.relpath(selected_file, self.base_path)
                self.path_entry.set_text(rel_path)
            except ValueError:
                # Path is outside base, show filename only
                self.path_entry.set_text(os.path.basename(selected_file))
        else:
            # Show current directory
            try:
                rel_path = os.path.relpath(self.current_path, self.base_path)
                if rel_path == '.':
                    self.path_entry.set_text("projects/")
                else:
                    self.path_entry.set_text(f"{rel_path}/")
            except ValueError:
                self.path_entry.set_text(f"{os.path.basename(self.current_path)}/")
    
    def _on_category_clicked(self, clicked_category):
        """Handle category title click - ensure only one expanded at a time.
        
        Like Topology Panel: only one category fills the space at a time.
        
        Args:
            clicked_category: The category that was clicked
        """
        # Toggle the clicked category
        new_state = not clicked_category.expanded
        
        # Update all categories: collapse others, expand clicked
        for category in self.categories:
            if category == clicked_category:
                category.set_expanded(new_state)
            else:
                category.set_expanded(False)
            
            # CRITICAL: Adjust packing so only expanded category fills space
            # Expanded category gets expand=True, collapsed get expand=False
            is_expanded = (category == clicked_category and new_state)
            self.container.child_set_property(category, 'expand', is_expanded)
            self.container.child_set_property(category, 'fill', is_expanded)
        
        return True  # Stop propagation
    
    def _refresh_tree(self):
        """Refresh TreeView with current directory contents."""
        self.tree_store.clear()
        
        # Update path entry
        self._update_path_label(self.current_file)
        
        try:
            # Add parent directory if not at base
            if self.current_path != self.base_path:
                parent_path = os.path.dirname(self.current_path)
                # Parent dir: "..", path, is_dir=True, weight=bold
                self.tree_store.append(None, ["..", parent_path, True, 700])
            
            # List directory contents
            if os.path.exists(self.current_path) and os.path.isdir(self.current_path):
                items = []
                for item in os.listdir(self.current_path):
                    # Skip hidden files (starting with .)
                    if item.startswith('.'):
                        continue
                    
                    full_path = os.path.join(self.current_path, item)
                    is_dir = os.path.isdir(full_path)
                    items.append((is_dir, item, full_path))
                
                # Sort: directories first, then files
                items.sort(key=lambda x: (not x[0], x[1].lower()))
                
                for is_dir, name, path in items:
                    # Add folder indicator and bold weight for directories
                    display_name = f"📁 {name}" if is_dir else name
                    weight = 700 if is_dir else 400  # Bold for folders, normal for files
                    self.tree_store.append(None, [display_name, path, is_dir, weight])
        
        except Exception as e:
            print(f"[FILE_PANEL_V2] Error refreshing tree: {e}", file=sys.stderr)
    
    def _get_selected_path(self) -> Optional[str]:
        """Get currently selected file path.
        
        Returns:
            Selected file path or None
        """
        selection = self.tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            return model.get_value(tree_iter, 1)  # path column (was 2, now 1 without icon)
        return None
    
    def _get_selected_is_dir(self) -> bool:
        """Check if selected item is a directory.
        
        Returns:
            True if directory, False otherwise
        """
        selection = self.tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            return model.get_value(tree_iter, 2)  # is_dir column (was 3, now 2 without icon)
        return False
    
    # =========================================================================
    # Event Handlers - TreeView
    # =========================================================================
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click on tree row (open file/folder)."""
        selected_path = self._get_selected_path()
        if not selected_path:
            return
        
        if self._get_selected_is_dir():
            # Navigate to directory
            self.current_path = selected_path
            self._refresh_tree()
        else:
            # Open file (delegate to callback if set)
            print(f"[FILE_PANEL_V2] Open file: {selected_path}")
            if hasattr(self, 'on_file_open') and self.on_file_open:
                self.on_file_open(selected_path)
    
    def _on_tree_button_press(self, widget, event):
        """Handle mouse button press on tree view.
        
        - Left click: Open folder or select file
        - Right click: Show context menu
        """
        if event.button == 1:  # Left-click
            # Get item under cursor
            path_info = self.tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path = path_info[0]
                self.tree_view.set_cursor(path)
                
                # If it's a folder, navigate into it
                selected_path = self._get_selected_path()
                if selected_path and self._get_selected_is_dir():
                    self.current_path = selected_path
                    self._refresh_tree()
                    return True
            return False
            
        elif event.button == 3:  # Right-click
            # Select item under cursor
            path_info = self.tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path = path_info[0]
                self.tree_view.set_cursor(path)
            
            # Show context menu
            self.context_menu.popup_at_pointer(event)
            return True
        return False
    
    def _on_selection_changed(self, selection):
        """Handle tree selection changes to update path entry."""
        model, tree_iter = selection.get_selected()
        if tree_iter:
            file_path = model.get_value(tree_iter, 1)  # Column 1 is path (was 2)
            is_dir = model.get_value(tree_iter, 2)     # Column 2 is is_dir (was 3)
            
            if is_dir:
                self.current_path = file_path
                self._update_path_label()
            else:
                self._update_path_label(selected_file=file_path)
    
    # =========================================================================
    # Inline Editing Handlers
    # =========================================================================
    
    def _on_cell_edited(self, renderer, path, new_text):
        """Handle inline cell editing (rename or create operation).
        
        Args:
            renderer: Cell renderer
            path: Tree path of edited cell
            new_text: New text entered
        """
        print(f"[FILE_PANEL_V2] Cell edited: {path} -> {new_text}", file=sys.stderr)
        
        if not new_text or new_text.strip() == "":
            # Empty name - remove the temporary item
            tree_iter = self.tree_store.get_iter(path)
            self.tree_store.remove(tree_iter)
            # Disable editing
            self.name_renderer.set_property('editable', False)
            return
        
        # Get item info
        tree_iter = self.tree_store.get_iter(path)
        old_path = self.tree_store.get_value(tree_iter, 1)  # path column
        old_display_name = self.tree_store.get_value(tree_iter, 0)  # display name column
        is_dir = self.tree_store.get_value(tree_iter, 2)    # is_dir column
        
        # Extract actual name (remove folder icon if present)
        old_name = old_display_name.replace("📁 ", "") if old_display_name.startswith("📁 ") else old_display_name
        
        # Clean the new text (user might include icon accidentally)
        new_text_clean = new_text.replace("📁 ", "").strip()
        
        if new_text_clean == old_name:
            return  # No change
        
        # Build new path
        parent_dir = os.path.dirname(old_path)
        new_path = os.path.join(parent_dir, new_text_clean)
        
        try:
            # Check if this is a new item (doesn't exist yet)
            if not os.path.exists(old_path):
                # Create new file or folder
                if is_dir:
                    os.makedirs(new_path, exist_ok=True)
                    print(f"[FILE_PANEL_V2] Created folder: {new_path}", file=sys.stderr)
                else:
                    # Create empty file
                    with open(new_path, 'w') as f:
                        pass
                    print(f"[FILE_PANEL_V2] Created file: {new_path}", file=sys.stderr)
            else:
                # Rename existing item
                os.rename(old_path, new_path)
                print(f"[FILE_PANEL_V2] Renamed: {old_path} -> {new_path}", file=sys.stderr)
            
            # Update tree store with proper display name and weight
            new_display_name = f"📁 {new_text_clean}" if is_dir else new_text_clean
            weight = 700 if is_dir else 400
            self.tree_store.set(tree_iter, 0, new_display_name, 1, new_path, 3, weight)
            
            # Update path entry if this was the selected file
            if hasattr(self, 'current_file') and self.current_file == old_path:
                self.current_file = new_path
                self._update_path_label(selected_file=new_path)
                
        except Exception as e:
            print(f"[FILE_PANEL_V2] Operation failed: {e}", file=sys.stderr)
            self._show_error("Error", f"Failed to create/rename: {e}")
            # Remove the temporary item on error
            self.tree_store.remove(tree_iter)
        finally:
            # Disable editing after operation completes
            self.name_renderer.set_property('editable', False)
    
    def _on_path_entry_activate(self, entry):
        """Handle path entry activation (Enter key).
        
        Navigate to entered path or open file.
        """
        path_text = entry.get_text().strip()
        if not path_text:
            return
        
        # Build full path
        if path_text.startswith('/'):
            full_path = path_text
        else:
            full_path = os.path.join(self.base_path, path_text)
        
        # Navigate or open
        if os.path.isdir(full_path):
            self.current_path = full_path
            self._refresh_tree()
        elif os.path.isfile(full_path):
            self._open_file_from_path(full_path)
        else:
            self._show_error("Path Error", f"Path not found: {path_text}")
    
    def _start_inline_edit(self, tree_path=None):
        """Start inline editing for a tree item.
        
        Args:
            tree_path: Tree path to edit, or None for selected item
        """
        if tree_path is None:
            # Get selected path
            selection = self.tree_view.get_selection()
            model, tree_iter = selection.get_selected()
            if not tree_iter:
                return
            tree_path = model.get_path(tree_iter)
        
        # Temporarily enable editing
        self.name_renderer.set_property('editable', True)
        
        # Set cursor and start editing
        self.tree_view.set_cursor(tree_path, self.tree_view.get_column(0), True)
    
    # =========================================================================
    # Event Handlers - Inline Buttons
    # =========================================================================
    
    def _on_new_file(self):
        """Handle New File button - create new file with inline editing."""
        print("[FILE_PANEL_V2] New File clicked", file=sys.stderr)
        
        # Add temporary item to tree (no icon for files, normal weight)
        new_name = "new_file.shy"
        new_path = os.path.join(self.current_path, new_name)
        tree_iter = self.tree_store.append(None, [new_name, new_path, False, 400])
        
        # Start inline editing
        tree_path = self.tree_store.get_path(tree_iter)
        self.tree_view.set_cursor(tree_path, self.tree_view.get_column(0), True)
        
        # Create empty file when editing completes
        # (Will be handled by _on_cell_edited)
    
    def _on_new_folder(self):
        """Handle New Folder button - create new folder with inline editing."""
        print("[FILE_PANEL_V2] New Folder clicked", file=sys.stderr)
        
        # Add temporary item to tree with folder icon and bold weight
        new_name = "📁 New Folder"
        new_path = os.path.join(self.current_path, "New Folder")
        tree_iter = self.tree_store.append(None, [new_name, new_path, True, 700])
        
        # Start inline editing
        tree_path = self.tree_store.get_path(tree_iter)
        self.tree_view.set_cursor(tree_path, self.tree_view.get_column(0), True)
    
    def _on_refresh(self):
        """Handle Refresh button."""
        print("[FILE_PANEL_V2] Refresh clicked")
        self._refresh_tree()
    
    def _on_collapse_all(self):
        """Handle Collapse All button - collapse tree and navigate to root."""
        print("[FILE_PANEL_V2] Collapse All clicked", file=sys.stderr)
        
        # Navigate to base path (root)
        self.current_path = self.base_path
        self.current_file = None
        
        # Refresh tree from root
        self._refresh_tree()
        
        # Collapse all tree nodes
        self.tree_view.collapse_all()
    
    # =========================================================================
    # Event Handlers - Context Menu
    # =========================================================================
    
    def _on_context_new_file(self, menu_item):
        """Handle context menu: New File."""
        self._on_new_file()
    
    def _on_context_new_folder(self, menu_item):
        """Handle context menu: New Folder."""
        self._on_new_folder()
    
    def _on_context_open(self, menu_item):
        """Handle context menu: Open."""
        selected_path = self._get_selected_path()
        if selected_path:
            if self._get_selected_is_dir():
                self.current_path = selected_path
                self._refresh_tree()
            else:
                print(f"[FILE_PANEL_V2] Open file: {selected_path}")
                if hasattr(self, 'on_file_open') and self.on_file_open:
                    self.on_file_open(selected_path)
    
    def _on_context_rename(self, menu_item):
        """Handle context menu: Rename - start inline editing."""
        print("[FILE_PANEL_V2] Context menu: Rename", file=sys.stderr)
        self._start_inline_edit()
    
    def _on_context_delete(self, menu_item):
        """Handle context menu: Delete."""
        selected_path = self._get_selected_path()
        if not selected_path:
            return
        
        file_name = os.path.basename(selected_path)
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete '{file_name}'?"
        )
        dialog.format_secondary_text("This action cannot be undone.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                import shutil
                if os.path.isdir(selected_path):
                    shutil.rmtree(selected_path)
                else:
                    os.remove(selected_path)
                
                self._refresh_tree()
                print(f"[FILE_PANEL_V2] Deleted: {selected_path}")
            except Exception as e:
                self._show_error("Error", f"Failed to delete: {e}")
    
    def _on_context_properties(self, menu_item):
        """Handle context menu: Properties."""
        selected_path = self._get_selected_path()
        if not selected_path:
            return
        
        try:
            stat_info = os.stat(selected_path)
            is_dir = os.path.isdir(selected_path)
            
            info_text = f"Path: {selected_path}\n"
            info_text += f"Type: {'Directory' if is_dir else 'File'}\n"
            info_text += f"Size: {stat_info.st_size} bytes\n"
            info_text += f"Modified: {stat_info.st_mtime}\n"
            
            self._show_info("Properties", info_text)
        except Exception as e:
            self._show_error("Error", f"Failed to get properties: {e}")
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def _show_info(self, title: str, message: str):
        """Show info dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_error(self, title: str, message: str):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def set_parent_window(self, parent: Gtk.Window):
        """Set parent window for dialogs (Wayland safety).
        
        Args:
            parent: Parent window
        """
        self.parent_window = parent
    
    def set_canvas_loader(self, canvas_loader):
        """Set canvas loader for document operations.
        
        Args:
            canvas_loader: ModelCanvasLoader instance
        """
        self.canvas_loader = canvas_loader
        print(f"[FILE_PANEL_V2] Canvas loader connected", file=sys.stderr)
        
        # Wire file open callback to load files into canvas
        self.on_file_open = self._open_file_from_path
    
    def _open_file_from_path(self, filepath: str):
        """Open a specific file from path into canvas.
        
        Used by double-click and context menu Open operations.
        Implements the same pattern as FileExplorerPanel.
        
        Args:
            filepath: Full path to .shy file to open
        """
        print(f"[FILE_PANEL_V2] _open_file_from_path: {filepath}", file=sys.stderr)
        
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            print("[FILE_PANEL_V2] Canvas loader not available", file=sys.stderr)
            return
        
        if not hasattr(self, 'persistency_manager') or self.persistency_manager is None:
            print("[FILE_PANEL_V2] Persistency manager not available", file=sys.stderr)
            return
        
        try:
            from shypn.data.canvas.document_model import DocumentModel
            print(f"[FILE_PANEL_V2] Loading document from: {filepath}", file=sys.stderr)
            document = DocumentModel.load_from_file(filepath)
            
            if document:
                print(f"[FILE_PANEL_V2] Document loaded, loading into canvas...", file=sys.stderr)
                self._load_document_into_canvas(document, filepath)
            else:
                print(f"[FILE_PANEL_V2] Failed to load document", file=sys.stderr)
                self._show_error("Load Error", f"Failed to load file: {filepath}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error("Load Error", f"Failed to open file: {e}")
    
    def _load_document_into_canvas(self, document, filepath: str):
        """Load a document model into the canvas.
        
        Helper method for loading documents into canvas tabs.
        Implements the same pattern as FileExplorerPanel.
        
        Args:
            document: DocumentModel instance
            filepath: Full path to the file
        """
        if not document or not filepath:
            return
        
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        
        print(f"[FILE_PANEL_V2] Adding document to canvas: {base_name}", file=sys.stderr)
        
        # Add new canvas tab
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        
        if manager:
            print(f"[FILE_PANEL_V2] Loading objects into canvas manager...", file=sys.stderr)
            
            # Use load_objects() for unified initialization
            manager.load_objects(
                places=document.places,
                transitions=document.transitions,
                arcs=document.arcs
            )
            
            # Set change callback for object state management
            manager.document_controller.set_change_callback(manager._on_object_changed)
            
            # Restore view state if available
            if hasattr(document, 'view_state') and document.view_state:
                manager.zoom = document.view_state.get('zoom', 1.0)
                manager.pan_x = document.view_state.get('pan_x', 0.0)
                manager.pan_y = document.view_state.get('pan_y', 0.0)
                manager.rotation = document.view_state.get('rotation', 0.0)
            
            # Fit to page to ensure objects are visible
            manager.fit_to_page()
            
            # Mark document as saved (not dirty)
            manager.document_controller.mark_saved(filepath)
            
            print(f"[FILE_PANEL_V2] Document loaded successfully", file=sys.stderr)
    
    def get_widget(self) -> Gtk.Widget:
        """Get main container widget.
        
        Returns:
            Main container widget
        """
        return self.container
