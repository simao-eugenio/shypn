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
from gi.repository import Gtk, Gdk

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
        # Completion store for the Target column: columns are
        #   (display_text, place_name)
        # where display_text carries a marker suffix so the user sees at a
        # glance whether a candidate is a parameter / signal / regular place.
        self._target_store = Gtk.ListStore(str, str)
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
        # Enable Ctrl+C / Ctrl+V / F2 keyboard shortcuts and right-click
        # context menu so users can copy cell values without entering
        # edit mode and paste expressions in from external sources.
        tv.connect('key-press-event', self._on_treeview_key_press)
        tv.connect('button-press-event', self._on_treeview_button_press)
        self._treeview = tv

        for col_idx, title in enumerate(_HEADERS):
            if col_idx == _COL_TARGET:
                # Target column: combo renderer driven by self._target_store
                # (freeform text allowed — users may still type a name that is
                # not yet in the model, or a multi-target expression).
                renderer = Gtk.CellRendererCombo()
                renderer.set_property('model', self._target_store)
                renderer.set_property('text-column', 0)
                renderer.set_property('editable', True)
                renderer.set_property('has-entry', True)
                renderer.set_property('ellipsize', 3)
                renderer.connect('edited', self._on_target_edited, col_idx)
            else:
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

        btn_duplicate = Gtk.Button.new_with_label('⧉ Duplicate')
        btn_duplicate.set_tooltip_text('Insert a new row copied from the selected event '
                                        '(useful for building a series like evt_maint_1, _2, _3)')
        btn_duplicate.connect('clicked', self._on_duplicate_clicked)
        tb.pack_start(btn_duplicate, False, False, 0)

        btn_remove = Gtk.Button.new_with_label('− Remove')
        btn_remove.set_tooltip_text('Remove selected event')
        btn_remove.connect('clicked', self._on_remove_clicked)
        tb.pack_start(btn_remove, False, False, 0)

        outer.pack_start(tb, False, False, 0)

        outer.show_all()
        return outer

    # ------------------------------------------------------------------
    # Keyboard / mouse: copy / paste / edit on the focused cell
    # ------------------------------------------------------------------

    def _focused_cell(self):
        """Return ``(path, column, col_idx)`` for the currently focused cell, or ``None``."""
        path, column = self._treeview.get_cursor()
        if path is None or column is None:
            return None
        try:
            col_idx = self._treeview.get_columns().index(column)
        except ValueError:
            return None
        return path, column, col_idx

    def _on_treeview_key_press(self, _tv, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        keyval = event.keyval
        if ctrl and keyval in (Gdk.KEY_c, Gdk.KEY_C):
            self._copy_focused_cell()
            return True
        if ctrl and keyval in (Gdk.KEY_v, Gdk.KEY_V):
            self._paste_into_focused_cell()
            return True
        if keyval in (Gdk.KEY_F2, Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._start_editing_focused_cell()
            return True
        return False

    def _on_treeview_button_press(self, tv, event):
        if event.button != 3:  # right-click
            return False
        path_info = tv.get_path_at_pos(int(event.x), int(event.y))
        if path_info is None:
            return False
        path, column, _cx, _cy = path_info
        tv.set_cursor(path, column, False)
        self._show_context_menu(event)
        return True

    def _copy_focused_cell(self) -> None:
        focus = self._focused_cell()
        if focus is None:
            return
        path, _column, col_idx = focus
        try:
            it = self._store.get_iter(path)
        except (ValueError, TypeError):
            return
        text = self._store.get_value(it, col_idx) or ''
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)

    def _paste_into_focused_cell(self) -> None:
        focus = self._focused_cell()
        if focus is None:
            return
        path, _column, col_idx = focus
        try:
            it = self._store.get_iter(path)
        except (ValueError, TypeError):
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text = clipboard.wait_for_text() or ''
        if col_idx == _COL_TARGET:
            text = self._resolve_target_canonical(text)
        self._store.set_value(it, col_idx, text)
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_modified', {})

    def _start_editing_focused_cell(self) -> None:
        focus = self._focused_cell()
        if focus is None:
            return
        path, column, _col_idx = focus
        self._treeview.set_cursor_on_cell(path, column, None, True)

    def _show_context_menu(self, event) -> None:
        menu = Gtk.Menu()

        item_copy = Gtk.MenuItem.new_with_label('Copy cell  (Ctrl+C)')
        item_copy.connect('activate', lambda _w: self._copy_focused_cell())
        menu.append(item_copy)

        item_paste = Gtk.MenuItem.new_with_label('Paste into cell  (Ctrl+V)')
        item_paste.connect('activate', lambda _w: self._paste_into_focused_cell())
        menu.append(item_paste)

        item_edit = Gtk.MenuItem.new_with_label('Edit cell  (F2)')
        item_edit.connect('activate', lambda _w: self._start_editing_focused_cell())
        menu.append(item_edit)

        menu.append(Gtk.SeparatorMenuItem())

        item_duplicate = Gtk.MenuItem.new_with_label('Duplicate event row')
        item_duplicate.connect('activate', lambda _w: self._on_duplicate_clicked(None))
        menu.append(item_duplicate)

        item_remove = Gtk.MenuItem.new_with_label('Remove event row')
        item_remove.connect('activate', lambda _w: self._on_remove_clicked(None))
        menu.append(item_remove)

        menu.show_all()
        menu.popup_at_pointer(event)

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

    def _on_target_edited(self, renderer, path_str, new_text, col_idx):
        """Target combo edit — strip any '[kind]' marker the display may carry.

        The completion store holds rows like "LOADING_DOSE  [param:dose]"
        (display) → "LOADING_DOSE" (canonical name). When the user picks
        such a row, new_text arrives as the display string; resolve it
        back to the canonical name before writing to the model.
        """
        if self._inhibit_edited:
            return
        canonical = self._resolve_target_canonical(new_text)
        self._on_cell_edited(renderer, path_str, canonical, col_idx)

    def _resolve_target_canonical(self, text: str) -> str:
        """Map a combo-display string back to the place name, or return as-is."""
        if not text:
            return ''
        for row in self._target_store:
            if row[0] == text:
                return row[1]
        # User typed freeform text — keep it verbatim (may reference a place
        # that does not yet exist, or a multi-target expression).
        return text.strip()

    # ------------------------------------------------------------------
    # Add / Remove buttons
    # ------------------------------------------------------------------

    def _on_add_clicked(self, _btn):
        event_id = f'evt_{uuid.uuid4().hex[:6]}'
        self._store.append([event_id, 't > 0', '', '0', '0'])
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_added', {'event_id': event_id})

    def _on_duplicate_clicked(self, _btn):
        """Insert a new row that copies the currently selected event.

        The new row gets a fresh ``id`` (so it is uniquely addressable in
        ``model.events``) but inherits Trigger / Target / Value / Delay
        from the source row. This is the natural way to build a series
        like ``evt_maint_1``, ``evt_maint_2``, ``evt_maint_3`` where only
        the trigger time changes between rows.
        """
        sel = self._treeview.get_selection()
        store, it = sel.get_selected()
        if it is None:
            return
        # Snapshot the source row.
        src = [store.get_value(it, i) for i in range(store.get_n_columns())]
        # Mint a fresh id so the duplicate is independently addressable.
        new_id = f'evt_{uuid.uuid4().hex[:6]}'
        new_row = [new_id, src[_COL_TRIGGER], src[_COL_TARGET],
                   src[_COL_VALUE], src[_COL_DELAY]]
        new_it = self._store.insert_after(it, new_row)
        self._sync_store_to_model()
        self._emit_bus('model.environment.event_added', {'event_id': new_id})
        # Select + scroll to the new row so the user can edit it immediately.
        path = self._store.get_path(new_it)
        sel.select_path(path)
        self._treeview.scroll_to_cell(path, None, False, 0.0, 0.0)

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
        self._refresh_target_store()
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

    def _refresh_target_store(self) -> None:
        """Rebuild the Target column's completion list from the current model.

        Order:
          1. Parameter places (with [param:kind] marker) — most likely to be
             referenced by event expressions.
          2. Signal places (with [signal]).
          3. Regular places (no marker).
        """
        self._target_store.clear()
        if self.model is None:
            return
        params, signals, regulars = [], [], []
        for p in getattr(self.model, 'places', []):
            name = getattr(p, 'name', '') or ''
            if not name:
                continue
            if getattr(p, 'is_parameter_place', False):
                kind = getattr(p, 'parameter_kind', None) or '?'
                display = f'{name}  [param:{kind}]'
                params.append((display, name))
            elif getattr(p, 'is_signal_place', False):
                display = f'{name}  [signal]'
                signals.append((display, name))
            else:
                regulars.append((name, name))
        for display, name in params + signals + regulars:
            self._target_store.append([display, name])

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
