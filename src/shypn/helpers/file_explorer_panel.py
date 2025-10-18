"""File Explorer Panel Controller for SHYpn.

This module provides the controller layer for the file explorer functionality.
It connects the FileExplorer API (business logic) to the GTK UI defined in
left_panel.ui (view).

This follows the MVC pattern:
    pass
- Model: FileExplorer API (shypn.api.file.explorer)
- View: left_panel.ui (GTK XML)
- Controller: FileExplorerPanel (this file)

The controller:
    pass
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

    def __init__(self, builder: Gtk.Builder, base_path: Optional[str]=None, root_boundary: Optional[str]=None):
        """Initialize the file explorer controller.
        
        Args:
            builder: GTK Builder instance with left_panel.ui loaded
            base_path: Starting directory (default: project root or home)
            root_boundary: Root boundary - cannot navigate above this (default: same as base_path)
        """
        self.builder = builder
        self.explorer = FileExplorer(base_path=base_path, root_boundary=root_boundary)
        self.explorer.on_path_changed = self._on_path_changed
        self.explorer.on_error = self._on_error
        # Default file is now in workspace/examples/
        self.current_opened_file: Optional[str] = 'workspace/examples/simple.shy'
        self.hierarchical_view = True
        self.selected_item_path: Optional[str] = None
        self.selected_item_name: Optional[str] = None
        self.selected_item_is_dir: bool = False
        self.clipboard_path: Optional[str] = None
        self.clipboard_operation: Optional[str] = None
        self.on_file_open_requested: Optional[Callable[[str], None]] = None
        self._get_widgets()
        self._configure_tree_view()
        self._setup_context_menu()
        self._connect_signals()
        self._load_current_directory()

    def _get_widgets(self):
        """Get widget references from builder.
        
        All widgets are defined in left_panel.ui XML file.
        This method just gets references to connect logic.
        Most widgets are optional except for the tree_view.
        """
        self.tree_view = self.builder.get_object('file_browser_tree')
        self.scrolled_window = self.builder.get_object('file_browser_scroll')
        self.new_button = self.builder.get_object('file_new_button')
        self.open_button = self.builder.get_object('file_open_button')
        self.save_button = self.builder.get_object('file_save_button')
        self.save_as_button = self.builder.get_object('file_save_as_button')
        self.new_folder_button = self.builder.get_object('file_new_folder_button')
        self.back_button = self.builder.get_object('nav_back_button')
        self.forward_button = self.builder.get_object('nav_forward_button')
        self.up_button = self.builder.get_object('nav_up_button')
        self.home_button = self.builder.get_object('nav_home_button')
        self.refresh_button = self.builder.get_object('nav_refresh_button')
        self.current_file_entry = self.builder.get_object('current_file_entry')
        self.current_file_label = self.current_file_entry
        self.status_label = self.builder.get_object('file_browser_status')
        if self.tree_view is None:
            raise ValueError("TreeView 'file_browser_tree' not found in UI file")
        if self.scrolled_window is None:
            raise ValueError("ScrolledWindow 'file_browser_scroll' not found in UI file")

    def _configure_tree_view(self):
        """Configure TreeView model and columns.
        
        This is display logic - how data is presented.
        The TreeView widget itself is defined in XML.
        """
        self.store = Gtk.TreeStore(str, str, str, bool)
        self.tree_view.set_model(self.store)
        self._apply_tree_view_css()
        name_column = Gtk.TreeViewColumn()
        name_column.set_title('Name')
        name_column.set_expand(True)
        name_column.set_sort_column_id(1)
        name_column.set_resizable(True)
        icon_renderer = Gtk.CellRendererPixbuf()
        name_column.pack_start(icon_renderer, False)
        name_column.add_attribute(icon_renderer, 'icon-name', 0)
        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        text_renderer.set_property('editable', False)
        text_renderer.connect('edited', self._on_cell_edited)
        text_renderer.connect('editing-canceled', self._on_cell_editing_canceled)
        name_column.pack_start(text_renderer, True)
        name_column.add_attribute(text_renderer, 'text', 1)
        self.text_renderer = text_renderer
        self.tree_view.append_column(name_column)

    def _apply_tree_view_css(self):
        """Apply CSS styling to improve TreeView appearance."""
        css_provider = Gtk.CssProvider()
        css = b'\n        /* File explorer TreeView styling */\n        treeview {\n            background-color: #fafafa;\n            color: #2e3436;\n        }\n        \n        /* Row styling */\n        treeview.view {\n            padding: 2px;\n        }\n        \n        /* Selected row */\n        treeview.view:selected {\n            background-color: #4a90d9;\n            color: #ffffff;\n        }\n        \n        /* Hover effect */\n        treeview.view:hover {\n            background-color: #e8e8e8;\n        }\n        \n        /* Selected and focused */\n        treeview.view:selected:focus {\n            background-color: #2a76c6;\n            color: #ffffff;\n        }\n        \n        /* Cell padding and spacing */\n        treeview.view cell {\n            padding-top: 4px;\n            padding-bottom: 4px;\n            padding-left: 6px;\n            padding-right: 6px;\n        }\n        \n        /* Header styling */\n        treeview header button {\n            background-color: #e8e8e8;\n            border: 1px solid #d0d0d0;\n            padding: 4px 8px;\n            font-weight: bold;\n        }\n        \n        /* Separator lines */\n        treeview.view.separator {\n            min-height: 2px;\n            color: #d0d0d0;\n        }\n        \n        /* Expander arrow for tree hierarchy */\n        treeview.view.expander {\n            color: #5a5a5a;\n        }\n        \n        treeview.view.expander:hover {\n            color: #2a76c6;\n        }\n        '
        try:
            css_provider.load_from_data(css)
            style_context = self.tree_view.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception as e:

            pass

    def _setup_context_menu(self):
        """Setup context menu as a proper GTK3 Gtk.Menu.
        
        Organized into groups:
            pass
        - File Operations: Open, New File, New Folder
        - File Modifications: Rename, Delete
        - View: Refresh, Properties
        
        GTK3 menus automatically handle:
            pass
        - Dismiss on Escape key
        - Dismiss on click outside
        - Focus management
        """
        self.context_menu = Gtk.Menu()
        # Attach menu to tree_view for proper Wayland parent window handling
        self.context_menu.attach_to_widget(self.tree_view, None)
        menu_items = [('Open', self._on_context_open_clicked), ('New File', self._on_context_new_file_clicked), ('New Folder', self._on_context_new_folder_clicked), ('---', None), ('Rename', self._on_rename_clicked), ('Delete', self._on_delete_clicked), ('---', None), ('Refresh', self._on_refresh_clicked), ('Properties', self._on_properties_clicked)]
        for label, callback in menu_items:
            if label == '---':
                separator = Gtk.SeparatorMenuItem()
                self.context_menu.append(separator)
            else:
                menu_item = Gtk.MenuItem(label=label)
                if callback:
                    menu_item.connect('activate', callback)
                self.context_menu.append(menu_item)
        self.context_menu.show_all()

    def _connect_signals(self):
        """Connect widget signals to controller methods.
        
        This is the Controller's main job - connecting UI events to business logic.
        """
        if self.new_button:
            self.new_button.connect('clicked', lambda btn: self.new_document())
        if self.open_button:
            self.open_button.connect('clicked', lambda btn: self.open_document())
        if self.save_button:
            self.save_button.connect('clicked', lambda btn: self.save_current_document())
        if self.save_as_button:
            self.save_as_button.connect('clicked', lambda btn: self.save_current_document_as())
        if self.new_folder_button:
            self.new_folder_button.connect('clicked', self._on_file_new_folder_clicked)
        if self.back_button:
            self.back_button.connect('clicked', self._on_back_clicked)
        if self.forward_button:
            self.forward_button.connect('clicked', self._on_forward_clicked)
        if self.up_button:
            self.up_button.connect('clicked', self._on_up_clicked)
        if self.home_button:
            self.home_button.connect('clicked', self._on_home_clicked)
        if self.refresh_button:
            self.refresh_button.connect('clicked', self._on_refresh_clicked)
        self.tree_view.connect('row-activated', self._on_row_activated)
        self.tree_view.connect('button-press-event', self._on_tree_view_button_press)
        self.scrolled_window.connect('button-press-event', self._on_scroll_button_press)

    def _get_expanded_paths(self):
        """Get list of currently expanded directory paths in tree view.
        
        Returns:
            set: Set of expanded directory paths
        """
        expanded = set()
        
        def collect_expanded(tree_iter):
            """Recursively collect expanded paths."""
            while tree_iter:
                path = self.store.get_value(tree_iter, 2)  # Column 2 is the path
                is_dir = self.store.get_value(tree_iter, 3)  # Column 3 is is_directory
                tree_path = self.store.get_path(tree_iter)
                
                if is_dir and self.tree_view.row_expanded(tree_path):
                    expanded.add(path)
                
                # Check children
                child_iter = self.store.iter_children(tree_iter)
                if child_iter:
                    collect_expanded(child_iter)
                
                tree_iter = self.store.iter_next(tree_iter)
        
        # Start from root
        root_iter = self.store.get_iter_first()
        if root_iter:
            collect_expanded(root_iter)
        
        return expanded
    
    def _restore_expanded_paths(self, expanded_paths):
        """Restore expanded state for directories in tree view.
        
        Args:
            expanded_paths: Set of directory paths that should be expanded
        """
        if not expanded_paths:
            return
        
        def expand_paths(tree_iter):
            """Recursively expand paths that were previously expanded."""
            while tree_iter:
                path = self.store.get_value(tree_iter, 2)  # Column 2 is the path
                is_dir = self.store.get_value(tree_iter, 3)  # Column 3 is is_directory
                tree_path = self.store.get_path(tree_iter)
                
                if is_dir and path in expanded_paths:
                    self.tree_view.expand_to_path(tree_path)
                
                # Check children
                child_iter = self.store.iter_children(tree_iter)
                if child_iter:
                    expand_paths(child_iter)
                
                tree_iter = self.store.iter_next(tree_iter)
        
        # Start from root
        root_iter = self.store.get_iter_first()
        if root_iter:
            expand_paths(root_iter)

    def _load_current_directory(self):
        """Load current directory contents into tree view (Controller logic)."""
        # Save expanded state before clearing
        expanded_paths = self._get_expanded_paths() if self.hierarchical_view else set()
        
        self.store.clear()
        if self.hierarchical_view:
            self._load_directory_tree(self.explorer.current_path, None)
            # Restore expanded state after loading
            self._restore_expanded_paths(expanded_paths)
        else:
            self._load_directory_flat(self.explorer.current_path)
        if self.current_file_label:
            if self.current_opened_file:
                self.current_file_label.set_text(self.current_opened_file)
            else:
                self.current_file_label.set_text('—')
        stats = self.explorer.get_stats()
        status_text = f"{stats['directories']} folders, {stats['files']} files"
        if self.status_label:
            self.status_label.set_text(status_text)
        self._update_button_states()

    def _load_directory_flat(self, directory: str):
        """Load directory contents in flat mode (current directory only).
        
        Args:
            directory: Directory path to load
        """
        entries = self.explorer.get_current_entries()
        for entry in entries:
            self.store.append(None, [entry['icon_name'], entry['name'], entry['path'], entry['is_directory']])

    def _load_directory_tree(self, directory: str, parent_iter):
        """Load directory contents recursively in tree mode.
        
        Args:
            directory: Directory path to load
            parent_iter: Parent TreeIter (None for root)
        """
        try:
            items = os.listdir(directory)
            directories = []
            files = []
            for item in items:
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
            directories.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())
            for name, path in directories:
                icon = self.explorer._get_icon_name(name, True)
                dir_iter = self.store.append(parent_iter, [icon, name, path, True])
                self._load_directory_tree(path, dir_iter)
            for name, path in files:
                icon = self.explorer._get_icon_name(name, False)
                self.store.append(parent_iter, [icon, name, path, False])
        except PermissionError:
            if self.explorer.on_error:
                self.explorer.on_error(f'Permission denied: {directory}')
        except Exception as e:
            if self.explorer.on_error:
                self.explorer.on_error(f'Error reading directory: {str(e)}')

    def _update_button_states(self):
        """Update navigation button sensitivity based on API state (Controller logic)."""
        if self.back_button:
            self.back_button.set_sensitive(self.explorer.can_go_back())
        if self.forward_button:
            self.forward_button.set_sensitive(self.explorer.can_go_forward())
        if self.up_button:
            self.up_button.set_sensitive(self.explorer.can_go_up())

    def _on_path_changed(self, new_path: str):
        """Callback when path changes in API (Model).
        
        Args:
            new_path: New current path
        """
        GLib.idle_add(self._load_current_directory)

    def _on_error(self, error_message: str):
        """Callback when error occurs in API (Model).
        
        Args:
            error_message: Error description
        """
        if self.status_label:
            GLib.idle_add(self.status_label.set_text, f'Error: {error_message}')

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
        self.hierarchical_view = not self.hierarchical_view
        if self.hierarchical_view:
            pass
        else:
            pass
        self._load_current_directory()

    def _on_file_new_folder_clicked(self, button: Gtk.Button):
        """Handle New Folder button click."""
        self._show_new_folder_dialog()

    def _on_row_activated(self, tree_view: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn):
        """Handle double-click on row (UI event → API call).
        
        Args:
            tree_view: The tree view
            path: Tree path of activated row
            column: Column that was activated
        """
        iter = self.store.get_iter(path)
        is_dir = self.store.get_value(iter, 3)
        full_path = self.store.get_value(iter, 2)
        filename = self.store.get_value(iter, 1)
        if is_dir:
            self.explorer.navigate_to(full_path)
        elif full_path.endswith('.shy'):
            if self.on_file_open_requested:
                self.on_file_open_requested(full_path)
            else:
                self._open_file_from_path(full_path)
        else:
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
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            if not self.context_menu:
                return False
            result = self.tree_view.get_path_at_pos(int(event.x), int(event.y))
            if result is not None:
                path, column, cell_x, cell_y = result
                iter = self.store.get_iter(path)
                self.selected_item_name = self.store.get_value(iter, 1)
                self.selected_item_path = self.store.get_value(iter, 2)
                self.selected_item_is_dir = self.store.get_value(iter, 3)
            else:
                self.selected_item_name = os.path.basename(self.explorer.current_path)
                self.selected_item_path = self.explorer.current_path
                self.selected_item_is_dir = True
            # Use popup_at_pointer() instead of deprecated popup() for Wayland compatibility
            self.context_menu.popup_at_pointer(event)
            return True
        return False

    def _on_scroll_button_press(self, widget, event):
        """Handle button press on scrolled window for outside clicks.
        
        GTK3 version using button-press-event signal.
        
        Args:
            widget: The ScrolledWindow widget
            event: Gdk.EventButton
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            return self._on_tree_view_button_press(self.tree_view, event)
        return False

    def _on_cut_clicked(self, button):
        """Handle 'Cut' context menu button."""
        if self.selected_item_path:
            self.clipboard_path = self.selected_item_path
            self.clipboard_operation = 'cut'

    def _on_copy_clicked(self, button):
        """Handle 'Copy' context menu button."""
        if self.selected_item_path:
            self.clipboard_path = self.selected_item_path
            self.clipboard_operation = 'copy'

    def _on_paste_clicked(self, button):
        """Handle 'Paste' context menu button."""
        if not self.clipboard_path or not self.clipboard_operation:
            return
        import shutil
        source = self.clipboard_path
        source_name = os.path.basename(source)
        if self.selected_item_is_dir:
            dest_dir = self.selected_item_path
        else:
            dest_dir = self.explorer.current_path
        dest = os.path.join(dest_dir, source_name)
        counter = 1
        base_name, ext = os.path.splitext(source_name)
        while os.path.exists(dest):
            dest = os.path.join(dest_dir, f'{base_name}_{counter}{ext}')
            counter += 1
        try:
            if self.clipboard_operation == 'copy':
                if os.path.isdir(source):
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
            elif self.clipboard_operation == 'cut':
                shutil.move(source, dest)
                self.clipboard_path = None
                self.clipboard_operation = None
            self._load_current_directory()
        except Exception as e:
            pass

    def _on_duplicate_clicked(self, button):
        """Handle 'Duplicate' context menu button."""
        if not self.selected_item_path:
            return
        import shutil
        source = self.selected_item_path
        source_name = os.path.basename(source)
        base_name, ext = os.path.splitext(source_name)
        counter = 1
        dest = os.path.join(os.path.dirname(source), f'{base_name}_copy{ext}')
        while os.path.exists(dest):
            counter += 1
            dest = os.path.join(os.path.dirname(source), f'{base_name}_copy{counter}{ext}')
        try:
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            self._load_current_directory()
        except Exception as e:
            pass

    def _on_rename_clicked(self, menu_item):
        """Handle 'Rename' context menu item.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        if self.selected_item_path:
            self._show_rename_dialog()

    def _on_delete_clicked(self, menu_item):
        """Handle 'Delete' context menu item.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        if self.selected_item_path:
            self._show_delete_confirmation()
        else:
            pass  # No item selected

    def _on_refresh_clicked(self, menu_item):
        """Handle 'Refresh' context menu item.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        self._load_current_directory()

    def _on_properties_clicked(self, menu_item):
        """Handle 'Properties' context menu item.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        if self.selected_item_path:
            self._show_properties_dialog()

    def _on_context_open_clicked(self, menu_item):
        """Handle 'Open' from context menu - opens file in canvas.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        if self.selected_item_path and (not self.selected_item_is_dir):
            if not self.selected_item_path.endswith('.shy'):
                if self.explorer.on_error:
                    self.explorer.on_error('Can only open .shy Petri net files')
                return
            if self.on_file_open_requested:
                self.on_file_open_requested(self.selected_item_path)
            else:
                self._open_file_from_path(self.selected_item_path)

    def _on_context_new_file_clicked(self, menu_item):
        """Handle 'New File' from context menu - creates new .shy file inline.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        self._start_inline_edit_new_file()

    def _on_context_new_folder_clicked(self, menu_item):
        """Handle 'New Folder' from context menu - creates new folder inline.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        self._start_inline_edit_new_folder()

    def _on_context_save_clicked(self, menu_item):
        """Handle 'Save' from context menu - saves current document.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        self.save_current_document()

    def _on_context_save_as_clicked(self, menu_item):
        """Handle 'Save As' from context menu - saves with new name.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        self.save_current_document_as()

    def _start_inline_edit_new_file(self):
        """Start inline editing to create a new .shy file at cursor position."""
        if self.selected_item_is_dir:
            parent_dir = self.selected_item_path
            parent_iter = self._find_iter_for_path(self.selected_item_path)
        else:
            parent_dir = self.explorer.current_path
            parent_iter = None
        icon_name = 'text-x-generic'
        temp_name = 'new_file.shy'
        temp_path = os.path.join(parent_dir, temp_name)
        new_iter = self.store.append(parent_iter, [icon_name, temp_name, temp_path, False])
        tree_path = self.store.get_path(new_iter)
        if parent_iter:
            self.tree_view.expand_to_path(tree_path)
        self.text_renderer.set_property('editable', True)
        self.editing_iter = new_iter
        self.editing_parent_dir = parent_dir
        self.editing_is_folder = False
        column = self.tree_view.get_column(0)
        self.tree_view.set_cursor(tree_path, column, True)

    def _start_inline_edit_new_folder(self):
        """Start inline editing to create a new folder at cursor position."""
        if self.selected_item_is_dir:
            parent_dir = self.selected_item_path
            parent_iter = self._find_iter_for_path(self.selected_item_path)
        else:
            parent_dir = self.explorer.current_path
            parent_iter = None
        icon_name = 'folder'
        temp_name = 'New Folder'
        temp_path = os.path.join(parent_dir, temp_name)
        new_iter = self.store.append(parent_iter, [icon_name, temp_name, temp_path, True])
        tree_path = self.store.get_path(new_iter)
        if parent_iter:
            self.tree_view.expand_to_path(tree_path)
        self.text_renderer.set_property('editable', True)
        self.editing_iter = new_iter
        self.editing_parent_dir = parent_dir
        self.editing_is_folder = True
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
                iter_path = model.get_value(iter_node, 2)
                if iter_path == path:
                    return iter_node
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
        self.text_renderer.set_property('editable', False)
        if not new_text or new_text.strip() == '':
            if hasattr(self, 'editing_iter') and self.editing_iter:
                self.store.remove(self.editing_iter)
            return
        new_text = new_text.strip()
        if not self.editing_is_folder:
            # Ensure .shy extension is present (case-insensitive check)
            if not new_text.lower().endswith('.shy'):
                new_text += '.shy'
            elif not new_text.endswith('.shy'):
                # Handle case where user typed .SHY or .Shy - normalize to .shy
                new_text = new_text[:-4] + '.shy'
        full_path = os.path.join(self.editing_parent_dir, new_text)
        if os.path.exists(full_path):
            if self.explorer.on_error:
                self.explorer.on_error(f"'{new_text}' already exists")
            if hasattr(self, 'editing_iter') and self.editing_iter:
                self.store.remove(self.editing_iter)
            return
        try:
            if self.editing_is_folder:
                os.makedirs(full_path, exist_ok=True)
            else:
                from shypn.data.canvas.document_model import DocumentModel
                doc = DocumentModel()
                doc.save_to_file(full_path)
            self._load_current_directory()
        except Exception as e:
            if self.explorer.on_error:
                self.explorer.on_error(f'Failed to create: {e}')
            if hasattr(self, 'editing_iter') and self.editing_iter:
                self.store.remove(self.editing_iter)
        if hasattr(self, 'editing_iter'):
            delattr(self, 'editing_iter')

    def _on_cell_editing_canceled(self, renderer):
        """Handle cell editing cancellation - remove temporary row.
        
        Args:
            renderer: CellRendererText
        """
        self.text_renderer.set_property('editable', False)
        if hasattr(self, 'editing_iter') and self.editing_iter:
            self.store.remove(self.editing_iter)
            delattr(self, 'editing_iter')

    def _on_open_action(self, action, parameter):
        """Handle 'Open' context menu action."""
        if self.selected_item_path and (not self.selected_item_is_dir):
            self.set_current_file(self.selected_item_path)

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
        if self.selected_item_is_dir:
            dest_dir = self.selected_item_path
        else:
            dest_dir = self.explorer.current_path
        dest = os.path.join(dest_dir, source_name)
        counter = 1
        base_name, ext = os.path.splitext(source_name)
        while os.path.exists(dest):
            dest = os.path.join(dest_dir, f'{base_name}_{counter}{ext}')
            counter += 1
        try:
            if self.clipboard_operation == 'copy':
                if os.path.isdir(source):
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
            elif self.clipboard_operation == 'cut':
                shutil.move(source, dest)
                self.clipboard_path = None
                self.clipboard_operation = None
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
        counter = 1
        dest = os.path.join(os.path.dirname(source), f'{base_name}_copy{ext}')
        while os.path.exists(dest):
            counter += 1
            dest = os.path.join(os.path.dirname(source), f'{base_name}_copy{counter}{ext}')
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

    def _show_new_folder_dialog(self):
        """Show dialog to create a new folder."""
        window = self.tree_view.get_toplevel()
        # Ensure window is valid before use (required for Wayland)
        parent = window if isinstance(window, Gtk.Window) else None
        dialog = Gtk.Dialog(title='New Folder', transient_for=parent, modal=True)
        dialog.set_modal(True)
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.set_default_size(300, -1)
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Create', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)
        label = Gtk.Label(label='Folder name:')
        label.set_halign(Gtk.Align.START)
        content.pack_start(label, False, False, 0)
        label.show()
        entry = Gtk.Entry()
        entry.set_placeholder_text('New Folder')
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)
        entry.show()
        dialog.connect('response', lambda d, r: self._on_new_folder_response(d, r, entry))
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
        # Ensure window is valid before use (required for Wayland)
        parent = window if isinstance(window, Gtk.Window) else None
        dialog = Gtk.Dialog(title='Rename', transient_for=parent, modal=True)
        dialog.set_modal(True)
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.set_default_size(300, -1)
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Rename', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)
        label = Gtk.Label(label='New name:')
        label.set_halign(Gtk.Align.START)
        content.pack_start(label, False, False, 0)
        label.show()
        entry = Gtk.Entry()
        entry.set_text(self.selected_item_name or '')
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)
        entry.show()
        dialog.connect('response', lambda d, r: self._on_rename_response(d, r, entry))
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
        # Ensure window is valid before use (required for Wayland)
        parent = window if isinstance(window, Gtk.Window) else None
        dialog = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.YES_NO, text=f"Delete '{self.selected_item_name}'?")
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        if self.selected_item_is_dir:
            dialog.set_property('secondary-text', 'This folder will be deleted. Only empty folders can be deleted.')
        else:
            dialog.set_property('secondary-text', 'This file will be permanently deleted.')
        dialog.connect('response', self._on_delete_response)
        dialog.show()

    def _on_delete_response(self, dialog, response):
        """Handle delete confirmation response."""
        if response == Gtk.ResponseType.YES:
            if self.selected_item_path:
                success = self.explorer.delete_item(self.selected_item_path)
                if success:
                    self._load_current_directory()
                elif self.explorer.on_error:
                    self.explorer.on_error(f"Failed to delete '{self.selected_item_name}'")
        dialog.close()

    def _show_properties_dialog(self):
        """Show properties dialog for selected item."""
        info = self.explorer.get_file_info(self.selected_item_path)
        if not info:
            return
        window = self.tree_view.get_toplevel()
        # Ensure window is valid before use (required for Wayland)
        parent = window if isinstance(window, Gtk.Window) else None
        dialog = Gtk.Dialog(title=f"Properties - {info['name']}", transient_for=parent, modal=True)
        dialog.set_modal(True)
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.set_default_size(400, -1)
        dialog.add_button('Close', Gtk.ResponseType.CLOSE)
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        content.pack_start(grid, True, True, 0)
        row = 0

        def add_property(label_text, value_text):
            nonlocal row
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class('dim-label')
            grid.attach(label, 0, row, 1, 1)
            value = Gtk.Label(label=value_text)
            value.set_halign(Gtk.Align.START)
            value.set_selectable(True)
            grid.attach(value, 1, row, 1, 1)
            row += 1
        add_property('Name:', info['name'])
        add_property('Type:', 'Folder' if info['is_directory'] else 'File')
        add_property('Location:', os.path.dirname(info['path']))
        if not info['is_directory']:
            add_property('Size:', info['size_formatted'])
        elif 'item_count' in info:
            add_property('Items:', str(info['item_count']))
        add_property('Modified:', info['modified_formatted'])
        if 'created_formatted' in info:
            add_property('Created:', info['created_formatted'])
        add_property('Permissions:', info['permissions'])
        access = []
        if info['readable']:
            access.append('Read')
        if info['writable']:
            access.append('Write')
        if info['executable']:
            access.append('Execute')
        add_property('Access:', ', '.join(access) if access else 'None')
        dialog.connect('response', lambda d, r: d.close())
        dialog.show_all()

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

    def save_current_document(self):
        """Save the current document using per-document state.
        
        PHASE 1 REFACTORING: Now uses manager's filepath and is_dirty state
        instead of global persistency state. This fixes multi-document issues.
        
        Behavior:
        - If manager has no filepath (new/unsaved): Show save dialog
        - If manager.is_default_filename() (imported/default): Show save dialog
        - Otherwise: Save directly to manager's filepath
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                return
            if not hasattr(self, 'persistency') or self.persistency is None:
                return
            
            drawing_area = self.canvas_loader.get_current_document()
            if drawing_area is None:
                return
            
            manager = self.canvas_loader.get_canvas_manager(drawing_area)
            if manager is None:
                return
            
            # Convert canvas state to document model
            document = manager.to_document_model()
            
            # Determine if we need to show file chooser
            needs_chooser = not manager.has_filepath() or manager.is_default_filename()
            
            if needs_chooser:
                # Show save dialog (new document or imported)
                
                # Set suggested filename from manager
                if manager.filename and manager.filename != "default":
                    self.persistency.suggested_filename = manager.filename
                
                # Show file chooser
                filepath = self.persistency._show_save_dialog()
                if not filepath:
                    return  # User cancelled
                
                # Save to chosen file
                document.save_to_file(filepath)
                
                # Update manager state
                manager.set_filepath(filepath)
                manager.mark_clean()
                manager.mark_as_saved()  # Clear imported flag
                
                # Update UI
                import os
                filename = os.path.basename(filepath)
                self.canvas_loader.update_current_tab_label(filename, is_modified=False)
                self.set_current_file(filepath)
                self._load_current_directory()  # Refresh file tree
                
            else:
                # Direct save to existing file
                filepath = manager.get_filepath()
                
                document.save_to_file(filepath)
                
                # Update manager state
                manager.mark_clean()
                
                # Update UI
                import os
                filename = os.path.basename(filepath)
                self.canvas_loader.update_current_tab_label(filename, is_modified=False)
                
                
        except Exception as e:
            print(f"[FileExplorer] save_current_document ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    def save_current_document_as(self):
        """Save the current document with a new name (Save As).
        
        PHASE 1 REFACTORING: Now uses manager's filepath and updates it after save.
        Always shows file chooser regardless of current state.
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                return
            if not hasattr(self, 'persistency') or self.persistency is None:
                return
            
            drawing_area = self.canvas_loader.get_current_document()
            if drawing_area is None:
                return
            
            manager = self.canvas_loader.get_canvas_manager(drawing_area)
            if manager is None:
                return
            
            # Convert canvas state to document model
            document = manager.to_document_model()
            
            # Set suggested filename from manager
            if manager.filename and manager.filename != "default":
                self.persistency.suggested_filename = manager.filename
            
            # Always show file chooser for Save As
            filepath = self.persistency._show_save_dialog()
            if not filepath:
                return  # User cancelled
            
            # Save to chosen file
            document.save_to_file(filepath)
            
            # Update manager state
            manager.set_filepath(filepath)
            manager.mark_clean()
            manager.mark_as_saved()  # Clear imported flag
            
            # Update UI - CRITICAL: Update tab label with new filename
            import os
            filename = os.path.basename(filepath)
            self.canvas_loader.update_current_tab_label(filename, is_modified=False)
            self.set_current_file(filepath)
            self._load_current_directory()  # Refresh file tree
            
            
        except Exception as e:
            print(f"[FileExplorer] save_current_document_as ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    def open_document(self):
        """Open a document from file using the persistency manager.
        
        Creates a new tab with the loaded document and sets the manager's filename
        correctly so is_default_filename() returns False.
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                return
            if not hasattr(self, 'persistency') or self.persistency is None:
                return
            document, filepath = self.persistency.load_document()
            if document and filepath:
                self._load_document_into_canvas(document, filepath)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _open_file_from_path(self, filepath: str):
        """Open a specific file from path into canvas.
        
        Used by double-click and context menu Open operations.
        
        Args:
            filepath: Full path to .shy file to open
        """
        if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
            return
        if not hasattr(self, 'persistency') or self.persistency is None:
            return
        try:
            from shypn.data.canvas.document_model import DocumentModel
            document = DocumentModel.load_from_file(filepath)
            if document:
                self._load_document_into_canvas(document, filepath)
        except Exception as e:
            import traceback
            traceback.print_exc()
            if self.explorer.on_error:
                self.explorer.on_error(f'Failed to open file: {e}')

    def _load_document_into_canvas(self, document, filepath: str):
        """Load a document model into the canvas.
        
        Helper method shared by open_document() and _open_file_from_path().
        
        Args:
            document: DocumentModel instance
            filepath: Full path to the file
        """
        if not document or not filepath:
            return
        import os
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        
        
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        if manager:
            # ===== UNIFIED OBJECT LOADING =====
            # Use load_objects() for consistent, unified initialization path
            # This replaces direct assignment + manual notification loop
            # Benefits: Single code path, automatic notifications, proper references
            manager.load_objects(
                places=document.places,
                transitions=document.transitions,
                arcs=document.arcs
            )
            
            # CRITICAL: Set on_changed callback on all loaded objects
            # This is required for proper object state management and dirty tracking
            manager.document_controller.set_change_callback(manager._on_object_changed)
            
            # Restore view state (zoom, pan, and rotation) if available
            # NOTE: We still fit_to_page afterwards to ensure objects are visible
            if hasattr(document, 'view_state') and document.view_state:
                manager.zoom = document.view_state.get('zoom', 1.0)
                manager.pan_x = document.view_state.get('pan_x', 0.0)
                manager.pan_y = document.view_state.get('pan_y', 0.0)
                manager._initial_pan_set = True  # Mark as set to prevent auto-centering
                
                # Restore transformations (rotation) if available
                if 'transformations' in document.view_state:
                    manager.transformation_manager.from_dict(document.view_state['transformations'])
            
            # ALWAYS fit loaded content to page to ensure visibility
            # This centers objects in viewport regardless of saved view state
            # Use deferred=True to wait for viewport dimensions on first draw
            # Use 30% horizontal offset to shift right (accounting for right panel)
            # Use +10% vertical offset to shift UP in Cartesian space (increase Y)
            manager.fit_to_page(padding_percent=15, deferred=True, horizontal_offset_percent=30, vertical_offset_percent=10)
            
            # PHASE 1: Set per-document file state
            # Initialize manager's filepath and mark as clean (just loaded)
            manager.set_filepath(filepath)
            manager.mark_clean()  # Just loaded, no unsaved changes
            
            # Legacy: Also update global persistency for backward compatibility
            if hasattr(self, 'persistency') and self.persistency:
                self.persistency.set_filepath(filepath)
                self.persistency.mark_clean()
            
            # Update tab label to show the actual filename
            self.canvas_loader.update_current_tab_label(filename, is_modified=False)
            self.canvas_loader.update_current_tab_label(filename, is_modified=False)
            
            drawing_area.queue_draw()

    def new_document(self):
        """Create a new document.
        
        Checks for unsaved changes and creates a new tab with "default" filename.
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                return
            if not hasattr(self, 'persistency') or self.persistency is None:
                return
            if not self.persistency.check_unsaved_changes():
                return
            if self.persistency.new_document():
                self.canvas_loader.add_document()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _on_file_saved_callback(self, filepath: str):
        """Called by NetObjPersistency when a file is saved.
        
        Updates the current file display and refreshes the file explorer tree
        to show the newly saved file. Also updates the tab label.
        
        Args:
            filepath: Full path to the saved file
        """
        self.set_current_file(filepath)
        self._load_current_directory()
        
        # Update tab label to show the saved filename
        if hasattr(self, 'canvas_loader') and self.canvas_loader:
            import os
            filename = os.path.basename(filepath)
            self.canvas_loader.update_current_tab_label(filename, is_modified=False)

    def _on_file_loaded_callback(self, filepath: str, document):
        """Called by NetObjPersistency when a file is loaded.
        
        Loads the document into the canvas and updates the current file display.
        
        Args:
            filepath: Full path to the loaded file
            document: The loaded DocumentModel instance
        """
        
        # Load the document into the canvas
        self._load_document_into_canvas(document, filepath)
        
        # Update the current file display
        self.set_current_file(filepath)

    def _on_dirty_changed_callback(self, is_dirty: bool):
        """Called by NetObjPersistency when dirty state changes.
        
        Updates the current file display to show dirty state indicator (asterisk).
        Also updates the tab label to show the asterisk.
        
        Args:
            is_dirty: True if document has unsaved changes, False otherwise
        """
        if not self.current_opened_file:
            return
        if self.current_file_label:
            display = self.current_opened_file
            if is_dirty and (not display.endswith(' *')):
                display = display + ' *'
            elif not is_dirty and display.endswith(' *'):
                display = display[:-2]
            self.current_file_label.set_text(display)
        
        # Update tab label to show/hide asterisk
        if hasattr(self, 'canvas_loader') and self.canvas_loader:
            if hasattr(self, 'persistency') and self.persistency:
                import os
                filename = os.path.basename(self.persistency.current_filepath) if self.persistency.current_filepath else 'default.shy'
                self.canvas_loader.update_current_tab_label(filename, is_modified=is_dirty)

    def set_current_file(self, filename_or_path: Optional[str]):
        """Set the currently opened file to display in toolbar.
        
        Shows the file with its relative path from the workspace root.
        For example: 'workspace/examples/simple.shy' or 'workspace/projects/myproject/network.shy'
        
        This should be called by the main application when a file is opened
        in the canvas/editor to show which file is being worked on.
        
        Args:
            filename_or_path: Name or full path of the opened file, or None to clear
        """
        if not filename_or_path:
            self.current_opened_file = None
            if self.current_file_label:
                self.current_file_label.set_text('—')
            return
        if os.path.isabs(filename_or_path):
            try:
                relative_path = os.path.relpath(filename_or_path, self.explorer.root_boundary)
                display_text = relative_path
            except ValueError:
                display_text = os.path.basename(filename_or_path)
        else:
            display_text = filename_or_path
        self.current_opened_file = display_text
        if self.current_file_label:
            self.current_file_label.set_text(display_text)