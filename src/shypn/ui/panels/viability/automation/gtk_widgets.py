#!/usr/bin/env python3
"""Shared GTK widget utilities for the viability automation panels.

Provides reusable custom widgets that fix known GTK3 UX limitations.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class SearchableComboBox(Gtk.ComboBox):
    """Scrollable, searchable drop-in replacement for Gtk.ComboBoxText.

    Typing filters the combo's own dropdown popup in real time (substring,
    case-insensitive).  Matching items appear at the top of the open popup;
    clicking any of them completes the selection.  Enter auto-selects the
    first match.

    Public API is fully compatible with Gtk.ComboBoxText:
        append(id_str, text)   — same as ComboBoxText.append(id, text)
        append_text(text)      — same as ComboBoxText.append_text(text)
        remove_all()           — same as ComboBoxText.remove_all()
        get_active_id()        — inherited from Gtk.ComboBox
        set_active_id(id_str)  — overridden (clears filter before selecting)
        set_active(index)      — inherited from Gtk.ComboBox
        get_active_text()      — returns the entry widget's current text
        connect("changed", …)  — inherited from Gtk.ComboBox
    """

    _COL_ID   = 0
    _COL_TEXT = 1

    def __init__(self, tooltip_text: str = ""):
        self._store      = Gtk.ListStore(str, str)   # full item list
        self._filter     = self._store.filter_new()  # live-filtered view
        self._filter_key = ""
        self._busy       = False  # re-entrancy guard

        self._filter.set_visible_func(self._filter_visible_func)

        super().__init__(model=self._filter, has_entry=True)
        self.set_id_column(self._COL_ID)
        self.set_entry_text_column(self._COL_TEXT)

        entry = self.get_child()
        entry.set_placeholder_text("Type to search…")
        entry.connect("changed", self._on_entry_changed)
        entry.connect("activate", self._on_entry_activate)

        # Catch when the user picks an item from the dropdown popup
        self.connect("changed", self._on_combo_changed)

        if tooltip_text:
            self.set_tooltip_text(tooltip_text)

    # ── filter ─────────────────────────────────────────────────────────────

    def _filter_visible_func(self, model, tree_iter, _data):
        if not self._filter_key:
            return True
        text = model[tree_iter][self._COL_TEXT]
        return bool(text) and self._filter_key.lower() in text.lower()

    # ── signal handlers ────────────────────────────────────────────────────

    def _on_entry_changed(self, entry):
        """User is typing: refilter and (re-)open the popup."""
        if self._busy:
            return
        self._filter_key = entry.get_text()
        self._filter.refilter()
        if self._filter_key:
            # Defer popup() so it doesn't fight the keypress event
            GLib.idle_add(self.popup)

    def _on_combo_changed(self, combo):
        """User clicked an item in the dropdown: commit that selection."""
        if self._busy:
            return
        tree_iter = self.get_active_iter()
        if tree_iter is None:
            return
        item_id   = self._filter[tree_iter][self._COL_ID]
        item_text = self._filter[tree_iter][self._COL_TEXT]
        self._commit(item_id, item_text)

    def _on_entry_activate(self, entry):
        """Enter key: commit the first store row matching the typed text."""
        key = entry.get_text().lower()
        if not key:
            return
        for row in self._store:
            if key in row[self._COL_TEXT].lower():
                self._commit(row[self._COL_ID], row[self._COL_TEXT])
                return

    # ── commit helper ───────────────────────────────────────────────────────

    def _commit(self, item_id: str, item_text: str) -> None:
        """Finalize a selection: clear filter, set active row, fill entry."""
        self._busy = True
        try:
            self._filter_key = ""
            self._filter.refilter()
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
        """Select by id, clearing the filter first so the item is reachable."""
        for row in self._store:
            if row[self._COL_ID] == item_id:
                self._commit(item_id, row[self._COL_TEXT])
                return True
        return False

    def append(self, id_str: str, text: str) -> None:
        """Append an item. Equivalent to Gtk.ComboBoxText.append(id, text)."""
        self._store.append([id_str, text])

    def append_text(self, text: str) -> None:
        """Append item using text as both id and display value."""
        self._store.append([text, text])

    def remove_all(self) -> None:
        """Remove all items. Equivalent to Gtk.ComboBoxText.remove_all()."""
        self._busy = True
        try:
            self._filter_key = ""
            self._store.clear()
            entry = self.get_child()
            if entry is not None:
                entry.set_text("")
        finally:
            self._busy = False

    def get_active_text(self) -> str:
        """Return current entry text. Equivalent to Gtk.ComboBoxText.get_active_text()."""
        entry = self.get_child()
        return entry.get_text() if entry is not None else ""
