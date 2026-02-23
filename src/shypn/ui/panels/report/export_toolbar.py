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
from shypn.reporting.generators import (
    HTMLGenerator, PDFGenerator, ExcelGenerator, DocumentType
)


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
        self.parent_panel = None  # Will be set to ReportPanel instance
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
        self.metadata_btn = Gtk.Button(label="Metadata")
        self.metadata_btn.set_tooltip_text("Edit model metadata")
        self.metadata_btn.connect('clicked', self._on_edit_metadata)
        metadata_box.pack_start(self.metadata_btn, False, False, 0)
        
        # Profile button
        self.profile_btn = Gtk.Button(label="Profile")
        self.profile_btn.set_tooltip_text("Manage user profile")
        self.profile_btn.connect('clicked', self._on_edit_profile)
        metadata_box.pack_start(self.profile_btn, False, False, 0)
        
        self.pack_start(metadata_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 6)
        
        # Right side - Unified export controls
        export_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Export format label
        format_label = Gtk.Label(label="Export to:")
        format_label.set_tooltip_text("Select export format")
        export_box.pack_start(format_label, False, False, 0)
        
        # Export format combo
        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append_text("PDF")
        self.format_combo.append_text("Excel")
        self.format_combo.append_text("HTML")
        self.format_combo.append_text("LaTeX")
        self.format_combo.set_active(0)  # Default to PDF
        self.format_combo.set_tooltip_text("Choose export format:\n• PDF - Portable document\n• Excel - Structured workbook\n• HTML - Web document\n• LaTeX - Scientific typesetting")
        export_box.pack_start(self.format_combo, False, False, 0)
        
        # Export button
        self.export_btn = Gtk.Button(label="Export")
        self.export_btn.set_tooltip_text("Export report in selected format")
        self.export_btn.connect('clicked', self._on_export)
        export_box.pack_start(self.export_btn, False, False, 0)
        
        self.pack_end(export_box, False, False, 0)
        
        # Separator before simulation export
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.pack_end(separator2, False, False, 6)
        
        # Simulation data export button
        sim_export_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.sim_export_btn = Gtk.Button(label="Export Simulation Data")
        self.sim_export_btn.set_tooltip_text("Export time-series simulation data (CSV/JSON/Plots)")
        self.sim_export_btn.connect('clicked', self._on_export_simulation_data)
        self.sim_export_btn.set_sensitive(False)  # Initially disabled
        sim_export_box.pack_start(self.sim_export_btn, False, False, 0)
        self.pack_end(sim_export_box, False, False, 0)
    
    def set_parent_window(self, window: Gtk.Window):
        """Set parent window for dialogs.
        
        Args:
            window: Parent window
        """
        self.parent_window = window
    
    def set_parent_panel(self, panel):
        """Set parent ReportPanel for accessing category data.
        
        Args:
            panel: ReportPanel instance
        """
        self.parent_panel = panel
    
    def _collect_report_data(self) -> dict:
        """Collect structured data from all report categories.
        
        Returns:
            dict: Report data with keys 'model', 'dynamic', 'topology', 'provenance'
        """
        report_data = {}
        
        if self.parent_panel and hasattr(self.parent_panel, 'categories'):
            for category in self.parent_panel.categories:
                if hasattr(category, 'get_structured_data'):
                    data = category.get_structured_data()
                    # Map category titles to keys
                    title = data.get('title', '')
                    if 'Model' in title or 'MODELS' in title:
                        report_data['model'] = data
                    elif 'Dynamic' in title or 'DYNAMIC' in title:
                        report_data['dynamic'] = data
                    elif 'Topolog' in title or 'TOPOLOG' in title:
                        report_data['topology'] = data
                    elif 'Provenance' in title or 'PROVENANCE' in title:
                        report_data['provenance'] = data
        
        return report_data
    
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
    
    def _get_export_directory(self) -> str:
        """Get the appropriate directory for export dialogs.
        
        Returns the same directory where the model is saved:
        workspace/projects/<project_name>/models/<model_name>
        
        Returns:
            Absolute path to export directory
        """
        try:
            from shypn.data.project_models import ProjectManager
            manager = ProjectManager.get_instance()
            
            # If we have a current file path, use its directory
            if self.current_filepath:
                model_dir = Path(self.current_filepath).parent
                if model_dir.exists():
                    return str(model_dir)
            
            # Otherwise, use current project's models directory
            if manager.current_project:
                models_dir = manager.current_project.get_models_dir()
                if models_dir:
                    models_path = Path(models_dir)
                    models_path.mkdir(parents=True, exist_ok=True)
                    return str(models_path)
        except (OSError, PermissionError, AttributeError) as e:
            self.logger.debug(f"Failed to create or access models directory: {e}")
        
        # Fallback to workspace/projects/
        try:
            script_dir = Path(__file__).parent
            repo_root = script_dir.parent.parent.parent.parent
            workspace_projects = repo_root / 'workspace' / 'projects'
            workspace_projects.mkdir(parents=True, exist_ok=True)
            return str(workspace_projects)
        except Exception:
            return str(Path.home())
    
    def _on_edit_metadata(self, button):
        """Handle metadata edit button click."""
        # Get the actual top-level window
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
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
        dialog = MetadataDialog(toplevel, self.metadata)
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
        # Get the actual top-level window
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        # Open dialog
        dialog = ProfileDialog(toplevel, self.profile)
        result = dialog.get_profile()
        dialog.destroy()
        
        # Update if OK was clicked (dialog auto-saves to disk)
        if result:
            self.profile = result
            self._show_info("Profile Saved", "User profile has been saved.")
    
    def _get_selected_format(self) -> str:
        """Get currently selected export format.
        
        Returns:
            Format name: 'PDF', 'Excel', 'HTML', or 'LaTeX'
        """
        return self.format_combo.get_active_text()
    
    def _get_file_extension(self, format_name: str) -> str:
        """Get file extension for format.
        
        Args:
            format_name: Export format name
            
        Returns:
            File extension including dot (e.g., '.pdf')
        """
        extensions = {
            "PDF": ".pdf",
            "Excel": ".xlsx",
            "HTML": ".html",
            "LaTeX": ".tex"
        }
        return extensions.get(format_name, ".pdf")
    
    def _get_file_filter(self, format_name: str) -> Gtk.FileFilter:
        """Get file filter for format.
        
        Args:
            format_name: Export format name
            
        Returns:
            GTK file filter
        """
        file_filter = Gtk.FileFilter()
        
        if format_name == "PDF":
            file_filter.set_name("PDF files")
            file_filter.add_mime_type("application/pdf")
            file_filter.add_pattern("*.pdf")
        elif format_name == "Excel":
            file_filter.set_name("Excel files")
            file_filter.add_mime_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            file_filter.add_pattern("*.xlsx")
        elif format_name == "HTML":
            file_filter.set_name("HTML files")
            file_filter.add_mime_type("text/html")
            file_filter.add_pattern("*.html")
        elif format_name == "LaTeX":
            file_filter.set_name("LaTeX files")
            file_filter.add_mime_type("text/x-tex")
            file_filter.add_pattern("*.tex")
        else:
            file_filter.set_name("All files")
            file_filter.add_pattern("*")
        
        return file_filter
    
    def _create_generator(self, format_name: str):
        """Create appropriate generator for format.
        
        Args:
            format_name: Export format name
            
        Returns:
            Generator instance (HTMLGenerator, PDFGenerator, etc.)
        """
        if format_name == "PDF":
            return PDFGenerator(self.metadata, self.profile)
        elif format_name == "Excel":
            return ExcelGenerator(self.metadata, self.profile)
        elif format_name == "HTML":
            return HTMLGenerator(self.metadata, self.profile)
        elif format_name == "LaTeX":
            # Import LaTeX generator when implemented
            try:
                from shypn.reporting.generators import LaTeXGenerator
                return LaTeXGenerator(self.metadata, self.profile)
            except ImportError:
                self._show_error("LaTeX Not Available", 
                               "LaTeX export is not yet implemented.")
                return None
        else:
            return None
    
    def _on_export(self, button):
        """Handle unified export with selected format."""
        # Validate metadata
        if not self.metadata:
            self._show_error("No Metadata", 
                           "Please edit metadata first before exporting.")
            return
        
        # Get selected format
        format_name = self._get_selected_format()
        if not format_name:
            self._show_error("No Format Selected", 
                           "Please select an export format.")
            return
        
        # Get file extension and filter
        extension = self._get_file_extension(format_name)
        file_filter = self._get_file_filter(format_name)
        
        # File chooser dialog
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        dialog = Gtk.FileChooserDialog(
            title=f"Export as {format_name}",
            transient_for=toplevel,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(f"{self.metadata.model_name or 'report'}{extension}")
        
        # Set default directory to project's exports folder
        export_dir = self._get_export_directory()
        dialog.set_current_folder(export_dir)
        
        # Add file filter
        dialog.add_filter(file_filter)
        
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and filepath:
            try:
                # Collect report data from all categories
                report_data = self._collect_report_data()
                
                # Create appropriate generator
                generator = self._create_generator(format_name)
                if not generator:
                    return
                
                # Generate document (always use TECHNICAL type for unified executive format)
                success = generator.generate(
                    Path(filepath), 
                    DocumentType.TECHNICAL,
                    additional_data={'report_data': report_data}
                )
                
                if success:
                    self._show_info("Export Successful", 
                                  f"Document exported to:\n{filepath}")
                else:
                    self._show_error("Export Failed", 
                                   "Failed to generate document.")
                                   
            except Exception as e:
                self._show_error("Export Error", 
                               f"An error occurred during export:\n{str(e)}")
    
    # =========================================================================
    # DEPRECATED: Old export handlers (kept for backward compatibility)
    # Use _on_export() with format combo instead
    # =========================================================================
    
    def _on_export_pdf(self, button):
        """[DEPRECATED] Handle PDF export button click.
        
        This method is kept for backward compatibility.
        New code should use _on_export() with format combo.
        """
        if not self.metadata:
            self._show_error("No Metadata", 
                           "Please edit metadata first before exporting.")
            return
        
        # Choose document type
        doc_type = self._choose_document_type()
        if not doc_type:
            return
        
        # File chooser dialog
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        dialog = Gtk.FileChooserDialog(
            title="Export as PDF",
            transient_for=toplevel,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(f"{self.metadata.model_name or 'report'}.pdf")
        
        # Set default directory to project's exports folder
        export_dir = self._get_export_directory()
        dialog.set_current_folder(export_dir)
        
        # Add file filter
        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("PDF files")
        filter_pdf.add_mime_type("application/pdf")
        filter_pdf.add_pattern("*.pdf")
        dialog.add_filter(filter_pdf)
        
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and filepath:
            try:
                # Collect report data from all categories
                report_data = self._collect_report_data()
                
                generator = PDFGenerator(self.metadata, self.profile)
                success = generator.generate(
                    Path(filepath), 
                    doc_type,
                    additional_data={'report_data': report_data}
                )
                
                if success:
                    self._show_info("Export Successful", 
                                  f"PDF exported to:\n{filepath}")
                else:
                    self._show_error("Export Failed", 
                                   "Failed to generate PDF document.")
            except ImportError as e:
                self._show_error("Missing Dependency", 
                               f"PDF export requires WeasyPrint.\n\n{str(e)}")
            except Exception as e:
                self._show_error("Export Error", 
                               f"An error occurred during export:\n{str(e)}")
    
    def _on_export_excel(self, button):
        """Handle Excel export button click."""
        if not self.metadata:
            self._show_error("No Metadata", 
                           "Please edit metadata first before exporting.")
            return
        
        # Choose document type
        doc_type = self._choose_document_type()
        if not doc_type:
            return
        
        # File chooser dialog
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        dialog = Gtk.FileChooserDialog(
            title="Export as Excel",
            transient_for=toplevel,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(f"{self.metadata.model_name or 'report'}.xlsx")
        
        # Set default directory to project's exports folder
        export_dir = self._get_export_directory()
        dialog.set_current_folder(export_dir)
        
        # Add file filter
        filter_excel = Gtk.FileFilter()
        filter_excel.set_name("Excel files")
        filter_excel.add_mime_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        filter_excel.add_pattern("*.xlsx")
        dialog.add_filter(filter_excel)
        
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and filepath:
            try:
                # Collect report data from all categories
                report_data = self._collect_report_data()
                
                generator = ExcelGenerator(self.metadata, self.profile)
                success = generator.generate(
                    Path(filepath), 
                    doc_type,
                    additional_data={'report_data': report_data}
                )
                
                if success:
                    self._show_info("Export Successful", 
                                  f"Excel workbook exported to:\n{filepath}")
                else:
                    self._show_error("Export Failed", 
                                   "Failed to generate Excel workbook.")
            except ImportError as e:
                self._show_error("Missing Dependency", 
                               f"Excel export requires openpyxl.\n\n{str(e)}")
            except Exception as e:
                self._show_error("Export Error", 
                               f"An error occurred during export:\n{str(e)}")
    
    def _on_export_html(self, button):
        """Handle HTML export button click."""
        if not self.metadata:
            self._show_error("No Metadata", 
                           "Please edit metadata first before exporting.")
            return
        
        # Choose document type
        doc_type = self._choose_document_type()
        if not doc_type:
            return
        
        # File chooser dialog
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        dialog = Gtk.FileChooserDialog(
            title="Export as HTML",
            transient_for=toplevel,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(f"{self.metadata.model_name or 'report'}.html")
        
        # Set default directory to project's exports folder
        export_dir = self._get_export_directory()
        dialog.set_current_folder(export_dir)
        
        # Add file filter
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        filter_html.add_pattern("*.html")
        dialog.add_filter(filter_html)
        
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and filepath:
            try:
                # Collect report data from all categories
                report_data = self._collect_report_data()
                
                generator = HTMLGenerator(self.metadata, self.profile)
                success = generator.generate(
                    Path(filepath), 
                    doc_type,
                    additional_data={'report_data': report_data}
                )
                
                if success:
                    self._show_info("Export Successful", 
                                  f"HTML document exported to:\n{filepath}")
                else:
                    self._show_error("Export Failed", 
                                   "Failed to generate HTML document.")
            except Exception as e:
                self._show_error("Export Error", 
                               f"An error occurred during export:\n{str(e)}")
    
    def _show_info(self, title: str, message: str):
        """Show info dialog.
        
        Args:
            title: Dialog title
            message: Info message
        """
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        dialog = Gtk.MessageDialog(
            transient_for=toplevel,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration()
    
    def _show_error(self, title: str, message: str):
        """Show error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        dialog = Gtk.MessageDialog(
            transient_for=toplevel,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration()
    
    def _choose_document_type(self) -> Optional[DocumentType]:
        """Show dialog to choose document type.
        
        Returns:
            Selected DocumentType or None if cancelled
        """
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        dialog = Gtk.Dialog(
            title="Choose Document Type",
            transient_for=toplevel,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = dialog.get_content_area()
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        label = Gtk.Label(label="Select the type of document to generate:")
        label.set_halign(Gtk.Align.START)
        content.pack_start(label, False, False, 10)
        
        # Radio buttons for document types
        technical_radio = Gtk.RadioButton.new_with_label_from_widget(
            None, "Technical Report (comprehensive)"
        )
        content.pack_start(technical_radio, False, False, 5)
        
        publication_radio = Gtk.RadioButton.new_with_label_from_widget(
            technical_radio, "Publication Document (focused)"
        )
        content.pack_start(publication_radio, False, False, 5)
        
        summary_radio = Gtk.RadioButton.new_with_label_from_widget(
            technical_radio, "Summary Sheet (brief)"
        )
        content.pack_start(summary_radio, False, False, 5)
        
        dialog.show_all()
        response = dialog.run()
        
        result = None
        if response == Gtk.ResponseType.OK:
            if technical_radio.get_active():
                result = DocumentType.TECHNICAL
            elif publication_radio.get_active():
                result = DocumentType.PUBLICATION
            elif summary_radio.get_active():
                result = DocumentType.SUMMARY
        
        # Always destroy the dialog before returning
        dialog.destroy()
        
        # Process any pending GTK events to ensure dialog is fully cleaned up
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        # Additional event processing to ensure complete cleanup
        import time
        time.sleep(0.05)  # 50ms delay
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        return result
    
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

    # =========================================================================
    # SIMULATION DATA EXPORT
    # =========================================================================
    
    def update_simulation_data_availability(self, has_data: bool):
        """Enable/disable simulation export button based on data availability.
        
        Args:
            has_data: True if simulation data is available
        """
        if hasattr(self, 'sim_export_btn'):
            self.sim_export_btn.set_sensitive(has_data)
    
    def _on_export_simulation_data(self, button):
        """Handle simulation data export button click."""
        try:
            # Get simulation data from parent panel
            if not self.parent_panel:
                self._show_error("No Data", "No simulation data available.")
                return
            
            sim_data = self._get_simulation_data()
            if not sim_data:
                self._show_error("No Data", 
                               "No simulation data available. Run a simulation first.")
                return
            
            # Get the actual top-level window
            toplevel = self.get_toplevel()
            if not isinstance(toplevel, Gtk.Window):
                toplevel = None
            
            # Open export dialog
            from .simulation_export_dialog import SimulationExportDialog
            dialog = SimulationExportDialog(toplevel, sim_data, self.metadata or {})
            response, export_config = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                self._execute_simulation_export(export_config, sim_data)
        except Exception as e:
            print(f"Error in simulation export: {e}")
            import traceback
            traceback.print_exc()
            self._show_error("Export Error", f"Failed to open export dialog: {e}")
    
    def _get_simulation_data(self) -> dict:
        """Get simulation data from Dynamic Analyses category.
        
        Returns:
            Dict with simulation data or None if not available
        """
        if not self.parent_panel or not hasattr(self.parent_panel, 'categories'):
            return None
        
        for category in self.parent_panel.categories:
            if hasattr(category, 'controller') and category.controller:
                if hasattr(category.controller, 'data_collector'):
                    dc = category.controller.data_collector
                    if dc and dc.has_data():
                        # Get stored simulation data from document report data
                        stored_data = None
                        if hasattr(category.controller, 'drawing_area'):
                            da = category.controller.drawing_area
                            if hasattr(da, 'report_data') and da.report_data:
                                stored_data = da.report_data.last_simulation_data
                        
                        # Get accounting report if enabled
                        accounting_report = None
                        if hasattr(category.controller, 'get_accounting_report'):
                            accounting_report = category.controller.get_accounting_report()
                        
                        return {
                            'time_points': stored_data['time_points'] if stored_data else dc.time_points,
                            'place_data': stored_data['place_data'] if stored_data else dc.place_data,
                            'transition_data': stored_data['transition_data'] if stored_data else dc.transition_data,
                            'model': category.controller.model,
                            'metadata': stored_data.get('metadata', {}) if stored_data else {},
                            'accounting_report': accounting_report
                        }
        return None
    
    def _execute_simulation_export(self, config: dict, sim_data: dict):
        """Execute the export based on user configuration.
        
        Args:
            config: Export configuration dict
            sim_data: Simulation data dict
        """
        format_type = config['format']
        
        # Get default filename
        model_name = "simulation"
        if sim_data.get('model'):
            model_name = getattr(sim_data['model'], 'name', 
                               getattr(sim_data['model'], 'id', 'simulation'))
        elif self.metadata:
            model_name = self.metadata.model_name or 'simulation'
        
        default_filename = f"{model_name}_data{config['extension']}"
        
        # File chooser dialog
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            toplevel = None
        
        dialog = Gtk.FileChooserDialog(
            title="Export Simulation Data",
            transient_for=toplevel,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(default_filename)
        
        # Set default directory
        export_dir = self._get_export_directory()
        dialog.set_current_folder(export_dir)
        
        # Add file filter
        file_filter = Gtk.FileFilter()
        if format_type.startswith('csv'):
            file_filter.set_name("CSV files")
            file_filter.add_pattern("*.csv")
        elif format_type == 'json':
            file_filter.set_name("JSON files")
            file_filter.add_pattern("*.json")
        elif format_type == 'svg':
            file_filter.set_name("SVG files")
            file_filter.add_pattern("*.svg")
        elif format_type == 'png':
            file_filter.set_name("PNG files")
            file_filter.add_pattern("*.png")
        dialog.add_filter(file_filter)
        
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        
        if response != Gtk.ResponseType.OK or not filepath:
            return
        
        # Execute export
        try:
            success = False
            
            if format_type == 'csv_timeseries_wide':
                from shypn.reporting.exporters import CSVSimulationExporter
                accounting_data = sim_data.get('accounting_report')
                exporter = CSVSimulationExporter(sim_data, self.metadata, accounting_data)
                success = exporter.export_timeseries_wide(filepath)
            
            elif format_type == 'csv_timeseries_long':
                from shypn.reporting.exporters import CSVSimulationExporter
                accounting_data = sim_data.get('accounting_report')
                exporter = CSVSimulationExporter(sim_data, self.metadata, accounting_data)
                success = exporter.export_timeseries_long(filepath)
            
            elif format_type == 'csv_summary':
                from shypn.reporting.exporters import CSVSimulationExporter
                accounting_data = sim_data.get('accounting_report')
                exporter = CSVSimulationExporter(sim_data, self.metadata, accounting_data)
                success = exporter.export_summary_statistics(filepath)
            
            elif format_type == 'json':
                from shypn.reporting.exporters import JSONSimulationExporter
                exporter = JSONSimulationExporter(sim_data, self.metadata, sim_data.get('model'))
                success = exporter.export(
                    filepath,
                    include_metadata=config.get('include_metadata', True),
                    include_timeseries=True,
                    include_statistics=config.get('include_statistics', True)
                )
            
            elif format_type in ['svg', 'png']:
                from shypn.reporting.exporters import PlotExporter
                exporter = PlotExporter(sim_data, self.metadata, sim_data.get('model'))
                plot_opts = config.get('plot_options', {})
                
                if plot_opts.get('combined', False):
                    success = exporter.export_combined_plot(
                        filepath, format=format_type, dpi=plot_opts.get('dpi', 300)
                    )
                elif plot_opts.get('firing_rates', False):
                    success = exporter.export_firing_rate_curves(
                        filepath, format=format_type, dpi=plot_opts.get('dpi', 300)
                    )
                else:  # Default to concentrations
                    success = exporter.export_concentration_curves(
                        filepath, format=format_type, dpi=plot_opts.get('dpi', 300)
                    )
            
            if success:
                self._show_info("Export Successful", 
                              f"Simulation data exported to:\n{filepath}")
            else:
                self._show_error("Export Failed", 
                               "Failed to export simulation data.")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error("Export Error", 
                           f"An error occurred during export:\n{str(e)}")
