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
from typing import Optional, Callable

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, GLib, Pango, Gio, Gdk
except Exception as e:
    print(f'ERROR: GTK3 not available in file_explorer_panel: {e}', file=sys.stderr)
    sys.exit(1)

# Import the FileExplorer API
from shypn.file import FileExplorer


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
        
        # Callback for opening files (set by main app to integrate with canvas)
        self.on_file_open_requested: Optional[Callable[[str], None]] = None
        
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
        
        # Apply CSS styling to TreeView
        self._apply_tree_view_css()
        
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
        
        # Text renderer - editable for inline file/folder creation
        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        text_renderer.set_property("editable", False)  # Only editable when explicitly set
        text_renderer.connect("edited", self._on_cell_edited)
        text_renderer.connect("editing-canceled", self._on_cell_editing_canceled)
        name_column.pack_start(text_renderer, True)
        name_column.add_attribute(text_renderer, "text", 1)
        
        # Store reference to text renderer for enabling/disabling editing
        self.text_renderer = text_renderer
        
        self.tree_view.append_column(name_column)
    
    def _apply_tree_view_css(self):
        """Apply CSS styling to improve TreeView appearance."""
        css_provider = Gtk.CssProvider()
        
        # Modern, clean TreeView styling
        css = b"""
        /* File explorer TreeView styling */
        treeview {
            background-color: #fafafa;
            color: #2e3436;
        }
        
        /* Row styling */
        treeview.view {
            padding: 2px;
        }
        
        /* Selected row */
        treeview.view:selected {
            background-color: #4a90d9;
            color: #ffffff;
        }
        
        /* Hover effect */
        treeview.view:hover {
            background-color: #e8e8e8;
        }
        
        /* Selected and focused */
        treeview.view:selected:focus {
            background-color: #2a76c6;
            color: #ffffff;
        }
        
        /* Cell padding and spacing */
        treeview.view cell {
            padding-top: 4px;
            padding-bottom: 4px;
            padding-left: 6px;
            padding-right: 6px;
        }
        
        /* Header styling */
        treeview header button {
            background-color: #e8e8e8;
            border: 1px solid #d0d0d0;
            padding: 4px 8px;
            font-weight: bold;
        }
        
        /* Separator lines */
        treeview.view.separator {
            min-height: 2px;
            color: #d0d0d0;
        }
        
        /* Expander arrow for tree hierarchy */
        treeview.view.expander {
            color: #5a5a5a;
        }
        
        treeview.view.expander:hover {
            color: #2a76c6;
        }
        """
        
        try:
            css_provider.load_from_data(css)
            
            # Apply to the TreeView widget
            style_context = self.tree_view.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            print("[FileExplorer] CSS styling applied to TreeView")
        except Exception as e:
            print(f"[FileExplorer] Warning: Could not apply CSS styling: {e}")
    
        
    
    def _setup_context_menu(self):
        """Setup context menu as a proper GTK3 Gtk.Menu.
        
        Organized into groups:
        - File Operations: Open, New File, New Folder
        - File Modifications: Rename, Delete
        - View: Refresh, Properties
        
        GTK3 menus automatically handle:
        - Dismiss on Escape key
        - Dismiss on click outside
        - Focus management
        """
        # Create a proper GTK3 Menu
        self.context_menu = Gtk.Menu()
        
        # Add menu items organized by groups
        menu_items = [
            # Group 1: File Operations
            ("Open", self._on_context_open_clicked),
            ("New File", self._on_context_new_file_clicked),
            ("New Folder", self._on_context_new_folder_clicked),
            ("---", None),  # Separator
            
            # Group 2: File Modifications
            ("Rename", self._on_rename_clicked),
            ("Delete", self._on_delete_clicked),
            ("---", None),  # Separator
            
            # Group 3: View Operations
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
        # These are now handled by FileExplorerPanel itself, cooperating with
        # ModelCanvasLoader and NetObjPersistency (wired via set_canvas_loader
        # and set_persistency_manager methods)
        if self.new_button:
            self.new_button.connect("clicked", lambda btn: self.new_document())
        if self.open_button:
            self.open_button.connect("clicked", lambda btn: self.open_document())
        if self.save_button:
            self.save_button.connect("clicked", lambda btn: self.save_current_document())
        if self.save_as_button:
            self.save_as_button.connect("clicked", lambda btn: self.save_current_document_as())
        
        # New Folder button (file explorer specific)
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
    
    # NOTE: File operation toolbar buttons (New/Open/Save/Save As) are handled
    # in shypn.py main app to integrate with NetObjPersistency and ModelCanvasLoader.
    # Only the New Folder button is handled here for file explorer-specific operations.
    
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
            # File activated - open it in canvas
            if full_path.endswith('.shy'):
                # Request main app to open this Petri net file
                if self.on_file_open_requested:
                    self.on_file_open_requested(full_path)
                else:
                    # Fallback: Load file using document operations
                    self._open_file_from_path(full_path)
            else:
                # Not a Petri net file, just update display
                self.set_current_file(full_path)
    
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
    # New Context Menu Handlers (File Operations Group)
    # ========================================================================
    
    def _on_context_open_clicked(self, button):
        """Handle 'Open' from context menu - opens file in canvas."""
        # Menu automatically dismisses in GTK3
        if self.selected_item_path and not self.selected_item_is_dir:
            # Check if file is a .shy file (Petri net file)
            if not self.selected_item_path.endswith('.shy'):
                if self.explorer.on_error:
                    self.explorer.on_error("Can only open .shy Petri net files")
                return
            
            # Open the file in canvas
            if self.on_file_open_requested:
                self.on_file_open_requested(self.selected_item_path)
            else:
                # Fallback: Load file using document operations
                self._open_file_from_path(self.selected_item_path)
    
    def _on_context_new_file_clicked(self, button):
        """Handle 'New File' from context menu - creates new .shy file inline."""
        # Menu automatically dismisses in GTK3
        self._start_inline_edit_new_file()
    
    def _on_context_new_folder_clicked(self, button):
        """Handle 'New Folder' from context menu - creates new folder inline."""
        # Menu automatically dismisses in GTK3
        self._start_inline_edit_new_folder()
    
    def _on_context_save_clicked(self, button):
        """Handle 'Save' from context menu - saves current document."""
        # Menu automatically dismisses in GTK3
        self.save_current_document()
    
    def _on_context_save_as_clicked(self, button):
        """Handle 'Save As' from context menu - saves with new name."""
        # Menu automatically dismisses in GTK3
        self.save_current_document_as()
    
    # ========================================================================
    # Inline Editing for New Files/Folders
    # ========================================================================
    
    def _start_inline_edit_new_file(self):
        """Start inline editing to create a new .shy file at cursor position."""
        # Determine where to insert: in selected directory or current directory
        if self.selected_item_is_dir:
            parent_dir = self.selected_item_path
            parent_iter = self._find_iter_for_path(self.selected_item_path)
        else:
            parent_dir = self.explorer.current_path
            parent_iter = None
        
        # Insert a new temporary row
        icon_name = "text-x-generic"  # Generic file icon
        temp_name = "new_file.shy"
        temp_path = os.path.join(parent_dir, temp_name)
        
        # Add temporary row to store
        new_iter = self.store.append(parent_iter, [icon_name, temp_name, temp_path, False])
        
        # Get path to the new row
        tree_path = self.store.get_path(new_iter)
        
        # Expand parent if needed
        if parent_iter:
            self.tree_view.expand_to_path(tree_path)
        
        # Make text renderer editable temporarily
        self.text_renderer.set_property("editable", True)
        
        # Store context for editing
        self.editing_iter = new_iter
        self.editing_parent_dir = parent_dir
        self.editing_is_folder = False
        
        # Set cursor and start editing
        column = self.tree_view.get_column(0)
        self.tree_view.set_cursor(tree_path, column, True)
    
    def _start_inline_edit_new_folder(self):
        """Start inline editing to create a new folder at cursor position."""
        # Determine where to insert: in selected directory or current directory
        if self.selected_item_is_dir:
            parent_dir = self.selected_item_path
            parent_iter = self._find_iter_for_path(self.selected_item_path)
        else:
            parent_dir = self.explorer.current_path
            parent_iter = None
        
        # Insert a new temporary row
        icon_name = "folder"
        temp_name = "New Folder"
        temp_path = os.path.join(parent_dir, temp_name)
        
        # Add temporary row to store
        new_iter = self.store.append(parent_iter, [icon_name, temp_name, temp_path, True])
        
        # Get path to the new row
        tree_path = self.store.get_path(new_iter)
        
        # Expand parent if needed
        if parent_iter:
            self.tree_view.expand_to_path(tree_path)
        
        # Make text renderer editable temporarily
        self.text_renderer.set_property("editable", True)
        
        # Store context for editing
        self.editing_iter = new_iter
        self.editing_parent_dir = parent_dir
        self.editing_is_folder = True
        
        # Set cursor and start editing
        column = self.tree_view.get_column(0)
        self.tree_view.set_cursor(tree_path, column, True)
    
    def _find_iter_for_path(self, path):
        """Find TreeIter for given file path.
        
        Args:
            path: File system path to find
            
        Returns:
            TreeIter if found, None otherwise
        """
        def search_tree(model, iter_node):
            while iter_node:
                iter_path = model.get_value(iter_node, 2)  # Column 2 is path
                if iter_path == path:
                    return iter_node
                
                # Check children
                if model.iter_has_child(iter_node):
                    child_iter = model.iter_children(iter_node)
                    result = search_tree(model, child_iter)
                    if result:
                        return result
                
                iter_node = model.iter_next(iter_node)
            return None
        
        return search_tree(self.store, self.store.get_iter_first())
    
    def _on_cell_edited(self, renderer, path, new_text):
        """Handle cell editing completion - create the file/folder.
        
        Args:
            renderer: CellRendererText
            path: Tree path (string)
            new_text: New text entered by user
        """
        # Disable editing
        self.text_renderer.set_property("editable", False)
        
        if not new_text or new_text.strip() == "":
            # User entered empty name - cancel
            if hasattr(self, 'editing_iter') and self.editing_iter:
                self.store.remove(self.editing_iter)
            return
        
        # Clean up the name
        new_text = new_text.strip()
        
        # Add .shy extension if creating a file and not already present
        if not self.editing_is_folder and not new_text.endswith('.shy'):
            new_text += '.shy'
        
        # Build full path
        full_path = os.path.join(self.editing_parent_dir, new_text)
        
        # Check if already exists
        if os.path.exists(full_path):
            if self.explorer.on_error:
                self.explorer.on_error(f"'{new_text}' already exists")
            # Remove temporary row
            if hasattr(self, 'editing_iter') and self.editing_iter:
                self.store.remove(self.editing_iter)
            return
        
        try:
            if self.editing_is_folder:
                # Create directory
                os.makedirs(full_path, exist_ok=True)
            else:
                # Create empty .shy file with minimal JSON structure
                from shypn.data.canvas.document_model import DocumentModel
                doc = DocumentModel()
                doc.save_to_file(full_path)
            
            # Refresh the tree view
            self._load_current_directory()
            
        except Exception as e:
            if self.explorer.on_error:
                self.explorer.on_error(f"Failed to create: {e}")
            # Remove temporary row
            if hasattr(self, 'editing_iter') and self.editing_iter:
                self.store.remove(self.editing_iter)
        
        # Clean up editing context
        if hasattr(self, 'editing_iter'):
            delattr(self, 'editing_iter')
    
    def _on_cell_editing_canceled(self, renderer):
        """Handle cell editing cancellation - remove temporary row.
        
        Args:
            renderer: CellRendererText
        """
        # Disable editing
        self.text_renderer.set_property("editable", False)
        
        # Remove temporary row
        if hasattr(self, 'editing_iter') and self.editing_iter:
            self.store.remove(self.editing_iter)
            delattr(self, 'editing_iter')

    
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
        # Get the toplevel window for parent (GTK3)
        window = self.tree_view.get_toplevel()
        
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
        window = self.tree_view.get_toplevel()
        
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
        window = self.tree_view.get_toplevel()
        
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
                    # Refresh tree view to show deletion
                    self._load_current_directory()
                    print(f"[FileExplorer] Deleted: {self.selected_item_path}")
                else:
                    # Show error if deletion failed
                    if self.explorer.on_error:
                        self.explorer.on_error(f"Failed to delete '{self.selected_item_name}'")
        
        dialog.close()
    
    def _show_properties_dialog(self):
        """Show properties dialog for selected item."""
        info = self.explorer.get_file_info(self.selected_item_path)
        if not info:
            return
        
        window = self.tree_view.get_toplevel()
        
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
    
    def set_persistency_manager(self, persistency):
        """Wire file explorer to persistency manager for file operations integration.
        
        This connects the file explorer to receive notifications about file operations
        (save, load, dirty state changes) so the UI can stay synchronized with the
        actual state of the document.
        
        Args:
            persistency: NetObjPersistency instance from main application
        """
        from shypn.file import NetObjPersistency
        
        self.persistency = persistency
        
        # Wire callbacks to receive notifications from persistency manager
        persistency.on_file_saved = self._on_file_saved_callback
        persistency.on_file_loaded = self._on_file_loaded_callback
        persistency.on_dirty_changed = self._on_dirty_changed_callback
    
    def set_canvas_loader(self, canvas_loader):
        """Wire file explorer to canvas loader for document operations integration.
        
        This allows file explorer to access the current canvas manager and its
        is_default_filename() flag for proper save operation behavior.
        
        Args:
            canvas_loader: ModelCanvasLoader instance from main application
        """
        self.canvas_loader = canvas_loader
    
    # ========================================================================
    # File Operations (cooperating with ModelCanvasManager and NetObjPersistency)
    # ========================================================================
    
    def save_current_document(self):
        """Save the current document using the persistency manager.
        
        This method properly checks the ModelCanvasManager's is_default_filename()
        flag to determine if a file chooser should be shown.
        """
        print("[FileExplorer] save_current_document() called")
        
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            print("[FileExplorer] Error: Canvas loader not wired")
            return
        
        if not hasattr(self, 'persistency') or self.persistency is None:
            print("[FileExplorer] Error: Persistency manager not wired")
            return
        
        # Get current document from canvas loader
        drawing_area = self.canvas_loader.get_current_document()
        if drawing_area is None:
            print("[FileExplorer] No document to save")
            return
        
        # Get canvas manager for the current document
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        if manager is None:
            print("[FileExplorer] No canvas manager found")
            return
        
        # Debug: Print manager state
        print(f"[FileExplorer] Manager filename: '{manager.filename}'")
        print(f"[FileExplorer] is_default_filename(): {manager.is_default_filename()}")
        print(f"[FileExplorer] Calling save_document with is_default_filename={manager.is_default_filename()}")
        
        # Convert manager's Petri net objects to DocumentModel for saving
        document = manager.to_document_model()
        
        # Save using persistency manager with is_default_filename flag
        # This ensures file chooser is shown for documents with "default" filename
        self.persistency.save_document(
            document,
            save_as=False,
            is_default_filename=manager.is_default_filename()
        )
    
    def save_current_document_as(self):
        """Save the current document with a new name (Save As).
        
        Always shows file chooser regardless of filename state.
        """
        print("[FileExplorer] save_current_document_as() called")
        
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            print("[FileExplorer] Error: Canvas loader not wired")
            return
        
        if not hasattr(self, 'persistency') or self.persistency is None:
            print("[FileExplorer] Error: Persistency manager not wired")
            return
        
        # Get current document from canvas loader
        drawing_area = self.canvas_loader.get_current_document()
        if drawing_area is None:
            print("[FileExplorer] No document to save")
            return
        
        # Get canvas manager for the current document
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        if manager is None:
            print("[FileExplorer] No canvas manager found")
            return
        
        print(f"[FileExplorer] Current filename: '{manager.filename}'")
        print("[FileExplorer] Calling save_document with save_as=True")
        
        # Convert manager's Petri net objects to DocumentModel for saving
        document = manager.to_document_model()
        
        # Save As always prompts for new filename
        self.persistency.save_document(
            document,
            save_as=True,
            is_default_filename=manager.is_default_filename()
        )
    
    def open_document(self):
        """Open a document from file using the persistency manager.
        
        Creates a new tab with the loaded document and sets the manager's filename
        correctly so is_default_filename() returns False.
        """
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            print("[FileExplorer] Error: Canvas loader not wired")
            return
        
        if not hasattr(self, 'persistency') or self.persistency is None:
            print("[FileExplorer] Error: Persistency manager not wired")
            return
        
        # Load using persistency manager
        document, filepath = self.persistency.load_document()
        
        if document and filepath:
            self._load_document_into_canvas(document, filepath)
    
    def _open_file_from_path(self, filepath: str):
        """Open a specific file from path into canvas.
        
        Used by double-click and context menu Open operations.
        
        Args:
            filepath: Full path to .shy file to open
        """
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            print("[FileExplorer] Error: Canvas loader not wired")
            return
        
        if not hasattr(self, 'persistency') or self.persistency is None:
            print("[FileExplorer] Error: Persistency manager not wired")
            return
        
        try:
            # Load document from file
            from shypn.data.canvas.document_model import DocumentModel
            document = DocumentModel.load_from_file(filepath)
            
            # Load into canvas
            self._load_document_into_canvas(document, filepath)
            
            print(f"[FileExplorer] Opened file: {filepath}")
            
        except Exception as e:
            print(f"[FileExplorer] Error opening file: {e}")
            import traceback
            traceback.print_exc()
            if self.explorer.on_error:
                self.explorer.on_error(f"Failed to open file: {e}")
    
    def _load_document_into_canvas(self, document, filepath: str):
        """Load a document model into the canvas.
        
        Helper method shared by open_document() and _open_file_from_path().
        
        Args:
            document: DocumentModel instance
            filepath: Full path to the file
        """
        if not document or not filepath:
            return
        
        # Create new tab with loaded document
        import os
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        
        # Add document with the base filename (without extension)
        # This ensures ModelCanvasManager gets initialized with the correct filename
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        print(f"[FileExplorer] add_document returned: page_index={page_index}, drawing_area={drawing_area}")
        
        # Get the canvas manager
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        print(f"[FileExplorer] Retrieved canvas manager: {manager}")
        if manager:
            # Load object lists from document into manager
            manager.places = list(document.places)
            manager.transitions = list(document.transitions)
            manager.arcs = list(document.arcs)
            
            # Sync ID counters to prevent ID conflicts
            manager._next_place_id = document._next_place_id
            manager._next_transition_id = document._next_transition_id
            manager._next_arc_id = document._next_arc_id
            
            # Update persistency manager state
            if hasattr(self, 'persistency') and self.persistency:
                self.persistency.set_filepath(filepath)
                self.persistency.mark_clean()
                print(f"[FileExplorer] Persistency state updated: filepath={filepath}, dirty=False")
            
            # Trigger redraw - signals all canvas instances to draw the model
            drawing_area.queue_draw()
            
            print(f"[FileExplorer] Document loaded into canvas: {base_name}")
            print(f"[FileExplorer] Objects: {len(manager.places)} places, "
                  f"{len(manager.transitions)} transitions, {len(manager.arcs)} arcs")
            print(f"[FileExplorer] is_default_filename() = {manager.is_default_filename()}")
        else:
            print("[FileExplorer] Error: Could not get canvas manager")
    
    def new_document(self):
        """Create a new document.
        
        Checks for unsaved changes and creates a new tab with "default" filename.
        """
        print("[FileExplorer] new_document() called")
        
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            print("[FileExplorer] Error: Canvas loader not wired")
            return
        
        if not hasattr(self, 'persistency') or self.persistency is None:
            print("[FileExplorer] Error: Persistency manager not wired")
            return
        
        # Check for unsaved changes
        if not self.persistency.check_unsaved_changes():
            print("[FileExplorer] User cancelled new document")
            return
        
        # Create new document
        if self.persistency.new_document():
            print("[FileExplorer] Creating new document tab with default filename")
            self.canvas_loader.add_document()  # Uses "default" filename
    
    # ========================================================================
    # Persistency Callbacks (for integration with file operations)
    # ========================================================================
    
    def _on_file_saved_callback(self, filepath: str):
        """Called by NetObjPersistency when a file is saved.
        
        Updates the current file display and refreshes the file explorer tree
        to show the newly saved file.
        
        Args:
            filepath: Full path to the saved file
        """
        # Update current file display
        self.set_current_file(filepath)
        
        # Refresh tree view to show the saved file
        self._load_current_directory()
    
    def _on_file_loaded_callback(self, filepath: str, document):
        """Called by NetObjPersistency when a file is loaded.
        
        Updates the current file display to show the loaded file.
        
        Args:
            filepath: Full path to the loaded file
            document: The loaded DocumentModel instance
        """
        # Update current file display
        self.set_current_file(filepath)
        
        # Optionally navigate to the directory containing the loaded file
        # (commented out to avoid unexpected navigation)
        # directory = os.path.dirname(filepath)
        # if directory and os.path.isdir(directory):
        #     self.explorer.navigate_to(directory)
    
    def _on_dirty_changed_callback(self, is_dirty: bool):
        """Called by NetObjPersistency when dirty state changes.
        
        Updates the current file display to show dirty state indicator (asterisk).
        
        Args:
            is_dirty: True if document has unsaved changes, False otherwise
        """
        if not self.current_opened_file:
            return
        
        # Update current file label with dirty indicator
        if self.current_file_label:
            display = self.current_opened_file
            
            # Add or remove asterisk for dirty state
            if is_dirty and not display.endswith(' *'):
                display = display + ' *'
            elif not is_dirty and display.endswith(' *'):
                display = display[:-2]  # Remove ' *'
            
            self.current_file_label.set_text(display)
    
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
        
