#!/usr/bin/env python3
"""Export toolbar for report panel.

Provides buttons for document generation, metadata management,
and user profile configuration.

Author: Simão Eugénio
Date: 2025-11-15
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
from typing import Optional, Callable

# Import from top-level shypn.reporting module
import sys
from pathlib import Path
# Get to src/shypn level
module_path = Path(__file__).parent.parent.parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

from shypn.reporting import ModelMetadata, UserProfile, MetadataStorage
from shypn.reporting import MetadataDialog, ProfileDialog


class ExportToolbar(Gtk.Box):
    """Toolbar for document export and metadata management.
    
    Provides buttons for:
    - Metadata editing (opens MetadataDialog)
    - User profile management (opens ProfileDialog)
    - PDF export
    - Excel export
    - HTML export
    """
    
    def __init__(self, parent_window: Optional[Gtk.Window] = None):
        """Initialize export toolbar.
        
        Args:
            parent_window: Parent window for modal dialogs
        """
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.parent_window = parent_window
        self.current_filepath = None  # Will be set when file is loaded
        self.metadata = None  # Current model metadata
        self.profile = UserProfile.load()  # Load user profile
        
        # Callbacks for composition (future refactoring)
        self.get_model_callback = None  # Callback to get current model
        self.get_file_info_callback = None  # Callback to get file info
        
        # Set margins
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build toolbar UI."""
        # Left side - Metadata management
        metadata_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        
        # Metadata button
        self.metadata_btn = Gtk.Button(label="📝 Metadata")
        self.metadata_btn.set_tooltip_text("Edit model metadata")
        self.metadata_btn.connect('clicked', self._on_edit_metadata)
        metadata_box.pack_start(self.metadata_btn, False, False, 0)
        
        # Profile button
        self.profile_btn = Gtk.Button(label="👤 Profile")
        self.profile_btn.set_tooltip_text("Manage user profile")
        self.profile_btn.connect('clicked', self._on_edit_profile)
        metadata_box.pack_start(self.profile_btn, False, False, 0)
        
        self.pack_start(metadata_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 6)
        
        # Right side - Export buttons
        export_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        
        # PDF export
        self.pdf_btn = Gtk.Button(label="📤 PDF")
        self.pdf_btn.set_tooltip_text("Export report as PDF")
        self.pdf_btn.connect('clicked', self._on_export_pdf)
        export_box.pack_start(self.pdf_btn, False, False, 0)
        
        # Excel export
        self.excel_btn = Gtk.Button(label="📊 Excel")
        self.excel_btn.set_tooltip_text("Export data as Excel workbook")
        self.excel_btn.connect('clicked', self._on_export_excel)
        export_box.pack_start(self.excel_btn, False, False, 0)
        
        # HTML export
        self.html_btn = Gtk.Button(label="🌐 HTML")
        self.html_btn.set_tooltip_text("Export report as HTML")
        self.html_btn.connect('clicked', self._on_export_html)
        export_box.pack_start(self.html_btn, False, False, 0)
        
        self.pack_end(export_box, False, False, 0)
    
    def set_parent_window(self, window: Gtk.Window):
        """Set parent window for dialogs.
        
        Args:
            window: Parent window
        """
        self.parent_window = window
    
    def set_filepath(self, filepath: str):
        """Set current file path for metadata storage.
        
        Args:
            filepath: Path to .shypn file
        """
        self.current_filepath = filepath
        # Load metadata from file if exists
        if filepath:
            loaded_metadata = MetadataStorage.load_from_shypn_file(filepath)
            if loaded_metadata:
                self.metadata = loaded_metadata
            else:
                # Initialize empty metadata
                self.metadata = ModelMetadata()
    
    def set_model_callback(self, callback: Callable):
        """Set callback to get current model for composition.
        
        Future refactoring: Will auto-populate metadata from model.
        
        Args:
            callback: Function that returns current model object
        """
        self.get_model_callback = callback
    
    def set_file_info_callback(self, callback: Callable):
        """Set callback to get file info for composition.
        
        Future refactoring: Will auto-populate metadata from file info.
        
        Args:
            callback: Function that returns (filepath, import_source)
        """
        self.get_file_info_callback = callback
    
    def _on_edit_metadata(self, button):
        """Handle metadata edit button click."""
        # Ensure we have a parent window
        if not self.parent_window:
            self.parent_window = self.get_toplevel()
        
        # Initialize metadata if needed
        if not self.metadata:
            self.metadata = ModelMetadata()
            
            # Future: Auto-populate from model and file info
            # if self.get_model_callback:
            #     model = self.get_model_callback()
            #     if model:
            #         self.metadata = MetadataStorage.initialize_metadata_from_model(
            #             self.current_filepath or "", model
            #         )
        
        # Open dialog
        dialog = MetadataDialog(self.parent_window, self.metadata)
        result = dialog.get_metadata()
        dialog.destroy()
        
        # Save if OK was clicked
        if result:
            self.metadata = result
            
            # Save to file if we have a filepath
            if self.current_filepath:
                success = MetadataStorage.save_to_shypn_file(self.current_filepath, self.metadata)
                if success:
                    self._show_info("Metadata Saved", "Metadata has been saved to the model file.")
                else:
                    self._show_error("Save Failed", "Failed to save metadata to file.")
            else:
                # No file yet - metadata will be saved when file is saved
                self._show_info("Metadata Updated", 
                              "Metadata updated. Will be saved when you save the model file.")
    
    def _on_edit_profile(self, button):
        """Handle profile edit button click."""
        # Ensure we have a parent window
        if not self.parent_window:
            self.parent_window = self.get_toplevel()
        
        # Open dialog
        dialog = ProfileDialog(self.parent_window, self.profile)
        result = dialog.get_profile()
        dialog.destroy()
        
        # Update if OK was clicked (dialog auto-saves to disk)
        if result:
            self.profile = result
            self._show_info("Profile Saved", "User profile has been saved.")
    
    def _on_export_pdf(self, button):
        """Handle PDF export button click."""
        # TODO: Implement PDF generator (Phase 4)
        self._show_todo("PDF Export", 
                       "PDF export will be implemented in Phase 4 using WeasyPrint.")
    
    def _on_export_excel(self, button):
        """Handle Excel export button click."""
        # TODO: Implement Excel generator (Phase 4)
        self._show_todo("Excel Export",
                       "Excel export will be implemented in Phase 4 using openpyxl.")
    
    def _on_export_html(self, button):
        """Handle HTML export button click."""
        # For now, trigger the existing HTML export from parent
        # This will be refactored in Phase 4 to use the new generator system
        self._show_info("HTML Export",
                       "Please use the existing HTML export button in the report panel.\n"
                       "Will be integrated into this toolbar in Phase 4.")
    
    def _show_info(self, title: str, message: str):
        """Show info dialog.
        
        Args:
            title: Dialog title
            message: Info message
        """
        parent = self.parent_window or self.get_toplevel()
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_error(self, title: str, message: str):
        """Show error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        parent = self.parent_window or self.get_toplevel()
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_todo(self, title: str, message: str):
        """Show TODO dialog for not-yet-implemented features.
        
        Args:
            title: Dialog title
            message: TODO message
        """
        parent = self.parent_window or self.get_toplevel()
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(f"Coming soon!\n\n{message}")
        dialog.run()
        dialog.destroy()
    
    def get_metadata(self) -> Optional[ModelMetadata]:
        """Get current metadata.
        
        Returns:
            Current ModelMetadata instance or None
        """
        return self.metadata
    
    def get_profile(self) -> UserProfile:
        """Get current user profile.
        
        Returns:
            Current UserProfile instance
        """
        return self.profile
