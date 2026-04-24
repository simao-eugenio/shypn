#!/usr/bin/env python3
"""Experiment Queue View - Display and manage queued experiments.

Shows a list of experiments to be executed with their status, progress,
and control actions. Integrates with BatchExecutor for execution.

Author: Simão Eugénio
Date: December 7, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango


class ExperimentQueueView(Gtk.Box):
    """Widget displaying experiment queue with status and controls.
    
    Features:
    - TreeView showing queued experiments
    - Status indicators (pending/running/completed/failed)
    - Progress tracking per experiment
    - Control buttons (run/pause/clear)
    """
    
    # Status constants
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(self):
        """Initialize experiment queue view."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Queue data: list of dicts with experiment info
        self.queue = []
        
        # Callbacks
        self.on_run_callback = None
        self.on_cancel_callback = None
        self.on_clear_callback = None
        self.on_pause_callback = None  # Stage 3
        self.on_run_remote_callback = None  # Remote dispatch
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build queue view UI."""
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Experiment Queue</b>")
        title_label.set_xalign(0)
        self.pack_start(title_label, False, False, 0)
        
        # Queue TreeView in ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        # Create ListStore: name, status, progress, snapshot_index
        # Columns: 0=name (str), 1=status (str), 2=progress (str), 3=snapshot_index (int)
        self.queue_store = Gtk.ListStore(str, str, str, int)
        
        # Create TreeView
        self.queue_tree = Gtk.TreeView(model=self.queue_store)
        self.queue_tree.set_headers_visible(True)
        
        # Column 1: Experiment Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Experiment", renderer_name, text=0)
        column_name.set_expand(True)
        column_name.set_resizable(True)
        self.queue_tree.append_column(column_name)
        
        # Column 2: Status
        renderer_status = Gtk.CellRendererText()
        column_status = Gtk.TreeViewColumn("Status", renderer_status, text=1)
        column_status.set_min_width(100)
        column_status.set_resizable(True)
        self.queue_tree.append_column(column_status)
        
        # Column 3: Progress
        renderer_progress = Gtk.CellRendererText()
        column_progress = Gtk.TreeViewColumn("Progress", renderer_progress, text=2)
        column_progress.set_min_width(80)
        column_progress.set_resizable(True)
        self.queue_tree.append_column(column_progress)
        
        scrolled.add(self.queue_tree)
        self.pack_start(scrolled, True, True, 0)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Run All button
        self.run_button = Gtk.Button(label="▶ Run All")
        self.run_button.set_tooltip_text("Execute all pending experiments")
        self.run_button.connect("clicked", self._on_run_clicked)
        button_box.pack_start(self.run_button, False, False, 0)
        
        # Run Remote button
        self.run_remote_button = Gtk.Button(label="☁ Run Remote")
        self.run_remote_button.set_tooltip_text(
            "Dispatch sweep to remote server via SSH.\n"
            "Uploads model + config, runs CLI remotely, fetches results."
        )
        self.run_remote_button.connect("clicked", self._on_run_remote_clicked)
        button_box.pack_start(self.run_remote_button, False, False, 0)
        
        # Pause/Resume button (Stage 3)
        self.pause_button = Gtk.Button(label="⏸ Pause")
        self.pause_button.set_tooltip_text("Pause execution after current experiment")
        self.pause_button.set_sensitive(False)
        self.pause_button.connect("clicked", self._on_pause_clicked)
        button_box.pack_start(self.pause_button, False, False, 0)
        
        # Cancel button
        self.cancel_button = Gtk.Button(label="⏹ Stop")
        self.cancel_button.set_tooltip_text("Stop execution immediately")
        self.cancel_button.set_sensitive(False)
        self.cancel_button.connect("clicked", self._on_cancel_clicked)
        button_box.pack_start(self.cancel_button, False, False, 0)
        
        # Clear Completed button
        clear_button = Gtk.Button(label="Clear Completed")
        clear_button.set_tooltip_text("Remove completed experiments from queue")
        clear_button.connect("clicked", self._on_clear_clicked)
        button_box.pack_start(clear_button, False, False, 0)
        
        # Reset All button
        reset_button = Gtk.Button(label="⟲ Reset All")
        reset_button.set_tooltip_text("Reset all completed/failed experiments back to pending")
        reset_button.connect("clicked", self._on_reset_clicked)
        button_box.pack_start(reset_button, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        button_box.pack_start(separator, False, False, 0)
        
        # Parallel execution checkbox (E2 enhancement)
        self.parallel_checkbox = Gtk.CheckButton(label="Parallel Execution")
        self.parallel_checkbox.set_tooltip_text(
            "Execute experiments in parallel using multiple CPU cores\n"
            "Significantly faster for large batches (e.g., 100 experiments: 6h → 36min)"
        )
        self.parallel_checkbox.set_active(True)  # Default: enabled for speed
        button_box.pack_start(self.parallel_checkbox, False, False, 0)
        
        self.pack_start(button_box, False, False, 0)

        # Status bar — scrollable, selectable, copyable text view.
        # Acts as a category-aware append-only log so messages from
        # different sources (setup, allocation, stream, events, results)
        # never overwrite each other.
        status_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        status_title = Gtk.Label()
        status_title.set_markup('<small><b>Activity log</b></small>')
        status_title.set_xalign(0)
        status_header.pack_start(status_title, True, True, 0)
        # Explicit Copy button: works even if the textview never gets
        # keyboard focus (some embedding contexts steal focus, making
        # Ctrl+C unreliable). Copies the current selection or, if none,
        # the entire log.
        self._status_copy_btn = Gtk.Button(label='Copy')
        self._status_copy_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._status_copy_btn.set_tooltip_text(
            'Copy selection (or full log if nothing selected) to clipboard')
        self._status_copy_btn.connect(
            'clicked', lambda *_: self._copy_status_to_clipboard())
        status_header.pack_end(self._status_copy_btn, False, False, 0)
        self._status_clear_btn = Gtk.Button(label='Clear')
        self._status_clear_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._status_clear_btn.set_tooltip_text('Clear the activity log')
        self._status_clear_btn.connect('clicked', lambda *_: self.clear_status())
        status_header.pack_end(self._status_clear_btn, False, False, 0)
        self.pack_start(status_header, False, False, 0)

        # Sticky summary line — always visible, never scrolls. Updated
        # by _update_status_label() whenever queue state changes.
        self._status_summary = Gtk.Label()
        self._status_summary.set_xalign(0)
        self._status_summary.set_margin_start(4)
        self._status_summary.set_margin_end(4)
        self._status_summary.set_margin_top(1)
        self._status_summary.set_margin_bottom(1)
        self._status_summary.override_font(
            Pango.FontDescription.from_string('monospace 9'))
        self._status_summary.set_markup(
            "<small><span foreground='#888888'><i>Queue empty</i></span></small>")
        self.pack_start(self._status_summary, False, False, 0)

        status_scroll = Gtk.ScrolledWindow()
        status_scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                 Gtk.PolicyType.AUTOMATIC)
        status_scroll.set_min_content_height(72)
        status_scroll.set_max_content_height(160)

        self._status_view = Gtk.TextView()
        self._status_view.set_editable(False)
        self._status_view.set_cursor_visible(True)
        self._status_view.set_can_focus(True)
        self._status_view.set_focus_on_click(True)
        self._status_view.connect('key-press-event', self._on_status_key_press)
        # Force focus on click — some parent containers steal keyboard
        # focus on tab switches, leaving the textview unfocused even
        # after the user clicks into it. Without focus, the default
        # GTK Ctrl+C binding cannot reach the textview.
        self._status_view.connect(
            'button-press-event',
            lambda w, e: (w.grab_focus(), False)[1])
        # Right-click → context menu with our Copy entry guaranteed
        # to be present (the default popup may be overridden by themes).
        self._status_view.connect(
            'populate-popup', self._on_status_populate_popup)
        self._status_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._status_view.set_left_margin(4)
        self._status_view.set_right_margin(4)
        self._status_view.set_top_margin(2)
        self._status_view.set_bottom_margin(2)
        self._status_view.override_font(
            Pango.FontDescription.from_string('monospace 9'))

        self._status_buffer = self._status_view.get_buffer()
        # Coloured tags for category visual coding
        self._status_buffer.create_tag('blue', foreground='#3465a4')
        self._status_buffer.create_tag('green', foreground='#4e9a06')
        self._status_buffer.create_tag('red', foreground='#cc0000')
        self._status_buffer.create_tag('orange', foreground='#ce5c00')
        self._status_buffer.create_tag('grey', foreground='#888888')
        self._status_buffer.create_tag('bold',
                                       weight=Pango.Weight.BOLD)
        self._status_buffer.create_tag('italic',
                                       style=Pango.Style.ITALIC)

        # Append-log bookkeeping
        self._status_max_lines = 200
        self._status_last_line = None  # (category, text) for dedup

        status_scroll.add(self._status_view)
        self.pack_start(status_scroll, False, False, 0)

        # Keep legacy attribute name for callers that do
        # ``self.queue_view.status_label.set_markup(...)``
        self.status_label = _StatusLabelCompat(self)
    
    def add_experiment(self, name, snapshot_index):
        """Add experiment to queue.
        
        Args:
            name: Experiment name (from snapshot)
            snapshot_index: Index of snapshot in ExperimentManager
        """
        self.queue_store.append([name, self.STATUS_PENDING, "0%", snapshot_index])
        self._update_status_label()
    
    def add_experiments(self, experiments):
        """Add multiple experiments to queue.
        
        Args:
            experiments: List of (name, snapshot_index) tuples
        """
        for name, snapshot_index in experiments:
            self.add_experiment(name, snapshot_index)
    
    def clear_queue(self):
        """Clear all experiments from queue."""
        self.queue_store.clear()
        self._update_status_label()
    
    def clear_completed(self):
        """Remove completed experiments from queue."""
        iter = self.queue_store.get_iter_first()
        while iter:
            status = self.queue_store.get_value(iter, 1)
            if status == self.STATUS_COMPLETED:
                # Store next iter before removing current
                next_iter = self.queue_store.iter_next(iter)
                self.queue_store.remove(iter)
                iter = next_iter
            else:
                iter = self.queue_store.iter_next(iter)
        self._update_status_label()
    
    def update_experiment_status(self, index, status, progress=None):
        """Update experiment status and progress.
        
        Args:
            index: Row index in queue (TreeView row number)
            status: New status (pending/running/completed/failed/cancelled)
            progress: Optional progress string (e.g., "50%", "100%", error message)
        """
        try:
            # Validate index is within bounds
            if index < 0 or index >= len(self.queue_store):
                # Row no longer exists (queue was cleared/modified)
                return
            
            # Get iterator for the row
            iter = self.queue_store.get_iter(index)
            if not iter:
                # print(f"[QUEUE_VIEW] ERROR: Could not get iter for index {index}")
                return
            
            # Get experiment name for logging (disabled for performance)
            # name = self.queue_store.get_value(iter, 0)
            # print(f"[QUEUE_VIEW] Updating '{name}' (row {index}): status={status}, progress={progress}")
            
            # Update status (column 1)
            self.queue_store.set_value(iter, 1, status)
            
            # Update progress (column 2) if provided
            if progress is not None:
                self.queue_store.set_value(iter, 2, str(progress))
            
            # Update global status label
            self._update_status_label()
            
            # print(f"[QUEUE_VIEW] Successfully updated '{name}' to {status}")
            
        except Exception as e:
            # print(f"[QUEUE_VIEW] ERROR: update_experiment_status failed for index {index}: {e}")
            import traceback
            traceback.print_exc()
    
    def get_pending_experiments(self):
        """Get list of pending experiments.
        
        Returns:
            list: List of (index, name, snapshot_index) tuples for pending experiments
        """
        pending = []
        iter = self.queue_store.get_iter_first()
        index = 0
        while iter:
            status = self.queue_store.get_value(iter, 1)
            if status == self.STATUS_PENDING:
                name = self.queue_store.get_value(iter, 0)
                snapshot_index = self.queue_store.get_value(iter, 3)
                pending.append((index, name, snapshot_index))
            iter = self.queue_store.iter_next(iter)
            index += 1
        return pending
    
    def set_running(self, is_running, is_paused=False):
        """Update UI for running/stopped/paused state (Stage 3).
        
        Args:
            is_running: True if execution is running or paused
            is_paused: True if execution is paused (requires is_running=True)
        """
        # Button states
        self.run_button.set_sensitive(not is_running)
        self.cancel_button.set_sensitive(is_running)
        self.pause_button.set_sensitive(is_running)  # Stage 3
        
        # Update pause button label based on paused state
        if is_paused:
            self.pause_button.set_label("▶ Resume")
            self.pause_button.set_tooltip_text("Resume execution")
        else:
            self.pause_button.set_label("⏸ Pause")
            self.pause_button.set_tooltip_text("Pause execution after current experiment")
        
        # Update status label to reflect running/paused state
        if is_running:
            # Count all statuses so the label always shows the full picture
            running = 0
            pending = 0
            completed = 0
            failed = 0
            iter = self.queue_store.get_iter_first()
            while iter:
                status = self.queue_store.get_value(iter, 1)
                if status == self.STATUS_RUNNING:
                    running += 1
                elif status == self.STATUS_PENDING:
                    pending += 1
                elif status == self.STATUS_COMPLETED:
                    completed += 1
                elif status == self.STATUS_FAILED:
                    failed += 1
                iter = self.queue_store.iter_next(iter)

            total = running + pending + completed + failed
            done_str = f", {completed} done" if completed > 0 else ""
            failed_str = f", <span foreground='red'>{failed} failed</span>" if failed > 0 else ""

            if is_paused:
                self._write_summary(
                    f"<small><span foreground='#ce5c00'><b>Paused</b> — "
                    f"{running} active, {pending} pending{done_str}{failed_str} "
                    f"/ {total} total</span></small>"
                )
            elif running > 0 or pending > 0:
                self._write_summary(
                    f"<small><b>Running…</b> {running} active, {pending} pending"
                    f"{done_str}{failed_str} / {total} total</small>"
                )
        else:
            # Not running - refresh normal summary
            self._update_status_label()
    
    def _update_status_label(self):
        """Update the sticky summary label with queue statistics."""
        total = len(self.queue_store)
        if total == 0:
            self._write_summary(
                "<small><span foreground='#888888'><i>Queue empty</i></span></small>")
            return False  # For GLib.timeout_add
        
        # Count by status
        pending = 0
        running = 0
        completed = 0
        failed = 0
        cancelled = 0
        
        iter = self.queue_store.get_iter_first()
        while iter:
            status = self.queue_store.get_value(iter, 1)
            if status == self.STATUS_PENDING:
                pending += 1
            elif status == self.STATUS_RUNNING:
                running += 1
            elif status == self.STATUS_COMPLETED:
                completed += 1
            elif status == self.STATUS_FAILED:
                failed += 1
            elif status == self.STATUS_CANCELLED:
                cancelled += 1
            iter = self.queue_store.iter_next(iter)
        
        # Build status text
        parts = []
        if pending > 0:
            parts.append(f"{pending} pending")
        if running > 0:
            parts.append(f"<b>{running} running</b>")
        if completed > 0:
            parts.append(f"{completed} completed")
        if cancelled > 0:
            parts.append(f"<span foreground='#ce5c00'>{cancelled} cancelled</span>")
        if failed > 0:
            parts.append(f"<span foreground='#cc0000'>{failed} failed</span>")
        
        status_text = f"<small>{total} total: {', '.join(parts)}</small>"
        self._write_summary(status_text)
        return False  # For GLib.timeout_add

    def _write_summary(self, markup: str) -> None:
        """Write Pango markup to the sticky summary label (above the log)."""
        try:
            self._status_summary.set_markup(markup)
        except Exception:
            # Fallback to plain text
            import re
            self._status_summary.set_text(re.sub(r'<[^>]+>', '', markup))
    
    def _on_run_clicked(self, button):
        """Handle Run All button click."""
        if self.on_run_callback:
            pending = self.get_pending_experiments()
            if pending:
                self.on_run_callback(pending)
            else:
                # No pending experiments - show helpful message
                total = len(self.queue_store)
                if total == 0:
                    self.status_label.set_markup("<i>Queue empty - generate experiments first</i>")
                else:
                    self.status_label.set_markup("<i>No pending experiments - use 'Reset All' to re-run</i>")
    
    def _on_cancel_clicked(self, button):
        """Handle Cancel button click."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def _on_pause_clicked(self, button):
        """Handle Pause/Resume button click (Stage 3).
        
        Toggles between paused and running states. When paused, execution
        stops after the current experiment completes.
        """
        # Check current label to determine action
        if self.pause_button.get_label() == "⏸ Pause":
            # Pause execution
            if hasattr(self, 'on_pause_callback') and self.on_pause_callback:
                self.on_pause_callback(True)  # True = pause
            self.pause_button.set_label("▶ Resume")
            self.pause_button.set_tooltip_text("Resume execution")
            self.status_label.set_markup("<span foreground='orange'><b>Paused</b> - click Resume to continue</span>")
        else:
            # Resume execution
            if hasattr(self, 'on_pause_callback') and self.on_pause_callback:
                self.on_pause_callback(False)  # False = resume
            self.pause_button.set_label("⏸ Pause")
            self.pause_button.set_tooltip_text("Pause execution after current experiment")
            self.status_label.set_markup("<i>Resumed execution</i>")
            GLib.timeout_add(1000, self._update_status_label)  # Restore normal status after 1s
    
    def _on_clear_clicked(self, button):
        """Handle Clear Completed button click."""
        count_before = len(self.queue_store)
        self.clear_completed()
        count_after = len(self.queue_store)
        removed = count_before - count_after
        
        if removed > 0:
            self.status_label.set_markup(f"<i>Removed {removed} completed experiments</i>")
            # Give brief feedback then restore normal status
            GLib.timeout_add(2000, self._update_status_label)
        
        if self.on_clear_callback:
            self.on_clear_callback()
    
    def _on_reset_clicked(self, button):
        """Handle Reset All button click."""
        count = self.reset_all_to_pending()
        if count > 0:
            self.status_label.set_markup(f"<i>Reset {count} experiments to pending</i>")
            # Give brief feedback then restore normal status
            GLib.timeout_add(2000, self._update_status_label)
    
    def reset_all_to_pending(self):
        """Reset all completed/failed experiments back to pending status.
        
        Returns:
            int: Number of experiments reset
        """
        count = 0
        iter = self.queue_store.get_iter_first()
        while iter:
            status = self.queue_store.get_value(iter, 1)
            # Reset any non-pending status back to pending
            if status != self.STATUS_PENDING:
                self.queue_store.set_value(iter, 1, self.STATUS_PENDING)
                self.queue_store.set_value(iter, 2, "0%")
                count += 1
            iter = self.queue_store.iter_next(iter)
        self._update_status_label()
        return count
    
    def set_run_callback(self, callback):
        """Set callback for Run All button.
        
        Args:
            callback: Function to call with list of pending experiments
        """
        self.on_run_callback = callback
    
    def set_cancel_callback(self, callback):
        """Set callback for Cancel button.
        
        Args:
            callback: Function to call when canceling
        """
        self.on_cancel_callback = callback
    
    def set_clear_callback(self, callback):
        """Set callback for Clear button.
        
        Args:
            callback: Function to call after clearing
        """
        self.on_clear_callback = callback
    
    def set_pause_callback(self, callback):
        """Set callback for Pause/Resume button (Stage 3).
        
        Args:
            callback: Function to call with boolean (True=pause, False=resume)
        """
        self.on_pause_callback = callback
    
    def set_run_remote_callback(self, callback):
        """Set callback for Run Remote button.
        
        Args:
            callback: Function to call when dispatching to remote server
        """
        self.on_run_remote_callback = callback
    
    def _on_run_remote_clicked(self, button):
        """Handle Run Remote button click."""
        if self.on_run_remote_callback:
            pending = self.get_pending_experiments()
            if pending:
                self.on_run_remote_callback(pending)
            else:
                total = len(self.queue_store)
                if total == 0:
                    self.status_label.set_markup("<i>Queue empty - generate experiments first</i>")
                else:
                    self.status_label.set_markup("<i>No pending experiments - use 'Reset All' to re-run</i>")

    # ── Public status API ────────────────────────────────────────────

    # Category → (label-prefix, default-tag) mapping for the activity log
    _CATEGORIES = {
        'setup':      ('SETUP',  'grey'),
        'allocation': ('ALLOC',  'blue'),
        'event':      ('EVENT',  'orange'),
        'stream':     ('REMOTE', 'blue'),
        'condition':  ('COND',   'blue'),
        'done':       ('DONE',   'green'),
        'error':      ('ERROR',  'red'),
        'paused':     ('PAUSE',  'orange'),
        'info':       ('INFO',   'grey'),
    }

    def append_status(self, text: str, category: str = 'info',
                      tag: str = '') -> None:
        """Append a categorised line to the activity log.

        Each call adds a new line so messages never overwrite each other;
        the user can scroll back through the full history. Consecutive
        identical lines are coalesced (the prior duplicate is silently
        dropped) to avoid spam from rapid re-emits.

        Args:
            text:     Plain text to display (already markup-stripped).
            category: One of ``_CATEGORIES`` keys (default 'info').
            tag:      Override tag name; falls back to category default.
        """
        cat_label, default_tag = self._CATEGORIES.get(
            category, self._CATEGORIES['info'])
        tag = tag or default_tag

        # Drop exact-duplicate consecutive emits
        line_key = (category, text)
        if self._status_last_line == line_key:
            return
        self._status_last_line = line_key

        import time as _time
        ts = _time.strftime('%H:%M:%S')
        prefix = f'[{ts}] [{cat_label}] '

        buf = self._status_buffer
        # Add separating newline if buffer not empty
        end = buf.get_end_iter()
        if buf.get_char_count() > 0:
            buf.insert(end, '\n')
            end = buf.get_end_iter()

        # Insert prefix in grey, message in chosen tag
        buf.insert_with_tags_by_name(end, prefix, 'grey')
        end = buf.get_end_iter()
        if tag and buf.get_tag_table().lookup(tag):
            buf.insert_with_tags_by_name(end, text, tag)
        else:
            buf.insert(end, text)

        # Cap buffer to last N lines (drop oldest)
        line_count = buf.get_line_count()
        if line_count > self._status_max_lines:
            cut = buf.get_iter_at_line(line_count - self._status_max_lines)
            buf.delete(buf.get_start_iter(), cut)

        # Auto-scroll to end
        self._status_view.scroll_to_iter(
            buf.get_end_iter(), 0.0, False, 0.0, 0.0)

    def set_status(self, text: str, tag: str = ''):
        """Backward-compatible entry point — forwards to :meth:`append_status`.

        Args:
            text: Status message (plain text — no markup).
            tag:  Optional tag name. The category is inferred from the tag.
        """
        tag_to_cat = {
            'green':  'done',
            'red':    'error',
            'orange': 'paused',
            'blue':   'stream',
            'grey':   'info',
            '':       'info',
        }
        category = tag_to_cat.get(tag, 'info')
        self.append_status(text, category=category, tag=tag)

    def clear_status(self) -> None:
        """Clear the activity log.

        Resets dedup state and emits a confirmation marker so the user
        gets immediate feedback that the log is alive (the next sweep
        message may not arrive for several seconds while workers are
        silently simulating).
        """
        self._status_buffer.set_text('')
        self._status_last_line = None
        # Force redraw and emit a confirmation line so the user sees
        # the log is still receiving messages.
        self._status_view.queue_draw()
        self.append_status('Activity log cleared', category='info', tag='grey')

    def _copy_status_to_clipboard(self) -> str:
        """Copy current selection (or the whole log) to the clipboard.

        Returns the text actually copied so callers / tests can inspect.
        """
        buf = self._status_buffer
        if buf.get_has_selection():
            bounds = buf.get_selection_bounds()
            text = buf.get_text(bounds[0], bounds[1], False)
        else:
            text = buf.get_text(buf.get_start_iter(),
                                buf.get_end_iter(), False)
        if not text:
            return ''
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        # Also copy to the PRIMARY (X11 middle-click) selection for
        # convenience on Linux.
        try:
            primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
            primary.set_text(text, -1)
        except Exception:
            pass
        return text

    def _copy_full_log_to_clipboard(self) -> str:
        """Copy the entire activity log to the clipboard, ignoring selection."""
        buf = self._status_buffer
        text = buf.get_text(buf.get_start_iter(),
                            buf.get_end_iter(), False)
        if not text:
            return ''
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        return text

    def _on_status_populate_popup(self, textview, popup) -> None:
        """Inject Copy / Copy all / Select all into the right-click menu.

        Some GTK themes override the default popup; this guarantees the
        copy actions are always discoverable.
        """
        if not isinstance(popup, Gtk.Menu):
            return
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        popup.append(sep)
        item_copy = Gtk.MenuItem(label='Copy selection')
        item_copy.connect('activate',
                          lambda *_: self._copy_status_to_clipboard())
        item_copy.show()
        popup.append(item_copy)
        item_copy_all = Gtk.MenuItem(label='Copy entire log')
        item_copy_all.connect(
            'activate',
            lambda *_: self._copy_full_log_to_clipboard())
        item_copy_all.show()
        popup.append(item_copy_all)
        item_select_all = Gtk.MenuItem(label='Select all')
        item_select_all.connect(
            'activate',
            lambda *_: self._status_buffer.select_range(
                self._status_buffer.get_start_iter(),
                self._status_buffer.get_end_iter()))
        item_select_all.show()
        popup.append(item_select_all)

    def _on_status_key_press(self, widget, event):
        """Handle Ctrl+C / Ctrl+A on the status TextView."""
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval in (Gdk.KEY_c, Gdk.KEY_C):
            self._copy_status_to_clipboard()
            return True  # handled
        if ctrl and event.keyval in (Gdk.KEY_a, Gdk.KEY_A):
            buf = self._status_buffer
            buf.select_range(buf.get_start_iter(), buf.get_end_iter())
            return True
        return False


class _StatusLabelCompat:
    """Shim so ``queue_view.status_label.set_markup(...)`` keeps working.

    Translates Pango markup calls into category-aware appends to the
    new :class:`Gtk.TextView`-based activity log.
    """

    # Minimal regex to strip Pango/HTML tags for the plain-text view
    import re as _re
    _TAG_RE = _re.compile(r'<[^>]+>')
    _ENT = {'&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"'}

    def __init__(self, view: ExperimentQueueView):
        self._view = view

    def _infer_category(self, markup: str, text: str) -> tuple:
        """Return ``(category, tag)`` based on markup + text content."""
        low = text.lower()
        # Remote-stream lines first: a "done in 7.2s (30 ok, 0 errors)"
        # is success, not an error, even though it contains "errors".
        if low.startswith('remote:') or low.startswith('[remote]'):
            # Promote to DONE if the streamed line is a clear completion
            if 'done in' in low or '✓' in markup:
                return 'done', 'green'
            # Real failures from the remote side
            if '✗' in markup or ' failed' in low or 'traceback' in low:
                return 'error', 'red'
            return 'stream', 'blue'
        if '✓' in markup or low.startswith('done'):
            return 'done', 'green'
        # Tighten: require word-boundaries, not substring "errors" in "0 errors"
        if ('✗' in markup
                or ' failed' in low or low.startswith('failed')
                or low.endswith('failed')
                or ' error:' in low or low.startswith('error')
                or 'traceback' in low or 'exception' in low):
            return 'error', 'red'
        if 'paused' in low or 'orange' in markup:
            return 'paused', 'orange'
        if 'allocated' in low:
            return 'allocation', 'blue'
        if 'event' in low and ('dispatch' in low or 'redose' in low
                               or 'washout' in low or '@' in text):
            return 'event', 'orange'
        if low.startswith(('exporting', 'uploading', 'opening',
                           'cleaning', 'checking', 'creating', 'fetching')):
            return 'setup', 'grey'
        if low.startswith('running sweep'):
            return 'condition', 'blue'
        if 'foreground=' in markup:
            if 'green' in markup:
                return 'done', 'green'
            if 'red' in markup:
                return 'error', 'red'
            if 'orange' in markup:
                return 'paused', 'orange'
            if 'blue' in markup:
                return 'stream', 'blue'
        return 'info', ''

    def set_markup(self, markup: str):
        """Accept Pango markup, strip tags, append a categorised log line."""
        text = self._TAG_RE.sub('', markup)
        for ent, ch in self._ENT.items():
            text = text.replace(ent, ch)
        text = text.strip()
        if not text:
            return
        category, tag = self._infer_category(markup, text)
        self._view.append_status(text, category=category, tag=tag)
