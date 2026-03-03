#!/usr/bin/env python3
"""Events Category — editable schedule of model-level environment events.

Each row represents one Event (shypn.data.pathway.pathway_data.Event) that
lives in model.events.  The user can:
  - Add a new event (blank row, then edit inline)
  - Remove a selected event
  - Edit trigger, target place, value expression, and delay inline

On every user change the EventBus emits (document-scoped):
  model.environment.event_added   — when a row is added
  model.environment.event_removed — when a row is deleted
  model.environment.event_modified — when a cell is edited

Columns displayed:
  ID        — event.id (editable, user's label)
  Trigger   — event.trigger expression (e.g. ``t > 100``)
  Target    — first target place name (from first assignment key)
  Value     — first assignment value expression
  Delay     — event.delay (seconds)
"""
import logging
import uuid

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

logger = logging.getLogger(__name__)

_COL_ID, _COL_TRIGGER, _COL_TARGET, _COL_VALUE, _COL_DELAY = range(5)
_HEADERS = ('ID', 'Trigger', 'Target Place', 'Value Expr', 'Delay (s)')


class EventsCategory:
    """Editable TreeView for model.events (environment event schedule)."""

    def __init__(self, model=None, document_id=None):
        self.model = model
        self.document_id = document_id
        self._store = Gtk.ListStore(str, str, str, str, str)
        self._inhibit_edited = False
        self.widget = self._build_widget()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _build_widget(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # No title header here — CategoryFrame in environment_panel.py provides it

        # TreeView
        tv = Gtk.TreeView(model=self._store)
        tv.set_headers_visible(True)
        tv.set_enable_search(False)
        tv.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self._treeview = tv

        for col_idx, title in enumerate(_HEADERS):
            renderer = Gtk.CellRendererText()
            renderer.set_property('editable', True)
            renderer.set_property('ellipsize', 3)
            renderer.connect('edited', self._on_cell_edited, col_idx)
            col = Gtk.TreeViewColumn(title, renderer, text=col_idx)
            col.set_resizable(True)
            col.set_min_width(60)
            tv.append_column(col)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(100)
        scroll.add(tv)
        outer.pack_start(scroll, True, True, 0)

        # Toolbar: Add / Remove
        tb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        tb.set_margin_top(4)
        tb.set_margin_bottom(4)
        tb.set_margin_start(8)
        tb.set_margin_end(8)

        btn_add = Gtk.Button.new_with_label('+ Add Event')
        btn_add.set_tooltip_text('Add a new environment event')
        btn_add.connect('clicked', self._on_add_clicked)
        tb.pack_start(btn_add, False, False, 0)

        btn_remove = Gtk.Button.new_with_label('− Remove')
        btn_remove.set_tooltip_text('Remove selected event')
        btn_remove.connect('clicked', self._on_remove_clicked)
        tb.pack_start(btn_remove, False, False, 0)

        outer.pack_start(tb, False, False, 0)

        outer.show_all()
        return outer

    # ------------------------------------------------------------------
    # Cell editing
    # ------------------------------------------------------------------

    def _on_cell_edited(self, renderer, path_str, new_text, col_idx):
        if self._inhibit_edited:
            return
        it = self._store.get_iter(path_str)
        if it is None:
            return
        old_text = self._store.get_value(it, col_idx)
        if old_text == new_text:
            return
        self._store.set_value(it, col_idx, new_text)
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_modified', {})

    # ------------------------------------------------------------------
    # Add / Remove buttons
    # ------------------------------------------------------------------

    def _on_add_clicked(self, _btn):
        event_id = f'evt_{uuid.uuid4().hex[:6]}'
        self._store.append([event_id, 't > 0', '', '0', '0'])
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_added', {'event_id': event_id})

    def _on_remove_clicked(self, _btn):
        sel = self._treeview.get_selection()
        model, it = sel.get_selected()
        if it is None:
            return
        event_id = model.get_value(it, _COL_ID)
        model.remove(it)
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_removed', {'event_id': event_id})

    # ------------------------------------------------------------------
    # Store ↔ model synchronization
    # ------------------------------------------------------------------

    def _sync_store_to_model(self) -> None:
        """Write the current TreeView rows back to model.events."""
        if self.model is None:
            return
        try:
            from shypn.data.pathway.pathway_data import Event as ModelEvent
        except ImportError:
            return
        events = []
        for row in self._store:
            eid, trigger, target, value, delay_str = row[:]
            assignments = {}
            if target.strip():
                assignments[target.strip()] = value.strip() or '0'
            try:
                delay = float(delay_str)
            except (ValueError, TypeError):
                delay = 0.0
            events.append(ModelEvent(
                id=eid,
                name=eid,
                trigger=trigger,
                delay=delay,
                assignments=assignments,
            ))
        self.model.events = events

    def _sync_model_to_store(self) -> None:
        """Read model.events and populate the TreeView store."""
        self._inhibit_edited = True
        self._store.clear()
        if self.model is None:
            self._inhibit_edited = False
            return
        for event in getattr(self.model, 'events', []):
            eid = getattr(event, 'id', '') or ''
            trigger = getattr(event, 'trigger', '') or ''
            assignments = getattr(event, 'assignments', {}) or {}
            target = next(iter(assignments), '') if assignments else ''
            value = assignments.get(target, '') if target else ''
            delay = str(getattr(event, 'delay', 0.0))
            self._store.append([eid, trigger, target, value, delay])
        self._inhibit_edited = False

    # ------------------------------------------------------------------
    # EventBus emit helper
    # ------------------------------------------------------------------

    def _emit_bus(self, event_name: str, data: dict) -> None:
        try:
            from shypn.events import EventBus
            EventBus.emit(event_name, data, document_id=self.document_id)
        except Exception as exc:
            logger.debug('EventsCategory emit failed (%s): %s', event_name, exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_event_for_place(self, place_name: str) -> None:
        """Add a new environment event pre-filled with *place_name* as the target.

        Called when the user double-clicks a signal place row.  The new row is
        appended, selected, and scrolled into view so the user can edit it
        immediately.
        """
        event_id = f'evt_{uuid.uuid4().hex[:6]}'
        it = self._store.append([event_id, 't > 0', place_name.strip(), '0', '0'])
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_added', {'event_id': event_id})
        # Select + scroll to the new row
        path = self._store.get_path(it)
        self._treeview.get_selection().select_path(path)
        self._treeview.scroll_to_cell(path, None, False, 0.0, 0.0)

    def select_for_place(self, place_name: str) -> None:
        """Scroll to and select the first event whose Target Place matches *place_name*."""
        name = place_name.strip()
        for i, row in enumerate(self._store):
            if row[_COL_TARGET].strip() == name:
                path = Gtk.TreePath.new_from_indices([i])
                self._treeview.get_selection().select_path(path)
                self._treeview.scroll_to_cell(path, None, False, 0.0, 0.0)
                return

    def set_model(self, model) -> None:
        self.model = model
        self.refresh()

    def refresh(self) -> None:
        self._sync_model_to_store()
