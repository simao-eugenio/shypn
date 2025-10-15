"""NetObj Persistency - File operations for Petri net documents.

This module provides a clean separation of concerns for file operations,
cooperating with FileExplorer for file browser integration and DocumentModel
for document canvas integration.

Responsibilities:
    pass
- File save/load operations
- Dirty state tracking and management
- File path management
- User interaction dialogs (file chooser, confirmations)
- Error handling for file operations

Design Philosophy:
    pass
- Single Responsibility: handles ONLY file operations and dirty logic
- Cooperates with FileExplorer for file system operations
- Cooperates with DocumentModel for document serialization
- NOT responsible for: UI loading, canvas rendering, object creation
"""
import os
import sys
from typing import Optional, Callable
from pathlib import Path
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK3 not available in netobj_persistency: {e}', file=sys.stderr)
    sys.exit(1)

class NetObjPersistency:
    """Handles file operations for Petri net documents.
    
    This class manages:
        pass
    - Saving documents to JSON files
    - Loading documents from JSON files
    - Tracking dirty state (unsaved changes)
    - File path management
    - User interaction for file operations
    
    It cooperates with:
        pass
    - FileExplorer: for file system navigation
    - DocumentModel: for document serialization
    - Canvas managers: for getting current document
    
    Attributes:
        current_filepath: Path to currently open file (None if unsaved)
        is_dirty: Whether document has unsaved changes
        parent_window: Parent window for dialogs
        on_file_saved: Callback(filepath) when file is saved
        on_file_loaded: Callback(filepath, document) when file is loaded
        on_dirty_changed: Callback(is_dirty) when dirty state changes
    """

    def __init__(self, parent_window: Optional[Gtk.Window]=None, models_directory: Optional[str]=None):
        """Initialize file persistence manager.
        
        Args:
            parent_window: Parent window for dialogs (optional)
            models_directory: Root directory for Petri net models (default: uses ProjectManager)
        """
        self.parent_window = parent_window
        self.current_filepath: Optional[str] = None
        self._is_dirty: bool = False
        self.on_file_saved: Optional[Callable[[str], None]] = None
        self.on_file_loaded: Optional[Callable[[str, any], None]] = None
        self.on_dirty_changed: Optional[Callable[[bool], None]] = None
        
        # Determine models directory
        if models_directory is None:
            # Try to use current project's models directory
            try:
                from shypn.data.project_models import ProjectManager
                manager = ProjectManager()
                
                if manager.current_project:
                    # Use current project's models directory
                    models_directory = manager.current_project.get_models_dir()
                else:
                    # No active project - use repo root's models/ directory as fallback
                    # This allows users to open files from the legacy models/ folder
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
                    models_directory = os.path.join(repo_root, 'models')
            except Exception:
                # Fallback if ProjectManager not available - use repo root's models/ directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
                models_directory = os.path.join(repo_root, 'models')
        
        self.models_directory = models_directory
        if not os.path.exists(self.models_directory):
            try:
                os.makedirs(self.models_directory)
            except Exception as e:
                pass
        self._last_directory: Optional[str] = self.models_directory
        
        # Suggested filename for save dialog (used for imported documents)
        self.suggested_filename: Optional[str] = None

    def update_models_directory_from_project(self) -> None:
        """Update models directory based on current project.
        
        Call this method when the active project changes to ensure
        save/load dialogs open in the correct project directory.
        """
        try:
            from shypn.data.project_models import ProjectManager
            manager = ProjectManager()
            
            if manager.current_project:
                # Use current project's models directory
                new_dir = manager.current_project.get_models_dir()
                if new_dir and os.path.exists(new_dir):
                    self.models_directory = new_dir
                    # Only update last_directory if user hasn't navigated elsewhere
                    if not self._last_directory or self._last_directory == self.models_directory:
                        self._last_directory = new_dir
            else:
                # No active project, use projects root
                self.models_directory = manager.projects_root
                if not self._last_directory:
                    self._last_directory = self.models_directory
        except Exception as e:
            # If ProjectManager not available, keep current directory
            pass

    @property
    def is_dirty(self) -> bool:
        """Check if document has unsaved changes.
        
        Returns:
            bool: True if document has unsaved changes
        """
        return self._is_dirty

    def mark_dirty(self) -> None:
        """Mark document as having unsaved changes."""
        if not self._is_dirty:
            self._is_dirty = True
            if self.on_dirty_changed:
                self.on_dirty_changed(True)

    def mark_clean(self) -> None:
        """Mark document as having no unsaved changes."""
        if self._is_dirty:
            self._is_dirty = False
            if self.on_dirty_changed:
                self.on_dirty_changed(False)

    def set_filepath(self, filepath: Optional[str]) -> None:
        """Set the current file path.
        
        Args:
            filepath: Path to file, or None for new unsaved document
        """
        self.current_filepath = filepath
        if filepath:
            self._last_directory = os.path.dirname(filepath)

    def has_filepath(self) -> bool:
        """Check if document has an associated file path.
        
        Returns:
            bool: True if document has been saved to a file
        """
        return self.current_filepath is not None

    def get_display_name(self) -> str:
        """Get display name for current document.
        
        Returns:
            str: Filename if saved, "Untitled" if new document
        """
        if self.current_filepath:
            return os.path.basename(self.current_filepath)
        return 'Untitled'

    def get_title(self) -> str:
        """Get window title for current document.
        
        Returns:
            str: Title with dirty indicator (e.g., "*Untitled" or "model.json")
        """
        name = self.get_display_name()
        if self.is_dirty:
            return f'*{name}'
        return name

    def save_document(self, document, save_as: bool=False, is_default_filename: bool=False) -> bool:
        """Save document to file.
        
        The is_default_filename flag acts as a signal throughout the system that
        the document is in an unsaved/new state and should always prompt for a filename.
        
        Behavior:
            pass
        - If is_default_filename=True: ALWAYS show file chooser (even with existing filepath)
        - If save_as=True: ALWAYS show file chooser (Save As operation)
        - If document has NO filepath: Show file chooser dialog
        - Otherwise: Save directly to existing file
        
        The file chooser pre-fills with "default.shy" for new documents.
        
        Args:
            document: DocumentModel instance to save
            save_as: If True, always prompt for filename (Save As)
            is_default_filename: If True, document has "default" filename (always prompt)
            
        Returns:
            bool: True if save successful, False if cancelled or error
        """
        needs_prompt = save_as or not self.has_filepath() or is_default_filename
        if needs_prompt:
            filepath = self._show_save_dialog()
            if not filepath:
                return False
            self.set_filepath(filepath)
        try:
            document.save_to_file(self.current_filepath)
            self.mark_clean()
            if self.on_file_saved:
                self.on_file_saved(self.current_filepath)
            self._show_success_dialog('File saved successfully', f'Saved to:\n{self.current_filepath}')
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error_dialog('Error saving file', str(e))
            return False

    def load_document(self):
        """Load document from file.
        
        Shows file chooser dialog and loads the selected file.
        
        Returns:
            tuple: (document, filepath) if successful, (None, None) if cancelled/error
        """
        filepath = self._show_open_dialog()
        if not filepath:
            return (None, None)
        try:
            from shypn.data.canvas.document_model import DocumentModel
            document = DocumentModel.load_from_file(filepath)
            self.set_filepath(filepath)
            self.mark_clean()
            if self.on_file_loaded:
                self.on_file_loaded(filepath, document)
            self._show_success_dialog('File loaded successfully', f'Loaded from:\n{filepath}\n\n' + f'Places: {len(document.places)}\n' + f'Transitions: {len(document.transitions)}\n' + f'Arcs: {len(document.arcs)}')
            return (document, filepath)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error_dialog('Error loading file', str(e))
            return (None, None)

    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user if needed.
        
        Shows a dialog asking user to save, discard, or cancel.
        
        Returns:
            bool: True if operation should continue (saved or discarded),
                  False if user cancelled
        """
        if not self.is_dirty:
            return True
        # Ensure parent window is set (fixes Wayland crash)
        parent = self.parent_window if self.parent_window else None
        dialog = Gtk.MessageDialog(parent=parent, modal=True, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.NONE, text='Unsaved changes')
        dialog.format_secondary_text(f"Document '{self.get_display_name()}' has unsaved changes.\n" + 'Do you want to save before continuing?')
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Discard Changes', Gtk.ResponseType.NO)
        dialog.add_button('Save', Gtk.ResponseType.YES)
        dialog.set_default_response(Gtk.ResponseType.YES)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            return True
        elif response == Gtk.ResponseType.NO:
            return True
        else:
            return False

    def new_document(self) -> bool:
        """Create a new document (check for unsaved changes first).
        
        Returns:
            bool: True if operation should continue, False if cancelled
        """
        if not self.check_unsaved_changes():
            return False
        self.set_filepath(None)
        self.mark_clean()
        return True

    def _show_save_dialog(self) -> Optional[str]:
        """Show save file chooser dialog.
        
        Returns:
            str: Selected filepath, or None if cancelled
        """
        # Ensure parent window is set (fixes Wayland crash)
        parent = self.parent_window if self.parent_window else None
        dialog = Gtk.FileChooserDialog(title='Save Petri Net', parent=parent, action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_do_overwrite_confirmation(True)
        filter_shy = Gtk.FileFilter()
        filter_shy.set_name('SHYpn Petri Net files (*.shy)')
        filter_shy.add_pattern('*.shy')
        dialog.add_filter(filter_shy)
        filter_all = Gtk.FileFilter()
        filter_all.set_name('All files')
        filter_all.add_pattern('*')
        dialog.add_filter(filter_all)
        if self._last_directory and os.path.isdir(self._last_directory):
            dialog.set_current_folder(self._last_directory)
        elif os.path.isdir(self.models_directory):
            dialog.set_current_folder(self.models_directory)
        if self.current_filepath:
            dialog.set_filename(self.current_filepath)
        else:
            # Use suggested filename if available (e.g., for imported documents)
            if self.suggested_filename:
                default_name = f'{self.suggested_filename}.shy'
            else:
                default_name = 'default.shy'
            dialog.set_current_name(default_name)
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        if response != Gtk.ResponseType.OK or not filepath:
            return None
        if not filepath.endswith('.shy'):
            filepath += '.shy'
        filename = os.path.basename(filepath)
        if filename.lower() == 'default.shy':
            warning_dialog = Gtk.MessageDialog(parent=parent, modal=True, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.YES_NO, text="Save as 'default.shy'?")
            warning_dialog.format_secondary_text("You are about to save with the default filename 'default.shy'.\n\nThis may overwrite existing default files or make it hard to identify this model later.\n\nDo you want to continue with this filename?")
            warning_response = warning_dialog.run()
            warning_dialog.destroy()
            if warning_response != Gtk.ResponseType.YES:
                return self._show_save_dialog()
        self._last_directory = os.path.dirname(filepath)
        return filepath

    def _show_open_dialog(self) -> Optional[str]:
        """Show open file chooser dialog.
        
        Returns:
            str: Selected filepath, or None if cancelled
        """
        # Ensure parent window is set (fixes Wayland crash)
        parent = self.parent_window if self.parent_window else None
        dialog = Gtk.FileChooserDialog(title='Open Petri Net', parent=parent, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter_shy = Gtk.FileFilter()
        filter_shy.set_name('SHYpn Petri Net files (*.shy)')
        filter_shy.add_pattern('*.shy')
        dialog.add_filter(filter_shy)
        filter_all = Gtk.FileFilter()
        filter_all.set_name('All files')
        filter_all.add_pattern('*')
        dialog.add_filter(filter_all)
        if self._last_directory and os.path.isdir(self._last_directory):
            dialog.set_current_folder(self._last_directory)
        elif os.path.isdir(self.models_directory):
            dialog.set_current_folder(self.models_directory)
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        if response != Gtk.ResponseType.OK or not filepath:
            return None
        self._last_directory = os.path.dirname(filepath)
        return filepath

    def _show_success_dialog(self, title: str, message: str) -> None:
        """Show success message dialog.
        
        Args:
            title: Dialog title
            message: Message text
        """
        # Ensure parent window is set (fixes Wayland crash)
        parent = self.parent_window if self.parent_window else None
        dialog = Gtk.MessageDialog(parent=parent, modal=True, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _show_error_dialog(self, title: str, message: str) -> None:
        """Show error message dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        # Ensure parent window is set (fixes Wayland crash)
        parent = self.parent_window if self.parent_window else None
        dialog = Gtk.MessageDialog(parent=parent, modal=True, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

def create_persistency_manager(parent_window: Optional[Gtk.Window]=None, models_directory: Optional[str]=None) -> NetObjPersistency:
    """Convenience function to create a persistence manager.
    
    The manager automatically detects the current project and uses its models directory.
    If no project is active, it uses the workspace/projects root.
    
    Args:
        parent_window: Parent window for dialogs
        models_directory: Root directory for models (default: auto-detect from ProjectManager)
        
    Returns:
        NetObjPersistency: The persistence manager instance
        
    Example:
        persistency = create_persistency_manager(main_window)
        
        # Save dialog opens in current project's models directory
        success = persistency.save_document(document)
        
        # Load dialog opens in current project's models directory
        document, filepath = persistency.load_document()
        
        # Update directory when project changes
        persistency.update_models_directory_from_project()
    """
    return NetObjPersistency(parent_window, models_directory)