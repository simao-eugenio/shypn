#!/usr/bin/env python3
"""Signal Places Category — read-only view of signal spatial places.

Signal spatial places are "read-only environment registers": their token
value is the current environmental state (Temperature, pH, O2_concentration,
…).  They are NOT written by arcs during simulation; they change only via
Environment Events (see EventsCategory) or explicit user edits.

This category subscribes to:
  - model.loaded        → full refresh
  - model.place.created / .deleted / .modified → incremental refresh
  - model.environment.place_value_changed → token value refresh

All subscriptions are scoped to the document_id so multiple open documents
stay isolated.
"""
import logging
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

logger = logging.getLogger(__name__)


class SignalPlacesCategory:
    """Read-only list of signal spatial places with their live token values.

    Columns:
        Name          — place.name
        Compartment   — place.properties.get('compartment', '—')
        Type          — place.place_type (e.g. 'continuous', 'signal')
        Tokens        — place.tokens (current value)
    """

    _COLUMNS = ('Name', 'Compartment', 'Type', 'Tokens')
    _COL_NAME, _COL_COMP, _COL_TYPE, _COL_TOKENS = range(4)

    def __init__(self, model=None, document_id=None):
        self.model = model
        self.document_id = document_id
        self._store = Gtk.ListStore(str, str, str, str)
        self._on_place_activated = None  # callback(place_name: str)
        self.widget = self._build_widget()
        self._subscribe_events()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _build_widget(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Compact refresh toolbar (no title — CategoryFrame provides it)
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hdr.set_margin_top(2)
        hdr.set_margin_bottom(2)
        hdr.set_margin_end(4)

        btn_refresh = Gtk.Button.new_from_icon_name('view-refresh-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        btn_refresh.set_tooltip_text('Refresh signal places list')
        btn_refresh.connect('clicked', lambda _: self.refresh())
        hdr.pack_end(btn_refresh, False, False, 0)

        outer.pack_start(hdr, False, False, 0)

        # TreeView
        tv = Gtk.TreeView(model=self._store)
        tv.set_headers_visible(True)
        tv.set_enable_search(False)
        tv.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        tv.connect('row-activated', self._on_row_activated)
        self._treeview = tv

        for col_idx, title in enumerate(self._COLUMNS):
            renderer = Gtk.CellRendererText()
            renderer.set_property('ellipsize', 3)  # PANGO_ELLIPSIZE_END
            col = Gtk.TreeViewColumn(title, renderer, text=col_idx)
            col.set_resizable(True)
            col.set_min_width(60)
            tv.append_column(col)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(100)
        scroll.add(tv)

        outer.pack_start(scroll, True, True, 0)

        outer.show_all()
        return outer

    # ------------------------------------------------------------------
    # EventBus subscriptions
    # ------------------------------------------------------------------

    def _subscribe_events(self) -> None:
        try:
            from shypn.events import EventBus
            for event_name in ('model.loaded', 'model.place.created',
                               'model.place.deleted', 'model.place.modified',
                               'model.environment.place_value_changed'):
                EventBus.subscribe(
                    event_name,
                    self._on_model_changed,
                    document_id=self.document_id,
                )
        except Exception as exc:
            logger.debug('SignalPlacesCategory: EventBus subscription failed: %s', exc)

    def _on_row_activated(self, tv, path, column) -> None:
        """Double-click on a signal place row — notify the events table."""
        it = self._store.get_iter(path)
        if it is not None:
            place_name = self._store.get_value(it, self._COL_NAME)
            if callable(self._on_place_activated):
                self._on_place_activated(place_name)

    def set_on_place_activated(self, callback) -> None:
        """Register a callback invoked when the user double-clicks a place row.

        Parameters
        ----------
        callback:
            Callable receiving one argument: the place name string.
        """
        self._on_place_activated = callback

    def _on_model_changed(self, event_data=None) -> None:
        GLib.idle_add(self.refresh)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def set_model(self, model) -> None:
        self.model = model
        self.refresh()

    def refresh(self) -> None:
        """Repopulate the store from the current model's signal places."""
        self._store.clear()
        if self.model is None:
            return
        places = getattr(self.model, 'places', [])
        for p in places:
            place_type = getattr(p, 'place_type', None) or ''
            is_signal = (place_type.lower() == 'signal'
                         or getattr(p, 'is_signal_place', False))
            if not is_signal:
                continue
            name = getattr(p, 'name', '') or ''
            comp = (getattr(p, 'properties', {}) or {}).get('compartment', '—')
            ptype = getattr(p, 'place_type', 'signal') or 'signal'
            tokens = str(getattr(p, 'tokens', 0))
            self._store.append([name, str(comp), ptype, tokens])
        # Auto-select the first row when the list is populated
        if len(self._store) > 0:
            self._treeview.get_selection().select_path(Gtk.TreePath.new_first())
