"""Environment Panel Loader — per-document architecture.

Follows the exact pattern of TopologyPanelLoader / ViabilityPanelLoader:
  - Inherits PerDocumentPanelLoader
  - Creates one EnvironmentPanel per document
  - Float / attach / left_dock_stack managed by base class
  - On tab switch: calls panel.refresh() so signal places + events stay current

Author: Simão Eugénio, SHYPN Development Team
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.events import EventBus
from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
from shypn.ui.panels.environment import EnvironmentPanel


class EnvironmentPanelLoader(PerDocumentPanelLoader):
    """Per-document loader for the Environment Panel.

    Parameters
    ----------
    model:
        ModelCanvasManager for this document (may be None; used as initial model).
    parent_window:
        Parent Gtk.Window for floating window and dialogs.
    document_id:
        Integer doc_id for EventBus scoping (prevents cross-document events).
    drawing_area:
        The Gtk.DrawingArea that owns this document.
    """

    def __init__(self, model, parent_window=None, document_id=None, drawing_area=None):
        # Store before super().__init__ which calls _create_panel()
        self.document_id = document_id
        self.drawing_area = drawing_area
        self.model_canvas_loader = None

        super().__init__(model, parent_window)

        # self.controller kept for compatibility (same pattern as topology loader)
        self.controller = self

    # ------------------------------------------------------------------
    # PerDocumentPanelLoader abstract implementations
    # ------------------------------------------------------------------

    def _create_panel(self) -> Gtk.Widget:
        """Factory: create the EnvironmentPanel for this document."""
        panel = EnvironmentPanel(
            model=self.model,
            model_canvas=None,          # wired later via set_model_canvas_loader
            document_id=self.document_id,
        )
        return panel

    def get_panel_name(self) -> str:
        return 'Environment'

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize panel and wire float button (called by DocumentPanelSetup).

        Guard against double-initialization: PerDocumentPanelLoader.__init__
        already calls initialize() internally, so the explicit call from
        DocumentPanelSetup must be a no-op if the panel was already created.
        """
        if self.panel is not None:
            return  # already initialized via __init__ → super().__init__ → initialize()
        super().initialize()
        # Subscribe to document.focused for per-document panel swapping
        EventBus.subscribe('document.focused', self._on_document_focused)

    def _on_document_focused(self, data: dict) -> None:
        """Swap this panel in/out of its container when document focus changes."""
        event_doc_id = data.get('_document_id')

        # Floating panels manage their own window visibility
        if not self.is_hanged:
            return
        if not self.parent_container:
            return

        is_ours = (event_doc_id == self.document_id)
        if is_ours:
            # Move widget into our container if it isn't already there
            current_parent = self.widget.get_parent()
            if current_parent != self.parent_container:
                if current_parent:
                    current_parent.remove(self.widget)
                self.parent_container.pack_start(self.widget, True, True, 0)
            # Update model and refresh
            canvas_manager = data.get('canvas_manager')
            if canvas_manager is not None and self.panel is not None:
                self.panel.set_model(canvas_manager)
            if self.panel is not None:
                GLib.idle_add(self.panel.refresh)
            self.widget.show()
        else:
            self.widget.hide()

    def refresh(self) -> None:
        """Refresh panel data (called by tab switch and file open)."""
        super().refresh()
        if self.panel is not None:
            GLib.idle_add(self.panel.refresh)

    # ------------------------------------------------------------------
    # Model canvas loader integration
    # ------------------------------------------------------------------

    def set_model_canvas_loader(self, model_canvas_loader) -> None:
        """Set the ModelCanvasLoader so the panel can obtain the active model."""
        self.model_canvas_loader = model_canvas_loader
        if self.panel is not None:
            self.panel.set_model_canvas(model_canvas_loader)

    # ------------------------------------------------------------------
    # Tab-switch handler
    # ------------------------------------------------------------------

    def on_tab_switched(self, drawing_area) -> None:
        """Called by ModelCanvasLoader when the user switches document tabs.

        Updates the panel's model reference to the newly active document and
        schedules a deferred refresh so animations complete before populating.
        """
        if self.model_canvas_loader is not None:
            try:
                canvas_manager = self.model_canvas_loader.get_current_model()
                if canvas_manager is not None and self.panel is not None:
                    self.panel.set_model(canvas_manager)
            except Exception:
                pass
        if self.panel is not None:
            GLib.idle_add(self.panel.refresh)

    def on_tab_closed(self) -> None:
        """Called when this document's tab is closed — clean up subscriptions."""
        try:
            EventBus.unsubscribe('document.focused', self._on_document_focused)
        except Exception:
            pass
        if self.panel is not None:
            try:
                EventBus.clear_document(self.document_id)
            except Exception:
                pass
