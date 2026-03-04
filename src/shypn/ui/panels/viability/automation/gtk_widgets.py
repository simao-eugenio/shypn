#!/usr/bin/env python3
"""Shared GTK widget utilities for the viability automation panels.

Provides reusable custom widgets that fix known GTK3 UX limitations.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class SearchableComboBox(Gtk.ComboBox):
    """Scrollable, searchable drop-in replacement for Gtk.ComboBoxText.

    GTK3 ComboBoxText does not scroll its popup when item count exceeds the
    screen height — making bottom entries unreachable.  This widget uses a
    real ListStore backend so the popup always shows a scrollbar, and embeds
    a text entry with EntryCompletion so the user can type to filter/jump
    to any item immediately.

    Public API is fully compatible with Gtk.ComboBoxText:
        append(id_str, text)   — same as ComboBoxText.append(id, text)
        append_text(text)      — same as ComboBoxText.append_text(text)
        remove_all()           — same as ComboBoxText.remove_all()
        get_active_id()        — inherited from Gtk.ComboBox
        set_active_id(id_str)  — inherited from Gtk.ComboBox
        set_active(index)      — inherited from Gtk.ComboBox
        get_active_text()      — returns the entry widget's current text
        connect("changed", …)  — inherited from Gtk.ComboBox
    """

    _COL_ID   = 0
    _COL_TEXT = 1

    def __init__(self, tooltip_text: str = ""):
        self._store = Gtk.ListStore(str, str)   # (id, display_text)
        super().__init__(model=self._store, has_entry=True)
        self.set_id_column(self._COL_ID)
        self.set_entry_text_column(self._COL_TEXT)

        entry = self.get_child()
        entry.set_placeholder_text("Type to search…")

        # Build EntryCompletion with case-insensitive substring matching.
        # GTK may auto-create a completion via set_entry_text_column; replace
        # it unconditionally so we control the match function.
        completion = Gtk.EntryCompletion()
        completion.set_model(self._store)
        completion.set_text_column(self._COL_TEXT)
        # Substring, case-insensitive: "temp" matches "Temperature (K)"
        completion.set_match_func(self._match_func)
        completion.set_minimum_key_length(1)
        completion.set_inline_completion(False)   # don't auto-fill — confusing for substrings
        completion.set_popup_completion(True)
        # When user picks an entry from the completion popup, sync the combo
        completion.connect("match-selected", self._on_completion_match_selected)
        entry.set_completion(completion)

        # Also handle Enter: select the first substring match in the store
        entry.connect("activate", self._on_entry_activate)

        if tooltip_text:
            self.set_tooltip_text(tooltip_text)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _match_func(self, completion, key, tree_iter):
        """Case-insensitive substring match for EntryCompletion."""
        model = completion.get_model()
        text = model[tree_iter][self._COL_TEXT]
        if not text:
            return False
        return key.lower() in text.lower()

    def _on_completion_match_selected(self, completion, model, tree_iter):
        """Sync the ComboBox active item when a completion entry is clicked."""
        item_id   = model[tree_iter][self._COL_ID]
        item_text = model[tree_iter][self._COL_TEXT]
        self.set_active_id(item_id)
        # Also update the entry text — set_active_id alone doesn't always
        # repaint the embedded entry when returning True
        entry = self.get_child()
        if entry is not None:
            entry.set_text(item_text)
            entry.set_position(-1)   # move cursor to end
        return True   # prevent default (which would double-set entry text)

    def _on_entry_activate(self, entry):
        """On Enter, select the first store row whose text contains the typed key."""
        key = entry.get_text().lower()
        if not key:
            return
        for row in self._store:
            if key in row[self._COL_TEXT].lower():
                self.set_active_id(row[self._COL_ID])
                break

    # ── ComboBoxText-compatible API ────────────────────────────────────────

    def append(self, id_str: str, text: str) -> None:
        """Append an item. Equivalent to Gtk.ComboBoxText.append(id, text)."""
        self._store.append([id_str, text])

    def append_text(self, text: str) -> None:
        """Append an item using text as both id and display value.

        Equivalent to Gtk.ComboBoxText.append_text(text).
        get_active_id() will return the same string as get_active_text().
        """
        self._store.append([text, text])

    def remove_all(self) -> None:
        """Remove all items. Equivalent to Gtk.ComboBoxText.remove_all()."""
        self._store.clear()
        # Also clear the embedded entry so the box looks blank
        entry = self.get_child()
        if entry is not None:
            entry.set_text("")

    def get_active_text(self) -> str:
        """Return current entry text. Equivalent to Gtk.ComboBoxText.get_active_text()."""
        entry = self.get_child()
        return entry.get_text() if entry is not None else ""
