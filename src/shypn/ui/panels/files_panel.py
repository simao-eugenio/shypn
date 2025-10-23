"""Files panel controller."""

import sys
from gi.repository import Gtk
from .base_panel import BasePanel


class FilesPanelController(BasePanel):
    """Controller for Files panel (file explorer + project controls).
    
    Manages:
    - File tree view (GtkTreeView)
    - File operations toolbar (New, Open, Save, Save As)
    - Navigation toolbar (Home, Back, Forward, Refresh)
    - Project actions (New Project, Open Project, Settings)
    - Quit button
    
    Architecture:
    - Builds UI programmatically (Wayland-safe, no reparenting)
    - All widgets created directly in container
    - Clean separation: UI building vs. event handling
    """
    
    def __init__(self, builder: Gtk.Builder):
        """Initialize Files panel controller.
        
        Args:
            builder: Gtk.Builder with main window UI loaded
        """
        super().__init__(builder, 'files')
        
        # Widgets (created in initialize())
        self.file_browser_tree = None
        self.file_browser_scroll = None
        self.current_file_entry = None
        self.nav_back_button = None
        self.nav_forward_button = None
        
        # Buttons (for external wiring)
        self.file_new_button = None
        self.file_open_button = None
        self.file_save_button = None
        self.file_save_as_button = None
        self.new_project_button = None
        self.open_project_button = None
        self.quit_button = None
    
    def get_preferred_width(self) -> int:
        """Get preferred width for Files panel.
        
        Returns:
            300 pixels
        """
        return 300
    
    def initialize(self):
        """Initialize Files panel widgets - build complete UI."""
        print(f"[FILES_PANEL] Initializing...", file=sys.stderr)
        
        try:
            # Get container from builder
            self._container = self.builder.get_object('files_panel_container')
            if not self._container:
                raise ValueError("files_panel_container not found in UI")
            
            # Build UI sections
            self._build_file_operations_toolbar()
            self._add_separator()
            self._build_navigation_toolbar()
            self._add_separator()
            self._build_file_browser()
            self._add_separator()
            self._build_project_actions()
            self._add_separator()
            self._build_quit_button()
            
            # Show all widgets
            self._container.show_all()
            
            print(f"[FILES_PANEL] Initialized successfully", file=sys.stderr)
            self._emit_ready()
            
        except Exception as e:
            error_msg = f"Failed to initialize Files panel: {e}"
            print(f"[FILES_PANEL] ERROR: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self._emit_error(error_msg)
    
    def _add_separator(self):
        """Add horizontal separator to container."""
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_visible(True)
        self._container.pack_start(separator, False, True, 0)
    
    def _build_file_operations_toolbar(self):
        """Build file operations toolbar (New, Open, Save, Save As)."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(3)
        toolbar.set_margin_bottom(3)
        
        # New button
        self.file_new_button = Gtk.Button(label="New")
        self.file_new_button.set_tooltip_text("New File (Ctrl+N)")
        self.file_new_button.get_style_context().add_class("flat")
        toolbar.pack_start(self.file_new_button, False, False, 0)
        
        # Open button
        self.file_open_button = Gtk.Button(label="Open")
        self.file_open_button.set_tooltip_text("Open File (Ctrl+O)")
        self.file_open_button.get_style_context().add_class("flat")
        toolbar.pack_start(self.file_open_button, False, False, 0)
        
        # Save button
        self.file_save_button = Gtk.Button(label="Save")
        self.file_save_button.set_tooltip_text("Save File (Ctrl+S)")
        self.file_save_button.get_style_context().add_class("flat")
        toolbar.pack_start(self.file_save_button, False, False, 0)
        
        # Save As button
        self.file_save_as_button = Gtk.Button(label="Save As...")
        self.file_save_as_button.set_tooltip_text("Save As... (Ctrl+Shift+S)")
        self.file_save_as_button.get_style_context().add_class("flat")
        toolbar.pack_start(self.file_save_as_button, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.pack_start(sep, False, False, 0)
        
        # New Folder button
        new_folder_btn = Gtk.Button(label="New Folder")
        new_folder_btn.set_tooltip_text("Create New Folder")
        new_folder_btn.get_style_context().add_class("flat")
        toolbar.pack_start(new_folder_btn, False, False, 0)
        
        self._container.pack_start(toolbar, False, True, 0)
    
    def _build_navigation_toolbar(self):
        """Build navigation toolbar (Home, Back, Forward, Refresh)."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(3)
        toolbar.set_margin_bottom(3)
        
        # Home button
        home_btn = Gtk.Button(label="Home")
        home_btn.set_tooltip_text("Go to Models Home")
        home_btn.get_style_context().add_class("flat")
        toolbar.pack_start(home_btn, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.pack_start(sep, False, False, 0)
        
        # Back button
        self.nav_back_button = Gtk.Button(label="◀")
        self.nav_back_button.set_tooltip_text("Back")
        self.nav_back_button.set_sensitive(False)
        self.nav_back_button.get_style_context().add_class("flat")
        toolbar.pack_start(self.nav_back_button, False, False, 0)
        
        # Current file entry
        self.current_file_entry = Gtk.Entry()
        self.current_file_entry.set_editable(False)
        self.current_file_entry.set_text("workspace/examples/simple.shy")
        self.current_file_entry.set_width_chars(20)
        self.current_file_entry.get_style_context().add_class("flat")
        toolbar.pack_start(self.current_file_entry, True, True, 0)
        
        # Forward button
        self.nav_forward_button = Gtk.Button(label="▶")
        self.nav_forward_button.set_tooltip_text("Forward")
        self.nav_forward_button.set_sensitive(False)
        self.nav_forward_button.get_style_context().add_class("flat")
        toolbar.pack_start(self.nav_forward_button, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.pack_start(sep, False, False, 0)
        
        # Refresh button
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.set_tooltip_text("Refresh / Toggle Hierarchical View")
        refresh_btn.get_style_context().add_class("flat")
        toolbar.pack_start(refresh_btn, False, False, 0)
        
        self._container.pack_start(toolbar, False, True, 0)
    
    def _build_file_browser(self):
        """Build file browser tree view."""
        # Scrolled window
        self.file_browser_scroll = Gtk.ScrolledWindow()
        self.file_browser_scroll.set_policy(
            Gtk.PolicyType.AUTOMATIC,
            Gtk.PolicyType.AUTOMATIC
        )
        self.file_browser_scroll.set_shadow_type(Gtk.ShadowType.IN)
        self.file_browser_scroll.set_size_request(-1, 400)
        
        # Tree view
        self.file_browser_tree = Gtk.TreeView()
        self.file_browser_tree.set_headers_visible(True)
        self.file_browser_tree.set_enable_tree_lines(True)
        self.file_browser_tree.set_show_expanders(True)
        self.file_browser_tree.set_activate_on_single_click(False)
        
        # Add tree to scroll
        self.file_browser_scroll.add(self.file_browser_tree)
        
        self._container.pack_start(self.file_browser_scroll, True, True, 0)
    
    def _build_project_actions(self):
        """Build project actions section."""
        frame = Gtk.Frame()
        frame.set_label_align(0, 0.5)
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.set_margin_start(6)
        frame.set_margin_end(6)
        frame.set_margin_top(6)
        frame.set_margin_bottom(3)
        
        # Frame label
        label = Gtk.Label(label="Project Actions")
        label.get_style_context().add_class("dim-label")
        frame.set_label_widget(label)
        
        # Actions box
        actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        actions_box.set_margin_start(12)
        actions_box.set_margin_end(12)
        actions_box.set_margin_top(6)
        actions_box.set_margin_bottom(6)
        
        # New Project button
        self.new_project_button = Gtk.Button(label="New Project")
        self.new_project_button.set_tooltip_text("Create a new shypn project")
        actions_box.pack_start(self.new_project_button, False, True, 0)
        
        # Open Project button
        self.open_project_button = Gtk.Button(label="Open Project")
        self.open_project_button.set_tooltip_text("Open an existing project or import archive")
        actions_box.pack_start(self.open_project_button, False, True, 0)
        
        # Project Settings button (disabled for now)
        settings_btn = Gtk.Button(label="Project Settings")
        settings_btn.set_tooltip_text("View and edit project properties")
        settings_btn.set_sensitive(False)
        actions_box.pack_start(settings_btn, False, True, 0)
        
        frame.add(actions_box)
        self._container.pack_start(frame, False, True, 0)
    
    def _build_quit_button(self):
        """Build quit application button."""
        self.quit_button = Gtk.Button(label="Quit Application")
        self.quit_button.set_tooltip_text("Exit shypn (prompts to save unsaved changes)")
        self.quit_button.set_margin_start(6)
        self.quit_button.set_margin_end(6)
        self.quit_button.set_margin_top(3)
        self.quit_button.set_margin_bottom(3)
        
        self._container.pack_start(self.quit_button, False, True, 0)
    
    def activate(self):
        """Called when Files panel becomes visible."""
        print(f"[FILES_PANEL] Activated", file=sys.stderr)
        # TODO: Refresh file tree if needed
    
    def deactivate(self):
        """Called when Files panel becomes hidden."""
        print(f"[FILES_PANEL] Deactivated", file=sys.stderr)
        # TODO: Save state if needed
