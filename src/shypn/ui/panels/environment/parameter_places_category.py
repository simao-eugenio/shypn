#!/usr/bin/env python3
"""Parameter Places Category — editable view of exogenous parameter places.

Parameter places (Place.is_parameter_place=True) are constant scalars
that hold experimental knobs read by events, rate functions, or trigger
expressions (e.g. LOADING_DOSE, MAINT_DOSE, REDOSE_TIME). They carry no
biology, have no arcs, and are not consumed/produced by reactions.

This category mirrors SignalPlacesCategory but:
  - Filters on `is_parameter_place` instead of `is_signal_place`.
  - Shows Kind / Units columns sourced from `parameter_kind` / `parameter_units`.
  - The Value column is INLINE-EDITABLE — editing updates both
    `place.tokens` and `place.initial_marking` so the new value is the
    canonical baseline used by the next simulation reset and by the
    sweep CLI.

EventBus (document-scoped):
  - subscribes to: model.loaded, model.place.created, .deleted, .modified,
                   model.environment.place_value_changed
  - emits:        model.environment.place_value_changed on inline edit
"""
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

logger = logging.getLogger(__name__)


class ParameterPlacesCategory:
    """Editable list of parameter places.

    Columns:
        Name   — place.name
        Kind   — place.parameter_kind (free-form: 'dose', 'interval', ...)
        Units  — place.parameter_units (free-form, documentation only)
        Value  — place.initial_marking (inline-editable)
    """

    _COLUMNS = ('Name', 'Kind', 'Units', 'Value')
    _COL_NAME, _COL_KIND, _COL_UNITS, _COL_VALUE = range(4)

    def __init__(self, model=None, document_id=None):
        self.model = model
        self.document_id = document_id
        # Store: name, kind, units, value (all str for the TreeView)
        self._store = Gtk.ListStore(str, str, str, str)
        # Map row → place object so the edit handler can mutate it directly
        self._row_places: list = []
        self._on_place_activated = None  # callback(place_name: str)
        self._inhibit_edited = False
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
        btn_refresh.set_tooltip_text('Refresh parameter places list')
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
            # Only the Value column is editable; Name/Kind/Units are managed
            # via the place properties dialog so the canonical model file is
            # not mutated from two places.
            if col_idx == self._COL_VALUE:
                renderer.set_property('editable', True)
                renderer.connect('edited', self._on_value_edited)
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
            logger.debug('ParameterPlacesCategory: EventBus subscription failed: %s', exc)

    def _on_row_activated(self, tv, path, column) -> None:
        """Double-click on a row — notify the events table."""
        it = self._store.get_iter(path)
        if it is not None:
            place_name = self._store.get_value(it, self._COL_NAME)
            if callable(self._on_place_activated):
                self._on_place_activated(place_name)

    def set_on_place_activated(self, callback) -> None:
        """Register a callback invoked when the user double-clicks a row."""
        self._on_place_activated = callback

    def _on_model_changed(self, event_data=None) -> None:
        GLib.idle_add(self.refresh)

    # ------------------------------------------------------------------
    # Inline edit on the Value column
    # ------------------------------------------------------------------

    def _on_value_edited(self, _renderer, path_str, new_text):
        if self._inhibit_edited:
            return
        try:
            row_idx = int(path_str)
        except (TypeError, ValueError):
            return
        if not (0 <= row_idx < len(self._row_places)):
            return
        place = self._row_places[row_idx]

        text = (new_text or '').strip()
        try:
            value = float(text)
        except ValueError:
            logger.warning('ParameterPlacesCategory: invalid numeric value %r', text)
            # Restore previous text in the store
            old = str(getattr(place, 'initial_marking', getattr(place, 'tokens', 0)))
            self._inhibit_edited = True
            try:
                it = self._store.get_iter_from_string(path_str)
                if it is not None:
                    self._store.set_value(it, self._COL_VALUE, old)
            finally:
                self._inhibit_edited = False
            return

        # Update both initial_marking (canonical baseline used by sweeps and
        # simulation reset) and the live tokens count.
        place.initial_marking = value
        place.tokens = value

        # Reflect the parsed value back in the store (normalises e.g. "20" → "20.0")
        self._inhibit_edited = True
        try:
            it = self._store.get_iter_from_string(path_str)
            if it is not None:
                self._store.set_value(it, self._COL_VALUE, str(value))
        finally:
            self._inhibit_edited = False

        # Mark document dirty + notify other panels.
        try:
            from shypn.events import EventBus
            EventBus.emit(
                'model.environment.place_value_changed',
                {'object': place, 'object_id': getattr(place, 'id', None),
                 'value': value},
                document_id=self.document_id,
            )
            EventBus.emit(
                'model.place.modified',
                {'object': place, 'object_id': getattr(place, 'id', None)},
                document_id=self.document_id,
            )
        except Exception as exc:
            logger.debug('ParameterPlacesCategory: EventBus emit failed: %s', exc)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def set_model(self, model) -> None:
        self.model = model
        self.refresh()

    def refresh(self) -> None:
        """Repopulate the store from the current model's parameter places."""
        self._store.clear()
        self._row_places = []
        if self.model is None:
            return
        places = getattr(self.model, 'places', [])
        for p in places:
            if not getattr(p, 'is_parameter_place', False):
                continue
            name = getattr(p, 'name', '') or ''
            kind = getattr(p, 'parameter_kind', None) or '—'
            units = getattr(p, 'parameter_units', None) or '—'
            # Show initial_marking (the canonical baseline). Fall back to
            # tokens if missing for any reason.
            value = getattr(p, 'initial_marking', None)
            if value is None:
                value = getattr(p, 'tokens', 0)
            self._store.append([name, str(kind), str(units), str(value)])
            self._row_places.append(p)

        # Auto-select the first row when the list is populated
        if len(self._store) > 0:
            self._treeview.get_selection().select_path(Gtk.TreePath.new_first())
