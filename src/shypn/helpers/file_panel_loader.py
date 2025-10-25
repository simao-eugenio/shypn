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
                ("↻", self._on_refresh_clicked)
            ],
            expanded=True  # Expanded by default
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
        """Create Project Information category.
        
        TODO: Create ProjectInfoController to populate this category with live data:
              - Project name
              - Project path
              - Created date
              - Last modified date
              - Models count
              - Project status
              - Git status (if applicable)
              Controller should update when project changes or files are added/removed.
        """
        self.project_info_category = CategoryFrame(
            title="PROJECT INFORMATION",
            expanded=False  # Collapsed by default
        )
        
        # Get project info content from builder (currently static placeholder)
        project_info_content = self.builder.get_object('project_info_content')
        if project_info_content:
            self.project_info_category.set_content(project_info_content)
        
        container.pack_start(self.project_info_category, False, False, 0)
        self.categories.append(self.project_info_category)
    
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
            self.file_explorer = FileExplorerPanel(
                self.builder,
                base_path=self.base_path,
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
        if not self.file_explorer or not self.file_explorer.context_menu:
            return
        
        # Clear existing menu items
        for child in self.file_explorer.context_menu.get_children():
            self.file_explorer.context_menu.remove(child)
        
        # Build comprehensive VS Code-style context menu
        menu_items = [
            ('Open', self.file_explorer._on_context_open_clicked),
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
        
        for label, callback in menu_items:
            if label == '---':
                separator = Gtk.SeparatorMenuItem()
                self.file_explorer.context_menu.append(separator)
            else:
                menu_item = Gtk.MenuItem(label=label)
                if callback:
                    menu_item.connect('activate', callback)
                self.file_explorer.context_menu.append(menu_item)
        
        self.file_explorer.context_menu.show_all()
    
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
        except Exception as e:
            print(f"[LEFT_PANEL] Failed to initialize project controller: {e}", file=sys.stderr)
    
    # Button handlers for Files category
    
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
    
    def _on_refresh_clicked(self):
        """Handle Refresh button click."""
        if self.file_explorer:
            self.file_explorer._on_refresh_clicked(None)
    
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
