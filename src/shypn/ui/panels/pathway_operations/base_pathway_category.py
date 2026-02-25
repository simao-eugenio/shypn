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
        """Set or update the model canvas / manager.

        Args:
            model_canvas: Either a ModelCanvasLoader (multi-document) or a
                ModelCanvasManager. Subclasses that need direct access to the
                manager should use ``self._get_canvas_manager()`` method.
        """
        self.model_canvas = model_canvas
    
    def _get_canvas_loader(self):
        """Get the canvas loader instance (for creating new tabs).
        
        Returns:
            ModelCanvasLoader instance if available, None otherwise
        """
        if self.model_canvas is None:
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning("_get_canvas_loader: self.model_canvas is None")
            return None
        
        # Check if it's a loader (has add_document method)
        if hasattr(self.model_canvas, 'add_document'):
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.info(f"_get_canvas_loader: Found loader (type={type(self.model_canvas).__name__})")
            return self.model_canvas
        
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        logger.warning(f"_get_canvas_loader: model_canvas has no add_document method (type={type(self.model_canvas).__name__})")
        return None
    
    def _get_canvas_manager(self):
        """Get the current canvas manager instance consistently.
        
        This method normalizes access to the canvas manager across all
        per-document panel instances, handling both loader and direct
        manager references.
        
        Returns:
            ModelCanvasManager instance if available, None otherwise
        """
        if self.model_canvas is None:
            return None
        
        # If it has add_document, it's a loader - get current manager
        if hasattr(self.model_canvas, 'add_document'):
            # It's a ModelCanvasLoader
            try:
                if hasattr(self.model_canvas, 'get_current_model'):
                    return self.model_canvas.get_current_model()
                elif hasattr(self.model_canvas, 'get_current_model_manager'):
                    return self.model_canvas.get_current_model_manager()
            except Exception as e:
                import logging
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning(f"Failed to get manager from loader: {e}")
                return None
        
        # Check if it's already a manager (has places/transitions)
        if hasattr(self.model_canvas, 'places') and hasattr(self.model_canvas, 'transitions'):
            return self.model_canvas
        
        return None
    
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
    # Shared simulation helpers (used by BRENDA, SABIO-RK, and similar)
    # ========================================================================

    def _reset_simulation_after_parameter_changes(self):
        """Reset the simulation after enrichment parameters have been applied.

        When parameters are applied to transitions (e.g. via BRENDA or SABIO-RK
        enrichment) the simulation controller's behaviour cache contains stale
        TransitionBehavior instances.  This method clears that cache so the new
        parameter values are picked up on the next simulation run.

        Subclasses may override this method if they need different reset
        behaviour (e.g. partial resets).
        """
        source = self.__class__.__name__
        try:
            if not self.model_canvas:
                import logging
                logging.getLogger(__name__).warning(
                    "No model canvas available for simulation reset (%s)", source)
                return
            drawing_area = self.model_canvas.get_current_document()
            if not drawing_area:
                return
            if not hasattr(self.model_canvas, 'simulation_controllers'):
                return
            controllers = self.model_canvas.simulation_controllers
            if drawing_area not in controllers:
                return
            controller = controllers[drawing_area]
            canvas_manager = getattr(self.model_canvas, 'canvas_managers', {}).get(drawing_area)
            import logging
            _log = logging.getLogger(__name__)
            if canvas_manager:
                controller.reset_for_new_model(canvas_manager)
                _log.info("Simulation fully reset after %s parameter changes "
                          "(model adapter recreated)", source)
            else:
                controller.reset()
                _log.info("Simulation reset after %s parameter changes", source)
            drawing_area.queue_draw()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "Error resetting simulation after %s parameter changes: %s",
                source, e, exc_info=True)

    def _open_sbml_file_dialog(self, entry_widget):
        """Open a Wayland-safe SBML file chooser and populate *entry_widget*.

        Shared by SBML and BiGG import categories which both load local
        SBML / XML files.  Sets the initial directory to the active project's
        ``pathways/`` folder when available.

        Args:
            entry_widget: Gtk.Entry to fill with the chosen file path.
        """
        import os
        dialog = Gtk.FileChooserDialog(
            title="Select SBML File",
            transient_for=self.parent_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        # Root to active project's pathways folder when available
        try:
            from shypn.data.project_models import get_project_manager
            pm = get_project_manager()
            if pm.current_project:
                pathways_dir = os.path.join(pm.current_project.base_path, 'pathways')
                if os.path.exists(pathways_dir):
                    dialog.set_current_folder(pathways_dir)
                else:
                    dialog.set_current_folder(pm.current_project.base_path)
        except (ImportError, AttributeError):
            pass
        # File filters
        filter_sbml = Gtk.FileFilter()
        filter_sbml.set_name("SBML Files")
        filter_sbml.add_pattern("*.sbml")
        filter_sbml.add_pattern("*.xml")
        dialog.add_filter(filter_sbml)
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        dialog.set_current_name("")
        # Wayland-safe async pattern (nested main loop)
        result_container = [None]

        def on_response(dlg, response_id):
            if response_id == Gtk.ResponseType.OK:
                result_container[0] = dlg.get_filename()
            dlg.destroy()
            Gtk.main_quit()

        dialog.connect('response', on_response)
        dialog.show()
        Gtk.main()
        filepath = result_container[0]
        if filepath:
            entry_widget.set_text(filepath)

    # ========================================================================
    # CategoryFrame compatibility methods
    # ========================================================================

    def is_expanded(self) -> bool:
        """Check if category is currently expanded.
        
        Returns:
            bool: True if expanded, False if collapsed
        """
        return self.expanded

