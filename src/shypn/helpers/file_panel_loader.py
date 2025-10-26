#!/usr/bin/env python3
"""File Panel Loader - Modern Explorer Style.

Implements modern file explorer panel with collapsible categories:
1. Files - File browser tree (expanded by default)
2. Project Information - Current project details (collapsed)
3. Project Actions - Project management buttons (collapsed)

Architecture:
  FilePanelLoader: Category management and UI coordination
  └── Delegates to:
      ├── FileExplorerPanel: File browsing logic (Files category)
      ├── ProjectInfoController: Project details display (Project Info category)
      └── ProjectActionsController: Project actions (Project Actions category)
"""
import os
import sys
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in file_panel loader:', e, file=sys.stderr)
    sys.exit(1)

# Import controllers
from shypn.helpers.file_explorer_panel import FileExplorerPanel
from shypn.helpers.project_actions_controller import ProjectActionsController
from shypn.ui.category_frame import CategoryFrame


class FilePanelLoader:
    """Loader and controller for the File Explorer panel."""
    
    def __init__(self, ui_path=None, base_path=None):
        """Initialize the file panel loader.
        
        Args:
            ui_path: Optional path to left_panel_vscode.ui. If None, uses default location.
            base_path: Optional base path for file explorer. If None, uses workspace directory.
        """
        if ui_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'panels', 'left_panel_vscode.ui')
            
            if base_path is None:
                base_path = os.path.join(repo_root, 'workspace')
                if not os.path.exists(base_path):
                    try:
                        os.makedirs(base_path)
                    except Exception as e:
                        base_path = repo_root
        
        self.ui_path = ui_path
        self.base_path = base_path
        self.repo_root = repo_root if ui_path is None else os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.builder = None
        self.window = None
        self.content = None
        self.parent_container = None
        self.parent_window = None
        self._updating_button = False
        self.on_float_callback = None
        self.on_attach_callback = None
        self.on_quit_callback = None
        self.is_hanged = False  # State flag: True when in stack, False when floating
        
        # Category frames
        self.files_category = None
        self.project_info_category = None
        self.project_actions_category = None
        self.categories = []
        
        # Sub-controllers
        self.file_explorer = None
        self.project_controller = None
        self.pathway_panel_loader = None  # For updating pathway panel on project open
        
        # Project reference
        self.project = None
        self.model_canvas = None
    
    def load(self):
        """Load the panel UI and create category-based layout.
        
        Returns:
            Gtk.Window: The left panel window.
        """
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Left panel UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('left_panel_window')
        self.content = self.builder.get_object('left_panel_content')
        
        if self.window is None:
            raise ValueError("Object 'left_panel_window' not found in left_panel_vscode.ui")
        if self.content is None:
            raise ValueError("Object 'left_panel_content' not found in left_panel_vscode.ui")
        
        # Get float button
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
        else:
            self.float_button = None
        
        # Get categories container
        categories_container = self.builder.get_object('categories_container')
        if not categories_container:
            raise ValueError("Object 'categories_container' not found")
        
        # Create and setup categories
        self._create_files_category(categories_container)
        self._create_project_info_category(categories_container)
        self._create_project_actions_category(categories_container)
        
        # Setup exclusive expansion behavior
        self._setup_category_expansion()
        
        # Initialize controllers
        self._init_file_explorer()
        self._init_project_controller()
        
        # Connect delete-event
        self.window.connect('delete-event', self._on_delete_event)
        
        # WAYLAND FIX
        self.window.realize()
        if self.window.get_window():
            try:
                from gi.repository import Gdk
                self.window.get_window().set_events(
                    self.window.get_window().get_events() | 
                    Gdk.EventMask.STRUCTURE_MASK |
                    Gdk.EventMask.PROPERTY_CHANGE_MASK
                )
            except Exception:
                pass  # Wayland-specific issue, not critical
        
        return self.window
    
    def _create_files_category(self, container):
        """Create Files category with file browser."""
        # Create category with inline action buttons
        self.files_category = CategoryFrame(
            title="FILES",
            buttons=[
                ("+ File", self._on_new_file_clicked),
                ("+ Folder", self._on_new_folder_clicked),
                ("⌂", self._on_collapse_tree_clicked)  # Home/collapse button
            ],
            expanded=True,  # Expanded by default
            on_collapse=self._on_files_category_collapse  # Callback for collapse
        )
        
        # Build content for Files category
        files_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Breadcrumb bar
        breadcrumb_bar = self.builder.get_object('files_breadcrumb_bar')
        if breadcrumb_bar:
            files_content.pack_start(breadcrumb_bar, False, False, 0)
        
        # File browser tree
        file_browser_scroll = self.builder.get_object('file_browser_scroll')
        if file_browser_scroll:
            files_content.pack_start(file_browser_scroll, True, True, 0)
        
        # Status bar
        files_status_bar = self.builder.get_object('files_status_bar')
        if files_status_bar:
            files_content.pack_start(files_status_bar, False, False, 0)
        
        self.files_category.set_content(files_content)
        container.pack_start(self.files_category, True, True, 0)
        self.categories.append(self.files_category)
    
    def _create_project_info_category(self, container):
        """Create Project Information category with spreadsheet-like view.
        
        Displays project summary in a read-only TreeView (2 columns: Property | Value).
        Auto-populated from project data, no action buttons.
        """
        self.project_info_category = CategoryFrame(
            title="PROJECT INFORMATION",
            expanded=False  # Collapsed by default
        )
        
        # Create spreadsheet-like TreeView
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # Create TreeView with 2 columns: Property | Value
        self.project_info_store = Gtk.ListStore(str, str)  # Property, Value
        self.project_info_treeview = Gtk.TreeView(model=self.project_info_store)
        self.project_info_treeview.set_headers_visible(True)
        self.project_info_treeview.set_enable_search(False)
        self.project_info_treeview.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        
        # Column 1: Property
        property_renderer = Gtk.CellRendererText()
        property_renderer.set_property('weight', 600)  # Bold
        property_column = Gtk.TreeViewColumn('Property', property_renderer, text=0)
        property_column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        property_column.set_min_width(150)
        self.project_info_treeview.append_column(property_column)
        
        # Column 2: Value
        value_renderer = Gtk.CellRendererText()
        value_column = Gtk.TreeViewColumn('Value', value_renderer, text=1)
        value_column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        value_column.set_expand(True)
        self.project_info_treeview.append_column(value_column)
        
        scrolled.add(self.project_info_treeview)
        content_box.pack_start(scrolled, True, True, 0)
        
        self.project_info_category.set_content(content_box)
        container.pack_start(self.project_info_category, False, False, 0)
        self.categories.append(self.project_info_category)
        
        # Populate with initial data
        self._refresh_project_info()
    
    def _create_project_actions_category(self, container):
        """Create Project Actions category."""
        self.project_actions_category = CategoryFrame(
            title="PROJECT ACTIONS",
            expanded=False  # Collapsed by default
        )
        
        # Get project actions content from builder
        project_actions_content = self.builder.get_object('project_actions_content')
        if project_actions_content:
            self.project_actions_category.set_content(project_actions_content)
        
        container.pack_start(self.project_actions_category, False, False, 0)
        self.categories.append(self.project_actions_category)
    
    def _setup_category_expansion(self):
        """Setup exclusive expansion - only one category expanded at a time."""
        for category in self.categories:
            category._title_event_box.connect('button-press-event',
                lambda w, e, cat=category: self._on_category_clicked(cat))
    
    def _on_category_clicked(self, clicked_category):
        """Handle category click - implement exclusive expansion."""
        # If clicked category is collapsed, expand it and collapse others
        if not clicked_category.expanded:
            for category in self.categories:
                if category == clicked_category:
                    category.set_expanded(True)
                else:
                    category.set_expanded(False)
        # If clicked category is already expanded, leave it expanded (don't collapse all)
        return True
    
    def _init_file_explorer(self):
        """Initialize file explorer controller."""
        try:
            workspace_boundary = os.path.join(self.repo_root, 'workspace')
            # Start at workspace root, not subdirectory
            self.file_explorer = FileExplorerPanel(
                self.builder,
                base_path=workspace_boundary,  # Changed from self.base_path to workspace_boundary
                root_boundary=workspace_boundary
            )
            
            # Enhance context menu with VS Code-style operations
            self._enhance_context_menu()
            
            # Connect keyboard shortcuts for file operations
            self._setup_keyboard_shortcuts()
            
        except Exception as e:
            print(f"[LEFT_PANEL] Failed to initialize file explorer: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def _enhance_context_menu(self):
        """Enhance context menu with VS Code-style operations."""
        print("[FILE_PANEL] Enhancing context menu...")
        if not self.file_explorer or not self.file_explorer.context_menu:
            print("[FILE_PANEL] ERROR: file_explorer or context_menu not available")
            return
        
        print(f"[FILE_PANEL] Context menu exists: {self.file_explorer.context_menu}")
        
        # Clear existing menu items
        for child in self.file_explorer.context_menu.get_children():
            self.file_explorer.context_menu.remove(child)
        
        print("[FILE_PANEL] Cleared existing menu items")
        
        # Build comprehensive VS Code-style context menu
        menu_items = [
            ('Open', self.file_explorer._on_context_open_clicked),
            ('Open Project', self._on_open_project_clicked),  # NEW: Open project folder
            ('---', None),
            ('Rename', self.file_explorer._on_rename_clicked),
            ('Delete', self.file_explorer._on_delete_clicked),
            ('---', None),
            ('Cut', self.file_explorer._on_cut_clicked),
            ('Copy', self.file_explorer._on_copy_clicked),
            ('Paste', self.file_explorer._on_paste_clicked),
            ('---', None),
            ('Copy Path', self._on_copy_path_clicked),
            ('Copy Relative Path', self._on_copy_relative_path_clicked),
            ('---', None),
            ('Reveal in File Manager', self._on_reveal_in_file_manager),
            ('Properties', self.file_explorer._on_properties_clicked),
        ]
        
        # Store references for dynamic enable/disable
        self.file_explorer.menu_items_refs = {}
        
        for label, callback in menu_items:
            if label == '---':
                separator = Gtk.SeparatorMenuItem()
                self.file_explorer.context_menu.append(separator)
            else:
                menu_item = Gtk.MenuItem(label=label)
                if callback:
                    menu_item.connect('activate', callback)
                self.file_explorer.context_menu.append(menu_item)
                # Store reference for items that need dynamic visibility
                if label == 'Open Project':
                    self.file_explorer.menu_items_refs['Open Project'] = menu_item
        
        print(f"[FILE_PANEL] Added {len(menu_items)} menu items")
        print(f"[FILE_PANEL] 'Open Project' in refs: {'Open Project' in self.file_explorer.menu_items_refs}")
        
        # Connect to menu show event to update item visibility
        self.file_explorer.context_menu.connect('show', self._on_context_menu_show_enhanced)
        self.file_explorer.context_menu.show_all()
        
        print("[FILE_PANEL] Context menu enhancement complete")
    
    def _on_context_menu_show_enhanced(self, menu):
        """Update context menu item visibility when menu is shown.
        
        Show "Open Project" only when right-clicking on a directory.
        """
        print(f"[FILE_PANEL] Context menu shown")
        if not self.file_explorer or 'Open Project' not in self.file_explorer.menu_items_refs:
            print(f"[FILE_PANEL] ERROR: file_explorer={self.file_explorer}, 'Open Project' in refs={'Open Project' in self.file_explorer.menu_items_refs if self.file_explorer else 'N/A'}")
            return
        
        # Show "Open Project" for any directory (user can create/open project in any folder)
        is_directory = self.file_explorer.selected_item_is_dir if self.file_explorer.selected_item_path else False
        print(f"[FILE_PANEL] Selected path: {self.file_explorer.selected_item_path}")
        print(f"[FILE_PANEL] Is directory: {is_directory}")
        
        # Additional check: see if it has .project.shy (for styling later)
        has_project_file = False
        if is_directory and self.file_explorer.selected_item_path:
            project_file = os.path.join(self.file_explorer.selected_item_path, '.project.shy')
            has_project_file = os.path.exists(project_file)
            print(f"[FILE_PANEL] Project file exists: {has_project_file}")
        
        # Show "Open Project" for any directory
        print(f"[FILE_PANEL] Setting 'Open Project' visible: {is_directory}")
        self.file_explorer.menu_items_refs['Open Project'].set_visible(is_directory)
    
    def _on_open_project_clicked(self, menu_item):
        """Open the selected folder as a SHYpn project (create if needed)."""
        if not self.file_explorer or not self.file_explorer.selected_item_path:
            return
        
        if not self.file_explorer.selected_item_is_dir:
            return
        
        project_dir = self.file_explorer.selected_item_path
        project_file = os.path.join(project_dir, '.project.shy')
        
        # Check if project already exists
        project_exists = os.path.exists(project_file)
        
        # Get folder name as default project name
        folder_name = os.path.basename(project_dir)
        
        if project_exists:
            # Load existing project
            try:
                from shypn.data.project_models import Project
                project = Project.load(project_file)
                project_name = project.name if project and project.name else folder_name
            except:
                project_name = folder_name
            
            # Show confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.file_explorer.parent_window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Open Project?"
            )
            dialog.format_secondary_text(
                f"Do you want to open the project '{project_name}'?\n\n"
                f"This will set the project as the active workspace for all operations."
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                print(f"[FILES] Opening existing project: {project_file}")
                self._on_project_opened_from_file_panel(project_file)
            else:
                print(f"[FILES] User cancelled project open")
        else:
            # Create new project in this folder
            dialog = Gtk.MessageDialog(
                transient_for=self.file_explorer.parent_window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Create Project?"
            )
            dialog.format_secondary_text(
                f"The folder '{folder_name}' is not a SHYpn project yet.\n\n"
                f"Do you want to create a new project in this folder?"
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                try:
                    from shypn.data.project_models import Project
                    # Create new project
                    project = Project(name=folder_name, base_path=project_dir)
                    project.save()
                    print(f"[FILES] Created new project: {project_file}")
                    self._on_project_opened_from_file_panel(project_file)
                except Exception as e:
                    print(f"[FILES] Error creating project: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[FILES] User cancelled project creation")
    
    def _on_copy_path_clicked(self, menu_item):
        """Copy absolute path to clipboard."""
        if not self.file_explorer or not self.file_explorer.selected_item_path:
            return
        
        from gi.repository import Gdk
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.file_explorer.selected_item_path, -1)
        print(f"[FILES] Copied path: {self.file_explorer.selected_item_path}", file=sys.stderr)
    
    def _on_copy_relative_path_clicked(self, menu_item):
        """Copy workspace-relative path to clipboard."""
        if not self.file_explorer or not self.file_explorer.selected_item_path:
            return
        
        from gi.repository import Gdk
        import os
        abs_path = self.file_explorer.selected_item_path
        workspace_path = os.path.join(self.repo_root, 'workspace')
        
        try:
            rel_path = os.path.relpath(abs_path, workspace_path)
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(rel_path, -1)
            print(f"[FILES] Copied relative path: {rel_path}", file=sys.stderr)
        except ValueError:
            # File is outside workspace, copy absolute path
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(abs_path, -1)
    
    def _on_reveal_in_file_manager(self, menu_item):
        """Open file manager and select the file."""
        if not self.file_explorer or not self.file_explorer.selected_item_path:
            return
        
        import subprocess
        import os
        
        path = self.file_explorer.selected_item_path
        
        try:
            # Use xdg-open to open the parent directory
            parent_dir = os.path.dirname(path) if os.path.isfile(path) else path
            subprocess.Popen(['xdg-open', parent_dir])
            print(f"[FILES] Revealed in file manager: {parent_dir}", file=sys.stderr)
        except Exception as e:
            print(f"[FILES] Failed to reveal in file manager: {e}", file=sys.stderr)
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for file operations (F2=Rename, Del=Delete, etc.)."""
        if not self.file_explorer or not self.file_explorer.tree_view:
            return
        
        tree_view = self.file_explorer.tree_view
        
        # Connect key-press-event
        tree_view.connect('key-press-event', self._on_tree_key_press)
    
    def _on_tree_key_press(self, widget, event):
        """Handle keyboard shortcuts in file tree.
        
        Shortcuts:
        - F2: Rename selected file/folder (inline)
        - Delete: Delete selected file/folder
        - Ctrl+C: Copy
        - Ctrl+X: Cut
        - Ctrl+V: Paste
        - Ctrl+N: New file (inline)
        - Ctrl+Shift+N: New folder (inline)
        """
        from gi.repository import Gdk
        
        keyval = event.keyval
        state = event.state
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        shift = state & Gdk.ModifierType.SHIFT_MASK
        
        # F2 - Rename
        if keyval == Gdk.KEY_F2:
            if self.file_explorer and self.file_explorer.selected_item_path:
                self.file_explorer._on_rename_clicked(None)
            return True
        
        # Delete - Delete file/folder
        elif keyval == Gdk.KEY_Delete:
            if self.file_explorer and self.file_explorer.selected_item_path:
                self.file_explorer._on_delete_clicked(None)
            return True
        
        # Ctrl+C - Copy
        elif ctrl and keyval == Gdk.KEY_c:
            if self.file_explorer and self.file_explorer.selected_item_path:
                self.file_explorer._on_copy_clicked(None)
            return True
        
        # Ctrl+X - Cut
        elif ctrl and keyval == Gdk.KEY_x:
            if self.file_explorer and self.file_explorer.selected_item_path:
                self.file_explorer._on_cut_clicked(None)
            return True
        
        # Ctrl+V - Paste
        elif ctrl and keyval == Gdk.KEY_v:
            if self.file_explorer:
                self.file_explorer._on_paste_clicked(None)
            return True
        
        # Ctrl+N - New file (inline)
        elif ctrl and not shift and keyval == Gdk.KEY_n:
            self._on_new_file_clicked()
            return True
        
        # Ctrl+Shift+N - New folder (inline)
        elif ctrl and shift and keyval == Gdk.KEY_N:
            self._on_new_folder_clicked()
            return True
        
        return False
    
    def _init_project_controller(self):
        """Initialize project actions controller.
        
        TODO: Add ProjectInfoController to populate PROJECT INFORMATION category.
              This controller should:
              1. Monitor workspace for changes (file additions/deletions)
              2. Display current project statistics (models count, etc.)
              3. Show project metadata (name, path, dates)
              4. Update live when project state changes
              5. Integrate with persistency manager for project data
              
              Implementation:
              - Create src/shypn/helpers/project_info_controller.py
              - Wire to project_info_content widget
              - Connect to file_explorer signals for updates
        """
        try:
            self.project_controller = ProjectActionsController(self.builder, parent_window=None)
            self.project_controller.on_quit_requested = self._on_quit_requested
            
            # Wire project controller callbacks to propagate project to all components
            self.project_controller.on_project_opened = self._on_project_opened_handler
            self.project_controller.on_project_created = self._on_project_created_handler
            
            # Wire file explorer to project controller for project opening mode
            # NOTE: FileExplorerPanel doesn't support inline project creation yet
            # For now, it will fallback to dialogs (which is expected behavior)
            # TODO: Migrate to FilePanelV3Loader which has inline support
            if self.file_explorer:
                print("[LEFT_PANEL] FileExplorerPanel doesn't support inline project creation - will use dialogs")
                # Still wire callbacks for when projects are opened/created
                # These will be called from context menu actions instead
                
        except Exception as e:
            print(f"[LEFT_PANEL] Failed to initialize project controller: {e}", file=sys.stderr)
    
    # Button handlers for Files category
    
    def _on_files_category_collapse(self):
        """Handle FILES category collapse - navigate to workspace root and collapse tree."""
        if self.file_explorer:
            # Navigate to workspace root
            if hasattr(self.file_explorer.explorer, 'root_boundary') and self.file_explorer.explorer.root_boundary:
                self.file_explorer.explorer.navigate_to(self.file_explorer.explorer.root_boundary)
            # Collapse all expanded folders
            self.file_explorer.tree_view.collapse_all()
            print("[FILES] Category collapsed - navigated to workspace root and collapsed tree", file=sys.stderr)
    
    def _on_new_file_clicked(self):
        """Handle New File button click - creates file with inline editing."""
        if self.file_explorer:
            # Use existing inline editing infrastructure
            self.file_explorer._start_inline_edit_new_file()
    
    def _on_new_folder_clicked(self):
        """Handle New Folder button click - creates folder with inline editing."""
        if self.file_explorer:
            # Use existing inline editing infrastructure
            self.file_explorer._start_inline_edit_new_folder()
    
    def _on_collapse_tree_clicked(self):
        """Handle collapse tree button click - navigate to workspace root and collapse tree."""
        if self.file_explorer:
            # Navigate to workspace root
            if hasattr(self.file_explorer.explorer, 'root_boundary') and self.file_explorer.explorer.root_boundary:
                self.file_explorer.explorer.navigate_to(self.file_explorer.explorer.root_boundary)
            # Collapse all expanded folders
            self.file_explorer.tree_view.collapse_all()
            print("[FILES] Tree collapsed - navigated to workspace root", file=sys.stderr)
    
    def _on_quit_requested(self):
        """Handle quit request from project controller."""
        if self.on_quit_callback:
            self.on_quit_callback()
        else:
            Gtk.main_quit()
    
    # Panel management methods (same as original)
    
    def _on_float_toggled(self, button):
        """Handle float button toggle - detach/attach panel."""
        print(f"[FILE_PANEL] Float button toggled: active={button.get_active()}")
        
        if button.get_active():
            # Button is active -> detach (float)
            self.detach()
        else:
            # Button is inactive -> attach
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def detach(self):
        """Detach from container and create floating window."""
        print(f"[FILE_PANEL] detach() called, is_hanged={self.is_hanged}, window exists={self.window is not None}")
        
        if not self.is_hanged:
            print(f"[FILE_PANEL] Already detached")
            return
        
        if not self.parent_container:
            print(f"[FILE_PANEL] No parent container, aborting detach")
            return
        
        # Create window if it doesn't exist
        if self.window is None:
            print(f"[FILE_PANEL] Creating window on-demand")
            self.window = Gtk.Window()
            self.window.set_title('Files')
            self.window.set_default_size(300, 600)
            self.window.connect('delete-event', self._on_delete_event)
        
        # Remove content from container
        print(f"[FILE_PANEL] Removing content from container")
        self.parent_container.remove(self.content)
        self.parent_container.set_visible(False)
        
        # Hide the stack itself when detaching to avoid showing empty container
        if hasattr(self, '_stack') and self._stack:
            print(f"[FILE_PANEL] Hiding stack")
            self._stack.set_visible(False)
        
        # Add content to window
        print(f"[FILE_PANEL] Adding content to window")
        self.window.add(self.content)
        
        # Set transient for main window
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state - panel is now floating
        self.is_hanged = False
        
        # Show window
        print(f"[FILE_PANEL] Showing window")
        self.window.show_all()
        print(f"[FILE_PANEL] Detach complete")
    
    def hang_on(self, container):
        """Attach panel back to container."""
        print(f"[FILE_PANEL] hang_on() called, is_hanged={self.is_hanged}")
        
        if self.is_hanged:
            print(f"[FILE_PANEL] Already hanged, just showing")
            if not self.content.get_visible():
                self.content.show()
            # Make sure container is visible when re-showing
            if not container.get_visible():
                container.set_visible(True)
            return
        
        if not self.window:
            print(f"[FILE_PANEL] No window exists, aborting hang_on")
            return
        
        # Hide window
        print(f"[FILE_PANEL] Hiding window")
        self.window.hide()
        
        # Remove content from window
        print(f"[FILE_PANEL] Removing content from window")
        self.window.remove(self.content)
        
        # Add content back to container
        print(f"[FILE_PANEL] Adding content to container")
        container.add(self.content)
        container.set_visible(True)
        self.content.show_all()
        
        # Show the stack again when re-attaching
        if hasattr(self, '_stack') and self._stack:
            print(f"[FILE_PANEL] Showing stack")
            self._stack.set_visible(True)
            self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Update state - panel is now in stack
        self.is_hanged = True
        
        print(f"[FILE_PANEL] Hang complete")
    
    def _on_delete_event(self, window, event):
        """Handle window delete event - hide and re-attach."""
        print(f"[FILE_PANEL] Window close button clicked")
        window.hide()
        
        # Re-attach to container
        if self.parent_container and self.float_button:
            # Deactivate float button (will trigger hang_on)
            self.float_button.set_active(False)
        
        return True
    
    def set_parent_window(self, window):
        """Set parent window reference for dialogs."""
        self.parent_window = window
        if self.file_explorer:
            self.file_explorer.parent_window = window
        if self.project_controller:
            self.project_controller.set_parent_window(window)
    
    def add_to_stack(self, stack, container, panel_name='files'):
        """Add panel content to GtkStack for docked mode.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('files')
        """
        # WAYLAND FIX: Load content if not already loaded
        if not self.content:
            if not os.path.exists(self.ui_path):
                raise FileNotFoundError(f"Left panel UI file not found: {self.ui_path}")
            
            # Load the UI
            self.builder = Gtk.Builder.new_from_file(self.ui_path)
            
            # Extract ONLY the content (not the window)
            self.content = self.builder.get_object('left_panel_content')
            
            if self.content is None:
                raise ValueError("Object 'left_panel_content' not found in left_panel_vscode.ui")
            
            # Get float button and connect signal
            float_button = self.builder.get_object('float_button')
            if float_button:
                float_button.connect('toggled', self._on_float_toggled)
                self.float_button = float_button
            else:
                self.float_button = None
            
            # Get categories container
            categories_container = self.builder.get_object('categories_container')
            if categories_container:
                # Create and setup categories
                self._create_files_category(categories_container)
                self._create_project_info_category(categories_container)
                self._create_project_actions_category(categories_container)
                
                # Setup exclusive expansion behavior
                self._setup_category_expansion()
                
                # Initialize controllers (CRITICAL: must happen after categories are created)
                self._init_file_explorer()
                self._init_project_controller()
        
        if not container:
            return
        
        # Remove from current parent
        parent = self.content.get_parent()
        if parent and parent != container:
            parent.remove(self.content)
        
        # Add content to container
        if self.content.get_parent() != container:
            container.add(self.content)
        
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        # Mark as hanged in stack mode
        self.is_hanged = True
    
    def show_in_stack(self):
        """Show this panel in the GtkStack."""
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # If panel is floating, don't try to show in stack
        if not self.is_hanged:
            print(f"[FILE_PANEL] Panel is floating, skipping show_in_stack")
            return
        
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        if self.content:
            self.content.set_no_show_all(False)
            self.content.show_all()
        
        if self.parent_container:
            self.parent_container.set_visible(True)
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack."""
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        if self.parent_container:
            self.parent_container.set_visible(False)
    
    def set_project(self, project):
        """Set the active project and refresh project information.
        
        Args:
            project: Project instance with metadata
        """
        self.project = project
        self._refresh_project_info()
    
    def set_model_canvas(self, model_canvas):
        """Set the model canvas for extracting model statistics.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        self._refresh_project_info()
    
    def set_pathway_panel_loader(self, pathway_panel_loader):
        """Set the pathway panel loader for project synchronization.
        
        Args:
            pathway_panel_loader: PathwayPanelLoader instance
        """
        self.pathway_panel_loader = pathway_panel_loader
    
    def set_model_canvas_loader(self, model_canvas):
        """Set the model canvas loader for project synchronization.
        
        Args:
            model_canvas: ModelCanvasLoader instance
        """
        self.model_canvas = model_canvas
    
    def _refresh_project_info(self):
        """Refresh project information spreadsheet view."""
        if not hasattr(self, 'project_info_store'):
            return  # Not initialized yet
        
        self.project_info_store.clear()
        
        if not self.project:
            # No project loaded
            self.project_info_store.append(['Status', 'No project loaded'])
            return
        
        # Project basic info
        self.project_info_store.append(['Project Name', self.project.name or 'Untitled'])
        self.project_info_store.append(['Path', self.project.base_path or 'N/A'])
        
        # Dates
        if hasattr(self.project, 'created_date') and self.project.created_date:
            self.project_info_store.append(['Created', str(self.project.created_date)])
        if hasattr(self.project, 'modified_date') and self.project.modified_date:
            self.project_info_store.append(['Last Modified', str(self.project.modified_date)])
        
        # Add separator row
        self.project_info_store.append(['', ''])
        
        # Content counts
        models_count = len(self.project.models) if hasattr(self.project, 'models') else 0
        self.project_info_store.append(['Models', str(models_count)])
        
        # Pathways count
        if hasattr(self.project, 'pathways'):
            pathways = self.project.pathways.list_pathways()
            kegg_count = len([p for p in pathways if p.source_type == 'kegg'])
            sbml_count = len([p for p in pathways if p.source_type == 'sbml'])
            total_pathways = len(pathways)
            
            pathways_str = f"{total_pathways}"
            if kegg_count > 0 or sbml_count > 0:
                pathways_str += f" (KEGG: {kegg_count}, SBML: {sbml_count})"
            
            self.project_info_store.append(['Pathways', pathways_str])
            
            # Enrichments count
            total_enrichments = sum(len(p.enrichments) for p in pathways)
            if total_enrichments > 0:
                # Count by source
                brenda_count = 0  # TODO: Count actual BRENDA enrichments
                sabiork_count = 0  # TODO: Count actual SABIO-RK enrichments
                
                enrichments_str = f"{total_enrichments}"
                if brenda_count > 0 or sabiork_count > 0:
                    enrichments_str += f" (BRENDA: {brenda_count}, SABIO-RK: {sabiork_count})"
                
                self.project_info_store.append(['Enrichments', enrichments_str])
            else:
                self.project_info_store.append(['Enrichments', '0'])
        
        # Model canvas statistics (if available)
        if self.model_canvas:
            self.project_info_store.append(['', ''])
            
            try:
                places = len(self.model_canvas.model.places) if hasattr(self.model_canvas, 'model') else 0
                transitions = len(self.model_canvas.model.transitions) if hasattr(self.model_canvas, 'model') else 0
                arcs = len(self.model_canvas.model.arcs) if hasattr(self.model_canvas, 'model') else 0
                
                self.project_info_store.append(['Places', str(places)])
                self.project_info_store.append(['Transitions', str(transitions)])
                self.project_info_store.append(['Arcs', str(arcs)])
            except Exception as e:
                print(f"[FILE_PANEL] Could not extract model statistics: {e}")
    
    def _on_project_opened_from_file_panel(self, project_path):
        """Handle project opening from file panel selection.
        
        Args:
            project_path: Path to the .shy project file
        """
        print(f"[FILE_PANEL] Project selected for opening: {project_path}")
        
        try:
            # Use project manager to open the project
            from shypn.data.project_models import get_project_manager
            project_manager = get_project_manager()
            project = project_manager.open_project_by_path(project_path)
            
            if project:
                print(f"[FILE_PANEL] Project opened successfully: {project.name}")
                self._propagate_project_to_all_components(project)
                
                # Trigger project controller callback
                if self.project_controller:
                    self.project_controller._on_project_opened(project)
            else:
                print(f"[FILE_PANEL] Failed to open project: {project_path}", file=sys.stderr)
                
        except Exception as e:
            print(f"[FILE_PANEL] Error opening project: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def _on_project_opened_handler(self, project):
        """Handle project opened from dialog (not file panel).
        
        Args:
            project: The opened Project instance
        """
        print(f"[FILE_PANEL] Project opened via dialog: {project.name}")
        self._propagate_project_to_all_components(project)
    
    def _on_project_created_handler(self, project):
        """Handle project created from dialog (not file panel).
        
        Args:
            project: The newly created Project instance
        """
        print(f"[FILE_PANEL] Project created via dialog: {project.name}")
        self._propagate_project_to_all_components(project)
    
    def _propagate_project_to_all_components(self, project):
        """Propagate project reference to all components that need it.
        
        Args:
            project: Project instance to propagate
        """
        print(f"[FILE_PANEL] Propagating project to all components: {project.name}")
        
        # Update project info display
        self.set_project(project)
        
        # Update file explorer so it saves to project/models/
        if self.file_explorer:
            print(f"[FILE_PANEL]   → file_explorer")
            self.file_explorer.set_project(project)
        
        # Update canvas loader so all managers save to correct project paths
        if self.model_canvas:
            print(f"[FILE_PANEL]   → model_canvas")
            self.model_canvas.set_project(project)
        
        # Notify pathway panel about project (so import controllers can save to it)
        if self.pathway_panel_loader:
            print(f"[FILE_PANEL]   → pathway_panel_loader")
            self.pathway_panel_loader.set_project(project)
    
    def _on_project_created_from_file_panel(self, project):
        """Handle project creation from file panel inline edit.
        
        Args:
            project: The newly created Project instance
        """
        print(f"[FILE_PANEL] Project created from file panel: {project.name}")
        
        try:
            # Trigger project controller callback
            if self.project_controller:
                self.project_controller._on_project_created(project)
                
        except Exception as e:
            print(f"[FILE_PANEL] Error handling project creation: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()


def create_left_panel(ui_path=None, base_path=None, load_window=False):
    """Convenience function to create the modern file panel loader.
    
    Args:
        ui_path: Optional path to left_panel_vscode.ui (default: auto-detected).
        base_path: Optional base path for file explorer (default: models directory).
        load_window: If True, loads the window. If False (default), defers to add_to_stack().
        
    Returns:
        FilePanelLoader: The file panel loader instance.
        
    Example:
        loader = create_left_panel(base_path="/home/user/projects/models", load_window=True)
        loader.window.show_all()  # Show as floating
        # or
        loader = create_left_panel()  # Don't load window yet
        loader.add_to_stack(stack, container)  # Will load content directly to stack
    """
    loader = FilePanelLoader(ui_path, base_path)
    if load_window:
        loader.load()  # Only load if explicitly requested
    return loader
