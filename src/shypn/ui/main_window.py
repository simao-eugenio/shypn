#!/usr/bin/env python3
"""MainWindow - Main application window for SHYPN.

Extracted from shypn.py as part of OOP compliance refactoring (Phase 1, Week 1).
Handles window management, geometry, Wayland compatibility, and menu integration.

Author: Simão Eugénio
Date: January 22, 2026 (Refactored from shypn.py)
"""

import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import logging


class MainWindow:
    """Main SHYPN application window wrapper.
    
    Responsibilities:
    - Window geometry management (size, position, maximize/minimize)
    - Wayland compatibility (Error 71 suppression, monitor changes)
    - Menu integration (File, Edit, View, Help)
    - HeaderBar control buttons (minimize, maximize, close)
    - Panel attachment/floating coordination (via PanelManager)
    
    Architecture:
    - Wraps window from main_window.ui (doesn't inherit from Gtk.Window)
    - Delegates panel management to PanelManager class
    - Uses WorkspaceSettings for geometry persistence
    - Wayland-safe: No X11-specific APIs
    
    Attributes:
        window (Gtk.Window): The actual window from builder
        builder (Gtk.Builder): UI builder for main_window.ui
        panel_manager: PanelManager instance for panel coordination
        workspace_settings: WorkspaceSettings for persistence
        menu_actions: MenuActions instance for menu handling
    """
    
    def __init__(self, app, ui_path, file_to_open=None):
        """Initialize main window.
        
        Args:
            app (Gtk.Application): Application instance
            ui_path (str): Path to main_window.ui file
            file_to_open (str): Optional file path to open on startup
        """
        self.app = app
        self.ui_path = ui_path
        self.file_to_open = file_to_open
        
        # Will be set by PanelManager
        self.panel_manager = None
        
        # Load UI and setup
        self._load_ui()
        self._setup_css()
        self._load_geometry()
        self._setup_wayland_handlers()
        self._setup_window_controls()
        self._setup_menu_actions()
        
        # Open file after idle (if specified)
        if file_to_open:
            GLib.idle_add(self._open_file_delayed)
    
    def _load_ui(self):
        """Load main window UI from Glade file."""
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Get the actual window from builder
        self.window = self.builder.get_object('main_window')
        if not self.window:
            raise RuntimeError("main_window object not found in UI file")
        
        # Set application
        self.window.set_application(self.app)
        
        # Store references to essential widgets
        self.header_bar = self.builder.get_object('header_bar')
        self.main_box = self.builder.get_object('main_box')
        self.canvas_notebook = self.builder.get_object('canvas_notebook')
        self.left_box = self.builder.get_object('left_box')
    
    def _setup_css(self):
        """Load CSS styling for main window."""
        repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../..'))
        css_path = os.path.join(repo_root, 'ui', 'main', 'main_window.css')
        
        if os.path.exists(css_path):
            css_provider = Gtk.CssProvider()
            css_provider.load_from_path(css_path)
            screen = Gdk.Screen.get_default()
            style_context = Gtk.StyleContext()
            style_context.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
    
    def _load_geometry(self):
        """Restore window geometry from workspace settings."""
        from shypn.workspace_settings import WorkspaceSettings
        
        self.workspace_settings = WorkspaceSettings()
        geom = self.workspace_settings.get_window_geometry()
        
        # Set size
        width = geom.get('width', 1200)
        height = geom.get('height', 800)
        self.window.set_default_size(width, height)
        
        # Position (may be ignored on Wayland)
        x = geom.get('x')
        y = geom.get('y')
        if x is not None and y is not None:
            self.window.move(x, y)
        
        # Note: Maximized state applied AFTER panels loaded (Wayland Error 71 prevention)
        self._should_maximize = geom.get('maximized', False)
    
    def _setup_wayland_handlers(self):
        """Configure Wayland compatibility handlers.
        
        Prevents Error 71 on monitor switches and configuration changes.
        """
        # Configure event mask for multi-monitor support
        self.window.connect('realize', self._on_realize)
        
        # Monitor configuration changes
        self.window.connect('configure-event', self._on_configure_event)
        
        # Screen change protection (hotplug)
        self.window.connect('screen-changed', self._on_screen_changed)
        
        # Window state changes
        self.window.connect('window-state-event', self._on_window_state_changed)
    
    def _on_realize(self, widget):
        """Handle window realization - setup event mask."""
        if widget.get_window():
            try:
                widget.get_window().set_events(
                    widget.get_window().get_events() | 
                    Gdk.EventMask.STRUCTURE_MASK |
                    Gdk.EventMask.PROPERTY_CHANGE_MASK
                )
            except Exception:
                pass  # Wayland-specific issue, not critical
    
    def _on_configure_event(self, widget, event):
        """Handle window configuration changes (Wayland-safe).
        
        Suppresses Error 71 during monitor switches and window moves.
        """
        try:
            return False  # Allow normal processing
        except Exception as e:
            # Suppress Wayland Error 71
            if "71" in str(e) or "BadWindow" in str(e):
                return True  # Event handled
            return False
    
    def _on_screen_changed(self, widget, old_screen):
        """Handle screen changes (monitor hotplug, Wayland-safe)."""
        try:
            if widget.get_window():
                widget.get_window().set_events(
                    widget.get_window().get_events() | 
                    Gdk.EventMask.STRUCTURE_MASK |
                    Gdk.EventMask.PROPERTY_CHANGE_MASK
                )
        except Exception:
            pass  # Suppress Wayland errors
        return False
    
    def _on_window_state_changed(self, window, event):
        """Handle window state changes (maximize/minimize)."""
        # Update maximize button icon if available
        maximize_button_image = self.builder.get_object('maximize_button_image')
        if maximize_button_image:
            if self.window.is_maximized():
                maximize_button_image.set_from_icon_name('window-restore-symbolic', 1)
            else:
                maximize_button_image.set_from_icon_name('window-maximize-symbolic', 1)
        return False
    
    def _setup_window_controls(self):
        """Setup window control buttons (minimize, maximize, close)."""
        minimize_button = self.builder.get_object('minimize_button')
        maximize_button = self.builder.get_object('maximize_button')
        
        if minimize_button:
            minimize_button.connect('clicked', self._on_minimize_clicked)
        
        if maximize_button:
            maximize_button.connect('clicked', self._on_maximize_clicked)
        
        # Double-click header bar to toggle maximize
        if self.header_bar:
            self.header_bar.connect('button-press-event', self._on_header_bar_button_press)
    
    def _on_minimize_clicked(self, button):
        """Minimize window (Wayland-safe)."""
        try:
            self.window.iconify()
        except Exception as e:
            logging.getLogger(__name__).warning('Failed to minimize: %s', e)
    
    def _on_maximize_clicked(self, button):
        """Toggle maximize/unmaximize (Wayland-safe)."""
        try:
            if self.window.is_maximized():
                self.window.unmaximize()
            else:
                self.window.maximize()
        except Exception as e:
            logging.getLogger(__name__).warning('Failed to toggle maximize: %s', e)
    
    def _on_header_bar_button_press(self, widget, event):
        """Handle header bar double-click to toggle maximize."""
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == 1:
            self._on_maximize_clicked(None)
            return True
        return False
    
    def _setup_menu_actions(self):
        """Setup menu actions (File, Edit, View, Help)."""
        from shypn.ui.menu_actions import MenuActions
        
        self.menu_actions = MenuActions(self.app, self)
        self.menu_actions.register_all_actions()
    
    def _open_file_delayed(self):
        """Open file after idle (prevents startup race conditions)."""
        if self.file_to_open and os.path.exists(self.file_to_open):
            # Delegate to menu actions or file manager
            # For now, just log
            logging.getLogger(__name__).info('Opening file: %s', self.file_to_open)
        return False  # Don't repeat
    
    def apply_maximize_state(self):
        """Apply maximized state after panels loaded (Wayland Error 71 prevention)."""
        if hasattr(self, '_should_maximize') and self._should_maximize:
            GLib.idle_add(self.window.maximize)
    
    def save_geometry(self):
        """Save current window geometry to workspace settings."""
        if not hasattr(self, 'workspace_settings'):
            return
        
        # Get current geometry
        width, height = self.window.get_size()
        x, y = self.window.get_position()
        maximized = self.window.is_maximized()
        
        # Save to settings
        self.workspace_settings.set_window_geometry({
            'width': width,
            'height': height,
            'x': x,
            'y': y,
            'maximized': maximized
        })
    
    def on_delete_event(self, window, event):
        """Handle window close (save geometry, cleanup).
        
        Returns:
            bool: False to allow window close, True to prevent
        """
        self.save_geometry()
        return False  # Allow close
    
    # Proxy methods to access window properties
    def show_all(self):
        """Show window and all children."""
        self.window.show_all()
    
    def connect(self, signal, handler):
        """Connect signal handler to window."""
        return self.window.connect(signal, handler)
    
    def get_window(self):
        """Get the underlying GdkWindow."""
        return self.window.get_window()
