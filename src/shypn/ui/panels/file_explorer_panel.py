#!/usr/bin/env python3
"""File Explorer Panel Controller for SHYpn.

This module provides the controller layer for the file explorer functionality.
It connects the FileExplorer API (business logic) to the GTK UI defined in
left_panel.ui (view).

This follows the MVC pattern:
- Model: FileExplorer API (shypn.api.file.explorer)
- View: left_panel.ui (GTK XML)
- Controller: FileExplorerPanel (this file)

The controller:
1. Gets widget references from Builder (doesn't create widgets)
2. Configures TreeView model and columns (display logic)
3. Connects signals between widgets and API
4. Updates UI when API state changes

Example:
    # After loading UI with builder
    builder = Gtk.Builder.new_from_file('left_panel.ui')
    explorer_panel = FileExplorerPanel(builder, base_path="/home/user/projects")
    
    # The controller connects everything automatically
"""

import os
import sys
from typing import Optional

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, GLib, Pango, Gio, Gdk
except Exception as e:
    print(f'ERROR: GTK3 not available in file_explorer_panel: {e}', file=sys.stderr)
    sys.exit(1)

# Import the FileExplorer API
from shypn.api.file import FileExplorer


class FileExplorerPanel:
    """Controller for file explorer functionality.
    
    Connects FileExplorer API (model) to GTK UI (view).
    Does NOT create widgets - only gets references and connects signals.
    
    Attributes:
        explorer: FileExplorer API instance (business logic)
        builder: GTK Builder instance (UI references)
        tree_view: GTK TreeView widget (from builder)
        store: GTK ListStore for tree data (created by controller)
        status_label: GTK Label for status messages (from builder)
        Navigation buttons: All from builder
    """
    
    def __init__(self, builder: Gtk.Builder, base_path: Optional[str] = None):
        """Initialize the file explorer controller.
        
        Args:
            builder: GTK Builder instance with left_panel.ui loaded
            base_path: Starting directory (default: project root or home)
        """
        self.builder = builder
        
        # Create the FileExplorer API instance (Model)
        self.explorer = FileExplorer(base_path=base_path)
        
        # Connect API callbacks
        self.explorer.on_path_changed = self._on_path_changed
        self.explorer.on_error = self._on_error
        
        # Track current opened file (for display in toolbar)
        # Set default filename with relative path from models directory
        self.current_opened_file: Optional[str] = "models/default.shy"
        
        # Track view mode: hierarchical (True) or flat (False)
        self.hierarchical_view = True
        
        # Track selected item for context menu operations
        self.selected_item_path: Optional[str] = None
        self.selected_item_name: Optional[str] = None
        self.selected_item_is_dir: bool = False
        
        # Clipboard for cut/copy operations
        self.clipboard_path: Optional[str] = None
        self.clipboard_operation: Optional[str] = None  # 'cut' or 'copy'
        
        # Get UI widgets from builder (View)
        self._get_widgets()
        
        # Configure TreeView (display logic)
        self._configure_tree_view()
        
        # Setup context menu
        self._setup_context_menu()
        
        # Connect signals (Controller)
        self._connect_signals()
        
        # Load initial directory
        self._load_current_directory()
    
    def _get_widgets(self):
        """Get widget references from builder.
        
        All widgets are defined in left_panel.ui XML file.
        This method just gets references to connect logic.
        Most widgets are optional except for the tree_view.
        """
        # Tree view and scrolled window (required)
        self.tree_view = self.builder.get_object('file_browser_tree')
        self.scrolled_window = self.builder.get_object('file_browser_scroll')
        
        # File operations toolbar buttons (optional)
        self.new_button = self.builder.get_object('file_new_button')
        
        self.open_button = self.builder.get_object('file_open_button')
        self.save_button = self.builder.get_object('file_save_button')
        self.save_as_button = self.builder.get_object('file_save_as_button')
        self.new_folder_button = self.builder.get_object('file_new_folder_button')
        
        # Navigation buttons (optional)
        self.back_button = self.builder.get_object('nav_back_button')
        self.forward_button = self.builder.get_object('nav_forward_button')
        self.up_button = self.builder.get_object('nav_up_button')
        self.home_button = self.builder.get_object('nav_home_button')
        self.refresh_button = self.builder.get_object('nav_refresh_button')
        
        # Current file entry (optional - changed from label to entry for lowered relief)
        self.current_file_entry = self.builder.get_object('current_file_entry')
        # Keep reference as current_file_label for compatibility
        self.current_file_label = self.current_file_entry
        
        # Status label (optional)
        self.status_label = self.builder.get_object('file_browser_status')
        
        # Validate critical widgets
        if self.tree_view is None:
            raise ValueError("TreeView 'file_browser_tree' not found in UI file")
        if self.scrolled_window is None:
            raise ValueError("ScrolledWindow 'file_browser_scroll' not found in UI file")
        
    
    def _configure_tree_view(self):
        """Configure TreeView model and columns.
        
        This is display logic - how data is presented.
        The TreeView widget itself is defined in XML.
        """
        # Create tree store for hierarchical view: icon_name(str), name(str), path(str), is_dir(bool)
        self.store = Gtk.TreeStore(str, str, str, bool)
        
        # Set model
        self.tree_view.set_model(self.store)
        
        # Name column (icon + text) - the only column now
        name_column = Gtk.TreeViewColumn()
        name_column.set_title("Name")
        name_column.set_expand(True)
        name_column.set_sort_column_id(1)
        name_column.set_resizable(True)
        
        # Icon renderer
        icon_renderer = Gtk.CellRendererPixbuf()
        name_column.pack_start(icon_renderer, False)
        name_column.add_attribute(icon_renderer, "icon-name", 0)
        
        # Text renderer
        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        name_column.pack_start(text_renderer, True)
        name_column.add_attribute(text_renderer, "text", 1)
        
        self.tree_view.append_column(name_column)
        
    
    def _setup_context_menu(self):
        """Setup context menu as a proper GTK3 Gtk.Menu.
        
        GTK3 menus automatically handle:
        - Dismiss on Escape key
        - Dismiss on click outside
        - Focus management
        
        GTK3 Gtk.Menu handles all dismiss behavior automatically!
        """
        # Create a proper GTK3 Menu
        self.context_menu = Gtk.Menu()
        
        # Add menu items
        menu_items = [
            ("Open", self._on_open_clicked),
            ("New Folder", self._on_new_folder_clicked),
            ("---", None),  # Separator
            ("Cut", self._on_cut_clicked),
            ("Copy", self._on_copy_clicked),
            ("Paste", self._on_paste_clicked),
            ("Duplicate", self._on_duplicate_clicked),
            ("---", None),  # Separator
            ("Rename", self._on_rename_clicked),
            ("Delete", self._on_delete_clicked),
            ("---", None),  # Separator
            ("Refresh", self._on_refresh_clicked),
            ("Properties", self._on_properties_clicked),
        ]
        
        for label, callback in menu_items:
            if label == "---":
                # Add separator
                separator = Gtk.SeparatorMenuItem()
                self.context_menu.append(separator)
            else:
                # Add menu item
                menu_item = Gtk.MenuItem(label=label)
                if callback:
                    menu_item.connect("activate", callback)
                self.context_menu.append(menu_item)
        
        # Show all items (required for GTK3 menus)
        self.context_menu.show_all()
        
    
    def _connect_signals(self):
        """Connect widget signals to controller methods.
        
        This is the Controller's main job - connecting UI events to business logic.
        """
        # File operations toolbar buttons
        if self.new_button:
            self.new_button.connect("clicked", self._on_file_new_clicked)
        if self.open_button:
            self.open_button.connect("clicked", self._on_file_open_clicked)
        if self.save_button:
            self.save_button.connect("clicked", self._on_file_save_clicked)
        if self.save_as_button:
            self.save_as_button.connect("clicked", self._on_file_save_as_clicked)
        if self.new_folder_button:
            self.new_folder_button.connect("clicked", self._on_file_new_folder_clicked)
        
        # Navigation buttons
        if self.back_button:
            self.back_button.connect("clicked", self._on_back_clicked)
        if self.forward_button:
            self.forward_button.connect("clicked", self._on_forward_clicked)
        if self.up_button:
            self.up_button.connect("clicked", self._on_up_clicked)
        if self.home_button:
            self.home_button.connect("clicked", self._on_home_clicked)
        if self.refresh_button:
            self.refresh_button.connect("clicked", self._on_refresh_clicked)
        
        # Tree view
        self.tree_view.connect("row-activated", self._on_row_activated)
        
        # Context menu (right-click) - GTK3 button-press-event
        self.tree_view.connect("button-press-event", self._on_tree_view_button_press)
        
        # Add left-click handler to scrolled window to detect clicks outside menu
        # Note: GTK3 menus handle Escape and outside clicks automatically!
        self.scrolled_window.connect('button-press-event', self._on_scroll_button_press)
        

    
    def _load_current_directory(self):
        """Load current directory contents into tree view (Controller logic)."""
        # Clear existing data
        self.store.clear()
        
        if self.hierarchical_view:
            # Load hierarchical view: show all subdirectories as tree
            self._load_directory_tree(self.explorer.current_path, None)
        else:
            # Load flat view: show only current directory contents
            self._load_directory_flat(self.explorer.current_path)
        
        # Update current file label to show opened file (not directory)
        if self.current_file_label:
            if self.current_opened_file:
                # Show the currently opened file name
                self.current_file_label.set_text(self.current_opened_file)
            else:
                # No file opened yet - show placeholder
                self.current_file_label.set_text("—")
        
        # Update status (View)
        stats = self.explorer.get_stats()
        status_text = f"{stats['directories']} folders, {stats['files']} files"
        if self.status_label:
            self.status_label.set_text(status_text)
        
        # Update button states (View)
        self._update_button_states()
    
    def _load_directory_flat(self, directory: str):
        """Load directory contents in flat mode (current directory only).
        
        Args:
            directory: Directory path to load
        """
        # Get entries from API (Model)
        entries = self.explorer.get_current_entries()
        
        # Populate store (update View) - only icon, name, path, is_dir
        for entry in entries:
            self.store.append(None, [
                entry['icon_name'],
                entry['name'],
                entry['path'],
                entry['is_directory']
            ])
    
    def _load_directory_tree(self, directory: str, parent_iter):
        """Load directory contents recursively in tree mode.
        
        Args:
            directory: Directory path to load
            parent_iter: Parent TreeIter (None for root)
        """
        try:
            items = os.listdir(directory)
            
            # Separate directories and files
            directories = []
            files = []
            
            for item in items:
                # Skip hidden files if not showing them
                if not self.explorer.show_hidden and item.startswith('.'):
                    continue
                
                full_path = os.path.join(directory, item)
                
                try:
                    if os.path.isdir(full_path):
                        directories.append((item, full_path))
                    else:
                        files.append((item, full_path))
                except (PermissionError, OSError):
                    continue
            
            # Sort directories and files
            directories.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())
            
            # Add directories first (with their subdirectories)
            for name, path in directories:
                icon = self.explorer._get_icon_name(name, True)
                dir_iter = self.store.append(parent_iter, [icon, name, path, True])
                # Recursively load subdirectories
                self._load_directory_tree(path, dir_iter)
            
            # Add files
            for name, path in files:
                icon = self.explorer._get_icon_name(name, False)
                self.store.append(parent_iter, [icon, name, path, False])
                
        except PermissionError:
            if self.explorer.on_error:
                self.explorer.on_error(f"Permission denied: {directory}")
        except Exception as e:
            if self.explorer.on_error:
                self.explorer.on_error(f"Error reading directory: {str(e)}")
    
    def _update_button_states(self):
        """Update navigation button sensitivity based on API state (Controller logic)."""
        if self.back_button:
            self.back_button.set_sensitive(self.explorer.can_go_back())
        
        if self.forward_button:
            self.forward_button.set_sensitive(self.explorer.can_go_forward())
        
        if self.up_button:
            self.up_button.set_sensitive(self.explorer.can_go_up())
    
    # ========================================================================
    # API Callbacks (Model → Controller → View)
    # ========================================================================
    
    def _on_path_changed(self, new_path: str):
        """Callback when path changes in API (Model).
        
        Args:
            new_path: New current path
        """
        
        # Reload directory on main thread (update View)
        GLib.idle_add(self._load_current_directory)
    
    def _on_error(self, error_message: str):
        """Callback when error occurs in API (Model).
        
        Args:
            error_message: Error description
        """
        
        # Update status label (View)
        if self.status_label:
            GLib.idle_add(self.status_label.set_text, f"Error: {error_message}")
    
    # ========================================================================
    # Signal Handlers (View → Controller → Model)
    # ========================================================================
    
    def _on_back_clicked(self, button: Gtk.Button):
        """Handle back button click (UI event → API call)."""
        self.explorer.go_back()
    
    def _on_forward_clicked(self, button: Gtk.Button):
        """Handle forward button click (UI event → API call)."""
        self.explorer.go_forward()
    
    def _on_up_clicked(self, button: Gtk.Button):
        """Handle up button click (UI event → API call)."""
        self.explorer.go_up()
    
    def _on_home_clicked(self, button: Gtk.Button):
        """Handle home button click (UI event → API call)."""
        self.explorer.go_home()
    
    def _on_refresh_clicked(self, button: Gtk.Button):
        """Handle refresh button click.
        
        Toggles between hierarchical tree view and flat list view.
        """
        # Toggle view mode
        self.hierarchical_view = not self.hierarchical_view
        
        if self.hierarchical_view:
            pass
        else:
            pass
        
        # Reload directory with new view mode
        self._load_current_directory()
    
    # ========================================================================
    # File Operations Toolbar Signal Handlers (UI events)
    # ========================================================================
    
    def _on_file_new_clicked(self, button: Gtk.Button):
        """Handle New File button click.
        
        Note: The main application (shypn.py) connects its own handler
        to this button to create new documents. This handler just updates
        the current file display.
        """
        # The main app will handle document creation
        # We just update the display
        # self.set_current_file("untitled.shy")
    
    def _on_file_open_clicked(self, button: Gtk.Button):
        """Handle Open File button click."""
        # TODO: Show file chooser dialog or use selected file from tree
        # For now, use the selected item if it's a file
        if self.selected_item_path and not self.selected_item_is_dir:
            self.set_current_file(self.selected_item_name)
    
    def _on_file_save_clicked(self, button: Gtk.Button):
        """Handle Save button click."""
        # TODO: Save current file to disk
        if self.current_opened_file:
            pass
        else:
            pass
    
    def _on_file_save_as_clicked(self, button: Gtk.Button):
        """Handle Save As button click."""
        # TODO: Show save as dialog
        if self.current_opened_file:
            pass
    
    def _on_file_new_folder_clicked(self, button: Gtk.Button):
        """Handle New Folder button click."""
        # Reuse the existing new folder dialog
        self._show_new_folder_dialog()
    
    def _on_row_activated(self, tree_view: Gtk.TreeView, path: Gtk.TreePath, 
                          column: Gtk.TreeViewColumn):
        """Handle double-click on row (UI event → API call).
        
        Args:
            tree_view: The tree view
            path: Tree path of activated row
            column: Column that was activated
        """
        # Get the row data (View)
        iter = self.store.get_iter(path)
        is_dir = self.store.get_value(iter, 3)  # Column 3: is_directory
        full_path = self.store.get_value(iter, 2)  # Column 2: path
        filename = self.store.get_value(iter, 1)  # Column 1: name
        
        if is_dir:
            # Navigate into directory (API call)
            self.explorer.navigate_to(full_path)
        else:
            # File activated - set as current file with full path for relative path calculation
            self.set_current_file(full_path)
            # TODO: Emit signal or call callback for file opening in canvas
    
    def _on_tree_view_button_press(self, widget, event):
        """Handle button press on tree view to show context menu.
        
        GTK3 version using button-press-event signal.
        
        Args:
            widget: The TreeView widget
            event: Gdk.EventButton
            
        Returns:
            True if event was handled, False otherwise
        """
        # Check for right-click (button 3)
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            
            if not self.context_menu:
                return False
            
            # Get the path at the clicked position
            result = self.tree_view.get_path_at_pos(int(event.x), int(event.y))
            
            if result is not None:
                # Clicked on a row - select that item
                path, column, cell_x, cell_y = result
                
                # Get the row data
                iter = self.store.get_iter(path)
                self.selected_item_name = self.store.get_value(iter, 1)  # name
                self.selected_item_path = self.store.get_value(iter, 2)  # path
                self.selected_item_is_dir = self.store.get_value(iter, 3)  # is_dir
            else:
                # Clicked on empty space - use current directory
                self.selected_item_name = os.path.basename(self.explorer.current_path)
                self.selected_item_path = self.explorer.current_path
                self.selected_item_is_dir = True
            
            # Show GTK3 menu at pointer position
            # popup() takes: parent_menu_shell, parent_menu_item, func, button, activate_time
            # For context menus, we use popup() with the event button and time
            self.context_menu.popup(None, None, None, None, event.button, event.time)
            
            return True  # Event handled
        
        return False  # Event not handled
    
    def _on_scroll_button_press(self, widget, event):
        """Handle button press on scrolled window for outside clicks.
        
        GTK3 version using button-press-event signal.
        
        Args:
            widget: The ScrolledWindow widget
            event: Gdk.EventButton
            
        Returns:
            True if event was handled, False otherwise
        """
        # Check for right-click (button 3) - delegate to main handler
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            
            # Delegate to the main handler (which will use menu.popup())
            return self._on_tree_view_button_press(self.tree_view, event)
        
        # GTK3 menus automatically dismiss on left-clicks outside, so no handler needed
        return False  # Event not handled
    
    # ========================================================================
    # Context Menu Actions (UI events → Dialogs → API calls)
    # ========================================================================
    
    # ========================================================================
    # Context Menu Handlers (GTK3 Gtk.Menu)
    # ========================================================================
    
    def _on_open_clicked(self, button):
        """Handle 'Open' context menu button."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path and not self.selected_item_is_dir:
            # Open the file (for now, just set as current file)
            self.set_current_file(self.selected_item_path)
            # TODO: Integrate with document management to actually open file in editor
    
    def _on_new_folder_clicked(self, button):
        """Handle 'New Folder' context menu button."""
        # Menu automatically dismisses in GTK3
        self._show_new_folder_dialog()
    
    def _on_cut_clicked(self, button):
        """Handle 'Cut' context menu button."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path:
            self.clipboard_path = self.selected_item_path
            self.clipboard_operation = 'cut'
    
    def _on_copy_clicked(self, button):
        """Handle 'Copy' context menu button."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path:
            self.clipboard_path = self.selected_item_path
            self.clipboard_operation = 'copy'
    
    def _on_paste_clicked(self, button):
        """Handle 'Paste' context menu button."""
        # Menu automatically dismisses in GTK3
        if not self.clipboard_path or not self.clipboard_operation:
            return
        
        import shutil
        
        source = self.clipboard_path
        source_name = os.path.basename(source)
        
        # Determine destination directory
        if self.selected_item_is_dir:
            dest_dir = self.selected_item_path
        else:
            dest_dir = self.explorer.current_path
        
        # Generate unique destination name if needed
        dest = os.path.join(dest_dir, source_name)
        counter = 1
        base_name, ext = os.path.splitext(source_name)
        while os.path.exists(dest):
            dest = os.path.join(dest_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        try:
            if self.clipboard_operation == 'copy':
                if os.path.isdir(source):
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
            elif self.clipboard_operation == 'cut':
                shutil.move(source, dest)
                # Clear clipboard after cut
                self.clipboard_path = None
                self.clipboard_operation = None
            
            # Refresh view
            self._load_current_directory()
        except Exception as e:
            pass
    
    def _on_duplicate_clicked(self, button):
        """Handle 'Duplicate' context menu button."""
        # Menu automatically dismisses in GTK3
        if not self.selected_item_path:
            return
        
        import shutil
        
        source = self.selected_item_path
        source_name = os.path.basename(source)
        base_name, ext = os.path.splitext(source_name)
        
        # Find next available name
        counter = 1
        dest = os.path.join(os.path.dirname(source), f"{base_name}_copy{ext}")
        while os.path.exists(dest):
            counter += 1
            dest = os.path.join(os.path.dirname(source), f"{base_name}_copy{counter}{ext}")
        
        try:
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            self._load_current_directory()
        except Exception as e:
            pass
    
    def _on_rename_clicked(self, button):
        """Handle 'Rename' context menu button."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path:
            self._show_rename_dialog()
    
    def _on_delete_clicked(self, button):
        """Handle 'Delete' context menu button."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path:
            self._show_delete_confirmation()
    
    def _on_refresh_clicked(self, button):
        """Handle 'Refresh' context menu button."""
        # Menu automatically dismisses in GTK3
        self._load_current_directory()
    
    def _on_properties_clicked(self, button):
        """Handle 'Properties' context menu button."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path:
            self._show_properties_dialog()
    
    # ========================================================================
    # Old Action Handlers (kept for backwards compatibility, now call button handlers)
    # ========================================================================
    
    def _on_open_action(self, action, parameter):
        """Handle 'Open' context menu action."""
        if self.selected_item_path and not self.selected_item_is_dir:
            # Open the file (for now, just set as current file)
            self.set_current_file(self.selected_item_path)
            # TODO: Integrate with document management to actually open file in editor
    
    def _on_new_folder_action(self, action, parameter):
        """Handle 'New Folder' context menu action."""
        self._show_new_folder_dialog()
    
    def _on_cut_action(self, action, parameter):
        """Handle 'Cut' context menu action."""
        if self.selected_item_path:
            self.clipboard_path = self.selected_item_path
            self.clipboard_operation = 'cut'
    
    def _on_copy_action(self, action, parameter):
        """Handle 'Copy' context menu action."""
        if self.selected_item_path:
            self.clipboard_path = self.selected_item_path
            self.clipboard_operation = 'copy'
    
    def _on_paste_action(self, action, parameter):
        """Handle 'Paste' context menu action."""
        if not self.clipboard_path or not self.clipboard_operation:
            return
        
        import shutil
        
        source = self.clipboard_path
        source_name = os.path.basename(source)
        
        # Determine destination directory
        if self.selected_item_is_dir:
            dest_dir = self.selected_item_path
        else:
            dest_dir = self.explorer.current_path
        
        # Generate unique destination name if needed
        dest = os.path.join(dest_dir, source_name)
        counter = 1
        base_name, ext = os.path.splitext(source_name)
        while os.path.exists(dest):
            dest = os.path.join(dest_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        try:
            if self.clipboard_operation == 'copy':
                if os.path.isdir(source):
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
            elif self.clipboard_operation == 'cut':
                shutil.move(source, dest)
                # Clear clipboard after cut
                self.clipboard_path = None
                self.clipboard_operation = None
            
            # Refresh view
            self._load_current_directory()
        except Exception as e:
            pass
    
    def _on_duplicate_action(self, action, parameter):
        """Handle 'Duplicate' context menu action."""
        if not self.selected_item_path:
            return
        
        import shutil
        
        source = self.selected_item_path
        source_name = os.path.basename(source)
        base_name, ext = os.path.splitext(source_name)
        
        # Find next available name
        counter = 1
        dest = os.path.join(os.path.dirname(source), f"{base_name}_copy{ext}")
        while os.path.exists(dest):
            counter += 1
            dest = os.path.join(os.path.dirname(source), f"{base_name}_copy{counter}{ext}")
        
        try:
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            self._load_current_directory()
        except Exception as e:
            pass
    
    def _on_rename_action(self, action, parameter):
        """Handle 'Rename' context menu action."""
        if self.selected_item_path:
            self._show_rename_dialog()
    
    def _on_delete_action(self, action, parameter):
        """Handle 'Delete' context menu action."""
        if self.selected_item_path:
            self._show_delete_confirmation()
    
    def _on_refresh_action(self, action, parameter):
        """Handle 'Refresh' context menu action."""
        self._load_current_directory()
    
    def _on_properties_action(self, action, parameter):
        """Handle 'Properties' context menu action."""
        if self.selected_item_path:
            self._show_properties_dialog()
    
    # ========================================================================
    # Dialogs for File Operations
    # ========================================================================
    
    def _show_new_folder_dialog(self):
        """Show dialog to create a new folder."""
        # Get the window for parent
        window = self.tree_view.get_root()
        
        dialog = Gtk.Dialog()
        dialog.set_title("New Folder")
        dialog.set_transient_for(window)
        dialog.set_modal(True)
        dialog.set_default_size(300, -1)
        
        # Add buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Create", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        # Create content
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)
        
        label = Gtk.Label(label="Folder name:")
        label.set_halign(Gtk.Align.START)
        content.pack_start(label, False, False, 0)
        label.show()
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("New Folder")
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)
        entry.show()
        
        # Show and handle response
        dialog.connect("response", lambda d, r: self._on_new_folder_response(d, r, entry))
        dialog.show()
    
    def _on_new_folder_response(self, dialog, response, entry):
        """Handle new folder dialog response."""
        if response == Gtk.ResponseType.OK:
            folder_name = entry.get_text().strip()
            if folder_name:
                success = self.explorer.create_folder(folder_name)
                if success:
                    pass
        
        dialog.close()
    
    def _show_rename_dialog(self):
        """Show dialog to rename selected item."""
        window = self.tree_view.get_root()
        
        dialog = Gtk.Dialog()
        dialog.set_title("Rename")
        dialog.set_transient_for(window)
        dialog.set_modal(True)
        dialog.set_default_size(300, -1)
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Rename", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)
        
        label = Gtk.Label(label="New name:")
        label.set_halign(Gtk.Align.START)
        content.pack_start(label, False, False, 0)
        label.show()
        
        entry = Gtk.Entry()
        entry.set_text(self.selected_item_name or "")
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)
        entry.show()
        
        dialog.connect("response", lambda d, r: self._on_rename_response(d, r, entry))
        dialog.show()
    
    def _on_rename_response(self, dialog, response, entry):
        """Handle rename dialog response."""
        if response == Gtk.ResponseType.OK:
            new_name = entry.get_text().strip()
            if new_name and self.selected_item_path:
                success = self.explorer.rename_item(self.selected_item_path, new_name)
                if success:
                    pass
        
        dialog.close()
    
    def _show_delete_confirmation(self):
        """Show confirmation dialog for delete operation."""
        window = self.tree_view.get_root()
        
        dialog = Gtk.MessageDialog(
            transient_for=window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete '{self.selected_item_name}'?"
        )
        
        if self.selected_item_is_dir:
            dialog.set_property("secondary-text", 
                              "This folder will be deleted. Only empty folders can be deleted.")
        else:
            dialog.set_property("secondary-text", 
                              "This file will be permanently deleted.")
        
        dialog.connect("response", self._on_delete_response)
        dialog.show()
    
    def _on_delete_response(self, dialog, response):
        """Handle delete confirmation response."""
        if response == Gtk.ResponseType.YES:
            if self.selected_item_path:
                success = self.explorer.delete_item(self.selected_item_path)
                if success:
                    pass
        
        dialog.close()
    
    def _show_properties_dialog(self):
        """Show properties dialog for selected item."""
        info = self.explorer.get_file_info(self.selected_item_path)
        if not info:
            return
        
        window = self.tree_view.get_root()
        
        dialog = Gtk.Dialog()
        dialog.set_title(f"Properties - {info['name']}")
        dialog.set_transient_for(window)
        dialog.set_modal(True)
        dialog.set_default_size(400, -1)
        
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)
        
        # Create property grid
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        content.pack_start(grid, True, True, 0)
        
        row = 0
        
        def add_property(label_text, value_text):
            nonlocal row
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")  # GTK3 uses get_style_context()
            grid.attach(label, 0, row, 1, 1)
            
            value = Gtk.Label(label=value_text)
            value.set_halign(Gtk.Align.START)
            value.set_selectable(True)
            grid.attach(value, 1, row, 1, 1)
            
            row += 1
        
        add_property("Name:", info['name'])
        add_property("Type:", "Folder" if info['is_directory'] else "File")
        add_property("Location:", os.path.dirname(info['path']))
        
        if not info['is_directory']:
            add_property("Size:", info['size_formatted'])
        elif 'item_count' in info:
            add_property("Items:", str(info['item_count']))
        
        add_property("Modified:", info['modified_formatted'])
        
        if 'created_formatted' in info:
            add_property("Created:", info['created_formatted'])
        
        add_property("Permissions:", info['permissions'])
        
        # Access rights
        access = []
        if info['readable']:
            access.append("Read")
        if info['writable']:
            access.append("Write")
        if info['executable']:
            access.append("Execute")
        add_property("Access:", ", ".join(access) if access else "None")
        
        dialog.connect("response", lambda d, r: d.close())
        dialog.show_all()
    
    # ========================================================================
    # Public API (for left_panel_loader or other components)
    # ========================================================================
    
    def navigate_to(self, path: str):
        """Public method to navigate to a specific path.
        
        Args:
            path: Directory path to navigate to
        """
        self.explorer.navigate_to(path)
    
    def get_current_path(self) -> str:
        """Get current directory path.
        
        Returns:
            Current path string
        """
        return self.explorer.current_path
    
    def set_current_file(self, filename_or_path: Optional[str]):
        """Set the currently opened file to display in toolbar.
        
        Shows the file with its relative path from the models directory.
        For example: 'subfolder1/test.txt' or just 'file.txt' if in root.
        
        This should be called by the main application when a file is opened
        in the canvas/editor to show which file is being worked on.
        
        Args:
            filename_or_path: Name or full path of the opened file, or None to clear
        """
        if not filename_or_path:
            self.current_opened_file = None
            if self.current_file_label:
                self.current_file_label.set_text("—")
            return
        
        # Calculate relative path from models directory
        if os.path.isabs(filename_or_path):
            # Full path provided - calculate relative path from root boundary
            try:
                relative_path = os.path.relpath(filename_or_path, self.explorer.root_boundary)
                display_text = relative_path
            except ValueError:
                # Path is not relative to root boundary, just use filename
                display_text = os.path.basename(filename_or_path)
        else:
            # Just a filename provided - use as is
            display_text = filename_or_path
        
        self.current_opened_file = display_text
        
        # Update the label immediately
        if self.current_file_label:
            self.current_file_label.set_text(display_text)
        
