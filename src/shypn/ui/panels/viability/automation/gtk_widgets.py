#!/usr/bin/env python3
"""Shared GTK widget utilities for the viability automation panels.

Provides reusable custom widgets that fix known GTK3 UX limitations.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class SearchableComboBox(Gtk.ComboBox):
    """Scrollable, searchable drop-in replacement for Gtk.ComboBoxText.

    Typing into the embedded entry shows a filtered completion popup
    (substring, case-insensitive).  Clicking any match or pressing Enter
    completes the selection.  The dropdown arrow lists all items with a
    scrollbar.

    Public API is fully compatible with Gtk.ComboBoxText:
        append(id_str, text)   — same as ComboBoxText.append(id, text)
        append_text(text)      — same as ComboBoxText.append_text(text)
        remove_all()           — same as ComboBoxText.remove_all()
        get_active_id()        — returns currently selected id
        set_active_id(id_str)  — select by id
        set_active(index)      — select by store index
        get_active_text()      — returns current entry text
        connect("changed", …)  — emitted after every selection commit
    """

    _COL_ID   = 0
    _COL_TEXT = 1

    def __init__(self, tooltip_text: str = ""):
        self._store       = Gtk.ListStore(str, str)   # (id, display_text)
        self._selected_id = None   # track selection ourselves
        self._busy        = False

        # Give the combo the store so the dropdown arrow still works
        super().__init__(model=self._store, has_entry=True)
        # Do NOT call set_id_column / set_entry_text_column — those cause
        # GTK to overwrite the entry whenever set_active* changes the row.
        # We manage entry text entirely in _commit().

        # Pack a cell renderer so the dropdown popup can display items.
        # Gtk.ComboBox (unlike ComboBoxText) does not add one automatically.
        renderer = Gtk.CellRendererText()
        self.pack_start(renderer, True)
        self.add_attribute(renderer, "text", self._COL_TEXT)

        entry = self.get_child()
        entry.set_placeholder_text("Type to search…")

        # EntryCompletion: separate popup, substring match, never touches entry
        completion = Gtk.EntryCompletion()
        completion.set_model(self._store)
        completion.set_text_column(self._COL_TEXT)
        completion.set_match_func(self._match_func)
        completion.set_minimum_key_length(1)
        completion.set_inline_completion(False)
        completion.set_popup_completion(True)
        completion.connect("match-selected", self._on_match_selected)
        entry.set_completion(completion)

        entry.connect("activate", self._on_entry_activate)

        if tooltip_text:
            self.set_tooltip_text(tooltip_text)

    # ── EntryCompletion helpers ────────────────────────────────────────────

    def _match_func(self, completion, key, tree_iter):
        text = completion.get_model()[tree_iter][self._COL_TEXT]
        return bool(text) and key.lower() in text.lower()

    def _on_match_selected(self, completion, model, tree_iter):
        """User clicked a row in the completion popup."""
        self._commit(model[tree_iter][self._COL_ID],
                     model[tree_iter][self._COL_TEXT])
        return True   # prevent GTK default (it would set wrong text)

    def _on_entry_activate(self, entry):
        """Enter: commit first substring match."""
        key = entry.get_text().lower()
        if not key:
            return
        for row in self._store:
            if key in row[self._COL_TEXT].lower():
                self._commit(row[self._COL_ID], row[self._COL_TEXT])
                return

    # ── core selection ─────────────────────────────────────────────────────

    def _commit(self, item_id: str, item_text: str) -> None:
        """Store selection, update entry text, emit 'changed'."""
        if self._busy:
            return
        self._busy = True
        try:
            self._selected_id = item_id
            entry = self.get_child()
            if entry is not None:
                entry.set_text(item_text)
                entry.set_position(-1)
            # Emit 'changed' so callers connected to combo.changed() are notified
            self.emit("changed")
        finally:
            self._busy = False

    # ── ComboBoxText-compatible public API ─────────────────────────────────

    def get_active_id(self):
        return self._selected_id

    def set_active_id(self, item_id: str) -> bool:
        for row in self._store:
            if row[self._COL_ID] == item_id:
                self._commit(item_id, row[self._COL_TEXT])
                return True
        return False

    def set_active(self, index: int) -> None:
        try:
            row = self._store[index]
            self._commit(row[self._COL_ID], row[self._COL_TEXT])
        except IndexError:
            pass

    def append(self, id_str: str, text: str) -> None:
        self._store.append([id_str, text])

    def append_text(self, text: str) -> None:
        self._store.append([text, text])

    def remove_all(self) -> None:
        self._selected_id = None
        self._store.clear()
        entry = self.get_child()
        if entry is not None:
            entry.set_text("")

    def get_active_text(self) -> str:
        entry = self.get_child()
        return entry.get_text() if entry is not None else ""
