#!/usr/bin/env python3
"""Project Dialog Manager.

This module manages the project dialogs (New, Open, Properties) and handles
project operations like creating, opening, closing, and exporting projects.
"""

import os
import sys
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in project_dialog_manager:', e, file=sys.stderr)
    sys.exit(1)

from shypn.data.project_models import Project, get_project_manager


class ProjectDialogManager:
    """Manages project dialogs and operations."""
    
    def __init__(self, parent_window=None, ui_path=None):
        """Initialize the dialog manager.
        
        Args:
            parent_window: Parent window for dialogs
            ui_path: Path to project_dialogs.ui file
        """
        self.parent_window = parent_window
        self.project_manager = get_project_manager()
        
        # Determine UI path
        if ui_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'dialogs', 'project_dialogs.ui')
        
        self.ui_path = ui_path
        self.builder = None
        
        # Callbacks
        self.on_project_opened = None  # Callback(project) when project is opened
        self.on_project_created = None  # Callback(project) when project is created
        self.on_project_closed = None  # Callback() when project is closed
    
    def _load_builder(self):
        """Load the UI builder if not already loaded."""
        if self.builder is None:
            if not os.path.exists(self.ui_path):
                raise FileNotFoundError(f"Project dialogs UI file not found: {self.ui_path}")
            self.builder = Gtk.Builder.new_from_file(self.ui_path)
    
    def show_new_project_dialog(self):
        """Show the New Project dialog.
        
        Returns:
            Project instance if created, None if cancelled
        """
        try:
            self._load_builder()
            
            dialog = self.builder.get_object('new_project_dialog')
            if not dialog:
                return None
            
            # Wayland compatibility: Always set parent (explicitly None if not available)
            parent = self.parent_window if self.parent_window else None
            if parent:
                dialog.set_transient_for(parent)
                dialog.set_modal(True)
            
            # Ensure dialog is realized before showing (Wayland fix)
            dialog.realize()
            dialog.show_all()
            
            # Get widgets
            name_entry = self.builder.get_object('new_project_name_entry')
            location_entry = self.builder.get_object('new_project_location_entry')
            description_text = self.builder.get_object('new_project_description_text')
            create_button = self.builder.get_object('new_project_create_button')
            
            # Set default location
            location_entry.set_text(self.project_manager.projects_root)
            
            # Set create button as default
            create_button.grab_default()
            
            # Focus on name entry
            name_entry.grab_focus()
            
            # Run dialog
            try:
                response = dialog.run()
            except Exception as e:
                import traceback
                traceback.print_exc()
                dialog.hide()
                raise
            
            project = None
            if response == Gtk.ResponseType.OK:
                # Get values
                name = name_entry.get_text().strip()
                
                description_buffer = description_text.get_buffer()
                start, end = description_buffer.get_bounds()
                description = description_buffer.get_text(start, end, False).strip()
                
                if not name:
                    name = "Untitled Project"
                
                # Create project (empty - users import data via KEGG/SBML panels)
                try:
                    project = self.project_manager.create_project(
                        name=name,
                        description=description
                    )
                    
                    # Set as current project
                    self.project_manager.current_project = project
                    
                    # Notify callback
                    if self.on_project_created:
                        self.on_project_created(project)
                        
                except Exception as e:
                    # Show error dialog
                    error_dialog = Gtk.MessageDialog(
                        transient_for=dialog,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Failed to create project"
                    )
                    error_dialog.format_secondary_text(str(e))
                    error_dialog.run()
                    error_dialog.destroy()
                    project = None
            
            dialog.hide()
            return project
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None
    
    def show_open_project_dialog(self):
        """Show the Open Project dialog.
        
        Returns:
            Project instance if opened, None if cancelled
        """
        self._load_builder()
        
        dialog = self.builder.get_object('open_project_dialog')
        # Wayland compatibility: Always set parent (explicitly None if not available)
        parent = self.parent_window if self.parent_window else None
        if parent:
            dialog.set_transient_for(parent)
        
        # Get widgets
        notebook = self.builder.get_object('open_project_notebook')
        recent_tree = self.builder.get_object('recent_projects_tree')
        browse_chooser = self.builder.get_object('browse_project_chooser')
        browse_info = self.builder.get_object('browse_project_info')
        import_chooser = self.builder.get_object('import_archive_chooser')
        import_info = self.builder.get_object('import_archive_info')
        open_button = self.builder.get_object('open_project_open_button')
        
        # Setup recent projects tree
        self._setup_recent_projects_tree(recent_tree, open_button)
        
        # Setup browse tab
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Shypn Projects")
        file_filter.add_pattern("*.shy")
        browse_chooser.add_filter(file_filter)
        
        def on_browse_file_set(chooser):
            filename = chooser.get_filename()
            if filename:
                browse_info.set_text(f"Selected: {filename}")
                open_button.set_sensitive(True)
            else:
                browse_info.set_text("No file selected")
                open_button.set_sensitive(False)
        
        browse_chooser.connect('file-set', on_browse_file_set)
        
        # Setup import archive tab
        archive_filter = Gtk.FileFilter()
        archive_filter.set_name("ZIP Archives")
        archive_filter.add_pattern("*.zip")
        import_chooser.add_filter(archive_filter)
        
        def on_import_file_set(chooser):
            filename = chooser.get_filename()
            if filename:
                import_info.set_text(f"Selected: {filename}")
                open_button.set_sensitive(True)
            else:
                import_info.set_text("No archive selected")
                open_button.set_sensitive(False)
        
        import_chooser.connect('file-set', on_import_file_set)
        
        # Run dialog
        response = dialog.run()
        
        project = None
        if response == Gtk.ResponseType.OK:
            active_tab = notebook.get_current_page()
            
            try:
                if active_tab == 0:  # Recent Projects
                    # Get selected project
                    selection = recent_tree.get_selection()
                    model, tree_iter = selection.get_selected()
                    if tree_iter:
                        project_id = model.get_value(tree_iter, 3)  # Hidden ID column
                        project = self.project_manager.open_project(project_id)
                
                elif active_tab == 1:  # Browse
                    filename = browse_chooser.get_filename()
                    if filename:
                        project = self.project_manager.open_project_by_path(filename)
                
                elif active_tab == 2:  # Import Archive
                    filename = import_chooser.get_filename()
                    if filename:
                        # TODO: Implement import from archive
                        error_dialog = Gtk.MessageDialog(
                            transient_for=dialog,
                            message_type=Gtk.MessageType.INFO,
                            buttons=Gtk.ButtonsType.OK,
                            text="Import Archive Not Yet Implemented"
                        )
                        error_dialog.format_secondary_text(
                            "Archive import will be implemented in Phase 7.\n"
                            "For now, please extract the archive manually and use Browse."
                        )
                        error_dialog.run()
                        error_dialog.destroy()
                
                if project and self.on_project_opened:
                    self.on_project_opened(project)
                    
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=dialog,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Failed to open project"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
                project = None
        
        dialog.hide()
        return project
    
    def _setup_recent_projects_tree(self, tree_view, open_button):
        """Setup the recent projects tree view.
        
        Args:
            tree_view: GtkTreeView widget
            open_button: Open button to enable when selection changes
        """
        # Clear existing columns
        for col in tree_view.get_columns():
            tree_view.remove_column(col)
        
        # Create columns: Name, Location, Last Modified, ID (hidden)
        renderer = Gtk.CellRendererText()
        
        col_name = Gtk.TreeViewColumn("Name", renderer, text=0)
        col_name.set_sort_column_id(0)
        tree_view.append_column(col_name)
        
        col_location = Gtk.TreeViewColumn("Location", renderer, text=1)
        col_location.set_sort_column_id(1)
        tree_view.append_column(col_location)
        
        col_modified = Gtk.TreeViewColumn("Last Modified", renderer, text=2)
        col_modified.set_sort_column_id(2)
        tree_view.append_column(col_modified)
        
        # Create model: Name, Location, Modified, ID (hidden)
        list_store = Gtk.ListStore(str, str, str, str)
        
        # Populate with recent projects
        for project_info in self.project_manager.get_recent_projects_info():
            list_store.append([
                project_info['name'],
                project_info['path'],
                project_info['modified_date'][:10],  # Just date part
                project_info['id']
            ])
        
        tree_view.set_model(list_store)
        
        # Enable open button when row is selected
        def on_selection_changed(selection):
            model, tree_iter = selection.get_selected()
            open_button.set_sensitive(tree_iter is not None)
        
        selection = tree_view.get_selection()
        selection.connect('changed', on_selection_changed)
        
        # Double-click to open
        def on_row_activated(tree_view, path, column):
            # Trigger OK response
            dialog = tree_view.get_toplevel()
            dialog.response(Gtk.ResponseType.OK)
        
        tree_view.connect('row-activated', on_row_activated)
    
    def show_project_properties_dialog(self, project=None):
        """Show the Project Properties dialog.
        
        Args:
            project: Project to show properties for (default: current project)
            
        Returns:
            True if changes were saved, False otherwise
        """
        if project is None:
            project = self.project_manager.current_project
        
        if project is None:
            return False
        
        self._load_builder()
        
        dialog = self.builder.get_object('project_properties_dialog')
        # Wayland compatibility: Always set parent (explicitly None if not available)
        parent = self.parent_window if self.parent_window else None
        if parent:
            dialog.set_transient_for(parent)
        
        # Get widgets
        name_entry = self.builder.get_object('props_project_name_entry')
        location_label = self.builder.get_object('props_project_location_label')
        created_label = self.builder.get_object('props_project_created_label')
        modified_label = self.builder.get_object('props_project_modified_label')
        description_text = self.builder.get_object('props_project_description_text')
        content_summary = self.builder.get_object('props_content_summary_label')
        
        # Populate fields
        name_entry.set_text(project.name)
        location_label.set_text(project.base_path or "N/A")
        created_label.set_text(project.created_date[:10])
        modified_label.set_text(project.modified_date[:10])
        
        description_buffer = description_text.get_buffer()
        description_buffer.set_text(project.description)
        
        # Update content summary
        num_models = len(project.models)
        num_pathways = len(project.pathways)
        num_simulations = len(project.simulations)
        summary_text = f"Project contains:\n• {num_models} model(s)\n• {num_pathways} pathway(s)\n• {num_simulations} simulation(s)"
        content_summary.set_text(summary_text)
        
        # Run dialog
        response = dialog.run()
        
        saved = False
        if response == Gtk.ResponseType.OK:
            # Save changes
            project.name = name_entry.get_text().strip()
            
            start, end = description_buffer.get_bounds()
            project.description = description_buffer.get_text(start, end, False).strip()
            
            project.update_modified_date()
            
            try:
                project.save()
                
                # Update index
                if project.id in self.project_manager.project_index:
                    self.project_manager.project_index[project.id]['name'] = project.name
                    self.project_manager.project_index[project.id]['modified_date'] = project.modified_date
                    self.project_manager.save_index()
                
                saved = True
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=dialog,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Failed to save project"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.hide()
        return saved
    
    def confirm_close_with_unsaved_changes(self, unsaved_files=None):
        """Show confirmation dialog for closing with unsaved changes.
        
        Args:
            unsaved_files: List of unsaved file names (optional)
            
        Returns:
            'save', 'discard', or 'cancel'
        """
        if unsaved_files is None:
            unsaved_files = []
        
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Unsaved Changes"
        )
        
        if unsaved_files:
            file_list = "\n".join([f"  • {f}" for f in unsaved_files])
            secondary_text = f"You have unsaved changes in:\n{file_list}\n\nWhat would you like to do?"
        else:
            secondary_text = "You have unsaved changes.\n\nWhat would you like to do?"
        
        dialog.format_secondary_text(secondary_text)
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Discard Changes", Gtk.ResponseType.NO)
        dialog.add_button("Save & Close", Gtk.ResponseType.YES)
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            return 'save'
        elif response == Gtk.ResponseType.NO:
            return 'discard'
        else:
            return 'cancel'
    
    def confirm_delete_project(self, project_name: str, delete_files: bool = False) -> str:
        """Show confirmation dialog for project deletion with safety measures.
        
        Args:
            project_name: Name of project to delete
            delete_files: Whether files will be permanently deleted
            
        Returns:
            'delete': Confirmed deletion
            'archive': User chose to archive instead
            'cancel': User cancelled
        """
        if delete_files:
            # CRITICAL: Multiple confirmations for permanent deletion
            
            # First dialog: Offer safer alternatives
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text=f"⚠️ Delete Project '{project_name}'?"
            )
            
            dialog.format_secondary_text(
                "Permanent deletion cannot be undone!\n\n"
                "What would you like to do?"
            )
            
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Archive (Keep Backup)", Gtk.ResponseType.NO)
            delete_button = dialog.add_button("Delete Forever", Gtk.ResponseType.YES)
            
            # Style delete button as dangerous
            delete_context = delete_button.get_style_context()
            delete_context.add_class("destructive-action")
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.CANCEL:
                return 'cancel'
            elif response == Gtk.ResponseType.NO:
                return 'archive'  # User chose safer option
            
            # Second dialog: Require typing project name to confirm
            confirm_dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.NONE,
                text="⚠️ FINAL CONFIRMATION"
            )
            
            confirm_dialog.format_secondary_text(
                f"You are about to PERMANENTLY DELETE all files in:\n"
                f"'{project_name}'\n\n"
                f"This action CANNOT be undone!\n\n"
                f"Type the project name exactly to confirm:"
            )
            
            # Add entry for name confirmation
            content_area = confirm_dialog.get_content_area()
            entry = Gtk.Entry()
            entry.set_placeholder_text(project_name)
            entry.set_activates_default(True)
            content_area.pack_start(entry, False, False, 6)
            
            confirm_dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            final_delete_button = confirm_dialog.add_button(
                "Delete Forever", 
                Gtk.ResponseType.YES
            )
            final_delete_button.get_style_context().add_class("destructive-action")
            final_delete_button.set_can_default(True)
            final_delete_button.grab_default()
            
            confirm_dialog.show_all()
            response = confirm_dialog.run()
            confirmed_name = entry.get_text().strip()
            confirm_dialog.destroy()
            
            # Require exact name match
            if response == Gtk.ResponseType.YES and confirmed_name == project_name:
                return 'delete'
            else:
                return 'cancel'
        
        else:
            # Simple confirmation for index removal only (files remain)
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Remove '{project_name}' from list?"
            )
            
            dialog.format_secondary_text(
                "Project files will remain on disk.\n"
                "You can re-import the project later."
            )
            
            response = dialog.run()
            dialog.destroy()
            
            return 'delete' if response == Gtk.ResponseType.YES else 'cancel'
    
    def delete_or_archive_project(self, project_id: str, prefer_archive: bool = True) -> bool:
        """Delete or archive a project with user confirmation.
        
        This is the RECOMMENDED way to remove projects safely.
        
        Args:
            project_id: UUID of project to remove
            prefer_archive: If True, default to archiving (safer)
            
        Returns:
            True if project was removed, False if cancelled
        """
        if project_id not in self.project_manager.project_index:
            return False
        
        project_info = self.project_manager.project_index[project_id]
        project_name = project_info['name']
        
        # Show confirmation dialog
        action = self.confirm_delete_project(project_name, delete_files=not prefer_archive)
        
        if action == 'cancel':
            return False
        
        try:
            if action == 'archive':
                # SAFE: Archive project (keep backup)
                archive_path = self.project_manager.archive_project(project_id)
                
                # Show success message
                success_dialog = Gtk.MessageDialog(
                    transient_for=self.parent_window,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Project Archived Successfully"
                )
                success_dialog.format_secondary_text(
                    f"Project '{project_name}' has been archived to:\n{archive_path}\n\n"
                    f"You can restore it later by extracting the ZIP file."
                )
                success_dialog.run()
                success_dialog.destroy()
                return True
                
            elif action == 'delete':
                # DANGEROUS: Permanent deletion
                self.project_manager.delete_project(project_id, delete_files=True)
                
                # Show warning that deletion is complete
                success_dialog = Gtk.MessageDialog(
                    transient_for=self.parent_window,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="Project Deleted"
                )
                success_dialog.format_secondary_text(
                    f"Project '{project_name}' has been permanently deleted.\n"
                    f"This action cannot be undone."
                )
                success_dialog.run()
                success_dialog.destroy()
                return True
            
        except Exception as e:
            # Show error
            error_dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Operation Failed"
            )
            error_dialog.format_secondary_text(
                f"Failed to remove project '{project_name}':\n{str(e)}"
            )
            error_dialog.run()
            error_dialog.destroy()
            return False
        
        return False


def create_project_dialog_manager(parent_window=None, ui_path=None):
    """Convenience function to create a ProjectDialogManager.
    
    Args:
        parent_window: Parent window for dialogs
        ui_path: Optional path to project_dialogs.ui
        
    Returns:
        ProjectDialogManager instance
    """
    return ProjectDialogManager(parent_window, ui_path)
