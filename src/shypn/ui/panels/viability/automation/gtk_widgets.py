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
    (substring, case-insensitive).  Clicking any match completes the
    selection.  Enter auto-selects the first substring match.
    The dropdown arrow still works to browse all items with a scrollbar.

    Public API is fully compatible with Gtk.ComboBoxText:
        append(id_str, text)   — same as ComboBoxText.append(id, text)
        append_text(text)      — same as ComboBoxText.append_text(text)
        remove_all()           — same as ComboBoxText.remove_all()
        get_active_id()        — inherited from Gtk.ComboBox
        set_active_id(id_str)  — overridden
        set_active(index)      — inherited from Gtk.ComboBox
        get_active_text()      — returns current entry text
        connect("changed", …)  — inherited from Gtk.ComboBox
    """

    _COL_ID   = 0
    _COL_TEXT = 1

    def __init__(self, tooltip_text: str = ""):
        self._store = Gtk.ListStore(str, str)   # (id, display_text)
        self._busy  = False

        super().__init__(model=self._store, has_entry=True)
        self.set_id_column(self._COL_ID)
        self.set_entry_text_column(self._COL_TEXT)

        entry = self.get_child()
        entry.set_placeholder_text("Type to search…")

        # ── EntryCompletion: separate popup, does NOT overwrite the entry ──
        completion = Gtk.EntryCompletion()
        completion.set_model(self._store)
        completion.set_text_column(self._COL_TEXT)
        completion.set_match_func(self._match_func)
        completion.set_minimum_key_length(1)
        completion.set_inline_completion(False)  # no auto-fill while typing
        completion.set_popup_completion(True)
        completion.connect("match-selected", self._on_match_selected)
        entry.set_completion(completion)

        # Enter key: commit first substring match
        entry.connect("activate", self._on_entry_activate)

        if tooltip_text:
            self.set_tooltip_text(tooltip_text)

    # ── match / commit helpers ─────────────────────────────────────────────

    def _match_func(self, completion, key, tree_iter):
        text = completion.get_model()[tree_iter][self._COL_TEXT]
        return bool(text) and key.lower() in text.lower()

    def _on_match_selected(self, completion, model, tree_iter):
        """User clicked a row in the completion popup — commit selection."""
        self._commit(model[tree_iter][self._COL_ID],
                     model[tree_iter][self._COL_TEXT])
        return True   # suppress GTK default (avoids double entry.set_text)

    def _on_entry_activate(self, entry):
        """Enter: commit first substring match."""
        key = entry.get_text().lower()
        if not key:
            return
        for row in self._store:
            if key in row[self._COL_TEXT].lower():
                self._commit(row[self._COL_ID], row[self._COL_TEXT])
                return

    def _commit(self, item_id: str, item_text: str) -> None:
        """Finalize selection: set active row and fill entry text."""
        self._busy = True
        try:
            super().set_active_id(item_id)
            entry = self.get_child()
            if entry is not None:
                entry.set_text(item_text)
                entry.set_position(-1)
            self.popdown()
        finally:
            self._busy = False

    # ── ComboBoxText-compatible public API ─────────────────────────────────

    def set_active_id(self, item_id: str) -> bool:
        for row in self._store:
            if row[self._COL_ID] == item_id:
                self._commit(item_id, row[self._COL_TEXT])
                return True
        return False

    def append(self, id_str: str, text: str) -> None:
        self._store.append([id_str, text])

    def append_text(self, text: str) -> None:
        self._store.append([text, text])

    def remove_all(self) -> None:
        self._store.clear()
        entry = self.get_child()
        if entry is not None:
            entry.set_text("")

    def get_active_text(self) -> str:
        entry = self.get_child()
        return entry.get_text() if entry is not None else ""
