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
        self._selected_id = None

        super().__init__(model=self._store, has_entry=True)

        # Both columns must be set for full popup behaviour:
        #   set_entry_text_column  — renders text in dropdown popup; keeps
        #                            entry text in sync when active row changes
        #                            (GTK reads priv->text_column on entry update)
        #   set_id_column          — lets GTK commit a clicked popup row as the
        #                            active selection (without it clicks are lost)
        self.set_entry_text_column(self._COL_TEXT)
        self.set_id_column(self._COL_ID)

        entry = self.get_child()
        entry.set_placeholder_text("Type to search…")
        entry.connect("activate", self._on_entry_activate)

        # Replace the EntryCompletion that GTK created in gtk_combo_box_constructed
        # (which has GTK's own match-selected handler that would block ours via
        # the g_signal_accumulator_true_handled chain) with a fresh one that only
        # has our substring-match handler.
        # NOTE: entry.set_completion must come AFTER set_entry_text_column so
        # that GTK's priv->text_column is configured before our completion is
        # installed; GTK's entry-sync path uses priv->text_column, not the
        # completion's text_column, so it keeps working after we swap it out.
        completion = Gtk.EntryCompletion()
        completion.set_model(self._store)
        completion.set_text_column(self._COL_TEXT)
        completion.set_match_func(self._match_func)
        completion.set_minimum_key_length(1)
        completion.set_inline_completion(False)
        completion.set_popup_completion(True)
        completion.connect("match-selected", self._on_match_selected)
        entry.set_completion(completion)

        # Track _selected_id for every selection (popup click, set_active*, …)
        self.connect("changed", self._on_changed)

        if tooltip_text:
            self.set_tooltip_text(tooltip_text)

    # ── EntryCompletion helpers ────────────────────────────────────────────

    def _match_func(self, completion, key, tree_iter):
        """Substring, case-insensitive match (key is already case-folded by GTK)."""
        text = completion.get_model()[tree_iter][self._COL_TEXT]
        return bool(text) and key.lower() in text.lower()

    def _on_match_selected(self, completion, model, tree_iter):
        """User clicked/Enter-selected a row in the EntryCompletion popup.

        We capture the ID and let the default handler run (return value is
        implicitly False/None): it sets the entry text to the matched row's
        text.  GTK's combo entry-changed handler then fires, finds the text
        in the store, and sets the active row — which in turn emits 'changed'
        and triggers _on_changed.  No need to call set_active() ourselves.
        """
        self._selected_id = model[tree_iter][self._COL_ID]
        # Return nothing (None → False) so the default EntryCompletion handler
        # runs and updates the entry text, which chain-triggers active-row sync.

    def _on_entry_activate(self, entry):
        """Enter key: commit first substring match."""
        key = entry.get_text().lower()
        if not key:
            return
        for i, row in enumerate(self._store):
            if key in row[self._COL_TEXT].lower():
                Gtk.ComboBox.set_active(self, i)
                return

    # ── Active-row tracking ────────────────────────────────────────────────

    def _on_changed(self, combo):
        """Sync _selected_id on every GTK-side active-row change."""
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            self._selected_id = self._store[tree_iter][self._COL_ID]

    # ── ComboBoxText-compatible public API ─────────────────────────────────

    def get_active_id(self):
        return self._selected_id

    def set_active_id(self, item_id: str) -> bool:
        for i, row in enumerate(self._store):
            if row[self._COL_ID] == item_id:
                Gtk.ComboBox.set_active(self, i)
                return True
        return False

    def set_active(self, index: int) -> None:
        if index >= 0:
            Gtk.ComboBox.set_active(self, index)

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
