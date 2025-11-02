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
        # No default file - will be set when user selects one
        self.current_opened_file: Optional[str] = None
        self.hierarchical_view = True
        self.selected_item_path: Optional[str] = None
        self.selected_item_name: Optional[str] = None
        self.selected_item_is_dir: bool = False
        self.clipboard_path: Optional[str] = None
        self.clipboard_operation: Optional[str] = None
        self.on_file_open_requested: Optional[Callable[[str], None]] = None
        # WAYLAND FIX: Store parent window reference for dialogs
        self.parent_window: Optional[Gtk.Window] = None
        # Project reference for saving imported models to project/models/
        self.project = None
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
        # TreeStore columns: icon, display_name, full_path, is_directory, is_project, weight, background
        self.store = Gtk.TreeStore(str, str, str, bool, bool, int, str)
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
        # Add styling attributes for projects (bold text, darker background)
        name_column.add_attribute(text_renderer, 'weight', 5)  # Font weight
        name_column.add_attribute(text_renderer, 'background', 6)  # Background color
        self.text_renderer = text_renderer
        self.tree_view.append_column(name_column)
        
        # Enable drag and drop for moving files
        self._setup_drag_and_drop()
    
    def _setup_drag_and_drop(self):
        """Enable drag-and-drop support for moving files/folders within the tree."""
        # Define the drag-and-drop target (text/uri-list is standard for file paths)
        targets = [Gtk.TargetEntry.new('text/plain', Gtk.TargetFlags.SAME_WIDGET, 0)]
        
        # Enable drag source (allows dragging from tree)
        self.tree_view.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,  # Left mouse button
            targets,
            Gdk.DragAction.MOVE
        )
        
        # Enable drag destination (allows dropping onto tree)
        self.tree_view.enable_model_drag_dest(
            targets,
            Gdk.DragAction.MOVE
        )
        
        # Connect drag-and-drop signals
        self.tree_view.connect('drag-data-get', self._on_drag_data_get)
        self.tree_view.connect('drag-data-received', self._on_drag_data_received)
        self.tree_view.connect('drag-drop', self._on_drag_drop)
    
    def _on_drag_data_get(self, widget, drag_context, data, info, time):
        """Handle drag start - store the source file path."""
        selection = self.tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            # Get the file path from the selected row
            source_path = model.get_value(tree_iter, 2)  # Column 2 is full_path
            # Send the path as drag data
            data.set_text(source_path, -1)
    
    def _on_drag_drop(self, widget, drag_context, x, y, time):
        """Handle drag drop event."""
        # Get the drop position in the tree
        drop_info = self.tree_view.get_dest_row_at_pos(x, y)
        
        if drop_info:
            path, position = drop_info
            # Request the drag data
            target = drag_context.list_targets()[0]
            widget.drag_get_data(drag_context, target, time)
            return True
        
        return False
    
    def _on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        """Handle drop completion - move the file to the target location."""
        import shutil
        
        # Get source path from drag data
        source_path = data.get_text()
        if not source_path or not os.path.exists(source_path):
            pass
            drag_context.finish(False, False, time)
            return
        
        # Get drop target from tree position
        drop_info = self.tree_view.get_dest_row_at_pos(x, y)
        if not drop_info:
            pass
            drag_context.finish(False, False, time)
            return
        
        path, position = drop_info
        model = self.tree_view.get_model()
        tree_iter = model.get_iter(path)
        
        # Get target path and check if it's a directory
        target_path = model.get_value(tree_iter, 2)  # Column 2 is full_path
        is_directory = model.get_value(tree_iter, 3)  # Column 3 is is_directory
        
        # Determine the destination directory
        if is_directory:
            dest_dir = target_path
        else:
            # If dropping on a file, use its parent directory
            dest_dir = os.path.dirname(target_path)
        
        # Build destination path
        source_name = os.path.basename(source_path)
        dest_path = os.path.join(dest_dir, source_name)
        
        # Prevent moving to itself or to its own subdirectory
        if source_path == dest_path:
            pass
            drag_context.finish(False, False, time)
            return
        
        if os.path.isdir(source_path) and dest_dir.startswith(source_path):
            pass
            drag_context.finish(False, False, time)
            return
        
        # Check if destination already exists
        if os.path.exists(dest_path):
            # Show confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="File Already Exists"
            )
            dialog.format_secondary_text(
                f"A file named '{source_name}' already exists in the destination.\n"
                f"Do you want to replace it?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response != Gtk.ResponseType.YES:
                drag_context.finish(False, False, time)
                return
        
        # Perform the move operation
        try:
            pass
            shutil.move(source_path, dest_path)
            
            # Refresh the file tree to show the changes
            self.refresh()
            
            # Mark drag as successful
            drag_context.finish(True, True, time)
            
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Move Failed"
            )
            dialog.format_secondary_text(f"Could not move the file:\n{str(e)}")
            dialog.run()
            dialog.destroy()
            
            drag_context.finish(False, False, time)

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
        - Clipboard: Cut, Copy, Paste
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
        
        # Store references to menu items that need dynamic enable/disable
        self.menu_items_refs = {}
        
        menu_items = [('Open', self._on_context_open_clicked), ('New File', self._on_context_new_file_clicked), ('New Folder', self._on_context_new_folder_clicked), ('---', None), ('Cut', self._on_cut_clicked), ('Copy', self._on_copy_clicked), ('Paste', self._on_paste_clicked), ('---', None), ('Rename', self._on_rename_clicked), ('Delete', self._on_delete_clicked), ('---', None), ('Refresh', self._on_refresh_clicked), ('Properties', self._on_properties_clicked)]
        for label, callback in menu_items:
            if label == '---':
                separator = Gtk.SeparatorMenuItem()
                self.context_menu.append(separator)
            else:
                menu_item = Gtk.MenuItem(label=label)
                if callback:
                    menu_item.connect('activate', callback)
                self.context_menu.append(menu_item)
                # Store references for items that need dynamic state
                if label in ['Cut', 'Copy', 'Paste', 'Rename', 'Delete', 'Open']:
                    self.menu_items_refs[label] = menu_item
        
        # Connect to menu show event to update item states
        self.context_menu.connect('show', self._on_context_menu_show)
        self.context_menu.show_all()
    
    def _on_context_menu_show(self, menu):
        """Update context menu item states when menu is shown.
        
        Args:
            menu: The Gtk.Menu being shown
        """
        # Enable/disable Paste based on clipboard state
        if 'Paste' in self.menu_items_refs:
            has_clipboard = bool(self.clipboard_path and self.clipboard_operation)
            self.menu_items_refs['Paste'].set_sensitive(has_clipboard)
        
        # Enable/disable Cut, Copy, Rename, Delete based on selection
        has_selection = bool(self.selected_item_path)
        for item_name in ['Cut', 'Copy', 'Rename', 'Delete']:
            if item_name in self.menu_items_refs:
                self.menu_items_refs[item_name].set_sensitive(has_selection)
        
        # Enable/disable Open based on whether selection is a file
        if 'Open' in self.menu_items_refs:
            can_open = has_selection and not self.selected_item_is_dir
            self.menu_items_refs['Open'].set_sensitive(can_open)

    def _connect_signals(self):
        """Connect widget signals to controller methods.
        
        This is the Controller's main job - connecting UI events to business logic.
        """
        if self.new_button:
            self.new_button.connect('clicked', lambda btn: self._start_inline_edit_new_file())
        if self.open_button:
            self.open_button.connect('clicked', lambda btn: self.open_document())
        if self.save_button:
            self.save_button.connect('clicked', lambda btn: self.save_current_document())
        if self.save_as_button:
            self.save_as_button.connect('clicked', lambda btn: self.save_current_document_as())
        if self.new_folder_button:
            self.new_folder_button.connect('clicked', lambda btn: self._start_inline_edit_new_folder())
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
        
        # Connect to selection changes to update current file display
        selection = self.tree_view.get_selection()
        selection.connect('changed', self._on_tree_selection_changed)

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
        
        # Block selection handler during load to prevent auto-selection
        selection = self.tree_view.get_selection()
        selection.handler_block_by_func(self._on_tree_selection_changed)
        
        self.store.clear()
        if self.hierarchical_view:
            self._load_directory_tree(self.explorer.current_path, None)
            # Restore expanded state after loading
            self._restore_expanded_paths(expanded_paths)
        else:
            self._load_directory_flat(self.explorer.current_path)
        
        # Clear any auto-selection that GTK might have made
        selection.unselect_all()
        
        # Unblock selection handler
        selection.handler_unblock_by_func(self._on_tree_selection_changed)
        
        # Don't modify the current file entry during refresh
        # It should only change when user selects a different file
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
            is_project, display_name = self._check_if_project(entry['path'], entry['is_directory'], entry['name'])
            weight = 700 if is_project else 400  # Bold for projects
            bg_color = '#e8e8e8' if is_project else None  # Darker background for projects
            self.store.append(None, [
                entry['icon_name'], 
                display_name,  # Use display name (alias)
                entry['path'], 
                entry['is_directory'],
                is_project,
                weight,
                bg_color
            ])
    
    def _check_if_project(self, path: str, is_directory: bool, name: str):
        """Check if a directory is a SHYpn project and get its display name.
        
        Args:
            path: Full path to the item
            is_directory: Whether the item is a directory
            name: Original folder/file name
            
        Returns:
            Tuple of (is_project: bool, display_name: str)
        """
        if not is_directory:
            return False, name
        
        # Check if directory contains a .project.shy file
        project_file = os.path.join(path, '.project.shy')
        if not os.path.exists(project_file):
            return False, name
        
        # Try to read project name from .project.shy file
        try:
            from shypn.data.project_models import Project
            project = Project.load(project_file)
            if project and project.name:
                return True, project.name  # Use project's display name
        except:
            pass
        
        # Fallback: it's a project but couldn't read name, use folder name
        return True, name

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
                is_project, display_name = self._check_if_project(path, True, name)
                weight = 700 if is_project else 400  # Bold for projects
                bg_color = '#e8e8e8' if is_project else None  # Darker background for projects
                dir_iter = self.store.append(parent_iter, [icon, display_name, path, True, is_project, weight, bg_color])
                self._load_directory_tree(path, dir_iter)
            for name, path in files:
                icon = self.explorer._get_icon_name(name, False)
                self.store.append(parent_iter, [icon, name, path, False, False, 400, None])
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
        """Handle home button click - navigate to workspace root and collapse tree."""
        # Navigate to workspace root (root_boundary)
        if hasattr(self.explorer, 'root_boundary') and self.explorer.root_boundary:
            self.explorer.navigate_to(self.explorer.root_boundary)
            # Collapse all expanded folders when going home
            self.tree_view.collapse_all()
        else:
            self.explorer.go_home()
            self.tree_view.collapse_all()

    def _on_refresh_clicked(self, button: Gtk.Button):
        """Handle refresh button click - reload current directory."""
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
        """Handle button press on tree view to show context menu and expand folders.
        
        GTK3 version using button-press-event signal.
        
        Args:
            widget: The TreeView widget
            event: Gdk.EventButton
            
        Returns:
            True if event was handled, False otherwise
        """
        # Handle right-click for context menu
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
        
        # Handle left-click on folders to expand/collapse
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            result = self.tree_view.get_path_at_pos(int(event.x), int(event.y))
            if result is not None:
                path, column, cell_x, cell_y = result
                iter = self.store.get_iter(path)
                is_dir = self.store.get_value(iter, 3)
                full_path = self.store.get_value(iter, 2)
                
                # Update selection first (for both files and folders)
                self.selected_item_path = full_path
                self.selected_item_name = self.store.get_value(iter, 1)
                self.selected_item_is_dir = is_dir
                
                # Only expand/collapse if clicking on a directory AND not on the expander
                # Check if click is on the expander arrow (very left side of the row)
                if is_dir:
                    # Get the cell area to determine if click was on expander
                    cell_area = self.tree_view.get_cell_area(path, column)
                    # Expander is typically in the first ~20 pixels
                    depth = len(path.get_indices()) - 1  # Tree depth
                    expander_size = 20
                    expander_indent = depth * expander_size
                    click_on_expander = cell_x < (expander_indent + expander_size)
                    
                    # Only toggle if NOT clicking on expander (to avoid double-toggle)
                    if not click_on_expander:
                        if self.tree_view.row_expanded(path):
                            self.tree_view.collapse_row(path)
                        else:
                            self.tree_view.expand_row(path, False)
                else:
                    # For files, update current file display
                    self.set_current_file(full_path)
        
        return False

    def _on_tree_selection_changed(self, selection):
        """Handle tree view selection changes - update current file display.
        
        Args:
            selection: Gtk.TreeSelection object
        """
        model, tree_iter = selection.get_selected()
        if tree_iter is not None:
            # Get the selected item details
            full_path = model.get_value(tree_iter, 2)  # Column 2 is the path
            is_dir = model.get_value(tree_iter, 3)     # Column 3 is is_directory
            
            # Update selected_item for context menu
            self.selected_item_path = full_path
            self.selected_item_name = model.get_value(tree_iter, 1)
            self.selected_item_is_dir = is_dir
            
            # Update current file display if it's a file (not a directory)
            if not is_dir:
                self.set_current_file(full_path)

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
        """Handle 'Rename' context menu item - inline editing.
        
        Args:
            menu_item: The Gtk.MenuItem that was activated (from 'activate' signal)
        """
        if self.selected_item_path:
            pass
            self._start_inline_edit_rename()
        else:
            pass

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
        # TreeStore columns: icon, display_name, full_path, is_directory, is_project, weight, background
        new_iter = self.store.append(parent_iter, [icon_name, temp_name, temp_path, False, False, 400, None])
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
        # TreeStore columns: icon, display_name, full_path, is_directory, is_project, weight, background
        new_iter = self.store.append(parent_iter, [icon_name, temp_name, temp_path, True, False, 400, None])
        tree_path = self.store.get_path(new_iter)
        if parent_iter:
            self.tree_view.expand_to_path(tree_path)
        self.text_renderer.set_property('editable', True)
        self.editing_iter = new_iter
        self.editing_parent_dir = parent_dir
        self.editing_is_folder = True
        column = self.tree_view.get_column(0)
        self.tree_view.set_cursor(tree_path, column, True)

    def _start_inline_edit_rename(self):
        """Start inline editing to rename selected file/folder."""
        if not self.selected_item_path:
            return
        
        # Find the iter for the selected item
        iter_to_edit = self._find_iter_for_path(self.selected_item_path)
        if not iter_to_edit:
            return
        
        # Store original path and name for rename operation
        self.text_renderer.set_property('editable', True)
        self.editing_iter = iter_to_edit
        self.editing_parent_dir = os.path.dirname(self.selected_item_path)
        self.editing_is_folder = self.selected_item_is_dir
        self.editing_old_path = self.selected_item_path  # Store for rename
        self.editing_old_name = os.path.basename(self.selected_item_path)
        self.is_rename_operation = True  # Flag to distinguish rename from new file/folder
        
        # Start editing the cell
        tree_path = self.store.get_path(iter_to_edit)
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
        """Handle cell editing completion - create file/folder or rename.
        
        Args:
            renderer: CellRendererText
            path: Tree path (string)
            new_text: New text entered by user
        """
        self.text_renderer.set_property('editable', False)
        
        # Check if this is a rename operation
        is_rename = getattr(self, 'is_rename_operation', False)
        
        if not new_text or new_text.strip() == '':
            if hasattr(self, 'editing_iter') and self.editing_iter and not is_rename:
                self.store.remove(self.editing_iter)
            self._cleanup_editing_state()
            return
        
        new_text = new_text.strip()
        
        # For rename, check if name actually changed
        if is_rename:
            old_name = getattr(self, 'editing_old_name', '')
            if new_text == old_name:
                self._cleanup_editing_state()
                return
        
        if not self.editing_is_folder:
            # Ensure .shy extension is present (case-insensitive check)
            if not new_text.lower().endswith('.shy'):
                new_text += '.shy'
            elif not new_text.endswith('.shy'):
                # Handle case where user typed .SHY or .Shy - normalize to .shy
                new_text = new_text[:-4] + '.shy'
        
        full_path = os.path.join(self.editing_parent_dir, new_text)
        
        # Check if destination already exists (but not if it's the same file during rename)
        if os.path.exists(full_path):
            if not is_rename or full_path != getattr(self, 'editing_old_path', None):
                if self.explorer.on_error:
                    self.explorer.on_error(f"'{new_text}' already exists")
                if hasattr(self, 'editing_iter') and self.editing_iter and not is_rename:
                    self.store.remove(self.editing_iter)
                self._cleanup_editing_state()
                return
        
        try:
            if is_rename:
                # Rename operation
                old_path = getattr(self, 'editing_old_path', None)
                if old_path and old_path != full_path:
                    os.rename(old_path, full_path)
                    # Update current file if we renamed it
                    if self.current_opened_file == old_path:
                        self.current_opened_file = full_path
            else:
                # Create new file/folder
                if self.editing_is_folder:
                    os.makedirs(full_path, exist_ok=True)
                else:
                    from shypn.data.canvas.document_model import DocumentModel
                    doc = DocumentModel()
                    doc.save_to_file(full_path)
            
            self._load_current_directory()
        except Exception as e:
            if self.explorer.on_error:
                self.explorer.on_error(f'Failed to {"rename" if is_rename else "create"}: {e}')
            if hasattr(self, 'editing_iter') and self.editing_iter and not is_rename:
                self.store.remove(self.editing_iter)
        
        self._cleanup_editing_state()
    
    def _cleanup_editing_state(self):
        """Clean up all editing-related state variables."""
        if hasattr(self, 'editing_iter'):
            delattr(self, 'editing_iter')
        if hasattr(self, 'is_rename_operation'):
            delattr(self, 'is_rename_operation')
        if hasattr(self, 'editing_old_path'):
            delattr(self, 'editing_old_path')
        if hasattr(self, 'editing_old_name'):
            delattr(self, 'editing_old_name')

    def _on_cell_editing_canceled(self, renderer):
        """Handle cell editing cancellation - remove temporary row or revert changes.
        
        Args:
            renderer: CellRendererText
        """
        self.text_renderer.set_property('editable', False)
        
        # Only remove the iter if it's a new file/folder (not a rename)
        is_rename = getattr(self, 'is_rename_operation', False)
        if hasattr(self, 'editing_iter') and self.editing_iter and not is_rename:
            self.store.remove(self.editing_iter)
        
        self._cleanup_editing_state()

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
        """Handle 'Rename' context menu action - inline editing."""
        if self.selected_item_path:
            self._start_inline_edit_rename()

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
        # WAYLAND FIX: Use stored parent_window instead of get_toplevel()
        # get_toplevel() may return the wrong window when panel is reparented
        parent = self.parent_window if self.parent_window else None
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
        # WAYLAND FIX: Use stored parent_window instead of get_toplevel()
        parent = self.parent_window if self.parent_window else None
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
        # WAYLAND FIX: Use stored parent_window instead of get_toplevel()
        parent = self.parent_window if self.parent_window else None
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
        # WAYLAND FIX: Use stored parent_window instead of get_toplevel()
        parent = self.parent_window if self.parent_window else None
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

    def set_parent_window(self, parent_window: Optional[Gtk.Window]):
        """Set parent window for dialogs (WAYLAND FIX).
        
        This should be called when the panel attaches/floats to ensure
        all dialogs (New Folder, Rename, Delete, Properties) use the
        correct parent window.
        
        Args:
            parent_window: The main window or floating panel window
        """
        self.parent_window = parent_window
        
        # CRITICAL FIX: Also update persistency manager's parent window
        # This ensures FileChooser dialogs (Open/Save) use correct parent
        if hasattr(self, 'persistency') and self.persistency:
            self.persistency.parent_window = parent_window
    
    def set_project(self, project):
        """Set the current project for saving imported models to project/models/.
        
        Args:
            project: Project instance or None
        """
        self.project = project

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
        
        Inline save behavior (no dialogs):
        - If manager has no filepath (new/unsaved): Auto-generate filename in workspace
        - If manager.is_default_filename() (imported/default): Auto-save to workspace
        - Otherwise: Save directly to manager's filepath
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                pass
                return
            
            drawing_area = self.canvas_loader.get_current_document()
            if drawing_area is None:
                pass
                return
            
            manager = self.canvas_loader.get_canvas_manager(drawing_area)
            if manager is None:
                pass
                return
            
            
            # Convert canvas state to document model
            document = manager.to_document_model()
            
            # Determine if we need to auto-generate a filepath
            needs_new_filepath = not manager.has_filepath() or manager.is_default_filename()
            
            
            if needs_new_filepath:
                # Open file chooser dialog for default/imported files
                
                # Determine initial directory: project/models/ if project is open, otherwise workspace
                if self.project and hasattr(self.project, 'base_path'):
                    initial_dir = os.path.join(self.project.base_path, 'models')
                    os.makedirs(initial_dir, exist_ok=True)
                else:
                    initial_dir = self.explorer.current_path
                
                # Determine default filename
                if manager.filename and manager.filename != "default":
                    default_filename = manager.filename
                    if not default_filename.endswith('.shy'):
                        default_filename += '.shy'
                else:
                    # Use 'default.shy' as the default filename
                    default_filename = "default.shy"
                
                # Create file chooser dialog
                dialog = Gtk.FileChooserDialog(
                    title="Save File",
                    parent=self.parent_window,
                    action=Gtk.FileChooserAction.SAVE,
                    buttons=(
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK
                    )
                )
                
                # Set initial directory and filename
                dialog.set_current_folder(initial_dir)
                dialog.set_current_name(default_filename)
                
                # Add file filters
                filter_shy = Gtk.FileFilter()
                filter_shy.set_name("SHYpn Files (*.shy)")
                filter_shy.add_pattern("*.shy")
                dialog.add_filter(filter_shy)
                
                filter_all = Gtk.FileFilter()
                filter_all.set_name("All Files")
                filter_all.add_pattern("*")
                dialog.add_filter(filter_all)
                
                # Set overwrite confirmation
                dialog.set_do_overwrite_confirmation(True)
                
                # Run dialog
                response = dialog.run()
                filepath = None
                
                if response == Gtk.ResponseType.OK:
                    filepath = dialog.get_filename()
                    
                    # Ensure .shy extension
                    if not filepath.endswith('.shy'):
                        filepath += '.shy'
                    
                    # Save to selected file
                    document.save_to_file(filepath)
                    
                    
                    # Update manager state
                    manager.set_filepath(filepath)
                    manager.mark_clean()
                    manager.mark_as_saved()  # Clear imported flag
                    
                    # Update UI
                    filename = os.path.basename(filepath)
                    self.canvas_loader.update_current_tab_label(filename, is_modified=False)
                    self.set_current_file(filepath)
                    self._load_current_directory()  # Refresh file tree
                else:
                    pass
                
                # Close dialog
                dialog.destroy()
                
            else:
                # Direct save to existing file
                filepath = manager.get_filepath()
                
                
                document.save_to_file(filepath)
                
                # Update manager state
                manager.mark_clean()
                
                # Update UI
                filename = os.path.basename(filepath)
                self.canvas_loader.update_current_tab_label(filename, is_modified=False)
                
                
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()

    def save_current_document_as(self):
        """Save the current document with a new name using a file chooser dialog.
        
        Opens a file chooser dialog with 'default.shy' as the default filename.
        User can choose location and filename interactively.
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                pass
                return
            
            drawing_area = self.canvas_loader.get_current_document()
            if drawing_area is None:
                pass
                return
            
            manager = self.canvas_loader.get_canvas_manager(drawing_area)
            if manager is None:
                pass
                return
            
            # Convert canvas state to document model
            document = manager.to_document_model()
            
            # Determine initial directory: project/models/ if project is open, otherwise workspace
            if self.project:
                pass
            
            if self.project and hasattr(self.project, 'base_path'):
                # Start in project/models/ directory
                initial_dir = os.path.join(self.project.base_path, 'models')
                os.makedirs(initial_dir, exist_ok=True)
            else:
                # Start in workspace directory
                initial_dir = self.explorer.current_path
            
            # Determine default filename
            if manager.filename and manager.filename != "default":
                default_filename = manager.filename
                if not default_filename.endswith('.shy'):
                    default_filename += '.shy'
            else:
                # Use 'default.shy' as the default filename
                default_filename = "default.shy"
            
            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Save As",
                parent=self.parent_window,
                action=Gtk.FileChooserAction.SAVE,
                buttons=(
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE, Gtk.ResponseType.OK
                )
            )
            
            # Set initial directory
            dialog.set_current_folder(initial_dir)
            
            # Set default filename
            dialog.set_current_name(default_filename)
            
            # Add file filter for .shy files
            filter_shy = Gtk.FileFilter()
            filter_shy.set_name("SHYpn Files (*.shy)")
            filter_shy.add_pattern("*.shy")
            dialog.add_filter(filter_shy)
            
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All Files")
            filter_all.add_pattern("*")
            dialog.add_filter(filter_all)
            
            # Set overwrite confirmation
            dialog.set_do_overwrite_confirmation(True)
            
            # Run dialog
            response = dialog.run()
            filepath = None
            
            if response == Gtk.ResponseType.OK:
                filepath = dialog.get_filename()
                
                # Ensure .shy extension
                if not filepath.endswith('.shy'):
                    filepath += '.shy'
                
                # Save to selected file
                document.save_to_file(filepath)
                
                
                # Update manager state
                manager.set_filepath(filepath)
                manager.mark_clean()
                manager.mark_as_saved()  # Clear imported flag
                
                # Update UI - CRITICAL: Update tab label with new filename
                filename = os.path.basename(filepath)
                self.canvas_loader.update_current_tab_label(filename, is_modified=False)
                self.set_current_file(filepath)
                self._load_current_directory()  # Refresh file tree
            
            # Close dialog
            dialog.destroy()
            
            
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()

    def open_document(self):
        """Open a document via FileChooserDialog.
        
        Shows a file chooser dialog to let the user select a .shy file to open.
        If invoked via Ctrl+O or File > Open menu, opens a dialog.
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                return
            if not hasattr(self, 'parent_window') or self.parent_window is None:
                print("[FILES] ERROR: No parent window set for file chooser dialog")
                return
            
            # Create FileChooserDialog for opening files
            dialog = Gtk.FileChooserDialog(
                title="Open File",
                parent=self.parent_window,
                action=Gtk.FileChooserAction.OPEN
            )
            
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            
            # Set starting directory
            if self.project:
                # If project is open, start in project/models/
                models_dir = os.path.join(self.project.base_path, 'models')
                if os.path.exists(models_dir):
                    dialog.set_current_folder(models_dir)
                else:
                    dialog.set_current_folder(self.project.base_path)
            else:
                # Otherwise use current directory in file tree
                current_path = self.get_current_path()
                if current_path and os.path.exists(current_path):
                    if os.path.isfile(current_path):
                        dialog.set_current_folder(os.path.dirname(current_path))
                    else:
                        dialog.set_current_folder(current_path)
                else:
                    # Default to workspace root
                    workspace_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'workspace')
                    workspace_path = os.path.normpath(workspace_path)
                    if os.path.exists(workspace_path):
                        dialog.set_current_folder(workspace_path)
            
            # Add file filter for .shy files
            filter_shy = Gtk.FileFilter()
            filter_shy.set_name("SHYpn Models (*.shy)")
            filter_shy.add_pattern("*.shy")
            dialog.add_filter(filter_shy)
            
            # Add filter for all files
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All Files")
            filter_all.add_pattern("*")
            dialog.add_filter(filter_all)
            
            # Show dialog and handle response
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                filepath = dialog.get_filename()
                dialog.destroy()
                
                # Open the selected file
                if filepath and os.path.exists(filepath):
                    self._open_file_from_path(filepath)
            else:
                dialog.destroy()
                
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
        
        # Check if current tab is empty/default and can be reused
        current_page = self.canvas_loader.notebook.get_current_page()
        can_reuse_tab = False
        
        if current_page >= 0:
            page_widget = self.canvas_loader.notebook.get_nth_page(current_page)
            drawing_area = self.canvas_loader._get_drawing_area_from_page(page_widget)
            if drawing_area:
                manager = self.canvas_loader.get_canvas_manager(drawing_area)
                # Only reuse tab if it's empty (no objects) and has default name
                if manager:
                    is_empty = (len(manager.places) == 0 and 
                               len(manager.transitions) == 0 and 
                               len(manager.arcs) == 0)
                    is_default_name = (manager.filename == 'default' or 
                                      manager.get_display_name() == 'default')
                    is_clean = not manager.is_dirty()
                    can_reuse_tab = is_empty and is_default_name and is_clean
        
        # Either reuse current empty tab or create new one
        if can_reuse_tab:
            # Reuse the current empty default tab
            # CRITICAL: Reset manager state before loading to avoid stale state bugs
            # This ensures callbacks are enabled and all flags are reset
            self.canvas_loader._reset_manager_for_load(manager, base_name)
        else:
            # Create a new tab for this document
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
            has_view_state = False
            if hasattr(document, 'view_state') and document.view_state:
                # Always restore view state, even if it's default (0, 0, 1.0)
                # This prevents unwanted auto-centering on canvas draw
                zoom = document.view_state.get('zoom', 1.0)
                pan_x = document.view_state.get('pan_x', 0.0)
                pan_y = document.view_state.get('pan_y', 0.0)
                
                # Restore zoom and pan (even if default values)
                manager.zoom = zoom
                manager.pan_x = pan_x
                manager.pan_y = pan_y
                
                # CRITICAL: Set initial_pan_set flag in BOTH manager and viewport_controller
                # These can get out of sync, causing pan/zoom disruption
                manager._initial_pan_set = True  # Manager's flag
                manager.viewport_controller._initial_pan_set = True  # Controller's flag
                
                # Restore transformations (rotation) if available
                if 'transformations' in document.view_state:
                    manager.transformation_manager.from_dict(document.view_state['transformations'])
                
                # Consider view state as "custom" if different from defaults
                # Used to decide whether to call fit_to_page later
                has_view_state = (pan_x != 0.0 or pan_y != 0.0 or zoom != 1.0)
            
            # Only fit to page if no saved view state exists
            # This preserves user's saved view position and zoom level
            if not has_view_state:
                # Use deferred=True to wait for viewport dimensions on first draw
                # Use 30% horizontal offset to shift right (accounting for right panel)
                # Use +10% vertical offset to shift UP in Cartesian space (increase Y)
                manager.fit_to_page(padding_percent=15, deferred=True, horizontal_offset_percent=30, vertical_offset_percent=10)
            
            # PHASE 1: Set per-document file state
            # Initialize manager's filepath and mark as clean (just loaded)
            manager.set_filepath(filepath)
            manager.mark_clean()  # Just loaded, no unsaved changes
            
            # Update manager's filename to match the loaded file
            manager.filename = base_name
            
            # Update tab label with the loaded file's name
            self.canvas_loader.update_current_tab_label(base_name, is_modified=False)
            
            # Legacy: Also update global persistency for backward compatibility
            if hasattr(self, 'persistency') and self.persistency:
                self.persistency.set_filepath(filepath)
                self.persistency.mark_clean()
            
            # Force redraw to display loaded objects
            manager.mark_needs_redraw()

    def new_document(self):
        """Create a new document.
        
        Creates a new tab with "default" filename. Does NOT check for unsaved
        changes because File→New should always create a new tab (multi-document
        interface), not replace the current one.
        """
        try:
            if not hasattr(self, 'canvas_loader') or self.canvas_loader is None:
                return
            if not hasattr(self, 'persistency') or self.persistency is None:
                return
            # Create new tab directly - no unsaved changes check needed
            # File→New creates additional tab, doesn't close/replace existing ones
            # Pass replace_empty_default=False to always create new tab
            self.canvas_loader.add_document(replace_empty_default=False)
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