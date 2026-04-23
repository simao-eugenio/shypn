#!/usr/bin/env python3
"""Environment Panel — top-level container.

Architecture mirrors TopologyPanel:
  - EnvironmentPanel(Gtk.Box) owns the widget tree
  - Header: <b>ENVIRONMENT</b> + float ToggleButton + separator
  - Body: ScrolledWindow → categories_box with CategoryFrame expanders
      1. SIGNAL SPATIAL PLACES  (SignalPlacesCategory)
      2. ENVIRONMENT EVENTS     (EventsCategory)
  - EnvironmentPanelLoader manages per-document lifecycle / float / stack

Author: SHYPN Development Team
"""
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.category_frame import CategoryFrame
from .signal_places_category import SignalPlacesCategory
from .parameter_places_category import ParameterPlacesCategory
from .events_category import EventsCategory

logger = logging.getLogger(__name__)


class EnvironmentPanel(Gtk.Box):
    """Main widget for the Environment panel.

    Parameters
    ----------
    model:
        ModelCanvasManager for the active document.  Can be None initially.
    model_canvas:
        ModelCanvasLoader reference (optional).
    document_id:
        Integer document id for EventBus scoping.
    """

    def __init__(self, model=None, model_canvas=None, document_id=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.model = model
        self.model_canvas_loader = model_canvas
        self.document_id = document_id

        self._signal_places_cat: SignalPlacesCategory | None = None
        self._parameter_places_cat: ParameterPlacesCategory | None = None
        self._events_cat: EventsCategory | None = None

        self._build_ui()

        if model is not None:
            self._sync_model(model)

    # ------------------------------------------------------------------
    # UI construction  (matches TopologyPanel layout conventions)
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Panel header (same height / markup as TopologyPanel) ─────────
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)

        header_label = Gtk.Label()
        header_label.set_markup('<b>ENVIRONMENT</b>')
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)

        # Float toggle button — loader reads self.float_button
        self.float_button = Gtk.ToggleButton(label='⬈')
        self.float_button.get_style_context().add_class('float-button')
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)

        self.pack_start(header_box, False, False, 0)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # ── Scrolled window containing CategoryFrame expanders ────────────
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)

        self.categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.categories_box.set_margin_start(5)
        self.categories_box.set_margin_end(5)
        self.categories_box.set_margin_top(5)
        self.categories_box.set_margin_bottom(5)

        # ── Category 1: SIGNAL SPATIAL PLACES ────────────────────────────
        self._signal_places_cat = SignalPlacesCategory(
            model=self.model,
            document_id=self.document_id,
        )
        self._sp_frame = CategoryFrame(
            title='SIGNAL SPATIAL PLACES',
            expanded=True,
        )
        self._sp_frame.set_content(self._signal_places_cat.widget)
        self.categories_box.pack_start(self._sp_frame, False, False, 0)

        # ── Category 2: PARAMETER PLACES (exogenous experimental constants) ──
        self._parameter_places_cat = ParameterPlacesCategory(
            model=self.model,
            document_id=self.document_id,
        )
        self._pp_frame = CategoryFrame(
            title='PARAMETER PLACES',
            expanded=True,
        )
        self._pp_frame.set_content(self._parameter_places_cat.widget)
        self.categories_box.pack_start(self._pp_frame, False, False, 0)

        # ── Category 3: ENVIRONMENT EVENTS ───────────────────────────
        self._events_cat = EventsCategory(
            model=self.model,
            document_id=self.document_id,
        )
        self._ev_frame = CategoryFrame(
            title='ENVIRONMENT EVENTS',
            expanded=True,
        )
        self._ev_frame.set_content(self._events_cat.widget)
        self.categories_box.pack_start(self._ev_frame, True, True, 0)

        # Wire double-click on a signal place to jump to the events table
        self._signal_places_cat.set_on_place_activated(self._on_place_activated)
        # Same for parameter places
        self._parameter_places_cat.set_on_place_activated(self._on_place_activated)

        self.scrolled_window.add(self.categories_box)
        self.pack_start(self.scrolled_window, True, True, 0)

        # Show children (not self — parent loader controls panel visibility)
        self.categories_box.show_all()
        self.scrolled_window.show_all()

    # ------------------------------------------------------------------
    # Model / loader wiring
    # ------------------------------------------------------------------

    def set_model(self, model) -> None:
        """Update the active model (called on tab switch)."""
        self.model = model
        self._sync_model(model)

    def set_model_canvas(self, model_canvas_loader) -> None:
        """Called by EnvironmentPanelLoader after initialization."""
        self.model_canvas_loader = model_canvas_loader

    def _on_place_activated(self, place_name: str) -> None:
        """Add a new event pre-filled for the double-clicked signal place."""
        if self._events_cat is not None:
            self._events_cat.add_event_for_place(place_name)

    def _sync_model(self, model) -> None:
        if self._signal_places_cat is not None:
            self._signal_places_cat.set_model(model)
        if self._parameter_places_cat is not None:
            self._parameter_places_cat.set_model(model)
        if self._events_cat is not None:
            self._events_cat.set_model(model)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh all sub-categories (called on tab switch)."""
        model = self.model
        if self.model_canvas_loader is not None:
            try:
                canvas_mgr = self.model_canvas_loader.get_current_model()
                if canvas_mgr is not None:
                    model = canvas_mgr
            except Exception:
                pass
        self._sync_model(model)
