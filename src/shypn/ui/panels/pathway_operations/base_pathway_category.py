#!/usr/bin/env python3
"""Base class for pathway operation categories.

All pathway categories (KEGG, SBML, BRENDA) inherit from BasePathwayCategory
and implement the _build_content() method to populate their specific import/enrichment views.

Each category contains:
1. Import/enrichment controls
2. Status indicators
3. Preview/results display
4. Action buttons

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.category_frame import CategoryFrame


class BasePathwayCategory(CategoryFrame):
    """Base class for pathway operation category controllers.
    
    Each category is responsible for:
    1. Building its content view (import controls + preview/status)
    2. Managing import/enrichment workflow (with threading)
    3. Preserving state when collapsed/expanded
    4. Signaling when data is imported (for BRENDA integration)
    5. Integrating with project for metadata tracking
    
    Subclasses must implement:
    - _build_content(): Create and return the content widget
    
    Subclasses may override:
    - _on_import_complete(): Called when import finishes successfully
    - _on_import_error(): Called when import encounters error
    """
    
    def __init__(self, category_name, expanded=False):
        """Initialize base pathway category.
        
        Args:
            category_name: Category name displayed in expander
            expanded: Whether category starts expanded
        """
        super().__init__(title=category_name, expanded=expanded)
        
        self.category_name = category_name
        self.model_canvas = None
        self.project = None
        self.parent_panel = None  # Will be set by PathwayOperationsPanel
        
        # Import state
        self.current_import_data = None  # Current imported pathway/model data
        self.import_in_progress = False
        self.import_complete_callback = None  # Callback for KEGG/SBML→BRENDA flow
        
        # Widgets (to be set by subclasses)
        self.status_label = None
        self.preview_widget = None
        
        # Build content (implemented by subclasses)
        content_widget = self._build_content()
        if content_widget:
            self.set_content(content_widget)
    
    def _build_content(self):
        """Build and return the content widget.
        
        Must be implemented by subclasses.
        
        Returns:
            Gtk.Widget: The content to display in this category
        """
        raise NotImplementedError("Subclasses must implement _build_content()")
    
    def _get_status_widget(self):
        """Get the status label widget for displaying messages.
        
        Should be implemented by subclasses to return their status label.
        
        Returns:
            Gtk.Label: Status label or None
        """
        return self.status_label
    
    # ========================================================================
    # Status Message Helpers (Wayland-safe)
    # ========================================================================
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message in label (Wayland-safe).
        
        Args:
            message: Status message to display
            error: If True, display as error (red text)
        """
        status_widget = self._get_status_widget()
        if not status_widget:
            return
        
        if error:
            status_widget.set_markup(f'<span foreground="red">{message}</span>')
        else:
            status_widget.set_text(message)
    
    def _show_progress(self, message: str):
        """Show progress message with spinner icon.
        
        Args:
            message: Progress message to display
        """
        self._show_status(f"🔄 {message}")
    
    def _show_success(self, message: str):
        """Show success message with checkmark icon.
        
        Args:
            message: Success message to display
        """
        self._show_status(f"✅ {message}")
    
    def _show_error(self, message: str):
        """Show error message with error icon.
        
        Args:
            message: Error message to display
        """
        self._show_status(f"❌ {message}", error=True)
    
    # ========================================================================
    # Threading Helpers (Wayland-safe)
    # ========================================================================
    
    def _run_in_thread(self, task_func, on_complete=None, on_error=None):
        """Run a blocking task in background thread (Wayland-safe).
        
        Args:
            task_func: Function to run in background thread
            on_complete: Callback when task completes successfully (receives result)
            on_error: Callback when task encounters error (receives exception)
        """
        import threading
        
        def thread_wrapper():
            try:
                result = task_func()
                if on_complete:
                    GLib.idle_add(on_complete, result)
            except Exception as e:
                if on_error:
                    GLib.idle_add(on_error, e)
                else:
                    # Default error handling
                    GLib.idle_add(self._show_error, str(e))
        
        threading.Thread(target=thread_wrapper, daemon=True).start()
    
    # ========================================================================
    # Project Integration
    # ========================================================================
    
    def set_project(self, project):
        """Set or update the current project.
        
        Updates UI state based on project availability.
        
        Args:
            project: Project instance or None
        """
        self.project = project
        self._update_ui_for_project_state()
    
    def _update_ui_for_project_state(self):
        """Update UI elements based on project availability.
        
        Subclasses can override to enable/disable controls based on project state.
        Default implementation does nothing.
        """
        pass
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
    
    # ========================================================================
    # Import Lifecycle (Override in subclasses)
    # ========================================================================
    
    def _on_import_complete(self, imported_data):
        """Called when import completes successfully.
        
        Subclasses can override to perform additional actions.
        Default implementation notifies parent panel.
        
        Args:
            imported_data: The imported pathway/model data
        """
        self.current_import_data = imported_data
        self.import_in_progress = False
        
        # Notify parent panel (for BRENDA integration)
        if self.parent_panel and hasattr(self.parent_panel, '_on_category_import_complete'):
            self.parent_panel._on_category_import_complete(self, imported_data)
    
    def _on_import_error(self, error):
        """Called when import encounters an error.
        
        Subclasses can override to perform additional actions.
        Default implementation shows error message.
        
        Args:
            error: Exception or error message
        """
        self.import_in_progress = False
        self._show_error(f"Import failed: {error}")
    
    # ========================================================================
    # Signal for KEGG/SBML → BRENDA data flow
    # ========================================================================
    
    def _trigger_import_complete(self, data: dict):
        """Trigger import complete signal for BRENDA integration.
        
        Args:
            data: Import data dict with species, reactions, etc.
        """
        if self.import_complete_callback:
            self.import_complete_callback(data)
    
    # ========================================================================
    # CategoryFrame compatibility methods
    # ========================================================================
    
    def is_expanded(self) -> bool:
        """Check if category is currently expanded.
        
        Returns:
            bool: True if expanded, False if collapsed
        """
        return self.expanded

