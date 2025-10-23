#!/usr/bin/env python3
"""Left Panel Loader - VS Code Explorer Style.

Implements VS Code-style Explorer panel with collapsible categories:
1. Files - File browser tree (expanded by default)
2. Project Information - Current project details (collapsed)
3. Project Actions - Project management buttons (collapsed)

Architecture:
  LeftPanelLoader: Category management and UI coordination
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
    print('ERROR: GTK3 not available in left_panel loader:', e, file=sys.stderr)
    sys.exit(1)

# Import controllers
from shypn.helpers.file_explorer_panel import FileExplorerPanel
from shypn.helpers.project_actions_controller import ProjectActionsController
from shypn.ui.category_frame import CategoryFrame


class LeftPanelLoaderVSCode:
    """Loader and controller for the File Explorer panel (VS Code style)."""
    
    def __init__(self, ui_path=None, base_path=None):
        """Initialize the left panel loader.
        
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
            except Exception as e:
                print(f"[LEFT_PANEL] Could not set window event mask: {e}", file=sys.stderr)
        
        print("[LOAD] File Panel (VS Code style) loaded", file=sys.stderr)
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
        """Create Project Information category."""
        self.project_info_category = CategoryFrame(
            title="PROJECT INFORMATION",
            expanded=False  # Collapsed by default
        )
        
        # Get project info content from builder
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
        except Exception as e:
            print(f"[LEFT_PANEL] Failed to initialize file explorer: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def _init_project_controller(self):
        """Initialize project actions controller."""
        try:
            self.project_controller = ProjectActionsController(self.builder, parent_window=None)
            self.project_controller.on_quit_requested = self._on_quit_requested
        except Exception as e:
            print(f"[LEFT_PANEL] Failed to initialize project controller: {e}", file=sys.stderr)
    
    # Button handlers for Files category
    
    def _on_new_file_clicked(self):
        """Handle New File button click."""
        print("[FILES] New File clicked", file=sys.stderr)
        # TODO: Implement new file creation
    
    def _on_new_folder_clicked(self):
        """Handle New Folder button click."""
        print("[FILES] New Folder clicked", file=sys.stderr)
        if self.file_explorer:
            self.file_explorer._on_file_new_folder_clicked(None)
    
    def _on_refresh_clicked(self):
        """Handle Refresh button click."""
        print("[FILES] Refresh clicked", file=sys.stderr)
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
        """Handle float button toggle."""
        pass  # Skeleton - implement later
    
    def _on_delete_event(self, window, event):
        """Handle window delete event - hide instead of destroy."""
        window.hide()
        return True
    
    def set_parent_window(self, window):
        """Set parent window reference for dialogs."""
        self.parent_window = window
        if self.file_explorer:
            self.file_explorer.parent_window = window
        if self.project_controller:
            self.project_controller.set_parent_window(window)
    
    def add_to_stack(self, stack, panel_name='files'):
        """Add panel content to GtkStack for docked mode."""
        if not self.content or not stack:
            return
        
        parent = self.content.get_parent()
        if parent == self.window:
            self.window.remove(self.content)
        elif parent:
            parent.remove(self.content)
        
        stack.add_named(self.content, panel_name)
        self.parent_container = stack
        self._stack = stack
        self._stack_panel_name = panel_name
        print(f"[STACK] FilePanel (VS Code) add_to_stack() called for panel '{panel_name}'", file=sys.stderr)
    
    def show_in_stack(self):
        """Show this panel in the GtkStack."""
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        if self.content:
            self.content.set_no_show_all(False)
            self.content.show_all()
        
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        print("[STACK] FilePanel (VS Code) now visible in stack", file=sys.stderr)
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack."""
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        if self.parent_container:
            self.parent_container.set_visible(False)
        
        print("[STACK] FilePanel (VS Code) hidden in stack", file=sys.stderr)
