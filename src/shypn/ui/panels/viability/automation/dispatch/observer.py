"""Observer protocol for sweep-dispatch progress / completion events.

Implementers (typically the viability automation category) translate
these into queue-view UI updates. The controller must call observer
methods on the **GTK main thread** — controllers wrap background-thread
callbacks in ``GLib.idle_add`` before forwarding.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class DispatchObserver(Protocol):
    """Receives lifecycle events from a ``SweepDispatchController``.

    All methods are called on the GTK main thread.
    """

    def on_status(self, message: str, level: str = 'info') -> None:
        """Free-form status line for the activity log.

        ``level`` is one of ``'info' | 'success' | 'warning' | 'error'``.
        """

    def on_row_started(self, row_index: int) -> None:
        """A queue row transitioned to running."""

    def on_row_completed(
        self,
        row_index: int,
        ok_replicates: int,
        error_replicates: int,
        wall_seconds: float,
    ) -> None:
        """A queue row finished. Implementers should mark it completed."""

    def on_dispatch_complete(
        self,
        success: bool,
        results_dir: Optional[str],
        message: str,
    ) -> None:
        """Whole sweep finished (success or failure).

        After this call the controller's ``is_active`` is False and the
        observer should restore the idle UI state (Run buttons enabled,
        Cancel disabled) and reconcile any leftover ``running`` rows.
        """
