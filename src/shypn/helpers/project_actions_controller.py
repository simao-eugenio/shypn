#!/usr/bin/env python3
"""Project Actions Controller.

This module provides the controller for project management actions in the File Explorer panel.
Handles project lifecycle operations: create, open, close, settings, and quit.

This follows the OOP principle of separating concerns:
- ProjectActionsController: Business logic for project actions
- ProjectDialogManager: Dialog presentation layer
- ProjectManager: Data model and persistence layer
"""

import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print('ERROR: GTK3 not available in project_actions_controller:', e, file=sys.stderr)
    sys.exit(1)

from shypn.helpers.project_dialog_manager import ProjectDialogManager
from shypn.data.project_models import get_project_manager


class ProjectActionsController:
    """Controller for project management actions.
    
    Responsibilities:
    - Handle button click events
    - Coordinate between dialogs and data models
    - Manage UI state (enable/disable buttons)
    - Trigger callbacks for integration with other components
    
    Does NOT:
    - Load UI widgets (that's the loader's job)
    - Present dialogs (that's ProjectDialogManager's job)
    - Manage data (that's ProjectManager's job)
    """
    
    def __init__(self, builder, parent_window=None):
        """Initialize the project actions controller.
        
        Args:
            builder: Gtk.Builder with loaded UI widgets
            parent_window: Parent window for dialogs
        """
        self.builder = builder
        self.parent_window = parent_window
        
        # Get project manager singleton
        self.project_manager = get_project_manager()
        
        # Initialize dialog manager
        self.dialog_manager = ProjectDialogManager(parent_window=parent_window)
        
        # Setup dialog callbacks
        self.dialog_manager.on_project_created = self._on_project_created
        self.dialog_manager.on_project_opened = self._on_project_opened
        self.dialog_manager.on_project_closed = self._on_project_closed
        
        # Store widget references
        self.new_project_button = None
        self.open_project_button = None
        self.project_settings_button = None
        self.quit_button = None
        
        # External callbacks (set by owner)
        self.on_project_created = None  # Callback(project)
        self.on_project_opened = None   # Callback(project)
        self.on_project_closed = None   # Callback()
        self.on_quit_requested = None   # Callback()
        
        # Connect buttons
        self._connect_buttons()
    
    def _connect_buttons(self):
        """Connect project action buttons to handlers."""
        # New Project button
        self.new_project_button = self.builder.get_object('new_project_button')
        if self.new_project_button:
            self.new_project_button.connect('clicked', self._on_new_project_clicked)
        
        # Open Project button
        self.open_project_button = self.builder.get_object('open_project_button')
        if self.open_project_button:
            self.open_project_button.connect('clicked', self._on_open_project_clicked)
        
        # Project Settings button
        self.project_settings_button = self.builder.get_object('project_settings_button')
        if self.project_settings_button:
            self.project_settings_button.connect('clicked', self._on_project_settings_clicked)
        
        # Quit button
        self.quit_button = self.builder.get_object('quit_button')
        if self.quit_button:
            self.quit_button.connect('clicked', self._on_quit_clicked)
    
    # Button Click Handlers
    
    def _on_new_project_clicked(self, button):
        """Handle New Project button click."""
        print("[ProjectActions] New Project button clicked")
        try:
            project = self.dialog_manager.show_new_project_dialog()
            if project:
                print(f"[ProjectActions] Created project: {project.name} at {project.base_path}")
        except Exception as e:
            print(f"[ProjectActions] ERROR: Failed to show new project dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_open_project_clicked(self, button):
        """Handle Open Project button click."""
        project = self.dialog_manager.show_open_project_dialog()
        if project:
            print(f"Opened project: {project.name} from {project.base_path}")
    
    def _on_project_settings_clicked(self, button):
        """Handle Project Settings button click."""
        if self.project_manager.current_project:
            saved = self.dialog_manager.show_project_properties_dialog()
            if saved:
                print("Project properties saved")
        else:
            print("Warning: No current project to show settings for")
    
    def _on_quit_clicked(self, button):
        """Handle Quit button click."""
        # Check for unsaved changes
        # TODO: Implement proper unsaved changes detection
        
        if self.on_quit_requested:
            # Let the owner handle quit (e.g., main window)
            self.on_quit_requested()
        else:
            # Default: quit immediately
            Gtk.main_quit()
    
    # Project Lifecycle Callbacks (from DialogManager)
    
    def _on_project_created(self, project):
        """Called when a project is created.
        
        Args:
            project: The newly created Project instance
        """
        # Enable project settings button
        if self.project_settings_button:
            self.project_settings_button.set_sensitive(True)
        
        # Notify external callback
        if self.on_project_created:
            self.on_project_created(project)
    
    def _on_project_opened(self, project):
        """Called when a project is opened.
        
        Args:
            project: The opened Project instance
        """
        # Enable project settings button
        if self.project_settings_button:
            self.project_settings_button.set_sensitive(True)
        
        # Notify external callback
        if self.on_project_opened:
            self.on_project_opened(project)
    
    def _on_project_closed(self):
        """Called when a project is closed."""
        # Disable project settings button
        if self.project_settings_button:
            self.project_settings_button.set_sensitive(False)
        
        # Notify external callback
        if self.on_project_closed:
            self.on_project_closed()
    
    # Public Methods (API for integration)
    
    def set_parent_window(self, window):
        """Update parent window reference.
        
        Args:
            window: New parent window for dialogs
        """
        self.parent_window = window
        if self.dialog_manager:
            self.dialog_manager.parent_window = window
    
    def update_project_state(self, has_project):
        """Update UI state based on whether a project is open.
        
        Args:
            has_project: True if a project is currently open
        """
        if self.project_settings_button:
            self.project_settings_button.set_sensitive(has_project)
    
    def get_current_project(self):
        """Get the current active project.
        
        Returns:
            Project instance or None
        """
        return self.project_manager.current_project
    
    def close_current_project(self, save=True):
        """Close the current project.
        
        Args:
            save: Whether to save before closing
        """
        self.project_manager.close_current_project(save=save)
        self._on_project_closed()


def create_project_actions_controller(builder, parent_window=None):
    """Factory function to create a ProjectActionsController.
    
    Args:
        builder: Gtk.Builder with loaded UI
        parent_window: Parent window for dialogs
        
    Returns:
        ProjectActionsController instance
    """
    return ProjectActionsController(builder, parent_window)
