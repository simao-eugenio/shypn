"""File Panel V3 Loader - Normalized architecture with XML UI.

Follows the same pattern as TopologyPanelLoader:
- Inherits from FilePanelBase
- Loads UI from XML file
- Delegates business logic to controller
- Wires float button and signals

Author: Simão Eugénio
Date: 2025-10-22
"""

import sys
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.file_panel_base import FilePanelBase
from shypn.ui.file_panel_controller import FilePanelController


class FilePanelV3Loader(FilePanelBase):
    """Loader for File Panel V3 (XML UI-based).
    
    Responsibilities (MINIMAL):
    - Load UI from XML
    - Get widget references (TreeView, buttons, etc.)
    - Connect signals to controller
    - Delegate all logic to controller
    
    NOT responsible for:
    - File operations (handled by controller)
    - TreeView population (handled by controller)
    - Context menu logic (handled by controller)
    """
    
    def __init__(self, base_path=None, ui_path=None):
        """Initialize file panel loader.
        
        Args:
            base_path: Base directory for file browser
            ui_path: Optional path to UI file
        """
        # Determine base path
        if base_path is None:
            script_dir = Path(__file__).parent
            repo_root = script_dir.parent.parent.parent
            base_path = repo_root / 'workspace'
            
            # Ensure workspace exists
            if not base_path.exists():
                try:
                    base_path.mkdir(parents=True, exist_ok=True)
                except Exception:
                    base_path = repo_root
        
        # Store base path
        self.base_path = Path(base_path)
        
        # Controller (created after UI loads)
        self.controller = None
        
        # Compatibility attributes
        self.project_controller = None  # Not used in V3 (project operations moved elsewhere)
        
        # Widget references
        self.path_entry = None
        self.tree_view = None
        self.tree_store = None
        self.tree_scroll = None
        self.categories_container = None
        
        # Initialize base (loads UI)
        super().__init__(ui_path)
        
        # Load UI
        self.load()
    
    def _init_widgets(self):
        """Get widget references from builder.
        
        Called by base class after UI loads.
        """
        # Get main widgets
        self.path_entry = self.builder.get_object('file_path_entry')
        self.tree_view = self.builder.get_object('file_tree_view')
        self.tree_store = self.builder.get_object('file_tree_store')
        self.tree_scroll = self.builder.get_object('file_tree_scroll')
        self.categories_container = self.builder.get_object('file_panel_categories_container')
        
        # Configure TreeView
        if self.tree_view and self.tree_store:
            self.tree_view.set_model(self.tree_store)
            
            # Add column with cell renderer
            name_column = Gtk.TreeViewColumn("Name")
            name_column.set_expand(True)
            
            # Name renderer (with weight for bold folders)
            self.name_renderer = Gtk.CellRendererText()
            self.name_renderer.set_property('editable', False)
            name_column.pack_start(self.name_renderer, True)
            name_column.add_attribute(self.name_renderer, 'text', 0)
            name_column.add_attribute(self.name_renderer, 'weight', 3)  # Bold for folders
            
            self.tree_view.append_column(name_column)
    
    def _connect_signals(self):
        """Connect signals to controller methods.
        
        Called by base class after widgets are initialized.
        """
        # IMPORTANT: Replace the basic TreeView structure with CategoryFrame structure
        # The XML UI has a simple container, but we need the CategoryFrame design
        self._build_category_structure()
        
        # Create controller
        self.controller = FilePanelController(
            base_path=self.base_path,
            tree_view=self.tree_view,
            tree_store=self.tree_store,
            path_entry=self.path_entry,
            name_renderer=self.name_renderer,
        )
        
        # Connect TreeView signals
        if self.tree_view:
            self.tree_view.connect('row-activated', self.controller.on_row_activated)
            self.tree_view.connect('button-press-event', self.controller.on_tree_button_press)
            
            # Selection tracking
            selection = self.tree_view.get_selection()
            selection.connect('changed', self.controller.on_selection_changed)
        
        # Connect path entry
        if self.path_entry:
            self.path_entry.connect('activate', self.controller.on_path_entry_activate)
        
        # Connect float button if present
        float_button = self.builder.get_object('file_panel_float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
            self._updating_button = False  # Flag to prevent recursive toggle events
        else:
            self.float_button = None
        
        # Load initial file tree
        self.controller.refresh_tree()
        
    
    def _build_category_structure(self):
        """Build CategoryFrame structure programmatically (like File Panel V2).
        
        Replaces the simple TreeView container from XML with proper CategoryFrames.
        """
        from shypn.ui.category_frame import CategoryFrame
        
        
        # Clear the categories container
        for child in self.categories_container.get_children():
            self.categories_container.remove(child)
        
        # Category 1: Files (CRITICAL - expanded by default)
        self.files_category = CategoryFrame(
            title="Files",
            buttons=[
                ("＋", self.controller.on_new_file if self.controller else lambda: None),
                ("📁", self.controller.on_new_folder if self.controller else lambda: None),
                ("↻", self.controller.on_refresh if self.controller else lambda: None),
                ("─", self.controller.on_collapse_all if self.controller else lambda: None)
            ],
            expanded=True
        )
        
        # Connect category expand to ensure only one is open at a time
        self.files_category._title_event_box.connect('button-press-event', 
            lambda w, e: self._on_category_clicked(self.files_category))
        
        # Create content box for Files category
        files_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Move path entry and tree view from XML container to Files category
        if self.path_entry and self.path_entry.get_parent():
            self.path_entry.get_parent().remove(self.path_entry)
        if self.tree_scroll and self.tree_scroll.get_parent():
            self.tree_scroll.get_parent().remove(self.tree_scroll)
        
        files_content.pack_start(self.path_entry, False, False, 0)
        files_content.pack_start(self.tree_scroll, True, True, 0)
        
        # Make sure all widgets are visible
        files_content.show_all()
        
        self.files_category.set_content(files_content)
        self.categories_container.pack_start(self.files_category, True, True, 0)
        
        # Category 2: Project Information (PLACEHOLDER)
        self.project_info_category = CategoryFrame(
            title="Project Information",
            expanded=False,
            placeholder=True
        )
        self.project_info_category._title_event_box.connect('button-press-event',
            lambda w, e: self._on_category_clicked(self.project_info_category))
        self.categories_container.pack_start(self.project_info_category, False, False, 0)
        
        # Category 3: Project Settings (PLACEHOLDER)
        self.project_settings_category = CategoryFrame(
            title="Project Settings",
            expanded=False,
            placeholder=True
        )
        self.project_settings_category._title_event_box.connect('button-press-event',
            lambda w, e: self._on_category_clicked(self.project_settings_category))
        self.categories_container.pack_start(self.project_settings_category, False, False, 0)
        
        # Keep track of all categories for exclusive expansion
        self.categories = [
            self.files_category,
            self.project_info_category,
            self.project_settings_category
        ]
        
    
    def _on_category_clicked(self, clicked_category):
        """Handle category title click - ensure only one expanded at a time.
        
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
            is_expanded = (category == clicked_category and new_state)
            self.categories_container.child_set_property(category, 'expand', is_expanded)
            self.categories_container.child_set_property(category, 'fill', is_expanded)
        
        return True  # Stop propagation
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        if is_active:
            # Button is now active → detach the panel (float)
            self.detach()
        else:
            # Button is now inactive → attach the panel back
            if hasattr(self, 'parent_container') and self.parent_container:
                self.hang_on(self.parent_container)
    
    # ===============================
    # Public API for shypn.py
    # ===============================
    
    def set_parent_window(self, parent_window):
        """Set parent window for dialogs.
        
        Args:
            parent_window: Parent window instance
        """
        self.parent_window = parent_window
        if self.controller:
            self.controller.set_parent_window(parent_window)
    
    def set_canvas_loader(self, canvas_loader):
        """Set canvas loader for file open operations.
        
        Args:
            canvas_loader: ModelCanvasLoader instance
        """
        if self.controller:
            self.controller.set_canvas_loader(canvas_loader)
    
    def set_persistency_manager(self, persistency):
        """Set persistency manager for file operations.
        
        Args:
            persistency: Persistency manager instance
        """
        if self.controller:
            self.controller.set_persistency_manager(persistency)
    
    def get_widget(self):
        """Get the main content widget (for backward compatibility).
        
        Returns:
            Gtk.Box: Main content widget
        """
        return self.content
    
    # ===============================
    # Backward Compatibility Wrapper
    # ===============================
    
    @property
    def file_explorer(self):
        """Provide file_explorer interface for backward compatibility.
        
        Returns a wrapper that delegates to the controller.
        """
        if not hasattr(self, '_file_explorer_wrapper'):
            self._file_explorer_wrapper = FileExplorerWrapper(self)
        return self._file_explorer_wrapper


class FileExplorerWrapper:
    """Compatibility wrapper to mimic old file_explorer interface."""
    
    def __init__(self, loader):
        """Initialize wrapper.
        
        Args:
            loader: FilePanelV3Loader instance
        """
        self.loader = loader
        self.persistency = None
    
    def set_parent_window(self, window):
        """Set parent window."""
        self.loader.set_parent_window(window)
        if self.persistency:
            self.persistency.parent_window = window
    
    def set_canvas_loader(self, canvas_loader):
        """Set canvas loader."""
        self.loader.set_canvas_loader(canvas_loader)
    
    def set_persistency_manager(self, persistency):
        """Set persistency manager."""
        self.persistency = persistency
        self.loader.set_persistency_manager(persistency)
    
    def _open_file_from_path(self, filepath):
        """Open file (delegates to controller)."""
        if self.loader.controller:
            self.loader.controller._open_file(filepath)


def create_file_panel_v3(base_path=None):
    """Factory function to create File Panel V3 loader.
    
    Args:
        base_path: Base directory for file browser
    
    Returns:
        FilePanelV3Loader instance
    """
    loader = FilePanelV3Loader(base_path=base_path)
    return loader
