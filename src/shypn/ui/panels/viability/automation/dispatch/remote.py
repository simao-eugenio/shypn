"""Remote sweep dispatch controller.

Wraps the existing ``RemoteSweepDispatcher`` (which handles SSH +
ControlMaster + tar fetch) and translates its raw ``progress_cb`` /
``complete_cb`` stream into typed observer callbacks.

CLI ``--verbose`` line shapes parsed here::

    [1/4] Condition.name=50 (10 replicates)...
      done in 7.2s (10 ok, 0 errors)
    Sweep complete in 28.3s
"""
from __future__ import annotations

import logging
import re
from typing import Optional, TYPE_CHECKING

from gi.repository import GLib

from .base import SweepDispatchController
from .observer import DispatchObserver
from .types import DispatchKind, DispatchRequest

if TYPE_CHECKING:
    from ..remote_sweep_dispatcher import RemoteSweepDispatcher, RemoteSweepSettings

_log = logging.getLogger(__name__)

# Pre-compiled regexes — the hot path runs once per CLI line.
#
# CLI line shapes (sweep_runner.py, --verbose):
#   start: "[1/8] Baseline (30 replicates)..."
#   done : "[done 3/8] Baseline in 4681.9s (30 ok, 0 errors) [cpu=...]"
#
# The explicit row index on the *done* line is required because the
# CLI submits conditions to a process pool with sliding-window
# parallelism: when workers >= conditions, every [i/N] start line
# emits before any condition finishes, so we cannot pair a bare
# 'done in Xs' against the most-recent start.
_RE_ROW_START = re.compile(r'^\[(\d+)/(\d+)\]\s+(.+?)\s+\(')
_RE_ROW_DONE = re.compile(
    r'^\[done\s+(\d+)/(\d+)\]\s+(.+?)\s+in\s+([\d.]+)s\s+'
    r'\((\d+)\s+ok,\s+(\d+)\s+error'
)
# Legacy bare-form, kept so older server engines still produce some
# (best-effort, last-row) progress instead of nothing.
_RE_ROW_DONE_LEGACY = re.compile(
    r'^\s*done in ([\d.]+)s\s+\((\d+)\s+ok,\s+(\d+)\s+error'
)


class RemoteSweepDispatchController(SweepDispatchController):
    """Drives a sweep on the remote GPU server via SSH.

    Owns the underlying ``RemoteSweepDispatcher`` instance so the loader
    no longer has to. ``cancel()`` propagates to the SSH stream + remote
    pkill via the wrapped dispatcher.
    """

    KIND = DispatchKind.REMOTE

    def __init__(
        self,
        observer: DispatchObserver,
        settings: 'RemoteSweepSettings',
        experiment_manager,
    ) -> None:
        super().__init__(observer)
        # Lazy import to avoid pulling SSH/threading code at module load.
        from ..remote_sweep_dispatcher import RemoteSweepDispatcher
        self._dispatcher: 'RemoteSweepDispatcher' = RemoteSweepDispatcher(settings)
        self._experiment_manager = experiment_manager
        self._n_total: int = 0
        # Tracks the row currently parsing as 'running' so we can pair
        # the next 'done in Xs' line with the right row index.
        self._current_row: Optional[int] = None

    # ── transport accessors ───────────────────────────────────────
    @property
    def underlying(self) -> 'RemoteSweepDispatcher':
        """Escape hatch for code that still pokes the raw dispatcher."""
        return self._dispatcher

    # ── SweepDispatchController hooks ─────────────────────────────
    def _run(self, request: DispatchRequest) -> None:
        self._n_total = len(request.experiments)
        self._current_row = None
        self._dispatcher.dispatch(
            model_filepath=request.model_filepath,
            project_folder=request.project_folder,
            experiment_manager=self._experiment_manager,
            sim_params=request.sim_params.to_dict(),
            progress_cb=self._on_raw_progress,
            complete_cb=self._on_raw_complete,
            ssh_password=request.ssh_password,
            events=request.events or [],
            fixed_overrides=request.fixed_overrides or None,
        )

    def _cancel_impl(self) -> None:
        try:
            self._dispatcher.cancel()
        except Exception:
            _log.exception('remote dispatcher cancel raised')

    # ── raw → typed event translation ─────────────────────────────
    def _on_raw_progress(self, msg: str) -> None:
        """Background-thread callback from RemoteSweepDispatcher.

        Translates the CLI line into either a row event or a status line,
        marshalling onto the GTK main thread before forwarding.
        """
        text = str(msg)

        m_start = _RE_ROW_START.match(text)
        if m_start:
            cond_idx = int(m_start.group(1)) - 1
            # Track for the legacy fallback path only; the new explicit
            # done-line carries its own index and does not consult this.
            self._current_row = cond_idx
            if 0 <= cond_idx < self._n_total:
                GLib.idle_add(self._dispatch_row_started, cond_idx)
            GLib.idle_add(self._dispatch_status, text, 'info')
            return

        m_done = _RE_ROW_DONE.match(text)
        if m_done:
            row = int(m_done.group(1)) - 1
            wall = float(m_done.group(4))
            ok = int(m_done.group(5))
            errors = int(m_done.group(6))
            if 0 <= row < self._n_total:
                GLib.idle_add(
                    self._dispatch_row_completed, row, ok, errors, wall)
            GLib.idle_add(self._dispatch_status, text, 'info')
            return

        m_done_legacy = _RE_ROW_DONE_LEGACY.match(text)
        if m_done_legacy:
            wall = float(m_done_legacy.group(1))
            ok = int(m_done_legacy.group(2))
            errors = int(m_done_legacy.group(3))
            row = self._current_row if self._current_row is not None else -1
            if 0 <= row < self._n_total:
                GLib.idle_add(
                    self._dispatch_row_completed, row, ok, errors, wall)
            GLib.idle_add(self._dispatch_status, text, 'info')
            return

        GLib.idle_add(self._dispatch_status, text, 'info')

    def _on_raw_complete(
        self, success: bool, local_results_dir: str, message: str,
    ) -> None:
        """Background-thread callback when the SSH pipeline finishes."""
        results = local_results_dir if success and local_results_dir else None
        GLib.idle_add(self._dispatch_complete, success, results, message)

    # ── GTK-thread trampolines ────────────────────────────────────
    # All return False so GLib.idle_add fires them once and discards.
    def _dispatch_status(self, message: str, level: str) -> bool:
        self._emit_status(message, level)
        return False

    def _dispatch_row_started(self, row_index: int) -> bool:
        self._emit_row_started(row_index)
        return False

    def _dispatch_row_completed(
        self, row_index: int, ok: int, errors: int, wall_seconds: float,
    ) -> bool:
        self._emit_row_completed(row_index, ok, errors, wall_seconds)
        return False

    def _dispatch_complete(
        self, success: bool, results_dir: Optional[str], message: str,
    ) -> bool:
        self._emit_complete(success, results_dir, message)
        return False
