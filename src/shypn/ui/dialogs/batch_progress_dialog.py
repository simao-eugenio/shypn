#!/usr/bin/env python3
"""Batch Progress Dialog - Show progress during batch simulation execution.

Displays progress bar, current replicate, elapsed time, and ETA during
batch mode simulation. Allows user to cancel execution gracefully.

Author: SHYpn Development Team
Date: December 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, Callable


class BatchProgressDialog(Gtk.Dialog):
    """Progress dialog for batch simulation execution.
    
    Features:
    - Progress bar showing percentage complete
    - Text showing current replicate (e.g., "Running replicate 42/100")
    - Elapsed time display
    - ETA display (e.g., "Estimated: 2m 15s remaining")
    - Cancel button for graceful cancellation
    - Auto-closes on completion with summary
    
    The dialog is non-modal and stays on top of parent window.
    """
    
    def __init__(self, parent: Optional[Gtk.Window] = None, total_replicates: int = 100):
        """Initialize batch progress dialog.
        
        Args:
            parent: Parent window (dialog will center on this)
            total_replicates: Total number of replicates to run
        """
        super().__init__(
            title="Batch Simulation Progress",
            transient_for=parent,
            modal=False,
            destroy_with_parent=True
        )
        
        self.total_replicates = total_replicates
        self.is_cancelled = False
        self._cancel_callback: Optional[Callable] = None
        
        # Configure dialog
        self.set_default_size(500, 200)
        self.set_keep_above(True)  # Stay on top
        self.set_deletable(False)  # Prevent closing during execution
        
        # Build UI
        self._build_ui()
        
        # Show all widgets
        self.show_all()
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Get content area
        content = self.get_content_area()
        content.set_spacing(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title label
        title_label = Gtk.Label()
        title_label.set_markup("<b>Running Batch Simulation</b>")
        title_label.set_halign(Gtk.Align.START)
        content.pack_start(title_label, False, False, 0)
        
        # Status label (e.g., "Running replicate 42/100")
        self.status_label = Gtk.Label()
        self.status_label.set_text(f"Preparing batch execution ({self.total_replicates} replicates)...")
        self.status_label.set_halign(Gtk.Align.START)
        content.pack_start(self.status_label, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("0%")
        content.pack_start(self.progress_bar, False, False, 0)
        
        # Details box (elapsed time and ETA)
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        
        # Elapsed time label
        self.elapsed_label = Gtk.Label()
        self.elapsed_label.set_text("Elapsed: 0s")
        self.elapsed_label.set_halign(Gtk.Align.START)
        details_box.pack_start(self.elapsed_label, True, True, 0)
        
        # ETA label
        self.eta_label = Gtk.Label()
        self.eta_label.set_text("Estimated: Calculating...")
        self.eta_label.set_halign(Gtk.Align.END)
        details_box.pack_start(self.eta_label, True, True, 0)
        
        content.pack_start(details_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content.pack_start(separator, False, False, 5)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup("<i>Note: Cancellation will complete after current replicate finishes</i>")
        info_label.set_halign(Gtk.Align.START)
        info_label.get_style_context().add_class("dim-label")
        content.pack_start(info_label, False, False, 0)
        
        # Cancel button
        self.cancel_button = self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.cancel_button.connect("clicked", self._on_cancel_clicked)
    
    def _on_cancel_clicked(self, button):
        """Handle cancel button clicked."""
        self.is_cancelled = True
        self.cancel_button.set_sensitive(False)
        self.cancel_button.set_label("Cancelling...")
        self.status_label.set_markup("<b>Cancellation requested - finishing current replicate...</b>")
        
        # Call cancel callback if registered
        if self._cancel_callback:
            self._cancel_callback()
    
    def set_cancel_callback(self, callback: Callable):
        """Register callback to invoke when user clicks cancel.
        
        Args:
            callback: Function to call when cancel is clicked
        """
        self._cancel_callback = callback
    
    def update_progress(self, replicate_num: int, total: int, elapsed: float, eta_str: str):
        """Update progress display.
        
        Args:
            replicate_num: Current replicate number (1-based)
            total: Total number of replicates
            elapsed: Elapsed time in seconds
            eta_str: Formatted ETA string (e.g., "2m 15s")
        """
        # Update progress bar
        fraction = replicate_num / total
        percent = int(fraction * 100)
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{percent}%")
        
        # Update status label
        self.status_label.set_text(f"Running replicate {replicate_num}/{total}")
        
        # Update elapsed time
        if elapsed < 60:
            elapsed_str = f"{int(elapsed)}s"
        elif elapsed < 3600:
            minutes = int(elapsed / 60)
            seconds = int(elapsed % 60)
            elapsed_str = f"{minutes}m {seconds}s"
        else:
            hours = int(elapsed / 3600)
            minutes = int((elapsed % 3600) / 60)
            elapsed_str = f"{hours}h {minutes}m"
        
        self.elapsed_label.set_text(f"Elapsed: {elapsed_str}")
        
        # Update ETA
        if replicate_num >= total:
            self.eta_label.set_text("Estimated: Complete")
        else:
            self.eta_label.set_text(f"Estimated: {eta_str} remaining")
    
    def show_completion(self, successful: int, total: int, total_time: float):
        """Show completion summary.
        
        Args:
            successful: Number of successful replicates
            total: Total number of replicates attempted
            total_time: Total elapsed time in seconds
        """
        # Update progress bar to 100%
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("100%")
        
        # Update status
        if successful == total:
            status_text = f"✅ Batch complete: All {total} replicates successful"
        else:
            status_text = f"⚠️ Batch complete: {successful}/{total} replicates successful"
        
        self.status_label.set_markup(f"<b>{status_text}</b>")
        
        # Update time display
        if total_time < 60:
            time_str = f"{total_time:.1f}s"
        elif total_time < 3600:
            minutes = int(total_time / 60)
            seconds = int(total_time % 60)
            time_str = f"{minutes}m {seconds}s"
        else:
            hours = int(total_time / 3600)
            minutes = int((total_time % 3600) / 60)
            time_str = f"{hours}h {minutes}m"
        
        self.elapsed_label.set_text(f"Total time: {time_str}")
        self.eta_label.set_text("")
        
        # Change cancel button to close button
        self.cancel_button.set_label("Close")
        self.cancel_button.set_sensitive(True)
        self.cancel_button.disconnect_by_func(self._on_cancel_clicked)
        self.cancel_button.connect("clicked", lambda b: self.destroy())
        
        # Allow closing
        self.set_deletable(True)
        
        # Auto-close after 3 seconds (optional)
        # GLib.timeout_add_seconds(3, self.destroy)
    
    def show_error(self, error_message: str):
        """Show error message.
        
        Args:
            error_message: Error description
        """
        self.status_label.set_markup(f"<b>❌ Error: {error_message}</b>")
        self.cancel_button.set_label("Close")
        self.cancel_button.set_sensitive(True)
        self.cancel_button.disconnect_by_func(self._on_cancel_clicked)
        self.cancel_button.connect("clicked", lambda b: self.destroy())
        self.set_deletable(True)


# ============================================================================
# Convenience Functions
# ============================================================================

def show_batch_progress_dialog(parent: Optional[Gtk.Window], total_replicates: int) -> BatchProgressDialog:
    """Create and show batch progress dialog.
    
    Args:
        parent: Parent window
        total_replicates: Total number of replicates
        
    Returns:
        BatchProgressDialog instance
        
    Example:
        dialog = show_batch_progress_dialog(main_window, 100)
        dialog.update_progress(50, 100, 45.2, "45s")
        dialog.show_completion(100, 100, 90.5)
    """
    dialog = BatchProgressDialog(parent, total_replicates)
    dialog.show()
    return dialog
